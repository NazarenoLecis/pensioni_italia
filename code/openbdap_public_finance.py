from __future__ import annotations

from pathlib import Path

import pandas as pd
from italian_our_world_data import fetch_bdap_data, list_bdap_datasets
from utils import METADATA_DIR, RAW_DIR, PROCESSED_DIR, ensure_project_dirs, read_optional_csv, write_frame

WHITELIST_PATH = METADATA_DIR / "openbdap_dataset_whitelist.csv"
CATALOGUE_PATH = METADATA_DIR / "openbdap_catalogue.csv"
RAW_OPENBDAP_DIR = RAW_DIR / "openbdap"
DOWNLOAD_LOG_PATH = PROCESSED_DIR / "openbdap_download_log.csv"


def discover_openbdap_catalogue(query: str | None = None, rows: int = 200) -> pd.DataFrame:
    """Scarica il catalogo OpenBDAP.

    Flow: interroga il catalogo RGS, restituisce i dataset disponibili, permette
    un filtro testuale per cercare bilancio, rendiconto, trasferimenti o INPS.
    """
    return list_bdap_datasets(query=query, rows=rows)


def run_openbdap_discovery(output_path: str | Path = CATALOGUE_PATH, query: str | None = None) -> pd.DataFrame:
    """Salva il catalogo OpenBDAP utile per scegliere i dataset da mettere in whitelist."""
    ensure_project_dirs()
    frame = discover_openbdap_catalogue(query=query)
    write_frame(frame, output_path)
    return frame


def fetch_openbdap_whitelist(output_dir: str | Path = RAW_OPENBDAP_DIR) -> pd.DataFrame:
    """Scarica le risorse OpenBDAP selezionate nella whitelist.

    La whitelist puo' usare `dataset_id`, `resource_id` o `resource_url`. Questo
    permette di gestire sia risorse CKAN standard sia file puntuali trovati nella
    fase di discovery.
    """
    whitelist = read_optional_csv(WHITELIST_PATH)
    if whitelist.empty:
        return pd.DataFrame(columns=["dataset_id", "status", "rows", "columns", "output_path", "error"])
    if "status" in whitelist.columns:
        whitelist = whitelist[whitelist["status"].fillna("").str.lower().isin({"selected", "active", "keep"})]

    logs = []
    for _, row in whitelist.iterrows():
        dataset_id = row.get("dataset_id") if pd.notna(row.get("dataset_id")) else None
        resource_id = row.get("resource_id") if pd.notna(row.get("resource_id")) else None
        resource_url = row.get("resource_url") if pd.notna(row.get("resource_url")) else None
        resource_index = int(row.get("resource_index", 0) or 0)
        resource_format = row.get("resource_format") if pd.notna(row.get("resource_format")) else None
        output_name = row.get("output_name") if pd.notna(row.get("output_name")) else str(dataset_id or resource_id or "openbdap_resource")
        try:
            data = fetch_bdap_data(
                dataset_id=dataset_id,
                resource_id=resource_id,
                resource_index=resource_index,
                resource_url=resource_url,
                resource_format=resource_format,
            )
            output_path = Path(output_dir) / f"{output_name}.csv"
            write_frame(data, output_path)
            logs.append({"dataset_id": dataset_id, "status": "ok", "rows": len(data), "columns": len(data.columns), "output_path": str(output_path), "error": ""})
        except Exception as exc:
            logs.append({"dataset_id": dataset_id, "status": "error", "rows": 0, "columns": 0, "output_path": "", "error": str(exc)})
    return pd.DataFrame(logs)


def run_openbdap_download(output_path: str | Path = DOWNLOAD_LOG_PATH) -> pd.DataFrame:
    """Scarica i dati OpenBDAP selezionati e salva il log."""
    ensure_project_dirs()
    log = fetch_openbdap_whitelist()
    write_frame(log, output_path)
    return log
