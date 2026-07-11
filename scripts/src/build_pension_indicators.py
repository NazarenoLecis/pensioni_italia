from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from config import FINAL_TABLE_PATHS, LOG_PATHS
from utils import prepare_directories, read_csv_optional, save_table

FINAL_TABLE_SCHEMAS = {
    "tabella_annuale_pensioni": ["anno", "indicatore_id", "famiglia_definizione", "fonte_id", "valore", "unita", "area", "note"],
    "tabella_gestioni": ["anno", "gestione_id", "gestione_nome", "gruppo_gestione", "indicatore_id", "fonte_id", "valore", "unita", "note"],
    "tabella_trasferimenti_inps": ["anno", "fonte_id", "perimetro", "voce_id", "voce_nome", "categoria_analitica", "finalita", "gestione_id", "indicatore_id", "valore", "unita", "note"],
    "tabella_territoriale": ["anno", "livello_territoriale", "codice_territorio", "nome_territorio", "categoria_pensione", "indicatore_id", "fonte_id", "valore", "unita", "note"],
    "tabella_flussi_pensionamento": ["anno", "misura", "gestione_id", "sesso", "classe_eta", "indicatore_id", "fonte_id", "valore", "unita", "note"],
    "tabella_confronto_europeo": ["anno", "paese", "indicatore_id", "definizione", "fonte_id", "valore", "unita", "note"],
    "tabella_distribuzione_pensionati": ["anno", "popolazione", "misura_distribuzione", "classe_importo", "classe_importo_min", "classe_importo_max", "classe_eta", "sesso", "territorio", "indicatore_id", "fonte_id", "valore", "unita", "note"],
    "tabella_demografia_lavoro": ["anno", "area", "classe_eta", "sesso", "scenario", "indicatore_id", "fonte_id", "valore", "unita", "note"],
    "tabella_previdenza_complementare": ["anno", "paese", "forma_pensionistica", "indicatore_id", "fonte_id", "valore", "unita", "note"],
    "tabella_parametri_sistema": ["anno", "parametro_id", "sistema", "fonte_id", "valore", "unita", "note"],
    "tabella_copertura_live": ["domanda_id", "tema", "domanda", "stato", "tabella_finale", "indicatore_richiesto", "fonte_principale", "note"],
    "inps_bilancio_voci": ["anno", "fonte_id", "documento", "tipo_documento", "sezione", "tabella_pagina", "gestione_id", "gestione_nome", "voce_originale", "voce_normalizzata", "macro_area", "perimetro", "indicatore_id", "importo_nominale", "unita", "importo_reale", "deflatore", "note"],
    "inps_gestioni_previdenziali": ["anno", "fonte_id", "gestione_id", "gestione_nome", "categoria_professionale", "perimetro", "indicatore_id", "valore", "unita", "documento", "tabella_pagina", "note"],
    "pensionati_per_gestione_professione": ["anno", "fonte_id", "gestione_id", "gestione_nome", "categoria_professionale", "criterio_classificazione", "tipo_pensione", "sesso", "classe_eta", "territorio", "indicatore_id", "pensionati", "prestazioni", "importo_complessivo", "importo_medio_annuo", "importo_medio_mensile", "unita", "duplicazione_teste", "note"],
}


def empty_final_table(table_name: str) -> pd.DataFrame:
    """Restituisce una tabella finale vuota con lo schema registrato."""
    if table_name not in FINAL_TABLE_SCHEMAS:
        raise KeyError(f"Schema non registrato: {table_name}")
    return pd.DataFrame(columns=FINAL_TABLE_SCHEMAS[table_name])


def initialize_final_tables() -> dict[str, str]:
    """Crea le tabelle finali vuote in output/data/final se non sono gia' popolate."""
    prepare_directories()
    written = {}
    for table_name, path in FINAL_TABLE_PATHS.items():
        existing = read_csv_optional(path)
        table = existing if not existing.empty else empty_final_table(table_name)
        written[table_name] = str(save_table(table, path))
    return written


def build_pension_indicators(log_path: str | Path = LOG_PATHS["build_indicators"]) -> pd.DataFrame:
    """Prepara le tabelle finali e registra lo stato delle trasformazioni.

    Le trasformazioni specifiche dalle fonti grezze a indicatori finali vanno
    collegate qui. Per ora la funzione garantisce schemi stabili e log esplicito.
    """
    initialize_final_tables()
    rows = []
    for table_name, path in FINAL_TABLE_PATHS.items():
        table = read_csv_optional(path)
        rows.append(
            {
                "fase": "build_indicators",
                "tabella": table_name,
                "righe": len(table),
                "percorso": str(path),
                "stato": "schema_pronto" if table.empty else "dati_presenti",
            }
        )
    log = pd.DataFrame(rows)
    save_table(log, log_path)
    return log


if __name__ == "__main__":
    build_pension_indicators()
