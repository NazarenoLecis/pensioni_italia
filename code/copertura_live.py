from __future__ import annotations

from pathlib import Path

import pandas as pd

from costruisci_tabelle_finali import TABELLE_FINALI
from utilita import CARTELLA_FINAL, CARTELLA_METADATA, CARTELLA_PROCESSED, leggi_csv_opzionale, prepara_cartelle, salva_tabella

PERCORSO_DOMANDE = CARTELLA_METADATA / "domande_live.csv"
PERCORSO_OUTPUT = CARTELLA_FINAL / "tabella_copertura_live.csv"
PERCORSO_LOG = CARTELLA_PROCESSED / "log_copertura_live.csv"

COLONNE_DOMANDE = [
    "domanda_id",
    "tema",
    "domanda",
    "tabella_finale",
    "indicatore_richiesto",
    "fonte_principale",
    "note",
]


def dividi_indicatori(valore: object) -> list[str]:
    testo = "" if pd.isna(valore) else str(valore).strip()
    if testo == "" or testo.lower() in {"n/a", "na", "metodologico"}:
        return []
    return [parte.strip() for parte in testo.split(";") if parte.strip()]


def leggi_domande_live(percorso_domande: str | Path = PERCORSO_DOMANDE) -> pd.DataFrame:
    domande = leggi_csv_opzionale(percorso_domande)
    if domande.empty:
        return pd.DataFrame(columns=COLONNE_DOMANDE)
    colonne_mancanti = [colonna for colonna in COLONNE_DOMANDE if colonna not in domande.columns]
    if colonne_mancanti:
        raise ValueError(f"Colonne mancanti in domande_live.csv: {colonne_mancanti}")
    return domande[COLONNE_DOMANDE].copy()


def verifica_indicatori(tabella: pd.DataFrame, indicatori: list[str]) -> tuple[bool, str]:
    if not indicatori:
        return True, "domanda metodologica o non legata a un indicatore singolo"
    if tabella.empty:
        return False, "tabella finale vuota"
    if "indicatore_id" not in tabella.columns:
        return False, "colonna indicatore_id assente"
    presenti = set(tabella["indicatore_id"].dropna().astype(str))
    mancanti = [indicatore for indicatore in indicatori if indicatore not in presenti]
    if mancanti:
        return False, "indicatori mancanti: " + "; ".join(mancanti)
    return True, "indicatori presenti"


def valuta_domanda(riga: pd.Series) -> dict[str, object]:
    nome_tabella = str(riga.get("tabella_finale", "")).strip()
    indicatori = dividi_indicatori(riga.get("indicatore_richiesto"))

    if nome_tabella == "" or nome_tabella.lower() in {"n/a", "metodologico"}:
        stato = "metodologica"
        dettaglio = "nessuna tabella finale richiesta"
    elif nome_tabella not in TABELLE_FINALI:
        stato = "non_mappata"
        dettaglio = f"tabella finale non registrata: {nome_tabella}"
    else:
        tabella = leggi_csv_opzionale(TABELLE_FINALI[nome_tabella])
        coperta, dettaglio = verifica_indicatori(tabella, indicatori)
        stato = "coperta" if coperta and not tabella.empty else "mancano_dati"
        if coperta and tabella.empty and not indicatori:
            stato = "metodologica"

    note = str(riga.get("note", "")).strip()
    note_output = dettaglio if note == "" else f"{note} | {dettaglio}"
    return {
        "domanda_id": riga.get("domanda_id"),
        "tema": riga.get("tema"),
        "domanda": riga.get("domanda"),
        "stato": stato,
        "tabella_finale": nome_tabella,
        "indicatore_richiesto": riga.get("indicatore_richiesto"),
        "fonte_principale": riga.get("fonte_principale"),
        "note": note_output,
    }


def costruisci_copertura_live(percorso_domande: str | Path = PERCORSO_DOMANDE) -> pd.DataFrame:
    domande = leggi_domande_live(percorso_domande)
    if domande.empty:
        return pd.DataFrame(
            columns=[
                "domanda_id",
                "tema",
                "domanda",
                "stato",
                "tabella_finale",
                "indicatore_richiesto",
                "fonte_principale",
                "note",
            ]
        )
    return pd.DataFrame([valuta_domanda(riga) for _, riga in domande.iterrows()])


def esegui_copertura_live(
    percorso_output: str | Path = PERCORSO_OUTPUT,
    percorso_log: str | Path = PERCORSO_LOG,
) -> pd.DataFrame:
    prepara_cartelle()
    copertura = costruisci_copertura_live()
    salva_tabella(copertura, percorso_output)
    log = copertura.groupby("stato", dropna=False).size().reset_index(name="domande") if not copertura.empty else pd.DataFrame(columns=["stato", "domande"])
    salva_tabella(log, percorso_log)
    return copertura


if __name__ == "__main__":
    esegui_copertura_live()
