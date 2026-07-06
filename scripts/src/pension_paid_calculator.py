from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from config import ANALYTIC_OUTPUT_PATHS, SCENARI_CALCOLATORE_PATH
from utils import prepare_directories, read_csv_optional, save_table

DEFAULT_SCENARIO = {
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


def build_contribution_career(scenario: dict[str, float | int]) -> pd.DataFrame:
    """Costruisce una carriera contributiva teorica anno per anno.

    Il criterio e' didattico: salario indicizzato, aliquota media e
    capitalizzazione figurativa. Le ipotesi possono essere sostituite da serie
    storiche quando disponibili.
    """
    start_year = int(scenario["anno_inizio"])
    retirement_year = int(scenario["anno_pensione"])
    starting_salary = float(scenario["salario_iniziale"])
    salary_growth = float(scenario["crescita_salario_annua"])
    contribution_rate = float(scenario["aliquota_contributiva"])
    capitalization_rate = float(scenario["tasso_capitalizzazione"])

    rows = []
    accrued_capital = 0.0
    for index, year in enumerate(range(start_year, retirement_year)):
        salary = starting_salary * ((1 + salary_growth) ** index)
        contributions = salary * contribution_rate
        accrued_capital = accrued_capital * (1 + capitalization_rate) + contributions
        rows.append(
            {
                "anno": year,
                "indice_anno": index + 1,
                "salario": salary,
                "aliquota_contributiva": contribution_rate,
                "contributi": contributions,
                "tasso_capitalizzazione": capitalization_rate,
                "montante_contributivo": accrued_capital,
            }
        )
    return pd.DataFrame(rows)


def calculate_paid_pension_metrics(career: pd.DataFrame, scenario: dict[str, float | int]) -> pd.DataFrame:
    """Calcola pensione teorica sostenibile e quota non coperta."""
    if career.empty:
        raise ValueError("La carriera contributiva e' vuota.")
    residual_life = float(scenario["speranza_vita_residua"])
    if residual_life <= 0:
        raise ValueError("La speranza di vita residua deve essere positiva.")

    last_salary = float(career["salario"].iloc[-1])
    accrued_capital = float(career["montante_contributivo"].iloc[-1])
    total_contributions = float(career["contributi"].sum())
    theoretical_pension = accrued_capital / residual_life
    theoretical_replacement_rate = theoretical_pension / last_salary
    actual_replacement_rate = float(scenario["tasso_sostituzione_effettivo"])
    actual_pension = last_salary * actual_replacement_rate
    annual_gap = actual_pension - theoretical_pension
    uncovered_share = max(annual_gap, 0.0) / actual_pension if actual_pension > 0 else 0.0

    total_pension_spending = float(scenario["spesa_pensionistica_totale"])
    pensioners = float(scenario["numero_pensionati"])
    workers = float(scenario["numero_occupati"])
    total_contributions_aggregate = float(scenario["contributi_totali"])
    uncovered_spending = total_pension_spending * uncovered_share

    return pd.DataFrame(
        [
            {
                "anni_contribuzione": float(len(career)),
                "ultimo_salario": last_salary,
                "contributi_versati": total_contributions,
                "montante_contributivo": accrued_capital,
                "speranza_vita_residua": residual_life,
                "pensione_annua_teorica": theoretical_pension,
                "tasso_sostituzione_teorico": theoretical_replacement_rate,
                "tasso_sostituzione_effettivo": actual_replacement_rate,
                "pensione_annua_effettiva": actual_pension,
                "differenza_annua": annual_gap,
                "quota_pensione_non_coperta": uncovered_share,
                "spesa_pensionistica_totale": total_pension_spending,
                "spesa_non_coperta_stimata": uncovered_spending,
                "quota_non_coperta_per_pensionato": uncovered_spending / pensioners if pensioners else 0.0,
                "quota_non_coperta_per_occupato": uncovered_spending / workers if workers else 0.0,
                "contributi_per_occupato": total_contributions_aggregate / workers if workers else 0.0,
            }
        ]
    )


def read_scenario(scenario_id: str = "scenario_video_didattico") -> dict[str, float | int]:
    """Legge uno scenario dal file metadata e lo fonde con i valori di default."""
    scenario = dict(DEFAULT_SCENARIO)
    scenarios = read_csv_optional(SCENARI_CALCOLATORE_PATH)
    if scenarios.empty or "scenario_id" not in scenarios.columns:
        return scenario
    selected = scenarios[scenarios["scenario_id"].astype(str).eq(scenario_id)]
    if selected.empty:
        return scenario
    row = selected.iloc[0].to_dict()
    for key in scenario:
        if key in row and pd.notna(row[key]):
            scenario[key] = row[key]
    return scenario


def run_pension_paid_calculator(scenario_id: str = "scenario_video_didattico") -> pd.DataFrame:
    """Esegue il calcolatore e salva carriera e risultati in output/data/final."""
    prepare_directories()
    scenario = read_scenario(scenario_id)
    career = build_contribution_career(scenario)
    results = calculate_paid_pension_metrics(career, scenario)
    save_table(career, ANALYTIC_OUTPUT_PATHS["calcolatore_pensione_pagata_carriera"])
    save_table(results, ANALYTIC_OUTPUT_PATHS["calcolatore_pensione_pagata_base"])
    return results


if __name__ == "__main__":
    print(run_pension_paid_calculator().to_string(index=False))
