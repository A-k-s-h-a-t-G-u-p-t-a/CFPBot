from dataclasses import dataclass, field
from typing import Optional

from layers.query_planner.route_decider import decide_route


@dataclass
class ExecutionPlan:
    route:                   str                      # "pre_agg" | "raw_sql" | "rag"
    queries:                 list[str] = field(default_factory=list)
    shared_dimensions:       list[str] = field(default_factory=list)
    needs_comparison:        bool = False
    comparison_period:       Optional[dict] = None
    needs_driver_analysis:   bool = False
    needs_significance_test: bool = False
    decompose_by:            list[str] = field(default_factory=list)
    pre_agg_file:            Optional[str] = None
    time_window:             dict = field(default_factory=dict)
    dimensions:              list[str] = field(default_factory=list)


def build_plan(structured_req, resolved_metrics: list) -> ExecutionPlan:
    """Builds an ExecutionPlan from a StructuredRequest and resolved metrics."""
    intent      = structured_req.intent
    dimensions  = structured_req.dimensions
    time_window = structured_req.time_window
    granularity = time_window.get("granularity", "daily")
    metric_keys = [m.key for m in resolved_metrics] if resolved_metrics else ["transaction_volume"]

    route, pre_agg_file = decide_route(metric_keys, dimensions, granularity)

    return ExecutionPlan(
        route=route,
        queries=[],          # populated later by sql_generator
        shared_dimensions=dimensions,
        needs_comparison=time_window.get("comparison", False),
        comparison_period=(
            {"start": time_window.get("prior_start"), "end": time_window.get("prior_end")}
            if time_window.get("comparison") else None
        ),
        needs_driver_analysis=(intent == "driver_analysis"),
        needs_significance_test=(intent == "compare"),
        decompose_by=dimensions,
        pre_agg_file=pre_agg_file,
        time_window=time_window,
        dimensions=dimensions,
    )
