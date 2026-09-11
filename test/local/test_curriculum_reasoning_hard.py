"""
test/local/test_curriculum_reasoning_hard.py
---------------------------------
Hard real-world curriculum reasoning test suite for Saarthi Curriculum Agent (GPT-OSS-120B via Groq API).

Focuses exclusively on the most complex, borderline scenarios where simple heuristics fail.
Requires nuanced weighing of prerequisite dependencies vs. pacing pressure vs. mastery trends.
"""

import sys
import json
from pathlib import Path

# Ensure stdout uses UTF-8 to prevent Windows cp1252 encoding crashes
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.local_ollama import reconcile_curriculum_local
import time


def safe_reconcile(*args, **kwargs):
    for attempt in range(3):
        try:
            return reconcile_curriculum_local(*args, **kwargs)
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2)



def run_hard_curriculum_tests():
    outputs = {}

    # =========================================================================
    # SCENARIO 1 — BROKEN DIRECT PREREQUISITE + EXAM PRESSURE
    # =========================================================================
    ctx_1 = {
        "grade": "4",
        "subject": "Math",
        "current_topic": "Equivalent Fractions",
        "syllabus_target": "Multiplying fractions",
        "prerequisites": "Equivalent Fractions is a DIRECT prerequisite for Multiplying fractions.",
        "progress_diagnosis": {
            "grade": "4",
            "subject": "Math",
            "topic": "Equivalent Fractions",
            "mastery_estimate": "struggling",
            "trend": "stagnant",
            "confidence": "high",
            "trouble_spots": [
                "cannot reliably generate equivalent fractions",
                "changes numerator without proportional denominator change"
            ],
            "recommendation_direction": "reteach"
        },
        "session_constraints": {"available_time": "40m"},
        "teacher_constraints": {"exam_deadline": "Multiplying fractions exam is in 3 days. We still need to make progress toward the exam."}
    }
    print("=" * 80)
    print("SCENARIO 1 — BROKEN DIRECT PREREQUISITE + EXAM PRESSURE")
    print("=" * 80)
    print("INPUT CONTEXT:")
    print(json.dumps(ctx_1, indent=2))
    print("\nAGENT OUTPUT:")
    res_1 = safe_reconcile(
        grade="4",
        subject="Math",
        current_topic="Equivalent Fractions",
        progress_diagnosis=ctx_1["progress_diagnosis"],
        session_constraints=ctx_1["session_constraints"],
        teacher_constraints=ctx_1["teacher_constraints"]
    )
    outputs[1] = res_1
    print(json.dumps(res_1, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 2 — NON-BLOCKING TROUBLE
    # =========================================================================
    ctx_2 = {
        "grade": "5",
        "subject": "Math",
        "current_topic": "Decimals - multiplication",
        "syllabus_target": "Decimals - multiplication",
        "prerequisites": "Decimal Multiplication requires place value, multiplication, decimal addition/subtraction (all mastered). Word-problem wording misreading is explicitly NOT a prerequisite blocker.",
        "progress_diagnosis": {
            "grade": "5",
            "subject": "Math",
            "topic": "Decimals - multiplication",
            "mastery_estimate": "proficient",
            "trend": "stable",
            "confidence": "high",
            "trouble_spots": ["occasionally misreads word-problem wording"],
            "recommendation_direction": "advance"
        },
        "session_constraints": {"available_time": "45m"},
        "teacher_constraints": {"directive": "Stay on syllabus."}
    }
    print("=" * 80)
    print("SCENARIO 2 — NON-BLOCKING TROUBLE")
    print("=" * 80)
    print("INPUT CONTEXT:")
    print(json.dumps(ctx_2, indent=2))
    print("\nAGENT OUTPUT:")
    res_2 = safe_reconcile(
        grade="5",
        subject="Math",
        current_topic="Decimals - multiplication",
        progress_diagnosis=ctx_2["progress_diagnosis"],
        session_constraints=ctx_2["session_constraints"],
        teacher_constraints=ctx_2["teacher_constraints"]
    )
    outputs[2] = res_2
    print(json.dumps(res_2, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 3 — IMPROVING DIRECT PREREQUISITE
    # =========================================================================
    ctx_3 = {
        "grade": "6",
        "subject": "Math",
        "current_topic": "Fractions - adding with unlike denominators",
        "syllabus_target": "Fractions - subtracting with unlike denominators",
        "prerequisites": "Adding Fractions with Unlike Denominators is a DIRECT prerequisite for Subtracting Fractions with Unlike Denominators.",
        "progress_diagnosis": {
            "grade": "6",
            "subject": "Math",
            "topic": "Fractions - adding with unlike denominators",
            "mastery_estimate": "developing",
            "trend": "improving",
            "confidence": "medium",
            "trouble_spots": ["occasional LCM errors", "occasional numerator conversion errors"],
            "recommendation_direction": "reinforce"
        },
        "session_constraints": {"available_time": "40m"},
        "teacher_constraints": {}
    }
    print("=" * 80)
    print("SCENARIO 3 — IMPROVING DIRECT PREREQUISITE")
    print("=" * 80)
    print("INPUT CONTEXT:")
    print(json.dumps(ctx_3, indent=2))
    print("\nAGENT OUTPUT:")
    res_3 = safe_reconcile(
        grade="6",
        subject="Math",
        current_topic="Fractions - adding with unlike denominators",
        progress_diagnosis=ctx_3["progress_diagnosis"],
        session_constraints=ctx_3["session_constraints"],
        teacher_constraints=ctx_3["teacher_constraints"]
    )
    outputs[3] = res_3
    print(json.dumps(res_3, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 4 — SAME LEARNING STATE, DIFFERENT TIME (4A: 15m, 4B: 60m)
    # =========================================================================
    ctx_4a = {
        "grade": "7",
        "subject": "Math",
        "current_topic": "Integer operations",
        "syllabus_target": "Linear equations",
        "prerequisites": "Integer Operations is a DIRECT prerequisite for Linear equations.",
        "progress_diagnosis": {
            "grade": "7",
            "subject": "Math",
            "topic": "Integer operations",
            "mastery_estimate": "developing",
            "trend": "improving",
            "confidence": "medium",
            "trouble_spots": ["negative-number arithmetic errors"],
            "recommendation_direction": "reinforce"
        },
        "session_constraints": {"available_time": "15m"},
        "teacher_constraints": {}
    }
    ctx_4b = dict(ctx_4a)
    ctx_4b["session_constraints"] = {"available_time": "60m"}

    print("=" * 80)
    print("SCENARIO 4A — SAME LEARNING STATE, 15 MINUTES AVAILABLE TIME")
    print("=" * 80)
    print("INPUT CONTEXT:")
    print(json.dumps(ctx_4a, indent=2))
    print("\nAGENT OUTPUT:")
    res_4a = safe_reconcile(
        grade="7",
        subject="Math",
        current_topic="Integer operations",
        progress_diagnosis=ctx_4a["progress_diagnosis"],
        session_constraints=ctx_4a["session_constraints"],
        teacher_constraints=ctx_4a["teacher_constraints"]
    )
    outputs["4A"] = res_4a
    print(json.dumps(res_4a, indent=2))
    print("\n")

    print("=" * 80)
    print("SCENARIO 4B — SAME LEARNING STATE, 60 MINUTES AVAILABLE TIME")
    print("=" * 80)
    print("INPUT CONTEXT:")
    print(json.dumps(ctx_4b, indent=2))
    print("\nAGENT OUTPUT:")
    res_4b = safe_reconcile(
        grade="7",
        subject="Math",
        current_topic="Integer operations",
        progress_diagnosis=ctx_4b["progress_diagnosis"],
        session_constraints=ctx_4b["session_constraints"],
        teacher_constraints=ctx_4b["teacher_constraints"]
    )
    outputs["4B"] = res_4b
    print(json.dumps(res_4b, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 5 — TEACHER PRIORITY VS LEARNING GAP
    # =========================================================================
    ctx_5 = {
        "grade": "8",
        "subject": "Math",
        "current_topic": "Linear equations",
        "syllabus_target": "Linear equations",
        "prerequisites": "Integer Operations is a prerequisite (mastered). Sign/transposition errors are topic-specific errors.",
        "progress_diagnosis": {
            "grade": "8",
            "subject": "Math",
            "topic": "Linear equations",
            "mastery_estimate": "developing",
            "trend": "stagnant",
            "confidence": "high",
            "trouble_spots": ["sign/transposition errors"],
            "recommendation_direction": "reteach"
        },
        "session_constraints": {"available_time": "45m"},
        "teacher_constraints": {"exam_deadline": "External exam is tomorrow. We MUST cover Linear Equations today. Do not spend the entire session reteaching."}
    }
    print("=" * 80)
    print("SCENARIO 5 — TEACHER PRIORITY VS LEARNING GAP")
    print("=" * 80)
    print("INPUT CONTEXT:")
    print(json.dumps(ctx_5, indent=2))
    print("\nAGENT OUTPUT:")
    res_5 = safe_reconcile(
        grade="8",
        subject="Math",
        current_topic="Linear equations",
        progress_diagnosis=ctx_5["progress_diagnosis"],
        session_constraints=ctx_5["session_constraints"],
        teacher_constraints=ctx_5["teacher_constraints"]
    )
    outputs[5] = res_5
    print(json.dumps(res_5, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 6 — HISTORICAL STABILITY VS ONE BAD SESSION
    # =========================================================================
    ctx_6 = {
        "grade": "6",
        "subject": "Math",
        "current_topic": "Fractions - adding with unlike denominators",
        "syllabus_target": "Fractions - subtracting with unlike denominators",
        "prerequisites": "Adding Fractions with Unlike Denominators is a prerequisite for Subtracting Fractions.",
        "progress_diagnosis": {
            "grade": "6",
            "subject": "Math",
            "topic": "Fractions - adding with unlike denominators",
            "mastery_estimate": "proficient",
            "trend": "declining",
            "confidence": "medium",
            "trouble_spots": ["denominator comparison errors"],
            "historical_context": "Previous 4 sessions were consistently proficient. Latest session showed one sudden performance drop.",
            "recommendation_direction": "reinforce"
        },
        "session_constraints": {"available_time": "50m"},
        "teacher_constraints": {"teacher_observation": "Yesterday they were doing fine. Today they seemed confused."}
    }
    print("=" * 80)
    print("SCENARIO 6 — HISTORICAL STABILITY VS ONE BAD SESSION")
    print("=" * 80)
    print("INPUT CONTEXT:")
    print(json.dumps(ctx_6, indent=2))
    print("\nAGENT OUTPUT:")
    res_6 = safe_reconcile(
        grade="6",
        subject="Math",
        current_topic="Fractions - adding with unlike denominators",
        progress_diagnosis=ctx_6["progress_diagnosis"],
        session_constraints=ctx_6["session_constraints"],
        teacher_constraints=ctx_6["teacher_constraints"]
    )
    outputs[6] = res_6
    print(json.dumps(res_6, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 7 — TRUE PREREQUISITE VS UNRELATED WEAKNESS
    # =========================================================================
    ctx_7 = {
        "grade": "5",
        "subject": "Math",
        "current_topic": "Multiplication",
        "syllabus_target": "Area of Rectangles",
        "prerequisites": "Multiplication fluency is a prerequisite for Area. Verbal explanation ability is explicitly NOT required for Area.",
        "progress_diagnosis": {
            "grade": "5",
            "subject": "Math",
            "topic": "Multiplication",
            "mastery_estimate": "proficient",
            "trend": "stable",
            "confidence": "high",
            "trouble_spots": ["weak verbal explanation of multiplication"],
            "recommendation_direction": "advance"
        },
        "session_constraints": {"available_time": "40m"},
        "teacher_constraints": {"directive": "Continue with the syllabus."}
    }
    print("=" * 80)
    print("SCENARIO 7 — TRUE PREREQUISITE VS UNRELATED WEAKNESS")
    print("=" * 80)
    print("INPUT CONTEXT:")
    print(json.dumps(ctx_7, indent=2))
    print("\nAGENT OUTPUT:")
    res_7 = safe_reconcile(
        grade="5",
        subject="Math",
        current_topic="Multiplication",
        progress_diagnosis=ctx_7["progress_diagnosis"],
        session_constraints=ctx_7["session_constraints"],
        teacher_constraints=ctx_7["teacher_constraints"]
    )
    outputs[7] = res_7
    print(json.dumps(res_7, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 8 — NO PREREQUISITE BLOCKER BUT LOW MASTERY
    # =========================================================================
    ctx_8 = {
        "grade": "4",
        "subject": "Math",
        "current_topic": "Geometry vocabulary",
        "syllabus_target": "Geometry: Angles",
        "prerequisites": "No direct prerequisite is required for Geometry: Angles.",
        "progress_diagnosis": {
            "grade": "4",
            "subject": "Math",
            "topic": "Geometry vocabulary",
            "mastery_estimate": "developing",
            "trend": "improving",
            "confidence": "medium",
            "trouble_spots": ["vocabulary confusion"],
            "recommendation_direction": "reinforce"
        },
        "session_constraints": {"available_time": "40m"},
        "teacher_constraints": {"directive": "We need to stay roughly on syllabus."}
    }
    print("=" * 80)
    print("SCENARIO 8 — NO PREREQUISITE BLOCKER BUT LOW MASTERY")
    print("=" * 80)
    print("INPUT CONTEXT:")
    print(json.dumps(ctx_8, indent=2))
    print("\nAGENT OUTPUT:")
    res_8 = safe_reconcile(
        grade="4",
        subject="Math",
        current_topic="Geometry vocabulary",
        progress_diagnosis=ctx_8["progress_diagnosis"],
        session_constraints=ctx_8["session_constraints"],
        teacher_constraints=ctx_8["teacher_constraints"]
    )
    outputs[8] = res_8
    print(json.dumps(res_8, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 9 — TEACHER DEADLINE WITH TRUE PREREQUISITE FAILURE
    # =========================================================================
    ctx_9 = {
        "grade": "6",
        "subject": "Math",
        "current_topic": "Fraction equivalence",
        "syllabus_target": "Ratio and Proportion",
        "prerequisites": "Fraction equivalence is a DIRECT prerequisite for Ratio and Proportion.",
        "progress_diagnosis": {
            "grade": "6",
            "subject": "Math",
            "topic": "Fraction equivalence",
            "mastery_estimate": "struggling",
            "trend": "stagnant",
            "confidence": "high",
            "trouble_spots": ["cannot identify equivalent fractions"],
            "recommendation_direction": "reteach"
        },
        "session_constraints": {"available_time": "45m"},
        "teacher_constraints": {"exam_deadline": "District assessment is tomorrow. We have to at least introduce Ratio and Proportion today."}
    }
    print("=" * 80)
    print("SCENARIO 9 — TEACHER DEADLINE WITH TRUE PREREQUISITE FAILURE")
    print("=" * 80)
    print("INPUT CONTEXT:")
    print(json.dumps(ctx_9, indent=2))
    print("\nAGENT OUTPUT:")
    res_9 = safe_reconcile(
        grade="6",
        subject="Math",
        current_topic="Fraction equivalence",
        progress_diagnosis=ctx_9["progress_diagnosis"],
        session_constraints=ctx_9["session_constraints"],
        teacher_constraints=ctx_9["teacher_constraints"]
    )
    outputs[9] = res_9
    print(json.dumps(res_9, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 10 — CONFLICTING TEACHER AND PROGRESS SIGNAL
    # =========================================================================
    ctx_10 = {
        "grade": "4",
        "subject": "Math",
        "current_topic": "Equivalent Fractions",
        "syllabus_target": "Multiplying fractions",
        "prerequisites": "Equivalent Fractions is a DIRECT prerequisite for Multiplying fractions.",
        "progress_diagnosis": {
            "grade": "4",
            "subject": "Math",
            "topic": "Equivalent Fractions",
            "mastery_estimate": "developing",
            "trend": "improving",
            "confidence": "medium",
            "trouble_spots": ["occasional equivalent-fraction errors"],
            "recommendation_direction": "reinforce"
        },
        "session_constraints": {"available_time": "40m"},
        "teacher_constraints": {"teacher_opinion": "I think they are ready. Let's move forward."}
    }
    print("=" * 80)
    print("SCENARIO 10 — CONFLICTING TEACHER AND PROGRESS SIGNAL")
    print("=" * 80)
    print("INPUT CONTEXT:")
    print(json.dumps(ctx_10, indent=2))
    print("\nAGENT OUTPUT:")
    res_10 = safe_reconcile(
        grade="4",
        subject="Math",
        current_topic="Equivalent Fractions",
        progress_diagnosis=ctx_10["progress_diagnosis"],
        session_constraints=ctx_10["session_constraints"],
        teacher_constraints=ctx_10["teacher_constraints"]
    )
    outputs[10] = res_10
    print(json.dumps(res_10, indent=2))
    print("\n")

    return outputs


if __name__ == "__main__":
    run_hard_curriculum_tests()
