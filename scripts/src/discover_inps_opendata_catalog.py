from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import requests

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from config import CACHE_DATA_DIR, LOG_PATHS
from utils import prepare_directories, save_table

API_URL = "https://serviziweb2.inps.it/odapi/current_package_list_with_resources"
DEFAULT_TERMS = [
    "pensione",
    "pensioni",
    "pensionati",
    "bilancio",
    "rendiconto",
    "rendiconti",
    "artigiani",
    "commercianti",
    "coltivatori",
    "lavoratori dipendenti",
    "dipendenti pubblici",
    "gestione separata",
]


def text_contains_terms(text: str, terms: list[str]) -> str:
    """Restituisce i termini trovati in un testo, separati da punto e virgola."""
    lowered = text.lower()
    found = [term for term in terms if term.lower() in lowered]
    return "; ".join(sorted(set(found)))


def flatten_package(package: dict) -> dict[str, object]:
    """Riduce il JSON CKAN INPS a una riga di catalogo leggibile."""
    resources = package.get("resources") or []
    resource_urls = []
    resource_formats = []
    for resource in resources:
        if resource.get("url"):
            resource_urls.append(str(resource.get("url")))
        if resource.get("format"):
            resource_formats.append(str(resource.get("format")))
    tags = package.get("tags") or []
    tag_names = [str(tag.get("name")) for tag in tags if tag.get("name")]
    return {
        "dataset_id": package.get("id"),
        "name": package.get("name"),
        "title": package.get("title"),
        "notes": package.get("notes"),
        "tags": "; ".join(tag_names),
        "metadata_created": package.get("metadata_created"),
        "metadata_modified": package.get("metadata_modified"),
        "license_id": package.get("license_id"),
        "download_url": package.get("download_url"),
        "resource_formats": "; ".join(sorted(set(resource_formats))),
        "resource_urls": "; ".join(resource_urls),
    }


def fetch_catalog_page(limit: int, offset: int, timeout: int = 30) -> list[dict]:
    """Scarica una pagina del catalogo Open Data INPS."""
    response = requests.get(API_URL, params={"limit": limit, "offset": offset}, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    result = payload.get("result", [])
    if not isinstance(result, list):
        raise ValueError("Risposta INPS inattesa: campo result non lista")
    return result


def discover_inps_opendata_catalog(max_pages: int = 20, limit: int = 50, terms: list[str] | None = None) -> pd.DataFrame:
    """Scarica il catalogo INPS per pagine e filtra i dataset pensione/bilancio."""
    prepare_directories()
    terms = terms or DEFAULT_TERMS
    rows: list[dict[str, object]] = []
    for page in range(max_pages):
        packages = fetch_catalog_page(limit=limit, offset=page * limit)
        if not packages:
            break
        rows.extend(flatten_package(package) for package in packages)
    catalog = pd.DataFrame(rows)
    if catalog.empty:
        return catalog
    search_text = catalog[["name", "title", "notes", "tags"]].fillna("").agg(" ".join, axis=1)
    catalog["termini_trovati"] = [text_contains_terms(text, terms) for text in search_text]
    return catalog[catalog["termini_trovati"].astype(str).str.len() > 0].copy()


def run_discovery() -> pd.DataFrame:
    """Esegue discovery e salva catalogo filtrato in output/data/cache."""
    table = discover_inps_opendata_catalog()
    output_path = CACHE_DATA_DIR / "inps_opendata_catalog_filtrato.csv"
    save_table(table, output_path)
    log = pd.DataFrame([
        {
            "fase": "opendata_discovery",
            "righe": len(table),
            "percorso_output": str(output_path),
            "stato": "ok" if not table.empty else "nessun_dataset_trovato_o_catalogo_non_raggiungibile",
        }
    ])
    save_table(log, LOG_PATHS["opendata_discovery"])
    return table


if __name__ == "__main__":
    run_discovery()
