import json
from pathlib import Path
from pydantic import BaseModel
from strands.models import BedrockModel

from tools.curriculum_tools import get_syllabus_position, get_prerequisite_map
from agents.curriculum_agent import (
    reconcile_curriculum,
    curriculum_agent,
    apply_curriculum_guardrails,
    CurriculumDecision
)

CLASSROOM_STATE_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "classroom_state.json"
)


def test_bedrock_configuration():
    print("=" * 60)
    print("TEST 1: VERIFYING BEDROCK MODEL CONFIGURATION & TOOLS")
    print("=" * 60)

    # 1. Verify model instance & configuration
    assert isinstance(curriculum_agent.model, BedrockModel), "Failed: curriculum_agent.model must be an instance of BedrockModel"
    cfg = curriculum_agent.model.get_config()
    
    assert cfg.get("model_id") == "global.anthropic.claude-sonnet-4-6", f"Failed: model_id must be global.anthropic.claude-sonnet-4-6, got {cfg.get('model_id')}"
    assert cfg.get("region_name", "us-east-1") == "us-east-1", f"Failed: region_name must be us-east-1"

    print(f"  [OK] Model Class: {curriculum_agent.model.__class__.__name__}")
    print(f"  [OK] Model ID: {cfg.get('model_id')}")
    print(f"  [OK] Region Name: {cfg.get('region_name', 'us-east-1')}")

    # 2. Verify tool definitions registered on agent
    tool_names = curriculum_agent.tool_names
    assert "get_syllabus_position" in tool_names, "Failed: get_syllabus_position missing from tool_names"
    assert "get_prerequisite_map" in tool_names, "Failed: get_prerequisite_map missing from tool_names"
    print(f"  [OK] Registered Agent Tool Names: {tool_names}")

    # 3. Verify Agent metadata
    assert curriculum_agent.name == "CurriculumAgent", "Failed: Agent name must be CurriculumAgent"
    print(f"  [OK] Strands Agent Name: {curriculum_agent.name}")

    print("\nSUCCESS: Bedrock model configuration & tools verified!\n")


def test_deterministic_guardrails():
    print("=" * 60)
    print("TEST 2: VERIFYING DETERMINISTIC GUARDRAILS")
    print("=" * 60)

    # Test invalid pacing decision correction
    bad_decision = {
        "grade": "4",
        "subject": "Math",
        "syllabus_topic": "Fractions",
        "decided_topic": "Fractions",
        "pacing_decision": "INVALID_PACING",
        "is_blocking_prerequisite": True,
        "explanation": "Test explanation",
        "activity": "illegal_worksheet_recommendation",
        "resource": "illegal_tablet_recommendation"
    }

    guarded = apply_curriculum_guardrails(
        bad_decision,
        grade="4",
        subject="Math",
        current_topic="Fractions",
        progress_diagnosis={},
        session_constraints={}
    )

    assert guarded["pacing_decision"] in ["advance", "hold", "branch"], "Failed: Invalid pacing decision was not corrected"
    assert "activity" not in guarded, "Failed: Guardrails did not strip illegal cross-boundary key 'activity'"
    assert "resource" not in guarded, "Failed: Guardrails did not strip illegal cross-boundary key 'resource'"
    print("  [OK] Guardrails corrected invalid pacing decision to allowed enum.")
    print("  [OK] Guardrails stripped illegal cross-boundary keys ('activity', 'resource').")

    print("\nSUCCESS: Deterministic guardrails verified!\n")


def test_curriculum_scenarios():
    print("=" * 60)
    print("TEST 3: RUNNING CURRICULUM SCENARIO TEST SUITE")
    print("=" * 60)

    mtime_before = CLASSROOM_STATE_PATH.stat().st_mtime if CLASSROOM_STATE_PATH.exists() else None

    scenarios = [
        {
            "id": "SCENARIO 1",
            "name": "Students on pace -> advance",
            "grade": 4,
            "subject": "Math",
            "current_topic": "Equivalent fractions",
            "progress_diagnosis": {
                "mastery_estimate": "proficient",
                "trend": "improving",
                "confidence": "high",
                "trouble_spots": [],
                "attention_flag": False
            },
            "session_constraints": {"available_time": "30m"},
            "teacher_constraints": {},
            "expected_pacing": "advance",
            "expected_blocking": False
        },
        {
            "id": "SCENARIO 2",
            "name": "Prerequisite trouble spot directly blocks next topic -> hold",
            "grade": 4,
            "subject": "Math",
            "current_topic": "Equivalent fractions",
            "progress_diagnosis": {
                "mastery_estimate": "struggling",
                "trend": "stagnant",
                "confidence": "medium",
                "trouble_spots": ["confusing numerator/denominator when scaling"],
                "attention_flag": True
            },
            "session_constraints": {"available_time": "30m"},
            "teacher_constraints": {},
            "expected_pacing": "hold",
            "expected_blocking": True
        },
        {
            "id": "SCENARIO 3",
            "name": "Prerequisite issue exists but can be fixed briefly -> branch",
            "grade": 5,
            "subject": "Math",
            "current_topic": "Decimals - addition",
            "progress_diagnosis": {
                "mastery_estimate": "developing",
                "trend": "improving",
                "confidence": "medium",
                "trouble_spots": ["decimal point alignment in simple carrying"],
                "attention_flag": False
            },
            "session_constraints": {"available_time": "45m"},
            "teacher_constraints": {},
            "expected_pacing": "branch",
            "expected_blocking": False
        },
        {
            "id": "SCENARIO 4",
            "name": "Urgent exam/syllabus deadline -> verify teacher constraint considered",
            "grade": 6,
            "subject": "Math",
            "current_topic": "Algebra - linear equations",
            "progress_diagnosis": {
                "mastery_estimate": "developing",
                "trend": "stagnant",
                "confidence": "medium",
                "trouble_spots": ["sign errors in multi-step equations"],
                "attention_flag": False
            },
            "session_constraints": {"available_time": "30m"},
            "teacher_constraints": {"exam_deadline": "In 2 days - must cover linear equations"},
            "expected_pacing": "branch",
            "expected_blocking": False
        },
        {
            "id": "SCENARIO 5",
            "name": "Trouble spot is unrelated to next syllabus topic -> advance",
            "grade": 3,
            "subject": "Math",
            "current_topic": "Addition and Subtraction",
            "progress_diagnosis": {
                "mastery_estimate": "developing",
                "trend": "improving",
                "confidence": "medium",
                "trouble_spots": ["word problem reading comprehension"],
                "attention_flag": False
            },
            "session_constraints": {"available_time": "30m"},
            "teacher_constraints": {},
            "expected_pacing": "advance",
            "expected_blocking": False
        }
    ]

    forbidden_keys = {"activity", "worksheet", "quiz", "lesson_plan", "teaching_method", "resource"}

    for tc in scenarios:
        print(f"\n--- Running {tc['name']} ---")
        decision = reconcile_curriculum(
            grade=tc["grade"],
            subject=tc["subject"],
            current_topic=tc["current_topic"],
            progress_diagnosis=tc["progress_diagnosis"],
            session_constraints=tc["session_constraints"],
            teacher_constraints=tc["teacher_constraints"]
        )

        print(f"Execution Mode: [{decision.get('_execution_mode')}]")
        print("Curriculum Decision:")
        print(json.dumps({k: v for k, v in decision.items() if k != "_execution_mode"}, indent=2))

        # Assertions
        assert decision.get("pacing_decision") == tc["expected_pacing"], (
            f"Failed {tc['id']}: expected pacing '{tc['expected_pacing']}', got '{decision.get('pacing_decision')}'"
        )
        assert decision.get("is_blocking_prerequisite") == tc["expected_blocking"], (
            f"Failed {tc['id']}: expected blocking {tc['expected_blocking']}, got {decision.get('is_blocking_prerequisite')}"
        )

        for fk in forbidden_keys:
            assert fk not in decision, f"Boundary Violation: Output contains forbidden key '{fk}'"

        if tc["id"] == "SCENARIO 4":
            assert "exam" in decision.get("explanation", "").lower() or "deadline" in decision.get("explanation", "").lower(), (
                "Failed SCENARIO 4: Explanation must explicitly reference the teacher's exam constraint."
            )

        print(f"VERIFIED {tc['id']}: Output matches expected contract and respects three-way boundary!")

    # Verify state integrity
    mtime_after = CLASSROOM_STATE_PATH.stat().st_mtime if CLASSROOM_STATE_PATH.exists() else None
    assert mtime_before == mtime_after, "Failed: classroom_state.json was modified!"
    print("\nVERIFIED STATE INTEGRITY: Shared classroom state was NOT mutated during execution.")


def test_live_bedrock_invocation():
    print("\n" + "=" * 60)
    print("LIVE_BEDROCK TEST: EXPLICIT BEDROCK CALL ATTEMPT")
    print("=" * 60)

    prompt = """
Reconcile curriculum direction for:
- Grade: 4
- Subject: Math
- Current Topic: Equivalent fractions

Progress Agent Diagnosis:
{
  "mastery_estimate": "proficient",
  "trend": "improving",
  "confidence": "high",
  "trouble_spots": [],
  "attention_flag": false
}

Session Constraints:
{
  "available_time": "30m"
}

Teacher Constraints: {}

First call get_syllabus_position and get_prerequisite_map to inspect syllabus position and prerequisite dependencies before making your pacing decision.
"""
    cfg = curriculum_agent.model.get_config()
    print(f"Attempting live invocation on model: {cfg.get('model_id')} (Region: {cfg.get('region_name', 'us-east-1')})...")

    try:
        res = curriculum_agent(prompt)
        print("\n[LIVE_BEDROCK] SUCCESS! Real Bedrock response received:")
        if hasattr(res, "structured_output") and res.structured_output:
            print(json.dumps(res.structured_output.model_dump() if hasattr(res.structured_output, "model_dump") else dict(res.structured_output), indent=2))
        else:
            print(res)
    except Exception as e:
        print(f"\n[LIVE_BEDROCK] API EXCEPTION ENCOUNTERED ({type(e).__name__}):")
        print(f"  Error Detail: {e}")
        print("  Note: Account authorization / AWS Bedrock credentials required for live execution.")


if __name__ == "__main__":
    test_bedrock_configuration()
    test_deterministic_guardrails()
    test_curriculum_scenarios()
    test_live_bedrock_invocation()
