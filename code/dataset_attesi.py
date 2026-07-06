from __future__ import annotations

from pathlib import Path

import pandas as pd

from costruisci_tabelle_finali import TABELLE_FINALI
from utilita import CARTELLA_METADATA, leggi_csv_opzionale

PERCORSO_DATASET_ATTESI = CARTELLA_METADATA / "dataset_attesi.csv"
PERCORSO_FONTI = CARTELLA_METADATA / "registro_fonti.csv"
PERCORSO_INDICATORI = CARTELLA_METADATA / "definizioni_indicatori.csv"
PERCORSO_OUTPUT_ANALITICI = CARTELLA_METADATA / "output_analitici.csv"

COLONNE_DATASET_ATTESI = [
    "dataset_logico_id",
    "fonte_id",
    "ente",
    "ambito",
    "perimetro",
    "tabelle_finali",
    "indicatori",
    "frequenza",
    "stato",
    "note",
]


def separa_valori(valore: object) -> list[str]:
    """Divide campi separati da punto e virgola ignorando vuoti."""
    if pd.isna(valore):
        return []
    return [parte.strip() for parte in str(valore).split(";") if parte.strip()]


def leggi_dataset_attesi(percorso: str | Path = PERCORSO_DATASET_ATTESI) -> pd.DataFrame:
    """Legge il catalogo dei dataset logici attesi."""
    return leggi_csv_opzionale(percorso)


def output_analitici_registrati() -> set[str]:
    """Restituisce gli output analitici registrati in metadata/output_analitici.csv."""
    output = leggi_csv_opzionale(PERCORSO_OUTPUT_ANALITICI)
    if output.empty or "output_id" not in output.columns:
        return set()
    return set(output["output_id"].dropna().astype(str))


def controlla_dataset_attesi() -> list[dict[str, object]]:
    """Controlla coerenza tra dataset attesi, fonti, indicatori e output."""
    dataset = leggi_dataset_attesi()
    risultati: list[dict[str, object]] = []

    if dataset.empty:
        return [
            {
                "tabella": "dataset_attesi",
                "controllo": "presenza_dati",
                "stato": "errore",
                "dettaglio": "catalogo dataset_attesi.csv mancante o vuoto",
            }
        ]

    colonne_mancanti = [colonna for colonna in COLONNE_DATASET_ATTESI if colonna not in dataset.columns]
    risultati.append(
        {
            "tabella": "dataset_attesi",
            "controllo": "colonne_attese",
            "stato": "errore" if colonne_mancanti else "ok",
            "dettaglio": "; ".join(colonne_mancanti),
        }
    )
    if colonne_mancanti:
        return risultati

    fonti = leggi_csv_opzionale(PERCORSO_FONTI)
    fonte_id_validi = set(fonti["fonte_id"].dropna().astype(str)) if "fonte_id" in fonti.columns else set()
    fonti_non_registrate = sorted(set(dataset["fonte_id"].dropna().astype(str)) - fonte_id_validi)
    risultati.append(
        {
            "tabella": "dataset_attesi",
            "controllo": "fonti_registrate",
            "stato": "errore" if fonti_non_registrate else "ok",
            "dettaglio": "; ".join(fonti_non_registrate),
        }
    )

    indicatori = leggi_csv_opzionale(PERCORSO_INDICATORI)
    indicatori_validi = set(indicatori["indicatore_id"].dropna().astype(str)) if "indicatore_id" in indicatori.columns else set()
    indicatori_richiesti = {
        indicatore
        for valore in dataset["indicatori"]
        for indicatore in separa_valori(valore)
    }
    indicatori_non_registrati = sorted(indicatori_richiesti - indicatori_validi)
    risultati.append(
        {
            "tabella": "dataset_attesi",
            "controllo": "indicatori_registrati",
            "stato": "errore" if indicatori_non_registrati else "ok",
            "dettaglio": "; ".join(indicatori_non_registrati),
        }
    )

    output_validi = set(TABELLE_FINALI) | output_analitici_registrati()
    output_richiesti = {
        tabella
        for valore in dataset["tabelle_finali"]
        for tabella in separa_valori(valore)
    }
    output_non_registrati = sorted(output_richiesti - output_validi)
    risultati.append(
        {
            "tabella": "dataset_attesi",
            "controllo": "output_registrati",
            "stato": "errore" if output_non_registrati else "ok",
            "dettaglio": "; ".join(output_non_registrati),
        }
    )

    duplicati = int(dataset["dataset_logico_id"].duplicated().sum())
    risultati.append(
        {
            "tabella": "dataset_attesi",
            "controllo": "dataset_logico_id_univoco",
            "stato": "errore" if duplicati else "ok",
            "dettaglio": duplicati,
        }
    )

    return risultati
