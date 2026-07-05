from __future__ import annotations

from pathlib import Path

import pandas as pd

from costruisci_tabelle_finali import TABELLE_FINALI
from tabelle_finali import SCHEMI_TABELLE_FINALI
from utilita import CARTELLA_PROCESSED, leggi_csv_opzionale, prepara_cartelle, salva_tabella

PERCORSO_LOG_QUALITA = CARTELLA_PROCESSED / "log_controlli_qualita.csv"
TABELLE_DA_CONTROLLARE = {
    nome_tabella: (percorso, SCHEMI_TABELLE_FINALI[nome_tabella])
    for nome_tabella, percorso in TABELLE_FINALI.items()
}


def controlla_tabella(nome_tabella: str, percorso: str | Path, colonne_attese: list[str]) -> list[dict[str, object]]:
    tabella = leggi_csv_opzionale(percorso)
    risultati: list[dict[str, object]] = []
    if tabella.empty:
        return [
            {
                "tabella": nome_tabella,
                "controllo": "presenza_dati",
                "stato": "avviso",
                "dettaglio": "tabella mancante o vuota",
            }
        ]

    colonne_mancanti = [colonna for colonna in colonne_attese if colonna not in tabella.columns]
    risultati.append(
        {
            "tabella": nome_tabella,
            "controllo": "colonne_attese",
            "stato": "errore" if colonne_mancanti else "ok",
            "dettaglio": "; ".join(colonne_mancanti),
        }
    )

    duplicati = int(tabella.duplicated().sum())
    risultati.append(
        {
            "tabella": nome_tabella,
            "controllo": "duplicati",
            "stato": "avviso" if duplicati else "ok",
            "dettaglio": duplicati,
        }
    )

    if "anno" in tabella.columns:
        anni_non_validi = int(pd.to_numeric(tabella["anno"], errors="coerce").isna().sum())
        risultati.append(
            {
                "tabella": nome_tabella,
                "controllo": "anno_valido",
                "stato": "avviso" if anni_non_validi else "ok",
                "dettaglio": anni_non_validi,
            }
        )

    if "valore" in tabella.columns:
        valori_non_validi = int(pd.to_numeric(tabella["valore"], errors="coerce").isna().sum())
        risultati.append(
            {
                "tabella": nome_tabella,
                "controllo": "valore_numerico",
                "stato": "avviso" if valori_non_validi else "ok",
                "dettaglio": valori_non_validi,
            }
        )

    for colonna_identificativa in ["fonte_id", "indicatore_id"]:
        if colonna_identificativa in tabella.columns:
            mancanti = int(tabella[colonna_identificativa].isna().sum())
            risultati.append(
                {
                    "tabella": nome_tabella,
                    "controllo": f"{colonna_identificativa}_presente",
                    "stato": "avviso" if mancanti else "ok",
                    "dettaglio": mancanti,
                }
            )

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
