from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from config import DIRECTORIES


def prepare_directories(extra_directories: Iterable[str | Path] | None = None) -> None:
    """Crea le cartelle standard del progetto e, se passate, cartelle aggiuntive."""
    directories = list(DIRECTORIES)
    if extra_directories is not None:
        directories.extend(Path(path) for path in extra_directories)
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def read_csv_optional(path: str | Path) -> pd.DataFrame:
    """Legge un CSV se esiste; restituisce un DataFrame vuoto se manca o se e' vuoto."""
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with path.open("r", encoding=encoding) as handle:
                first_line = handle.readline()
            separator = ";" if first_line.count(";") > first_line.count(",") else ","
            return pd.read_csv(path, encoding=encoding, sep=separator)
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
    return pd.read_csv(path, encoding="utf-8", encoding_errors="replace", sep=None, engine="python")


def save_table(table: pd.DataFrame, path: str | Path, index: bool = False) -> Path:
    """Salva una tabella in CSV o Parquet creando la cartella di destinazione."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        table.to_csv(path, index=index)
    elif suffix == ".parquet":
        table.to_parquet(path, index=index)
    else:
        raise ValueError(f"Formato non supportato: {suffix}")
    return path


def clean_text(value: object) -> str:
    """Converte valori mancanti o non testuali in stringhe pulite."""
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def normalize_columns(table: pd.DataFrame) -> pd.DataFrame:
    """Normalizza i nomi colonna per renderli stabili nelle trasformazioni."""
    result = table.copy()
    result.columns = [str(column).strip().lower().replace(" ", "_") for column in result.columns]
    return result


def split_semicolon(value: object) -> list[str]:
    """Divide un campo separato da punto e virgola ignorando valori mancanti e vuoti."""
    if value is None or pd.isna(value):
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def check_required_columns(table: pd.DataFrame, required_columns: Iterable[str]) -> list[str]:
    """Restituisce l'elenco delle colonne richieste che mancano in una tabella."""
    return [column for column in required_columns if column not in table.columns]


def safe_to_numeric(series: pd.Series) -> pd.Series:
    """Converte una serie in numerico usando NaN per valori non convertibili."""
    return pd.to_numeric(series, errors="coerce")


def count_csv_rows(path: str | Path) -> int:
    """Conta le righe dati di un CSV, escludendo l'intestazione."""
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return 0
    with path.open("r", encoding="utf-8") as file:
        return max(sum(1 for _ in file) - 1, 0)
