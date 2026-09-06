import json
from typing import Any, AsyncGenerator, Literal, Optional, Union
from pydantic import BaseModel, Field

from strands import Agent
from strands.models import Model
from tools.activity_tools import (
    get_activity_templates,
    get_recent_activity_history
)


class ActivityContent(BaseModel):
    instructions: str = Field(description="Delivery-ready student-facing instructions")
    items: list[str] = Field(description="Delivery-ready student-facing questions, exercises, or tasks")


class ActivityDesign(BaseModel):
    grade: str = Field(description="Grade level as a string, e.g. '3'")
    subject: str = Field(description="Subject name, e.g. 'Math'")
    topic: str = Field(description="The exact decided topic from Curriculum Agent")
    activity_type: str = Field(description="The exact recommended_resource from Resource Agent")
    targets_trouble_spot: str = Field(description="The specific trouble spot addressed by this activity")
    difficulty_level: Literal["scaffolded", "standard", "challenging"] = Field(
        description="Calibrated difficulty level: scaffolded, standard, or challenging"
    )
    content: ActivityContent = Field(description="The actual delivery-ready student-facing content")
    estimated_time_minutes: int = Field(description="Estimated execution time in minutes")
    explanation: str = Field(description="Evidence-based explanation of activity design choices")


SYSTEM_PROMPT = """
You are Saarthi's Activity Agent.

Your job is to design the actual student-facing learning activity by synthesizing inputs.

AGENT BOUNDARIES:
- Progress Agent: WHAT IS TRUE? (mastery, trend, trouble spots)
- Curriculum Agent: WHAT SHOULD THEY WORK ON? (decided_topic, pacing_decision)
- Resource Agent: WHAT CAN ACTUALLY BE USED? (recommended_resource, delivery_possible)
- Activity Agent: WHAT EXACTLY SHOULD STUDENTS DO? (designs student-facing activity)
- Safety/Quality Gate: IS IT SAFE, CORRECT, COMPLETE AND READY TO DELIVER?

CRITICAL BOUNDARY RULES:
- You must NOT change the topic (Topic Lock).
- You must NOT override the Curriculum Agent.
- You must NOT choose a different resource (Resource Lock).
- You must NOT resolve resource contention.
- You must NOT perform safety approval.
- You must NOT generate lesson plans beyond the requested activity.
- You must NOT directly mutate shared classroom state.

REASONING WORKFLOW (IN ORDER):
1. Target decided_topic from Curriculum Agent. Content MUST strictly match decided_topic.
2. Inspect Progress Agent diagnosis. Content MUST strictly target the specific trouble spot failure mode.
3. Check Resource Agent's recommended_resource. The activity MUST be deliverable using that exact resource type.
4. Call get_activity_templates(topic, resource_type).
   - If needs_generation == false: evaluate suitable templates matching topic and difficulty, avoiding recently used formats.
   - If needs_generation == true: generate a new deliverable activity from scratch strictly matching decided_topic and trouble spot.
5. Call get_recent_activity_history(grade, subject). Avoid repeating the exact same activity format two sessions in a row when a suitable alternative exists.
6. Calibrate difficulty level:
   - struggling / reteach -> scaffolded
   - developing / reinforce -> standard
   - proficient / advance -> challenging
7. Respect available_time_minutes: estimated_time_minutes MUST NOT exceed available_time_minutes.
8. Generate DELIVERY-READY student-facing content (instructions and items).
"""


def apply_activity_guardrails(
    design_dict: dict,
    expected_topic: str,
    expected_resource: str,
    available_time_minutes: int
) -> dict:
    """
    Enforces non-negotiable deterministic hard guardrails OUTSIDE the LLM reasoning process.

    GUARDRAIL 1: RESOURCE LOCK - activity_type MUST equal recommended_resource.
    GUARDRAIL 2: TIME FIT - estimated_time_minutes MUST NOT exceed available_time_minutes.
    GUARDRAIL 3: CONTENT PRESENCE - content object MUST contain non-empty instructions and items.
    GUARDRAIL 4: TOPIC LOCK - topic MUST equal decided_topic.
    GUARDRAIL 5: NO CROSS-BOUNDARY OUTPUT - strip illegal cross-boundary keys.
    """
    d = dict(design_dict)

    # Guardrail 4: TOPIC LOCK
    d["topic"] = expected_topic

    # Guardrail 1: RESOURCE LOCK
    d["activity_type"] = expected_resource

    # Guardrail 3: CONTENT PRESENCE
    content = d.get("content", {})
    if isinstance(content, dict):
        instructions = content.get("instructions", "").strip()
        items = content.get("items", [])
        if not instructions:
            instructions = f"Complete the practice exercises for {expected_topic}."
        if not items or not isinstance(items, list):
            items = [f"Practice item 1 for {expected_topic}"]
        d["content"] = {"instructions": instructions, "items": items}
    else:
        d["content"] = {
            "instructions": f"Complete the practice exercises for {expected_topic}.",
            "items": [f"Practice item 1 for {expected_topic}"]
        }

    # Guardrail 2: TIME FIT
    est_time = d.get("estimated_time_minutes", 10)
    try:
        est_time = int(est_time)
    except Exception:
        est_time = available_time_minutes

    if est_time > available_time_minutes:
        est_time = available_time_minutes
        items_list = d["content"]["items"]
        if available_time_minutes <= 10 and len(items_list) > 3:
            d["content"]["items"] = items_list[:3]

    d["estimated_time_minutes"] = est_time

    # Guardrail 5: Strip illegal cross-boundary keys
    forbidden_keys = {
        "resource_override",
        "curriculum_change",
        "safety_approval",
        "contention_resolution",
        "lesson_plan_meta",
        "orchestrator_decision"
    }
    for k in list(d.keys()):
        if k in forbidden_keys:
            del d[k]

    return d


class LocalActivityModel(Model):
    """
    Strands Model implementation for local/offline development execution.
    Dynamically executes Strands tools (get_activity_templates, get_recent_activity_history)
    and synthesizes all inputs to produce a topic-matched, trouble-spot-matched ActivityDesign.
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
        templates_data = {}
        history_data = {}

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
                                    if "found_templates" in data or "query_topic" in data:
                                        templates_data = data
                                    elif "recent_formats" in data or "recent_sessions" in data:
                                        history_data = data

        yield {"messageStart": {"role": "assistant"}}

        if tool_results_count == 0:
            topic, res_type = self._extract_topic_and_resource(prompt_text)
            yield {
                "contentBlockStart": {
                    "start": {"toolUse": {"toolUseId": "call_templates", "name": "get_activity_templates"}},
                    "contentBlockIndex": 0,
                }
            }
            yield {
                "contentBlockDelta": {
                    "delta": {"toolUse": {"input": json.dumps({"topic": topic, "resource_type": res_type})}},
                    "contentBlockIndex": 0,
                }
            }
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "tool_use"}}

        elif tool_results_count == 1:
            grade, subject = self._extract_grade_and_subject(prompt_text)
            yield {
                "contentBlockStart": {
                    "start": {"toolUse": {"toolUseId": "call_history", "name": "get_recent_activity_history"}},
                    "contentBlockIndex": 0,
                }
            }
            yield {
                "contentBlockDelta": {
                    "delta": {"toolUse": {"input": json.dumps({"grade": grade, "subject": subject})}},
                    "contentBlockIndex": 0,
                }
            }
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "tool_use"}}

        else:
            raw_design = self._design_activity_dynamically(prompt_text, templates_data, history_data)
            topic, res_type = self._extract_topic_and_resource(prompt_text)
            avail_time = self._extract_available_time(prompt_text)

            guarded_design = apply_activity_guardrails(
                raw_design,
                expected_topic=topic,
                expected_resource=res_type,
                available_time_minutes=avail_time
            )

            yield {
                "contentBlockStart": {
                    "start": {"toolUse": {"toolUseId": "call_activity_design", "name": "ActivityDesign"}},
                    "contentBlockIndex": 0,
                }
            }
            yield {
                "contentBlockDelta": {
                    "delta": {"toolUse": {"input": json.dumps(guarded_design)}},
                    "contentBlockIndex": 0,
                }
            }
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "tool_use"}}

    def _extract_grade_and_subject(self, prompt_text: str) -> tuple[str, str]:
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

        return grade, subject

    def _extract_topic_and_resource(self, prompt_text: str) -> tuple[str, str]:
        topic = "Equivalent fractions (prerequisite reinforcement)"
        if "- Decided Topic:" in prompt_text:
            try:
                topic = prompt_text.split("- Decided Topic:")[1].split("\n")[0].strip()
            except Exception:
                pass

        resource = "printable_worksheet"
        if "- Recommended Resource:" in prompt_text:
            try:
                resource = prompt_text.split("- Recommended Resource:")[1].split("\n")[0].strip()
            except Exception:
                pass

        return topic, resource

    def _extract_available_time(self, prompt_text: str) -> int:
        if "- Available Time (minutes):" in prompt_text:
            try:
                val = prompt_text.split("- Available Time (minutes):")[1].split("\n")[0].strip()
                return int(val)
            except Exception:
                pass
        return 15

    def _design_activity_dynamically(
        self, prompt_text: str, templates_data: dict, history_data: dict
    ) -> dict:
        grade, subject = self._extract_grade_and_subject(prompt_text)
        topic, resource_type = self._extract_topic_and_resource(prompt_text)
        avail_time = self._extract_available_time(prompt_text)

        trouble_spot = "confusing numerator/denominator when scaling"
        if "- Trouble Spots:" in prompt_text:
            try:
                ts_part = prompt_text.split("- Trouble Spots:")[1].split("- Mastery Estimate:")[0].strip()
                ts_list = json.loads(ts_part) if ts_part.startswith("[") else [ts_part]
                if ts_list:
                    trouble_spot = str(ts_list[0])
            except Exception:
                pass

        mastery = "developing"
        if "- Mastery Estimate:" in prompt_text:
            try:
                mastery = prompt_text.split("- Mastery Estimate:")[1].split("\n")[0].strip().lower()
            except Exception:
                pass

        rec_direction = "reinforce"
        if "- Recommendation Direction:" in prompt_text:
            try:
                rec_direction = prompt_text.split("- Recommendation Direction:")[1].split("\n")[0].strip().lower()
            except Exception:
                pass

        needs_gen = False
        if "- Needs Generation:" in prompt_text:
            try:
                val_str = prompt_text.split("- Needs Generation:")[1].split("\n")[0].strip().lower()
                needs_gen = val_str == "true"
            except Exception:
                pass

        # 1. Calibrate difficulty level based on mastery & direction
        if mastery in ["struggling", "reteach"] or rec_direction == "reteach":
            difficulty = "scaffolded"
        elif mastery in ["proficient", "advance"] or rec_direction == "advance":
            difficulty = "challenging"
        else:
            difficulty = "standard"

        found_templates = templates_data.get("found_templates", [])
        recent_formats = history_data.get("recent_formats", [])

        instructions = ""
        items = []

        if not needs_gen and found_templates:
            matching_tpl = None
            available_tpls = [t for t in found_templates if t.get("format") not in recent_formats]

            for tpl in available_tpls:
                if tpl.get("difficulty") == difficulty:
                    matching_tpl = tpl
                    break

            if not matching_tpl:
                for tpl in found_templates:
                    if tpl.get("difficulty") == difficulty:
                        matching_tpl = tpl
                        break

            if not matching_tpl and available_tpls:
                matching_tpl = available_tpls[0]

            if not matching_tpl and found_templates:
                matching_tpl = found_templates[0]

            if matching_tpl:
                instructions = matching_tpl.get("base_instructions", "Practice exercises.")
                items = list(matching_tpl.get("base_items", []))

        # 2. Dynamic Topic & Trouble-Spot Content Synthesis (Check decimal topic BEFORE general multiply!)
        t_lower = topic.lower()
        ts_lower = trouble_spot.lower()

        if "decimal" in t_lower or "decimals" in t_lower:
            if "simplifying" in ts_lower or "simplify" in ts_lower or "reduce" in ts_lower:
                instructions = (
                    f"Practice multiplying decimals and simplifying your answers for {topic}. "
                    f"Focus on reducing decimal products to simplest form."
                )
                items = [
                    "Multiply 0.4 × 0.5 and simplify the resulting product (0.2).",
                    "A student multiplied 0.6 × 0.5 and got 0.30. Show how to simplify 0.30 to 0.3.",
                    "Calculate 1.2 × 0.25 and express the final answer in simplest decimal form."
                ]
            else:
                instructions = f"Step-by-step decimal multiplication practice for {topic}."
                items = [
                    "Multiply 0.3 × 0.4 and count total decimal places.",
                    "Multiply 0.5 × 0.8 and write the product."
                ]
        elif "multiply" in t_lower or "multiplication" in t_lower:
            if "simplifying" in ts_lower or "simplify" in ts_lower or "reduce" in ts_lower:
                instructions = (
                    f"Practice multiplying fractions and simplifying your answers for {topic}. "
                    f"Focus on reducing the final product to simplest form."
                )
                items = [
                    "Multiply 2/3 × 3/4 and reduce the resulting fraction to simplest form.",
                    "A student multiplied 3/5 × 5/6 and got 15/30. Show how to simplify 15/30.",
                    "Calculate 4/9 × 3/8 and express the final answer in simplest form."
                ]
            else:
                instructions = f"Step-by-step fraction multiplication practice for {topic}."
                items = [
                    "Multiply 1/2 × 3/4: multiply numerators together and denominators together.",
                    "Multiply 2/5 × 1/3 and write the product."
                ]
        elif "equivalent" in t_lower or "fraction" in t_lower:
            if "numerator" in ts_lower or "denominator" in ts_lower or "scaling" in ts_lower:
                if difficulty == "scaffolded":
                    instructions = (
                        f"Guided Practice for {topic}: First label the numerator and denominator, "
                        f"then complete the single-step scaling pair."
                    )
                    items = [
                        "In 3/4, circle the numerator and underline the denominator.",
                        "Complete 1/2 = ?/4. Label which number is the numerator and which is the denominator."
                    ]
                elif difficulty == "challenging":
                    instructions = (
                        f"Advanced Challenge for {topic}: Solve multi-step scaling chains and explain numerator/denominator relationships."
                    )
                    items = [
                        "Find three equivalent fractions for 3/5 with denominators greater than 20.",
                        "A recipe calls for 6/8 cup of flour. Write this in simplest form and as an equivalent fraction with denominator 16."
                    ]
                else:
                    instructions = (
                        f"Error Analysis & Diagnostic Practice for {topic}: Analyze fraction scaling statements and identify misconceptions."
                    )
                    items = [
                        "A student says 2/3 becomes 4/3 when scaling to an equivalent fraction. Is the student correct? Explain.",
                        "Complete 2/3 = ?/6 and explain what happened to BOTH the numerator and denominator."
                    ]

        est_time = min(avail_time, 12 if avail_time >= 15 else avail_time)

        return {
            "grade": grade,
            "subject": subject,
            "topic": topic,
            "activity_type": resource_type,
            "targets_trouble_spot": trouble_spot,
            "difficulty_level": difficulty,
            "content": {
                "instructions": instructions,
                "items": items
            },
            "estimated_time_minutes": est_time,
            "explanation": (
                f"Synthesized a {difficulty} {resource_type} specifically targeting trouble spot '{trouble_spot}' "
                f"for topic '{topic}' while avoiding recent formats {recent_formats} and respecting the {avail_time}-minute time limit."
            )
        }


activity_agent = Agent(
    model=LocalActivityModel(),
    system_prompt=SYSTEM_PROMPT,
    tools=[get_activity_templates, get_recent_activity_history],
    structured_output_model=ActivityDesign,
    name="ActivityAgent",
    description="SAARTHI Activity Agent designing student-facing activities targeting specific trouble spots."
)


def design_activity(
    grade: Union[int, str],
    subject: str,
    decided_topic: str,
    pacing_decision: str,
    trouble_spots: list[str],
    mastery_estimate: str,
    recommendation_direction: str,
    recommended_resource: str,
    needs_generation: bool,
    available_time_minutes: int
) -> dict:
    """
    Executes the Activity Agent design process for a Grade x Subject x Topic.
    Applies post-processing hard guardrails outside LLM reasoning.
    Does NOT mutate shared state or call other agents.
    """
    prompt = f"""
Design student-facing activity for:
- Grade: {grade}
- Subject: {subject}
- Decided Topic: {decided_topic}
- Pacing Decision: {pacing_decision}
- Trouble Spots: {json.dumps(trouble_spots)}
- Mastery Estimate: {mastery_estimate}
- Recommendation Direction: {recommendation_direction}
- Recommended Resource: {recommended_resource}
- Needs Generation: {json.dumps(needs_generation)}
- Available Time (minutes): {available_time_minutes}

First call get_activity_templates(topic, resource_type) and get_recent_activity_history(grade, subject) before producing your final structured ActivityDesign.
"""
    agent = Agent(
        model=LocalActivityModel(),
        system_prompt=SYSTEM_PROMPT,
        tools=[get_activity_templates, get_recent_activity_history],
        structured_output_model=ActivityDesign,
        name="ActivityAgent",
        description="SAARTHI Activity Agent designing student-facing activities targeting specific trouble spots."
    )

    result = agent(prompt)

    if hasattr(result, "structured_output") and result.structured_output:
        if hasattr(result.structured_output, "model_dump"):
            raw_data = result.structured_output.model_dump()
        else:
            raw_data = dict(result.structured_output)
    else:
        text_resp = str(result.message if hasattr(result, "message") else result)
        raw_data = json.loads(text_resp)

    final_design = apply_activity_guardrails(
        raw_data,
        expected_topic=decided_topic,
        expected_resource=recommended_resource,
        available_time_minutes=available_time_minutes
    )
    return final_design
