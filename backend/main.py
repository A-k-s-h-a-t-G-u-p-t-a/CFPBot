import asyncio
import io
import json
import os
import time
import uuid
from dataclasses import asdict
from datetime import date

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

load_dotenv()

from agents.guard_rail import guard_rail_check
from agents.rag_retriever import retrieve_context
from agents.response_generator import generate_response
from agents.sql_generator import generate_sql
from agents.sql_validator import ALLOWED_COLUMNS, validate_sql
from layers.conversation import add_turn, get_history, get_prior_request
from layers.execution.duckdb_engine import execute_analytics_query, query_pre_agg, row_count
from layers.execution.result_cache import result_cache
from layers.insight_engine import EmptyInsight, StructuredInsights, run_insight_engine
from layers.query_planner.planner import build_plan
from layers.query_planner.result_merger import merge_results
from layers.query_understanding import StructuredRequest, understand_query
from layers.semantic_cache import semantic_cache
from layers.semantic_layer.metric_registry import (
    get_all_definitions,
    get_metric_context,
    resolve_metrics,
)
from layers.vector_store import get_collection_count, get_relevant_examples, get_relevant_schema
from utils.errors import ErrorCode, ErrorResponse
from utils.gemini_client import call_gemini
from utils.logger import LayerLogger

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="CFPBot Backend", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_check():
    issues = []
    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_key_here":
        issues.append("GEMINI_API_KEY not set in .env")
    if row_count() == 0:
        issues.append("DuckDB is empty — run: python ingest.py")
    for issue in issues:
        print(f"[STARTUP WARNING] {issue}")
    if not issues:
        print(f"[STARTUP] OK — {row_count():,} rows loaded")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    question:   str
    session_id: str | None = None


# ---------------------------------------------------------------------------
# POST /api/query  — main pipeline
# ---------------------------------------------------------------------------

@app.post("/api/query")
async def query(request: QueryRequest):
    request_id = str(uuid.uuid4())
    log        = LayerLogger(request_id)
    session_id = request.session_id or str(uuid.uuid4())
    sql_used   = ""
    insights   = StructuredInsights(key_finding=EmptyInsight(), source_tables=["transactions"])

    # Layer 0: semantic cache
    log.start("semantic_cache")
    cached = semantic_cache.lookup(request.question)
    if cached:
        log.end("semantic_cache", detail="hit")
        return {**cached, "from_cache": True, "session_id": session_id, "request_id": request_id}
    log.end("semantic_cache", detail="miss")

    try:
        # Layer 1: query understanding
        log.start("query_understanding")
        prior_req      = get_prior_request(session_id)
        structured_req = await understand_query(request.question, date.today(), prior_req)

        if structured_req.ambiguity_score > float(os.getenv("AMBIGUITY_THRESHOLD", 0.7)):
            return JSONResponse(content={
                "clarify":    True,
                "question":   structured_req.clarifying_question or "Could you be more specific?",
                "session_id": session_id,
                "request_id": request_id,
            })
        log.end("query_understanding", detail=f"intent={structured_req.intent} metrics={structured_req.metrics}")

        # Layer 2: semantic layer
        log.start("semantic_layer")
        resolved_metrics = resolve_metrics(structured_req.metrics)
        metric_context   = get_metric_context(request.question)
        metric_label     = resolved_metrics[0].label if resolved_metrics else "Transaction Volume"
        source_tables    = list({t.split(".")[0] for m in resolved_metrics for t in m.lineage}) or ["transactions"]
        columns_used     = list({m.column for m in resolved_metrics})
        log.end("semantic_layer")

        # RAG path — triggered when user asks about definitions/policies
        is_rag = (
            not structured_req.metrics
            or any(w in request.question.lower() for w in ["what does", "what is", "define", "meaning of", "explain"])
        )

        if is_rag:
            log.start("rag")
            rag_ctx  = retrieve_context(structured_req.rewritten)
            insights = StructuredInsights(key_finding="", source_tables=source_tables, columns_used=columns_used)
            payload  = await generate_response(request.question, insights, metric_label, rag_context=rag_ctx)
            log.end("rag")

        else:
            # Layer 3: query planner
            log.start("query_planner")
            plan = build_plan(structured_req, resolved_metrics)
            log.end("query_planner", detail=f"route={plan.route}")

            # Layer 3b: SQL generation + validation
            log.start("sql_generation")
            schema_ctx  = get_relevant_schema(structured_req.rewritten)
            few_shot    = get_relevant_examples(structured_req.rewritten)
            error_ctx   = ""
            sql_result  = await generate_sql(
                structured_req.rewritten, metric_context, schema_ctx, few_shot, plan
            )
            sql_used    = sql_result["sql"]
            confidence  = sql_result.get("confidence", 0.5)
            columns_used = sql_result.get("columns_referenced", columns_used)

            valid = False
            for _ in range(int(os.getenv("MAX_SQL_RETRIES", 2))):
                valid, reason = validate_sql(sql_used, ALLOWED_COLUMNS)
                if valid:
                    break
                error_ctx  = reason
                sql_result = await generate_sql(
                    structured_req.rewritten, metric_context, schema_ctx,
                    few_shot, plan, error_context=reason,
                )
                sql_used   = sql_result["sql"]
                confidence = sql_result.get("confidence", 0.3)

            if not valid:
                return JSONResponse(status_code=422, content=ErrorResponse(
                    error_code=ErrorCode.SQL_GENERATION_FAILED,
                    message="I couldn't generate a valid query for that question. Try rephrasing.",
                    recoverable=False,
                    request_id=request_id,
                    suggestion="Try being more specific, e.g. 'Show transaction volume by channel last week'",
                ).model_dump())
            log.end("sql_generation", detail=f"confidence={confidence:.2f}")

            # Layer 4: execution
            log.start("execution")
            t0          = time.perf_counter()
            cached_rows = result_cache.get(sql_used)
            if cached_rows is not None:
                rows = cached_rows
            elif plan.route == "pre_agg" and plan.pre_agg_file:
                rows = query_pre_agg(plan.pre_agg_file)
            else:
                rows = execute_analytics_query(sql_used)
            if cached_rows is None:
                result_cache.set(sql_used, rows)
            exec_ms = int((time.perf_counter() - t0) * 1000)
            log.end("execution", detail=f"rows={len(rows)} ms={exec_ms}")

            # Layer 5: insight engine
            log.start("insight_engine")
            insights = run_insight_engine(
                rows, structured_req,
                columns_used=columns_used,
                source_tables=source_tables,
                execution_ms=exec_ms,
            )
            log.end("insight_engine")

            # Layer 6: response generator
            log.start("response_generator")
            payload             = await generate_response(request.question, insights, metric_label)
            payload["sql_used"] = sql_used
            payload["confidence"] = confidence
            log.end("response_generator")

        # Guard rail
        payload["answer"] = guard_rail_check(
            payload["answer"], insights, payload.get("confidence", 1.0)
        )

        # Persist to cache and session
        semantic_cache.store(request.question, payload)
        add_turn(session_id, asdict(structured_req), payload["answer"])

        return {**payload, "from_cache": False, "session_id": session_id, "request_id": request_id}

    except Exception as exc:
        log.error("orchestrator", str(exc))
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Something went wrong. Please try again.",
                recoverable=True,
                request_id=request_id,
            ).model_dump(),
        ) from exc


# ---------------------------------------------------------------------------
# GET /api/summary  — weekly executive summary
# ---------------------------------------------------------------------------

_SUMMARY_QUESTIONS = [
    "Total transaction volume this week vs last week with percentage change",
    "Top channel by transaction volume this week",
    "Average transaction amount by location top 5 this month",
    "Biggest single day transaction spike this week",
]


@app.get("/api/summary")
async def weekly_summary():
    request_id = str(uuid.uuid4())

    async def run_one(q: str):
        res = await query(QueryRequest(question=q, session_id="summary"))
        if hasattr(res, "body"):
            return json.loads(res.body).get("answer", "Data unavailable")
        if isinstance(res, dict):
            return res.get("answer", "Data unavailable")
        return "Data unavailable"

    answers = await asyncio.gather(*[run_one(q) for q in _SUMMARY_QUESTIONS], return_exceptions=True)
    answers = [str(a) if isinstance(a, Exception) else a for a in answers]

    prompt = f"""Produce a 4-bullet weekly executive bank summary. Each bullet: one sentence, one key number.
No technical terms. No SQL. Plain English.

Findings:
1. {answers[0]}
2. {answers[1]}
3. {answers[2]}
4. {answers[3]}

Respond in JSON: {{"bullets": ["...", "...", "...", "..."]}}"""

    try:
        result  = json.loads(await call_gemini(prompt, json_mode=True))
        bullets = result.get("bullets", answers)
    except Exception:
        bullets = answers

    return {"bullets": bullets, "request_id": request_id}


# ---------------------------------------------------------------------------
# GET /api/health
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {
        "status":          "ok",
        "duckdb_rows":     row_count(),
        "chroma_schema":   get_collection_count("schema_docs"),
        "chroma_metrics":  get_collection_count("metric_docs"),
        "chroma_examples": get_collection_count("sample_queries"),
        "cache_hit_rate":  semantic_cache.hit_rate(),
        "cache_entries":   len(semantic_cache._cache),
    }


# ---------------------------------------------------------------------------
# GET /api/metrics  — metric dictionary for frontend
# ---------------------------------------------------------------------------

@app.get("/api/metrics")
async def get_metrics():
    return get_all_definitions()


# ---------------------------------------------------------------------------
# DELETE /api/cache  — reset caches for demo
# ---------------------------------------------------------------------------

@app.delete("/api/cache")
async def clear_cache():
    semantic_cache.invalidate_all()
    result_cache.clear()
    return {"status": "cleared", "message": "Semantic and result caches cleared."}


# ---------------------------------------------------------------------------
# GET /api/export  — download last query as CSV
# ---------------------------------------------------------------------------

@app.get("/api/export")
async def export(session_id: str):
    history = get_history(session_id)
    if not history:
        raise HTTPException(status_code=404, detail="Session not found")

    sql = history[-1].get("structured", {}).get("sql_used", "")
    if not sql:
        raise HTTPException(status_code=404, detail="No SQL found for this session")

    rows = execute_analytics_query(sql)
    if not rows:
        return JSONResponse(content={"data": []})

    import csv
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"},
    )
