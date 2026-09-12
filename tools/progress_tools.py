import json
from pathlib import Path
from typing import Any, Union
from strands import tool


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "classroom_state.json"
)


from tools.orchestrator_tools import safe_read_local_json


def load_classroom_data() -> dict:
    """Helper to read the classroom state JSON file."""
    return safe_read_local_json(DATA_FILE, {"classrooms": []})


def find_grade_entry(data: dict, grade: Union[int, str], subject: str = "") -> dict:
    """Helper to locate per-grade state entry from grades dict."""
    g_str = str(grade).strip()
    grades_dict = data.get("grades", {})
    if not isinstance(grades_dict, dict):
        return {}

    candidates = [
        g_str,
        f"Grade_{g_str}_{subject}",
        f"Grade_{g_str}",
        f"Grade {g_str}_{subject}",
        f"Grade {g_str}"
    ]
    for c in candidates:
        if c in grades_dict and isinstance(grades_dict[c], dict):
            return grades_dict[c]

    for k, v in grades_dict.items():
        if isinstance(v, dict):
            k_g = str(v.get("grade", ""))
            if k_g == g_str or g_str in k:
                return v

    return {}


@tool
def get_history(grade: Union[int, str], subject: str, topic: str, n: int = 10) -> dict:
    """
    Return the last N sessions of prior diagnoses/signals for a Grade x Subject and topic.
    Computes overall_avg, linear regression trend, total_below_60, and aggregated_error_tags.
    Reads from the shared state data store.
    Does NOT perform diagnosis or call LLMs.
    """
    data = load_classroom_data()
    grade_str = str(grade)

    g_entry = find_grade_entry(data, grade, subject)
    if g_entry and "history" in g_entry and isinstance(g_entry["history"], list) and len(g_entry["history"]) > 0:
        all_hist = g_entry["history"]
        topic_clean = topic.strip().lower()
        matching = [s for s in all_hist if topic_clean in str(s.get("topic", "")).lower() or str(s.get("topic", "")).lower() in topic_clean]
        selected = matching if matching else all_hist
        recent = selected[-n:] if n > 0 else selected

        count = len(recent)
        avg_vals = [float(s.get("avg_correctness", s.get("correctness", 0.7))) for s in recent]
        overall_avg = sum(avg_vals) / count if count > 0 else 0.0

        # Linear regression trend calculation over session index
        if count < 2:
            trend = "insufficient_data"
        else:
            x_mean = (count - 1) / 2.0
            y_mean = overall_avg
            num = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(avg_vals))
            den = sum((i - x_mean) ** 2 for i in range(count))
            slope = (num / den) if den != 0 else 0.0
            if slope >= 0.04:
                trend = "improving"
            elif slope <= -0.04:
                trend = "declining"
            else:
                trend = "stagnant"

        total_below_60 = sum(int(s.get("below_60_count", 0)) for s in recent)

        agg_error_tags = {}
        for s in recent:
            err_dict = s.get("error_tags", {})
            if isinstance(err_dict, dict):
                for k_tag, val in err_dict.items():
                    agg_error_tags[k_tag] = agg_error_tags.get(k_tag, 0) + (int(val) if isinstance(val, (int, float)) else 1)

        return {
            "grade": grade_str,
            "subject": subject,
            "topic": topic,
            "count": count,
            "sessions": recent,
            "overall_avg": round(overall_avg, 3),
            "trend": trend,
            "total_below_60": total_below_60,
            "aggregated_error_tags": agg_error_tags
        }

    # Fall back to existing mock/classrooms shape when key missing
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
                    "overall_avg": 0.0,
                    "trend": "insufficient_data",
                    "total_below_60": 0,
                    "aggregated_error_tags": {},
                    "message": f"Subject '{subject}' not found for Grade {grade}"
                }

            all_sessions = subj_data.get("sessions", [])
            topic_clean = topic.strip().lower()
            matching_sessions = []
            for sess in all_sessions:
                sess_topic = str(sess.get("topic", "")).strip().lower()
                if topic_clean in sess_topic or sess_topic in topic_clean:
                    matching_sessions.append(sess)

            selected_sessions = matching_sessions if matching_sessions else all_sessions
            recent = selected_sessions[-n:] if n > 0 else selected_sessions
            count = len(recent)
            avg_vals = [float(s.get("correctness", 0.7)) for s in recent]
            overall_avg = sum(avg_vals) / count if count > 0 else 0.0

            return {
                "grade": grade_str,
                "subject": subject,
                "topic": topic,
                "sessions": recent,
                "count": count,
                "overall_avg": round(overall_avg, 3),
                "trend": "insufficient_data" if count < 2 else "stagnant",
                "total_below_60": 0,
                "aggregated_error_tags": {}
            }

    return {
        "grade": grade_str,
        "subject": subject,
        "topic": topic,
        "sessions": [],
        "count": 0,
        "overall_avg": 0.0,
        "trend": "insufficient_data",
        "total_below_60": 0,
        "aggregated_error_tags": {},
        "message": f"Grade {grade} not found"
    }


@tool
def get_trouble_spot_log(grade: Union[int, str], subject: str) -> dict:
    """
    Return previously flagged conceptual gaps/trouble spots for a Grade x Subject verbatim from state["grades"][g]["trouble_spot_log"].
    Reads from the shared state data store.
    Does NOT perform diagnosis or call LLMs.
    """
    data = load_classroom_data()
    grade_str = str(grade)

    g_entry = find_grade_entry(data, grade, subject)
    if g_entry and "trouble_spot_log" in g_entry:
        log_val = g_entry["trouble_spot_log"]
        return {
            "grade": grade_str,
            "subject": subject,
            "trouble_spots": log_val,
            "trouble_spot_log": log_val
        }

    subject_clean = subject.strip().lower()
    for classroom in data.get("classrooms", []):
        if str(classroom.get("grade")) == grade_str:
            subjects = classroom.get("subjects", {})
            subj_data = None
            for s_key, s_val in subjects.items():
                if s_key.lower() == subject_clean:
                    subj_data = s_val
                    break

            if subj_data:
                ts = subj_data.get("trouble_spot_log", [])
                return {
                    "grade": grade_str,
                    "subject": subject,
                    "trouble_spots": ts,
                    "trouble_spot_log": ts
                }

    return {
        "grade": grade_str,
        "subject": subject,
        "trouble_spots": [],
        "trouble_spot_log": [],
        "message": f"Grade {grade} not found"
    }