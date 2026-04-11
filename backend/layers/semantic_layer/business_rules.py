GLOBAL_RULES: list[str] = [
    "Use TransactionDate as the primary time filter column.",
    "When counting unique customers or accounts, always use COUNT(DISTINCT AccountID).",
    "Revenue always means SUM(TransactionAmount) WHERE TransactionType = 'Credit'.",
    "Exclude LoginAttempts > 5 from clean revenue and volume metrics unless the question is explicitly about fraud.",
]


def get_rules_for_metric(metric_key: str) -> list[str]:
    """Returns global rules plus any metric-specific rules."""
    from layers.semantic_layer.metric_registry import resolve_metric
    resolved = resolve_metric(metric_key)
    metric_rules = resolved.business_rules if resolved else []
    return GLOBAL_RULES + metric_rules


def format_rules_for_prompt(metric_key: str) -> str:
    rules = get_rules_for_metric(metric_key)
    return "\n".join(f"- {r}" for r in rules)
