import json
from datetime import datetime

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


def _fmt_number(value) -> str:
    try:
        return f"{float(value):,.2f}"
    except Exception:
        return str(value)


def _fmt_date(value) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    text = str(value)
    return text[:10] if len(text) >= 10 else text


def _fallback_answer(reasoning: ReasoningResult, metric_label: str) -> str:
    ctx = reasoning.narrative_context or {}
    rows = ctx.get("rows") or reasoning.rows or []

    if not rows:
        return f"I could not generate a narrative right now, but the query executed successfully for {metric_label}."

    first = rows[0]
    keys = [k for k in first.keys()]
    if len(keys) >= 2:
        dim_key = keys[0]
        val_key = keys[1]
        top_dim = first.get(dim_key)
        top_val = first.get(val_key)
        return (
            f"I could not use the language model just now, but your query ran successfully. "
            f"Top result: {top_dim} with {metric_label} = {_fmt_number(top_val)}."
        )

    only_key = keys[0] if keys else "value"
    return (
        f"I could not use the language model just now, but your query ran successfully. "
        f"{metric_label}: {_fmt_number(first.get(only_key))}."
    )


def _fallback_follow_up(reasoning: ReasoningResult) -> str:
    ctx = reasoning.narrative_context or {}
    time_window = ctx.get("time_window") or {}
    start = time_window.get("start")
    end = time_window.get("end")
    if start and end:
        return f"Would you like a comparison against the previous period ({_fmt_date(start)} to {_fmt_date(end)})?"
    return "Would you like a breakdown by region or channel next?"


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
        "answer":        result.get("answer") or _fallback_answer(reasoning, metric_label),
        "chart_type":    reasoning.chart_spec.get("type") if reasoning.chart_spec else None,
        "chart_data":    reasoning.chart_spec,
        "metric_used":   metric_label,
        "source_tables": ["orders"],
        "follow_up":     result.get("follow_up") or _fallback_follow_up(reasoning),
        "confidence":    0.9,
        "anomaly_flag":  result.get("anomaly_flag") or reasoning.anomaly_flag,
        "intent":        reasoning.intent,
    }
