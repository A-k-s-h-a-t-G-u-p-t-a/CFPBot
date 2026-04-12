# NatWest CFPBot — Full Backend Build Plan (v2)
### Integrating: Query Understanding · Semantic Layer · Query Planner · Fast Execution · Insight Engine · Response Generator

---

## What Exists Already

Your Next.js 16 frontend repo is set up at `CFPBot/` with:
- Prisma 7 configured against PostgreSQL
- Tailwind CSS 4 + TypeScript

The entire backend is built from scratch as a separate Python FastAPI service.

---

## Full Pipeline Architecture

Every user message passes through 6 layers before a response is returned.
The key principle: **the LLM never calculates numbers — it only narrates results.**

```
User Message ("Why did mobile transactions drop last week?")
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 0 — Semantic Cache                                        │
│  Cosine similarity check against past questions (threshold 0.92) │
│  Cache hit → return instantly, skip all layers below             │
└─────────────────────────────────────────────────────────────────┘
        │ cache miss
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1 — Query Understanding                                   │
│  rules classifier → entity linker → (LLM only if ambiguous)     │
│  Injects prior_request from session for follow-up resolution     │
│                                                                   │
│  Outputs StructuredRequest:                                       │
│  { intent, metric, dimensions, time_window, granularity,         │
│    output_type, ambiguity_score, prior_request }                 │
└─────────────────────────────────────────────────────────────────┘
        │ ambiguity_score > 0.7 → return CLARIFY question to user
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2 — Semantic Layer                                        │
│  Resolves metric name → SQL fragments, joins, business rules     │
│                                                                   │
│  Outputs ResolvedMetric:                                          │
│  { sql_fragment, joins, filters, time_logic,                     │
│    dimension_hierarchy, lineage }                                 │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3 — Query Planner                                         │
│  Decides routing + decomposition strategy                        │
│                                                                   │
│  Routes to:  pre-aggregated Parquet / materialized view / SQL    │
│  Plans:      comparison baseline, driver analysis, decomposition  │
│  Merges:     multiple result sets if multi-metric query          │
│                                                                   │
│  Outputs ExecutionPlan:                                           │
│  { queries[], route, needs_driver_analysis, needs_sig_test }     │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3b — SQL Generator + Validator                            │
│  Generates SQL from ExecutionPlan + validates (no LLM on valid.) │
│  Retries up to 2 times on failure                                │
│  Gemini calls wrapped in exponential backoff + Semaphore(4)      │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 4 — Fast Execution (DuckDB)                               │
│  Columnar in-process engine — 10–100x faster than row-store PG  │
│  Pre-aggregation Parquet files for common rollups                │
│  Result cache for repeated exact queries                         │
│                                                                   │
│  Outputs RawResults: { rows, columns, execution_ms }             │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 5 — Insight Engine                                        │
│  Pure Python/numpy — no LLM call                                 │
│  Guards against empty results before every computation           │
│  trend detection · outlier detection · contribution analysis     │
│  decomposition · statistical significance · chart recommendation │
│                                                                   │
│  Outputs StructuredInsights:                                      │
│  { key_finding, anomalies[], drivers[], trends[],                │
│    chart_spec, source_tables[] }                                  │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 6 — Response Generator                                    │
│  LLM reads StructuredInsights — does NOT recalculate             │
│  Produces: plain-English narrative, source citations,            │
│  chart data payload, one follow-up suggestion                    │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 6b — Guard Rail                                           │
│  Pure Python — verifies every number in the answer appears       │
│  in StructuredInsights. Appends disclaimer if confidence < 0.7   │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
  JSON Response → Next.js 16 frontend
```

---

## Folder Structure

```
backend/
├── main.py                          # FastAPI app + orchestrator
│
├── agents/
│   ├── __init__.py
│   ├── sql_generator.py             # LLM: ExecutionPlan → SQL string
│   ├── sql_validator.py             # Pure Python: safety + syntax checks
│   ├── rag_retriever.py             # ChromaDB: RAG path only
│   ├── response_generator.py        # LLM: StructuredInsights → narrative
│   └── guard_rail.py                # Pure Python: hallucination check
│
├── layers/
│   │
│   ├── query_understanding/
│   │   ├── __init__.py
│   │   ├── intent_classifier.py     # Rules-first intent → LLM fallback
│   │   ├── entity_linker.py         # Maps terms to metric catalog entries
│   │   └── time_parser.py           # "last month" → {start, end} dates
│   │
│   ├── semantic_layer/
│   │   ├── __init__.py
│   │   ├── metric_registry.py       # Loads metrics.json, resolves to SQL
│   │   ├── dimension_hierarchy.py   # Channel > Region > Location hierarchy
│   │   └── business_rules.py        # Filters, exclusions, definition guards
│   │
│   ├── query_planner/
│   │   ├── __init__.py
│   │   ├── planner.py               # Builds ExecutionPlan from intent+metric
│   │   ├── route_decider.py         # pre-agg / materialized / raw SQL
│   │   └── result_merger.py         # Merges multiple result sets (multi-metric)
│   │
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── duckdb_engine.py         # Primary: fast columnar analytics
│   │   ├── pg_engine.py             # Fallback: PostgreSQL
│   │   └── result_cache.py          # Exact-query result cache (TTL 5 min)
│   │
│   ├── insight_engine/
│   │   ├── __init__.py
│   │   ├── trend_detector.py        # Moving avg, WoW/MoM change %
│   │   ├── outlier_detector.py      # Z-score detection (threshold > 2σ)
│   │   ├── contribution_analyzer.py # Which dimension drove the change
│   │   └── chart_recommender.py     # Auto-selects bar/pie/line/table
│   │
│   ├── vector_store.py              # ChromaDB client (RAG + few-shot)
│   ├── semantic_cache.py            # Embedding similarity cache (TTL 1hr)
│   └── conversation.py              # Session memory (last 5 StructuredRequests)
│
├── utils/
│   ├── __init__.py
│   ├── logger.py                    # Structured logging with request_id
│   ├── gemini_client.py             # Gemini wrapper: backoff + Semaphore
│   └── errors.py                    # ErrorResponse model + error codes
│
├── data/
│   ├── metrics.json
│   ├── schema_docs.txt
│   ├── sample_queries.json
│   └── aggregations/
│       ├── daily_by_channel.parquet
│       ├── weekly_by_location.parquet
│       └── monthly_summary.parquet
│
├── ingest.py                        # One-time: embed + load ChromaDB + DuckDB
├── precompute.py                    # One-time: build aggregation Parquet files
├── .env
└── requirements.txt
```

---

## Critical Fix 1 — Session Memory Stores `StructuredRequest`, Not Text

**Problem**: If session memory only stores `{role, content}` strings, a follow-up like "break that down by region" has nothing to resolve "that" against. The entity linker needs the previous intent, metric, and time window — not just the previous sentence.

### `layers/conversation.py`

```python
from dataclasses import dataclass, asdict

session_store: dict[str, list[dict]] = {}

def get_history(session_id: str) -> list[dict]:
    return session_store.get(session_id, [])

def add_turn(session_id: str, structured_request: dict, answer: str):
    """
    Stores the full StructuredRequest dict per turn, not just the raw text.
    The Query Understanding layer receives prior_request on the next turn
    so it can resolve "that", "those", "same period" correctly.
    """
    history = session_store.get(session_id, [])
    history.append({
        "role":             "user",
        "raw_question":     structured_request["raw_question"],
        "structured":       structured_request,   # full StructuredRequest dict
        "answer":           answer,
    })
    session_store[session_id] = history[-10:]     # keep last 5 turns (10 entries)

def get_prior_request(session_id: str) -> dict | None:
    """Returns the StructuredRequest from the most recent turn."""
    history = session_store.get(session_id, [])
    if not history:
        return None
    return history[-1].get("structured")
```

The `prior_request` is injected into Layer 1:

```python
# In main.py orchestrator
prior_request = get_prior_request(session_id)
structured_req = understand_query(question, today, prior_request)
```

---

## Critical Fix 2 — Structured Logging with `request_id`

**Problem**: Without tracing, when a failure happens during the demo there is no way to know which layer broke or how long each step took.

### `utils/logger.py`

```python
import logging
import uuid
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | req=%(request_id)s | layer=%(layer)s | %(message)s"
)
logger = logging.getLogger("cfpbot")

class LayerLogger:
    def __init__(self, request_id: str):
        self.request_id = request_id
        self._timings: dict[str, float] = {}

    def start(self, layer: str):
        self._timings[layer] = time.perf_counter()
        logger.info("started", extra={"request_id": self.request_id, "layer": layer})

    def end(self, layer: str, status: str = "ok", detail: str = ""):
        elapsed_ms = int((time.perf_counter() - self._timings[layer]) * 1000)
        logger.info(
            f"completed in {elapsed_ms}ms — {detail}",
            extra={"request_id": self.request_id, "layer": layer}
        )
        return elapsed_ms
```

Usage in orchestrator:

```python
request_id = str(uuid.uuid4())
log = LayerLogger(request_id)

log.start("query_understanding")
structured_req = understand_query(...)
log.end("query_understanding", detail=f"intent={structured_req.intent}")

log.start("duckdb_execution")
rows = execute_analytics_query(sql)
log.end("duckdb_execution", detail=f"rows={len(rows)}")
```

Every response includes `request_id` so the frontend can show it in the source panel — judges can cross-reference logs.

---

## Critical Fix 3 — Error Response Contract

**Problem**: If the SQL validator exhausts retries or Gemini times out, the frontend gets a raw 500. It does not know whether to show a retry button, a "rephrase" prompt, or a hard error.

### `utils/errors.py`

```python
from pydantic import BaseModel
from enum import Enum

class ErrorCode(str, Enum):
    AMBIGUOUS_QUERY        = "AMBIGUOUS_QUERY"        # Layer 1: ambiguity > 0.7
    METRIC_NOT_FOUND       = "METRIC_NOT_FOUND"        # Layer 2: unknown metric
    SQL_GENERATION_FAILED  = "SQL_GENERATION_FAILED"   # Layer 3b: all retries failed
    NO_DATA_FOUND          = "NO_DATA_FOUND"           # Layer 4: 0 rows returned
    LLM_UNAVAILABLE        = "LLM_UNAVAILABLE"         # Gemini rate-limit or timeout
    INTERNAL_ERROR         = "INTERNAL_ERROR"          # Unexpected exception

class ErrorResponse(BaseModel):
    error_code:   ErrorCode
    message:      str         # plain English — shown directly to user
    recoverable:  bool        # True = show retry, False = show "try rephrasing"
    request_id:   str
    suggestion:   str | None  # e.g. "Try asking about a specific channel instead"
```

All FastAPI exception handlers return this shape:

```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(status_code=500, content=ErrorResponse(
        error_code=ErrorCode.INTERNAL_ERROR,
        message="Something went wrong. Please try again.",
        recoverable=True,
        request_id=getattr(exc, "request_id", "unknown")
    ).model_dump())
```

The frontend TypeScript type:

```typescript
type ErrorResponse = {
  error_code: "AMBIGUOUS_QUERY" | "METRIC_NOT_FOUND" | "SQL_GENERATION_FAILED"
            | "NO_DATA_FOUND" | "LLM_UNAVAILABLE" | "INTERNAL_ERROR";
  message:    string;
  recoverable: boolean;
  request_id: string;
  suggestion?: string;
}
```

---

## Critical Fix 4 — Gemini Rate-Limit Backoff

**Problem**: Gemini 2.0 Flash free tier allows 15 requests/minute. The weekly summary endpoint fires 4 parallel Gemini calls. During a busy demo, you will hit a 429 and the system will crash visibly.

### `utils/gemini_client.py`

```python
import asyncio
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Cap concurrent Gemini calls across all agents
_gemini_semaphore = asyncio.Semaphore(4)

model = genai.GenerativeModel("gemini-2.0-flash")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(Exception),
)
async def call_gemini(prompt: str, system: str = "", json_mode: bool = False) -> str:
    """
    All agents call this function — never call the Gemini SDK directly.
    Handles:
      - Semaphore to cap concurrent calls to 4
      - Automatic retry: 1s → 2s → 4s backoff on any exception
      - json_mode=True enables structured JSON output
    """
    async with _gemini_semaphore:
        config = {"response_mime_type": "application/json"} if json_mode else {}
        response = await model.generate_content_async(
            [system, prompt] if system else prompt,
            generation_config=config
        )
        return response.text
```

Add `tenacity` to `requirements.txt`:
```
tenacity==8.3.0
```

---

## Critical Fix 5 — Insight Engine Empty-Result Guards

**Problem**: If the SQL returns 0 rows, every Insight Engine function receives an empty list and crashes with `ZeroDivisionError` or `IndexError`. The Response Generator then hallucinates because it has no data to narrate.

### Rule: every insight function starts with this guard

```python
# In every function inside layers/insight_engine/

from dataclasses import dataclass

@dataclass
class EmptyInsight:
    reason: str = "no_data"
    message: str = "No transactions found for this period."

def detect_trend(rows: list[dict], value_col: str, time_col: str):
    if not rows:
        return EmptyInsight()
    # ... rest of function

def detect_outliers(rows: list[dict], value_col: str):
    if len(rows) < 10:          # z-score is meaningless below 10 data points
        return EmptyInsight(reason="insufficient_data",
                            message="Not enough data points for anomaly detection.")
    # ... rest of function

def analyze_contribution(rows: list[dict], ...):
    if not rows:
        return EmptyInsight()
    # ... rest of function
```

The Response Generator checks for `EmptyInsight` before narrating:

```python
def generate_response(question, insights, metric_used):
    if isinstance(insights.key_finding, EmptyInsight):
        return ResponsePayload(
            answer=insights.key_finding.message,
            chart_type=None,
            chart_data=None,
            ...
        )
    # normal narration path
```

---

## Critical Fix 6 — Multi-Metric Query Merging

**Problem**: "Compare revenue and volume by channel" requires two SQL queries. `ExecutionPlan.queries[]` supports this but there is no function that merges the two result sets before passing to the Insight Engine.

### `layers/query_planner/result_merger.py`

```python
def merge_results(
    results: list[list[dict]],
    join_on: list[str],         # shared dimension columns, e.g. ["Channel"]
    plan: "ExecutionPlan"
) -> list[dict]:
    """
    Merges multiple query result sets by their shared dimension columns.

    Example:
      results[0] = [{"Channel": "Mobile", "revenue": 12000}, ...]
      results[1] = [{"Channel": "Mobile", "volume": 450}, ...]
      join_on    = ["Channel"]

    Output:
      [{"Channel": "Mobile", "revenue": 12000, "volume": 450}, ...]

    If a dimension value appears in one result but not the other,
    the missing metric is filled with None (never dropped).
    """
    if len(results) == 1:
        return results[0]

    # Build lookup dict keyed by join_on values
    merged: dict[tuple, dict] = {}
    for result_set in results:
        for row in result_set:
            key = tuple(row[col] for col in join_on)
            merged.setdefault(key, {col: row[col] for col in join_on})
            merged[key].update({k: v for k, v in row.items() if k not in join_on})

    return list(merged.values())
```

In the orchestrator, execution and merging happen together:

```python
# Execute all queries in the plan concurrently
raw_results = await asyncio.gather(*[
    execute_analytics_query(q) for q in plan.queries
])

# Merge before passing to Insight Engine
merged = merge_results(raw_results, join_on=plan.shared_dimensions, plan=plan)
insights = run_insight_engine(merged, structured_req)
```

---

## Layer 1 — Query Understanding

### Design: Rules First, LLM Only for Ambiguous Cases

```python
# layers/query_understanding/intent_classifier.py

INTENT_RULES = {
    "compare":         ["compare", "vs", "versus", "difference", "more than", "less than"],
    "breakdown":       ["breakdown", "by", "split", "per", "each", "across"],
    "driver_analysis": ["why", "reason", "cause", "drove", "explain", "factor"],
    "summary":         ["summary", "overview", "report", "this week", "today"],
    "trend":           ["trend", "over time", "grew", "declined", "trajectory"],
}

def classify_intent(question: str) -> tuple[str, float]:
    """
    Returns (intent, confidence).
    If confidence < 0.6, falls through to Gemini for disambiguation.
    """
```

```python
# layers/query_understanding/entity_linker.py

def link_to_metric_catalog(question: str, catalog: dict, prior_request: dict | None) -> list[str]:
    """
    Maps question terms to metric catalog entries.
    If prior_request exists and question contains "that"/"those"/"same",
    inherits the metric from prior_request["metrics"].
    """
```

```python
# layers/query_understanding/time_parser.py

def parse_time_window(question: str, today: date) -> dict:
    """
    "last week"    → {start: "2026-04-04", end: "2026-04-10", granularity: "daily"}
    "last month"   → {start: "2026-03-01", end: "2026-03-31", granularity: "daily"}
    "WoW"          → {current_week: ..., prior_week: ..., comparison: True}
    "this quarter" → {start: "2026-01-01", end: "2026-03-31", granularity: "weekly"}
    """
```

### StructuredRequest Output Shape

```python
@dataclass
class StructuredRequest:
    raw_question:    str
    rewritten:       str
    intent:          str              # compare | breakdown | driver | summary | trend
    metrics:         list[str]        # ["transaction_volume", "revenue"]
    dimensions:      list[str]        # ["channel", "location"]
    time_window:     dict             # {start, end, granularity, comparison}
    output_type:     str              # table | narrative | chart | both
    ambiguity_score: float            # > 0.7 triggers CLARIFY
    prior_request:   dict | None      # previous turn's StructuredRequest
```

---

## Layer 2 — Semantic Layer

### `data/metrics.json`

```json
{
  "revenue": {
    "label": "Revenue",
    "column": "TransactionAmount",
    "aggregation": "SUM",
    "filter": "TransactionType = 'Credit'",
    "joins": [],
    "time_column": "TransactionDate",
    "description": "Total money received from credit transactions",
    "unit": "GBP",
    "lineage": ["transactions.TransactionAmount", "transactions.TransactionType"],
    "business_rules": [
      "Exclude transactions where LoginAttempts > 5",
      "Only count completed transactions"
    ]
  },
  "transaction_volume": {
    "label": "Transaction Volume",
    "column": "TransactionID",
    "aggregation": "COUNT",
    "filter": null,
    "joins": [],
    "time_column": "TransactionDate",
    "description": "Total number of transactions",
    "unit": "count",
    "lineage": ["transactions.TransactionID"],
    "business_rules": []
  },
  "average_transaction": {
    "label": "Average Transaction Value",
    "column": "TransactionAmount",
    "aggregation": "AVG",
    "filter": null,
    "joins": [],
    "description": "Mean transaction amount across all types",
    "unit": "GBP",
    "lineage": ["transactions.TransactionAmount"]
  },
  "churn_risk": {
    "label": "Churn Risk Accounts",
    "column": "AccountID",
    "aggregation": "COUNT DISTINCT",
    "filter": "PreviousTransactionDate < CURRENT_DATE - INTERVAL '90 days'",
    "joins": [],
    "description": "Accounts with no activity in the last 90 days",
    "unit": "accounts",
    "lineage": ["transactions.AccountID", "transactions.PreviousTransactionDate"]
  }
}
```

---

## Layer 3 — Query Planner

### Route Decision Tree

```
Is there a pre-aggregated Parquet that covers this metric + dimension + time_window?
  ├── YES → route = "pre_agg"        (query Parquet via DuckDB — fastest)
  └── NO  →
       Is there a materialized view in PostgreSQL?
         ├── YES → route = "materialized"
         └── NO  → route = "raw_sql"   (full scan, DuckDB still fast)
```

### `layers/query_planner/planner.py`

```python
@dataclass
class ExecutionPlan:
    route:                   str
    queries:                 list[str]     # one per metric — merged after execution
    shared_dimensions:       list[str]     # used by result_merger.py
    comparison_query:        str | None
    needs_driver_analysis:   bool
    needs_significance_test: bool
    decompose_by:            list[str]
    pre_agg_file:            str | None
```

---

## Layer 4 — Fast Execution (DuckDB)

**Why DuckDB over PostgreSQL for analytics:**
- In-process, no server — same simplicity as SQLite
- Columnar storage — 10–100x faster on GROUP BY + SUM queries
- Reads Parquet files natively
- Persisted to a `.db` file so startup is instant on second run

### `layers/execution/duckdb_engine.py`

```python
import duckdb

# Persisted DB — loads instantly after first ingest
_conn = duckdb.connect("data/analytics.db")

def execute_analytics_query(sql: str) -> list[dict]:
    """
    Runs on the persisted DuckDB instance.
    Hard limit: 1000 rows.
    Falls back to pg_engine.py if DuckDB raises.
    """
    try:
        result = _conn.execute(sql + " LIMIT 1000").fetchdf()
        return result.to_dict(orient="records")
    except Exception as e:
        return pg_engine.execute_safe_query(sql)

def query_pre_agg(file_path: str, filters: dict) -> list[dict]:
    """Directly queries a Parquet file — no SQL generation needed."""
    sql = f"SELECT * FROM read_parquet('{file_path}')"
    return _conn.execute(sql).fetchdf().to_dict(orient="records")
```

---

## Layer 5 — Insight Engine

All functions start with empty-result guards (Critical Fix 5).

### `layers/insight_engine/trend_detector.py`

```python
def detect_trend(rows: list[dict], value_col: str, time_col: str):
    if not rows:
        return EmptyInsight()
    # 7-day moving average, returns direction + pct_change + peak + trough
```

### `layers/insight_engine/outlier_detector.py`

```python
def detect_outliers(rows: list[dict], value_col: str):
    if len(rows) < 10:
        return EmptyInsight(reason="insufficient_data")
    # Z-score per point, flags |z| > 2.0 as spike or drop
```

### `layers/insight_engine/contribution_analyzer.py`

```python
def analyze_contribution(rows: list[dict], dimension_col: str, value_col: str, total_change: float):
    if not rows:
        return EmptyInsight()
    # Ranks each dimension member by % contribution to total_change
```

### `layers/insight_engine/chart_recommender.py`

```python
def recommend_chart(req: StructuredRequest, rows: list[dict]) -> dict:
    """
    Rule-based — not LLM-based:
    compare     → bar (side by side)
    breakdown   → pie (≤6 categories) else bar
    trend       → line
    summary     → table
    driver      → horizontal bar (contribution %)
    """
```

### StructuredInsights Shape

```python
@dataclass
class StructuredInsights:
    key_finding:   str | EmptyInsight
    anomalies:     list[dict]
    drivers:       list[dict]
    trends:        list[dict]
    chart_spec:    dict
    source_tables: list[str]
    columns_used:  list[str]
    execution_ms:  int
```

---

## Layer 6 — Response Generator

**The LLM's only job is narration.** It reads `StructuredInsights` and writes plain English. It never recalculates.

### Gemini System Prompt Rules

```
You are a bank data analyst summarising pre-calculated findings.
You will receive a JSON object called StructuredInsights.
Rules:
1. Never recalculate any numbers — use exactly what is in StructuredInsights.
2. Lead with the key_finding number.
3. Explain one driver (from drivers[0]) in plain English.
4. If anomalies is non-empty, mention the spike/drop with its date.
5. Cite the source_tables in one sentence at the end.
6. Max 3 sentences. No SQL jargon. No column names.
7. Suggest one follow-up question.
```

---

## Layer 6b — Guard Rail

```python
def guard_rail_check(answer: str, insights: StructuredInsights, confidence: float) -> str:
    if isinstance(insights.key_finding, EmptyInsight):
        return insights.key_finding.message  # override with "No data found"
    # Extract all numbers from answer, verify each appears in insights
    # If confidence < 0.7, append disclaimer
    return answer
```

---

## FastAPI Orchestrator (`main.py`)

### `POST /api/query`

```python
@app.post("/api/query")
async def query(request: QueryRequest):
    request_id = str(uuid.uuid4())
    log = LayerLogger(request_id)
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # Layer 0: semantic cache
        log.start("semantic_cache")
        cached = semantic_cache.lookup(request.question)
        if cached:
            log.end("semantic_cache", detail="hit")
            return {**cached, "from_cache": True, "session_id": session_id, "request_id": request_id}
        log.end("semantic_cache", detail="miss")

        # Layer 1: query understanding
        log.start("query_understanding")
        prior_req = get_prior_request(session_id)
        structured_req = understand_query(request.question, date.today(), prior_req)
        if structured_req.ambiguity_score > float(os.getenv("AMBIGUITY_THRESHOLD", 0.7)):
            return {"clarify": True, "question": structured_req.clarifying_question,
                    "request_id": request_id, "session_id": session_id}
        log.end("query_understanding", detail=f"intent={structured_req.intent}")

        # Layer 2: semantic layer
        log.start("semantic_layer")
        resolved = resolve_metrics(structured_req.metrics)
        log.end("semantic_layer")

        # Layer 3: query planner
        log.start("query_planner")
        plan = build_plan(structured_req, resolved)
        log.end("query_planner", detail=f"route={plan.route}, queries={len(plan.queries)}")

        if plan.route == "rag":
            context = retrieve_context(structured_req.rewritten, chroma_client)
            insights = StructuredInsights(key_finding=context, ...)
        else:
            # Layer 3b: SQL generation + validation
            log.start("sql_generation")
            sqls = []
            for q in plan.queries:
                sql_json = await call_gemini(build_sql_prompt(q), json_mode=True)
                sql = json.loads(sql_json)["sql"]
                for attempt in range(int(os.getenv("MAX_SQL_RETRIES", 2))):
                    valid, reason = validate_sql(sql, allowed_columns)
                    if valid:
                        break
                    sql_json = await call_gemini(build_sql_prompt(q, error=reason), json_mode=True)
                    sql = json.loads(sql_json)["sql"]
                sqls.append(sql)
            log.end("sql_generation", detail=f"queries={len(sqls)}")

            # Layer 4: execution
            log.start("execution")
            raw_results = await asyncio.gather(*[execute_analytics_query(s) for s in sqls])
            merged = merge_results(list(raw_results), plan.shared_dimensions, plan)
            log.end("execution", detail=f"rows={len(merged)}")

            # Layer 5: insight engine
            log.start("insight_engine")
            insights = run_insight_engine(merged, structured_req)
            log.end("insight_engine")

        # Layer 6: response generation
        log.start("response_generator")
        payload = await generate_response(structured_req.raw_question, insights, resolved)
        payload["sql_used"] = sqls[0] if plan.route != "rag" else ""
        log.end("response_generator")

        # Guard rail
        payload["answer"] = guard_rail_check(payload["answer"], insights, payload.get("confidence", 1.0))

        # Store in cache + session
        semantic_cache.store(request.question, payload)
        add_turn(session_id, asdict(structured_req), payload["answer"])

        return {**payload, "from_cache": False, "session_id": session_id, "request_id": request_id}

    except Exception as e:
        log.end("error", status="error", detail=str(e))
        raise
```

### Other Endpoints

```python
@app.get("/api/summary")   # 4 parallel pre-canned ExecutionPlans
@app.get("/api/health")    # DB status, ChromaDB count, cache hit rate
@app.get("/api/metrics")   # Full metric dictionary for frontend
@app.delete("/api/cache")  # Reset semantic cache for demo
@app.get("/api/export")    # Last query rows as CSV download
```

---

## `requirements.txt`

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
google-generativeai==0.8.3
sentence-transformers==3.0.1
chromadb==0.5.0
duckdb==0.10.3
psycopg2-binary==2.9.9
pandas==2.2.0
pyarrow==16.0.0
python-dotenv==1.0.1
pydantic==2.8.0
numpy==1.26.4
scipy==1.13.0
tenacity==8.3.0
```

---

## `.env`

```
GEMINI_API_KEY=your_key_here
DB_URL=postgresql://readonly_user:hackathon2024@localhost:5432/natwest_demo
CACHE_THRESHOLD=0.92
AMBIGUITY_THRESHOLD=0.7
MAX_SQL_RETRIES=2
RESULT_CACHE_TTL_SECONDS=300
SEMANTIC_CACHE_TTL_HOURS=1
```

---

## ChromaDB — What It Still Does in v2

ChromaDB was not removed. Its role narrowed from 3 jobs in v1 to 2 jobs in v2:

| Job | v1 | v2 |
|---|---|---|
| Schema context for SQL generator | ChromaDB vector search | Semantic Layer direct lookup (more reliable) |
| Few-shot SQL examples for SQL generator | ChromaDB | Still ChromaDB |
| RAG path ("what does revenue mean?") | ChromaDB | Still ChromaDB |

The reason schema context moved out of ChromaDB: a fuzzy vector search returning "the most similar schema doc" is less reliable than a direct structured lookup by metric name. ChromaDB remains essential for the RAG path and few-shot examples.

---

## Build Order (2-day sprint)

### Day 1 — Data + Infrastructure

| # | Task | Files |
|---|---|---|
| 1 | Python venv, install deps, `.env` | `requirements.txt`, `.env` |
| 2 | `utils/logger.py`, `utils/errors.py`, `utils/gemini_client.py` | Critical fixes 2, 3, 4 |
| 3 | Write `data/schema_docs.txt` + `data/metrics.json` | `data/` |
| 4 | DuckDB engine (persisted `.db` file) + PG fallback | `layers/execution/` |
| 5 | Load CSV into DuckDB, build Parquet pre-aggs | `ingest.py`, `precompute.py` |
| 6 | ChromaDB ingest (schema docs + metrics + SQL examples) | `ingest.py` |
| 7 | Semantic cache (cosine sim, 1hr TTL) | `layers/semantic_cache.py` |
| 8 | Session memory (stores `StructuredRequest`) | `layers/conversation.py` |
| 9 | Metric registry + dimension hierarchy | `layers/semantic_layer/` |

### Day 2 — Agents + Wire-up

| # | Task | Files |
|---|---|---|
| 1 | Query Understanding (classifier + entity linker + time parser) | `layers/query_understanding/` |
| 2 | Query Planner + `result_merger.py` | `layers/query_planner/` |
| 3 | SQL Generator (uses ExecutionPlan, returns JSON via Gemini) | `agents/sql_generator.py` |
| 4 | SQL Validator (pure Python) | `agents/sql_validator.py` |
| 5 | Insight Engine (all 4 files, with empty-result guards) | `layers/insight_engine/` |
| 6 | Response Generator (reads StructuredInsights) | `agents/response_generator.py` |
| 7 | Guard Rail | `agents/guard_rail.py` |
| 8 | FastAPI orchestrator + all endpoints | `main.py` |
| 9 | CORS config + Next.js integration test | `main.py` |
| 10 | Demo dry-run: all 4 judge questions end-to-end | — |

---

## API Response Shapes (for Next.js)

```typescript
// Success
type QueryResponse = {
  answer:        string;
  chart_type:    "bar" | "pie" | "line" | "table";
  chart_data:    object;
  metric_used:   string;
  columns_used:  string[];
  source_tables: string[];
  sql_used:      string;
  from_cache:    boolean;
  session_id:    string;
  request_id:    string;       // for source panel + log cross-reference
  confidence:    number;
  anomaly_flag:  string | null;
  follow_up:     string;
}

// Error
type ErrorResponse = {
  error_code:  "AMBIGUOUS_QUERY" | "METRIC_NOT_FOUND" | "SQL_GENERATION_FAILED"
             | "NO_DATA_FOUND" | "LLM_UNAVAILABLE" | "INTERNAL_ERROR";
  message:    string;
  recoverable: boolean;
  request_id: string;
  suggestion?: string;
}

// Clarify (ambiguity > 0.7)
type ClarifyResponse = {
  clarify:    true;
  question:   string;   // e.g. "Do you mean revenue or transaction volume?"
  session_id: string;
  request_id: string;
}
```

---

## Demo Sequence for Judges (5 minutes)

| Step | Action | What It Shows |
|---|---|---|
| 1 | "Why did transaction volume drop last week?" | Driver analysis → ranked contribution by channel |
| 2 | "Which location drove most of that drop?" | Session memory + `prior_request` resolving "that" |
| 3 | Ask Q1 again | Semantic cache → `from_cache: true`, ~50ms |
| 4 | "What does 'revenue' mean here?" | RAG path → metric registry definition |
| 5 | Click "Weekly Summary" | 4 parallel ExecutionPlans → 4-bullet executive summary |
| 6 | Open `/api/health` in browser | Live cache hit rate, row count, avg response ms |
| 7 | Ask an ambiguous question | CLARIFY response with suggested rephrasing |
