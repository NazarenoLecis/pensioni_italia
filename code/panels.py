from __future__ import annotations

import pandas as pd

ANNUAL_PANEL_COLUMNS = ["year", "indicator_id", "source_id", "value", "unit", "notes"]
SCHEME_PANEL_COLUMNS = ["year", "scheme_id", "indicator_id", "source_id", "value", "unit", "notes"]
TERRITORIAL_PANEL_COLUMNS = ["year", "geo_code", "indicator_id", "source_id", "value", "unit", "notes"]


def empty_annual_panel() -> pd.DataFrame:
    return pd.DataFrame(columns=ANNUAL_PANEL_COLUMNS)


def empty_scheme_panel() -> pd.DataFrame:
    return pd.DataFrame(columns=SCHEME_PANEL_COLUMNS)


def empty_territorial_panel() -> pd.DataFrame:
    return pd.DataFrame(columns=TERRITORIAL_PANEL_COLUMNS)
