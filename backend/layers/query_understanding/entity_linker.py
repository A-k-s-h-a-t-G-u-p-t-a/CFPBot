METRIC_ALIASES: dict[str, str] = {
    # Revenue
    "revenue":              "revenue",
    "sales":                "revenue",
    "income":               "revenue",
    "earnings":             "revenue",
    "money":                "revenue",
    "total sales":          "revenue",
    "order value":          "revenue",
    "amount":               "revenue",
    # Order volume
    "orders":               "order_volume",
    "order volume":         "order_volume",
    "number of orders":     "order_volume",
    "how many orders":      "order_volume",
    "total orders":         "order_volume",
    "order count":          "order_volume",
    # Units
    "units":                "units_sold",
    "quantity":             "units_sold",
    "qty":                  "units_sold",
    "items":                "units_sold",
    "items sold":           "units_sold",
    "units sold":           "units_sold",
    # Average order value
    "average order":        "avg_order_value",
    "avg order":            "avg_order_value",
    "average value":        "avg_order_value",
    "aov":                  "avg_order_value",
    "average order value":  "avg_order_value",
    # Cancellations
    "cancellation":         "cancellation_rate",
    "cancellations":        "cancellation_rate",
    "cancelled":            "cancellation_rate",
    "cancel rate":          "cancellation_rate",
    "cancellation rate":    "cancellation_rate",
    # B2B
    "b2b":                  "b2b_share",
    "business orders":      "b2b_share",
    "business customers":   "b2b_share",
    "b2b share":            "b2b_share",
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

    return matched if matched else ["order_volume"]  # sensible default for e-commerce
