from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from build_inps_balance_and_professional_distribution import build_inps_balance_and_professional_distribution
from build_contribution_rate_history import build_contribution_rate_history
from build_dataset_inventory import run_dataset_inventory
from build_live_coverage import build_live_coverage
from build_pension_indicators import build_pension_indicators
from clean_pension_data import clean_available_data
from download_pension_data import run_downloads
from make_pension_charts import make_pension_charts
from pension_paid_calculator import run_pension_paid_calculator
from run_quality_checks import run_quality_checks
from config import LOG_PATHS
from utils import prepare_directories, save_table


def add_log_row(rows: list[dict[str, object]], step: str, result: pd.DataFrame | None) -> None:
    """Aggiunge al log della pipeline lo stato sintetico di una fase."""
    if result is None:
        rows.append({"fase": step, "stato": "saltata", "righe_log": 0})
    else:
        rows.append({"fase": step, "stato": "eseguita", "righe_log": len(result)})


def run_pipeline(log_path: str | Path = LOG_PATHS["pipeline"]) -> pd.DataFrame:
    """Esegue l'intera pipeline modulare del repository.

    Sequenza: download, pulizia, costruzione indicatori, tabelle INPS di bilancio
    e professione, copertura live, controlli qualita', calcolatore pensione pagata
    e grafici.
    """
    prepare_directories()
    rows: list[dict[str, object]] = []
    add_log_row(rows, "download", run_downloads())
    add_log_row(rows, "dataset_inventory", run_dataset_inventory())
    add_log_row(rows, "cleaning", clean_available_data())
    add_log_row(rows, "build_indicators", build_pension_indicators())
    add_log_row(rows, "contribution_rate_history", build_contribution_rate_history())
    add_log_row(rows, "inps_balance_profession", build_inps_balance_and_professional_distribution())
    add_log_row(rows, "live_coverage", build_live_coverage())
    add_log_row(rows, "quality_checks", run_quality_checks())
    add_log_row(rows, "pension_paid_calculator", run_pension_paid_calculator())
    add_log_row(rows, "charts", make_pension_charts())
    log = pd.DataFrame(rows)
    save_table(log, log_path)
    return log


if __name__ == "__main__":
    run_pipeline()
