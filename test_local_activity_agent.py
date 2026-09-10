"""
test_local_activity_agent.py
-----------------------------
Tests the local Qwen3 8B Activity Agent via Ollama across three independent scenarios.

The Activity Agent synthesizes:
  Progress diagnosis + Curriculum decision + Resource constraints
  -> Concrete delivery-ready classroom activity

SCENARIO A — VISUAL / CREATIVE LEARNING NEED
  Grade 3, Math, Fractions introduction
  Diagnosis: struggling, trust issue with part-whole concept (visual difficulty)
  Curriculum: hold / reinforce prerequisite
  Resources: printer + paper AVAILABLE, whiteboard available
  Time: 20 minutes
  → Qwen must reason whether a visual/printable/drawing activity is appropriate.
    It MUST produce actual student instructions and exercises — not a vague suggestion.

SCENARIO B — KNOWLEDGE / PRACTICE REINFORCEMENT
  Grade 6, fractions, adding with unlike denominators
  Diagnosis: developing, LCM and unlike-denominator trouble spots
  Curriculum: branch (reinforce while advancing)
  Resources: printer + paper AVAILABLE, whiteboard available
  Time: 25 minutes
  → Qwen must produce a concrete practice activity targeting LCM / unlike-denominator errors.
    If it chooses a quiz format, actual questions must exist targeting the trouble spot.

SCENARIO C — NON-DIGITAL / PHYSICAL / COLLABORATIVE ACTIVITY
  Grade 8, Mathematics, Algebra linear equations
  Diagnosis: developing, sign-error and transposition trouble spot
  Curriculum: hold / reinforce
  Resources: NO printer, NO tablet, NO TV — only whiteboard + classroom materials
  Time: 30 minutes
  → Qwen must choose an appropriate resource-free/physical/offline/collaborative activity.
    The chosen activity must be executable without digital resources.
    actual student-facing instructions and tasks must be present.

Semantic validation rules:
  - Do NOT assert a specific activity_type must be "drawing", "quiz", or "sports".
  - Instead evaluate: specificity, feasibility, topic-alignment, trouble-spot targeting,
    resource respect, time fit, content presence.

22 assertions per scenario (66 total across 3 scenarios) + guardrail smoke-test.
"""

import json
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.activity_agent import ActivityDesign, apply_activity_guardrails
from agents.local_ollama import design_activity_local, LOCAL_MODEL, PROVIDER

CLASSROOM_STATE_PATH = Path(__file__).resolve().parent / "data" / "classroom_state.json"

# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------

SCENARIO_A = {
    "id"                      : "A",
    "grade"                   : 3,
    "subject"                 : "Math",
    "decided_topic"           : "Fractions - introduction",
    "pacing_decision"         : "hold",
    "trouble_spots"           : ["cannot identify the part vs whole in fraction diagrams",
                                  "confuses numerator and denominator labels"],
    "mastery_estimate"        : "struggling",
    "recommendation_direction": "reteach",
    "recommended_resource"    : "printable_worksheet",  # printer + paper available
    "needs_generation"        : True,
    "available_time_minutes"  : 20,
    # Semantic expectations (not exact assertions)
    "printer_available"       : True,
    "expected_difficulty"     : "scaffolded",          # struggling -> scaffolded
    "expected_trouble_keyword": ["numerator", "denominator", "part", "whole", "fraction"],
}

SCENARIO_B = {
    "id"                      : "B",
    "grade"                   : 6,
    "subject"                 : "Mathematics",
    "decided_topic"           : "Fractions - adding with unlike denominators",
    "pacing_decision"         : "branch",
    "trouble_spots"           : ["adding fractions with unlike denominators",
                                  "finding LCM for denominators"],
    "mastery_estimate"        : "developing",
    "recommendation_direction": "reinforce",
    "recommended_resource"    : "printable_worksheet",  # printer + paper available
    "needs_generation"        : True,
    "available_time_minutes"  : 25,
    # Semantic expectations
    "printer_available"       : True,
    "expected_difficulty"     : "standard",            # developing -> standard
    "expected_trouble_keyword": ["lcm", "denominator", "unlike", "fraction", "common"],
}

SCENARIO_C = {
    "id"                      : "C",
    "grade"                   : 8,
    "subject"                 : "Mathematics",
    "decided_topic"           : "Algebra - linear equations",
    "pacing_decision"         : "hold",
    "trouble_spots"           : ["sign errors when transposing terms across the equals sign",
                                  "forgetting to apply operations to both sides"],
    "mastery_estimate"        : "developing",
    "recommendation_direction": "reinforce",
    "recommended_resource"    : "whiteboard_activity",  # no printer, no tablets, no TV
    "needs_generation"        : True,
    "available_time_minutes"  : 30,
    # Semantic expectations
    "printer_available"       : False,   # must NOT assume printing
    "expected_difficulty"     : "standard",
    "expected_trouble_keyword": ["sign", "transpose", "equation", "algebra",
                                  "both sides", "equals", "linear"],
}

SCENARIOS = [SCENARIO_A, SCENARIO_B, SCENARIO_C]

FORBIDDEN_KEYS = {
    "resource_override", "curriculum_change", "safety_approval",
    "contention_resolution", "lesson_plan_meta", "orchestrator_decision",
}

MASTERY_DIAGNOSIS_TERMS   = ["mastery_estimate", "diagnos", "progress agent"]
PACING_DECISION_TERMS     = ["pacing_decision", "curriculum direction",
                              "advance", "hold", "branch", "reteach curriculum"]


class TestLocalQwenActivityAgent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run design_activity_local once per scenario and cache results."""
        cls._ollama_call_count = 0
        cls._ollama_models     = []
        cls._mtime_before      = (
            CLASSROOM_STATE_PATH.stat().st_mtime
            if CLASSROOM_STATE_PATH.exists() else None
        )
        cls._start_time = time.time()

        original_chat = __import__("ollama").chat

        def spy_chat(*args, **kwargs):
            cls._ollama_call_count += 1
            cls._ollama_models.append(kwargs.get("model", ""))
            return original_chat(*args, **kwargs)

        cls.results = {}

        with patch("agents.local_ollama.ollama.chat", side_effect=spy_chat):
            for sc in SCENARIOS:
                result = design_activity_local(
                    grade                   = sc["grade"],
                    subject                 = sc["subject"],
                    decided_topic           = sc["decided_topic"],
                    pacing_decision         = sc["pacing_decision"],
                    trouble_spots           = sc["trouble_spots"],
                    mastery_estimate        = sc["mastery_estimate"],
                    recommendation_direction= sc["recommendation_direction"],
                    recommended_resource    = sc["recommended_resource"],
                    needs_generation        = sc["needs_generation"],
                    available_time_minutes  = sc["available_time_minutes"],
                )
                cls.results[sc["id"]] = result

        cls._elapsed = time.time() - cls._start_time
        cls._mtime_after = (
            CLASSROOM_STATE_PATH.stat().st_mtime
            if CLASSROOM_STATE_PATH.exists() else None
        )

    # ── 1. Ollama was actually called ─────────────────────────────────────────
    def test_01_ollama_was_called(self):
        self.assertGreaterEqual(self._ollama_call_count, len(SCENARIOS),
            "Ollama was called fewer times than scenarios — some Qwen calls were skipped")

    # ── 2. Model is exactly qwen3:8b ──────────────────────────────────────────
    def test_02_model_is_qwen3_8b(self):
        for m in self._ollama_models:
            self.assertEqual(m, "qwen3:8b",
                f"Expected model 'qwen3:8b', got '{m}'")

    # ── 3. Bedrock NOT used ───────────────────────────────────────────────────
    def test_03_bedrock_not_used(self):
        # design_activity() (Bedrock path) is never called by our adapter
        for sid, res in self.results.items():
            self.assertNotIn("_execution_mode", res,
                f"Scenario {sid}: '_execution_mode' key present — Bedrock path invoked")

    # ── 4. Schema validation ──────────────────────────────────────────────────
    def test_04_schema_validation(self):
        for sid, res in self.results.items():
            try:
                ActivityDesign(**res)
            except Exception as exc:
                self.fail(f"Scenario {sid}: does not conform to ActivityDesign schema: {exc}")

    # ── 5. Grade correct ──────────────────────────────────────────────────────
    def test_05_grade_correct(self):
        for sc in SCENARIOS:
            res = self.results[sc["id"]]
            self.assertEqual(str(res.get("grade")), str(sc["grade"]),
                f"Scenario {sc['id']}: grade mismatch")

    # ── 6. Topic locked to decided_topic ─────────────────────────────────────
    def test_06_topic_lock(self):
        for sc in SCENARIOS:
            res = self.results[sc["id"]]
            self.assertEqual(res.get("topic"), sc["decided_topic"],
                f"Scenario {sc['id']}: topic not locked to decided_topic")

    # ── 7. activity_type locked to recommended_resource ───────────────────────
    def test_07_resource_lock(self):
        for sc in SCENARIOS:
            res = self.results[sc["id"]]
            self.assertEqual(res.get("activity_type"), sc["recommended_resource"],
                f"Scenario {sc['id']}: activity_type not locked to recommended_resource "
                f"(got '{res.get('activity_type')}', expected '{sc['recommended_resource']}')")

    # ── 8. Activity is specific — instructions are non-empty ─────────────────
    def test_08_instructions_present(self):
        for sid, res in self.results.items():
            content = res.get("content", {})
            instr = str(content.get("instructions", "")).strip()
            self.assertGreater(len(instr), 20,
                f"Scenario {sid}: instructions are missing or too vague (len={len(instr)})")

    # ── 9. Activity contains actual items ─────────────────────────────────────
    def test_09_items_present(self):
        for sid, res in self.results.items():
            content = res.get("content", {})
            items = content.get("items", [])
            self.assertGreater(len(items), 0,
                f"Scenario {sid}: content.items is empty — no actual exercises generated")
            for item in items:
                self.assertGreater(len(str(item).strip()), 5,
                    f"Scenario {sid}: item is too short to be a real exercise: '{item}'")

    # ── 10. Activity addresses the trouble spot ───────────────────────────────
    def test_10_targets_trouble_spot(self):
        for sc in SCENARIOS:
            res  = self.results[sc["id"]]
            sid  = sc["id"]
            ts   = str(res.get("targets_trouble_spot", "")).lower()
            instr = str(res.get("content", {}).get("instructions", "")).lower()
            items_text = " ".join(str(i) for i in res.get("content", {}).get("items", [])).lower()
            combined = ts + " " + instr + " " + items_text
            keywords = sc["expected_trouble_keyword"]
            matched  = [kw for kw in keywords if kw in combined]
            self.assertGreater(len(matched), 0,
                f"Scenario {sid}: activity does not address trouble spot.\n"
                f"Expected at least one of {keywords} in content.\n"
                f"targets_trouble_spot: {ts}\n"
                f"instructions snippet: {instr[:200]}")

    # ── 11. Difficulty calibrated to mastery ──────────────────────────────────
    def test_11_difficulty_calibrated(self):
        for sc in SCENARIOS:
            res = self.results[sc["id"]]
            sid = sc["id"]
            diff = res.get("difficulty_level")
            self.assertEqual(diff, sc["expected_difficulty"],
                f"Scenario {sid}: difficulty '{diff}' does not match "
                f"expected '{sc['expected_difficulty']}' for mastery '{sc['mastery_estimate']}'")

    # ── 12. Duration fits session time ────────────────────────────────────────
    def test_12_duration_fits_session(self):
        for sc in SCENARIOS:
            res = self.results[sc["id"]]
            sid = sc["id"]
            est = res.get("estimated_time_minutes", 9999)
            self.assertLessEqual(est, sc["available_time_minutes"],
                f"Scenario {sid}: estimated_time_minutes={est} exceeds "
                f"available_time_minutes={sc['available_time_minutes']}")

    # ── 13. Scenario A: printable resource consistent with printer availability
    def test_13_scenario_a_printable_consistent(self):
        res = self.results["A"]
        # Guardrail 1 locks activity_type to "printable_worksheet"
        # Since printer IS available for A, this is valid
        self.assertEqual(res.get("activity_type"), "printable_worksheet",
            "Scenario A: activity_type should be printable_worksheet (printer available)")

    # ── 14. Scenario B: content has questions targeting LCM/unlike denominators
    def test_14_scenario_b_quiz_targets_lcm(self):
        res = self.results["B"]
        items = res.get("content", {}).get("items", [])
        items_text = " ".join(str(i) for i in items).lower()
        lcm_keywords = ["lcm", "denominator", "unlike", "common denominator", "fraction"]
        matched = [kw for kw in lcm_keywords if kw in items_text]
        self.assertGreater(len(matched), 0,
            f"Scenario B: content items do not target LCM/unlike denominators.\n"
            f"Items: {items}")

    # ── 15. Scenario B: at least 2 distinct exercises present ─────────────────
    def test_15_scenario_b_sufficient_exercises(self):
        res = self.results["B"]
        items = res.get("content", {}).get("items", [])
        self.assertGreaterEqual(len(items), 2,
            f"Scenario B: only {len(items)} exercise(s) — expected at least 2 for reinforcement")

    # ── 16. Scenario C: whiteboard activity — no printable dependency ─────────
    def test_16_scenario_c_no_print_dependency(self):
        res = self.results["C"]
        self.assertEqual(res.get("activity_type"), "whiteboard_activity",
            "Scenario C: activity_type must be whiteboard_activity (no printer available)")
        # Instructions must not require printing
        instr = str(res.get("content", {}).get("instructions", "")).lower()
        self.assertNotIn("print", instr,
            f"Scenario C: instructions require printing but printer is unavailable: {instr[:200]}")

    # ── 17. Scenario C: targets algebra sign/transposition trouble spot ────────
    def test_17_scenario_c_targets_algebra(self):
        res   = self.results["C"]
        items = res.get("content", {}).get("items", [])
        instr = str(res.get("content", {}).get("instructions", "")).lower()
        combined = instr + " " + " ".join(str(i) for i in items).lower()
        algebra_keywords = ["equation", "algebra", "sign", "transpose", "both sides",
                             "solve", "linear", "equals"]
        matched = [kw for kw in algebra_keywords if kw in combined]
        self.assertGreater(len(matched), 0,
            f"Scenario C: activity does not address algebra/sign-error trouble spot.\n"
            f"Expected one of {algebra_keywords}.\nContent: {combined[:300]}")

    # ── 18. Agent does NOT make curriculum pacing decisions ───────────────────
    def test_18_no_pacing_decisions(self):
        for sid, res in self.results.items():
            explanation = str(res.get("explanation", "")).lower()
            for term in ["pacing_decision", "curriculum agent decided", "decided to advance",
                         "decided to hold", "decided to branch"]:
                self.assertNotIn(term, explanation,
                    f"Scenario {sid}: explanation contains curriculum-pacing language: '{term}'")

    # ── 19. Agent does NOT diagnose mastery ───────────────────────────────────
    def test_19_no_mastery_diagnosis(self):
        for sid, res in self.results.items():
            explanation = str(res.get("explanation", "")).lower()
            for term in ["progress agent diagnosed", "diagnos student"]:
                self.assertNotIn(term, explanation,
                    f"Scenario {sid}: explanation contains mastery-diagnosis language: '{term}'")

    # ── 20. Shared state NOT mutated ──────────────────────────────────────────
    def test_20_shared_state_not_mutated(self):
        self.assertEqual(self._mtime_before, self._mtime_after,
            "classroom_state.json was modified during activity agent calls!")

    # ── 21. No forbidden cross-boundary keys ─────────────────────────────────
    def test_21_no_forbidden_keys(self):
        for sid, res in self.results.items():
            present = FORBIDDEN_KEYS & set(res.keys())
            self.assertEqual(present, set(),
                f"Scenario {sid}: forbidden keys found: {present}")

    # ── 22. apply_activity_guardrails() smoke-test ────────────────────────────
    def test_22_guardrails_applied(self):
        poisoned = {
            "grade"               : "6",
            "subject"             : "Mathematics",
            "topic"               : "WRONG TOPIC",         # must be overridden
            "activity_type"       : "tablet_quiz",         # must be overridden to printable_worksheet
            "targets_trouble_spot": "some issue",
            "difficulty_level"    : "standard",
            "content"             : {"instructions": "", "items": []},  # must be filled
            "estimated_time_minutes": 9999,               # must be capped
            "explanation"         : "test",
            "resource_override"   : "ILLEGAL",            # must be stripped
        }
        guarded = apply_activity_guardrails(
            poisoned,
            expected_topic     = "Fractions - adding with unlike denominators",
            expected_resource  = "printable_worksheet",
            available_time_minutes = 25,
        )
        # Guardrail 4: topic lock
        self.assertEqual(guarded["topic"], "Fractions - adding with unlike denominators",
            "Guardrail 4 (topic lock) failed")
        # Guardrail 1: resource lock
        self.assertEqual(guarded["activity_type"], "printable_worksheet",
            "Guardrail 1 (resource lock) failed")
        # Guardrail 2: time cap
        self.assertLessEqual(guarded["estimated_time_minutes"], 25,
            "Guardrail 2 (time fit) failed")
        # Guardrail 3: content presence
        self.assertGreater(len(guarded["content"]["instructions"]), 0,
            "Guardrail 3 (content presence — instructions) failed")
        self.assertGreater(len(guarded["content"]["items"]), 0,
            "Guardrail 3 (content presence — items) failed")
        # Guardrail 5: forbidden key stripped
        self.assertNotIn("resource_override", guarded,
            "Guardrail 5 (boundary strip) failed")


def _print_scenario_report(sid, sc, res):
    print(f"\n{'='*60}")
    print(f"SCENARIO {sid}: Grade {sc['grade']} | {sc['subject']} | {sc['decided_topic']}")
    print(f"{'='*60}")
    print("PROGRESS INPUT:")
    print(f"  mastery_estimate        : {sc['mastery_estimate']}")
    print(f"  recommendation_direction: {sc['recommendation_direction']}")
    print(f"  trouble_spots           : {sc['trouble_spots']}")
    print("CURRICULUM INPUT:")
    print(f"  pacing_decision         : {sc['pacing_decision']}")
    print(f"  decided_topic           : {sc['decided_topic']}")
    print("RESOURCE INPUT:")
    print(f"  recommended_resource    : {sc['recommended_resource']}")
    print(f"  printer_available       : {sc['printer_available']}")
    print(f"  available_time_minutes  : {sc['available_time_minutes']}")
    print("\nACTIVITY RETURNED BY QWEN3 8B:")
    print(json.dumps(res, indent=2))
    content = res.get("content", {})
    print(f"\n  activity_type    : {res.get('activity_type')}")
    print(f"  difficulty_level : {res.get('difficulty_level')}")
    print(f"  estimated_time   : {res.get('estimated_time_minutes')} min")
    print(f"  targets_trouble  : {res.get('targets_trouble_spot')}")
    print(f"\n  INSTRUCTIONS:\n  {content.get('instructions', '')}")
    print(f"\n  EXERCISES/ITEMS ({len(content.get('items', []))} items):")
    for i, item in enumerate(content.get("items", []), 1):
        safe = str(item).encode("utf-8", errors="replace").decode("utf-8")
        print(f"    {i}. {safe}")
    print(f"\n  EXPLANATION: {res.get('explanation', '')}")


def main():
    # Ensure stdout uses UTF-8 so Qwen unicode output (e.g. → \u2192) prints cleanly
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    loader     = unittest.TestLoader()
    suite      = loader.loadTestsFromTestCase(TestLocalQwenActivityAgent)
    runner     = unittest.TextTestRunner(verbosity=2)
    result_obj = runner.run(suite)

    total      = result_obj.testsRun
    failures   = len(result_obj.failures)
    errors     = len(result_obj.errors)
    passed     = total - failures - errors

    print()
    print("=" * 60)
    if result_obj.wasSuccessful():
        print("LOCAL QWEN ACTIVITY AGENT: PASS")
        print(f"Model: {LOCAL_MODEL}")
        print(f"Provider: {PROVIDER}")
        print("Bedrock: NOT USED")
        elapsed    = getattr(TestLocalQwenActivityAgent, "_elapsed", 0.0)
        call_count = getattr(TestLocalQwenActivityAgent, "_ollama_call_count", 0)
        print(f"Total execution time: {elapsed:.1f}s  ({call_count} Ollama calls)")
        print(f"Total assertions: {total}  |  Passed: {passed}  |  Failed: {failures + errors}")
    else:
        print("LOCAL QWEN ACTIVITY AGENT: FAIL")
        print(f"Total assertions: {total}  |  Passed: {passed}  |  Failed: {failures + errors}")
        for name, tb in result_obj.failures + result_obj.errors:
            print(f"\n--- {name} ---")
            print(tb)
    print("=" * 60)

    # Always print per-scenario reports
    results_map = getattr(TestLocalQwenActivityAgent, "results", {})
    sc_map = {sc["id"]: sc for sc in SCENARIOS}
    for sid in ["A", "B", "C"]:
        if sid in results_map and sid in sc_map:
            _print_scenario_report(sid, sc_map[sid], results_map[sid])

    sys.exit(0 if result_obj.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
