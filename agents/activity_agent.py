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
    answer_key: list[str] = Field(default_factory=list, description="Answer key or expected outcome for items where applicable")


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
4. Inspect available activity templates and recent activity history to avoid exact repetitions.
5. Calibrate difficulty level:
   - struggling / reteach -> scaffolded
   - developing / reinforce -> standard
   - proficient / advance -> challenging
6. Respect available_time_minutes: estimated_time_minutes MUST NOT exceed available_time_minutes.
7. Generate DELIVERY-READY student-facing content including clear instructions, concrete items/questions, and an answer key or expected outcomes.
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
        instructions = content.get("instructions", "").strip() if isinstance(content.get("instructions"), str) else ""
        items = content.get("items", [])
        answer_key = content.get("answer_key")
        if not instructions:
            instructions = f"Complete the practice exercises for {expected_topic}."
        if not items or not isinstance(items, list):
            items = [f"Practice item 1 for {expected_topic}"]
        
        c_dict = {"instructions": instructions, "items": items}
        if answer_key:
            c_dict["answer_key"] = answer_key
        d["content"] = c_dict
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


from agents.model_factory import get_saarthi_model
_ACTIVITY_MODEL = get_saarthi_model(tier="fast")


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
    available_time_minutes: int,
    progress_diagnosis: Optional[dict] = None,
    curriculum_decision: Optional[dict] = None,
    resource_recommendation: Optional[dict] = None,
    session_constraints: Optional[dict] = None,
    recent_history: Optional[list] = None
) -> dict:
    """
    Executes the Activity Agent design process using Strands + Ollama Qwen3:8b.
    Applies post-processing hard guardrails outside LLM reasoning.
    Does NOT mutate shared state or call other agents.
    """
    # Fetch template and history context via existing tools
    templates_res = get_activity_templates(decided_topic, recommended_resource)
    history_res = get_recent_activity_history(grade, subject)

    prompt = f"""
Design a complete, delivery-ready student-facing activity for Grade {grade} {subject}.

UPSTREAM AGENT REASONING & RUNTIME CONTEXT:
- Grade: {grade}
- Subject: {subject}
- Decided Topic (Curriculum Agent): {decided_topic}
- Pacing Decision (Curriculum Agent): {pacing_decision}
- Curriculum Decision Details: {json.dumps(curriculum_decision or {}, indent=2)}
- Progress Diagnosis (Progress Agent): {json.dumps(progress_diagnosis or {}, indent=2)}
- Diagnosed Trouble Spots: {json.dumps(trouble_spots)}
- Mastery Estimate: {mastery_estimate}
- Recommendation Direction: {recommendation_direction}
- Resource Recommendation Details: {json.dumps(resource_recommendation or {}, indent=2)}
- Recommended Resource: {recommended_resource}
- Needs Generation: {needs_generation}
- Available Time (minutes): {available_time_minutes}
- Session Constraints: {json.dumps(session_constraints or {}, indent=2)}

AVAILABLE ACTIVITY TEMPLATES:
{json.dumps(templates_res, indent=2)}

RECENT ACTIVITY HISTORY FOR THIS GRADE:
{json.dumps(history_res, indent=2)}

INSTRUCTIONS:
1. Target the decided topic '{decided_topic}' from Curriculum Agent strictly.
2. Direct the activity specifically to address trouble spot: {trouble_spots[0] if trouble_spots else 'general practice'}.
3. Use recommended resource format '{recommended_resource}'.
4. Calibrate difficulty ('scaffolded' for struggling/reteach, 'standard' for developing/reinforce, 'challenging' for proficient/advance).
5. Generate delivery-ready student-facing content:
   - Clear student-facing instructions explaining what to do.
   - Specific, concrete exercises/items (questions, tasks, or problems).
   - An answer key or expected outcomes for the items where applicable.
6. Ensure estimated_time_minutes <= {available_time_minutes}.
"""
    print(f"\n[STRANDS AGENT] Invoking ActivityAgent (Groq openai/gpt-oss-120b) for Grade {grade} {subject} topic '{decided_topic}'...")
    # Fresh Agent per call — avoids ConcurrencyException for concurrent grade evaluation.
    agent = Agent(
        model=_ACTIVITY_MODEL,
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
    elif hasattr(result, "message") and result.message:
        raw_data = json.loads(result.message.content)
    else:
        raw_data = json.loads(str(result))

    final_design = apply_activity_guardrails(
        raw_data,
        expected_topic=decided_topic,
        expected_resource=recommended_resource,
        available_time_minutes=available_time_minutes
    )
    return final_design

