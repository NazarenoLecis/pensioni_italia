from __future__ import annotations

from pathlib import Path

import pandas as pd

from grafici import CARTELLA_GRAFICI, grafico_barre, grafico_linea, prepara_cartella_grafici
from utilita import CARTELLA_FINAL, leggi_csv_opzionale, salva_tabella

PERCORSO_PANNELLO_ANNUALE = CARTELLA_FINAL / "pannello_annuale_pensioni.csv"
PERCORSO_PANNELLO_GESTIONI = CARTELLA_FINAL / "pannello_gestioni.csv"
PERCORSO_LOG_ANALISI = CARTELLA_FINAL / "log_analisi_pensioni.csv"


def filtra_indicatore(tabella: pd.DataFrame, indicatore_id: str) -> pd.DataFrame:
    """Filtra un pannello lungo per indicatore_id."""
    if tabella.empty or "indicatore_id" not in tabella.columns:
        return pd.DataFrame()
    return tabella[tabella["indicatore_id"].astype(str).eq(indicatore_id)].copy()


def grafico_indicatore_annuale(indicatore_id: str, titolo: str, nome_output: str, etichetta_y: str = "valore") -> dict[str, object]:
    """Crea un grafico a linea per un indicatore annuale nazionale."""
    tabella = filtra_indicatore(leggi_csv_opzionale(PERCORSO_PANNELLO_ANNUALE), indicatore_id)
    if tabella.empty:
        return {"grafico": nome_output, "status": "saltato", "motivo": "dati mancanti"}
    percorso_output = CARTELLA_GRAFICI / f"{nome_output}.png"
    grafico_linea(tabella, colonna_x="anno", colonna_y="valore", percorso_output=percorso_output, titolo=titolo, etichetta_x="Anno", etichetta_y=etichetta_y, nota_fonte="Fonte: dati ufficiali; elaborazione Nazareno Lecis.")
    return {"grafico": nome_output, "status": "ok", "output_path": str(percorso_output)}


def grafico_indicatore_gestioni(indicatore_id: str, titolo: str, nome_output: str, anno: int | None = None, primi_n: int = 15) -> dict[str, object]:
    """Crea un grafico a barre per un indicatore per gestione o fondo."""
    tabella = filtra_indicatore(leggi_csv_opzionale(PERCORSO_PANNELLO_GESTIONI), indicatore_id)
    if tabella.empty:
        return {"grafico": nome_output, "status": "saltato", "motivo": "dati mancanti"}
    if anno is None:
        anno = int(pd.to_numeric(tabella["anno"], errors="coerce").dropna().max())
    tabella = tabella[pd.to_numeric(tabella["anno"], errors="coerce").eq(anno)]
    colonna_categoria = "gestione_nome" if "gestione_nome" in tabella.columns else "gestione_id"
    percorso_output = CARTELLA_GRAFICI / f"{nome_output}.png"
    grafico_barre(tabella, colonna_categoria=colonna_categoria, colonna_valore="valore", percorso_output=percorso_output, titolo=titolo, etichetta_x="Gestione", etichetta_y="Valore", nota_fonte="Fonte: dati ufficiali; elaborazione Nazareno Lecis.", primi_n=primi_n)
    return {"grafico": nome_output, "status": "ok", "output_path": str(percorso_output)}


def esegui_grafici_pensioni(percorso_log: str | Path = PERCORSO_LOG_ANALISI) -> pd.DataFrame:
    """Esegue i primi grafici standard sulle pensioni e salva un log."""
    prepara_cartella_grafici()
    log = [
        grafico_indicatore_annuale("spesa_pensionistica_pil", "Spesa pensionistica in rapporto al PIL", "spesa_pensionistica_pil", "Percentuale del PIL"),
        grafico_indicatore_annuale("pensionati_su_occupati", "Pensionati su occupati", "pensionati_su_occupati", "Rapporto"),
        grafico_indicatore_gestioni("spesa_pensionistica_inps", "Spesa pensionistica per gestione", "spesa_per_gestione"),
    ]
    tabella_log = pd.DataFrame(log)
    salva_tabella(tabella_log, percorso_log)
    return tabella_log


if __name__ == "__main__":
    esegui_grafici_pensioni()
