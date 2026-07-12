from __future__ import annotations

from pathlib import Path
import sys
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
CALCULATOR_SRC = ROOT / "calcolatore" / "src"
for path in [SCRIPTS, CALCULATOR_SRC]:
    if str(path) not in sys.path:
        sys.path.append(str(path))

from pension_paid_calculator import (  # noqa: E402
    build_accurate_career,
    build_simplified_career,
    calculate_paid_pension_metrics,
    capitalization_for_year,
    contribution_months_by_year,
    artisan_rate_for_year,
    merchant_rate_for_year,
    pension_gross_annual_from_net,
    pension_net_annual_estimate,
    remaining_life_expectancy,
    synthetic_mortality_table,
    transformation_coefficient,
    weighted_fpld_rate_for_year,
)


# Fixture dei test: il calcolatore reale non usa questi valori fissi.
# Ogni test parte da uno scenario completo e sovrascrive solo i campi rilevanti.
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
    def test_capitalization_is_calculated_from_nominal_gdp_levels(self):
        info = capitalization_for_year(2025)
        expected = (info.pil_finale_milioni / info.pil_iniziale_milioni) ** (1 / 5) - 1
        self.assertAlmostEqual(info.tasso, expected, places=12)
        self.assertEqual(info.pil_anno_finale, 2024)
        self.assertEqual(info.pil_anno_iniziale, 2019)
        self.assertEqual(info.fonte_id, "istat_pil_nominale_sdmx")

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

    def test_contributed_years_change_taxable_even_with_seasonal_months(self):
        full_span = scenario(anno_inizio=1984, anno_fine=2024, anni_contribuiti=41, mesi_lavorati_annui=8)
        shorter = scenario(anno_inizio=1984, anno_fine=2024, anni_contribuiti=37, mesi_lavorati_annui=8)
        career_41 = build_simplified_career(full_span)
        career_37 = build_simplified_career(shorter)
        self.assertGreater(float(career_41["imponibile_previdenziale"].sum()), float(career_37["imponibile_previdenziale"].sum()))
        self.assertGreater(float(career_41["montante_fine_anno"].iloc[-1]), float(career_37["montante_fine_anno"].iloc[-1]))
        self.assertEqual(float(career_37.loc[career_37["anno"].eq(1984), "mesi_lavorati"].iloc[0]), 0)
        self.assertEqual(float(career_37.loc[career_37["anno"].eq(1987), "mesi_lavorati"].iloc[0]), 0)
        self.assertEqual(float(career_37.loc[career_37["anno"].eq(1988), "mesi_lavorati"].iloc[0]), 8)

    def test_contribution_months_are_allocated_backwards_from_retirement(self):
        allocation = contribution_months_by_year(list(range(1980, 2022)), 37, 12)
        self.assertEqual(allocation[1980], 0)
        self.assertEqual(allocation[1984], 0)
        self.assertEqual(allocation[1985], 12)
        self.assertEqual(allocation[2021], 12)

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

    def test_actuarial_coverage_uses_required_capital_from_coefficient(self):
        short = scenario(anno_inizio=1997, anni_contribuiti=28, ral_finale=44_000, pensione_lorda_mensile_effettiva=2_000)
        career = build_simplified_career(short)
        result = calculate_paid_pension_metrics(career, short, synthetic_mortality_table(2024)).iloc[0]
        required = float(result["pensione_effettiva_annua_lorda"]) / float(result["coefficiente_trasformazione"])
        self.assertAlmostEqual(float(result["capitale_attuariale_necessario"]), required, places=6)
        self.assertAlmostEqual(
            float(result["copertura_attuariale"]),
            float(result["montante_contributivo"]) / required,
            places=6,
        )

    def test_future_indexation_increases_actuarial_required_capital(self):
        flat = scenario(rivalutazione_futura_pensione="nessuna", tasso_inflazione_futura=0.02)
        indexed = scenario(rivalutazione_futura_pensione="inflazione_costante", tasso_inflazione_futura=0.02)
        career = build_simplified_career(flat)
        flat_result = calculate_paid_pension_metrics(career, flat, synthetic_mortality_table(2024)).iloc[0]
        indexed_result = calculate_paid_pension_metrics(career, indexed, synthetic_mortality_table(2024)).iloc[0]
        self.assertGreater(float(indexed_result["fattore_capitale_perequazione"]), 1)
        self.assertGreater(float(indexed_result["capitale_attuariale_necessario"]), float(flat_result["capitale_attuariale_necessario"]))
        self.assertLess(float(indexed_result["copertura_attuariale"]), float(flat_result["copertura_attuariale"]))
        self.assertGreater(float(indexed_result["valore_atteso_prestazioni_lorde"]), float(flat_result["valore_atteso_prestazioni_lorde"]))

    def test_worker_and_employer_contributions_are_reported_separately(self):
        career = build_simplified_career(scenario(anno_inizio=2020, anno_fine=2024, anni_contribuiti=5))
        self.assertIn("contributi_lavoratore", career.columns)
        self.assertIn("contributi_datore", career.columns)
        self.assertAlmostEqual(
            float((career["contributi_lavoratore"] + career["contributi_datore"]).sum()),
            float(career["contributi_finanziari"].sum()),
            delta=5,
        )
        result = calculate_paid_pension_metrics(career, scenario(anno_inizio=2020, anno_fine=2024, anni_contribuiti=5), synthetic_mortality_table(2024)).iloc[0]
        self.assertGreater(float(result["contributi_lavoratore_versati"]), 0)
        self.assertGreater(float(result["contributi_datore_versati"]), 0)

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

    def test_fpld_sector_category_is_operational_and_named(self):
        career = build_simplified_career(scenario(categoria_id="metalmeccanici_industria"))
        self.assertEqual(set(career["categoria"]), {"metalmeccanici_industria"})
        self.assertEqual(set(career["gestione"]), {"FPLD lavoratori dipendenti"})

    def test_artisan_category_uses_its_own_historical_rates(self):
        self.assertEqual(artisan_rate_for_year(1996).aliquota_computo, 0.15)
        self.assertEqual(artisan_rate_for_year(2012).aliquota_computo, 0.213)
        self.assertEqual(artisan_rate_for_year(2025).aliquota_computo, 0.24)
        artisan = build_simplified_career(scenario(categoria_id="artigiani"))
        employee = build_simplified_career(scenario(categoria_id="generica_fpld"))
        self.assertEqual(set(artisan["gestione"]), {"Gestione speciale artigiani"})
        self.assertLess(float(artisan["montante_fine_anno"].iloc[-1]), float(employee["montante_fine_anno"].iloc[-1]))

    def test_artisan_percentage_series_does_not_invent_pre_1990_rates(self):
        with self.assertRaises(ValueError):
            build_simplified_career(scenario(categoria_id="artigiani", anno_inizio=1989))

    def test_merchant_financing_includes_non_pension_component(self):
        merchant = merchant_rate_for_year(2025)
        self.assertEqual(merchant.aliquota_computo, 0.24)
        self.assertEqual(merchant.aliquota_finanziamento, 0.2448)
        career = build_simplified_career(scenario(categoria_id="commercianti"))
        self.assertEqual(set(career["gestione"]), {"Gestione speciale commercianti"})

    def test_public_employee_profiles_are_distinct(self):
        state = build_simplified_career(scenario(categoria_id="pubblico_impiego"))
        local = build_simplified_career(scenario(categoria_id="pubblico_enti_locali"))
        self.assertEqual(float(state["aliquota_computo"].iloc[-1]), 0.33)
        self.assertEqual(float(local["aliquota_computo"].iloc[-1]), 0.3265)
        self.assertGreater(float(state["montante_fine_anno"].iloc[-1]), float(local["montante_fine_anno"].iloc[-1]))

    def test_agricultural_profiles_use_different_bases_and_rates(self):
        employee_scenario = scenario(categoria_id="agricoltura", anno_inizio=1998, anni_contribuiti=27)
        employee = build_simplified_career(employee_scenario)
        self.assertAlmostEqual(float(employee["aliquota_finanziamento"].iloc[-1]), 0.301, places=6)
        self.assertEqual(float(employee["aliquota_computo"].iloc[-1]), 0.33)
        self_employed_scenario = scenario(categoria_id="agricoli_autonomi", anno_inizio=2012, anni_contribuiti=13)
        self_employed = build_simplified_career(self_employed_scenario)
        self.assertEqual(float(self_employed["aliquota_computo"].iloc[-1]), 0.24)

    def test_net_to_gross_estimate_round_trips(self):
        annual_gross = 32_500.0
        annual_net = pension_net_annual_estimate(annual_gross, 2026)
        reconstructed = pension_gross_annual_from_net(annual_net, 2026)
        self.assertAlmostEqual(reconstructed, annual_gross, places=4)

    def test_retirement_year_selects_historical_coefficient_table(self):
        old = transformation_coefficient(2009, 65, 0)
        revised = transformation_coefficient(2010, 65, 0)
        current = transformation_coefficient(2025, 65, 0)
        self.assertEqual(old.coefficiente, 0.06136)
        self.assertEqual(revised.coefficiente, 0.0562)
        self.assertEqual(current.coefficiente, 0.0525)

    def test_dates_drive_retirement_age_and_timeline_metrics(self):
        dated = scenario(
            data_nascita="1960-06-15",
            data_pensionamento="2025-02-15",
            anno_nascita=1960,
            anno_pensione=2025,
            eta_pensione=64,
            mesi_eta_pensione=8,
        )
        career = build_simplified_career(dated)
        result = calculate_paid_pension_metrics(career, dated, synthetic_mortality_table(2024)).iloc[0]
        self.assertEqual(result["data_nascita"], "1960-06-15")
        self.assertEqual(result["data_pensionamento"], "2025-02-15")
        expected_age = 65 + remaining_life_expectancy(synthetic_mortality_table(2024), "T", 65)
        self.assertEqual(int(result["eta_base_speranza_vita"]), 65)
        self.assertAlmostEqual(float(result["eta_attesa"]), expected_age, places=6)
        self.assertGreater(float(result["anni_dal_pensionamento"]), 1)
        self.assertAlmostEqual(
            float(result["differenza_mensile_lorda"]),
            (
                float(result["pensione_effettiva_annua_lorda_anno_riferimento"])
                - float(result["pensione_contributiva_annua_equivalente_anno_riferimento"])
            )
            / 13,
            places=6,
        )


if __name__ == "__main__":
    unittest.main()
