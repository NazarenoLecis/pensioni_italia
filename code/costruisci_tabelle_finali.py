from __future__ import annotations

from pathlib import Path

from tabelle_finali import tabella_annuale_vuota, tabella_gestioni_vuota, tabella_territoriale_vuota
from utilita import CARTELLA_FINAL, prepara_cartelle, salva_tabella

PERCORSO_TABELLA_ANNUALE = CARTELLA_FINAL / "tabella_annuale_pensioni.csv"
PERCORSO_TABELLA_GESTIONI = CARTELLA_FINAL / "tabella_gestioni.csv"
PERCORSO_TABELLA_TERRITORIALE = CARTELLA_FINAL / "tabella_territoriale.csv"


def inizializza_tabelle_finali(
    *,
    percorso_tabella_annuale: str | Path = PERCORSO_TABELLA_ANNUALE,
    percorso_tabella_gestioni: str | Path = PERCORSO_TABELLA_GESTIONI,
    percorso_tabella_territoriale: str | Path = PERCORSO_TABELLA_TERRITORIALE,
) -> dict[str, str]:
    """Crea le tabelle finali vuote."""
    prepara_cartelle()
    output = {
        "annuale": salva_tabella(tabella_annuale_vuota(), percorso_tabella_annuale),
        "gestioni": salva_tabella(tabella_gestioni_vuota(), percorso_tabella_gestioni),
        "territoriale": salva_tabella(tabella_territoriale_vuota(), percorso_tabella_territoriale),
    }
    return {chiave: str(percorso) for chiave, percorso in output.items()}


if __name__ == "__main__":
    inizializza_tabelle_finali()
