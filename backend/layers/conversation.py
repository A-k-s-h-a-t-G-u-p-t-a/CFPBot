import time

_SESSION_TTL = 1800  # 30 minutes — sessions auto-expire to prevent memory leak

session_store: dict[str, dict] = {}


def get_history(session_id: str) -> list[dict]:
    _cleanup_expired()
    return session_store.get(session_id, {}).get("turns", [])


def add_turn(session_id: str, structured_request: dict, answer: str):
    """
    Stores the full StructuredRequest dict (not just raw text) per turn.
    The Query Understanding layer receives prior_request on the next call
    so it can resolve follow-ups like 'break that down by region' correctly.
    """
    _cleanup_expired()
    if session_id not in session_store:
        session_store[session_id] = {"turns": [], "last_active": time.time()}
    turns = session_store[session_id]["turns"]
    turns.append({
        "role":         "user",
        "raw_question": structured_request.get("raw_question", ""),
        "structured":   structured_request,
        "answer":       answer,
    })
    session_store[session_id]["turns"] = turns[-10:]  # keep last 5 turns (10 entries)
    session_store[session_id]["last_active"] = time.time()


def get_prior_request(session_id: str) -> dict | None:
    """Returns the StructuredRequest dict from the most recent turn."""
    turns = get_history(session_id)
    return turns[-1]["structured"] if turns else None


def _cleanup_expired():
    now = time.time()
    expired = [sid for sid, d in session_store.items()
               if now - d.get("last_active", 0) > _SESSION_TTL]
    for sid in expired:
        del session_store[sid]
