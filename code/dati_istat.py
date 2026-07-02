from __future__ import annotations

from pathlib import Path

import pandas as pd
from italian_our_world_data import fetch_istat_data, list_istat_dataflows

from utilita import CARTELLA_METADATA, CARTELLA_PROCESSED, CARTELLA_RAW, leggi_csv_opzionale, prepara_cartelle, salva_tabella

PERCORSO_WHITELIST = CARTELLA_METADATA / "whitelist_istat.csv"
PERCORSO_CATALOGO = CARTELLA_METADATA / "catalogo_istat.csv"
CARTELLA_RAW_ISTAT = CARTELLA_RAW / "istat"
PERCORSO_LOG_DOWNLOAD = CARTELLA_PROCESSED / "log_download_istat.csv"


def esegui_discovery_istat(percorso_output: str | Path = PERCORSO_CATALOGO) -> pd.DataFrame:
    prepara_cartelle()
    tabella = list_istat_dataflows()
    salva_tabella(tabella, percorso_output)
    return tabella


def scarica_istat_da_whitelist(cartella_output: str | Path = CARTELLA_RAW_ISTAT) -> pd.DataFrame:
    whitelist = leggi_csv_opzionale(PERCORSO_WHITELIST)
    if whitelist.empty:
        return pd.DataFrame(columns=["dataflow_id", "stato", "righe", "colonne", "percorso_output", "errore"])
    if "stato" in whitelist.columns:
        whitelist = whitelist[whitelist["stato"].fillna("").str.lower().isin({"selezionato", "attivo", "mantieni"})]
    log = []
    for _, riga in whitelist.iterrows():
        dataflow_id = str(riga["dataflow_id"]).strip()
        key = str(riga.get("key", "")).strip()
        start_period = riga.get("start_period") if pd.notna(riga.get("start_period")) else None
        end_period = riga.get("end_period") if pd.notna(riga.get("end_period")) else None
        nome_output = riga.get("nome_output") if pd.notna(riga.get("nome_output")) else dataflow_id
        try:
            dati = fetch_istat_data(dataflow_id, key=key, start_period=start_period, end_period=end_period)
            percorso_output = Path(cartella_output) / f"{nome_output}.csv"
            salva_tabella(dati, percorso_output)
            log.append({"dataflow_id": dataflow_id, "stato": "ok", "righe": len(dati), "colonne": len(dati.columns), "percorso_output": str(percorso_output), "errore": ""})
        except Exception as errore:
            log.append({"dataflow_id": dataflow_id, "stato": "errore", "righe": 0, "colonne": 0, "percorso_output": "", "errore": str(errore)})
    return pd.DataFrame(log)


def esegui_download_istat(percorso_log: str | Path = PERCORSO_LOG_DOWNLOAD) -> pd.DataFrame:
    prepara_cartelle()
    log = scarica_istat_da_whitelist()
    salva_tabella(log, percorso_log)
    return log


if __name__ == "__main__":
    esegui_download_istat()
