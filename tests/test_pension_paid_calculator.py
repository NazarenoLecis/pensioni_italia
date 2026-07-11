from __future__ import annotations

from pathlib import Path
import sys
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SRC = SCRIPTS / "src"
for path in [SCRIPTS, SRC]:
    if str(path) not in sys.path:
        sys.path.append(str(path))

from pension_paid_calculator import (  # noqa: E402
    build_accurate_career,
    build_simplified_career,
    calculate_paid_pension_metrics,
    synthetic_mortality_table,
    transformation_coefficient,
    weighted_fpld_rate_for_year,
)


def scenario(**overrides):
    base = {
        "scenario_id": "test",
        "descrizione": "test",
        "anno_nascita": 1960,
        "sesso": "T",
        "categoria_id": "generica_fpld",
        "anno_inizio": 1996,
        "anno_fine": 2024,
        "anno_pensione": 2025,
        "eta_pensione": 65,
        "mesi_eta_pensione": 0,
        "ral_iniziale": 20_000,
        "ral_finale": 40_000,
        "livello_iniziale": "medio",
        "livello_finale": "medio",
        "progressione": "media",
        "anni_contribuiti": 29,
        "percentuale_lavoro": 100,
        "mesi_lavorati_annui": 12,
        "pensione_lorda_mensile_effettiva": 2_000,
        "mensilita_pensione": 13,
        "anno_riferimento_pensione": 2025,
        "rivalutazione_futura_pensione": "nessuna",
        "tasso_inflazione_futura": 0.02,
    }
    base.update(overrides)
    return base


class PensionPaidCalculatorTests(unittest.TestCase):
    def test_post_1995_complete_career_has_no_aggregate_spending_columns(self):
        career = build_simplified_career(scenario())
        result = calculate_paid_pension_metrics(career, scenario(), synthetic_mortality_table(2024))
        self.assertGreater(float(result["montante_contributivo"].iloc[0]), 0)
        self.assertGreater(float(result["pensione_contributiva_annua_equivalente"].iloc[0]), 0)
        self.assertNotIn("spesa_non_coperta_stimata", result.columns)
        self.assertNotIn("quota_non_coperta_per_occupato", result.columns)

    def test_annual_rate_is_weighted_when_rate_changes_during_year(self):
        periods = pd.DataFrame(
            [
                {
                    "periodo_dal": "2000-01-01",
                    "periodo_al": "2000-06-30",
                    "aliquota_totale": 10,
                    "aliquota_lavoratore": 4,
                    "aliquota_datore_lavoro": 6,
                },
                {
                    "periodo_dal": "2000-07-01",
                    "periodo_al": "2000-12-31",
                    "aliquota_totale": 20,
                    "aliquota_lavoratore": 8,
                    "aliquota_datore_lavoro": 12,
                },
            ]
        )
        rate = weighted_fpld_rate_for_year(2000, periods)
        self.assertAlmostEqual(rate.aliquota_finanziamento, 0.15027, places=4)
        self.assertEqual(rate.aliquota_computo, 0.33)

    def test_part_time_reduces_taxable_and_contributions(self):
        full = build_simplified_career(scenario(percentuale_lavoro=100))
        part = build_simplified_career(scenario(percentuale_lavoro=50))
        self.assertAlmostEqual(
            float(part["imponibile_previdenziale"].sum()),
            float(full["imponibile_previdenziale"].sum()) / 2,
            delta=1,
        )
        self.assertLess(float(part["contributi_finanziari"].sum()), float(full["contributi_finanziari"].sum()))

    def test_monthly_interpolation_of_transformation_coefficient(self):
        coeff_65 = transformation_coefficient(2025, 65, 0).coefficiente
        coeff_66 = transformation_coefficient(2025, 66, 0).coefficiente
        coeff_65_6 = transformation_coefficient(2025, 65, 6).coefficiente
        self.assertAlmostEqual(coeff_65_6, (coeff_65 + coeff_66) / 2, places=6)

    def test_actual_pension_below_counterfactual_gives_negative_difference(self):
        low = scenario(pensione_lorda_mensile_effettiva=500)
        career = build_simplified_career(low)
        result = calculate_paid_pension_metrics(career, low, synthetic_mortality_table(2024))
        self.assertLess(float(result["differenza_annua_lorda"].iloc[0]), 0)

    def test_simplified_and_accurate_match_when_taxables_match(self):
        small = scenario(anno_inizio=2020, anno_fine=2022, anno_pensione=2023, eta_pensione=63, anno_nascita=1960, anni_contribuiti=3)
        simple = build_simplified_career(small)
        annual_rows = [
            {"anno": int(row.anno), "imponibile_previdenziale": float(row.imponibile_previdenziale)}
            for row in simple.itertuples()
        ]
        accurate = build_accurate_career(annual_rows, small)
        self.assertAlmostEqual(
            float(simple["montante_fine_anno"].iloc[-1]),
            float(accurate["montante_fine_anno"].iloc[-1]),
            places=6,
        )

    def test_categories_without_parameters_are_not_silent_substitutes(self):
        with self.assertRaises(ValueError):
            build_simplified_career(scenario(categoria_id="gestione_separata_professionisti"))


if __name__ == "__main__":
    unittest.main()
