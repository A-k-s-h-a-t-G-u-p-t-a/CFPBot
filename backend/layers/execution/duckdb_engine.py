import os

import duckdb
from dotenv import load_dotenv

load_dotenv()

_DB_PATH  = os.path.join(os.path.dirname(__file__), "../../data/analytics.db")
_CSV_PATH = os.path.join(os.path.dirname(__file__), "../../data/transactions.csv")


def _init_connection() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(_DB_PATH)
    tables = conn.execute("SHOW TABLES").fetchdf()["name"].tolist()
    if "transactions" not in tables:
        if os.path.exists(_CSV_PATH):
            conn.execute(
                f"CREATE TABLE transactions AS SELECT * FROM read_csv_auto('{_CSV_PATH}')"
            )
            n = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
            print(f"[DuckDB] Loaded {n:,} rows from CSV")
        else:
            print(f"[DuckDB] WARNING: {_CSV_PATH} not found — run ingest.py first")
    return conn


_conn = _init_connection()


def execute_analytics_query(sql: str) -> list[dict]:
    """Runs an analytics query. Falls back to PostgreSQL on error."""
    try:
        if "LIMIT" not in sql.upper():
            sql = sql.rstrip(";") + " LIMIT 1000"
        return _conn.execute(sql).fetchdf().to_dict(orient="records")
    except Exception as e:
        print(f"[DuckDB] Error: {e} — falling back to PostgreSQL")
        try:
            from layers.execution.pg_engine import execute_safe_query
            return execute_safe_query(sql)
        except Exception as pg_err:
            raise RuntimeError(f"Both DuckDB and PostgreSQL failed: {pg_err}") from e


def query_pre_agg(file_path: str) -> list[dict]:
    """Directly queries a pre-aggregated Parquet file."""
    return _conn.execute(f"SELECT * FROM read_parquet('{file_path}')").fetchdf().to_dict(orient="records")


def get_schema_string() -> str:
    try:
        return _conn.execute("DESCRIBE transactions").fetchdf().to_string(index=False)
    except Exception:
        return "Schema unavailable — run ingest.py first"


def row_count() -> int:
    try:
        return _conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    except Exception:
        return 0
