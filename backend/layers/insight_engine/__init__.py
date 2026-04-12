from layers.insight_engine.models import EmptyInsight, StructuredInsights
from layers.insight_engine.trend_detector import detect_trend
from layers.insight_engine.outlier_detector import detect_outliers
from layers.insight_engine.contribution_analyzer import analyze_contribution
from layers.insight_engine.chart_recommender import recommend_chart


def run_insight_engine(
    rows: list[dict],
    structured_req,
    columns_used: list[str] | None = None,
    source_tables: list[str] | None = None,
    execution_ms: int = 0,
) -> StructuredInsights:
    """Main entry point — converts raw SQL rows into StructuredInsights."""
    if not rows:
        return StructuredInsights(
            key_finding=EmptyInsight(),
            source_tables=source_tables or [],
            columns_used=columns_used or [],
            execution_ms=execution_ms,
        )

    # Identify column types
    sample        = rows[0]
    numeric_cols  = [k for k, v in sample.items() if isinstance(v, (int, float))]
    time_cols     = [k for k in sample if any(t in k.lower() for t in ("date", "week", "month", "day"))]
    dim_cols      = [k for k, v in sample.items() if isinstance(v, str)]

    value_col = numeric_cols[0] if numeric_cols else None
    time_col  = time_cols[0]  if time_cols  else None

    # Trends
    trends = []
    if time_col and value_col:
        t = detect_trend(rows, value_col, time_col)
        if not isinstance(t, EmptyInsight):
            trends = [t]

    # Anomalies
    anomalies = []
    if value_col:
        a = detect_outliers(rows, value_col)
        if not isinstance(a, EmptyInsight):
            anomalies = a

    # Drivers (contribution analysis)
    drivers = []
    if dim_cols and value_col and len(rows) > 1:
        d = analyze_contribution(rows, dim_cols[0], value_col)
        if not isinstance(d, EmptyInsight):
            drivers = d

    chart_spec   = recommend_chart(structured_req, rows, value_col, time_col, dim_cols)
    key_finding  = _build_key_finding(rows, value_col, dim_cols)

    return StructuredInsights(
        key_finding=key_finding,
        anomalies=anomalies,
        drivers=drivers,
        trends=trends,
        chart_spec=chart_spec,
        source_tables=source_tables or ["transactions"],
        columns_used=columns_used or list(sample.keys()),
        execution_ms=execution_ms,
    )


def _build_key_finding(rows: list[dict], value_col: str | None, dim_cols: list[str]) -> str:
    if not rows or not value_col:
        return f"Found {len(rows)} result(s)."
    top   = rows[0]
    val   = top.get(value_col, 0)
    label = value_col.replace("_", " ").title()
    fmt   = f"{val:,.2f}" if isinstance(val, float) else f"{val:,}"
    if dim_cols:
        return f"{label}: {fmt} (top: {top.get(dim_cols[0], '')})"
    return f"{label}: {fmt}"
