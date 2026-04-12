"""
Vector store backed by Neon pgvector.
Replaces chromadb + fastembed with Gemini text-embedding-004 + pgvector cosine search.

Table schema (created by ingest.py):
  embeddings(id SERIAL, collection TEXT, document TEXT, embedding vector(768))
"""
import os

import psycopg
import psycopg.rows
from dotenv import load_dotenv

from utils.gemini_embedder import embed_text

load_dotenv()

_DATABASE_URL = os.getenv("DATABASE_URL", "")


def _connect() -> psycopg.Connection:
    return psycopg.connect(_DATABASE_URL)


def _query_collection(collection: str, question: str, top_k: int) -> str:
    try:
        embedding = embed_text(question)
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        sql = """
            SELECT document
            FROM embeddings
            WHERE collection = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (collection, embedding_str, top_k))
                rows = cur.fetchall()
                return "\n".join(r[0] for r in rows)
    except Exception as e:
        print(f"[vector_store] collection={collection} error: {e}")
        return ""


def get_relevant_schema(question: str, top_k: int = 3) -> str:
    return _query_collection("schema_docs", question, top_k)


def get_relevant_metric_docs(question: str, top_k: int = 3) -> str:
    return _query_collection("metric_docs", question, top_k)


def get_relevant_examples(question: str, top_k: int = 2) -> str:
    return _query_collection("sample_queries", question, top_k)


def get_collection_count(name: str) -> int:
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM embeddings WHERE collection = %s", (name,))
                result = cur.fetchone()
                return result[0] if result else 0
    except Exception:
        return 0
