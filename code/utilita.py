from __future__ import annotations

from pathlib import Path

import pandas as pd

RADICE_PROGETTO = Path(__file__).resolve().parents[1]
CARTELLA_DATI = RADICE_PROGETTO / "data"
CARTELLA_RAW = CARTELLA_DATI / "raw"
CARTELLA_PROCESSED = CARTELLA_DATI / "processed"
CARTELLA_FINAL = CARTELLA_DATI / "final"
CARTELLA_CACHE = CARTELLA_DATI / "cache"
CARTELLA_METADATA = RADICE_PROGETTO / "metadata"
CARTELLA_OUTPUT = RADICE_PROGETTO / "outputs"
CARTELLA_GRAFICI = CARTELLA_OUTPUT / "charts"


def prepara_cartelle() -> None:
    """Crea le cartelle locali usate dal progetto.

    Flow:
    1. definisce le cartelle standard;
    2. crea le cartelle se mancano;
    3. non scrive nessun dato, prepara solo la struttura locale.
    """
    cartelle = (
        CARTELLA_DATI,
        CARTELLA_RAW,
        CARTELLA_PROCESSED,
        CARTELLA_FINAL,
        CARTELLA_CACHE,
        CARTELLA_METADATA,
        CARTELLA_OUTPUT,
        CARTELLA_GRAFICI,
    )
    for cartella in cartelle:
        cartella.mkdir(parents=True, exist_ok=True)


def salva_tabella(tabella: pd.DataFrame, percorso_output: str | Path, *, indice: bool = False) -> Path:
    """Salva una tabella in CSV o Parquet.

    Flow:
    1. converte il percorso in `Path`;
    2. crea la cartella di destinazione;
    3. sceglie il formato in base all'estensione;
    4. restituisce il percorso scritto, utile nei log.
    """
    percorso = Path(percorso_output)
    percorso.parent.mkdir(parents=True, exist_ok=True)
    estensione = percorso.suffix.lower()

    if estensione == ".csv":
        tabella.to_csv(percorso, index=indice)
    elif estensione == ".parquet":
        tabella.to_parquet(percorso, index=indice)
    else:
        raise ValueError(f"Formato output non supportato: {estensione}")

    return percorso


def leggi_csv_opzionale(percorso_input: str | Path) -> pd.DataFrame:
    """Legge un CSV se esiste, altrimenti restituisce una tabella vuota."""
    percorso = Path(percorso_input)
    if not percorso.exists() or percorso.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(percorso)


def testo_pulito(valore: object) -> str:
    """Converte valori mancanti o non testuali in stringhe pulite."""
    if valore is None:
        return ""
    return str(valore).strip()
