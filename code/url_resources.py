from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests

from utils import METADATA_DIR, RAW_DIR, PROCESSED_DIR, ensure_project_dirs, read_optional_csv, write_frame

RESOURCES_PATH = METADATA_DIR / "url_resources.csv"
RAW_URL_DIR = RAW_DIR / "url_resources"
DOWNLOAD_LOG_PATH = PROCESSED_DIR / "url_resources_download_log.csv"


def infer_extension(url: str) -> str:
    """Ricava l'estensione dal path dell'URL.

    Serve per salvare PDF, Excel, CSV e altri file senza imporre manualmente
    l'estensione nella tabella dei metadati.
    """
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix else ".bin"


def download_url_resource(url: str, output_path: str | Path, timeout: int = 60) -> Path:
    """Scarica una risorsa puntuale da URL.

    Flow: crea la cartella di output, scarica il contenuto, controlla eventuali
    errori HTTP, salva i byte sul disco e restituisce il path scritto.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    path.write_bytes(response.content)
    return path


def fetch_url_resources(category: str | None = None, output_dir: str | Path = RAW_URL_DIR) -> pd.DataFrame:
    """Scarica le risorse elencate in `metadata/url_resources.csv`.

    La colonna `category` permette di separare bilancio INPS, COVIP, MEF,
    casse professionali e altre fonti senza duplicare codice.
    """
    resources = read_optional_csv(RESOURCES_PATH)
    if resources.empty:
        return pd.DataFrame(columns=["resource_id", "category", "status", "output_path", "error"])

    if "status" in resources.columns:
        resources = resources[resources["status"].fillna("").str.lower().isin({"selected", "active", "keep"})]
    if category is not None and "category" in resources.columns:
        resources = resources[resources["category"].fillna("").str.lower().eq(category.lower())]

    logs = []
    for _, row in resources.iterrows():
        resource_id = str(row.get("resource_id", "resource")).strip()
        resource_category = str(row.get("category", "other")).strip()
        url = str(row.get("url", "")).strip()
        output_name = str(row.get("output_name") or resource_id).strip()
        try:
            extension = infer_extension(url)
            output_path = Path(output_dir) / resource_category / f"{output_name}{extension}"
            written_path = download_url_resource(url, output_path)
            logs.append({"resource_id": resource_id, "category": resource_category, "status": "ok", "output_path": str(written_path), "error": ""})
        except Exception as exc:
            logs.append({"resource_id": resource_id, "category": resource_category, "status": "error", "output_path": "", "error": str(exc)})
    return pd.DataFrame(logs)


def run_url_resources_download(category: str | None = None, output_path: str | Path = DOWNLOAD_LOG_PATH) -> pd.DataFrame:
    """Scarica le risorse URL e salva il log."""
    ensure_project_dirs()
    log = fetch_url_resources(category=category)
    write_frame(log, output_path)
    return log


def run_inps_balance_download() -> pd.DataFrame:
    """Scarica solo le risorse URL marcate come bilancio INPS."""
    return run_url_resources_download(category="bilancio_inps")


def run_covip_download() -> pd.DataFrame:
    """Scarica solo le risorse URL marcate come COVIP."""
    return run_url_resources_download(category="covip")


def run_professional_funds_download() -> pd.DataFrame:
    """Scarica solo le risorse URL marcate come casse professionali."""
    return run_url_resources_download(category="casse_professionali")
