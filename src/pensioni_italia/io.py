from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_frame(frame: pd.DataFrame, path: str | Path, *, index: bool = False) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix.lower()
    if suffix == ".parquet":
        frame.to_parquet(output_path, index=index)
    elif suffix == ".csv":
        frame.to_csv(output_path, index=index)
    else:
        raise ValueError(f"Unsupported output format: {suffix}")
    return output_path


def read_optional_csv(path: str | Path) -> pd.DataFrame:
    input_path = Path(path)
    if not input_path.exists() or input_path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(input_path)


def normalise_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()
