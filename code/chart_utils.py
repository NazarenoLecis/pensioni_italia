from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from utils import PROJECT_ROOT

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
CHARTS_DIR = OUTPUTS_DIR / "charts"


def ensure_charts_dir(output_dir: str | Path = CHARTS_DIR) -> Path:
    """Create the chart output folder and return it."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def require_columns(frame: pd.DataFrame, columns: list[str]) -> None:
    """Stop the analysis when the input table misses required columns."""
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")


def save_current_chart(output_path: str | Path) -> Path:
    """Save the current matplotlib figure and close it."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def plot_line_chart(
    frame: pd.DataFrame,
    *,
    x_column: str,
    y_column: str,
    output_path: str | Path,
    title: str,
    x_label: str = "",
    y_label: str = "",
    group_column: str | None = None,
    source_note: str = "",
) -> Path:
    """Create a line chart from a long or wide table.

    Flow: check required columns, sort the data, plot one line or one line per
    group, add labels and source note, save the chart as PNG.
    """
    required = [x_column, y_column]
    if group_column is not None:
        required.append(group_column)
    require_columns(frame, required)
    data = frame.dropna(subset=[x_column, y_column]).copy()
    data = data.sort_values([group_column, x_column] if group_column else [x_column])

    plt.figure(figsize=(10, 6))
    if group_column:
        for group_value, group_data in data.groupby(group_column):
            plt.plot(group_data[x_column], group_data[y_column], marker="o", label=str(group_value))
        plt.legend(frameon=False)
    else:
        plt.plot(data[x_column], data[y_column], marker="o")

    plt.title(title)
    plt.xlabel(x_label or x_column)
    plt.ylabel(y_label or y_column)
    if source_note:
        plt.figtext(0.01, 0.01, source_note, ha="left", fontsize=9)
    return save_current_chart(output_path)


def plot_bar_chart(
    frame: pd.DataFrame,
    *,
    category_column: str,
    value_column: str,
    output_path: str | Path,
    title: str,
    x_label: str = "",
    y_label: str = "",
    source_note: str = "",
    top_n: int | None = None,
) -> Path:
    """Create a bar chart from a categorical table."""
    require_columns(frame, [category_column, value_column])
    data = frame.dropna(subset=[category_column, value_column]).copy()
    data = data.sort_values(value_column, ascending=False)
    if top_n is not None:
        data = data.head(top_n)

    plt.figure(figsize=(10, 6))
    plt.bar(data[category_column].astype(str), data[value_column])
    plt.title(title)
    plt.xlabel(x_label or category_column)
    plt.ylabel(y_label or value_column)
    plt.xticks(rotation=45, ha="right")
    if source_note:
        plt.figtext(0.01, 0.01, source_note, ha="left", fontsize=9)
    return save_current_chart(output_path)
