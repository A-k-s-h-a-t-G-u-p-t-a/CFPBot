import json

from utils.gemini_client import call_gemini

_SYSTEM = """You are a SQL expert for a bank transaction analytics system.

Table: transactions
Columns: TransactionID, AccountID, TransactionAmount, TransactionDate, TransactionType,
         Location, DeviceID, MerchantID, Channel, CustomerAge, CustomerOccupation,
         TransactionDuration, LoginAttempts, AccountBalance, PreviousTransactionDate

Strict rules:
1. Only write SELECT statements — never INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE
2. Always include at least one aggregation (COUNT, SUM, AVG, MIN, MAX)
3. Use ONLY the exact column names listed above
4. Apply the metric filters and business rules provided
5. Use DATE literals: CURRENT_DATE, CURRENT_DATE - INTERVAL '7 days', etc.
6. Return ONLY the JSON object — no markdown fences, no explanation
"""


async def generate_sql(
    question: str,
    metric_context: str,
    schema_context: str,
    few_shot_examples: str,
    plan,
    error_context: str = "",
) -> dict:
    """
    Generates SQL using the ExecutionPlan context.
    Returns: {sql, columns_referenced, confidence}
    """
    error_note = f"\n[Previous attempt failed: {error_context}. Fix this specific issue.]\n" if error_context else ""

    prompt = f"""{error_note}
Question: {question}

Metric definitions (use these exactly):
{metric_context}

Schema documentation:
{schema_context}

Similar query examples for reference:
{few_shot_examples}

Execution context:
- Time window: {plan.time_window}
- Group by dimensions: {plan.dimensions}
- Needs period comparison: {plan.needs_comparison}

Respond in JSON:
{{
  "sql": "<complete SELECT statement>",
  "columns_referenced": ["col1", "col2"],
  "confidence": <0.0 to 1.0>
}}"""

    response = await call_gemini(prompt, system=_SYSTEM, json_mode=True)

    try:
        result = json.loads(response)
        return {
            "sql":                 result.get("sql", "").strip(),
            "columns_referenced":  result.get("columns_referenced", []),
            "confidence":          float(result.get("confidence", 0.5)),
        }
    except (json.JSONDecodeError, ValueError):
        return {"sql": response.strip(), "columns_referenced": [], "confidence": 0.3}
