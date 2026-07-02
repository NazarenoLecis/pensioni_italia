from __future__ import annotations

from pathlib import Path

import pandas as pd

from chart_utils import CHARTS_DIR, ensure_charts_dir, plot_bar_chart, plot_line_chart
from utils import FINAL_DIR, read_optional_csv, write_frame

ANNUAL_PANEL_PATH = FINAL_DIR / "annual_pensions_panel.csv"
SCHEME_PANEL_PATH = FINAL_DIR / "schemes_panel.csv"
TERRITORIAL_PANEL_PATH = FINAL_DIR / "territorial_panel.csv"
ANALYSIS_LOG_PATH = FINAL_DIR / "analysis_log.csv"


def load_panel(input_path: str | Path) -> pd.DataFrame:
    """Read a final panel if it exists.

    The function returns an empty DataFrame when the file is missing. This lets
    the analysis flow run before all panels are available, while still producing
    a clear log of skipped charts.
    """
    return read_optional_csv(input_path)


def filter_indicator(frame: pd.DataFrame, indicator_id: str) -> pd.DataFrame:
    """Filter a long panel by indicator_id."""
    if frame.empty or "indicator_id" not in frame.columns:
        return pd.DataFrame()
    return frame[frame["indicator_id"].astype(str).eq(indicator_id)].copy()


def plot_annual_indicator(
    *,
    indicator_id: str,
    title: str,
    output_name: str,
    y_label: str = "value",
    input_path: str | Path = ANNUAL_PANEL_PATH,
) -> dict[str, object]:
    """Create a line chart for one national annual indicator.

    Expected input format: long panel with at least `year`, `indicator_id` and
    `value`. This keeps the chart function independent from the original source.
    """
    frame = filter_indicator(load_panel(input_path), indicator_id)
    if frame.empty:
        return {"chart": output_name, "status": "skipped", "reason": "missing indicator or panel"}
    output_path = CHARTS_DIR / f"{output_name}.png"
    plot_line_chart(
        frame,
        x_column="year",
        y_column="value",
        output_path=output_path,
        title=title,
        x_label="Anno",
        y_label=y_label,
        source_note="Fonte: dati ufficiali; elaborazione Nazareno Lecis.",
    )
    return {"chart": output_name, "status": "ok", "output_path": str(output_path)}


def plot_scheme_indicator(
    *,
    indicator_id: str,
    title: str,
    output_name: str,
    year: int | None = None,
    top_n: int = 15,
    input_path: str | Path = SCHEME_PANEL_PATH,
) -> dict[str, object]:
    """Create a bar chart for one indicator by pension scheme.

    If `year` is not provided, the function uses the latest year available in
    the panel. This is useful for rankings by scheme or fund.
    """
    frame = filter_indicator(load_panel(input_path), indicator_id)
    if frame.empty:
        return {"chart": output_name, "status": "skipped", "reason": "missing indicator or panel"}
    if year is None:
        year = int(pd.to_numeric(frame["year"], errors="coerce").dropna().max())
    frame = frame[pd.to_numeric(frame["year"], errors="coerce").eq(year)]
    if frame.empty:
        return {"chart": output_name, "status": "skipped", "reason": "missing selected year"}
    output_path = CHARTS_DIR / f"{output_name}.png"
    category_column = "scheme_name" if "scheme_name" in frame.columns else "scheme_id"
    plot_bar_chart(
        frame,
        category_column=category_column,
        value_column="value",
        output_path=output_path,
        title=title,
        x_label="Gestione",
        y_label="Valore",
        source_note="Fonte: dati ufficiali; elaborazione Nazareno Lecis.",
        top_n=top_n,
    )
    return {"chart": output_name, "status": "ok", "output_path": str(output_path)}


def run_core_pension_charts(output_log_path: str | Path = ANALYSIS_LOG_PATH) -> pd.DataFrame:
    """Run the first standard charts from final panels.

    The function is deliberately conservative. It skips charts whose input panel
    or indicator is not yet available, then writes a log explaining what happened.
    """
    ensure_charts_dir()
    logs = []
    logs.append(plot_annual_indicator(
        indicator_id="pension_expenditure_to_gdp",
        title="Spesa pensionistica in rapporto al PIL",
        output_name="spesa_pensionistica_pil",
        y_label="Percentuale del PIL",
    ))
    logs.append(plot_annual_indicator(
        indicator_id="pensioners_to_employed",
        title="Pensionati su occupati",
        output_name="pensionati_su_occupati",
        y_label="Rapporto",
    ))
    logs.append(plot_scheme_indicator(
        indicator_id="inps_pension_expenditure",
        title="Spesa pensionistica per gestione",
        output_name="spesa_per_gestione",
    ))
    log = pd.DataFrame(logs)
    write_frame(log, output_log_path)
    return log


if __name__ == "__main__":
    run_core_pension_charts()
