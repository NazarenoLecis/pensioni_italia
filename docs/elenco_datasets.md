# Elenco dataset pensioni

Inventario derivato dal catalogo Open Data INPS filtrato e da alcune fonti da ricostruire manualmente.
Il file operativo completo e' `metadata/elenco_datasets.csv`.

## Dataset usati dalla dashboard

| Dataset / fonte | Copertura usata | Contenuto |
|---|---:|---|
| Rapporti annuali INPS XVIII-XXII | 2018-2022 | Pensioni vigenti, pensionati e reddito pensionistico complessivo |
| Appendici statistiche INPS XXIII-XXV, capitolo 3 | 2022-2025 | Serie aggiornate, gestioni e distribuzione del reddito pensionistico |
| Bilanci e Rendiconti generali INPS | 2013-2025 | Entrate contributive accertate |
| Appendici di bilancio INPS XXIII-XXV, tavola 2.4 | 2019-2025 | Trasferimenti dal bilancio dello Stato |
| API Osservatori statistici INPS 413 e 416 | 2024 | Pensionati, pensioni e importo medio lordo per regione |
| INPS Open Data ID-5291 e ID-5297 | 2012-2016 | Serie territoriali storiche di spesa e pensionati |
| Casellario dei pensionati, report 2024 | 2024 | Pensioni per classe di importo e relativa spesa |
| Eurostat `spr_exp_pens` | 2000-2024 | Spesa pensionistica ESSPROS in percentuale del PIL per paese |
| Eurostat `demo_r_pjanaggr3` | dal 2012 | Popolazione regionale per il rapporto pensionati/popolazione |
| Eurostat `nama_10r_2gdp` | dal 2012 | PIL regionale per il rapporto spesa pensionistica/PIL |

Le serie nazionali 2018-2025 provengono dallo stesso impianto di tavole annuali. I vecchi CSV Open Data con perimetri diversi restano nell'inventario, ma non vengono concatenati alla serie pubblicata.
La pipeline usa le API ufficiali quando l'indicatore e' disponibile. Ricorre a download diretti di file ufficiali soltanto come fallback e non esegue scraping di pagine HTML.

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
- La serie storica dell'aliquota IVS per dipendenti ordinari e' segnata come fonte da ricostruire, distinta dalle aliquote per autonomi disponibili nei CSV INPS.
