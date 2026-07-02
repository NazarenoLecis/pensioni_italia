from __future__ import annotations

from pathlib import Path

import pandas as pd

from eurostat_data import run_eurostat_download as eurostat_download
from inps_open_data import run_inps_discovery as inps_discovery
from inps_open_data import run_inps_download as inps_download
from inps_open_data import run_inps_resource_table as inps_resources
from istat_data import run_istat_download as istat_download
from openbdap_public_finance import run_openbdap_download as openbdap_download
from url_resources import run_url_resources_download as url_resources_download
from utils import PROCESSED_DIR, ensure_project_dirs, write_frame

RUN_INPS_DISCOVERY = True
RUN_INPS_RESOURCES = True
RUN_INPS_DOWNLOAD = True
RUN_OPENBDAP_DOWNLOAD = True
RUN_ISTAT_DOWNLOAD = True
RUN_EUROSTAT_DOWNLOAD = True
RUN_URL_RESOURCES_DOWNLOAD = True
MASTER_LOG_PATH = PROCESSED_DIR / "download_all_log.csv"


def add_step_log(rows: list[dict[str, object]], step: str, log: pd.DataFrame | None) -> None:
    if log is None:
        rows.append({"step": step, "result": "skipped", "rows": 0})
        return
    rows.append({"step": step, "result": "done", "rows": len(log)})


def download_all(
    *,
    do_inps_discovery: bool = RUN_INPS_DISCOVERY,
    do_inps_resources: bool = RUN_INPS_RESOURCES,
    do_inps_download: bool = RUN_INPS_DOWNLOAD,
    do_openbdap_download: bool = RUN_OPENBDAP_DOWNLOAD,
    do_istat_download: bool = RUN_ISTAT_DOWNLOAD,
    do_eurostat_download: bool = RUN_EUROSTAT_DOWNLOAD,
    do_url_resources_download: bool = RUN_URL_RESOURCES_DOWNLOAD,
    master_log_path: str | Path = MASTER_LOG_PATH,
) -> pd.DataFrame:
    """Esegue tutti i download selezionati e salva un log sintetico."""
    ensure_project_dirs()
    rows: list[dict[str, object]] = []
    add_step_log(rows, "inps_discovery", inps_discovery() if do_inps_discovery else None)
    add_step_log(rows, "inps_resources", inps_resources() if do_inps_resources else None)
    add_step_log(rows, "inps_download", inps_download() if do_inps_download else None)
    add_step_log(rows, "openbdap_download", openbdap_download() if do_openbdap_download else None)
    add_step_log(rows, "istat_download", istat_download() if do_istat_download else None)
    add_step_log(rows, "eurostat_download", eurostat_download() if do_eurostat_download else None)
    add_step_log(rows, "url_resources_download", url_resources_download() if do_url_resources_download else None)
    master_log = pd.DataFrame(rows)
    write_frame(master_log, master_log_path)
    return master_log


if __name__ == "__main__":
    download_all()
