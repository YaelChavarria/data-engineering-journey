from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import duckdb

from nyc_taxi_pipeline.pipeline import (
    create_daily_metrics,
    create_raw_table,
    create_staging_table,
    quality_report,
    source_url,
)


class PipelineTests(unittest.TestCase):
    def test_source_url_requires_year_and_month(self) -> None:
        self.assertEqual(
            source_url("2024-01"),
            "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet",
        )
        with self.assertRaises(ValueError):
            source_url("2024-13")

    def test_staging_removes_invalid_records(self) -> None:
        connection = duckdb.connect()
        try:
            connection.execute(
                """
                CREATE TABLE raw_trips AS
                SELECT * FROM (VALUES
                    (1, TIMESTAMP '2024-01-01 10:00:00', TIMESTAMP '2024-01-01 10:15:00', 1.0, 2.0, 1.0),
                    (2, TIMESTAMP '2024-01-01 11:00:00', TIMESTAMP '2024-01-01 10:59:00', 1.0, 2.0, 5.0),
                    (3, TIMESTAMP '2024-01-01 12:00:00', TIMESTAMP '2024-01-01 12:15:00', 1.0, -1.0, 5.0)
                ) AS rows(vendor_id, pickup_at, dropoff_at, passenger_count, trip_distance, total_amount)
                """
            )
            create_staging_table(connection)
            report = quality_report(connection)
            self.assertEqual(report["raw_rows"], 3)
            self.assertEqual(report["staged_rows"], 1)
            self.assertEqual(report["dropped_rows"], 2)
            self.assertTrue(report["passed"])
        finally:
            connection.close()

    def test_daily_metrics_aggregate_by_date(self) -> None:
        connection = duckdb.connect()
        try:
            connection.execute(
                """
                CREATE TABLE stg_trips AS
                SELECT * FROM (VALUES
                    (TIMESTAMP '2024-01-01 10:00:00', 1.0, 2.0, 10.0),
                    (TIMESTAMP '2024-01-01 11:00:00', 2.0, 4.0, 20.0),
                    (TIMESTAMP '2024-01-02 10:00:00', 1.0, 3.0, 15.0)
                ) AS rows(pickup_at, passenger_count, trip_distance, total_amount)
                """
            )
            metric_days = create_daily_metrics(connection)
            first_day = connection.execute(
                "SELECT trip_count, gross_revenue FROM daily_metrics ORDER BY trip_date LIMIT 1"
            ).fetchone()
            self.assertEqual(metric_days, 2)
            self.assertEqual(first_day, (2, 30.0))
        finally:
            connection.close()

    def test_parquet_source_can_be_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parquet_path = Path(directory) / "sample.parquet"
            connection = duckdb.connect()
            try:
                connection.execute(
                    """
                    CREATE TABLE source AS
                    SELECT * FROM (VALUES
                        (1, TIMESTAMP '2024-01-01 10:00:00', TIMESTAMP '2024-01-01 10:15:00', 1.0, 2.0, 1, 2, 3, 1, 10.0, 1.0, 0.0, 12.0)
                    ) AS rows(VendorID, tpep_pickup_datetime, tpep_dropoff_datetime,
                              passenger_count, trip_distance, RatecodeID, PULocationID,
                              DOLocationID, payment_type, fare_amount, tip_amount,
                              tolls_amount, total_amount)
                    """
                )
                connection.execute("COPY source TO ? (FORMAT PARQUET)", [str(parquet_path)])
                create_raw_table(connection, parquet_path)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM raw_trips").fetchone()[0], 1)
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
