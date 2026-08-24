"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .generator import generate_source_data
from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the e-commerce lakehouse")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Use existing source CSVs instead of regenerating the demo source",
    )
    args = parser.parse_args()

    if not args.skip_generate:
        generate_source_data(args.data_dir / "source")
    summary = run_pipeline(args.data_dir)
    print(json.dumps(summary, indent=2))
