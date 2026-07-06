from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from config import CLEAN_DATA_DIR, LOG_PATHS, RAW_DATA_DIR
from utils import normalize_columns, prepare_directories, read_csv_optional, save_table


def clean_raw_csv_file(path: Path) -> tuple[pd.DataFrame, str]:
    """Legge un CSV grezzo e normalizza i nomi colonna.

    La funzione applica solo una pulizia minima e non cambia il contenuto dei dati.
    Scelte metodologiche specifiche devono essere implementate nei moduli di
    costruzione degli indicatori.
    """
    table = read_csv_optional(path)
    if table.empty:
        return table, "vuoto_o_non_leggibile"
    return normalize_columns(table), "ok"


def clean_available_data(log_path: str | Path = LOG_PATHS["cleaning"]) -> pd.DataFrame:
    """Pulisce i CSV disponibili in output/data/raw e salva in output/data/clean."""
    prepare_directories([RAW_DATA_DIR, CLEAN_DATA_DIR])
    rows = []
    for input_path in sorted(RAW_DATA_DIR.rglob("*.csv")):
        relative_path = input_path.relative_to(RAW_DATA_DIR)
        output_path = CLEAN_DATA_DIR / relative_path
        table, status = clean_raw_csv_file(input_path)
        if not table.empty:
            save_table(table, output_path)
        rows.append(
            {
                "input": str(input_path),
                "output": str(output_path),
                "righe": len(table),
                "colonne": len(table.columns),
                "stato": status,
            }
        )
    log = pd.DataFrame(rows)
    save_table(log, log_path)
    return log


if __name__ == "__main__":
    clean_available_data()
