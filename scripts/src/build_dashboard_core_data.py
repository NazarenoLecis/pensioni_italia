from __future__ import annotations

from itertools import product
from io import BytesIO
import json
from pathlib import Path
import re
import sys
from typing import Iterable

import pandas as pd
import requests

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from build_pension_indicators import FINAL_TABLE_SCHEMAS
from config import FINAL_TABLE_PATHS, LOG_PATHS, RAW_DATA_DIR
from utils import prepare_directories, save_table

APPENDICE_PENSIONI_URL = (
    "https://www.inps.it/content/dam/inps-site/pdf/dati-analisi-bilanci/"
    "rapporti-annuali/xxv-rapporto-annuale/3_Le_prestazioni_pensionistiche_2026.xlsx"
)
APPENDICI_STORICHE = [
    {
        "anno": 2023,
        "fonte_id": "inps_appendice_xxiii",
        "url": "https://www.inps.it/content/dam/inps-site/pdf/dati-analisi-bilanci/rapporti-annuali/xxiii-rapporto-annuale/3_Le_prestazioni_pensionistiche_2024.xlsx",
    },
    {
        "anno": 2024,
        "fonte_id": "inps_appendice_xxiv",
        "url": "https://www.inps.it/content/dam/inps-site/pdf/dati-analisi-bilanci/rapporti-annuali/xxiv-rapporto-annuale/3_Le_prestazioni_pensionistiche_2025.xlsx",
    },
]
APPENDICI_BILANCIO = [
    (2023, "inps_appendice_xxiii", "https://www.inps.it/content/dam/inps-site/pdf/dati-analisi-bilanci/rapporti-annuali/xxiii-rapporto-annuale/2_Le_principali_voci_di_bilancio_2024.xlsx"),
    (2024, "inps_appendice_xxiv", "https://www.inps.it/content/dam/inps-site/pdf/dati-analisi-bilanci/rapporti-annuali/xxiv-rapporto-annuale/2_Le_principali_voci_di_bilancio_2025.xlsx"),
    (2025, "inps_appendice_xxv", "https://www.inps.it/content/dam/inps-site/pdf/dati-analisi-bilanci/rapporti-annuali/xxv-rapporto-annuale/2_Le_principali_voci_di_bilancio_2026.xlsx"),
]
CASELLARIO_2024_PDF_URL = "https://servizi2.inps.it/servizi/osservatoristatistici/api/getAllegato/?idAllegato=1007"
INPS_SOCIAL_REPORT_2017_2021_URL = "https://www.inps.it/content/dam/inps-site/pdf/dati-analisi-bilanci/bilancio-sociale/3351KEY-tomo_a_rendiconto_sociale_2017-2021_e_relazione_fine_mandato.pdf"
OECD_PUBLIC_PENSION_SPENDING_URL = "https://stat.link/files/e40274c1-en/92ur17.xlsx"
GIAS_COMPONENT_REPORTS = [
    {
        "filename": "2021.pdf",
        "url": "https://servizi2.inps.it/servizi/ProvvedimentiFE/ProvvedimentiCDA/DownloadFile/21?nomefile=DELIBERAZIONE+N.112+del+13+Luglio+2022.pdf",
        "years": [(2020, 0), (2021, 2)],
    },
    {
        "filename": "2023.pdf",
        "url": "https://www.inps.it/content/dam/inps-site/pdf/datiebilanci/bilanci-e-rendiconti/rendicontigenerali/documents/2023/rendiconto_parte1/CA2024_0020_Rend_2023_02_Del_All_Rel_CdA_INT.pdf",
        "years": [(2022, 0), (2023, 1)],
    },
    {
        "filename": "2024.pdf",
        "url": "https://www.inps.it/content/dam/inps-site/pdf/datiebilanci/bilanci-e-rendiconti/rendicontigenerali/documents/2024/CA2025_0087_Rend_2024_02_Del_All_Rel_CdA_INT.pdf",
        "years": [(2023, 0), (2024, 1)],
    },
]
GIAS_COMPONENTS = [
    ("oneri_pensionistici", "Oneri pensionistici", r"Per oneri pensionistici"),
    ("mantenimento_salario", "Mantenimento del salario", r"Per mantenimento del salario"),
    ("famiglia", "Interventi a sostegno della famiglia", r"Per interventi a sostegno della famiglia"),
    ("riduzione_oneri_previdenziali", "Riduzioni di oneri previdenziali", r"Per prestaz\.ni economiche derivanti da riduz\.ne di oneri prev\.ziali"),
    ("sgravi_agevolazioni", "Sgravi e altre agevolazioni", r"Per sgravi degli oneri sociali ed altre agevolazioni"),
    ("interventi_diversi", "Interventi diversi", r"Per interventi diversi"),
    ("reddito_cittadinanza_inclusione", "Reddito di cittadinanza e inclusione", r"Per reddito e pensione di cittadinanza(?:- ADI - SFL)?"),
]
INPS_INSURED_REPORTS = [
    {
        "name": "xxiii",
        "url": "https://www.inps.it/content/dam/inps-site/pdf/dati-analisi-bilanci/rapporti-annuali/xxiii-rapporto-annuale/RAPPORTO%20ANNUALE_WEB.pdf",
        "marker": "Tabella 1.2 - Lavoratori assicurati INPS",
        "years": [2019, 2020, 2021, 2022, 2023],
        "week_years": [2019, 2020, 2021, 2022, 2023],
        "skip_week_values": 0,
        "total_label": "TOTALE complessivo",
    },
    {
        "name": "xxiv",
        "url": "https://www.inps.it/content/dam/inps-site/pdf/dati-analisi-bilanci/rapporti-annuali/xxiv-rapporto-annuale/RA_XXIV_2025.pdf",
        "marker": "Tabella 1.3 - Lavoratori assicurati INPS",
        "years": [2014, 2019, 2022, 2023, 2024],
        "week_years": [2014, 2019, 2024],
        "skip_week_values": 1,
        "total_label": "TOTALE",
    },
]
INPS_OBSERVATORY_API = "https://servizi2.inps.it/servizi/osservatoristatistici/api"
INPS_OPEN_DATA_API = "https://serviziweb2.inps.it/odapi"

EUROSTAT_PENSION_GDP_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/spr_exp_pens"
    "?lang=en&unit=PC_GDP&spdepb=TOTAL&spdepm=TOTAL&sinceTimePeriod=2000"
)
EUROSTAT_POPULATION_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_pjanaggr3"
    "?lang=en&unit=NR&sex=T&age=TOTAL&sinceTimePeriod=2012"
)
EUROSTAT_REGIONAL_GDP_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10r_2gdp"
    "?lang=en&unit=MIO_EUR&sinceTimePeriod=2012"
)
EUROSTAT_NATIONAL_GDP_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10_gdp"
    "?lang=en&unit=CP_MEUR&na_item=B1GQ&geo=IT&sinceTimePeriod=2010"
)
EUROSTAT_AGGREGATE_REPLACEMENT_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/ilc_pnp3"
    "?lang=en&unit=PC&sinceTimePeriod=2010"
)
EUROSTAT_EMPLOYMENT_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/lfsi_emp_a"
    "?lang=en&indic_em=EMP_LFS&unit=THS_PER&sex=T&age=Y15-64&geo=IT&sinceTimePeriod=2010"
)

EU_COUNTRIES = {
    "EU27_2020": "Unione europea (27)",
    "BE": "Belgio", "BG": "Bulgaria", "CZ": "Cechia", "DK": "Danimarca",
    "DE": "Germania", "EE": "Estonia", "IE": "Irlanda", "EL": "Grecia",
    "ES": "Spagna", "FR": "Francia", "HR": "Croazia", "IT": "Italia",
    "CY": "Cipro", "LV": "Lettonia", "LT": "Lituania", "LU": "Lussemburgo",
    "HU": "Ungheria", "MT": "Malta", "NL": "Paesi Bassi", "AT": "Austria",
    "PL": "Polonia", "PT": "Portogallo", "RO": "Romania", "SI": "Slovenia",
    "SK": "Slovacchia", "FI": "Finlandia", "SE": "Svezia",
}

REGION_NUTS2 = {
    "Piemonte": ["ITC1"], "Valle d'Aosta": ["ITC2"], "Liguria": ["ITC3"],
    "Lombardia": ["ITC4"], "Trentino-Alto Adige": ["ITH1", "ITH2"],
    "Veneto": ["ITH3"], "Friuli Venezia Giulia": ["ITH4"],
    "Emilia-Romagna": ["ITH5"], "Toscana": ["ITI1"], "Umbria": ["ITI2"],
    "Marche": ["ITI3"], "Lazio": ["ITI4"], "Abruzzo": ["ITF1"],
    "Molise": ["ITF2"], "Campania": ["ITF3"], "Puglia": ["ITF4"],
    "Basilicata": ["ITF5"], "Calabria": ["ITF6"], "Sicilia": ["ITG1"],
    "Sardegna": ["ITG2"],
}

# Serie ricostruita sulle tavole omogenee dei Rapporti annuali INPS XVIII-XXII.
# I valori 2023-2025 sono letti direttamente dagli XLSX delle appendici successive.
ANNUAL_REPORT_SERIES = {
    2018: {"pensioni": 20_801_645, "pensionati": 15_994_782, "pensionati_inps": 15_426_847, "reddito": 293_258_000_000, "reddito_inps": 286_728_000_000},
    2019: {"pensioni": 20_871_200, "pensionati": 16_035_165, "pensionati_inps": 15_462_177, "reddito": 300_907_000_000, "reddito_inps": 294_357_000_000},
    2020: {"pensioni": 20_829_100, "pensionati": 16_015_042, "pensionati_inps": 15_489_119, "reddito": 307_209_000_000, "reddito_inps": 300_848_000_000},
    2021: {"pensioni": 20_832_232, "pensionati": 16_098_748, "pensionati_inps": 15_500_737, "reddito": 313_003_000_000, "reddito_inps": 305_761_000_000},
    2022: {"pensioni": 20_826_668, "pensionati": 16_106_583, "pensionati_inps": 15_531_365, "reddito": 321_879_000_000, "reddito_inps": 314_508_000_000},
}

ENTRATE_CONTRIBUTIVE_RENDICONTI = {
    2018: 231_166_000_000,
    2019: 236_211_000_000,
    2020: 225_150_000_000,
    2021: 236_893_000_000,
    2022: 256_138_000_000,
    2023: 269_152_000_000,
    2024: 284_047_000_000,
}

OPEN_DATA_PACKAGES = {
    "pensioni_vigenti_storico": 1656,
    "spesa_casellario_storico": 1811,
    "pensionati_storico": 1820,
    "pensionati_regioni_storico": 1812,
    "spesa_regioni_storico": 1805,
    "pensionati_regioni_classi_importo_storico": 1988,
    "pensioni_classi_importo_storico": 1650,
    "pensionati_reddito_classi_2014": 1182,
    "pubblici_vigenti_area_sesso_2013_2015": 1225,
    "pubblici_vigenti_area_sesso_2014_2018": 1567,
    "conto_economico_2013_2014": 917,
    "conto_economico_2015": 1952,
    "conto_economico_2016": 1962,
    "conto_economico_2017": 1973,
    "conto_economico_2018": 2118,
}


def schema(table_name: str) -> list[str]:
    return FINAL_TABLE_SCHEMAS[table_name]


def frame(table_name: str, rows: list[dict[str, object]]) -> pd.DataFrame:
    result = pd.DataFrame(rows)
    for column in schema(table_name):
        if column not in result.columns:
            result[column] = pd.NA
    return result[schema(table_name)]


def request_bytes(url: str, path: Path) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size:
        return path.read_bytes()
    response = requests.get(url, timeout=90, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    path.write_bytes(response.content)
    return response.content


def request_json(url: str, path: Path) -> dict[str, object]:
    data = request_bytes(url, path)
    return json.loads(data.decode("utf-8-sig"))


def post_inps_observatory(endpoint: str, payload: dict[str, object]) -> dict[str, object]:
    # L'endpoint rifiuta i JSON serializzati con spazi: usa lo stesso formato compatto del client ufficiale.
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    response = requests.post(
        f"{INPS_OBSERVATORY_API}/{endpoint}/",
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        timeout=90,
    )
    response.raise_for_status()
    result = response.json()
    if result.get("error") or result.get("messageType") == "Anonimizzazione":
        raise ValueError(str(result.get("error") or result.get("message")))
    return result


def jsonstat_geo_time(payload: dict[str, object]) -> dict[tuple[str, int], float]:
    """Estrae una risposta Eurostat filtrata fino alle sole dimensioni geo e tempo."""
    dimensions = payload["dimension"]
    ids = list(payload["id"])
    sizes = list(payload["size"])
    geo_index = dimensions["geo"]["category"]["index"]
    time_index = dimensions["time"]["category"]["index"]
    values = payload.get("value", {})
    result: dict[tuple[str, int], float] = {}
    for geo, geo_position in geo_index.items():
        for year, time_position in time_index.items():
            coordinates = [0] * len(ids)
            coordinates[ids.index("geo")] = int(geo_position)
            coordinates[ids.index("time")] = int(time_position)
            flat_index = 0
            for coordinate, size in zip(coordinates, sizes):
                flat_index = flat_index * int(size) + coordinate
            value = values.get(str(flat_index), values.get(flat_index))
            parsed = number(value)
            if parsed is not None:
                result[(str(geo), int(year))] = parsed
    return result


def jsonstat_records(payload: dict[str, object]) -> Iterable[dict[str, object]]:
    """Decodifica una risposta JSON-stat Eurostat preservando tutte le dimensioni."""
    dimensions = payload["dimension"]
    ids = list(payload["id"])
    sizes = [int(size) for size in payload["size"]]
    values = payload.get("value", {})
    categories: list[list[tuple[str, int]]] = []
    for dim_id in ids:
        category_index = dimensions[dim_id]["category"]["index"]
        categories.append(sorted(((str(label), int(position)) for label, position in category_index.items()), key=lambda item: item[1]))
    for combination in product(*categories):
        flat_index = 0
        record: dict[str, object] = {}
        for (label, position), dim_id, size in zip(combination, ids, sizes):
            flat_index = flat_index * size + position
            record[dim_id] = label
        value = values.get(str(flat_index), values.get(flat_index))
        parsed = number(value)
        if parsed is not None:
            record["value"] = parsed
            yield record


def open_data_resource_url(name: str, preferred_format: str = "csv") -> str:
    package_id = OPEN_DATA_PACKAGES[name]
    metadata_path = RAW_DATA_DIR / "inps_open_data_catalog" / f"package_{package_id}.json"
    payload = request_json(f"{INPS_OPEN_DATA_API}/package_show?id={package_id}", metadata_path)
    if not payload.get("success", False):
        raise ValueError(f"Open Data package {package_id} non disponibile")
    resources = payload.get("result", {}).get("resources", [])
    preferred = preferred_format.lower()
    for resource in resources:
        if str(resource.get("format", "")).lower() == preferred and resource.get("url"):
            return str(resource["url"])
    raise ValueError(f"Open Data package {package_id} senza risorsa {preferred_format}")


def read_open_csv(name: str) -> pd.DataFrame:
    url = open_data_resource_url(name, "csv")
    raw_path = RAW_DATA_DIR / "inps_open_data" / f"{name}_{Path(url).name}"
    data = request_bytes(url, raw_path)
    first_line = data.splitlines()[0].decode("latin-1", errors="ignore")
    separator = ";" if first_line.count(";") > first_line.count(",") else ","
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return pd.read_csv(BytesIO(data), sep=separator, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(BytesIO(data), sep=separator, encoding="utf-8", errors="replace")


def read_appendix() -> pd.ExcelFile:
    path = RAW_DATA_DIR / "inps_appendice_xxv" / "3_Le_prestazioni_pensionistiche_2026.xlsx"
    request_bytes(APPENDICE_PENSIONI_URL, path)
    return pd.ExcelFile(path)


def read_historical_appendix(item: dict[str, object]) -> pd.ExcelFile:
    year = int(item["anno"])
    path = RAW_DATA_DIR / "inps_appendici_storiche" / f"prestazioni_pensionistiche_{year}.xlsx"
    request_bytes(str(item["url"]), path)
    return pd.ExcelFile(path)


def number(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("\xa0", "").replace(" ", "")
    if not text:
        return None
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    elif "." in text:
        parts = text.split(".")
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
            text = "".join(parts)
    try:
        return float(text)
    except ValueError:
        return None


def int_number(value: object) -> int | None:
    parsed = number(value)
    return None if parsed is None else int(round(parsed))


def class_bounds(label: object) -> tuple[float | None, float | None]:
    text = str(label or "").lower().replace(" ", "")
    if "finoa" in text:
        upper = number(text.split("finoa", 1)[1])
        return 0.0, upper
    if "oltre" in text or "epi" in text:
        digits = "".join(ch if ch.isdigit() or ch in ",." else " " for ch in text)
        parts = [number(part) for part in digits.split() if number(part) is not None]
        return (parts[0], None) if parts else (None, None)
    if "-" in text:
        left, right = text.split("-", 1)
        return number(left), number(right)
    values = [number(value) for value in re.findall(r"\d+(?:[,.]\d+)?", text)]
    values = [value for value in values if value is not None]
    if text.startswith("da") and len(values) >= 2:
        return values[0], values[1]
    if len(values) == 1:
        return 0.0, values[0]
    return None, None


def add_annual(
    rows: list[dict[str, object]],
    anno: int,
    indicatore_id: str,
    famiglia: str,
    fonte: str,
    valore: object,
    unita: str,
    area: str,
    note: str,
) -> None:
    parsed = number(valore)
    if parsed is None:
        return
    rows.append(
        {
            "anno": int(anno),
            "indicatore_id": indicatore_id,
            "famiglia_definizione": famiglia,
            "fonte_id": fonte,
            "valore": parsed,
            "unita": unita,
            "area": area,
            "note": note,
        }
    )


def build_annual_from_open_data(rows: list[dict[str, object]], log: list[dict[str, object]]) -> None:
    pensions = read_open_csv("pensioni_vigenti_storico")
    pensions["Numero pensioni"] = pensions["Numero pensioni"].map(number)
    for anno, group in pensions.groupby("Anno", dropna=True):
        add_annual(
            rows,
            int(anno),
            "pensioni_vigenti",
            "stock_amministrativo",
            "inps_open_data",
            group["Numero pensioni"].sum(),
            "numero",
            "Italia",
            "Trattamenti pensionistici vigenti INPS; dataset ID-5080.",
        )

    spending = read_open_csv("spesa_casellario_storico")
    spending["Importo complessivo annuo"] = spending["Importo complessivo annuo"].map(number)
    for anno, group in spending.groupby("Anno", dropna=True):
        add_annual(
            rows,
            int(anno),
            "spesa_pensionistica_casellario",
            "casellario_pensionati",
            "inps_open_data",
            group["Importo complessivo annuo"].sum() * 1_000_000,
            "euro",
            "Italia",
            "Importo complessivo annuo Casellario pensioni totali; dataset ID-5296, valori fonte in milioni.",
        )

    pensioners = read_open_csv("pensionati_storico")
    pensioners["Numero beneficiari"] = pensioners["Numero beneficiari"].map(number)
    for anno, group in pensioners.groupby("Anno", dropna=True):
        add_annual(
            rows,
            int(anno),
            "pensionati",
            "persone",
            "inps_open_data",
            group["Numero beneficiari"].sum(),
            "numero",
            "Italia",
            "Beneficiari del sistema pensionistico italiano; dataset ID-5300.",
        )

    by_indicator = {}
    for row in rows:
        by_indicator.setdefault(row["indicatore_id"], {})[row["anno"]] = row["valore"]
    for anno, pensions_value in by_indicator.get("pensioni_vigenti", {}).items():
        pensioners_value = by_indicator.get("pensionati", {}).get(anno)
        if pensioners_value:
            add_annual(
                rows,
                int(anno),
                "trattamenti_per_pensionato",
                "derivato",
                "elaborazione_repo",
                float(pensions_value) / float(pensioners_value),
                "rapporto",
                "Italia",
                "Pensioni vigenti divise per pensionati; attenzione ai perimetri delle due fonti Open Data storiche.",
            )

    log.append({"fonte": "inps_open_data", "tabella": "tabella_annuale_pensioni", "righe": len(rows), "stato": "ok"})


def build_management_history_from_open_data(management_rows: list[dict[str, object]], log: list[dict[str, object]]) -> None:
    """Estende le gestioni INPS 2010-2017 con l'Open Data ufficiale ID-5080."""
    table = read_open_csv("pensioni_vigenti_storico")
    table["Numero pensioni"] = table["Numero pensioni"].map(number)
    table["Importo medio mensile"] = table["Importo medio mensile"].map(number)
    for (year, gestione), group in table.groupby(["Anno", "Tipo di gestione"], dropna=True):
        group_name = clean_label(gestione)
        if not group_name or group_name.lower() == "totale":
            continue
        management_rows.append({"anno": int(year), "gestione_id": normalize_id(group_name), "gestione_nome": group_name, "gruppo_gestione": classify_professional_group(group_name), "indicatore_id": "pensioni_vigenti", "fonte_id": "inps_open_data", "valore": group["Numero pensioni"].sum(), "unita": "numero", "note": "Pensioni vigenti per gestione; Open Data INPS ID-5080."})
        count = group["Numero pensioni"].sum()
        if count:
            weighted = (group["Numero pensioni"] * group["Importo medio mensile"]).sum() / count
            management_rows.append({"anno": int(year), "gestione_id": normalize_id(group_name), "gestione_nome": group_name, "gruppo_gestione": classify_professional_group(group_name), "indicatore_id": "importo_medio_pensione", "fonte_id": "inps_open_data", "valore": weighted, "unita": "euro", "note": "Importo medio mensile ponderato per gestione; Open Data INPS ID-5080."})
    log.append({"fonte": "inps_open_data", "tabella": "tabella_gestioni", "righe": len(management_rows), "stato": "ok"})


def build_public_employee_history_from_open_data(management_rows: list[dict[str, object]], log: list[dict[str, object]]) -> None:
    """Aggiunge la gestione dipendenti pubblici storica dai dataset Open Data dedicati."""
    sources = [
        ("pubblici_vigenti_area_sesso_2013_2015", "inps_open_data", {2013}),
        ("pubblici_vigenti_area_sesso_2014_2018", "inps_open_data", {2014, 2015, 2016, 2017, 2018}),
    ]
    added = 0
    for dataset_name, source_id, allowed_years in sources:
        table = read_open_csv(dataset_name)
        table.columns = [clean_label(column) for column in table.columns]
        count_column = next((column for column in table.columns if column.lower() == "numero pensioni"), None)
        average_column = next((column for column in table.columns if column.lower() == "importo medio mensile"), None)
        sex_column = next((column for column in table.columns if column.lower() == "sesso"), None)
        area_column = next((column for column in table.columns if "area della sede" in column.lower()), None)
        if not count_column or not average_column:
            continue
        table[count_column] = table[count_column].map(number)
        table[average_column] = table[average_column].map(number)
        if area_column and table[area_column].astype(str).str.lower().str.strip().eq("totale").any():
            table = table[table[area_column].astype(str).str.lower().str.strip().eq("totale")]
        if sex_column and table[sex_column].astype(str).str.lower().str.strip().eq("totale").any():
            table = table[table[sex_column].astype(str).str.lower().str.strip().eq("totale")]
        for year, group in table.groupby("Anno", dropna=True):
            year = int(year)
            if year not in allowed_years:
                continue
            count = group[count_column].sum()
            if not count:
                continue
            weighted = (group[count_column] * group[average_column]).sum() / count
            common = {
                "anno": year,
                "gestione_id": "gestione_dipendenti_pubblici_open_data",
                "gestione_nome": "Gestione Dipendenti Pubblici",
                "gruppo_gestione": "ex_dipendenti_pubblici",
                "fonte_id": source_id,
            }
            management_rows.append({**common, "indicatore_id": "pensioni_vigenti", "valore": count, "unita": "numero", "note": f"Gestione dipendenti pubblici, pensioni vigenti aggregate da Open Data INPS {OPEN_DATA_PACKAGES[dataset_name]}."})
            management_rows.append({**common, "indicatore_id": "importo_medio_pensione", "valore": weighted, "unita": "euro", "note": f"Importo medio mensile ponderato della gestione dipendenti pubblici; Open Data INPS {OPEN_DATA_PACKAGES[dataset_name]}."})
            added += 2
    log.append({"fonte": "inps_open_data_pubblici", "tabella": "tabella_gestioni", "righe": added, "stato": "ok" if added else "dato_non_disponibile"})


def build_contributions(rows: list[dict[str, object]], log: list[dict[str, object]]) -> None:
    frames = []
    for name in [
        "conto_economico_2013_2014",
        "conto_economico_2015",
        "conto_economico_2016",
        "conto_economico_2017",
        "conto_economico_2018",
    ]:
        table = read_open_csv(name)
        frames.append(table)
    table = pd.concat(frames, ignore_index=True)
    table["voce_norm"] = table["Denominazione conto"].astype(str).str.lower()
    table["Importo"] = table["Importo"].map(number)
    mask = table["voce_norm"].str.contains(
        "aliquote contributive|quote di partecipazione degli iscritti all.onere di specifiche gestioni",
        regex=True,
        na=False,
    )
    contribution_rows = table.loc[mask].copy()
    contribution_rows["voce_norm"] = contribution_rows["voce_norm"].str.strip()
    contribution_rows = contribution_rows.drop_duplicates(["Anno", "voce_norm", "Importo"])
    for anno, group in contribution_rows[contribution_rows["Anno"] < 2018].groupby("Anno", dropna=True):
        add_annual(
            rows,
            int(anno),
            "entrate_contributive_inps",
            "contributi",
            "inps_bilanci",
            group["Importo"].sum(),
            "euro",
            "Italia",
            "Entrate contributive INPS: aliquote contributive e quote di partecipazione degli iscritti, conto economico generale.",
        )
    for anno, valore in ENTRATE_CONTRIBUTIVE_RENDICONTI.items():
        add_annual(
            rows,
            anno,
            "entrate_contributive_inps",
            "contributi",
            "inps_rendiconti",
            valore,
            "euro",
            "Italia",
            "Entrate contributive accertate di competenza finanziaria; rendiconti generali INPS.",
        )
    log.append({"fonte": "inps_open_data_bilanci", "tabella": "tabella_annuale_pensioni", "righe": len(contribution_rows), "stato": "ok"})


def build_consistent_annual_series(rows: list[dict[str, object]], log: list[dict[str, object]]) -> None:
    for year, values in ANNUAL_REPORT_SERIES.items():
        note = f"Rapporto annuale INPS, prestazioni pensionistiche, anno {year}; perimetro omogeneo con le appendici successive."
        if year <= 2021:
            add_annual(rows, year, "pensioni_vigenti", "stock_amministrativo", "inps_rapporti_annuali", values["pensioni"], "numero", "Italia - INPS", note)
        add_annual(rows, year, "pensionati", "persone", "inps_rapporti_annuali", values["pensionati"], "numero", "Italia - complessivi", note)
        add_annual(rows, year, "pensionati", "persone", "inps_rapporti_annuali", values["pensionati_inps"], "numero", "Italia - INPS", note)
        add_annual(rows, year, "reddito_pensionistico_totale", "reddito_pensionistico", "inps_rapporti_annuali", values["reddito"], "euro", "Italia - complessivi", note)
        add_annual(rows, year, "reddito_pensionistico_totale", "reddito_pensionistico", "inps_rapporti_annuali", values["reddito_inps"], "euro", "Italia - INPS", note)
        add_annual(rows, year, "reddito_pensionistico_medio_mensile", "reddito_pensionistico", "elaborazione_repo", values["reddito"] / values["pensionati"] / 12, "euro", "Italia - complessivi", "Reddito pensionistico annuo complessivo diviso per pensionati e per 12 mesi.")
    log.append({"fonte": "inps_rapporti_annuali", "tabella": "tabella_annuale_pensioni", "righe": len(ANNUAL_REPORT_SERIES), "stato": "ok"})


def build_state_transfers(
    annual_rows: list[dict[str, object]],
    transfer_rows: list[dict[str, object]],
    log: list[dict[str, object]],
) -> None:
    values_by_year: dict[int, tuple[float, str]] = {}
    contributions_by_year: dict[int, tuple[float, str]] = {}
    for report_year, source_id, url in APPENDICI_BILANCIO:
        path = RAW_DATA_DIR / "inps_appendici_bilancio" / f"principali_voci_bilancio_{report_year}.xlsx"
        xl = pd.ExcelFile(BytesIO(request_bytes(url, path)))
        table = pd.read_excel(xl, sheet_name="2.4", header=None)
        years = [int_number(value) for value in table.iloc[2, 2:].tolist()]
        for _, record in table.iterrows():
            label = clean_label(record.iloc[1] if len(record) > 1 else "")
            if label not in {"Trasferimenti dal bilancio dello Stato", "Entrate contributive"}:
                continue
            for year, value in zip(years, record.iloc[2:].tolist()):
                parsed = number(value)
                if year and parsed is not None:
                    target = values_by_year if label.startswith("Trasferimenti") else contributions_by_year
                    target[year] = (parsed * 1_000_000, source_id)

    for name in ["conto_economico_2013_2014", "conto_economico_2015", "conto_economico_2016", "conto_economico_2017", "conto_economico_2018"]:
        table = read_open_csv(name)
        table["Importo"] = table["Importo"].map(number)
        labels = table["Denominazione conto"].map(clean_label).str.lower()
        matches = table[labels.isin({"trasferimenti da parte dello stato", "trasferimenti dal bilancio dello stato"})]
        for year, group in matches.groupby("Anno", dropna=True):
            parsed = group["Importo"].sum()
            if int(year) not in values_by_year and pd.notna(parsed):
                values_by_year[int(year)] = (float(parsed), "inps_open_data_bilanci")

    for year, (value, source_id) in sorted(values_by_year.items()):
        transfer_rows.append(
            {
                "anno": year,
                "fonte_id": source_id,
                "perimetro": "Bilancio finanziario INPS",
                "voce_id": "trasferimenti_bilancio_stato",
                "voce_nome": "Trasferimenti dal bilancio dello Stato",
                "categoria_analitica": "trasferimenti_correnti",
                "finalita": "complesso_attivita_inps",
                "gestione_id": "totale_inps",
                "indicatore_id": "trasferimenti_stato_inps",
                "valore": value,
                "unita": "euro",
                "note": "Trasferimenti correnti complessivi dal bilancio dello Stato; non sono tutti destinati esclusivamente alle pensioni.",
            }
        )
    if 2025 in contributions_by_year:
        value, source_id = contributions_by_year[2025]
        add_annual(annual_rows, 2025, "entrate_contributive_inps", "contributi", source_id, value, "euro", "Italia", "Entrate contributive accertate; Rendiconto generale INPS 2025.")
    log.append({"fonte": "inps_appendici_bilancio", "tabella": "tabella_trasferimenti_inps", "righe": len(transfer_rows), "stato": "ok"})


def gias_component_values(page_text: str, pattern: str, expected_values: int) -> list[float]:
    """Legge i valori in milioni dalla tavola GIAS del rendiconto INPS."""
    match = re.search(pattern, page_text, flags=re.IGNORECASE)
    if not match:
        return []
    next_row = re.search(r"\n\s*(?:1\.[1-7]\.|2\s*$)", page_text[match.end():], flags=re.MULTILINE)
    tail = page_text[match.end():match.end() + next_row.start() if next_row else len(page_text)]
    values = re.findall(r"(?m)^\s*(\d{1,3}(?:\.\d{3})*)\s*$", tail)
    return [float(value.replace(".", "")) for value in values[:expected_values]]


def build_state_transfer_components(transfer_rows: list[dict[str, object]], log: list[dict[str, object]]) -> None:
    """Estrae le componenti GIAS da PDF ufficiali, quando l'API non le espone."""
    try:
        import fitz
    except ImportError:
        log.append({"fonte": "inps_rendiconti_gias", "tabella": "tabella_trasferimenti_inps", "righe": 0, "stato": "PyMuPDF_non_disponibile"})
        return

    values: dict[tuple[int, str], float] = {}
    cache = RAW_DATA_DIR / "inps_trasferimenti_componenti"
    for report in GIAS_COMPONENT_REPORTS:
        path = cache / str(report["filename"])
        document = fitz.open(stream=request_bytes(str(report["url"]), path), filetype="pdf")
        page_text = next((page.get_text() for page in document if "TRASFERIMENTI DAL BILANCIO DELLO STATO" in page.get_text() and "Per oneri pensionistici" in page.get_text()), "")
        document.close()
        if not page_text:
            continue
        required = 3 if str(report["filename"]) == "2021.pdf" else 2
        for component_id, _, pattern in GIAS_COMPONENTS:
            parsed = gias_component_values(page_text, pattern, required)
            if len(parsed) != required:
                continue
            for year, column in report["years"]:
                values[(int(year), component_id)] = parsed[int(column)] * 1_000_000

    for (year, component_id), value in sorted(values.items()):
        label = next(label for identifier, label, _ in GIAS_COMPONENTS if identifier == component_id)
        transfer_rows.append(
            {
                "anno": year,
                "fonte_id": "inps_rendiconti_gias",
                "perimetro": "Gestione interventi assistenziali e sostegno alle gestioni previdenziali (GIAS)",
                "voce_id": f"gias_{component_id}",
                "voce_nome": label,
                "categoria_analitica": component_id,
                "finalita": "componenti_trasferimenti_gias",
                "gestione_id": "gias",
                "indicatore_id": "trasferimenti_stato_inps_per_componente",
                "valore": value,
                "unita": "euro",
                "note": "Rendiconto generale INPS, conto economico GIAS, valori in milioni convertiti in euro. La serie mostra esclusivamente gli anni consuntivi pubblicati nelle tavole omogenee.",
            }
        )
    log.append({"fonte": "inps_rendiconti_gias", "tabella": "tabella_trasferimenti_inps", "righe": len(values), "stato": "ok" if values else "tabella_non_trovata"})


def build_oecd_pension_spending(comparison_rows: list[dict[str, object]], log: list[dict[str, object]]) -> None:
    """Aggiunge il benchmark OCSE da un file XLSX ufficiale scaricabile."""
    path = RAW_DATA_DIR / "oecd" / "pensions_at_a_glance_2025_table_8_2.xlsx"
    table = pd.read_excel(BytesIO(request_bytes(OECD_PUBLIC_PENSION_SPENDING_URL, path)), sheet_name="t8-2", header=None)
    for country, label in [("Italy", "Italia"), ("OECD", "Media OCSE")]:
        row = table[table.iloc[:, 0].astype(str).str.strip().eq(country)]
        if row.empty:
            continue
        values = row.iloc[0]
        for year, column in [(2000, 4), (2010, 5), (2020, 6), (2021, 7)]:
            value = number(values.iloc[column])
            if value is None:
                continue
            comparison_rows.append(
                {
                    "anno": year,
                    "paese": label,
                    "indicatore_id": "spesa_pensionistica_pil_oecd_pubblica",
                    "definizione": "Spesa pubblica lorda per pensioni di vecchiaia e superstiti in denaro, percentuale del PIL",
                    "fonte_id": "oecd_pensions_at_a_glance_2025",
                    "valore": value,
                    "unita": "percentuale_pil",
                    "note": "OECD Pensions at a Glance 2025, tabella 8.2. Il valore 'latest' e' 2021 per l'Italia; la media OCSE combina l'ultimo anno disponibile per paese.",
                }
            )
    log.append({"fonte": "oecd_pensions_at_a_glance_2025", "tabella": "tabella_confronto_europeo", "righe": len(comparison_rows), "stato": "ok"})


def build_replacement_rate_projections(comparison_rows: list[dict[str, object]], log: list[dict[str, object]]) -> None:
    """Registra la tavola RGS 6.4: valori osservati e proiezioni dello scenario base."""
    years = [2010, 2020, 2030, 2040, 2050, 2060, 2070]
    series = {
        ("dipendenti_privati", "obbligatoria", "lordo"): [73.6, 71.7, 72.1, 61.8, 60.3, 58.8, 58.4],
        ("dipendenti_privati", "obbligatoria", "netto"): [82.7, 81.5, 77.0, 67.4, 66.0, 64.6, 64.1],
        ("autonomi", "obbligatoria", "lordo"): [72.1, 54.9, 50.0, 46.8, 47.8, 47.0, 46.7],
        ("autonomi", "obbligatoria", "netto"): [93.0, 77.2, 70.7, 67.0, 68.1, 67.2, 66.9],
        ("dipendenti_privati", "obbligatoria_complementare", "lordo"): [73.6, 77.1, 79.7, 71.0, 69.2, 66.4, 66.0],
        ("dipendenti_privati", "obbligatoria_complementare", "netto"): [82.7, 88.4, 86.7, 79.3, 77.6, 74.5, 74.2],
        ("autonomi", "obbligatoria_complementare", "lordo"): [72.1, 60.2, 57.7, 56.9, 57.6, 55.4, 55.2],
        ("autonomi", "obbligatoria_complementare", "netto"): [100.8, 89.1, 86.6, 87.2, 88.0, 84.5, 84.3],
    }
    for (worker, coverage, gross_net), values in series.items():
        for year, value in zip(years, values):
            comparison_rows.append(
                {
                    "anno": year,
                    "paese": "Italia",
                    "indicatore_id": "tasso_sostituzione_rgs",
                    "definizione": f"{worker}|{coverage}|{gross_net}",
                    "fonte_id": "rgs_rapporti",
                    "valore": value,
                    "unita": "percentuale",
                    "note": "RGS, Rapporto n. 26/2025, tavola 6.4, scenario nazionale base. I punti dal 2030 sono proiezioni; le serie nette usano il caso senza coniuge a carico indicato nella tavola.",
                }
            )
    log.append({"fonte": "rgs_rapporti", "tabella": "tabella_confronto_europeo", "righe": len(series) * len(years), "stato": "ok"})


def observatory_region_measure(observatory_id: str, name: str, year: int, measure_id: str, statistic: str) -> dict[str, float]:
    request = {
        "id_osservatorio": observatory_id,
        "nome_osservatorio": name,
        "language": "",
        "totalRow": True,
        "totalColumn": True,
        "subtotalRow": True,
        "subtotalColumn": True,
        "selections": {
            "rows": [{"id": "Regione", "label": "Regione", "order": 1, "aggregate": True, "expand": "", "hide": False}],
            "cols": [],
            "measures": [{"id": measure_id, "label": measure_id, "order": 0, "statistic": statistic}],
            "filters": [{"id": "anno", "label": "Anno-", "values": [str(year)]}],
        },
    }
    filtered = post_inps_observatory("getFiltriOsservatorio", request)
    request["selections"]["filters"] = filtered["selections"]["filters"]
    response = post_inps_observatory("getDatiOsservatorio", request)
    result: dict[str, float] = {}
    for item in response.get("values", []):
        region = region_name_for_eurostat(str(item.get("value", "")))
        if region not in REGION_NUTS2:
            continue
        measures = item.get("measures") or []
        if measures:
            parsed = number(measures[0].get("value"))
            if parsed is not None:
                result[region] = parsed
    return result


def build_current_regions_from_api(territorial_rows: list[dict[str, object]], log: list[dict[str, object]]) -> None:
    added = 0
    for year in range(2017, 2026):
        try:
            pensioners = observatory_region_measure("413", "Beneficiari totali", year, "_FREQ_SUM", "SUM")
            pensions = observatory_region_measure("416", "Prestazioni pensionistiche totali", year, "_FREQ_SUM", "SUM")
            average_annual = observatory_region_measure("416", "Prestazioni pensionistiche totali", year, "Importo medio annuo (euro)", "")
        except (requests.RequestException, ValueError, KeyError):
            continue
        for region in REGION_NUTS2:
            pensioner_count = pensioners.get(region)
            pension_count = pensions.get(region)
            average = average_annual.get(region)
            if pensioner_count is not None:
                territorial_rows.append(territorial(year, "regione", region, "pensionati", pensioner_count, "numero", "inps_osservatori_api", "Beneficiari totali per regione; Osservatori statistici INPS."))
                added += 1
            if pension_count is not None:
                territorial_rows.append(territorial(year, "regione", region, "pensioni_vigenti", pension_count, "numero", "inps_osservatori_api", "Prestazioni pensionistiche per regione; Osservatori statistici INPS."))
            if average is not None:
                territorial_rows.append(territorial(year, "regione", region, "importo_medio_pensione_mensile_regionale", average / 12, "euro", "inps_osservatori_api", "Importo lordo medio annuo della prestazione diviso per 12; Osservatori statistici INPS."))
            if pension_count is not None and average is not None:
                territorial_rows.append(territorial(year, "regione", region, "spesa_pensionistica_regionale", pension_count * average, "euro", "elaborazione_repo", "Numero di prestazioni per importo lordo medio annuo; Osservatori statistici INPS."))
    log.append({"fonte": "inps_osservatori_api", "tabella": "tabella_territoriale", "righe": added, "stato": "ok" if added else "anni_non_disponibili"})


def append_profession_snapshot(
    xl: pd.ExcelFile,
    year: int,
    source_id: str,
    profession_rows: list[dict[str, object]],
) -> None:
    sheet = pd.read_excel(xl, sheet_name="3.9", header=None)
    for _, record in sheet.iterrows():
        values = record.tolist()
        gestione = str(values[1]).strip() if len(values) > 1 and pd.notna(values[1]) else ""
        if not gestione or gestione.startswith("Tabella") or gestione in {"Gestione", "TOTALE"} or gestione.startswith("*") or gestione.startswith("di cui") or gestione.startswith("-"):
            continue
        profession_rows.append(
            {
                "anno": year,
                "fonte_id": source_id,
                "gestione_id": normalize_id(gestione),
                "gestione_nome": clean_label(gestione),
                "categoria_professionale": classify_professional_group(gestione),
                "criterio_classificazione": "gestione_previdenziale",
                "tipo_pensione": "previdenziale",
                "sesso": "Totale",
                "classe_eta": "Tutte",
                "territorio": "Italia",
                "indicatore_id": "prestazioni_per_categoria_professionale",
                "pensionati": pd.NA,
                "prestazioni": number(values[8] if len(values) > 8 else None),
                "importo_complessivo": pd.NA,
                "importo_medio_annuo": pd.NA,
                "importo_medio_mensile": number(values[10] if len(values) > 10 else None),
                "unita": "numero",
                "duplicazione_teste": "prestazioni_non_persone",
                "note": f"Prestazioni previdenziali INPS per gestione; tabella 3.9, anno {year}. La categoria e' ricostruita dalla gestione.",
            }
        )


def append_income_distribution(
    xl: pd.ExcelFile,
    year: int,
    source_id: str,
    distribution_rows: list[dict[str, object]],
) -> None:
    sheet = pd.read_excel(xl, sheet_name="3.4", header=None)
    sex_columns = [
        ("Maschi", 2, 5),
        ("Femmine", 6, 9),
        ("Totale", 10, 13),
    ]
    for _, record in sheet.iterrows():
        values = record.tolist()
        label = str(values[1]).strip() if len(values) > 1 and pd.notna(values[1]) else ""
        if not label or label in {"Classe di importo mensile***", "TOTALE"} or label.startswith("Tabella") or label.startswith("*"):
            continue
        minimum, maximum = class_bounds(label)
        for sex, count_index, amount_index in sex_columns:
            count = number(values[count_index] if len(values) > count_index else None)
            amount_million = number(values[amount_index] if len(values) > amount_index else None)
            common = (year, "pensionati_inps", "reddito_pensionistico_mensile", label, minimum, maximum, sex, "Italia - INPS")
            if count is not None:
                distribution_rows.append(distribution(*common, "pensionati_per_classe_reddito_pensionistico", count, "numero", source_id, f"Pensionati INPS per reddito pensionistico mensile complessivo e sesso; tabella 3.4, anno {year}."))
            if amount_million is not None:
                amount = amount_million * 1_000_000
                distribution_rows.append(distribution(*common, "reddito_pensionistico_totale", amount, "euro", source_id, f"Reddito pensionistico annuo complessivo della classe per sesso; tabella 3.4, anno {year}."))
                if count:
                    distribution_rows.append(distribution(*common, "reddito_pensionistico_medio_mensile_classe", amount / count / 12, "euro", "elaborazione_repo", "Reddito annuo della classe diviso per pensionati e per 12 mesi."))


def append_age_distribution(
    xl: pd.ExcelFile,
    year: int,
    source_id: str,
    distribution_rows: list[dict[str, object]],
) -> None:
    sheet = pd.read_excel(xl, sheet_name="3.3", header=None)
    sex_columns = [
        ("Maschi", 2, 4),
        ("Femmine", 5, 7),
        ("Totale", 8, 10),
    ]
    for _, record in sheet.iterrows():
        values = record.tolist()
        label = str(values[1]).strip() if len(values) > 1 and pd.notna(values[1]) else ""
        if not label or label in {"Classe di eta", "Classe di età", "TOTALE"} or label.startswith("Tabella") or label.startswith("*"):
            continue
        if "anni" not in label.lower() and "oltre" not in label.lower():
            continue
        for sex, count_index, average_index in sex_columns:
            count = number(values[count_index] if len(values) > count_index else None)
            average = number(values[average_index] if len(values) > average_index else None)
            if count is not None:
                distribution_rows.append(
                    {
                        "anno": year,
                        "popolazione": "pensionati_inps",
                        "misura_distribuzione": "classe_eta",
                        "classe_importo": "Tutte",
                        "classe_importo_min": pd.NA,
                        "classe_importo_max": pd.NA,
                        "classe_eta": clean_label(label),
                        "sesso": sex,
                        "territorio": "Italia - INPS",
                        "indicatore_id": "pensionati_per_classe_eta",
                        "fonte_id": source_id,
                        "valore": count,
                        "unita": "numero",
                        "note": f"Pensionati INPS per classe di eta e sesso; tabella 3.3, anno {year}.",
                    }
                )
            if average is not None:
                distribution_rows.append(
                    {
                        "anno": year,
                        "popolazione": "pensionati_inps",
                        "misura_distribuzione": "classe_eta",
                        "classe_importo": "Tutte",
                        "classe_importo_min": pd.NA,
                        "classe_importo_max": pd.NA,
                        "classe_eta": clean_label(label),
                        "sesso": sex,
                        "territorio": "Italia - INPS",
                        "indicatore_id": "reddito_pensionistico_medio_mensile_eta",
                        "fonte_id": source_id,
                        "valore": average,
                        "unita": "euro",
                        "note": f"Importo lordo medio mensile del reddito pensionistico per classe di eta e sesso; tabella 3.3, anno {year}.",
                    }
                )


def build_from_historical_appendices(
    rows: list[dict[str, object]],
    management_rows: list[dict[str, object]],
    profession_rows: list[dict[str, object]],
    distribution_rows: list[dict[str, object]],
    log: list[dict[str, object]],
) -> None:
    for item in APPENDICI_STORICHE:
        year = int(item["anno"])
        source_id = str(item["fonte_id"])
        xl = read_historical_appendix(item)

        sheet31 = pd.read_excel(xl, sheet_name="3.1", header=None)
        current_group = ""
        for _, record in sheet31.iterrows():
            values = record.tolist()
            label = str(values[1]).strip() if len(values) > 1 and pd.notna(values[1]) else ""
            if label in {"Pensionati complessivi", "Di cui pensionati INPS"}:
                current_group = label
            if label != "TOTALE" or not current_group:
                continue
            area = "Italia - complessivi" if current_group == "Pensionati complessivi" else "Italia - INPS"
            note = f"Appendice statistica Rapporto annuale INPS, tabella 3.1, anno {year}."
            add_annual(rows, year, "pensionati", "persone", source_id, values[2], "numero", area, note)
            add_annual(rows, year, "reddito_pensionistico_totale", "reddito_pensionistico", source_id, number(values[4]) * 1_000_000, "euro", area, note)
            add_annual(rows, year, "reddito_pensionistico_medio_mensile", "reddito_pensionistico", source_id, values[6], "euro", area, note)

        if year == 2023:
            sheet37 = pd.read_excel(xl, sheet_name="3.7", header=None)
            for _, record in sheet37.iterrows():
                values = record.tolist()
                gestione = str(values[1]).strip() if len(values) > 1 and pd.notna(values[1]) else ""
                if not gestione or gestione.startswith("Tabella") or gestione in {"Gestione", "Prestazioni previdenziali", "Prestazioni assistenziali"} or gestione.startswith("*"):
                    continue
                for data_year, count_idx, avg_idx in [(2022, 2, 5), (2023, 3, 6)]:
                    count = number(values[count_idx])
                    avg = number(values[avg_idx])
                    if count is None:
                        continue
                    if gestione == "TOTALE":
                        add_annual(rows, data_year, "pensioni_vigenti", "stock_amministrativo", source_id, count, "numero", "Italia - INPS", "Prestazioni INPS vigenti; tabella 3.7.")
                        if avg is not None:
                            add_annual(rows, data_year, "importo_medio_pensione_mensile", "distribuzione", source_id, avg, "euro", "Italia - INPS", "Importo lordo medio mensile per prestazione; tabella 3.7.")
                        continue
                    group = classify_professional_group(gestione)
                    management_rows.append({"anno": data_year, "gestione_id": normalize_id(gestione), "gestione_nome": clean_label(gestione), "gruppo_gestione": group, "indicatore_id": "pensioni_vigenti", "fonte_id": source_id, "valore": count, "unita": "numero", "note": "Prestazioni INPS vigenti per gestione; tabella 3.7."})
                    if avg is not None:
                        management_rows.append({"anno": data_year, "gestione_id": normalize_id(gestione), "gestione_nome": clean_label(gestione), "gruppo_gestione": group, "indicatore_id": "importo_medio_pensione", "fonte_id": source_id, "valore": avg, "unita": "euro", "note": "Importo lordo medio mensile per prestazione; tabella 3.7."})

        append_profession_snapshot(xl, year, source_id, profession_rows)
        append_income_distribution(xl, year, source_id, distribution_rows)
        append_age_distribution(xl, year, source_id, distribution_rows)
        log.append({"fonte": source_id, "tabella": "core_dashboard", "righe": len(rows) + len(management_rows) + len(profession_rows), "stato": "ok"})


def append_sheet_row(sheet: pd.DataFrame, label: str) -> list[object]:
    for _, row in sheet.iterrows():
        values = row.tolist()
        if values and str(values[1] if len(values) > 1 else values[0]).strip().lower() == label.lower():
            return values
    return []


def build_from_appendix(
    rows: list[dict[str, object]],
    management_rows: list[dict[str, object]],
    territorial_rows: list[dict[str, object]],
    distribution_rows: list[dict[str, object]],
    profession_rows: list[dict[str, object]],
    log: list[dict[str, object]],
) -> None:
    xl = read_appendix()

    sheet31 = pd.read_excel(xl, sheet_name="3.1", header=None)
    total_rows = []
    current_group = ""
    for _, record in sheet31.iterrows():
        values = record.tolist()
        label = str(values[1]).strip() if len(values) > 1 and pd.notna(values[1]) else ""
        if label in {"Pensionati complessivi", "Di cui pensionati INPS"}:
            current_group = label
        if label == "TOTALE" and current_group:
            total_rows.append((current_group, values))
    for group, values in total_rows:
        area = "Italia - complessivi" if group == "Pensionati complessivi" else "Italia - INPS"
        fonte_note = "Appendice statistica XXV Rapporto annuale INPS, tabella 3.1, dati provvisori 2025."
        add_annual(rows, 2025, "pensionati", "persone", "inps_appendice_xxv", values[2], "numero", area, fonte_note)
        add_annual(rows, 2025, "reddito_pensionistico_totale", "reddito_pensionistico", "inps_appendice_xxv", number(values[4]) * 1_000_000, "euro", area, fonte_note)
        add_annual(rows, 2025, "reddito_pensionistico_medio_mensile", "reddito_pensionistico", "inps_appendice_xxv", values[6], "euro", area, fonte_note)

    sheet37 = pd.read_excel(xl, sheet_name="3.7", header=None)
    for _, record in sheet37.iterrows():
        values = record.tolist()
        gestione = str(values[1]).strip() if len(values) > 1 and pd.notna(values[1]) else ""
        if not gestione or gestione.startswith("Tabella") or gestione in {"Gestione", "TOTALE", "Prestazioni previdenziali", "Prestazioni assistenziali"} or gestione.startswith("*"):
            continue
        for year, count_idx, avg_idx in [(2024, 2, 5), (2025, 3, 6)]:
            count = number(values[count_idx])
            avg = number(values[avg_idx])
            if count is None:
                continue
            group = classify_professional_group(gestione)
            management_rows.append(
                {
                    "anno": year,
                    "gestione_id": normalize_id(gestione),
                    "gestione_nome": clean_label(gestione),
                    "gruppo_gestione": group,
                    "indicatore_id": "pensioni_vigenti",
                    "fonte_id": "inps_appendice_xxv",
                    "valore": count,
                    "unita": "numero",
                    "note": "Prestazioni INPS vigenti per gestione; appendice statistica XXV Rapporto annuale, tabella 3.7.",
                }
            )
            if avg is not None:
                management_rows.append(
                    {
                        "anno": year,
                        "gestione_id": normalize_id(gestione),
                        "gestione_nome": clean_label(gestione),
                        "gruppo_gestione": group,
                        "indicatore_id": "importo_medio_pensione",
                        "fonte_id": "inps_appendice_xxv",
                        "valore": avg,
                        "unita": "euro",
                        "note": "Importo lordo medio mensile per prestazione; appendice statistica XXV Rapporto annuale, tabella 3.7.",
                    }
                )
            if gestione == "TOTALE":
                add_annual(rows, year, "pensioni_vigenti", "stock_amministrativo", "inps_appendice_xxv", count, "numero", "Italia - INPS", "Prestazioni INPS vigenti; tabella 3.7.")

    total37 = sheet37[sheet37.iloc[:, 1].astype(str).str.strip().eq("TOTALE")]
    if not total37.empty:
        values = total37.iloc[0].tolist()
        for year, count_idx, avg_idx in [(2024, 2, 5), (2025, 3, 6)]:
            count = number(values[count_idx])
            avg = number(values[avg_idx])
            if count is not None:
                add_annual(rows, year, "pensioni_vigenti", "stock_amministrativo", "inps_appendice_xxv", count, "numero", "Italia - INPS", "Prestazioni INPS vigenti; tabella 3.7.")
                if avg is not None:
                    add_annual(rows, year, "importo_medio_pensione_mensile", "distribuzione", "inps_appendice_xxv", avg, "euro", "Italia - INPS", "Importo lordo medio mensile per prestazione; tabella 3.7.")

    sheet32 = pd.read_excel(xl, sheet_name="3.2", header=None)
    for _, record in sheet32.iterrows():
        values = record.tolist()
        area = str(values[1]).strip() if len(values) > 1 and pd.notna(values[1]) else ""
        if area not in {"Nord", "Centro", "Mezzogiorno", "Estero", "TOTALE"}:
            continue
        territorial_rows.extend(
            [
                territorial(2025, "area", area, "pensionati", values[8], "numero", "inps_appendice_xxv", "Pensionati INPS maschi e femmine; tabella 3.2."),
                territorial(2025, "area", area, "reddito_pensionistico_medio_mensile", values[10], "euro", "inps_appendice_xxv", "Importo lordo medio mensile del reddito pensionistico; tabella 3.2."),
            ]
        )

    sheet36 = pd.read_excel(xl, sheet_name="3.6", header=None)
    for _, record in sheet36.iterrows():
        values = record.tolist()
        region = str(values[1]).strip() if len(values) > 1 and pd.notna(values[1]) else ""
        if not region or region.startswith("Tabella") or region.startswith("*") or region in {"Regione\nArea geeografica"}:
            continue
        if region in {"I", "II"}:
            continue
        gini = number(values[11] if len(values) > 11 else None)
        if gini is not None:
            level = "area" if region in {"Nord", "Centro", "Mezzogiorno", "Italia"} else "regione"
            territorial_rows.append(territorial(2025, level, region, "gini_reddito_pensionistico", gini, "percentuale", "inps_appendice_xxv", "Coefficiente di Gini del reddito pensionistico lordo annuo; tabella 3.6."))
        for index, decile in enumerate(["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"], start=2):
            value = number(values[index] if len(values) > index else None)
            if value is not None:
                level = "area" if region in {"Nord", "Centro", "Mezzogiorno", "Italia"} else "regione"
                territorial_rows.append(territorial(2025, level, region, f"decile_{decile}_reddito_pensionistico", value, "euro", "inps_appendice_xxv", "Decile del reddito pensionistico lordo annuo; tabella 3.6."))

    append_income_distribution(xl, 2025, "inps_appendice_xxv", distribution_rows)
    append_age_distribution(xl, 2025, "inps_appendice_xxv", distribution_rows)

    sheet39 = pd.read_excel(xl, sheet_name="3.9", header=None)
    for _, record in sheet39.iterrows():
        values = record.tolist()
        gestione = str(values[1]).strip() if len(values) > 1 and pd.notna(values[1]) else ""
        if not gestione or gestione.startswith("Tabella") or gestione in {"Gestione", "TOTALE"} or gestione.startswith("*") or gestione.startswith("di cui") or gestione.startswith("-"):
            continue
        profession_rows.append(
            {
                "anno": 2025,
                "fonte_id": "inps_appendice_xxv",
                "gestione_id": normalize_id(gestione),
                "gestione_nome": clean_label(gestione),
                "categoria_professionale": classify_professional_group(gestione),
                "criterio_classificazione": "gestione_previdenziale",
                "tipo_pensione": "previdenziale",
                "sesso": "Totale",
                "classe_eta": "Tutte",
                "territorio": "Italia",
                "indicatore_id": "prestazioni_per_categoria_professionale",
                "pensionati": pd.NA,
                "prestazioni": number(values[8] if len(values) > 8 else None),
                "importo_complessivo": pd.NA,
                "importo_medio_annuo": pd.NA,
                "importo_medio_mensile": number(values[10] if len(values) > 10 else None),
                "unita": "numero",
                "duplicazione_teste": "prestazioni_non_persone",
                "note": "Prestazioni previdenziali INPS per gestione; tabella 3.9. La classificazione professionale e' ricostruita dalla gestione.",
            }
        )

    log.append({"fonte": "inps_appendice_xxv", "tabella": "core_dashboard", "righe": len(rows) + len(management_rows) + len(territorial_rows) + len(distribution_rows), "stato": "ok"})


def build_pdf_pension_distribution(distribution_rows: list[dict[str, object]], log: list[dict[str, object]]) -> None:
    path = RAW_DATA_DIR / "inps_casellario" / "casellario_2024.pdf"
    request_bytes(CASELLARIO_2024_PDF_URL, path)
    try:
        import fitz
    except ImportError:
        log.append({"fonte": "inps_casellario_2024", "tabella": "tabella_distribuzione_pensionati", "righe": 0, "stato": "pymupdf_non_installato"})
        return

    doc = fitz.open(path)
    table_rows: list[list[object]] = []
    for page_index in range(doc.page_count):
        page = doc.load_page(page_index)
        for table in page.find_tables().tables:
            extracted = table.extract()
            if extracted and extracted[0] and "CLASSE DI" in str(extracted[0][0]) and "% sui" in " ".join(str(x) for x in extracted[0]):
                table_rows = extracted[1:]
                break
        if table_rows:
            break
    for row in table_rows:
        if not row or str(row[0]).strip().lower() == "totale":
            continue
        label = clean_label(row[0])
        if label.startswith("5.000"):
            label = "5.000,00 e più"
        min_value, max_value = class_bounds(label)
        count = number(row[1] if len(row) > 1 else None)
        amount = number(row[3] if len(row) > 3 else None)
        if count is not None:
            distribution_rows.append(distribution(2024, "pensioni", "importo_pensione_mensile", label, min_value, max_value, "Totale", "Italia", "pensioni_per_classe_importo", count, "numero", "inps_casellario_2024", "Singole prestazioni pensionistiche per classe di importo mensile; report Casellario 2024, Tavola 6."))
        if amount is not None:
            distribution_rows.append(distribution(2024, "pensioni", "importo_pensione_mensile", label, min_value, max_value, "Totale", "Italia", "spesa_per_classe_importo", amount * 1_000_000, "euro", "inps_casellario_2024", "Importo complessivo annuo della classe; report Casellario 2024, fonte in milioni."))
            if count:
                distribution_rows.append(distribution(2024, "pensioni", "importo_pensione_mensile", label, min_value, max_value, "Totale", "Italia", "importo_medio_pensione_mensile_classe", amount * 1_000_000 / count / 12, "euro", "elaborazione_repo", "Importo annuo della classe diviso per numero di prestazioni e per 12 mesi."))
    log.append({"fonte": "inps_casellario_2024", "tabella": "tabella_distribuzione_pensionati", "righe": len(table_rows), "stato": "ok" if table_rows else "tabella_non_trovata"})


def build_historical_distribution_from_open_data(distribution_rows: list[dict[str, object]], log: list[dict[str, object]]) -> None:
    pensioners = read_open_csv("pensionati_regioni_classi_importo_storico")
    pensioners["Numero pensionati"] = pensioners["Numero pensionati"].map(number)
    added = 0
    grouped_pensioners = pensioners.groupby(["Anno", "Classe importo"], dropna=True)["Numero pensionati"].sum()
    for (year, label), count in grouped_pensioners.items():
        min_value, max_value = class_bounds(label)
        distribution_rows.append(
            distribution(
                int(year),
                "pensionati_inps",
                "reddito_pensionistico_mensile_complessivo",
                label,
                min_value,
                max_value,
                "Totale",
                "Italia",
                "pensionati_per_classe_reddito_pensionistico",
                count,
                "numero",
                "inps_open_data",
                "Pensionati del sistema pensionistico italiano per regione e classe di importo; valori aggregati a Italia dal pacchetto Open Data INPS 1988.",
            )
        )
        added += 1

    pensions = read_open_csv("pensioni_classi_importo_storico")
    pensions["Importo medio mensile"] = pensions["Importo medio mensile"].map(number)
    pensions["Importo complessivo annuo"] = pensions["Importo complessivo annuo"].map(number)
    derived_rows: list[dict[str, object]] = []
    for _, record in pensions.iterrows():
        average = number(record["Importo medio mensile"])
        amount = number(record["Importo complessivo annuo"])
        if average is None or average <= 0 or amount is None:
            continue
        annual_amount = amount * 1_000_000
        derived_rows.append(
            {
                "anno": int(record["Anno"]),
                "classe": str(record["Classe di importo"]),
                "spesa": annual_amount,
                "pensioni": annual_amount / average / 12,
            }
        )
    if derived_rows:
        frame_rows = pd.DataFrame(derived_rows)
        grouped = frame_rows.groupby(["anno", "classe"], dropna=True).sum(numeric_only=True).reset_index()
        for _, record in grouped.iterrows():
            min_value, max_value = class_bounds(record["classe"])
            count = number(record["pensioni"])
            amount = number(record["spesa"])
            distribution_rows.append(distribution(int(record["anno"]), "pensioni", "importo_pensione_mensile", record["classe"], min_value, max_value, "Totale", "Italia", "pensioni_per_classe_importo", count, "numero", "elaborazione_repo", "Numero di pensioni ricavato da importo complessivo annuo e importo medio mensile della classe; pacchetto Open Data INPS 1650."))
            distribution_rows.append(distribution(int(record["anno"]), "pensioni", "importo_pensione_mensile", record["classe"], min_value, max_value, "Totale", "Italia", "spesa_per_classe_importo", amount, "euro", "inps_open_data", "Importo complessivo annuo delle pensioni vigenti per classe di importo; pacchetto Open Data INPS 1650."))
            if count:
                distribution_rows.append(distribution(int(record["anno"]), "pensioni", "importo_pensione_mensile", record["classe"], min_value, max_value, "Totale", "Italia", "importo_medio_pensione_mensile_classe", amount / count / 12, "euro", "elaborazione_repo", "Importo annuo della classe diviso per numero di prestazioni e per 12 mesi."))
                added += 3
    log.append({"fonte": "inps_open_data", "tabella": "tabella_distribuzione_pensionati", "righe": added, "stato": "ok"})


def build_region_history(territorial_rows: list[dict[str, object]], log: list[dict[str, object]]) -> None:
    pensioners = read_open_csv("pensionati_regioni_storico")
    pensioners["Numero beneficiari"] = pensioners["Numero beneficiari"].map(number)
    pensioner_totals = pensioners.groupby(["Anno", "Regione"], dropna=True)["Numero beneficiari"].sum()

    spending = read_open_csv("spesa_regioni_storico")
    spending["Importo complessivo annuo"] = spending["Importo complessivo annuo"].map(number)
    spending_totals = spending.groupby(["Anno", "Regione"], dropna=True)["Importo complessivo annuo"].sum() * 1_000_000

    for (anno, regione), pensioner_count in pensioner_totals.items():
        year = int(anno)
        name = str(regione)
        territorial_rows.append(territorial(year, "regione", name, "pensionati", pensioner_count, "numero", "inps_open_data", "Beneficiari del sistema pensionistico italiano per regione; dataset ID-5297."))
        total_spending = spending_totals.get((anno, regione))
        if total_spending is None or pd.isna(total_spending):
            continue
        territorial_rows.append(territorial(year, "regione", name, "spesa_pensionistica_regionale", total_spending, "euro", "inps_open_data", "Importo complessivo annuo delle pensioni per regione; dataset ID-5291."))
        if pensioner_count:
            territorial_rows.append(territorial(year, "regione", name, "reddito_pensionistico_medio_mensile", total_spending / pensioner_count / 12, "euro", "elaborazione_repo", "Spesa pensionistica regionale divisa per pensionati e per 12 mesi; dataset INPS ID-5291 e ID-5297."))
    log.append({"fonte": "inps_open_data", "tabella": "tabella_territoriale", "righe": len(pensioners) + len(spending), "stato": "ok"})


def build_region_bridge_2017_2019(territorial_rows: list[dict[str, object]], log: list[dict[str, object]]) -> None:
    """Colma i pensionati regionali 2017-2019 dalla tavola 0.2.1 INPS."""
    try:
        import fitz
    except ImportError:
        return
    path = RAW_DATA_DIR / "inps_sociale" / "rendiconto_sociale_2017_2021.pdf"
    document = fitz.open(stream=request_bytes(INPS_SOCIAL_REPORT_2017_2021_URL, path), filetype="pdf")
    pages = [
        page.get_text()
        for page in document
        if "Abruzzo" in page.get_text() and "Veneto" in page.get_text() and "ITALIA" in page.get_text() and "Tavola 0.2.1" in page.get_text()
    ]
    document.close()
    regions = ["Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia Romagna", "Friuli Venezia Giulia", "Lazio", "Liguria", "Lombardia", "Marche", "Molise", "Piemonte", "Puglia", "Sardegna", "Sicilia", "Toscana", "Trentino Alto Adige", "Umbria", "Valle d'Aosta", "Veneto"]
    added = 0
    for page_text, years in zip(pages[-2:], [(2017, 2018), (2019, 2020)]):
        values = [int(value.replace(".", "")) for value in re.findall(r"\b\d{1,3}\.\d{3}\b", page_text)]
        values = values[: len(regions) * 6]
        if len(values) != len(regions) * 6:
            continue
        for index, region in enumerate(regions):
            row = values[index * 6:(index + 1) * 6]
            for year, value in [(years[0], row[2]), (years[1], row[5])]:
                if year <= 2019:
                    territorial_rows.append(territorial(year, "regione", region, "pensionati", value, "numero", "inps_rendiconto_sociale", "Pensionati per regione al 31 dicembre; Rendiconto sociale INPS 2017-2021, tavola 0.2.1."))
                    added += 1
    log.append({"fonte": "inps_rendiconto_sociale", "tabella": "tabella_territoriale", "righe": added, "stato": "ok" if added else "tabella_non_trovata"})


def build_eurostat_data(
    territorial_rows: list[dict[str, object]],
    comparison_rows: list[dict[str, object]],
    log: list[dict[str, object]],
) -> None:
    cache = RAW_DATA_DIR / "eurostat"
    pension_gdp = jsonstat_geo_time(request_json(EUROSTAT_PENSION_GDP_URL, cache / "spr_exp_pens_pc_gdp.json"))
    for (country, year), value in pension_gdp.items():
        if country not in EU_COUNTRIES:
            continue
        comparison_rows.append(
            {
                "anno": year,
                "paese": EU_COUNTRIES[country],
                "indicatore_id": "spesa_pensionistica_pil_esspros",
                "definizione": "Spesa per prestazioni pensionistiche ESSPROS in percentuale del PIL",
                "fonte_id": "eurostat_esspros",
                "valore": value,
                "unita": "percentuale_pil",
                "note": "Eurostat spr_exp_pens: tutte le funzioni pensionistiche e tutti i regimi; perimetro armonizzato europeo.",
            }
        )

    population = jsonstat_geo_time(request_json(EUROSTAT_POPULATION_URL, cache / "demo_r_pjanaggr3_total.json"))
    gdp = jsonstat_geo_time(request_json(EUROSTAT_REGIONAL_GDP_URL, cache / "nama_10r_2gdp_mio_eur.json"))
    index = {
        (int(row["anno"]), region_name_for_eurostat(str(row["nome_territorio"])), str(row["indicatore_id"])): number(row["valore"])
        for row in territorial_rows
        if row.get("livello_territoriale") == "regione"
    }
    for (year, region, indicator), value in list(index.items()):
        if indicator != "pensionati" or value is None or region not in REGION_NUTS2:
            continue
        codes = REGION_NUTS2[region]
        region_population = sum(population.get((code, year), 0) for code in codes)
        region_gdp = sum(gdp.get((code, year), 0) for code in codes) * 1_000_000
        spending = index.get((year, region, "spesa_pensionistica_regionale"))
        if region_population:
            territorial_rows.append(territorial(year, "regione", region, "pensionati_percentuale_popolazione", value / region_population * 100, "percentuale", "inps_eurostat", "Pensionati INPS divisi per popolazione residente Eurostat al 1 gennaio dello stesso anno."))
        if region_gdp and spending:
            territorial_rows.append(territorial(year, "regione", region, "spesa_pensionistica_percentuale_pil", spending / region_gdp * 100, "percentuale_pil", "inps_eurostat", "Spesa pensionistica regionale INPS divisa per PIL regionale Eurostat dello stesso anno."))
    log.append({"fonte": "eurostat", "tabella": "tabella_confronto_europeo", "righe": len(comparison_rows), "stato": "ok"})


def build_eurostat_replacement_rates(comparison_rows: list[dict[str, object]], log: list[dict[str, object]]) -> None:
    """Aggiunge il tasso di sostituzione aggregato annuale Eurostat."""
    cache = RAW_DATA_DIR / "eurostat"
    payload = request_json(EUROSTAT_AGGREGATE_REPLACEMENT_URL, cache / "ilc_pnp3_aggregate_replacement.json")
    sex_labels = {"T": "Totale", "M": "Maschi", "F": "Femmine"}
    added = 0
    for record in jsonstat_records(payload):
        country = str(record.get("geo"))
        sex = str(record.get("sex"))
        if country not in EU_COUNTRIES or sex not in sex_labels:
            continue
        value = number(record.get("value"))
        year = int(record["time"])
        if value is None:
            continue
        comparison_rows.append(
            {
                "anno": year,
                "paese": EU_COUNTRIES[country],
                "indicatore_id": "tasso_sostituzione_aggregato_eurostat",
                "definizione": f"aggregato|{sex}",
                "fonte_id": "eurostat_ilc_pnp3",
                "valore": value * 100 if value <= 1 else value,
                "unita": "percentuale",
                "note": "Eurostat ilc_pnp3: rapporto aggregato tra pensione individuale mediana lorda delle persone 65-74 e reddito individuale mediano lordo da lavoro delle persone 50-59, esclusi altri benefici sociali.",
            }
        )
        added += 1
    log.append({"fonte": "eurostat_ilc_pnp3", "tabella": "tabella_confronto_europeo", "righe": added, "stato": "ok" if added else "dato_non_disponibile"})


def build_pension_income_gdp_ratio(
    annual_rows: list[dict[str, object]],
    comparison_rows: list[dict[str, object]],
    log: list[dict[str, object]],
) -> None:
    """Calcola reddito pensionistico lordo / PIL nominale usando lo stesso anno."""
    cache = RAW_DATA_DIR / "eurostat"
    gdp = jsonstat_geo_time(request_json(EUROSTAT_NATIONAL_GDP_URL, cache / "nama_10_gdp_it_cp_meur.json"))
    income_rows = [
        row for row in annual_rows
        if row.get("indicatore_id") == "reddito_pensionistico_totale"
        and row.get("area") in {"Italia - complessivi", "Italia - INPS"}
    ]
    added = 0
    for row in income_rows:
        year = int(row["anno"])
        gdp_million = gdp.get(("IT", year))
        income = number(row.get("valore"))
        if not gdp_million or income is None:
            continue
        is_total = row.get("area") == "Italia - complessivi"
        comparison_rows.append(
            {
                "anno": year,
                "paese": "Italia",
                "indicatore_id": "reddito_pensionistico_pil_complessivo" if is_total else "reddito_pensionistico_pil_inps",
                "definizione": "Reddito pensionistico lordo annuo diviso per PIL nominale dello stesso anno",
                "fonte_id": "inps_eurostat",
                "valore": income / (gdp_million * 1_000_000) * 100,
                "unita": "percentuale_pil",
                "note": (
                    "Reddito pensionistico lordo complessivo della Tavola 3.1 diviso per PIL nominale Eurostat nama_10_gdp."
                    if is_total else
                    "Reddito pensionistico lordo del sottoinsieme pensionati INPS della Tavola 3.1 diviso per PIL nominale Eurostat nama_10_gdp."
                ),
            }
        )
        added += 1
    log.append({"fonte": "inps_eurostat", "tabella": "tabella_confronto_europeo", "righe": added, "stato": "ok" if added else "pil_non_disponibile"})


def insured_workers_from_reports() -> dict[int, dict[str, float]]:
    try:
        import fitz
    except ImportError:
        return {}

    result: dict[int, dict[str, float]] = {}
    cache = RAW_DATA_DIR / "inps_rapporti_assicurati"
    for report in INPS_INSURED_REPORTS:
        path = cache / f"rapporto_{report['name']}.pdf"
        request_bytes(str(report["url"]), path)
        document = fitz.open(path)
        page_text = next((page.get_text() for page in document if str(report["marker"]) in page.get_text()), "")
        document.close()
        if not page_text:
            continue
        tail = page_text.split(str(report["total_label"]), 1)[-1]
        values = re.findall(r"\b\d{1,3}\.\d{3}\b", tail)[: len(report["years"])]
        if len(values) != len(report["years"]):
            continue
        for year, value in zip(report["years"], values):
            result.setdefault(int(year), {})["assicurati"] = float(value.replace(".", "")) * 1_000
        week_values = re.findall(r"\b\d{1,2},\d\b", tail)
        skip = int(report.get("skip_week_values", 0))
        week_values = week_values[skip: skip + len(report.get("week_years", []))]
        for year, value in zip(report.get("week_years", []), week_values):
            weeks = number(value)
            if weeks is not None:
                result.setdefault(int(year), {})["settimane_medie"] = weeks
    return result


def average_insured_from_social_report() -> dict[int, float]:
    try:
        import fitz
    except ImportError:
        return {}
    path = RAW_DATA_DIR / "inps_sociale" / "rendiconto_sociale_2017_2021.pdf"
    document = fitz.open(stream=request_bytes(INPS_SOCIAL_REPORT_2017_2021_URL, path), filetype="pdf")
    page_text = next((page.get_text() for page in document if "Tavola 0.1 - Numero medio annuo degli assicurati" in page.get_text()), "")
    document.close()
    if not page_text:
        return {}
    tail = page_text.split("TOTALE", 1)[-1]
    values = re.findall(r"\b\d{1,3}(?:\.\d{3})+\b", tail)[:4]
    if len(values) != 4:
        return {}
    return {year: float(value.replace(".", "")) for year, value in zip([2017, 2018, 2019, 2020], values)}


def build_workers_and_pensioners(
    annual_rows: list[dict[str, object]],
    demography_rows: list[dict[str, object]],
    log: list[dict[str, object]],
) -> None:
    cache = RAW_DATA_DIR / "eurostat"
    employment = jsonstat_geo_time(request_json(EUROSTAT_EMPLOYMENT_URL, cache / "lfsi_emp_a_it_y15_64.json"))
    annual_index = {
        (int(row["anno"]), str(row["indicatore_id"]), str(row["area"])): number(row["valore"])
        for row in annual_rows
    }
    for (geo, year), value_thousands in sorted(employment.items()):
        if geo != "IT":
            continue
        workers = value_thousands * 1_000
        pensioners = annual_index.get((year, "pensionati", "Italia - complessivi"))
        contributions = annual_index.get((year, "entrate_contributive_inps", "Italia"))
        spending = annual_index.get((year, "reddito_pensionistico_totale", "Italia - INPS"))
        common = {"anno": year, "area": "Italia", "classe_eta": "15-64", "sesso": "Totale", "scenario": "osservato"}
        demography_rows.append({**common, "indicatore_id": "occupati", "fonte_id": "eurostat_lfs", "valore": workers, "unita": "numero", "note": "Occupati 15-64 anni secondo EU-LFS. E' un perimetro demografico, non il numero di contribuenti INPS unici."})
        if pensioners:
            demography_rows.append({**common, "indicatore_id": "occupati_per_pensionato", "fonte_id": "eurostat_inps", "valore": workers / pensioners, "unita": "rapporto", "note": "Occupati 15-64 Eurostat divisi per pensionati complessivi INPS."})
            if contributions:
                demography_rows.append({**common, "indicatore_id": "contributi_inps_per_pensionato", "fonte_id": "inps_rendiconti", "valore": contributions / pensioners, "unita": "euro", "note": "Entrate contributive INPS divise per pensionati; misura finanziaria, non contributo medio individuale."})
            if spending:
                demography_rows.append({**common, "indicatore_id": "spesa_lorda_per_pensionato", "fonte_id": "inps_rapporti_annuali", "valore": spending / pensioners, "unita": "euro", "note": "Reddito pensionistico lordo INPS diviso per pensionati INPS."})
            if contributions and spending:
                demography_rows.append({**common, "indicatore_id": "copertura_spesa_contributi", "fonte_id": "elaborazione_repo", "valore": contributions / spending * 100, "unita": "percentuale", "note": "Entrate contributive INPS in rapporto al reddito pensionistico lordo INPS. Il rapporto resta aggregato e non attribuisce le entrate alle singole prestazioni."})
    for year, insured in sorted(insured_workers_from_reports().items()):
        common = {"anno": year, "area": "Italia", "classe_eta": "Tutte", "sesso": "Totale", "scenario": "osservato"}
        count = insured.get("assicurati")
        weeks = insured.get("settimane_medie")
        if count:
            demography_rows.append({**common, "indicatore_id": "assicurati_inps", "fonte_id": "inps_assicurati_rapporti", "valore": count, "unita": "numero", "note": "Lavoratori con almeno un contributo o una giornata retribuita nell'anno, al netto delle sovrapposizioni tra gestioni INPS."})
        equivalent = count * weeks / 52 if count and weeks else None
        if equivalent:
            demography_rows.append({**common, "indicatore_id": "assicurati_inps_ponderati_settimane", "fonte_id": "inps_assicurati_rapporti", "valore": equivalent, "unita": "numero", "note": "Assicurati INPS ponderati per il numero medio di settimane lavorate nell'anno; misura derivata per avvicinare l'intensita' contributiva effettiva."})
        pensioners = annual_index.get((year, "pensionati", "Italia - complessivi"))
        if pensioners and equivalent:
            demography_rows.append({**common, "indicatore_id": "assicurati_inps_per_pensionato", "fonte_id": "inps_assicurati_rapporti", "valore": equivalent / pensioners, "unita": "rapporto", "note": "Assicurati INPS ponderati per settimane lavorate divisi per pensionati complessivi."})
    for year, insured_average in sorted(average_insured_from_social_report().items()):
        common = {"anno": year, "area": "Italia", "classe_eta": "Tutte", "sesso": "Totale", "scenario": "osservato"}
        demography_rows.append({**common, "indicatore_id": "assicurati_medi_annui_inps", "fonte_id": "inps_rendiconto_sociale", "valore": insured_average, "unita": "numero", "note": "Numero medio annuo degli assicurati; Rendiconto sociale INPS 2017-2021, tavola 0.1."})
        pensioners = annual_index.get((year, "pensionati", "Italia - complessivi"))
        if pensioners:
            demography_rows.append({**common, "indicatore_id": "assicurati_medi_annui_per_pensionato", "fonte_id": "inps_rendiconto_sociale", "valore": insured_average / pensioners, "unita": "rapporto", "note": "Numero medio annuo degli assicurati diviso per pensionati complessivi."})
    log.append({"fonte": "eurostat_lfs", "tabella": "tabella_demografia_lavoro", "righe": len(demography_rows), "stato": "ok"})


def region_name_for_eurostat(name: str) -> str:
    value = clean_label(name)
    if value.lower().startswith("valle d'aosta"):
        return "Valle d'Aosta"
    if value.lower().startswith("trentino"):
        return "Trentino-Alto Adige"
    if value.lower().startswith("friuli"):
        return "Friuli Venezia Giulia"
    if value.lower().startswith("emilia"):
        return "Emilia-Romagna"
    return value


def territorial(anno: int, livello: str, nome: str, indicatore: str, valore: object, unita: str, fonte: str, note: str) -> dict[str, object]:
    return {
        "anno": anno,
        "livello_territoriale": livello,
        "codice_territorio": normalize_id(nome),
        "nome_territorio": clean_label(nome),
        "indicatore_id": indicatore,
        "fonte_id": fonte,
        "valore": number(valore),
        "unita": unita,
        "note": note,
    }


def distribution(
    anno: int,
    popolazione: str,
    misura: str,
    classe: str,
    minimum: float | None,
    maximum: float | None,
    sesso: str,
    territorio: str,
    indicatore: str,
    valore: object,
    unita: str,
    fonte: str,
    note: str,
) -> dict[str, object]:
    return {
        "anno": anno,
        "popolazione": popolazione,
        "misura_distribuzione": misura,
        "classe_importo": clean_label(classe),
        "classe_importo_min": minimum,
        "classe_importo_max": maximum,
        "classe_eta": "Tutte",
        "sesso": sesso,
        "territorio": territorio,
        "indicatore_id": indicatore,
        "fonte_id": fonte,
        "valore": number(valore),
        "unita": unita,
        "note": note,
    }


def clean_label(value: object) -> str:
    return " ".join(str(value or "").replace("\n", " ").split())


def normalize_id(value: object) -> str:
    text = clean_label(value).lower()
    replacements = {
        "à": "a",
        "è": "e",
        "é": "e",
        "ì": "i",
        "ò": "o",
        "ù": "u",
        "'": "",
        "/": "_",
        "-": "_",
        "(": "",
        ")": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return "_".join(part for part in "".join(ch if ch.isalnum() or ch == "_" else " " for ch in text).split() if part)


def classify_professional_group(gestione: object) -> str:
    text = clean_label(gestione).lower()
    normalized = normalize_id(text).replace("_", " ")
    if "dipendenti pubblici" in text:
        return "ex_dipendenti_pubblici"
    if "lavoratori dipendenti" in text:
        return "ex_dipendenti_privati"
    if "lavoratori autonomi" in text:
        return "ex_partite_iva_parasubordinati"
    if "artigiani" in text or "commercianti" in text:
        return "ex_imprenditori_autonomi"
    if "coltivatori" in text or "mezzadri" in text:
        return "ex_autonomi_agricoli"
    if "gestione separata" in text or "parasubordinati" in text:
        return "ex_partite_iva_parasubordinati"
    if "assistenz" in normalized or "invalidita civile" in normalized or "sociali" in normalized:
        return "prestazioni_assistenziali"
    return "altre_gestioni"


def drop_invalid(rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    result = []
    for row in rows:
        value = row.get("valore")
        if value is pd.NA or value is None:
            continue
        if isinstance(value, float) and pd.isna(value):
            continue
        result.append(row)
    return result


def interpolate_management_gap(management_rows: list[dict[str, object]], log: list[dict[str, object]]) -> None:
    """Colma il tratto 2018-2021 delle categorie aggregate quando manca la tavola omogenea."""
    counts: dict[tuple[int, str], float] = {}
    weighted_amounts: dict[tuple[int, str], float] = {}
    weighted_counts: dict[tuple[int, str], float] = {}
    count_by_management = {
        (int(row["anno"]), str(row["gestione_id"])): number(row["valore"])
        for row in management_rows
        if row.get("indicatore_id") == "pensioni_vigenti"
    }
    for row in management_rows:
        year = int(row["anno"])
        group = str(row.get("gruppo_gestione") or "altre_gestioni")
        value = number(row.get("valore"))
        if value is None:
            continue
        key = (year, group)
        if row.get("indicatore_id") == "pensioni_vigenti":
            counts[key] = counts.get(key, 0) + value
        elif row.get("indicatore_id") == "importo_medio_pensione":
            weight = count_by_management.get((year, str(row["gestione_id"])))
            if weight:
                weighted_amounts[key] = weighted_amounts.get(key, 0) + value * weight
                weighted_counts[key] = weighted_counts.get(key, 0) + weight

    added = 0
    groups = sorted({group for _, group in counts} | {group for _, group in weighted_amounts})
    for group in groups:
        start_count = counts.get((2017, group))
        end_count = counts.get((2022, group))
        if start_count is not None and end_count is not None:
            for year in range(2018, 2022):
                if counts.get((year, group)) is not None:
                    continue
                share = (year - 2017) / 5
                value = start_count + (end_count - start_count) * share
                management_rows.append(
                    {
                        "anno": year,
                        "gestione_id": f"interpolazione_{group}",
                        "gestione_nome": f"{label_interpolated_group(group)} (interpolazione)",
                        "gruppo_gestione": group,
                        "indicatore_id": "pensioni_vigenti",
                        "fonte_id": "elaborazione_repo",
                        "valore": value,
                        "unita": "numero",
                        "note": "Interpolazione lineare tra l'ultimo dato Open Data 2017 e la prima appendice omogenea 2022; usata solo per evitare il buco 2018-2021 nella vista aggregata per categoria.",
                    }
                )
                added += 1
        start_avg = weighted_amounts.get((2017, group))
        start_weight = weighted_counts.get((2017, group))
        end_avg = weighted_amounts.get((2022, group))
        end_weight = weighted_counts.get((2022, group))
        if start_avg is not None and start_weight and end_avg is not None and end_weight:
            start_value = start_avg / start_weight
            end_value = end_avg / end_weight
            for year in range(2018, 2022):
                if weighted_amounts.get((year, group)) is not None and weighted_counts.get((year, group)):
                    continue
                share = (year - 2017) / 5
                value = start_value + (end_value - start_value) * share
                management_rows.append(
                    {
                        "anno": year,
                        "gestione_id": f"interpolazione_{group}",
                        "gestione_nome": f"{label_interpolated_group(group)} (interpolazione)",
                        "gruppo_gestione": group,
                        "indicatore_id": "importo_medio_pensione",
                        "fonte_id": "elaborazione_repo",
                        "valore": value,
                        "unita": "euro",
                        "note": "Interpolazione lineare tra l'ultimo dato Open Data 2017 e la prima appendice omogenea 2022; usata solo per evitare il buco 2018-2021 nella vista aggregata per categoria.",
                    }
                )
                added += 1
    log.append({"fonte": "elaborazione_repo", "tabella": "tabella_gestioni", "righe": added, "stato": "interpolazione_2018_2021"})


def label_interpolated_group(group: str) -> str:
    labels = {
        "altre_gestioni": "Altre gestioni",
        "ex_dipendenti_privati": "Ex dipendenti privati",
        "ex_dipendenti_pubblici": "Ex dipendenti pubblici",
        "ex_imprenditori_autonomi": "Artigiani e commercianti",
        "ex_autonomi_agricoli": "Autonomi agricoli",
        "ex_partite_iva_parasubordinati": "Autonomi e parasubordinati",
        "prestazioni_assistenziali": "Prestazioni assistenziali",
    }
    return labels.get(group, group.replace("_", " "))


def build_dashboard_core_data(log_path: str | Path = LOG_PATHS["dashboard_core"]) -> pd.DataFrame:
    prepare_directories()
    annual_rows: list[dict[str, object]] = []
    transfer_rows: list[dict[str, object]] = []
    management_rows: list[dict[str, object]] = []
    territorial_rows: list[dict[str, object]] = []
    comparison_rows: list[dict[str, object]] = []
    demography_rows: list[dict[str, object]] = []
    distribution_rows: list[dict[str, object]] = []
    profession_rows: list[dict[str, object]] = []
    log_rows: list[dict[str, object]] = []

    build_annual_from_open_data(annual_rows, log_rows)
    build_management_history_from_open_data(management_rows, log_rows)
    build_public_employee_history_from_open_data(management_rows, log_rows)
    build_contributions(annual_rows, log_rows)
    build_consistent_annual_series(annual_rows, log_rows)
    build_state_transfers(annual_rows, transfer_rows, log_rows)
    build_state_transfer_components(transfer_rows, log_rows)
    build_region_history(territorial_rows, log_rows)
    build_region_bridge_2017_2019(territorial_rows, log_rows)
    build_current_regions_from_api(territorial_rows, log_rows)
    build_eurostat_data(territorial_rows, comparison_rows, log_rows)
    build_eurostat_replacement_rates(comparison_rows, log_rows)
    build_oecd_pension_spending(comparison_rows, log_rows)
    build_replacement_rate_projections(comparison_rows, log_rows)
    build_from_historical_appendices(annual_rows, management_rows, profession_rows, distribution_rows, log_rows)
    build_from_appendix(annual_rows, management_rows, territorial_rows, distribution_rows, profession_rows, log_rows)
    interpolate_management_gap(management_rows, log_rows)
    build_pension_income_gdp_ratio(annual_rows, comparison_rows, log_rows)
    build_workers_and_pensioners(annual_rows, demography_rows, log_rows)
    build_historical_distribution_from_open_data(distribution_rows, log_rows)
    build_pdf_pension_distribution(distribution_rows, log_rows)

    by_year_indicator_area = {}
    for row in annual_rows:
        by_year_indicator_area[(row["anno"], row["indicatore_id"], row["area"])] = row["valore"]
    for (anno, indicator, area), pension_count in list(by_year_indicator_area.items()):
        if indicator != "pensioni_vigenti":
            continue
        if (anno, "trattamenti_per_pensionato", area) in by_year_indicator_area:
            continue
        pensioners = by_year_indicator_area.get((anno, "pensionati", area))
        if pensioners:
            add_annual(annual_rows, int(anno), "trattamenti_per_pensionato", "derivato", "elaborazione_repo", float(pension_count) / float(pensioners), "rapporto", str(area), "Pensioni vigenti divise per pensionati nello stesso perimetro quando disponibile.")

    outputs = {
        "tabella_annuale_pensioni": frame("tabella_annuale_pensioni", annual_rows),
        "tabella_trasferimenti_inps": frame("tabella_trasferimenti_inps", transfer_rows),
        "tabella_gestioni": frame("tabella_gestioni", management_rows),
        "tabella_territoriale": frame("tabella_territoriale", drop_invalid(territorial_rows)),
        "tabella_confronto_europeo": frame("tabella_confronto_europeo", drop_invalid(comparison_rows)),
        "tabella_demografia_lavoro": frame("tabella_demografia_lavoro", drop_invalid(demography_rows)),
        "tabella_distribuzione_pensionati": frame("tabella_distribuzione_pensionati", drop_invalid(distribution_rows)),
        "pensionati_per_gestione_professione": frame("pensionati_per_gestione_professione", profession_rows),
    }
    for table_name, table in outputs.items():
        save_table(table, FINAL_TABLE_PATHS[table_name])
        log_rows.append({"fonte": "build_dashboard_core_data", "tabella": table_name, "righe": len(table), "stato": "scritto"})

    log = pd.DataFrame(log_rows)
    save_table(log, log_path)
    return log


if __name__ == "__main__":
    build_dashboard_core_data()
