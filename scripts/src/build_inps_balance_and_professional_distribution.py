from __future__ import annotations

from pathlib import Path
import sys
import unicodedata

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from build_pension_indicators import FINAL_TABLE_SCHEMAS
from config import CLEAN_DATA_DIR, FINAL_TABLE_PATHS, LOG_PATHS, MAPPING_GESTIONI_PROFESSIONI_INPS_PATH, RAW_DATA_DIR
from utils import prepare_directories, read_csv_optional, save_table, split_semicolon

RAW_INPUTS = {
    "inps_bilancio_voci": [
        RAW_DATA_DIR / "inps_bilancio" / "inps_bilancio_voci.csv",
        CLEAN_DATA_DIR / "inps_bilancio_voci.csv",
    ],
    "inps_gestioni_previdenziali": [
        RAW_DATA_DIR / "inps_bilancio" / "inps_gestioni_previdenziali.csv",
        CLEAN_DATA_DIR / "inps_gestioni_previdenziali.csv",
    ],
    "pensionati_per_gestione_professione": [
        RAW_DATA_DIR / "inps_pensionati" / "pensionati_per_gestione.csv",
        CLEAN_DATA_DIR / "pensionati_per_gestione_professione.csv",
    ],
}


def normalize_text(value: object) -> str:
    """Normalizza una stringa per confronti robusti sui nomi delle gestioni."""
    if value is None or pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.lower().replace("-", " ").replace("_", " ").split())


def with_schema(table: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Allinea una tabella allo schema finale registrato."""
    schema = FINAL_TABLE_SCHEMAS[table_name]
    if table.empty:
        return pd.DataFrame(columns=schema)
    result = table.copy()
    for column in schema:
        if column not in result.columns:
            result[column] = pd.NA
    return result[schema]


def first_available(paths: list[Path]) -> tuple[pd.DataFrame, str]:
    """Legge il primo CSV disponibile e non vuoto da una lista di percorsi."""
    for path in paths:
        table = read_csv_optional(path)
        if not table.empty:
            return table, str(path)
    return pd.DataFrame(), ""


def read_mapping(path: str | Path = MAPPING_GESTIONI_PROFESSIONI_INPS_PATH) -> pd.DataFrame:
    """Legge il mapping gestione INPS -> categoria professionale normalizzata."""
    mapping = read_csv_optional(path)
    required = ["gestione_id", "gestione_nome", "parole_chiave", "categoria_professionale", "criterio_classificazione", "priorita"]
    for column in required:
        if column not in mapping.columns:
            mapping[column] = pd.Series(dtype=str)
    if not mapping.empty:
        mapping["priorita"] = pd.to_numeric(mapping["priorita"], errors="coerce").fillna(9999)
        mapping = mapping.sort_values(["priorita", "gestione_id"], na_position="last")
    return mapping


def classify_gestione(gestione_id: object, gestione_nome: object, mapping: pd.DataFrame) -> dict[str, str]:
    """Classifica una gestione o fondo INPS usando mapping esplicito e parole chiave."""
    text = normalize_text(f"{gestione_id} {gestione_nome}")
    if text == "" or mapping.empty:
        return {"categoria_professionale": "non_classificabile", "criterio_classificazione": "gestione_mancante_o_mapping_non_disponibile"}

    for _, row in mapping.iterrows():
        keys = [row.get("gestione_id"), row.get("gestione_nome"), *split_semicolon(row.get("parole_chiave"))]
        normalized_keys = [normalize_text(key) for key in keys if normalize_text(key)]
        if any(key in text for key in normalized_keys):
            return {
                "categoria_professionale": str(row.get("categoria_professionale", "non_classificabile")),
                "criterio_classificazione": str(row.get("criterio_classificazione", "gestione_previdenziale")),
            }
    return {"categoria_professionale": "non_classificabile", "criterio_classificazione": "nessuna_regola_mapping"}


def apply_professional_mapping(table: pd.DataFrame, table_name: str, mapping: pd.DataFrame) -> pd.DataFrame:
    """Aggiunge categoria professionale e criterio di classificazione quando mancano."""
    result = with_schema(table, table_name)
    if result.empty:
        return result
    has_category = "categoria_professionale" in result.columns
    has_criterion = "criterio_classificazione" in result.columns
    if not has_category and not has_criterion:
        return result

    categories = []
    criteria = []
    for _, row in result.iterrows():
        classified = classify_gestione(row.get("gestione_id"), row.get("gestione_nome"), mapping)
        categories.append(classified["categoria_professionale"])
        criteria.append(classified["criterio_classificazione"])

    if has_category:
        result["categoria_professionale"] = result["categoria_professionale"].fillna(pd.Series(categories, index=result.index))
        result.loc[result["categoria_professionale"].astype(str).str.strip().eq(""), "categoria_professionale"] = pd.Series(categories, index=result.index)
    if has_criterion:
        result["criterio_classificazione"] = result["criterio_classificazione"].fillna(pd.Series(criteria, index=result.index))
        result.loc[result["criterio_classificazione"].astype(str).str.strip().eq(""), "criterio_classificazione"] = pd.Series(criteria, index=result.index)
    return result


def build_table(table_name: str, mapping: pd.DataFrame) -> tuple[pd.DataFrame, str, str]:
    """Costruisce una delle tabelle specialistiche da raw/clean se disponibile."""
    raw, source_path = first_available(RAW_INPUTS[table_name])
    if raw.empty:
        return with_schema(pd.DataFrame(), table_name), source_path, "schema_pronto_raw_assente"
    if table_name in {"inps_gestioni_previdenziali", "pensionati_per_gestione_professione"}:
        result = apply_professional_mapping(raw, table_name, mapping)
    else:
        result = with_schema(raw, table_name)
    return result, source_path, "dati_trasformati"


def build_inps_balance_and_professional_distribution(log_path: str | Path = LOG_PATHS["inps_balance_profession"]) -> pd.DataFrame:
    """Costruisce le tabelle per bilancio INPS e pensionati per gestione/professione.

    La funzione lavora in modo conservativo. Se i file raw o clean non sono ancora
    presenti, crea comunque gli schemi finali e registra nel log che i dati devono
    essere scaricati o estratti dai documenti INPS.
    """
    prepare_directories()
    mapping = read_mapping()
    rows: list[dict[str, object]] = []
    for table_name in RAW_INPUTS:
        table, source_path, status = build_table(table_name, mapping)
        save_table(table, FINAL_TABLE_PATHS[table_name])
        rows.append(
            {
                "fase": "inps_balance_profession",
                "tabella": table_name,
                "righe": len(table),
                "percorso_output": str(FINAL_TABLE_PATHS[table_name]),
                "percorso_input": source_path,
                "stato": status,
                "note": "popolare output/data/raw o output/data/clean con le estrazioni INPS" if table.empty else "",
            }
        )
    log = pd.DataFrame(rows)
    save_table(log, log_path)
    return log


if __name__ == "__main__":
    build_inps_balance_and_professional_distribution()
