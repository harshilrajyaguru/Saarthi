import json
from pathlib import Path
from typing import Union
from strands import tool

ACTIVITY_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "activity_data.json"
)


def load_activity_data() -> dict:
    """Helper to read the local activity data JSON file."""
    if not ACTIVITY_FILE.exists():
        return {"templates": [], "recent_history": {}}
    with open(ACTIVITY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@tool
def get_activity_templates(topic: str, resource_type: str) -> dict:
    """
    Returns existing activity templates for a given topic and resource type that may be adapted.
    Reads from the local activity template store.
    Does NOT modify templates or call LLMs.
    """
    data = load_activity_data()
    templates = data.get("templates", [])

    matched = []
    for t in templates:
        t_topic = t.get("topic", "").lower()
        t_res = t.get("resource_type", "").lower()
        
        # Check topic match (exact or substring) and resource_type match
        topic_match = topic.lower() in t_topic or t_topic in topic.lower() or "fraction" in t_topic and "fraction" in topic.lower()
        res_match = resource_type.lower() in t_res or t_res in resource_type.lower()
        
        if topic_match and res_match:
            matched.append(t)

    return {
        "query_topic": topic,
        "query_resource_type": resource_type,
        "found_templates": matched,
        "count": len(matched)
    }


@tool
def get_recent_activity_history(grade: Union[int, str], subject: str) -> dict:
    """
    Returns recently used activity formats for a Grade x Subject.
    Used to avoid repeating the exact same activity format two sessions in a row when an alternative exists.
    Does NOT perform activity design or call LLMs.
    """
    data = load_activity_data()
    recent_history = data.get("recent_history", {})

    grade_str = str(grade)
    key_exact = f"Grade {grade_str}_{subject}"

    matched_history = recent_history.get(key_exact, [])
    if not matched_history:
        for k, v in recent_history.items():
            if grade_str in k and subject.lower() in k.lower():
                matched_history = v
                break

    recent_formats = [h.get("format", "") for h in matched_history]

    return {
        "grade": grade_str,
        "subject": subject,
        "recent_sessions": matched_history,
        "recent_formats": recent_formats
    }
