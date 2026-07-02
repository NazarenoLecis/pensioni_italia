# pensioni-italia

Repository per scaricare, documentare e analizzare dati ufficiali sul sistema pensionistico italiano.

L'obiettivo e' tenere separati i diversi perimetri statistici e contabili. La spesa pensionistica INPS, la spesa pensionistica delle amministrazioni pubbliche, la spesa ESSPROS, le prestazioni assistenziali e la previdenza complementare misurano cose diverse. Ogni analisi deve indicare fonte, definizione, trasformazione e perimetro.

## Struttura

```text
pensioni-italia/
  code/
    utilita.py
    grafici.py
    dati_inps.py
    finanza_pubblica.py
    dati_istat.py
    dati_eurostat.py
    risorse_url.py
    pannelli.py
    costruisci_pannelli.py
    scarica_tutto.py
    analisi_pensioni.py
    analisi_tutto.py
  metadata/
  data/
    raw/
    processed/
    final/
  outputs/
    charts/
```

## Installazione

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Scaricamento completo

```bash
python code/scarica_tutto.py
```

## Scaricamento per categoria

```bash
python code/dati_inps.py
python code/finanza_pubblica.py
python code/dati_istat.py
python code/dati_eurostat.py
python code/risorse_url.py
```

## Pannelli finali

```bash
python code/costruisci_pannelli.py
```

## Analisi e grafici

```bash
python code/analisi_tutto.py
```

L'analisi legge i pannelli finali in `data/final/` e salva i grafici in `outputs/charts/`.

## Metodologia

### 1. Discovery

La discovery identifica dataset potenzialmente rilevanti nelle fonti ufficiali. Per INPS il punto di partenza e' il catalogo Open Data interrogato tramite `italian_our_world_data`. La discovery produce candidati, non dataset finali. I risultati vanno controllati prima dell'uso.

Output principale per INPS:

```text
metadata/inps_catalogue_candidates.csv
```

La discovery usa i termini in:

```text
metadata/inps_search_terms.csv
```

### 2. Whitelist

I dataset verificati vengono inseriti nelle whitelist in `metadata/`. Esempi:

```text
metadata/inps_dataset_whitelist.csv
metadata/openbdap_dataset_whitelist.csv
metadata/istat_dataset_whitelist.csv
metadata/eurostat_whitelist.csv
metadata/url_resources.csv
```

Le whitelist decidono cosa scaricare. Lo stato `selected`, `active` o `keep` abilita il download. I dataset non verificati restano fuori dal flusso.

### 3. Download

I dati grezzi vengono salvati in `data/raw/`. Questa cartella e' ignorata da Git. I dati grezzi devono essere rigenerabili dalle fonti ufficiali.

### 4. Pulizia e normalizzazione

Le trasformazioni intermedie vanno in `data/processed/`. Questa cartella e' ignorata da Git. Serve per lavorare localmente senza versionare file pesanti o instabili.

### 5. Pannelli finali

I dataset finali, piccoli e documentati, possono essere salvati in `data/final/`. Prima di versionarli bisogna avere fonte, data di estrazione, definizione e dizionario dati.

Pannelli previsti:

```text
data/final/annual_pensions_panel.csv
data/final/schemes_panel.csv
data/final/territorial_panel.csv
data/final/pension_flows_panel.csv
data/final/eu_comparison_panel.csv
```

## Definizioni operative

### Pensioni e pensionati

`pensioni` indica trattamenti. `pensionati` indica persone. Una persona puo' ricevere piu' trattamenti.

### Previdenza e assistenza

Le prestazioni previdenziali sono legate a contribuzione e gestione assicurativa. Le prestazioni assistenziali sono finanziate dalla fiscalita' generale o da trasferimenti pubblici. Invalidita' civile e assegno sociale vanno tenuti separati dalle pensioni previdenziali.

### Spesa INPS, spesa PA e ESSPROS

La spesa pensionistica INPS, la spesa pensionistica delle amministrazioni pubbliche e la spesa ESSPROS non sono la stessa misura. Ogni confronto deve indicare la fonte e il perimetro.

### Lordo e netto

Le pensioni sono normalmente rilevate al lordo. Le analisi sul netto richiedono dati fiscali o simulazioni IRPEF. Il passaggio dal lordo al netto va documentato.

## Flusso operativo

1. Aggiornare le whitelist in `metadata/`.
2. Eseguire `python code/scarica_tutto.py`.
3. Costruire o aggiornare i pannelli finali.
4. Eseguire `python code/analisi_tutto.py`.
5. Controllare i log in `data/processed/` e `data/final/`.

I dati raw e processed restano locali. I grafici generati restano in `outputs/charts/` e non vengono versionati, salvo scelta esplicita.