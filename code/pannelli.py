from __future__ import annotations

import pandas as pd

COLONNE_PANNELLO_ANNUALE = [
    "anno",
    "indicatore_id",
    "famiglia_definizione",
    "fonte_id",
    "valore",
    "unita",
    "area",
    "note",
]

COLONNE_PANNELLO_GESTIONI = [
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

COLONNE_PANNELLO_TERRITORIALE = [
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


def pannello_annuale_vuoto() -> pd.DataFrame:
    """Restituisce il template vuoto del pannello annuale nazionale."""
    return pd.DataFrame(columns=COLONNE_PANNELLO_ANNUALE)


def pannello_gestioni_vuoto() -> pd.DataFrame:
    """Restituisce il template vuoto del pannello per gestione o fondo."""
    return pd.DataFrame(columns=COLONNE_PANNELLO_GESTIONI)


def pannello_territoriale_vuoto() -> pd.DataFrame:
    """Restituisce il template vuoto del pannello territoriale."""
    return pd.DataFrame(columns=COLONNE_PANNELLO_TERRITORIALE)


def controlla_schema(tabella: pd.DataFrame, colonne_richieste: list[str]) -> None:
    """Controlla che una tabella contenga tutte le colonne richieste."""
    mancanti = [colonna for colonna in colonne_richieste if colonna not in tabella.columns]
    if mancanti:
        raise ValueError(f"Colonne mancanti: {mancanti}")
