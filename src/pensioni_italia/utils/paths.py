from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FINAL_DIR = DATA_DIR / "final"
CACHE_DIR = DATA_DIR / "cache"
METADATA_DIR = PROJECT_ROOT / "metadata"
DOCS_DIR = PROJECT_ROOT / "docs"


def ensure_project_dirs() -> None:
    """Create the local folders used by the project."""
    for path in (DATA_DIR, RAW_DIR, PROCESSED_DIR, FINAL_DIR, CACHE_DIR, METADATA_DIR):
        path.mkdir(parents=True, exist_ok=True)
