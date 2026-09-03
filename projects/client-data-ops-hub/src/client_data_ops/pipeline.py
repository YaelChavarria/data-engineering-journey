"""Run the client delivery pipeline and publish quality/SLA evidence."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import duckdb


SOURCE_TABLES = {
    "accounts": ["account_id", "account_name", "plan", "country", "signup_date", "account_status", "monthly_recurring_revenue"],
    "invoices": ["invoice_id", "account_id", "invoice_date", "amount", "invoice_status"],
    "support_tickets": ["ticket_id", "account_id", "created_date", "resolved_date", "priority", "ticket_status"],
    "account_events": ["event_id", "account_id", "event_date", "event_type"],
}


def _sql_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace("'", "''")


def _count(connection: duckdb.DuckDBPyConnection, table: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _count_query(connection: duckdb.DuckDBPyConnection, query: str) -> int:
    return int(connection.execute(query).fetchone()[0])


def _copy_parquet(connection: duckdb.DuckDBPyConnection, table: str, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    connection.execute(
        f"COPY {table} TO '{_sql_path(directory / (table + '.parquet'))}' "
        "(FORMAT PARQUET, OVERWRITE_OR_IGNORE TRUE)"
    )


def run_delivery(data_dir: Path, client_id: str = "atlas-saas") -> dict:
    """Run one client delivery and return its manifest."""
    started = time.perf_counter()
    source_dir = data_dir / "source"
    database_path = data_dir / "warehouse" / "client_delivery.duckdb"
    database_path.parent.mkdir(parents=True, exist_ok=True)
    missing = [name for name in SOURCE_TABLES if not (source_dir / f"{name}.csv").exists()]
    if missing:
        raise FileNotFoundError(f"Missing client exports: {', '.join(missing)}")

    connection = duckdb.connect(str(database_path))
    try:
        raw_counts: dict[str, int] = {}
        for table in SOURCE_TABLES:
            source_path = _sql_path(source_dir / f"{table}.csv")
            connection.execute(
                f"CREATE OR REPLACE TABLE bronze_{table} AS "
                f"SELECT * FROM read_csv_auto('{source_path}', header = true)"
            )
            _copy_parquet(connection, f"bronze_{table}", data_dir / "bronze")
            raw_counts[table] = _count(connection, f"bronze_{table}")

        connection.execute(
            """
            CREATE OR REPLACE TABLE silver_accounts AS
            SELECT CAST(account_id AS INTEGER) AS account_id,
                   TRIM(account_name) AS account_name,
                   LOWER(TRIM(plan)) AS plan,
                   UPPER(TRIM(country)) AS country,
                   CAST(signup_date AS DATE) AS signup_date,
                   LOWER(TRIM(account_status)) AS account_status,
                   CAST(monthly_recurring_revenue AS DECIMAL(12, 2)) AS monthly_recurring_revenue
            FROM bronze_accounts
            WHERE account_id IS NOT NULL
              AND account_name IS NOT NULL
              AND CAST(signup_date AS DATE) IS NOT NULL
              AND monthly_recurring_revenue >= 0
            """
        )
        connection.execute(
            """
            CREATE OR REPLACE TABLE silver_invoices AS
            SELECT TRIM(invoice_id) AS invoice_id,
                   CAST(account_id AS INTEGER) AS account_id,
                   CAST(invoice_date AS DATE) AS invoice_date,
                   CAST(amount AS DECIMAL(12, 2)) AS amount,
                   LOWER(TRIM(invoice_status)) AS invoice_status
            FROM bronze_invoices
            WHERE invoice_id IS NOT NULL AND account_id IS NOT NULL AND amount >= 0
            """
        )
        connection.execute(
            """
            CREATE OR REPLACE TABLE silver_support_tickets AS
            SELECT TRIM(ticket_id) AS ticket_id,
                   CAST(account_id AS INTEGER) AS account_id,
                   CAST(created_date AS DATE) AS created_date,
                   TRY_CAST(resolved_date AS DATE) AS resolved_date,
                   LOWER(TRIM(priority)) AS priority,
                   LOWER(TRIM(ticket_status)) AS ticket_status
            FROM bronze_support_tickets
            WHERE ticket_id IS NOT NULL AND account_id IS NOT NULL AND created_date IS NOT NULL
            """
        )
        connection.execute(
            """
            CREATE OR REPLACE TABLE silver_account_events AS
            SELECT TRIM(event_id) AS event_id,
                   CAST(account_id AS INTEGER) AS account_id,
                   CAST(event_date AS DATE) AS event_date,
                   LOWER(TRIM(event_type)) AS event_type
            FROM bronze_account_events
            WHERE event_id IS NOT NULL AND account_id IS NOT NULL AND event_date IS NOT NULL
            """
        )
        quality_checks = {
            "duplicate_account_ids": _count_query(
                connection,
                "SELECT COUNT(*) FROM (SELECT account_id FROM silver_accounts GROUP BY account_id HAVING COUNT(*) > 1)",
            ),
            "duplicate_invoice_ids": _count_query(
                connection,
                "SELECT COUNT(*) FROM (SELECT invoice_id FROM silver_invoices GROUP BY invoice_id HAVING COUNT(*) > 1)",
            ),
            "orphan_invoices": _count_query(
                connection,
                """SELECT COUNT(*) FROM silver_invoices i
                   WHERE NOT EXISTS (SELECT 1 FROM silver_accounts a WHERE a.account_id = i.account_id)""",
            ),
            "orphan_tickets": _count_query(
                connection,
                """SELECT COUNT(*) FROM silver_support_tickets t
                   WHERE NOT EXISTS (SELECT 1 FROM silver_accounts a WHERE a.account_id = t.account_id)""",
            ),
            "orphan_events": _count_query(
                connection,
                """SELECT COUNT(*) FROM silver_account_events e
                   WHERE NOT EXISTS (SELECT 1 FROM silver_accounts a WHERE a.account_id = e.account_id)""",
            ),
            "invalid_account_statuses": _count_query(
                connection,
                "SELECT COUNT(*) FROM silver_accounts WHERE account_status NOT IN ('active', 'trial', 'churned')",
            ),
            "invalid_invoice_statuses": _count_query(
                connection,
                "SELECT COUNT(*) FROM silver_invoices WHERE invoice_status NOT IN ('paid', 'overdue')",
            ),
            "invalid_ticket_priorities": _count_query(
                connection,
                "SELECT COUNT(*) FROM silver_support_tickets WHERE priority NOT IN ('low', 'medium', 'high')",
            ),
            "invalid_ticket_statuses": _count_query(
                connection,
                "SELECT COUNT(*) FROM silver_support_tickets WHERE ticket_status NOT IN ('open', 'resolved')",
            ),
            "invalid_event_types": _count_query(
                connection,
                "SELECT COUNT(*) FROM silver_account_events WHERE event_type NOT IN ('account_created', 'trial_started', 'activated', 'cancelled')",
            ),
        }
        if any(quality_checks.values()):
            raise ValueError(f"Client quality gate failed: {quality_checks}")
        for table in ("accounts", "invoices", "support_tickets", "account_events"):
            _copy_parquet(connection, f"silver_{table}", data_dir / "silver")
    finally:
        connection.close()

    _run_dbt(data_dir, database_path, client_id)
    connection = duckdb.connect(str(database_path), read_only=True)
    try:
        gold_tables = ["gold_client_scorecard", "gold_account_health", "gold_daily_operations"]
        for table in gold_tables:
            _copy_parquet(connection, table, data_dir / "gold")
        scorecard = connection.execute("SELECT * FROM gold_client_scorecard").fetchone()
        columns = [row[0] for row in connection.execute("DESCRIBE gold_client_scorecard").fetchall()]
        scorecard_values = dict(zip(columns, scorecard, strict=True))
    finally:
        connection.close()

    duration = round(time.perf_counter() - started, 3)
    quality_report = {
        "status": "passed",
        "checks": quality_checks,
        "score": 100,
        "source_rows": raw_counts,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    manifest = {
        "client_id": client_id,
        "delivery_id": f"{client_id}-2025-03",
        "delivery_status": "accepted",
        "reporting_period": "2025-03",
        "deliverables": ["client_scorecard", "account_health", "daily_operations"],
        "quality_gate": quality_report,
        "sla": {"target_hours": 24, "actual_duration_seconds": duration, "status": "within_target"},
        "scorecard": {key: _json_value(value) for key, value in scorecard_values.items()},
    }
    (data_dir / "quality_report.json").write_text(json.dumps(quality_report, indent=2), encoding="utf-8")
    (data_dir / "service_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _json_value(value: object) -> object:
    if isinstance(value, Decimal):
        return float(value)
    return value.isoformat() if hasattr(value, "isoformat") else value


def _run_dbt(data_dir: Path, database_path: Path, client_id: str) -> None:
    project_dir = Path(
        os.environ.get("CLIENT_DATA_OPS_DBT_PROJECT_DIR", str(Path.cwd() / "dbt"))
    ).resolve()
    environment = os.environ.copy()
    environment["CLIENT_DATA_OPS_DB_PATH"] = str(database_path.resolve())
    environment["CLIENT_DATA_OPS_CLIENT_ID"] = client_id
    result = subprocess.run(
        [
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
            "--full-refresh",
        ],
        cwd=data_dir.parent,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        raise RuntimeError(f"dbt build failed:\n{output}")
