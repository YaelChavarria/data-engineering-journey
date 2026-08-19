from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the NYC TLC batch pipeline")
    parser.add_argument("--month", default="2024-01", help="Month in YYYY-MM format")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Download the source again even if it already exists",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        summary = run_pipeline(
            month=args.month,
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            force_download=args.force_download,
        )
    except Exception as error:  # noqa: BLE001 - CLI must return a useful failure
        print(f"Pipeline failed: {error}")
        return 1

    print(json.dumps(summary, indent=2))
    return 0
