import re

# All valid columns in the orders table
ALLOWED_COLUMNS: set[str] = {
    "order_id", "date", "status", "fulfilment", "ship_service_level",
    "style", "sku", "category", "size", "asin", "courier_status",
    "qty", "amount", "ship_city", "ship_state", "is_b2b",
    "orders",  # table name
}

_FORBIDDEN = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|EXEC|EXECUTE|UNION\s+ALL|UNION)\b",
    re.IGNORECASE,
)

_HALLUCINATED_COLUMNS = {
    "order_date": "date",
    "created_at": "date",
    "updated_at": "date",
}


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

    lowered = s.lower()
    for bad_col, replacement in _HALLUCINATED_COLUMNS.items():
        if re.search(rf"\b{re.escape(bad_col)}\b", lowered):
            return False, f"Unknown column '{bad_col}'. Use '{replacement}' instead"

    if allowed_columns:
        # Guard the most common runtime break: WHERE/JOIN/ORDER BY against unknown identifiers.
        candidates = set(re.findall(r"\b([a-z_][a-z0-9_]*)\b", lowered))
        sql_keywords = {
            "select", "from", "where", "group", "by", "order", "limit", "as", "and", "or", "not",
            "between", "in", "is", "null", "true", "false", "case", "when", "then", "else", "end",
            "distinct", "desc", "asc", "count", "sum", "avg", "min", "max", "round", "filter", "over",
            "partition", "on", "join", "left", "right", "inner", "outer", "having", "interval", "date",
            "current_date", "extract", "coalesce", "nullif", "numeric", "cast"
        }
        allowed = {c.lower() for c in allowed_columns}
        unknown = sorted(
            token for token in candidates
            if token not in sql_keywords and token not in allowed and not token.isdigit()
        )
        # Keep false positives low by only failing when obvious schema-miss tokens appear.
        obvious_schema_miss = [t for t in unknown if t.endswith("_date") or t.endswith("_at")]
        if obvious_schema_miss:
            return False, f"Unknown identifier(s): {', '.join(obvious_schema_miss)}"

    return True, ""
