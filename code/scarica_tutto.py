from __future__ import annotations

from pathlib import Path

import pandas as pd

from dati_eurostat import esegui_download_eurostat
from dati_inps import esegui_discovery_inps, esegui_download_inps, esegui_tabella_risorse_inps
from dati_istat import esegui_download_istat
from finanza_pubblica import esegui_download_openbdap
from risorse_url import esegui_download_risorse_url
from utilita import CARTELLA_PROCESSED, prepara_cartelle, salva_tabella

ESEGUI_DISCOVERY_INPS = True
ESEGUI_RISORSE_INPS = True
ESEGUI_DOWNLOAD_INPS = True
ESEGUI_DOWNLOAD_OPENBDAP = True
ESEGUI_DOWNLOAD_ISTAT = True
ESEGUI_DOWNLOAD_EUROSTAT = True
ESEGUI_DOWNLOAD_RISORSE_URL = True
PERCORSO_LOG_COMPLESSIVO = CARTELLA_PROCESSED / "log_scaricamento_completo.csv"


def aggiungi_log(righe: list[dict[str, object]], blocco: str, log: pd.DataFrame | None) -> None:
    if log is None:
        righe.append({"blocco": blocco, "risultato": "saltato", "righe": 0})
        return
    righe.append({"blocco": blocco, "risultato": "eseguito", "righe": len(log)})


def scarica_tutto(
    *,
    discovery_inps: bool = ESEGUI_DISCOVERY_INPS,
    risorse_inps: bool = ESEGUI_RISORSE_INPS,
    download_inps: bool = ESEGUI_DOWNLOAD_INPS,
    download_openbdap: bool = ESEGUI_DOWNLOAD_OPENBDAP,
    download_istat: bool = ESEGUI_DOWNLOAD_ISTAT,
    download_eurostat: bool = ESEGUI_DOWNLOAD_EUROSTAT,
    download_risorse_url: bool = ESEGUI_DOWNLOAD_RISORSE_URL,
    percorso_log: str | Path = PERCORSO_LOG_COMPLESSIVO,
) -> pd.DataFrame:
    """Esegue tutti i blocchi di download attivi e salva un log sintetico."""
    prepara_cartelle()
    righe: list[dict[str, object]] = []
    aggiungi_log(righe, "discovery_inps", esegui_discovery_inps() if discovery_inps else None)
    aggiungi_log(righe, "risorse_inps", esegui_tabella_risorse_inps() if risorse_inps else None)
    aggiungi_log(righe, "download_inps", esegui_download_inps() if download_inps else None)
    aggiungi_log(righe, "download_openbdap", esegui_download_openbdap() if download_openbdap else None)
    aggiungi_log(righe, "download_istat", esegui_download_istat() if download_istat else None)
    aggiungi_log(righe, "download_eurostat", esegui_download_eurostat() if download_eurostat else None)
    aggiungi_log(righe, "download_risorse_url", esegui_download_risorse_url() if download_risorse_url else None)
    log_complessivo = pd.DataFrame(righe)
    salva_tabella(log_complessivo, percorso_log)
    return log_complessivo


if __name__ == "__main__":
    scarica_tutto()
