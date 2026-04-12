INTENT_RULES: dict[str, list[str]] = {
    "compare":         ["compare", " vs ", "versus", "difference between", "more than", "less than",
                        "higher than", "lower than", "better than", "worse than"],
    "breakdown":       ["breakdown", " by ", "split by", "per ", "each ", "across ",
                        "distribute", "group by", "by channel", "by location", "by region"],
    "driver_analysis": ["why", "reason", "cause", "drove", "explain", "what caused",
                        "factor", "because of", "responsible for", "led to"],
    "summary":         ["summary", "overview", "report", "tell me about", "how are we doing",
                        "what happened", "give me", "show me today", "this week's"],
    "trend":           ["trend", "over time", "growing", "declining", "trajectory",
                        "pattern", "week by week", "month by month", "history of"],
}


def classify_intent(question: str) -> tuple[str, float]:
    """
    Returns (intent, confidence_0_to_1).
    Confidence below 0.6 signals the orchestrator should use LLM fallback.
    """
    q = question.lower()
    scores: dict[str, int] = {intent: 0 for intent in INTENT_RULES}

    for intent, keywords in INTENT_RULES.items():
        scores[intent] = sum(1 for kw in keywords if kw in q)

    total = sum(scores.values())
    if total == 0:
        return "summary", 0.3  # safe default with low confidence

    best = max(scores, key=lambda k: scores[k])
    confidence = min(scores[best] / total, 1.0)
    return best, confidence
