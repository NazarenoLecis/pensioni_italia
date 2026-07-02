from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests

from utilita import CARTELLA_METADATA, CARTELLA_PROCESSED, CARTELLA_RAW, leggi_csv_opzionale, prepara_cartelle, salva_tabella

PERCORSO_RISORSE = CARTELLA_METADATA / "risorse_url.csv"
CARTELLA_RAW_RISORSE = CARTELLA_RAW / "risorse_url"
PERCORSO_LOG_DOWNLOAD = CARTELLA_PROCESSED / "log_download_risorse_url.csv"


def ricava_estensione(url: str) -> str:
    estensione = Path(urlparse(url).path).suffix.lower()
    return estensione if estensione else ".bin"


def scarica_risorsa_url(url: str, percorso_output: str | Path, timeout: int = 60) -> Path:
    percorso = Path(percorso_output)
    percorso.parent.mkdir(parents=True, exist_ok=True)
    risposta = requests.get(url, timeout=timeout)
    risposta.raise_for_status()
    percorso.write_bytes(risposta.content)
    return percorso


def scarica_risorse_url(categoria: str | None = None, cartella_output: str | Path = CARTELLA_RAW_RISORSE) -> pd.DataFrame:
    risorse = leggi_csv_opzionale(PERCORSO_RISORSE)
    if risorse.empty:
        return pd.DataFrame(columns=["risorsa_id", "categoria", "stato", "percorso_output", "errore"])
    if "stato" in risorse.columns:
        risorse = risorse[risorse["stato"].fillna("").str.lower().isin({"selezionato", "attivo", "mantieni"})]
    if categoria is not None and "categoria" in risorse.columns:
        risorse = risorse[risorse["categoria"].fillna("").str.lower().eq(categoria.lower())]
    log = []
    for _, riga in risorse.iterrows():
        risorsa_id = str(riga.get("risorsa_id", "risorsa")).strip()
        categoria_risorsa = str(riga.get("categoria", "altro")).strip()
        url = str(riga.get("url", "")).strip()
        nome_output = str(riga.get("nome_output") or risorsa_id).strip()
        try:
            estensione = ricava_estensione(url)
            percorso_output = Path(cartella_output) / categoria_risorsa / f"{nome_output}{estensione}"
            percorso_scritto = scarica_risorsa_url(url, percorso_output)
            log.append({"risorsa_id": risorsa_id, "categoria": categoria_risorsa, "stato": "ok", "percorso_output": str(percorso_scritto), "errore": ""})
        except Exception as errore:
            log.append({"risorsa_id": risorsa_id, "categoria": categoria_risorsa, "stato": "errore", "percorso_output": "", "errore": str(errore)})
    return pd.DataFrame(log)


def esegui_download_risorse_url(categoria: str | None = None, percorso_log: str | Path = PERCORSO_LOG_DOWNLOAD) -> pd.DataFrame:
    prepara_cartelle()
    log = scarica_risorse_url(categoria=categoria)
    salva_tabella(log, percorso_log)
    return log


def esegui_download_bilanci_inps() -> pd.DataFrame:
    return esegui_download_risorse_url(categoria="bilancio_inps")


def esegui_download_covip() -> pd.DataFrame:
    return esegui_download_risorse_url(categoria="covip")


def esegui_download_casse_professionali() -> pd.DataFrame:
    return esegui_download_risorse_url(categoria="casse_professionali")


if __name__ == "__main__":
    esegui_download_risorse_url()
