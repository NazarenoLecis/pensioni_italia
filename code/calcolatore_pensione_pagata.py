from __future__ import annotations

from pathlib import Path

import pandas as pd

from utilita import CARTELLA_FINAL, prepara_cartelle, salva_tabella

PERCORSO_OUTPUT_BASE = CARTELLA_FINAL / "calcolatore_pensione_pagata_base.csv"
PERCORSO_OUTPUT_CARRIERA = CARTELLA_FINAL / "calcolatore_pensione_pagata_carriera.csv"

SCENARIO_BASE = {
    "anno_inizio": 1985,
    "anno_pensione": 2025,
    "salario_iniziale": 100.0,
    "crescita_salario_annua": 0.03,
    "aliquota_contributiva": 0.31,
    "tasso_capitalizzazione": 0.03,
    "eta_pensione": 64,
    "speranza_vita_residua": 22.0,
    "tasso_sostituzione_effettivo": 0.81,
    "spesa_pensionistica_totale": 347_000_000_000.0,
    "numero_pensionati": 16_000_000.0,
    "numero_occupati": 22_837_000.0,
    "contributi_totali": 269_000_000_000.0,
}


def costruisci_carriera(
    anno_inizio: int,
    anno_pensione: int,
    salario_iniziale: float,
    crescita_salario_annua: float,
    aliquota_contributiva: float,
    tasso_capitalizzazione: float,
) -> pd.DataFrame:
    """Costruisce la carriera contributiva teorica anno per anno.

    Il modello e' didattico. Usa un salario iniziale indicizzato, una aliquota
    contributiva media e un tasso di capitalizzazione figurativo. Le tre serie
    possono essere sostituite in futuro da dati storici effettivi.
    """
    righe: list[dict[str, float | int]] = []
    montante = 0.0

    for indice, anno in enumerate(range(anno_inizio, anno_pensione)):
        salario = salario_iniziale * ((1.0 + crescita_salario_annua) ** indice)
        contributi = salario * aliquota_contributiva
        montante = montante * (1.0 + tasso_capitalizzazione) + contributi
        righe.append(
            {
                "anno": anno,
                "indice_anno": indice + 1,
                "salario": salario,
                "aliquota_contributiva": aliquota_contributiva,
                "contributi": contributi,
                "tasso_capitalizzazione": tasso_capitalizzazione,
                "montante_contributivo": montante,
            }
        )

    return pd.DataFrame(righe)


def calcola_risultati(
    carriera: pd.DataFrame,
    speranza_vita_residua: float,
    tasso_sostituzione_effettivo: float,
    spesa_pensionistica_totale: float | None = None,
    numero_pensionati: float | None = None,
    numero_occupati: float | None = None,
    contributi_totali: float | None = None,
) -> dict[str, float]:
    """Calcola pensione teoricamente coperta e differenza rispetto al tasso effettivo."""
    if carriera.empty:
        raise ValueError("La carriera contributiva e' vuota.")
    if speranza_vita_residua <= 0:
        raise ValueError("La speranza di vita residua deve essere positiva.")

    ultimo_salario = float(carriera["salario"].iloc[-1])
    montante = float(carriera["montante_contributivo"].iloc[-1])
    contributi_versati = float(carriera["contributi"].sum())

    pensione_annua_teorica = montante / speranza_vita_residua
    tasso_sostituzione_teorico = pensione_annua_teorica / ultimo_salario
    pensione_annua_effettiva = ultimo_salario * tasso_sostituzione_effettivo
    differenza_annua = pensione_annua_effettiva - pensione_annua_teorica

    quota_non_coperta = 0.0
    if pensione_annua_effettiva > 0:
        quota_non_coperta = max(differenza_annua, 0.0) / pensione_annua_effettiva

    risultati = {
        "anni_contribuzione": float(len(carriera)),
        "ultimo_salario": ultimo_salario,
        "contributi_versati": contributi_versati,
        "montante_contributivo": montante,
        "speranza_vita_residua": float(speranza_vita_residua),
        "pensione_annua_teorica": pensione_annua_teorica,
        "tasso_sostituzione_teorico": tasso_sostituzione_teorico,
        "tasso_sostituzione_effettivo": float(tasso_sostituzione_effettivo),
        "pensione_annua_effettiva": pensione_annua_effettiva,
        "differenza_annua": differenza_annua,
        "quota_pensione_non_coperta": quota_non_coperta,
    }

    if spesa_pensionistica_totale is not None:
        spesa_non_coperta = float(spesa_pensionistica_totale) * quota_non_coperta
        risultati["spesa_pensionistica_totale"] = float(spesa_pensionistica_totale)
        risultati["spesa_non_coperta_stimata"] = spesa_non_coperta

        if numero_pensionati:
            risultati["quota_non_coperta_per_pensionato"] = spesa_non_coperta / float(numero_pensionati)
        if numero_occupati:
            risultati["quota_non_coperta_per_occupato"] = spesa_non_coperta / float(numero_occupati)
        if contributi_totali and numero_occupati:
            contributi_per_occupato = float(contributi_totali) / float(numero_occupati)
            risultati["contributi_per_occupato"] = contributi_per_occupato
            risultati["quota_non_coperta_su_contributi_per_occupato"] = (
                risultati.get("quota_non_coperta_per_occupato", 0.0) / contributi_per_occupato
                if contributi_per_occupato > 0 else 0.0
            )

    return risultati


def esegui_scenario(scenario: dict[str, float | int] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Esegue uno scenario e restituisce carriera e risultati in formato tabellare."""
    parametri = dict(SCENARIO_BASE)
    if scenario:
        parametri.update(scenario)

    carriera = costruisci_carriera(
        anno_inizio=int(parametri["anno_inizio"]),
        anno_pensione=int(parametri["anno_pensione"]),
        salario_iniziale=float(parametri["salario_iniziale"]),
        crescita_salario_annua=float(parametri["crescita_salario_annua"]),
        aliquota_contributiva=float(parametri["aliquota_contributiva"]),
        tasso_capitalizzazione=float(parametri["tasso_capitalizzazione"]),
    )
    risultati = calcola_risultati(
        carriera=carriera,
        speranza_vita_residua=float(parametri["speranza_vita_residua"]),
        tasso_sostituzione_effettivo=float(parametri["tasso_sostituzione_effettivo"]),
        spesa_pensionistica_totale=float(parametri["spesa_pensionistica_totale"]),
        numero_pensionati=float(parametri["numero_pensionati"]),
        numero_occupati=float(parametri["numero_occupati"]),
        contributi_totali=float(parametri["contributi_totali"]),
    )
    tabella_risultati = pd.DataFrame([risultati])
    return carriera, tabella_risultati


def esegui_calcolatore_base(
    percorso_output_base: str | Path = PERCORSO_OUTPUT_BASE,
    percorso_output_carriera: str | Path = PERCORSO_OUTPUT_CARRIERA,
) -> pd.DataFrame:
    """Esegue lo scenario base e salva risultati e carriera in data/final."""
    prepara_cartelle()
    carriera, risultati = esegui_scenario()
    salva_tabella(carriera, percorso_output_carriera)
    salva_tabella(risultati, percorso_output_base)
    return risultati


if __name__ == "__main__":
    output = esegui_calcolatore_base()
    print(output.to_string(index=False))
