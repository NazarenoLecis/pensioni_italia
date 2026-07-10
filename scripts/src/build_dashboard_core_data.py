from __future__ import annotations

from io import BytesIO
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
CASELLARIO_2024_PDF_URL = "https://servizi2.inps.it/servizi/osservatoristatistici/api/getAllegato/?idAllegato=1007"

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


def build_from_historical_appendices(
    rows: list[dict[str, object]],
    management_rows: list[dict[str, object]],
    profession_rows: list[dict[str, object]],
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
                if not gestione or gestione.startswith("Tabella") or gestione in {"Gestione"} or gestione.startswith("*"):
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
        if not gestione or gestione.startswith("Tabella") or gestione in {"Gestione", "TOTALE"} or gestione.startswith("*"):
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

    sheet34 = pd.read_excel(xl, sheet_name="3.4", header=None)
    for _, record in sheet34.iterrows():
        values = record.tolist()
        label = str(values[1]).strip() if len(values) > 1 and pd.notna(values[1]) else ""
        if not label or label in {"Classe di importo mensile***", "TOTALE"} or label.startswith("Tabella") or label.startswith("*"):
            continue
        total_count = number(values[10] if len(values) > 10 else None)
        total_amount_million = number(values[13] if len(values) > 13 else None)
        min_value, max_value = class_bounds(label)
        if total_count is not None:
            distribution_rows.append(distribution(2025, "pensionati_inps", "reddito_pensionistico_mensile", label, min_value, max_value, "Totale", "Italia - INPS", "pensionati_per_classe_reddito_pensionistico", total_count, "numero", "inps_appendice_xxv", "Persone classificate per reddito pensionistico mensile complessivo; tabella 3.4."))
        if total_amount_million is not None:
            distribution_rows.append(distribution(2025, "pensionati_inps", "reddito_pensionistico_mensile", label, min_value, max_value, "Totale", "Italia - INPS", "reddito_pensionistico_totale", total_amount_million * 1_000_000, "euro", "inps_appendice_xxv", "Reddito pensionistico annuo complessivo della classe; tabella 3.4, fonte in milioni."))

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
    if "assistenz" in text or "invalidita civile" in text or "sociali" in text:
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
    management_rows: list[dict[str, object]] = []
    territorial_rows: list[dict[str, object]] = []
    distribution_rows: list[dict[str, object]] = []
    profession_rows: list[dict[str, object]] = []
    log_rows: list[dict[str, object]] = []

    build_annual_from_open_data(annual_rows, log_rows)
    build_contributions(annual_rows, log_rows)
    build_region_history(territorial_rows, log_rows)
    build_from_historical_appendices(annual_rows, management_rows, profession_rows, log_rows)
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
        "tabella_gestioni": frame("tabella_gestioni", management_rows),
        "tabella_territoriale": frame("tabella_territoriale", drop_invalid(territorial_rows)),
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
