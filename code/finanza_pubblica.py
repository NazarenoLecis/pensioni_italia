from __future__ import annotations

from pathlib import Path

import pandas as pd
from italian_our_world_data import fetch_bdap_data, list_bdap_datasets

from utilita import CARTELLA_METADATA, CARTELLA_PROCESSED, CARTELLA_RAW, leggi_csv_opzionale, prepara_cartelle, salva_tabella

PERCORSO_WHITELIST = CARTELLA_METADATA / "whitelist_openbdap.csv"
PERCORSO_CATALOGO = CARTELLA_METADATA / "catalogo_openbdap.csv"
CARTELLA_RAW_OPENBDAP = CARTELLA_RAW / "openbdap"
PERCORSO_LOG_DOWNLOAD = CARTELLA_PROCESSED / "log_download_openbdap.csv"


def scopri_catalogo_openbdap(query: str | None = None, righe: int = 200) -> pd.DataFrame:
    return list_bdap_datasets(query=query, rows=righe)


def esegui_discovery_openbdap(percorso_output: str | Path = PERCORSO_CATALOGO, query: str | None = None) -> pd.DataFrame:
    prepara_cartelle()
    tabella = scopri_catalogo_openbdap(query=query)
    salva_tabella(tabella, percorso_output)
    return tabella


def scarica_openbdap_da_whitelist(cartella_output: str | Path = CARTELLA_RAW_OPENBDAP) -> pd.DataFrame:
    whitelist = leggi_csv_opzionale(PERCORSO_WHITELIST)
    if whitelist.empty:
        return pd.DataFrame(columns=["dataset_id", "stato", "righe", "colonne", "percorso_output", "errore"])
    if "stato" in whitelist.columns:
        whitelist = whitelist[whitelist["stato"].fillna("").str.lower().isin({"selezionato", "attivo", "mantieni"})]
    log = []
    for _, riga in whitelist.iterrows():
        dataset_id = riga.get("dataset_id") if pd.notna(riga.get("dataset_id")) else None
        resource_id = riga.get("resource_id") if pd.notna(riga.get("resource_id")) else None
        url_risorsa = riga.get("url_risorsa") if pd.notna(riga.get("url_risorsa")) else None
        indice_risorsa = int(riga.get("indice_risorsa", 0) or 0)
        formato = riga.get("formato_risorsa") if pd.notna(riga.get("formato_risorsa")) else None
        nome_output = riga.get("nome_output") if pd.notna(riga.get("nome_output")) else str(dataset_id or resource_id or "openbdap")
        try:
            dati = fetch_bdap_data(dataset_id=dataset_id, resource_id=resource_id, resource_index=indice_risorsa, resource_url=url_risorsa, resource_format=formato)
            percorso_output = Path(cartella_output) / f"{nome_output}.csv"
            salva_tabella(dati, percorso_output)
            log.append({"dataset_id": dataset_id, "stato": "ok", "righe": len(dati), "colonne": len(dati.columns), "percorso_output": str(percorso_output), "errore": ""})
        except Exception as errore:
            log.append({"dataset_id": dataset_id, "stato": "errore", "righe": 0, "colonne": 0, "percorso_output": "", "errore": str(errore)})
    return pd.DataFrame(log)


def esegui_download_openbdap(percorso_log: str | Path = PERCORSO_LOG_DOWNLOAD) -> pd.DataFrame:
    prepara_cartelle()
    log = scarica_openbdap_da_whitelist()
    salva_tabella(log, percorso_log)
    return log


if __name__ == "__main__":
    esegui_download_openbdap()
