"""
Run AFTER ingest.py to build pre-aggregated Parquet files.
These are used by the Query Planner to skip full table scans.

Usage:
    cd backend
    python precompute.py
"""
import os

import duckdb

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH  = os.path.join(DATA_DIR, "analytics.db")
AGG_DIR  = os.path.join(DATA_DIR, "aggregations")


def build():
    os.makedirs(AGG_DIR, exist_ok=True)
    conn = duckdb.connect(DB_PATH)

    print("[Precompute] Building daily_by_channel.parquet ...")
    conn.execute(f"""
        COPY (
            SELECT
                CAST(TransactionDate AS DATE)      AS date,
                Channel,
                COUNT(*)                           AS transaction_volume,
                SUM(TransactionAmount)             AS revenue,
                AVG(TransactionAmount)             AS avg_transaction
            FROM transactions
            GROUP BY date, Channel
            ORDER BY date, Channel
        ) TO '{AGG_DIR}/daily_by_channel.parquet' (FORMAT PARQUET)
    """)

    print("[Precompute] Building weekly_by_location.parquet ...")
    conn.execute(f"""
        COPY (
            SELECT
                YEAR(CAST(TransactionDate AS DATE))                AS year,
                WEEK(CAST(TransactionDate AS DATE))                AS week,
                Location,
                COUNT(*)                                           AS transaction_volume,
                SUM(TransactionAmount)                             AS revenue,
                AVG(TransactionAmount)                             AS avg_transaction
            FROM transactions
            GROUP BY year, week, Location
            ORDER BY year, week, Location
        ) TO '{AGG_DIR}/weekly_by_location.parquet' (FORMAT PARQUET)
    """)

    print("[Precompute] Building monthly_summary.parquet ...")
    conn.execute(f"""
        COPY (
            SELECT
                YEAR(CAST(TransactionDate AS DATE))   AS year,
                MONTH(CAST(TransactionDate AS DATE))  AS month,
                Channel,
                TransactionType,
                COUNT(*)                              AS transaction_volume,
                SUM(TransactionAmount)                AS revenue,
                AVG(TransactionAmount)                AS avg_transaction,
                COUNT(DISTINCT AccountID)             AS unique_accounts
            FROM transactions
            GROUP BY year, month, Channel, TransactionType
            ORDER BY year, month
        ) TO '{AGG_DIR}/monthly_summary.parquet' (FORMAT PARQUET)
    """)

    conn.close()
    print(f"[Precompute] Done. 3 files written to {AGG_DIR}/")


if __name__ == "__main__":
    build()
