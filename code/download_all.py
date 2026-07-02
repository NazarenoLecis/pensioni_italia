from __future__ import annotations

import pandas as pd

from eurostat_data import run_eurostat_download
from inps_open_data import run_inps_discovery, run_inps_download, run_inps_resource_table
from istat_data import run_istat_download
from openbdap_public_finance import run_openbdap_download
from url_resources import run_url_resources_download
from utils import PROCESSED_DIR, ensure_project_dirs, write_frame

RUN_INPS_DISCOVERY = True
RUN_INPS_RESOURCES = True
RUN_INPS_DOWNLOAD = True
RUN_OPENBDAP_DOWNLOAD = True
RUN_ISTAT_DOWNLOAD = True
RUN_EUROSTAT_DOWNLOAD = True
RUN_URL_RESOURCES_DOWNLOAD = True
MASTER_LOG_PATH = PROCESSED_DIR / "download_all_log.csv"


def add_step_log(rows: list[dict[str, object]], step: str, log: pd.DataFrame) -> None:
    """Aggiunge al master log una riga sintetica per ogni passaggio.

    Il master log non sostituisce i log specifici. Serve solo per capire se un
    blocco ha prodotto righe, se ha errori e dove guardare dopo.
    """
    if log is None:
        rows.append({"step": step, "status": "skipped", "rows": 0, "errors": 0})
        return
    errors = 0
    if "status" in log.columns:
        errors = int(log["status"].astype(str).str.lower().eq("error").sum())
    rows.append({"step": step, "status": "done", "rows": len(log), "errors": errors})


def download_all(
    *,
    run_inps_discovery: bool = RUN_INPS_DISCOVERY,
    run_inps_resources: bool = RUN_INPS_RESOURCES,
    run_inps_download: bool = RUN_INPS_DOWNLOAD,
    run_openbdap_download: bool = RUN_OPENBDAP_DOWNLOAD,
    run_istat_download_step: bool = RUN_ISTAT_DOWNLOAD,
    run_eurostat_download_step: bool = RUN_EUROSTAT_DOWNLOAD,
    run_url_resources_download_step: bool = RUN_URL_RESOURCES_DOWNLOAD,
    master_log_path: str = MASTER_LOG_PATH,
) -> pd.DataFrame:
    """Esegue tutti i download del progetto.

    Flow:
    1. crea le cartelle locali;
    2. aggiorna discovery e risorse INPS;
    3. scarica i dataset INPS selezionati in whitelist;
    4. scarica OpenBDAP, ISTAT, Eurostat e risorse URL selezionate;
    5. salva un log sintetico unico in `data/processed/download_all_log.csv`.
    """
    ensure_project_dirs()
    rows: list[dict[str, object]] = []

    add_step_log(rows, "inps_discovery", run_inps_discovery() if run_inps_discovery else None)
    add_step_log(rows, "inps_resources", run_inps_resource_table() if run_inps_resources else None)
    add_step_log(rows, "inps_download", run_inps_download() if run_inps_download else None)
    add_step_log(rows, "openbdap_download", run_openbdap_download() if run_openbdap_download else None)
    add_step_log(rows, "istat_download", run_istat_download() if run_istat_download_step else None)
    add_step_log(rows, "eurostat_download", run_eurostat_download() if run_eurostat_download_step else None)
    add_step_log(rows, "url_resources_download", run_url_resources_download() if run_url_resources_download_step else None)

    master_log = pd.DataFrame(rows)
    write_frame(master_log, master_log_path)
    return master_log


if __name__ == "__main__":
    download_all()
