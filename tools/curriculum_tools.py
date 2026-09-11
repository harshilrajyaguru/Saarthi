import json
from pathlib import Path
from typing import Union
from strands import tool

CURRICULUM_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "curriculum_data.json"
)


from tools.orchestrator_tools import safe_read_local_json


def load_curriculum_data() -> dict:
    """Helper to read the local curriculum JSON file."""
    return safe_read_local_json(CURRICULUM_FILE, {"curriculum": {}})


@tool
def get_syllabus_position(grade: Union[int, str], subject: str) -> dict:
    """
    Returns the official expected topic/pacing for a Grade x Subject.
    Reads from the local curriculum store.
    Does NOT perform curriculum decisions or call LLMs.
    """
    data = load_curriculum_data().get("curriculum", {})
    grade_str = str(grade)
    subject_clean = subject.strip().lower()

    grade_data = data.get(grade_str)
    if not grade_data:
        return {
            "grade": grade_str,
            "subject": subject,
            "syllabus_topics": [],
            "message": f"No curriculum found for Grade {grade}"
        }

    topics = grade_data.get("topics", [])
    topic_names = [t["name"] for t in topics]

    return {
        "grade": grade_str,
        "subject": subject,
        "syllabus_topics": topic_names,
        "current_syllabus_target": topic_names[-1] if topic_names else "Unknown",
        "full_syllabus": topics
    }


@tool
def get_prerequisite_map(topic: str) -> dict:
    """
    Returns prerequisite skills and direct dependencies for a given topic.
    Reads from the local curriculum store.
    Does NOT perform curriculum decisions or call LLMs.
    """
    data = load_curriculum_data().get("curriculum", {})
    topic_clean = topic.strip().lower()

    for g_key, g_val in data.items():
        for t in g_val.get("topics", []):
            t_name = t["name"].strip().lower()
            if topic_clean in t_name or t_name in topic_clean:
                prereqs = t.get("prerequisites", [])
                return {
                    "topic": t["name"],
                    "prerequisites": prereqs,
                    "has_prerequisites": len(prereqs) > 0
                }

    return {
        "topic": topic,
        "prerequisites": [],
        "has_prerequisites": False,
        "message": f"Topic '{topic}' not found in prerequisite map"
    }
