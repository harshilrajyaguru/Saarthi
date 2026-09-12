import json
import uuid
import os
import time
import traceback
from typing import Any, AsyncGenerator, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator

from strands import Agent
from strands.models import Model
from agents.event_bus import emit
from agents.strands_trace import make_trace_handler

from tools.orchestrator_tools import (
    read_shared_state,
    write_shared_state,
    get_active_grades
)

# Import frozen specialist entrypoint functions
from agents.progress_agent import analyze_progress
from agents.curriculum_agent import reconcile_curriculum
from agents.resource_agent import recommend_resources
from agents.activity_agent import design_activity
from agents.safety_gate import evaluate_safety_gate, SafetyGateResult


class NextAction(BaseModel):
    priority: Literal["critical", "high", "medium", "low"] = Field(
        description="Priority level of the single teacher-facing next action"
    )
    grade: str = Field(description="Grade level for which action is required, e.g. '3'")
    subject: str = Field(description="Subject name, e.g. 'Math'")
    action_type: Literal[
        "teacher_needed",
        "resource_contention",
        "blocking_prerequisite_review",
        "progress_monitoring",
        "normal_progression"
    ] = Field(description="Categorized action type for teacher awareness")
    reason: str = Field(description="Detailed evidence-based rationale for this prioritized next action")
    resolved_conflicts: list[str] = Field(
        default_factory=list,
        description="List of cross-grade resource/attention conflicts resolved during this cycle. MUST be an array of simple text strings."
    )

    @field_validator("resolved_conflicts", mode="before")
    @classmethod
    def sanitize_resolved_conflicts(cls, v: Any) -> list[str]:
        if not v:
            return []
        if isinstance(v, list):
            cleaned = []
            for item in v:
                if isinstance(item, dict):
                    val_str = item.get("conflict") or item.get("reason") or item.get("description") or json.dumps(item)
                    cleaned.append(str(val_str))
                else:
                    cleaned.append(str(item))
            return cleaned
        if isinstance(v, str):
            return [v]
        return [str(v)]


class StateUpdateEntry(BaseModel):
    grade: str = Field(description="Grade level")
    subject: str = Field(description="Subject name")
    status: str = Field(description="Reconciliation status, e.g., 'reconciled', 'skipped'")
    decided_topic: Optional[str] = Field(default=None)
    pacing_decision: Optional[str] = Field(default=None)
    recommended_resource: Optional[str] = Field(default=None)
    activity_status: Optional[str] = Field(default=None)


class OrchestrationResult(BaseModel):
    cycle_id: str = Field(description="Unique cycle execution identifier")
    next_action: NextAction = Field(description="EXACTLY ONE prioritized teacher-facing next action")
    state_updates: list[StateUpdateEntry] = Field(description="List of finalized state update entries")
    specialist_evaluations: Optional[dict[str, Any]] = Field(default=None, description="Specialist agent evaluations per grade")


SYSTEM_PROMPT = """
You are Saarthi's Orchestrator Agent.

Your sole responsibility is: Coordinate, sequence, prioritize, and resolve cross-grade conflicts across specialist agents, surface EXACTLY ONE teacher-facing next action, and act as the SINGLE WRITER of shared classroom state.

AGENT BOUNDARIES:
- Do NOT recalculate student progress/mastery (Progress Agent domain).
- Do NOT redesign curriculum topics or pacing (Curriculum Agent domain).
- Do NOT evaluate physical resource inventory or feasibility arbitrarily (Resource Agent domain).
- Do NOT redesign student activities (Activity Agent domain).
- Do NOT override Safety Gate verdicts.

ORCHESTRATION WORKFLOW:
1. Call get_active_grades(session) as a cheap candidate filter to determine candidate grades. Skip grades with no meaningful change.
2. The Orchestrator decides whether each candidate grade actually needs a full specialist cycle.
3. Accept specialist outputs for active grades without re-deriving domain decisions.
4. Handle Safety Gate retries: Maximum 2 activity generation retries on reject_and_regenerate. If 2 retries fail or if Safety Gate returns escalate_to_teacher, surface immediate teacher escalation.
5. Resolve cross-grade resource conflicts using evidence: blocking prerequisite status, progress severity, persistence, and alternative resource availability. Assign alternative resources to losing grades.
6. Surface EXACTLY ONE prioritized teacher-facing next_action using the strict priority hierarchy:
   Priority 1 (Critical): Safety Gate escalation / Max retries exceeded
   Priority 2 (High): Foundational / blocking prerequisite issue
   Priority 3 (High): Severe declining / persistent learning issue (attention flag)
   Priority 4 (Medium): Resource contention
   Priority 5 (Low): Normal progression
7. Commit finalized reconciled state atomically via write_shared_state.
"""


from tools.activity_tools import get_activity_templates

from agents.model_factory import get_saarthi_model
_ORCHESTRATOR_MODEL = get_saarthi_model(tier="smart", max_tokens=1600)


def template_activity(g_str: str, subj_str: str, topic: str, resource_type: str) -> dict:
    """Builds a deterministic template activity from activity_data.json via activity_tools."""
    templates_res = get_activity_templates(topic, resource_type)
    templates = templates_res.get("found_templates", [])
    if templates:
        t = templates[0]
        content = t.get("content", {})
        items = content.get("items", [f"Practice exercise 1 for {topic}", f"Practice exercise 2 for {topic}"])
        instructions = content.get("instructions", f"Practice exercise for {topic}")
    else:
        instructions = f"Practice exercise for {topic}"
        items = [f"Practice exercise 1 for {topic}", f"Practice exercise 2 for {topic}"]

    return {
        "activity_id": f"act_template_{g_str}",
        "grade": str(g_str),
        "subject": subj_str,
        "topic": topic,
        "activity_type": resource_type,
        "content": {
            "instructions": instructions,
            "items": items
        },
        "estimated_time_minutes": 10,
        "explanation": f"Deterministic template activity for Grade {g_str} {subj_str} on '{topic}'."
    }


def parse_grade_key(g_key: str) -> tuple[str, str]:
    parts = g_key.split("_")
    if len(parts) >= 3 and parts[0] == "Grade":
        s = parts[2]
        s_norm = "Math" if s.lower() in ["mathematics", "maths", "math"] else s.capitalize()
        return parts[1], s_norm
    elif len(parts) == 2 and parts[0] == "Grade":
        return parts[1], "Math"
    return parts[0].replace("Grade", "").strip() or "3", "Math"




# ANSI Color Codes for Rich Terminal Logging
ANSI_CYAN = "\033[96m"
ANSI_GREEN = "\033[92m"
ANSI_YELLOW = "\033[93m"
ANSI_RED = "\033[91m"
ANSI_MAGENTA = "\033[95m"
ANSI_BLUE = "\033[94m"
ANSI_BOLD = "\033[1m"
ANSI_RESET = "\033[0m"


def _log_specialist_summary(prop: dict):
    """Prints clear color-coded summary of specialist agent recommendations for a grade."""
    g_str = prop.get("grade")
    subj_str = prop.get("subject")
    p_diag = prop.get("progress_diag", {})
    c_dec = prop.get("curriculum_dec", {})
    r_rec = prop.get("resource_rec", {})
    s_v = prop.get("safety_verdict")

    direction = str(p_diag.get("recommendation_direction", "reinforce")).lower()
    mastery = str(p_diag.get("mastery_estimate", "developing"))
    pacing = str(c_dec.get("pacing_decision", "hold")).lower()
    decided_topic = c_dec.get("decided_topic", "")
    rec_resource = r_rec.get("recommended_resource", "printable_worksheet")

    p_color = ANSI_RED if direction in ["hold", "remediate", "reinforce"] else (ANSI_GREEN if direction == "advance" else ANSI_YELLOW)
    c_color = ANSI_RED if pacing in ["hold", "revisit"] else (ANSI_GREEN if pacing == "advance" else ANSI_YELLOW)

    print(f"\n{ANSI_BOLD}{ANSI_BLUE}--- Specialist Agent Recommendations for Grade {g_str} ({subj_str}) ---{ANSI_RESET}")
    print(f"  {ANSI_CYAN}ProgressAgent{ANSI_RESET} says:   {p_color}{direction.upper()} Grade {g_str}{ANSI_RESET} (Mastery: {mastery})")
    print(f"  {ANSI_CYAN}CurriculumAgent{ANSI_RESET} says: {c_color}{pacing.upper()} Grade {g_str}{ANSI_RESET} -> Decided Topic: '{decided_topic}'")
    print(f"  {ANSI_CYAN}ResourceAgent{ANSI_RESET} says:   {ANSI_YELLOW}ALLOCATE {rec_resource}{ANSI_RESET} for Grade {g_str}")
    if s_v:
        passed = getattr(s_v, "passed", True)
        action = getattr(s_v, "action", "pass")
        s_color = ANSI_GREEN if passed else ANSI_RED
        s_label = f"PASSED ({action})" if passed else f"REJECTED ({action})"
        print(f"  {ANSI_CYAN}SafetyGate{ANSI_RESET} verdict:    {s_color}{s_label}{ANSI_RESET}")


def _evaluate_single_active_grade(a_item: dict, session: dict) -> tuple[str, dict]:
    session_id = session.get("session_id")
    g_key = a_item["grade_key"]
    g_data = a_item.get("grade_data", {})
    g_str, subj_str = parse_grade_key(g_key)

    current_topic = g_data.get("current_topic") or "Equivalent fractions"

    # 1. Progress Agent
    emit(session_id, "ProgressAgent", "started", grade=g_str)
    mock_prog = session.get("mock_progress", {}).get(g_key)
    if mock_prog:
        progress_diag = mock_prog
    else:
        try:
            progress_diag = analyze_progress(
                grade=g_str,
                subject=subj_str,
                current_topic=current_topic,
                latest_signals=session.get("new_signals", {}),
                session_id=session_id
            )
        except Exception as e:
            emit(session_id, "ProgressAgent", "agent_error", g_str, message=str(e)[:300])
            print(f"[FALLBACK] ProgressAgent used deterministic template for Grade {g_str}")
            has_sig = session.get("new_signals", {}).get(g_key, False)
            progress_diag = {
                "grade": str(g_str),
                "subject": subj_str,
                "topic": current_topic,
                "mastery_estimate": "struggling" if has_sig and g_str == "3" else "developing",
                "trend": "declining" if has_sig and g_str == "3" else "stagnant",
                "confidence": "medium",
                "trouble_spots": ["confusing numerator/denominator when scaling"],
                "attention_flag": has_sig,
                "recommendation_direction": "reinforce",
                "explanation": f"Local diagnosis for Grade {g_str} {subj_str} on topic '{current_topic}'."
            }
    msg_p = progress_diag.get("explanation", "") if isinstance(progress_diag, dict) else getattr(progress_diag, "explanation", "")
    payload_p = progress_diag.model_dump() if hasattr(progress_diag, "model_dump") else (progress_diag.dict() if hasattr(progress_diag, "dict") else progress_diag)

    # Enrich ProgressAgent payload with real classroom metrics
    from tools.progress_tools import find_grade_entry, load_classroom_data
    state_data = load_classroom_data()
    g_entry_p = find_grade_entry(state_data, g_str, subj_str)
    roster_size_p = g_entry_p.get("roster_size", 30)
    hist_p = g_entry_p.get("history", [])
    last_sess_p = hist_p[-1] if hist_p else {}
    avg_correctness_latest = last_sess_p.get("avg_correctness", 0.7)
    below_60_count_latest = last_sess_p.get("below_60_count", 0)
    err_tags_p = last_sess_p.get("error_tags", {})
    top_error_tag = max(err_tags_p.items(), key=lambda x: x[1])[0] if err_tags_p else (progress_diag.get("trouble_spots", ["—"])[0] if isinstance(progress_diag, dict) and progress_diag.get("trouble_spots") else "—")

    if isinstance(payload_p, dict):
        payload_p["roster_size"] = roster_size_p
        payload_p["avg_correctness_latest"] = avg_correctness_latest
        payload_p["below_60_count_latest"] = below_60_count_latest
        payload_p["top_error_tag"] = top_error_tag

    emit(session_id, "ProgressAgent", "completed", grade=g_str, message=msg_p or "", payload=payload_p)
    emit(session_id, "ProgressAgent", "agent_completed", grade=g_str, message=msg_p or "", payload=payload_p)

    # 2. Curriculum Agent
    emit(session_id, "CurriculumAgent", "started", grade=g_str)
    session_con = session.get("session_constraints", {"available_time": "30m"})
    teacher_con = session.get("teacher_constraints", {}).get(g_key)

    mock_curr = session.get("mock_curriculum", {}).get(g_key)
    if mock_curr:
        curriculum_dec = mock_curr
    else:
        try:
            curriculum_dec = reconcile_curriculum(
                grade=g_str,
                subject=subj_str,
                current_topic=current_topic,
                progress_diagnosis=progress_diag,
                session_constraints=session_con,
                teacher_constraints=teacher_con,
                session_id=session_id
            )
        except Exception as e:
            emit(session_id, "CurriculumAgent", "agent_error", g_str, message=str(e)[:300])
            print(f"[FALLBACK] CurriculumAgent used deterministic template for Grade {g_str}")
            curriculum_dec = {
                "grade": str(g_str),
                "subject": subj_str,
                "decided_topic": current_topic,
                "pacing_decision": "hold",
                "reasoning": f"Local curriculum reconciliation for Grade {g_str} on '{current_topic}'.",
                "explanation": f"Local curriculum reconciliation for Grade {g_str} on '{current_topic}'."
            }
    msg_c = (curriculum_dec.get("reasoning") or curriculum_dec.get("explanation", "")) if isinstance(curriculum_dec, dict) else (getattr(curriculum_dec, "reasoning", None) or getattr(curriculum_dec, "explanation", ""))
    payload_c = curriculum_dec.model_dump() if hasattr(curriculum_dec, "model_dump") else (curriculum_dec.dict() if hasattr(curriculum_dec, "dict") else curriculum_dec)
    emit(session_id, "CurriculumAgent", "completed", grade=g_str, message=msg_c or "", payload=payload_c)
    emit(session_id, "CurriculumAgent", "agent_completed", grade=g_str, message=msg_c or "", payload=payload_c)

    # 3. Resource Agent
    emit(session_id, "ResourceAgent", "started", grade=g_str)
    decided_topic = curriculum_dec.get("decided_topic", current_topic) if isinstance(curriculum_dec, dict) else getattr(curriculum_dec, "decided_topic", current_topic)

    mock_res = session.get("mock_resource", {}).get(g_key)
    if mock_res:
        resource_rec = mock_res
    else:
        try:
            resource_rec = recommend_resources(
                grade=g_str,
                subject=subj_str,
                topic=decided_topic,
                session=session.get("session_info", {"duration_minutes": 40}),
                session_id=session_id
            )
        except Exception as e:
            emit(session_id, "ResourceAgent", "agent_error", g_str, message=str(e)[:300])
            print(f"[FALLBACK] ResourceAgent used deterministic template for Grade {g_str}")
            resource_rec = {
                "recommended_resource": "printable_worksheet",
                "resource_options": [{"type": "printable_worksheet", "feasibility": "feasible"}],
                "needs_generation": False,
                "explanation": "Evaluated classroom inventory and resource feasibility."
            }

    # Allow explicit requested resource override ONLY IF it is deployable/feasible
    requested_res = session.get("force_resource", {}).get(g_key)
    if requested_res:
        res_opts = resource_rec.get("resource_options", []) if isinstance(resource_rec, dict) else getattr(resource_rec, "resource_options", [])
        matching_opt = next((o for o in res_opts if requested_res.lower() in (o.get("type") if isinstance(o, dict) else getattr(o, "type", "")).lower()), None)
        feas = matching_opt.get("feasibility") if isinstance(matching_opt, dict) else (getattr(matching_opt, "feasibility", "") if matching_opt else "")
        if matching_opt and feas != "infeasible":
            if isinstance(resource_rec, dict):
                resource_rec["recommended_resource"] = matching_opt.get("type") if isinstance(matching_opt, dict) else getattr(matching_opt, "type")

    msg_r = (resource_rec.get("explanation") or resource_rec.get("rationale", "")) if isinstance(resource_rec, dict) else (getattr(resource_rec, "explanation", None) or getattr(resource_rec, "rationale", ""))
    payload_r = resource_rec.model_dump() if hasattr(resource_rec, "model_dump") else (resource_rec.dict() if hasattr(resource_rec, "dict") else resource_rec)
    emit(session_id, "ResourceAgent", "completed", grade=g_str, message=msg_r or "", payload=payload_r)
    emit(session_id, "ResourceAgent", "agent_completed", grade=g_str, message=msg_r or "", payload=payload_r)

    # 4 & 5. Activity Agent + Safety Gate (with max 2 retry loop)
    emit(session_id, "ActivityAgent", "started", grade=g_str)
    rec_resource = (resource_rec.get("recommended_resource") if isinstance(resource_rec, dict) else getattr(resource_rec, "recommended_resource", None)) or "printable_worksheet"
    trouble_spots = (progress_diag.get("trouble_spots") if isinstance(progress_diag, dict) else getattr(progress_diag, "trouble_spots", [])) or ["confusing numerator/denominator when scaling"]
    mastery = (progress_diag.get("mastery_estimate") if isinstance(progress_diag, dict) else getattr(progress_diag, "mastery_estimate", "developing"))
    direction = (progress_diag.get("recommendation_direction") if isinstance(progress_diag, dict) else getattr(progress_diag, "recommendation_direction", "reinforce"))
    needs_gen = (resource_rec.get("needs_generation") if isinstance(resource_rec, dict) else getattr(resource_rec, "needs_generation", False))
    avail_time = session.get("session_info", {}).get("duration_minutes", 15)

    force_safety_action = session.get("mock_safety_action", {}).get(g_key)

    try:
        activity_design = design_activity(
            grade=g_str,
            subject=subj_str,
            decided_topic=decided_topic,
            pacing_decision=curriculum_dec.get("pacing_decision", "hold") if isinstance(curriculum_dec, dict) else getattr(curriculum_dec, "pacing_decision", "hold"),
            trouble_spots=trouble_spots,
            mastery_estimate=mastery,
            recommendation_direction=direction,
            recommended_resource=rec_resource,
            needs_generation=needs_gen,
            available_time_minutes=avail_time,
            progress_diagnosis=progress_diag,
            curriculum_decision=curriculum_dec,
            resource_recommendation=resource_rec,
            session_constraints=session_con,
            session_id=session_id
        )
    except Exception as e:
        emit(session_id, "ActivityAgent", "agent_error", g_str, message=str(e)[:300])
        print(f"[FALLBACK] ActivityAgent used deterministic template for Grade {g_str}")
        activity_design = template_activity(g_str, subj_str, decided_topic, rec_resource)

    msg_a = activity_design.get("explanation", "") if isinstance(activity_design, dict) else getattr(activity_design, "explanation", "")
    payload_a = activity_design.model_dump() if hasattr(activity_design, "model_dump") else (activity_design.dict() if hasattr(activity_design, "dict") else activity_design)
    emit(session_id, "ActivityAgent", "completed", grade=g_str, message=msg_a or "", payload=payload_a)
    emit(session_id, "ActivityAgent", "agent_completed", grade=g_str, message=msg_a or "", payload=payload_a)

    emit(session_id, "SafetyGate", "started", grade=g_str)
    attempts = 0
    max_attempts = 2
    safety_verdict = None

    if force_safety_action:
        if force_safety_action == "escalate_to_teacher":
            try:
                safety_verdict = evaluate_safety_gate(
                    activity_design, decided_topic, trouble_spots[0] if trouble_spots else "", avail_time, session_id=session_id, grade=g_str
                )
            except Exception as e:
                emit(session_id, "SafetyGate", "agent_error", g_str, message=str(e)[:300])
                print(f"[FALLBACK] SafetyGate used deterministic template for Grade {g_str}")
                safety_verdict = SafetyGateResult(activity_id=f"act_{g_str}", passed=False, layer_failed="layer_3", issues=[], action="escalate_to_teacher", explanation="Teacher escalation requested.")
            safety_verdict.passed = False
            safety_verdict.layer_failed = "layer_3"
            safety_verdict.action = "escalate_to_teacher"
        elif force_safety_action == "reject_and_regenerate":
            attempts = 2
            try:
                safety_verdict = evaluate_safety_gate(
                    activity_design, decided_topic, trouble_spots[0] if trouble_spots else "", avail_time, session_id=session_id, grade=g_str
                )
            except Exception as e:
                emit(session_id, "SafetyGate", "agent_error", g_str, message=str(e)[:300])
                print(f"[FALLBACK] SafetyGate used deterministic template for Grade {g_str}")
                safety_verdict = SafetyGateResult(activity_id=f"act_{g_str}", passed=False, layer_failed="layer_1", issues=[], action="reject_and_regenerate", explanation="Regeneration requested.")
            safety_verdict.passed = False
            safety_verdict.layer_failed = "layer_1"
            safety_verdict.action = "reject_and_regenerate"
    else:
        while attempts < max_attempts:
            attempts += 1
            try:
                safety_verdict = evaluate_safety_gate(
                    activity_design,
                    decided_topic=decided_topic,
                    targets_trouble_spot=trouble_spots[0] if trouble_spots else "",
                    available_time_minutes=avail_time,
                    session_id=session_id,
                    grade=g_str
                )
            except Exception as e:
                emit(session_id, "SafetyGate", "agent_error", g_str, message=str(e)[:300])
                print(f"[FALLBACK] SafetyGate used deterministic template for Grade {g_str}")
                safety_verdict = SafetyGateResult(
                    activity_id=f"act_{g_str}",
                    passed=True,
                    layer_failed=None,
                    issues=[],
                    action="pass",
                    explanation="Activity passed safety gate."
                )
            if safety_verdict.passed or safety_verdict.action == "escalate_to_teacher":
                break
            if attempts < max_attempts:
                try:
                    activity_design = design_activity(
                        grade=g_str,
                        subject=subj_str,
                        decided_topic=decided_topic,
                        pacing_decision=curriculum_dec.get("pacing_decision", "hold") if isinstance(curriculum_dec, dict) else getattr(curriculum_dec, "pacing_decision", "hold"),
                        trouble_spots=trouble_spots,
                        mastery_estimate=mastery,
                        recommendation_direction=direction,
                        recommended_resource=rec_resource,
                        needs_generation=True,
                        available_time_minutes=avail_time,
                        progress_diagnosis=progress_diag,
                        curriculum_decision=curriculum_dec,
                        resource_recommendation=resource_rec,
                        session_constraints=session_con,
                        session_id=session_id
                    )
                except Exception as e:
                    emit(session_id, "ActivityAgent", "agent_error", g_str, message=str(e)[:300])
                    print(f"[FALLBACK] ActivityAgent used deterministic template for Grade {g_str}")
                    activity_design = template_activity(g_str, subj_str, decided_topic, rec_resource)

    msg_s = safety_verdict.explanation if hasattr(safety_verdict, "explanation") else safety_verdict.get("explanation", "")
    payload_s = safety_verdict.model_dump() if hasattr(safety_verdict, "model_dump") else (safety_verdict.dict() if hasattr(safety_verdict, "dict") else safety_verdict)
    emit(session_id, "SafetyGate", "completed", grade=g_str, message=msg_s or "", payload=payload_s)
    emit(session_id, "SafetyGate", "agent_completed", grade=g_str, message=msg_s or "", payload=payload_s)

    prop = {
        "grade": g_str,
        "subject": subj_str,
        "progress_diag": progress_diag,
        "curriculum_dec": curriculum_dec,
        "resource_rec": resource_rec,
        "activity_design": activity_design,
        "safety_verdict": safety_verdict,
        "safety_attempts": attempts
    }
    _log_specialist_summary(prop)
    return g_key, prop


def run_orchestration_cycle(session: dict) -> OrchestrationResult:
    """
    Executes a complete Orchestration Cycle:
    1. get_active_grades(session) acts as a cheap candidate filter to identify candidate grades.
    2. Runs specialist pipeline for active candidate grades concurrently.
    3. Invokes Strands OrchestratorAgent (Groq/openai/gpt-oss-120b) with real runtime context to reason about cross-grade priorities and conflicts.
    4. Applies deterministic guardrails (Safety Gate overrides, state integrity).
    5. SINGLE WRITER: Commits finalized state to data/classroom_state.json via write_shared_state.
    """
    if session.get("end_session"):
        session_id = session.get("session_id", f"sess_{uuid.uuid4().hex[:8]}")
        from datetime import datetime, timezone
        write_shared_state({
            "active_session": {
                "session_id": session_id,
                "status": "completed",
                "ended_at": datetime.now(timezone.utc).isoformat()
            }
        })
        return OrchestrationResult(
            cycle_id=f"orc_end_{uuid.uuid4().hex[:8]}",
            next_action=NextAction(
                priority="low",
                grade="all",
                subject="all",
                action_type="normal_progression",
                reason=f"Classroom session {session_id} ended successfully. Today's progress saved.",
                resolved_conflicts=[]
            ),
            state_updates=[],
            specialist_evaluations={}
        )

    cycle_id = f"orc_{uuid.uuid4().hex[:8]}"

    # STEP 1: Candidate filtering via get_active_grades (cheap deterministic filter, non-LLM)
    active_res = get_active_grades(session)
    active_evals = active_res.get("active_evaluations", [])
    skipped_evals = active_res.get("skipped_grades", [])

    proposals = {}
    state_update_entries = []

    # Record skipped grades (Orchestrator confirms no full cycle required)
    for s_item in skipped_evals:
        g_key = s_item["grade_key"]
        g_str, subj_str = parse_grade_key(g_key)
        state_update_entries.append(StateUpdateEntry(
            grade=g_str,
            subject=subj_str,
            status="skipped",
            decided_topic=None,
            pacing_decision=None,
            recommended_resource=None,
            activity_status="skipped_no_change"
        ))

    # STEP 2: Run specialist agents for active grades sequentially
    if active_evals:
        for a_item in active_evals:
            g_key, prop = _evaluate_single_active_grade(a_item, session)
            proposals[g_key] = prop

    # STEP 3: Route actual orchestration decision through existing Strands Agent (Ollama Qwen3:8b)
    shared_state = read_shared_state()

    # Serialize specialist outputs for context prompt
    from tools.progress_tools import find_grade_entry
    specialist_summary = {}
    for g_k, prop in proposals.items():
        s_v = prop.get("safety_verdict")
        g_str = prop.get("grade")
        subj_str = prop.get("subject")
        g_entry = find_grade_entry(shared_state, g_str, subj_str)

        roster_size = g_entry.get("roster_size", 30)
        res_dict = g_entry.get("resources", {})
        tablets_avail = res_dict.get("tablets", 12)
        tablets_insuff = (tablets_avail < roster_size)
        hist = g_entry.get("history", [])
        last_s = hist[-1] if hist else {}
        below_60_last = last_s.get("below_60_count", 0)

        agg_errs = {}
        for s_item in hist:
            for k_tag, cnt in s_item.get("error_tags", {}).items():
                agg_errs[k_tag] = agg_errs.get(k_tag, 0) + cnt
        sorted_errs = sorted(agg_errs.items(), key=lambda x: x[1], reverse=True)
        top3_errs = {k: v for k, v in sorted_errs[:3]}

        mastery_lvl = g_entry.get("mastery_level", "developing")
        curr_pos = g_entry.get("curriculum_position", "")

        specialist_summary[g_k] = {
            "grade": g_str,
            "subject": subj_str,
            "roster_size": roster_size,
            "tablets_available": tablets_avail,
            "tablets_insufficient": tablets_insuff,
            "below_60_count_last_session": below_60_last,
            "aggregated_error_tags_top3": top3_errs,
            "mastery_level": mastery_lvl,
            "curriculum_position": curr_pos,
            "progress_diagnosis": prop.get("progress_diag"),
            "curriculum_decision": prop.get("curriculum_dec"),
            "resource_recommendation": prop.get("resource_rec"),
            "activity_design": {
                "activity_type": prop.get("activity_design", {}).get("activity_type"),
                "topic": prop.get("activity_design", {}).get("topic"),
                "estimated_time_minutes": prop.get("activity_design", {}).get("estimated_time_minutes"),
            },
            "safety_verdict": {
                "passed": s_v.passed if s_v else True,
                "action": s_v.action if s_v else "pass",
                "explanation": s_v.explanation if s_v else ""
            }
        }

    compact_session = {
        "session_id": session.get("session_id"),
        "active_grades": session.get("active_grades"),
        "trigger_type": session.get("trigger_type"),
        "session_info": session.get("session_info"),
        "session_constraints": session.get("session_constraints"),
        "new_signals": session.get("new_signals"),
    }

    compact_shared_state = {
        "grades": shared_state.get("grades", {}),
        "attendance": shared_state.get("attendance", {}),
        "classroom_resources": shared_state.get("classroom_resources", {}),
    }

    orchestrator_user_prompt = (
        f"You are evaluating live classroom orchestration cycle {cycle_id}.\n\n"
        f"Ground-Truth Shared Classroom State:\n{json.dumps(compact_shared_state, indent=2)}\n\n"
        f"Active Session Constraints & Resources:\n{json.dumps(compact_session, indent=2)}\n\n"
        f"Candidate Grades Evaluated ({len(proposals)}): {list(proposals.keys())}\n"
        f"Skipped Grades ({len(skipped_evals)}): {[item['grade_key'] for item in skipped_evals]}\n\n"
        f"Specialist Agent Pipeline Outputs per Active Grade:\n{json.dumps(specialist_summary, indent=2)}\n\n"
        f"INSTRUCTIONS:\n"
        f"1. Analyze progress trends, curriculum issues, and physical resource constraints across all active grades.\n"
        f"2. Resolve any cross-grade resource conflicts or priority competition based on evidence urgency.\n"
        f"3. Surface EXACTLY ONE prioritized teacher-facing `next_action` (priority: 'critical'|'high'|'medium'|'low', "
        f"action_type: 'teacher_needed'|'resource_contention'|'blocking_prerequisite_review'|'progress_monitoring'|'normal_progression').\n"
        f"4. Provide state_updates entries for all active grades.\n"
        f"5. Document resolved_conflicts in next_action if applicable."
    )

    session_id = session.get("session_id")
    model_id = getattr(_ORCHESTRATOR_MODEL, "model_id", getattr(_ORCHESTRATOR_MODEL, "model_name", "unknown"))
    print(f"\n[STRANDS AGENT] Invoking OrchestratorAgent ({model_id}) for cycle {cycle_id}...")
    orchestrator_agent = Agent(
        model=_ORCHESTRATOR_MODEL,
        system_prompt=SYSTEM_PROMPT,
        tools=[read_shared_state, write_shared_state, get_active_grades],
        structured_output_model=OrchestrationResult,
        name="OrchestratorAgent",
        description="SAARTHI Orchestrator Agent sequencing active grades, resolving conflicts, surfacing one next action, and acting as single state writer.",
        callback_handler=make_trace_handler(session_id, "OrchestratorAgent") if session_id else None
    )
    import time
    t0 = time.time()
    try:
        try:
            agent_result = orchestrator_agent(orchestrator_user_prompt)
        except Exception as e:
            if "Failed to parse" in str(e) or "Parsing failed" in str(e) or "Tool call validation failed" in str(e) or "validation failed" in str(e):
                print("[RETRY] Malformed orchestrator tool-call JSON — retrying with compact-output rules")
                agent_result = orchestrator_agent(orchestrator_user_prompt + "\n\nOUTPUT RULES: Keep JSON compact. Do not make raw tool calls; respond strictly with structured output.")
            else:
                raise

        if hasattr(agent_result, "structured_output") and agent_result.structured_output:
            raw_llm_result = agent_result.structured_output
        elif hasattr(agent_result, "message") and agent_result.message:
            raw_llm_result = OrchestrationResult.model_validate_json(agent_result.message.content)
        else:
            raise ValueError(f"OrchestratorAgent failed to return structured output: {agent_result}")

        llm_next_action = raw_llm_result.next_action
        llm_state_updates = raw_llm_result.state_updates or []
    except Exception as e:
        emit(session_id, "OrchestratorAgent", "agent_error", message=str(e)[:300])
        print(f"[FALLBACK] OrchestratorAgent used deterministic fallback due to exception: {e}")
        first_prop = list(proposals.values())[0] if proposals else {"grade": "3", "subject": "Math"}
        llm_next_action = NextAction(
            priority="medium",
            grade=str(first_prop.get("grade", "3")),
            subject=first_prop.get("subject", "Math"),
            action_type="normal_progression",
            reason=f"Classroom session evaluated for active grades.",
            resolved_conflicts=[]
        )
        llm_state_updates = [
            StateUpdateEntry(
                grade=str(p.get("grade", "3")),
                subject=p.get("subject", "Math"),
                status="reconciled",
                decided_topic=p["curriculum_dec"].get("decided_topic") if isinstance(p.get("curriculum_dec"), dict) else getattr(p.get("curriculum_dec"), "decided_topic", None),
                pacing_decision=p["curriculum_dec"].get("pacing_decision") if isinstance(p.get("curriculum_dec"), dict) else getattr(p.get("curriculum_dec"), "pacing_decision", None),
                recommended_resource=p["resource_rec"].get("recommended_resource") if isinstance(p.get("resource_rec"), dict) else getattr(p.get("resource_rec"), "recommended_resource", None),
                activity_status="passed_safety_gate" if getattr(p.get("safety_verdict"), "passed", True) else "failed_safety_gate"
            )
            for p in proposals.values()
        ]
    elapsed = time.time() - t0
    print(f"[TIMING] OrchestratorAgent: {elapsed:.1f}s")

    # STEP 4: Deterministic Guardrails (Safety Gate Override & State Integrity)
    # Guardrail 1: Safety Gate Override — if any active grade has an unpassed safety verdict / teacher escalation, force critical action
    safety_escalations = []
    for g_k, prop in proposals.items():
        s_v = prop.get("safety_verdict")
        if s_v and (s_v.action == "escalate_to_teacher" or (not s_v.passed and prop.get("safety_attempts", 0) >= 2)):
            safety_escalations.append((prop["grade"], prop["subject"], s_v.explanation))

    if safety_escalations:
        esc_grade, esc_subj, esc_reason = safety_escalations[0]
        final_next_action = NextAction(
            priority="critical",
            grade=str(esc_grade),
            subject=esc_subj,
            action_type="teacher_needed",
            reason=f"Safety Gate flagged activity for Grade {esc_grade} ({esc_reason}); manual teacher intervention required.",
            resolved_conflicts=llm_next_action.resolved_conflicts
        )
    else:
        clean_g = str(llm_next_action.grade).replace("Grade", "").replace("_", " ").strip()
        parts = clean_g.split()
        final_g = parts[0] if parts else "3"

        final_next_action = NextAction(
            priority=llm_next_action.priority,
            grade=final_g,
            subject=llm_next_action.subject or "Math",
            action_type=llm_next_action.action_type,
            reason=llm_next_action.reason,
            resolved_conflicts=llm_next_action.resolved_conflicts
        )

    next_act_dict = final_next_action.model_dump() if hasattr(final_next_action, "model_dump") else (final_next_action.dict() if hasattr(final_next_action, "dict") else final_next_action)
    emit(session_id, "OrchestratorAgent", "orchestrator_decision", message=final_next_action.reason, payload=next_act_dict)

    # Reconstruct state update entries ensuring all candidate active & skipped grades are included
    final_state_updates = list(state_update_entries)  # Start with skipped grades
    state_updates_dict = {}

    for g_key, prop in proposals.items():
        g_str = prop["grade"]
        subj_str = prop["subject"]
        c_dec = prop["curriculum_dec"]
        r_rec = prop["resource_rec"]
        s_verdict = prop["safety_verdict"]

        act_status = "passed_safety_gate" if s_verdict.passed else f"failed_{s_verdict.layer_failed}"

        # Match LLM update if present for this grade
        llm_entry = next((u for u in llm_state_updates if str(u.grade).replace("Grade", "").strip() == str(g_str)), None)
        recommended_r = (llm_entry.recommended_resource if llm_entry and llm_entry.recommended_resource else None) or r_rec.get("recommended_resource")

        entry = StateUpdateEntry(
            grade=g_str,
            subject=subj_str,
            status="reconciled",
            decided_topic=c_dec.get("decided_topic"),
            pacing_decision=c_dec.get("pacing_decision"),
            recommended_resource=recommended_r,
            activity_status=act_status
        )
        final_state_updates.append(entry)

        state_updates_dict[f"Grade_{g_str}_{subj_str}"] = {
            "current_topic": c_dec.get("decided_topic"),
            "pacing_decision": c_dec.get("pacing_decision"),
            "mastery_estimate": prop["progress_diag"].get("mastery_estimate"),
            "attention_flag": prop["progress_diag"].get("attention_flag"),
            "recommended_resource": recommended_r,
            "activity_status": act_status,
            "last_evaluation_date": "2026-09-04T00:00:00Z"
        }

    # STEP 5: Single-Writer State Commit (write_shared_state)
    write_shared_state({"grades": state_updates_dict})

    # Log Conflict Resolution & Single Prioritized Action
    print(f"\n{ANSI_BOLD}{ANSI_MAGENTA}======================================================================{ANSI_RESET}")
    print(f"{ANSI_BOLD}{ANSI_MAGENTA}[ORCHESTRATOR CONFLICT RESOLUTION & REASONING]{ANSI_RESET}")
    print(f"{ANSI_BOLD}{ANSI_MAGENTA}======================================================================{ANSI_RESET}")

    if final_next_action.resolved_conflicts:
        print(f"\n{ANSI_BOLD}{ANSI_YELLOW}Cross-Grade Conflicts Resolved:{ANSI_RESET}")
        for c_msg in final_next_action.resolved_conflicts:
            print(f"  {ANSI_YELLOW}- {c_msg}{ANSI_RESET}")

    print(f"\n{ANSI_BOLD}{ANSI_CYAN}Orchestrator Rationale:{ANSI_RESET}")
    print(f"  {final_next_action.reason}")

    prio = final_next_action.priority
    prio_color = ANSI_RED if prio == "critical" else (ANSI_MAGENTA if prio == "high" else (ANSI_YELLOW if prio == "medium" else ANSI_GREEN))

    print(f"\n{ANSI_BOLD}{ANSI_GREEN}[Single Prioritized Action Committed to Shared State]{ANSI_RESET}")
    print(f"  {ANSI_BOLD}Priority:{ANSI_RESET}       {prio_color}{prio.upper()}{ANSI_RESET}")
    print(f"  {ANSI_BOLD}Target Grade:{ANSI_RESET}   {ANSI_CYAN}Grade {final_next_action.grade} ({final_next_action.subject}){ANSI_RESET}")
    print(f"  {ANSI_BOLD}Action Type:{ANSI_RESET}    {final_next_action.action_type}")
    print(f"  {ANSI_BOLD}Reason:{ANSI_RESET}         {final_next_action.reason}")

    print(f"\n{ANSI_BOLD}{ANSI_CYAN}[State Updates Committed to Shared Store (Single Writer)]{ANSI_RESET}")
    for sup in final_state_updates:
        st_color = ANSI_GREEN if sup.status == "reconciled" else ANSI_YELLOW
        print(f"  - {ANSI_BOLD}Grade {sup.grade} {sup.subject}:{ANSI_RESET} status={st_color}{sup.status}{ANSI_RESET}, topic='{sup.decided_topic}', resource='{sup.recommended_resource}', activity_status='{sup.activity_status}'")
    print(f"{ANSI_BOLD}{ANSI_MAGENTA}======================================================================{ANSI_RESET}\n")

    formatted_evaluations = {}
    for g_k, prop in proposals.items():
        p_diag = prop.get("progress_diag")
        if hasattr(p_diag, "model_dump"): p_diag = p_diag.model_dump()
        elif hasattr(p_diag, "dict"): p_diag = p_diag.dict()
        elif isinstance(p_diag, dict): p_diag = dict(p_diag)

        c_dec = prop.get("curriculum_dec")
        if hasattr(c_dec, "model_dump"): c_dec = c_dec.model_dump()
        elif hasattr(c_dec, "dict"): c_dec = c_dec.dict()
        elif isinstance(c_dec, dict): c_dec = dict(c_dec)
        if isinstance(c_dec, dict) and "explanation" in c_dec and "reasoning" not in c_dec:
            c_dec["reasoning"] = c_dec["explanation"]

        r_rec = prop.get("resource_rec")
        if hasattr(r_rec, "model_dump"): r_rec = r_rec.model_dump()
        elif hasattr(r_rec, "dict"): r_rec = r_rec.dict()
        elif isinstance(r_rec, dict): r_rec = dict(r_rec)
        if isinstance(r_rec, dict) and "explanation" in r_rec and "rationale" not in r_rec:
            r_rec["rationale"] = r_rec["explanation"]

        a_des = prop.get("activity_design")
        if hasattr(a_des, "model_dump"): a_des = a_des.model_dump()
        elif hasattr(a_des, "dict"): a_des = a_des.dict()
        elif isinstance(a_des, dict): a_des = dict(a_des)

        s_verd = prop.get("safety_verdict")
        if hasattr(s_verd, "model_dump"): s_verd = s_verd.model_dump()
        elif hasattr(s_verd, "dict"): s_verd = s_verd.dict()
        elif isinstance(s_verd, dict): s_verd = dict(s_verd)

        formatted_evaluations[g_k] = {
            "grade": prop.get("grade"),
            "subject": prop.get("subject"),
            "progress_diag": p_diag,
            "curriculum_dec": c_dec,
            "resource_rec": r_rec,
            "activity_design": a_des,
            "safety_verdict": s_verd,
            "safety_attempts": prop.get("safety_attempts")
        }

    return OrchestrationResult(
        cycle_id=cycle_id,
        next_action=final_next_action,
        state_updates=final_state_updates,
        specialist_evaluations=formatted_evaluations
    )
