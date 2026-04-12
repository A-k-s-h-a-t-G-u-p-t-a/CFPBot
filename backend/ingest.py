"""
One-time ingestion script for the e-commerce orders CSV into Neon PostgreSQL + pgvector.

Usage:
    cd backend
    python ingest.py                          # uses data/orders.csv by default
    python ingest.py --csv path/to/file.csv   # custom path

Steps:
  1. Creates the orders table and pgvector embeddings table in Neon
  2. Bulk-loads the CSV into the orders table
  3. Embeds schema/metric/query documents and stores them in embeddings table
"""
import argparse
import json
import os
import sys

import pandas as pd
import psycopg
import psycopg.rows
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    sys.exit("ERROR: DATABASE_URL not set in backend/.env")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

DDL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS orders (
    order_id           TEXT,
    date               DATE,
    status             TEXT,
    fulfilment         TEXT,
    ship_service_level TEXT,
    style              TEXT,
    sku                TEXT,
    category           TEXT,
    size               TEXT,
    asin               TEXT,
    courier_status     TEXT,
    qty                INTEGER,
    amount             NUMERIC(12,2),
    ship_city          TEXT,
    ship_state         TEXT,
    is_b2b             BOOLEAN
);

CREATE TABLE IF NOT EXISTS embeddings (
    id         SERIAL PRIMARY KEY,
    collection TEXT NOT NULL,
    document   TEXT NOT NULL,
    embedding  vector(3072)
);

CREATE INDEX IF NOT EXISTS embeddings_collection_idx ON embeddings(collection);
"""


# ---------------------------------------------------------------------------
# Step 1: Create schema
# ---------------------------------------------------------------------------

def create_schema(conn: psycopg.Connection) -> None:
    print("\n[schema] Running DDL...")
    with conn.cursor() as cur:
        cur.execute(DDL)
    conn.commit()
    print("[schema] Done.")


# ---------------------------------------------------------------------------
# Step 2: Load CSV → orders table
# ---------------------------------------------------------------------------

COLUMN_MAP = {
    "Order ID":           "order_id",
    "Date":               "date",
    "Status":             "status",
    "Fulfilment":         "fulfilment",
    "ship-service-level": "ship_service_level",
    "Style":              "style",
    "SKU":                "sku",
    "Category":           "category",
    "Size":               "size",
    "ASIN":               "asin",
    "Courier Status":     "courier_status",
    "Qty":                "qty",
    "Amount":             "amount",
    "ship-city":          "ship_city",
    "ship-state":         "ship_state",
    "B2B":                "is_b2b",
}


def load_csv(conn: psycopg.Connection, csv_path: str) -> None:
    print(f"\n[orders] Loading CSV from {csv_path} ...")
    if not os.path.exists(csv_path):
        sys.exit(f"ERROR: CSV not found at {csv_path}")

    df = pd.read_csv(csv_path, low_memory=False)

    # Rename columns
    df = df.rename(columns=COLUMN_MAP)

    # Keep only known columns
    known = list(COLUMN_MAP.values())
    df = df[[c for c in known if c in df.columns]]

    # Clean data
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    if "qty" in df.columns:
        df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0).astype(int)
    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    if "is_b2b" in df.columns:
        df["is_b2b"] = df["is_b2b"].astype(str).str.lower().isin(["true", "1", "yes"])

    df = df.dropna(subset=["order_id"])

    # Truncate existing data and reload
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE orders")
    cols = list(df.columns)
    placeholders = ", ".join(["%s"] * len(cols))
    col_names    = ", ".join(cols)
    insert_sql   = f"INSERT INTO orders ({col_names}) VALUES ({placeholders})"

    rows = [tuple(None if pd.isna(v) else v for v in row) for row in df.itertuples(index=False, name=None)]
    with conn.cursor() as cur:
        cur.executemany(insert_sql, rows)
    conn.commit()
    print(f"[orders] Inserted {len(rows):,} rows.")


# ---------------------------------------------------------------------------
# Step 3: Embed documents → embeddings table
# ---------------------------------------------------------------------------

# Inline documents describing the schema and metrics for vector search
SCHEMA_DOCS = [
    "order_id: Unique identifier for each order",
    "date: The date the order was placed (DATE type, format YYYY-MM-DD)",
    "status: Order status — values include Shipped, Cancelled, Pending, Delivered",
    "fulfilment: Fulfilled by Amazon (FBA) or Merchant",
    "ship_service_level: Shipping tier — Expedited or Standard",
    "style: Visual style or design code of the product",
    "sku: Stock Keeping Unit identifier",
    "category: Product category (e.g. T-shirt, Shirt, Blazzer)",
    "size: Product size (S, M, L, XL, XXL, etc.)",
    "asin: Amazon Standard Identification Number",
    "courier_status: Status from the courier — Shipped, Unshipped, Cancelled",
    "qty: Quantity of items ordered (integer)",
    "amount: Order value in currency (numeric, can be NULL for cancelled orders)",
    "ship_city: City the order is shipping to",
    "ship_state: Indian state the order is shipping to",
    "is_b2b: TRUE if this is a Business-to-Business order, FALSE for consumer",
]

METRIC_DOCS = [
    "revenue: Total order value. Use SUM(amount) from orders. Only count non-cancelled orders for accurate revenue.",
    "order_volume: Total number of orders. Use COUNT(*) or COUNT(order_id) from orders.",
    "avg_order_value: Average value per order. Use AVG(amount) from orders.",
    "cancellation_rate: Percentage of orders with status = 'Cancelled'. Use COUNT(*) FILTER (WHERE status = 'Cancelled') / COUNT(*).",
    "b2b_share: Percentage of orders that are B2B. Use COUNT(*) FILTER (WHERE is_b2b = true) / COUNT(*).",
    "units_sold: Total quantity. Use SUM(qty) from orders.",
    "top_category: Category with highest order volume or revenue. Use GROUP BY category ORDER BY metric DESC.",
    "top_state: State with highest order volume. Use GROUP BY ship_state ORDER BY COUNT(*) DESC.",
    "fulfillment_mix: Split of Merchant vs Amazon orders. Use GROUP BY fulfilment.",
]

SAMPLE_QUERIES = [
    {
        "question": "What is total revenue this month?",
        "sql": "SELECT SUM(amount) AS total_revenue FROM orders WHERE date >= date_trunc('month', CURRENT_DATE)"
    },
    {
        "question": "Show revenue by category",
        "sql": "SELECT category, SUM(amount) AS revenue FROM orders GROUP BY category ORDER BY revenue DESC"
    },
    {
        "question": "Compare order volume this week vs last week",
        "sql": "SELECT CASE WHEN date >= CURRENT_DATE - 7 THEN 'This Week' ELSE 'Last Week' END AS period, COUNT(*) AS orders FROM orders WHERE date >= CURRENT_DATE - 14 GROUP BY 1"
    },
    {
        "question": "What is the cancellation rate by state?",
        "sql": "SELECT ship_state, ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'Cancelled') / COUNT(*), 2) AS cancel_rate FROM orders GROUP BY ship_state ORDER BY cancel_rate DESC LIMIT 10"
    },
    {
        "question": "Which categories have the highest average order value?",
        "sql": "SELECT category, ROUND(AVG(amount)::numeric, 2) AS avg_value FROM orders WHERE amount IS NOT NULL GROUP BY category ORDER BY avg_value DESC LIMIT 10"
    },
    {
        "question": "Revenue breakdown by fulfilment channel",
        "sql": "SELECT fulfilment, SUM(amount) AS revenue, ROUND(100.0 * SUM(amount) / SUM(SUM(amount)) OVER (), 2) AS share_pct FROM orders WHERE amount IS NOT NULL GROUP BY fulfilment ORDER BY revenue DESC"
    },
    {
        "question": "Top 5 states by order volume",
        "sql": "SELECT ship_state, COUNT(*) AS order_count FROM orders GROUP BY ship_state ORDER BY order_count DESC LIMIT 5"
    },
    {
        "question": "What is the B2B share of total orders?",
        "sql": "SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE is_b2b) / COUNT(*), 2) AS b2b_pct FROM orders"
    },
]


def embed_documents(conn: psycopg.Connection) -> None:
    from utils.gemini_embedder import embed_text

    print("\n[embeddings] Embedding documents into pgvector ...")

    # Clear existing
    with conn.cursor() as cur:
        cur.execute("DELETE FROM embeddings")
    conn.commit()

    def upsert_collection(collection: str, docs: list[str]) -> None:
        print(f"  [{collection}] embedding {len(docs)} documents...")
        with conn.cursor() as cur:
            for doc in docs:
                try:
                    vec = embed_text(doc)
                    vec_str = "[" + ",".join(str(x) for x in vec) + "]"
                    cur.execute(
                        "INSERT INTO embeddings (collection, document, embedding) VALUES (%s, %s, %s::vector)",
                        (collection, doc, vec_str),
                    )
                except Exception as e:
                    print(f"    WARNING: failed to embed doc — {e}")
        conn.commit()
        print(f"  [{collection}] done.")

    upsert_collection("schema_docs", SCHEMA_DOCS)
    upsert_collection("metric_docs", METRIC_DOCS)
    upsert_collection("sample_queries", [f"Q: {e['question']}\nSQL: {e['sql']}" for e in SAMPLE_QUERIES])

    print("[embeddings] Done.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest orders CSV into Neon PostgreSQL + pgvector")
    parser.add_argument("--csv", default=os.path.join(DATA_DIR, "orders.csv"), help="Path to the CSV file")
    parser.add_argument("--skip-embed", action="store_true", help="Skip embedding documents (faster for re-runs)")
    args = parser.parse_args()

    print(f"Connecting to Neon: {DATABASE_URL[:40]}...")
    with psycopg.connect(DATABASE_URL) as conn:
        create_schema(conn)
        load_csv(conn, args.csv)
        if not args.skip_embed:
            embed_documents(conn)

    print("\n✓ Ingestion complete. You can now start the server:")
    print("  uvicorn main:app --reload --port 8000")
