import os

# Maps (metric_key, dimension_column, granularity) → parquet file path
_BASE = os.path.join(os.path.dirname(__file__), "../../data/aggregations")

_PRE_AGG_MAP: dict[tuple, str] = {
    ("transaction_volume", "Channel", "daily"):   f"{_BASE}/daily_by_channel.parquet",
    ("revenue",            "Channel", "daily"):   f"{_BASE}/daily_by_channel.parquet",
    ("transaction_volume", "Location", "weekly"): f"{_BASE}/weekly_by_location.parquet",
    ("revenue",            "Location", "weekly"): f"{_BASE}/weekly_by_location.parquet",
    ("transaction_volume", "", "monthly"):        f"{_BASE}/monthly_summary.parquet",
    ("revenue",            "", "monthly"):        f"{_BASE}/monthly_summary.parquet",
}


def decide_route(
    metrics: list[str],
    dimensions: list[str],
    granularity: str,
) -> tuple[str, str | None]:
    """
    Returns (route, pre_agg_file_or_None).
    Routes to 'pre_agg' only when the file physically exists on disk.
    """
    dim_str = dimensions[0] if dimensions else ""

    for (metric, dim, gran), filepath in _PRE_AGG_MAP.items():
        if (
            metric in metrics
            and (dim == "" or dim.lower() in dim_str.lower())
            and gran == granularity
            and os.path.exists(filepath)
        ):
            return "pre_agg", filepath

    return "raw_sql", None
