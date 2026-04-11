import re

ALLOWED_COLUMNS: set[str] = {
    "TransactionID", "AccountID", "TransactionAmount", "TransactionDate",
    "TransactionType", "Location", "DeviceID", "MerchantID", "Channel",
    "CustomerAge", "CustomerOccupation", "TransactionDuration",
    "LoginAttempts", "AccountBalance", "PreviousTransactionDate",
    "transactions",
}

_FORBIDDEN = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|EXEC|EXECUTE|UNION\s+ALL|UNION)\b",
    re.IGNORECASE,
)
_AGGREGATION = re.compile(r"\b(COUNT|SUM|AVG|MIN|MAX)\s*\(", re.IGNORECASE)


def validate_sql(sql: str, allowed_columns: set[str] | None = None) -> tuple[bool, str]:
    """
    Pure Python safety validation — no LLM call.
    Returns (is_valid, failure_reason).
    """
    if not sql or not sql.strip():
        return False, "SQL is empty"

    s = sql.strip()

    if not s.upper().startswith("SELECT"):
        return False, "SQL must start with SELECT"

    m = _FORBIDDEN.search(s)
    if m:
        return False, f"Forbidden keyword: {m.group()}"

    # Block stacked statements
    statements = [p.strip() for p in s.rstrip(";").split(";") if p.strip()]
    if len(statements) > 1:
        return False, "Multiple SQL statements are not allowed"

    if not _AGGREGATION.search(s):
        return False, "SQL must contain at least one aggregation (COUNT, SUM, AVG, MIN, MAX)"

    return True, ""
