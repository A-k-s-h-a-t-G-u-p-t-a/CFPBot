import json
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

_METRICS_PATH = os.path.join(os.path.dirname(__file__), "../../data/metrics.json")


@dataclass
class ResolvedMetric:
    key:            str
    label:          str
    column:         str
    aggregation:    str
    filter:         Optional[str]
    joins:          list[str]
    time_column:    str
    description:    str
    unit:           str
    lineage:        list[str]
    business_rules: list[str]


def _load() -> dict:
    with open(_METRICS_PATH) as f:
        return json.load(f)


_catalog = _load()


def resolve_metric(key: str) -> Optional[ResolvedMetric]:
    m = _catalog.get(key)
    if not m:
        return None
    return ResolvedMetric(
        key=key,
        label=m.get("label", key),
        column=m.get("column", ""),
        aggregation=m.get("aggregation", "COUNT"),
        filter=m.get("filter"),
        joins=m.get("joins", []),
        time_column=m.get("time_column", "TransactionDate"),
        description=m.get("description", ""),
        unit=m.get("unit", ""),
        lineage=m.get("lineage", []),
        business_rules=m.get("business_rules", []),
    )


def resolve_metrics(keys: list[str]) -> list[ResolvedMetric]:
    return [r for k in keys if (r := resolve_metric(k)) is not None]


def get_all_definitions() -> dict:
    return _catalog


def get_metric_context(question: str) -> str:
    """Returns formatted metric definitions most relevant to the question."""
    q = question.lower()
    matched = [
        f"- {m['label']}: {m['description']} (unit: {m.get('unit', 'n/a')})"
        for k, m in _catalog.items()
        if k in q or m.get("label", "").lower() in q
    ]
    if not matched:
        matched = [f"- {m['label']}: {m['description']}" for m in _catalog.values()]
    return "\n".join(matched)
