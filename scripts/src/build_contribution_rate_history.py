from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import sys
import zipfile

import pandas as pd
import requests

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from config import CLEAN_DATA_DIR, FINAL_TABLE_PATHS, LOG_PATHS, RAW_DATA_DIR
from utils import prepare_directories, read_csv_optional, save_table


ALIQUOTE_STORICHE_URL = "https://servizi2.inps.it/Servizi/CircMessStd/maestro.ashx?flagOriginale=1&idAllegato=4523"
ALIQUOTE_CORRENTI_URL = "https://www.inps.it/it/it/inps-comunica/diritti-e-obblighi-in-materia-di-sicurezza-sociale-nell-unione-e/per-le-imprese/aliquote-contributive.html"
RAW_ZIP_PATH = RAW_DATA_DIR / "inps" / "aliquote_storiche.zip"
RAW_XLS_PATH = RAW_DATA_DIR / "inps" / "Allegato 1 Aliquote storiche.xls"
CLEAN_PERIODS_PATH = CLEAN_DATA_DIR / "aliquote_ivs_fpld_periodi.csv"


def parse_percent(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().replace("%", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def parse_date(value: object) -> date | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=False)
    if pd.isna(parsed):
        return None
    return parsed.date()


def download_aliquote_storiche() -> Path:
    RAW_ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(ALIQUOTE_STORICHE_URL, timeout=30)
    response.raise_for_status()
    RAW_ZIP_PATH.write_bytes(response.content)
    with zipfile.ZipFile(RAW_ZIP_PATH) as archive:
        names = archive.namelist()
        if not names:
            raise ValueError("Archivio aliquote storiche vuoto")
        RAW_XLS_PATH.write_bytes(archive.read(names[0]))
    return RAW_XLS_PATH


def read_fpld_periods(xls_path: Path) -> pd.DataFrame:
    raw = pd.read_excel(xls_path, sheet_name="Aliquote storiche", header=None, engine="xlrd")
    rows: list[dict[str, object]] = []
    in_fpld_block = False
    for _, row in raw.iterrows():
        first = row.iloc[0]
        text = "" if pd.isna(first) else str(first)
        if "F.P.L.D" in text:
            in_fpld_block = True
            continue
        if not in_fpld_block:
            continue
        start = parse_date(row.iloc[0])
        total = parse_percent(row.iloc[2])
        if start is None or total is None:
            if rows:
                break
            continue
        end_value = row.iloc[1]
        end = parse_date(end_value)
        end_label = str(end_value).strip() if end is None and not pd.isna(end_value) else ""
        if end is None and "IN POI" in end_label.upper():
            end = date(datetime.now().year, 12, 31)
        if end is None:
            end = date(start.year, 12, 31)
        rows.append(
            {
                "periodo_dal": start.isoformat(),
                "periodo_al": end.isoformat(),
                "aliquota_totale": total,
                "aliquota_datore_lavoro": parse_percent(row.iloc[3]),
                "aliquota_lavoratore": parse_percent(row.iloc[4]),
                "fonte_id": "inps_aliquote_storiche",
                "sistema": "FPLD lavoratori dipendenti",
                "note": "Aliquote contributive IVS in vigore nel FPLD secondo allegato storico INPS.",
            }
        )
    if not rows:
        raise ValueError("Nessun periodo FPLD trovato nell'allegato aliquote storiche")
    return pd.DataFrame(rows)


def expand_year_end_series(periods: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    current_year = datetime.now().year
    for year in range(int(periods["periodo_dal"].str[:4].astype(int).min()), current_year + 1):
        year_end = date(year, 12, 31)
        active = periods[
            (pd.to_datetime(periods["periodo_dal"]).dt.date <= year_end)
            & (pd.to_datetime(periods["periodo_al"]).dt.date >= year_end)
        ]
        if active.empty:
            continue
        row = active.iloc[-1]
        for parameter_id, source_column in [
            ("aliquota_ivs_fpld_totale_fine_anno", "aliquota_totale"),
            ("aliquota_ivs_fpld_datore_lavoro_fine_anno", "aliquota_datore_lavoro"),
            ("aliquota_ivs_fpld_lavoratore_fine_anno", "aliquota_lavoratore"),
        ]:
            records.append(
                {
                    "anno": year,
                    "parametro_id": parameter_id,
                    "sistema": "FPLD lavoratori dipendenti",
                    "fonte_id": row["fonte_id"],
                    "valore": row[source_column],
                    "unita": "% della retribuzione imponibile",
                    "note": "Valore in vigore al 31 dicembre dell'anno; non include necessariamente contributi minori usati nel riferimento corrente al 33%.",
                }
            )
    records.append(
        {
            "anno": current_year,
            "parametro_id": "aliquota_ivs_standard_ago_corrente",
            "sistema": "AGO/FPLD lavoratori dipendenti",
            "fonte_id": "inps_aliquote_correnti",
            "valore": 33.0,
            "unita": "% della retribuzione imponibile",
            "note": "Riferimento corrente INPS: aliquota contributiva ai fini pensionistici IVS per assicurati al FPLD/AGO pari al 33%.",
        }
    )
    return pd.DataFrame(records)


def merge_parametri_sistema(rows: pd.DataFrame) -> pd.DataFrame:
    path = FINAL_TABLE_PATHS["tabella_parametri_sistema"]
    existing = read_csv_optional(path)
    if existing.empty:
        existing = pd.DataFrame(columns=["anno", "parametro_id", "sistema", "fonte_id", "valore", "unita", "note"])
    managed_sources = {"inps_aliquote_storiche", "inps_aliquote_correnti"}
    existing = existing[~existing.get("fonte_id", pd.Series(dtype=str)).isin(managed_sources)].copy()
    return pd.concat([existing, rows], ignore_index=True)


def build_contribution_rate_history(log_path: str | Path = LOG_PATHS["contribution_rates"]) -> pd.DataFrame:
    prepare_directories([RAW_ZIP_PATH.parent, CLEAN_DATA_DIR])
    xls_path = download_aliquote_storiche()
    periods = read_fpld_periods(xls_path)
    save_table(periods, CLEAN_PERIODS_PATH)
    annual_rows = expand_year_end_series(periods)
    merged = merge_parametri_sistema(annual_rows)
    save_table(merged, FINAL_TABLE_PATHS["tabella_parametri_sistema"])
    log = pd.DataFrame(
        [
            {
                "fase": "contribution_rate_history",
                "periodi": len(periods),
                "righe_annuali": len(annual_rows),
                "percorso_periodi": str(CLEAN_PERIODS_PATH),
                "percorso_finale": str(FINAL_TABLE_PATHS["tabella_parametri_sistema"]),
                "fonte_url": ALIQUOTE_STORICHE_URL,
                "stato": "ok",
            }
        ]
    )
    save_table(log, log_path)
    return log


if __name__ == "__main__":
    print(build_contribution_rate_history().to_string(index=False))
