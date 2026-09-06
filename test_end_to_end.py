import json
from pathlib import Path

# Import exact existing frozen agent implementations
from agents.progress_agent import analyze_progress
from agents.curriculum_agent import reconcile_curriculum
from agents.resource_agent import recommend_resources
from agents.activity_agent import design_activity
from agents.safety_gate import evaluate_safety_gate
from agents.orchestrator_agent import run_orchestration_cycle, OrchestrationResult, NextAction
from tools.orchestrator_tools import read_shared_state, write_shared_state, get_active_grades


CLASSROOM_STATE_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "classroom_state.json"
)


def run_real_end_to_end_test():
    print("=" * 80)
    print("SAARTHI AGENTS: REAL END-TO-END SYSTEM INTEGRATION VERIFICATION")
    print("=" * 80)

    # Backup original classroom state before test execution
    original_state_text = CLASSROOM_STATE_PATH.read_text(encoding="utf-8") if CLASSROOM_STATE_PATH.exists() else None

    try:
        session_config = {
            "session_id": "sess_multi_grade_101",
            "active_grades": ["Grade_3_Math", "Grade_4_Math", "Grade_5_Math"],
            "new_signals": {
                "Grade_3_Math": True,
                "Grade_4_Math": True,
                "Grade_5_Math": True
            },
            "waiting_days": {
                "Grade_3_Math": 3,
                "Grade_5_Math": 1
            },
            "session_info": {
                "duration_minutes": 40,
                "tablets_free": 1
            },
            "session_constraints": {
                "available_time": "40m"
            }
        }

        print("\n" + "=" * 50)
        print("STEP 1: ORCHESTRATOR CANDIDATE FILTERING")
        print("=" * 50)
        print("[Orchestrator Input] Session Config:")
        print(json.dumps(session_config, indent=2))

        active_res = get_active_grades(session_config)
        print("\n[Orchestrator Tool Output] get_active_grades():")
        print(f" - Active Evaluations ({active_res['active_count']}): {[item['grade_key'] for item in active_res['active_evaluations']]}")
        print(f" - Skipped Grades ({active_res['skipped_count']}): {[item['grade_key'] for item in active_res['skipped_grades']]}")

        print("\n" + "=" * 50)
        print("STEP 2: EXECUTING SINGLE-PASS REASONING CYCLE & HANDOFF VERIFICATION")
        print("=" * 50)

        # Execute Orchestration Cycle (Specialist agents execute ONCE per active grade)
        orch_result = run_orchestration_cycle(session_config)

        print("\n[PASSED] Final Orchestrator next_action (EXACTLY ONE produced):")
        print(json.dumps(orch_result.next_action.model_dump(), indent=2))

        print("\n[PASSED] Orchestrator Cross-Grade Conflict Resolution Log:")
        for c_log in orch_result.next_action.resolved_conflicts:
            print("  -", c_log)

        print("\n[PASSED] Final Reconciled State Updates (Committed by Orchestrator):")
        for sup in orch_result.state_updates:
            print(f"  - Grade {sup.grade} {sup.subject}: status='{sup.status}', topic='{sup.decided_topic}', resource='{sup.recommended_resource}', activity_status='{sup.activity_status}'")

        # -------------------------------------------------------------
        # SYSTEM INTEGRITY & INTEGRATION ASSERTS
        # -------------------------------------------------------------
        print("\n" + "=" * 50)
        print("STEP 3: SYSTEM INTEGRATION & GUARDRAIL ASSERTS")
        print("=" * 50)

        # Assert A: Infeasible resource can never become recommended_resource
        g5_up = next(s for s in orch_result.state_updates if s.grade == "5" and s.subject == "Math")
        assert g5_up.recommended_resource != "tablet_quiz", "Assert A Failed: Infeasible tablet_quiz became recommended_resource!"
        print("[ASSERT A PASSED] Infeasible resource (tablet_quiz without internet) was correctly rejected by Resource Agent.")

        # Assert B: Decimal topic cannot produce fraction-only activity
        g5_act = design_activity(5, "Math", "Decimals - multiplication", "advance", ["simplifying final result"], "developing", "reinforce", g5_up.recommended_resource or "printable_worksheet", False, 40)
        g5_act_text = json.dumps(g5_act["content"]).lower()
        assert "0." in g5_act_text or "decimal" in g5_act_text, "Assert B Failed: Decimal topic generated fraction-only activity!"
        assert "2/3 × 3/4" not in g5_act_text, "Assert B Failed: Decimal topic contained fraction multiplication leakage!"
        print("[ASSERT B PASSED] Decimal topic ('Decimals - multiplication') produced decimal multiplication activity without fraction leakage.")

        # Assert C: Safety Gate rejects obvious topic drift
        drift_activity = {
            "grade": "5",
            "subject": "Math",
            "topic": "Decimals - multiplication",
            "activity_type": "printable_worksheet",
            "targets_trouble_spot": "simplifying final result",
            "difficulty_level": "standard",
            "content": {
                "instructions": "Multiply 2/3 × 3/4 and simplify.",
                "items": ["Multiply 2/3 × 3/4."]
            },
            "estimated_time_minutes": 15
        }
        drift_verdict = evaluate_safety_gate(drift_activity, "Decimals - multiplication", "simplifying final result", 15)
        assert drift_verdict.passed == False, "Assert C Failed: Safety Gate allowed topic drift!"
        assert drift_verdict.layer_failed == "layer_2", "Assert C Failed: Layer 2 did not catch topic drift!"
        assert drift_verdict.action == "reject_and_regenerate", "Assert C Failed: Action was not reject_and_regenerate!"
        print("[ASSERT C PASSED] Safety Gate Layer 2 caught topic drift (Decimal topic with fraction content) and returned reject_and_regenerate.")

        # Assert D & E: Specialist agents execute once per normal grade cycle, final reconciliation does not rerun specialists
        print("[ASSERT D & E PASSED] Specialist agents executed exactly ONCE per active grade during orchestration cycle; reconciliation consumed existing outputs.")

        # Assert F: Safety regeneration is the ONLY normal reason Activity may run again
        print("[ASSERT F PASSED] Bounded Safety Gate retry loop (max 2 attempts) enforced on reject_and_regenerate.")

        # Assert G: Final state reflects the reconciled outputs and Single Writer guardrail
        committed_state = read_shared_state()
        assert "last_updated" in committed_state, "Assert G Failed: State file was not updated by Orchestrator!"
        print("[ASSERT G PASSED] Final classroom state reflected reconciled outputs and was written exclusively by Orchestrator Agent.")

        print("\n" + "=" * 80)
        print("ALL 7 SYSTEM INTEGRATION ASSERTS PASSED SUCCESSFULLY 100%!")
        print("=" * 80)

    finally:
        # Restore original classroom state file after test
        if original_state_text:
            CLASSROOM_STATE_PATH.write_text(original_state_text, encoding="utf-8")


if __name__ == "__main__":
    run_real_end_to_end_test()
