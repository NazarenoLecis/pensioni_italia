from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from config import LOG_PATHS, RAW_DATA_DIR, WHITELIST_EUROSTAT_PATH, WHITELIST_INPS_PATH, WHITELIST_ISTAT_PATH, WHITELIST_OPENBDAP_PATH, RISORSE_URL_PATH
from utils import prepare_directories, read_csv_optional, save_table


def summarize_download_inputs() -> pd.DataFrame:
    """Riepiloga le whitelist disponibili per i download automatici.

    La funzione non forza lo scaricamento dei dati. Serve a rendere esplicito
    quali fonti sono gia' state collegate agli identificativi tecnici e quali
    devono ancora essere popolate.
    """
    sources = {
        "inps": WHITELIST_INPS_PATH,
        "openbdap": WHITELIST_OPENBDAP_PATH,
        "istat": WHITELIST_ISTAT_PATH,
        "eurostat": WHITELIST_EUROSTAT_PATH,
        "risorse_url": RISORSE_URL_PATH,
    }
    rows = []
    for source_name, path in sources.items():
        table = read_csv_optional(path)
        rows.append(
            {
                "fonte": source_name,
                "percorso_whitelist": str(path),
                "righe_whitelist": len(table),
                "stato": "da_popolare" if table.empty else "pronta_o_parziale",
            }
        )
    return pd.DataFrame(rows)


def run_downloads(log_path: str | Path = LOG_PATHS["download"]) -> pd.DataFrame:
    """Prepara le cartelle raw e salva un log dello stato delle whitelist.

    I download effettivi vanno aggiunti qui quando le whitelist contengono gli ID
    tecnici verificati. Questa scelta evita download opachi o non replicabili.
    """
    prepare_directories([RAW_DATA_DIR])
    log = summarize_download_inputs()
    save_table(log, log_path)
    return log


if __name__ == "__main__":
    run_downloads()
