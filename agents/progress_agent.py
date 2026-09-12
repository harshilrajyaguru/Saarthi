import json
import os
import time
import traceback
from typing import Literal, Optional, Union
from pydantic import BaseModel, Field

from strands import Agent
from tools.progress_tools import get_history, get_trouble_spot_log


class ProgressDiagnosis(BaseModel):
    grade: str = Field(description="Grade level as a string, e.g. '4'")
    subject: str = Field(description="Subject name, e.g. 'Math'")
    topic: str = Field(description="Current topic name")
    mastery_estimate: Literal["struggling", "developing", "proficient", "mastered"] = Field(
        description="Confidence-weighted estimate of topic mastery"
    )
    trend: Literal["improving", "stagnant", "declining", "insufficient_data"] = Field(
        description="Trend of student performance over recent sessions"
    )
    confidence: Literal["low", "medium", "high"] = Field(
        description="Confidence in the diagnosis based on sample size and evidence"
    )
    trouble_spots: list[str] = Field(
        default_factory=list,
        description="Array of concise conceptual issues or learning gaps identified"
    )
    attention_flag: bool = Field(
        description="Boolean indicating whether urgent teacher/orchestrator attention is flagged"
    )
    recommendation_direction: Literal["advance", "reinforce", "reteach", "insufficient_data"] = Field(
        description="Pedagogical recommendation direction for the Orchestrator"
    )
    explanation: str = Field(
        description="Mandatory single concise sentence explaining the diagnosis referencing actual evidence"
    )


SYSTEM_PROMPT = """
You are Saarthi's Progress Agent.

Your sole responsibility is to transform noisy classroom evidence into a confidence-weighted diagnosis of the current learning state for a specific Grade × Subject.

You MUST perform your diagnostic reasoning in the following EXACT ORDER:

1. Pull history using the get_history tool for the specified grade, subject, and topic.
2. Pull the trouble-spot log using the get_trouble_spot_log tool for the specified grade and subject.
3. Compare today's/latest signals against historical patterns.
4. Determine whether today's result is:
   - consistent with previous sessions
   - improving
   - regressing
   - or a one-off anomaly.
5. Judge evidence/sample quality. Remember: a single data point must NOT produce high confidence.
6. Determine whether today's issue:
   - repeats a known trouble spot from the trouble-spot log
   - represents a new conceptual trouble spot
   - or is incidental/insufficient evidence.
7. Only after completing the reasoning above, determine:
   - mastery_estimate ("struggling" | "developing" | "proficient" | "mastered")
   - trend ("improving" | "stagnant" | "declining" | "insufficient_data")
   - confidence ("low" | "medium" | "high")
   - trouble_spots (array of concise conceptual issues)
   - attention_flag (boolean)
   - recommendation_direction ("advance" | "reinforce" | "reteach" | "insufficient_data")
8. Produce a concise evidence-based explanation referencing the actual evidence used.

HARD BOUNDARIES:
- You diagnose ONLY. You do NOT decide classroom activities, worksheets, quizzes, or teaching methods.
- You do NOT call an Activity Agent or write to shared state.
- recommendation_direction MUST ONLY be one of: "advance", "reinforce", "reteach", "insufficient_data".
- Your explanation MUST be exactly one concise sentence referencing actual evidence used (e.g. scores, session count, specific error patterns). Never use generic templates.
"""

from agents.model_factory import get_saarthi_model
_PROGRESS_MODEL = get_saarthi_model(tier="smart")


def apply_hard_guardrails(diagnosis_data: dict, history_count: int) -> dict:
    """
    Enforces non-negotiable hard guardrails OUTSIDE the LLM reasoning process.

    GUARDRAIL 1 — CONFIDENCE:
    If fewer than 2 historical sessions exist (history_count < 2), confidence MUST be "low".

    GUARDRAIL 2 — ATTENTION FLAG:
    attention_flag = True is allowed ONLY when trend is ("stagnant" OR "declining")
    AND confidence is NOT "low" (i.e. medium or high).
    Otherwise, attention_flag MUST be False.

    GUARDRAIL 3 — AGENT BOUNDARY:
    recommendation_direction can ONLY be "advance", "reinforce", "reteach", or "insufficient_data".
    No activity details or external mutation fields are allowed.
    """
    d = dict(diagnosis_data)

    # GUARDRAIL 1 — CONFIDENCE
    if history_count < 2:
        d["confidence"] = "low"

    # GUARDRAIL 2 — ATTENTION FLAG
    valid_trend = d.get("trend") in ["stagnant", "declining"]
    valid_confidence = d.get("confidence") in ["medium", "high"]
    if valid_trend and valid_confidence:
        d["attention_flag"] = bool(d.get("attention_flag", False))
    else:
        d["attention_flag"] = False

    # GUARDRAIL 3 — AGENT BOUNDARY
    allowed_directions = {"advance", "reinforce", "reteach", "insufficient_data"}
    if d.get("recommendation_direction") not in allowed_directions:
        d["recommendation_direction"] = "insufficient_data"

    forbidden_keys = {"activity", "lesson_plan", "quiz", "worksheet", "teaching_method", "activity_type"}
    for key in list(d.keys()):
        if key in forbidden_keys:
            del d[key]

    return d


def analyze_progress(
    grade: Union[int, str],
    subject: str,
    current_topic: str,
    latest_signals: dict,
    activity_metadata: Optional[dict] = None
) -> dict:
    """
    Executes the Progress Agent diagnosis for a given Grade x Subject with latest signals.
    Routes through Strands Agent → GroqModel → Groq API → openai/gpt-oss-120b.
    Creates a fresh Agent instance per call to support concurrent grade evaluation.
    Applies post-processing hard guardrails outside LLM reasoning.
    Does NOT mutate shared state.
    """
    prompt = f"""
Analyze the learning state for:
- Grade: {grade}
- Subject: {subject}
- Topic: {current_topic}

Latest Signals from current session:
{json.dumps(latest_signals, indent=2)}

Activity Metadata:
{json.dumps(activity_metadata or {}, indent=2)}

First call get_history and get_trouble_spot_log tools to inspect prior session data and known conceptual trouble spots before forming your final structured diagnosis.
"""
    history_res = get_history(grade=grade, subject=subject, topic=current_topic, n=10)
    history_count = history_res.get("count", 0) if isinstance(history_res, dict) else 0

    model_id = getattr(_PROGRESS_MODEL, "model_id", getattr(_PROGRESS_MODEL, "model_name", "unknown"))
    print(f"\n[STRANDS AGENT] Invoking ProgressAgent ({model_id}) for Grade {grade} {subject}...")
    # Fresh Agent per call — avoids ConcurrencyException when multiple grades run concurrently.
    agent = Agent(
        model=_PROGRESS_MODEL,
        system_prompt=SYSTEM_PROMPT,
        tools=[get_history, get_trouble_spot_log],
        structured_output_model=ProgressDiagnosis,
        name="ProgressAgent",
        description="SAARTHI Progress Agent diagnosing learning state from evidence.",
    )
    import time
    t0 = time.time()
    result = agent(prompt)
    elapsed = time.time() - t0
    print(f"[TIMING] ProgressAgent Grade {grade}: {elapsed:.1f}s")

    if hasattr(result, "structured_output") and result.structured_output:
        raw_diagnosis = (
            result.structured_output.model_dump()
            if hasattr(result.structured_output, "model_dump")
            else dict(result.structured_output)
        )
    elif hasattr(result, "message") and result.message:
        text_resp = str(result.message.content if hasattr(result.message, "content") else result.message)
        raw_diagnosis = json.loads(text_resp)
    else:
        raise ValueError(f"ProgressAgent failed to return structured output: {result}")

    final_diagnosis = apply_hard_guardrails(raw_diagnosis, history_count)
    return final_diagnosis