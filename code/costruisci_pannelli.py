from __future__ import annotations

from pathlib import Path

from pannelli import pannello_annuale_vuoto, pannello_gestioni_vuoto, pannello_territoriale_vuoto
from utilita import CARTELLA_FINAL, prepara_cartelle, salva_tabella

PERCORSO_PANNELLO_ANNUALE = CARTELLA_FINAL / "pannello_annuale_pensioni.csv"
PERCORSO_PANNELLO_GESTIONI = CARTELLA_FINAL / "pannello_gestioni.csv"
PERCORSO_PANNELLO_TERRITORIALE = CARTELLA_FINAL / "pannello_territoriale.csv"


def inizializza_pannelli_finali(
    *,
    percorso_pannello_annuale: str | Path = PERCORSO_PANNELLO_ANNUALE,
    percorso_pannello_gestioni: str | Path = PERCORSO_PANNELLO_GESTIONI,
    percorso_pannello_territoriale: str | Path = PERCORSO_PANNELLO_TERRITORIALE,
) -> dict[str, str]:
    """Crea i pannelli finali vuoti."""
    prepara_cartelle()
    output = {
        "annuale": salva_tabella(pannello_annuale_vuoto(), percorso_pannello_annuale),
        "gestioni": salva_tabella(pannello_gestioni_vuoto(), percorso_pannello_gestioni),
        "territoriale": salva_tabella(pannello_territoriale_vuoto(), percorso_pannello_territoriale),
    }
    return {chiave: str(percorso) for chiave, percorso in output.items()}


if __name__ == "__main__":
    inizializza_pannelli_finali()
