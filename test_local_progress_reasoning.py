"""
test_local_progress_reasoning.py
--------------------------------
Real-life classroom timeline reasoning test for Saarthi Progress Agent (Qwen3 8B via Ollama).

Tests sequential progress tracking for Grade 4 Mathematics:
  Step 1: First Session (Equivalent Fractions) - initial exposure, 2/5 correct, mixed errors.
  Step 2: Repeated Misconception (Equivalent Fractions) - 3/6 correct, numerator/denominator scaling error repeats.
  Step 3: Clear Improvement (Equivalent Fractions) - 7/8 correct, misconception resolved with explanation.
  Step 4: Positive Teacher Signal (Equivalent Fractions) - teacher records "went well".
  Step 5: Negative Teacher Signal After Apparent Mastery (Equivalent Fractions) - 2/5 correct, regression, teacher notes "struggled".
  Step 6: New Unrelated Topic (Decimals) - 5/6 correct, clean performance on new topic.
"""

import sys
import json
import shutil
from pathlib import Path

# Ensure stdout uses UTF-8 to prevent Windows cp1252 encoding crashes
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from agents.local_ollama import analyze_progress_local

DATA_FILE = Path(__file__).resolve().parent / "data" / "classroom_state.json"
BACKUP_FILE = Path(__file__).resolve().parent / "data" / "classroom_state_backup.json"


def load_state() -> dict:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def reset_grade4_math_state(state: dict) -> dict:
    """Sets Grade 4 Math to an empty starting state for testing."""
    for c in state.get("classrooms", []):
        if str(c.get("grade")) == "4":
            subjects = c.get("subjects", {})
            subjects["math"] = {
                "current_topic": "Equivalent Fractions",
                "trouble_spot_log": [],
                "sessions": []
            }
            subjects["mathematics"] = subjects["math"]  # alias for subject name matching
    return state


def update_grade4_math_session(state: dict, session_data: dict, trouble_spots: list = None):
    """Appends a completed session and updates trouble spot log in Grade 4 Math shared state."""
    for c in state.get("classrooms", []):
        if str(c.get("grade")) == "4":
            subjects = c.get("subjects", {})
            for key in ["math", "mathematics"]:
                if key in subjects:
                    if session_data:
                        subjects[key]["sessions"].append(session_data)
                    if trouble_spots is not None:
                        subjects[key]["trouble_spot_log"] = trouble_spots
                    if session_data and session_data.get("topic"):
                        subjects[key]["current_topic"] = session_data["topic"]
    save_state(state)


def print_step_output(step_num: int, title: str, diagnosis: dict):
    print("=" * 80)
    print(f"STEP {step_num} — {title.upper()}")
    print("=" * 80)
    print(json.dumps(diagnosis, indent=2))
    print("\n")


def run_timeline_test():
    # 1. Backup state
    if DATA_FILE.exists():
        shutil.copy(DATA_FILE, BACKUP_FILE)

    try:
        # Initialize pristine state for Grade 4 Math
        state = load_state()
        state = reset_grade4_math_state(state)
        save_state(state)

        diagnoses = {}

        # =========================================================================
        # STEP 1 — FIRST SESSION (Equivalent Fractions)
        # =========================================================================
        signals_step1 = {
            "session_id": "sess_101",
            "date": "2026-09-01",
            "topic": "Equivalent Fractions",
            "questions_attempted": 5,
            "correct_answers": 2,
            "correctness": 0.4,
            "error_patterns": [
                "Mixed errors: arithmetic miscalculation, visual representation confusion",
                "No repeated conceptual pattern identified yet on first exposure"
            ],
            "student_notes": "First exposure to equivalent fractions; 2 of 5 correct with inconsistent/mixed errors."
        }

        diag1 = analyze_progress_local(
            grade=4,
            subject="Math",
            current_topic="Equivalent Fractions",
            latest_signals=signals_step1
        )
        diagnoses[1] = diag1
        print_step_output(1, "First Session (Equivalent Fractions)", diag1)

        # Update state after Step 1
        sess1_data = {
            "session_id": "sess_101",
            "date": "2026-09-01",
            "topic": "Equivalent Fractions",
            "result": 40,
            "correctness": 0.4,
            "completion": 1.0,
            "questions_attempted": 5,
            "correct": 2,
            "teacher_signal": None,
            "trouble_spots": []
        }
        update_grade4_math_session(state, sess1_data, trouble_spots=[])

        # =========================================================================
        # STEP 2 — REPEATED MISCONCEPTION (Equivalent Fractions)
        # =========================================================================
        signals_step2 = {
            "session_id": "sess_102",
            "date": "2026-09-02",
            "topic": "Equivalent Fractions",
            "questions_attempted": 6,
            "correct_answers": 3,
            "correctness": 0.5,
            "error_patterns": [
                "Treating equivalent fractions as if the numerator can change without proportionally changing the denominator",
                "e.g., claiming 1/2 = 2/2 or adding 1 to numerator without multiplying denominator by same factor"
            ],
            "student_notes": "Repeated conceptual mistake: altering numerator without proportionally scaling denominator."
        }

        diag2 = analyze_progress_local(
            grade=4,
            subject="Math",
            current_topic="Equivalent Fractions",
            latest_signals=signals_step2
        )
        diagnoses[2] = diag2
        print_step_output(2, "Repeated Misconception (Equivalent Fractions)", diag2)

        # Update state after Step 2
        sess2_data = {
            "session_id": "sess_102",
            "date": "2026-09-02",
            "topic": "Equivalent Fractions",
            "result": 50,
            "correctness": 0.5,
            "completion": 1.0,
            "questions_attempted": 6,
            "correct": 3,
            "teacher_signal": None,
            "trouble_spots": ["altering numerator without proportionally scaling denominator"]
        }
        update_grade4_math_session(
            state,
            sess2_data,
            trouble_spots=["altering numerator without proportionally scaling denominator"]
        )

        # =========================================================================
        # STEP 3 — CLEAR IMPROVEMENT (Equivalent Fractions)
        # =========================================================================
        signals_step3 = {
            "session_id": "sess_103",
            "date": "2026-09-03",
            "topic": "Equivalent Fractions",
            "questions_attempted": 8,
            "correct_answers": 7,
            "correctness": 0.875,
            "observed_behavior": [
                "Student correctly generates equivalent fractions (e.g. 2/3 = 4/6 = 6/9)",
                "Student explicitly explains why numerator and denominator must change proportionally",
                "Previous scaling misconception is no longer observed"
            ],
            "student_notes": "Strong performance, clear conceptual explanation of proportional scaling."
        }

        diag3 = analyze_progress_local(
            grade=4,
            subject="Math",
            current_topic="Equivalent Fractions",
            latest_signals=signals_step3
        )
        diagnoses[3] = diag3
        print_step_output(3, "Clear Improvement (Equivalent Fractions)", diag3)

        # Update state after Step 3
        sess3_data = {
            "session_id": "sess_103",
            "date": "2026-09-03",
            "topic": "Equivalent Fractions",
            "result": 88,
            "correctness": 0.875,
            "completion": 1.0,
            "questions_attempted": 8,
            "correct": 7,
            "teacher_signal": None,
            "trouble_spots": []
        }
        update_grade4_math_session(state, sess3_data)

        # =========================================================================
        # STEP 4 — POSITIVE TEACHER SIGNAL
        # =========================================================================
        signals_step4 = {
            "session_id": "sess_104",
            "date": "2026-09-04",
            "topic": "Equivalent Fractions",
            "teacher_signal": "went well",
            "teacher_observation": "Teacher recorded 'went well' for Equivalent Fractions practice session.",
            "correctness": 0.875,
            "questions_attempted": 8,
            "correct_answers": 7
        }

        diag4 = analyze_progress_local(
            grade=4,
            subject="Math",
            current_topic="Equivalent Fractions",
            latest_signals=signals_step4
        )
        diagnoses[4] = diag4
        print_step_output(4, "Positive Teacher Signal ('went well')", diag4)

        # Update state after Step 4
        sess4_data = {
            "session_id": "sess_104",
            "date": "2026-09-04",
            "topic": "Equivalent Fractions",
            "result": 88,
            "correctness": 0.875,
            "completion": 1.0,
            "teacher_signal": "went well",
            "trouble_spots": []
        }
        update_grade4_math_session(state, sess4_data)

        # =========================================================================
        # STEP 5 — NEGATIVE TEACHER SIGNAL AFTER APPARENT MASTERY
        # =========================================================================
        signals_step5 = {
            "session_id": "sess_105",
            "date": "2026-09-05",
            "topic": "Equivalent Fractions",
            "questions_attempted": 5,
            "correct_answers": 2,
            "correctness": 0.4,
            "teacher_signal": "struggled",
            "error_patterns": [
                "Reverted to equivalent-fraction errors, changing numerator without proportionally multiplying denominator",
                "Teacher explicitly recorded 'struggled'"
            ],
            "student_notes": "Student struggled during review; 2 of 5 correct, repeated scaling error returned."
        }

        diag5 = analyze_progress_local(
            grade=4,
            subject="Math",
            current_topic="Equivalent Fractions",
            latest_signals=signals_step5
        )
        diagnoses[5] = diag5
        print_step_output(5, "Negative Teacher Signal After Apparent Mastery", diag5)

        # Update state after Step 5
        sess5_data = {
            "session_id": "sess_105",
            "date": "2026-09-05",
            "topic": "Equivalent Fractions",
            "result": 40,
            "correctness": 0.4,
            "completion": 1.0,
            "questions_attempted": 5,
            "correct": 2,
            "teacher_signal": "struggled",
            "trouble_spots": ["reverted to altering numerator without proportionally scaling denominator"]
        }
        update_grade4_math_session(
            state,
            sess5_data,
            trouble_spots=["reverted to altering numerator without proportionally scaling denominator"]
        )

        # =========================================================================
        # STEP 6 — NEW, UNRELATED TOPIC (Decimals)
        # =========================================================================
        signals_step6 = {
            "session_id": "sess_106",
            "date": "2026-09-06",
            "topic": "Decimals",
            "questions_attempted": 6,
            "correct_answers": 5,
            "correctness": 0.833,
            "error_patterns": [],
            "observed_behavior": [
                "Student demonstrated solid understanding of decimal place values and representations",
                "No equivalent-fraction errors were observed"
            ],
            "student_notes": "First session on Decimals. 5 of 6 correct. Clean performance."
        }

        diag6 = analyze_progress_local(
            grade=4,
            subject="Math",
            current_topic="Decimals",
            latest_signals=signals_step6
        )
        diagnoses[6] = diag6
        print_step_output(6, "New Unrelated Topic (Decimals)", diag6)

        return diagnoses

    finally:
        # Restore backup state
        if BACKUP_FILE.exists():
            shutil.copy(BACKUP_FILE, DATA_FILE)
            BACKUP_FILE.unlink()


if __name__ == "__main__":
    run_timeline_test()
