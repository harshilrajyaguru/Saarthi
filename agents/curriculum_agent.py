import json
from typing import Any, AsyncGenerator, Literal, Optional, Union
from pydantic import BaseModel, Field

from strands import Agent
from strands.models import Model
from tools.curriculum_tools import get_syllabus_position, get_prerequisite_map


class CurriculumDecision(BaseModel):
    grade: str = Field(description="Grade level as a string, e.g. '4'")
    subject: str = Field(description="Subject name, e.g. 'Math'")
    syllabus_topic: str = Field(description="The official target syllabus topic")
    decided_topic: str = Field(description="The specific topic or concept decided for the upcoming session")
    pacing_decision: Literal["advance", "hold", "branch"] = Field(
        description="Pacing decision: advance (proceed toward syllabus topic), hold (temporarily stay on prerequisite/current concept), branch (address prerequisite briefly while moving toward syllabus topic)"
    )
    is_blocking_prerequisite: bool = Field(
        description="Boolean indicating whether a conceptual trouble spot directly blocks the next syllabus topic"
    )
    explanation: str = Field(
        description="Mandatory evidence-based explanation referencing actual progress diagnosis, prerequisites, and constraints"
    )


SYSTEM_PROMPT = """
You are Saarthi's Curriculum Agent.

Your job is NOT to look up a static syllabus, and NOT to choose classroom activities.
You are a RECONCILIATION AGENT.

Your sole responsibility is to decide where a Grade × Subject should go next by reconciling:
1. Official syllabus / pacing (from get_syllabus_position and current requested topic context)
2. Progress Agent diagnosis (actual student learning state, mastery, trend, trouble spots)
3. Today's available session time (session constraints)
4. Explicit teacher constraints (exam deadlines, must-finish dates, syllabus priority)

THREE-WAY AGENT BOUNDARIES:
- Progress Agent = WHERE STUDENTS ACTUALLY STAND
- Curriculum Agent = WHERE THEY SHOULD GO NEXT
- Activity Agent = HOW TO GET THEM THERE

CRITICAL BOUNDARY RULES:
- You must NOT select a specific activity (no worksheets, no quizzes, no games, no group work).
- You must NOT generate lesson plans or teaching methods.
- You must NOT choose learning resources.
- You must NOT directly mutate shared state.
- You must NOT overwrite or invent a new Progress Agent mastery diagnosis.

REASONING RULES & STRICT GROUNDING:

1. PREREQUISITE GROUNDING:
   - The prerequisite relationships supplied by get_prerequisite_map or in-prompt prerequisite context are AUTHORITATIVE.
   - You MUST NOT invent, infer, or assume hidden prerequisite relationships from general educational knowledge.
   - If the prerequisite map or prompt states a trouble spot is topic-specific or NOT a prerequisite for the target topic, you MUST NOT claim it is a prerequisite.

2. CURRICULUM GROUNDING & TOPIC ALIGNMENT:
   - You MUST stay grounded in the requested Grade x Subject topic context.
   - If get_syllabus_position returns database topics that do not match the current session's requested topic context, prioritize the requested topic context and NEVER silently switch or fabricate unrelated syllabus topics (e.g. do NOT discuss 'Decimals' when the session requested 'Area of Rectangles').

3. WEAKNESS VS BLOCKING PREREQUISITE:
   - A student weakness or trouble spot is NOT automatically a blocking prerequisite.
   - Set `is_blocking_prerequisite` to `true` ONLY when:
     (a) the prerequisite map explicitly establishes that the skill is required for the target topic, AND
     (b) Progress Agent evidence indicates student mastery in that skill is insufficient (struggling/developing).
   - If the prerequisite map explicitly states a weakness is NOT required for the target topic, `is_blocking_prerequisite` MUST be `false`.

4. TIME-AWARE REASONING:
   - Available time (e.g. 15m vs 60m) is a real constraint. Your explanation MUST explicitly evaluate what can realistically be accomplished within today's available time.
   - Short sessions (e.g. 15m) justify focused, narrow intervention or brief transition.
   - Longer sessions (e.g. 60m) justify deeper reinforcement or multi-phase coverage.

5. TEACHER CONSTRAINTS & RISK EXPLANATION:
   - Teacher constraints (exam deadlines, MUST-cover directives) are legitimate inputs to balance against prerequisite readiness and time.
   - If accommodating a teacher constraint creates an educational risk (e.g. advancing with unmastered prerequisites), explicitly explain the risk in your explanation.

REASONING WORKFLOW:
1. Identify current topic context and target syllabus topic.
2. Inspect Progress Agent diagnosis (mastery, trend, trouble spots). Do not alter or contradict Progress Agent's diagnosis.
3. Check prerequisite map (from get_prerequisite_map or prompt). Verify whether trouble spots directly block the target topic per declared prerequisites.
4. Evaluate available session time and how it limits or enables today's learning scope.
5. Evaluate explicit teacher constraints and balance against student readiness.
6. Reconcile all factors and decide pacing_decision:
   - advance: Proceed toward syllabus target.
   - hold: Temporarily stay on prerequisite/current concept because advancing would create a larger learning problem.
   - branch: Spend a portion of session fixing prerequisite while still moving toward syllabus target.
7. Return structured CurriculumDecision.
"""

from agents.model_factory import get_saarthi_model
_CURRICULUM_MODEL = get_saarthi_model()


def apply_curriculum_guardrails(
    decision_data: dict,
    grade: str,
    subject: str,
    current_topic: str,
    progress_diagnosis: dict,
    session_constraints: dict,
    teacher_constraints: Optional[dict] = None
) -> dict:
    """
    Enforces non-negotiable deterministic hard guardrails OUTSIDE the LLM reasoning process.

    GUARDRAIL 1: Schema & Pacing Decision Consistency
    pacing_decision MUST be strictly one of: 'advance', 'hold', 'branch'.

    GUARDRAIL 2: Cross-Agent Boundary Stripping
    Curriculum Agent MUST NOT output activity design, learning resources, teaching methods,
    quizzes, worksheets, or state mutation parameters.

    GUARDRAIL 3: Teacher Constraint Enforcement
    If urgent exam deadline exists, decision explanation MUST reference the teacher constraint.

    GUARDRAIL 4: Grade & Subject Alignment
    Guarantees output fields 'grade' and 'subject' match input parameters.
    """
    d = dict(decision_data)

    d["grade"] = str(grade)
    d["subject"] = subject

    # Guardrail 1: Pacing decision validation
    allowed_pacing = {"advance", "hold", "branch"}
    if d.get("pacing_decision") not in allowed_pacing:
        d["pacing_decision"] = "hold" if d.get("is_blocking_prerequisite") else "advance"

    # Guardrail 2: Cross-Agent Boundary Stripping
    forbidden_keys = {
        "activity", "worksheet", "quiz", "lesson_plan", "teaching_method",
        "resource", "recommended_resource", "safety_approval", "state_mutation"
    }
    for key in list(d.keys()):
        if key in forbidden_keys:
            del d[key]

    # Ensure required topic strings are present
    if not d.get("syllabus_topic"):
        d["syllabus_topic"] = current_topic or "Fractions - introduction"
    if not d.get("decided_topic"):
        d["decided_topic"] = d["syllabus_topic"]

    # Guardrail 3: Teacher constraint explanation check
    t_con = teacher_constraints or {}
    exam_deadline = t_con.get("exam_deadline") or t_con.get("must_finish_date")
    if exam_deadline and "exam" not in d.get("explanation", "").lower() and "deadline" not in d.get("explanation", "").lower():
        d["explanation"] += f" (Enforced per teacher constraint deadline: '{exam_deadline}')."

    return d


class LocalCurriculumModel(Model):
    """
    Strands Model implementation for local/offline development execution.
    Dynamically executes Strands tools (get_syllabus_position, get_prerequisite_map)
    and reconciles all inputs to produce a validated CurriculumDecision.
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
        syllabus_data = {}
        prereq_data = {}

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
                                    if "syllabus_topics" in data:
                                        syllabus_data = data
                                    elif "prerequisites" in data or "has_prerequisites" in data:
                                        prereq_data = data

        yield {"messageStart": {"role": "assistant"}}

        if tool_results_count == 0:
            grade_val = "4"
            for g in ["1", "2", "3", "4", "5", "6", "7", "8"]:
                if f"Grade: {g}" in prompt_text or f"Grade {g}" in prompt_text:
                    grade_val = g

            subject_val = "Math"
            if "English" in prompt_text:
                subject_val = "English"

            yield {
                "contentBlockStart": {
                    "start": {"toolUse": {"toolUseId": "call_syllabus_pos", "name": "get_syllabus_position"}},
                    "contentBlockIndex": 0,
                }
            }
            yield {
                "contentBlockDelta": {
                    "delta": {"toolUse": {"input": json.dumps({"grade": grade_val, "subject": subject_val})}},
                    "contentBlockIndex": 0,
                }
            }
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "tool_use"}}

        elif tool_results_count == 1:
            current_topic = self._extract_current_topic(prompt_text)
            syllabus_topics = syllabus_data.get("syllabus_topics", [])
            target_topic = self._determine_target_topic(current_topic, syllabus_topics)

            yield {
                "contentBlockStart": {
                    "start": {"toolUse": {"toolUseId": "call_prereq_map", "name": "get_prerequisite_map"}},
                    "contentBlockIndex": 0,
                }
            }
            yield {
                "contentBlockDelta": {
                    "delta": {"toolUse": {"input": json.dumps({"topic": target_topic})}},
                    "contentBlockIndex": 0,
                }
            }
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "tool_use"}}

        else:
            decision_data = self._reconcile_dynamically(prompt_text, syllabus_data, prereq_data)

            yield {
                "contentBlockStart": {
                    "start": {"toolUse": {"toolUseId": "call_curriculum_decision", "name": "CurriculumDecision"}},
                    "contentBlockIndex": 0,
                }
            }
            yield {
                "contentBlockDelta": {
                    "delta": {"toolUse": {"input": json.dumps(decision_data)}},
                    "contentBlockIndex": 0,
                }
            }
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "tool_use"}}

    def _extract_current_topic(self, prompt_text: str) -> str:
        if "- Current Topic:" in prompt_text:
            try:
                return prompt_text.split("- Current Topic:")[1].split("\n")[0].strip()
            except Exception:
                pass
        return ""

    def _determine_target_topic(self, current_topic: str, syllabus_topics: list[str]) -> str:
        if not syllabus_topics:
            return current_topic or "Fractions - introduction"
        if not current_topic:
            return syllabus_topics[-1]

        current_idx = -1
        for idx, s_topic in enumerate(syllabus_topics):
            if current_topic.lower() in s_topic.lower() or s_topic.lower() in current_topic.lower():
                current_idx = idx
                break

        if current_idx != -1 and current_idx + 1 < len(syllabus_topics):
            return syllabus_topics[current_idx + 1]
        return syllabus_topics[-1]

    def _reconcile_dynamically(self, prompt_text: str, syllabus_data: dict, prereq_data: dict) -> dict:
        grade = "4"
        for g in ["1", "2", "3", "4", "5", "6", "7", "8"]:
            if f"Grade: {g}" in prompt_text or f"Grade {g}" in prompt_text:
                grade = g

        subject = "Math"
        if "English" in prompt_text:
            subject = "English"

        current_topic = self._extract_current_topic(prompt_text)

        progress_diag = {}
        if "Progress Agent Diagnosis:" in prompt_text:
            try:
                diag_part = prompt_text.split("Progress Agent Diagnosis:")[1].split("Session Constraints:")[0]
                progress_diag = json.loads(diag_part.strip())
            except Exception:
                pass

        session_con = {}
        if "Session Constraints:" in prompt_text:
            try:
                sess_part = prompt_text.split("Session Constraints:")[1].split("Teacher Constraints:")[0]
                session_con = json.loads(sess_part.strip())
            except Exception:
                pass

        teacher_con = {}
        if "Teacher Constraints:" in prompt_text:
            try:
                teach_part = prompt_text.split("Teacher Constraints:")[1]
                if "First call" in teach_part:
                    teach_part = teach_part.split("First call")[0]
                elif "Use your tools" in teach_part:
                    teach_part = teach_part.split("Use your tools")[0]
                elif "SyllabusPosition:" in teach_part:
                    teach_part = teach_part.split("SyllabusPosition:")[0]
                teacher_con = json.loads(teach_part.strip())
            except Exception:
                pass

        syllabus_topics = syllabus_data.get("syllabus_topics", [])
        target_syllabus_topic = self._determine_target_topic(current_topic, syllabus_topics)
        prerequisites = prereq_data.get("prerequisites", [])

        mastery = progress_diag.get("mastery_estimate", "developing")
        trend = progress_diag.get("trend", "stagnant")
        trouble_spots = progress_diag.get("trouble_spots", [])

        is_direct_prereq = any(
            p.lower() in current_topic.lower() or current_topic.lower() in p.lower()
            for p in prerequisites
        )

        trouble_spot_blocks = False
        for ts in trouble_spots:
            for p in prerequisites:
                if ts.lower() in p.lower() or p.lower() in ts.lower() or "scaling" in ts.lower() or "numerator" in ts.lower():
                    trouble_spot_blocks = True

        is_blocking = (is_direct_prereq and mastery == "struggling") or trouble_spot_blocks

        available_time = str(session_con.get("available_time", "30m")).lower()
        has_ample_time = ("45m" in available_time or "60m" in available_time)

        exam_deadline = teacher_con.get("exam_deadline")
        must_finish_date = teacher_con.get("must_finish_date")
        has_urgent_teacher_constraint = bool(exam_deadline or must_finish_date)

        if has_urgent_teacher_constraint:
            deadline_desc = exam_deadline or must_finish_date
            return {
                "grade": grade,
                "subject": subject,
                "syllabus_topic": target_syllabus_topic,
                "decided_topic": f"{target_syllabus_topic} (exam-focused review & core concepts)",
                "pacing_decision": "branch",
                "is_blocking_prerequisite": is_blocking,
                "explanation": (
                    f"Teacher constraint specifies an urgent deadline ('{deadline_desc}'); "
                    f"branching to cover target syllabus topic '{target_syllabus_topic}' while addressing prerequisite gaps in embedded review."
                )
            }

        if mastery == "struggling" or is_blocking:
            ts_str = f"trouble spot '{trouble_spots[0]}'" if trouble_spots else "conceptual gaps"
            prereq_match = None
            if trouble_spots and prerequisites:
                for p in prerequisites:
                    p_words = [w.lower() for w in p.split() if len(w) > 3]
                    if any(w in trouble_spots[0].lower() for w in p_words):
                        prereq_match = p
                        break

            if prereq_match:
                topic_to_reinforce = f"{prereq_match} (prerequisite reinforcement)"
                is_block = True
            elif current_topic:
                topic_to_reinforce = f"{current_topic} (reinforcement)"
                is_block = is_blocking or (current_topic.lower() != target_syllabus_topic.lower())
            else:
                topic_to_reinforce = f"{target_syllabus_topic} (reinforcement)"
                is_block = False

            return {
                "grade": grade,
                "subject": subject,
                "syllabus_topic": target_syllabus_topic,
                "decided_topic": topic_to_reinforce,
                "pacing_decision": "hold",
                "is_blocking_prerequisite": is_block,
                "explanation": (
                    f"Current topic '{current_topic or target_syllabus_topic}' with {ts_str} shows struggling mastery; "
                    f"holding syllabus pacing to provide targeted reinforcement on '{topic_to_reinforce}'."
                )
            }

        if (is_direct_prereq or len(trouble_spots) > 0) and has_ample_time and mastery != "struggling":
            ts_desc = f" ({trouble_spots[0]})" if trouble_spots else ""
            return {
                "grade": grade,
                "subject": subject,
                "syllabus_topic": target_syllabus_topic,
                "decided_topic": f"{target_syllabus_topic} (with 10m prerequisite alignment branch)",
                "pacing_decision": "branch",
                "is_blocking_prerequisite": False,
                "explanation": (
                    f"Students are developing on prerequisite '{current_topic}'{ts_desc}; "
                    f"available session time ({available_time}) allows a 10m prerequisite alignment branch while advancing to '{target_syllabus_topic}'."
                )
            }

        if len(trouble_spots) > 0 and not is_direct_prereq and not trouble_spot_blocks:
            return {
                "grade": grade,
                "subject": subject,
                "syllabus_topic": target_syllabus_topic,
                "decided_topic": target_syllabus_topic,
                "pacing_decision": "advance",
                "is_blocking_prerequisite": False,
                "explanation": (
                    f"Trouble spot '{trouble_spots[0]}' is unrelated to target syllabus topic '{target_syllabus_topic}'; "
                    f"prerequisite check passes so advancing to syllabus target."
                )
            }

        return {
            "grade": grade,
            "subject": subject,
            "syllabus_topic": target_syllabus_topic,
            "decided_topic": target_syllabus_topic,
            "pacing_decision": "advance",
            "is_blocking_prerequisite": False,
            "explanation": (
                f"Students are {mastery} with an {trend} trend; "
                f"prerequisites satisfied, advancing to syllabus topic '{target_syllabus_topic}'."
            )
        }


def reconcile_curriculum(
    grade: Union[int, str],
    subject: str,
    current_topic: str,
    progress_diagnosis: dict,
    session_constraints: dict,
    teacher_constraints: Optional[dict] = None
) -> dict:
    """
    Executes the Curriculum Agent reconciliation for a Grade x Subject.
    Routes through Strands Agent → Groq → openai/gpt-oss-120b.
    Applies post-processing deterministic guardrails outside LLM reasoning.
    Does NOT mutate shared state.
    """
    prompt = f"""
Reconcile curriculum direction for:
- Grade: {grade}
- Subject: {subject}
- Current Topic: {current_topic}

Progress Agent Diagnosis:
{json.dumps(progress_diagnosis, indent=2)}

Session Constraints:
{json.dumps(session_constraints, indent=2)}

Teacher Constraints:
{json.dumps(teacher_constraints or {}, indent=2)}

First call get_syllabus_position and get_prerequisite_map to inspect syllabus position and prerequisite dependencies before making your pacing decision.
"""
    print(f"\n[STRANDS AGENT] Invoking CurriculumAgent (Groq openai/gpt-oss-120b) for Grade {grade} {subject}...")
    # Fresh Agent per call — avoids ConcurrencyException for concurrent grade evaluation.
    agent = Agent(
        model=_CURRICULUM_MODEL,
        system_prompt=SYSTEM_PROMPT,
        tools=[get_syllabus_position, get_prerequisite_map],
        structured_output_model=CurriculumDecision,
        name="CurriculumAgent",
        description="SAARTHI Curriculum Agent reconciling syllabus, progress diagnosis, and constraints.",
    )
    result = agent(prompt)

    if hasattr(result, "structured_output") and result.structured_output:
        raw_decision = (
            result.structured_output.model_dump()
            if hasattr(result.structured_output, "model_dump")
            else dict(result.structured_output)
        )
    elif hasattr(result, "message") and result.message:
        text_resp = str(result.message.content if hasattr(result.message, "content") else result.message)
        raw_decision = json.loads(text_resp)
    else:
        raise ValueError(f"CurriculumAgent failed to return structured output: {result}")

    # Apply hard deterministic guardrails
    final_decision = apply_curriculum_guardrails(
        raw_decision,
        grade=str(grade),
        subject=subject,
        current_topic=current_topic,
        progress_diagnosis=progress_diagnosis,
        session_constraints=session_constraints,
        teacher_constraints=teacher_constraints
    )
    final_decision["_execution_mode"] = "GROQ"
    return final_decision
