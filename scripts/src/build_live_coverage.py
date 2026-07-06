from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from config import DOMANDE_LIVE_PATH, FINAL_TABLE_PATHS, LOG_PATHS
from utils import read_csv_optional, save_table, split_semicolon, prepare_directories

OUTPUT_PATH = FINAL_TABLE_PATHS["tabella_copertura_live"]

REQUIRED_COLUMNS = ["domanda_id", "tema", "domanda", "tabella_finale", "indicatore_richiesto", "fonte_principale", "note"]


def read_live_questions(path: str | Path = DOMANDE_LIVE_PATH) -> pd.DataFrame:
    """Legge la matrice delle domande live e verifica le colonne minime."""
    questions = read_csv_optional(path)
    if questions.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    missing = [column for column in REQUIRED_COLUMNS if column not in questions.columns]
    if missing:
        raise ValueError(f"Colonne mancanti in domande_live.csv: {missing}")
    return questions[REQUIRED_COLUMNS].copy()


def check_indicators(table: pd.DataFrame, indicators: list[str]) -> tuple[bool, str]:
    """Verifica che gli indicatori richiesti siano presenti nella tabella finale."""
    if not indicators:
        return True, "domanda metodologica o senza indicatore singolo"
    if table.empty:
        return False, "tabella finale vuota"
    if "indicatore_id" not in table.columns:
        return False, "colonna indicatore_id assente"
    available = set(table["indicatore_id"].dropna().astype(str))
    missing = [indicator for indicator in indicators if indicator not in available]
    if missing:
        return False, "indicatori mancanti: " + "; ".join(missing)
    return True, "indicatori presenti"


def evaluate_question(row: pd.Series) -> dict[str, object]:
    """Valuta lo stato di copertura di una domanda della matrice live."""
    table_name = str(row.get("tabella_finale", "")).strip()
    indicators = split_semicolon(row.get("indicatore_richiesto"))

    if table_name == "" or table_name.lower() in {"metodologico", "n/a", "na"}:
        status = "metodologica"
        detail = "nessuna tabella finale richiesta"
    elif table_name not in FINAL_TABLE_PATHS:
        status = "non_mappata"
        detail = f"tabella finale non registrata: {table_name}"
    else:
        table = read_csv_optional(FINAL_TABLE_PATHS[table_name])
        covered, detail = check_indicators(table, indicators)
        status = "coperta" if covered and not table.empty else "mancano_dati"
        if covered and not indicators:
            status = "metodologica"

    note = str(row.get("note", "")).strip()
    return {
        "domanda_id": row.get("domanda_id"),
        "tema": row.get("tema"),
        "domanda": row.get("domanda"),
        "stato": status,
        "tabella_finale": table_name,
        "indicatore_richiesto": row.get("indicatore_richiesto"),
        "fonte_principale": row.get("fonte_principale"),
        "note": detail if note == "" else f"{note} | {detail}",
    }


def build_live_coverage(output_path: str | Path = OUTPUT_PATH, log_path: str | Path = LOG_PATHS["coverage"]) -> pd.DataFrame:
    """Costruisce la tabella di copertura delle domande live e salva output e log."""
    prepare_directories()
    questions = read_live_questions()
    coverage = pd.DataFrame([evaluate_question(row) for _, row in questions.iterrows()]) if not questions.empty else pd.DataFrame()
    save_table(coverage, output_path)
    log = coverage.groupby("stato", dropna=False).size().reset_index(name="domande") if not coverage.empty else pd.DataFrame(columns=["stato", "domande"])
    save_table(log, log_path)
    return coverage


if __name__ == "__main__":
    build_live_coverage()
