from __future__ import annotations

import pandas as pd

COLONNE_TABELLA_ANNUALE = [
    "anno",
    "indicatore_id",
    "famiglia_definizione",
    "fonte_id",
    "valore",
    "unita",
    "area",
    "note",
]

COLONNE_TABELLA_GESTIONI = [
    "anno",
    "gestione_id",
    "gestione_nome",
    "gruppo_gestione",
    "indicatore_id",
    "fonte_id",
    "valore",
    "unita",
    "note",
]

COLONNE_TABELLA_TERRITORIALE = [
    "anno",
    "livello_territoriale",
    "codice_territorio",
    "nome_territorio",
    "indicatore_id",
    "fonte_id",
    "valore",
    "unita",
    "note",
]


def tabella_annuale_vuota() -> pd.DataFrame:
    """Restituisce la struttura vuota della tabella annuale nazionale."""
    return pd.DataFrame(columns=COLONNE_TABELLA_ANNUALE)


def tabella_gestioni_vuota() -> pd.DataFrame:
    """Restituisce la struttura vuota della tabella per gestione o fondo."""
    return pd.DataFrame(columns=COLONNE_TABELLA_GESTIONI)


def tabella_territoriale_vuota() -> pd.DataFrame:
    """Restituisce la struttura vuota della tabella territoriale."""
    return pd.DataFrame(columns=COLONNE_TABELLA_TERRITORIALE)


def controlla_schema(tabella: pd.DataFrame, colonne_richieste: list[str]) -> None:
    """Controlla che una tabella contenga tutte le colonne richieste."""
    mancanti = [colonna for colonna in colonne_richieste if colonna not in tabella.columns]
    if mancanti:
        raise ValueError(f"Colonne mancanti: {mancanti}")
