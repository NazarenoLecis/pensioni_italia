from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import pandas as pd

from italian_our_world_data import (
    fetch_inps_data,
    get_inps_dataset_metadata,
    list_inps_datasets,
)

from .io import read_optional_csv, write_frame
from .paths import METADATA_DIR, RAW_DIR

DEFAULT_TERMS = (
    "pensioni",
    "pensionati",
    "pensione",
    "vecchiaia",
    "anzianita",
    "anticipata",
    "invalidita",
    "inabilita",
    "superstiti",
    "reversibilita",
    "assegno sociale",
    "pensioni sociali",
    "invalidi civili",
    "invalidita civile",
    "accompagnamento",
    "liquidate",
    "vigenti",
    "gestione",
    "fondo",
    "FPLD",
    "dipendenti pubblici",
    "gestione separata",
    "artigiani",
    "commercianti",
    "coltivatori diretti",
    "ENPALS",
    "INPGI",
    "clero",
    "fondi speciali",
    "ex fondi",
    "GIAS",
    "prestazioni istituzionali",
    "rendiconto",
    "trasferimenti",
    "contributi",
)


def load_inps_search_terms(path: str | Path | None = None) -> list[str]:
    terms_path = Path(path) if path is not None else METADATA_DIR / "inps_search_terms.csv"
    frame = read_optional_csv(terms_path)
    if frame.empty or "term" not in frame:
        return list(DEFAULT_TERMS)
    if "include_default" in frame:
        frame = frame[frame["include_default"].fillna(0).astype(int).eq(1)]
    return sorted({str(term).strip() for term in frame["term"].dropna() if str(term).strip()})


def _match_terms(text: str, terms: Iterable[str]) -> list[str]:
    text_lower = text.lower()
    matches = []
    for term in terms:
        if re.search(re.escape(term.lower()), text_lower):
            matches.append(term)
    return matches


def discover_inps_datasets(
    *,
    terms: Iterable[str] | None = None,
    with_metadata: bool = False,
    limit: int | None = None,
    offset: int | None = None,
) -> pd.DataFrame:
    """Return INPS datasets whose identifiers or metadata match pension terms."""
    search_terms = list(terms) if terms is not None else load_inps_search_terms()
    catalogue = list_inps_datasets(limit=limit, offset=offset)
    if catalogue.empty:
        return catalogue

    rows: list[dict[str, object]] = []
    for dataset_id in catalogue["dataset_id"].dropna().astype(str):
        metadata = {}
        metadata_text = dataset_id
        if with_metadata:
            try:
                metadata = dict(get_inps_dataset_metadata(dataset_id))
            except Exception as exc:  # noqa: BLE001
                metadata = {"metadata_error": str(exc)}
            metadata_text = " ".join(
                str(metadata.get(key, ""))
                for key in ("id", "name", "title", "notes", "description", "metadata_error")
            )
        matches = _match_terms(metadata_text, search_terms)
        if matches:
            rows.append(
                {
                    "dataset_id": dataset_id,
                    "matched_terms": "; ".join(matches),
                    "title": metadata.get("title") or metadata.get("name"),
                    "notes": metadata.get("notes") or metadata.get("description"),
                    "resources_count": len(metadata.get("resources", [])) if metadata else pd.NA,
                    "metadata_error": metadata.get("metadata_error"),
                }
            )
    return pd.DataFrame(rows).sort_values(["dataset_id"]).reset_index(drop=True)


def build_inps_resource_table(dataset_ids: Iterable[str]) -> pd.DataFrame:
    """Return one row for each downloadable resource exposed by selected INPS datasets."""
    rows: list[dict[str, object]] = []
    for dataset_id in sorted({str(value).strip() for value in dataset_ids if str(value).strip()}):
        try:
            metadata = dict(get_inps_dataset_metadata(dataset_id))
        except Exception as exc:  # noqa: BLE001
            rows.append({"dataset_id": dataset_id, "metadata_error": str(exc)})
            continue
        for index, resource in enumerate(metadata.get("resources", []) or []):
            rows.append(
                {
                    "dataset_id": dataset_id,
                    "resource_index": index,
                    "resource_id": resource.get("id"),
                    "name": resource.get("name"),
                    "description": resource.get("description"),
                    "format": resource.get("format"),
                    "url": resource.get("url"),
                    "created": resource.get("created"),
                    "last_modified": resource.get("last_modified"),
                    "metadata_modified": metadata.get("metadata_modified"),
                    "dataset_title": metadata.get("title") or metadata.get("name"),
                }
            )
    return pd.DataFrame(rows)


def load_inps_whitelist(path: str | Path | None = None) -> pd.DataFrame:
    whitelist_path = Path(path) if path is not None else METADATA_DIR / "inps_dataset_whitelist.csv"
    frame = read_optional_csv(whitelist_path)
    if frame.empty:
        return frame
    if "status" in frame:
        frame = frame[frame["status"].fillna("").str.lower().isin({"selected", "active", "keep"})]
    return frame.dropna(subset=["dataset_id"]).copy()


def fetch_whitelisted_inps_datasets(
    *,
    whitelist_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    file_format: str = "csv",
) -> pd.DataFrame:
    """Download selected INPS datasets and return a download log."""
    whitelist = load_inps_whitelist(whitelist_path)
    target_dir = Path(output_dir) if output_dir is not None else RAW_DIR / "inps"
    rows: list[dict[str, object]] = []
    if whitelist.empty:
        return pd.DataFrame(
            columns=["dataset_id", "resource_index", "status", "rows", "columns", "output_path", "error"]
        )

    for _, item in whitelist.iterrows():
        dataset_id = str(item["dataset_id"]).strip()
        resource_index = int(item.get("resource_index", 0) or 0)
        try:
            data = fetch_inps_data(dataset_id, resource_index=resource_index)
            output_path = target_dir / f"{dataset_id}__resource_{resource_index}.{file_format}"
            write_frame(data, output_path)
            rows.append(
                {
                    "dataset_id": dataset_id,
                    "resource_index": resource_index,
                    "status": "ok",
                    "rows": len(data),
                    "columns": len(data.columns),
                    "output_path": str(output_path),
                    "error": "",
                }
            )
        except Exception as exc:  # noqa: BLE001
            rows.append(
                {
                    "dataset_id": dataset_id,
                    "resource_index": resource_index,
                    "status": "error",
                    "rows": 0,
                    "columns": 0,
                    "output_path": "",
                    "error": str(exc),
                }
            )
    return pd.DataFrame(rows)
