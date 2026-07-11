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

Per il blocco lavoro la pipeline combina gli occupati 15-64 dell'API Eurostat con i pensionati INPS e scarica dai Rapporti annuali ufficiali la serie degli assicurati INPS. Gli assicurati sono persone con almeno un contributo o una giornata retribuita nell'anno, deduplicate tra gestioni: non coincidono con lo stock medio degli occupati ne' con i contribuenti IRPEF con imposta netta positiva.

`metadata/dataset_attesi.csv` definisce i dataset logici necessari. Le whitelist operative collegano questi dataset agli ID tecnici o agli URL scaricabili quando si vuole attivare il download automatico.

`metadata/elenco_datasets.csv` e `docs/elenco_datasets.md` inventariano i dataset INPS individuati dal catalogo Open Data, classificandoli per ambito dashboard, priorita', formati disponibili, analisi possibili e stato d'uso. Questo file serve a decidere cosa trasformare nelle tabelle finali senza confondere catalogo e dato gia' pronto.

`metadata/temi_dashboard.csv` sintetizza i principali temi emersi nelle trascrizioni e li collega a domande live e indicatori. Serve al repo di pubblicazione dati per costruire il payload JSON della dashboard senza dipendere dai file di trascrizione locali.

`metadata/inps_bilancio_fonti.csv` censisce rendiconti generali, bilanci preventivi, flussi finanziari, Open Data, API INPS e Rapporto annuale da usare per il blocco bilancio INPS.

`metadata/mapping_gestioni_professioni_inps.csv` collega gestione o fondo INPS a categoria professionale normalizzata. Il mapping non va interpretato come professione anagrafica osservata direttamente se la fonte misura soltanto la gestione previdenziale.

## Conoscenza operativa su API e fonti

La pipeline segue un ordine preciso: API ufficiali, metadati Open Data, file tabellari ufficiali, PDF ufficiali solo quando la tabella non e' esposta in forma strutturata. Non vengono lette o raschiate pagine HTML.

### INPS Open Data

Endpoint base: `https://serviziweb2.inps.it/odapi`.

Per i pacchetti Open Data si usa `package_show?id=<package_id>`. La risposta contiene le risorse disponibili, i formati e gli URL ufficiali. Quando esiste una risorsa CSV o XLSX, la pipeline scarica quella risorsa indicata dal metadato. Alcuni pacchetti espongono solo CSV/XML, altri anche XLS.

Pacchetti gia' usati nella dashboard:

- `1650`: pensioni per classi d'importo storiche.
- `1988`: pensionati per regione e classe di reddito pensionistico.
- `1805`, `1812`: spesa e pensionati regionali storici.
- `1225`, `1567`: pensioni vigenti gestione dipendenti pubblici.
- `1189`, `1580`: pensioni liquidate gestione dipendenti pubblici per anno di decorrenza, sesso e classe di eta.
- `917`, `1952`, `1962`, `1973`, `2118`: conti economici generali 2013-2018.
- `1912`: oneri coperti da trasferimenti dal bilancio dello Stato per tipo onere, anno 2015.

Il pacchetto `1912` fornisce la scomposizione GIAS 2015 in oneri pensionistici, mantenimento salario, famiglia, interventi diversi, riduzioni di oneri previdenziali e sgravi. I pacchetti GIAS 2015-2016 e 2019 disponibili nel catalogo sono conti economici netti: utili per audit contabile, ma non sostituiscono la stessa tavola analitica per componenti usata nel barchart.

### API Osservatori statistici INPS

Endpoint base: `https://servizi2.inps.it/servizi/osservatoristatistici/api`.

Chiamate usate:

- `getStrutturaOsservatorio`: schema delle dimensioni e delle misure.
- `getFiltriOsservatorio`: valori ammessi per le dimensioni.
- `getDatiOsservatorio`: dati tabellari per righe, colonne e filtri selezionati.
- `getAllegato`: allegati PDF ufficiali degli osservatori, usato solo quando la tabella richiesta non e' ottenibile via dati strutturati.

Osservatori gia' verificati:

- `413`: beneficiari/pensionati, classi di importo del reddito pensionistico, eta, sesso e territorio.
- `416`: prestazioni/pensioni, classi di importo della singola pensione, eta, sesso, territorio e tipologia della prestazione.

Limite noto: alcune combinazioni granulari con classe d'importo o eta possono restituire "Dati al momento non disponibili" anche se la struttura elenca la dimensione. In questi casi la pipeline usa appendici statistiche XLSX o report ufficiali, mantenendo nota e fonte.

### Appendici statistiche INPS

Le appendici dei Rapporti annuali sono file XLSX ufficiali e hanno un formato stabile per il capitolo 3. Sono usate per:

- Tavola 3.1: pensionati complessivi, pensionati INPS e reddito pensionistico lordo.
- Tavola 3.3: pensionati INPS per classe di eta e sesso, con importo lordo medio mensile.
- Tavola 3.4: pensionati INPS per classe di reddito pensionistico e sesso, con importo annuo complessivo e medio.
- Tavole 3.7/3.9: prestazioni per gestione e ricostruzione delle categorie.
- Tavole 3.15a/3.15b: pensioni di vecchiaia, anzianita/anticipate e prepensionamenti vigenti al 31 dicembre 2025 per anno di decorrenza, eta media alla decorrenza e importo lordo medio mensile. Questa misura non va letta come eta media di tutti i nuovi pensionamenti dell'anno.

### Lordo, netto e simulazioni fiscali

Le fonti INPS della dashboard espongono importi lordi. Il netto nelle distribuzioni dei pensionati e' una simulazione applicata al reddito pensionistico lordo medio della fascia, non un dato individuale osservato. La metodologia applica scaglioni IRPEF nazionali, detrazione per redditi da pensione e una stima media delle addizionali regionali e comunali; non sottrae contributi previdenziali, perche' sulle pensioni non sono dovuti, e non considera altri redditi, oneri deducibili o detraibili e carichi familiari.

### Bilanci, rendiconti e GIAS

Le appendici di bilancio INPS, tavola 2.4, danno trasferimenti dal bilancio dello Stato e contributi per anni recenti. I conti economici Open Data coprono il totale dei trasferimenti anche per anni precedenti.

La mappa regionale usa il totale dei pensionati quando la categoria e' `totale`. Quando si seleziona una categoria, il perimetro passa alle prestazioni dell'Osservatorio 416: vecchiaia, invalidita', superstiti, indennitarie e assistenziali. La voce IVS e' ricostruita sommando vecchiaia, invalidita' e superstiti; di conseguenza i rapporti sulla popolazione indicano prestazioni per residenti, non persone pensionate uniche.

La scomposizione GIAS per componenti arriva da:

- Open Data INPS `1912` per il 2015.
- Rendiconti generali INPS, conto economico GIAS, per 2020-2024.

Non e' stata trovata nel catalogo Open Data una tavola analitica omogenea per il 2016-2019 con le stesse componenti del barchart. I dati esistenti per quegli anni sono conti economici netti o tavole diverse e non vengono fusi per evitare una falsa continuita'.

### Eurostat e OCSE

Eurostat viene letto via JSON-stat e decodificato preservando le dimensioni. Dataset usati:

- `spr_exp_pens`: spesa pensionistica ESSPROS in percentuale del PIL.
- `nama_10_gdp`: PIL nominale nazionale.
- `nama_10r_2gdp`: PIL regionale.
- `demo_r_pjanaggr3`: popolazione regionale.
- `lfsi_emp_a`: occupati 15-64.
- `ilc_pnp3`: tasso di sostituzione aggregato per sesso.

OCSE Pensions at a Glance 2025 viene letto da file XLSX ufficiale `stat.link` per il benchmark su pensioni pubbliche di vecchiaia e superstiti in rapporto al PIL.

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
calcolatore_pensione_pagata_parametri.csv
calcolatore_pensione_pagata_coefficienti.csv
calcolatore_pensione_pagata_categorie.csv
calcolatore_pensione_pagata_mortalita.csv
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

Il calcolatore in `scripts/src/pension_paid_calculator.py` e' la sola implementazione principale. Il file `code/calcolatore_pensione_pagata.py` resta come wrapper di compatibilita' e non contiene logica autonoma.

Il modello costruisce una carriera contributiva anno per anno, calcola i contributi finanziari con aliquota di finanziamento, accredita il montante con aliquota di computo e rivaluta il montante con i tassi annui di capitalizzazione comunicati da ISTAT. La pensione contributiva equivalente e' calcolata applicando il coefficiente di trasformazione per anno ed eta' di pensionamento: non usa piu' la divisione del montante per la speranza di vita residua.

La pensione effettiva e' inserita dall'utente nella dashboard. Il tool confronta quella pensione lorda con un controfattuale interamente contributivo e calcola differenza annua, valore atteso delle prestazioni con tavole di mortalita ISTAT, eta' approssimativa di pareggio e indicatore qualitativo di affidabilita'. Non applica la differenza individuale alla spesa pensionistica nazionale.

Gli scenari modificabili sono in `metadata/scenari_calcolatore_pensione_pagata.csv`. La prima categoria pienamente operativa e' `generica_fpld`; le altre categorie sono presenti nei metadata ma restano sperimentali o disabilitate finche' non sono disponibili serie storiche complete di CCNL, aliquote, minimali e massimali.

Parametri principali:

- aliquote FPLD: `build_contribution_rate_history.py` e `tabella_parametri_sistema.csv`;
- tassi di capitalizzazione del montante: nota ISTAT pubblicata dal Ministero del Lavoro;
- coefficienti di trasformazione: INPS e decreti ministeriali;
- mortalita': tavole ISTAT della popolazione residente;
- retribuzione: input utente, RAL calibrata o profilo generico stimato con affidabilita' inferiore.

## Limitazioni

Le whitelist possono essere vuote o parziali. In quel caso la pipeline crea schemi, log e controlli, ma non produce ancora indicatori empirici completi.

I confronti tra fonti richiedono attenzione al perimetro. INPS, amministrazioni pubbliche ed ESSPROS non misurano la stessa cosa.

Le analisi su netto, IRPEF e reddito complessivo richiedono dati fiscali o simulazioni dedicate.

## Interpretazione

Prima di usare un risultato bisogna controllare fonte, perimetro, anno, unita' di misura, trattamento dei valori mancanti, distinzione tra pensione e pensionato e criterio di classificazione della gestione professionale.
