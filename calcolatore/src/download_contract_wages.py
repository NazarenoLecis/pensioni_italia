from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from config import RAW_DATA_DIR  # noqa: E402


FLOW_URL = "https://esploradati.istat.it/SDMXWS/rest/data/155_318"
OUTPUT_PATH = ROOT / "output" / "data" / "clean" / "retribuzioni_contrattuali_ccnl.csv"
RAW_DIR = RAW_DATA_DIR / "istat_retribuzioni_contrattuali"

AGREEMENTS = {
    "totale_economia": ("Z3620", "Totale economia"),
    "agricoltura": ("Z0010", "Agricoltura"),
    "metalmeccanici": ("Z0720", "Metalmeccanica"),
    "edilizia": ("Z1180", "Costruzioni"),
    "commercio": ("Z1260", "Commercio"),
    "trasporti": ("Z1280", "Trasporti, poste e attivita connesse"),
    "turismo": ("Z1840", "Alloggio e ristorazione"),
    "pubblica_amministrazione": ("Z2540", "Pubblica amministrazione"),
}


def download_agreement(agreement_id: str, code: str, label: str) -> list[dict[str, object]]:
    url = (
        f"{FLOW_URL}/A.IT.WAGE_E_2021.N.10.{code}"
        "?startPeriod=1990&endPeriod=2025"
    )
    response = requests.get(url, headers={"Accept": "application/json"}, timeout=120)
    response.raise_for_status()
    payload = response.json()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / f"{agreement_id}.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )

    time_values = payload["structure"]["dimensions"]["observation"][0]["values"]
    series = next(iter(payload["dataSets"][0]["series"].values()))
    rows = []
    for position, observation in series["observations"].items():
        if not observation or observation[0] is None:
            continue
        rows.append(
            {
                "indice_ccnl_id": agreement_id,
                "codice_istat": code,
                "contratto_istat": label,
                "anno": int(time_values[int(position)]["id"]),
                "indice_retribuzione_contrattuale": float(observation[0]),
                "base": "dicembre 2021=100",
                "fonte_id": "istat_retribuzioni_contrattuali_sdmx",
                "natura_dato": "osservato",
            }
        )
    return rows


def main() -> None:
    rows = []
    for agreement_id, (code, label) in AGREEMENTS.items():
        rows.extend(download_agreement(agreement_id, code, label))
    result = pd.DataFrame(rows).sort_values(["indice_ccnl_id", "anno"])
    if result.empty or result["anno"].min() > 2005 or result["anno"].max() < 2025:
        raise ValueError("Copertura insufficiente delle retribuzioni contrattuali ISTAT")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)
    print(f"Salvate {len(result)} osservazioni contrattuali ISTAT in {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
