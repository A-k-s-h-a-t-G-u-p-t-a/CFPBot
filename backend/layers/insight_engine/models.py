from dataclasses import dataclass, field
from typing import Optional, Union


@dataclass
class EmptyInsight:
    reason:  str = "no_data"
    message: str = "No transactions found for this period."


@dataclass
class StructuredInsights:
    key_finding:   Union[str, EmptyInsight]
    anomalies:     list[dict] = field(default_factory=list)
    drivers:       list[dict] = field(default_factory=list)
    trends:        list[dict] = field(default_factory=list)
    chart_spec:    Optional[dict] = None
    source_tables: list[str] = field(default_factory=list)
    columns_used:  list[str] = field(default_factory=list)
    execution_ms:  int = 0
