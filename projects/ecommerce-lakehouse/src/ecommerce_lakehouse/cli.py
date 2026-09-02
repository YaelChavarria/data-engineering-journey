"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .generator import generate_source_data
from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Revenue Protection data platform")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Use existing source CSVs instead of regenerating the demo source",
    )
    parser.add_argument(
        "--order-count",
        type=int,
        default=36,
        help="Number of deterministic demo orders to generate",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Only add orders newer than the current Gold fact table",
    )
    args = parser.parse_args()

    if not args.skip_generate:
        generate_source_data(args.data_dir / "source", order_count=args.order_count)
    summary = run_pipeline(args.data_dir, incremental=args.incremental)
    print(json.dumps(summary, indent=2))
