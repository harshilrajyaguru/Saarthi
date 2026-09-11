"""
agents/local_ollama.py
----------------------
Groq API adapter for Saarthi's specialist agents.

Calls openai/gpt-oss-120b via the Groq API, uses Pydantic
model_json_schema() for structured-output via response_format,
and applies the same hard guardrails as the Strands agent path.

Design constraints enforced here:
  * Uses the EXACT SYSTEM_PROMPT from each agent module -- unmodified.
  * Uses the EXACT Pydantic schemas from each agent module -- unmodified.
  * Calls tool functions directly (same as Strands agent).
  * Applies the same guardrails after validation.
  * NEVER falls back to deterministic diagnosis on failure --
    the exception propagates so the caller knows the API did not work.
"""

import json
from typing import Optional, Union

from agents.groq_model import get_groq_client

from agents.progress_agent import (
    SYSTEM_PROMPT,
    ProgressDiagnosis,
    apply_hard_guardrails,
)
from tools.progress_tools import get_history, get_trouble_spot_log

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LOCAL_MODEL = "openai/gpt-oss-120b"
PROVIDER    = "Groq"
TEMPERATURE = 0          # deterministic output for testing


def _call_groq_structured(system_prompt: str, user_prompt: str, schema: dict, *, model: str = LOCAL_MODEL) -> str:
    """
    Shared helper: calls Groq chat completions with JSON-object response_format
    and a schema instruction injected into the system prompt.
    Returns the raw JSON string from the model.
    """
    client = get_groq_client()

    sys_content = system_prompt.strip() + (
        "\n\nCRITICAL OUTPUT REQUIREMENT:\n"
        "You MUST return ONLY a valid, raw JSON object matching this JSON Schema:\n"
        + json.dumps(schema, indent=2)
        + "\nDo NOT use markdown fences. Do NOT add surrounding text."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": sys_content},
            {"role": "user",   "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=TEMPERATURE,
    )

    raw = (response.choices[0].message.content or "{}").strip()
    # Strip markdown fences if present
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return raw.strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_progress_local(
    grade: Union[int, str],
    subject: str,
    current_topic: str,
    latest_signals: dict,
    activity_metadata: Optional[dict] = None,
    *,
    model: str = LOCAL_MODEL,
) -> dict:
    """
    Groq API equivalent of analyze_progress().

    Input contract is identical to analyze_progress() in progress_agent.py.

    Steps
    -----
    1.  Call get_history() -- same as the Strands agent.
    2.  Call get_trouble_spot_log() -- same as the Strands agent.
    3.  Build a user message that bundles the tool results + latest signals
        so the LLM has all evidence in-context.
    4.  Call Groq with openai/gpt-oss-120b and ProgressDiagnosis JSON schema as the
        structured-output format (response_format=json_object).
    5.  Validate the response with ProgressDiagnosis.model_validate_json().
    6.  Apply apply_hard_guardrails() -- same post-processing as Strands path.

    Raises
    ------
    Any exception from the Groq client or Pydantic validation propagates
    directly to the caller.  There is NO silent deterministic fallback.
    """
    grade_str = str(grade)

    # Step 1: pull history (same tools the Strands agent would call)
    history_res = get_history(
        grade=grade,
        subject=subject,
        topic=current_topic,
        n=10,
    )
    history_count = history_res.get("count", 0) if isinstance(history_res, dict) else 0

    # Step 2: pull trouble-spot log
    trouble_res = get_trouble_spot_log(grade=grade, subject=subject)

    # Step 3: build the user prompt
    user_prompt = (
        f"Analyze the learning state for:\n"
        f"- Grade: {grade_str}\n"
        f"- Subject: {subject}\n"
        f"- Topic: {current_topic}\n\n"
        f"Historical sessions retrieved by get_history tool:\n"
        f"{json.dumps(history_res, indent=2)}\n\n"
        f"Known trouble spots retrieved by get_trouble_spot_log tool:\n"
        f"{json.dumps(trouble_res, indent=2)}\n\n"
        f"Latest Signals from current session:\n"
        f"{json.dumps(latest_signals, indent=2)}\n\n"
        f"Activity Metadata:\n"
        f"{json.dumps(activity_metadata or {}, indent=2)}\n\n"
        f"Using the historical data and trouble-spot log above, produce a\n"
        f"structured ProgressDiagnosis following the exact reasoning steps in\n"
        f"your system prompt. Reference concrete evidence (session IDs, scores,\n"
        f"trouble-spot patterns) in your explanation."
    )

    # Step 4: call Groq
    raw_json = _call_groq_structured(
        SYSTEM_PROMPT,
        user_prompt,
        ProgressDiagnosis.model_json_schema(),
        model=model,
    )

    # Step 5: validate against ProgressDiagnosis schema
    diagnosis_obj: ProgressDiagnosis = ProgressDiagnosis.model_validate_json(raw_json)
    raw_diagnosis: dict = diagnosis_obj.model_dump()

    # Step 6: apply hard guardrails (same as Strands path)
    final_diagnosis = apply_hard_guardrails(raw_diagnosis, history_count)
    return final_diagnosis


# ===========================================================================
# CURRICULUM AGENT — GROQ API ADAPTER
# ===========================================================================
# Mirrors the pattern of analyze_progress_local() above.
# Uses CurriculumDecision schema, SYSTEM_PROMPT, apply_curriculum_guardrails,
# get_syllabus_position, get_prerequisite_map -- all from curriculum_agent.py.
# No Ollama. No deterministic fallback. Errors propagate.
# ===========================================================================

from agents.curriculum_agent import (
    SYSTEM_PROMPT as CURRICULUM_SYSTEM_PROMPT,
    CurriculumDecision,
    apply_curriculum_guardrails,
)
from tools.curriculum_tools import get_syllabus_position, get_prerequisite_map


def reconcile_curriculum_local(
    grade: Union[int, str],
    subject: str,
    current_topic: str,
    progress_diagnosis: dict,
    session_constraints: dict,
    teacher_constraints: Optional[dict] = None,
    *,
    model: str = LOCAL_MODEL,
) -> dict:
    """
    Groq API equivalent of reconcile_curriculum() in curriculum_agent.py.

    Input contract is identical to reconcile_curriculum().

    Steps
    -----
    1.  Call get_syllabus_position() -- same tool the Strands agent uses.
    2.  Call get_prerequisite_map() for the next target syllabus topic.
    3.  Build a user message bundling all tool results + progress diagnosis +
        session/teacher constraints.
    4.  Call Groq with openai/gpt-oss-120b and CurriculumDecision JSON schema as the
        structured-output format (response_format=json_object).
    5.  Validate the response with CurriculumDecision.model_validate_json().
    6.  Apply apply_curriculum_guardrails() -- same post-processing as Strands path.

    Raises
    ------
    Any exception from the Groq client or Pydantic validation propagates
    directly to the caller.  There is NO silent deterministic fallback.
    """
    grade_str = str(grade)

    # Step 1: pull syllabus position (same tool the Strands agent calls)
    syllabus_res = get_syllabus_position(grade=grade_str, subject=subject)
    syllabus_topics = syllabus_res.get("syllabus_topics", [])

    # Determine next syllabus target: first topic after current_topic in sequence
    current_clean = current_topic.strip().lower()
    found_match = False
    next_target = current_topic
    for idx, t in enumerate(syllabus_topics):
        if current_clean in t.lower() or t.lower() in current_clean:
            found_match = True
            if idx + 1 < len(syllabus_topics):
                next_target = syllabus_topics[idx + 1]
            else:
                next_target = t
            break

    # Step 2: pull prerequisite map for the target topic
    prereq_res = get_prerequisite_map(topic=next_target)

    # Step 3: build the user prompt with strict topic and prerequisite grounding
    user_prompt = (
        f"Reconcile curriculum direction for:\n"
        f"- Grade: {grade_str}\n"
        f"- Subject: {subject}\n"
        f"- Requested Current Topic: {current_topic}\n"
        f"- Target Topic: {next_target}\n\n"
        f"Syllabus position retrieved by get_syllabus_position tool:\n"
        f"{json.dumps(syllabus_res, indent=2)}\n\n"
        f"Prerequisite map retrieved by get_prerequisite_map tool for '{next_target}':\n"
        f"{json.dumps(prereq_res, indent=2)}\n\n"
        f"Progress Agent Diagnosis:\n"
        f"{json.dumps(progress_diagnosis, indent=2)}\n\n"
        f"Session Constraints:\n"
        f"{json.dumps(session_constraints, indent=2)}\n\n"
        f"Teacher Constraints:\n"
        f"{json.dumps(teacher_constraints or {}, indent=2)}\n\n"
        f"STRICT GROUNDING DIRECTIVES:\n"
        f"1. You MUST base your decision and explanation on the requested topic '{current_topic}' and target '{next_target}'. Do NOT fabricate or switch to an unrelated topic.\n"
        f"2. You MUST ONLY treat a skill as a prerequisite if it is explicitly declared in the prerequisite map or in-prompt prerequisite context above. Do NOT invent prerequisite relationships.\n"
        f"3. Set `is_blocking_prerequisite` to `true` ONLY if the skill is a declared prerequisite AND student mastery is insufficient. Weaknesses that are not declared prerequisites MUST NOT be marked as blocking.\n"
        f"4. Do NOT overwrite or contradict the Progress Agent's diagnosis (e.g. if Progress Agent states 'proficient', accept that mastery level).\n"
        f"5. Explicitly evaluate what can realistically be achieved within today's available session time ({session_constraints.get('available_time', 'unspecified')}).\n"
        f"6. Do NOT select specific activities, worksheets, quizzes, or learning resources."
    )

    # Step 4: call Groq with CurriculumDecision schema for structured output
    raw_json = _call_groq_structured(
        CURRICULUM_SYSTEM_PROMPT,
        user_prompt,
        CurriculumDecision.model_json_schema(),
        model=model,
    )

    # Step 5: validate against CurriculumDecision schema
    decision_obj: CurriculumDecision = CurriculumDecision.model_validate_json(raw_json)
    raw_decision: dict = decision_obj.model_dump()

    # Step 6: apply hard guardrails (same as Strands path)
    final_decision = apply_curriculum_guardrails(
        raw_decision,
        grade=grade_str,
        subject=subject,
        current_topic=current_topic,
        progress_diagnosis=progress_diagnosis,
        session_constraints=session_constraints,
        teacher_constraints=teacher_constraints,
    )
    return final_decision


# ===========================================================================
# RESOURCE AGENT — GROQ API ADAPTER
# ===========================================================================
# Mirrors the pattern of analyze_progress_local() and reconcile_curriculum_local().
# Uses ResourceRecommendation schema, SYSTEM_PROMPT, apply_resource_guardrails,
# get_resource_inventory, get_resource_usage_log, check_concurrent_demand —
# all from resource_agent.py.  No Ollama. No deterministic fallback.
# Errors propagate directly.
# ===========================================================================

from agents.resource_agent import (
    SYSTEM_PROMPT as RESOURCE_SYSTEM_PROMPT,
    ResourceRecommendation,
    apply_resource_guardrails,
)
from tools.resource_tools import (
    get_resource_inventory,
    get_resource_usage_log,
    check_concurrent_demand,
)


def recommend_resources_local(
    grade: Union[int, str],
    subject: str,
    topic: str,
    session: dict,
    *,
    model: str = LOCAL_MODEL,
) -> dict:
    """
    Groq API equivalent of recommend_resources() in resource_agent.py.

    Input contract is identical to recommend_resources().

    Steps
    -----
    1.  Call get_resource_inventory(session) -- same tool the Strands agent uses.
    2.  Call get_resource_usage_log(grade, subject, topic) -- staleness data.
    3.  Call check_concurrent_demand(session) -- contention data across grades.
    4.  Build a user message bundling all tool results + session config.
    5.  Call Groq with openai/gpt-oss-120b and ResourceRecommendation JSON schema as the
        structured-output format (response_format=json_object).
    6.  Validate the response with ResourceRecommendation.model_validate_json().
    7.  Apply apply_resource_guardrails() -- same deterministic post-processing.

    Raises
    ------
    Any exception from the Groq client or Pydantic validation propagates
    directly to the caller.  There is NO silent deterministic fallback.
    """
    grade_str = str(grade)

    # Step 1: pull inventory
    inventory = get_resource_inventory(session)

    # Step 2: pull usage/staleness log
    usage = get_resource_usage_log(grade=grade, subject=subject, topic=topic)

    # Step 3: pull concurrent demand (contention across grades)
    demand = check_concurrent_demand(session)

    # Step 4: build the user prompt — include full tool output so the model
    # has all physical constraints in-context before reasoning.
    user_prompt = (
        f"Evaluate resource feasibility for:\n"
        f"- Grade: {grade_str}\n"
        f"- Subject: {subject}\n"
        f"- Topic: {topic}\n"
        f"- Session Config: {json.dumps(session, indent=2)}\n\n"
        f"Resource inventory retrieved by get_resource_inventory tool:\n"
        f"{json.dumps(inventory, indent=2)}\n\n"
        f"Recent resource usage log retrieved by get_resource_usage_log tool:\n"
        f"{json.dumps(usage, indent=2)}\n\n"
        f"Concurrent resource demand across grades retrieved by check_concurrent_demand tool:\n"
        f"{json.dumps(demand, indent=2)}\n\n"
        f"Using the inventory, usage log, and concurrent demand above, produce a\n"
        f"structured ResourceRecommendation following your system prompt reasoning.\n"
        f"IMPORTANT:\n"
        f"- Respect hard physical constraints (printer unavailable, TV count, tablet count).\n"
        f"- If a scarce resource (TV, tablet) is simultaneously requested by another grade,\n"
        f"  set contention_flag=true and describe the conflict in contention_detail.\n"
        f"- Do NOT decide who wins a contested resource.\n"
        f"- Do NOT select a specific learning activity, worksheet, or quiz.\n"
        f"- Do NOT diagnose student mastery or decide curriculum pacing."
    )

    # Step 5: call Groq with ResourceRecommendation schema for structured output
    raw_json = _call_groq_structured(
        RESOURCE_SYSTEM_PROMPT,
        user_prompt,
        ResourceRecommendation.model_json_schema(),
        model=model,
    )

    # Step 6: validate against ResourceRecommendation schema
    rec_obj: ResourceRecommendation = ResourceRecommendation.model_validate_json(raw_json)
    raw_rec: dict = rec_obj.model_dump()

    # Step 7: apply hard guardrails (same as existing path)
    final_rec = apply_resource_guardrails(raw_rec, inventory, usage, demand)
    return final_rec


# ===========================================================================
# ACTIVITY AGENT — GROQ API ADAPTER
# ===========================================================================
# Mirrors the pattern of the validated Progress/Curriculum/Resource adapters.
# Uses ActivityDesign schema, SYSTEM_PROMPT, apply_activity_guardrails,
# get_activity_templates, get_recent_activity_history — all from activity_agent.py.
# No Ollama. No deterministic fallback. Errors propagate directly.
# ===========================================================================

from agents.activity_agent import (
    SYSTEM_PROMPT as ACTIVITY_SYSTEM_PROMPT,
    ActivityDesign,
    apply_activity_guardrails,
)
from tools.activity_tools import get_activity_templates, get_recent_activity_history


def design_activity_local(
    grade: Union[int, str],
    subject: str,
    decided_topic: str,
    pacing_decision: str,
    trouble_spots: list,
    mastery_estimate: str,
    recommendation_direction: str,
    recommended_resource: str,
    needs_generation: bool,
    available_time_minutes: int,
    *,
    model: str = LOCAL_MODEL,
) -> dict:
    """
    Groq API equivalent of design_activity() in activity_agent.py.

    Input contract is identical to design_activity().

    Steps
    -----
    1.  Call get_activity_templates(decided_topic, recommended_resource) -- same tool.
    2.  Call get_recent_activity_history(grade, subject) -- avoids format repetition.
    3.  Build a user message bundling all upstream agent outputs + tool results
        so the model can synthesize the concrete activity in-context.
    4.  Call Groq with openai/gpt-oss-120b and ActivityDesign JSON schema as the
        structured-output format (response_format=json_object).
    5.  Validate the response with ActivityDesign.model_validate_json().
    6.  Apply apply_activity_guardrails() -- topic lock, resource lock, time fit.

    Raises
    ------
    Any exception from the Groq client or Pydantic validation propagates
    directly to the caller.  There is NO silent deterministic fallback.
    """
    grade_str = str(grade)

    # Step 1: pull activity templates (same tool the Strands agent calls first)
    templates = get_activity_templates(
        topic=decided_topic,
        resource_type=recommended_resource,
    )

    # Step 2: pull recent activity history (avoid repeating formats)
    history = get_recent_activity_history(grade=grade, subject=subject)

    # Step 3: build the user prompt — full upstream context in-prompt
    user_prompt = (
        f"Design student-facing activity for:\n"
        f"- Grade: {grade_str}\n"
        f"- Subject: {subject}\n"
        f"- Decided Topic: {decided_topic}\n"
        f"- Pacing Decision: {pacing_decision}\n"
        f"- Trouble Spots: {json.dumps(trouble_spots)}\n"
        f"- Mastery Estimate: {mastery_estimate}\n"
        f"- Recommendation Direction: {recommendation_direction}\n"
        f"- Recommended Resource: {recommended_resource}\n"
        f"- Needs Generation: {json.dumps(needs_generation)}\n"
        f"- Available Time (minutes): {available_time_minutes}\n\n"
        f"Activity templates retrieved by get_activity_templates tool:\n"
        f"{json.dumps(templates, indent=2)}\n\n"
        f"Recent activity history retrieved by get_recent_activity_history tool:\n"
        f"{json.dumps(history, indent=2)}\n\n"
        f"CRITICAL INSTRUCTIONS:\n"
        f"1. The activity_type field MUST be set to exactly: {recommended_resource}\n"
        f"2. The topic field MUST be set to exactly: {decided_topic}\n"
        f"3. Content must directly target the trouble spots: {json.dumps(trouble_spots)}\n"
        f"4. estimated_time_minutes MUST NOT exceed {available_time_minutes}.\n"
        f"5. content.instructions must be delivery-ready and specific.\n"
        f"6. content.items must contain actual exercises/questions — NOT vague suggestions.\n"
        f"7. difficulty_level must reflect mastery '{mastery_estimate}': "
        f"struggling/reteach=scaffolded, developing/reinforce=standard, proficient/advance=challenging.\n"
        f"8. Do NOT make curriculum pacing decisions or mastery diagnoses.\n"
        f"9. Do NOT choose a different resource than: {recommended_resource}\n"
        f"10. Generate the complete, delivery-ready student-facing activity content now."
    )

    # Step 4: call Groq with ActivityDesign schema for structured output
    raw_json = _call_groq_structured(
        ACTIVITY_SYSTEM_PROMPT,
        user_prompt,
        ActivityDesign.model_json_schema(),
        model=model,
    )

    # Step 5: validate against ActivityDesign schema
    design_obj: ActivityDesign = ActivityDesign.model_validate_json(raw_json)
    raw_design: dict = design_obj.model_dump()

    # Step 6: apply hard guardrails (topic lock, resource lock, time fit)
    final_design = apply_activity_guardrails(
        raw_design,
        expected_topic=decided_topic,
        expected_resource=recommended_resource,
        available_time_minutes=available_time_minutes,
    )
    return final_design
