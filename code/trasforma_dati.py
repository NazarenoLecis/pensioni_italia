from __future__ import annotations

from pathlib import Path

import pandas as pd

from costruisci_tabelle_finali import inizializza_tabelle_finali
from utilita import CARTELLA_FINAL, CARTELLA_PROCESSED, leggi_csv_opzionale, prepara_cartelle, salva_tabella

PERCORSO_LOG_TRASFORMAZIONE = CARTELLA_PROCESSED / "log_trasformazione_dati.csv"
PERCORSO_TABELLA_ANNUALE = CARTELLA_FINAL / "tabella_annuale_pensioni.csv"
PERCORSO_TABELLA_GESTIONI = CARTELLA_FINAL / "tabella_gestioni.csv"
PERCORSO_TABELLA_TERRITORIALE = CARTELLA_FINAL / "tabella_territoriale.csv"
PERCORSO_TABELLA_FLUSSI = CARTELLA_FINAL / "tabella_flussi_pensionamento.csv"
PERCORSO_TABELLA_EUROPA = CARTELLA_FINAL / "tabella_confronto_europeo.csv"


def normalizza_colonne(tabella: pd.DataFrame) -> pd.DataFrame:
    """Rende i nomi colonna piu' stabili per le trasformazioni successive."""
    risultato = tabella.copy()
    risultato.columns = [str(colonna).strip().lower().replace(" ", "_") for colonna in risultato.columns]
    return risultato


def aggiungi_riga_log(log: list[dict[str, object]], tabella: str, stato: str, righe: int, note: str = "") -> None:
    """Aggiunge una riga al log della trasformazione."""
    log.append({"tabella": tabella, "stato": stato, "righe": righe, "note": note})


def costruisci_tabelle_da_fonti_grezze(percorso_log: str | Path = PERCORSO_LOG_TRASFORMAZIONE) -> pd.DataFrame:
    """Costruisce le tabelle finali a partire dai dati grezzi disponibili.

    Questa funzione prepara il punto unico in cui collegare le pulizie specifiche
    per fonte. Se le funzioni specifiche non sono ancora state completate,
    inizializza comunque le tabelle finali vuote e scrive un log esplicito.
    """
    prepara_cartelle()
    inizializza_tabelle_finali()
    log: list[dict[str, object]] = []

    for nome_tabella, percorso in {
        "tabella_annuale_pensioni": PERCORSO_TABELLA_ANNUALE,
        "tabella_gestioni": PERCORSO_TABELLA_GESTIONI,
        "tabella_territoriale": PERCORSO_TABELLA_TERRITORIALE,
        "tabella_flussi_pensionamento": PERCORSO_TABELLA_FLUSSI,
        "tabella_confronto_europeo": PERCORSO_TABELLA_EUROPA,
    }.items():
        tabella = leggi_csv_opzionale(percorso)
        aggiungi_riga_log(log, nome_tabella, "inizializzata", len(tabella), "tabella pronta per trasformazioni specifiche")

    tabella_log = pd.DataFrame(log)
    salva_tabella(tabella_log, percorso_log)
    return tabella_log


if __name__ == "__main__":
    costruisci_tabelle_da_fonti_grezze()
