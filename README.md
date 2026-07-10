# pensioni-italia

Repository per scaricare, documentare e analizzare dati ufficiali sul sistema pensionistico italiano.

L'obiettivo e' tenere separati i diversi perimetri statistici e contabili. La spesa pensionistica INPS, la spesa pensionistica delle amministrazioni pubbliche, la spesa ESSPROS, le prestazioni assistenziali e la previdenza complementare misurano cose diverse. Ogni analisi deve indicare fonte, definizione, trasformazione e perimetro.

Il repository include una matrice di copertura delle domande emerse nelle live, un catalogo dei dataset logici attesi, una matrice delle analisi pensionistiche da implementare, un calcolatore didattico sulla domanda: mi sono veramente pagato la pensione?, e un blocco dedicato a bilancio INPS e distribuzione dei pensionati per gestione o categoria professionale di provenienza.

## Struttura

```text
pensioni-italia/
  README.md
  requirements.txt

  scripts/
    config.py
    utils.py
    src/
      download_pension_data.py
      clean_pension_data.py
      build_pension_indicators.py
      build_inps_balance_and_professional_distribution.py
      discover_inps_opendata_catalog.py
      build_live_coverage.py
      run_quality_checks.py
      pension_paid_calculator.py
      make_pension_charts.py
      run_pipeline.py

  notebooks/
    01_overview.ipynb
    02_dataset_and_coverage.ipynb
    03_pensioni_demografia_lavoro.ipynb
    04_previdenza_complementare_confronti.ipynb
    05_trasferimenti_e_distribuzioni.ipynb
    06_calcolatore.ipynb

  metadata/
    registro_fonti.csv
    dataset_attesi.csv
    analisi_da_implementare.csv
    output_analitici.csv
    definizioni_indicatori.csv
    domande_live.csv
    temi_dashboard.csv
    classificazione_prestazioni_inps.csv
    classificazione_trasferimenti_inps.csv
    inps_bilancio_fonti.csv
    mapping_gestioni_professioni_inps.csv
    schema_bilancio_professioni_inps.csv
    scenari_calcolatore_pensione_pagata.csv

  docs/
    metodo_bilancio_inps_e_professioni.md

  output/
    data/
      raw/
      clean/
      final/
      cache/
      logs/
    charts/
```

## Installazione

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Esecuzione

Pipeline completa:

```bash
python scripts/src/run_pipeline.py
```

Esecuzione per blocco:

```bash
python scripts/src/download_pension_data.py
python scripts/src/discover_inps_opendata_catalog.py
python scripts/src/build_dataset_inventory.py
python scripts/src/clean_pension_data.py
python scripts/src/build_pension_indicators.py
python scripts/src/build_contribution_rate_history.py
python scripts/src/build_inps_balance_and_professional_distribution.py
python scripts/src/discover_inps_opendata_catalog.py
python scripts/src/build_live_coverage.py
python scripts/src/run_quality_checks.py
python scripts/src/pension_paid_calculator.py
python scripts/src/make_pension_charts.py
```

## Dati e fonti

Le fonti sono registrate in `metadata/registro_fonti.csv`. Il progetto usa o prevede dati da API Osservatori e Open Data INPS, bilanci INPS, OpenBDAP/MEF-RGS, ISTAT, Eurostat, COVIP, MEF Finanze, OECD e Normattiva.

Le estrazioni seguono un criterio API-first: si interrogano gli endpoint ufficiali quando espongono la misura richiesta; solo in assenza del dato si scaricano direttamente file XLSX, CSV o PDF ufficiali. La pipeline non effettua scraping di pagine HTML.

`metadata/dataset_attesi.csv` definisce i dataset logici necessari. Le whitelist operative collegano questi dataset agli ID tecnici o agli URL scaricabili quando si vuole attivare il download automatico.

`metadata/elenco_datasets.csv` e `docs/elenco_datasets.md` inventariano i dataset INPS individuati dal catalogo Open Data, classificandoli per ambito dashboard, priorita', formati disponibili, analisi possibili e stato d'uso. Questo file serve a decidere cosa trasformare nelle tabelle finali senza confondere catalogo e dato gia' pronto.

`metadata/temi_dashboard.csv` sintetizza i principali temi emersi nelle trascrizioni e li collega a domande live e indicatori. Serve al repo di pubblicazione dati per costruire il payload JSON della dashboard senza dipendere dai file di trascrizione locali.

`metadata/inps_bilancio_fonti.csv` censisce rendiconti generali, bilanci preventivi, flussi finanziari, Open Data, API INPS e Rapporto annuale da usare per il blocco bilancio INPS.

`metadata/mapping_gestioni_professioni_inps.csv` collega gestione o fondo INPS a categoria professionale normalizzata. Il mapping non va interpretato come professione anagrafica osservata direttamente se la fonte misura soltanto la gestione previdenziale.

## Output

Tutti i file generati vengono salvati in `output`.

```text
output/data/raw      dati scaricati
output/data/clean    dati puliti
output/data/final    tabelle finali e output analitici
output/data/cache    cataloghi e risultati di discovery
output/data/logs     log della pipeline e controlli
output/charts        grafici e immagini
```

Le principali tabelle finali sono:

```text
tabella_annuale_pensioni.csv
tabella_gestioni.csv
tabella_trasferimenti_inps.csv
tabella_territoriale.csv
tabella_flussi_pensionamento.csv
tabella_confronto_europeo.csv
tabella_distribuzione_pensionati.csv
tabella_demografia_lavoro.csv
tabella_previdenza_complementare.csv
tabella_parametri_sistema.csv
tabella_copertura_live.csv
inps_bilancio_voci.csv
inps_gestioni_previdenziali.csv
pensionati_per_gestione_professione.csv
```

Gli output del calcolatore sono:

```text
calcolatore_pensione_pagata_carriera.csv
calcolatore_pensione_pagata_base.csv
```

## Bilancio INPS e distribuzione professionale

Il blocco aggiunto costruisce tre tabelle:

`inps_bilancio_voci.csv` per le voci di bilancio INPS con anno, documento, tabella o pagina, voce originale, voce normalizzata, macro-area, gestione quando disponibile, importo nominale, unita e deflatore eventuale.

`inps_gestioni_previdenziali.csv` per entrate, uscite, risultati economici, saldi e trasferimenti per gestione o fondo.

`pensionati_per_gestione_professione.csv` per pensionati, prestazioni, importi complessivi e importi medi per categoria professionale ricostruita da gestione o fondo.

Le categorie minime sono ex dipendenti privati, ex dipendenti pubblici, ex autonomi agricoli, ex artigiani, ex commercianti e imprenditori iscritti alla gestione commercianti, ex parasubordinati e professionisti senza cassa iscritti alla Gestione separata, ex liberi professionisti con casse privatizzate quando disponibili da fonte esterna o Casellario, carriere miste, assistenza non professionale e non classificabili.

La documentazione metodologica e' in `docs/metodo_bilancio_inps_e_professioni.md`.

## Aliquote contributive

`scripts/src/build_contribution_rate_history.py` scarica l'allegato INPS "Aliquote storiche", estrae la serie FPLD e popola `tabella_parametri_sistema.csv` con aliquota totale, quota datore e quota lavoratore a fine anno.

La dashboard deve distinguere il valore FPLD storico, che dal 1998 risulta 32,70%, dal riferimento corrente INPS al 33% per l'aliquota contributiva IVS standard degli assicurati al FPLD/AGO. Sono perimetri vicini ma non identici, quindi il testo pubblico deve esplicitarlo.

## Notebook

I notebook sono numerati e pensati per utenti non tecnici. Usano le funzioni in `scripts` e leggono/scrivono da `output`.

`01_overview.ipynb` mostra struttura, fonti, dataset, analisi e output.

`02_dataset_and_coverage.ipynb` controlla coerenza tra dataset, indicatori, output e domande live.

`03_pensioni_demografia_lavoro.ipynb` esplora spesa pensionistica, pensioni, pensionati, occupati e demografia.

`04_previdenza_complementare_confronti.ipynb` esplora previdenza complementare e confronti internazionali.

`05_trasferimenti_e_distribuzioni.ipynb` esplora trasferimenti Stato-INPS e distribuzione di pensioni e pensionati.

`06_calcolatore.ipynb` esegue il calcolatore didattico.

## Metodo

La pipeline segue questa sequenza: preparazione delle cartelle, riepilogo fonti e whitelist, inventario dataset INPS, pulizia dei dati disponibili, costruzione delle tabelle finali, serie storica aliquote contributive, costruzione del blocco INPS bilancio/professioni, copertura delle domande live, controlli di qualita', calcolatore e grafici.

Le funzioni generali stanno in `scripts/utils.py`. Percorsi, nomi file e configurazioni stanno in `scripts/config.py`. Il codice operativo sta in `scripts/src`.

## Definizioni principali

`pensioni` indica trattamenti. `pensionati` indica persone. Una persona puo' ricevere piu' trattamenti.

La distribuzione delle pensioni misura i trattamenti per classe di importo. La distribuzione dei pensionati misura le persone per classe di reddito pensionistico complessivo.

La distribuzione professionale dei pensionati e' una ricostruzione per gestione o fondo di provenienza quando la fonte non osserva direttamente la professione svolta prima della pensione.

Le prestazioni previdenziali sono legate a contribuzione e gestione assicurativa. Le prestazioni assistenziali sono finanziate dalla fiscalita' generale o da trasferimenti pubblici.

La spesa pensionistica INPS, la spesa pensionistica delle amministrazioni pubbliche e la spesa ESSPROS non sono la stessa misura.

## Calcolatore pensione pagata

Il calcolatore in `scripts/src/pension_paid_calculator.py` costruisce una carriera teorica, calcola il montante contributivo simulato, lo divide per la speranza di vita residua e confronta il tasso di sostituzione teorico con quello effettivo o ipotizzato.

Gli scenari modificabili sono in `metadata/scenari_calcolatore_pensione_pagata.csv`. La metrica `quota_pensione_non_coperta` misura la parte della pensione effettiva che eccede la pensione teorica sostenibile nel modello. E' una simulazione didattica, non una stima ufficiale.

## Limitazioni

Le whitelist possono essere vuote o parziali. In quel caso la pipeline crea schemi, log e controlli, ma non produce ancora indicatori empirici completi.

I confronti tra fonti richiedono attenzione al perimetro. INPS, amministrazioni pubbliche ed ESSPROS non misurano la stessa cosa.

Le analisi su netto, IRPEF e reddito complessivo richiedono dati fiscali o simulazioni dedicate.

## Interpretazione

Prima di usare un risultato bisogna controllare fonte, perimetro, anno, unita' di misura, trattamento dei valori mancanti, distinzione tra pensione e pensionato e criterio di classificazione della gestione professionale.
