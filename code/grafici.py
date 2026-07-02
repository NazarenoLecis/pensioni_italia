from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from utilita import CARTELLA_GRAFICI


def prepara_cartella_grafici(cartella_output: str | Path = CARTELLA_GRAFICI) -> Path:
    """Crea la cartella dei grafici e restituisce il percorso."""
    percorso = Path(cartella_output)
    percorso.mkdir(parents=True, exist_ok=True)
    return percorso


def controlla_colonne(tabella: pd.DataFrame, colonne: list[str]) -> None:
    """Interrompe l'analisi se mancano colonne necessarie."""
    mancanti = [colonna for colonna in colonne if colonna not in tabella.columns]
    if mancanti:
        raise ValueError(f"Colonne mancanti: {mancanti}")


def salva_grafico_corrente(percorso_output: str | Path) -> Path:
    """Salva il grafico matplotlib corrente e chiude la figura."""
    percorso = Path(percorso_output)
    percorso.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(percorso, dpi=180, bbox_inches="tight")
    plt.close()
    return percorso


def grafico_linea(
    tabella: pd.DataFrame,
    *,
    colonna_x: str,
    colonna_y: str,
    percorso_output: str | Path,
    titolo: str,
    etichetta_x: str = "",
    etichetta_y: str = "",
    colonna_gruppo: str | None = None,
    nota_fonte: str = "",
) -> Path:
    """Crea un grafico a linea.

    Flow:
    1. controlla che le colonne necessarie esistano;
    2. rimuove righe senza x o y;
    3. ordina la tabella;
    4. disegna una linea singola o una linea per gruppo;
    5. salva il PNG.
    """
    colonne = [colonna_x, colonna_y]
    if colonna_gruppo is not None:
        colonne.append(colonna_gruppo)
    controlla_colonne(tabella, colonne)

    dati = tabella.dropna(subset=[colonna_x, colonna_y]).copy()
    dati = dati.sort_values([colonna_gruppo, colonna_x] if colonna_gruppo else [colonna_x])

    plt.figure(figsize=(10, 6))
    if colonna_gruppo:
        for valore_gruppo, dati_gruppo in dati.groupby(colonna_gruppo):
            plt.plot(dati_gruppo[colonna_x], dati_gruppo[colonna_y], marker="o", label=str(valore_gruppo))
        plt.legend(frameon=False)
    else:
        plt.plot(dati[colonna_x], dati[colonna_y], marker="o")

    plt.title(titolo)
    plt.xlabel(etichetta_x or colonna_x)
    plt.ylabel(etichetta_y or colonna_y)
    if nota_fonte:
        plt.figtext(0.01, 0.01, nota_fonte, ha="left", fontsize=9)
    return salva_grafico_corrente(percorso_output)


def grafico_barre(
    tabella: pd.DataFrame,
    *,
    colonna_categoria: str,
    colonna_valore: str,
    percorso_output: str | Path,
    titolo: str,
    etichetta_x: str = "",
    etichetta_y: str = "",
    nota_fonte: str = "",
    primi_n: int | None = None,
) -> Path:
    """Crea un grafico a barre da una tabella categoriale."""
    controlla_colonne(tabella, [colonna_categoria, colonna_valore])
    dati = tabella.dropna(subset=[colonna_categoria, colonna_valore]).copy()
    dati = dati.sort_values(colonna_valore, ascending=False)
    if primi_n is not None:
        dati = dati.head(primi_n)

    plt.figure(figsize=(10, 6))
    plt.bar(dati[colonna_categoria].astype(str), dati[colonna_valore])
    plt.title(titolo)
    plt.xlabel(etichetta_x or colonna_categoria)
    plt.ylabel(etichetta_y or colonna_valore)
    plt.xticks(rotation=45, ha="right")
    if nota_fonte:
        plt.figtext(0.01, 0.01, nota_fonte, ha="left", fontsize=9)
    return salva_grafico_corrente(percorso_output)
