"""
test_local_curriculum_reasoning.py
----------------------------------
Real-world curriculum reasoning test for Saarthi Curriculum Agent (Qwen3 8B via Ollama).

Tests 8 real-world classroom conflict scenarios to evaluate whether the Curriculum Agent
makes defensible curriculum decisions (advance, hold, branch) balancing syllabus pace,
prerequisites, time constraints, and teacher constraints.
"""

import sys
import json

# Ensure stdout uses UTF-8 to prevent Windows cp1252 encoding crashes
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from agents.local_ollama import reconcile_curriculum_local


def run_curriculum_reasoning_tests():
    results = {}

    # =========================================================================
    # SCENARIO 1 — SYLLABUS PRESSURE VS BROKEN PREREQUISITE
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 1 — SYLLABUS PRESSURE VS BROKEN PREREQUISITE")
    print("=" * 80)
    
    prog_1 = {
        "grade": "4",
        "subject": "Math",
        "topic": "Equivalent Fractions",
        "mastery_estimate": "struggling",
        "trend": "stagnant",
        "confidence": "high",
        "trouble_spots": [
            "cannot generate equivalent fractions reliably",
            "changes numerator without proportional denominator change"
        ],
        "attention_flag": True,
        "recommendation_direction": "reteach",
        "explanation": "Student is struggling with equivalent fractions, repeatedly changing numerator without scaling denominator."
    }
    sess_1 = {"available_time": "40m"}
    teach_1 = {"exam_deadline": "Class test on multiplying fractions is in 3 days."}

    res_1 = reconcile_curriculum_local(
        grade="4",
        subject="Math",
        current_topic="Equivalent Fractions",
        progress_diagnosis=prog_1,
        session_constraints=sess_1,
        teacher_constraints=teach_1
    )
    results[1] = res_1
    print(json.dumps(res_1, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 2 — SIDE ISSUE THAT SHOULD NOT BLOCK PROGRESS
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 2 — SIDE ISSUE THAT SHOULD NOT BLOCK PROGRESS")
    print("=" * 80)

    prog_2 = {
        "grade": "5",
        "subject": "Math",
        "topic": "Decimal multiplication",
        "mastery_estimate": "proficient",
        "trend": "improving",
        "confidence": "high",
        "trouble_spots": [
            "occasionally misreads word-problem language"
        ],
        "attention_flag": False,
        "recommendation_direction": "advance",
        "explanation": "All prerequisite skills (place value, decimal addition/subtraction, multiplication) are mastered. Word problem language misreading is minor."
    }
    sess_2 = {"available_time": "45m"}
    teach_2 = {"constraint": "Need to stay on syllabus because another assessment is next week."}

    res_2 = reconcile_curriculum_local(
        grade="5",
        subject="Math",
        current_topic="Decimal multiplication",
        progress_diagnosis=prog_2,
        session_constraints=sess_2,
        teacher_constraints=teach_2
    )
    results[2] = res_2
    print(json.dumps(res_2, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 3 — IMPROVING BUT NOT READY
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 3 — IMPROVING BUT NOT READY")
    print("=" * 80)

    prog_3 = {
        "grade": "6",
        "subject": "Math",
        "topic": "Adding fractions with unlike denominators",
        "mastery_estimate": "developing",
        "trend": "improving",
        "confidence": "medium",
        "trouble_spots": [
            "LCM errors still occur",
            "numerator conversion errors reduced significantly"
        ],
        "attention_flag": False,
        "recommendation_direction": "reinforce",
        "explanation": "Student shows improvement on fraction addition with unlike denominators, but LCM errors still occur."
    }
    sess_3 = {"available_time": "40m"}
    teach_3 = {}

    res_3 = reconcile_curriculum_local(
        grade="6",
        subject="Math",
        current_topic="Adding fractions with unlike denominators",
        progress_diagnosis=prog_3,
        session_constraints=sess_3,
        teacher_constraints=teach_3
    )
    results[3] = res_3
    print(json.dumps(res_3, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 4 — VERY LIMITED TIME
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 4 — VERY LIMITED TIME")
    print("=" * 80)

    prog_4 = {
        "grade": "7",
        "subject": "Math",
        "topic": "Integer operations",
        "mastery_estimate": "developing",
        "trend": "improving",
        "confidence": "medium",
        "trouble_spots": [
            "negative-number arithmetic"
        ],
        "attention_flag": False,
        "recommendation_direction": "reinforce",
        "explanation": "Student is developing integer operations skills, with persistent negative-number arithmetic gaps."
    }
    sess_4 = {"available_time": "15m"}
    teach_4 = {"constraint": "Only 15 minutes with this group today. We have to transition immediately afterward."}

    res_4 = reconcile_curriculum_local(
        grade="7",
        subject="Math",
        current_topic="Integer operations",
        progress_diagnosis=prog_4,
        session_constraints=sess_4,
        teacher_constraints=teach_4
    )
    results[4] = res_4
    print(json.dumps(res_4, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 5 — TEACHER EXPLICITLY OVERRIDES NORMAL PACE
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 5 — TEACHER EXPLICITLY OVERRIDES NORMAL PACE")
    print("=" * 80)

    prog_5 = {
        "grade": "8",
        "subject": "Math",
        "topic": "Linear equations",
        "mastery_estimate": "developing",
        "trend": "stagnant",
        "confidence": "high",
        "trouble_spots": [
            "transposition/sign errors"
        ],
        "attention_flag": True,
        "recommendation_direction": "reteach",
        "explanation": "Integer operations mastered. Transposition and sign errors persist in linear equations."
    }
    sess_5 = {"available_time": "45m"}
    teach_5 = {"exam_deadline": "External exam is tomorrow. We MUST cover linear equations today. Do not spend the whole session reteaching prerequisites."}

    res_5 = reconcile_curriculum_local(
        grade="8",
        subject="Math",
        current_topic="Linear equations",
        progress_diagnosis=prog_5,
        session_constraints=sess_5,
        teacher_constraints=teach_5
    )
    results[5] = res_5
    print(json.dumps(res_5, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 6 — MULTI-GRADE CONSTRAINT
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 6 — MULTI-GRADE CONSTRAINT")
    print("=" * 80)

    prog_6 = {
        "grade": "3",
        "subject": "Math",
        "topic": "Repeated Addition",
        "mastery_estimate": "developing",
        "trend": "improving",
        "confidence": "medium",
        "trouble_spots": [
            "repeated addition is still inconsistent"
        ],
        "attention_flag": False,
        "recommendation_direction": "reinforce",
        "explanation": "Student is developing repeated addition skills ahead of multiplication."
    }
    sess_6 = {
        "available_time": "20m",
        "total_classroom_session": "40m across Grade 3, 4, 5",
        "teacher_direct_attention_minutes": 20
    }
    teach_6 = {"context": "Teacher is simultaneously managing Grade 4 and Grade 5. Grade 3 gets 20m direct attention."}

    res_6 = reconcile_curriculum_local(
        grade="3",
        subject="Math",
        current_topic="Repeated Addition",
        progress_diagnosis=prog_6,
        session_constraints=sess_6,
        teacher_constraints=teach_6
    )
    results[6] = res_6
    print(json.dumps(res_6, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 7 — CONFLICTING SIGNALS
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 7 — CONFLICTING SIGNALS")
    print("=" * 80)

    prog_7 = {
        "grade": "6",
        "subject": "Math",
        "topic": "Fractions",
        "mastery_estimate": "proficient",
        "trend": "declining",
        "confidence": "medium",
        "trouble_spots": [
            "recent denominator comparison errors"
        ],
        "attention_flag": False,
        "recommendation_direction": "reinforce",
        "explanation": "Previous 4 sessions were consistently proficient. Latest session showed sudden drop. Teacher noted: 'Students seemed confused today, but yesterday they were doing fine.'"
    }
    sess_7 = {"available_time": "50m"}
    teach_7 = {"teacher_feedback": "Students seemed confused today, but yesterday they were doing fine."}

    res_7 = reconcile_curriculum_local(
        grade="6",
        subject="Math",
        current_topic="Fractions",
        progress_diagnosis=prog_7,
        session_constraints=sess_7,
        teacher_constraints=teach_7
    )
    results[7] = res_7
    print(json.dumps(res_7, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 8 — FALSE PREREQUISITE TRAP
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 8 — FALSE PREREQUISITE TRAP")
    print("=" * 80)

    prog_8 = {
        "grade": "5",
        "subject": "Math",
        "topic": "Multiplication",
        "mastery_estimate": "proficient",
        "trend": "stagnant",
        "confidence": "high",
        "trouble_spots": [
            "difficulty explaining multiplication verbally"
        ],
        "attention_flag": False,
        "recommendation_direction": "advance",
        "explanation": "Multiplication fluency is proficient. Verbal explanation ability is weak but not a mathematical prerequisite for Area calculation."
    }
    sess_8 = {"available_time": "40m"}
    teach_8 = {}

    res_8 = reconcile_curriculum_local(
        grade="5",
        subject="Math",
        current_topic="Multiplication",
        progress_diagnosis=prog_8,
        session_constraints=sess_8,
        teacher_constraints=teach_8
    )
    results[8] = res_8
    print(json.dumps(res_8, indent=2))
    print("\n")

    return results


if __name__ == "__main__":
    run_curriculum_reasoning_tests()
