from __future__ import annotations

from pathlib import Path

from tabelle_finali import SCHEMI_TABELLE_FINALI, tabella_vuota
from utilita import CARTELLA_FINAL, prepara_cartelle, salva_tabella

TABELLE_FINALI = {
    "tabella_annuale_pensioni": CARTELLA_FINAL / "tabella_annuale_pensioni.csv",
    "tabella_gestioni": CARTELLA_FINAL / "tabella_gestioni.csv",
    "tabella_trasferimenti_inps": CARTELLA_FINAL / "tabella_trasferimenti_inps.csv",
    "tabella_territoriale": CARTELLA_FINAL / "tabella_territoriale.csv",
    "tabella_flussi_pensionamento": CARTELLA_FINAL / "tabella_flussi_pensionamento.csv",
    "tabella_confronto_europeo": CARTELLA_FINAL / "tabella_confronto_europeo.csv",
    "tabella_distribuzione_pensionati": CARTELLA_FINAL / "tabella_distribuzione_pensionati.csv",
    "tabella_demografia_lavoro": CARTELLA_FINAL / "tabella_demografia_lavoro.csv",
    "tabella_previdenza_complementare": CARTELLA_FINAL / "tabella_previdenza_complementare.csv",
    "tabella_parametri_sistema": CARTELLA_FINAL / "tabella_parametri_sistema.csv",
    "tabella_copertura_live": CARTELLA_FINAL / "tabella_copertura_live.csv",
}


def percorso_tabella_finale(nome_tabella: str) -> Path:
    """Restituisce il percorso locale di una tabella finale registrata."""
    if nome_tabella not in TABELLE_FINALI:
        raise KeyError(f"Tabella finale non registrata: {nome_tabella}")
    return TABELLE_FINALI[nome_tabella]


def inizializza_tabelle_finali(tabelle: dict[str, Path] | None = None) -> dict[str, str]:
    """Crea file CSV finali vuoti con schema stabile.

    Le trasformazioni specifiche popoleranno questi file quando le fonti saranno
    selezionate nelle whitelist. L'inizializzazione evita ambiguita' sul perimetro
    atteso di ciascuna analisi.
    """
    prepara_cartelle()
    tabelle_da_creare = tabelle or TABELLE_FINALI
    output = {}
    for nome_tabella, percorso in tabelle_da_creare.items():
        if nome_tabella not in SCHEMI_TABELLE_FINALI:
            raise KeyError(f"Schema mancante per tabella finale: {nome_tabella}")
        output[nome_tabella] = salva_tabella(tabella_vuota(nome_tabella), percorso)
    return {chiave: str(percorso) for chiave, percorso in output.items()}


if __name__ == "__main__":
    inizializza_tabelle_finali()
