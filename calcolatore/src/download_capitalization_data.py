from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import re
import sys

import fitz
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from config import RAW_DATA_DIR  # noqa: E402


ISTAT_CURRENT_URL = (
    "https://esploradati.istat.it/SDMXWS/rest/data/92_506/"
    "A.IT.B1GQ_B_W2_S1.V.N.?startPeriod=1995"
)
ISTAT_HISTORICAL_URL = (
    "https://esploradati.istat.it/SDMXWS/rest/data/284_159/"
    "A.IT.B1XG_1.9.V.A.?startPeriod=1970&endPeriod=2013"
)
OFFICIAL_RATES_URL = "https://www.lavoro.gov.it/temi-e-priorita-previdenza/focus/nota-istat"
OUTPUT_PATH = ROOT / "output" / "data" / "clean" / "tassi_capitalizzazione_montante.csv"
GDP_OUTPUT_PATH = ROOT / "output" / "data" / "clean" / "pil_nominale_capitalizzazione.csv"
RAW_DIR = RAW_DATA_DIR / "istat_capitalizzazione_montante"


def download_json(url: str, filename: str) -> dict:
    response = requests.get(url, headers={"Accept": "application/json"}, timeout=120)
    response.raise_for_status()
    payload = response.json()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / filename).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return payload


def parse_sdmx_gdp(payload: dict, source_series: str) -> pd.DataFrame:
    structure = payload["structure"]
    dimensions = structure["dimensions"]["series"]
    time_values = structure["dimensions"]["observation"][0]["values"]
    records: list[dict] = []

    for key, series in payload["dataSets"][0]["series"].items():
        positions = [int(value) for value in key.split(":")]
        dimension_values = {
            dimension["id"]: dimension["values"][position]["id"]
            for dimension, position in zip(dimensions, positions)
        }
        edition = dimension_values["EDITION"]
        for time_position, observation in series["observations"].items():
            if not observation or observation[0] is None:
                continue
            records.append(
                {
                    "anno_pil": int(time_values[int(time_position)]["id"]),
                    "pil_nominale_milioni": float(observation[0]),
                    "edizione": edition,
                    "serie_istat": source_series,
                    "fonte_id": "istat_pil_nominale_sdmx",
                }
            )

    result = pd.DataFrame(records)
    if result.empty:
        raise ValueError(f"La serie ISTAT {source_series} non contiene osservazioni")
    return result.sort_values(["edizione", "anno_pil"]).reset_index(drop=True)


def download_official_rates() -> pd.DataFrame:
    response = requests.get(OFFICIAL_RATES_URL, timeout=120)
    response.raise_for_status()
    if not response.content.startswith(b"%PDF"):
        raise ValueError("La nota ufficiale ISTAT non ha restituito un PDF")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / "nota_istat_tassi_ufficiali.pdf").write_bytes(response.content)
    document = fitz.open(stream=BytesIO(response.content), filetype="pdf")
    text = "\n".join(page.get_text("text") for page in document)
    rows = [
        {
            "anno": int(match.group(1)),
            "tasso_ufficiale_pubblicato": float(match.group(2)),
            "coefficiente_ufficiale_pubblicato": float(match.group(3)),
        }
        for match in re.finditer(
            r"(?m)^(19\d{2}|20\d{2})\s+(-?0\.\d{6})\s+(0\.\d{6}|1\.\d{6})\s*$",
            text,
        )
    ]
    result = pd.DataFrame(rows).drop_duplicates("anno").sort_values("anno")
    if result.empty:
        raise ValueError("Nessun tasso estratto dalla nota ufficiale ISTAT")
    return result


def calculate_capitalization_rates(gdp: pd.DataFrame, official: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for year in range(1976, int(official["anno"].max()) + 1):
        start_year = year - 6
        end_year = year - 1
        candidates = []
        for edition, group in gdp.groupby(["serie_istat", "edizione"], sort=False):
            values = group.set_index("anno_pil")["pil_nominale_milioni"]
            if start_year in values.index and end_year in values.index:
                candidates.append((int(group["anno_pil"].max()), edition, values))
        if not candidates:
            raise ValueError(f"Mancano i livelli di PIL necessari per il tasso {year}")
        _, (series_name, edition), values = max(candidates, key=lambda item: (item[0], item[1][1]))
        start_gdp = float(values.loc[start_year])
        end_gdp = float(values.loc[end_year])
        rate = (end_gdp / start_gdp) ** (1 / 5) - 1
        rows.append(
            {
                "anno": year,
                "pil_anno_finale": end_year,
                "pil_finale_milioni": end_gdp,
                "pil_anno_iniziale": start_year,
                "pil_iniziale_milioni": start_gdp,
                "tasso_capitalizzazione": rate,
                "coefficiente_rivalutazione": 1 + rate,
                "edizione_pil": edition,
                "serie_istat": series_name,
                "fonte_id": "istat_pil_nominale_sdmx",
                "natura_dato": "calcolato_da_pil_nominale_istat",
                "note": "Formula (PIL t-1 / PIL t-6)^(1/5)-1",
            }
        )
    result = pd.DataFrame(rows).merge(official, on="anno", how="left", validate="one_to_one")
    result["scarto_da_tasso_ufficiale"] = (
        result["tasso_capitalizzazione"] - result["tasso_ufficiale_pubblicato"]
    )
    return result


def main() -> None:
    current = parse_sdmx_gdp(
        download_json(ISTAT_CURRENT_URL, "pil_nominale_corrente.json"), "DCCN_PILN"
    )
    historical = parse_sdmx_gdp(
        download_json(ISTAT_HISTORICAL_URL, "pil_nominale_storico.json"), "DCCN_PILN_SEC95"
    )
    gdp = pd.concat([historical, current], ignore_index=True)
    official = download_official_rates()
    rates = calculate_capitalization_rates(gdp, official)

    GDP_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    gdp.to_csv(GDP_OUTPUT_PATH, index=False)
    rates.to_csv(OUTPUT_PATH, index=False)
    print(
        f"Salvati {len(gdp)} livelli di PIL nominale e {len(rates)} tassi calcolati "
        f"con il metodo quinquennale ufficiale"
    )


if __name__ == "__main__":
    main()
