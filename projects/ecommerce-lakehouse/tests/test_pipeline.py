import json
import tempfile
import unittest
from pathlib import Path

import duckdb

from ecommerce_lakehouse.generator import generate_source_data
from ecommerce_lakehouse.pipeline import run_pipeline


class EcommerceLakehouseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name) / "data"
        generate_source_data(self.data_dir / "source")
        self.summary = run_pipeline(self.data_dir)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_all_layers_are_created(self) -> None:
        for layer in ("bronze", "silver", "gold"):
            self.assertTrue((self.data_dir / layer).exists())
        self.assertTrue((self.data_dir / "warehouse" / "ecommerce.duckdb").exists())

    def test_quality_checks_pass(self) -> None:
        self.assertEqual(set(self.summary["quality_checks"].values()), {0})
        summary_path = self.data_dir / "pipeline_summary.json"
        self.assertTrue(summary_path.exists())
        self.assertEqual(json.loads(summary_path.read_text())["completed_orders"], 33)

    def test_cancelled_orders_are_not_revenue(self) -> None:
        connection = duckdb.connect(str(self.data_dir / "warehouse" / "ecommerce.duckdb"), read_only=True)
        try:
            cancelled = connection.execute(
                "SELECT COUNT(*) FROM gold_fact_order WHERE order_status = 'cancelled' AND is_completed = FALSE"
            ).fetchone()[0]
            revenue = connection.execute(
                "SELECT SUM(order_total) FROM gold_fact_order WHERE is_completed"
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(cancelled, 3)
        self.assertGreater(float(revenue), 0)

    def test_gold_category_model_has_business_metrics(self) -> None:
        connection = duckdb.connect(str(self.data_dir / "warehouse" / "ecommerce.duckdb"), read_only=True)
        try:
            columns = [row[0] for row in connection.execute("DESCRIBE gold_category_sales").fetchall()]
            category_count = connection.execute("SELECT COUNT(*) FROM gold_category_sales").fetchone()[0]
        finally:
            connection.close()
        self.assertIn("revenue", columns)
        self.assertIn("units_sold", columns)
        self.assertEqual(category_count, 4)

    def test_incremental_run_appends_new_orders(self) -> None:
        generate_source_data(self.data_dir / "source", order_count=40)
        summary = run_pipeline(self.data_dir, incremental=True)
        self.assertEqual(summary["pipeline_mode"], "incremental")
        self.assertEqual(summary["gold_rows"]["fact_order"], 40)
        self.assertEqual(summary["completed_orders"], 37)


if __name__ == "__main__":
    unittest.main()
