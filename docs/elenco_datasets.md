# Elenco dataset pensioni

Inventario derivato dal catalogo Open Data INPS filtrato e da alcune fonti da ricostruire manualmente.
Il file operativo completo e' `metadata/elenco_datasets.csv`.

## Dataset usati dalla dashboard

| Dataset / fonte | Copertura usata | Contenuto |
|---|---:|---|
| Rapporti annuali INPS XVIII-XXII | 2018-2022 | Pensioni vigenti, pensionati e reddito pensionistico complessivo |
| Appendici statistiche INPS XXIII-XXV, capitolo 3 | 2022-2025 | Serie aggiornate, gestioni, distribuzione del reddito pensionistico e tavole 3.15 su eta alla decorrenza |
| Bilanci e Rendiconti generali INPS | 2013-2025 | Entrate contributive accertate |
| Appendici di bilancio INPS XXIII-XXV, tavola 2.4 | 2019-2025 | Trasferimenti dal bilancio dello Stato |
| Open Data INPS ID-5365 e Rendiconti generali INPS, conto economico GIAS | 2015, 2020-2024 | Trasferimenti dal bilancio dello Stato per componente |
| API Osservatori statistici INPS 413 e 416 | 2020-2024 | Pensionati, pensioni, importo medio lordo e tipologia di prestazione per regione |
| Rendiconto sociale INPS 2017-2021 | 2017-2020 | Numero medio annuo degli assicurati e pensionati regionali 2017-2019 |
| Rapporti annuali INPS XXIII e XXIV, lavoratori assicurati | 2014, 2019-2024 | Assicurati INPS, settimane medie lavorate e misura ponderata |
| INPS Open Data, pacchetti 1805, 1812, 1988, 1650 | 2012-2017 | Serie territoriali storiche e distribuzioni granulari per classe di importo |
| INPS Open Data, pacchetti 1225 e 1567 | 2013-2018 | Pensioni vigenti della gestione dipendenti pubblici per chiudere la serie categorie |
| INPS Open Data, pacchetti 1189 e 1580 | 2013-2017 | Pensioni liquidate della gestione dipendenti pubblici per decorrenza, sesso e classe di eta |
| Casellario dei pensionati, report 2024 | 2024 | Pensioni per classe di importo e relativa spesa |
| Eurostat `lfsi_emp_a` | 2010-2025 | Occupati 15-64 anni e rapporto demografico con i pensionati |
| Eurostat `spr_exp_pens` | 2000-2024 | Spesa pensionistica ESSPROS in percentuale del PIL per paese |
| Eurostat `nama_10_gdp` | 2018-2025 | PIL nominale nazionale per rapporto reddito pensionistico/PIL nello stesso anno |
| Eurostat `ilc_pnp3` | 2010-2025 | Tasso di sostituzione aggregato annuale per sesso e paese |
| OCSE, Pensions at a Glance 2025, tavola 8.2 | 2000-2021 | Benchmark Italia e media OCSE: pensioni pubbliche di vecchiaia e superstiti in rapporto al PIL |
| MEF-RGS, Rapporto n. 26/2025, tavola 6.4 | 2010-2070 | Tassi di sostituzione lordi e netti, con proiezioni per profilo lavorativo e copertura previdenziale |
| Eurostat `demo_r_pjanaggr3` | dal 2012 | Popolazione regionale per il rapporto pensionati/popolazione |
| Eurostat `nama_10r_2gdp` | dal 2012 | PIL regionale per il rapporto spesa pensionistica/PIL |

Le serie nazionali 2018-2025 provengono dallo stesso impianto di tavole annuali. I vecchi pacchetti Open Data con perimetri diversi restano nell'inventario e vengono usati solo dove la misura e' coerente e dichiarabile.
La pipeline interroga le API ufficiali quando l'indicatore e' disponibile. Per i pacchetti Open Data usa `package_show` JSON e scarica la risorsa tabellare ufficiale indicata nel metadato quando il dato non e' esposto come JSON tabellare. Non esegue scraping di pagine HTML.
Per i trasferimenti GIAS per componente la scomposizione omogenea e' disponibile nel pacchetto Open Data ID-5365 per il 2015 e nei Rendiconti generali per il 2020-2024; i conti economici GIAS 2016-2019 non espongono la stessa tavola analitica e restano documentati ma non fusi nel barchart.
Il netto mostrato nelle distribuzioni dei pensionati e' una simulazione: IRPEF nazionale, detrazione pensione e addizionali regionali/comunali medie stimate sul lordo medio della fascia. I pensionati non versano contributi previdenziali sulle pensioni, quindi questi non vengono sottratti.

## Conteggio per ambito

| Ambito | Priorita | Dataset |
|---|---:|---:|
| aliquote_contributive | alta | 7 |
| altro | media | 10 |
| bilancio_inps | media_alta | 29 |
| contributi_entrate | alta | 1 |
| flussi_pensionamento | media | 5 |
| gestioni_professioni | media_alta | 102 |
| numero_pensioni | alta | 59 |
| pensionati_reddito | alta | 21 |
| spesa_pensionistica | alta | 37 |

## Dataset ad alta priorita

| Ambito | Anni | Titolo | Stato |
|---|---:|---|---|
| aliquote_contributive |  | Serie storica aliquota IVS lavoro dipendente ordinario | da_popolare_da_fonti_normative |
| aliquote_contributive | 2006-2016 | Numero collaboratori delle aziende agricole di coltivatori diretti divisi per anno, aliquota contributiva e area. Serie storica, anni 2007-2016 | scaricabile_da_valutare |
| aliquote_contributive | 2011-2014 | Lavoratori agricoli autonomi coltivatori diretti - Numero aziende per aliquota contributiva e numero collaboratori 2011-2014 | scaricabile_da_valutare |
| aliquote_contributive | 2012-2014 | Coefficienti e aliquote lavoratori dipendenti senza contributo | scaricabile_da_valutare |
| aliquote_contributive | 2013-2014 | Aliquote contributive Agricoltura XII | scaricabile_da_valutare |
| aliquote_contributive | 2013-2014 | Aliquote contributive artigiani e commercianti | scaricabile_da_valutare |
| aliquote_contributive | 2015-2016 | Lavoratori agricoli autonomi coltivatori diretti - Numero aziende per aliquota contributiva e numero collaboratori 2015 | scaricabile_da_valutare |
| contributi_entrate | 2012-2014 | Gestione separata contributi versati per categoria e genere 2012 | scaricabile_da_valutare |
| numero_pensioni | 1985-2017 | Importo medio mensile (pensioni che percepiscono maggiorazione sociale) e importo medio mensile delle pensioni vigenti per anno, sesso, regione, tipo di importo, categoria e sottocategoria. Serie storica, anni 2013-2017 | scaricabile_da_valutare |
| numero_pensioni | 2006-2017 | Gestione dipendenti pubblici, pensioni liquidate. Serie storica per cassa pensioni. Serie storica mensile, anni 2008-2017 | scaricabile_da_valutare |
| numero_pensioni | 2006-2017 | Gestione dipendenti pubblici, pensioni liquidate. Serie storica per regione della sede INPS. Serie storica mensile, anni 2008-2017 | scaricabile_da_valutare |
| numero_pensioni | 2010-2014 | Gestione dip. pubblici_pensioni liquidate. Serie storica per cassa pensioni 2012-2014 | scaricabile_da_valutare |
| numero_pensioni | 2010-2014 | Gestione dip. pubblici_pensioni liquidate. Serie storica per regione della sede INPS 2012-2014 | scaricabile_da_valutare |
| numero_pensioni | 2010-2017 | Importo medio mensile e numero di pensioni vigenti per tipo di gestione, categoria e sottocategoria. Serie storica, anni 2010-2017 | scaricabile_da_valutare |
| numero_pensioni | 2010-2018 | Gestione dipendenti pubblici, pensioni liquidate. Numero pensioni, importo ed eta media mensile per anno di decorrenza, area sede INPS e cassa pensioni. Serie storica anni 2010-2017 | scaricabile_da_valutare |
| numero_pensioni | 2011-2014 | Andamento numero pensioni Inps previdenziali e assistenziali 2011-2012 | scaricabile_da_valutare |
| numero_pensioni | 2012-2014 | Importi medi mensili prestazioni assistenziali al 31 dicembre 2012  per tipologia e sesso | scaricabile_da_valutare |
| numero_pensioni | 2013-2014 | Gestione dip pubblici_pensioni liquidate. Numero pensioni importo e eta media per anno di decorrenza area sedeINPS e cassa pensioni 2014 | scaricabile_da_valutare |
| numero_pensioni | 2013-2014 | Gestione dip. pubblici_pensioni liquidate. Num pensioni importo medio mensile e eta media per cassa pensioni area sede INPS e categoria 2014 | scaricabile_da_valutare |
| numero_pensioni | 2013-2014 | Gestione dip. pubblici_pensioni liquidate. Numero pensioni e importo medio mensile per anno di decorrenza e categoria 2014 | scaricabile_da_valutare |
| numero_pensioni | 2013-2014 | Gestione dip. pubblici_pensioni liquidate. Numero pensioni e importo medio mensile per anno di decorrenza sesso e classe di eta 2014 | scaricabile_da_valutare |
| numero_pensioni | 2013-2014 | Gestione dip. pubblici_pensioni liquidate. Numero pensioni e importo medio mensile per anno di decorrenza sesso earea sede INPS 2014 | scaricabile_da_valutare |
| numero_pensioni | 2013-2014 | Gestione dip. pubblici_pensioni liquidate. Numero pensioni e importo medio mensile per cassa pensione e anno di pagamento 2014 | scaricabile_da_valutare |
| numero_pensioni | 2013-2014 | Gestione dip. pubblici_pensioni liquidate. Numero pensioni importo medio mensile e eta media per anno di decorrenza e cassa pensioni 2014 | scaricabile_da_valutare |
| numero_pensioni | 2013-2014 | Gestione dip. pubblici_pensioni liquidate. Numero pensioni importo medio mensile e eta media per anno di decorrenza e regione 2014 | scaricabile_da_valutare |
| numero_pensioni | 2013-2014 | Gestione dip. pubblici_pensioni liquidate. Numero pensioni importo medio mensile e eta media per anno di pagamento e regione 2014 | scaricabile_da_valutare |
| numero_pensioni | 2013-2014 | Gestione dip. pubblici_pensioni liquidate. Numero pensioni importo medio mensile e eta media per cassa pensioni e categoria 2014 | scaricabile_da_valutare |
| numero_pensioni | 2013-2014 | Gestione dip. pubblici_pensioni liquidate. Numero pensioni importo medio mensile e eta media per cassa pensioni e sesso 2014 | scaricabile_da_valutare |
| numero_pensioni | 2013-2014 | Gestione dip. pubblici_pensioni liquidate. Numero pensioni importo medio mensile e eta media per categoria anno di pagamento e importo 2014 | scaricabile_da_valutare |
| numero_pensioni | 2013-2014 | Gestione dip. pubblici_pensioni liquidate. Numero pensioni importo medio mensile e eta media per classe di eta e categoria 2014 | scaricabile_da_valutare |
| numero_pensioni | 2013-2014 | Gestione dip. pubblici_pensioni liquidate. Numero pensioni importo medio mensile e eta media per classi di importo e cassa pensioni 2014 | scaricabile_da_valutare |
| numero_pensioni | 2013-2014 | Gestione dip. pubblici_pensioni liquidate. Numero pensioni importo medio mensile e eta media per sesso e classi di eta 2014 | scaricabile_da_valutare |
| numero_pensioni | 2013-2016 | Gestione dip. pubblici_pensioni vigenti. Serie storica per area della sede INPS e sesso 2013-2015 | scaricabile_da_valutare |
| numero_pensioni | 2013-2016 | Gestione dip. pubblici_pensioni vigenti. Serie storica per cassa pensioni e categoria 2013-2015 | scaricabile_da_valutare |
| numero_pensioni | 2013-2017 | Importo medio mensile (pensiooni che percepiscono maggiorazione sociale) e importo medio mensile delle pensioni vigenti di vecchiaia per anno, sesso, gestione, classi di eta e tipo di importo. Serie storica, anni 2013-2017 | scaricabile_da_valutare |
| numero_pensioni | 2013-2018 | Gestione dipendenti pubblici, pensioni vigenti. Serie storica mensile per area della sede INPS e sesso. Anni 2014-2018 | scaricabile_da_valutare |
| numero_pensioni | 2013-2018 | Gestione dipendenti pubblici, pensioni vigenti. Serie storica mensile per cassa pensioni e categoria. Anni 2014-2018 | scaricabile_da_valutare |
| numero_pensioni | 2015-2016 | Gestione dip pubblici_pensioni vigenti. Numero pensioni e importo medio mensile per regione della sede INPS e cassa pensioni 2015 | scaricabile_da_valutare |
| numero_pensioni | 2015-2016 | Gestione dip. pubblici_pensioni vigenti. Importo medio annuo e eta media per cassa pensioni e area della sede INPS 2015 | scaricabile_da_valutare |
| numero_pensioni | 2015-2016 | Gestione dip. pubblici_pensioni vigenti. Numero pensioni e importo medio mensile per area della sede INPS e categoria 2015 | scaricabile_da_valutare |
| numero_pensioni | 2015-2016 | Gestione dip. pubblici_pensioni vigenti. Numero pensioni e importo medio mensile per cassa pensione 2015 | scaricabile_da_valutare |
| numero_pensioni | 2015-2016 | Gestione dip. pubblici_pensioni vigenti. Numero pensioni e importo medio mensile per cassa pensioni e sesso 2015 | scaricabile_da_valutare |
| numero_pensioni | 2015-2016 | Gestione dip. pubblici_pensioni vigenti. Numero pensioni e importo medio mensile per categoria e cassa pensioni 2015 | scaricabile_da_valutare |
| numero_pensioni | 2015-2016 | Gestione dip. pubblici_pensioni vigenti. Numero pensioni e importo medio mensile per classi d'importo e cassa pensioni 2015 | scaricabile_da_valutare |
| numero_pensioni | 2015-2016 | Gestione dip. pubblici_pensioni vigenti. Numero pensioni e importo medio mensile per sesso e categoria 2015 | scaricabile_da_valutare |
| numero_pensioni | 2015-2016 | Gestione dip. pubblici_pensioni vigenti. Numero pensioni e importo medio mensile per sesso e classe di eta 2015 | scaricabile_da_valutare |
| numero_pensioni | 2017 | Gestione dipendenti pubblici -  Numero pensioni liquidate, importo medio mensile, età media per anno di pagamento e di decorrenza e regione (valori assoluti e percentuali). Anno 2017 | scaricabile_da_valutare |
| numero_pensioni | 2017 | Gestione dipendenti pubblici, pensioni liquidate. Numero di pensioni e importo medio mensile e eta media per anno di decorrenza e cassa pensioni. Anno 2017 | scaricabile_da_valutare |
| numero_pensioni | 2017 | Gestione dipendenti pubblici, pensioni liquidate. Numero di pensioni e importo medio mensile e eta media per anno di decorrenza e regione. Anno 2017 | scaricabile_da_valutare |
| numero_pensioni | 2017 | Gestione dipendenti pubblici, pensioni liquidate. Numero di pensioni e importo medio mensile per anno di decorrenza e categoria. Anno 2017 | scaricabile_da_valutare |
| numero_pensioni | 2017 | Gestione dipendenti pubblici, pensioni liquidate. Numero di pensioni e importo medio mensile per anno di decorrenza, sesso e area sede INPS. Anno 2017 | scaricabile_da_valutare |
| numero_pensioni | 2017 | Gestione dipendenti pubblici, pensioni liquidate. Numero di pensioni, importo medio mensile e eta media per cassa pensioni, area sede INPS e categorie. Anno 2017 | scaricabile_da_valutare |
| numero_pensioni | 2017 | Gestione dipendenti pubblici, pensioni liquidate. Numero pensioni, importi medi mensili ed eta media per cassa pensioni e sesso. Anno 2017 | scaricabile_da_valutare |
| numero_pensioni | 2017 | Gestione dipendenti pubblici, pensioni liquidate. Numero pensioni, importi medi mensili ed eta media per categoria, anno di pagamento ed importo. Anno 2017 | scaricabile_da_valutare |
| numero_pensioni | 2017 | Gestione dipendenti pubblici, pensioni liquidate. Numero pensioni, importi medi mensili ed eta media per classi di eta e categoria. Anno 2017 | scaricabile_da_valutare |
| numero_pensioni | 2017 | Gestione dipendenti pubblici, pensioni liquidate. Numero pensioni, importi medi mensili ed eta media per classi importo e cassa pensioni. Anno 2017 | scaricabile_da_valutare |
| numero_pensioni | 2017 | Gestione dipendenti pubblici, pensioni liquidate. Numero pensioni, importo medio mensile e eta media per classi di eta. Anno 2017 | scaricabile_da_valutare |
| numero_pensioni | 2017 | Gestione dipendenti pubblici, pensioni liquidate. Numero pensioni, importo medio mensile ed eta media per cassa pensioni e categoria. Anno 2017 | scaricabile_da_valutare |
| numero_pensioni | 2017-2018 | Gestione dipendenti pubblici, pensioni vigenti. Importo medio annuo e età media per cassa pensioni e area della sede INPS. Anni 2017, 2018 | scaricabile_da_valutare |
| numero_pensioni | 2017-2018 | Gestione dipendenti pubblici, pensioni vigenti. Numero di pensioni e importo medio mensile per area della sede INPS e categoria. Anni 2017, 2018 | scaricabile_da_valutare |
| numero_pensioni | 2017-2018 | Gestione dipendenti pubblici, pensioni vigenti. Numero di pensioni e importo medio mensile per cassa pensioni e sesso. Anni 2017, 2018 | scaricabile_da_valutare |
| numero_pensioni | 2017-2018 | Gestione dipendenti pubblici, pensioni vigenti. Numero di pensioni e importo medio mensile per cassa pensioni. Anni 2017, 2018 | scaricabile_da_valutare |
| numero_pensioni | 2017-2018 | Gestione dipendenti pubblici, pensioni vigenti. Numero di pensioni e importo medio mensile per categoria e cassa pensioni. Anni 2017, 2018 | scaricabile_da_valutare |
| numero_pensioni | 2017-2018 | Gestione dipendenti pubblici, pensioni vigenti. Numero di pensioni e importo medio mensile per classi importo e cassa pensioni. Anni 2017, 2018 | scaricabile_da_valutare |
| numero_pensioni | 2017-2018 | Gestione dipendenti pubblici, pensioni vigenti. Numero di pensioni e importo medio mensile per sesso e categoria. Anni 2017, 2018 | scaricabile_da_valutare |
| numero_pensioni | 2017-2018 | Gestione dipendenti pubblici, pensioni vigenti. Numero di pensioni e importo medio mensile per sesso e classe di eta. Anni 2017, 2018 | scaricabile_da_valutare |
| numero_pensioni | 2017-2018 | Gestione dipendenti pubblici, pensioni vigenti. Numero pensioni ed importo medio mensile per regione della sede INPS e cassa pensioni. Anni 2017, 2018 | scaricabile_da_valutare |
| pensionati_reddito | 2007-2010 | Lavoratori dipendenti beneficiari di ANF  - Anni 2007-1° semestre 2010 | scaricabile_da_valutare |
| pensionati_reddito | 2007-2010 | Lavoratori dipendenti beneficiari di ANF - Anni 2007-1° semestre 2010 | scaricabile_da_valutare |
| pensionati_reddito | 2010-2014 | Beneficiari congedo parentale gestione separata 2010-2012 | scaricabile_da_valutare |
| pensionati_reddito | 2010-2016 | Numero beneficiari del sistema pensionistico italiano divisi per anno, area, classi di eta, classi di importo. Serie storica anni 2012-2016 | scaricabile_da_valutare |
| pensionati_reddito | 2010-2016 | Numero beneficiari del sistema pensionistico italiano divisi per anno, area, sesso, classi di importo. Serie storica anni 2012-2016 | scaricabile_da_valutare |
| pensionati_reddito | 2010-2016 | Numero beneficiari del sistema pensionistico italiano divisi per anno, area, tipologia e classi di eta. Serie storica anni 2012-2016 | scaricabile_da_valutare |
| pensionati_reddito | 2010-2016 | Numero beneficiari del sistema pensionistico italiano divisi per anno, area, tipologia e sesso. Serie storica anni 2012-2016 | scaricabile_da_valutare |
| pensionati_reddito | 2010-2016 | Numero beneficiari del sistema pensionistico italiano divisi per anno, regione e classi di eta. Serie storica anni 2012-2016 | scaricabile_da_valutare |
| pensionati_reddito | 2010-2016 | Numero beneficiari del sistema pensionistico italiano divisi per anno, regione e sesso. Serie storica anni 2012-2016 | scaricabile_da_valutare |
| pensionati_reddito | 2010-2016 | Numero beneficiari del sistema pensionistico italiano divisi per anno, regione e tipologia. Serie storica anni 2012-2016 | scaricabile_da_valutare |
| pensionati_reddito | 2010-2016 | Numero beneficiari pensioni ai superstiti divisi per anno, area e tipologia. Serie storica anni 2012-2016 | scaricabile_da_valutare |
| pensionati_reddito | 2010-2016 | Numero beneficiari pensioni ai superstiti divisi per anno, regione, sesso e classe di eta. Serie storica anni 2012-2016 | scaricabile_da_valutare |
| pensionati_reddito | 2010-2017 | Numero beneficiari del sistema pensionistico italiano divisi per anno, regione e classi di importo. Anni 2012-2017 | scaricabile_da_valutare |

## Lettura per dashboard

- La dashboard principale deve usare dati trasformati nelle tabelle finali, non direttamente questo inventario.
- `pensioni` indica trattamenti; `pensionati` o `beneficiari` indica persone.
- La distribuzione dei trattamenti per classe di importo non misura il reddito pensionistico complessivo della persona.
- Gli assicurati INPS hanno almeno un contributo o una giornata retribuita nell'anno e sono deduplicati tra gestioni; non sono uno stock medio di occupati equivalenti a tempo pieno. Per avvicinare l'intensita' contributiva vengono esposte anche la misura ponderata per settimane lavorate e, dove disponibile, il numero medio annuo degli assicurati.
- No-tax area e detrazioni riguardano l'IRPEF netta e non implicano, in generale, l'assenza di contribuzione previdenziale.
- Il netto pensionistico stimato non sottrae contributi sociali: la pensione e' tassata ai fini IRPEF e addizionali, ma non genera contribuzione previdenziale a carico del pensionato.
- La serie storica dell'aliquota IVS per dipendenti ordinari e' segnata come fonte da ricostruire, distinta dalle aliquote per autonomi disponibili nei CSV INPS.
