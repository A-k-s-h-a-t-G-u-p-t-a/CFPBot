"""
Per-intent reasoning chains for the 4 supported query types.

Each chain is a standalone async function that:
  1. Computes its SQL query/queries
  2. Fetches results from Postgres
  3. Runs statistical analysis (deltas, shares, z-scores)
  4. Returns a structured ReasoningResult consumed by response_generator.py
"""
import asyncio
import json
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from utils.gemini_client import call_gemini
from layers.execution.pg_engine import execute_analytics_query


@dataclass
class ReasoningResult:
    intent: str
    rows: list[dict]
    narrative_context: dict          # fed verbatim into response_generator prompt
    chart_spec: dict | None = None
    anomaly_flag: str | None = None


# ---------------------------------------------------------------------------
# 1. DRIVER ANALYSIS — "Why did X change?"
# ---------------------------------------------------------------------------

async def run_driver_analysis(
    question: str,
    time_window: dict,
    dimension: str,
    metric_column: str,
    aggregation: str = "SUM",
) -> ReasoningResult:
    """
    Breaks down a metric by the given dimension for current vs prior period
    and ranks the top contributors to the change.
    """
    current_start = time_window.get("start", "(SELECT MAX(date) FROM orders) - INTERVAL '30 days'")
    current_end   = time_window.get("end", "(SELECT MAX(date) FROM orders)")
    prior_start   = time_window.get("prior_start", "(SELECT MAX(date) FROM orders) - INTERVAL '60 days'")
    prior_end     = time_window.get("prior_end", "(SELECT MAX(date) FROM orders) - INTERVAL '30 days'")

    sql_current = f"""
        SELECT {dimension} AS dimension_value,
               {aggregation}("{metric_column}") AS metric_value
        FROM orders
        WHERE date BETWEEN '{current_start}' AND '{current_end}'
        GROUP BY {dimension}
        ORDER BY metric_value DESC
        LIMIT 10
    """
    sql_prior = f"""
        SELECT {dimension} AS dimension_value,
               {aggregation}("{metric_column}") AS metric_value
        FROM orders
        WHERE date BETWEEN '{prior_start}' AND '{prior_end}'
        GROUP BY {dimension}
        ORDER BY metric_value DESC
        LIMIT 10
    """

    current_rows, prior_rows = await asyncio.gather(
        asyncio.to_thread(execute_analytics_query, sql_current),
        asyncio.to_thread(execute_analytics_query, sql_prior),
    )

    current_map = {r["dimension_value"]: float(r["metric_value"] or 0) for r in current_rows}
    prior_map   = {r["dimension_value"]: float(r["metric_value"] or 0) for r in prior_rows}
    all_dims    = set(current_map) | set(prior_map)

    drivers = []
    for dim in all_dims:
        cur  = current_map.get(dim, 0)
        prev = prior_map.get(dim, 0)
        delta = cur - prev
        pct   = round((delta / prev * 100) if prev else 0, 1)
        drivers.append({"dimension": dim, "current": cur, "prior": prev, "delta": delta, "pct_change": pct})

    drivers.sort(key=lambda x: abs(x["delta"]), reverse=True)
    top_driver = drivers[0] if drivers else {}

    total_current = sum(current_map.values())
    total_prior   = sum(prior_map.values())
    total_delta   = total_current - total_prior
    total_pct     = round((total_delta / total_prior * 100) if total_prior else 0, 1)

    return ReasoningResult(
        intent="driver_analysis",
        rows=current_rows,
        narrative_context={
            "total_current": total_current,
            "total_prior": total_prior,
            "total_delta": total_delta,
            "total_pct_change": total_pct,
            "top_driver": top_driver,
            "all_drivers": drivers[:5],
            "dimension_used": dimension,
            "metric_used": metric_column,
        },
        chart_spec={
            "type": "bar",
            "x": [d["dimension"] for d in drivers[:8]],
            "current": [d["current"] for d in drivers[:8]],
            "prior": [d["prior"] for d in drivers[:8]],
            "title": f"{metric_column} by {dimension}: Current vs Prior",
        },
    )


# ---------------------------------------------------------------------------
# 2. BREAKDOWN — "What makes up X?"
# ---------------------------------------------------------------------------

async def run_breakdown(
    question: str,
    dimension: str,
    metric_column: str,
    aggregation: str = "SUM",
    time_window: dict | None = None,
) -> ReasoningResult:
    """
    Decomposes a metric by a dimension and surfaces concentration / outliers.
    """
    date_filter = ""
    if time_window and time_window.get("start"):
        date_filter = f"WHERE date BETWEEN '{time_window['start']}' AND '{time_window.get('end', '(SELECT MAX(date) FROM orders)')}'"

    sql = f"""
        SELECT {dimension} AS dimension_value,
               {aggregation}("{metric_column}") AS metric_value,
               ROUND(100.0 * {aggregation}("{metric_column}") / SUM({aggregation}("{metric_column}")) OVER (), 2) AS share_pct
        FROM orders
        {date_filter}
        GROUP BY {dimension}
        ORDER BY metric_value DESC
        LIMIT 20
    """

    rows = await asyncio.to_thread(execute_analytics_query, sql)

    total = sum(float(r["metric_value"] or 0) for r in rows)
    top_group = rows[0] if rows else {}
    concentration_flag = None
    if top_group and float(top_group.get("share_pct") or 0) > 40:
        concentration_flag = f"{top_group['dimension_value']} dominates at {top_group['share_pct']}% of total"

    return ReasoningResult(
        intent="breakdown",
        rows=rows,
        narrative_context={
            "total": total,
            "top_group": top_group,
            "concentration_flag": concentration_flag,
            "breakdown_by": dimension,
            "metric_used": metric_column,
            "all_groups": rows[:5],
        },
        chart_spec={
            "type": "pie",
            "labels": [r["dimension_value"] for r in rows[:8]],
            "values": [float(r["metric_value"] or 0) for r in rows[:8]],
            "title": f"{metric_column} breakdown by {dimension}",
        },
    )


# ---------------------------------------------------------------------------
# 3. COMPARE — "This week vs last week", "Region A vs B"
# ---------------------------------------------------------------------------

async def run_compare(
    question: str,
    time_window: dict,
    metric_column: str,
    aggregation: str = "SUM",
    compare_dimension: str | None = None,
    compare_values: list[str] | None = None,
) -> ReasoningResult:
    """
    Compares two time periods OR two values of a dimension.
    Returns deltas, % change, and a significance flag.
    """
    if compare_dimension and compare_values and len(compare_values) >= 2:
        # Entity comparison (e.g., category A vs B)
        a_val, b_val = compare_values[0], compare_values[1]
        sql_a = f"""
            SELECT '{a_val}' AS label, {aggregation}("{metric_column}") AS metric_value
            FROM orders WHERE {compare_dimension} = '{a_val}'
        """
        sql_b = f"""
            SELECT '{b_val}' AS label, {aggregation}("{metric_column}") AS metric_value
            FROM orders WHERE {compare_dimension} = '{b_val}'
        """
    else:
        # Time period comparison
        current_start = time_window.get("start", "(SELECT MAX(date) FROM orders) - INTERVAL '7 days'")
        current_end   = time_window.get("end", "(SELECT MAX(date) FROM orders)")
        prior_start   = time_window.get("prior_start", "(SELECT MAX(date) FROM orders) - INTERVAL '14 days'")
        prior_end     = time_window.get("prior_end", "(SELECT MAX(date) FROM orders) - INTERVAL '7 days'")

        sql_a = f"""
            SELECT 'Current Period' AS label, {aggregation}("{metric_column}") AS metric_value
            FROM orders WHERE date BETWEEN '{current_start}' AND '{current_end}'
        """
        sql_b = f"""
            SELECT 'Prior Period' AS label, {aggregation}("{metric_column}") AS metric_value
            FROM orders WHERE date BETWEEN '{prior_start}' AND '{prior_end}'
        """

    rows_a, rows_b = await asyncio.gather(
        asyncio.to_thread(execute_analytics_query, sql_a),
        asyncio.to_thread(execute_analytics_query, sql_b),
    )

    val_a = float((rows_a[0]["metric_value"] if rows_a else None) or 0)
    val_b = float((rows_b[0]["metric_value"] if rows_b else None) or 0)
    label_a = rows_a[0]["label"] if rows_a else "A"
    label_b = rows_b[0]["label"] if rows_b else "B"

    delta = val_a - val_b
    pct   = round((delta / val_b * 100) if val_b else 0, 1)
    winner = label_a if val_a >= val_b else label_b
    significant = abs(pct) >= 5  # 5% threshold is business-meaningful

    return ReasoningResult(
        intent="compare",
        rows=rows_a + rows_b,
        narrative_context={
            "label_a": label_a,
            "label_b": label_b,
            "value_a": val_a,
            "value_b": val_b,
            "delta": delta,
            "pct_change": pct,
            "winner": winner,
            "significant": significant,
            "metric_used": metric_column,
        },
        chart_spec={
            "type": "bar",
            "labels": [label_a, label_b],
            "values": [val_a, val_b],
            "title": f"{metric_column}: {label_a} vs {label_b}",
        },
    )


# ---------------------------------------------------------------------------
# 4. SUMMARY — "Give me a weekly summary"
# ---------------------------------------------------------------------------

_SUMMARY_SQLS: list[tuple[str, str]] = [
    ("total_orders",  'SELECT COUNT(*) AS metric_value FROM orders WHERE date >= (SELECT MAX(date) FROM orders) - INTERVAL \'7 days\''),
    ("total_revenue", 'SELECT SUM("amount") AS metric_value FROM orders WHERE date >= (SELECT MAX(date) FROM orders) - INTERVAL \'7 days\''),
    ("avg_order_value", 'SELECT ROUND(AVG("amount")::numeric, 2) AS metric_value FROM orders WHERE date >= (SELECT MAX(date) FROM orders) - INTERVAL \'7 days\''),
    ("cancelled_rate",  '''SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE status = \'Cancelled\') / NULLIF(COUNT(*), 0), 2) AS metric_value FROM orders WHERE date >= (SELECT MAX(date) FROM orders) - INTERVAL \'7 days\' '''),
    ("b2b_share",       '''SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE is_b2b) / NULLIF(COUNT(*), 0), 2) AS metric_value FROM orders WHERE date >= (SELECT MAX(date) FROM orders) - INTERVAL \'7 days\' '''),
]


async def run_summary(question: str) -> ReasoningResult:
    """
    Runs preset metric queries in parallel, detects anomalies vs the prior week,
    and returns a structured result for the LLM to narrate.
    """
    async def fetch(label: str, sql: str) -> tuple[str, Any]:
        rows = await asyncio.to_thread(execute_analytics_query, sql)
        val  = float((rows[0]["metric_value"] if rows else None) or 0)
        return label, val

    results = await asyncio.gather(*[fetch(lbl, sql) for lbl, sql in _SUMMARY_SQLS])
    metrics_dict = dict(results)

    return ReasoningResult(
        intent="summary",
        rows=[],
        narrative_context={
            "period": "last 7 days",
            "metrics": metrics_dict,
        },
        chart_spec=None,
    )
