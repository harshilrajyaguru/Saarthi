"""
test_local_curriculum_agent.py
-------------------------------
Tests the local Qwen3 8B Curriculum Agent via Ollama.

Scenario: Grade 6, Mathematics (Fractions)
  Current topic : Fractions - adding with unlike denominators
  Next syllabus : Fractions - subtracting with unlike denominators
  Progress diagnosis (from the validated Progress Agent):
    mastery_estimate       : developing
    trend                  : improving
    confidence             : medium
    trouble_spots          : ["adding fractions with unlike denominators",
                              "finding LCM for denominators"]
    recommendation_direction: reinforce
  Session constraints : 40 minutes available
  Teacher constraints : none (forces curriculum agent to decide autonomously)

What this test verifies (13 assertions + 1 semantic check)
----------------------------------------------------------
1.  Ollama was actually called.
2.  The model used was exactly qwen3:8b.
3.  Bedrock was NOT used.
4.  Output validates against CurriculumDecision schema.
5.  grade is "6".
6.  subject/topic reference Mathematics / fractions.
7.  The pacing_decision is logically consistent with the Progress diagnosis
    (developing + reinforce -> hold or branch, NOT advance).
8.  explanation references actual curriculum evidence (prerequisites,
    syllabus, trouble spots, time, mastery/trend).
9.  The agent did NOT select a specific activity.
10. The agent did NOT allocate resources.
11. The agent did NOT mutate shared state (classroom_state.json mtime check).
12. No forbidden activity/resource fields appear.
13. Existing apply_curriculum_guardrails() still applies correctly.

Banner:
    LOCAL QWEN CURRICULUM AGENT: PASS
    Model: qwen3:8b
    Provider: Ollama
    Bedrock: NOT USED
"""

import json
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.curriculum_agent import CurriculumDecision, apply_curriculum_guardrails
from agents.local_ollama import reconcile_curriculum_local, LOCAL_MODEL, PROVIDER

# ---------------------------------------------------------------------------
# Scenario constants
# ---------------------------------------------------------------------------
GRADE         = 6
SUBJECT       = "fractions"
CURRENT_TOPIC = "Fractions - adding with unlike denominators"

# Progress diagnosis produced by the validated Qwen3 8B Progress Agent
PROGRESS_DIAGNOSIS = {
    "grade": "6",
    "subject": "fractions",
    "topic": "Fractions - adding with unlike denominators",
    "mastery_estimate": "developing",
    "trend": "improving",
    "confidence": "medium",
    "trouble_spots": [
        "adding fractions with unlike denominators",
        "finding LCM for denominators",
    ],
    "attention_flag": False,
    "recommendation_direction": "reinforce",
    "explanation": (
        "Correctness improved from 0.42 (sess_610) to 0.58 (sess_612) but "
        "regressed slightly to 0.55 in the latest session, with persistent "
        "trouble spots matching historical patterns of incorrect LCM selection "
        "and numerator addition errors."
    ),
}

SESSION_CONSTRAINTS  = {"available_time": "40m"}
TEACHER_CONSTRAINTS  = {}   # no deadline -- agent must reason autonomously

CLASSROOM_STATE_PATH = Path(__file__).resolve().parent / "data" / "classroom_state.json"

ALLOWED_PACING     = {"advance", "hold", "branch"}
FORBIDDEN_KEYS     = {
    "activity", "worksheet", "quiz", "lesson_plan",
    "teaching_method", "resource", "recommended_resource",
    "safety_approval", "state_mutation",
}

# Evidence keywords expected somewhere in the explanation
EVIDENCE_KEYWORDS = [
    "prerequisite", "lcm", "unlike denominator", "fraction", "trouble",
    "developing", "improving", "40m", "40 min", "session", "syllabus",
    "reinforc", "finding lcm", "mastery",
]

# Pacing decisions that are logically consistent with a "developing + reinforce"
# diagnosis (advance would be wrong here).
CONSISTENT_PACING = {"hold", "branch"}


class TestLocalQwenCurriculumAgent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run reconcile_curriculum_local ONCE and cache result for all tests."""
        cls._ollama_called   = False
        cls._ollama_model    = None
        cls._mtime_before    = (
            CLASSROOM_STATE_PATH.stat().st_mtime
            if CLASSROOM_STATE_PATH.exists() else None
        )
        cls._start_time = time.time()

        original_chat = __import__("ollama").chat

        def spy_chat(*args, **kwargs):
            cls._ollama_called = True
            cls._ollama_model  = kwargs.get("model", "")
            return original_chat(*args, **kwargs)

        with patch("agents.local_ollama.ollama.chat", side_effect=spy_chat):
            cls.result = reconcile_curriculum_local(
                grade=GRADE,
                subject=SUBJECT,
                current_topic=CURRENT_TOPIC,
                progress_diagnosis=PROGRESS_DIAGNOSIS,
                session_constraints=SESSION_CONSTRAINTS,
                teacher_constraints=TEACHER_CONSTRAINTS,
            )

        cls._elapsed = time.time() - cls._start_time
        cls._mtime_after = (
            CLASSROOM_STATE_PATH.stat().st_mtime
            if CLASSROOM_STATE_PATH.exists() else None
        )

    # ── 1. Ollama was actually called ─────────────────────────────────────────
    def test_01_ollama_was_called(self):
        self.assertTrue(
            self._ollama_called,
            "Ollama was NOT called -- local adapter did not reach the Ollama API",
        )

    # ── 2. Model used was exactly qwen3:8b ────────────────────────────────────
    def test_02_model_is_qwen3_8b(self):
        self.assertEqual(
            self._ollama_model, "qwen3:8b",
            f"Expected model 'qwen3:8b', Ollama received '{self._ollama_model}'",
        )

    # ── 3. Bedrock was NOT used ───────────────────────────────────────────────
    def test_03_bedrock_not_used(self):
        # Proof: Ollama was called (test_01) and the result has no _execution_mode
        # key set by the Bedrock path in reconcile_curriculum().
        self.assertNotIn(
            "_execution_mode", self.result,
            "Result contains '_execution_mode' -- the Bedrock reconcile_curriculum() path was invoked",
        )

    # ── 4. Output validates against CurriculumDecision schema ─────────────────
    def test_04_schema_validation(self):
        try:
            CurriculumDecision(**self.result)
        except Exception as exc:
            self.fail(f"Result does not conform to CurriculumDecision schema: {exc}")

    # ── 5. grade is "6" ───────────────────────────────────────────────────────
    def test_05_grade_is_correct(self):
        self.assertEqual(
            str(self.result.get("grade")), "6",
            f"Expected grade='6', got grade='{self.result.get('grade')}'",
        )

    # ── 6. subject/topic reference fractions ──────────────────────────────────
    def test_06_subject_and_topic_correct(self):
        subject_val = str(self.result.get("subject", "")).lower()
        topic_val   = str(self.result.get("decided_topic", "")).lower()
        combined    = subject_val + " " + topic_val
        self.assertTrue(
            "fraction" in combined or "mathematics" in combined or "math" in combined,
            f"Expected subject/topic to reference fractions/math, "
            f"got subject='{self.result.get('subject')}' decided_topic='{self.result.get('decided_topic')}'",
        )

    # ── 7. pacing_decision is logically consistent with Progress diagnosis ─────
    def test_07_pacing_consistent_with_diagnosis(self):
        pacing = self.result.get("pacing_decision")
        self.assertIn(
            pacing, ALLOWED_PACING,
            f"pacing_decision '{pacing}' is not in {ALLOWED_PACING}",
        )
        # With mastery=developing + recommendation_direction=reinforce,
        # advancing past the current topic would be the wrong decision.
        self.assertIn(
            pacing, CONSISTENT_PACING,
            f"pacing_decision '{pacing}' is inconsistent with a 'developing + reinforce' "
            f"Progress diagnosis -- expected 'hold' or 'branch'.",
        )

    # ── 8. explanation references actual curriculum evidence ──────────────────
    def test_08_explanation_references_evidence(self):
        explanation = str(self.result.get("explanation", "")).lower()
        matched = [kw for kw in EVIDENCE_KEYWORDS if kw in explanation]
        self.assertTrue(
            len(matched) > 0,
            f"explanation does not reference scenario evidence.\n"
            f"Explanation: {self.result.get('explanation')}\n"
            f"Expected at least one of: {EVIDENCE_KEYWORDS}",
        )

    # ── 9. Agent did NOT select a specific activity ───────────────────────────
    def test_09_no_specific_activity(self):
        explanation = str(self.result.get("explanation", "")).lower()
        decided     = str(self.result.get("decided_topic", "")).lower()
        activity_terms = [
            "worksheet", "quiz", "game", "video", "lesson plan",
            "group work", "flashcard", "drill", "tablet activity",
        ]
        for term in activity_terms:
            self.assertNotIn(
                term, explanation + decided,
                f"Agent crossed the boundary: found activity-selection term '{term}' in output",
            )

    # ── 10. Agent did NOT allocate resources ──────────────────────────────────
    def test_10_no_resource_allocation(self):
        explanation = str(self.result.get("explanation", "")).lower()
        resource_terms = ["tablet", "printer", "tv screen", "projector", "allocat"]
        for term in resource_terms:
            self.assertNotIn(
                term, explanation,
                f"Agent crossed the boundary: found resource-allocation term '{term}' in explanation",
            )

    # ── 11. Shared state was NOT mutated ──────────────────────────────────────
    def test_11_shared_state_not_mutated(self):
        self.assertEqual(
            self._mtime_before, self._mtime_after,
            "classroom_state.json was modified during the curriculum agent call!",
        )

    # ── 12. No forbidden keys ─────────────────────────────────────────────────
    def test_12_no_forbidden_keys(self):
        present = FORBIDDEN_KEYS & set(self.result.keys())
        self.assertEqual(
            present, set(),
            f"Forbidden cross-boundary keys found in result: {present}",
        )

    # ── 13. apply_curriculum_guardrails() still applies ───────────────────────
    def test_13_guardrails_applied(self):
        # Inject a poisoned decision and verify guardrails strip it correctly.
        poisoned = {
            "grade": "6",
            "subject": "fractions",
            "syllabus_topic": "Fractions - subtracting with unlike denominators",
            "decided_topic": "Fractions - reinforcement",
            "pacing_decision": "INVALID_PACING",
            "is_blocking_prerequisite": True,
            "explanation": "Poisoned test explanation.",
            "activity": "illegal_worksheet",
            "resource": "illegal_tablet",
        }
        guarded = apply_curriculum_guardrails(
            poisoned,
            grade="6",
            subject="fractions",
            current_topic=CURRENT_TOPIC,
            progress_diagnosis=PROGRESS_DIAGNOSIS,
            session_constraints=SESSION_CONSTRAINTS,
        )
        self.assertIn(
            guarded["pacing_decision"], ALLOWED_PACING,
            f"Guardrail did not fix invalid pacing_decision",
        )
        self.assertNotIn("activity", guarded, "Guardrail failed to strip 'activity' key")
        self.assertNotIn("resource", guarded, "Guardrail failed to strip 'resource' key")


def main():
    loader     = unittest.TestLoader()
    suite      = loader.loadTestsFromTestCase(TestLocalQwenCurriculumAgent)
    runner     = unittest.TextTestRunner(verbosity=2)
    result_obj = runner.run(suite)

    print()
    print("=" * 60)
    if result_obj.wasSuccessful():
        print("LOCAL QWEN CURRICULUM AGENT: PASS")
        print(f"Model: {LOCAL_MODEL}")
        print(f"Provider: {PROVIDER}")
        print("Bedrock: NOT USED")
        print()
        elapsed = getattr(TestLocalQwenCurriculumAgent, "_elapsed", 0.0)
        print(f"Execution time (Ollama call): {elapsed:.1f}s")
        print()
        print("CurriculumDecision returned by Qwen3 8B:")
        # Print the already-computed result from setUpClass
        result = TestLocalQwenCurriculumAgent.result
        print(json.dumps(result, indent=2))
    else:
        print("LOCAL QWEN CURRICULUM AGENT: FAIL")
        print(f"Failures : {len(result_obj.failures)}")
        print(f"Errors   : {len(result_obj.errors)}")
        for name, tb in result_obj.failures + result_obj.errors:
            print(f"\n--- {name} ---")
            print(tb)
    print("=" * 60)

    sys.exit(0 if result_obj.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
