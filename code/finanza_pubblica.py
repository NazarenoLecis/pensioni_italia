from __future__ import annotations

from pathlib import Path

import pandas as pd
from italian_our_world_data import fetch_bdap_data, list_bdap_datasets

from utilita import CARTELLA_METADATA, CARTELLA_PROCESSED, CARTELLA_RAW, leggi_csv_opzionale, prepara_cartelle, salva_tabella

PERCORSO_WHITELIST = CARTELLA_METADATA / "openbdap_dataset_whitelist.csv"
PERCORSO_CATALOGO = CARTELLA_METADATA / "openbdap_catalogue.csv"
CARTELLA_RAW_OPENBDAP = CARTELLA_RAW / "openbdap"
PERCORSO_LOG_DOWNLOAD = CARTELLA_PROCESSED / "openbdap_download_log.csv"


def scopri_catalogo_openbdap(query: str | None = None, righe: int = 200) -> pd.DataFrame:
    """Scarica il catalogo OpenBDAP.

    Serve per trovare dataset su bilancio pubblico, trasferimenti statali,
    rendiconto e voci connesse a INPS e previdenza.
    """
    return list_bdap_datasets(query=query, rows=righe)


def esegui_discovery_openbdap(percorso_output: str | Path = PERCORSO_CATALOGO, query: str | None = None) -> pd.DataFrame:
    """Salva il catalogo OpenBDAP utile per compilare la whitelist."""
    prepara_cartelle()
    tabella = scopri_catalogo_openbdap(query=query)
    salva_tabella(tabella, percorso_output)
    return tabella


def scarica_openbdap_da_whitelist(cartella_output: str | Path = CARTELLA_RAW_OPENBDAP) -> pd.DataFrame:
    """Scarica le risorse OpenBDAP selezionate nella whitelist.

    La whitelist puo' usare dataset_id, resource_id o resource_url. Questo rende
    possibile scaricare sia dataset CKAN standard sia risorse puntuali.
    """
    whitelist = leggi_csv_opzionale(PERCORSO_WHITELIST)
    if whitelist.empty:
        return pd.DataFrame(columns=["dataset_id", "status", "rows", "columns", "output_path", "error"])
    if "status" in whitelist.columns:
        whitelist = whitelist[whitelist["status"].fillna("").str.lower().isin({"selected", "active", "keep"})]

    log = []
    for _, riga in whitelist.iterrows():
        dataset_id = riga.get("dataset_id") if pd.notna(riga.get("dataset_id")) else None
        resource_id = riga.get("resource_id") if pd.notna(riga.get("resource_id")) else None
        resource_url = riga.get("resource_url") if pd.notna(riga.get("resource_url")) else None
        indice_risorsa = int(riga.get("resource_index", 0) or 0)
        formato = riga.get("resource_format") if pd.notna(riga.get("resource_format")) else None
        nome_output = riga.get("output_name") if pd.notna(riga.get("output_name")) else str(dataset_id or resource_id or "openbdap")
        try:
            dati = fetch_bdap_data(dataset_id=dataset_id, resource_id=resource_id, resource_index=indice_risorsa, resource_url=resource_url, resource_format=formato)
            percorso_output = Path(cartella_output) / f"{nome_output}.csv"
            salva_tabella(dati, percorso_output)
            log.append({"dataset_id": dataset_id, "status": "ok", "rows": len(dati), "columns": len(dati.columns), "output_path": str(percorso_output), "error": ""})
        except Exception as errore:
            log.append({"dataset_id": dataset_id, "status": "error", "rows": 0, "columns": 0, "output_path": "", "error": str(errore)})
    return pd.DataFrame(log)


def esegui_download_openbdap(percorso_log: str | Path = PERCORSO_LOG_DOWNLOAD) -> pd.DataFrame:
    """Scarica i dati OpenBDAP selezionati e salva il log."""
    prepara_cartelle()
    log = scarica_openbdap_da_whitelist()
    salva_tabella(log, percorso_log)
    return log


if __name__ == "__main__":
    esegui_download_openbdap()
