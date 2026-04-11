import os

import psycopg2
import psycopg2.pool
from dotenv import load_dotenv

load_dotenv()

_pool: psycopg2.pool.SimpleConnectionPool | None = None


def _get_pool() -> psycopg2.pool.SimpleConnectionPool | None:
    global _pool
    if _pool is None:
        db_url = os.getenv("DB_URL")
        if db_url:
            try:
                _pool = psycopg2.pool.SimpleConnectionPool(1, 5, db_url)
            except Exception as e:
                print(f"[PostgreSQL] Connection failed: {e}")
    return _pool


def execute_safe_query(sql: str) -> list[dict]:
    pool = _get_pool()
    if not pool:
        return []
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchmany(1000)]
    except Exception as e:
        raise RuntimeError(f"PostgreSQL query failed: {e}") from e
    finally:
        pool.putconn(conn)
