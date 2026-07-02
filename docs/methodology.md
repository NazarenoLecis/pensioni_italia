# Metodologia

Questo repository tratta le pensioni come un insieme di perimetri statistici e contabili distinti.

La regola operativa e' mantenere separati fonte, definizione e trasformazione. Un indicatore derivato, per esempio spesa pensionistica su PIL, deve dichiarare quale definizione usa al numeratore.

## Livelli del progetto

### 1. Discovery

La discovery identifica i dataset potenzialmente rilevanti nelle fonti ufficiali. Per INPS il punto di partenza e' il catalogo Open Data interrogato tramite `italian_our_world_data`.

Output principale:

```text
metadata/inps_catalogue_candidates.csv
```

La discovery usa `metadata/inps_search_terms.csv`. Il risultato non va considerato automaticamente valido. Serve una revisione manuale dei metadati.

### 2. Whitelist

I dataset verificati vengono inseriti in:

```text
metadata/inps_dataset_whitelist.csv
```

La whitelist deve contenere solo dataset controllati. Lo stato `selected`, `active` o `keep` abilita il download.

### 3. Download

I dati grezzi vengono salvati in:

```text
data/raw/inps/
```

Questa cartella e' ignorata da Git. I dati grezzi possono essere rigenerati dalle fonti ufficiali.

### 4. Pulizia e normalizzazione

Le trasformazioni intermedie vanno in:

```text
data/processed/
```

Anche questa cartella e' ignorata da Git. Serve per lavorare localmente senza versionare file pesanti o instabili.

### 5. Dataset finali

I dataset finali, piccoli e documentati, possono essere salvati in:

```text
data/final/
```

Prima di versionarli bisogna aggiungere dizionario dati, fonte, data di estrazione e definizione.

## Definizioni da non confondere

### Pensioni e pensionati

`pensioni` indica trattamenti. `pensionati` indica persone. Una persona puo' ricevere piu' trattamenti.

### Previdenza e assistenza

Le prestazioni previdenziali sono legate a contribuzione e gestione assicurativa. Le prestazioni assistenziali sono finanziate dalla fiscalita' generale o da trasferimenti pubblici. Invalidita' civile e assegno sociale vanno tenuti separati dalle pensioni previdenziali.

### Spesa INPS, spesa PA e ESSPROS

La spesa pensionistica INPS, la spesa pensionistica delle amministrazioni pubbliche e la spesa ESSPROS non sono la stessa misura. Ogni confronto deve indicare la fonte e il perimetro.

### Lordo e netto

Le pensioni sono normalmente rilevate al lordo. Le analisi sul netto richiedono dati fiscali o simulazioni IRPEF. Il passaggio dal lordo al netto va documentato.

## Pannelli finali previsti

### annual_pensions_panel.csv

Serie annuali nazionali su spesa, contributi, trasferimenti, pensionati, pensioni, occupati, PIL e indicatori derivati.

### schemes_panel.csv

Serie per gestione o fondo: contributi, prestazioni, saldo, trasferimenti, iscritti, pensionati e pensioni.

### territorial_panel.csv

Serie regionali o provinciali su pensioni, pensionati, importi, popolazione e mercato del lavoro.

### pension_flows_panel.csv

Nuove pensioni liquidate, decorrenza, eta', genere, gestione, misura e importi iniziali.

### eu_comparison_panel.csv

Confronti europei da Eurostat/ESSPROS, con definizioni armonizzate.
