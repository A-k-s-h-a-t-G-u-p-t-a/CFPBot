from dataclasses import dataclass
from typing import Optional


@dataclass
class ResolvedMetric:
    key:            str
    label:          str
    column:         str
    aggregation:    str
    filter:         Optional[str]
    time_column:    str
    description:    str
    unit:           str


# ---------------------------------------------------------------------------
# Inline metric catalog for the orders table — no JSON file dependency
# ---------------------------------------------------------------------------

_CATALOG: dict[str, dict] = {
    "revenue": {
        "label":       "Revenue",
        "column":      "amount",
        "aggregation": "SUM",
        "filter":      "status != 'Cancelled'",
        "time_column": "date",
        "description": "Total order revenue (excludes cancelled orders)",
        "unit":        "currency",
        "keywords":    ["revenue", "sales", "amount", "earnings", "money", "value"],
    },
    "order_volume": {
        "label":       "Order Volume",
        "column":      "order_id",
        "aggregation": "COUNT",
        "filter":      None,
        "time_column": "date",
        "description": "Total number of orders placed",
        "unit":        "orders",
        "keywords":    ["orders", "volume", "count", "how many", "number of orders", "total orders"],
    },
    "units_sold": {
        "label":       "Units Sold",
        "column":      "qty",
        "aggregation": "SUM",
        "filter":      "status != 'Cancelled'",
        "time_column": "date",
        "description": "Total quantity of items sold",
        "unit":        "units",
        "keywords":    ["units", "quantity", "qty", "items", "products sold"],
    },
    "avg_order_value": {
        "label":       "Average Order Value",
        "column":      "amount",
        "aggregation": "AVG",
        "filter":      "amount IS NOT NULL",
        "time_column": "date",
        "description": "Average value per order",
        "unit":        "currency",
        "keywords":    ["average order", "aov", "avg order", "average value", "avg value"],
    },
    "cancellation_rate": {
        "label":       "Cancellation Rate",
        "column":      "order_id",
        "aggregation": "COUNT",
        "filter":      "status = 'Cancelled'",
        "time_column": "date",
        "description": "Percentage of orders that were cancelled",
        "unit":        "percent",
        "keywords":    ["cancellation", "cancelled", "cancel rate", "returns"],
    },
    "b2b_share": {
        "label":       "B2B Share",
        "column":      "is_b2b",
        "aggregation": "COUNT",
        "filter":      "is_b2b = true",
        "time_column": "date",
        "description": "Percentage of orders from business customers",
        "unit":        "percent",
        "keywords":    ["b2b", "business orders", "business share", "b2b orders"],
    },
}


def resolve_metric(key: str) -> Optional[ResolvedMetric]:
    m = _CATALOG.get(key)
    if not m:
        return None
    return ResolvedMetric(
        key=key,
        label=m["label"],
        column=m["column"],
        aggregation=m["aggregation"],
        filter=m.get("filter"),
        time_column=m.get("time_column", "date"),
        description=m.get("description", ""),
        unit=m.get("unit", ""),
    )


def resolve_metrics(keys: list[str]) -> list[ResolvedMetric]:
    return [r for k in keys if (r := resolve_metric(k)) is not None]


def get_all_definitions() -> dict:
    return {k: {kk: vv for kk, vv in v.items() if kk != "keywords"} for k, v in _CATALOG.items()}


def get_metric_context(question: str) -> str:
    """Returns formatted metric definitions most relevant to the question."""
    q = question.lower()
    matched = [
        f"- {m['label']}: {m['description']} (unit: {m.get('unit', 'n/a')}, column: {m['column']}, agg: {m['aggregation']})"
        for m in _CATALOG.values()
        if any(kw in q for kw in m.get("keywords", []))
    ]
    if not matched:
        # Return all if no keyword match
        matched = [
            f"- {m['label']}: {m['description']} (column: {m['column']}, agg: {m['aggregation']})"
            for m in _CATALOG.values()
        ]
    return "\n".join(matched)
