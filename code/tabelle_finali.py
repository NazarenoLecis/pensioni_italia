from __future__ import annotations

import pandas as pd

COLONNE_TABELLA_ANNUALE = ["anno", "indicatore_id", "famiglia_definizione", "fonte_id", "valore", "unita", "area", "note"]
COLONNE_TABELLA_GESTIONI = ["anno", "gestione_id", "gestione_nome", "gruppo_gestione", "indicatore_id", "fonte_id", "valore", "unita", "note"]
COLONNE_TABELLA_TERRITORIALE = ["anno", "livello_territoriale", "codice_territorio", "nome_territorio", "indicatore_id", "fonte_id", "valore", "unita", "note"]
COLONNE_TABELLA_FLUSSI = ["anno", "misura", "gestione_id", "sesso", "classe_eta", "indicatore_id", "fonte_id", "valore", "unita", "note"]
COLONNE_TABELLA_EUROPA = ["anno", "paese", "indicatore_id", "definizione", "fonte_id", "valore", "unita", "note"]


def tabella_annuale_vuota() -> pd.DataFrame:
    return pd.DataFrame(columns=COLONNE_TABELLA_ANNUALE)


def tabella_gestioni_vuota() -> pd.DataFrame:
    return pd.DataFrame(columns=COLONNE_TABELLA_GESTIONI)


def tabella_territoriale_vuota() -> pd.DataFrame:
    return pd.DataFrame(columns=COLONNE_TABELLA_TERRITORIALE)


def tabella_flussi_vuota() -> pd.DataFrame:
    return pd.DataFrame(columns=COLONNE_TABELLA_FLUSSI)


def tabella_europa_vuota() -> pd.DataFrame:
    return pd.DataFrame(columns=COLONNE_TABELLA_EUROPA)


def controlla_schema(tabella: pd.DataFrame, colonne_richieste: list[str]) -> None:
    mancanti = [colonna for colonna in colonne_richieste if colonna not in tabella.columns]
    if mancanti:
        raise ValueError(f"Colonne mancanti: {mancanti}")
