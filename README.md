# pensioni-italia

Repository per scaricare, documentare e analizzare dati ufficiali sul sistema pensionistico italiano.

L'obiettivo e' tenere separati i diversi perimetri statistici e contabili. La spesa pensionistica INPS, la spesa pensionistica delle amministrazioni pubbliche, la spesa ESSPROS, le prestazioni assistenziali e la previdenza complementare misurano cose diverse. Ogni analisi deve indicare fonte, definizione, trasformazione e perimetro.

Il repository ora include una matrice di copertura per le domande emerse nelle live sulle pensioni. La tabella `metadata/domande_live.csv` collega ogni domanda a tema, indicatore, fonte principale e tabella finale attesa. Lo script `code/copertura_live.py` genera `data/final/tabella_copertura_live.csv` e segnala quali domande hanno dati disponibili e quali restano da popolare.

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
    copertura_live.py
    scarica_tutto.py
    analisi.py
    esegui_pipeline.py
  metadata/
    registro_fonti.csv
    dizionario_dati.csv
    definizioni_indicatori.csv
    classificazione_prestazioni_inps.csv
    mappatura_gestioni.csv
    domande_live.csv
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

Esegue scaricamento, trasformazione verso tabelle finali, controllo di copertura delle domande live, controlli di qualita' e analisi grafica.

## Esecuzione per blocco

```bash
python code/scarica_tutto.py
python code/costruisci_tabelle_finali.py
python code/trasforma_dati.py
python code/copertura_live.py
python code/controlli_qualita.py
python code/analisi.py
```

## Metodologia

La discovery identifica dataset potenzialmente rilevanti. Le whitelist in `metadata/` decidono cosa scaricare. I dati grezzi vengono salvati in `data/raw/`. Le trasformazioni intermedie vanno in `data/processed/`. Le tabelle finali stanno in `data/final/` e alimentano analisi, grafici e dashboard.

Le definizioni delle prestazioni seguono la classificazione ufficiale della fonte quando disponibile. Per INPS, la tabella `metadata/classificazione_prestazioni_inps.csv` separa IVS, vecchiaia, anticipate, invalidita previdenziale, superstiti, assegno sociale, invalidita civile, accompagnamento, fondo casalinghe, pensioni integrative e previdenza complementare.

Tabelle finali previste:

```text
data/final/tabella_annuale_pensioni.csv
data/final/tabella_gestioni.csv
data/final/tabella_territoriale.csv
data/final/tabella_flussi_pensionamento.csv
data/final/tabella_confronto_europeo.csv
data/final/tabella_distribuzione_pensionati.csv
data/final/tabella_demografia_lavoro.csv
data/final/tabella_previdenza_complementare.csv
data/final/tabella_parametri_sistema.csv
data/final/tabella_copertura_live.csv
```

## Definizioni operative

`pensioni` indica trattamenti. `pensionati` indica persone. Una persona puo' ricevere piu' trattamenti.

Le prestazioni previdenziali sono legate a contribuzione e gestione assicurativa. Le prestazioni assistenziali sono finanziate dalla fiscalita' generale o da trasferimenti pubblici. Invalidita' civile e assegno sociale vanno tenuti separati dalle pensioni previdenziali.

La spesa pensionistica INPS, la spesa pensionistica delle amministrazioni pubbliche e la spesa ESSPROS non sono la stessa misura. Ogni confronto deve indicare fonte e perimetro.

Le pensioni sono normalmente rilevate al lordo. Le analisi sul netto richiedono dati fiscali o simulazioni IRPEF.

## Stato attuale

Il repository definisce domande, indicatori, fonti attese, schemi finali e controlli. Non contiene ancora dataset verificati nelle whitelist. Le tabelle finali vengono inizializzate con schema stabile e restano vuote finche' non vengono selezionate le fonti ufficiali.

## Cosa resta da fare manualmente

Popolare le whitelist con dataset effettivamente verificati. Questa parte richiede scegliere quali dataset ufficiali usare per ciascuna tabella finale.

Completare le trasformazioni specifiche da `data/raw/` verso `data/final/` per INPS, RGS/OpenBDAP, ISTAT, Eurostat, COVIP e MEF finanze.
