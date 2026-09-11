"""
agents/groq_model.py
--------------------
Strands Model adapter for Saarthi's live Groq inference.
Target: openai/gpt-oss-120b
"""

import os
import json
import uuid
import pathlib
import asyncio
import random
from typing import Any, AsyncGenerator, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

from strands.models import Model

_ENV_PATH = pathlib.Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=str(_ENV_PATH), override=True)

from agents.model_factory import get_saarthi_model, get_model

_GROQ_SEM = asyncio.Semaphore(int(os.getenv("GROQ_MAX_CONCURRENT", "2")))

# ── Groq client singleton ──────────────────────────────────────────────────────
_groq_client = None
_groq_client_key_len = 0


def get_groq_client():
    global _groq_client, _groq_client_key_len

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not set or is empty. "
            "Add your key to the project-root .env file: GROQ_API_KEY=gsk_..."
        )

    if _groq_client is None or len(api_key) != _groq_client_key_len:
        import groq as _groq_lib
        _groq_client = _groq_lib.Groq(api_key=api_key)
        _groq_client_key_len = len(api_key)

    return _groq_client


def _convert_strands_messages_to_groq(messages: list[Any], system_prompt: str | None = None) -> list[dict]:
    groq_msgs = []
    sys_str = (system_prompt or "").strip()
    if sys_str:
        groq_msgs.append({"role": "system", "content": sys_str})

    for m in messages:
        if isinstance(m, dict):
            role = m.get("role", "user")
            content = m.get("content", [])
        else:
            role = getattr(m, "role", "user")
            content = getattr(m, "content", [])

        if role == "system":
            continue

        if isinstance(content, str):
            groq_msgs.append({"role": role, "content": content})
            continue

        text_parts = []
        tool_calls = []
        tool_results = []

        for block in (content or []):
            if isinstance(block, dict):
                if "text" in block and block["text"]:
                    text_parts.append(str(block["text"]))
                elif "toolUse" in block:
                    tu = block["toolUse"]
                    inp = tu.get("input", {})
                    if not isinstance(inp, str):
                        inp = json.dumps(inp)
                    tool_calls.append({
                        "id": tu.get("toolUseId") or f"call_{uuid.uuid4().hex[:8]}",
                        "type": "function",
                        "function": {"name": tu.get("name", ""), "arguments": inp}
                    })
                elif "toolResult" in block:
                    tr = block["toolResult"]
                    tr_id = tr.get("toolUseId", "")
                    tr_content = tr.get("content", [])
                    tr_text = ""
                    if isinstance(tr_content, str):
                        tr_text = tr_content
                    elif isinstance(tr_content, list):
                        tr_text = " ".join([
                            str(b.get("text", "")) for b in tr_content
                            if isinstance(b, dict) and "text" in b
                        ])
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tr_id,
                        "content": tr_text or "Success"
                    })
            else:
                if hasattr(block, "text") and block.text:
                    text_parts.append(str(block.text))

        if tool_results:
            groq_msgs.extend(tool_results)
        elif tool_calls:
            msg_obj = {
                "role": "assistant",
                "content": "\n".join(text_parts) if text_parts else None,
                "tool_calls": tool_calls
            }
            groq_msgs.append(msg_obj)
        elif text_parts:
            groq_msgs.append({"role": role, "content": "\n".join(text_parts)})

    return groq_msgs


def _convert_tool_specs_to_groq(tool_specs: list[Any] | None) -> tuple[list[dict], Optional[str]]:
    groq_tools = []
    struct_tool_name = None

    if not tool_specs:
        return groq_tools, struct_tool_name

    for ts in tool_specs:
        if isinstance(ts, dict):
            name = ts.get("name", "")
            desc = ts.get("description", "")
            schema = ts.get("inputSchema", {})
        else:
            name = getattr(ts, "name", "")
            desc = getattr(ts, "description", "")
            schema = getattr(ts, "inputSchema", {})

        if isinstance(schema, dict) and "json" in schema:
            params = schema["json"]
        elif isinstance(schema, dict):
            params = schema
        else:
            params = {"type": "object", "properties": {}}

        if not name:
            continue

        groq_tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": desc or f"Execute {name}",
                "parameters": params
            }
        })

        if "StructuredOutput" in str(desc) or name[0].isupper() or name in ["OrchestrationResult", "CurriculumDecision", "ProgressDiagnosis", "ResourceRecommendation", "ActivityDesign"]:
            struct_tool_name = name
            groq_tools.append({
                "type": "function",
                "function": {
                    "name": "json",
                    "description": f"Output structured JSON for {name}",
                    "parameters": params
                }
            })

    return groq_tools, struct_tool_name


# ── GroqModel Implementation ──────────────────────────────────────────────────

def _get_fallback_chain(start_model: str) -> list[str]:
    raw_env = os.getenv(
        "GROQ_FALLBACK_MODELS",
        "openai/gpt-oss-120b,llama-3.3-70b-versatile,openai/gpt-oss-20b,llama-3.1-8b-instant"
    )
    fallback_list = [m.strip() for m in raw_env.split(",") if m.strip()]

    chain = []
    if start_model:
        chain.append(start_model)
    for model in fallback_list:
        if model not in chain:
            chain.append(model)
    return chain


def _is_decommissioned_error(e: Exception) -> bool:
    err_str = str(e).lower()
    body_str = ""
    if hasattr(e, "body") and isinstance(e.body, dict):
        body_str = json.dumps(e.body).lower()
    full_msg = f"{err_str} {body_str}"
    return (
        "decommissioned" in full_msg
        or "model_decommissioned" in full_msg
        or "model_not_found" in full_msg
        or "not_found" in full_msg
        or "not found" in full_msg
    )


def _sanitize_messages(messages: list[Any]) -> list[dict[str, Any]]:
    """Groq rejects reasoningContent on replayed multi-turn history."""
    clean = []
    for msg in messages:
        if isinstance(msg, dict):
            m = dict(msg)
            for key in ("reasoningContent", "reasoning_content", "reasoning"):
                m.pop(key, None)
            clean.append(m)
        else:
            clean.append(msg)
    return clean


async def _execute_completion_with_fallback(
    client: Any,
    req_kwargs: dict[str, Any],
    model_obj: Any,
    max_retries: int = 4,
    base_delay: float = 2.0,
) -> Any:
    import groq

    if "messages" in req_kwargs and isinstance(req_kwargs["messages"], list):
        req_kwargs["messages"] = _sanitize_messages(req_kwargs["messages"])

    start_model = req_kwargs.get("model") or getattr(model_obj, "model_name", None) or os.getenv("GROQ_MODEL_ID", "openai/gpt-oss-120b")
    chain = _get_fallback_chain(start_model)

    last_exception = None

    for candidate_model in chain:
        req_kwargs["model"] = candidate_model
        if getattr(model_obj, "model_name", None) != candidate_model:
            print(f"[GroqModel Fallback] Active model updated: '{candidate_model}' (previously '{getattr(model_obj, 'model_name', None)}')")
            if hasattr(model_obj, "model_name"):
                model_obj.model_name = candidate_model

        for attempt in range(max_retries):
            try:
                async with _GROQ_SEM:
                    reasoning = getattr(model_obj, "reasoning_effort", None)
                    if reasoning:
                        try:
                            req_kwargs["messages"] = _sanitize_messages(req_kwargs["messages"])
                            return client.chat.completions.create(
                                **req_kwargs, reasoning_effort=reasoning
                            )
                        except (TypeError, groq.BadRequestError, groq.UnprocessableEntityError) as err:
                            if _is_decommissioned_error(err):
                                raise err

                    req_kwargs["messages"] = _sanitize_messages(req_kwargs["messages"])
                    return client.chat.completions.create(**req_kwargs)

            except groq.BadRequestError as e:
                if _is_decommissioned_error(e):
                    last_exception = e
                    print(f"[GroqModel Fallback] Model '{candidate_model}' raised BadRequestError ({e}). Retrying with next model in fallback chain...")
                    break
                else:
                    raise

            except (groq.RateLimitError, groq.InternalServerError, groq.APIConnectionError, groq.APIStatusError) as e:
                last_exception = e
                if attempt == max_retries - 1:
                    raise

                retry_after = getattr(getattr(e, "response", None), "headers", {}).get("retry-after")
                try:
                    sleep_time = float(retry_after) if retry_after else base_delay * (2 ** attempt)
                except (ValueError, TypeError):
                    sleep_time = base_delay * (2 ** attempt)

                sleep_time += random.uniform(0, 1)  # Add 0-1s random jitter
                print(f"[GroqModel] API Error ({type(e).__name__} on '{candidate_model}'). Retrying in {sleep_time:.2f}s...")
                await asyncio.sleep(sleep_time)

    if last_exception:
        raise last_exception
    raise RuntimeError("All Groq model fallback candidates failed.")


class GroqModel(Model):
    """
    Strands Model implementation backing live Saarthi agent reasoning.
    Target model: openai/gpt-oss-120b via Groq API.
    """

    def __init__(
        self,
        model_name: str | None = None,
        reasoning_effort: str = "low",
        temperature: float = 0.2,
    ):
        if not model_name:
            model_name = os.getenv("GROQ_MODEL_ID", "openai/gpt-oss-120b")
        self.model_name = model_name
        self.reasoning_effort = reasoning_effort
        self.temperature = temperature

    def update_config(self, **model_config: Any) -> None:
        if "model_name" in model_config:
            self.model_name = model_config["model_name"]
        if "reasoning_effort" in model_config:
            self.reasoning_effort = model_config["reasoning_effort"]
        if "temperature" in model_config:
            self.temperature = model_config["temperature"]

    def get_config(self) -> Any:
        return {
            "model_name": self.model_name,
            "reasoning_effort": self.reasoning_effort,
            "temperature": self.temperature,
        }

    async def structured_output(
        self,
        output_model: type[BaseModel],
        prompt: Any,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[dict[str, Any], None]:
        client = get_groq_client()
        schema = output_model.model_json_schema() if hasattr(output_model, "model_json_schema") else {}

        sys_content = (system_prompt or "").strip()
        sys_content += (
            "\n\nCRITICAL OUTPUT REQUIREMENT:\n"
            "You MUST return ONLY a valid, raw JSON object matching this JSON Schema:\n"
            + json.dumps(schema, indent=2)
            + "\nDo NOT use markdown fences. Do NOT add surrounding text."
        )

        user_content = str(prompt)
        messages = [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": user_content}
        ]

        req_kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": self.temperature,
        }

        response = await _execute_completion_with_fallback(client, req_kwargs, self)

        raw = (response.choices[0].message.content or "{}").strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        parsed = output_model.model_validate_json(raw)
        yield parsed

    async def stream(
        self,
        messages: list[Any],
        tool_specs: list[Any] | None = None,
        system_prompt: str | None = None,
        *,
        tool_choice: dict | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[dict[str, Any], None]:
        client = get_groq_client()

        groq_msgs = _convert_strands_messages_to_groq(messages, system_prompt)
        groq_tools, struct_tool_name = _convert_tool_specs_to_groq(tool_specs)

        req_kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": groq_msgs,
            "temperature": self.temperature,
        }

        if groq_tools:
            req_kwargs["tools"] = groq_tools
            if isinstance(tool_choice, dict):
                if "any" in tool_choice:
                    req_kwargs["tool_choice"] = "required"
                elif "tool" in tool_choice and isinstance(tool_choice["tool"], dict):
                    t_name = tool_choice["tool"].get("name")
                    if t_name:
                        req_kwargs["tool_choice"] = {"type": "function", "function": {"name": t_name}}
                elif "auto" in tool_choice:
                    req_kwargs["tool_choice"] = "auto"
        else:
            has_json = any(
                "json" in m.get("content", "").lower()
                for m in groq_msgs
                if isinstance(m.get("content"), str)
            )
            if has_json:
                req_kwargs["response_format"] = {"type": "json_object"}

        print(f"[MODEL_PROVIDER: GROQ]  [MODEL: {self.model_name}]  [tools: {len(groq_tools)}]  [struct_tool: {struct_tool_name}]")

        response = await _execute_completion_with_fallback(client, req_kwargs, self)

        choice = response.choices[0]
        msg = choice.message

        if msg.tool_calls:
            for tc in msg.tool_calls:
                call_id = tc.id or f"call_{uuid.uuid4().hex[:8]}"
                fn_name = tc.function.name
                if fn_name == "json" and struct_tool_name:
                    fn_name = struct_tool_name

                fn_args = tc.function.arguments or "{}"

                yield {"messageStart": {"role": "assistant"}}
                yield {
                    "contentBlockStart": {
                        "start": {
                            "toolUse": {
                                "toolUseId": call_id,
                                "name": fn_name
                            }
                        },
                        "contentBlockIndex": 0
                    }
                }
                yield {
                    "contentBlockDelta": {
                        "delta": {
                            "toolUse": {
                                "input": fn_args
                            }
                        },
                        "contentBlockIndex": 0
                    }
                }
                yield {"contentBlockStop": {"contentBlockIndex": 0}}
                yield {"messageStop": {"stopReason": "tool_use"}}
        else:
            text = (msg.content or "").strip()
            if not text:
                text = "OK"

            yield {"messageStart": {"role": "assistant"}}
            yield {
                "contentBlockStart": {
                    "start": {"text": ""},
                    "contentBlockIndex": 0
                }
            }
            yield {
                "contentBlockDelta": {
                    "delta": {"text": text},
                    "contentBlockIndex": 0
                }
            }
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "end_turn"}}
