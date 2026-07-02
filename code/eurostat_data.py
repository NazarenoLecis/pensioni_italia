from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from italian_our_world_data import fetch_eurostat_data, list_eurostat_dataflows
from utils import METADATA_DIR, RAW_DIR, PROCESSED_DIR, ensure_project_dirs, read_optional_csv, write_frame

WHITELIST_PATH = METADATA_DIR / "eurostat_whitelist.csv"
CATALOGUE_PATH = METADATA_DIR / "eurostat_catalogue.csv"
RAW_EUROSTAT_DIR = RAW_DIR / "eurostat"
DOWNLOAD_LOG_PATH = PROCESSED_DIR / "eurostat_download_log.csv"


def run_eurostat_discovery(output_path: str | Path = CATALOGUE_PATH) -> pd.DataFrame:
    """Scarica il catalogo Eurostat e lo salva in metadata."""
    ensure_project_dirs()
    frame = list_eurostat_dataflows()
    write_frame(frame, output_path)
    return frame


def parse_filters(filters_text: object) -> dict[str, object]:
    """Converte i filtri Eurostat da JSON testuale a dizionario Python."""
    if pd.isna(filters_text) or str(filters_text).strip() == "":
        return {}
    return json.loads(str(filters_text))


def fetch_eurostat_whitelist(output_dir: str | Path = RAW_EUROSTAT_DIR) -> pd.DataFrame:
    """Scarica i dataset Eurostat selezionati nella whitelist.

    La whitelist usa `dataset` e una colonna `filters` in formato JSON, per
    esempio {"geo":"IT","unit":"PC_GDP"}.
    """
    whitelist = read_optional_csv(WHITELIST_PATH)
    if whitelist.empty:
        return pd.DataFrame(columns=["dataset", "status", "rows", "columns", "output_path", "error"])
    if "status" in whitelist.columns:
        whitelist = whitelist[whitelist["status"].fillna("").str.lower().isin({"selected", "active", "keep"})]
    logs = []
    for _, row in whitelist.iterrows():
        dataset = str(row["dataset"]).strip()
        output_name = row.get("output_name") if pd.notna(row.get("output_name")) else dataset
        try:
            data = fetch_eurostat_data(
                dataset,
                filters=parse_filters(row.get("filters")),
                start_period=row.get("start_period") if pd.notna(row.get("start_period")) else None,
                end_period=row.get("end_period") if pd.notna(row.get("end_period")) else None,
            )
            output_path = Path(output_dir) / f"{output_name}.csv"
            write_frame(data, output_path)
            logs.append({"dataset": dataset, "status": "ok", "rows": len(data), "columns": len(data.columns), "output_path": str(output_path), "error": ""})
        except Exception as exc:
            logs.append({"dataset": dataset, "status": "error", "rows": 0, "columns": 0, "output_path": "", "error": str(exc)})
    return pd.DataFrame(logs)


def run_eurostat_download(output_path: str | Path = DOWNLOAD_LOG_PATH) -> pd.DataFrame:
    """Scarica i dati Eurostat selezionati e salva il log."""
    ensure_project_dirs()
    log = fetch_eurostat_whitelist()
    write_frame(log, output_path)
    return log
