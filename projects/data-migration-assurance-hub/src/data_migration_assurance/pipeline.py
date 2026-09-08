"""Run migration validation, reconciliation and cutover assessment."""

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


TABLES = {
    "accounts": {
        "key": "account_id",
        "columns": ["account_id", "account_name", "country", "created_date", "monthly_value"],
    },
    "invoices": {
        "key": "invoice_id",
        "columns": ["invoice_id", "account_id", "invoice_date", "amount", "invoice_status"],
    },
    "transactions": {
        "key": "transaction_id",
        "columns": ["transaction_id", "account_id", "transaction_date", "amount", "transaction_type"],
    },
    "contacts": {
        "key": "contact_id",
        "columns": ["contact_id", "account_id", "email", "country", "contact_status"],
    },
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


def run_migration(
    data_dir: Path,
    migration_id: str = "MIG-2026-09-W03",
    scenario: str = "review",
) -> dict:
    """Run one migration review and publish its evidence manifest."""
    started = time.perf_counter()
    source_dir = data_dir / "source"
    target_dir = data_dir / "target"
    database_path = data_dir / "warehouse" / "migration_assurance.duckdb"
    database_path.parent.mkdir(parents=True, exist_ok=True)
    missing = [
        f"{side}/{table}.csv"
        for side, directory in (("source", source_dir), ("target", target_dir))
        for table in TABLES
        if not (directory / f"{table}.csv").exists()
    ]
    if missing:
        raise FileNotFoundError(f"Missing migration snapshots: {', '.join(missing)}")

    connection = duckdb.connect(str(database_path))
    try:
        raw_counts: dict[str, dict[str, int]] = {"source": {}, "target": {}}
        for side, directory in (("source", source_dir), ("target", target_dir)):
            for table in TABLES:
                source_path = _sql_path(directory / f"{table}.csv")
                bronze_table = f"bronze_{side}_{table}"
                connection.execute(
                    f"CREATE OR REPLACE TABLE {bronze_table} AS "
                    f"SELECT * FROM read_csv_auto('{source_path}', header = true)"
                )
                _copy_parquet(connection, bronze_table, data_dir / "bronze")
                raw_counts[side][table] = _count(connection, bronze_table)

        _create_silver_tables(connection)
        quality_checks = _source_quality_checks(connection)
        if any(quality_checks.values()):
            raise ValueError(f"Source quality gate failed: {quality_checks}")
        for side in ("source", "target"):
            for table in TABLES:
                _copy_parquet(connection, f"silver_{side}_{table}", data_dir / "silver")
    finally:
        connection.close()

    _run_dbt(data_dir, database_path, migration_id)
    connection = duckdb.connect(str(database_path), read_only=True)
    try:
        gold_tables = [
            "gold_reconciliation",
            "gold_exception_queue",
            "gold_cutover_readiness",
        ]
        for table in gold_tables:
            _copy_parquet(connection, table, data_dir / "gold")
        readiness = connection.execute("SELECT * FROM gold_cutover_readiness").fetchone()
        readiness_columns = [row[0] for row in connection.execute("DESCRIBE gold_cutover_readiness").fetchall()]
        readiness_values = dict(zip(readiness_columns, readiness, strict=True))
        exceptions = connection.execute(
            "SELECT severity, COUNT(*) AS issue_count FROM gold_exception_queue GROUP BY severity ORDER BY severity"
        ).fetchall()
        reconciliation = connection.execute("SELECT * FROM gold_reconciliation ORDER BY entity").fetchall()
        reconciliation_columns = [row[0] for row in connection.execute("DESCRIBE gold_reconciliation").fetchall()]
    finally:
        connection.close()

    exception_counts = {str(row[0]): int(row[1]) for row in exceptions}
    duration = round(time.perf_counter() - started, 3)
    decision = str(readiness_values["cutover_decision"])
    quality_report = {
        "status": "passed",
        "checks": quality_checks,
        "score": 100,
        "source_rows": raw_counts["source"],
        "target_rows": raw_counts["target"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    checklist = [
        {"check": "source_snapshot_received", "status": "passed", "owner": "Data"},
        {"check": "source_quality_gate", "status": "passed", "owner": "Data"},
        {"check": "row_and_amount_reconciliation", "status": "review" if decision != "READY" else "passed", "owner": "Data"},
        {"check": "blocking_exceptions_resolved", "status": "blocked" if decision == "HOLD" else "passed", "owner": "Migration lead"},
        {"check": "finance_signoff", "status": "pending", "owner": "Finance"},
        {"check": "business_owner_signoff", "status": "pending", "owner": "Business owner"},
    ]
    manifest = {
        "migration_id": migration_id,
        "scenario": scenario,
        "source_system": "Legacy CRM and Billing",
        "target_system": "Analytics Warehouse",
        "wave": "03",
        "cutover_decision": decision,
        "delivery_status": "review_required" if decision == "HOLD" else "ready_for_signoff",
        "quality_gate": quality_report,
        "exceptions_by_severity": exception_counts,
        "checklist": checklist,
        "sla": {"target_hours": 24, "actual_duration_seconds": duration, "status": "within_target"},
        "reconciliation": [
            {_json_value(key): _json_value(value) for key, value in zip(reconciliation_columns, row, strict=True)}
            for row in reconciliation
        ],
    }
    (data_dir / "quality_report.json").write_text(json.dumps(quality_report, indent=2), encoding="utf-8")
    (data_dir / "migration_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _create_silver_tables(connection: duckdb.DuckDBPyConnection) -> None:
    for side in ("source", "target"):
        connection.execute(
            f"""
            CREATE OR REPLACE TABLE silver_{side}_accounts AS
            SELECT CAST(account_id AS INTEGER) AS account_id,
                   TRIM(account_name) AS account_name,
                   UPPER(TRIM(country)) AS country,
                   CAST(created_date AS DATE) AS created_date,
                   CAST(monthly_value AS DECIMAL(12, 2)) AS monthly_value
            FROM bronze_{side}_accounts
            WHERE account_id IS NOT NULL AND account_name IS NOT NULL AND monthly_value >= 0
            """
        )
        connection.execute(
            f"""
            CREATE OR REPLACE TABLE silver_{side}_invoices AS
            SELECT TRIM(invoice_id) AS invoice_id,
                   CAST(account_id AS INTEGER) AS account_id,
                   CAST(invoice_date AS DATE) AS invoice_date,
                   CAST(amount AS DECIMAL(12, 2)) AS amount,
                   LOWER(TRIM(invoice_status)) AS invoice_status
            FROM bronze_{side}_invoices
            WHERE invoice_id IS NOT NULL AND account_id IS NOT NULL AND amount >= 0
            """
        )
        connection.execute(
            f"""
            CREATE OR REPLACE TABLE silver_{side}_transactions AS
            SELECT TRIM(transaction_id) AS transaction_id,
                   CAST(account_id AS INTEGER) AS account_id,
                   CAST(transaction_date AS DATE) AS transaction_date,
                   CAST(amount AS DECIMAL(12, 2)) AS amount,
                   LOWER(TRIM(transaction_type)) AS transaction_type
            FROM bronze_{side}_transactions
            WHERE transaction_id IS NOT NULL AND account_id IS NOT NULL AND amount >= 0
            """
        )
        connection.execute(
            f"""
            CREATE OR REPLACE TABLE silver_{side}_contacts AS
            SELECT TRIM(contact_id) AS contact_id,
                   CAST(account_id AS INTEGER) AS account_id,
                   LOWER(TRIM(email)) AS email,
                   UPPER(TRIM(country)) AS country,
                   LOWER(TRIM(contact_status)) AS contact_status
            FROM bronze_{side}_contacts
            WHERE contact_id IS NOT NULL AND account_id IS NOT NULL AND email IS NOT NULL
            """
        )


def _source_quality_checks(connection: duckdb.DuckDBPyConnection) -> dict[str, int]:
    checks: dict[str, int] = {}
    for table, config in TABLES.items():
        key = config["key"]
        checks[f"duplicate_source_{table}"] = _count_query(
            connection,
            f"SELECT COUNT(*) FROM (SELECT {key} FROM silver_source_{table} GROUP BY {key} HAVING COUNT(*) > 1)",
        )
        checks[f"null_source_{key}"] = _count_query(
            connection, f"SELECT COUNT(*) FROM silver_source_{table} WHERE {key} IS NULL"
        )
    checks["orphan_source_invoices"] = _count_query(
        connection,
        """SELECT COUNT(*) FROM silver_source_invoices i
           WHERE NOT EXISTS (SELECT 1 FROM silver_source_accounts a WHERE a.account_id = i.account_id)""",
    )
    checks["orphan_source_transactions"] = _count_query(
        connection,
        """SELECT COUNT(*) FROM silver_source_transactions t
           WHERE NOT EXISTS (SELECT 1 FROM silver_source_accounts a WHERE a.account_id = t.account_id)""",
    )
    checks["orphan_source_contacts"] = _count_query(
        connection,
        """SELECT COUNT(*) FROM silver_source_contacts c
           WHERE NOT EXISTS (SELECT 1 FROM silver_source_accounts a WHERE a.account_id = c.account_id)""",
    )
    return checks


def _json_value(value: object) -> object:
    if isinstance(value, Decimal):
        return float(value)
    return value.isoformat() if hasattr(value, "isoformat") else value


def _run_dbt(data_dir: Path, database_path: Path, migration_id: str) -> None:
    project_dir = Path(
        os.environ.get("DATA_MIGRATION_DBT_PROJECT_DIR", str(Path.cwd() / "dbt"))
    ).resolve()
    environment = os.environ.copy()
    environment["DATA_MIGRATION_DB_PATH"] = str(database_path.resolve())
    environment["DATA_MIGRATION_ID"] = migration_id
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
