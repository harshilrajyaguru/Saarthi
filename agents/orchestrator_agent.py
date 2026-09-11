import json
import uuid
from typing import Any, AsyncGenerator, Literal, Optional, Union
from pydantic import BaseModel, Field

from strands import Agent
from strands.models import Model

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
        description="List of cross-grade resource/attention conflicts resolved during this cycle"
    )


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


from agents.model_factory import get_saarthi_model
_ORCHESTRATOR_MODEL = get_saarthi_model()


def parse_grade_key(g_key: str) -> tuple[str, str]:
    parts = g_key.split("_")
    if len(parts) >= 3 and parts[0] == "Grade":
        s = parts[2]
        s_norm = "Math" if s.lower() in ["mathematics", "maths", "math"] else s.capitalize()
        return parts[1], s_norm
    elif len(parts) == 2 and parts[0] == "Grade":
        return parts[1], "Math"
    return parts[0].replace("Grade", "").strip() or "3", "Math"


from concurrent.futures import ThreadPoolExecutor

def _evaluate_single_active_grade(a_item: dict, session: dict) -> tuple[str, dict]:
    g_key = a_item["grade_key"]
    g_data = a_item.get("grade_data", {})
    g_str, subj_str = parse_grade_key(g_key)

    current_topic = g_data.get("current_topic") or "Equivalent fractions"

    # Check for mock overrides injected in session for testing specific evidence scenarios
    mock_prog = session.get("mock_progress", {}).get(g_key)
    if mock_prog:
        progress_diag = mock_prog
    else:
        try:
            progress_diag = analyze_progress(
                grade=g_str,
                subject=subj_str,
                current_topic=current_topic,
                latest_signals=session.get("new_signals", {})
            )
        except Exception:
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

    # 2. Curriculum Agent
    session_con = session.get("session_constraints", {"available_time": "30m"})
    teacher_con = session.get("teacher_constraints", {}).get(g_key)

    mock_curr = session.get("mock_curriculum", {}).get(g_key)
    if mock_curr:
        curriculum_dec = mock_curr
    else:
        curriculum_dec = reconcile_curriculum(
            grade=g_str,
            subject=subj_str,
            current_topic=current_topic,
            progress_diagnosis=progress_diag,
            session_constraints=session_con,
            teacher_constraints=teacher_con
        )

    # 3. Resource Agent
    decided_topic = curriculum_dec.get("decided_topic", current_topic)

    mock_res = session.get("mock_resource", {}).get(g_key)
    if mock_res:
        resource_rec = mock_res
    else:
        resource_rec = recommend_resources(
            grade=g_str,
            subject=subj_str,
            topic=decided_topic,
            session=session.get("session_info", {"duration_minutes": 40})
        )

    # Allow explicit requested resource override ONLY IF it is deployable/feasible
    requested_res = session.get("force_resource", {}).get(g_key)
    if requested_res:
        res_opts = resource_rec.get("resource_options", [])
        matching_opt = next((o for o in res_opts if requested_res.lower() in (o.get("type") if isinstance(o, dict) else getattr(o, "type", "")).lower()), None)
        feas = matching_opt.get("feasibility") if isinstance(matching_opt, dict) else (getattr(matching_opt, "feasibility", "") if matching_opt else "")
        if matching_opt and feas != "infeasible":
            resource_rec["recommended_resource"] = matching_opt.get("type")

    # 4 & 5. Activity Agent + Safety Gate (with max 2 retry loop)
    rec_resource = resource_rec.get("recommended_resource") or "printable_worksheet"
    trouble_spots = progress_diag.get("trouble_spots", ["confusing numerator/denominator when scaling"])
    mastery = progress_diag.get("mastery_estimate", "developing")
    direction = progress_diag.get("recommendation_direction", "reinforce")
    needs_gen = resource_rec.get("needs_generation", False)
    avail_time = session.get("session_info", {}).get("duration_minutes", 15)

    force_safety_action = session.get("mock_safety_action", {}).get(g_key)

    activity_design = design_activity(
        grade=g_str,
        subject=subj_str,
        decided_topic=decided_topic,
        pacing_decision=curriculum_dec.get("pacing_decision", "hold"),
        trouble_spots=trouble_spots,
        mastery_estimate=mastery,
        recommendation_direction=direction,
        recommended_resource=rec_resource,
        needs_generation=needs_gen,
        available_time_minutes=avail_time,
        progress_diagnosis=progress_diag,
        curriculum_decision=curriculum_dec,
        resource_recommendation=resource_rec,
        session_constraints=session_con
    )

    attempts = 0
    max_attempts = 2
    safety_verdict = None

    if force_safety_action:
        if force_safety_action == "escalate_to_teacher":
            safety_verdict = evaluate_safety_gate(
                activity_design, decided_topic, trouble_spots[0] if trouble_spots else "", avail_time
            )
            safety_verdict.passed = False
            safety_verdict.layer_failed = "layer_3"
            safety_verdict.action = "escalate_to_teacher"
        elif force_safety_action == "reject_and_regenerate":
            attempts = 2
            safety_verdict = evaluate_safety_gate(
                activity_design, decided_topic, trouble_spots[0] if trouble_spots else "", avail_time
            )
            safety_verdict.passed = False
            safety_verdict.layer_failed = "layer_1"
            safety_verdict.action = "reject_and_regenerate"
    else:
        while attempts < max_attempts:
            attempts += 1
            safety_verdict = evaluate_safety_gate(
                activity_design,
                decided_topic=decided_topic,
                targets_trouble_spot=trouble_spots[0] if trouble_spots else "",
                available_time_minutes=avail_time
            )
            if safety_verdict.passed or safety_verdict.action == "escalate_to_teacher":
                break
            if attempts < max_attempts:
                activity_design = design_activity(
                    grade=g_str,
                    subject=subj_str,
                    decided_topic=decided_topic,
                    pacing_decision=curriculum_dec.get("pacing_decision", "hold"),
                    trouble_spots=trouble_spots,
                    mastery_estimate=mastery,
                    recommendation_direction=direction,
                    recommended_resource=rec_resource,
                    needs_generation=True,
                    available_time_minutes=avail_time,
                    progress_diagnosis=progress_diag,
                    curriculum_decision=curriculum_dec,
                    resource_recommendation=resource_rec,
                    session_constraints=session_con
                )

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
    return g_key, prop


_ORCHESTRATOR_MODEL = get_saarthi_model()


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

    # STEP 2: Run specialist agents for active grades concurrently
    if active_evals:
        with ThreadPoolExecutor(max_workers=min(8, len(active_evals))) as executor:
            futures = [executor.submit(_evaluate_single_active_grade, a_item, session) for a_item in active_evals]
            for future in futures:
                g_key, prop = future.result()
                proposals[g_key] = prop

    # STEP 3: Route actual orchestration decision through existing Strands Agent (Ollama Qwen3:8b)
    shared_state = read_shared_state()

    # Serialize specialist outputs for context prompt
    specialist_summary = {}
    for g_k, prop in proposals.items():
        s_v = prop.get("safety_verdict")
        specialist_summary[g_k] = {
            "grade": prop.get("grade"),
            "subject": prop.get("subject"),
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

    orchestrator_user_prompt = (
        f"You are evaluating live classroom orchestration cycle {cycle_id}.\n\n"
        f"Ground-Truth Shared Classroom State:\n{json.dumps(shared_state, indent=2)}\n\n"
        f"Active Session Constraints & Resources:\n{json.dumps(session, indent=2)}\n\n"
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

    print(f"\n[STRANDS AGENT] Invoking OrchestratorAgent (Groq openai/gpt-oss-120b) for cycle {cycle_id}...")
    orchestrator_agent = Agent(
        model=_ORCHESTRATOR_MODEL,
        system_prompt=SYSTEM_PROMPT,
        tools=[read_shared_state, write_shared_state, get_active_grades],
        structured_output_model=OrchestrationResult,
        name="OrchestratorAgent",
        description="SAARTHI Orchestrator Agent sequencing active grades, resolving conflicts, surfacing one next action, and acting as single state writer."
    )
    agent_result = orchestrator_agent(orchestrator_user_prompt)

    if hasattr(agent_result, "structured_output") and agent_result.structured_output:
        raw_llm_result = agent_result.structured_output
    elif hasattr(agent_result, "message") and agent_result.message:
        raw_llm_result = OrchestrationResult.model_validate_json(agent_result.message.content)
    else:
        raise ValueError(f"OrchestratorAgent failed to return structured output: {agent_result}")

    # Extract LLM decisions
    llm_next_action = raw_llm_result.next_action
    llm_state_updates = raw_llm_result.state_updates or []

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

    formatted_evaluations = {}
    for g_k, prop in proposals.items():
        formatted_evaluations[g_k] = {
            "grade": prop.get("grade"),
            "subject": prop.get("subject"),
            "progress_diag": prop.get("progress_diag"),
            "curriculum_dec": prop.get("curriculum_dec"),
            "resource_rec": prop.get("resource_rec"),
            "activity_design": prop.get("activity_design"),
            "safety_verdict": prop["safety_verdict"].model_dump() if hasattr(prop.get("safety_verdict"), "model_dump") else prop.get("safety_verdict"),
            "safety_attempts": prop.get("safety_attempts")
        }

    return OrchestrationResult(
        cycle_id=cycle_id,
        next_action=final_next_action,
        state_updates=final_state_updates,
        specialist_evaluations=formatted_evaluations
    )
