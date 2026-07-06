# pensioni-italia

Repository per scaricare, documentare e analizzare dati ufficiali sul sistema pensionistico italiano.

L'obiettivo e' tenere separati i diversi perimetri statistici e contabili. La spesa pensionistica INPS, la spesa pensionistica delle amministrazioni pubbliche, la spesa ESSPROS, le prestazioni assistenziali e la previdenza complementare misurano cose diverse. Ogni analisi deve indicare fonte, definizione, trasformazione e perimetro.

Il repository include una matrice di copertura per le domande emerse nelle live sulle pensioni. La tabella `metadata/domande_live.csv` collega ogni domanda a tema, indicatore, fonte principale e tabella finale attesa. Lo script `code/copertura_live.py` genera `data/final/tabella_copertura_live.csv` e segnala quali domande hanno dati disponibili e quali restano da popolare.

Il catalogo `metadata/dataset_attesi.csv` definisce i dataset logici da usare: INPS, bilanci INPS, RGS/OpenBDAP, ISTAT, Eurostat, COVIP, MEF finanze, OECD e Normattiva. Le whitelist operative servono solo a collegare questi dataset logici agli ID tecnici o agli URL specifici quando si esegue il download automatico.

## Struttura

```text
pensioni-italia/
  code/
  metadata/
    classificazione_trasferimenti_inps.csv
  notebooks/
    01_overview.ipynb
    02_dataset_and_coverage.ipynb
    03_pensioni_demografia_lavoro.ipynb
    04_previdenza_complementare_confronti.ipynb
    05_trasferimenti_e_distribuzioni.ipynb
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

## Notebook esplorativi

I notebook sono pensati per utenti che vogliono capire il repository senza partire dagli script. Contengono spiegazioni, parametri modificabili, controlli e codice commentato. Funzionano anche quando le tabelle finali sono ancora vuote.

Ordine consigliato:

```text
notebooks/01_overview.ipynb
notebooks/02_dataset_and_coverage.ipynb
notebooks/03_pensioni_demografia_lavoro.ipynb
notebooks/04_previdenza_complementare_confronti.ipynb
notebooks/05_trasferimenti_e_distribuzioni.ipynb
```

## Metodologia

La discovery identifica dataset potenzialmente rilevanti. Il catalogo `metadata/dataset_attesi.csv` definisce i dataset logici necessari per rispondere alle domande. Le whitelist in `metadata/` collegano questi dataset logici agli ID tecnici o agli URL specifici della fonte. I dati grezzi vengono salvati in `data/raw/`. Le trasformazioni intermedie vanno in `data/processed/`. Le tabelle finali stanno in `data/final/` e alimentano analisi, grafici e dashboard.

Le definizioni delle prestazioni seguono la classificazione ufficiale della fonte quando disponibile. Per INPS, la tabella `metadata/classificazione_prestazioni_inps.csv` separa IVS, vecchiaia, anticipate, invalidita previdenziale, superstiti, assegno sociale, invalidita civile, accompagnamento, fondo casalinghe, pensioni integrative e previdenza complementare.

La scomposizione dei trasferimenti Stato-INPS usa `metadata/classificazione_trasferimenti_inps.csv`. Le categorie analitiche previste sono oneri pensionistici, assistenza, sgravi contributivi, famiglia e inclusione, copertura disavanzi delle gestioni e altro.

Tabelle finali previste:

```text
data/final/tabella_annuale_pensioni.csv
data/final/tabella_gestioni.csv
data/final/tabella_trasferimenti_inps.csv
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

La distribuzione delle pensioni misura i trattamenti per classe di importo. La distribuzione dei pensionati misura le persone per classe di reddito pensionistico complessivo. Le due cose non vanno confuse.

Le prestazioni previdenziali sono legate a contribuzione e gestione assicurativa. Le prestazioni assistenziali sono finanziate dalla fiscalita' generale o da trasferimenti pubblici. Invalidita' civile e assegno sociale vanno tenuti separati dalle pensioni previdenziali.

La spesa pensionistica INPS, la spesa pensionistica delle amministrazioni pubbliche e la spesa ESSPROS non sono la stessa misura. Ogni confronto deve indicare fonte e perimetro.

Le pensioni sono normalmente rilevate al lordo. Le analisi sul netto richiedono dati fiscali o simulazioni IRPEF.

## Stato attuale

Il repository definisce domande, indicatori, fonti attese, dataset logici, schemi finali, notebook esplorativi e controlli. Le whitelist operative collegano i dataset logici agli identificativi tecnici delle API o agli URL scaricabili. Le tabelle finali vengono inizializzate con schema stabile e vengono popolate dalle trasformazioni specifiche.

## Cosa resta da fare

Collegare ogni riga di `metadata/dataset_attesi.csv` agli ID tecnici effettivi nelle whitelist operative quando si vuole attivare il download automatico.

Completare le trasformazioni specifiche da `data/raw/` verso `data/final/` per INPS, RGS/OpenBDAP, ISTAT, Eurostat, COVIP, MEF finanze, OECD e Normattiva.
