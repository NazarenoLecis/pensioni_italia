from __future__ import annotations

from pathlib import Path

import pandas as pd

from panels import empty_annual_panel, empty_scheme_panel, empty_territorial_panel
from utils import FINAL_DIR, ensure_project_dirs, write_frame

ANNUAL_PANEL_PATH = FINAL_DIR / "annual_pensions_panel.csv"
SCHEME_PANEL_PATH = FINAL_DIR / "schemes_panel.csv"
TERRITORIAL_PANEL_PATH = FINAL_DIR / "territorial_panel.csv"


def initialise_final_panels(
    *,
    annual_panel_path: str | Path = ANNUAL_PANEL_PATH,
    scheme_panel_path: str | Path = SCHEME_PANEL_PATH,
    territorial_panel_path: str | Path = TERRITORIAL_PANEL_PATH,
) -> dict[str, str]:
    """Crea i pannelli finali vuoti se la pipeline non li ha ancora generati.

    Flow: crea le cartelle locali, costruisce tre template coerenti, salva i CSV
    in `data/final`. In seguito le funzioni di pulizia popoleranno questi file
    usando i dati scaricati dalle fonti ufficiali.
    """
    ensure_project_dirs()
    outputs = {
        "annual": write_frame(empty_annual_panel(), annual_panel_path),
        "scheme": write_frame(empty_scheme_panel(), scheme_panel_path),
        "territorial": write_frame(empty_territorial_panel(), territorial_panel_path),
    }
    return {key: str(value) for key, value in outputs.items()}


if __name__ == "__main__":
    initialise_final_panels()
