from __future__ import annotations

from pathlib import Path

import pandas as pd

from analysis_pensions import run_core_pension_charts
from utils import FINAL_DIR, write_frame

ANALYSIS_ALL_LOG_PATH = FINAL_DIR / "analysis_all_log.csv"
RUN_CORE_PENSION_CHARTS = True


def add_analysis_log(rows: list[dict[str, object]], block: str, log: pd.DataFrame | None) -> None:
    """Add one summary row for an analysis block."""
    if log is None:
        rows.append({"block": block, "result": "skipped", "charts": 0, "ok": 0})
        return
    ok = int(log["status"].astype(str).str.lower().eq("ok").sum()) if "status" in log.columns else 0
    rows.append({"block": block, "result": "done", "charts": len(log), "ok": ok})


def run_all_analysis(
    *,
    run_core_pension_charts_flag: bool = RUN_CORE_PENSION_CHARTS,
    output_log_path: str | Path = ANALYSIS_ALL_LOG_PATH,
) -> pd.DataFrame:
    """Run all analysis blocks and save a compact log."""
    rows: list[dict[str, object]] = []
    add_analysis_log(
        rows,
        "core_pension_charts",
        run_core_pension_charts() if run_core_pension_charts_flag else None,
    )
    log = pd.DataFrame(rows)
    write_frame(log, output_log_path)
    return log


if __name__ == "__main__":
    run_all_analysis()
