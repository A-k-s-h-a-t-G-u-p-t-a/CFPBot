# MetricLens — Conversational Financial Analytics Platform

> A full-stack AI system that turns plain-English business questions into validated analytical insights — no SQL, no dashboards, no data team required.

---

## What MetricLens Does

MetricLens is an **AI-powered conversational BI copilot** that combines natural-language understanding, semantic metric mapping, agentic SQL execution, and statistical insight extraction into a single chat interface.

```
"Why did revenue drop last week?"
        ↓
MetricLens understands intent → maps to business metrics → generates + validates SQL
        ↓
Executes against live transaction data → extracts trends, outliers, drivers
        ↓
"Revenue fell 12.4% WoW. The primary driver was a 31% drop in Online Banking
 channel transactions on Tuesday — flagged as a statistical outlier (z = 2.8)."
```

**Core design principle:** The LLM never calculates numbers. Every figure originates from real SQL against real data. Gemini is used for language and narration only — never arithmetic.

---

## Architecture at a Glance

<img width="1025" height="576" alt="image" src="https://github.com/user-attachments/assets/68750ce9-2040-4ee4-8760-907ca642fe13" />


---

## The 7-Layer Backend Pipeline

Every user question passes through a deterministic, layered pipeline before a single LLM token is generated for the response. This makes the system fast, auditable, and hallucination-resistant.

<img width="1376" height="768" alt="image" src="https://github.com/user-attachments/assets/0c60f2ef-fbaa-420d-982c-7eda8fe2684f" />


---

## RAG Path — Definitions & Policy Questions

When a question is definitional ("What does chargeback rate mean?"), the pipeline bypasses SQL entirely and routes to retrieval-augmented generation:

<img width="1376" height="768" alt="image" src="https://github.com/user-attachments/assets/9ba80989-7032-4c2c-aa5d-d490b6a89cf5" />


---

## Product Features

| Feature | What It Delivers |
|---|---|
| **Conversational Analytics** | Session-aware chat with follow-up resolution and clarification prompts |
| **Intent & Entity Understanding** | Classifies intent (compare, trend, breakdown, driver, summary) and links terms to metric registry |
| **Semantic Metric Layer** | Business semantics decoupled from raw schema — metric definitions, dimension hierarchies, domain rules |
| **Agentic SQL Pipeline** | Generate → validate → execute → repair loop with schema-aware safety guards |
| **Insight Engine** | Trend detection, outlier flagging, contribution analysis, chart recommendation — all deterministic Python |
| **RAG for Definitions** | Retrieval-augmented path for explanatory questions using vectorised schema and metric docs |
| **Two-Level Caching** | Semantic cache (cosine similarity) + SQL result cache for near-zero latency on repeated queries |
| **Auth & User Isolation** | NextAuth credentials auth, bcrypt hashing, per-user conversation scoping |

---

## Technology Stack

### Frontend

| | Technology |
|---|---|
| Framework | Next.js 16.2 — App Router |
| UI Library | React 19 |
| Language | TypeScript |
| Styling | Tailwind CSS v4 |
| Animations | Framer Motion 12 |
| Authentication | NextAuth v4 (credentials provider) |
| ORM | Prisma 7 — PostgreSQL adapter |
| Icons | Tabler Icons, Lucide React |

### Backend

| | Technology |
|---|---|
| API Server | FastAPI (Python) — async, Pydantic-typed |
| LLM | Google Gemini — SQL generation + response narration |
| Database | PostgreSQL via Neon (serverless, connection pooling) |
| Numerical Analysis | NumPy — trend detection, outlier scoring, contribution analysis |
| Vector Retrieval | Semantic vector store — schema docs, metric docs, sample queries |
| Session State | In-memory session store — 30-minute TTL, auto-expiry |
| Caching | Semantic cache (cosine similarity ≥ 0.92) + SQL result cache |
| Resilience | Exponential backoff, retry with repair context, structured error codes |

### Data Model

```
User ──────────────── Conversation ──────────────── Message
 │                          │                           │
 id (cuid)                 id (cuid)               role: USER | ASSISTANT | SYSTEM
 email (unique)            title (auto-generated)  content (structured JSON payload)
 hashedPassword (bcrypt)   userId (FK)             conversationId (FK)
 createdAt / updatedAt     createdAt / updatedAt   createdAt
```

---

## Key Engineering Decisions

### LLM Called in Two Places Only
Gemini is invoked exactly twice per request: SQL generation (Layer 3b) and response narration (Layer 6). Every other step — intent classification, entity linking, time parsing, trend detection, outlier scoring, chart selection — runs as deterministic Python. This keeps the system fast, cheap, and auditable.

### Semantic Metric Layer
Business semantics are not embedded in prompts — they live in a typed metric registry. `revenue` is always `SUM(Amount) WHERE Type = 'Credit'`. `unique_customers` is always `COUNT(DISTINCT AccountID)`. This prevents an entire class of prompt-injection and metric-definition errors, regardless of how the user phrases the question.

### Agentic SQL Loop with Repair
The SQL generator doesn't just generate once. If the output fails schema validation, the agent re-runs with the error message included as context — up to two repair attempts before surfacing a structured error to the user. No silent failures.

### Two-Level Caching Strategy
- **Semantic cache** (Layer 0): questions within cosine distance 0.92 of a prior answer return instantly — no pipeline, no LLM, no DB query
- **Result cache**: identical SQL strings skip execution entirely — sub-millisecond repeat queries

### Follow-up Conversation Awareness
Each session stores the last 5 `StructuredRequest` objects. *"Break that down by region"* correctly inherits the metric and time window from the previous turn — without the user needing to restate context.

### Guard Rails on Output
The guard rail agent compares every number in the Gemini narrative against the `StructuredInsights` payload. Any figure that didn't come from the data is removed before the response reaches the user. The LLM is not trusted to produce numbers — only to narrate them.

---

## Project Structure

```
MetricLens/
├── frontend/                              Next.js 16 application
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/                   Sign-in and sign-up pages
│   │   │   ├── (pages)/chat/             Chat UI, server actions, message state
│   │   │   └── api/
│   │   │       ├── auth/[...nextauth]/   NextAuth route handler
│   │   │       ├── chat/                 Bridge route → FastAPI backend
│   │   │       ├── conversations/        Conversation CRUD
│   │   │       ├── register/             User registration + password hashing
│   │   │       └── summary/              Weekly executive summary proxy
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx         Chat input, pending state, answer rendering
│   │   │   ├── AnswerCard.tsx            Structured response card with expandable sections
│   │   │   ├── Timeline.tsx              Product story / explainability visuals
│   │   │   └── ui/                       wavy-background, glowing-effect, hero-highlight,
│   │   │                                 draggable-card, sidebar, navbar, badge, button
│   │   └── lib/                          auth-options, prisma singleton, utils
│   └── prisma/schema.prisma              User · Conversation · Message schema
│
└── backend/                              FastAPI Python service
    ├── main.py                           API orchestrator — all routes + pipeline wiring
    ├── ingest.py                         CSV ingestion → PostgreSQL
    ├── precompute.py                     Pre-aggregation for common rollups
    ├── agents/
    │   ├── sql_generator.py              Gemini SQL generation with context injection
    │   ├── sql_validator.py              Schema-aware SQL safety validation
    │   ├── rag_retriever.py              Semantic retrieval → RAG context builder
    │   ├── response_generator.py         Gemini narrative generation from StructuredInsights
    │   ├── guard_rail.py                 Hallucination filter on final output
    │   └── reasoning_chain.py            Intent-specific analytical post-processing
    ├── layers/
    │   ├── agent_engine.py               Agentic loop: generate → validate → execute → repair
    │   ├── semantic_cache.py             Cosine-similarity cache (threshold 0.92)
    │   ├── vector_store.py               Semantic retrieval for schema/metric/example docs
    │   ├── conversation.py               Session store — 30-min TTL, last-5-turns context
    │   ├── query_understanding/          Intent classifier · entity linker · time parser
    │   ├── semantic_layer/               Metric registry · dimension hierarchy · business rules
    │   ├── query_planner/                Route decider · execution plan builder · result merger
    │   ├── execution/                    PostgreSQL engine · result cache
    │   └── insight_engine/               Trend · outlier · contribution · chart recommender
    ├── utils/
    │   ├── gemini_client.py              Gemini wrapper — backoff + rate limiting
    │   ├── gemini_embedder.py            Embedding helper for vector workflows
    │   ├── errors.py                     Typed error codes with recoverable flag
    │   └── logger.py                     Per-layer trace + timing logger
    └── data/
        ├── transactions.csv              Source transaction data
        ├── schema_docs.txt               Column documentation for RAG
        ├── metrics.json                  Metric definitions for RAG
        └── sample_queries.json           Few-shot Q&A examples for retrieval
```

---

## API Reference

### `POST /api/query` — Main Analytics Pipeline

**Request**
```json
{
  "question":   "Which channel had the highest revenue drop last week?",
  "session_id": "optional-uuid-for-conversation-continuity"
}
```

**Response — analytics answer**
```json
{
  "answer":     "Online Banking saw the sharpest drop at -18.3% WoW, driven primarily by...",
  "chart_spec": { "type": "bar", "x": "channel", "y": "revenue_delta_pct" },
  "confidence": 0.94,
  "sources":    ["transactions"],
  "trace":      { "query_understanding_ms": 14, "execution_ms": 43, "total_ms": 310 },
  "from_cache": false,
  "session_id": "abc-123",
  "request_id": "uuid"
}
```

**Response — clarification needed**
```json
{
  "clarify":    true,
  "question":   "Did you mean revenue by channel or by product category?",
  "session_id": "abc-123"
}
```

### `GET /api/summary` — Weekly Executive Summary
Runs the full pipeline against a pre-defined summary question and returns a narrative digest.

### `GET /api/health` — System Status
Returns DB row count, vector store document counts, and cache entry count.

### `GET /api/metrics` — Metric Dictionary
Returns the full metric registry with definitions, SQL fragments, and business rules.

### `DELETE /api/cache` — Cache Reset
Clears semantic and result caches — useful for demo resets.

---

## Example Questions MetricLens Can Answer

| Question | Pipeline Route |
|---|---|
| "What was total revenue last week?" | analytics → SQL → trend detection |
| "Which region had the most transactions in June?" | analytics → SQL → contribution analysis |
| "Why did mobile payments drop on Tuesday?" | analytics → driver analysis → outlier flagging |
| "Compare this month vs last month" | analytics → comparison plan → significance test |
| "Break that down by product type" | follow-up → inherits prior context → SQL |
| "What does chargeback rate mean?" | RAG → vector retrieval → Gemini |
| "Give me a weekly executive summary" | summary endpoint → full pipeline |

---

## Running Locally

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Set: GEMINI_API_KEY, DATABASE_URL (Neon PostgreSQL connection string)

# Ingest data
python ingest.py --csv data/transactions.csv

# Start API server
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install

# Configure environment
cp .env.example .env.local
# Set: DATABASE_URL, NEXTAUTH_SECRET, FASTAPI_URL=http://localhost:8000

# Run database migrations
npx prisma migrate dev

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Guard Rails & Safety

| Concern | Mitigation |
|---|---|
| Hallucinated numbers | Guard rail agent strips any figure not present in `StructuredInsights` before response reaches user |
| SQL injection | All SQL generated against a fixed, validated schema and executed read-only |
| Metric misinterpretation | Business rules in Semantic Layer enforce canonical definitions regardless of phrasing |
| Fraud data leakage | Flagged accounts excluded from clean metrics unless question explicitly targets fraud |
| Session data isolation | Conversation history scoped strictly by session ID, auto-expires at 30 minutes |
| Unauthorised access | Every API route validates a live NextAuth session before any DB or backend call |

---

## Why MetricLens Is Different

Most BI tools answer *what*. MetricLens answers *why*.

The combination of a semantic metric layer (enforced definitions), an agentic SQL loop (self-correcting execution), a statistical insight engine (deterministic, LLM-free), and conversational follow-up awareness makes MetricLens more than a chatbot — it is a validated analytical workflow with a conversational interface.

---

