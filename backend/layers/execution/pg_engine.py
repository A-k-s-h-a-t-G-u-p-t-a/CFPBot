"""
Neon PostgreSQL execution engine.
Replaces duckdb_engine.py — all analytics queries now run against Neon Postgres.
"""
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

_DATABASE_URL = os.getenv("DATABASE_URL", "")


def _connect() -> psycopg.Connection:
    return psycopg.connect(_DATABASE_URL)


def execute_analytics_query(sql: str) -> list[dict]:
    """
    Run a read-only SELECT against Neon Postgres.
    Caps at 1000 rows to prevent runaway queries.
    """
    if "LIMIT" not in sql.upper():
        sql = sql.rstrip(";") + " LIMIT 1000"
    with _connect() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(sql)
            return cur.fetchall()


def execute_safe_query(sql: str) -> list[dict]:
    """Alias used by legacy imports."""
    return execute_analytics_query(sql)


def row_count() -> int:
    """Returns total rows in the orders table — used for startup health check."""
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM orders")
                result = cur.fetchone()
                return result[0] if result else 0
    except Exception as e:
        print(f"[pg_engine] row_count failed: {e}")
        return 0
