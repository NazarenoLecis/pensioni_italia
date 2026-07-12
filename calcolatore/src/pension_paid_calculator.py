from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
import math
import sys
import zipfile

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from config import ANALYTIC_OUTPUT_PATHS, FINAL_TABLE_PATHS, RAW_DATA_DIR, SCENARI_CALCOLATORE_PATH
from utils import prepare_directories, read_csv_optional, save_table


CURRENT_YEAR = datetime.now().year
FPLD_PERIODS_PATH = Path(__file__).resolve().parents[2] / "output" / "data" / "clean" / "aliquote_ivs_fpld_periodi.csv"
CAPITALIZATION_RATES_PATH = ROOT / "output" / "data" / "clean" / "tassi_capitalizzazione_montante.csv"
CONTRACT_WAGES_PATH = ROOT / "output" / "data" / "clean" / "retribuzioni_contrattuali_ccnl.csv"
MORTALITY_RAW_DIR = RAW_DATA_DIR / "istat_mortalita"
DEFAULT_MORTALITY_YEAR = 2025
LIFE_EXPECTANCY_BASE_AGE = 65


def load_capitalization_table() -> pd.DataFrame:
    if not CAPITALIZATION_RATES_PATH.exists():
        from download_capitalization_data import main as download_capitalization_data

        download_capitalization_data()
    table = pd.read_csv(CAPITALIZATION_RATES_PATH)
    numeric_columns = [
        "anno",
        "pil_finale_milioni",
        "pil_iniziale_milioni",
        "tasso_capitalizzazione",
        "coefficiente_rivalutazione",
    ]
    for column in numeric_columns:
        table[column] = pd.to_numeric(table[column], errors="raise")
    table["anno"] = table["anno"].astype(int)
    expected = (table["pil_finale_milioni"] / table["pil_iniziale_milioni"]) ** (1 / 5) - 1
    if not (expected - table["tasso_capitalizzazione"]).abs().lt(1e-12).all():
        raise ValueError("Tassi incoerenti con i livelli di PIL nominale scaricati da ISTAT")
    if not (
        table["coefficiente_rivalutazione"] - 1 - table["tasso_capitalizzazione"]
    ).abs().lt(1e-12).all():
        raise ValueError("Coefficienti incoerenti: il coefficiente deve essere 1 + tasso")
    return table.sort_values("anno").reset_index(drop=True)


_capitalization_table = load_capitalization_table()
CAPITALIZATION_RATES = dict(
    zip(_capitalization_table["anno"], _capitalization_table["tasso_capitalizzazione"])
)


def load_contract_wages() -> pd.DataFrame:
    if not CONTRACT_WAGES_PATH.exists():
        from download_contract_wages import main as download_contract_wages

        download_contract_wages()
    table = pd.read_csv(CONTRACT_WAGES_PATH)
    table["anno"] = pd.to_numeric(table["anno"], errors="raise").astype(int)
    table["indice_retribuzione_contrattuale"] = pd.to_numeric(
        table["indice_retribuzione_contrattuale"], errors="raise"
    )
    if table.duplicated(["indice_ccnl_id", "anno"]).any():
        raise ValueError("Anni duplicati nelle serie ISTAT delle retribuzioni contrattuali")
    return table.sort_values(["indice_ccnl_id", "anno"]).reset_index(drop=True)


_contract_wages_table = load_contract_wages()


# Aliquota IVS ordinaria per titolari artigiani e collaboratori con piu' di 21 anni.
# Prima del luglio 1990 la contribuzione seguiva classi e importi fissi non
# confrontabili con un'aliquota applicata direttamente al reddito imponibile.
ARTISAN_RATES: dict[int, float] = {
    1990: 0.1200,
    1991: 0.1275,
    1992: 0.1350,
    1993: 0.1429,
    1994: 0.1500,
    1995: 0.1500,
    1996: 0.1500,
    1997: 0.1500,
    1998: 0.1580,
    1999: 0.1600,
    2000: 0.1620,
    2001: 0.1640,
    2002: 0.1660,
    2003: 0.1680,
    2004: 0.1700,
    2005: 0.1720,
    2006: 0.1740,
    2007: 0.1950,
    2008: 0.2000,
    2009: 0.2000,
    2010: 0.2000,
    2011: 0.2000,
    2012: 0.2130,
    2013: 0.2175,
    2014: 0.2220,
    2015: 0.2265,
    2016: 0.2310,
    2017: 0.2355,
}
for _year in range(2018, max(CURRENT_YEAR, 2026) + 1):
    ARTISAN_RATES[_year] = 0.2400


# La gestione commercianti segue l'IVS degli artigiani, con una componente
# aggiuntiva che finanzia l'indennizzo per cessazione dell'attivita' e non
# incrementa il montante pensionistico.
MERCHANT_ADDITIONAL_RATES: dict[int, float] = {
    **{year: 0.0 for year in range(1990, 1996)},
    **{year: 0.0009 for year in range(1996, 2022)},
    **{year: 0.0048 for year in range(2022, max(CURRENT_YEAR, 2026) + 1)},
}

PUBLIC_PENSION_PROFILES: dict[str, dict[str, float | str]] = {
    "pubblico_ctps": {
        "aliquota": 0.3300,
        "quota_lavoratore": 0.0880,
        "quota_datore": 0.2420,
        "gestione": "Gestione dipendenti pubblici - CTPS",
    },
    "pubblico_enti_locali": {
        "aliquota": 0.3265,
        "quota_lavoratore": 0.0885,
        "quota_datore": 0.2380,
        "gestione": "Gestione dipendenti pubblici - CPDEL/CPS/CPI/CPUG",
    },
}

AGRICULTURAL_EMPLOYEE_RATES: dict[int, float] = {
    year: 0.2490 + 0.0020 * (year - 1998)
    for year in range(1998, max(CURRENT_YEAR, 2026) + 1)
}

AGRICULTURAL_SELF_EMPLOYED_RATES: dict[int, float] = {
    2012: 0.216,
    2013: 0.220,
    2014: 0.224,
    2015: 0.228,
    2016: 0.232,
    2017: 0.236,
}
for _year in range(2018, max(CURRENT_YEAR, 2026) + 1):
    AGRICULTURAL_SELF_EMPLOYED_RATES[_year] = 0.240


COEFFICIENT_PERIODS: list[dict[str, object]] = [
    {
        "periodo_dal": 1996,
        "periodo_al": 2009,
        "fonte_id": "inps_coefficiente_trasformazione_storico",
        "norma": "Legge 8 agosto 1995, n. 335",
        "note": "Coefficienti originari della riforma Dini, validi dal 1996 al 2009; dai 65 anni si applicava il valore massimo della tabella.",
        "coefficients": {57: 4.720, 58: 4.860, 59: 5.006, 60: 5.163, 61: 5.334, 62: 5.514, 63: 5.706, 64: 5.911, 65: 6.136},
    },
    {
        "periodo_dal": 2010,
        "periodo_al": 2012,
        "fonte_id": "ministero_lavoro_coefficiente_trasformazione_storico",
        "norma": "Legge 24 dicembre 2007, n. 247",
        "note": "Prima revisione dei coefficienti, valida dal 2010 al 2012; dai 65 anni si applicava il valore massimo della tabella.",
        "coefficients": {57: 4.419, 58: 4.538, 59: 4.664, 60: 4.798, 61: 4.940, 62: 5.093, 63: 5.257, 64: 5.432, 65: 5.620},
    },
    {
        "periodo_dal": 2013,
        "periodo_al": 2015,
        "fonte_id": "ministero_lavoro_coefficiente_trasformazione_storico",
        "norma": "Decreto direttoriale 15 maggio 2012",
        "note": "Coefficienti validi dal 2013 al 2015.",
        "coefficients": {57: 4.304, 58: 4.416, 59: 4.535, 60: 4.661, 61: 4.796, 62: 4.940, 63: 5.094, 64: 5.259, 65: 5.435, 66: 5.624, 67: 5.826, 68: 6.046, 69: 6.283, 70: 6.541},
    },
    {
        "periodo_dal": 2016,
        "periodo_al": 2018,
        "fonte_id": "ministero_lavoro_coefficiente_trasformazione_storico",
        "norma": "Decreto interministeriale 22 giugno 2015",
        "note": "Coefficienti validi dal 2016 al 2018.",
        "coefficients": {57: 4.246, 58: 4.354, 59: 4.468, 60: 4.589, 61: 4.719, 62: 4.856, 63: 5.002, 64: 5.159, 65: 5.326, 66: 5.506, 67: 5.700, 68: 5.910, 69: 6.135, 70: 6.378},
    },
    {
        "periodo_dal": 2019,
        "periodo_al": 2020,
        "fonte_id": "ministero_lavoro_coefficiente_trasformazione_storico",
        "norma": "Decreto interministeriale 15 maggio 2018",
        "note": "Coefficienti validi dal 2019 al 2020.",
        "coefficients": {57: 4.200, 58: 4.304, 59: 4.414, 60: 4.532, 61: 4.657, 62: 4.790, 63: 4.932, 64: 5.083, 65: 5.245, 66: 5.419, 67: 5.604, 68: 5.804, 69: 6.021, 70: 6.257, 71: 6.513},
    },
    {
        "periodo_dal": 2021,
        "periodo_al": 2022,
        "fonte_id": "inps_coefficiente_trasformazione",
        "norma": "DM 1 giugno 2020",
        "note": "Tabella pubblicata da INPS per i coefficienti in vigore dal 1 gennaio 2021.",
        "coefficients": {
            57: 4.186,
            58: 4.289,
            59: 4.399,
            60: 4.515,
            61: 4.639,
            62: 4.770,
            63: 4.910,
            64: 5.060,
            65: 5.220,
            66: 5.391,
            67: 5.575,
            68: 5.772,
            69: 5.985,
            70: 6.215,
            71: 6.466,
        },
    },
    {
        "periodo_dal": 2023,
        "periodo_al": 2024,
        "fonte_id": "ministero_lavoro_coefficiente_trasformazione",
        "norma": "Decreto direttoriale 1 dicembre 2022",
        "note": "Valori ministeriali 2023-2024 riportati nella tabella storica del calcolatore.",
        "coefficients": {
            57: 4.270,
            58: 4.378,
            59: 4.493,
            60: 4.615,
            61: 4.744,
            62: 4.882,
            63: 5.028,
            64: 5.184,
            65: 5.352,
            66: 5.531,
            67: 5.723,
            68: 5.931,
            69: 6.154,
            70: 6.395,
            71: 6.655,
        },
    },
    {
        "periodo_dal": 2025,
        "periodo_al": 2026,
        "fonte_id": "ministero_lavoro_coefficiente_trasformazione",
        "norma": "Decreto direttoriale 20 novembre 2024",
        "note": "Valori ministeriali 2025-2026; per eta' intermedie si usa interpolazione mensile lineare.",
        "coefficients": {
            57: 4.204,
            58: 4.308,
            59: 4.419,
            60: 4.536,
            61: 4.661,
            62: 4.795,
            63: 4.936,
            64: 5.088,
            65: 5.250,
            66: 5.423,
            67: 5.608,
            68: 5.808,
            69: 6.024,
            70: 6.258,
            71: 6.510,
        },
    },
]


CATEGORY_ROWS: list[dict[str, object]] = [
    {
        "categoria_id": "generica_fpld",
        "categoria_nome": "Dipendente privato - profilo generico",
        "gestione": "FPLD lavoratori dipendenti",
        "ccnl": "Profilo generico",
        "indice_ccnl_id": "totale_economia",
        "stato": "operativa",
        "abilitata_frontend": True,
        "profilo_aliquota_id": "fpld",
        "aliquote": "storiche FPLD",
        "profilo_retributivo": "stima calibrata su RAL inserita o scenario basso/centrale/alto",
        "note": "Categoria pienamente calcolabile per il controfattuale contributivo; non ricostruisce una pensione amministrativa INPS.",
    },
    {
        "categoria_id": "metalmeccanici_industria",
        "categoria_nome": "Metalmeccanici e industria",
        "gestione": "FPLD lavoratori dipendenti",
        "ccnl": "CCNL metalmeccanici industria",
        "indice_ccnl_id": "metalmeccanici",
        "stato": "operativa",
        "abilitata_frontend": True,
        "profilo_aliquota_id": "fpld",
        "aliquote": "storiche FPLD",
        "profilo_retributivo": "da integrare con minimi CNEL/ISTAT storici",
        "note": "Operativa con aliquote FPLD. Il settore non modifica la formula previdenziale; la precisione dipende dalle retribuzioni inserite.",
    },
    {
        "categoria_id": "commercio_terziario",
        "categoria_nome": "Commercio e terziario",
        "gestione": "FPLD lavoratori dipendenti",
        "ccnl": "CCNL commercio e terziario",
        "indice_ccnl_id": "commercio",
        "stato": "operativa",
        "abilitata_frontend": True,
        "profilo_aliquota_id": "fpld",
        "aliquote": "storiche FPLD",
        "profilo_retributivo": "da integrare con minimi CNEL/ISTAT storici",
        "note": "Operativa con aliquote FPLD. Il settore non modifica la formula previdenziale; la precisione dipende dalle retribuzioni inserite.",
    },
    {
        "categoria_id": "edilizia",
        "categoria_nome": "Edilizia",
        "gestione": "FPLD lavoratori dipendenti",
        "ccnl": "CCNL edilizia",
        "indice_ccnl_id": "edilizia",
        "stato": "operativa",
        "abilitata_frontend": True,
        "profilo_aliquota_id": "fpld",
        "aliquote": "storiche FPLD",
        "profilo_retributivo": "da integrare",
        "note": "Operativa con aliquote FPLD. Eventuali discontinuita' e periodi non lavorati vanno indicati nella carriera.",
    },
    {
        "categoria_id": "turismo_pubblici_esercizi",
        "categoria_nome": "Turismo e pubblici esercizi",
        "gestione": "FPLD lavoratori dipendenti",
        "ccnl": "CCNL turismo/pubblici esercizi",
        "indice_ccnl_id": "turismo",
        "stato": "operativa",
        "abilitata_frontend": True,
        "profilo_aliquota_id": "fpld",
        "aliquote": "storiche FPLD",
        "profilo_retributivo": "da integrare",
        "note": "Operativa con aliquote FPLD. Stagionalita' e mesi lavorati incidono sull'imponibile e vanno indicati.",
    },
    {
        "categoria_id": "trasporti_logistica",
        "categoria_nome": "Trasporti e logistica",
        "gestione": "FPLD lavoratori dipendenti",
        "ccnl": "CCNL trasporti/logistica",
        "indice_ccnl_id": "trasporti",
        "stato": "operativa",
        "abilitata_frontend": True,
        "profilo_aliquota_id": "fpld",
        "aliquote": "storiche FPLD",
        "profilo_retributivo": "da integrare",
        "note": "Operativa con aliquote FPLD. La categoria descrive il settore; il calcolo usa le retribuzioni inserite.",
    },
    {
        "categoria_id": "agricoltura",
        "categoria_nome": "Dipendente agricolo",
        "gestione": "FPLD operai agricoli",
        "ccnl": "Operai agricoli",
        "indice_ccnl_id": "agricoltura",
        "stato": "operativa_con_limiti",
        "abilitata_frontend": True,
        "profilo_aliquota_id": "agricoli_dipendenti",
        "aliquote": "FPLD agricolo dal 1998",
        "profilo_retributivo": "retribuzione imponibile inserita dall'utente",
        "anno_minimo_calcolabile": 1998,
        "note": "Profilo per operai agricoli dipendenti. L'aliquota di finanziamento cresce di 0,20 punti annui; il montante contributivo usa il 33%. Non ricostruisce minimali giornalieri, giornate effettive o agevolazioni territoriali.",
    },
    {
        "categoria_id": "agricoli_autonomi",
        "categoria_nome": "Coltivatore diretto, colono, mezzadro o IAP",
        "gestione": "Gestione autonoma agricola CD/CM/IAP",
        "ccnl": "",
        "indice_ccnl_id": "",
        "stato": "operativa_con_limiti",
        "abilitata_frontend": True,
        "profilo_aliquota_id": "agricoli_autonomi",
        "aliquote": "finanziamento e computo dal 2012",
        "profilo_retributivo": "reddito convenzionale contributivo annuo inserito dall'utente",
        "anno_minimo_calcolabile": 2012,
        "note": "L'input economico e' il reddito convenzionale contributivo, non il reddito d'impresa. Non ricostruisce le quattro fasce aziendali, giornate, addizionali fisse, zone svantaggiate, riduzioni o agevolazioni.",
    },
    {
        "categoria_id": "pubblico_impiego",
        "categoria_nome": "Dipendente pubblico - Stato (CTPS)",
        "gestione": "Gestione dipendenti pubblici - CTPS",
        "ccnl": "Amministrazioni statali",
        "indice_ccnl_id": "pubblica_amministrazione",
        "stato": "operativa_con_limiti",
        "abilitata_frontend": True,
        "profilo_aliquota_id": "pubblico_ctps",
        "aliquote": "33%: 8,80% lavoratore e 24,20% amministrazione",
        "profilo_retributivo": "retribuzione imponibile inserita dall'utente",
        "anno_minimo_calcolabile": 1996,
        "note": "Profilo CTPS per dipendenti dello Stato. Il 33% e' applicato dal 1996 nel controfattuale contributivo; non include TFS/TFR, Fondo credito o altre contribuzioni non pensionistiche.",
    },
    {
        "categoria_id": "pubblico_enti_locali",
        "categoria_nome": "Dipendente pubblico - enti locali e sanita'",
        "gestione": "Gestione dipendenti pubblici - CPDEL/CPS/CPI/CPUG",
        "ccnl": "Enti locali, sanita' e casse assimilate",
        "indice_ccnl_id": "pubblica_amministrazione",
        "stato": "operativa_con_limiti",
        "abilitata_frontend": True,
        "profilo_aliquota_id": "pubblico_enti_locali",
        "aliquote": "32,65%: 8,85% lavoratore e 23,80% amministrazione",
        "profilo_retributivo": "retribuzione imponibile inserita dall'utente",
        "anno_minimo_calcolabile": 1996,
        "note": "Profilo CPDEL/CPS/CPI/CPUG. Il 32,65% e' applicato dal 1996 nel controfattuale contributivo; non include TFS/TFR, Fondo credito o altre contribuzioni non pensionistiche.",
    },
    {
        "categoria_id": "artigiani",
        "categoria_nome": "Artigiani",
        "gestione": "Gestione speciale artigiani",
        "ccnl": "",
        "indice_ccnl_id": "",
        "stato": "operativa_con_limiti",
        "abilitata_frontend": True,
        "profilo_aliquota_id": "artigiani",
        "aliquote": "storiche Gestione artigiani dal 1990",
        "profilo_retributivo": "reddito imponibile d'impresa inserito dall'utente",
        "anno_minimo_calcolabile": 1990,
        "note": "Calcolo sul reddito imponibile d'impresa inserito. Non ricostruisce minimali, massimali, maggiorazione oltre la prima fascia, riduzioni per eta' o agevolazioni; carriere anteriori al 1990 richiedono dati contributivi anno per anno.",
    },
    {
        "categoria_id": "commercianti",
        "categoria_nome": "Commercianti",
        "gestione": "Gestione speciale commercianti",
        "ccnl": "",
        "indice_ccnl_id": "",
        "stato": "operativa_con_limiti",
        "abilitata_frontend": True,
        "profilo_aliquota_id": "commercianti",
        "aliquote": "IVS storica e contributo aggiuntivo per cessazione attivita'",
        "profilo_retributivo": "reddito imponibile d'impresa inserito dall'utente",
        "anno_minimo_calcolabile": 1990,
        "note": "Il montante usa l'aliquota IVS; i contributi finanziari includono anche la componente per l'indennizzo di cessazione dell'attivita'. Non ricostruisce minimali, massimali, maggiorazioni, riduzioni o agevolazioni.",
    },
    {
        "categoria_id": "gestione_separata_professionisti",
        "categoria_nome": "Gestione separata e professionisti",
        "gestione": "Gestione separata",
        "ccnl": "",
        "indice_ccnl_id": "",
        "stato": "non_implementata",
        "abilitata_frontend": False,
        "profilo_aliquota_id": "gestione_separata_da_costruire",
        "aliquote": "da costruire",
        "profilo_retributivo": "reddito imponibile e massimali",
        "note": "Non viene presentata come operativa perche' aliquote e massimali cambiano per profilo assicurativo.",
    },
]


PROGRESSION_RATES = {
    "nessuna": 0.0,
    "lenta": 0.01,
    "media": 0.02,
    "rapida": 0.03,
}

GENERIC_LEVEL_RAL_2025 = {
    "basso": 24_000.0,
    "medio": 36_000.0,
    "alto": 58_000.0,
}


DEFAULT_SCENARIO = {
    "scenario_id": "scenario_generico_fpld",
    "descrizione": "Esempio FPLD con RAL finale inserita e pensione effettiva lorda.",
    "anno_nascita": 1960,
    "data_nascita": "1960-01-01",
    "sesso": "T",
    "categoria_id": "generica_fpld",
    "anno_inizio": 1996,
    "anno_fine": 2024,
    "anno_pensione": 2025,
    "data_pensionamento": "2025-01-01",
    "eta_pensione": 65,
    "mesi_eta_pensione": 0,
    "ral_iniziale": None,
    "ral_finale": 38_000.0,
    "ral_anno": None,
    "ral_valore": None,
    "livello_iniziale": "medio",
    "livello_finale": "medio",
    "progressione": "media",
    "anni_contribuiti": 29,
    "percentuale_lavoro": 100.0,
    "mesi_lavorati_annui": 12.0,
    "pensione_lorda_mensile_effettiva": 2_000.0,
    "pensione_mensile_attuale": 2_000.0,
    "pensione_valore_tipo": "lordo",
    "pensione_netto_mensile_stimato": None,
    "mensilita_pensione": 13.0,
    "anno_riferimento_pensione": CURRENT_YEAR,
    "rivalutazione_futura_pensione": "nessuna",
    "tasso_inflazione_futura": 0.02,
    "fonte_retribuzione": "ral_finale_inserita",
    "note": "Scenario dimostrativo. La dashboard permette di sostituire i valori nel browser.",
}


@dataclass(frozen=True)
class RateInfo:
    aliquota_finanziamento: float
    aliquota_computo: float
    quota_lavoratore: float
    quota_datore: float
    fonte_id: str
    note: str


@dataclass(frozen=True)
class CapitalizationInfo:
    anno: int
    tasso: float
    pil_anno_finale: int
    pil_finale_milioni: float
    pil_anno_iniziale: int
    pil_iniziale_milioni: float
    edizione_pil: str
    tasso_ufficiale_pubblicato: float | None
    fonte_id: str
    natura_dato: str
    note: str


@dataclass(frozen=True)
class CoefficientInfo:
    coefficiente: float
    eta_usata: float
    fonte_id: str
    norma: str
    natura_dato: str
    note: str


def to_float(value: object, default: float | None = None) -> float | None:
    if value is None:
        return default
    if isinstance(value, str) and not value.strip():
        return default
    try:
        number = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return default
    if math.isnan(number):
        return default
    return number


def to_int(value: object, default: int | None = None) -> int | None:
    number = to_float(value)
    if number is None:
        return default
    return int(number)


def pension_net_annual_estimate(annual_gross: float, year: int = CURRENT_YEAR) -> float:
    if annual_gross <= 0:
        return 0.0
    middle_rate = 0.33 if year >= 2026 else 0.35
    if annual_gross <= 28_000:
        gross_tax = annual_gross * 0.23
    elif annual_gross <= 50_000:
        gross_tax = 6_440 + (annual_gross - 28_000) * middle_rate
    else:
        gross_tax = 6_440 + 22_000 * middle_rate + (annual_gross - 50_000) * 0.43
    if annual_gross <= 8_500:
        detraction = 1_955.0
    elif annual_gross <= 28_000:
        detraction = 700 + 1_255 * (28_000 - annual_gross) / 19_500
    elif annual_gross <= 50_000:
        detraction = 700 * (50_000 - annual_gross) / 22_000
    else:
        detraction = 0.0
    if 25_000 < annual_gross <= 29_000:
        detraction += 50
    national_tax = max(gross_tax - max(detraction, 0.0), 0.0)
    local_additional_tax = annual_gross * 0.021
    return max(annual_gross - national_tax - local_additional_tax, 0.0)


def pension_gross_annual_from_net(annual_net: float, year: int = CURRENT_YEAR) -> float:
    if annual_net <= 0:
        return 0.0
    low = annual_net
    high = max(annual_net * 2.5, annual_net + 30_000)
    while pension_net_annual_estimate(high, year) < annual_net:
        high *= 1.5
    for _ in range(80):
        middle = (low + high) / 2
        if pension_net_annual_estimate(middle, year) < annual_net:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def normalize_scenario(raw: dict[str, object]) -> dict[str, object]:
    scenario = dict(DEFAULT_SCENARIO)
    for key, value in raw.items():
        if key in scenario and pd.notna(value):
            scenario[key] = value
    for key in [
        "anno_nascita",
        "anno_inizio",
        "anno_fine",
        "anno_pensione",
        "eta_pensione",
        "mesi_eta_pensione",
        "ral_anno",
        "anno_riferimento_pensione",
    ]:
        scenario[key] = to_int(scenario.get(key), to_int(DEFAULT_SCENARIO.get(key)))
    for key in [
        "ral_iniziale",
        "ral_finale",
        "ral_valore",
        "anni_contribuiti",
        "percentuale_lavoro",
        "mesi_lavorati_annui",
        "pensione_lorda_mensile_effettiva",
        "pensione_mensile_attuale",
        "pensione_netto_mensile_stimato",
        "mensilita_pensione",
        "tasso_inflazione_futura",
    ]:
        scenario[key] = to_float(scenario.get(key), to_float(DEFAULT_SCENARIO.get(key)))
    pension_months = float(scenario.get("mensilita_pensione") or 13.0)
    current_input = to_float(raw.get("pensione_mensile_attuale"))
    if current_input is None:
        current_input = to_float(raw.get("pensione_lorda_mensile_effettiva"), 2_000.0) or 0.0
    pension_value_type = str(raw.get("pensione_valore_tipo") or scenario.get("pensione_valore_tipo") or "lordo").lower()
    scenario["pensione_mensile_attuale"] = current_input
    scenario["pensione_valore_tipo"] = pension_value_type if pension_value_type in {"lordo", "netto"} else "lordo"
    if scenario["pensione_valore_tipo"] == "netto":
        annual_gross = pension_gross_annual_from_net(current_input * pension_months, CURRENT_YEAR)
        scenario["pensione_lorda_mensile_effettiva"] = annual_gross / pension_months
        scenario["pensione_netto_mensile_stimato"] = current_input
    else:
        scenario["pensione_lorda_mensile_effettiva"] = current_input
        scenario["pensione_netto_mensile_stimato"] = pension_net_annual_estimate(current_input * pension_months, CURRENT_YEAR) / pension_months
    scenario["anno_riferimento_pensione"] = CURRENT_YEAR
    birth_date = parse_date(raw.get("data_nascita"))
    retirement_date = parse_date(raw.get("data_pensionamento"))
    if birth_date is None:
        birth_date = date(int(scenario["anno_nascita"]), 1, 1)
    if retirement_date is None:
        retirement_date = date(int(scenario["anno_pensione"]), 1, 1)
    age_years, age_months = age_at_date(birth_date, retirement_date)
    scenario["data_nascita"] = birth_date.isoformat()
    scenario["data_pensionamento"] = retirement_date.isoformat()
    scenario["anno_nascita"] = birth_date.year
    scenario["anno_pensione"] = retirement_date.year
    scenario["eta_pensione"] = age_years
    scenario["mesi_eta_pensione"] = age_months
    return scenario


def validate_scenario(scenario: dict[str, object]) -> None:
    start = int(scenario["anno_inizio"])
    end = int(scenario["anno_fine"])
    retirement = int(scenario["anno_pensione"])
    birth = int(scenario["anno_nascita"])
    age = int(scenario["eta_pensione"])
    if start > end:
        raise ValueError("anno_inizio deve essere minore o uguale ad anno_fine")
    if end >= retirement:
        raise ValueError("anno_fine deve precedere anno_pensione")
    birth_date = parse_date(scenario.get("data_nascita"))
    retirement_date = parse_date(scenario.get("data_pensionamento"))
    if birth_date is None or retirement_date is None or retirement_date <= birth_date:
        raise ValueError("data di nascita e data di pensionamento non sono valide")
    if retirement - birth not in range(age - 1, age + 2):
        raise ValueError("data di nascita, pensionamento ed eta non sono coerenti")
    if not (0 < float(scenario["percentuale_lavoro"]) <= 100):
        raise ValueError("percentuale_lavoro deve essere compresa tra 0 e 100")
    if not (0 <= float(scenario["mesi_lavorati_annui"]) <= 12):
        raise ValueError("mesi_lavorati_annui deve essere compreso tra 0 e 12")


def parse_date(value: object) -> date | None:
    if value is None or pd.isna(value):
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def age_at_date(birth_date: date, reference_date: date) -> tuple[int, int]:
    total_months = (reference_date.year - birth_date.year) * 12 + reference_date.month - birth_date.month
    if reference_date.day < birth_date.day:
        total_months -= 1
    total_months = max(total_months, 0)
    return total_months // 12, total_months % 12


def category_parameters(category_id: str) -> dict[str, object]:
    category = next((row for row in CATEGORY_ROWS if row["categoria_id"] == category_id), None)
    if category is None:
        raise ValueError(f"Categoria sconosciuta: {category_id}")
    supported_profiles = {
        "fpld",
        "artigiani",
        "commercianti",
        "pubblico_ctps",
        "pubblico_enti_locali",
        "agricoli_dipendenti",
        "agricoli_autonomi",
    }
    if not bool(category.get("abilitata_frontend")) or category.get("profilo_aliquota_id") not in supported_profiles:
        raise ValueError(f"Categoria non ancora calcolabile con una serie storica propria: {category['categoria_nome']}")
    return category


def load_fpld_periods() -> pd.DataFrame:
    periods = read_csv_optional(FPLD_PERIODS_PATH)
    if periods.empty:
        return periods
    required = {"periodo_dal", "periodo_al", "aliquota_totale"}
    missing = required - set(periods.columns)
    if missing:
        raise ValueError(f"Tabella aliquote FPLD senza colonne: {', '.join(sorted(missing))}")
    return periods


def weighted_fpld_rate_for_year(year: int, periods: pd.DataFrame | None = None) -> RateInfo:
    periods = load_fpld_periods() if periods is None else periods
    if periods.empty:
        return rate_from_system_parameters(year)

    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)
    year_days = (year_end - year_start).days + 1
    totals = {"aliquota_totale": 0.0, "aliquota_lavoratore": 0.0, "aliquota_datore_lavoro": 0.0}
    covered_days = 0
    for _, row in periods.iterrows():
        start = parse_date(row.get("periodo_dal"))
        end = parse_date(row.get("periodo_al"))
        if start is None or end is None or end < year_start or start > year_end:
            continue
        overlap_start = max(start, year_start)
        overlap_end = min(end, year_end)
        days = (overlap_end - overlap_start).days + 1
        covered_days += days
        for column in totals:
            value = to_float(row.get(column), 0.0) or 0.0
            totals[column] += value * days / year_days
    if covered_days == 0:
        return rate_from_system_parameters(year)

    financing = totals["aliquota_totale"] / 100.0
    computation = 0.33 if year >= 1996 else financing
    note = (
        "Aliquota FPLD ponderata sui giorni dell'anno quando cambia nel corso dell'anno. "
        "Per il controfattuale prima del 1996 l'aliquota di computo e' approssimata con l'aliquota di finanziamento FPLD."
    )
    return RateInfo(
        aliquota_finanziamento=financing,
        aliquota_computo=computation,
        quota_lavoratore=totals["aliquota_lavoratore"] / 100.0,
        quota_datore=totals["aliquota_datore_lavoro"] / 100.0,
        fonte_id="inps_aliquote_storiche",
        note=note,
    )


def rate_from_system_parameters(year: int) -> RateInfo:
    table = read_csv_optional(FINAL_TABLE_PATHS["tabella_parametri_sistema"])
    if table.empty:
        raise ValueError("tabella_parametri_sistema mancante: eseguire build_contribution_rate_history")
    table["anno"] = pd.to_numeric(table["anno"], errors="coerce")
    records = table[table["anno"].eq(year)]
    if records.empty:
        nearest_year = int(table["anno"].dropna().astype(int).iloc[(table["anno"].dropna() - year).abs().argmin()])
        records = table[table["anno"].eq(nearest_year)]
    values = dict(zip(records["parametro_id"], pd.to_numeric(records["valore"], errors="coerce")))
    total = float(values.get("aliquota_ivs_fpld_totale_fine_anno", 32.7)) / 100.0
    worker = float(values.get("aliquota_ivs_fpld_lavoratore_fine_anno", 8.89)) / 100.0
    employer = float(values.get("aliquota_ivs_fpld_datore_lavoro_fine_anno", 23.81)) / 100.0
    return RateInfo(total, 0.33 if year >= 1996 else total, worker, employer, "inps_aliquote_storiche", "Aliquota FPLD a fine anno.")


def artisan_rate_for_year(year: int) -> RateInfo:
    if year < min(ARTISAN_RATES):
        raise ValueError("La serie percentuale della Gestione artigiani e' disponibile dal 1990.")
    rate = ARTISAN_RATES.get(year, ARTISAN_RATES[max(ARTISAN_RATES)])
    note = (
        "Aliquota pensionistica IVS ordinaria della Gestione artigiani, usata sia per il finanziamento sia per il computo. "
        "Il modello la applica al reddito imponibile inserito e non ricostruisce minimali, massimali, aliquota aggiuntiva "
        "oltre la prima fascia, riduzioni per eta' o agevolazioni."
    )
    if year == 1990:
        note += " Per il 1990 usa il 12% in vigore dal 1 luglio come approssimazione annuale."
    return RateInfo(rate, rate, rate, 0.0, "inps_aliquote_artigiani", note)


def merchant_rate_for_year(year: int) -> RateInfo:
    artisan = artisan_rate_for_year(year)
    additional = MERCHANT_ADDITIONAL_RATES.get(year, MERCHANT_ADDITIONAL_RATES[max(MERCHANT_ADDITIONAL_RATES)])
    note = (
        "L'aliquota di computo segue l'IVS della Gestione commercianti. L'aliquota di finanziamento include anche "
        "la componente per l'indennizzo di cessazione dell'attivita', che non incrementa il montante. "
        "Minimali, massimali, maggiorazioni oltre la prima fascia, riduzioni e agevolazioni non sono ricostruiti."
    )
    return RateInfo(
        artisan.aliquota_finanziamento + additional,
        artisan.aliquota_computo,
        artisan.quota_lavoratore + additional,
        0.0,
        "inps_aliquote_commercianti",
        note,
    )


def public_employee_rate(profile_id: str, year: int) -> RateInfo:
    if year < 1996:
        raise ValueError("Il profilo contributivo semplificato dei dipendenti pubblici e' disponibile dal 1996.")
    profile = PUBLIC_PENSION_PROFILES[profile_id]
    rate = float(profile["aliquota"])
    return RateInfo(
        rate,
        rate,
        float(profile["quota_lavoratore"]),
        float(profile["quota_datore"]),
        "inps_aliquote_dipendenti_pubblici",
        "Aliquota pensionistica della cassa pubblica selezionata; TFS/TFR, Fondo credito e contribuzioni non pensionistiche sono esclusi.",
    )


def agricultural_employee_rate_for_year(year: int) -> RateInfo:
    if year < min(AGRICULTURAL_EMPLOYEE_RATES):
        raise ValueError("La serie semplificata degli operai agricoli dipendenti e' disponibile dal 1998.")
    financing = AGRICULTURAL_EMPLOYEE_RATES.get(year, AGRICULTURAL_EMPLOYEE_RATES[max(AGRICULTURAL_EMPLOYEE_RATES)])
    worker = 0.0884 if year >= 2007 else 0.0854
    return RateInfo(
        financing,
        0.33,
        worker,
        financing - worker,
        "inps_aliquote_agricoli_dipendenti",
        "Aliquota FPLD agricola di finanziamento; il controfattuale contributivo accredita il 33%. Minimali giornalieri e agevolazioni non sono ricostruiti.",
    )


def agricultural_self_employed_rate_for_year(year: int) -> RateInfo:
    if year < min(AGRICULTURAL_SELF_EMPLOYED_RATES):
        raise ValueError("La serie omogenea CD/CM/IAP e' disponibile dal 2012.")
    rate = AGRICULTURAL_SELF_EMPLOYED_RATES.get(year, AGRICULTURAL_SELF_EMPLOYED_RATES[max(AGRICULTURAL_SELF_EMPLOYED_RATES)])
    return RateInfo(
        rate,
        rate,
        rate,
        0.0,
        "inps_aliquote_agricoli_autonomi",
        "Aliquota CD/CM/IAP applicata al reddito convenzionale contributivo inserito; fasce aziendali, giornate, addizionali fisse e agevolazioni non sono ricostruite.",
    )


def rate_for_category_year(category_id: str, year: int, periods: pd.DataFrame | None = None) -> RateInfo:
    category = category_parameters(category_id)
    profile_id = str(category["profilo_aliquota_id"])
    if profile_id == "artigiani":
        return artisan_rate_for_year(year)
    if profile_id == "commercianti":
        return merchant_rate_for_year(year)
    if profile_id in PUBLIC_PENSION_PROFILES:
        return public_employee_rate(profile_id, year)
    if profile_id == "agricoli_dipendenti":
        return agricultural_employee_rate_for_year(year)
    if profile_id == "agricoli_autonomi":
        return agricultural_self_employed_rate_for_year(year)
    return weighted_fpld_rate_for_year(year, periods)


def capitalization_for_year(year: int) -> CapitalizationInfo:
    available_year = year
    nature = "calcolato_da_pil_nominale_istat"
    if year not in CAPITALIZATION_RATES:
        available_year = max(
            [item for item in CAPITALIZATION_RATES if item <= year],
            default=min(CAPITALIZATION_RATES),
        )
        nature = "stimato_per_trascinamento"
    row = _capitalization_table.loc[_capitalization_table["anno"] == available_year].iloc[0]
    official = to_float(row.get("tasso_ufficiale_pubblicato"))
    note = (
        "Tasso calcolato dai livelli di PIL nominale ISTAT scaricati via SDMX: "
        "(PIL t-1 / PIL t-6)^(1/5)-1. Le revisioni dei conti nazionali possono produrre "
        "uno scarto rispetto al tasso storico pubblicato. L'accredito dell'anno non viene "
        "rivalutato nello stesso anno."
    )
    if available_year != year:
        note += f" Per l'anno {year}, non ancora disponibile, e' usato il {available_year}."
    return CapitalizationInfo(
        anno=available_year,
        tasso=float(row["tasso_capitalizzazione"]),
        pil_anno_finale=int(row["pil_anno_finale"]),
        pil_finale_milioni=float(row["pil_finale_milioni"]),
        pil_anno_iniziale=int(row["pil_anno_iniziale"]),
        pil_iniziale_milioni=float(row["pil_iniziale_milioni"]),
        edizione_pil=str(row["edizione_pil"]),
        tasso_ufficiale_pubblicato=official,
        fonte_id="istat_pil_nominale_sdmx",
        natura_dato=nature,
        note=note,
    )


def coefficient_period_for_year(year: int) -> dict[str, object]:
    for period in COEFFICIENT_PERIODS:
        if int(period["periodo_dal"]) <= year <= int(period["periodo_al"]):
            return period
    if year < int(COEFFICIENT_PERIODS[0]["periodo_dal"]):
        return COEFFICIENT_PERIODS[0]
    return COEFFICIENT_PERIODS[-1]


def transformation_coefficient(retirement_year: int, age_years: int, age_months: int = 0) -> CoefficientInfo:
    period = coefficient_period_for_year(retirement_year)
    coefficients: dict[int, float] = period["coefficients"]  # type: ignore[assignment]
    age_months = max(0, min(int(age_months), 11))
    raw_age = int(age_years) + age_months / 12.0
    min_age = min(coefficients)
    max_age = max(coefficients)
    notes = [str(period["note"])]
    nature = "osservato"
    if retirement_year < int(period["periodo_dal"]) or retirement_year > int(period["periodo_al"]):
        nature = "stimato_per_tabella_piu_vicina"
        notes.append("Per l'anno di pensionamento indicato non e' ancora caricata una tabella storica dedicata.")
    if raw_age < min_age:
        raw_age = float(min_age)
        nature = "stimato_eta_minima"
        notes.append("Eta' inferiore al minimo: applicato il coefficiente dei 57 anni.")
    if raw_age > max_age:
        raw_age = float(max_age)
        nature = "stimato_eta_massima"
        notes.append("Eta' superiore al massimo della tabella: applicato l'ultimo coefficiente disponibile.")

    lower = int(math.floor(raw_age))
    upper = min(lower + 1, max_age)
    if lower == upper:
        coefficient = coefficients[lower]
    else:
        share = raw_age - lower
        coefficient = coefficients[lower] + (coefficients[upper] - coefficients[lower]) * share
        if share:
            notes.append("Eta' intermedia calcolata con interpolazione mensile lineare tra eta' intere.")
    return CoefficientInfo(
        coefficiente=coefficient / 100.0,
        eta_usata=raw_age,
        fonte_id=str(period["fonte_id"]),
        norma=str(period["norma"]),
        natura_dato=nature,
        note=" ".join(notes),
    )


def contractual_salary_profile(
    years: list[int],
    scenario: dict[str, object],
    known_points: dict[int, float],
) -> tuple[dict[int, float], str] | None:
    category = category_parameters(str(scenario.get("categoria_id") or "generica_fpld"))
    agreement_id = str(category.get("indice_ccnl_id") or "")
    if not agreement_id or not known_points:
        return None
    table = _contract_wages_table[_contract_wages_table["indice_ccnl_id"].astype(str).eq(agreement_id)].copy()
    if table.empty:
        return None
    index_by_year = dict(
        zip(
            pd.to_numeric(table["anno"], errors="coerce").astype(int),
            pd.to_numeric(table["indice_retribuzione_contrattuale"], errors="coerce"),
        )
    )
    observed_years = sorted(index_by_year)
    first_observed = observed_years[0]
    last_observed = observed_years[-1]

    def index_for(year: int) -> float:
        if year in index_by_year:
            return float(index_by_year[year])
        if year < first_observed:
            return float(index_by_year[first_observed]) / ((1.02) ** (first_observed - year))
        return float(index_by_year[last_observed]) * ((1.02) ** (year - last_observed))

    ordered = sorted(known_points.items())
    profile: dict[int, float] = {}
    if len(ordered) >= 2:
        first_year, first_value = ordered[0]
        last_year, last_value = ordered[-1]
        contractual_ratio = index_for(last_year) / max(index_for(first_year), 0.0001)
        target_ratio = last_value / max(first_value, 1.0)
        correction = (target_ratio / max(contractual_ratio, 0.0001)) ** (1 / max(1, last_year - first_year))
        for year in years:
            profile[year] = first_value * index_for(year) / index_for(first_year) * (correction ** (year - first_year))
        return profile, f"indice_retribuzioni_contrattuali_istat_{agreement_id}_calibrato_su_input"

    ref_year, ref_value = ordered[0]
    for year in years:
        profile[year] = ref_value * index_for(year) / index_for(ref_year)
    return profile, f"indice_retribuzioni_contrattuali_istat_{agreement_id}_calibrato_su_input"


def salary_profile(years: list[int], scenario: dict[str, object]) -> tuple[dict[int, float], str]:
    progression = str(scenario.get("progressione") or "media")
    growth = PROGRESSION_RATES.get(progression, PROGRESSION_RATES["media"])
    known_points: dict[int, float] = {}
    start = years[0]
    end = years[-1]
    if to_float(scenario.get("ral_iniziale")):
        known_points[start] = float(scenario["ral_iniziale"])
    if to_float(scenario.get("ral_finale")):
        known_points[end] = float(scenario["ral_finale"])
    known_year = to_int(scenario.get("ral_anno"))
    known_value = to_float(scenario.get("ral_valore"))
    if known_year in years and known_value:
        known_points[int(known_year)] = float(known_value)

    profile: dict[int, float] = {}
    contractual = contractual_salary_profile(years, scenario, known_points)
    if contractual is not None:
        return contractual

    if len(known_points) >= 2:
        ordered = sorted(known_points.items())
        for year in years:
            before = max((item for item in ordered if item[0] <= year), default=ordered[0])
            after = min((item for item in ordered if item[0] >= year), default=ordered[-1])
            if before[0] == after[0]:
                profile[year] = before[1]
            else:
                years_between = after[0] - before[0]
                local_growth = (after[1] / before[1]) ** (1 / years_between) - 1 if before[1] > 0 else growth
                profile[year] = before[1] * ((1 + local_growth) ** (year - before[0]))
        return profile, "stimato_calibrato_su_ral"

    if len(known_points) == 1:
        ref_year, ref_salary = next(iter(known_points.items()))
        for year in years:
            profile[year] = ref_salary * ((1 + growth) ** (year - ref_year))
        return profile, "stimato_calibrato_su_ral"

    level = str(scenario.get("livello_finale") or "medio").lower()
    ref_salary = GENERIC_LEVEL_RAL_2025.get(level, GENERIC_LEVEL_RAL_2025["medio"])
    for year in years:
        profile[year] = ref_salary / ((1 + max(growth, 0.015)) ** (2025 - year))
    return profile, "stimato_scenario_senza_ral"


def build_simplified_career(scenario: dict[str, object], periods: pd.DataFrame | None = None) -> pd.DataFrame:
    scenario = normalize_scenario(scenario)
    validate_scenario(scenario)
    category = str(scenario.get("categoria_id") or "generica_fpld")
    category_info = category_parameters(category)

    years = list(range(int(scenario["anno_inizio"]), int(scenario["anno_fine"]) + 1))
    salaries, salary_nature = salary_profile(years, scenario)
    possible_years = len(years)
    contributed_years = min(float(scenario["anni_contribuiti"] or possible_years), possible_years)
    months_from_contributed_years = 12.0 * contributed_years / possible_years if possible_years else 0.0
    months_per_year = min(float(scenario["mesi_lavorati_annui"] or 12.0), months_from_contributed_years or 12.0)
    work_share = float(scenario["percentuale_lavoro"] or 100.0) / 100.0

    rows: list[dict[str, object]] = []
    accrued = 0.0
    for index, year in enumerate(years, start=1):
        gross_salary = max(salaries[year], 0.0)
        taxable = gross_salary * work_share * months_per_year / 12.0
        rate = rate_for_category_year(category, year, periods)
        cap = capitalization_for_year(year)
        financial_contributions = taxable * rate.aliquota_finanziamento
        montante_credit = taxable * rate.aliquota_computo
        accrued = accrued * (1 + cap.tasso) + montante_credit
        rows.append(
            {
                "scenario_id": scenario["scenario_id"],
                "anno": year,
                "categoria": category,
                "gestione": category_info["gestione"],
                "ccnl": category_info["ccnl"],
                "livello": scenario.get("livello_finale") or "medio",
                "retribuzione_stimata": gross_salary,
                "retribuzione_inserita": gross_salary if salary_nature == "stimato_calibrato_su_ral" else None,
                "mesi_lavorati": months_per_year,
                "percentuale_part_time": work_share * 100,
                "imponibile_previdenziale": taxable,
                "aliquota_finanziamento": rate.aliquota_finanziamento,
                "aliquota_computo": rate.aliquota_computo,
                "quota_lavoratore": rate.quota_lavoratore,
                "quota_datore": rate.quota_datore,
                "contributi_finanziari": financial_contributions,
                "accredito_montante": montante_credit,
                "tasso_rivalutazione": cap.tasso,
                "montante_fine_anno": accrued,
                "fonte": rate.fonte_id + "; " + cap.fonte_id,
                "natura_dato": salary_nature,
                "note": rate.note + " " + cap.note,
                "indice_anno": index,
            }
        )
    return pd.DataFrame(rows)


def build_accurate_career(annual_rows: list[dict[str, object]], scenario: dict[str, object] | None = None) -> pd.DataFrame:
    scenario = normalize_scenario(scenario or DEFAULT_SCENARIO)
    default_category = str(scenario.get("categoria_id") or "generica_fpld")
    default_category_info = category_parameters(default_category)
    rows = sorted(annual_rows, key=lambda row: int(row["anno"]))
    seen_years: set[int] = set()
    output: list[dict[str, object]] = []
    accrued = 0.0
    for index, row in enumerate(rows, start=1):
        year = int(row["anno"])
        if year in seen_years:
            raise ValueError(f"Anno duplicato nella carriera accurata: {year}")
        seen_years.add(year)
        row_category = str(row.get("categoria") or default_category)
        row_category_info = category_parameters(row_category)
        taxable = float(to_float(row.get("imponibile_previdenziale"), 0.0) or 0.0)
        if taxable < 0:
            raise ValueError("imponibile_previdenziale non puo' essere negativo")
        rate = rate_for_category_year(row_category, year)
        cap = capitalization_for_year(year)
        financial = float(to_float(row.get("contributi"), taxable * rate.aliquota_finanziamento) or 0.0)
        montante_credit = taxable * rate.aliquota_computo + float(to_float(row.get("contributi_figurativi"), 0.0) or 0.0)
        accrued = accrued * (1 + cap.tasso) + montante_credit
        output.append(
            {
                "scenario_id": scenario["scenario_id"],
                "anno": year,
                "categoria": row_category,
                "gestione": row.get("gestione") or row_category_info.get("gestione") or default_category_info["gestione"],
                "ccnl": row.get("ccnl") or row_category_info.get("ccnl") or "",
                "livello": row.get("livello") or "",
                "retribuzione_stimata": to_float(row.get("retribuzione_stimata")),
                "retribuzione_inserita": to_float(row.get("retribuzione_inserita"), taxable),
                "mesi_lavorati": to_float(row.get("mesi_lavorati"), 12.0),
                "percentuale_part_time": to_float(row.get("percentuale_part_time"), 100.0),
                "imponibile_previdenziale": taxable,
                "aliquota_finanziamento": rate.aliquota_finanziamento,
                "aliquota_computo": rate.aliquota_computo,
                "quota_lavoratore": rate.quota_lavoratore,
                "quota_datore": rate.quota_datore,
                "contributi_finanziari": financial,
                "accredito_montante": montante_credit,
                "tasso_rivalutazione": cap.tasso,
                "montante_fine_anno": accrued,
                "fonte": "input_utente; " + rate.fonte_id + "; " + cap.fonte_id,
                "natura_dato": "inserito_utente",
                "note": "Riga annuale inserita o caricata dall'utente; file non salvato dal frontend.",
                "indice_anno": index,
            }
        )
    return pd.DataFrame(output)


def download_istat_mortality(year: int) -> pd.DataFrame:
    MORTALITY_RAW_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = MORTALITY_RAW_DIR / f"datiripartizionecompleti{year}.zip"
    csv_path = MORTALITY_RAW_DIR / f"datiripartizionecompleti{year}.csv"
    if not csv_path.exists():
        url = f"https://demo.istat.it/data/tvm/datiripartizionecompleti{year}.zip"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        zip_path.write_bytes(response.content)
        with zipfile.ZipFile(BytesIO(response.content)) as archive:
            csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
            if not csv_names:
                raise ValueError("Archivio ISTAT senza CSV")
            csv_path.write_bytes(archive.read(csv_names[0]))
    raw = pd.read_csv(csv_path, sep=",")
    raw.columns = [str(column).strip() for column in raw.columns]
    return raw


def synthetic_mortality_table(year: int) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for sex in ["Totale", "Maschi", "Femmine"]:
        survivors = 100_000.0
        for age in range(0, 111):
            if age > 0:
                base_qx = min(0.002 + (age / 105) ** 5 * 0.35, 0.95)
                if sex == "Maschi":
                    base_qx *= 1.08
                if sex == "Femmine":
                    base_qx *= 0.92
                survivors *= max(0.0, 1 - min(base_qx, 0.98))
            rows.append(
                {
                    "anno": year,
                    "sesso": sex,
                    "eta": age,
                    "sopravviventi": survivors,
                    "probabilita_morte_per_mille": None,
                    "speranza_vita": None,
                    "fonte_id": "stima_fallback",
                    "natura_dato": "stimato_fallback",
                    "note": "Fallback usato solo se il download ISTAT non e' disponibile.",
                }
            )
    return pd.DataFrame(rows)


def build_mortality_table(preferred_year: int = DEFAULT_MORTALITY_YEAR) -> pd.DataFrame:
    for year in [preferred_year, preferred_year - 1, 2024]:
        try:
            raw = download_istat_mortality(year)
            break
        except Exception:
            raw = pd.DataFrame()
    if raw.empty:
        return synthetic_mortality_table(2024)

    rip_col = "Ripartizione"
    sex_col = "Sesso"
    age_col = next((column for column in raw.columns if str(column).lower().startswith(("eta", "et"))), "Età")
    survivors_col = "Sopravviventi"
    qx_col = next((column for column in raw.columns if "morte" in str(column).lower()), "Probabilità di morte (per mille)")
    life_col = "Speranza di vita"
    italy = raw[raw[rip_col].astype(str).str.lower().eq("italia")].copy()
    if italy.empty:
        italy = raw.copy()
    rows: list[dict[str, object]] = []
    sex_map = {"Maschi": "Maschi", "Femmine": "Femmine", "Totale": "Totale", "Maschi e femmine": "Totale"}
    for _, row in italy.iterrows():
        age_text = str(row.get(age_col, "")).replace("+", "").strip()
        age_number = to_float(age_text)
        if age_number is None:
            continue
        rows.append(
            {
                "anno": year,
                "sesso": sex_map.get(str(row.get(sex_col, "")).strip(), str(row.get(sex_col, "")).strip()),
                "eta": int(age_number),
                "sopravviventi": to_float(row.get(survivors_col), 0.0),
                "probabilita_morte_per_mille": to_float(row.get(qx_col)),
                "speranza_vita": to_float(row.get(life_col)),
                "fonte_id": "istat_tavole_mortalita",
                "natura_dato": "osservato",
                "note": "Tavole di mortalita' ISTAT per l'Italia; anno piu' vicino alla decorrenza disponibile nel payload.",
            }
        )
    return pd.DataFrame(rows).drop_duplicates(subset=["anno", "sesso", "eta"])


def survival_probabilities(mortality: pd.DataFrame, sex: str, start_age: int, max_horizon: int = 55) -> list[float]:
    if mortality.empty:
        mortality = synthetic_mortality_table(2024)
    sex_map = {"M": "Maschi", "F": "Femmine", "T": "Totale", "Totale": "Totale", "Maschi": "Maschi", "Femmine": "Femmine"}
    selected_sex = sex_map.get(str(sex), "Totale")
    rows = mortality[mortality["sesso"].astype(str).eq(selected_sex)].copy()
    if rows.empty:
        rows = mortality[mortality["sesso"].astype(str).eq("Totale")].copy()
    rows["eta"] = pd.to_numeric(rows["eta"], errors="coerce")
    rows["sopravviventi"] = pd.to_numeric(rows["sopravviventi"], errors="coerce")
    base = rows[rows["eta"].eq(start_age)]["sopravviventi"]
    if base.empty or not float(base.iloc[0]):
        base_survivors = float(rows["sopravviventi"].max() or 100_000)
    else:
        base_survivors = float(base.iloc[0])
    probabilities: list[float] = []
    max_age = int(rows["eta"].max()) if not rows.empty else start_age + max_horizon
    for horizon in range(0, max_horizon + 1):
        age = min(start_age + horizon, max_age)
        survivors = rows[rows["eta"].eq(age)]["sopravviventi"]
        if survivors.empty:
            probability = 0.0
        else:
            probability = max(0.0, min(1.0, float(survivors.iloc[0]) / base_survivors))
        probabilities.append(probability)
    return probabilities


def remaining_life_expectancy(mortality: pd.DataFrame, sex: str, start_age: int) -> float:
    sex_map = {"M": "Maschi", "F": "Femmine", "T": "Totale", "Totale": "Totale"}
    selected = sex_map.get(str(sex), "Totale")
    rows = mortality[mortality["sesso"].astype(str).eq(selected)].copy()
    if rows.empty:
        rows = mortality[mortality["sesso"].astype(str).eq("Totale")].copy()
    rows["eta"] = pd.to_numeric(rows["eta"], errors="coerce")
    rows["speranza_vita"] = pd.to_numeric(rows.get("speranza_vita"), errors="coerce")
    exact = rows[rows["eta"].eq(start_age)]["speranza_vita"].dropna()
    if not exact.empty:
        return float(exact.iloc[0])
    probabilities = survival_probabilities(mortality, sex, start_age, max_horizon=55)
    return float(sum(probabilities[1:]))


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    month_lengths = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return date(year, month, min(value.day, month_lengths[month - 1]))


def pension_timeline_metrics(
    scenario: dict[str, object],
    accrued: float,
    actual_annual_at_retirement: float,
    mortality: pd.DataFrame,
) -> dict[str, object]:
    birth_date = parse_date(scenario.get("data_nascita")) or date(int(scenario["anno_nascita"]), 1, 1)
    retirement_date = parse_date(scenario.get("data_pensionamento")) or date(int(scenario["anno_pensione"]), 1, 1)
    today = date.today()
    elapsed_years = max(0.0, (today - retirement_date).days / 365.2425) if retirement_date <= today else 0.0
    retirement_age_years, retirement_age_months = age_at_date(birth_date, retirement_date)
    retirement_age = retirement_age_years + retirement_age_months / 12.0
    life_at_65 = remaining_life_expectancy(
        mortality,
        str(scenario.get("sesso") or "T"),
        LIFE_EXPECTANCY_BASE_AGE,
    )
    expected_life_age = LIFE_EXPECTANCY_BASE_AGE + life_at_65
    life_remaining = max(0.0, expected_life_age - retirement_age)
    future_rate = (
        float(scenario.get("tasso_inflazione_futura") or 0.0)
        if str(scenario.get("rivalutazione_futura_pensione")) == "inflazione_costante"
        else 0.0
    )
    elapsed_months = max(0, int((today - retirement_date).days / 30.436875)) if retirement_date <= today else 0
    expected_months = max(0, int(round(life_remaining * 12)))
    cumulative = 0.0
    received_to_date = 0.0
    cumulative_at_life = 0.0
    exhaustion_month: int | None = None
    max_months = max(expected_months + 240, elapsed_months + 240, 960)
    for month in range(1, max_months + 1):
        if month <= elapsed_months:
            annual_payment = actual_annual_at_retirement * ((1.02) ** (month / 12.0))
        else:
            past_base = actual_annual_at_retirement * ((1.02) ** (elapsed_months / 12.0))
            annual_payment = past_base * ((1 + future_rate) ** ((month - elapsed_months) / 12.0))
        cumulative += annual_payment / 12.0
        if month == elapsed_months:
            received_to_date = cumulative
        if month == expected_months:
            cumulative_at_life = cumulative
        if exhaustion_month is None and cumulative >= accrued:
            exhaustion_month = month
    if elapsed_months == 0:
        received_to_date = 0.0
    if expected_months == 0:
        cumulative_at_life = 0.0
    exhaustion_date = add_months(retirement_date, exhaustion_month) if exhaustion_month is not None else None
    return {
        "data_nascita": birth_date.isoformat(),
        "data_pensionamento": retirement_date.isoformat(),
        "anni_dal_pensionamento": elapsed_years,
        "eta_attuale": age_at_date(birth_date, today)[0] + age_at_date(birth_date, today)[1] / 12.0,
        "speranza_vita_residua_pensionamento": life_remaining,
        "eta_base_speranza_vita": LIFE_EXPECTANCY_BASE_AGE,
        "speranza_vita_residua_a_65": life_at_65,
        "eta_attesa_da_speranza_vita_65": expected_life_age,
        "eta_attesa": expected_life_age,
        "prestazioni_lorde_stimate_gia_ricevute": received_to_date,
        "montante_virtuale_residuo_oggi": accrued - received_to_date,
        "prestazioni_lorde_cumulate_eta_attesa": cumulative_at_life,
        "saldo_montante_eta_attesa": accrued - cumulative_at_life,
        "mesi_esaurimento_montante_virtuale": exhaustion_month,
        "data_esaurimento_montante_virtuale": exhaustion_date.isoformat() if exhaustion_date else None,
        "eta_esaurimento_montante_virtuale": retirement_age + exhaustion_month / 12.0 if exhaustion_month else None,
    }


def effective_annual_pension(scenario: dict[str, object]) -> tuple[float, str]:
    monthly = float(scenario["pensione_lorda_mensile_effettiva"] or 0.0)
    months = float(scenario["mensilita_pensione"] or 13.0)
    annual = monthly * months
    reference_year = int(scenario.get("anno_riferimento_pensione") or scenario["anno_pensione"])
    retirement_year = int(scenario["anno_pensione"])
    if reference_year > retirement_year:
        years = reference_year - retirement_year
        annual = annual / ((1 + 0.02) ** years)
        note = "Pensione lorda attuale riportata alla decorrenza con perequazione annua stimata al 2%."
    else:
        note = "Pensione lorda attuale nello stesso anno del pensionamento."
    if str(scenario.get("pensione_valore_tipo")) == "netto":
        note += " Il lordo attuale e' stimato dal netto con IRPEF, detrazione da pensione e addizionali locali medie."
    return annual, note


def classify_regime(career: pd.DataFrame) -> str:
    years_before_1996 = len(career[pd.to_numeric(career["anno"], errors="coerce") < 1996])
    if years_before_1996 == 0:
        return "contributivo"
    if years_before_1996 >= 18:
        return "prevalentemente_retributivo"
    return "misto"


def reliability_level(career: pd.DataFrame, scenario: dict[str, object]) -> tuple[str, str]:
    natures = set(career["natura_dato"].astype(str))
    if "inserito_utente" in natures:
        return "alta", "Imponibili annuali inseriti o caricati: il margine maggiore resta sui parametri normativi e sulla pensione effettiva."
    has_salary = bool(to_float(scenario.get("ral_iniziale")) or to_float(scenario.get("ral_finale")) or to_float(scenario.get("ral_valore")))
    if has_salary:
        return "media", "Aggiungere imponibili annuali dall'estratto contributivo migliorerebbe la precisione."
    return "bassa", "Inserire almeno una RAL reale o caricare un CSV annuale migliorerebbe molto la stima."


def calculate_paid_pension_metrics(
    career: pd.DataFrame,
    scenario: dict[str, object],
    mortality: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if career.empty:
        raise ValueError("La carriera contributiva e' vuota.")
    scenario = normalize_scenario(scenario)
    mortality = build_mortality_table() if mortality is None else mortality
    accrued = float(career["montante_fine_anno"].iloc[-1])
    total_financial = float(career["contributi_finanziari"].sum())
    total_credit = float(career["accredito_montante"].sum())
    final_salary = float(career["retribuzione_stimata"].dropna().iloc[-1])
    age = int(scenario["eta_pensione"])
    age_months = int(scenario.get("mesi_eta_pensione") or 0)
    coefficient = transformation_coefficient(int(scenario["anno_pensione"]), age, age_months)
    contributive_pension = accrued * coefficient.coefficiente
    actual_pension, pension_note = effective_annual_pension(scenario)
    reference_year = int(scenario.get("anno_riferimento_pensione") or scenario["anno_pensione"])
    years_to_reference = max(0, reference_year - int(scenario["anno_pensione"]))
    reference_factor = (1.02) ** years_to_reference
    contributive_pension_reference = contributive_pension * reference_factor
    actual_pension_reference = float(scenario["pensione_lorda_mensile_effettiva"] or 0.0) * float(scenario["mensilita_pensione"] or 13.0)
    annual_difference = actual_pension_reference - contributive_pension_reference
    difference_pct = annual_difference / contributive_pension_reference if contributive_pension_reference else 0.0
    pension_months = float(scenario.get("mensilita_pensione") or 13.0)
    monthly_actual = actual_pension_reference / pension_months
    monthly_contributive = contributive_pension_reference / pension_months
    future_rate = 0.0
    if str(scenario.get("rivalutazione_futura_pensione")) == "inflazione_costante":
        future_rate = float(scenario.get("tasso_inflazione_futura") or 0.02)

    survival = survival_probabilities(mortality, str(scenario.get("sesso") or "T"), age)
    expected_benefits = 0.0
    cumulative = 0.0
    break_even_age: float | None = None
    for horizon, probability in enumerate(survival):
        payment = actual_pension * ((1 + future_rate) ** horizon)
        expected_benefits += payment * probability
        cumulative += payment
        if break_even_age is None and cumulative >= accrued:
            break_even_age = age + horizon
    timeline = pension_timeline_metrics(scenario, accrued, actual_pension, mortality)
    if timeline["eta_esaurimento_montante_virtuale"] is not None:
        break_even_age = float(timeline["eta_esaurimento_montante_virtuale"])
    reliability, improvements = reliability_level(career, scenario)
    return pd.DataFrame(
        [
            {
                "scenario_id": scenario["scenario_id"],
                "descrizione": scenario.get("descrizione") or "",
                "categoria_id": scenario.get("categoria_id") or "generica_fpld",
                "regime_indicativo": classify_regime(career),
                "anni_contribuzione": float(pd.to_numeric(career["mesi_lavorati"], errors="coerce").fillna(0).sum() / 12.0),
                "retribuzione_finale": final_salary,
                "contributi_finanziari_versati": total_financial,
                "accredito_totale_montante": total_credit,
                "montante_contributivo": accrued,
                "coefficiente_trasformazione": coefficient.coefficiente,
                "eta_coefficiente_usata": coefficient.eta_usata,
                "pensione_contributiva_annua_equivalente": contributive_pension,
                "pensione_effettiva_annua_lorda": actual_pension,
                "pensione_valore_tipo_inserito": scenario.get("pensione_valore_tipo") or "lordo",
                "pensione_mensile_attuale_inserita": scenario.get("pensione_mensile_attuale"),
                "pensione_netto_mensile_stimato": scenario.get("pensione_netto_mensile_stimato"),
                "anno_riferimento_confronto": reference_year,
                "pensione_contributiva_annua_equivalente_anno_riferimento": contributive_pension_reference,
                "pensione_effettiva_annua_lorda_anno_riferimento": actual_pension_reference,
                "pensione_contributiva_mensile_equivalente": monthly_contributive,
                "pensione_effettiva_mensile_lorda_anno_riferimento": monthly_actual,
                "differenza_mensile_lorda": monthly_actual - monthly_contributive,
                "differenza_annua_lorda": annual_difference,
                "differenza_percentuale_su_contributiva": difference_pct,
                "valore_atteso_prestazioni_lorde": expected_benefits,
                "eta_pareggio": break_even_age,
                "rapporto_prestazioni_attese_montante": expected_benefits / accrued if accrued else None,
                "livello_affidabilita": reliability,
                "input_migliorativi": improvements,
                "fonte_coefficiente": coefficient.fonte_id,
                "natura_coefficiente": coefficient.natura_dato,
                "note": pension_note + " " + coefficient.note,
                **timeline,
            }
        ]
    )


def read_scenarios() -> list[dict[str, object]]:
    scenarios = read_csv_optional(SCENARI_CALCOLATORE_PATH)
    if scenarios.empty or "scenario_id" not in scenarios.columns:
        return [normalize_scenario(DEFAULT_SCENARIO)]
    return [normalize_scenario(row.to_dict()) for _, row in scenarios.iterrows()]


def parameter_tables(mortality: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rate_rows: list[dict[str, object]] = []
    start_year = 1976
    end_year = max(CURRENT_YEAR, 2026)
    profiles = [
        ("fpld", "generica_fpld", "FPLD lavoratori dipendenti", start_year),
        ("artigiani", "artigiani", "Gestione speciale artigiani", min(ARTISAN_RATES)),
        ("commercianti", "commercianti", "Gestione speciale commercianti", min(ARTISAN_RATES)),
        ("pubblico_ctps", "pubblico_impiego", "Gestione dipendenti pubblici - CTPS", 1996),
        ("pubblico_enti_locali", "pubblico_enti_locali", "Gestione dipendenti pubblici - CPDEL/CPS/CPI/CPUG", 1996),
        ("agricoli_dipendenti", "agricoltura", "FPLD operai agricoli", min(AGRICULTURAL_EMPLOYEE_RATES)),
        ("agricoli_autonomi", "agricoli_autonomi", "Gestione autonoma agricola CD/CM/IAP", min(AGRICULTURAL_SELF_EMPLOYED_RATES)),
    ]
    for profile_id, category_id, management, profile_start in profiles:
        for year in range(profile_start, end_year + 1):
            try:
                rate = rate_for_category_year(category_id, year)
            except Exception:
                if profile_id != "fpld":
                    raise
                rate = RateInfo(0.327, 0.33 if year >= 1996 else 0.327, 0.0889, 0.2381, "fallback", "Fallback per anno senza aliquota.")
            cap = capitalization_for_year(year)
            rate_rows.append(
                {
                    "anno": year,
                    "profilo_aliquota_id": profile_id,
                    "gestione": management,
                    "aliquota_finanziamento": rate.aliquota_finanziamento,
                    "aliquota_computo": rate.aliquota_computo,
                    "quota_lavoratore": rate.quota_lavoratore,
                    "quota_datore": rate.quota_datore,
                    "tasso_capitalizzazione": cap.tasso,
                    "coefficiente_rivalutazione": 1 + cap.tasso,
                    "pil_anno_finale": cap.pil_anno_finale,
                    "pil_finale_milioni": cap.pil_finale_milioni,
                    "pil_anno_iniziale": cap.pil_anno_iniziale,
                    "pil_iniziale_milioni": cap.pil_iniziale_milioni,
                    "edizione_pil": cap.edizione_pil,
                    "tasso_ufficiale_pubblicato": cap.tasso_ufficiale_pubblicato,
                    "fonte_id": rate.fonte_id + "; " + cap.fonte_id,
                    "natura_dato": cap.natura_dato,
                    "note": rate.note + " " + cap.note,
                }
            )
    coefficient_rows: list[dict[str, object]] = []
    for period in COEFFICIENT_PERIODS:
        for age, coeff in dict(period["coefficients"]).items():
            coefficient_rows.append(
                {
                    "periodo_dal": period["periodo_dal"],
                    "periodo_al": period["periodo_al"],
                    "eta": age,
                    "coefficiente": float(coeff) / 100.0,
                    "fonte_id": period["fonte_id"],
                    "norma": period["norma"],
                    "note": period["note"],
                }
            )
    return pd.DataFrame(rate_rows), pd.DataFrame(coefficient_rows), mortality


def run_pension_paid_calculator(scenario_id: str | None = None) -> pd.DataFrame:
    prepare_directories([MORTALITY_RAW_DIR])
    scenarios = read_scenarios()
    if scenario_id:
        scenarios = [scenario for scenario in scenarios if str(scenario.get("scenario_id")) == scenario_id]
    if not scenarios:
        raise ValueError(f"Nessuno scenario trovato per scenario_id={scenario_id!r}")

    mortality = build_mortality_table()
    careers = []
    results = []
    for scenario in scenarios:
        career = build_simplified_career(scenario)
        careers.append(career)
        results.append(calculate_paid_pension_metrics(career, scenario, mortality))

    career_table = pd.concat(careers, ignore_index=True) if careers else pd.DataFrame()
    result_table = pd.concat(results, ignore_index=True) if results else pd.DataFrame()
    rate_table, coefficient_table, mortality_table = parameter_tables(mortality)
    category_table = pd.DataFrame(CATEGORY_ROWS)

    save_table(career_table, ANALYTIC_OUTPUT_PATHS["calcolatore_pensione_pagata_carriera"])
    save_table(result_table, ANALYTIC_OUTPUT_PATHS["calcolatore_pensione_pagata_base"])
    save_table(rate_table, ANALYTIC_OUTPUT_PATHS["calcolatore_pensione_pagata_parametri"])
    save_table(coefficient_table, ANALYTIC_OUTPUT_PATHS["calcolatore_pensione_pagata_coefficienti"])
    save_table(category_table, ANALYTIC_OUTPUT_PATHS["calcolatore_pensione_pagata_categorie"])
    save_table(mortality_table, ANALYTIC_OUTPUT_PATHS["calcolatore_pensione_pagata_mortalita"])
    save_table(_contract_wages_table, ANALYTIC_OUTPUT_PATHS["calcolatore_pensione_pagata_ccnl"])
    return result_table


if __name__ == "__main__":
    print(run_pension_paid_calculator().to_string(index=False))
