from __future__ import annotations

from pathlib import Path

from tabelle_finali import tabella_annuale_vuota, tabella_europa_vuota, tabella_flussi_vuota, tabella_gestioni_vuota, tabella_territoriale_vuota
from utilita import CARTELLA_FINAL, prepara_cartelle, salva_tabella

PERCORSO_TABELLA_ANNUALE = CARTELLA_FINAL / "tabella_annuale_pensioni.csv"
PERCORSO_TABELLA_GESTIONI = CARTELLA_FINAL / "tabella_gestioni.csv"
PERCORSO_TABELLA_TERRITORIALE = CARTELLA_FINAL / "tabella_territoriale.csv"
PERCORSO_TABELLA_FLUSSI = CARTELLA_FINAL / "tabella_flussi_pensionamento.csv"
PERCORSO_TABELLA_EUROPA = CARTELLA_FINAL / "tabella_confronto_europeo.csv"


def inizializza_tabelle_finali(
    *,
    percorso_tabella_annuale: str | Path = PERCORSO_TABELLA_ANNUALE,
    percorso_tabella_gestioni: str | Path = PERCORSO_TABELLA_GESTIONI,
    percorso_tabella_territoriale: str | Path = PERCORSO_TABELLA_TERRITORIALE,
    percorso_tabella_flussi: str | Path = PERCORSO_TABELLA_FLUSSI,
    percorso_tabella_europa: str | Path = PERCORSO_TABELLA_EUROPA,
) -> dict[str, str]:
    prepara_cartelle()
    output = {
        "annuale": salva_tabella(tabella_annuale_vuota(), percorso_tabella_annuale),
        "gestioni": salva_tabella(tabella_gestioni_vuota(), percorso_tabella_gestioni),
        "territoriale": salva_tabella(tabella_territoriale_vuota(), percorso_tabella_territoriale),
        "flussi": salva_tabella(tabella_flussi_vuota(), percorso_tabella_flussi),
        "europa": salva_tabella(tabella_europa_vuota(), percorso_tabella_europa),
    }
    return {chiave: str(percorso) for chiave, percorso in output.items()}


if __name__ == "__main__":
    inizializza_tabelle_finali()
