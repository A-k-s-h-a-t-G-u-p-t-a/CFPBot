import asyncio
import io
import json
import os
import time
import uuid
from datetime import date

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

load_dotenv()

from agents.guard_rail import guard_rail_check
from agents.rag_retriever import retrieve_context
from agents.reasoning_chain import ReasoningResult
from agents.response_generator import generate_response
from layers.agent_engine import run_agentic_query
from layers.conversation import add_turn, get_history, get_prior_request
from layers.execution.pg_engine import row_count
from layers.execution.result_cache import result_cache
from layers.query_understanding import StructuredRequest, understand_query
from layers.semantic_cache import semantic_cache
from layers.semantic_layer.metric_registry import (
    get_all_definitions,
    get_metric_context,
    resolve_metrics,
)
from layers.vector_store import get_collection_count
from utils.errors import ErrorCode, ErrorResponse
from utils.logger import LayerLogger

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="CFPBot Backend", version="3.0")

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
    if not os.getenv("DATABASE_URL"):
        issues.append("DATABASE_URL not set in .env — cannot connect to Neon")
    n = row_count()
    if n == 0:
        issues.append("orders table is empty — run: python ingest.py --csv data/orders.csv")
    for issue in issues:
        print(f"[STARTUP WARNING] {issue}")
    if not issues:
        print(f"[STARTUP] OK — {n:,} rows in orders table")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    question:   str
    session_id: str | None = None


# ---------------------------------------------------------------------------
# Helpers — request signatures and routing
# ---------------------------------------------------------------------------

def _build_cache_key(structured_req: StructuredRequest, resolved_metrics, mode: str) -> str:
    metric_keys = ",".join(m.key for m in resolved_metrics) if resolved_metrics else "none"
    dimensions = ",".join(structured_req.dimensions) if structured_req.dimensions else "none"
    time_window = json.dumps(structured_req.time_window, sort_keys=True, default=str)
    return f"{mode}:{structured_req.intent}:{metric_keys}:{dimensions}:{time_window}:{structured_req.output_type}"


# ---------------------------------------------------------------------------
# POST /api/query  — main pipeline
# ---------------------------------------------------------------------------

@app.post("/api/query")
async def query(request: QueryRequest):
    request_id = str(uuid.uuid4())
    log        = LayerLogger(request_id)
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # Layer 1: query understanding
        log.start("query_understanding")
        prior_req      = get_prior_request(session_id)
        # Use the latest date available in the dataset, otherwise time queries fail
        anchored_today = date(2022, 6, 29)
        structured_req = await understand_query(request.question, anchored_today, prior_req)

        if structured_req.ambiguity_score > float(os.getenv("AMBIGUITY_THRESHOLD", 0.7)):
            return JSONResponse(content={
                "clarify":    True,
                "question":   structured_req.clarifying_question or "Could you be more specific?",
                "session_id": session_id,
                "request_id": request_id,
            })
        log.data("query_understanding", "Structured Output", structured_req.__dict__)
        log.end("query_understanding", detail=f"intent={structured_req.intent} metrics={structured_req.metrics}")

        # Layer 2: semantic layer
        log.start("semantic_layer")
        resolved_metrics = resolve_metrics(structured_req.metrics)
        metric_context   = get_metric_context(request.question)
        metric_label     = resolved_metrics[0].label if resolved_metrics else "Order Volume"
        log.data("semantic_layer", "Metrics", [m.__dict__ if hasattr(m, "__dict__") else m for m in resolved_metrics])
        log.end("semantic_layer")

        # RAG path — definitions / policy questions
        is_rag = (
            not structured_req.metrics
            or any(w in request.question.lower() for w in ["what does", "what is", "define", "meaning of", "explain"])
        )

        cache_mode = "rag" if is_rag else "analytics"
        cache_key = _build_cache_key(structured_req, resolved_metrics, cache_mode)

        log.start("semantic_cache")
        cached = semantic_cache.lookup(request.question, cache_key=cache_key)
        if cached:
            log.end("semantic_cache", detail="hit")
            return {**cached, "trace": log.get_trace(), "from_cache": True, "session_id": session_id, "request_id": request_id}
        log.end("semantic_cache", detail="miss")

        if is_rag:
            log.start("rag")
            rag_ctx  = retrieve_context(structured_req.rewritten)
            log.data("rag", "Context Docs", rag_ctx)
            reasoning = ReasoningResult(
                intent="rag",
                rows=[],
                narrative_context={},
            )
            payload = await generate_response(request.question, reasoning, metric_label, rag_context=rag_ctx)
            log.end("rag")

        else:
            # Layer 3: agentic analytics engine
            log.start("agent_engine")
            reasoning = await run_agentic_query(request.question, structured_req, resolved_metrics, metric_context)
            log.data("agent_engine", "Reasoning Object", reasoning.__dict__)
            log.end("agent_engine", detail=f"intent={structured_req.intent}")

            # Layer 4: response generation
            log.start("response_generator")
            payload = await generate_response(request.question, reasoning, metric_label)
            log.data("response_generator", "Final Payload", payload)
            log.end("response_generator")

        # Guard rail
        payload["answer"] = guard_rail_check(
            payload["answer"], None, payload.get("confidence", 1.0)
        )

        # Persist
        semantic_cache.store(request.question, payload, cache_key=cache_key)
        add_turn(session_id, structured_req.__dict__, payload["answer"])

        return {**payload, "trace": log.get_trace(), "from_cache": False, "session_id": session_id, "request_id": request_id}

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

@app.get("/api/summary")
async def weekly_summary():
    request_id = str(uuid.uuid4())

    anchored_today = date(2022, 6, 29)
    structured_req = await understand_query("Give me a weekly summary", anchored_today, None)
    resolved_metrics = resolve_metrics(structured_req.metrics)
    metric_context = get_metric_context("Give me a weekly summary")

    reasoning = await run_agentic_query("Give me a weekly summary", structured_req, resolved_metrics, metric_context)
    payload   = await generate_response("Give me a weekly executive summary", reasoning, "Order Metrics")

    return {**payload, "request_id": request_id}


# ---------------------------------------------------------------------------
# GET /api/health
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {
        "status":             "ok",
        "db":                 "neon_postgres",
        "orders_row_count":   row_count(),
        "vector_schema_docs": get_collection_count("schema_docs"),
        "vector_metric_docs": get_collection_count("metric_docs"),
        "vector_examples":    get_collection_count("sample_queries"),
        "cache_entries":      len(semantic_cache._cache),
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

    # Try to get the last rows from result_cache
    raise HTTPException(status_code=404, detail="No cached query result found for export. Run a query first.")
