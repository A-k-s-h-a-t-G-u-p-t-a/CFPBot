import numpy as np

from layers.insight_engine.models import EmptyInsight


def detect_trend(rows: list[dict], value_col: str, time_col: str) -> dict | EmptyInsight:
    """Compares first-half vs second-half average to determine direction and magnitude."""
    if not rows:
        return EmptyInsight()
    if len(rows) < 2:
        return EmptyInsight(reason="insufficient_data", message="Not enough data points for trend analysis.")

    values = [float(r.get(value_col) or 0) for r in rows]
    mid    = max(len(values) // 2, 1)

    first_avg  = float(np.mean(values[:mid]))
    second_avg = float(np.mean(values[mid:]))

    if first_avg == 0:
        return EmptyInsight(reason="zero_baseline")

    pct_change = ((second_avg - first_avg) / first_avg) * 100

    direction = "flat" if abs(pct_change) < 2 else ("up" if pct_change > 0 else "down")
    peak_i    = int(np.argmax(values))
    trough_i  = int(np.argmin(values))

    return {
        "direction":      direction,
        "pct_change":     round(pct_change, 1),
        "peak_period":    rows[peak_i].get(time_col, str(peak_i)),
        "trough_period":  rows[trough_i].get(time_col, str(trough_i)),
        "first_avg":      round(first_avg, 2),
        "second_avg":     round(second_avg, 2),
    }
