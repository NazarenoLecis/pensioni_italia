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

COLONNE_TABELLA_FLUSSI = [
    "anno",
    "misura",
    "gestione_id",
    "sesso",
    "classe_eta",
    "indicatore_id",
    "fonte_id",
    "valore",
    "unita",
    "note",
]

COLONNE_TABELLA_EUROPA = [
    "anno",
    "paese",
    "indicatore_id",
    "definizione",
    "fonte_id",
    "valore",
    "unita",
    "note",
]

COLONNE_TABELLA_DISTRIBUZIONE = [
    "anno",
    "popolazione",
    "classe_importo",
    "classe_eta",
    "sesso",
    "territorio",
    "indicatore_id",
    "fonte_id",
    "valore",
    "unita",
    "note",
]

COLONNE_TABELLA_DEMOGRAFIA_LAVORO = [
    "anno",
    "area",
    "classe_eta",
    "sesso",
    "scenario",
    "indicatore_id",
    "fonte_id",
    "valore",
    "unita",
    "note",
]

COLONNE_TABELLA_PREVIDENZA_COMPLEMENTARE = [
    "anno",
    "paese",
    "forma_pensionistica",
    "indicatore_id",
    "fonte_id",
    "valore",
    "unita",
    "note",
]

COLONNE_TABELLA_PARAMETRI = [
    "anno",
    "parametro_id",
    "sistema",
    "fonte_id",
    "valore",
    "unita",
    "note",
]

COLONNE_TABELLA_COPERTURA_LIVE = [
    "domanda_id",
    "tema",
    "domanda",
    "stato",
    "tabella_finale",
    "indicatore_richiesto",
    "fonte_principale",
    "note",
]

SCHEMI_TABELLE_FINALI = {
    "tabella_annuale_pensioni": COLONNE_TABELLA_ANNUALE,
    "tabella_gestioni": COLONNE_TABELLA_GESTIONI,
    "tabella_territoriale": COLONNE_TABELLA_TERRITORIALE,
    "tabella_flussi_pensionamento": COLONNE_TABELLA_FLUSSI,
    "tabella_confronto_europeo": COLONNE_TABELLA_EUROPA,
    "tabella_distribuzione_pensionati": COLONNE_TABELLA_DISTRIBUZIONE,
    "tabella_demografia_lavoro": COLONNE_TABELLA_DEMOGRAFIA_LAVORO,
    "tabella_previdenza_complementare": COLONNE_TABELLA_PREVIDENZA_COMPLEMENTARE,
    "tabella_parametri_sistema": COLONNE_TABELLA_PARAMETRI,
    "tabella_copertura_live": COLONNE_TABELLA_COPERTURA_LIVE,
}


def tabella_vuota(nome_tabella: str) -> pd.DataFrame:
    """Restituisce una tabella vuota usando lo schema finale registrato."""
    if nome_tabella not in SCHEMI_TABELLE_FINALI:
        raise KeyError(f"Tabella finale non registrata: {nome_tabella}")
    return pd.DataFrame(columns=SCHEMI_TABELLE_FINALI[nome_tabella])


def tabella_annuale_vuota() -> pd.DataFrame:
    return tabella_vuota("tabella_annuale_pensioni")


def tabella_gestioni_vuota() -> pd.DataFrame:
    return tabella_vuota("tabella_gestioni")


def tabella_territoriale_vuota() -> pd.DataFrame:
    return tabella_vuota("tabella_territoriale")


def tabella_flussi_vuota() -> pd.DataFrame:
    return tabella_vuota("tabella_flussi_pensionamento")


def tabella_europa_vuota() -> pd.DataFrame:
    return tabella_vuota("tabella_confronto_europeo")


def controlla_schema(tabella: pd.DataFrame, colonne_richieste: list[str]) -> None:
    mancanti = [colonna for colonna in colonne_richieste if colonna not in tabella.columns]
    if mancanti:
        raise ValueError(f"Colonne mancanti: {mancanti}")
