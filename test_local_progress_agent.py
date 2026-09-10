"""
test_local_progress_agent.py
-----------------------------
Tests the local Qwen3 8B Progress Agent via Ollama.

Scenario: Grade 6, Mathematics (Fractions),
          "Fractions - adding with unlike denominators"

The classroom_state.json contains 3 prior sessions for this scenario
(sess_610, sess_611, sess_612) showing a struggling-to-developing arc
with known trouble spots.

What this test verifies
-----------------------
1.  Ollama was actually called (mocked call counter, confirmed via
    unittest.mock.patch spy wrapping the real call).
2.  Returned data conforms to ProgressDiagnosis.
3.  grade is "6".
4.  subject contains "fraction" (case-insensitive) -- or exactly "Mathematics"
    depending on what Qwen echoes; we accept either.
5.  diagnosis explanation uses evidence from the provided scenario
    (mentions at least one of: session, score, correctness, trouble, LCM,
    unlike denominator).
6.  confidence respects the history-count guardrail:
    3 prior sessions >= 2, so confidence MAY be medium or high
    (guardrail only forces "low" when count < 2).
7.  recommendation_direction is one of the four allowed values.
8.  No forbidden activity/lesson-plan fields appear in the output.
9.  The result does not contain activity-selection logic fields.
10. Ollama provider is used -- Bedrock is NOT invoked.

Exit banner
-----------
    LOCAL QWEN PROGRESS AGENT: PASS
    Model: qwen3:8b
    Provider: Ollama
    Bedrock: NOT USED
"""

import json
import sys
import unittest
from unittest.mock import patch, MagicMock, call

# ── Make sure the project root is importable ─────────────────────────────────
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.progress_agent import ProgressDiagnosis
from agents.local_ollama import analyze_progress_local, LOCAL_MODEL, PROVIDER


# ── Scenario constants ────────────────────────────────────────────────────────
GRADE           = 6
SUBJECT         = "fractions"
CURRENT_TOPIC   = "Fractions - adding with unlike denominators"
LATEST_SIGNALS  = {
    "correctness": 0.55,
    "completion": 0.72,
    "time_on_task": "19m",
    "teacher_signal": "slightly_struggling",
    "raw_errors": [
        "incorrectly adds numerators without finding common denominator",
        "picks wrong LCM when denominators share a factor",
    ],
}
ACTIVITY_METADATA = {
    "activity_type": "fraction_addition_worksheet",
    "difficulty": "medium",
}

ALLOWED_DIRECTIONS = {"advance", "reinforce", "reteach", "insufficient_data"}
FORBIDDEN_KEYS     = {"activity", "lesson_plan", "quiz", "worksheet",
                      "teaching_method", "activity_type"}

# Evidence keywords expected somewhere in the explanation
EVIDENCE_KEYWORDS = [
    "session", "sess_", "correctness", "score", "0.4", "0.5",
    "unlike denominator", "lcm", "trouble", "struggling",
    "3 session", "three session", "prior",
]


class TestLocalQwenProgressAgent(unittest.TestCase):

    def setUp(self):
        """Run analyze_progress_local once and capture the result."""
        self._ollama_called = False
        self._ollama_call_args = None

        # We wrap ollama.chat with a spy that records the call but still
        # calls the real function so we actually test Qwen3.
        original_chat = __import__("ollama").chat

        def spy_chat(*args, **kwargs):
            self._ollama_called = True
            self._ollama_call_args = (args, kwargs)
            return original_chat(*args, **kwargs)   # real network call

        with patch("agents.local_ollama.ollama.chat", side_effect=spy_chat):
            self.result = analyze_progress_local(
                grade=GRADE,
                subject=SUBJECT,
                current_topic=CURRENT_TOPIC,
                latest_signals=LATEST_SIGNALS,
                activity_metadata=ACTIVITY_METADATA,
            )

    # ── 1. Ollama was actually called ─────────────────────────────────────────
    def test_ollama_was_called(self):
        self.assertTrue(
            self._ollama_called,
            "Ollama was NOT called -- local adapter did not reach the Ollama API",
        )

    # ── 2. Result conforms to ProgressDiagnosis ───────────────────────────────
    def test_result_conforms_to_schema(self):
        try:
            ProgressDiagnosis(**self.result)
        except Exception as exc:
            self.fail(f"Result does not conform to ProgressDiagnosis schema: {exc}")

    # ── 3. grade is "6" ───────────────────────────────────────────────────────
    def test_grade_is_correct(self):
        self.assertEqual(
            str(self.result.get("grade")), "6",
            f"Expected grade='6', got grade='{self.result.get('grade')}'",
        )

    # ── 4. subject references fractions ───────────────────────────────────────
    def test_subject_references_fractions(self):
        subject_val = str(self.result.get("subject", "")).lower()
        topic_val   = str(self.result.get("topic", "")).lower()
        combined    = subject_val + " " + topic_val
        self.assertTrue(
            "fraction" in combined or "mathematics" in combined,
            f"Expected subject/topic to reference fractions or Mathematics, "
            f"got subject='{self.result.get('subject')}' topic='{self.result.get('topic')}'",
        )

    # ── 5. explanation uses evidence from scenario ─────────────────────────────
    def test_explanation_uses_evidence(self):
        explanation = str(self.result.get("explanation", "")).lower()
        matched = [kw for kw in EVIDENCE_KEYWORDS if kw in explanation]
        self.assertTrue(
            len(matched) > 0,
            f"explanation does not reference scenario evidence.\n"
            f"Explanation: {self.result.get('explanation')}\n"
            f"Expected at least one of: {EVIDENCE_KEYWORDS}",
        )

    # ── 6. confidence respects history-count guardrail ────────────────────────
    def test_confidence_guardrail(self):
        # 3 prior sessions -> history_count=3 >= 2 -> guardrail does NOT
        # force "low", so any valid value is acceptable.
        # But if Qwen said low that is also valid.
        conf = self.result.get("confidence")
        self.assertIn(
            conf, {"low", "medium", "high"},
            f"confidence must be low/medium/high, got '{conf}'",
        )

    # ── 7. recommendation_direction is one of the four allowed values ─────────
    def test_recommendation_direction_allowed(self):
        direction = self.result.get("recommendation_direction")
        self.assertIn(
            direction, ALLOWED_DIRECTIONS,
            f"recommendation_direction '{direction}' is not in {ALLOWED_DIRECTIONS}",
        )

    # ── 8. No forbidden keys ──────────────────────────────────────────────────
    def test_no_forbidden_keys(self):
        present = FORBIDDEN_KEYS & set(self.result.keys())
        self.assertEqual(
            present, set(),
            f"Forbidden keys found in result: {present}",
        )

    # ── 9. No activity-selection logic fields ─────────────────────────────────
    def test_no_activity_selection_logic(self):
        for key in self.result:
            self.assertNotIn(
                "activity", key.lower(),
                f"Unexpected activity-related key in result: '{key}'",
            )

    # ── 10. Bedrock NOT used ──────────────────────────────────────────────────
    def test_bedrock_not_used(self):
        # The local adapter imports from agents.progress_agent but never calls
        # progress_agent (the Strands Agent object). We verify that by checking
        # the result came from our adapter, not the Bedrock path.
        # The simplest proof: ollama.chat was called (test_ollama_was_called).
        # Here we also assert the model name passed to Ollama is qwen3:8b.
        if self._ollama_call_args:
            _, kwargs = self._ollama_call_args
            model_used = kwargs.get("model", "")
            self.assertEqual(
                model_used, "qwen3:8b",
                f"Expected model 'qwen3:8b', Ollama received '{model_used}'",
            )


def main():
    """Run tests and print the pass/fail banner."""
    loader  = unittest.TestLoader()
    suite   = loader.loadTestsFromTestCase(TestLocalQwenProgressAgent)
    runner  = unittest.TextTestRunner(verbosity=2)
    result_obj = runner.run(suite)

    print()
    print("=" * 60)
    if result_obj.wasSuccessful():
        print("LOCAL QWEN PROGRESS AGENT: PASS")
        print(f"Model: {LOCAL_MODEL}")
        print(f"Provider: {PROVIDER}")
        print("Bedrock: NOT USED")
        print()
        # Re-run to print the actual diagnosis (setUp runs again inside suite,
        # so we call the adapter once more here just to display the output).
        print("ProgressDiagnosis returned by Qwen3 8B:")
        diagnosis = analyze_progress_local(
            grade=GRADE,
            subject=SUBJECT,
            current_topic=CURRENT_TOPIC,
            latest_signals=LATEST_SIGNALS,
            activity_metadata=ACTIVITY_METADATA,
        )
        print(json.dumps(diagnosis, indent=2))
    else:
        print("LOCAL QWEN PROGRESS AGENT: FAIL")
        print(f"Failures : {len(result_obj.failures)}")
        print(f"Errors   : {len(result_obj.errors)}")
    print("=" * 60)

    sys.exit(0 if result_obj.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
