# pensioni-italia

Repository per scaricare, documentare e analizzare dati ufficiali sul sistema pensionistico italiano.

## Regole

- Solo funzioni.
- Nessuna classe.
- Nessun argparse.
- Una sola cartella di codice: `code/`.
- Parametri modificabili come variabili o argomenti di funzione.
- Utility in `code/utils.py` e `code/chart_utils.py`.
- Download complessivo in `code/download_all.py`.
- Analisi complessiva in `code/analysis_all.py`.
- Download e analisi per categoria in file separati.

## Struttura

```text
pensioni-italia/
  code/
    utils.py
    chart_utils.py
    inps_open_data.py
    openbdap_public_finance.py
    istat_data.py
    eurostat_data.py
    url_resources.py
    panels.py
    build_panels.py
    download_all.py
    analysis_pensions.py
    analysis_all.py
  metadata/
  data/
    raw/
    processed/
    final/
  outputs/
    charts/
  docs/
```

## Installazione

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Download all

```bash
python code/download_all.py
```

## Download per categoria

```bash
python code/inps_open_data.py
python code/openbdap_public_finance.py
python code/istat_data.py
python code/eurostat_data.py
python code/url_resources.py
```

## Pannelli finali

```bash
python code/build_panels.py
```

## Analisi e grafici

```bash
python code/analysis_all.py
```

L'analisi legge i pannelli finali in `data/final/` e salva i grafici in `outputs/charts/`.

Le whitelist in `metadata/` decidono cosa scaricare. I dati raw e processed restano locali.
