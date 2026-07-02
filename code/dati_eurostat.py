from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from italian_our_world_data import fetch_eurostat_data, list_eurostat_dataflows

from utilita import CARTELLA_METADATA, CARTELLA_PROCESSED, CARTELLA_RAW, leggi_csv_opzionale, prepara_cartelle, salva_tabella

PERCORSO_WHITELIST = CARTELLA_METADATA / "whitelist_eurostat.csv"
PERCORSO_CATALOGO = CARTELLA_METADATA / "catalogo_eurostat.csv"
CARTELLA_RAW_EUROSTAT = CARTELLA_RAW / "eurostat"
PERCORSO_LOG_DOWNLOAD = CARTELLA_PROCESSED / "log_download_eurostat.csv"


def esegui_discovery_eurostat(percorso_output: str | Path = PERCORSO_CATALOGO) -> pd.DataFrame:
    prepara_cartelle()
    tabella = list_eurostat_dataflows()
    salva_tabella(tabella, percorso_output)
    return tabella


def interpreta_filtri(testo_filtri: object) -> dict[str, object]:
    if pd.isna(testo_filtri) or str(testo_filtri).strip() == "":
        return {}
    return json.loads(str(testo_filtri))


def scarica_eurostat_da_whitelist(cartella_output: str | Path = CARTELLA_RAW_EUROSTAT) -> pd.DataFrame:
    whitelist = leggi_csv_opzionale(PERCORSO_WHITELIST)
    if whitelist.empty:
        return pd.DataFrame(columns=["dataset", "stato", "righe", "colonne", "percorso_output", "errore"])
    if "stato" in whitelist.columns:
        whitelist = whitelist[whitelist["stato"].fillna("").str.lower().isin({"selezionato", "attivo", "mantieni"})]
    log = []
    for _, riga in whitelist.iterrows():
        dataset = str(riga["dataset"]).strip()
        nome_output = riga.get("nome_output") if pd.notna(riga.get("nome_output")) else dataset
        try:
            dati = fetch_eurostat_data(dataset, filters=interpreta_filtri(riga.get("filtri")), start_period=riga.get("start_period") if pd.notna(riga.get("start_period")) else None, end_period=riga.get("end_period") if pd.notna(riga.get("end_period")) else None)
            percorso_output = Path(cartella_output) / f"{nome_output}.csv"
            salva_tabella(dati, percorso_output)
            log.append({"dataset": dataset, "stato": "ok", "righe": len(dati), "colonne": len(dati.columns), "percorso_output": str(percorso_output), "errore": ""})
        except Exception as errore:
            log.append({"dataset": dataset, "stato": "errore", "righe": 0, "colonne": 0, "percorso_output": "", "errore": str(errore)})
    return pd.DataFrame(log)


def esegui_download_eurostat(percorso_log: str | Path = PERCORSO_LOG_DOWNLOAD) -> pd.DataFrame:
    prepara_cartelle()
    log = scarica_eurostat_da_whitelist()
    salva_tabella(log, percorso_log)
    return log


if __name__ == "__main__":
    esegui_download_eurostat()
