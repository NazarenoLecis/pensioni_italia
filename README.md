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
    tabelle_finali.py
    costruisci_tabelle_finali.py
    trasforma_dati.py
    controlli_qualita.py
    scarica_tutto.py
    analisi.py
    esegui_pipeline.py
  metadata/
    registro_fonti.csv
    dizionario_dati.csv
    termini_ricerca_inps.csv
    whitelist_inps.csv
    whitelist_openbdap.csv
    whitelist_istat.csv
    whitelist_eurostat.csv
    risorse_url.csv
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

## Esecuzione completa

```bash
python code/esegui_pipeline.py
```

Questo esegue scaricamento, trasformazione verso tabelle finali, controlli di qualita' e analisi grafica.

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

## Tabelle finali

```bash
python code/costruisci_tabelle_finali.py
python code/trasforma_dati.py
```

Le tabelle finali sono dataset puliti e coerenti, costruiti a partire dai dati grezzi scaricati dalle fonti ufficiali. Sono le tabelle usate dall'analisi, dai grafici e da eventuali dashboard.

## Controlli qualita'

```bash
python code/controlli_qualita.py
```

I controlli verificano presenza dei dati, colonne attese, duplicati, anni validi e valori numerici.

## Analisi e grafici

```bash
python code/analisi.py
```

L'analisi legge le tabelle finali in `data/final/` e salva i grafici in `outputs/charts/`.

## Metodologia

### 1. Discovery

La discovery identifica dataset potenzialmente rilevanti nelle fonti ufficiali. Per INPS il punto di partenza e' il catalogo Open Data interrogato tramite `italian_our_world_data`. La discovery produce candidati, non dataset finali. I risultati vanno controllati prima dell'uso.

Output principale per INPS:

```text
metadata/candidati_catalogo_inps.csv
```

La discovery usa i termini in:

```text
metadata/termini_ricerca_inps.csv
```

### 2. Whitelist

I dataset verificati vengono inseriti nelle whitelist in `metadata/`:

```text
metadata/whitelist_inps.csv
metadata/whitelist_openbdap.csv
metadata/whitelist_istat.csv
metadata/whitelist_eurostat.csv
metadata/risorse_url.csv
```

Le whitelist decidono cosa scaricare. I dataset non verificati restano fuori dal flusso.

### 3. Download

I dati grezzi vengono salvati in `data/raw/`. Questa cartella e' ignorata da Git. I dati grezzi devono essere rigenerabili dalle fonti ufficiali.

### 4. Pulizia e normalizzazione

Le trasformazioni intermedie vanno in `data/processed/`. Questa cartella e' ignorata da Git. Serve per lavorare localmente senza versionare file pesanti o instabili.

### 5. Tabelle finali

I dataset finali, piccoli e documentati, possono essere salvati in `data/final/`. Prima di versionarli bisogna avere fonte, data di estrazione, definizione e dizionario dati.

Tabelle finali previste:

```text
data/final/tabella_annuale_pensioni.csv
data/final/tabella_gestioni.csv
data/final/tabella_territoriale.csv
data/final/tabella_flussi_pensionamento.csv
data/final/tabella_confronto_europeo.csv
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

## Cosa resta da fare manualmente

Le whitelist devono essere popolate con dataset effettivamente verificati. Questa parte richiede una scelta metodologica sui dataset da includere e sui perimetri da usare.

## Flusso operativo

1. Popolare le whitelist in `metadata/`.
2. Eseguire `python code/esegui_pipeline.py`.
3. Controllare i log in `data/processed/` e `data/final/`.
4. Verificare i grafici in `outputs/charts/`.

I dati raw e processed restano locali. I grafici generati restano in `outputs/charts/` e non vengono versionati, salvo scelta esplicita.