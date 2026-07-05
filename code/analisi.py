from __future__ import annotations

from pathlib import Path

import pandas as pd

from grafici import CARTELLA_GRAFICI, grafico_linea, prepara_cartella_grafici
from utilita import CARTELLA_FINAL, leggi_csv_opzionale, salva_tabella

PERCORSO_TABELLA_ANNUALE = CARTELLA_FINAL / "tabella_annuale_pensioni.csv"
PERCORSO_TABELLA_DEMOGRAFIA = CARTELLA_FINAL / "tabella_demografia_lavoro.csv"
PERCORSO_TABELLA_COMPLEMENTARE = CARTELLA_FINAL / "tabella_previdenza_complementare.csv"
PERCORSO_LOG_ANALISI = CARTELLA_FINAL / "log_analisi.csv"

INDICATORI_GRAFICI = [
    {
        "percorso": PERCORSO_TABELLA_ANNUALE,
        "indicatore_id": "spesa_pensionistica_pil",
        "titolo": "Spesa pensionistica in rapporto al PIL",
        "nome_output": "spesa_pensionistica_pil",
        "etichetta_y": "Percentuale del PIL",
    },
    {
        "percorso": PERCORSO_TABELLA_ANNUALE,
        "indicatore_id": "trasferimenti_stato_inps",
        "titolo": "Trasferimenti statali a INPS",
        "nome_output": "trasferimenti_stato_inps",
        "etichetta_y": "Euro",
    },
    {
        "percorso": PERCORSO_TABELLA_DEMOGRAFIA,
        "indicatore_id": "pensionati_su_occupati",
        "titolo": "Rapporto tra pensionati e occupati",
        "nome_output": "pensionati_su_occupati",
        "etichetta_y": "Rapporto",
    },
    {
        "percorso": PERCORSO_TABELLA_COMPLEMENTARE,
        "indicatore_id": "asset_fondi_pensione_pil",
        "titolo": "Asset dei fondi pensione in rapporto al PIL",
        "nome_output": "asset_fondi_pensione_pil",
        "etichetta_y": "Percentuale del PIL",
    },
]


def filtra_indicatore(tabella: pd.DataFrame, indicatore_id: str) -> pd.DataFrame:
    if tabella.empty or "indicatore_id" not in tabella.columns:
        return pd.DataFrame()
    return tabella[tabella["indicatore_id"].astype(str).eq(indicatore_id)].copy()


def grafico_indicatore_annuale(
    percorso_tabella: str | Path,
    indicatore_id: str,
    titolo: str,
    nome_output: str,
    etichetta_y: str = "valore",
) -> dict[str, object]:
    tabella = filtra_indicatore(leggi_csv_opzionale(percorso_tabella), indicatore_id)
    if tabella.empty:
        return {"grafico": nome_output, "stato": "saltato", "motivo": "dati mancanti"}
    percorso_output = CARTELLA_GRAFICI / f"{nome_output}.png"
    grafico_linea(
        tabella,
        colonna_x="anno",
        colonna_y="valore",
        percorso_output=percorso_output,
        titolo=titolo,
        etichetta_x="Anno",
        etichetta_y=etichetta_y,
    )
    return {"grafico": nome_output, "stato": "ok", "percorso_output": str(percorso_output)}


def esegui_analisi(percorso_log: str | Path = PERCORSO_LOG_ANALISI) -> pd.DataFrame:
    prepara_cartella_grafici()
    log = [grafico_indicatore_annuale(**configurazione) for configurazione in INDICATORI_GRAFICI]
    tabella_log = pd.DataFrame(log)
    salva_tabella(tabella_log, percorso_log)
    return tabella_log


if __name__ == "__main__":
    esegui_analisi()
