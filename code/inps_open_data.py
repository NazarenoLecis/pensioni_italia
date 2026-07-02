from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import pandas as pd
from italian_our_world_data import fetch_inps_data, get_inps_dataset_metadata, list_inps_datasets
from utils import METADATA_DIR, RAW_DIR, PROCESSED_DIR, ensure_project_dirs, read_optional_csv, write_frame

WITH_METADATA = True
CANDIDATES_PATH = METADATA_DIR / "inps_catalogue_candidates.csv"
RESOURCES_PATH = METADATA_DIR / "inps_resource_table.csv"
WHITELIST_PATH = METADATA_DIR / "inps_dataset_whitelist.csv"
RAW_INPS_DIR = RAW_DIR / "inps"
DOWNLOAD_LOG_PATH = PROCESSED_DIR / "inps_download_log.csv"

DEFAULT_TERMS = (
    "pensioni", "pensionati", "pensione", "vecchiaia", "anzianita", "anticipata",
    "invalidita", "inabilita", "superstiti", "reversibilita", "assegno sociale",
    "invalidita civile", "accompagnamento", "liquidate", "vigenti", "decorrenza",
    "gestione", "fondo", "FPLD", "dipendenti pubblici", "gestione separata",
    "artigiani", "commercianti", "coltivatori diretti", "ENPALS", "INPGI",
    "clero", "fondi speciali", "ex fondi", "GIAS", "trasferimenti", "contributi",
)


def load_inps_search_terms(search_terms_path: str | Path = METADATA_DIR / "inps_search_terms.csv") -> list[str]:
    """Legge i termini usati per scoprire dataset INPS sulle pensioni.

    Flow: legge il CSV dei termini, tiene solo quelli attivi, usa i termini di
    fallback se il file non esiste, restituisce una lista pulita senza duplicati.
    """
    frame = read_optional_csv(search_terms_path)
    if frame.empty or "term" not in frame.columns:
        return list(DEFAULT_TERMS)
    if "include_default" in frame.columns:
        frame = frame[frame["include_default"].fillna(0).astype(int).eq(1)]
    return sorted({str(term).strip() for term in frame["term"].dropna() if str(term).strip()})


def match_terms(text: str, terms: Iterable[str]) -> list[str]:
    """Trova i termini presenti in una stringa di metadati."""
    text_lower = str(text).lower()
    return [term for term in terms if re.search(re.escape(term.lower()), text_lower)]


def discover_inps_datasets(with_metadata: bool = WITH_METADATA) -> pd.DataFrame:
    """Crea la lista dei dataset INPS candidati per il tema pensioni.

    Flow: scarica il catalogo INPS, cerca i termini nei dataset id, opzionalmente
    scarica i metadati, salva solo i dataset con almeno un match testuale.
    """
    terms = load_inps_search_terms()
    catalogue = list_inps_datasets()
    rows = []
    for dataset_id in catalogue["dataset_id"].dropna().astype(str):
        metadata = {}
        search_text = dataset_id
        if with_metadata:
            try:
                metadata = dict(get_inps_dataset_metadata(dataset_id))
            except Exception as exc:
                metadata = {"metadata_error": str(exc)}
            fields = ("id", "name", "title", "notes", "description", "metadata_error")
            search_text = " ".join([dataset_id] + [str(metadata.get(field, "")) for field in fields])
        matches = match_terms(search_text, terms)
        if matches:
            rows.append({
                "dataset_id": dataset_id,
                "matched_terms": "; ".join(matches),
                "title": metadata.get("title") or metadata.get("name"),
                "notes": metadata.get("notes") or metadata.get("description"),
                "resources_count": len(metadata.get("resources", [])) if metadata else pd.NA,
                "metadata_error": metadata.get("metadata_error"),
            })
    return pd.DataFrame(rows)


def run_inps_discovery(output_path: str | Path = CANDIDATES_PATH) -> pd.DataFrame:
    """Esegue la discovery e salva la tabella dei candidati."""
    ensure_project_dirs()
    frame = discover_inps_datasets()
    write_frame(frame, output_path)
    return frame


def build_inps_resource_table(candidates_path: str | Path = CANDIDATES_PATH) -> pd.DataFrame:
    """Legge i candidati e crea una riga per ogni risorsa pubblicata da INPS."""
    candidates = read_optional_csv(candidates_path)
    rows = []
    for dataset_id in candidates.get("dataset_id", pd.Series(dtype=str)).dropna().astype(str):
        try:
            metadata = dict(get_inps_dataset_metadata(dataset_id))
        except Exception as exc:
            rows.append({"dataset_id": dataset_id, "metadata_error": str(exc)})
            continue
        for resource_index, resource in enumerate(metadata.get("resources", []) or []):
            rows.append({
                "dataset_id": dataset_id,
                "resource_index": resource_index,
                "format": resource.get("format"),
                "url": resource.get("url"),
                "name": resource.get("name"),
                "dataset_title": metadata.get("title") or metadata.get("name"),
            })
    return pd.DataFrame(rows)


def run_inps_resource_table(output_path: str | Path = RESOURCES_PATH) -> pd.DataFrame:
    """Salva la tabella delle risorse INPS disponibili."""
    frame = build_inps_resource_table()
    write_frame(frame, output_path)
    return frame


def fetch_whitelisted_inps(output_dir: str | Path = RAW_INPS_DIR) -> pd.DataFrame:
    """Scarica i dataset INPS selezionati nella whitelist e restituisce un log."""
    whitelist = read_optional_csv(WHITELIST_PATH)
    if whitelist.empty:
        return pd.DataFrame(columns=["dataset_id", "status", "rows", "columns", "output_path", "error"])
    if "status" in whitelist.columns:
        whitelist = whitelist[whitelist["status"].fillna("").str.lower().isin({"selected", "active", "keep"})]
    logs = []
    for _, row in whitelist.iterrows():
        dataset_id = str(row["dataset_id"]).strip()
        resource_index = int(row.get("resource_index", 0) or 0)
        try:
            data = fetch_inps_data(dataset_id, resource_index=resource_index)
            output_path = Path(output_dir) / f"{dataset_id}__resource_{resource_index}.csv"
            write_frame(data, output_path)
            logs.append({"dataset_id": dataset_id, "status": "ok", "rows": len(data), "columns": len(data.columns), "output_path": str(output_path), "error": ""})
        except Exception as exc:
            logs.append({"dataset_id": dataset_id, "status": "error", "rows": 0, "columns": 0, "output_path": "", "error": str(exc)})
    return pd.DataFrame(logs)


def run_inps_download(output_path: str | Path = DOWNLOAD_LOG_PATH) -> pd.DataFrame:
    """Scarica i dataset INPS selezionati e salva il log del download."""
    ensure_project_dirs()
    log = fetch_whitelisted_inps()
    write_frame(log, output_path)
    return log
