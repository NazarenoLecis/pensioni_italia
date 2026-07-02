from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import pandas as pd
from italian_our_world_data import fetch_inps_data, get_inps_dataset_metadata, list_inps_datasets

from utilita import CARTELLA_METADATA, CARTELLA_PROCESSED, CARTELLA_RAW, leggi_csv_opzionale, prepara_cartelle, salva_tabella

USA_METADATA = True
PERCORSO_TERMINI = CARTELLA_METADATA / "termini_ricerca_inps.csv"
PERCORSO_CANDIDATI = CARTELLA_METADATA / "candidati_catalogo_inps.csv"
PERCORSO_RISORSE = CARTELLA_METADATA / "tabella_risorse_inps.csv"
PERCORSO_WHITELIST = CARTELLA_METADATA / "whitelist_inps.csv"
CARTELLA_RAW_INPS = CARTELLA_RAW / "inps"
PERCORSO_LOG_DOWNLOAD = CARTELLA_PROCESSED / "log_download_inps.csv"

TERMINI_FALLBACK = (
    "pensioni", "pensionati", "pensione", "vecchiaia", "anzianita", "anticipata",
    "invalidita", "inabilita", "superstiti", "reversibilita", "assegno sociale",
    "invalidita civile", "accompagnamento", "liquidate", "vigenti", "decorrenza",
    "gestione", "fondo", "FPLD", "dipendenti pubblici", "gestione separata",
    "artigiani", "commercianti", "coltivatori diretti", "ENPALS", "INPGI",
    "clero", "fondi speciali", "ex fondi", "GIAS", "trasferimenti", "contributi",
)


def leggi_termini_inps(percorso_termini: str | Path = PERCORSO_TERMINI) -> list[str]:
    tabella = leggi_csv_opzionale(percorso_termini)
    if tabella.empty or "termine" not in tabella.columns:
        return list(TERMINI_FALLBACK)
    if "includi" in tabella.columns:
        tabella = tabella[tabella["includi"].fillna(0).astype(int).eq(1)]
    return sorted({str(x).strip() for x in tabella["termine"].dropna() if str(x).strip()})


def trova_termini(testo: str, termini: Iterable[str]) -> list[str]:
    testo_minuscolo = str(testo).lower()
    return [termine for termine in termini if re.search(re.escape(termine.lower()), testo_minuscolo)]


def scopri_dataset_inps(usa_metadata: bool = USA_METADATA) -> pd.DataFrame:
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
            righe.append({"dataset_id": dataset_id, "termini_trovati": "; ".join(termini_trovati), "titolo": metadata.get("title") or metadata.get("name"), "note": metadata.get("notes") or metadata.get("description"), "numero_risorse": len(metadata.get("resources", [])) if metadata else pd.NA, "errore_metadata": metadata.get("metadata_error")})
    return pd.DataFrame(righe)


def esegui_discovery_inps(percorso_output: str | Path = PERCORSO_CANDIDATI) -> pd.DataFrame:
    prepara_cartelle()
    tabella = scopri_dataset_inps()
    salva_tabella(tabella, percorso_output)
    return tabella


def costruisci_tabella_risorse_inps(percorso_candidati: str | Path = PERCORSO_CANDIDATI) -> pd.DataFrame:
    candidati = leggi_csv_opzionale(percorso_candidati)
    righe = []
    for dataset_id in candidati.get("dataset_id", pd.Series(dtype=str)).dropna().astype(str):
        try:
            metadata = dict(get_inps_dataset_metadata(dataset_id))
        except Exception as errore:
            righe.append({"dataset_id": dataset_id, "errore_metadata": str(errore)})
            continue
        for indice_risorsa, risorsa in enumerate(metadata.get("resources", []) or []):
            righe.append({"dataset_id": dataset_id, "indice_risorsa": indice_risorsa, "formato": risorsa.get("format"), "url": risorsa.get("url"), "nome": risorsa.get("name"), "titolo_dataset": metadata.get("title") or metadata.get("name")})
    return pd.DataFrame(righe)


def esegui_tabella_risorse_inps(percorso_output: str | Path = PERCORSO_RISORSE) -> pd.DataFrame:
    tabella = costruisci_tabella_risorse_inps()
    salva_tabella(tabella, percorso_output)
    return tabella


def scarica_inps_da_whitelist(cartella_output: str | Path = CARTELLA_RAW_INPS) -> pd.DataFrame:
    whitelist = leggi_csv_opzionale(PERCORSO_WHITELIST)
    if whitelist.empty:
        return pd.DataFrame(columns=["dataset_id", "stato", "righe", "colonne", "percorso_output", "errore"])
    if "stato" in whitelist.columns:
        whitelist = whitelist[whitelist["stato"].fillna("").str.lower().isin({"selezionato", "attivo", "mantieni"})]
    log = []
    for _, riga in whitelist.iterrows():
        dataset_id = str(riga["dataset_id"]).strip()
        indice_risorsa = int(riga.get("indice_risorsa", 0) or 0)
        try:
            dati = fetch_inps_data(dataset_id, resource_index=indice_risorsa)
            percorso_output = Path(cartella_output) / f"{dataset_id}__risorsa_{indice_risorsa}.csv"
            salva_tabella(dati, percorso_output)
            log.append({"dataset_id": dataset_id, "stato": "ok", "righe": len(dati), "colonne": len(dati.columns), "percorso_output": str(percorso_output), "errore": ""})
        except Exception as errore:
            log.append({"dataset_id": dataset_id, "stato": "errore", "righe": 0, "colonne": 0, "percorso_output": "", "errore": str(errore)})
    return pd.DataFrame(log)


def esegui_download_inps(percorso_log: str | Path = PERCORSO_LOG_DOWNLOAD) -> pd.DataFrame:
    prepara_cartelle()
    log = scarica_inps_da_whitelist()
    salva_tabella(log, percorso_log)
    return log


if __name__ == "__main__":
    esegui_discovery_inps()
