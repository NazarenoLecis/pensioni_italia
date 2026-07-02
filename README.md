# pensioni-italia

Repository per scaricare e documentare dati ufficiali sul sistema pensionistico italiano.

## Regole

- Solo funzioni.
- Nessuna classe.
- Nessun argparse.
- Una sola cartella di codice: `code/`.
- Parametri modificabili come variabili o argomenti di funzione.
- Utility in `code/utils.py`.
- Download complessivo in `code/download_all.py`.
- Download per categoria in file separati.

## Struttura

```text
pensioni-italia/
  code/
    utils.py
    inps_open_data.py
    openbdap_public_finance.py
    istat_data.py
    eurostat_data.py
    url_resources.py
    download_all.py
  metadata/
  data/
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

Le whitelist in `metadata/` decidono cosa scaricare. I dati raw e processed restano locali.
