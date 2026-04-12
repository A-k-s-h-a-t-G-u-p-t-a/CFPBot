import json

from agents.reasoning_chain import ReasoningResult
from utils.gemini_client import call_gemini

_SYSTEM = """You are an e-commerce data analyst producing executive summaries.

You receive pre-calculated structured findings. Never recalculate or invent numbers.

Rules:
1. Use EXACTLY the numbers provided — do not round or modify them
2. Lead with the most important number first
3. Write in plain English — no SQL, no column names, no jargon
4. Be concise, but you may use as many sentences as needed to explain the finding clearly
5. End with one short follow-up question the user might want to ask next
"""

_INTENT_VOICE = {
    "driver_analysis": "Focus on the root cause. State which dimension drove the change and by how much (quantify with %).",
    "breakdown":       "Lead with the biggest contributor. If one group dominates (>40%), flag the concentration risk.",
    "compare":         "State the winner first, then the delta and % change. Note if the difference is statistically meaningful (>=5%).",
    "summary":         "Use a natural, conversational tone. Summarize the most useful finding first, then add context if it helps.",
}


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```json"):
        text = text.replace("```json", "", 1)
    elif text.startswith("```"):
        text = text.replace("```", "", 1)
    text = text.removesuffix("```")
    return json.loads(text.strip())


async def generate_response(
    question: str,
    reasoning: ReasoningResult,
    metric_label: str,
    rag_context: str = "",
) -> dict:
    """
    Generates the final plain-English response from a ReasoningResult.
    The LLM reads pre-computed facts — it never recalculates.
    """
    # RAG path (definitions / policy questions)
    if rag_context and not reasoning.narrative_context.get("total_current"):
        prompt = f"""Question: {question}

Relevant documentation:
{rag_context}

Explain clearly and naturally. Keep it brief unless the context needs more detail. Suggest one follow-up question.

Respond in JSON: {{"answer": "...", "follow_up": "..."}}"""
        try:
            result = _parse_json(await call_gemini(prompt, system=_SYSTEM, json_mode=True))
            return _build_response(result, reasoning, metric_label)
        except Exception as e:
            print(f"[generator error] {e}")

    # Intent-specific voice instruction
    voice = _INTENT_VOICE.get(reasoning.intent, "")

    prompt = f"""Question: {question}
Metric: {metric_label}
Intent type: {reasoning.intent}
{voice}

Pre-calculated findings (use these numbers exactly):
{json.dumps(reasoning.narrative_context, indent=2, default=str)}

Write a concise, natural answer that sounds like a capable analyst, not a template. If the result is simple, keep it short; if it needs context, explain it.

End with one follow-up question.

Respond in JSON: {{"answer": "...", "follow_up": "...", "anomaly_flag": "..." or null}}"""

    try:
        result = _parse_json(await call_gemini(prompt, system=_SYSTEM, json_mode=True))
    except Exception as e:
        print(f"[generator error] {e}")
        result = {}

    return _build_response(result, reasoning, metric_label)


def _build_response(result: dict, reasoning: ReasoningResult, metric_label: str) -> dict:
    return {
        "answer":        result.get("answer") or str(reasoning.narrative_context),
        "chart_type":    reasoning.chart_spec.get("type") if reasoning.chart_spec else None,
        "chart_data":    reasoning.chart_spec,
        "metric_used":   metric_label,
        "source_tables": ["orders"],
        "follow_up":     result.get("follow_up", "Would you like to explore further?"),
        "confidence":    0.9,
        "anomaly_flag":  result.get("anomaly_flag") or reasoning.anomaly_flag,
        "intent":        reasoning.intent,
    }
