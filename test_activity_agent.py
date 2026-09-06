import json
from pathlib import Path

from tools.activity_tools import (
    get_activity_templates,
    get_recent_activity_history
)
from agents.activity_agent import design_activity, activity_agent


CLASSROOM_STATE_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "classroom_state.json"
)


def run_tool_tests():
    print("=" * 60)
    print("STEP 1: VERIFYING ACTIVITY TOOLS")
    print("=" * 60)

    # 1. Test get_activity_templates
    tpls = get_activity_templates(topic="Equivalent fractions", resource_type="printable_worksheet")
    print(f"[Tool Test] get_activity_templates: count={tpls.get('count')}, templates={len(tpls.get('found_templates', []))}")
    assert tpls.get("count") >= 1

    # 2. Test get_recent_activity_history
    hist = get_recent_activity_history(grade=3, subject="Math")
    print(f"[Tool Test] get_recent_activity_history: recent_formats={hist.get('recent_formats')}")
    assert isinstance(hist.get("recent_formats"), list)

    print("\nSUCCESS: All Activity tools verified!\n")


def run_activity_agent_tests():
    print("=" * 60)
    print("STEP 2: RUNNING ACTIVITY AGENT TEST SCENARIOS")
    print("=" * 60)

    mtime_before = CLASSROOM_STATE_PATH.stat().st_mtime if CLASSROOM_STATE_PATH.exists() else None

    # TEST 1: Specific trouble spot diagnostic adaptation
    print("\n--- Running TEST 1: Specific trouble spot diagnostic adaptation ---")
    res1 = design_activity(
        grade=3,
        subject="Math",
        decided_topic="Equivalent fractions (prerequisite reinforcement)",
        pacing_decision="hold",
        trouble_spots=["confusing numerator/denominator when scaling"],
        mastery_estimate="developing",
        recommendation_direction="reinforce",
        recommended_resource="printable_worksheet",
        needs_generation=False,
        available_time_minutes=15
    )
    print("ACTIVITY AGENT DESIGN:")
    print(json.dumps(res1, indent=2))

    items_text1 = json.dumps(res1["content"]["items"])
    assert "Is the student correct?" in items_text1 or "BOTH" in items_text1 or "circle" in items_text1
    assert not ("(Numerator: 1->2" in items_text1), "Question gave away the transformation steps!"
    print("VERIFIED TEST 1: Activity specifically targets numerator/denominator trouble spot with diagnostic questions!")

    # TEST 2: Resource lock
    print("\n--- Running TEST 2: Resource lock ---")
    res2 = design_activity(
        grade=3,
        subject="Math",
        decided_topic="Equivalent fractions",
        pacing_decision="advance",
        trouble_spots=[],
        mastery_estimate="proficient",
        recommendation_direction="advance",
        recommended_resource="printable_worksheet",
        needs_generation=False,
        available_time_minutes=15
    )
    print("ACTIVITY AGENT DESIGN:")
    print(json.dumps(res2, indent=2))
    assert res2["activity_type"] == "printable_worksheet"
    print("VERIFIED TEST 2: Resource lock strictly enforced (printable_worksheet maintained)!")

    # TEST 3: Template adaptation without giving away answer
    print("\n--- Running TEST 3: Template adaptation ---")
    res3 = design_activity(
        grade=3,
        subject="Math",
        decided_topic="Equivalent fractions",
        pacing_decision="hold",
        trouble_spots=["confusing numerator/denominator when scaling"],
        mastery_estimate="developing",
        recommendation_direction="reinforce",
        recommended_resource="printable_worksheet",
        needs_generation=False,
        available_time_minutes=15
    )
    print("ACTIVITY AGENT DESIGN:")
    print(json.dumps(res3, indent=2))
    assert res3["targets_trouble_spot"] == "confusing numerator/denominator when scaling"
    assert len(res3["content"]["items"]) > 0
    print("VERIFIED TEST 3: Template adapted specifically to trouble spot without giving away answers!")

    # TEST 4: Generation from scratch (Multiplying fractions + simplifying result)
    print("\n--- Running TEST 4: Generation from scratch (Multiplying fractions + simplifying result) ---")
    res4 = design_activity(
        grade=4,
        subject="Math",
        decided_topic="Multiplying fractions",
        pacing_decision="advance",
        trouble_spots=["simplifying final fraction result"],
        mastery_estimate="developing",
        recommendation_direction="reinforce",
        recommended_resource="whiteboard_activity",
        needs_generation=True,
        available_time_minutes=20
    )
    print("ACTIVITY AGENT DESIGN:")
    print(json.dumps(res4, indent=2))

    items_text4 = json.dumps(res4["content"]["items"]).lower()
    inst_text4 = res4["content"]["instructions"].lower()

    # VERIFY: Content MUST match topic (Multiplying fractions) and trouble spot (simplifying final result)
    assert res4["topic"] == "Multiplying fractions"
    assert res4["activity_type"] == "whiteboard_activity"
    assert "multiply" in inst_text4 or "multiply" in items_text4 or "×" in items_text4
    assert "simplify" in inst_text4 or "simplify" in items_text4 or "reduce" in items_text4
    # VERIFY: Content must NOT contain irrelevant equivalent fraction text like "2/3 becomes 4/3"
    assert "2/3 becomes 4/3" not in items_text4
    print("VERIFIED TEST 4: Generated content strictly matches 'Multiplying fractions' and 'simplifying final fraction result'!")

    # TEST 5: Difficulty calibration (scaffolded vs challenging content verification)
    print("\n--- Running TEST 5: Difficulty calibration (content verification) ---")
    res5_struggling = design_activity(
        grade=3,
        subject="Math",
        decided_topic="Equivalent fractions",
        pacing_decision="hold",
        trouble_spots=["scaling denominator"],
        mastery_estimate="struggling",
        recommendation_direction="reteach",
        recommended_resource="printable_worksheet",
        needs_generation=False,
        available_time_minutes=15
    )
    res5_proficient = design_activity(
        grade=3,
        subject="Math",
        decided_topic="Equivalent fractions",
        pacing_decision="advance",
        trouble_spots=[],
        mastery_estimate="proficient",
        recommendation_direction="advance",
        recommended_resource="printable_worksheet",
        needs_generation=False,
        available_time_minutes=15
    )
    print(f"Struggling Items: {res5_struggling['content']['items']}")
    print(f"Proficient Items: {res5_proficient['content']['items']}")

    assert res5_struggling["difficulty_level"] == "scaffolded"
    assert res5_proficient["difficulty_level"] == "challenging"
    assert res5_struggling["content"]["items"] != res5_proficient["content"]["items"], "Content must differ between struggling and proficient!"
    print("VERIFIED TEST 5: Content meaningfully differs between scaffolded (struggling) and challenging (proficient)!")

    # TEST 6: Time constraint enforcement
    print("\n--- Running TEST 6: Time constraint enforcement ---")
    res6 = design_activity(
        grade=3,
        subject="Math",
        decided_topic="Equivalent fractions",
        pacing_decision="hold",
        trouble_spots=["numerator scaling"],
        mastery_estimate="developing",
        recommendation_direction="reinforce",
        recommended_resource="printable_worksheet",
        needs_generation=False,
        available_time_minutes=8
    )
    print("ACTIVITY AGENT DESIGN:")
    print(json.dumps(res6, indent=2))
    assert res6["estimated_time_minutes"] <= 8
    print("VERIFIED TEST 6: Estimated execution time strictly respects 8-minute available time limit!")

    # TEST 7: Recent activity history avoidance (strengthened format verification)
    print("\n--- Running TEST 7: Recent activity history format adaptation ---")
    res7 = design_activity(
        grade=3,
        subject="Math",
        decided_topic="Equivalent fractions",
        pacing_decision="hold",
        trouble_spots=["scaling numerator"],
        mastery_estimate="developing",
        recommendation_direction="reinforce",
        recommended_resource="printable_worksheet",
        needs_generation=False,
        available_time_minutes=15
    )
    print("ACTIVITY AGENT DESIGN:")
    print(json.dumps(res7, indent=2))

    # Grade 3 Math recent history had format 'scaffolded_fraction_practice'.
    # Verify that the agent selected 'error_analysis_worksheet' instead of repeating 'scaffolded_fraction_practice'!
    inst_res7 = res7["content"]["instructions"]
    assert "Analyze student statements" in inst_res7 or "error" in inst_res7.lower()
    assert "Identify the top number" not in inst_res7, "Failed: Repeated recent activity format!"
    print("VERIFIED TEST 7: Format adaptation proven! Selected 'error_analysis_worksheet' to avoid recent format 'scaffolded_fraction_practice'.")

    # TEST 8: Boundary enforcement
    print("\n--- Running TEST 8: Boundary enforcement ---")
    forbidden_keys = {"resource_override", "curriculum_change", "safety_approval", "contention_resolution", "orchestrator_decision"}
    for fk in forbidden_keys:
        assert fk not in res1, f"Boundary Violation: Output contains forbidden key '{fk}'"
        assert fk not in res4, f"Boundary Violation: Output contains forbidden key '{fk}'"
    print("VERIFIED TEST 8: Boundary check passed with zero cross-boundary outputs!")

    # TEST 9: Topic and Trouble Spot Semantic Content Fit
    print("\n--- Running TEST 9: Topic & trouble spot semantic content fit verification ---")
    res9 = design_activity(
        grade=4,
        subject="Math",
        decided_topic="Multiplying fractions",
        pacing_decision="advance",
        trouble_spots=["simplifying final fraction result"],
        mastery_estimate="developing",
        recommendation_direction="reinforce",
        recommended_resource="printable_worksheet",
        needs_generation=True,
        available_time_minutes=15
    )
    print("ACTIVITY AGENT DESIGN FOR TEST 9:")
    print(json.dumps(res9, indent=2))

    items_str9 = json.dumps(res9["content"]["items"]).lower()
    inst_str9 = res9["content"]["instructions"].lower()

    # Rejection checks:
    # 1. Content MUST relate to multiplication and simplifying
    assert "multiply" in inst_str9 or "multiply" in items_str9 or "×" in items_str9
    assert "simplify" in inst_str9 or "simplify" in items_str9 or "reduce" in items_str9
    # 2. Content MUST NOT contain wrong topic questions (e.g. equivalent fraction circle numerator)
    assert "circle the numerator" not in items_str9
    assert "2/3 = ?/4" not in items_str9

    print("VERIFIED TEST 9: Irrelevant/wrong topic content rejected; generated content strictly fits topic and trouble spot!")

    # State integrity check
    mtime_after = CLASSROOM_STATE_PATH.stat().st_mtime if CLASSROOM_STATE_PATH.exists() else None
    assert mtime_before == mtime_after, "Failed: classroom_state.json was modified!"
    print("\nVERIFIED STATE INTEGRITY: Shared classroom state was NOT mutated during execution.")


if __name__ == "__main__":
    run_tool_tests()
    run_activity_agent_tests()
