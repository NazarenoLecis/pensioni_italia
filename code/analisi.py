from __future__ import annotations

from pathlib import Path

import pandas as pd

from grafici import CARTELLA_GRAFICI, grafico_barre, grafico_linea, prepara_cartella_grafici
from utilita import CARTELLA_FINAL, leggi_csv_opzionale, salva_tabella

PERCORSO_TABELLA_ANNUALE = CARTELLA_FINAL / "tabella_annuale_pensioni.csv"
PERCORSO_TABELLA_GESTIONI = CARTELLA_FINAL / "tabella_gestioni.csv"
PERCORSO_LOG_ANALISI = CARTELLA_FINAL / "log_analisi.csv"


def filtra_indicatore(tabella: pd.DataFrame, indicatore_id: str) -> pd.DataFrame:
    if tabella.empty or "indicatore_id" not in tabella.columns:
        return pd.DataFrame()
    return tabella[tabella["indicatore_id"].astype(str).eq(indicatore_id)].copy()


def grafico_indicatore_annuale(indicatore_id: str, titolo: str, nome_output: str, etichetta_y: str = "valore") -> dict[str, object]:
    tabella = filtra_indicatore(leggi_csv_opzionale(PERCORSO_TABELLA_ANNUALE), indicatore_id)
    if tabella.empty:
        return {"grafico": nome_output, "stato": "saltato", "motivo": "dati mancanti"}
    percorso_output = CARTELLA_GRAFICI / f"{nome_output}.png"
    grafico_linea(tabella, colonna_x="anno", colonna_y="valore", percorso_output=percorso_output, titolo=titolo, etichetta_x="Anno", etichetta_y=etichetta_y)
    return {"grafico": nome_output, "stato": "ok", "percorso_output": str(percorso_output)}


def esegui_analisi(percorso_log: str | Path = PERCORSO_LOG_ANALISI) -> pd.DataFrame:
    prepara_cartella_grafici()
    log = [grafico_indicatore_annuale("spesa_pensionistica_pil", "Spesa pensionistica in rapporto al PIL", "spesa_pensionistica_pil", "Percentuale del PIL")]
    tabella_log = pd.DataFrame(log)
    salva_tabella(tabella_log, percorso_log)
    return tabella_log


if __name__ == "__main__":
    esegui_analisi()
