# pensioni-italia

Repository per raccogliere, normalizzare e documentare dati ufficiali sul sistema pensionistico italiano.

L'obiettivo non e' produrre una singola serie di "spesa per pensioni". L'obiettivo e' conservare separatamente le principali definizioni amministrative, statistiche e di contabilita' pubblica, in modo che ogni analisi dichiari chiaramente quale perimetro usa.

## Perimetro

Il repository copre quattro blocchi.

1. Prestazioni pensionistiche e assistenziali erogate in Italia.
2. Contributi, gestioni previdenziali, fondi ed ex fondi.
3. Trasferimenti statali, bilanci INPS e raccordo con la finanza pubblica.
4. Contesto demografico, mercato del lavoro, previdenza complementare e confronti europei.

## Fonti principali

Le fonti censite sono in `metadata/source_catalogue.csv`.

Priorita' iniziali:

- INPS Open Data per pensioni vigenti, pensioni liquidate, gestioni, invalidita' civile, assegni sociali e dataset amministrativi.
- INPS bilanci e rendiconti per conti economici, gestioni, GIAS, trasferimenti e saldi.
- MEF-RGS OpenBDAP per trasferimenti statali, rendiconto, legge di bilancio e classificazioni della spesa.
- ISTAT per pensionati, trattamenti, distribuzioni territoriali, demografia e mercato del lavoro.
- Eurostat ESSPROS per confronti europei sulla protezione sociale.
- COVIP per previdenza complementare.
- MEF Dipartimento Finanze per dichiarazioni fiscali e redditi da pensione.
- Casse professionali per la parte non INPS del primo pilastro.

## Struttura

```text
pensioni-italia/
  data/
    raw/
    processed/
    final/
  docs/
    methodology.md
    data_dictionary.md
  metadata/
    source_catalogue.csv
    inps_search_terms.csv
    inps_dataset_whitelist.csv
    scheme_mapping.csv
    definitions.csv
  notebooks/
  scripts/
  src/pensioni_italia/
```

`data/raw` e `data/processed` sono ignorate da Git. I dataset finali piccoli e documentati possono essere salvati in `data/final` dopo revisione.

## Installazione

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

In alternativa:

```bash
pip install -r requirements.txt
```

## Flusso operativo iniziale

Scoperta dei dataset INPS potenzialmente rilevanti:

```bash
python scripts/01_discover_inps.py --with-metadata
```

Creazione della tabella delle risorse disponibili per i dataset candidati:

```bash
python scripts/02_build_inps_resources.py
```

Download dei dataset selezionati nella whitelist:

```bash
python scripts/03_fetch_inps_selected.py
```

La whitelist sta in `metadata/inps_dataset_whitelist.csv`. All'inizio e' vuota. Va popolata dopo la discovery, inserendo solo dataset verificati.

## Relazione con gli altri repository

`italian_our_world_data` resta la libreria generale per chiamare API pubbliche.

Questo repository usa quella libreria e aggiunge logica specifica sulle pensioni italiane: cataloghi, mapping, definizioni, pulizia e pannelli finali.

`Declino_Italia` puo' consumare i dataset finali di questo repository per grafici e analisi tematiche.
