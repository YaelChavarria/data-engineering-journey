import json
import tempfile
import unittest
from pathlib import Path

import duckdb

from data_migration_assurance.generator import generate_snapshots
from data_migration_assurance.pipeline import run_migration


class MigrationAssuranceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name) / "data"
        generate_snapshots(self.data_dir / "source", self.data_dir / "target", scenario="review")
        self.manifest = run_migration(self.data_dir, migration_id="TEST-MIG-W03", scenario="review")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_review_scenario_blocks_cutover(self) -> None:
        self.assertEqual(self.manifest["cutover_decision"], "HOLD")
        self.assertGreater(self.manifest["exceptions_by_severity"]["high"], 0)
        self.assertEqual(self.manifest["delivery_status"], "review_required")

    def test_reconciliation_models_are_materialized(self) -> None:
        connection = duckdb.connect(str(self.data_dir / "warehouse" / "migration_assurance.duckdb"), read_only=True)
        try:
            tables = connection.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'gold_%' ORDER BY table_name"
            ).fetchall()
            invoice = connection.execute(
                "SELECT row_count_delta, amount_delta, reconciliation_status FROM gold_reconciliation WHERE entity = 'invoices'"
            ).fetchone()
            contacts = connection.execute(
                "SELECT row_count_delta, reconciliation_status FROM gold_reconciliation WHERE entity = 'contacts'"
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual(
            [row[0] for row in tables],
            ["gold_cutover_readiness", "gold_exception_queue", "gold_reconciliation"],
        )
        self.assertEqual(int(invoice[0]), 0)
        self.assertNotEqual(float(invoice[1]), 0)
        self.assertEqual(invoice[2], "review")
        self.assertEqual(int(contacts[0]), -2)
        self.assertEqual(contacts[1], "review")

    def test_manifest_contains_client_review_evidence(self) -> None:
        manifest_path = self.data_dir / "migration_manifest.json"
        saved = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["migration_id"], "TEST-MIG-W03")
        self.assertEqual(saved["checklist"][3]["status"], "blocked")
        self.assertEqual(saved["sla"]["status"], "within_target")


if __name__ == "__main__":
    unittest.main()
