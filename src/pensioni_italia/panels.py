from __future__ import annotations

import pandas as pd

ANNUAL_PANEL_COLUMNS = [
    "year",
    "indicator_id",
    "definition_family",
    "source_id",
    "value",
    "unit",
    "geo",
    "notes",
]

SCHEME_PANEL_COLUMNS = [
    "year",
    "scheme_id",
    "scheme_name",
    "scheme_group",
    "indicator_id",
    "source_id",
    "value",
    "unit",
    "notes",
]

TERRITORIAL_PANEL_COLUMNS = [
    "year",
    "geo_level",
    "geo_code",
    "geo_name",
    "indicator_id",
    "source_id",
    "value",
    "unit",
    "notes",
]


def empty_annual_panel() -> pd.DataFrame:
    return pd.DataFrame(columns=ANNUAL_PANEL_COLUMNS)


def empty_scheme_panel() -> pd.DataFrame:
    return pd.DataFrame(columns=SCHEME_PANEL_COLUMNS)


def empty_territorial_panel() -> pd.DataFrame:
    return pd.DataFrame(columns=TERRITORIAL_PANEL_COLUMNS)


def validate_columns(frame: pd.DataFrame, required_columns: list[str]) -> None:
    missing = [column for column in required_columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
