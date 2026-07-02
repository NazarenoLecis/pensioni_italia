from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests

from utilita import CARTELLA_METADATA, CARTELLA_PROCESSED, CARTELLA_RAW, leggi_csv_opzionale, prepara_cartelle, salva_tabella

PERCORSO_RISORSE = CARTELLA_METADATA / "url_resources.csv"
CARTELLA_RAW_RISORSE = CARTELLA_RAW / "risorse_url"
PERCORSO_LOG_DOWNLOAD = CARTELLA_PROCESSED / "risorse_url_download_log.csv"


def ricava_estensione(url: str) -> str:
    """Ricava l'estensione del file da un URL."""
    estensione = Path(urlparse(url).path).suffix.lower()
    return estensione if estensione else ".bin"


def scarica_risorsa_url(url: str, percorso_output: str | Path, timeout: int = 60) -> Path:
    """Scarica una risorsa puntuale da URL.

    Flow: crea la cartella di output, scarica i byte, controlla errori HTTP,
    salva il file e restituisce il percorso scritto.
    """
    percorso = Path(percorso_output)
    percorso.parent.mkdir(parents=True, exist_ok=True)
    risposta = requests.get(url, timeout=timeout)
    risposta.raise_for_status()
    percorso.write_bytes(risposta.content)
    return percorso


def scarica_risorse_url(categoria: str | None = None, cartella_output: str | Path = CARTELLA_RAW_RISORSE) -> pd.DataFrame:
    """Scarica le risorse elencate in metadata/url_resources.csv.

    La colonna categoria permette di separare bilanci INPS, COVIP, MEF,
    casse professionali e altre fonti documentali.
    """
    risorse = leggi_csv_opzionale(PERCORSO_RISORSE)
    if risorse.empty:
        return pd.DataFrame(columns=["resource_id", "category", "status", "output_path", "error"])

    if "status" in risorse.columns:
        risorse = risorse[risorse["status"].fillna("").str.lower().isin({"selected", "active", "keep"})]
    if categoria is not None and "category" in risorse.columns:
        risorse = risorse[risorse["category"].fillna("").str.lower().eq(categoria.lower())]

    log = []
    for _, riga in risorse.iterrows():
        resource_id = str(riga.get("resource_id", "risorsa")).strip()
        categoria_risorsa = str(riga.get("category", "altro")).strip()
        url = str(riga.get("url", "")).strip()
        nome_output = str(riga.get("output_name") or resource_id).strip()
        try:
            estensione = ricava_estensione(url)
            percorso_output = Path(cartella_output) / categoria_risorsa / f"{nome_output}{estensione}"
            percorso_scritto = scarica_risorsa_url(url, percorso_output)
            log.append({"resource_id": resource_id, "category": categoria_risorsa, "status": "ok", "output_path": str(percorso_scritto), "error": ""})
        except Exception as errore:
            log.append({"resource_id": resource_id, "category": categoria_risorsa, "status": "error", "output_path": "", "error": str(errore)})
    return pd.DataFrame(log)


def esegui_download_risorse_url(categoria: str | None = None, percorso_log: str | Path = PERCORSO_LOG_DOWNLOAD) -> pd.DataFrame:
    """Scarica le risorse URL selezionate e salva il log."""
    prepara_cartelle()
    log = scarica_risorse_url(categoria=categoria)
    salva_tabella(log, percorso_log)
    return log


def esegui_download_bilanci_inps() -> pd.DataFrame:
    """Scarica solo le risorse marcate come bilancio INPS."""
    return esegui_download_risorse_url(categoria="bilancio_inps")


def esegui_download_covip() -> pd.DataFrame:
    """Scarica solo le risorse marcate come COVIP."""
    return esegui_download_risorse_url(categoria="covip")


def esegui_download_casse_professionali() -> pd.DataFrame:
    """Scarica solo le risorse marcate come casse professionali."""
    return esegui_download_risorse_url(categoria="casse_professionali")


if __name__ == "__main__":
    esegui_download_risorse_url()
