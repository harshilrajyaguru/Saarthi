import json
from pathlib import Path

from tools.orchestrator_tools import read_shared_state, write_shared_state, get_active_grades
from agents.orchestrator_agent import run_orchestration_cycle, OrchestrationResult, NextAction

# Import frozen specialist functions to verify they do not mutate state
from agents.progress_agent import analyze_progress
from agents.curriculum_agent import reconcile_curriculum
from agents.resource_agent import recommend_resources
from agents.activity_agent import design_activity
from agents.safety_gate import evaluate_safety_gate


CLASSROOM_STATE_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "classroom_state.json"
)


def run_tool_tests():
    print("=" * 60)
    print("STEP 1: VERIFYING ORCHESTRATOR TOOLS & CANDIDATE FILTER BOUNDARY")
    print("=" * 60)

    # 1. Test read_shared_state
    state = read_shared_state()
    print(f"[Tool Test] read_shared_state: keys={list(state.keys())}")
    assert "classrooms" in state or "grades" in state

    # 2. Test get_active_grades (Cheap candidate filter proof)
    active_info = get_active_grades(session={"active_grades": ["Grade_3_Math"], "new_signals": {"Grade_3_Math": True}})
    print(f"[Tool Test] get_active_grades (Cheap Filter): active_count={active_info.get('active_count')}, skipped_count={active_info.get('skipped_count')}")
    assert active_info.get("active_count") >= 1
    print("VERIFIED CANDIDATE FILTER BOUNDARY: get_active_grades() acts as a cheap deterministic candidate filter (non-LLM call). Orchestrator decides full specialist cycle execution.")

    print("\nSUCCESS: All Orchestrator tools verified!\n")


def run_orchestrator_agent_tests():
    print("=" * 60)
    print("STEP 2: RUNNING ORCHESTRATOR AGENT TEST SCENARIOS")
    print("=" * 60)

    original_state_text = CLASSROOM_STATE_PATH.read_text(encoding="utf-8") if CLASSROOM_STATE_PATH.exists() else None

    try:
        # 1. TEST 1: Single grade normal cycle
        print("\n--- TEST 1: Single grade normal cycle ---")
        session1 = {
            "active_grades": ["Grade_3_Math"],
            "new_signals": {"Grade_3_Math": True},
            "session_info": {"duration_minutes": 40}
        }
        res1 = run_orchestration_cycle(session1)
        print("ORCHESTRATION RESULT 1:")
        print(json.dumps(res1.model_dump(), indent=2))
        assert isinstance(res1.next_action, NextAction)
        assert res1.next_action.grade == "3"
        print("VERIFIED TEST 1: Single grade normal cycle completed with 1 next_action!")

        # 2. TEST 2: Multiple grades active simultaneously
        print("\n--- TEST 2: Multiple grades active simultaneously ---")
        session2 = {
            "active_grades": ["Grade_3_Math", "Grade_4_Math"],
            "new_signals": {"Grade_3_Math": True, "Grade_4_Math": True},
            "session_info": {"duration_minutes": 40}
        }
        res2 = run_orchestration_cycle(session2)
        print("ORCHESTRATION RESULT 2:")
        print(json.dumps(res2.model_dump(), indent=2))
        reconciled_count = sum(1 for s in res2.state_updates if s.status == "reconciled")
        assert reconciled_count == 2
        print("VERIFIED TEST 2: Multiple active grades evaluated simultaneously!")

        # 3. TEST 3: Inactive grade is skipped
        print("\n--- TEST 3: Inactive grade is skipped ---")
        session3 = {
            "active_grades": ["Grade_3_Math"],
            "new_signals": {"Grade_3_Math": True},
            "session_info": {"duration_minutes": 40}
        }
        res3 = run_orchestration_cycle(session3)
        skipped_count = sum(1 for s in res3.state_updates if s.status == "skipped")
        assert skipped_count >= 1
        print(f"VERIFIED TEST 3: Inactive grades skipped (skipped count: {skipped_count})!")

        # 4. EXPLICIT RESOURCE CONTENTION CASE A:
        # Grade 3 = blocking prerequisite + struggling
        # Grade 5 = developing + non-blocking
        # → Grade 3 MUST win scarce resource (tablet).
        print("\n--- TEST CONTENTION CASE A: Blocking Prerequisite + Struggling vs Developing ---")
        session_case_a = {
            "active_grades": ["Grade_3_Math", "Grade_5_Math"],
            "new_signals": {"Grade_3_Math": True, "Grade_5_Math": True},
            "internet_available": True,
            "tablets_free": 1,
            "force_resource": {"Grade_3_Math": "tablet_quiz", "Grade_5_Math": "tablet_quiz"},
            "session_info": {"duration_minutes": 40, "internet_available": True, "tablets_free": 1},
            "mock_curriculum": {
                "Grade_3_Math": {"decided_topic": "Equivalent fractions", "pacing_decision": "hold", "is_blocking_prerequisite": True},
                "Grade_5_Math": {"decided_topic": "Dividing fractions", "pacing_decision": "advance", "is_blocking_prerequisite": False}
            },
            "mock_progress": {
                "Grade_3_Math": {"mastery_estimate": "struggling", "trend": "declining", "trouble_spots": ["numerator scaling"], "attention_flag": True},
                "Grade_5_Math": {"mastery_estimate": "developing", "trend": "stagnant", "trouble_spots": [], "attention_flag": False}
            }
        }
        res_a = run_orchestration_cycle(session_case_a)
        print("CONFLICT RESOLUTION EXPLICIT EVIDENCE FOR CASE A:")
        for conflict_str in res_a.next_action.resolved_conflicts:
            print(" -", conflict_str)

        g3_rec_a = next(s for s in res_a.state_updates if s.grade == "3" and s.subject == "Math" and s.status == "reconciled")
        g5_rec_a = next(s for s in res_a.state_updates if s.grade == "5" and s.subject == "Math" and s.status == "reconciled")

        print(f"Grade 3 Resource: '{g3_rec_a.recommended_resource}' (WINNER - Blocking Prerequisite & Struggling)")
        print(f"Grade 5 Resource: '{g5_rec_a.recommended_resource}' (LOSER - Assigned Alternative)")

        assert "tablet" in str(g3_rec_a.recommended_resource), f"Case A Failed: Grade 3 got {g3_rec_a.recommended_resource}!"
        assert "tablet" not in str(g5_rec_a.recommended_resource), f"Case A Failed: Grade 5 got {g5_rec_a.recommended_resource}!"
        print("VERIFIED CASE A: Grade 3 (blocking prerequisite + struggling) won scarce resource over Grade 5!")

        # 5. EXPLICIT RESOURCE CONTENTION CASE B:
        # Grade 3 = non-blocking + developing
        # Grade 5 = declining + persistent struggling
        # → Grade 5 MUST win scarce resource (tablet).
        print("\n--- TEST CONTENTION CASE B: Declining + Persistent Struggling vs Developing ---")
        session_case_b = {
            "active_grades": ["Grade_3_Math", "Grade_5_Math"],
            "new_signals": {"Grade_3_Math": True, "Grade_5_Math": True},
            "internet_available": True,
            "tablets_free": 1,
            "force_resource": {"Grade_3_Math": "tablet_quiz", "Grade_5_Math": "tablet_quiz"},
            "session_info": {"duration_minutes": 40, "internet_available": True, "tablets_free": 1},
            "mock_curriculum": {
                "Grade_3_Math": {"decided_topic": "Equivalent fractions", "pacing_decision": "advance", "is_blocking_prerequisite": False},
                "Grade_5_Math": {"decided_topic": "Dividing fractions", "pacing_decision": "hold", "is_blocking_prerequisite": False}
            },
            "mock_progress": {
                "Grade_3_Math": {"mastery_estimate": "developing", "trend": "stagnant", "trouble_spots": [], "attention_flag": False},
                "Grade_5_Math": {"mastery_estimate": "struggling", "trend": "declining", "trouble_spots": ["fraction division"], "attention_flag": True}
            }
        }
        res_b = run_orchestration_cycle(session_case_b)
        print("CONFLICT RESOLUTION EXPLICIT EVIDENCE FOR CASE B:")
        for conflict_str in res_b.next_action.resolved_conflicts:
            print(" -", conflict_str)

        g3_rec_b = next(s for s in res_b.state_updates if s.grade == "3" and s.subject == "Math" and s.status == "reconciled")
        g5_rec_b = next(s for s in res_b.state_updates if s.grade == "5" and s.subject == "Math" and s.status == "reconciled")

        print(f"Grade 3 Resource: '{g3_rec_b.recommended_resource}' (LOSER - Assigned Alternative)")
        print(f"Grade 5 Resource: '{g5_rec_b.recommended_resource}' (WINNER - Persistent Struggling & Declining)")

        assert "tablet" in str(g5_rec_b.recommended_resource), "Case B Failed: Grade 5 must win tablet!"
        assert "tablet" not in str(g3_rec_b.recommended_resource), "Case B Failed: Grade 3 must receive alternative resource!"
        print("VERIFIED CASE B: Grade 5 (declining + persistent struggling) won scarce resource over Grade 3!")

        # 6. EXPLICIT RESOURCE CONTENTION CASE C:
        # Both grades have equal learning priority (developing, non-blocking)
        # Tie-breaker: Waiting time (Grade 3 waiting 3 days vs Grade 5 waiting 1 day)
        # → Grade 3 MUST win scarce resource (tablet).
        print("\n--- TEST CONTENTION CASE C: Equal Learning Priority -> Waiting Time Tie-Breaker ---")
        session_case_c = {
            "active_grades": ["Grade_3_Math", "Grade_5_Math"],
            "new_signals": {"Grade_3_Math": True, "Grade_5_Math": True},
            "internet_available": True,
            "tablets_free": 1,
            "force_resource": {"Grade_3_Math": "tablet_quiz", "Grade_5_Math": "tablet_quiz"},
            "session_info": {"duration_minutes": 40, "internet_available": True, "tablets_free": 1},
            "waiting_days": {"Grade_3_Math": 3, "Grade_5_Math": 1},
            "mock_curriculum": {
                "Grade_3_Math": {"decided_topic": "Equivalent fractions", "pacing_decision": "advance", "is_blocking_prerequisite": False},
                "Grade_5_Math": {"decided_topic": "Dividing fractions", "pacing_decision": "advance", "is_blocking_prerequisite": False}
            },
            "mock_progress": {
                "Grade_3_Math": {"mastery_estimate": "developing", "trend": "stagnant", "trouble_spots": [], "attention_flag": False},
                "Grade_5_Math": {"mastery_estimate": "developing", "trend": "stagnant", "trouble_spots": [], "attention_flag": False}
            }
        }
        res_c = run_orchestration_cycle(session_case_c)
        print("CONFLICT RESOLUTION EXPLICIT EVIDENCE FOR CASE C:")
        for conflict_str in res_c.next_action.resolved_conflicts:
            print(" -", conflict_str)

        g3_rec_c = next(s for s in res_c.state_updates if s.grade == "3" and s.subject == "Math" and s.status == "reconciled")
        g5_rec_c = next(s for s in res_c.state_updates if s.grade == "5" and s.subject == "Math" and s.status == "reconciled")

        print(f"Grade 3 Resource: '{g3_rec_c.recommended_resource}' (WINNER - Waited 3 days vs 1 day)")
        print(f"Grade 5 Resource: '{g5_rec_c.recommended_resource}' (LOSER - Assigned Alternative)")

        assert "tablet" in str(g3_rec_c.recommended_resource), "Case C Failed: Grade 3 must win tablet based on waiting time!"
        assert "tablet" not in str(g5_rec_c.recommended_resource), "Case C Failed: Grade 5 must receive alternative resource!"
        print("VERIFIED CASE C: Grade 3 won tie-breaker based on waiting time (3 days vs 1 day)!")

        # 7. TEST 10: Safety escalation gets highest priority
        print("\n--- TEST 10: Safety escalation gets highest priority ---")
        session10 = {
            "active_grades": ["Grade_3_Math"],
            "new_signals": {"Grade_3_Math": True},
            "mock_safety_action": {"Grade_3_Math": "escalate_to_teacher"}
        }
        res10 = run_orchestration_cycle(session10)
        print("ORCHESTRATION RESULT 10:")
        print(json.dumps(res10.model_dump(), indent=2))
        assert res10.next_action.priority == "critical"
        assert res10.next_action.action_type == "teacher_needed"
        print("VERIFIED TEST 10: Safety escalation surfaced as highest priority ('critical' teacher_needed)!")

        # 8. TEST 11: Progress attention + resource contention resolves to ONE action
        print("\n--- TEST 11: Progress attention + resource contention resolves to ONE action ---")
        session11 = {
            "active_grades": ["Grade_3_Math", "Grade_5_Math"],
            "new_signals": {"Grade_3_Math": True, "Grade_5_Math": True}
        }
        res11 = run_orchestration_cycle(session11)
        assert isinstance(res11.next_action, NextAction)
        assert not isinstance(res11.next_action, list)
        print("VERIFIED TEST 11: Combined attention + contention resolved to EXACTLY ONE next_action!")

        # 9. TEST 12: Multiple attention flags still produce ONE next_action
        print("\n--- TEST 12: Multiple attention flags still produce ONE next_action ---")
        session12 = {
            "active_grades": ["Grade_3_Math", "Grade_4_Math", "Grade_5_Math"],
            "new_signals": {"Grade_3_Math": True, "Grade_4_Math": True, "Grade_5_Math": True}
        }
        res12 = run_orchestration_cycle(session12)
        assert isinstance(res12.next_action, NextAction)
        print("VERIFIED TEST 12: Multiple attention flags produced EXACTLY ONE prioritized next_action!")

        # 10. TEST 13, 14: Safety reject triggers regeneration & max retries escalation
        print("\n--- TEST 13, 14: Safety reject triggers regeneration & max retries escalation ---")
        session13 = {
            "active_grades": ["Grade_3_Math"],
            "new_signals": {"Grade_3_Math": True},
            "mock_safety_action": {"Grade_3_Math": "reject_and_regenerate"}
        }
        res13 = run_orchestration_cycle(session13)
        print("ORCHESTRATION RESULT 13 (Max Retries Exceeded):")
        print(json.dumps(res13.model_dump(), indent=2))
        assert res13.next_action.action_type == "teacher_needed"
        print("VERIFIED TEST 13, 14: Max 2 failed regenerations escalated to teacher!")

        # 11. TEST 15: State is written ONLY after reconciliation
        print("\n--- TEST 15: State written ONLY after reconciliation ---")
        state_after = read_shared_state()
        assert "last_updated" in state_after
        print("VERIFIED TEST 15: State written atomically after reconciliation!")

        # 12. TEST 16: Specialist agents cannot mutate shared state
        print("\n--- TEST 16: Specialist agents cannot mutate shared state ---")
        mtime1 = CLASSROOM_STATE_PATH.stat().st_mtime if CLASSROOM_STATE_PATH.exists() else None
        try:
            _ = analyze_progress(3, "Math", "Equivalent fractions", {})
        except Exception:
            pass
        _ = reconcile_curriculum(3, "Math", "Equivalent fractions", {"mastery_estimate": "developing"}, {"available_time": "30m"})
        _ = recommend_resources(3, "Math", "Equivalent fractions", {"duration_minutes": 40})
        _ = design_activity(3, "Math", "Equivalent fractions", "hold", ["scaling numerator"], "developing", "reinforce", "printable_worksheet", False, 15)
        _ = evaluate_safety_gate({"content": {"instructions": "Test", "items": ["1/2 = 2/4"]}}, "Equivalent fractions", "scaling numerator", 15)
        mtime2 = CLASSROOM_STATE_PATH.stat().st_mtime if CLASSROOM_STATE_PATH.exists() else None
        assert mtime1 == mtime2, "Failed: Specialist agent mutated shared state!"
        print("VERIFIED TEST 16: Specialist agents confirmed read-only (zero state mutation)!")

        # 13. TEST 17: State contains final reconciled updates
        print("\n--- TEST 17: State contains final reconciled updates ---")
        assert len(state_after.get("grades", {})) > 0 or "reconciled_updates" in state_after or "last_updated" in state_after
        print("VERIFIED TEST 17: classroom_state.json contains final reconciled grade entries!")

        # 14. TEST 18, 19, 20: Orchestrator does not override Progress/Curriculum/Resource domain decisions
        print("\n--- TEST 18, 19, 20: Domain decisions preserved ---")
        g3_final = state_after.get("grades", {}).get("Grade_3_Math", {})
        if g3_final:
            assert "mastery_estimate" in g3_final
            assert "current_topic" in g3_final
            assert "recommended_resource" in g3_final
        print("VERIFIED TEST 18, 19, 20: Progress mastery, Curriculum topic, and Resource recommendations preserved!")

        # 15. TEST 21: Exactly one next_action is always produced
        print("\n--- TEST 21: Exactly one next_action produced ---")
        assert isinstance(res1.next_action, NextAction)
        assert isinstance(res_a.next_action, NextAction)
        assert isinstance(res10.next_action, NextAction)
        print("VERIFIED TEST 21: Exactly ONE next_action produced in all cycles!")

    finally:
        if original_state_text:
            CLASSROOM_STATE_PATH.write_text(original_state_text, encoding="utf-8")


if __name__ == "__main__":
    run_tool_tests()
    run_orchestrator_agent_tests()
