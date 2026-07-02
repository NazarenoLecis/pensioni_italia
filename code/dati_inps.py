from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import pandas as pd
from italian_our_world_data import fetch_inps_data, get_inps_dataset_metadata, list_inps_datasets

from utilita import CARTELLA_METADATA, CARTELLA_PROCESSED, CARTELLA_RAW, leggi_csv_opzionale, prepara_cartelle, salva_tabella

USA_METADATA = True
PERCORSO_CANDIDATI = CARTELLA_METADATA / "inps_catalogue_candidates.csv"
PERCORSO_RISORSE = CARTELLA_METADATA / "inps_resource_table.csv"
PERCORSO_WHITELIST = CARTELLA_METADATA / "inps_dataset_whitelist.csv"
CARTELLA_RAW_INPS = CARTELLA_RAW / "inps"
PERCORSO_LOG_DOWNLOAD = CARTELLA_PROCESSED / "inps_download_log.csv"

TERMINI_FALLBACK = (
    "pensioni", "pensionati", "pensione", "vecchiaia", "anzianita", "anticipata",
    "invalidita", "inabilita", "superstiti", "reversibilita", "assegno sociale",
    "invalidita civile", "accompagnamento", "liquidate", "vigenti", "decorrenza",
    "gestione", "fondo", "FPLD", "dipendenti pubblici", "gestione separata",
    "artigiani", "commercianti", "coltivatori diretti", "ENPALS", "INPGI",
    "clero", "fondi speciali", "ex fondi", "GIAS", "trasferimenti", "contributi",
)


def leggi_termini_inps(percorso_termini: str | Path = CARTELLA_METADATA / "inps_search_terms.csv") -> list[str]:
    """Legge i termini usati per trovare dataset INPS sulle pensioni.

    Flow: legge il CSV dei termini, tiene quelli attivi, usa i termini interni se
    il file manca, restituisce una lista ordinata e senza duplicati.
    """
    tabella = leggi_csv_opzionale(percorso_termini)
    if tabella.empty or "term" not in tabella.columns:
        return list(TERMINI_FALLBACK)
    if "include_default" in tabella.columns:
        tabella = tabella[tabella["include_default"].fillna(0).astype(int).eq(1)]
    return sorted({str(termine).strip() for termine in tabella["term"].dropna() if str(termine).strip()})


def trova_termini(testo: str, termini: Iterable[str]) -> list[str]:
    """Restituisce i termini trovati dentro un testo."""
    testo_minuscolo = str(testo).lower()
    return [termine for termine in termini if re.search(re.escape(termine.lower()), testo_minuscolo)]


def scopri_dataset_inps(usa_metadata: bool = USA_METADATA) -> pd.DataFrame:
    """Scopre dataset INPS potenzialmente rilevanti.

    Flow: scarica il catalogo INPS, cerca termini pensionistici negli id, se
    richiesto scarica anche i metadati, restituisce una tabella candidati da
    revisionare prima di popolare la whitelist.
    """
    termini = leggi_termini_inps()
    catalogo = list_inps_datasets()
    righe = []

    for dataset_id in catalogo["dataset_id"].dropna().astype(str):
        metadata = {}
        testo_ricerca = dataset_id
        if usa_metadata:
            try:
                metadata = dict(get_inps_dataset_metadata(dataset_id))
            except Exception as errore:
                metadata = {"metadata_error": str(errore)}
            campi = ("id", "name", "title", "notes", "description", "metadata_error")
            testo_ricerca = " ".join([dataset_id] + [str(metadata.get(campo, "")) for campo in campi])

        termini_trovati = trova_termini(testo_ricerca, termini)
        if termini_trovati:
            righe.append({
                "dataset_id": dataset_id,
                "matched_terms": "; ".join(termini_trovati),
                "title": metadata.get("title") or metadata.get("name"),
                "notes": metadata.get("notes") or metadata.get("description"),
                "resources_count": len(metadata.get("resources", [])) if metadata else pd.NA,
                "metadata_error": metadata.get("metadata_error"),
            })

    return pd.DataFrame(righe)


def esegui_discovery_inps(percorso_output: str | Path = PERCORSO_CANDIDATI) -> pd.DataFrame:
    """Esegue la discovery INPS e salva la tabella dei candidati."""
    prepara_cartelle()
    tabella = scopri_dataset_inps()
    salva_tabella(tabella, percorso_output)
    return tabella


def costruisci_tabella_risorse_inps(percorso_candidati: str | Path = PERCORSO_CANDIDATI) -> pd.DataFrame:
    """Crea una riga per ogni risorsa pubblicata dai dataset candidati."""
    candidati = leggi_csv_opzionale(percorso_candidati)
    righe = []
    for dataset_id in candidati.get("dataset_id", pd.Series(dtype=str)).dropna().astype(str):
        try:
            metadata = dict(get_inps_dataset_metadata(dataset_id))
        except Exception as errore:
            righe.append({"dataset_id": dataset_id, "metadata_error": str(errore)})
            continue
        for indice_risorsa, risorsa in enumerate(metadata.get("resources", []) or []):
            righe.append({
                "dataset_id": dataset_id,
                "resource_index": indice_risorsa,
                "format": risorsa.get("format"),
                "url": risorsa.get("url"),
                "name": risorsa.get("name"),
                "dataset_title": metadata.get("title") or metadata.get("name"),
            })
    return pd.DataFrame(righe)


def esegui_tabella_risorse_inps(percorso_output: str | Path = PERCORSO_RISORSE) -> pd.DataFrame:
    """Salva la tabella delle risorse INPS disponibili."""
    tabella = costruisci_tabella_risorse_inps()
    salva_tabella(tabella, percorso_output)
    return tabella


def scarica_inps_da_whitelist(cartella_output: str | Path = CARTELLA_RAW_INPS) -> pd.DataFrame:
    """Scarica i dataset INPS selezionati nella whitelist."""
    whitelist = leggi_csv_opzionale(PERCORSO_WHITELIST)
    if whitelist.empty:
        return pd.DataFrame(columns=["dataset_id", "status", "rows", "columns", "output_path", "error"])
    if "status" in whitelist.columns:
        whitelist = whitelist[whitelist["status"].fillna("").str.lower().isin({"selected", "active", "keep"})]

    log = []
    for _, riga in whitelist.iterrows():
        dataset_id = str(riga["dataset_id"]).strip()
        indice_risorsa = int(riga.get("resource_index", 0) or 0)
        try:
            dati = fetch_inps_data(dataset_id, resource_index=indice_risorsa)
            percorso_output = Path(cartella_output) / f"{dataset_id}__resource_{indice_risorsa}.csv"
            salva_tabella(dati, percorso_output)
            log.append({"dataset_id": dataset_id, "status": "ok", "rows": len(dati), "columns": len(dati.columns), "output_path": str(percorso_output), "error": ""})
        except Exception as errore:
            log.append({"dataset_id": dataset_id, "status": "error", "rows": 0, "columns": 0, "output_path": "", "error": str(errore)})
    return pd.DataFrame(log)


def esegui_download_inps(percorso_log: str | Path = PERCORSO_LOG_DOWNLOAD) -> pd.DataFrame:
    """Scarica i dataset INPS selezionati e salva il log."""
    prepara_cartelle()
    log = scarica_inps_da_whitelist()
    salva_tabella(log, percorso_log)
    return log


if __name__ == "__main__":
    esegui_discovery_inps()
