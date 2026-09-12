import json
from pathlib import Path

from tools.resource_tools import (
    get_resource_inventory,
    get_resource_usage_log,
    check_concurrent_demand
)
from agents.resource_agent import recommend_resources


CLASSROOM_STATE_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "classroom_state.json"
)


def run_tool_tests():
    print("=" * 60)
    print("STEP 1: VERIFYING RESOURCE TOOLS")
    print("=" * 60)

    inv = get_resource_inventory(session={"internet_available": False, "tablets_free": 1})
    print(f"[Tool Test] get_resource_inventory: internet_available={inv.get('internet_available')}, tablets_free={inv.get('tablets_free')}")
    assert inv.get("internet_available") == False
    assert inv.get("tablets_free") == 1

    log = get_resource_usage_log(grade=3, subject="Math", topic="Equivalent fractions (prerequisite reinforcement)")
    print(f"[Tool Test] get_resource_usage_log: total_recent={log.get('total_recent_sessions')}, counts={log.get('usage_counts')}")
    assert log.get("total_recent_sessions") >= 3

    demand = check_concurrent_demand(session={"concurrent_demand": {"Grade 5": ["tablet"], "Grade 3": ["tablet"]}})
    print(f"[Tool Test] check_concurrent_demand: active_grades={demand.get('active_grades')}")
    assert "Grade 5" in demand.get("active_grades", [])

    print("\nSUCCESS: All Resource tools verified!\n")


def run_resource_agent_tests():
    print("=" * 60)
    print("STEP 2: RUNNING RESOURCE AGENT TEST SCENARIOS")
    print("=" * 60)

    mtime_before = CLASSROOM_STATE_PATH.stat().st_mtime if CLASSROOM_STATE_PATH.exists() else None

    scenarios = [
        {
            "id": "TEST 1",
            "name": "TEST 1: Internet unavailable -> verify internet resources infeasible, offline possible",
            "grade": 3,
            "subject": "Math",
            "topic": "Equivalent fractions",
            "session": {"duration_minutes": 40, "internet_available": False, "tablets_free": 1, "printer_has_paper": True},
            "check": lambda res: (
                res.get("delivery_possible") == True
                and any(opt["type"] == "tablet_quiz" and opt["feasibility"] == "infeasible" for opt in res["resource_options"])
                and res.get("recommended_resource") == res["resource_options"][0]["type"]
                and res["resource_options"][0]["feasibility"] != "infeasible"
            )
        },
        {
            "id": "TEST 2",
            "name": "TEST 2: Scarce tablet requested by Grade 3 & Grade 5 -> contention_flag = true",
            "grade": 3,
            "subject": "Math",
            "topic": "Equivalent fractions",
            "session": {
                "duration_minutes": 40,
                "tablets_free": 1,
                "concurrent_demand": {"Grade 5": ["tablet"], "Grade 3": ["tablet"]}
            },
            "check": lambda res: (
                res.get("delivery_possible") == True
                and res.get("contention_flag") == True
                and res.get("contention_detail") is not None
                and "Grade 5" in str(res.get("contention_detail"))
                and res.get("recommended_resource") == res["resource_options"][0]["type"]
            )
        },
        {
            "id": "TEST 3",
            "name": "TEST 3: Printer has no paper -> printable resources infeasible",
            "grade": 4,
            "subject": "Math",
            "topic": "Multiplying fractions",
            "session": {"duration_minutes": 40, "printer_has_paper": False, "tablets_free": 0},
            "check": lambda res: (
                res.get("delivery_possible") == True
                and any(opt["type"] == "printable_worksheet" and opt["feasibility"] == "infeasible" for opt in res["resource_options"])
                and res.get("recommended_resource") == res["resource_options"][0]["type"]
                and res.get("recommended_resource") != "printable_worksheet"
            )
        },
        {
            "id": "TEST 4",
            "name": "TEST 4: Resource used repeatedly in recent sessions -> staleness ranking reduction",
            "grade": 3,
            "subject": "Math",
            "topic": "Equivalent fractions (prerequisite reinforcement)",
            "session": {"duration_minutes": 40, "internet_available": False, "tablets_free": 0, "printer_has_paper": True},
            "check": lambda res: (
                res.get("delivery_possible") == True
                and any(opt["type"] == "whiteboard_activity" and opt["feasibility"] == "low" for opt in res["resource_options"])
                and res.get("recommended_resource") == "printable_worksheet"
                and res.get("recommended_resource") == res["resource_options"][0]["type"]
            )
        },
        {
            "id": "TEST 5",
            "name": "TEST 5: All delivery mechanisms infeasible -> delivery_possible = false, needs_generation = false",
            "grade": 4,
            "subject": "Math",
            "topic": "Multi-digit division",
            "session": {
                "duration_minutes": 40,
                "internet_available": False,
                "tablets_free": 0,
                "printer_has_paper": False,
                "tv_available": False,
                "whiteboard_available": False
            },
            "check": lambda res: (
                res.get("delivery_possible") == False
                and res.get("needs_generation") == False
                and res.get("recommended_resource") is None
                and all(opt["feasibility"] == "infeasible" for opt in res["resource_options"])
            )
        },
        {
            "id": "TEST 6",
            "name": "TEST 6: Multiple feasible resources exist -> strict ranking match",
            "grade": 5,
            "subject": "Math",
            "topic": "Decimals - addition",
            "session": {
                "duration_minutes": 45,
                "internet_available": True,
                "tablets_free": 5,
                "printer_has_paper": True,
                "tv_available": True
            },
            "check": lambda res: (
                res.get("delivery_possible") == True
                and len(res.get("resource_options", [])) >= 3
                and res.get("recommended_resource") == res["resource_options"][0]["type"]
                and res["resource_options"][0]["feasibility"] == "high"
            )
        },
        {
            "id": "TEST 7",
            "name": "TEST 7: Strict Feasibility Guardrail -> Infeasible option CANNOT become recommended_resource",
            "grade": 5,
            "subject": "Math",
            "topic": "Decimals - multiplication",
            "session": {
                "duration_minutes": 40,
                "internet_available": False,
                "tablets_free": 0
            },
            "check": lambda res: (
                res.get("recommended_resource") != "tablet_quiz"
                and res.get("recommended_resource") != "tablet"
                and res.get("recommended_resource") in ["whiteboard_activity", "printable_worksheet"]
            )
        }
    ]

    forbidden_content_keys = {"worksheet_content", "quiz_questions", "lesson_plan", "teaching_instructions", "activity_design"}

    for tc in scenarios:
        print(f"\n--- Running {tc['name']} ---")
        recommendation = recommend_resources(
            grade=tc["grade"],
            subject=tc["subject"],
            topic=tc["topic"],
            session=tc["session"]
        )

        print("RESOURCE AGENT RECOMMENDATION:")
        print(json.dumps(recommendation, indent=2))

        # Check scenario assertions
        assert tc["check"](recommendation), f"Failed {tc['id']}: Output failed scenario verification check!"

        # Verify boundary constraints (no activity content generated)
        for fk in forbidden_content_keys:
            assert fk not in recommendation, f"Boundary Violation: Output contains forbidden key '{fk}'"

        print(f"VERIFIED {tc['id']}: Scenario check passed, hard guardrails enforced, and no activity content generated!")

    # Verify no shared classroom state mutation occurred
    mtime_after = CLASSROOM_STATE_PATH.stat().st_mtime if CLASSROOM_STATE_PATH.exists() else None
    assert mtime_before == mtime_after, "Failed: classroom_state.json was modified!"
    print("\nVERIFIED STATE INTEGRITY: Shared classroom state was NOT mutated during execution.")


if __name__ == "__main__":
    run_tool_tests()
    run_resource_agent_tests()
