from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FINAL_DIR = DATA_DIR / "final"
CACHE_DIR = DATA_DIR / "cache"
METADATA_DIR = PROJECT_ROOT / "metadata"
DOCS_DIR = PROJECT_ROOT / "docs"


def ensure_project_dirs() -> None:
    """Crea le cartelle locali usate dal progetto.

    Il repository non deve salvare i dati raw e processed in Git. Le cartelle
    vengono comunque create quando si esegue il flusso locale, cosi' ogni file
    puo' scrivere output senza richiedere passaggi manuali.
    """
    for path in (DATA_DIR, RAW_DIR, PROCESSED_DIR, FINAL_DIR, CACHE_DIR, METADATA_DIR):
        path.mkdir(parents=True, exist_ok=True)


def write_frame(frame: pd.DataFrame, output_path: str | Path, *, index: bool = False) -> Path:
    """Salva un DataFrame in CSV o Parquet.

    Flow:
    1. converte il path in oggetto `Path`;
    2. crea la cartella di destinazione;
    3. sceglie il writer in base all'estensione;
    4. restituisce il path scritto, utile per log e controlli successivi.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        frame.to_csv(path, index=index)
    elif suffix == ".parquet":
        frame.to_parquet(path, index=index)
    else:
        raise ValueError(f"Formato output non supportato: {suffix}")

    return path


def read_optional_csv(input_path: str | Path) -> pd.DataFrame:
    """Legge un CSV se esiste, altrimenti restituisce un DataFrame vuoto.

    Questa funzione serve per file di metadati che possono non essere ancora
    stati generati, per esempio la lista dei dataset candidati dopo la prima
    discovery.
    """
    path = Path(input_path)
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path)


def normalise_text(value: object) -> str:
    """Converte valori mancanti o non testuali in stringhe pulite."""
    if value is None:
        return ""
    return str(value).strip()
