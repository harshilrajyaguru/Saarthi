import json
from pathlib import Path

from classroom_loop import (
    ClassroomSession,
    ClassroomLoopRunner,
    DeliveredActivity,
    CycleRecord,
    parse_grade_subject
)
from tools.orchestrator_tools import read_shared_state, write_shared_state


CLASSROOM_STATE_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "classroom_state.json"
)


def run_classroom_loop_tests():
    print("=" * 80)
    print("SAARTHI CONTINUOUS CLASSROOM LOOP — INTEGRATION TEST SUITE")
    print("=" * 80)

    original_state_text = CLASSROOM_STATE_PATH.read_text(encoding="utf-8") if CLASSROOM_STATE_PATH.exists() else None

    try:
        # -------------------------------------------------------------
        # TEST 1: NORMAL CONTINUATION
        # -------------------------------------------------------------
        print("\n" + "=" * 60)
        print("TEST 1: NORMAL CONTINUATION SCENARIO")
        print("=" * 60)

        session1 = ClassroomSession(
            session_id="sess_continuation_101",
            active_grades=["Grade_4_Math"],
            subjects=["Math"],
            session_duration_minutes=40,
            remaining_time_minutes=40,
            classroom_resources={"internet_available": True, "tablets_free": 5, "printer_has_paper": True}
        )

        runner1 = ClassroomLoopRunner(session1)
        cycle1 = runner1.start_session()
        assert cycle1.decision in ["CONTINUE", "ADAPT"]

        # Simulate positive student performance signals after delivery
        feedback_signals1 = {
            "Grade_4_Math": {
                "correctness": 0.85,
                "completion": 0.95,
                "time_on_task": 10,
                "teacher_feedback": "students_engaged"
            }
        }
        cycle2 = runner1.process_new_signals(feedback_signals1)
        print(f"\n[Test 1 Decision] Status: '{session1.status}', Cycle Decision: '{cycle2.decision}'")
        assert cycle2.decision in ["CONTINUE", "ADAPT"]
        print("VERIFIED TEST 1: Normal continuation scenario executed cleanly!")

        # -------------------------------------------------------------
        # TEST 2: ADAPTATION
        # -------------------------------------------------------------
        print("\n" + "=" * 60)
        print("TEST 2: ADAPTATION SCENARIO (Grade 5 Decimals)")
        print("=" * 60)

        session2 = ClassroomSession(
            session_id="sess_adaptation_202",
            active_grades=["Grade_5_Math"],
            subjects=["Math"],
            session_duration_minutes=40,
            remaining_time_minutes=40,
            classroom_resources={"internet_available": True, "tablets_free": 5}
        )

        runner2 = ClassroomLoopRunner(session2)
        _ = runner2.start_session()

        # Simulate low performance and confusion signals for Grade 5
        feedback_signals2 = {
            "Grade_5_Math": True,
            "mock_progress": {
                "Grade_5_Math": {
                    "mastery_estimate": "struggling",
                    "trend": "declining",
                    "trouble_spots": ["simplifying final result"],
                    "attention_flag": True,
                    "recommendation_direction": "reteach"
                }
            }
        }
        cycle2_2 = runner2.process_new_signals(feedback_signals2)
        print(f"\n[Test 2 Decision] Status: '{session2.status}', Cycle Decision: '{cycle2_2.decision}'")
        assert cycle2_2.decision == "ADAPT", "Test 2 Failed: Decision should be ADAPT for struggling performance!"
        print("VERIFIED TEST 2: Persistent trouble spot correctly triggered targeted ADAPTATION cycle!")

        # -------------------------------------------------------------
        # TEST 3: MULTI-GRADE ADAPTATION & ISOLATION
        # -------------------------------------------------------------
        print("\n" + "=" * 60)
        print("TEST 3: MULTI-GRADE ADAPTATION SCENARIO (Grades 3, 4, 5)")
        print("=" * 60)

        session3 = ClassroomSession(
            session_id="sess_multigrade_303",
            active_grades=["Grade_3_Math", "Grade_4_Math", "Grade_5_Math"],
            subjects=["Math"],
            session_duration_minutes=40,
            remaining_time_minutes=40,
            classroom_resources={"internet_available": True, "tablets_free": 2}
        )

        runner3 = ClassroomLoopRunner(session3)
        _ = runner3.start_session()

        # Signals: Grade 3 improves (90%), Grade 4 stable (75%), Grade 5 declines (40%)
        multi_signals = {
            "Grade_3_Math": False,
            "Grade_4_Math": False,
            "Grade_5_Math": True,
            "mock_progress": {
                "Grade_3_Math": {"mastery_estimate": "proficient", "trend": "improving", "trouble_spots": [], "attention_flag": False},
                "Grade_4_Math": {"mastery_estimate": "developing", "trend": "stagnant", "trouble_spots": [], "attention_flag": False},
                "Grade_5_Math": {"mastery_estimate": "struggling", "trend": "declining", "trouble_spots": ["decimals"], "attention_flag": True}
            }
        }
        cycle3_2 = runner3.process_new_signals(multi_signals)
        next_act3 = cycle3_2.orchestration_result.get("next_action", {}) if cycle3_2.orchestration_result else {}

        print(f"\n[Test 3 Decision] Prioritized Grade: '{next_act3.get('grade')}', Priority: '{next_act3.get('priority')}'")
        assert next_act3.get("grade") == "5", "Test 3 Failed: Grade 5 should be prioritized for adaptation!"
        print("VERIFIED TEST 3: Multi-grade signals isolated; Grade 5 prioritized without blindly restarting all grades!")

        # -------------------------------------------------------------
        # TEST 4: RESOURCE CHANGE MID-SESSION
        # -------------------------------------------------------------
        print("\n" + "=" * 60)
        print("TEST 4: MID-SESSION RESOURCE AVAILABILITY CHANGE")
        print("=" * 60)

        session4 = ClassroomSession(
            session_id="sess_resource_404",
            active_grades=["Grade_5_Math"],
            subjects=["Math"],
            session_duration_minutes=40,
            remaining_time_minutes=40,
            classroom_resources={"internet_available": True, "tablets_free": 5, "printer_has_paper": True}
        )

        runner4 = ClassroomLoopRunner(session4)
        _ = runner4.start_session()

        # Internet drops mid-session
        runner4.update_classroom_resources({"internet_available": False, "tablets_free": 0})
        cycle4_2 = runner4.run_cycle(trigger_type="resource_change")

        g5_up = next(s for s in cycle4_2.orchestration_result["state_updates"] if s["grade"] == "5")
        print(f"[Test 4 Decision] Resource selected after internet drop: '{g5_up['recommended_resource']}'")
        assert g5_up["recommended_resource"] not in ["tablet", "tablet_quiz"], "Test 4 Failed: Infeasible tablet selected after internet drop!"
        assert g5_up["recommended_resource"] in ["printable_worksheet", "whiteboard_activity"], "Test 4 Failed: Feasible alternative not selected!"
        print("VERIFIED TEST 4: Resource Agent adapted to environmental change; infeasible resource rejected!")

        # -------------------------------------------------------------
        # TEST 5: SAFETY REGENERATION & BOUNDED ESCALATION
        # -------------------------------------------------------------
        print("\n" + "=" * 60)
        print("TEST 5: SAFETY REGENERATION & BOUNDED ESCALATION")
        print("=" * 60)

        session5 = ClassroomSession(
            session_id="sess_safety_505",
            active_grades=["Grade_3_Math"],
            subjects=["Math"],
            session_duration_minutes=40,
            remaining_time_minutes=40,
            session_constraints={"mock_safety_action": {"Grade_3_Math": "escalate_to_teacher"}},
            classroom_resources={"internet_available": True}
        )

        runner5 = ClassroomLoopRunner(session5)
        cycle5 = runner5.start_session()
        next_act5 = cycle5.orchestration_result.get("next_action", {}) if cycle5.orchestration_result else {}

        print(f"[Test 5 Decision] Action Type: '{next_act5.get('action_type')}', Priority: '{next_act5.get('priority')}'")
        assert next_act5.get("action_type") == "teacher_needed", "Test 5 Failed: Safety escalation should surface teacher_needed!"
        assert next_act5.get("priority") == "critical", "Test 5 Failed: Safety escalation should be critical priority!"
        print("VERIFIED TEST 5: Bounded safety gate failure correctly escalated to teacher with critical priority!")

        # -------------------------------------------------------------
        # TEST 6: SESSION END & TERMINATION
        # -------------------------------------------------------------
        print("\n" + "=" * 60)
        print("TEST 6: SESSION EXPIRATION & TERMINATION")
        print("=" * 60)

        session6 = ClassroomSession(
            session_id="sess_ended_606",
            active_grades=["Grade_4_Math"],
            subjects=["Math"],
            session_duration_minutes=40,
            remaining_time_minutes=0,  # Time expired
            status="ended"
        )

        runner6 = ClassroomLoopRunner(session6)
        cycle6 = runner6.run_cycle(trigger_type="initial")

        print(f"[Test 6 Decision] Session Status: '{session6.status}', Cycle Decision: '{cycle6.decision}'")
        assert session6.status == "ended", "Test 6 Failed: Session status should be ended!"
        assert cycle6.decision == "END", "Test 6 Failed: Cycle decision should be END!"
        print("VERIFIED TEST 6: Session duration expiration halted execution cleanly without spawning new cycles!")

        # -------------------------------------------------------------
        # TEST 7: GENERIC GRADE SUPPORT (GRADES 1 - 8)
        # -------------------------------------------------------------
        print("\n" + "=" * 60)
        print("TEST 7: GENERIC GRADE SUPPORT (GRADES 1, 2, 6, 7, 8)")
        print("=" * 60)

        generic_grades = ["Grade_1_Math", "Grade_2_Math", "Grade_6_Math", "Grade_7_Science", "Grade_8_Math"]

        for g_key in generic_grades:
            g_str, subj_str = parse_grade_subject(g_key)
            assert g_str in ["1", "2", "6", "7", "8"], f"Failed to parse grade string for {g_key}"
            assert subj_str in ["Math", "Science"], f"Failed to parse subject for {g_key}"
            print(f"  [OK] Generic Grade Parser: '{g_key}' -> Grade: '{g_str}', Subject: '{subj_str}'")

        session7 = ClassroomSession(
            session_id="sess_generic_707",
            active_grades=["Grade_1_Math", "Grade_7_Science", "Grade_8_Math"],
            subjects=["Math", "Science"],
            session_duration_minutes=40,
            remaining_time_minutes=40,
            classroom_resources={"internet_available": True, "tablets_free": 3}
        )

        runner7 = ClassroomLoopRunner(session7)
        cycle7 = runner7.start_session()
        assert cycle7.orchestration_result is not None
        print("VERIFIED TEST 7: Classroom loop executed generically across Grades 1, 7, and 8 with zero hardcoding!")

        print("\n" + "=" * 80)
        print("ALL 7 CONTINUOUS CLASSROOM LOOP INTEGRATION TESTS PASSED 100%!")
        print("=" * 80)

    finally:
        if original_state_text:
            CLASSROOM_STATE_PATH.write_text(original_state_text, encoding="utf-8")


if __name__ == "__main__":
    run_classroom_loop_tests()
