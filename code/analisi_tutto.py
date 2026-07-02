from __future__ import annotations

from pathlib import Path

import pandas as pd

from analisi_pensioni import esegui_grafici_pensioni
from utilita import CARTELLA_FINAL, salva_tabella

PERCORSO_LOG_ANALISI_COMPLESSIVA = CARTELLA_FINAL / "log_analisi_complessiva.csv"
ESEGUI_GRAFICI_PENSIONI = True


def aggiungi_log_analisi(righe: list[dict[str, object]], blocco: str, log: pd.DataFrame | None) -> None:
    """Aggiunge una riga sintetica al log dell'analisi complessiva."""
    if log is None:
        righe.append({"blocco": blocco, "risultato": "saltato", "grafici": 0, "ok": 0})
        return
    ok = int(log["status"].astype(str).str.lower().eq("ok").sum()) if "status" in log.columns else 0
    righe.append({"blocco": blocco, "risultato": "eseguito", "grafici": len(log), "ok": ok})


def esegui_analisi_tutto(
    *,
    grafici_pensioni: bool = ESEGUI_GRAFICI_PENSIONI,
    percorso_log: str | Path = PERCORSO_LOG_ANALISI_COMPLESSIVA,
) -> pd.DataFrame:
    """Esegue tutti i blocchi di analisi attivi e salva un log sintetico."""
    righe: list[dict[str, object]] = []
    aggiungi_log_analisi(righe, "grafici_pensioni", esegui_grafici_pensioni() if grafici_pensioni else None)
    log = pd.DataFrame(righe)
    salva_tabella(log, percorso_log)
    return log


if __name__ == "__main__":
    esegui_analisi_tutto()
