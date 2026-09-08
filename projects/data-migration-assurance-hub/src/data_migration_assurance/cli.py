"""Command-line entry point for a migration assurance review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .generator import generate_snapshots
from .pipeline import run_migration


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a data migration assurance review")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--migration-id", default="MIG-2026-09-W03")
    parser.add_argument("--account-count", type=int, default=60)
    parser.add_argument("--scenario", choices=("review", "clean"), default="review")
    parser.add_argument("--skip-generate", action="store_true", help="Use existing source and target snapshots")
    args = parser.parse_args()

    if not args.skip_generate:
        generate_snapshots(
            args.data_dir / "source",
            args.data_dir / "target",
            account_count=args.account_count,
            scenario=args.scenario,
        )
    print(json.dumps(run_migration(args.data_dir, args.migration_id, args.scenario), indent=2, default=str))
