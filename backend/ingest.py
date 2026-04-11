"""
Run this ONCE before starting the server to load data into DuckDB and ChromaDB.

Usage:
    cd backend
    python ingest.py
"""
import json
import os

import chromadb
import duckdb
from fastembed import TextEmbedding

DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")
DB_PATH    = os.path.join(DATA_DIR, "analytics.db")
CSV_PATH   = os.path.join(DATA_DIR, "transactions.csv")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma_db")


def ingest_duckdb():
    print("\n[DuckDB] Loading transactions CSV...")
    if not os.path.exists(CSV_PATH):
        print(f"  ERROR: {CSV_PATH} not found.")
        print("  Download the dataset from Kaggle and place it at backend/data/transactions.csv")
        return False

    conn = duckdb.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS transactions")
    conn.execute(f"CREATE TABLE transactions AS SELECT * FROM read_csv_auto('{CSV_PATH}')")
    n = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    print(f"  Loaded {n:,} rows")
    print(f"  Schema:\n{conn.execute('DESCRIBE transactions').fetchdf().to_string(index=False)}")
    conn.close()
    return True


def ingest_chromadb():
    print("\n[ChromaDB] Embedding documents...")
    model  = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    existing = {c.name for c in client.list_collections()}

    def upsert(name: str, docs: list[str]):
        if name in existing:
            client.delete_collection(name)
        col  = client.create_collection(name)
        embs = [list(e) for e in model.embed(docs)]
        col.add(documents=docs, embeddings=embs, ids=[f"{name}_{i}" for i in range(len(docs))])
        print(f"  {name}: {len(docs)} documents")

    # schema_docs
    schema_path = os.path.join(DATA_DIR, "schema_docs.txt")
    if os.path.exists(schema_path):
        with open(schema_path) as f:
            lines = [l.strip() for l in f if l.strip()]
        upsert("schema_docs", lines)

    # metric_docs
    metrics_path = os.path.join(DATA_DIR, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            metrics = json.load(f)
        docs = [f"{k}: {v['description']} (unit: {v.get('unit', 'n/a')})" for k, v in metrics.items()]
        upsert("metric_docs", docs)

    # sample_queries
    examples_path = os.path.join(DATA_DIR, "sample_queries.json")
    if os.path.exists(examples_path):
        with open(examples_path) as f:
            examples = json.load(f)
        docs = [f"Q: {e['question']}\nSQL: {e['sql']}" for e in examples]
        upsert("sample_queries", docs)

    print("[ChromaDB] Done.")


if __name__ == "__main__":
    os.makedirs(DATA_DIR,   exist_ok=True)
    os.makedirs(CHROMA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "aggregations"), exist_ok=True)

    ok = ingest_duckdb()
    ingest_chromadb()

    if ok:
        print("\n  Run precompute.py next to build Parquet pre-aggregations.")
        print("  Then start the server:  uvicorn main:app --reload --port 8000")
