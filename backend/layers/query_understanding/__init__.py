import json
import os
from dataclasses import dataclass
from datetime import date
from typing import Optional

from dotenv import load_dotenv

from layers.query_understanding.entity_linker import link_to_metric_catalog
from layers.query_understanding.intent_classifier import classify_intent
from layers.query_understanding.time_parser import parse_time_window
from utils.gemini_client import call_gemini

load_dotenv()

_AMBIGUITY_THRESHOLD = float(os.getenv("AMBIGUITY_THRESHOLD", 0.7))


@dataclass
class StructuredRequest:
    raw_question:        str
    rewritten:           str
    intent:              str
    metrics:             list[str]
    dimensions:          list[str]
    time_window:         dict
    output_type:         str
    ambiguity_score:     float
    prior_request:       Optional[dict]
    clarifying_question: Optional[str] = None


async def understand_query(
    question: str,
    today: date,
    prior_request: dict | None = None,
) -> StructuredRequest:
    """Main entry point for Layer 1 — Query Understanding."""
    intent, confidence = classify_intent(question)
    metrics    = link_to_metric_catalog(question, prior_request)
    time_win   = parse_time_window(question, today, prior_request)
    dimensions = _extract_dimensions(question, prior_request)
    output_t   = _output_type(intent)

    ambiguity_score     = round(1.0 - confidence, 2)
    rewritten           = question
    clarifying_question = None

    # Only call Gemini if the question is genuinely ambiguous
    if ambiguity_score > _AMBIGUITY_THRESHOLD:
        llm_result          = await _llm_understand(question, prior_request, today)
        rewritten           = llm_result.get("rewritten", question)
        clarifying_question = llm_result.get("clarifying_question")

    return StructuredRequest(
        raw_question=question,
        rewritten=rewritten,
        intent=intent,
        metrics=metrics,
        dimensions=dimensions,
        time_window=time_win,
        output_type=output_t,
        ambiguity_score=ambiguity_score,
        prior_request=prior_request,
        clarifying_question=clarifying_question,
    )


def _extract_dimensions(question: str, prior_request: dict | None) -> list[str]:
    from layers.semantic_layer.dimension_hierarchy import VALID_DIMENSIONS
    q = question.lower()

    # Follow-up: inherit dimensions if user says "same breakdown"
    if prior_request and any(p in q for p in ["same breakdown", "same dimension", "by the same"]):
        return prior_request.get("dimensions", [])

    return [col for term, col in VALID_DIMENSIONS.items() if term in q]


def _output_type(intent: str) -> str:
    return {
        "compare":         "chart",
        "breakdown":       "chart",
        "driver_analysis": "both",
        "summary":         "narrative",
        "trend":           "chart",
    }.get(intent, "both")


async def _llm_understand(question: str, prior_request: dict | None, today: date) -> dict:
    context = f"Previous question context: {prior_request.get('raw_question', '')}" if prior_request else ""
    prompt = f"""Today: {today}
{context}
User question: "{question}"

Respond in JSON:
{{
  "rewritten": "<clear, unambiguous restatement of the question with any relative dates resolved>",
  "clarifying_question": "<one short yes/no or choice question if still ambiguous, else null>"
}}"""
    try:
        response = await call_gemini(prompt, json_mode=True)
        return json.loads(response)
    except Exception:
        return {"rewritten": question, "clarifying_question": None}
