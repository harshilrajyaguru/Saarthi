"""
test/local/retest_curriculum_5.py
---------------------------------
Retest script for the 5 previously problematic Curriculum Agent scenarios following prompt grounding fixes.
Executes:
  - Scenario 4A (15m time sensitivity)
  - Scenario 4B (60m time sensitivity)
  - Scenario 5 (No invented prerequisites)
  - Scenario 6 (Declared prerequisite reasoning only)
  - Scenario 7 (Custom topic preservation: Multiplication -> Area of Rectangles)
  - Scenario 8 (Custom topic preservation & weakness != blocker: Geometry vocabulary -> Geometry: Angles)
"""

import sys
import json
import time
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


def safe_reconcile(*args, **kwargs):
    for attempt in range(3):
        try:
            return reconcile_curriculum_local(*args, **kwargs)
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2)


def run_retest_5():
    outputs = {}

    # =========================================================================
    # RETEST SCENARIO 4A — TIME SENSITIVITY (15 MINUTES)
    # =========================================================================
    ctx_4a = {
        "grade": "7",
        "subject": "Math",
        "current_topic": "Integer operations",
        "syllabus_target": "Linear equations",
        "prerequisites": "Integer Operations is a DIRECT prerequisite for Linear Equations.",
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
    print("=" * 80)
    print("RETEST SCENARIO 4A — TIME SENSITIVITY (15 MINUTES)")
    print("=" * 80)
    print("INPUT CONTEXT:")
    print(json.dumps(ctx_4a, indent=2))
    print("\nFULL AGENT OUTPUT:")
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

    # =========================================================================
    # RETEST SCENARIO 4B — TIME SENSITIVITY (60 MINUTES)
    # =========================================================================
    ctx_4b = dict(ctx_4a)
    ctx_4b["session_constraints"] = {"available_time": "60m"}

    print("=" * 80)
    print("RETEST SCENARIO 4B — TIME SENSITIVITY (60 MINUTES)")
    print("=" * 80)
    print("INPUT CONTEXT:")
    print(json.dumps(ctx_4b, indent=2))
    print("\nFULL AGENT OUTPUT:")
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
    # RETEST SCENARIO 5 — INVENTED PREREQUISITE
    # =========================================================================
    ctx_5 = {
        "grade": "8",
        "subject": "Math",
        "current_topic": "Linear equations",
        "syllabus_target": "Linear equations",
        "prerequisites": "Integer Operations is a prerequisite (mastered). Sign/transposition errors are topic-specific errors, NOT declared as a prerequisite relationship.",
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
    print("RETEST SCENARIO 5 — INVENTED PREREQUISITE")
    print("=" * 80)
    print("INPUT CONTEXT:")
    print(json.dumps(ctx_5, indent=2))
    print("\nFULL AGENT OUTPUT:")
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
    # RETEST SCENARIO 6 — INVENTED LCM PREREQUISITE
    # =========================================================================
    ctx_6 = {
        "grade": "6",
        "subject": "Math",
        "current_topic": "Adding Fractions with Unlike Denominators",
        "syllabus_target": "Subtracting Fractions with Unlike Denominators",
        "prerequisites": "Adding Fractions with Unlike Denominators is the ONLY declared prerequisite for Subtracting Fractions.",
        "progress_diagnosis": {
            "grade": "6",
            "subject": "Math",
            "topic": "Adding Fractions with Unlike Denominators",
            "mastery_estimate": "proficient",
            "trend": "declining",
            "confidence": "medium",
            "trouble_spots": ["denominator comparison errors"],
            "historical_context": "Previous 4 sessions were consistently proficient. Latest session had one sudden performance drop.",
            "recommendation_direction": "reinforce"
        },
        "session_constraints": {"available_time": "50m"},
        "teacher_constraints": {"teacher_observation": "Yesterday they were doing fine. Today they seemed confused."}
    }
    print("=" * 80)
    print("RETEST SCENARIO 6 — INVENTED LCM PREREQUISITE")
    print("=" * 80)
    print("INPUT CONTEXT:")
    print(json.dumps(ctx_6, indent=2))
    print("\nFULL AGENT OUTPUT:")
    res_6 = safe_reconcile(
        grade="6",
        subject="Math",
        current_topic="Adding Fractions with Unlike Denominators",
        progress_diagnosis=ctx_6["progress_diagnosis"],
        session_constraints=ctx_6["session_constraints"],
        teacher_constraints=ctx_6["teacher_constraints"]
    )
    outputs[6] = res_6
    print(json.dumps(res_6, indent=2))
    print("\n")

    # =========================================================================
    # RETEST SCENARIO 7 — CUSTOM TOPIC PRESERVATION
    # =========================================================================
    ctx_7 = {
        "grade": "5",
        "subject": "Math",
        "current_topic": "Multiplication",
        "syllabus_target": "Area of Rectangles",
        "prerequisites": "Multiplication fluency is a prerequisite for Area of Rectangles. Verbal explanation ability is explicitly NOT required.",
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
    print("RETEST SCENARIO 7 — CUSTOM TOPIC PRESERVATION")
    print("=" * 80)
    print("INPUT CONTEXT:")
    print(json.dumps(ctx_7, indent=2))
    print("\nFULL AGENT OUTPUT:")
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
    # RETEST SCENARIO 8 — CUSTOM TOPIC PRESERVATION + NO BLOCKER
    # =========================================================================
    ctx_8 = {
        "grade": "4",
        "subject": "Math",
        "current_topic": "Geometry vocabulary",
        "syllabus_target": "Geometry: Angles",
        "prerequisites": "NO direct prerequisite is required for Geometry: Angles.",
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
    print("RETEST SCENARIO 8 — CUSTOM TOPIC PRESERVATION + NO BLOCKER")
    print("=" * 80)
    print("INPUT CONTEXT:")
    print(json.dumps(ctx_8, indent=2))
    print("\nFULL AGENT OUTPUT:")
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

    return outputs


if __name__ == "__main__":
    run_retest_5()
