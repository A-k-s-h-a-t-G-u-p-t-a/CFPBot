import numpy as np

from layers.insight_engine.models import EmptyInsight

_THRESHOLD = 2.0
_MIN_ROWS  = 10


def detect_outliers(rows: list[dict], value_col: str) -> list[dict] | EmptyInsight:
    """Z-score based outlier detection. Requires at least 10 data points."""
    if not rows:
        return EmptyInsight()
    if len(rows) < _MIN_ROWS:
        return EmptyInsight(
            reason="insufficient_data",
            message=f"Anomaly detection requires at least {_MIN_ROWS} data points ({len(rows)} found).",
        )

    values = np.array([float(r.get(value_col) or 0) for r in rows])
    std    = np.std(values)
    if std == 0:
        return []  # all identical — no outliers

    z_scores = (values - np.mean(values)) / std
    period_keys = [k for k in rows[0] if any(t in k.lower() for t in ("date", "week", "month", "day"))]

    outliers = []
    for i, (row, z) in enumerate(zip(rows, z_scores)):
        if abs(z) >= _THRESHOLD:
            period = row.get(period_keys[0], str(i)) if period_keys else str(i)
            outliers.append({
                "period":  period,
                "value":   float(row.get(value_col, 0)),
                "z_score": round(float(z), 2),
                "label":   "spike" if z > 0 else "drop",
            })
    return outliers
