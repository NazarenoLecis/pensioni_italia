from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from italian_our_world_data import fetch_eurostat_data, list_eurostat_dataflows

from utilita import CARTELLA_METADATA, CARTELLA_PROCESSED, CARTELLA_RAW, leggi_csv_opzionale, prepara_cartelle, salva_tabella

PERCORSO_WHITELIST = CARTELLA_METADATA / "eurostat_whitelist.csv"
PERCORSO_CATALOGO = CARTELLA_METADATA / "eurostat_catalogue.csv"
CARTELLA_RAW_EUROSTAT = CARTELLA_RAW / "eurostat"
PERCORSO_LOG_DOWNLOAD = CARTELLA_PROCESSED / "eurostat_download_log.csv"


def esegui_discovery_eurostat(percorso_output: str | Path = PERCORSO_CATALOGO) -> pd.DataFrame:
    """Scarica il catalogo Eurostat e lo salva in metadata."""
    prepara_cartelle()
    tabella = list_eurostat_dataflows()
    salva_tabella(tabella, percorso_output)
    return tabella


def interpreta_filtri(testo_filtri: object) -> dict[str, object]:
    """Converte i filtri Eurostat da testo JSON a dizionario Python."""
    if pd.isna(testo_filtri) or str(testo_filtri).strip() == "":
        return {}
    return json.loads(str(testo_filtri))


def scarica_eurostat_da_whitelist(cartella_output: str | Path = CARTELLA_RAW_EUROSTAT) -> pd.DataFrame:
    """Scarica i dataset Eurostat selezionati nella whitelist."""
    whitelist = leggi_csv_opzionale(PERCORSO_WHITELIST)
    if whitelist.empty:
        return pd.DataFrame(columns=["dataset", "status", "rows", "columns", "output_path", "error"])
    if "status" in whitelist.columns:
        whitelist = whitelist[whitelist["status"].fillna("").str.lower().isin({"selected", "active", "keep"})]

    log = []
    for _, riga in whitelist.iterrows():
        dataset = str(riga["dataset"]).strip()
        nome_output = riga.get("output_name") if pd.notna(riga.get("output_name")) else dataset
        try:
            dati = fetch_eurostat_data(
                dataset,
                filters=interpreta_filtri(riga.get("filters")),
                start_period=riga.get("start_period") if pd.notna(riga.get("start_period")) else None,
                end_period=riga.get("end_period") if pd.notna(riga.get("end_period")) else None,
            )
            percorso_output = Path(cartella_output) / f"{nome_output}.csv"
            salva_tabella(dati, percorso_output)
            log.append({"dataset": dataset, "status": "ok", "rows": len(dati), "columns": len(dati.columns), "output_path": str(percorso_output), "error": ""})
        except Exception as errore:
            log.append({"dataset": dataset, "status": "error", "rows": 0, "columns": 0, "output_path": "", "error": str(errore)})
    return pd.DataFrame(log)


def esegui_download_eurostat(percorso_log: str | Path = PERCORSO_LOG_DOWNLOAD) -> pd.DataFrame:
    """Scarica i dati Eurostat selezionati e salva il log."""
    prepara_cartelle()
    log = scarica_eurostat_da_whitelist()
    salva_tabella(log, percorso_log)
    return log


if __name__ == "__main__":
    esegui_download_eurostat()
