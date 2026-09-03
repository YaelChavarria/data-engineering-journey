"""Command-line entry point for a client delivery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .generator import generate_client_export
from .pipeline import run_delivery


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a client DataOps delivery")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--client-id", default="atlas-saas")
    parser.add_argument("--account-count", type=int, default=24)
    parser.add_argument("--skip-generate", action="store_true", help="Use existing client exports")
    args = parser.parse_args()

    if not args.skip_generate:
        generate_client_export(args.data_dir / "source", account_count=args.account_count)
    print(json.dumps(run_delivery(args.data_dir, client_id=args.client_id), indent=2, default=str))
