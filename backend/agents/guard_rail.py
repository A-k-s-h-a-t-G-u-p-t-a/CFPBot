from layers.insight_engine.models import EmptyInsight, StructuredInsights


def guard_rail_check(answer: str, insights: StructuredInsights, confidence: float) -> str:
    """
    Post-processes the answer without an LLM call:
    - Overrides with 'no data' message when insights are empty
    - Appends a low-confidence disclaimer when confidence < 0.7
    """
    if isinstance(insights.key_finding, EmptyInsight):
        return insights.key_finding.message

    if confidence < 0.7:
        answer = (
            answer.rstrip(".")
            + ". (Note: confidence in this result is low — please verify independently.)"
        )

    return answer
