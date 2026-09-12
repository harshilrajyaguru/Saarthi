import json
import traceback

from tools.progress_tools import get_history, get_trouble_spot_log
from agents.progress_agent import (
    apply_hard_guardrails,
    analyze_progress
)


def run_unit_and_guardrail_tests():
    print("=" * 60)
    print("STEP 1: VERIFYING STRANDS TOOLS & DETERMINISTIC GUARDRAILS")
    print("=" * 60)

    # 1. Test get_history
    hist_g3 = get_history(grade=3, subject="Math", topic="Fractions", n=3)
    print(f"\n[Tool Test] get_history(Grade 3, Math): count={hist_g3['count']}")
    assert hist_g3["count"] == 1, f"Expected 1 session for Grade 3 Math, got {hist_g3['count']}"

    hist_g4 = get_history(grade=4, subject="Math", topic="Fractions", n=3)
    print(f"[Tool Test] get_history(Grade 4, Math): count={hist_g4['count']}")
    assert hist_g4["count"] == 3, f"Expected 3 sessions for Grade 4 Math, got {hist_g4['count']}"

    # 2. Test get_trouble_spot_log
    log_g4 = get_trouble_spot_log(grade=4, subject="Math")
    print(f"[Tool Test] get_trouble_spot_log(Grade 4, Math): {log_g4['trouble_spots']}")
    assert len(log_g4["trouble_spots"]) > 0, "Expected trouble spots for Grade 4 Math"

    # 3. Test Guardrail 1: Confidence forced to 'low' when history_count < 2
    mock_diag_1 = {
        "grade": "3",
        "subject": "Math",
        "topic": "Fractions",
        "mastery_estimate": "proficient",
        "trend": "improving",
        "confidence": "high",  # LLM overconfident
        "trouble_spots": [],
        "attention_flag": True,
        "recommendation_direction": "advance",
        "explanation": "Test explanation."
    }
    guarded_1 = apply_hard_guardrails(mock_diag_1, history_count=1)
    print("\n[Guardrail Test 1] History Count < 2:")
    print(f"  Input Confidence: 'high'  -> Guarded Confidence: '{guarded_1['confidence']}'")
    print(f"  Input Attention Flag: True -> Guarded Attention Flag: {guarded_1['attention_flag']}")
    assert guarded_1["confidence"] == "low", "Guardrail 1 failed: confidence should be 'low'"
    assert guarded_1["attention_flag"] == False, "Guardrail 2 failed: attention_flag must be False when confidence is low"

    # 4. Test Guardrail 2: attention_flag True allowed ONLY when trend in (stagnant, declining) AND confidence != low
    mock_diag_2 = {
        "grade": "4",
        "subject": "Math",
        "topic": "Fractions",
        "mastery_estimate": "struggling",
        "trend": "stagnant",
        "confidence": "medium",
        "trouble_spots": ["scaling numerator"],
        "attention_flag": True,
        "recommendation_direction": "reteach",
        "explanation": "Repeated error pattern over 3 sessions."
    }
    guarded_2 = apply_hard_guardrails(mock_diag_2, history_count=3)
    print("\n[Guardrail Test 2] Stagnant trend + Medium confidence:")
    print(f"  Guarded Attention Flag: {guarded_2['attention_flag']}")
    assert guarded_2["attention_flag"] == True, "Guardrail 2 failed: attention_flag should be True for stagnant + medium confidence"

    # 5. Test Guardrail 3: Boundary enforcement (no activity allowed)
    mock_diag_3 = {
        "grade": "4",
        "subject": "Math",
        "topic": "Fractions",
        "mastery_estimate": "developing",
        "trend": "stagnant",
        "confidence": "medium",
        "trouble_spots": [],
        "attention_flag": False,
        "recommendation_direction": "worksheet_practice",  # Invalid direction
        "activity": "Do 10 fraction worksheets",  # Illegal key
        "explanation": "Test illegal field."
    }
    guarded_3 = apply_hard_guardrails(mock_diag_3, history_count=3)
    print("\n[Guardrail Test 3] Agent Boundary & illegal keys:")
    print(f"  Guarded Direction: '{guarded_3['recommendation_direction']}'")
    print(f"  Contains 'activity' key: {'activity' in guarded_3}")
    assert guarded_3["recommendation_direction"] == "insufficient_data"
    assert "activity" not in guarded_3

    print("\nSUCCESS: All Strands tools and deterministic hard guardrail unit tests passed!\n")


def run_test_cases():
    print("=" * 60)
    print("STEP 2: RUNNING PROGRESS AGENT TEST CASES")
    print("=" * 60)

    test_scenarios = [
        {
            "name": "CASE 1: Single Historical Session (Grade 3 Math)",
            "grade": 3,
            "subject": "Math",
            "current_topic": "Fractions - introduction",
            "latest_signals": {
                "correctness": 0.65,
                "completion": 0.80,
                "time_on_task": "14m",
                "teacher_signal": "slightly_struggling"
            },
            "activity_metadata": {"activity_type": "practice_quiz", "difficulty": "medium"},
            "expected_notes": "confidence MUST be 'low', attention_flag MUST be False."
        },
        {
            "name": "CASE 2: Multiple Sessions with Repeated Error (Grade 4 Math)",
            "grade": 4,
            "subject": "Math",
            "current_topic": "Fractions - equivalent fractions",
            "latest_signals": {
                "correctness": 0.50,
                "completion": 0.60,
                "time_on_task": "16m",
                "teacher_signal": "struggling",
                "raw_errors": ["confusing numerator/denominator when scaling"]
            },
            "activity_metadata": {"activity_type": "fraction_scaling_worksheet", "difficulty": "medium"},
            "expected_notes": "Should identify repeated trouble spot; confidence medium/high; attention_flag adheres to guardrails."
        },
        {
            "name": "CASE 3: Improving Historical Performance (Grade 5 Math)",
            "grade": 5,
            "subject": "Math",
            "current_topic": "Decimals - addition",
            "latest_signals": {
                "correctness": 0.90,
                "completion": 1.0,
                "time_on_task": "10m",
                "teacher_signal": "on_track"
            },
            "activity_metadata": {"activity_type": "decimal_quiz", "difficulty": "medium"},
            "expected_notes": "trend = 'improving', recommendation_direction should NOT be 'reteach'."
        },
        {
            "name": "CASE 4: Single Bad Result After Good Sessions (Grade 6 Math)",
            "grade": 6,
            "subject": "Math",
            "current_topic": "Algebra - linear equations",
            "latest_signals": {
                "correctness": 0.45,
                "completion": 0.50,
                "time_on_task": "3m",
                "teacher_signal": "distracted"
            },
            "activity_metadata": {"activity_type": "timed_test", "difficulty": "hard"},
            "expected_notes": "Agent considers possible one-off anomaly rather than blindly declaring conceptual gap."
        },
        {
            "name": "CASE 5: Repeated Known Trouble Spot with Stagnant/Declining Evidence (Grade 4 English)",
            "grade": 4,
            "subject": "English",
            "current_topic": "Reading Comprehension",
            "latest_signals": {
                "correctness": 0.40,
                "completion": 0.60,
                "time_on_task": "18m",
                "teacher_signal": "declining"
            },
            "activity_metadata": {"activity_type": "passage_reading", "difficulty": "hard"},
            "expected_notes": "attention_flag can become True (history count >= 2, stagnant/declining trend, non-low confidence)."
        }
    ]

    for scenario in test_scenarios:
        print(f"\n--- Running {scenario['name']} ---")
        print(f"Expected: {scenario['expected_notes']}")
        try:
            diagnosis = analyze_progress(
                grade=scenario["grade"],
                subject=scenario["subject"],
                current_topic=scenario["current_topic"],
                latest_signals=scenario["latest_signals"],
                activity_metadata=scenario["activity_metadata"]
            )
            print("AGENT RESULT:")
            print(json.dumps(diagnosis, indent=2))
        except Exception as e:
            print("\n[REPORTED AWS / BEDROCK / STRANDS EXCEPTION]")
            print(f"Exception Type: {type(e).__name__}")
            print(f"Exception Message: {str(e)}")
            print("Full Traceback:")
            traceback.print_exc()


if __name__ == "__main__":
    run_unit_and_guardrail_tests()
    run_test_cases()
