from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from build_pension_indicators import FINAL_TABLE_SCHEMAS
from config import ANALISI_DA_IMPLEMENTARE_PATH, DATASET_ATTESI_PATH, DEFINIZIONI_INDICATORI_PATH, FINAL_TABLE_PATHS, LOG_PATHS, OUTPUT_ANALITICI_PATH, REGISTRO_FONTI_PATH
from utils import check_required_columns, read_csv_optional, save_table, safe_to_numeric, split_semicolon, prepare_directories

STATI_ANALISI_AMMESSI = {"da_implementare", "in_corso", "implementata", "sospesa"}
PRIORITA_AMMESSE = {"alta", "media", "bassa"}


def registered_outputs() -> set[str]:
    """Restituisce tabelle finali e output analitici registrati."""
    outputs = set(FINAL_TABLE_PATHS)
    analytic_outputs = read_csv_optional(OUTPUT_ANALITICI_PATH)
    if not analytic_outputs.empty and "output_id" in analytic_outputs.columns:
        outputs |= set(analytic_outputs["output_id"].dropna().astype(str))
    return outputs


def check_metadata_catalogs() -> list[dict[str, object]]:
    """Controlla coerenza di dataset attesi e analisi da implementare."""
    rows: list[dict[str, object]] = []
    sources = read_csv_optional(REGISTRO_FONTI_PATH)
    indicators = read_csv_optional(DEFINIZIONI_INDICATORI_PATH)
    datasets = read_csv_optional(DATASET_ATTESI_PATH)
    analyses = read_csv_optional(ANALISI_DA_IMPLEMENTARE_PATH)

    source_ids = set(sources.get("fonte_id", pd.Series(dtype=str)).dropna().astype(str))
    indicator_ids = set(indicators.get("indicatore_id", pd.Series(dtype=str)).dropna().astype(str))
    dataset_ids = set(datasets.get("dataset_logico_id", pd.Series(dtype=str)).dropna().astype(str))
    output_ids = registered_outputs()

    if not datasets.empty:
        missing_sources = sorted(set(datasets["fonte_id"].dropna().astype(str)) - source_ids)
        requested_indicators = {item for value in datasets["indicatori"] for item in split_semicolon(value)}
        missing_indicators = sorted(requested_indicators - indicator_ids)
        requested_outputs = {item for value in datasets["tabelle_finali"] for item in split_semicolon(value)}
        missing_outputs = sorted(requested_outputs - output_ids)
        rows.extend([
            {"tabella": "dataset_attesi", "controllo": "fonti_registrate", "stato": "errore" if missing_sources else "ok", "dettaglio": "; ".join(missing_sources)},
            {"tabella": "dataset_attesi", "controllo": "indicatori_registrati", "stato": "errore" if missing_indicators else "ok", "dettaglio": "; ".join(missing_indicators)},
            {"tabella": "dataset_attesi", "controllo": "output_registrati", "stato": "errore" if missing_outputs else "ok", "dettaglio": "; ".join(missing_outputs)},
        ])

    if not analyses.empty:
        requested_datasets = {item for value in analyses["dataset_logici"] for item in split_semicolon(value)}
        requested_indicators = {item for value in analyses["indicatori_richiesti"] for item in split_semicolon(value)}
        requested_outputs = {item for value in analyses["tabelle_finali"] for item in split_semicolon(value)}
        rows.extend([
            {"tabella": "analisi_da_implementare", "controllo": "dataset_logici_registrati", "stato": "errore" if sorted(requested_datasets - dataset_ids) else "ok", "dettaglio": "; ".join(sorted(requested_datasets - dataset_ids))},
            {"tabella": "analisi_da_implementare", "controllo": "indicatori_registrati", "stato": "errore" if sorted(requested_indicators - indicator_ids) else "ok", "dettaglio": "; ".join(sorted(requested_indicators - indicator_ids))},
            {"tabella": "analisi_da_implementare", "controllo": "output_registrati", "stato": "errore" if sorted(requested_outputs - output_ids) else "ok", "dettaglio": "; ".join(sorted(requested_outputs - output_ids))},
            {"tabella": "analisi_da_implementare", "controllo": "stato_ammesso", "stato": "errore" if sorted(set(analyses["stato"].dropna().astype(str)) - STATI_ANALISI_AMMESSI) else "ok", "dettaglio": "; ".join(sorted(set(analyses["stato"].dropna().astype(str)) - STATI_ANALISI_AMMESSI))},
            {"tabella": "analisi_da_implementare", "controllo": "priorita_ammessa", "stato": "errore" if sorted(set(analyses["priorita"].dropna().astype(str)) - PRIORITA_AMMESSE) else "ok", "dettaglio": "; ".join(sorted(set(analyses["priorita"].dropna().astype(str)) - PRIORITA_AMMESSE))},
        ])
    return rows


def check_final_table(table_name: str, path: Path, expected_columns: list[str]) -> list[dict[str, object]]:
    """Controlla schema, duplicati e colonne numeriche di una tabella finale."""
    table = read_csv_optional(path)
    if table.empty:
        return [{"tabella": table_name, "controllo": "presenza_dati", "stato": "avviso", "dettaglio": "tabella vuota o non ancora popolata"}]
    missing = check_required_columns(table, expected_columns)
    rows = [
        {"tabella": table_name, "controllo": "colonne_attese", "stato": "errore" if missing else "ok", "dettaglio": "; ".join(missing)},
        {"tabella": table_name, "controllo": "duplicati", "stato": "avviso" if int(table.duplicated().sum()) else "ok", "dettaglio": int(table.duplicated().sum())},
    ]
    if "anno" in table.columns:
        invalid_years = int(safe_to_numeric(table["anno"]).isna().sum())
        rows.append({"tabella": table_name, "controllo": "anno_valido", "stato": "avviso" if invalid_years else "ok", "dettaglio": invalid_years})
    if "valore" in table.columns:
        invalid_values = int(safe_to_numeric(table["valore"]).isna().sum())
        rows.append({"tabella": table_name, "controllo": "valore_numerico", "stato": "avviso" if invalid_values else "ok", "dettaglio": invalid_values})
    return rows


def run_quality_checks(log_path: str | Path = LOG_PATHS["quality"]) -> pd.DataFrame:
    """Esegue tutti i controlli di qualita' e salva il log finale."""
    prepare_directories()
    rows = check_metadata_catalogs()
    for table_name, path in FINAL_TABLE_PATHS.items():
        rows.extend(check_final_table(table_name, path, FINAL_TABLE_SCHEMAS[table_name]))
    log = pd.DataFrame(rows)
    save_table(log, log_path)
    return log


if __name__ == "__main__":
    run_quality_checks()
