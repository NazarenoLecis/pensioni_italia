# Bilancio INPS e distribuzione professionale dei pensionati

Questo blocco separa due piani diversi.

Il bilancio INPS misura voci contabili. Le fonti principali sono rendiconti generali, bilanci preventivi, flussi finanziari, rendiconti delle gestioni e dei fondi amministrati, Open Data e rapporti annuali. Ogni numero deve conservare anno, documento, sezione, tabella o pagina, voce originale, voce normalizzata, perimetro e unita di misura.

La distribuzione professionale dei pensionati non deve essere trattata come professione anagrafica osservata direttamente quando la fonte fornisce solo la gestione previdenziale o il fondo. In quel caso la variabile corretta e' la gestione o il fondo di erogazione, riclassificata in categorie leggibili.

## Tabelle aggiunte

`output/data/final/inps_bilancio_voci.csv` contiene le voci di bilancio normalizzate. Le macro-aree minime sono entrate contributive, trasferimenti pubblici, prestazioni pensionistiche, prestazioni assistenziali, spese di funzionamento, altre entrate o uscite e poste patrimoniali.

`output/data/final/inps_gestioni_previdenziali.csv` contiene indicatori per gestione o fondo: contributi, prestazioni, trasferimenti, saldi, risultati economici e altre poste quando disponibili.

`output/data/final/pensionati_per_gestione_professione.csv` contiene pensionati, prestazioni, importi complessivi e importi medi per categoria ricostruita da gestione o fondo.

## Mapping professionale

Il mapping operativo e' `metadata/mapping_gestioni_professioni_inps.csv`.

Categorie minime:

- ex_dipendenti_privati
- ex_dipendenti_pubblici
- ex_autonomi_agricoli
- ex_artigiani
- ex_commercianti_imprenditori
- ex_parasubordinati_professionisti_senza_cassa
- ex_liberi_professionisti_con_cassa
- carriere_miste_o_pluripensione
- assistenza_o_sostegno_non_professionale
- non_classificabile

Per i pensionati con piu prestazioni il criterio deve essere dichiarato. Le opzioni operative sono gestione della pensione principale per importo, categoria multipla, oppure esclusione dalle distribuzioni per categoria singola con tabella separata.

## File raw attesi

La pipeline legge, quando presenti, questi file:

```text
output/data/raw/inps_bilancio/inps_bilancio_voci.csv
output/data/raw/inps_bilancio/inps_gestioni_previdenziali.csv
output/data/raw/inps_pensionati/pensionati_per_gestione.csv
```

In assenza dei raw, la pipeline crea gli schemi finali e segnala nel log che i dati devono essere estratti.

## Discovery Open Data INPS

Per cercare dataset INPS compatibili con pensioni, pensionati, bilancio e gestioni:

```bash
python scripts/src/discover_inps_opendata_catalog.py
```

Lo script salva `output/data/cache/inps_opendata_catalog_filtrato.csv`. I dataset verificati vanno poi riportati nelle whitelist operative, mantenendo ID dataset, URL della risorsa, formato e data di accesso.

## Regole di qualita'

Ogni valore numerico deve avere fonte e perimetro. Le prestazioni non vanno sommate ai pensionati. Le prestazioni assistenziali non vanno classificate come ex professione se non esiste un legame contributivo o gestionale. Le casse professionali privatizzate sono fuori dal perimetro INPS ordinario e richiedono fonte separata o Casellario con nota metodologica.
