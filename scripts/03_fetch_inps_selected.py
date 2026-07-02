from __future__ import annotations

import argparse
from pathlib import Path

from pensioni_italia.inps import fetch_whitelisted_inps_datasets
from pensioni_italia.io import write_frame
from pensioni_italia.paths import PROCESSED_DIR, RAW_DIR, ensure_project_dirs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch selected INPS datasets from the whitelist.")
    parser.add_argument("--whitelist", type=Path, default=None, help="Optional whitelist CSV path.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RAW_DIR / "inps",
        help="Directory where raw INPS CSV files are written.",
    )
    parser.add_argument(
        "--log-output",
        type=Path,
        default=PROCESSED_DIR / "inps_download_log.csv",
        help="Download log CSV path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_project_dirs()
    log = fetch_whitelisted_inps_datasets(
        whitelist_path=args.whitelist,
        output_dir=args.output_dir,
    )
    write_frame(log, args.log_output)
    print(f"Saved download log with {len(log)} rows to {args.log_output}")


if __name__ == "__main__":
    main()
