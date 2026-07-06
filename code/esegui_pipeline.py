from __future__ import annotations

from pathlib import Path

import pandas as pd

from analisi import esegui_analisi
from calcolatore_pensione_pagata import esegui_calcolatore_base
from controlli_qualita import esegui_controlli_qualita
from copertura_live import esegui_copertura_live
from scarica_tutto import scarica_tutto
from trasforma_dati import costruisci_tabelle_da_fonti_grezze
from utilita import CARTELLA_PROCESSED, prepara_cartelle, salva_tabella

PERCORSO_LOG_PIPELINE = CARTELLA_PROCESSED / "log_pipeline.csv"


def aggiungi_log(righe: list[dict[str, object]], fase: str, log: pd.DataFrame | None) -> None:
    if log is None:
        righe.append({"fase": fase, "stato": "saltata", "righe_log": 0})
        return
    righe.append({"fase": fase, "stato": "eseguita", "righe_log": len(log)})


def esegui_pipeline(percorso_log: str | Path = PERCORSO_LOG_PIPELINE) -> pd.DataFrame:
    """Esegue download, trasformazione, copertura live, controlli, calcolatore e analisi."""
    prepara_cartelle()
    righe: list[dict[str, object]] = []
    aggiungi_log(righe, "download", scarica_tutto())
    aggiungi_log(righe, "trasformazione", costruisci_tabelle_da_fonti_grezze())
    aggiungi_log(righe, "copertura_live", esegui_copertura_live())
    aggiungi_log(righe, "controlli_qualita", esegui_controlli_qualita())
    aggiungi_log(righe, "calcolatore_pensione_pagata", esegui_calcolatore_base())
    aggiungi_log(righe, "analisi", esegui_analisi())
    log = pd.DataFrame(righe)
    salva_tabella(log, percorso_log)
    return log


if __name__ == "__main__":
    esegui_pipeline()
