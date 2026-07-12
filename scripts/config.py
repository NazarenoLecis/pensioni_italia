from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
SRC_DIR = SCRIPTS_DIR / "src"
METADATA_DIR = PROJECT_ROOT / "metadata"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DATA_DIR = OUTPUT_DIR / "data"
OUTPUT_CHARTS_DIR = OUTPUT_DIR / "charts"
RAW_DATA_DIR = OUTPUT_DATA_DIR / "raw"
CLEAN_DATA_DIR = OUTPUT_DATA_DIR / "clean"
FINAL_DATA_DIR = OUTPUT_DATA_DIR / "final"
CACHE_DATA_DIR = OUTPUT_DATA_DIR / "cache"
LOG_DATA_DIR = OUTPUT_DATA_DIR / "logs"

DIRECTORIES = [OUTPUT_DIR, OUTPUT_DATA_DIR, OUTPUT_CHARTS_DIR, RAW_DATA_DIR, CLEAN_DATA_DIR, FINAL_DATA_DIR, CACHE_DATA_DIR, LOG_DATA_DIR]

REGISTRO_FONTI_PATH = METADATA_DIR / "registro_fonti.csv"
DATASET_ATTESI_PATH = METADATA_DIR / "dataset_attesi.csv"
OUTPUT_ANALITICI_PATH = METADATA_DIR / "output_analitici.csv"
ANALISI_DA_IMPLEMENTARE_PATH = METADATA_DIR / "analisi_da_implementare.csv"
DEFINIZIONI_INDICATORI_PATH = METADATA_DIR / "definizioni_indicatori.csv"
DOMANDE_LIVE_PATH = METADATA_DIR / "domande_live.csv"
ELENCO_DATASETS_PATH = METADATA_DIR / "elenco_datasets.csv"
SCENARI_CALCOLATORE_PATH = PROJECT_ROOT / "calcolatore" / "metadata" / "scenari_calcolatore_pensione_pagata.csv"
TERMINI_RICERCA_INPS_PATH = METADATA_DIR / "termini_ricerca_inps.csv"
WHITELIST_INPS_PATH = METADATA_DIR / "whitelist_inps.csv"
WHITELIST_OPENBDAP_PATH = METADATA_DIR / "whitelist_openbdap.csv"
WHITELIST_ISTAT_PATH = METADATA_DIR / "whitelist_istat.csv"
WHITELIST_EUROSTAT_PATH = METADATA_DIR / "whitelist_eurostat.csv"
RISORSE_URL_PATH = METADATA_DIR / "risorse_url.csv"
INPS_BILANCIO_FONTI_PATH = METADATA_DIR / "inps_bilancio_fonti.csv"
MAPPING_GESTIONI_PROFESSIONI_INPS_PATH = METADATA_DIR / "mapping_gestioni_professioni_inps.csv"

FINAL_TABLE_PATHS = {
    "tabella_annuale_pensioni": FINAL_DATA_DIR / "tabella_annuale_pensioni.csv",
    "tabella_gestioni": FINAL_DATA_DIR / "tabella_gestioni.csv",
    "tabella_trasferimenti_inps": FINAL_DATA_DIR / "tabella_trasferimenti_inps.csv",
    "tabella_territoriale": FINAL_DATA_DIR / "tabella_territoriale.csv",
    "tabella_flussi_pensionamento": FINAL_DATA_DIR / "tabella_flussi_pensionamento.csv",
    "tabella_confronto_europeo": FINAL_DATA_DIR / "tabella_confronto_europeo.csv",
    "tabella_distribuzione_pensionati": FINAL_DATA_DIR / "tabella_distribuzione_pensionati.csv",
    "tabella_demografia_lavoro": FINAL_DATA_DIR / "tabella_demografia_lavoro.csv",
    "tabella_previdenza_complementare": FINAL_DATA_DIR / "tabella_previdenza_complementare.csv",
    "tabella_parametri_sistema": FINAL_DATA_DIR / "tabella_parametri_sistema.csv",
    "tabella_copertura_live": FINAL_DATA_DIR / "tabella_copertura_live.csv",
    "inps_bilancio_voci": FINAL_DATA_DIR / "inps_bilancio_voci.csv",
    "inps_gestioni_previdenziali": FINAL_DATA_DIR / "inps_gestioni_previdenziali.csv",
    "pensionati_per_gestione_professione": FINAL_DATA_DIR / "pensionati_per_gestione_professione.csv",
}

ANALYTIC_OUTPUT_PATHS = {
    "calcolatore_pensione_pagata_base": FINAL_DATA_DIR / "calcolatore_pensione_pagata_base.csv",
    "calcolatore_pensione_pagata_carriera": FINAL_DATA_DIR / "calcolatore_pensione_pagata_carriera.csv",
    "calcolatore_pensione_pagata_parametri": FINAL_DATA_DIR / "calcolatore_pensione_pagata_parametri.csv",
    "calcolatore_pensione_pagata_coefficienti": FINAL_DATA_DIR / "calcolatore_pensione_pagata_coefficienti.csv",
    "calcolatore_pensione_pagata_categorie": FINAL_DATA_DIR / "calcolatore_pensione_pagata_categorie.csv",
    "calcolatore_pensione_pagata_mortalita": FINAL_DATA_DIR / "calcolatore_pensione_pagata_mortalita.csv",
    "calcolatore_pensione_pagata_ccnl": FINAL_DATA_DIR / "calcolatore_pensione_pagata_ccnl.csv",
}

LOG_PATHS = {
    "pipeline": LOG_DATA_DIR / "log_pipeline.csv",
    "download": LOG_DATA_DIR / "log_download.csv",
    "cleaning": LOG_DATA_DIR / "log_cleaning.csv",
    "build_indicators": LOG_DATA_DIR / "log_build_indicators.csv",
    "quality": LOG_DATA_DIR / "log_quality_checks.csv",
    "coverage": LOG_DATA_DIR / "log_live_coverage.csv",
    "charts": LOG_DATA_DIR / "log_charts.csv",
    "inps_balance_profession": LOG_DATA_DIR / "log_inps_balance_profession.csv",
    "opendata_discovery": LOG_DATA_DIR / "log_inps_opendata_discovery.csv",
    "dataset_inventory": LOG_DATA_DIR / "log_dataset_inventory.csv",
    "contribution_rates": LOG_DATA_DIR / "log_contribution_rates.csv",
    "dashboard_core": LOG_DATA_DIR / "log_dashboard_core.csv",
}
