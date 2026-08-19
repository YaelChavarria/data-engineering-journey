from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

import duckdb

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def source_url(month: str) -> str:
    """Return the official TLC Parquet URL for a YYYY-MM month."""
    if not MONTH_PATTERN.fullmatch(month):
        raise ValueError("month must use YYYY-MM format, for example 2024-01")
    return f"{BASE_URL}/yellow_tripdata_{month}.parquet"


def download_source(url: str, destination: Path, force: bool = False) -> Path:
    """Download a source file once and stream it to disk."""
    if destination.exists() and destination.stat().st_size > 0 and not force:
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "data-engineering-journey/0.1"})
    with urlopen(request, timeout=120) as response, destination.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
    return destination


def create_raw_table(connection: duckdb.DuckDBPyConnection, parquet_path: Path) -> None:
    """Load the source Parquet file into a typed raw table."""
    connection.execute(
        """
        CREATE OR REPLACE TABLE raw_trips AS
        SELECT
            CAST(VendorID AS INTEGER) AS vendor_id,
            CAST(tpep_pickup_datetime AS TIMESTAMP) AS pickup_at,
            CAST(tpep_dropoff_datetime AS TIMESTAMP) AS dropoff_at,
            CAST(passenger_count AS DOUBLE) AS passenger_count,
            CAST(trip_distance AS DOUBLE) AS trip_distance,
            CAST(RatecodeID AS INTEGER) AS rate_code_id,
            CAST(PULocationID AS INTEGER) AS pickup_location_id,
            CAST(DOLocationID AS INTEGER) AS dropoff_location_id,
            CAST(payment_type AS INTEGER) AS payment_type,
            CAST(fare_amount AS DOUBLE) AS fare_amount,
            CAST(tip_amount AS DOUBLE) AS tip_amount,
            CAST(tolls_amount AS DOUBLE) AS tolls_amount,
            CAST(total_amount AS DOUBLE) AS total_amount
        FROM read_parquet(?)
        """,
        [str(parquet_path)],
    )


def create_staging_table(connection: duckdb.DuckDBPyConnection) -> None:
    """Keep records that satisfy the pipeline's basic analytical rules."""
    connection.execute(
        """
        CREATE OR REPLACE TABLE stg_trips AS
        SELECT *
        FROM raw_trips
        WHERE pickup_at IS NOT NULL
          AND dropoff_at IS NOT NULL
          AND dropoff_at >= pickup_at
          AND trip_distance >= 0
          AND total_amount >= 0
        """
    )


def create_daily_metrics(connection: duckdb.DuckDBPyConnection) -> int:
    """Create the final daily analytical table and return its row count."""
    connection.execute(
        """
        CREATE OR REPLACE TABLE daily_metrics AS
        SELECT
            CAST(pickup_at AS DATE) AS trip_date,
            COUNT(*) AS trip_count,
            ROUND(SUM(COALESCE(passenger_count, 0)), 2) AS passenger_count,
            ROUND(SUM(total_amount), 2) AS gross_revenue,
            ROUND(AVG(trip_distance), 2) AS avg_trip_distance,
            ROUND(AVG(total_amount), 2) AS avg_total_amount
        FROM stg_trips
        GROUP BY 1
        ORDER BY 1
        """
    )
    return connection.execute("SELECT COUNT(*) FROM daily_metrics").fetchone()[0]


def quality_report(connection: duckdb.DuckDBPyConnection) -> dict[str, int | bool]:
    """Return source, staging, and post-cleaning quality metrics."""
    raw_rows = connection.execute("SELECT COUNT(*) FROM raw_trips").fetchone()[0]
    staged_rows = connection.execute("SELECT COUNT(*) FROM stg_trips").fetchone()[0]
    invalid_rows = connection.execute(
        """
        SELECT COUNT(*)
        FROM raw_trips
        WHERE pickup_at IS NULL
           OR dropoff_at IS NULL
           OR dropoff_at < pickup_at
           OR trip_distance < 0
           OR total_amount < 0
        """
    ).fetchone()[0]
    staged_invalid_rows = connection.execute(
        """
        SELECT COUNT(*)
        FROM stg_trips
        WHERE pickup_at IS NULL
           OR dropoff_at IS NULL
           OR dropoff_at < pickup_at
           OR trip_distance < 0
           OR total_amount < 0
        """
    ).fetchone()[0]

    return {
        "raw_rows": raw_rows,
        "staged_rows": staged_rows,
        "dropped_rows": raw_rows - staged_rows,
        "invalid_rows_detected": invalid_rows,
        "invalid_rows_after_cleaning": staged_invalid_rows,
        "passed": staged_rows > 0 and staged_invalid_rows == 0,
    }


def run_pipeline(
    month: str,
    data_dir: Path = Path("data"),
    output_dir: Path = Path("data/processed"),
    force_download: bool = False,
) -> dict[str, object]:
    """Run extraction, staging, quality checks, and daily aggregation."""
    url = source_url(month)
    raw_path = data_dir / "raw" / f"yellow_tripdata_{month}.parquet"
    database_path = output_dir / "nyc_taxi.duckdb"
    metrics_path = output_dir / "daily_metrics.parquet"
    summary_path = output_dir / "pipeline_summary.json"

    output_dir.mkdir(parents=True, exist_ok=True)
    download_source(url, raw_path, force=force_download)

    connection = duckdb.connect(str(database_path))
    try:
        create_raw_table(connection, raw_path)
        create_staging_table(connection)
        report = quality_report(connection)
        if not report["passed"]:
            raise RuntimeError("staging quality checks failed")
        metric_days = create_daily_metrics(connection)
        connection.execute("COPY daily_metrics TO ? (FORMAT PARQUET)", [str(metrics_path)])
    finally:
        connection.close()

    summary: dict[str, object] = {
        "month": month,
        "source_url": url,
        "raw_file": raw_path.name,
        "metric_days": metric_days,
        "quality": report,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
