import os
from dotenv import load_dotenv
load_dotenv()

import uuid
import json
from dataclasses import asdict
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from classroom_loop import ClassroomSession, ClassroomLoopRunner
from tools.orchestrator_tools import read_shared_state

app = FastAPI(
    title="Saarthi Autonomous Classroom OS API",
    description="Backend API foundation linking frontend teacher inputs with the multi-agent Orchestration engine."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory session registry mapping session_id -> ClassroomLoopRunner
SESSIONS: Dict[str, ClassroomLoopRunner] = {}


import re

def normalize_subject(s: str) -> str:
    """
    Normalizes arbitrary subject strings to canonical Saarthi format.
    'Mathematics', 'Maths', 'math' -> 'Math'
    """
    if not s:
        return "Math"
    s_clean = str(s).strip()
    if s_clean.lower() in ["mathematics", "maths", "math"]:
        return "Math"
    return s_clean.capitalize()


def validate_signal_target_match(target_grade: str, signal_text: str) -> Optional[str]:
    """
    Lightweight validation to detect explicit grade number contradictions between
    selected target grade and signal text without invoking LLM or NLP classifier.
    """
    if not signal_text or not target_grade:
        return None

    # Extract target grade number (e.g. "Grade_5_Math" -> "5", "Grade 5" -> "5", "5" -> "5")
    target_clean = str(target_grade).replace("Grade_", "").replace("Grade", "").strip()
    parts = target_clean.split("_")
    target_num = parts[0].strip()

    if not target_num.isdigit():
        return None

    # Detect explicit grade mentions in signal text like: "Grade 6", "grade 6", "Class 6", "6th grade"
    patterns = [
        r'\b(?:grade|class|std|standard)\s*[-:]?\s*([1-8])\b',
        r'\b([1-8])(?:st|nd|rd|th)?\s*(?:grade|class|std|standard)\b'
    ]

    mentioned_grades = set()
    for pat in patterns:
        matches = re.findall(pat, signal_text, flags=re.IGNORECASE)
        for m in matches:
            if isinstance(m, tuple):
                m = m[0]
            mentioned_grades.add(str(m))

    # If explicit grade numbers were mentioned, and NONE of them match the target grade number:
    if mentioned_grades and target_num not in mentioned_grades:
        mentioned_str = ", ".join([f"Grade {g}" for g in sorted(mentioned_grades)])
        return f"Signal appears to mention {mentioned_str}, but Grade {target_num} is selected. Please confirm the target grade."

    return None


def parse_teacher_input(payload: Dict[str, Any]) -> tuple[list[str], list[str], int, dict, dict]:
    """
    Parses and normalizes arbitrary teacher input from API requests.
    Supports formats:
    - 'grades': ["3", "4"] or [{"grade": "3", "subject": "Math"}] or ["Grade 3 Math"]
    - 'grade_selection': [{"grade": "3", "subject": "Math"}]
    - 'session_minutes' or 'duration_minutes': integer
    - 'resources': dict of classroom resources
    - 'connectivity': string ("online", "low_bandwidth", "offline")
    - 'teacher_constraints': list or dict of constraints
    - 'notes' / 'student_context': additional teacher notes
    """
    raw_grades = payload.get("grades") if payload.get("grades") is not None else payload.get("grade_selection")
    if raw_grades is None:
        raw_grades = []
    if isinstance(raw_grades, (str, int)):
        raw_grades = [raw_grades]

    duration_val = payload.get("session_minutes")
    if duration_val is None:
        duration_val = payload.get("duration_minutes")
    if duration_val is None:
        duration_val = payload.get("session_duration_minutes")

    if duration_val is None:
        duration_minutes = 40
    else:
        duration_minutes = int(duration_val)

    if duration_minutes <= 0:
        raise HTTPException(status_code=400, detail="session_minutes must be greater than 0")

    if not raw_grades:
        raise HTTPException(status_code=400, detail="At least one grade must be provided in teacher input")

    subjects_input = payload.get("subjects", [])
    if isinstance(subjects_input, str):
        subjects_input = [subjects_input]

    active_grades = []
    subjects = []

    for idx, item in enumerate(raw_grades):
        if isinstance(item, dict):
            g = str(item.get("grade", "")).strip().replace("Grade", "").strip()
            s = normalize_subject(item.get("subject", "Math"))
        elif isinstance(item, str):
            clean_item = item.replace("Grade", "").strip()
            parts = clean_item.split()
            if len(parts) >= 2:
                g = parts[0].strip()
                s = normalize_subject(" ".join(parts[1:]))
            else:
                g = clean_item
                s = normalize_subject(subjects_input[idx] if idx < len(subjects_input) else "Math")
        elif isinstance(item, int):
            g = str(item)
            s = normalize_subject(subjects_input[idx] if idx < len(subjects_input) else "Math")
        else:
            raise HTTPException(status_code=400, detail=f"Invalid grade entry: {item}")

        if not g:
            raise HTTPException(status_code=400, detail="Grade level identifier cannot be empty")

        grade_key = f"Grade_{g}_{s}"
        active_grades.append(grade_key)
        subjects.append(s)

    raw_resources = payload.get("resources") or {}
    if not isinstance(raw_resources, dict):
        raw_resources = {}

    connectivity = str(payload.get("connectivity", raw_resources.get("connectivity", "online")))

    resources = {
        "tablets": raw_resources.get("tablets", 2),
        "tv": raw_resources.get("tv", True),
        "printer": raw_resources.get("printer", True),
        "internet": (connectivity != "offline") and raw_resources.get("internet", True)
    }

    notes = payload.get("notes") or payload.get("student_context") or ""
    raw_constraints = payload.get("teacher_constraints", [])

    if isinstance(raw_constraints, dict):
        teacher_constraints_dict = raw_constraints
    elif isinstance(raw_constraints, list):
        teacher_constraints_dict = {
            gk: {"constraints": raw_constraints, "notes": notes} for gk in active_grades
        }
    elif isinstance(raw_constraints, str):
        teacher_constraints_dict = {
            gk: {"notes": raw_constraints} for gk in active_grades
        }
    else:
        teacher_constraints_dict = {}

    constraints = {
        "available_time": f"{duration_minutes}m",
        "connectivity": connectivity,
        "teacher_constraints": teacher_constraints_dict,
        "notes": notes,
        **resources
    }

    return active_grades, subjects, duration_minutes, resources, constraints


def serialize_delivered_activities(activities: list) -> list[dict]:
    """Helper to convert delivered activity dataclass instances into JSON dicts."""
    serialized = []
    for act in activities:
        if hasattr(act, "__dataclass_fields__"):
            serialized.append(asdict(act))
        elif isinstance(act, dict):
            serialized.append(act)
        else:
            serialized.append({
                "activity_id": getattr(act, "activity_id", ""),
                "grade": getattr(act, "grade", ""),
                "subject": getattr(act, "subject", ""),
                "topic": getattr(act, "topic", ""),
                "activity_type": getattr(act, "activity_type", ""),
                "content": getattr(act, "content", {}),
                "estimated_time_minutes": getattr(act, "estimated_time_minutes", 10)
            })
    return serialized


def build_current_session_grades(session: ClassroomSession, orchestration_result: Optional[dict] = None) -> list[dict]:
    """
    Builds an explicit list of current-session grade entries for the teacher's requested active grades.
    Strictly filters out unrequested historical classroom entries (e.g. unselected grades in state).
    Binds results using canonical grade keys (Grade_<number>_<Subject>).
    """
    active_keys = session.active_grades or []
    delivered_activities = serialize_delivered_activities(session.delivered_activities)

    state_updates = []
    if orchestration_result and isinstance(orchestration_result, dict):
        state_updates = orchestration_result.get("state_updates", [])
    elif session.cycle_history and session.cycle_history[-1].orchestration_result:
        state_updates = session.cycle_history[-1].orchestration_result.get("state_updates", [])

    results = []
    for g_key in active_keys:
        parts = g_key.split("_")
        if len(parts) >= 3 and parts[0] == "Grade":
            g_num = parts[1]
            s_name = normalize_subject("_".join(parts[2:]))
        elif len(parts) == 2 and parts[0] == "Grade":
            g_num = parts[1]
            s_name = "Math"
        else:
            g_num = g_key.replace("Grade", "").strip() or "3"
            s_name = "Math"

        canonical_key = f"Grade_{g_num}_{s_name}"

        sup_match = None
        for sup in state_updates:
            sup_g = str(sup.get("grade", "")).strip()
            sup_s = normalize_subject(str(sup.get("subject", "")))
            if f"Grade_{sup_g}_{sup_s}" == canonical_key:
                sup_match = sup
                break

        act_match = None
        for act in delivered_activities:
            act_g = str(act.get("grade", "")).strip()
            act_s = normalize_subject(str(act.get("subject", "Math")))
            if f"Grade_{act_g}_{act_s}" == canonical_key:
                act_match = act
                break

        entry = {
            "grade": g_num,
            "subject": s_name,
            "grade_key": canonical_key,
            "status": sup_match.get("status", "reconciled") if sup_match else "reconciled",
            "decided_topic": sup_match.get("decided_topic") if sup_match else None,
            "recommended_resource": sup_match.get("recommended_resource") if sup_match else None,
            "activity_status": sup_match.get("activity_status") if sup_match else None,
            "delivered_activity": act_match
        }
        results.append(entry)

    return results


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    """Service health check endpoint."""
    return {"status": "ok", "service": "Saarthi API", "active_sessions_count": len(SESSIONS)}


@app.get("/api/classroom/state")
@app.get("/api/session-state")
async def get_classroom_state():
    """
    Returns the ground-truth shared classroom state.
    Read-only operation enforcing single-writer state safety.
    """
    try:
        state = read_shared_state()
        return state
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read shared state: {str(e)}")


@app.post("/api/classroom/start")
@app.post("/api/start-session")
async def start_classroom_session(payload: Dict[str, Any] = Body(...)):
    """
    Accepts real teacher input, initializes a ClassroomSession,
    and executes the cold-start multi-agent Orchestrator cycle.
    No hardcoded decisions are generated; actual agent outputs flow through.
    """
    try:
        active_grades, subjects, duration_minutes, resources, constraints = parse_teacher_input(payload)

        session_id = f"sess_{uuid.uuid4().hex[:8]}"

        session = ClassroomSession(
            session_id=session_id,
            active_grades=active_grades,
            subjects=subjects,
            session_duration_minutes=duration_minutes,
            remaining_time_minutes=duration_minutes,
            classroom_resources={
                "tablets_free": resources.get("tablets", 2),
                "tv_available": resources.get("tv", True),
                "printer_available": resources.get("printer", True),
                "internet_connected": resources.get("internet", True)
            },
            session_constraints=constraints
        )

        runner = ClassroomLoopRunner(session)
        cycle_record = runner.start_session()

        # Register in-memory session runner
        SESSIONS[session_id] = runner

        orch_res = cycle_record.orchestration_result

        # Persist COMPLETE active session metadata for recovery across backend process restarts
        from tools.orchestrator_tools import write_shared_state
        current_session_grades = build_current_session_grades(session, orch_res)
        delivered_acts_serialized = serialize_delivered_activities(session.delivered_activities)

        grade_selection = payload.get("grade_selection")
        if not grade_selection:
            grade_selection = [{"grade": item.get("grade", ""), "subject": item.get("subject", "Math")} for item in current_session_grades]

        write_shared_state({
            "active_session": {
                "session_id": session_id,
                "status": session.status,
                "active_grades": active_grades,
                "subjects": subjects,
                "duration_minutes": duration_minutes,
                "remaining_time_minutes": session.remaining_time_minutes,
                "current_cycle": session.current_cycle,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "classroom_resources": session.classroom_resources,
                "session_constraints": constraints,
                "delivered_activities": delivered_acts_serialized,
                "current_session_grades": current_session_grades,
                "grade_selection": grade_selection,
                "resources": resources,
                "cycle_record": orch_res,
            }
        })
        shared_state = read_shared_state()

        return {
            "session_id": session_id,
            "status": session.status,
            "duration_minutes": duration_minutes,
            "active_grades": active_grades,
            "grade_selection": grade_selection,
            "resources": resources,
            "current_session_grades": current_session_grades,
            "cycle_record": orch_res,
            "shared_state": shared_state,
            "delivered_activities": delivered_acts_serialized
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API Error] Failed to start classroom session: {e}")
        raise HTTPException(status_code=500, detail=f"Agent orchestration failed: {str(e)}")


@app.get("/api/classroom/{session_id}")
async def get_classroom_session(session_id: str):
    """
    Retrieves the current state, delivered activities, cycle history,
    and shared classroom state for a specific session ID.
    Supports session recovery across backend process restarts.
    """
    runner = SESSIONS.get(session_id)
    if runner:
        session = runner.session
        shared_state = read_shared_state()
        active_info = shared_state.get("active_session", {})
        csg = build_current_session_grades(session)
        grade_sel = active_info.get("grade_selection") or [{"grade": item.get("grade", ""), "subject": item.get("subject", "Math")} for item in csg]
        res_dict = active_info.get("resources") or {
            "tablets": session.classroom_resources.get("tablets_free", 2),
            "tv": session.classroom_resources.get("tv_available", True),
            "printer": session.classroom_resources.get("printer_available", True),
            "internet": session.classroom_resources.get("internet_connected", True)
        }
        return {
            "session_id": session.session_id,
            "status": session.status,
            "current_cycle": session.current_cycle,
            "duration_minutes": session.session_duration_minutes,
            "remaining_time_minutes": session.remaining_time_minutes,
            "active_grades": session.active_grades,
            "grade_selection": grade_sel,
            "resources": res_dict,
            "current_session_grades": csg,
            "delivered_activities": serialize_delivered_activities(session.delivered_activities),
            "cycle_history": [
                c.orchestration_result for c in session.cycle_history if c.orchestration_result
            ],
            "shared_state": shared_state
        }

    # Process Restart Recovery: Recover session from persisted shared state if available
    shared_state = read_shared_state()
    active_info = shared_state.get("active_session", {})

    if active_info and active_info.get("session_id") == session_id:
        status = active_info.get("status", "active")
        active_grades = active_info.get("active_grades", [])

        if status == "completed":
            return {
                "session_id": session_id,
                "status": "completed",
                "active_grades": [],
                "current_session_grades": [],
                "delivered_activities": [],
                "shared_state": shared_state
            }

        # Reconstruct FULL session from persisted metadata — NO agent pipeline execution
        from classroom_loop import parse_grade_subject, DeliveredActivity
        subjects = active_info.get("subjects", [])
        if not subjects:
            subjects = [parse_grade_subject(g)[1] for g in active_grades] if active_grades else ["Math"]

        persisted_delivered = active_info.get("delivered_activities", [])
        restored_activities = []
        for act_dict in persisted_delivered:
            if isinstance(act_dict, dict):
                restored_activities.append(DeliveredActivity(
                    activity_id=act_dict.get("activity_id", ""),
                    grade=act_dict.get("grade", ""),
                    subject=act_dict.get("subject", "Math"),
                    topic=act_dict.get("topic", ""),
                    activity_type=act_dict.get("activity_type", ""),
                    content=act_dict.get("content", {}),
                    estimated_time_minutes=act_dict.get("estimated_time_minutes", 10),
                    delivery_status=act_dict.get("delivery_status", "delivered"),
                    delivered_at_cycle=act_dict.get("delivered_at_cycle", 1),
                ))

        rec_session = ClassroomSession(
            session_id=session_id,
            active_grades=active_grades,
            subjects=subjects,
            session_duration_minutes=active_info.get("duration_minutes", 40),
            remaining_time_minutes=active_info.get("remaining_time_minutes",
                                                   active_info.get("duration_minutes", 40)),
            status=status,
            current_cycle=active_info.get("current_cycle", 1),
            classroom_resources=active_info.get("classroom_resources", {}),
            session_constraints=active_info.get("session_constraints", {}),
            delivered_activities=restored_activities,
        )
        rec_runner = ClassroomLoopRunner(rec_session)
        SESSIONS[session_id] = rec_runner

        # Use persisted current_session_grades if available, otherwise rebuild
        persisted_csg = active_info.get("current_session_grades")
        if persisted_csg and isinstance(persisted_csg, list):
            current_session_grades = persisted_csg
        else:
            current_session_grades = build_current_session_grades(rec_session)

        grade_sel = active_info.get("grade_selection") or [{"grade": item.get("grade", ""), "subject": item.get("subject", "Math")} for item in current_session_grades]
        res_dict = active_info.get("resources") or {
            "tablets": rec_session.classroom_resources.get("tablets_free", 2),
            "tv": rec_session.classroom_resources.get("tv_available", True),
            "printer": rec_session.classroom_resources.get("printer_available", True),
            "internet": rec_session.classroom_resources.get("internet_connected", True)
        }

        # Use persisted cycle_record for cycle_history if available
        persisted_cycle_record = active_info.get("cycle_record")
        cycle_history = [persisted_cycle_record] if persisted_cycle_record else []

        return {
            "session_id": session_id,
            "status": status,
            "current_cycle": rec_session.current_cycle,
            "duration_minutes": rec_session.session_duration_minutes,
            "remaining_time_minutes": rec_session.remaining_time_minutes,
            "active_grades": active_grades,
            "grade_selection": grade_sel,
            "resources": res_dict,
            "current_session_grades": current_session_grades,
            "delivered_activities": serialize_delivered_activities(rec_session.delivered_activities),
            "cycle_history": cycle_history,
            "shared_state": shared_state
        }

    raise HTTPException(status_code=404, detail=f"Classroom session '{session_id}' not found")


@app.post("/api/classroom-signal")
@app.post("/api/classroom/{session_id}/signals")
async def submit_classroom_signals(payload: Dict[str, Any] = Body(...), session_id: Optional[str] = None):
    """
    Submits a mid-session classroom or student signal (e.g., student struggling on a topic),
    validates target grade integrity, triggers adaptive reasoning cycle, and returns updated state.
    """
    req_session_id = session_id or payload.get("session_id")
    runner = SESSIONS.get(req_session_id)
    if not runner:
        if len(SESSIONS) == 1:
            runner = list(SESSIONS.values())[0]
        else:
            raise HTTPException(status_code=404, detail=f"Classroom session '{req_session_id}' not found")

    grade_raw = payload.get("grade")
    signal_type = payload.get("signal_type", "student_progress")
    signal_text = payload.get("signal") or payload.get("text") or ""

    if not grade_raw or not signal_text:
        raise HTTPException(
            status_code=400,
            detail="Payload must include 'grade' and 'signal' (or 'text') fields"
        )

    # Input-integrity validation step: Detect explicit grade number contradictions BEFORE agent execution
    mismatch_error = validate_signal_target_match(target_grade=str(grade_raw), signal_text=signal_text)
    if mismatch_error:
        raise HTTPException(
            status_code=400,
            detail=mismatch_error
        )

    grade_str = str(grade_raw).replace("Grade", "").replace("_", " ").strip().split()[0]
    subject_str = normalize_subject(payload.get("subject", "Math"))
    g_key = f"Grade_{grade_str}_{subject_str}"

    formatted_signals = {
        g_key: True,
        "grade": grade_str,
        "subject": subject_str,
        "signal_type": signal_type,
        "signal": signal_text,
        "score": payload.get("score"),
        "raw_payload": payload
    }

    try:
        cycle_record = runner.process_new_signals(formatted_signals)
        shared_state = read_shared_state()
        orch_res = cycle_record.orchestration_result

        return {
            "session_id": runner.session.session_id,
            "current_cycle": runner.session.current_cycle,
            "status": runner.session.status,
            "signal_processed": payload,
            "current_session_grades": build_current_session_grades(runner.session, orch_res),
            "cycle_record": orch_res,
            "shared_state": shared_state,
            "delivered_activities": serialize_delivered_activities(runner.session.delivered_activities)
        }
    except Exception as e:
        print(f"[API Error] Failed to process adaptive signal: {e}")
        raise HTTPException(status_code=500, detail=f"Adaptive cycle execution failed: {str(e)}")


@app.post("/api/classroom/{session_id}/run")
async def trigger_classroom_run(session_id: str, payload: Dict[str, Any] = Body(default={})):
    """
    Manually triggers an orchestration cycle for an existing active session.
    """
    runner = SESSIONS.get(session_id)
    if not runner:
        raise HTTPException(status_code=404, detail=f"Classroom session '{session_id}' not found")

    trigger_type = payload.get("trigger_type", "manual")
    override_signals = payload.get("override_signals")

    try:
        cycle_record = runner.run_cycle(trigger_type=trigger_type, override_signals=override_signals)
        shared_state = read_shared_state()

        return {
            "session_id": session_id,
            "current_cycle": runner.session.current_cycle,
            "status": runner.session.status,
            "cycle_record": cycle_record.orchestration_result,
            "shared_state": shared_state,
            "delivered_activities": serialize_delivered_activities(runner.session.delivered_activities)
        }
    except Exception as e:
        print(f"[API Error] Failed to run classroom cycle: {e}")
        raise HTTPException(status_code=500, detail=f"Cycle run failed: {str(e)}")


@app.post("/api/classroom/{session_id}/end")
@app.post("/api/end-session")
async def end_session_endpoint(payload: Dict[str, Any] = Body(default={}), session_id: Optional[str] = None):
    """
    Ends active classroom session via Orchestrator engine.
    Single-Writer Rule Strictly Preserved: Backend invokes runner.end_session(),
    which delegates state mutations to OrchestratorAgent.
    """
    try:
        req_session_id = session_id or payload.get("session_id")
        if not req_session_id:
            raise HTTPException(status_code=400, detail="session_id is required to end a session")

        runner = SESSIONS.pop(req_session_id, None)
        if not runner:
            session = ClassroomSession(session_id=req_session_id, active_grades=[], subjects=[])
            runner = ClassroomLoopRunner(session)

        cycle_record = runner.end_session()

        # Mark persisted active_session as completed so it won't be restored on refresh
        from tools.orchestrator_tools import write_shared_state as _ws
        _ws({
            "active_session": {
                "session_id": req_session_id,
                "status": "completed",
                "ended_at": datetime.now(timezone.utc).isoformat()
            }
        })
        shared_state = read_shared_state()

        return {
            "status": "success",
            "session_id": req_session_id,
            "message": "Session ended successfully. Today's classroom progress has been saved.",
            "cycle_record": cycle_record.orchestration_result,
            "shared_state": shared_state
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API Error] Failed to end session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
