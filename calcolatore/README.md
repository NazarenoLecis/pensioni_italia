# Calcolatore "Mi sono pagato la pensione?"

Questa cartella contiene la parte individuale e simulativa del repository. La dashboard statistica nazionale continua a essere costruita dalla pipeline in `scripts/`; il calcolatore usa gli stessi principi di tracciabilita', ma ha motore, scenari, test e notebook separati.

## Esecuzione

```bash
python calcolatore/src/download_capitalization_data.py
python calcolatore/src/download_contract_wages.py
python calcolatore/src/pension_paid_calculator.py
python -m unittest discover -s calcolatore/tests -v
```

Il primo comando scarica due serie ufficiali del PIL nominale tramite API JSON SDMX ISTAT: la serie SEC 95 per il tratto storico e la serie SEC 2010 corrente. Per ciascun anno sceglie una coppia di livelli appartenente alla stessa edizione e calcola:

```text
tasso_t = (PIL_nominale_t-1 / PIL_nominale_t-6)^(1/5) - 1
montante_t = montante_t-1 * (1 + tasso_t) + accredito_t
```

L'accredito dell'anno non viene quindi rivalutato nello stesso anno. Numeratore, denominatore, edizione della serie e scarto dal tasso storico pubblicato sono salvati in `output/data/clean/tassi_capitalizzazione_montante.csv`. Lo scarto non viene nascosto: le revisioni dei conti nazionali possono modificare retroattivamente i livelli del PIL, mentre i coefficienti applicati in passato erano calcolati con le edizioni disponibili allora.

## Modalita

- `Semplificata`: ricostruisce la carriera da pochi dati. Per i dipendenti usa, quando disponibile, l'indice ISTAT delle retribuzioni contrattuali del contratto scelto, calibrato sull'importo inserito dall'utente.
- `Accurata`: richiede gli imponibili previdenziali effettivi anno per anno, preferibilmente dall'estratto contributivo INPS. Una tabella generata automaticamente non viene classificata come affidabilita alta finche' l'utente non sostituisce le stime.

Gli importi di carriera possono essere inseriti in euro o convertiti dalle lire con il cambio ufficiale 1 euro = 1.936,27 lire. La conversione riguarda le retribuzioni/imponibili storici, non la pensione attuale.

## Categorie operative

Il motore distingue dipendenti privati FPLD, dipendenti pubblici CTPS, dipendenti pubblici CPDEL/CPS/CPI/CPUG, dipendenti agricoli, artigiani, commercianti e autonomi agricoli CD/CM/IAP. Il reddito richiesto cambia con la gestione: RAL per i dipendenti, imponibile d'impresa per artigiani e commercianti, reddito convenzionale contributivo per gli autonomi agricoli.

Minimali, massimali, fasce convenzionali, addizionali fisse, riduzioni e agevolazioni personali non sono inventati. Quando non possono essere ricostruiti dai dati inseriti, il limite e' dichiarato.

## Pensione e data

L'utente inserisce la pensione mensile attuale lorda oppure netta. Dal netto il motore stima il lordo con scaglioni IRPEF 2026, detrazione da pensione e addizionali regionali/comunali medie del 2,1%. Non sottrae contributi previdenziali, perche' la pensione non e' retribuzione da lavoro.

La data di pensionamento determina eta' e mesi alla decorrenza, tabella storica e interpolazione mensile del coefficiente di trasformazione, pensioni gia' ricevute e data di raggiungimento del montante virtuale. L'eta' attesa mostrata usa invece la speranza di vita residua a 65 anni: `65 + e65` dalla tavola ISTAT per sesso.

## Output

Gli output pubblicabili sono scritti in `output/data/final/` e comprendono esempio sintetico, carriera annuale, parametri, coefficienti, categorie, mortalita e indici contrattuali. Il payload pubblico non contiene input personali; il calcolo utente avviene nel browser.
