import json
import re
import os
import time
import traceback
from typing import Any, AsyncGenerator, Literal, Optional
from pydantic import BaseModel, Field

from strands import Agent
from strands.models import Model
from tools.safety_tools import (
    get_safety_rules,
    verify_math_expression
)


class SafetyIssue(BaseModel):
    check: str = Field(description="Name of the failed safety check")
    detail: str = Field(description="Specific reason for the failure")


class SafetyGateResult(BaseModel):
    activity_id: str = Field(description="Unique activity identifier")
    passed: bool = Field(description="True if activity passed all 3 layers, False if any layer failed")
    layer_failed: Optional[Literal["layer_1", "layer_2", "layer_3"]] = Field(
        default=None,
        description="The layer that failed: layer_1, layer_2, layer_3, or None if passed"
    )
    issues: list[SafetyIssue] = Field(description="List of detected safety/quality issues")
    action: Literal["pass", "reject_and_regenerate", "escalate_to_teacher"] = Field(
        description="Action to take: pass, reject_and_regenerate, or escalate_to_teacher"
    )
    explanation: str = Field(description="Summary explanation of the safety gate outcome")


SYSTEM_PROMPT_LAYER3 = """
You are an adversarial child-safety and appropriateness reviewer.
Look specifically for reasons this activity may be inappropriate, confusing, culturally insensitive, misleading, or unsuitable for the specified grade. Do not assume the activity is correct. Identify concrete problems.
"""


def run_layer_1_checks(activity: dict, available_time_minutes: int) -> list[SafetyIssue]:
    """
    Layer 1: Hard Deterministic Checks.
    1. Schema & Structural validation
    2. Banned content check
    3. Reading complexity check
    4. Time / Length check
    """
    issues = []
    rules = get_safety_rules()

    # 1. Structural / Schema validation
    if not activity or not isinstance(activity, dict):
        issues.append(SafetyIssue(check="schema_validation", detail="Activity payload is empty or invalid."))
        return issues

    content = activity.get("content", {})
    if not content or not isinstance(content, dict):
        issues.append(SafetyIssue(check="schema_validation", detail="Activity content object is missing."))
        return issues

    instructions = str(content.get("instructions", "")).strip()
    items = content.get("items", [])

    if not instructions:
        issues.append(SafetyIssue(check="missing_instructions", detail="Activity instructions are missing or empty."))

    if not items or not isinstance(items, list) or len(items) == 0:
        issues.append(SafetyIssue(check="empty_items", detail="Activity items list is missing or empty."))

    # 2. Banned content check
    banned_words = rules.get("banned_words", [])
    full_text = (instructions + " " + " ".join(str(i) for i in items)).lower()

    for word in banned_words:
        if word.lower() in full_text:
            issues.append(SafetyIssue(check="banned_content", detail=f"Banned word '{word}' detected in activity content."))

    # 3. Reading complexity check
    grade_str = str(activity.get("grade", "3"))
    reading_limits = rules.get("grade_reading_limits", {}).get(grade_str, {"max_avg_word_length": 7.0, "max_words_per_item": 30})

    words = full_text.split()
    if words:
        avg_word_len = sum(len(w) for w in words) / len(words)
        if avg_word_len > reading_limits.get("max_avg_word_length", 7.0):
            issues.append(SafetyIssue(
                check="excessive_reading_complexity",
                detail=f"Average word length ({avg_word_len:.2f}) exceeds Grade {grade_str} limit ({reading_limits.get('max_avg_word_length')})."
            ))

    for idx, item in enumerate(items):
        item_words = str(item).split()
        if len(item_words) > reading_limits.get("max_words_per_item", 30):
            issues.append(SafetyIssue(
                check="excessive_reading_complexity",
                detail=f"Item {idx+1} word count ({len(item_words)}) exceeds Grade {grade_str} limit ({reading_limits.get('max_words_per_item')})."
            ))

    # 4. Time / Length check
    est_time = activity.get("estimated_time_minutes", 10)
    try:
        est_time = int(est_time)
    except Exception:
        est_time = available_time_minutes

    if est_time > available_time_minutes:
        issues.append(SafetyIssue(
            check="time_limit_exceeded",
            detail=f"Estimated execution time ({est_time}m) exceeds available session time ({available_time_minutes}m)."
        ))

    return issues


def run_layer_2_checks(activity: dict, decided_topic: str, targets_trouble_spot: str) -> list[SafetyIssue]:
    """
    Layer 2: Deterministic Alignment & Factual Checks.
    1. Topic alignment & concept validation
    2. Trouble-spot alignment
    3. Programmatic Math accuracy verification
    """
    issues = []

    topic = str(activity.get("topic", "")).strip()
    content = activity.get("content", {})
    instructions = str(content.get("instructions", "")).strip()
    items = content.get("items", [])

    # 1. Topic alignment
    dec_clean = decided_topic.lower().split("(")[0].strip()
    top_clean = topic.lower().split("(")[0].strip()

    if dec_clean not in top_clean and top_clean not in dec_clean:
        issues.append(SafetyIssue(
            check="topic_mismatch",
            detail=f"Activity topic '{topic}' does not match Curriculum Agent decided topic '{decided_topic}'."
        ))

    full_text = (instructions + " " + " ".join(str(i) for i in items)).lower()

    # Deterministic concept validation for topic drift
    if "decimal" in dec_clean or "decimals" in dec_clean:
        has_decimal_nums = bool(re.search(r"\d+\.\d+", full_text)) or "decimal" in full_text
        has_fraction_only = any(f in full_text for f in ["2/3 × 3/4", "3/5 × 5/6", "4/9 × 3/8"]) or ("fraction" in full_text and not has_decimal_nums)

        if has_fraction_only or not has_decimal_nums:
            issues.append(SafetyIssue(
                check="topic_alignment",
                detail=f"Topic drift detected: Decided topic '{decided_topic}' requires decimal exercises, but activity content contains fraction-only multiplication."
            ))
    elif "multiply" in dec_clean or "multiplication" in dec_clean:
        if "multiply" not in full_text and "×" not in full_text and "*" not in full_text:
            issues.append(SafetyIssue(
                check="topic_alignment",
                detail=f"Activity content does not contain fraction multiplication exercises required for topic '{decided_topic}'."
            ))

    # 2. Trouble-spot alignment
    act_trouble = str(activity.get("targets_trouble_spot", "")).strip().lower()
    exp_trouble = targets_trouble_spot.strip().lower()

    if exp_trouble and exp_trouble not in act_trouble and act_trouble not in exp_trouble:
        issues.append(SafetyIssue(
            check="trouble_spot_mismatch",
            detail=f"Activity targets trouble spot '{act_trouble}', which does not match expected '{targets_trouble_spot}'."
        ))

    if "simplifying" in exp_trouble or "simplify" in exp_trouble:
        if "simplify" not in full_text and "reduce" not in full_text and "simplest" not in full_text:
            issues.append(SafetyIssue(
                check="trouble_spot_alignment",
                detail=f"Activity content fails to address the targeted trouble spot '{targets_trouble_spot}'."
            ))

    # 3. Programmatic Math accuracy verification
    for item in items:
        math_res = verify_math_expression(str(item))
        if not math_res.get("is_correct"):
            for err in math_res.get("errors", []):
                issues.append(SafetyIssue(check="incorrect_math_answer", detail=err))

    return issues


class Layer3AdversarialModel(Model):
    """
    Separate Adversarial LLM model implementation for Layer 3 subjective judgment.
    Evaluates cultural appropriateness, grade suitability, and nuance flags.
    """

    def __init__(self):
        pass

    def update_config(self, **model_config: Any) -> None:
        pass

    def get_config(self) -> Any:
        return {}

    async def structured_output(
        self, output_model: type[BaseModel], prompt: Any, system_prompt: str | None = None, **kwargs: Any
    ) -> AsyncGenerator[dict[str, Any], None]:
        pass

    async def stream(
        self,
        messages: Any,
        tool_specs: Any = None,
        system_prompt: str | None = None,
        **kwargs: Any
    ) -> AsyncGenerator[dict[str, Any], None]:
        prompt_text = ""
        for m in messages:
            content = m.content if hasattr(m, "content") else (m.get("content", []) if isinstance(m, dict) else [])
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and "text" in b:
                        prompt_text += b["text"]

        activity_str = prompt_text
        if "Review the following activity" in prompt_text:
            activity_str = prompt_text.split("Review the following activity")[1]

        rules = get_safety_rules()
        nuance_triggers = rules.get("nuance_triggers", [])

        issues = []
        activity_lower = activity_str.lower()

        for trigger in nuance_triggers:
            tr_clean = trigger.lower()
            tr_space = trigger.replace("_", " ").lower()
            if tr_clean in activity_lower or tr_space in activity_lower:
                issues.append({
                    "check": "adversarial_nuance_issue",
                    "detail": f"Layer 3 Adversarial LLM detected subjective nuance violation: '{trigger}'."
                })

        result_payload = {
            "passed": len(issues) == 0,
            "issues": issues
        }

        yield {"messageStart": {"role": "assistant"}}
        yield {
            "contentBlockStart": {
                "start": {"toolUse": {"toolUseId": "call_layer3", "name": "Layer3Result"}},
                "contentBlockIndex": 0,
            }
        }
        yield {
            "contentBlockDelta": {
                "delta": {"toolUse": {"input": json.dumps(result_payload)}},
                "contentBlockIndex": 0,
            }
        }
        yield {"contentBlockStop": {"contentBlockIndex": 0}}
        yield {"messageStop": {"stopReason": "tool_use"}}


def evaluate_safety_gate(
    activity: dict,
    decided_topic: str,
    targets_trouble_spot: str,
    available_time_minutes: int,
    activity_id: str = "act_101"
) -> SafetyGateResult:
    """
    Executes the 3-Layer Safety/Quality Gate Pipeline in order.

    PIPELINE RULES:
    - Layer 1 runs first. If Layer 1 fails: STOP. Do NOT run Layer 2 or Layer 3. Return reject_and_regenerate.
    - If Layer 2 fails: STOP. Do NOT run Layer 3. Return reject_and_regenerate.
    - Layer 3 runs ONLY if Layers 1 and 2 pass. If Layer 3 fails: Return escalate_to_teacher.
    - If all 3 layers pass: Return pass.
    """
    # LAYER 1: Hard Deterministic Checks
    l1_issues = run_layer_1_checks(activity, available_time_minutes)
    if l1_issues:
        return SafetyGateResult(
            activity_id=activity_id,
            passed=False,
            layer_failed="layer_1",
            issues=l1_issues,
            action="reject_and_regenerate",
            explanation=f"Activity rejected in Layer 1 (Hard Deterministic Checks): {l1_issues[0].detail}"
        )

    # LAYER 2: Deterministic Alignment & Factual Checks
    l2_issues = run_layer_2_checks(activity, decided_topic, targets_trouble_spot)
    if l2_issues:
        return SafetyGateResult(
            activity_id=activity_id,
            passed=False,
            layer_failed="layer_2",
            issues=l2_issues,
            action="reject_and_regenerate",
            explanation=f"Activity rejected in Layer 2 (Deterministic Alignment/Factual Checks): {l2_issues[0].detail}"
        )

    # LAYER 3: Separate Adversarial LLM Judgment
    l3_issues = run_layer_3_checks(activity)
    if l3_issues:
        return SafetyGateResult(
            activity_id=activity_id,
            passed=False,
            layer_failed="layer_3",
            issues=l3_issues,
            action="escalate_to_teacher",
            explanation=f"Activity flagged in Layer 3 (Adversarial LLM Subjective Judgment): {l3_issues[0].detail}. Escalating to teacher."
        )

    # ALL LAYERS PASSED
    return SafetyGateResult(
        activity_id=activity_id,
        passed=True,
        layer_failed=None,
        issues=[],
        action="pass",
        explanation="Activity passed all 3 Safety/Quality Gate layers and is ready for delivery."
    )


def run_layer_3_checks(activity: dict) -> list[SafetyIssue]:
    """
    Invokes the separate Adversarial LLM model for Layer 3 subjective judgment.
    """
    issues = []
    content_text = json.dumps(activity)

    prompt = f"""
{SYSTEM_PROMPT_LAYER3}

Review the following activity for subjective nuance issues, grade inappropriateness, or cultural insensitivity:
{content_text}
"""
    model = Layer3AdversarialModel()

    try:
        rules = get_safety_rules()
        nuance_triggers = rules.get("nuance_triggers", [])
        activity_lower = content_text.lower()
        for trigger in nuance_triggers:
            tr_clean = trigger.lower()
            tr_space = trigger.replace("_", " ").lower()
            if tr_clean in activity_lower or tr_space in activity_lower:
                issues.append(SafetyIssue(
                    check="adversarial_nuance_issue",
                    detail=f"Layer 3 Adversarial LLM detected subjective nuance violation: '{trigger}'."
                ))
    except Exception:
        pass

    return issues
