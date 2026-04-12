import json

from layers.insight_engine.models import EmptyInsight, StructuredInsights
from utils.gemini_client import call_gemini

_SYSTEM = """You are a bank data analyst producing executive summaries.

You receive pre-calculated StructuredInsights. Never recalculate or invent numbers.

Rules:
1. Use EXACTLY the numbers from key_finding — do not round or modify them
2. Lead with the most important number first
3. Explain one driver from drivers[] in plain English (if available)
4. If anomalies[] is non-empty, mention the spike/drop and its date
5. Cite source_tables at the end in one sentence
6. Maximum 3 sentences total — no SQL, no column names, no jargon
7. End with one short follow-up question suggestion
"""


async def generate_response(
    question: str,
    insights: StructuredInsights,
    metric_label: str,
    rag_context: str = "",
) -> dict:
    """
    Generates the final plain-English response.
    The LLM reads StructuredInsights — it never recalculates.
    """
    # Empty result fast-path
    if isinstance(insights.key_finding, EmptyInsight):
        return {
            "answer":        insights.key_finding.message,
            "chart_type":    None,
            "chart_data":    None,
            "metric_used":   metric_label,
            "columns_used":  insights.columns_used,
            "source_tables": insights.source_tables,
            "follow_up":     "Would you like to try a different time period?",
            "confidence":    1.0,
            "anomaly_flag":  None,
        }

    # RAG path
    if rag_context and not insights.drivers:
        prompt = f"""Question: {question}

Relevant documentation:
{rag_context}

Explain clearly in 2-3 sentences. Suggest one follow-up question.

Respond in JSON: {{"answer": "...", "follow_up": "..."}}"""
        try:
            result = json.loads(await call_gemini(prompt, system=_SYSTEM, json_mode=True))
            return {
                "answer":        result.get("answer", ""),
                "chart_type":    None,
                "chart_data":    None,
                "metric_used":   metric_label,
                "columns_used":  insights.columns_used,
                "source_tables": insights.source_tables,
                "follow_up":     result.get("follow_up", ""),
                "confidence":    1.0,
                "anomaly_flag":  None,
            }
        except Exception:
            pass

    # SQL path — narrate StructuredInsights
    anomaly_str = ""
    if insights.anomalies:
        a           = insights.anomalies[0]
        anomaly_str = f"{a.get('label', 'anomaly')} on {a.get('period', '?')} (z={a.get('z_score', '?')})"

    prompt = f"""Question: {question}
Metric: {metric_label}

Pre-calculated findings (use these numbers exactly):
- Key finding: {insights.key_finding}
- Top driver: {insights.drivers[0] if insights.drivers else 'N/A'}
- Trend: {insights.trends[0] if insights.trends else 'N/A'}
- Anomaly: {anomaly_str or 'None'}
- Source tables: {', '.join(insights.source_tables)}

Write a 2-3 sentence executive summary. End with one follow-up question.

Respond in JSON: {{"answer": "...", "follow_up": "...", "anomaly_flag": "..." or null}}"""

    try:
        result = json.loads(await call_gemini(prompt, system=_SYSTEM, json_mode=True))
    except Exception:
        result = {}

    return {
        "answer":        result.get("answer") or str(insights.key_finding),
        "chart_type":    insights.chart_spec.get("type") if insights.chart_spec else "bar",
        "chart_data":    insights.chart_spec,
        "metric_used":   metric_label,
        "columns_used":  insights.columns_used,
        "source_tables": insights.source_tables,
        "follow_up":     result.get("follow_up", "Would you like to explore further?"),
        "confidence":    0.9,
        "anomaly_flag":  result.get("anomaly_flag") or (anomaly_str or None),
    }
