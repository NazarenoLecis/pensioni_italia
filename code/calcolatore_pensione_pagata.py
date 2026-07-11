from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
SRC_DIR = SCRIPTS_DIR / "src"
for path in [SCRIPTS_DIR, SRC_DIR]:
    if str(path) not in sys.path:
        sys.path.append(str(path))

from pension_paid_calculator import (  # noqa: E402
    build_accurate_career,
    build_simplified_career,
    calculate_paid_pension_metrics,
    run_pension_paid_calculator,
    transformation_coefficient,
    weighted_fpld_rate_for_year,
)


def esegui_calcolatore_base():
    """Wrapper di compatibilita': la logica vive in scripts/src/pension_paid_calculator.py."""
    return run_pension_paid_calculator()


if __name__ == "__main__":
    print(esegui_calcolatore_base().to_string(index=False))
