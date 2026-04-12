def guard_rail_check(answer: str, reasoning, confidence: float) -> str:
    """
    Post-processes the answer without an LLM call.
    - Appends a low-confidence disclaimer when confidence < 0.7
    """
    if not answer or not answer.strip():
        return "I don't have enough data to answer that question. Try rephrasing or selecting a different time period."

    if confidence < 0.7:
        answer = (
            answer.rstrip(".")
            + ". (Note: confidence in this result is low — please verify independently.)"
        )

    return answer
