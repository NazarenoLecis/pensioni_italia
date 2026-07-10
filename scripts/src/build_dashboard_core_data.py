from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
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
INPS_OBSERVATORY_API = "https://servizi2.inps.it/servizi/osservatoristatistici/api"

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

OPEN_DATA_URLS = {
    "pensioni_vigenti_storico": "http://www.inps.it/docallegati/Mig/OpenData/CSV/ID-5080.csv",
    "spesa_casellario_storico": "http://www.inps.it/docallegati/Mig/OpenData/CSV/ID-5296.csv",
    "pensionati_storico": "http://www.inps.it/docallegati/Mig/OpenData/CSV/ID-5300.csv",
    "pensionati_regioni_storico": "http://www.inps.it/docallegati/Mig/OpenData/CSV/ID-5297.csv",
    "spesa_regioni_storico": "http://www.inps.it/docallegati/Mig/OpenData/CSV/ID-5291.csv",
    "conto_economico_2013_2014": "http://www.inps.it/docallegati/Mig/OpenData/CSV/ID-2881.csv",
    "conto_economico_2015": "http://www.inps.it/docallegati/Mig/OpenData/CSV/ID-5373.csv",
    "conto_economico_2016": "http://www.inps.it/docallegati/Mig/OpenData/CSV/ID-5383.csv",
    "conto_economico_2017": "http://www.inps.it/docallegati/Mig/OpenData/CSV/ID-5393.csv",
    "conto_economico_2018": "http://www.inps.it/docallegati/Mig/OpenData/CSV/ID-5569.csv",
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


def read_open_csv(name: str) -> pd.DataFrame:
    url = OPEN_DATA_URLS[name]
    raw_path = RAW_DATA_DIR / "inps_open_data" / Path(url).name
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
    year = 2024
    pensioners = observatory_region_measure("413", "Beneficiari totali", year, "_FREQ_SUM", "SUM")
    pensions = observatory_region_measure("416", "Prestazioni pensionistiche totali", year, "_FREQ_SUM", "SUM")
    average_annual = observatory_region_measure("416", "Prestazioni pensionistiche totali", year, "Importo medio annuo (euro)", "")
    for region in REGION_NUTS2:
        pensioner_count = pensioners.get(region)
        pension_count = pensions.get(region)
        average = average_annual.get(region)
        if pensioner_count is not None:
            territorial_rows.append(territorial(year, "regione", region, "pensionati", pensioner_count, "numero", "inps_osservatori_api", "Beneficiari totali per regione; API Osservatori statistici INPS, osservatorio 413."))
        if pension_count is not None:
            territorial_rows.append(territorial(year, "regione", region, "pensioni_vigenti", pension_count, "numero", "inps_osservatori_api", "Prestazioni pensionistiche per regione; API Osservatori statistici INPS, osservatorio 416."))
        if average is not None:
            territorial_rows.append(territorial(year, "regione", region, "importo_medio_pensione_mensile_regionale", average / 12, "euro", "inps_osservatori_api", "Importo lordo medio annuo della prestazione diviso per 12; API Osservatori statistici INPS, osservatorio 416."))
        if pension_count is not None and average is not None:
            territorial_rows.append(territorial(year, "regione", region, "spesa_pensionistica_regionale", pension_count * average, "euro", "elaborazione_repo", "Numero di prestazioni per importo lordo medio annuo; dati API INPS osservatorio 416."))
    log.append({"fonte": "inps_osservatori_api", "tabella": "tabella_territoriale", "righe": len(pensioners), "stato": "ok"})


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
    for _, record in sheet.iterrows():
        values = record.tolist()
        label = str(values[1]).strip() if len(values) > 1 and pd.notna(values[1]) else ""
        if not label or label in {"Classe di importo mensile***", "TOTALE"} or label.startswith("Tabella") or label.startswith("*"):
            continue
        count = number(values[10] if len(values) > 10 else None)
        amount_million = number(values[13] if len(values) > 13 else None)
        minimum, maximum = class_bounds(label)
        common = (year, "pensionati_inps", "reddito_pensionistico_mensile", label, minimum, maximum, "Totale", "Italia - INPS")
        if count is not None:
            distribution_rows.append(distribution(*common, "pensionati_per_classe_reddito_pensionistico", count, "numero", source_id, f"Pensionati per reddito pensionistico mensile complessivo; tabella 3.4, anno {year}."))
        if amount_million is not None:
            amount = amount_million * 1_000_000
            distribution_rows.append(distribution(*common, "reddito_pensionistico_totale", amount, "euro", source_id, f"Reddito pensionistico annuo complessivo della classe; tabella 3.4, anno {year}."))
            if count:
                distribution_rows.append(distribution(*common, "reddito_pensionistico_medio_mensile_classe", amount / count / 12, "euro", "elaborazione_repo", "Reddito annuo della classe diviso per pensionati e per 12 mesi."))


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
                    add_annual(rows, year, "spesa_pensionistica_inps_stimata", "stock_amministrativo", "elaborazione_repo", count * avg * 12, "euro", "Italia - INPS", "Stima da numero prestazioni e importo medio mensile della tabella 3.7.")

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


def build_dashboard_core_data(log_path: str | Path = LOG_PATHS["dashboard_core"]) -> pd.DataFrame:
    prepare_directories()
    annual_rows: list[dict[str, object]] = []
    transfer_rows: list[dict[str, object]] = []
    management_rows: list[dict[str, object]] = []
    territorial_rows: list[dict[str, object]] = []
    comparison_rows: list[dict[str, object]] = []
    distribution_rows: list[dict[str, object]] = []
    profession_rows: list[dict[str, object]] = []
    log_rows: list[dict[str, object]] = []

    build_annual_from_open_data(annual_rows, log_rows)
    build_contributions(annual_rows, log_rows)
    build_consistent_annual_series(annual_rows, log_rows)
    build_state_transfers(annual_rows, transfer_rows, log_rows)
    build_region_history(territorial_rows, log_rows)
    build_current_regions_from_api(territorial_rows, log_rows)
    build_eurostat_data(territorial_rows, comparison_rows, log_rows)
    build_from_historical_appendices(annual_rows, management_rows, profession_rows, distribution_rows, log_rows)
    build_from_appendix(annual_rows, management_rows, territorial_rows, distribution_rows, profession_rows, log_rows)
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
