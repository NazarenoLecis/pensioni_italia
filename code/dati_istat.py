from __future__ import annotations

from pathlib import Path

import pandas as pd
from italian_our_world_data import fetch_istat_data, list_istat_dataflows

from utilita import CARTELLA_METADATA, CARTELLA_PROCESSED, CARTELLA_RAW, leggi_csv_opzionale, prepara_cartelle, salva_tabella

PERCORSO_WHITELIST = CARTELLA_METADATA / "istat_dataset_whitelist.csv"
PERCORSO_CATALOGO = CARTELLA_METADATA / "istat_catalogue.csv"
CARTELLA_RAW_ISTAT = CARTELLA_RAW / "istat"
PERCORSO_LOG_DOWNLOAD = CARTELLA_PROCESSED / "istat_download_log.csv"


def esegui_discovery_istat(percorso_output: str | Path = PERCORSO_CATALOGO) -> pd.DataFrame:
    """Scarica il catalogo ISTAT SDMX e lo salva in metadata."""
    prepara_cartelle()
    tabella = list_istat_dataflows()
    salva_tabella(tabella, percorso_output)
    return tabella


def scarica_istat_da_whitelist(cartella_output: str | Path = CARTELLA_RAW_ISTAT) -> pd.DataFrame:
    """Scarica i dataflow ISTAT selezionati nella whitelist.

    La whitelist deve contenere dataflow_id e key. start_period, end_period e
    output_name sono opzionali.
    """
    whitelist = leggi_csv_opzionale(PERCORSO_WHITELIST)
    if whitelist.empty:
        return pd.DataFrame(columns=["dataflow_id", "status", "rows", "columns", "output_path", "error"])
    if "status" in whitelist.columns:
        whitelist = whitelist[whitelist["status"].fillna("").str.lower().isin({"selected", "active", "keep"})]

    log = []
    for _, riga in whitelist.iterrows():
        dataflow_id = str(riga["dataflow_id"]).strip()
        key = str(riga.get("key", "")).strip()
        start_period = riga.get("start_period") if pd.notna(riga.get("start_period")) else None
        end_period = riga.get("end_period") if pd.notna(riga.get("end_period")) else None
        nome_output = riga.get("output_name") if pd.notna(riga.get("output_name")) else dataflow_id
        try:
            dati = fetch_istat_data(dataflow_id, key=key, start_period=start_period, end_period=end_period)
            percorso_output = Path(cartella_output) / f"{nome_output}.csv"
            salva_tabella(dati, percorso_output)
            log.append({"dataflow_id": dataflow_id, "status": "ok", "rows": len(dati), "columns": len(dati.columns), "output_path": str(percorso_output), "error": ""})
        except Exception as errore:
            log.append({"dataflow_id": dataflow_id, "status": "error", "rows": 0, "columns": 0, "output_path": "", "error": str(errore)})
    return pd.DataFrame(log)


def esegui_download_istat(percorso_log: str | Path = PERCORSO_LOG_DOWNLOAD) -> pd.DataFrame:
    """Scarica i dati ISTAT selezionati e salva il log."""
    prepara_cartelle()
    log = scarica_istat_da_whitelist()
    salva_tabella(log, percorso_log)
    return log


if __name__ == "__main__":
    esegui_download_istat()
