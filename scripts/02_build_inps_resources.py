from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from pensioni_italia.inps import build_inps_resource_table, load_inps_whitelist
from pensioni_italia.io import read_optional_csv, write_frame
from pensioni_italia.paths import METADATA_DIR, ensure_project_dirs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the INPS resource table for candidate datasets.")
    parser.add_argument(
        "--input",
        type=Path,
        default=METADATA_DIR / "inps_catalogue_candidates.csv",
        help="Candidate dataset CSV produced by 01_discover_inps.py.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=METADATA_DIR / "inps_resource_table.csv",
        help="Output CSV path.",
    )
    parser.add_argument(
        "--from-whitelist",
        action="store_true",
        help="Use selected rows from metadata/inps_dataset_whitelist.csv instead of the candidate table.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_project_dirs()
    if args.from_whitelist:
        source = load_inps_whitelist()
    else:
        source = read_optional_csv(args.input)
    if source.empty or "dataset_id" not in source:
        frame = pd.DataFrame()
    else:
        frame = build_inps_resource_table(source["dataset_id"])
    write_frame(frame, args.output)
    print(f"Saved {len(frame)} resource rows to {args.output}")


if __name__ == "__main__":
    main()
