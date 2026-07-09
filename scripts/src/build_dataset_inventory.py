from __future__ import annotations

from html import unescape
from pathlib import Path
import re
import sys

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from config import CACHE_DATA_DIR, LOG_DATA_DIR, METADATA_DIR
from utils import clean_text, prepare_directories, save_table, split_semicolon


CATALOG_PATH = CACHE_DATA_DIR / "inps_opendata_catalog_filtrato.csv"
INVENTORY_PATH = METADATA_DIR / "elenco_datasets.csv"
DOC_PATH = Path(__file__).resolve().parents[2] / "docs" / "elenco_datasets.md"
LOG_PATH = LOG_DATA_DIR / "log_dataset_inventory.csv"


TOPIC_RULES = [
    ("aliquote_contributive", ["aliquot"]),
    ("contributi_entrate", ["entrate contributive", "contributi versati", "contribuzione", "flussi contributivi"]),
    ("spesa_pensionistica", ["spesa", "importo complessivo", "ammontare", "reddito pensionistico"]),
    ("numero_pensioni", ["numero pensioni", "pensioni vigenti", "andamento numero pensioni"]),
    ("pensionati_reddito", ["numero pensionati", "beneficiari", "reddito pensionistico", "casellario"]),
    ("distribuzione_importi", ["classi di importo", "classe di importo", "scaglioni"]),
    ("gestioni_professioni", ["gestione", "artigiani", "commercianti", "dipendenti pubblici", "lavoratori dipendenti", "coltivatori", "gestione separata"]),
    ("flussi_pensionamento", ["liquidate", "decorrenza", "nuove pensioni"]),
    ("bilancio_inps", ["bilancio", "rendiconto", "conto economico", "gias"]),
    ("demografia_lavoro", ["lavoratori", "iscritti", "aziende", "dipendenti"]),
]

ANALYSIS_BY_TOPIC = {
    "aliquote_contributive": "Serie storica aliquote IVS/contributive per gestione; confronto 33% dipendenti e aliquote autonomi.",
    "contributi_entrate": "Serie storica entrate contributive o contributi versati, da distinguere dalle aliquote.",
    "spesa_pensionistica": "Serie storica spesa/importi pensionistici e confronto tra prestazioni, reddito pensionistico e perimetri INPS/Casellario.",
    "numero_pensioni": "Serie storica trattamenti: pensioni vigenti, previdenziali, assistenziali e categorie.",
    "pensionati_reddito": "Numero pensionati, reddito pensionistico complessivo, pluripensioni e importi medi per persona.",
    "distribuzione_importi": "Distribuzione per classe di importo dei trattamenti e dei redditi pensionistici delle persone.",
    "gestioni_professioni": "Ripartizione per gestione/fondo e ricostruzione di ex dipendenti privati, pubblici, autonomi, artigiani, commercianti.",
    "flussi_pensionamento": "Nuove pensioni liquidate, eta media, canali e dinamica degli ingressi.",
    "bilancio_inps": "Entrate contributive, prestazioni, trasferimenti, saldi e separazione previdenza/assistenza.",
    "demografia_lavoro": "Base per rapporto tra occupati/iscritti e pensionati.",
    "altro": "Dataset potenzialmente utile da classificare manualmente.",
}

TARGET_DASHBOARD_TOPICS = {
    "aliquote_contributive",
    "contributi_entrate",
    "spesa_pensionistica",
    "numero_pensioni",
    "pensionati_reddito",
    "distribuzione_importi",
    "gestioni_professioni",
    "bilancio_inps",
}


def normalize_text(value: object) -> str:
    text = unescape(clean_text(value)).lower()
    text = text.replace("\ufffd", " ")
    return re.sub(r"\s+", " ", text).strip()


def first_match_topic(text: str) -> str:
    for topic, needles in TOPIC_RULES:
        if any(needle in text for needle in needles):
            return topic
    return "altro"


def csv_urls(value: object) -> list[str]:
    return [url for url in split_semicolon(value) if ".csv" in url.lower()]


def xml_urls(value: object) -> list[str]:
    return [url for url in split_semicolon(value) if ".xml" in url.lower()]


def xls_urls(value: object) -> list[str]:
    return [url for url in split_semicolon(value) if ".xls" in url.lower() or ".xlsx" in url.lower()]


def extract_years(text: str) -> str:
    years = sorted({int(match) for match in re.findall(r"\b(?:19|20)\d{2}\b", text)})
    if not years:
        return ""
    if len(years) == 1:
        return str(years[0])
    return f"{years[0]}-{years[-1]}"


def dashboard_priority(topic: str, text: str) -> str:
    if topic in {"aliquote_contributive", "contributi_entrate"}:
        return "alta"
    if topic in {"spesa_pensionistica", "numero_pensioni", "pensionati_reddito", "distribuzione_importi"}:
        return "alta"
    if topic in {"gestioni_professioni", "bilancio_inps"}:
        return "media_alta"
    if topic == "flussi_pensionamento":
        return "media"
    if "pension" in text or "contribut" in text:
        return "media"
    return "bassa"


def readiness(row: pd.Series, topic: str) -> str:
    if row["csv_url"]:
        if topic in TARGET_DASHBOARD_TOPICS:
            return "scaricabile_da_valutare"
        return "scaricabile"
    if row["xls_url"] or row["xml_url"]:
        return "formato_disponibile_da_convertire"
    return "solo_metadati"


def build_inventory(catalog_path: Path = CATALOG_PATH) -> pd.DataFrame:
    if not catalog_path.exists():
        from discover_inps_opendata_catalog import run_discovery

        run_discovery()
    if not catalog_path.exists():
        raise FileNotFoundError(f"Catalogo INPS non trovato: {catalog_path}.")
    catalog = pd.read_csv(catalog_path)
    rows = []
    for _, source_row in catalog.iterrows():
        text = normalize_text(
            " ".join(
                [
                    clean_text(source_row.get("name")),
                    clean_text(source_row.get("title")),
                    clean_text(source_row.get("notes")),
                    clean_text(source_row.get("tags")),
                ]
            )
        )
        topic = first_match_topic(text)
        csv = csv_urls(source_row.get("resource_urls"))
        xls = xls_urls(source_row.get("resource_urls"))
        xml = xml_urls(source_row.get("resource_urls"))
        row = {
            "dataset_id": clean_text(source_row.get("dataset_id")),
            "name": clean_text(source_row.get("name")),
            "titolo": unescape(clean_text(source_row.get("title"))),
            "ambito_dashboard": topic,
            "priorita_dashboard": dashboard_priority(topic, text),
            "anni_titolo": extract_years(text),
            "formati": clean_text(source_row.get("resource_formats")),
            "csv_url": csv[0] if csv else "",
            "xls_url": xls[0] if xls else "",
            "xml_url": xml[0] if xml else "",
            "pagina_inps": clean_text(source_row.get("download_url")),
            "termini_trovati": clean_text(source_row.get("termini_trovati")),
            "analisi_possibili": ANALYSIS_BY_TOPIC.get(topic, ANALYSIS_BY_TOPIC["altro"]),
            "stato_uso": "",
            "note": "",
        }
        row["stato_uso"] = readiness(pd.Series(row), topic)
        rows.append(row)

    manual_rows = [
        {
            "dataset_id": "normativa_aliquote_ivs_lavoro_dipendente",
            "name": "aliquote-ivs-lavoro-dipendente-ordinario",
            "titolo": "Serie storica aliquota IVS lavoro dipendente ordinario",
            "ambito_dashboard": "aliquote_contributive",
            "priorita_dashboard": "alta",
            "anni_titolo": "",
            "formati": "normativa; circolari INPS; tabelle storiche da ricostruire",
            "csv_url": "",
            "xls_url": "",
            "xml_url": "",
            "pagina_inps": "",
            "termini_trovati": "aliquota contributiva IVS; 33%; FPLD",
            "analisi_possibili": ANALYSIS_BY_TOPIC["aliquote_contributive"],
            "stato_uso": "da_popolare_da_fonti_normative",
            "note": "Il 33% e' l'aliquota IVS standard per lavoro dipendente, ma la serie storica va ricostruita per anno e gestione.",
        }
    ]
    inventory = pd.concat([pd.DataFrame(rows), pd.DataFrame(manual_rows)], ignore_index=True)
    priority_order = {"alta": 0, "media_alta": 1, "media": 2, "bassa": 3}
    inventory["_priority_order"] = inventory["priorita_dashboard"].map(priority_order).fillna(9)
    inventory = inventory.sort_values(["_priority_order", "ambito_dashboard", "anni_titolo", "titolo"]).drop(columns=["_priority_order"])
    return inventory


def write_markdown_summary(inventory: pd.DataFrame, path: Path = DOC_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    counts = (
        inventory.groupby(["ambito_dashboard", "priorita_dashboard"], dropna=False)
        .size()
        .reset_index(name="dataset")
        .sort_values(["ambito_dashboard", "priorita_dashboard"])
    )
    high = inventory[inventory["priorita_dashboard"].isin(["alta", "media_alta"])].head(80)
    lines = [
        "# Elenco dataset pensioni",
        "",
        "Inventario derivato dal catalogo Open Data INPS filtrato e da alcune fonti da ricostruire manualmente.",
        "Il file operativo completo e' `metadata/elenco_datasets.csv`.",
        "",
        "## Conteggio per ambito",
        "",
        "| Ambito | Priorita | Dataset |",
        "|---|---:|---:|",
    ]
    for _, row in counts.iterrows():
        lines.append(f"| {row['ambito_dashboard']} | {row['priorita_dashboard']} | {int(row['dataset'])} |")
    lines.extend([
        "",
        "## Dataset ad alta priorita",
        "",
        "| Ambito | Anni | Titolo | Stato |",
        "|---|---:|---|---|",
    ])
    for _, row in high.iterrows():
        title = str(row["titolo"]).replace("|", "\\|")
        lines.append(f"| {row['ambito_dashboard']} | {row['anni_titolo']} | {title} | {row['stato_uso']} |")
    lines.extend([
        "",
        "## Lettura per dashboard",
        "",
        "- La dashboard principale deve usare dati trasformati nelle tabelle finali, non direttamente questo inventario.",
        "- `pensioni` indica trattamenti; `pensionati` o `beneficiari` indica persone.",
        "- La distribuzione dei trattamenti per classe di importo non misura il reddito pensionistico complessivo della persona.",
        "- La serie storica dell'aliquota IVS per dipendenti ordinari e' segnata come fonte da ricostruire, distinta dalle aliquote per autonomi disponibili nei CSV INPS.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def run_dataset_inventory() -> pd.DataFrame:
    prepare_directories([METADATA_DIR, LOG_DATA_DIR, DOC_PATH.parent])
    inventory = build_inventory()
    save_table(inventory, INVENTORY_PATH)
    write_markdown_summary(inventory)
    log = pd.DataFrame(
        [
            {
                "fase": "dataset_inventory",
                "righe": len(inventory),
                "percorso_csv": str(INVENTORY_PATH),
                "percorso_doc": str(DOC_PATH),
                "stato": "ok",
            }
        ]
    )
    save_table(log, LOG_PATH)
    return inventory


if __name__ == "__main__":
    result = run_dataset_inventory()
    print(
        result.groupby(["ambito_dashboard", "priorita_dashboard"])
        .size()
        .reset_index(name="dataset")
        .to_string(index=False)
    )
