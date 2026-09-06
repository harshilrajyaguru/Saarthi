import json
from datetime import datetime, timezone
from pathlib import Path
from strands import tool

STATE_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "classroom_state.json"
)


@tool
def read_shared_state() -> dict:
    """
    Reads the shared classroom state from data/classroom_state.json.
    Does NOT mutate shared state.
    """
    if not STATE_FILE.exists():
        return {"classrooms": [], "last_updated": None}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@tool
def write_shared_state(updates: dict) -> dict:
    """
    SINGLE WRITER tool for updating data/classroom_state.json.
    ONLY the Orchestrator is allowed to invoke this tool after full reconciliation.
    """
    current_state = read_shared_state()

    if "reconciled_updates" in updates:
        current_state["reconciled_updates"] = updates["reconciled_updates"]

    if "grades" in updates:
        current_state["grades"] = updates["grades"]

    current_state["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(current_state, f, indent=2)

    return {"status": "success", "last_updated": current_state["last_updated"]}


@tool
def get_active_grades(session: dict) -> dict:
    """
    Identifies Grade x Subject entries that actually need re-evaluation.
    Evaluates:
    - New learning signals (unread session logs)
    - Pending flags (attention_flag = true)
    - Stale state (no session for >= 3 days)
    - Explicit session setup changes / resource changes
    Skips grades with no meaningful changes.
    Does NOT perform LLM calls or mutate state.
    """
    state = read_shared_state()
    grades_state = {}

    if "classrooms" in state:
        for c in state["classrooms"]:
            g_num = c.get("grade")
            subjs = c.get("subjects", {})
            for s_name, s_data in subjs.items():
                g_key = f"Grade_{g_num}_{s_name.capitalize()}"
                grades_state[g_key] = {
                    "grade": str(g_num),
                    "subject": s_name.capitalize(),
                    "current_topic": s_data.get("current_topic"),
                    "attention_flag": s_data.get("attention_flag", False),
                    "pending_action": s_data.get("pending_action", False),
                    "last_evaluation_date": s_data.get("last_evaluation_date", "2026-08-30T00:00:00Z")
                }
    elif "grades" in state:
        grades_state = state["grades"]

    if not grades_state:
        grades_state = {
            "Grade_3_Math": {"grade": "3", "subject": "Math", "current_topic": "Equivalent fractions"},
            "Grade_4_Math": {"grade": "4", "subject": "Math", "current_topic": "Multiplying fractions"},
            "Grade_5_Math": {"grade": "5", "subject": "Math", "current_topic": "Dividing fractions"},
            "Grade_6_Math": {"grade": "6", "subject": "Math", "current_topic": "Ratios"}
        }

    all_grades = list(grades_state.keys())
    active_specified = session.get("active_grades")

    active_evaluations = []
    skipped_grades = []

    for g_key in all_grades:
        g_data = grades_state.get(g_key, {})

        if active_specified is not None and g_key not in active_specified:
            skipped_grades.append({
                "grade_key": g_key,
                "reason": "not_in_active_session"
            })
            continue

        has_new_signal = session.get("new_signals", {}).get(g_key, False) or g_data.get("has_new_signal", False)
        has_pending_flag = g_data.get("attention_flag", False) or g_data.get("pending_action", False)

        last_eval = g_data.get("last_evaluation_date")
        is_stale = False
        if last_eval:
            try:
                days_old = (datetime.now() - datetime.fromisoformat(last_eval.replace("Z", "+00:00").split("+")[0])).days
                if days_old >= 3:
                    is_stale = True
            except Exception:
                pass
        else:
            is_stale = True

        session_change = session.get("force_reevaluate", False) or g_key in session.get("changed_grades", [])

        if has_new_signal or has_pending_flag or is_stale or session_change:
            active_evaluations.append({
                "grade_key": g_key,
                "reason": (
                    "new_signal" if has_new_signal else
                    "pending_flag" if has_pending_flag else
                    "stale_state" if is_stale else
                    "session_change"
                ),
                "grade_data": g_data
            })
        else:
            skipped_grades.append({
                "grade_key": g_key,
                "reason": "no_change_or_pending_flag"
            })

    return {
        "active_evaluations": active_evaluations,
        "skipped_grades": skipped_grades,
        "active_count": len(active_evaluations),
        "skipped_count": len(skipped_grades)
    }
