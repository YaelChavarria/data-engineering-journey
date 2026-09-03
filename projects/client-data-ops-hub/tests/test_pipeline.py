import json
import tempfile
import unittest
from pathlib import Path

import duckdb

from client_data_ops.generator import generate_client_export
from client_data_ops.pipeline import run_delivery


class ClientDataOpsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name) / "data"
        generate_client_export(self.data_dir / "source")
        self.manifest = run_delivery(self.data_dir)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_delivery_is_accepted_with_quality_evidence(self) -> None:
        self.assertEqual(self.manifest["delivery_status"], "accepted")
        self.assertEqual(self.manifest["quality_gate"]["score"], 100)
        self.assertTrue((self.data_dir / "service_manifest.json").exists())
        self.assertEqual(json.loads((self.data_dir / "quality_report.json").read_text())["status"], "passed")

    def test_gold_models_are_materialized(self) -> None:
        connection = duckdb.connect(str(self.data_dir / "warehouse" / "client_delivery.duckdb"), read_only=True)
        try:
            models = connection.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'gold_%' ORDER BY table_name"
            ).fetchall()
            scorecard = connection.execute("SELECT mrr, collection_rate FROM gold_client_scorecard").fetchone()
            attention_count = connection.execute(
                "SELECT COUNT(*) FROM gold_account_health WHERE health_segment = 'needs_attention'"
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertEqual([row[0] for row in models], ["gold_account_health", "gold_client_scorecard", "gold_daily_operations"])
        self.assertGreater(float(scorecard[0]), 0)
        self.assertLess(float(scorecard[1]), 100)
        self.assertGreater(int(attention_count), 0)

    def test_manifest_contains_client_facing_deliverables(self) -> None:
        self.assertEqual(
            self.manifest["deliverables"],
            ["client_scorecard", "account_health", "daily_operations"],
        )
        self.assertEqual(self.manifest["sla"]["status"], "within_target")


if __name__ == "__main__":
    unittest.main()
