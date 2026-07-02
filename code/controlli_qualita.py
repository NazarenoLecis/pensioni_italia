from __future__ import annotations

from pathlib import Path

import pandas as pd

from tabelle_finali import COLONNE_TABELLA_ANNUALE, COLONNE_TABELLA_EUROPA, COLONNE_TABELLA_FLUSSI, COLONNE_TABELLA_GESTIONI, COLONNE_TABELLA_TERRITORIALE
from utilita import CARTELLA_FINAL, CARTELLA_PROCESSED, leggi_csv_opzionale, prepara_cartelle, salva_tabella

PERCORSO_LOG_QUALITA = CARTELLA_PROCESSED / "log_controlli_qualita.csv"
TABELLE_DA_CONTROLLARE = {
    "tabella_annuale_pensioni": (CARTELLA_FINAL / "tabella_annuale_pensioni.csv", COLONNE_TABELLA_ANNUALE),
    "tabella_gestioni": (CARTELLA_FINAL / "tabella_gestioni.csv", COLONNE_TABELLA_GESTIONI),
    "tabella_territoriale": (CARTELLA_FINAL / "tabella_territoriale.csv", COLONNE_TABELLA_TERRITORIALE),
    "tabella_flussi_pensionamento": (CARTELLA_FINAL / "tabella_flussi_pensionamento.csv", COLONNE_TABELLA_FLUSSI),
    "tabella_confronto_europeo": (CARTELLA_FINAL / "tabella_confronto_europeo.csv", COLONNE_TABELLA_EUROPA),
}


def controlla_tabella(nome_tabella: str, percorso: str | Path, colonne_attese: list[str]) -> list[dict[str, object]]:
    tabella = leggi_csv_opzionale(percorso)
    risultati: list[dict[str, object]] = []
    if tabella.empty:
        return [{"tabella": nome_tabella, "controllo": "presenza_dati", "stato": "avviso", "dettaglio": "tabella mancante o vuota"}]
    colonne_mancanti = [colonna for colonna in colonne_attese if colonna not in tabella.columns]
    risultati.append({"tabella": nome_tabella, "controllo": "colonne_attese", "stato": "errore" if colonne_mancanti else "ok", "dettaglio": "; ".join(colonne_mancanti)})
    duplicati = int(tabella.duplicated().sum())
    risultati.append({"tabella": nome_tabella, "controllo": "duplicati", "stato": "avviso" if duplicati else "ok", "dettaglio": duplicati})
    if "anno" in tabella.columns:
        anni_non_validi = int(pd.to_numeric(tabella["anno"], errors="coerce").isna().sum())
        risultati.append({"tabella": nome_tabella, "controllo": "anno_valido", "stato": "avviso" if anni_non_validi else "ok", "dettaglio": anni_non_validi})
    if "valore" in tabella.columns:
        valori_non_validi = int(pd.to_numeric(tabella["valore"], errors="coerce").isna().sum())
        risultati.append({"tabella": nome_tabella, "controllo": "valore_numerico", "stato": "avviso" if valori_non_validi else "ok", "dettaglio": valori_non_validi})
    return risultati


def esegui_controlli_qualita(percorso_log: str | Path = PERCORSO_LOG_QUALITA) -> pd.DataFrame:
    prepara_cartelle()
    righe: list[dict[str, object]] = []
    for nome_tabella, (percorso, colonne) in TABELLE_DA_CONTROLLARE.items():
        righe.extend(controlla_tabella(nome_tabella, percorso, colonne))
    log = pd.DataFrame(righe)
    salva_tabella(log, percorso_log)
    return log


if __name__ == "__main__":
    esegui_controlli_qualita()
