import json
import re
from fractions import Fraction
from pathlib import Path
from strands import tool

SAFETY_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "safety_data.json"
)


def load_safety_data() -> dict:
    """Helper to read local safety data JSON file."""
    if not SAFETY_FILE.exists():
        return {"banned_words": [], "grade_reading_limits": {}}
    with open(SAFETY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@tool
def get_safety_rules() -> dict:
    """
    Returns configurable banned word patterns, grade-level reading complexity limits, and nuance triggers.
    Does NOT perform LLM calls or mutate state.
    """
    return load_safety_data()


@tool
def verify_math_expression(expression: str) -> dict:
    """
    Programmatically verifies mathematical equations, fraction equivalences, and arithmetic statements.
    DOES NOT use LLMs for arithmetic verification.
    """
    text = str(expression).strip()
    errors = []

    # Check for direct fraction equality assertions like "1/2 = 3/4" or "2/3 = 4/3"
    # Match patterns like: "a/b = c/d" (ignoring placeholder questions like "?/4" or error-analysis questions asking "Is the student correct?")
    if "is the student correct" not in text.lower() and "misconception" not in text.lower():
        # Match equation pattern: (\d+/\d+)\s*=\s*(\d+/\d+)
        matches = re.findall(r"(\d+/\d+)\s*=\s*(\d+/\d+)", text)
        for f1_str, f2_str in matches:
            try:
                frac1 = Fraction(f1_str)
                frac2 = Fraction(f2_str)
                if frac1 != frac2:
                    errors.append(f"False mathematical assertion: {f1_str} = {f2_str} is mathematically incorrect.")
            except Exception:
                pass

        # Match fraction multiplication equations: (\d+/\d+)\s*[*×]\s*(\d+/\d+)\s*=\s*(\d+/\d+)
        mult_matches = re.findall(r"(\d+/\d+)\s*[*×]\s*(\d+/\d+)\s*=\s*(\d+/\d+)", text)
        for f1_str, f2_str, f3_str in mult_matches:
            try:
                frac1 = Fraction(f1_str)
                frac2 = Fraction(f2_str)
                expected_prod = frac1 * frac2
                actual_prod = Fraction(f3_str)
                if expected_prod != actual_prod:
                    errors.append(f"Incorrect fraction multiplication: {f1_str} * {f2_str} != {f3_str} (expected {expected_prod}).")
            except Exception:
                pass

    return {
        "expression": expression,
        "is_correct": len(errors) == 0,
        "errors": errors
    }
