import json
from pathlib import Path
from typing import Any, Union
from strands import tool


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "classroom_state.json"
)


def load_classroom_data() -> dict:
    """Helper to read the classroom state JSON file."""
    if not DATA_FILE.exists():
        return {"classrooms": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@tool
def get_history(grade: Union[int, str], subject: str, topic: str, n: int = 3) -> dict:
    """
    Return the last N sessions of prior diagnoses/signals for a Grade x Subject and topic.
    Reads from the shared state data store.
    Does NOT perform diagnosis or call LLMs.
    """
    data = load_classroom_data()
    grade_str = str(grade)
    subject_clean = subject.strip().lower()

    for classroom in data.get("classrooms", []):
        if str(classroom.get("grade")) == grade_str:
            subjects = classroom.get("subjects", {})
            subj_data = None
            for s_key, s_val in subjects.items():
                if s_key.lower() == subject_clean:
                    subj_data = s_val
                    break

            if not subj_data:
                return {
                    "grade": grade_str,
                    "subject": subject,
                    "topic": topic,
                    "sessions": [],
                    "count": 0,
                    "message": f"Subject '{subject}' not found for Grade {grade}"
                }

            all_sessions = subj_data.get("sessions", [])
            topic_clean = topic.strip().lower()
            matching_sessions = []
            for sess in all_sessions:
                sess_topic = str(sess.get("topic", "")).strip().lower()
                if topic_clean in sess_topic or sess_topic in topic_clean:
                    matching_sessions.append(sess)

            # Fall back to all sessions for the subject if specific topic substring has no match
            selected_sessions = matching_sessions if matching_sessions else all_sessions
            recent = selected_sessions[-n:] if n > 0 else selected_sessions

            return {
                "grade": grade_str,
                "subject": subject,
                "topic": topic,
                "sessions": recent,
                "count": len(recent)
            }

    return {
        "grade": grade_str,
        "subject": subject,
        "topic": topic,
        "sessions": [],
        "count": 0,
        "message": f"Grade {grade} not found"
    }


@tool
def get_trouble_spot_log(grade: Union[int, str], subject: str) -> dict:
    """
    Return previously flagged conceptual gaps/trouble spots for a Grade x Subject.
    Reads from the shared state data store.
    Does NOT perform diagnosis or call LLMs.
    """
    data = load_classroom_data()
    grade_str = str(grade)
    subject_clean = subject.strip().lower()

    for classroom in data.get("classrooms", []):
        if str(classroom.get("grade")) == grade_str:
            subjects = classroom.get("subjects", {})
            subj_data = None
            for s_key, s_val in subjects.items():
                if s_key.lower() == subject_clean:
                    subj_data = s_val
                    break

            if not subj_data:
                return {
                    "grade": grade_str,
                    "subject": subject,
                    "trouble_spots": [],
                    "message": f"Subject '{subject}' not found for Grade {grade}"
                }

            trouble_spots = subj_data.get("trouble_spot_log", [])
            return {
                "grade": grade_str,
                "subject": subject,
                "trouble_spots": trouble_spots
            }

    return {
        "grade": grade_str,
        "subject": subject,
        "trouble_spots": [],
        "message": f"Grade {grade} not found"
    }