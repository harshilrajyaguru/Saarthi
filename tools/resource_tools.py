import json
from pathlib import Path
from typing import Union
from strands import tool

RESOURCE_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "resource_data.json"
)


from tools.orchestrator_tools import safe_read_local_json


def load_resource_data() -> dict:
    """Helper to read the local resource data JSON file."""
    return safe_read_local_json(RESOURCE_FILE, {"inventory": {}, "usage_log": {}, "concurrent_demand": {}})


@tool
def get_resource_inventory(session: dict) -> dict:
    """
    Returns today's actual classroom resource inventory and environmental constraints.
    Reads from the local resource data store and overlays session-specific conditions.
    Does NOT perform resource evaluation or call LLMs.
    """
    data = load_resource_data()
    inv = dict(data.get("inventory", {}))

    # Apply session-specific overrides if provided in input session
    if isinstance(session, dict):
        for key, val in session.items():
            if key == "session_info" and isinstance(val, dict):
                for s_key, s_val in val.items():
                    inv[s_key] = s_val
            elif key != "concurrent_demand":
                inv[key] = val

    return inv


@tool
def get_resource_usage_log(grade: Union[int, str], subject: str, topic: str) -> dict:
    """
    Returns recent resource/activity-type usage history for a Grade x Subject x Topic.
    Used to detect staleness and avoid repeated usage of the same resource type.
    Does NOT perform resource evaluation or call LLMs.
    """
    data = load_resource_data()
    usage_log = data.get("usage_log", {})

    grade_str = str(grade)
    key_exact = f"Grade {grade_str}_{subject}_{topic}"

    recent_uses = usage_log.get(key_exact, [])
    if not recent_uses:
        for k, v in usage_log.items():
            if grade_str in k and subject.lower() in k.lower():
                recent_uses = v
                break

    resource_counts = {}
    for entry in recent_uses:
        r_type = entry.get("resource_type")
        if r_type:
            resource_counts[r_type] = resource_counts.get(r_type, 0) + 1

    return {
        "grade": grade_str,
        "subject": subject,
        "topic": topic,
        "total_recent_sessions": len(recent_uses),
        "usage_counts": resource_counts,
        "recent_usage_history": recent_uses
    }


@tool
def check_concurrent_demand(session: dict) -> dict:
    """
    Inspects concurrent resource requests across multiple active grades in today's session.
    Used to surface resource contention conflicts for shared physical/digital assets.
    Does NOT decide which grade wins the contested resource.
    """
    data = load_resource_data()
    default_demand = data.get("concurrent_demand", {})

    if isinstance(session, dict) and "concurrent_demand" in session:
        session_demand = session["concurrent_demand"]
        if isinstance(session_demand, dict):
            active_grades = list(session_demand.keys())
            return {
                "active_grades": active_grades,
                "concurrent_demand": session_demand
            }

    active_grades = list(default_demand.keys())
    return {
        "active_grades": active_grades,
        "concurrent_demand": default_demand
    }
