import json

from utils.gemini_client import call_gemini

_SYSTEM = """You are a SQL expert for an e-commerce order analytics system.

Table: orders
Columns:
  order_id TEXT, date DATE, status TEXT, fulfilment TEXT,
  ship_service_level TEXT, style TEXT, sku TEXT, category TEXT,
  size TEXT, asin TEXT, courier_status TEXT, qty INTEGER,
  amount NUMERIC, ship_city TEXT, ship_state TEXT, is_b2b BOOLEAN

Strict rules:
1. Only write SELECT statements — never INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE
2. Use ONLY the exact column names listed above, quoted with double quotes if needed
3. Use standard PostgreSQL date functions: CURRENT_DATE, date_trunc(), INTERVAL
4. Apply the metric filters and business rules provided
5. Return ONLY the JSON object — no markdown fences, no explanation
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
    Generates PostgreSQL SELECT SQL for the given question.
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
  "sql": "<complete SELECT statement targeting the orders table>",
  "columns_referenced": ["col1", "col2"],
  "confidence": <0.0 to 1.0>
}}"""

    response = await call_gemini(prompt, system=_SYSTEM, json_mode=True)

    try:
        # Strip markdown fences before loading
        text = response.strip()
        if text.startswith("```json"): text = text[7:]
        elif text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        result = json.loads(text.strip())
        
        return {
            "sql":                result.get("sql", "").strip(),
            "columns_referenced": result.get("columns_referenced", []),
            "confidence":         float(result.get("confidence", 0.5)),
        }
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[sql generator error] {e}")
        return {"sql": response.strip(), "columns_referenced": [], "confidence": 0.3}
