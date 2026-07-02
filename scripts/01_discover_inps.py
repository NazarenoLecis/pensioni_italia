from __future__ import annotations

import argparse
from pathlib import Path

from pensioni_italia.inps import discover_inps_datasets, load_inps_search_terms
from pensioni_italia.io import write_frame
from pensioni_italia.paths import METADATA_DIR, ensure_project_dirs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover INPS pension-related datasets.")
    parser.add_argument("--with-metadata", action="store_true", help="Fetch package metadata before filtering.")
    parser.add_argument("--limit", type=int, default=None, help="Optional INPS catalogue limit.")
    parser.add_argument("--offset", type=int, default=None, help="Optional INPS catalogue offset.")
    parser.add_argument(
        "--output",
        type=Path,
        default=METADATA_DIR / "inps_catalogue_candidates.csv",
        help="Output CSV path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_project_dirs()
    terms = load_inps_search_terms()
    frame = discover_inps_datasets(
        terms=terms,
        with_metadata=args.with_metadata,
        limit=args.limit,
        offset=args.offset,
    )
    write_frame(frame, args.output)
    print(f"Saved {len(frame)} candidate datasets to {args.output}")


if __name__ == "__main__":
    main()
