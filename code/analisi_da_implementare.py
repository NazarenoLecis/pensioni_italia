from __future__ import annotations

from pathlib import Path

import pandas as pd

from costruisci_tabelle_finali import TABELLE_FINALI
from dataset_attesi import output_analitici_registrati, separa_valori
from utilita import CARTELLA_METADATA, leggi_csv_opzionale

PERCORSO_ANALISI = CARTELLA_METADATA / "analisi_da_implementare.csv"
PERCORSO_DATASET = CARTELLA_METADATA / "dataset_attesi.csv"
PERCORSO_INDICATORI = CARTELLA_METADATA / "definizioni_indicatori.csv"

COLONNE_ANALISI = [
    "analisi_id",
    "area",
    "domanda_analitica",
    "motivazione",
    "indicatori_richiesti",
    "dataset_logici",
    "tabelle_finali",
    "priorita",
    "stato",
    "note",
]

STATI_AMMESSI = {"da_implementare", "in_corso", "implementata", "sospesa"}
PRIORITA_AMMESSE = {"alta", "media", "bassa"}


def leggi_analisi_da_implementare(percorso: str | Path = PERCORSO_ANALISI) -> pd.DataFrame:
    """Legge la matrice delle analisi pensionistiche da implementare."""
    return leggi_csv_opzionale(percorso)


def controlla_analisi_da_implementare() -> list[dict[str, object]]:
    """Controlla coerenza tra analisi, indicatori, dataset logici e output registrati."""
    analisi = leggi_analisi_da_implementare()
    risultati: list[dict[str, object]] = []

    if analisi.empty:
        return [
            {
                "tabella": "analisi_da_implementare",
                "controllo": "presenza_dati",
                "stato": "errore",
                "dettaglio": "analisi_da_implementare.csv mancante o vuoto",
            }
        ]

    colonne_mancanti = [colonna for colonna in COLONNE_ANALISI if colonna not in analisi.columns]
    risultati.append(
        {
            "tabella": "analisi_da_implementare",
            "controllo": "colonne_attese",
            "stato": "errore" if colonne_mancanti else "ok",
            "dettaglio": "; ".join(colonne_mancanti),
        }
    )
    if colonne_mancanti:
        return risultati

    dataset = leggi_csv_opzionale(PERCORSO_DATASET)
    dataset_validi = set(dataset["dataset_logico_id"].dropna().astype(str)) if "dataset_logico_id" in dataset.columns else set()
    dataset_richiesti = {
        dataset_id
        for valore in analisi["dataset_logici"]
        for dataset_id in separa_valori(valore)
    }
    dataset_non_registrati = sorted(dataset_richiesti - dataset_validi)
    risultati.append(
        {
            "tabella": "analisi_da_implementare",
            "controllo": "dataset_logici_registrati",
            "stato": "errore" if dataset_non_registrati else "ok",
            "dettaglio": "; ".join(dataset_non_registrati),
        }
    )

    indicatori = leggi_csv_opzionale(PERCORSO_INDICATORI)
    indicatori_validi = set(indicatori["indicatore_id"].dropna().astype(str)) if "indicatore_id" in indicatori.columns else set()
    indicatori_richiesti = {
        indicatore
        for valore in analisi["indicatori_richiesti"]
        for indicatore in separa_valori(valore)
    }
    indicatori_non_registrati = sorted(indicatori_richiesti - indicatori_validi)
    risultati.append(
        {
            "tabella": "analisi_da_implementare",
            "controllo": "indicatori_registrati",
            "stato": "errore" if indicatori_non_registrati else "ok",
            "dettaglio": "; ".join(indicatori_non_registrati),
        }
    )

    output_validi = set(TABELLE_FINALI) | output_analitici_registrati()
    output_richiesti = {
        output_id
        for valore in analisi["tabelle_finali"]
        for output_id in separa_valori(valore)
    }
    output_non_registrati = sorted(output_richiesti - output_validi)
    risultati.append(
        {
            "tabella": "analisi_da_implementare",
            "controllo": "output_registrati",
            "stato": "errore" if output_non_registrati else "ok",
            "dettaglio": "; ".join(output_non_registrati),
        }
    )

    stati_non_ammessi = sorted(set(analisi["stato"].dropna().astype(str)) - STATI_AMMESSI)
    risultati.append(
        {
            "tabella": "analisi_da_implementare",
            "controllo": "stato_ammesso",
            "stato": "errore" if stati_non_ammessi else "ok",
            "dettaglio": "; ".join(stati_non_ammessi),
        }
    )

    priorita_non_ammessa = sorted(set(analisi["priorita"].dropna().astype(str)) - PRIORITA_AMMESSE)
    risultati.append(
        {
            "tabella": "analisi_da_implementare",
            "controllo": "priorita_ammessa",
            "stato": "errore" if priorita_non_ammessa else "ok",
            "dettaglio": "; ".join(priorita_non_ammessa),
        }
    )

    duplicati = int(analisi["analisi_id"].duplicated().sum())
    risultati.append(
        {
            "tabella": "analisi_da_implementare",
            "controllo": "analisi_id_univoco",
            "stato": "errore" if duplicati else "ok",
            "dettaglio": duplicati,
        }
    )

    return risultati
