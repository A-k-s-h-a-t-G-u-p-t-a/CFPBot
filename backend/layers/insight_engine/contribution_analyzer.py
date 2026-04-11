from layers.insight_engine.models import EmptyInsight


def analyze_contribution(
    rows: list[dict],
    dimension_col: str,
    value_col: str,
) -> list[dict] | EmptyInsight:
    """
    Ranks each dimension member by its % share of the total value.
    Used for driver analysis: 'Mobile contributed 62% of the volume drop.'
    """
    if not rows:
        return EmptyInsight()

    total = sum(float(r.get(value_col) or 0) for r in rows)
    if total == 0:
        return EmptyInsight(reason="zero_total")

    contributions = sorted(
        [
            {
                "dimension":       dimension_col,
                "dimension_value": str(r.get(dimension_col, "Unknown")),
                "value":           round(float(r.get(value_col) or 0), 2),
                "contribution_pct": round(float(r.get(value_col) or 0) / total * 100, 1),
            }
            for r in rows
        ],
        key=lambda x: x["contribution_pct"],
        reverse=True,
    )
    return contributions
