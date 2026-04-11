import re
from datetime import date, timedelta

_TIME_PRONOUNS = ["same period", "that period", "same time", "same week", "same month"]


def parse_time_window(question: str, today: date, prior_request: dict | None = None) -> dict:
    """Resolves natural language time references to absolute date ranges."""
    q = question.lower()

    # Follow-up: inherit time window from prior request
    if prior_request and any(p in q for p in _TIME_PRONOUNS):
        return prior_request.get("time_window", _default(today))

    if "today" in q:
        return {"start": str(today), "end": str(today), "granularity": "hourly", "comparison": False}

    if "this week" in q:
        start = today - timedelta(days=today.weekday())
        return {"start": str(start), "end": str(today), "granularity": "daily", "comparison": False}

    if "last week" in q or "previous week" in q:
        end   = today - timedelta(days=today.weekday() + 1)
        start = end - timedelta(days=6)
        return {**_with_prior(start, end, timedelta(days=7)), "granularity": "daily"}

    if "wow" in q or "week over week" in q or "week-over-week" in q:
        end   = today
        start = today - timedelta(days=6)
        return {**_with_prior(start, end, timedelta(days=7)), "granularity": "daily"}

    if "this month" in q:
        start = today.replace(day=1)
        return {"start": str(start), "end": str(today), "granularity": "daily", "comparison": False}

    if "last month" in q or "previous month" in q:
        first = today.replace(day=1)
        end   = first - timedelta(days=1)
        start = end.replace(day=1)
        return {"start": str(start), "end": str(end), "granularity": "daily", "comparison": False}

    if "mom" in q or "month over month" in q or "month-over-month" in q:
        first = today.replace(day=1)
        prior_end   = first - timedelta(days=1)
        prior_start = prior_end.replace(day=1)
        return {
            "start": str(first), "end": str(today), "granularity": "weekly",
            "comparison": True, "prior_start": str(prior_start), "prior_end": str(prior_end),
        }

    if "this quarter" in q or "last quarter" in q:
        qm    = ((today.month - 1) // 3) * 3 + 1
        start = today.replace(month=qm, day=1)
        return {"start": str(start), "end": str(today), "granularity": "weekly", "comparison": False}

    # "last N days"
    m = re.search(r"last\s+(\d+)\s+days?", q)
    if m:
        n = int(m.group(1))
        return {"start": str(today - timedelta(days=n)), "end": str(today),
                "granularity": "daily", "comparison": False}

    return _default(today)


def _default(today: date) -> dict:
    return {"start": str(today - timedelta(days=30)), "end": str(today),
            "granularity": "daily", "comparison": False}


def _with_prior(start: date, end: date, delta: timedelta) -> dict:
    return {
        "start":       str(start),
        "end":         str(end),
        "comparison":  True,
        "prior_start": str(start - delta),
        "prior_end":   str(end - delta),
    }
