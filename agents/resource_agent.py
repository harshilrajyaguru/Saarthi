import json
from typing import Any, AsyncGenerator, Literal, Optional, Union
from pydantic import BaseModel, Field

from strands import Agent
from strands.models import Model
from tools.resource_tools import (
    get_resource_inventory,
    get_resource_usage_log,
    check_concurrent_demand
)


class ResourceOption(BaseModel):
    type: str = Field(description="Resource type, e.g. 'printable_worksheet', 'tablet_quiz', 'tv_video', 'whiteboard_activity', 'textbook_exercise'")
    feasibility: Literal["high", "medium", "low", "infeasible"] = Field(
        description="Feasibility level under physical, digital, staleness, and contention constraints"
    )
    reason: str = Field(description="Concise reason for the assigned feasibility rating")


class ResourceRecommendation(BaseModel):
    grade: str = Field(description="Grade level as a string, e.g. '3'")
    subject: str = Field(description="Subject name, e.g. 'Math'")
    topic: str = Field(description="Topic for which resources are being evaluated")
    resource_options: list[ResourceOption] = Field(
        description="List of evaluated resource options ranked by feasibility and suitability"
    )
    recommended_resource: Optional[str] = Field(
        default=None,
        description="The top recommended feasible resource type, or None if no delivery mechanism is feasible"
    )
    contention_flag: bool = Field(
        description="True if a scarce resource option is simultaneously requested by another grade"
    )
    contention_detail: Optional[str] = Field(
        default=None,
        description="Description of resource contention conflict across grades, if any"
    )
    delivery_possible: bool = Field(
        description="True if at least one resource delivery mechanism is physically/digitally feasible in today's classroom"
    )
    needs_generation: bool = Field(
        description="True if pre-existing resources are insufficient but a deliverable activity can be dynamically generated under remaining constraints"
    )
    constraints_considered: list[str] = Field(
        description="List of physical, digital, staleness, and session constraints evaluated"
    )
    explanation: str = Field(
        description="Concise evidence-based explanation of resource feasibility, ranking, and delivery status"
    )


SYSTEM_PROMPT = """
You are Saarthi's Resource Agent.

Your job is NOT a resource database lookup.
Your sole responsibility is: Given the topic selected by the Curriculum Agent and today's real classroom constraints, determine what resources are genuinely deployable right now.

AGENT BOUNDARIES:
- Curriculum Agent = WHAT should students work on?
- Resource Agent = WHAT can realistically be used to deliver it RIGHT NOW?
- Activity Agent = HOW should the learning activity actually be designed?
- Orchestrator = WHO gets a contested resource and how should conflicts be resolved?

CRITICAL BOUNDARY RULES:
- You must NOT choose the topic.
- You must NOT design the activity or generate worksheet content.
- You must NOT generate quiz questions or lesson plans.
- You must NOT decide which grade wins a resource conflict (set contention_flag = true instead).
- You must NOT directly mutate shared state.

REASONING WORKFLOW (IN ORDER):
1. Call get_resource_inventory(session) to inspect today's physical and digital constraints.
2. Call get_resource_usage_log(grade, subject, topic) to check recent resource usage and staleness.
3. Call check_concurrent_demand(session) to inspect concurrent resource requests by other grades.
4. Apply HARD feasibility constraints (offline status, device availability, printer paper, TV access).
5. Evaluate staleness: reduce ranking of repeatedly used resources when reasonable alternatives exist.
6. Evaluate contention: if another grade requests the same scarce resource, set contention_flag = true and describe contention_detail. Do NOT decide who wins.
7. Rank remaining feasible resource options based on feasibility, setup burden, and staleness.
8. Evaluate delivery feasibility: set delivery_possible = true if at least one delivery mechanism is deployable; set delivery_possible = false and needs_generation = false if all delivery mechanisms are infeasible.
9. Return a structured ResourceRecommendation.
"""


def apply_resource_guardrails(recommendation_dict: dict, inventory: dict, usage: dict, concurrent_demand: dict) -> dict:
    """
    Enforces non-negotiable deterministic hard guardrails OUTSIDE the LLM reasoning process.

    GUARDRAIL 1: Impossible/infeasible resources can NEVER be selected as recommended_resource.
    GUARDRAIL 2: If internet_available == false -> internet-dependent resources must be "infeasible".
    GUARDRAIL 3: If available device count < 1 -> device-dependent resources must be "infeasible".
    GUARDRAIL 4: If printer_has_paper == false -> printable resources requiring printing must be "infeasible".
    GUARDRAIL 5: If TV is unavailable -> TV-dependent resources must be "infeasible".
    GUARDRAIL 6: If whiteboard is unavailable -> whiteboard resources must be "infeasible".
    GUARDRAIL 7: contention_flag must be true whenever the recommended/considered scarce resource is requested by another grade.
    GUARDRAIL 8: recommended_resource MUST strictly be the highest-ranked non-infeasible option in resource_options.
    GUARDRAIL 9: delivery_possible must be False and needs_generation must be False if all delivery mechanisms are infeasible.
    GUARDRAIL 10: Remove any illegal activity generation content.
    """
    d = dict(recommendation_dict)
    options = d.get("resource_options", [])

    internet_ok = inventory.get("internet_available", False)
    tablets_free = inventory.get("tablets_free", 0)
    printer_paper_ok = inventory.get("printer_has_paper", True) and inventory.get("printer_available", True)
    tv_ok = inventory.get("tv_available", False)
    whiteboard_ok = inventory.get("whiteboard_available", True)

    demand_map = concurrent_demand.get("concurrent_demand", {})
    current_grade = d.get("grade", "")
    usage_counts = usage.get("usage_counts", {}) if isinstance(usage, dict) else {}

    updated_options = []
    contention_detected = False
    contention_reasons = []

    for opt in options:
        opt_dict = dict(opt if isinstance(opt, dict) else opt.model_dump())
        r_type = opt_dict.get("type", "").lower()
        reason = opt_dict.get("reason", "")
        feasibility = "high"

        # Guardrail 2: Internet & Guardrail 3: Tablets / Devices
        if "tablet" in r_type or any(k in r_type for k in ["online", "cloud", "internet", "web"]):
            if not internet_ok or tablets_free < 1:
                feasibility = "infeasible"
                reason = "Infeasible: Internet access or online connectivity is unavailable or insufficient free tablets."

        # Guardrail 4: Printer / Paper
        if "printable" in r_type and not printer_paper_ok:
            feasibility = "infeasible"
            reason = "Infeasible: Printer is unavailable or out of paper."

        # Guardrail 5: TV
        if ("tv" in r_type or "video" in r_type) and not tv_ok:
            feasibility = "infeasible"
            reason = "Infeasible: TV display is unavailable."

        # Guardrail 6: Whiteboard
        if "whiteboard" in r_type and not whiteboard_ok:
            feasibility = "infeasible"
            reason = "Infeasible: Whiteboard or classroom presentation materials unavailable."

        # Staleness evaluation: if resource used >= 3 times recently, penalize ranking
        usage_num = usage_counts.get(r_type, 0)
        if usage_num >= 3 and feasibility != "infeasible":
            feasibility = "low"
            reason += f" [Staleness penalty: used {usage_num} times recently]"

        # Guardrail 7: Contention check across other grades
        is_scarce = any(k in r_type for k in ["tablet", "tv", "printable"])
        is_contended = False

        for g, reqs in demand_map.items():
            g_clean = str(g).replace("Grade", "").strip()
            curr_clean = str(current_grade).replace("Grade", "").strip()
            if g_clean != curr_clean:
                for req in reqs:
                    req_lower = str(req).lower()
                    if req_lower in r_type or r_type in req_lower or ("tablet" in req_lower and "tablet" in r_type):
                        is_contended = True
                        if is_scarce:
                            contention_detected = True
                            contention_reasons.append(f"Resource '{r_type}' is simultaneously requested by {g}.")

        if is_contended and feasibility != "infeasible":
            feasibility = "low"
            reason += " [Contended with another grade]"

        opt_dict["feasibility"] = feasibility
        opt_dict["reason"] = reason
        updated_options.append(opt_dict)

    # Sort resource options dynamically by feasibility ranking: high > medium > low > infeasible
    feasibility_order = {"high": 3, "medium": 2, "low": 1, "infeasible": 0}
    updated_options.sort(key=lambda o: feasibility_order.get(o["feasibility"], 0), reverse=True)
    d["resource_options"] = updated_options

    if contention_detected:
        d["contention_flag"] = True
        if not d.get("contention_detail"):
            d["contention_detail"] = " ".join(sorted(list(set(contention_reasons))))
    else:
        d["contention_flag"] = False

    # Check delivery feasibility: deliverable_options MUST be strictly non-infeasible
    deliverable_options = [o for o in updated_options if o["feasibility"] != "infeasible"]

    if deliverable_options:
        d["delivery_possible"] = True
        # Guardrail 1 & 8: recommended_resource MUST strictly match the top deliverable non-infeasible option
        d["recommended_resource"] = deliverable_options[0]["type"]
        d["needs_generation"] = bool(d.get("needs_generation", False))
        d["explanation"] = f"Recommended '{d['recommended_resource']}' as the highest-feasibility deployable option under today's constraints."
    else:
        # Guardrail 1 & 9: No delivery possible -> recommended_resource MUST be None
        d["delivery_possible"] = False
        d["recommended_resource"] = None
        d["needs_generation"] = False
        d["explanation"] = "No resource delivery mechanism is feasible under current classroom constraints; activity delivery is impossible today."

    # Guardrail 10: Remove illegal content generation keys
    forbidden_keys = {"worksheet_content", "quiz_questions", "lesson_plan", "teaching_instructions", "activity_design"}
    for k in list(d.keys()):
        if k in forbidden_keys:
            del d[k]

    return d


class LocalResourceModel(Model):
    """
    Strands Model implementation for local/offline development execution.
    Dynamically executes Strands tools (get_resource_inventory, get_resource_usage_log, check_concurrent_demand)
    and applies deterministic hard guardrails outside LLM reasoning.
    """

    def __init__(self):
        pass

    def update_config(self, **model_config: Any) -> None:
        pass

    def get_config(self) -> Any:
        return {}

    async def structured_output(
        self, output_model: type[BaseModel], prompt: Any, system_prompt: str | None = None, **kwargs: Any
    ) -> AsyncGenerator[dict[str, Any], None]:
        pass

    async def stream(
        self,
        messages: Any,
        tool_specs: Any = None,
        system_prompt: str | None = None,
        **kwargs: Any
    ) -> AsyncGenerator[dict[str, Any], None]:
        last_user_prompt_idx = 0
        prompt_text = ""

        for idx, m in enumerate(messages):
            role = m.role if hasattr(m, "role") else (m.get("role") if isinstance(m, dict) else "")
            content = m.content if hasattr(m, "content") else (m.get("content", []) if isinstance(m, dict) else [])

            has_tool_result = False
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and "toolResult" in b:
                        has_tool_result = True

            if role == "user" and not has_tool_result:
                last_user_prompt_idx = idx
                if isinstance(content, list):
                    for b in content:
                        if isinstance(b, dict) and "text" in b:
                            prompt_text += b["text"]

        tool_results_count = 0
        inventory_data = {}
        usage_data = {}
        demand_data = {}

        for m in messages[last_user_prompt_idx:]:
            content = m.content if hasattr(m, "content") else (m.get("content", []) if isinstance(m, dict) else [])
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and "toolResult" in b:
                        tool_results_count += 1
                        tr = b["toolResult"]
                        tr_content = tr.get("content", []) if isinstance(tr, dict) else []
                        for item in tr_content:
                            if isinstance(item, dict):
                                data = {}
                                if "json" in item:
                                    data = item["json"]
                                elif "text" in item:
                                    try:
                                        data = json.loads(item["text"])
                                    except Exception:
                                        pass

                                if isinstance(data, dict):
                                    if "internet_available" in data or "tablets_free" in data:
                                        inventory_data = data
                                    elif "usage_log" in data or "recent_usage" in data or "usage_counts" in data:
                                        usage_data = data
                                    elif "concurrent_demand" in data or "other_active_grades" in data:
                                        demand_data = data

        yield {"messageStart": {"role": "assistant"}}

        if tool_results_count == 0:
            yield {
                "contentBlockStart": {
                    "start": {"toolUse": {"toolUseId": "call_inventory", "name": "get_resource_inventory"}},
                    "contentBlockIndex": 0,
                }
            }
            yield {
                "contentBlockDelta": {
                    "delta": {"toolUse": {"input": json.dumps({})}},
                    "contentBlockIndex": 0,
                }
            }
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "tool_use"}}

        elif tool_results_count == 1:
            grade, subject, topic = self._extract_grade_subject_topic(prompt_text)
            yield {
                "contentBlockStart": {
                    "start": {"toolUse": {"toolUseId": "call_usage", "name": "get_resource_usage_log"}},
                    "contentBlockIndex": 0,
                }
            }
            yield {
                "contentBlockDelta": {
                    "delta": {"toolUse": {"input": json.dumps({"grade": grade, "subject": subject, "topic": topic})}},
                    "contentBlockIndex": 0,
                }
            }
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "tool_use"}}

        elif tool_results_count == 2:
            yield {
                "contentBlockStart": {
                    "start": {"toolUse": {"toolUseId": "call_demand", "name": "check_concurrent_demand"}},
                    "contentBlockIndex": 0,
                }
            }
            yield {
                "contentBlockDelta": {
                    "delta": {"toolUse": {"input": json.dumps({})}},
                    "contentBlockIndex": 0,
                }
            }
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "tool_use"}}

        else:
            raw_rec = self._evaluate_resources_dynamically(prompt_text, inventory_data, usage_data, demand_data)
            guarded_rec = apply_resource_guardrails(raw_rec, inventory_data, usage_data, demand_data)

            yield {
                "contentBlockStart": {
                    "start": {"toolUse": {"toolUseId": "call_rec", "name": "ResourceRecommendation"}},
                    "contentBlockIndex": 0,
                }
            }
            yield {
                "contentBlockDelta": {
                    "delta": {"toolUse": {"input": json.dumps(guarded_rec)}},
                    "contentBlockIndex": 0,
                }
            }
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "tool_use"}}

    def _extract_grade_subject_topic(self, prompt_text: str) -> tuple[str, str, str]:
        grade = "3"
        if "- Grade:" in prompt_text:
            try:
                grade = prompt_text.split("- Grade:")[1].split("\n")[0].strip()
            except Exception:
                pass

        subject = "Math"
        if "- Subject:" in prompt_text:
            try:
                subject = prompt_text.split("- Subject:")[1].split("\n")[0].strip()
            except Exception:
                pass

        topic = "Equivalent fractions"
        if "- Topic:" in prompt_text:
            try:
                topic = prompt_text.split("- Topic:")[1].split("\n")[0].strip()
            except Exception:
                pass

        return grade, subject, topic

    def _evaluate_resources_dynamically(
        self, prompt_text: str, inventory: dict, usage: dict, demand: dict
    ) -> dict:
        grade, subject, topic = self._extract_grade_subject_topic(prompt_text)

        p_lower = prompt_text.lower()
        internet_ok = inventory.get("internet_available", False)
        if '"internet_available": true' in p_lower or 'internet_available: true' in p_lower:
            internet_ok = True
        elif '"internet_available": false' in p_lower or 'internet_available: false' in p_lower:
            internet_ok = False

        tablets_free = inventory.get("tablets_free", 0)
        if '"tablets_free": 1' in p_lower or 'tablets_free: 1' in p_lower or '"tablets_free": 5' in p_lower or 'tablets_free: 5' in p_lower:
            tablets_free = 1

        paper_ok = inventory.get("printer_has_paper", True) and inventory.get("printer_available", True)
        tv_ok = inventory.get("tv_available", False)
        wb_ok = inventory.get("whiteboard_available", True)

        options = []

        # Whiteboard Activity
        if wb_ok:
            options.append({
                "type": "whiteboard_activity",
                "feasibility": "high",
                "reason": "Whiteboard materials available with zero device or paper dependency."
            })

        # Printable Worksheet
        if paper_ok:
            options.append({
                "type": "printable_worksheet",
                "feasibility": "high",
                "reason": "Works reliably offline without internet or device requirements."
            })
        else:
            options.append({
                "type": "printable_worksheet",
                "feasibility": "infeasible",
                "reason": "Infeasible: Printer is unavailable or out of paper."
            })

        # TV Video
        if tv_ok:
            options.append({
                "type": "tv_video",
                "feasibility": "medium",
                "reason": "TV display available for group instruction."
            })
        else:
            options.append({
                "type": "tv_video",
                "feasibility": "infeasible",
                "reason": "Infeasible: TV display is unavailable."
            })

        # Tablet Quiz
        if internet_ok and tablets_free >= 1:
            options.append({
                "type": "tablet_quiz",
                "feasibility": "high",
                "reason": "Tablets available with active internet connection."
            })
        else:
            reason = "Infeasible: Tablet quiz requires online cloud access, but internet is unavailable." if not internet_ok else "Infeasible: Insufficient free tablets."
            options.append({
                "type": "tablet_quiz",
                "feasibility": "infeasible",
                "reason": reason
            })

        constraints = []
        if not internet_ok:
            constraints.append("no internet")
        constraints.append(f"{tablets_free} tablet free")
        if not paper_ok:
            constraints.append("no printer paper")

        rec_res = "tablet_quiz" if (internet_ok and tablets_free >= 1) else "whiteboard_activity"

        return {
            "grade": grade,
            "subject": subject,
            "topic": topic,
            "resource_options": options,
            "recommended_resource": rec_res,
            "contention_flag": False,
            "contention_detail": None,
            "delivery_possible": True,
            "needs_generation": False,
            "constraints_considered": constraints,
            "explanation": "Evaluated classroom inventory and resource feasibility."
        }


# GroqModel replaces LocalResourceModel for live Groq inference.
# _RESOURCE_MODEL is stateless — safe to share. Fresh Agent created per call.
from agents.groq_model import GroqModel
_RESOURCE_MODEL = GroqModel(reasoning_effort="low")



def recommend_resources(
    grade: Union[int, str],
    subject: str,
    topic: str,
    session: dict
) -> dict:
    """
    Executes the Resource Agent recommendation process for a Grade x Subject x Topic.
    Routes through Strands Agent → Groq → openai/gpt-oss-120b.
    Applies post-processing hard guardrails outside LLM reasoning.
    Does NOT mutate shared state or call other agents.
    """
    prompt = f"""
Evaluate resource feasibility for:
- Grade: {grade}
- Subject: {subject}
- Topic: {topic}
- Session Config: {json.dumps(session)}

First call get_resource_inventory(session), get_resource_usage_log(grade, subject, topic), and check_concurrent_demand(session) before producing your final structured ResourceRecommendation.
"""
    print(f"\n[STRANDS AGENT] Invoking ResourceAgent (Groq openai/gpt-oss-120b) for Grade {grade} {subject}...")
    # Fresh Agent per call — avoids ConcurrencyException for concurrent grade evaluation.
    agent = Agent(
        model=_RESOURCE_MODEL,
        system_prompt=SYSTEM_PROMPT,
        tools=[get_resource_inventory, get_resource_usage_log, check_concurrent_demand],
        structured_output_model=ResourceRecommendation,
        name="ResourceAgent",
        description="SAARTHI Resource Agent evaluating deployable resource options under physical, digital, and contention constraints."
    )

    result = agent(prompt)

    if hasattr(result, "structured_output") and result.structured_output:
        if hasattr(result.structured_output, "model_dump"):
            raw_data = result.structured_output.model_dump()
        else:
            raw_data = dict(result.structured_output)
    elif hasattr(result, "message") and result.message:
        text_resp = str(result.message.content if hasattr(result.message, "content") else result.message)
        raw_data = json.loads(text_resp)
    else:
        raise ValueError(f"ResourceAgent failed to return structured output: {result}")

    inventory = get_resource_inventory(session)
    usage = get_resource_usage_log(grade, subject, topic)
    demand = check_concurrent_demand(session)

    final_recommendation = apply_resource_guardrails(raw_data, inventory, usage, demand)
    return final_recommendation
