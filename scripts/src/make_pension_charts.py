from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from config import FINAL_TABLE_PATHS, LOG_PATHS, OUTPUT_CHARTS_DIR
from utils import prepare_directories, read_csv_optional, save_table, safe_to_numeric

CHART_SPECS = [
    {
        "table": "tabella_annuale_pensioni",
        "indicator": "spesa_pensionistica_pil",
        "title": "Spesa pensionistica in rapporto al PIL",
        "filename": "spesa_pensionistica_pil.png",
        "ylabel": "Percentuale del PIL",
    },
    {
        "table": "tabella_annuale_pensioni",
        "indicator": "trasferimenti_stato_inps",
        "title": "Trasferimenti statali a INPS",
        "filename": "trasferimenti_stato_inps.png",
        "ylabel": "Euro",
    },
    {
        "table": "tabella_demografia_lavoro",
        "indicator": "pensionati_su_occupati",
        "title": "Rapporto tra pensionati e occupati",
        "filename": "pensionati_su_occupati.png",
        "ylabel": "Rapporto",
    },
]


def filter_indicator(table: pd.DataFrame, indicator_id: str) -> pd.DataFrame:
    """Filtra una tabella finale per indicatore_id."""
    if table.empty or "indicatore_id" not in table.columns:
        return pd.DataFrame()
    return table[table["indicatore_id"].astype(str).eq(indicator_id)].copy()


def make_line_chart(table: pd.DataFrame, output_path: str | Path, title: str, ylabel: str) -> Path | None:
    """Crea un grafico a linea se la tabella contiene anno e valore numerici."""
    if table.empty or not {"anno", "valore"}.issubset(table.columns):
        return None
    data = table.copy()
    data["anno"] = safe_to_numeric(data["anno"])
    data["valore"] = safe_to_numeric(data["valore"])
    data = data.dropna(subset=["anno", "valore"]).sort_values("anno")
    if data.empty:
        return None
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 6))
    plt.plot(data["anno"], data["valore"], marker="o")
    plt.title(title)
    plt.xlabel("Anno")
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close()
    return output_path


def make_pension_charts(log_path: str | Path = LOG_PATHS["charts"]) -> pd.DataFrame:
    """Genera i grafici configurati e salva un log in output/data/logs."""
    prepare_directories([OUTPUT_CHARTS_DIR])
    rows = []
    for spec in CHART_SPECS:
        source_table = read_csv_optional(FINAL_TABLE_PATHS[spec["table"]])
        indicator_table = filter_indicator(source_table, spec["indicator"])
        output_path = OUTPUT_CHARTS_DIR / spec["filename"]
        written = make_line_chart(indicator_table, output_path, spec["title"], spec["ylabel"])
        rows.append(
            {
                "grafico": spec["filename"],
                "tabella": spec["table"],
                "indicatore": spec["indicator"],
                "stato": "ok" if written else "saltato",
                "percorso_output": str(written or ""),
            }
        )
    log = pd.DataFrame(rows)
    save_table(log, log_path)
    return log


if __name__ == "__main__":
    make_pension_charts()
