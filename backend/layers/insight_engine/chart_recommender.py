def recommend_chart(
    req,
    rows: list[dict],
    value_col: str | None,
    time_col: str | None,
    dim_cols: list[str],
) -> dict | None:
    """
    Rule-based chart selection — never uses the LLM.
    Returns a Chart.js-ready spec or None if no chart is appropriate.
    """
    if not rows or not value_col:
        return None

    intent    = getattr(req, "intent", "summary") if req else "summary"
    n_rows    = len(rows)

    # Select chart type
    if intent == "trend" or (time_col and n_rows > 3):
        chart_type = "line"
    elif intent == "breakdown" and dim_cols and n_rows <= 6:
        chart_type = "pie"
    elif intent in ("compare", "driver_analysis", "breakdown"):
        chart_type = "bar"
    elif intent == "summary":
        chart_type = "bar"
    else:
        chart_type = "bar"

    label_col = dim_cols[0] if dim_cols else (time_col or list(rows[0].keys())[0])
    labels    = [str(r.get(label_col, "")) for r in rows]
    values    = [float(r.get(value_col) or 0) for r in rows]

    return {
        "type":     chart_type,
        "x_axis":   label_col,
        "y_axis":   value_col,
        "labels":   labels,
        "datasets": [{"label": value_col.replace("_", " ").title(), "data": values}],
    }
