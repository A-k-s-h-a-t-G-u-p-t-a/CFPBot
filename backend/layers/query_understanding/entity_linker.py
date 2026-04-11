METRIC_ALIASES: dict[str, str] = {
    "revenue":              "revenue",
    "income":               "revenue",
    "money received":       "revenue",
    "credit transactions":  "revenue",
    "transaction volume":   "transaction_volume",
    "volume":               "transaction_volume",
    "transactions":         "transaction_volume",
    "number of transactions": "transaction_volume",
    "average transaction":  "average_transaction",
    "avg transaction":      "average_transaction",
    "average value":        "average_transaction",
    "average amount":       "average_transaction",
    "ticket size":          "average_transaction",
    "churn":                "churn_risk",
    "churn risk":           "churn_risk",
    "at risk":              "churn_risk",
    "inactive":             "churn_risk",
    "dormant":              "churn_risk",
    "top channel":          "top_channel",
    "best channel":         "top_channel",
    "fraud":                "fraud_indicators",
    "fraudulent":           "fraud_indicators",
    "suspicious":           "fraud_indicators",
}

_FOLLOW_UP_PRONOUNS = ["that", "those", "it ", "this", "same", "the above", "the drop", "the change"]


def link_to_metric_catalog(question: str, prior_request: dict | None = None) -> list[str]:
    """
    Maps question terms to metric catalog keys.
    If the question contains follow-up pronouns and prior_request exists,
    inherits the metric from the previous turn.
    """
    q = question.lower()

    # Follow-up resolution — inherit metric from prior turn
    if prior_request and any(p in q for p in _FOLLOW_UP_PRONOUNS):
        prior_metrics = prior_request.get("metrics", [])
        if prior_metrics:
            return prior_metrics

    matched: list[str] = []
    for alias, key in METRIC_ALIASES.items():
        if alias in q and key not in matched:
            matched.append(key)

    return matched if matched else ["transaction_volume"]  # sensible default
