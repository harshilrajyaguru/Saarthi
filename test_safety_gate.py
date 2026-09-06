import json
from pathlib import Path

from tools.safety_tools import get_safety_rules, verify_math_expression
from agents.safety_gate import evaluate_safety_gate, SafetyGateResult


CLASSROOM_STATE_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "classroom_state.json"
)


def run_tool_tests():
    print("=" * 60)
    print("STEP 1: VERIFYING SAFETY TOOLS")
    print("=" * 60)

    # 1. Test get_safety_rules
    rules = get_safety_rules()
    print(f"[Tool Test] get_safety_rules: banned_words={rules.get('banned_words')}")
    assert len(rules.get("banned_words", [])) >= 5

    # 2. Test verify_math_expression
    correct_res = verify_math_expression("Complete 1/2 = 2/4.")
    print(f"[Tool Test] verify_math_expression (valid): is_correct={correct_res.get('is_correct')}")
    assert correct_res.get("is_correct") == True

    incorrect_res = verify_math_expression("Complete 1/2 = 3/4.")
    print(f"[Tool Test] verify_math_expression (invalid): is_correct={incorrect_res.get('is_correct')}, errors={incorrect_res.get('errors')}")
    assert incorrect_res.get("is_correct") == False
    assert len(incorrect_res.get("errors", [])) > 0

    print("\nSUCCESS: All Safety tools verified!\n")


def run_safety_gate_tests():
    print("=" * 60)
    print("STEP 2: RUNNING SAFETY/QUALITY GATE SCENARIOS")
    print("=" * 60)

    mtime_before = CLASSROOM_STATE_PATH.stat().st_mtime if CLASSROOM_STATE_PATH.exists() else None

    # Base valid activity payload
    valid_activity = {
        "grade": "3",
        "subject": "Math",
        "topic": "Equivalent fractions",
        "activity_type": "printable_worksheet",
        "targets_trouble_spot": "confusing numerator/denominator when scaling",
        "difficulty_level": "standard",
        "content": {
            "instructions": "Analyze student statements for fraction scaling errors and complete equivalent pairs with explanation.",
            "items": [
                "A student says 2/3 becomes 4/3 when scaling to an equivalent fraction. Is the student correct? Explain why or why not.",
                "Complete 2/3 = ?/6 and explain what happened to BOTH the numerator and denominator."
            ]
        },
        "estimated_time_minutes": 12
    }

    # TEST 1: Valid activity -> PASS
    print("\n--- Running TEST 1: Valid activity -> PASS ---")
    res1 = evaluate_safety_gate(valid_activity, decided_topic="Equivalent fractions", targets_trouble_spot="confusing numerator/denominator when scaling", available_time_minutes=15)
    print("GATE RESULT:", json.dumps(res1.model_dump(), indent=2))
    assert res1.passed == True
    assert res1.layer_failed is None
    assert res1.action == "pass"
    print("VERIFIED TEST 1: Valid activity passed all 3 layers!")

    # TEST 2: Missing instructions -> hard reject (Layer 1)
    print("\n--- Running TEST 2: Missing instructions -> hard reject (Layer 1) ---")
    act2 = json.loads(json.dumps(valid_activity))
    act2["content"]["instructions"] = ""
    res2 = evaluate_safety_gate(act2, decided_topic="Equivalent fractions", targets_trouble_spot="confusing numerator/denominator when scaling", available_time_minutes=15)
    print("GATE RESULT:", json.dumps(res2.model_dump(), indent=2))
    assert res2.passed == False
    assert res2.layer_failed == "layer_1"
    assert res2.action == "reject_and_regenerate"
    assert any(i.check == "missing_instructions" for i in res2.issues)
    print("VERIFIED TEST 2: Missing instructions caught in Layer 1!")

    # TEST 3: Empty items -> hard reject (Layer 1)
    print("\n--- Running TEST 3: Empty items -> hard reject (Layer 1) ---")
    act3 = json.loads(json.dumps(valid_activity))
    act3["content"]["items"] = []
    res3 = evaluate_safety_gate(act3, decided_topic="Equivalent fractions", targets_trouble_spot="confusing numerator/denominator when scaling", available_time_minutes=15)
    print("GATE RESULT:", json.dumps(res3.model_dump(), indent=2))
    assert res3.passed == False
    assert res3.layer_failed == "layer_1"
    assert res3.action == "reject_and_regenerate"
    assert any(i.check == "empty_items" for i in res3.issues)
    print("VERIFIED TEST 3: Empty items caught in Layer 1!")

    # TEST 4: Banned content -> hard reject (Layer 1)
    print("\n--- Running TEST 4: Banned content -> hard reject (Layer 1) ---")
    act4 = json.loads(json.dumps(valid_activity))
    act4["content"]["items"].append("A student plays a gambling game with fraction cards.")
    res4 = evaluate_safety_gate(act4, decided_topic="Equivalent fractions", targets_trouble_spot="confusing numerator/denominator when scaling", available_time_minutes=15)
    print("GATE RESULT:", json.dumps(res4.model_dump(), indent=2))
    assert res4.passed == False
    assert res4.layer_failed == "layer_1"
    assert res4.action == "reject_and_regenerate"
    assert any(i.check == "banned_content" for i in res4.issues)
    print("VERIFIED TEST 4: Banned content ('gambling') caught in Layer 1!")

    # TEST 5: Excessive reading complexity -> hard reject (Layer 1)
    print("\n--- Running TEST 5: Excessive reading complexity -> hard reject (Layer 1) ---")
    act5 = json.loads(json.dumps(valid_activity))
    act5["content"]["items"].append("Supercalifragilisticexpialidocious interdepartmental disproportionateness multidimensionality internationalization.")
    res5 = evaluate_safety_gate(act5, decided_topic="Equivalent fractions", targets_trouble_spot="confusing numerator/denominator when scaling", available_time_minutes=15)
    print("GATE RESULT:", json.dumps(res5.model_dump(), indent=2))
    assert res5.passed == False
    assert res5.layer_failed == "layer_1"
    assert res5.action == "reject_and_regenerate"
    assert any(i.check == "excessive_reading_complexity" for i in res5.issues)
    print("VERIFIED TEST 5: Excessive reading complexity caught in Layer 1!")

    # TEST 6: Activity exceeds available time -> hard reject (Layer 1)
    print("\n--- Running TEST 6: Activity exceeds available time -> hard reject (Layer 1) ---")
    act6 = json.loads(json.dumps(valid_activity))
    act6["estimated_time_minutes"] = 35
    res6 = evaluate_safety_gate(act6, decided_topic="Equivalent fractions", targets_trouble_spot="confusing numerator/denominator when scaling", available_time_minutes=15)
    print("GATE RESULT:", json.dumps(res6.model_dump(), indent=2))
    assert res6.passed == False
    assert res6.layer_failed == "layer_1"
    assert res6.action == "reject_and_regenerate"
    assert any(i.check == "time_limit_exceeded" for i in res6.issues)
    print("VERIFIED TEST 6: Exceeding available time caught in Layer 1!")

    # TEST 7: Wrong topic -> factual/alignment reject (Layer 2)
    print("\n--- Running TEST 7: Wrong topic -> alignment reject (Layer 2) ---")
    act7 = json.loads(json.dumps(valid_activity))
    act7["topic"] = "Multiplying fractions"
    res7 = evaluate_safety_gate(act7, decided_topic="Equivalent fractions", targets_trouble_spot="confusing numerator/denominator when scaling", available_time_minutes=15)
    print("GATE RESULT:", json.dumps(res7.model_dump(), indent=2))
    assert res7.passed == False
    assert res7.layer_failed == "layer_2"
    assert res7.action == "reject_and_regenerate"
    assert any(i.check == "topic_mismatch" for i in res7.issues)
    print("VERIFIED TEST 7: Topic mismatch caught in Layer 2!")

    # TEST 8: Wrong trouble spot -> alignment reject (Layer 2)
    print("\n--- Running TEST 8: Wrong trouble spot -> alignment reject (Layer 2) ---")
    act8 = json.loads(json.dumps(valid_activity))
    act8["targets_trouble_spot"] = "simplifying final fraction result"
    res8 = evaluate_safety_gate(act8, decided_topic="Equivalent fractions", targets_trouble_spot="confusing numerator/denominator when scaling", available_time_minutes=15)
    print("GATE RESULT:", json.dumps(res8.model_dump(), indent=2))
    assert res8.passed == False
    assert res8.layer_failed == "layer_2"
    assert res8.action == "reject_and_regenerate"
    assert any(i.check == "trouble_spot_mismatch" for i in res8.issues)
    print("VERIFIED TEST 8: Trouble spot mismatch caught in Layer 2!")

    # TEST 9: Incorrect Math answer -> factual reject (Layer 2)
    print("\n--- Running TEST 9: Incorrect Math answer -> factual reject (Layer 2) ---")
    act9 = json.loads(json.dumps(valid_activity))
    act9["content"]["items"].append("Complete 1/2 = 3/4.")
    res9 = evaluate_safety_gate(act9, decided_topic="Equivalent fractions", targets_trouble_spot="confusing numerator/denominator when scaling", available_time_minutes=15)
    print("GATE RESULT:", json.dumps(res9.model_dump(), indent=2))
    assert res9.passed == False
    assert res9.layer_failed == "layer_2"
    assert res9.action == "reject_and_regenerate"
    assert any(i.check == "incorrect_math_answer" for i in res9.issues)
    print("VERIFIED TEST 9: Programmatic math error (1/2 = 3/4) caught in Layer 2!")

    # TEST 10: Correct Math activity -> passes deterministic layers
    print("\n--- Running TEST 10: Correct Math activity -> passes deterministic layers ---")
    act10 = json.loads(json.dumps(valid_activity))
    act10["content"]["items"].append("Complete 2/4 = 4/8.")
    res10 = evaluate_safety_gate(act10, decided_topic="Equivalent fractions", targets_trouble_spot="confusing numerator/denominator when scaling", available_time_minutes=15)
    print("GATE RESULT:", json.dumps(res10.model_dump(), indent=2))
    assert res10.passed == True
    assert res10.layer_failed is None
    assert res10.action == "pass"
    print("VERIFIED TEST 10: Correct math activity passed all layers!")

    # TEST 11: Layer 3 nuance issue -> escalate_to_teacher
    print("\n--- Running TEST 11: Layer 3 nuance issue -> escalate_to_teacher ---")
    act11 = json.loads(json.dumps(valid_activity))
    act11["content"]["instructions"] += " Use culturally_insensitive stereotypes in fraction word problems."
    res11 = evaluate_safety_gate(act11, decided_topic="Equivalent fractions", targets_trouble_spot="confusing numerator/denominator when scaling", available_time_minutes=15)
    print("GATE RESULT:", json.dumps(res11.model_dump(), indent=2))
    assert res11.passed == False
    assert res11.layer_failed == "layer_3"
    assert res11.action == "escalate_to_teacher"
    assert any(i.check == "adversarial_nuance_issue" for i in res11.issues)
    print("VERIFIED TEST 11: Layer 3 subjective nuance issue escalated to teacher!")

    # TEST 12: Verify Layer 1 failure prevents Layer 2 & 3 execution
    print("\n--- Running TEST 12: Verify Layer 1 failure prevents Layer 2 & 3 ---")
    act12 = json.loads(json.dumps(valid_activity))
    act12["content"]["instructions"] = "" # Fail Layer 1
    act12["topic"] = "Wrong Topic" # Fail Layer 2
    res12 = evaluate_safety_gate(act12, decided_topic="Equivalent fractions", targets_trouble_spot="confusing numerator/denominator when scaling", available_time_minutes=15)
    print("GATE RESULT:", json.dumps(res12.model_dump(), indent=2))
    assert res12.layer_failed == "layer_1"
    assert not any(i.check == "topic_mismatch" for i in res12.issues), "Layer 2 should NOT have executed when Layer 1 failed!"
    print("VERIFIED TEST 12: Layer 1 failure immediately stopped pipeline before Layer 2!")

    # TEST 13: Verify Layer 2 failure prevents Layer 3 execution
    print("\n--- Running TEST 13: Verify Layer 2 failure prevents Layer 3 ---")
    act13 = json.loads(json.dumps(valid_activity))
    act13["topic"] = "Wrong Topic" # Fail Layer 2
    act13["content"]["instructions"] += " culturally_insensitive" # Fail Layer 3
    res13 = evaluate_safety_gate(act13, decided_topic="Equivalent fractions", targets_trouble_spot="confusing numerator/denominator when scaling", available_time_minutes=15)
    print("GATE RESULT:", json.dumps(res13.model_dump(), indent=2))
    assert res13.layer_failed == "layer_2"
    assert not any(i.check == "adversarial_nuance_issue" for i in res13.issues), "Layer 3 should NOT have executed when Layer 2 failed!"
    print("VERIFIED TEST 13: Layer 2 failure immediately stopped pipeline before Layer 3!")

    # TEST 14: Verify classroom_state.json is unchanged
    print("\n--- Running TEST 14: State Immutability Check ---")
    mtime_after = CLASSROOM_STATE_PATH.stat().st_mtime if CLASSROOM_STATE_PATH.exists() else None
    assert mtime_before == mtime_after, "Failed: classroom_state.json was modified!"
    print("VERIFIED TEST 14: Shared classroom state was NOT mutated during execution!")

    # TEST 15: Verify every rejection contains a specific reason
    print("\n--- Running TEST 15: Rejection details presence check ---")
    all_rejections = [res2, res3, res4, res5, res6, res7, res8, res9, res11]
    for r in all_rejections:
        assert r.passed == False
        assert len(r.issues) > 0
        assert r.issues[0].check != ""
        assert len(r.issues[0].detail.strip()) > 0
    print("VERIFIED TEST 15: Every rejection result contains specific check names and detailed reasons!")


if __name__ == "__main__":
    run_tool_tests()
    run_safety_gate_tests()
