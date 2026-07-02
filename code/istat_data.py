from __future__ import annotations

from pathlib import Path

import pandas as pd
from italian_our_world_data import fetch_istat_data, list_istat_dataflows
from utils import METADATA_DIR, RAW_DIR, PROCESSED_DIR, ensure_project_dirs, read_optional_csv, write_frame

WHITELIST_PATH = METADATA_DIR / "istat_dataset_whitelist.csv"
CATALOGUE_PATH = METADATA_DIR / "istat_catalogue.csv"
RAW_ISTAT_DIR = RAW_DIR / "istat"
DOWNLOAD_LOG_PATH = PROCESSED_DIR / "istat_download_log.csv"


def run_istat_discovery(output_path: str | Path = CATALOGUE_PATH) -> pd.DataFrame:
    """Scarica il catalogo ISTAT SDMX e lo salva in metadata."""
    ensure_project_dirs()
    frame = list_istat_dataflows()
    write_frame(frame, output_path)
    return frame


def fetch_istat_whitelist(output_dir: str | Path = RAW_ISTAT_DIR) -> pd.DataFrame:
    """Scarica i dataflow ISTAT selezionati nella whitelist."""
    whitelist = read_optional_csv(WHITELIST_PATH)
    if whitelist.empty:
        return pd.DataFrame(columns=["dataflow_id", "status", "rows", "columns", "output_path", "error"])
    if "status" in whitelist.columns:
        whitelist = whitelist[whitelist["status"].fillna("").str.lower().isin({"selected", "active", "keep"})]
    logs = []
    for _, row in whitelist.iterrows():
        dataflow_id = str(row["dataflow_id"]).strip()
        key = str(row.get("key", "")).strip()
        start_period = row.get("start_period") if pd.notna(row.get("start_period")) else None
        end_period = row.get("end_period") if pd.notna(row.get("end_period")) else None
        output_name = row.get("output_name") if pd.notna(row.get("output_name")) else dataflow_id
        try:
            data = fetch_istat_data(dataflow_id, key=key, start_period=start_period, end_period=end_period)
            output_path = Path(output_dir) / f"{output_name}.csv"
            write_frame(data, output_path)
            logs.append({"dataflow_id": dataflow_id, "status": "ok", "rows": len(data), "columns": len(data.columns), "output_path": str(output_path), "error": ""})
        except Exception as exc:
            logs.append({"dataflow_id": dataflow_id, "status": "error", "rows": 0, "columns": 0, "output_path": "", "error": str(exc)})
    return pd.DataFrame(logs)


def run_istat_download(output_path: str | Path = DOWNLOAD_LOG_PATH) -> pd.DataFrame:
    """Scarica i dati ISTAT selezionati e salva il log."""
    ensure_project_dirs()
    log = fetch_istat_whitelist()
    write_frame(log, output_path)
    return log
