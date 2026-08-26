"""Ingest and validate the local e-commerce lakehouse.

Python owns ingestion and the Silver layer. dbt owns the analytical Gold
models so that business logic is documented, testable and easy to extend.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import subprocess

import duckdb


SOURCE_TABLES = {
    "customers": ["customer_id", "full_name", "email", "country", "registered_date"],
    "products": ["product_id", "product_name", "category", "unit_price"],
    "orders": ["order_id", "customer_id", "order_date", "order_status", "shipping_country"],
    "order_items": ["order_item_id", "order_id", "product_id", "quantity", "unit_price"],
    "payments": ["payment_id", "order_id", "payment_method", "payment_status", "amount"],
}


def _sql_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace("'", "''")


def _copy_parquet(connection: duckdb.DuckDBPyConnection, table: str, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    connection.execute(
        f"COPY {table} TO '{_sql_path(directory / (table + '.parquet'))}' "
        "(FORMAT PARQUET, OVERWRITE_OR_IGNORE TRUE)"
    )


def _count(connection: duckdb.DuckDBPyConnection, table: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def run_pipeline(data_dir: Path, incremental: bool = False) -> dict:
    """Run ingestion, quality checks and dbt models.

    A full refresh is the default to keep local runs deterministic. Incremental
    runs append only order IDs not already present in the Gold fact table.
    """
    source_dir = data_dir / "source"
    bronze_dir = data_dir / "bronze"
    silver_dir = data_dir / "silver"
    gold_dir = data_dir / "gold"
    warehouse_dir = data_dir / "warehouse"
    warehouse_dir.mkdir(parents=True, exist_ok=True)
    database_path = warehouse_dir / "ecommerce.duckdb"

    missing = [name for name in SOURCE_TABLES if not (source_dir / f"{name}.csv").exists()]
    if missing:
        raise FileNotFoundError(f"Missing source files: {', '.join(missing)}")

    connection = duckdb.connect(str(database_path))
    try:
        raw_counts: dict[str, int] = {}
        for table in SOURCE_TABLES:
            source_path = _sql_path(source_dir / f"{table}.csv")
            connection.execute(
                f"CREATE OR REPLACE TABLE bronze_{table} AS "
                f"SELECT * FROM read_csv_auto('{source_path}', header = true)"
            )
            _copy_parquet(connection, f"bronze_{table}", bronze_dir)
            raw_counts[table] = _count(connection, f"bronze_{table}")

        connection.execute(
            """
            CREATE OR REPLACE TABLE silver_customers AS
            SELECT CAST(customer_id AS INTEGER) AS customer_id,
                   TRIM(full_name) AS full_name,
                   LOWER(TRIM(email)) AS email,
                   UPPER(TRIM(country)) AS country,
                   CAST(registered_date AS DATE) AS registered_date
            FROM bronze_customers
            WHERE customer_id IS NOT NULL AND email IS NOT NULL
            """
        )
        connection.execute(
            """
            CREATE OR REPLACE TABLE silver_products AS
            SELECT CAST(product_id AS INTEGER) AS product_id,
                   TRIM(product_name) AS product_name,
                   LOWER(TRIM(category)) AS category,
                   CAST(unit_price AS DECIMAL(12, 2)) AS unit_price
            FROM bronze_products
            WHERE product_id IS NOT NULL AND unit_price >= 0
            """
        )
        connection.execute(
            """
            CREATE OR REPLACE TABLE silver_orders AS
            SELECT CAST(order_id AS INTEGER) AS order_id,
                   CAST(customer_id AS INTEGER) AS customer_id,
                   CAST(order_date AS DATE) AS order_date,
                   LOWER(TRIM(order_status)) AS order_status,
                   UPPER(TRIM(shipping_country)) AS shipping_country
            FROM bronze_orders
            WHERE order_id IS NOT NULL
              AND customer_id IS NOT NULL
              AND order_date IS NOT NULL
              AND LOWER(TRIM(order_status)) IN ('delivered', 'shipped', 'cancelled')
            """
        )
        connection.execute(
            """
            CREATE OR REPLACE TABLE silver_order_items AS
            SELECT TRIM(order_item_id) AS order_item_id,
                   CAST(order_id AS INTEGER) AS order_id,
                   CAST(product_id AS INTEGER) AS product_id,
                   CAST(quantity AS INTEGER) AS quantity,
                   CAST(unit_price AS DECIMAL(12, 2)) AS unit_price
            FROM bronze_order_items
            WHERE order_item_id IS NOT NULL
              AND order_id IS NOT NULL
              AND product_id IS NOT NULL
              AND quantity > 0
              AND unit_price >= 0
            """
        )
        connection.execute(
            """
            CREATE OR REPLACE TABLE silver_payments AS
            SELECT TRIM(payment_id) AS payment_id,
                   CAST(order_id AS INTEGER) AS order_id,
                   LOWER(TRIM(payment_method)) AS payment_method,
                   LOWER(TRIM(payment_status)) AS payment_status,
                   CAST(amount AS DECIMAL(12, 2)) AS amount
            FROM bronze_payments
            WHERE payment_id IS NOT NULL AND order_id IS NOT NULL AND amount >= 0
            """
        )
        silver_tables = [
            "silver_customers",
            "silver_products",
            "silver_orders",
            "silver_order_items",
            "silver_payments",
        ]
        for table in silver_tables:
            _copy_parquet(connection, table, silver_dir)

        quality_checks = {
            "duplicate_customer_ids": _count_query(
                connection,
                "SELECT COUNT(*) FROM (SELECT customer_id FROM silver_customers GROUP BY customer_id HAVING COUNT(*) > 1)",
            ),
            "duplicate_product_ids": _count_query(
                connection,
                "SELECT COUNT(*) FROM (SELECT product_id FROM silver_products GROUP BY product_id HAVING COUNT(*) > 1)",
            ),
            "orphan_order_customers": _count_query(
                connection,
                """SELECT COUNT(*) FROM silver_orders o
                   WHERE NOT EXISTS (SELECT 1 FROM silver_customers c WHERE c.customer_id = o.customer_id)""",
            ),
            "orphan_order_items": _count_query(
                connection,
                """SELECT COUNT(*) FROM silver_order_items i
                   WHERE NOT EXISTS (SELECT 1 FROM silver_orders o WHERE o.order_id = i.order_id)""",
            ),
            "orphan_products": _count_query(
                connection,
                """SELECT COUNT(*) FROM silver_order_items i
                   WHERE NOT EXISTS (SELECT 1 FROM silver_products p WHERE p.product_id = i.product_id)""",
            ),
        }
        if any(quality_checks.values()):
            raise ValueError(f"Data quality checks failed: {quality_checks}")

        # Close before dbt opens the same DuckDB file to avoid file locks.
    finally:
        connection.close()

    _run_dbt(data_dir, database_path, full_refresh=not incremental)

    connection = duckdb.connect(str(database_path), read_only=True)
    try:
        gold_tables = [
            "gold_dim_customer",
            "gold_dim_product",
            "gold_fact_order",
            "gold_daily_sales",
            "gold_category_sales",
            "gold_customer_sales",
            "gold_product_sales",
        ]
        for table in gold_tables:
            _copy_parquet(connection, table, gold_dir)

        completed_orders = _count_query(
            connection, "SELECT COUNT(*) FROM gold_fact_order WHERE is_completed"
        )
        revenue = float(
            connection.execute(
                "SELECT COALESCE(SUM(order_total), 0) FROM gold_fact_order WHERE is_completed"
            ).fetchone()[0]
        )
        summary = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "database": str(database_path),
            "pipeline_mode": "incremental" if incremental else "full_refresh",
            "bronze_rows": raw_counts,
            "silver_rows": {table.removeprefix("silver_"): _count(connection, table) for table in silver_tables},
            "gold_rows": {table.removeprefix("gold_"): _count(connection, table) for table in gold_tables},
            "quality_checks": quality_checks,
            "completed_orders": completed_orders,
            "completed_revenue": round(revenue, 2),
        }
        (data_dir / "pipeline_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
        return summary
    finally:
        connection.close()


def _run_dbt(data_dir: Path, database_path: Path, full_refresh: bool) -> None:
    """Build Gold models and their schema tests with dbt-duckdb."""
    project_dir = Path(
        os.environ.get("ECOMMERCE_DBT_PROJECT_DIR", str(Path.cwd() / "dbt"))
    ).resolve()
    if not project_dir.exists():
        raise FileNotFoundError(f"dbt project not found: {project_dir}")

    environment = os.environ.copy()
    environment["ECOMMERCE_DB_PATH"] = str(database_path.resolve())
    command = [
        sys.executable,
        "-m",
        "dbt.cli.main",
        "build",
        "--project-dir",
        str(project_dir),
        "--profiles-dir",
        str(project_dir),
        "--target",
        "local",
    ]
    if full_refresh:
        command.append("--full-refresh")

    result = subprocess.run(
        command,
        cwd=data_dir.parent,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        raise RuntimeError(f"dbt build failed:\n{output}")


def _count_query(connection: duckdb.DuckDBPyConnection, query: str) -> int:
    return int(connection.execute(query).fetchone()[0])
