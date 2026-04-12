import asyncio
import json
import re
from typing import Any

from agents.reasoning_chain import ReasoningResult
from agents.sql_validator import ALLOWED_COLUMNS, validate_sql
from layers.execution.pg_engine import execute_analytics_query
from layers.execution.result_cache import result_cache
from layers.semantic_layer.metric_registry import ResolvedMetric
from layers.vector_store import get_relevant_examples, get_relevant_metric_docs, get_relevant_schema
from utils.gemini_client import call_gemini


_SYSTEM = """You are a SQL agent for an e-commerce analytics database.

You must turn the question into a single PostgreSQL SELECT query over the orders table.

Rules:
1. Use only the exact column names in the schema context.
2. Prefer the user's requested dimension if it exists, such as size, fulfilment, category, channel, or ship_state.
3. If no metric is specified, use COUNT(*) or COUNT(order_id) to measure usage or frequency.
4. Use anchored date ranges from the execution context when provided.
5. Return JSON only with sql, rationale, and confidence.
6. Do not invent joins or tables outside the provided schema.
"""


def _json_loads(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return json.loads(cleaned.strip())


def _default_metric(resolved_metrics: list[ResolvedMetric]) -> tuple[str, str, str]:
    if resolved_metrics:
        metric = resolved_metrics[0]
        return metric.column, metric.aggregation, metric.label
    return "order_id", "COUNT", "Order Volume"


def _normalize_sql(sql: str) -> str:
    """Patch common model hallucinations before validation/execution."""
    fixes = {
        r"\border_date\b": "date",
        r"\bcreated_at\b": "date",
        r"\bupdated_at\b": "date",
    }
    normalized = sql
    for pattern, replacement in fixes.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    return normalized


def _build_time_filter(time_window: dict[str, Any]) -> str:
    start = time_window.get("start")
    end = time_window.get("end")
    if start and end:
        return f"date BETWEEN '{start}' AND '{end}'"
    return ""


def _fallback_sql(question: str, structured_req, resolved_metrics: list[ResolvedMetric]) -> str:
    metric_column, aggregation, _ = _default_metric(resolved_metrics)
    dimension = structured_req.dimensions[0] if structured_req.dimensions else None
    time_filter = _build_time_filter(structured_req.time_window)

    if dimension:
        metric_expr = f'{aggregation}("{metric_column}")' if aggregation != "COUNT" else "COUNT(*)"
        where_clause = f"WHERE {time_filter}" if time_filter else ""
        return f"SELECT {dimension} AS dimension_value, {metric_expr} AS metric_value FROM orders {where_clause} GROUP BY {dimension} ORDER BY metric_value DESC LIMIT 10"

    where_clause = f"WHERE {time_filter}" if time_filter else ""
    metric_expr = f'{aggregation}("{metric_column}")' if aggregation != "COUNT" else "COUNT(*)"
    return f"SELECT {metric_expr} AS metric_value FROM orders {where_clause}"


def _build_chart_spec(rows: list[dict[str, Any]], structured_req) -> dict | None:
    if not rows:
        return None
    first_row = rows[0]
    if "dimension_value" in first_row:
        labels = [str(row.get("dimension_value")) for row in rows[:8]]
        values = [float(row.get("metric_value") or 0) for row in rows[:8]]
        return {
            "type": "bar" if len(labels) > 1 else "table",
            "labels": labels,
            "values": values,
            "title": structured_req.rewritten,
        }
    return None


def _build_narrative_context(rows: list[dict[str, Any]], structured_req, resolved_metrics: list[ResolvedMetric], sql: str, confidence: float) -> dict:
    metric_column, aggregation, metric_label = _default_metric(resolved_metrics)
    top_row = rows[0] if rows else {}
    return {
        "question": structured_req.rewritten,
        "metric_label": metric_label,
        "metric_column": metric_column,
        "aggregation": aggregation,
        "sql": sql,
        "rows": rows[:10],
        "row_count": len(rows),
        "top_row": top_row,
        "dimensions": structured_req.dimensions,
        "time_window": structured_req.time_window,
        "confidence": confidence,
    }


async def run_agentic_query(question: str, structured_req, resolved_metrics: list[ResolvedMetric], metric_context: str = "") -> ReasoningResult:
    metric_column, aggregation, metric_label = _default_metric(resolved_metrics)
    schema_ctx = get_relevant_schema(structured_req.rewritten)
    metric_docs = get_relevant_metric_docs(structured_req.rewritten)
    few_shot = get_relevant_examples(structured_req.rewritten)
    time_filter = _build_time_filter(structured_req.time_window)

    prompt = f"""Question: {question}

Structured request:
{json.dumps(structured_req.__dict__, indent=2, default=str)}

Metric context:
{metric_context or metric_docs}

Schema documentation:
{schema_ctx}

Few-shot examples:
{few_shot}

Execution hints:
- Default metric column: {metric_column}
- Default aggregation: {aggregation}
- Preferred dimensions: {structured_req.dimensions}
- Time filter: {time_filter or 'none'}

Return JSON with:
{{
  "sql": "<single SELECT statement>",
  "rationale": "<brief explanation of why this query fits>",
  "confidence": <0.0 to 1.0>
}}"""

    response_text = await call_gemini(prompt, system=_SYSTEM, json_mode=True)

    try:
        result = _json_loads(response_text)
        sql = str(result.get("sql", "")).strip()
        confidence = float(result.get("confidence", 0.5))
    except Exception:
        result = {}
        sql = ""
        confidence = 0.3

    if not sql:
        sql = _fallback_sql(question, structured_req, resolved_metrics)

    sql = _normalize_sql(sql)

    valid = False
    reason = ""
    for _ in range(2):
        valid, reason = validate_sql(sql, ALLOWED_COLUMNS)
        if valid:
            break
        repair_prompt = f"""The previous SQL was invalid.

Question: {question}
Failure reason: {reason}

Return a corrected JSON object with sql, rationale, and confidence."""
        repair_text = await call_gemini(repair_prompt, system=_SYSTEM, json_mode=True)
        try:
            repaired = _json_loads(repair_text)
            sql = _normalize_sql(str(repaired.get("sql", "")).strip() or sql)
            confidence = float(repaired.get("confidence", 0.3))
        except Exception:
            break

    if not valid:
        sql = _fallback_sql(question, structured_req, resolved_metrics)
        valid, reason = validate_sql(sql, ALLOWED_COLUMNS)

    cached_rows = result_cache.get(sql)
    if cached_rows is not None:
        rows = cached_rows
    else:
        try:
            rows = await asyncio.to_thread(execute_analytics_query, sql)
        except Exception as exc:
            # One last repair pass using the concrete database error.
            repair_prompt = f"""The SQL failed when executed.

Question: {question}
SQL: {sql}
Database error: {str(exc)}

Return corrected JSON with sql, rationale, and confidence. Use only columns from orders.
"""
            repair_text = await call_gemini(repair_prompt, system=_SYSTEM, json_mode=True)
            repaired = _json_loads(repair_text)
            repaired_sql = _normalize_sql(str(repaired.get("sql", "")).strip())
            valid, _ = validate_sql(repaired_sql, ALLOWED_COLUMNS)
            if not valid:
                repaired_sql = _fallback_sql(question, structured_req, resolved_metrics)
            sql = repaired_sql
            rows = await asyncio.to_thread(execute_analytics_query, sql)
        result_cache.set(sql, rows)

    narrative_context = _build_narrative_context(rows, structured_req, resolved_metrics, sql, confidence)

    return ReasoningResult(
        intent=structured_req.intent,
        rows=rows,
        narrative_context=narrative_context,
        chart_spec=_build_chart_spec(rows, structured_req),
        anomaly_flag=None,
    )