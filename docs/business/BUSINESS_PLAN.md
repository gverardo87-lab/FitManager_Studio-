# FitManager Studio+ — Business Plan

**Versione:** 4.3 — 27 marzo 2026
**Autore:** Giacomo Verardo
**Stato:** Confidenziale · baseline pre-validazione, non autorità operativa corrente

> **Avvertenza 2026-07-31:** questo documento conserva modello economico, pricing e ipotesi di
> marzo 2026. Non è fonte di verità per versione prodotto, stato deployment, tecnologia di accesso,
> claim marketing, sequenza pre-POC o calendario. La regia operativa corrente vive in
> `docs/specs/SPEC_PRE_POC.md`; i claim commerciali vengono autorizzati dal product marketing context.
>
> **Interlock 2026-08-29 — exit Alessio:** il ruolo Industry Partner e la proposta economica
> 20% prodotto / 35% ricorrente / equity fino al 12% sono ipotesi storiche **superseded**, non
> un'offerta corrente né una policy riutilizzabile. Nessuna parte del modello matura compensi o diritti
> per Alessio. Il percorso è founder-led fino alla nuova strategia commerciale; fonte operativa:
> `docs/specs/SPEC_EXIT_ALESSIO.md`.
>
> **Claim superati nel corpo — delta di verità al 2026-09-02:** il corpo riflette marzo 2026 e NON va
> citato su questi punti: versione prodotto «1.0.5» (reale: `api/__init__.py`, oggi 1.0.14);
> FitManager Box presentata come componente esistente (è roadmap post-Wave 0, `LAUNCH_SCOPE.md`);
> Nutrizione presentata come feature attiva (UI rimossa, backend dormiente); «500 esercizi»
> (canonico: 466 attivi su 522, catalog.db); POC «10 professionisti» (regia corrente: max 3 design
> partner, `SPEC_PRE_POC.md` D9); accesso remoto «Tailscale» (sostituito da tunnel FRP self-hosted);
> «Email automatiche» (MAI esistite nel prodotto — verificato 2026-09-03, zero SMTP/invio email in
> `api/`; la comunicazione è WhatsApp). I claim commerciali autorizzati vivono solo in
> `PRODUCT_MARKETING_CONTEXT.md` (A0 ratificato 2026-09-03).

---

## Guida alla lettura

Questo documento è la baseline economica pre-validazione di FitManager Studio+. È la fonte di
tracciabilità per numeri, assunzioni e proiezioni datati marzo 2026, fino alla loro revisione con i
dati POC. Non governa il lavoro corrente e non prova da solo alcun claim di prodotto o di mercato.

Ogni numero è tracciabile a un'assunzione dichiarata (Appendice A4). Le proiezioni sono costruite dal basso (bottom-up) partendo dalla capacità reale di generare vendite. Tre scenari (conservativo, base, ottimistico) coprono la gamma di risultati possibili. Le proiezioni sono presentate in due configurazioni strutturali (con e senza Industry Partner) per mostrare che il business sta in piedi indipendentemente dalla partnership.

---

## 1. Executive summary

FitManager Studio+ è un sistema completo — software e dispositivo dedicato — che permette al personal trainer di gestire clienti, schede di allenamento, pagamenti e anamnesi da qualunque dispositivo, con la scienza integrata e i dati che restano nel suo studio. Si compra una volta, non si paga ogni mese.

Il prodotto è completo e funzionante (v1.0.5). La prima utilizzatrice reale lo usa quotidianamente. Il mercato target — oltre 100.000 professionisti fitness P.IVA in Italia — non è servito da nessun prodotto che combini architettura locale, scienza dell'allenamento e nutrizione italiana.

Il lancio avviene con una Proof of Concept strutturata (10 professionisti, 90 giorni, metriche misurabili) che valida il prodotto e il modello prima di scalare. Il business non richiede investimento esterno nell'Anno 1 e non genera debito in nessuno scenario.

Cerchiamo un Industry Partner con esperienza e network nel settore fitness per accelerare la crescita (il business parte anche senza, ma più lentamente), e — dopo la validazione della POC — un eventuale finanziamento contenuto per il marketing e il primo collaboratore operativo.

---

## 2. Il problema

### Ogni personal trainer in Italia conosce questa storia

Marco ha 32 clienti. Gestisce le anamnesi su fogli Word, le schede su PDF, i pagamenti su un foglio Excel. Ogni lunedì perde due ore a ricostruire chi ha pagato e chi no. Un mese fa ha dimenticato che un cliente aveva un'ernia lombare e gli ha assegnato stacchi da terra. Il cliente non è tornato.

Marco non è un caso isolato. È la norma.

### I 6 problemi che ogni trainer riconosce

**Ore perse in amministrazione.** Tra schede, pagamenti, appuntamenti e messaggi WhatsApp, un trainer perde dalle 3 alle 5 ore ogni settimana in lavoro che non genera valore. Tempo che potrebbe dedicare ai clienti — o a sé stesso.

**Tetto ai clienti.** Oltre 25-30 clienti, il sistema artigianale crolla. Il trainer perde appuntamenti, dimentica pagamenti, confonde le schede. Non può crescere senza perdere qualità.

**Nessuna visione unificata.** L'anamnesi è su un file, la scheda su un altro, i pagamenti su un foglio. Nessuno strumento mette insieme tutto ciò che serve sapere su un cliente in un'unica vista.

**Contabilità dispersa.** Rate dimenticate, pagamenti non registrati, nessun report finanziario. Il trainer non sa quanto ha fatturato il mese scorso senza spendere un'ora a ricostruirlo.

**Rischio errori clinici.** Condizioni patologiche annotate su carta o dimenticate. Nessun sistema che segnala se un esercizio è controindicato per quel cliente specifico. Un errore può causare un danno fisico — e la perdita definitiva del cliente.

**Impossibilità di differenziarsi.** Senza dati, senza misurazioni, senza report, tutti i trainer offrono lo stesso servizio. Non c'è modo di dimostrare ai clienti i progressi ottenuti.

### Il competitor vero

Il competitor di FitManager non è un altro software. È l'abitudine. Il trainer usa WhatsApp ed Excel perché "ha sempre fatto così" — non perché funzioni, ma perché nessuno gli ha offerto qualcosa di meglio che rispetti il suo modo di lavorare.

WhatsApp è il centro del workflow di ogni trainer. È lì che conferma appuntamenti, manda schede, sollecita pagamenti, tiene i rapporti con i clienti. Ma lo fa manualmente — riscrive gli stessi messaggi 20 volte al giorno, dimentica promemoria, perde il filo delle conversazioni. Qualunque soluzione che chieda al trainer di abbandonare WhatsApp parte sconfitta. La soluzione giusta non sostituisce WhatsApp — lo potenzia.

---

## 3. La soluzione

### FitManager è un sistema completo: software + dispositivo dedicato

Un unico strumento che permette al personal trainer di gestire clienti, schede di allenamento, pagamenti e anamnesi da qualunque dispositivo, con la scienza integrata e i dati che restano nel suo studio. Si compra una volta, non si paga ogni mese.

### Il software

**Gestione clienti e contratti.** Anagrafica, contatti, contratti, scadenze, storico completo — tutto in una schermata. Ogni lunedì mattina sai esattamente chi ha pagato, chi deve rinnovare, chi non viene da due settimane.

**Schede di allenamento.** 500 esercizi con progressioni, regressioni e varianti. Crea una scheda professionale in 5 minuti, non in 30. Ogni esercizio è collegato ai muscoli coinvolti e alle articolazioni interessate.

Il database è progettato per crescere con il contributo diretto di professionisti del settore. Esercizi validati da migliaia di ore di pratica 1:1, varianti testate su clienti reali con patologie specifiche, progressioni e regressioni affinate sul campo. Questo trasforma il catalogo da raccolta scientifica a patrimonio di conoscenza clinica pratica — un differenziatore che nessun competitor può replicare acquistando un dataset.

**Protezione dagli errori clinici.** Il Safety Engine monitora 47 condizioni cliniche con 80 regole automatiche. Se assegni un esercizio controindicato per le patologie di quel cliente, il sistema ti avvisa.

**Nutrizione italiana.** 880 alimenti dal database CREA (Consiglio per la Ricerca in Agricoltura e l'Analisi dell'Economia Agraria), l'ente ufficiale italiano. Piani alimentari settimanali basati sui LARN (Livelli di Assunzione di Riferimento di Nutrienti).

**Anamnesi strutturata.** Percorso guidato in 6 passaggi. Il cliente può compilare la propria anamnesi da solo, dal proprio telefono, tramite un portale web sicuro.

**Pagamenti e cassa.** Registra pagamenti, gestisci rate, visualizza lo stato finanziario di ogni cliente e del tuo business in tempo reale.

**Comunicazione integrata con i clienti.**

**WhatsApp semi-automatico.** Un click e il messaggio parte — con il nome del cliente, la data, l'orario, l'importo già compilati. Promemoria appuntamento, sollecito pagamento, invio nuova scheda, messaggio di benvenuto. FitManager prepara il messaggio, tu lo mandi dal tuo WhatsApp. Zero configurazione, funziona dal giorno uno.

**Email automatiche.** Il sistema invia automaticamente conferme appuntamento, promemoria pagamento, notifiche di nuova scheda e messaggi di benvenuto. Il trainer configura una volta, poi il sistema lavora da solo. SMTP standard — funziona con qualunque provider email.

Il trainer non deve cambiare il modo in cui comunica con i clienti. FitManager si inserisce nel suo workflow esistente e lo rende professionale.

**Portale Allenamento Clienti.** Il cliente del trainer accede dal proprio telefono — nessuna app da scaricare. Vede la sessione del giorno, ogni esercizio con i parametri prescritti e le foto di esecuzione. Esegue, registra serie e ripetizioni, conferma o modifica il prescritto con un tap. A fine sessione: feedback rapido su energia, soddisfazione e difficoltà percepita.

**Workout Intelligence.** Il sistema analizza automaticamente l'esecuzione rispetto al piano: compliance esercizio per esercizio, volume effettivo per ogni gruppo muscolare confrontato con i target scientifici (MEV/MAV/MRV), equilibri biomeccanici su 5 rapporti (Push:Pull, Quad:Hamstring, Anteriore:Posteriore). Il trainer si siede col cliente e gli mostra esattamente dove il suo corpo risponde e dove serve aggiustare — muscolo per muscolo, con target personalizzati per sesso, età e obiettivo. Nessun competitor al mondo offre questo livello di analisi.

### La FitManager Box

Un piccolo dispositivo dedicato che il trainer mette nel suo studio. Lo attacca alla corrente e al WiFi — fine. Da quel momento accede a FitManager da qualunque dispositivo: il computer a casa, il telefono in palestra, il tablet durante le sessioni.

I dati non vanno mai in cloud. Restano fisicamente nello studio del trainer. Il dispositivo è sempre acceso — non dipende dal computer del trainer.

### Stato del prodotto

Il prodotto è completo e funzionante (versione 1.0.5). La prima utilizzatrice reale — una chinesiologia di Genova — lo usa quotidianamente per gestire i propri clienti. Le sue clienti ricevono schede professionali, compilano le anamnesi dal proprio telefono e registrano l'allenamento in tempo reale dal portale dedicato.

---

## 4. Cosa lo rende diverso

### Confronto con le alternative

|  | FitManager | Mangofit | EvolutionFit | Excel + WhatsApp |
|---|---|---|---|---|
| Dati nel tuo studio | Sì | No (cloud) | No (cloud) | Sì |
| Accesso da telefono/tablet | Sì | Sì | Sì | Parziale |
| Comunicazione cliente integrata | Sì (WhatsApp + email) | Parziale (notifiche in-app) | Parziale (notifiche in-app) | Manuale |
| Segnala errori su patologie | Sì (47 condizioni) | No | No | No |
| Nutrizione italiana (CREA) | Sì (880 alimenti) | No | No | No |
| Scienza allenamento integrata | Sì | No | Base | No |
| Monitoraggio allenamento live | Sì (portale + analytics muscolo×muscolo) | No | No | No |
| Si paga una volta sola | Sì | No (abbonamento) | No (abbonamento) | Sì (€0) |

### Quanto costa in 3 anni

| Software | Anno 1 | Anno 2 | Anno 3 | Totale 3 anni |
|---|---|---|---|---|
| FitManager (licenza + assistenza) | €249 | €79 | €79 | €407 |
| FitManager Box (Box + assistenza) | €449 | €79 | €79 | €607 |
| Mangofit Pro (€40/mese) | €480 | €480 | €480 | €1.440 |
| EvolutionFit (€60/mese) | €720 | €720 | €720 | €2.160 |

Il database esercizi non è statico. È progettato per essere arricchito da professionisti certificati con esperienza pratica validata — varianti, regressioni per patologie specifiche, progressioni testate su migliaia di sessioni reali. Questo crea un asset che cresce in valore nel tempo e che un competitor non può replicare con la sola tecnologia.

Nessun prodotto sul mercato combina accesso locale, scienza integrata e assenza di abbonamento.

---

## 5. Il mercato

### Dimensione

In Italia operano oltre 100.000 professionisti nel settore fitness con Partita IVA, tra personal trainer, chinesiologi, preparatori atletici e istruttori qualificati. Il dato è coerente con le stime di Sport e Salute (ex CONI) e con i registri degli enti di promozione sportiva. Il mercato fitness italiano nel suo complesso vale circa 3 miliardi di euro annui ed è in crescita di circa il 10% anno su anno.

*Nota: il dato 100K+ va confermato con fonte ufficiale (Sport e Salute, ISTAT, o ordini professionali). Nel presente documento è presentato come stima di ordine di grandezza.*

### Segmento target

Non tutti i 100K+ professionisti sono clienti potenziali. Il target iniziale è il sottoinsieme che soddisfa tre criteri: ha almeno 15-20 clienti attivi (il problema di gestione emerge da questa soglia), lavora in aree urbane o peri-urbane (accesso a connettività, propensione digitale), ed è aperto a strumenti professionali.

Stimiamo questo segmento in 10.000-15.000 professionisti. È una stima, non un dato verificato. I primi 6 mesi di attività commerciale forniranno il dato reale.

### Trend che favoriscono l'adozione

La professionalizzazione del settore è in corso: il Registro Nazionale CONI è attivo dal 1 luglio 2023, il codice ATECO 85.51.09 riconosce formalmente il personal trainer. La regolamentazione spinge verso strumenti strutturati.

La sensibilità sulla privacy dei dati clinici cresce: i trainer gestiscono anamnesi, patologie, dati sanitari. Il GDPR rende il modello "tutto in cloud su server di terzi" sempre più problematico per chi tratta dati sensibili. Il modello locale offre conformità nativa.

La domanda di personalizzazione aumenta: il cliente del trainer è più esigente, vuole progressioni misurabili, schede personalizzate, report.

### Perché il mercato è vuoto

Nessun prodotto combina architettura locale, scienza dell'allenamento integrata, nutrizione italiana e modello perpetuo. Questo posizionamento richiede competenze di dominio profonde (scienza dell'allenamento + nutrizione + compliance clinica) combinate con competenze tecniche specifiche (architettura locale-first, distribuzione desktop/embedded). FitManager è l'unico prodotto costruito all'intersezione di queste competenze.

### Oltre l'Italia: il mercato internazionale

FitManager nasce in italiano per il mercato italiano, ma l'architettura è progettata per l'internazionalizzazione. Il mercato fitness professionale anglofono — Scandinavia, UK, Nord Europa — presenta le stesse carenze: nessun prodotto combina architettura locale, scienza integrata e modello perpetuo.

La versione inglese è in roadmap entro i primi 6 mesi di attività. L'internazionalizzazione procede per blocchi, in ordine di complessità:

**Blocco 1 — Interfaccia e core (complessità bassa).** Traduzione dell'interfaccia utente, dei template e della documentazione. Adattamento formati data, valuta, unità di misura. Fattibile in poche settimane.

**Blocco 2 — Database esercizi e Safety Engine (complessità media).** I 500+ esercizi e le 80 regole cliniche si basano su scienza universale (biomeccanica, fisiologia dell'esercizio). La traduzione richiede adattamento terminologico professionale, non riscrittura. Il contributo di professionisti che operano in contesto internazionale accelera questo processo.

**Blocco 3 — Nutrizione e compliance locale (complessità alta).** Il database CREA e le tabelle LARN sono standard italiani. Per il mercato internazionale servono database nutrizionali locali (USDA, McCance & Widdowson, EuroFIR) e linee guida specifiche per giurisdizione. Questo blocco richiede ricerca e sviluppo dedicato ed è pianificato per la fase di espansione (Anno 2+).

**Blocco 4 — Moduli fiscali e contrattuali (complessità variabile).** Pagamenti, fatturazione e contratti sono attualmente configurati per il regime fiscale italiano. L'adattamento per altre giurisdizioni è modulare — ogni mercato richiede la propria configurazione.

L'approccio è incrementale: la versione inglese parte con i Blocchi 1 e 2 (gestione clienti, schede, Safety Engine), che rappresentano il valore core del prodotto. La nutrizione localizzata e la compliance fiscale seguono man mano che il mercato internazionale si sviluppa.

Il mercato italiano resta la priorità dell'Anno 1 — è qui che il prodotto viene validato, il modello affinato, e la base installata costruita. L'internazionalizzazione è la leva di crescita che trasforma un prodotto verticale italiano in un prodotto scalabile.

---

## 6. Il modello economico

### Pricing

| Prodotto | Prezzo | Cosa include |
|---|---|---|
| **Licenza software** | **€249** | Software completo sul PC del trainer. Accesso da telefono/tablet tramite connessione sicura (Tailscale). Installazione assistita. |
| **FitManager Box** | **€449** | Dispositivo dedicato + software preinstallato. Accesso ovunque. Dati nel tuo studio. Plug & play. |
| **Assistenza annuale** | **€79/anno** | Aggiornamenti software, nuovi esercizi e alimenti, template, supporto. Inclusa 12 mesi per i primi 30 clienti. |

Licenza perpetua: il trainer compra una volta e il software è suo per sempre. Nessun abbonamento obbligatorio.

### Margini unitari

| Prodotto | Prezzo | Costo vivo | Margine lordo |
|---|---|---|---|
| Licenza software | €249 | ~€30 (tempo installazione) | €219 (88%) |
| FitManager Box | €449 | ~€150 (hardware + spedizione + setup) | €299 (67%) |
| Assistenza annuale | €79 | ~€0 (contenuto digitale) | €79 (100%) |

Nessun costo server. I dati sono locali. Ogni vendita aggiuntiva è quasi interamente margine.

---

## 7. Come arriviamo ai clienti

### Le fonti di lead

| Fonte | Come funziona | Lead al mese (a regime) |
|---|---|---|
| Network del partner | Contatti diretti, presentazioni, eventi | 8-12 |
| LinkedIn del founder | Contenuti settimanali, post educativi | 5-8 |
| Referral dai clienti | Passaparola naturale + programma referral | 2-4 |
| Webinar mensile | Formazione gratuita con demo integrata | 3-5 |
| Passaparola e community | Crescita organica | 2-4 |
| **Totale a regime (mesi 7-12)** | | **20-33** |

### Il funnel

| Passaggio | Tasso | Logica |
|---|---|---|
| Da potenziale a demo | 50-60% | Lead già qualificati (network, referral) |
| Da demo ad acquisto | 20-25% | Benchmark software B2B early stage con prodotto funzionante |
| **Da potenziale a cliente** | **10-15%** | Combinazione dei due passaggi |

La demo include un momento di dimostrazione live: il trainer vede il proprio nome, il proprio cliente e un messaggio WhatsApp pronto da inviare con un click. Questo è il punto di conversione emotiva — il trainer capisce il valore di FitManager in 3 secondi, senza bisogno di spiegazioni tecniche. Tutto il resto (scienza, nutrizione, Safety Engine) è la profondità che scopre dopo.

### Break-even

| Voce | Valore |
|---|---|
| Costi fissi mensili | ~€360 |
| Margine medio per vendita (mix pesato) | ~€220 |
| Vendite per break-even operativo | 1,7 al mese |
| **Vendite per break-even reale (con tasse e rev share)** | **3 al mese** |

Tre vendite al mese è il numero chiave. Se lo raggiungiamo stabilmente dal mese 5-6, il business è sostenibile.

---

## 8. Strategia di marketing e acquisizione

### Il principio guida

FitManager opera in un mercato da educare. I trainer non cercano un gestionale — non sanno di averne bisogno. Il marketing tradizionale (pubblicità a pagamento) ha un ritorno basso su una domanda che non esiste. La strategia è creare la domanda attraverso contenuto educativo, community, e il concetto di Personal Trainer Evoluto.

### I tre canali

**Canali propri (owned):** sito web con landing page e waiting list, blog con contenuti ottimizzati SEO, sequenze email automatizzate, community dei clienti. Costano tempo, non denaro. Producono risultati crescenti nel tempo.

**Canali del partner (borrowed):** network personale, masterclass e webinar co-condotti, podcast di settore, rapporti con enti di formazione. Impatto immediato, dipendono dalla relazione con il partner.

**Canali a pagamento (paid):** solo dalla Fase 3 (mesi 7-12), budget €500-1.200/anno, parole chiave ad alta intenzione di acquisto. Non sono il motore — sono un acceleratore.

### Budget marketing Anno 1

| Voce | Importo |
|---|---|
| Dominio + hosting sito | €120/anno |
| Tool email marketing | €0-180/anno |
| Produzione video demo/testimonial | €0-200 |
| Pubblicità a pagamento (mesi 7-12) | €300-500 |
| **Totale marketing Anno 1** | **€120-880** |

Il budget è quasi zero nell'Anno 1. Il marketing a pagamento senza social proof brucia denaro. Prima servono i dati della POC e le storie dei Fondatori.

### Asset necessari prima del lancio

| Asset | Stato | Priorità |
|---|---|---|
| Sito web / landing page | Da creare | Critico — prerequisito del lancio |
| Waiting list con referral virale | Da creare | Critico |
| Video demo (3 minuti) | Da creare | Alto |
| Video teaser (60 secondi) | Da creare | Alto |
| Screenshot professionali | Da creare | Medio |
| Profilo LinkedIn attivo | Parziale | Alto |

### Il marketing virale integrato nel prodotto

Ogni volta che un trainer invia il link anamnesi a un proprio cliente, il cliente vede "Powered by FitManager Studio+" nel footer. Con 30 trainer attivi e 20 clienti ciascuno, sono oltre 600 esposizioni al mese a costo zero. Il meccanismo cresce automaticamente con la base installata.

### Risultati attesi per fase

| Fase | Periodo | Lead/mese | Vendite/mese |
|---|---|---|---|
| Pre-lancio | 4 sett. prima della POC | 50+ iscritti waiting list | 0 |
| POC | Mesi 1-3 | Focus sui 10 Fondatori | 10 (selezionati) |
| Early Adopter | Mesi 4-6 | 15-25 | 2-3 |
| Prezzo pieno | Mesi 7-12 | 22-35 | 3-5 |

---

## 9. Piano di validazione: la Proof of Concept

### Non vendiamo subito. Prima dimostriamo — il pacchetto completo.

I primi 10 non sono solo tester del software. Sono i primi studenti del Metodo PT Evoluto. La POC valida simultaneamente il prodotto, la categoria professionale, la community, e il ruolo dell'Industry Partner. Se funziona, al mese 4 abbiamo in mano la prova completa: non solo "il software funziona" ma "il percorso PT Evoluto trasforma il modo di lavorare, e i clienti del trainer lo notano."

Se non funziona, lo scopriamo con 10 persone e ~€1.000 — su tutti i fronti contemporaneamente.

La comunicazione WhatsApp è attiva dal giorno uno. È la prima feature che i Fondatori usano — non serve imparare il sistema per trarne valore immediato. Inserisci un cliente, clicchi "manda promemoria", WhatsApp si apre col messaggio pronto. Fatto. Il resto si scopre nei giorni successivi.

### Cosa ricevono i 10 Fondatori

I Fondatori non ricevono solo il software. Ricevono il percorso completo per 12 mesi:

| Incluso nel prezzo Fondatore | Dettaglio |
|---|---|
| Software o Box | 8 ricevono la licenza (€99), 2 ricevono la Box (€199) |
| Inner Circle 12 mesi | Masterclass, webinar, mastermind — incluso, non extra |
| Community Fondatori dedicata | Canale riservato per feedback, idee, supporto |
| Installazione assistita | Setup 1:1 con il founder |

Il prezzo Fondatore (€99 licenza / €199 Box) copre i costi vivi. Il valore reale del pacchetto (software + Inner Circle 12 mesi) sarebbe €249+€249 = €498 per la licenza, €449+€249 = €698 per la Box. I Fondatori lo ottengono a una frazione perché sono l'investimento più importante del progetto.

### Il protocollo: prodotto + formazione insieme

**Fase A — Setup, baseline e primo contatto col metodo (giorni 1-14).**

10 professionisti selezionati. Questionario baseline: come gestiscono i clienti oggi, quante ore perdono in admin, quanto si sentono organizzati, quanto sarebbero disposti a pagare (prima di rivelare il prezzo). Installazione e inserimento dei primi clienti.

KPI di attivazione: primo messaggio WhatsApp pre-compilato inviato entro 24 ore dall'installazione. Se il Fondatore manda il primo messaggio il giorno 1, è agganciato.

**Fase B — Adozione, feedback e masterclass (giorni 15-75).**

Uso reale quotidiano del software. Check-in bisettimanale di 15 minuti. Micro-sondaggio settimanale. Canale community dedicato per feedback in tempo reale.

In parallelo, il percorso formativo condotto dall'Industry Partner:

| Mese | Contenuto | Conduce | Obiettivo |
|---|---|---|---|
| Mese 1 | Masterclass: "Il Metodo PT Evoluto — come cambia il tuo lavoro" | Industry Partner | I 10 capiscono la visione, non solo il tool |
| Mese 2 | Webinar pratico: "Le prime 4 settimane con FitManager — risultati e domande" | Founder + Partner | Feedback live, problem solving, contenuto registrato |
| Mese 3 | Masterclass: "Da 25 a 45 clienti — il metodo in pratica" | Industry Partner | I 10 hanno i risultati, li raccontano nella sessione |

Le 3 sessioni vengono registrate. Queste registrazioni diventano il nucleo della libreria Inner Circle — un asset che genera valore per anni.

**Fase C — Misurazione e risultati (giorni 75-90).**

Questionario finale (stesse domande del baseline). Confronto prima/dopo. Video-intervista con ciascuno. Sessione di gruppo con tutti i 10. Decisione GO/NO-GO.

### Le metriche

La POC misura sia il prodotto sia il percorso:

| Metrica | Prima (atteso) | Dopo (target) | Cosa valida |
|---|---|---|---|
| Ore admin a settimana | 3-5 ore | Meno di 2 ore | Prodotto |
| Senso di organizzazione (1-10) | 4-6 | 8 o più | Prodotto |
| Dati persi al mese | 2-3 | Zero | Prodotto |
| NPS (scala -100/+100) | — | Sopra 50 | Prodotto + percorso |
| "Lo ricompreresti a prezzo pieno?" | — | 8 su 10 sì | Pricing |
| "Le masterclass hanno cambiato il tuo approccio?" | — | 7+ su 10 sì | Percorso/categoria |
| "I tuoi clienti hanno notato una differenza?" | — | 5+ su 10 sì | Volano PT Evoluto |
| "Ti definiresti un PT Evoluto?" | — | 6+ su 10 sì | Category creation |
| Messaggi WhatsApp pre-compilati usati/settimana | — | 15+ | Adozione comunicazione |
| Tempo risparmiato percepito in comunicazione | — | 30+ min/giorno | Valore feature |
| Clienti usano portale allenamento | — | 7+ su 10 attivi | Workout Intelligence |

Le ultime 4 metriche sono nuove rispetto a una POC solo-software. Sono quelle che validano la categoria, il volano e il fossato competitivo.

### I profili dei 10 Fondatori

3 trainer in palestra, 2 freelance con studio proprio, 2 chinesiologi con clienti clinici, 1 trainer online/ibrido, 1 neoqualificato, 1 senior con oltre 40 clienti. Criterio comune: almeno 10 clienti attivi, disponibilità a dare feedback strutturato per 90 giorni.

### La decisione

| Risultato POC | Decisione |
|---|---|
| NPS sopra 50, ore admin dimezzate, 8+ attivi, 5+ clienti notano differenza | **GO** — lanciamo con fiducia, pacchetto completo |
| NPS 30-50, miglioramenti parziali, categoria parzialmente recepita | **GO con cautela** — aggiustiamo prima di scalare |
| NPS sotto 30, meno di 6 attivi, categoria non risuona | **STOP** — ripensare prodotto, percorso o target |

### Cosa abbiamo al mese 4 (se GO)

Al termine della POC, il progetto dispone di:

- 10 storie reali con dati misurabili (prima/dopo)
- 10 video-interviste testimonial
- 3 masterclass registrate (contenuto riutilizzabile per la libreria Inner Circle)
- Dati aggregati ("i Fondatori hanno ridotto l'admin del X%, Y su 10 si definiscono PT Evoluti")
- Una community di 10 professionisti già attiva e funzionante
- La prova che il percorso PT Evoluto funziona — non solo il software

Questo pacchetto è la leva di vendita per la fase Early Adopter. Non vendiamo "un software." Vendiamo "guarda cosa hanno ottenuto questi 10 in 3 mesi — vuoi lo stesso?"

### Costo della POC

| Voce | Importo |
|---|---|
| 8 licenze Fondatore a €99 + 2 Box Fondatore a €199 | €1.190 (ricavo) |
| Costo vivo hardware 2 Box test | €300 |
| Tempo founder (check-in, supporto, analisi) | ~40 ore in 90 giorni |
| Tempo partner (selezione Fondatori, 3 masterclass, partecipazione webinar) | ~15-20 ore in 90 giorni |
| **Investimento netto in cash** | **~€300** |

Il partner viene compensato con il 20% dei ricavi POC (€238) e con la proprietà condivisa delle registrazioni: le 3 masterclass entrano nella libreria Inner Circle e generano il 35% di revenue share standard per ogni futuro membro che le fruisce.

---

## 10. Proiezioni finanziarie

### Due strutture a confronto

Le proiezioni hanno due configurazioni strutturali per mostrare che il business sta in piedi indipendentemente dalla partnership.

### Configurazione A — Founder solo (senza Industry Partner)

Il founder è l'unica risorsa commerciale. Canali: LinkedIn organico, SEO, referral, webinar self-hosted. Lead a regime: 10-14/mese. Vendite a regime: 1-2/mese.

| | Anno 1 | Anno 2 | Anno 3 |
|---|---|---|---|
| Nuovi clienti | 24 | 34 | 50 |
| Base installata cumulativa | 24 | 58 | 108 |
| Fatturato | €7.200 | €13.500 | €22.000 |
| Costi totali | €5.800 | €8.500 | €14.000 |
| Tasse | €1.512 | €2.835 | €4.400 |
| **Netto founder** | **-€112** | **€2.165** | **€3.600** |

Il business sopravvive. Non genera debito. Ma la crescita è lenta e il founder non si paga un vero stipendio per almeno 2 anni.

### Configurazione B — Founder + Industry Partner

Il partner aggiunge: network, credibilità, masterclass dal mese 1 (durante la POC), effetto di autorità nel funnel. Lead a regime: 22-35/mese. Vendite a regime: 3-6/mese. Inner Circle attivo dal mese 4 (il partner conduce le masterclass, primo contenuto creato durante la POC).

Il compenso del partner ha una struttura semplificata a due percentuali: 20% su tutte le vendite prodotto (licenze e Box, senza distinguere la fonte) e 35% su tutto il ricorrente e contenuto (PRO, Inner Circle, masterclass). Due percentuali, nessuna zona grigia — un lead arrivato dal webinar del partner ma convertito da un post LinkedIn del founder non genera dispute.

I ricavi sono suddivisi in tre flussi: vendite prodotto (licenze + Box), assistenza PRO (€79/anno, aggiornamenti e supporto), Inner Circle (€249/anno, include PRO + masterclass + mastermind + certificazione PT Evoluto).

**Scenario conservativo — partner arriva tardi, conversione 20%, IC con bassa adozione (12% della base):**

| | Anno 1 | Anno 2 | Anno 3 |
|---|---|---|---|
| Nuovi clienti | 33 | 35 | 49 |
| Base installata cumulativa | 33 | 68 | 117 |
| Vendite prodotto | €8.559 | €12.632 | €18.108 |
| Assistenza PRO | €160 | €2.414 | €4.945 |
| Inner Circle | €996 | €2.040 | €4.388 |
| **Fatturato** | **€10.715** | **€17.086** | **€27.441** |
| Costi diretti + operativi | €6.970 | €9.330 | €12.990 |
| Compenso partner (20% prodotto + 35% ricorrente) | €2.117 | €4.085 | €6.889 |
| Tasse | €2.250 | €3.588 | €6.467 |
| **Netto founder** | **-€622** | **€83** | **€1.095** |
| **Netto partner (cash)** | **€2.117** | **€4.085** | **€6.889** |

**Scenario base — partner operativo dal mese 2, conversione 25%, IC al 20% della base:**

| | Anno 1 | Anno 2 | Anno 3 |
|---|---|---|---|
| Nuovi clienti | 46 | 58 | 87 |
| Base installata cumulativa | 46 | 104 | 191 |
| Vendite prodotto | €13.950 | €21.450 | €32.850 |
| Assistenza PRO | €950 | €3.700 | €7.300 |
| Inner Circle | €2.250 | €4.500 | €9.500 |
| **Fatturato** | **€17.150** | **€29.650** | **€49.650** |
| Costi diretti + operativi | €8.560 | €14.325 | €22.865 |
| Compenso partner (20% prodotto + 35% ricorrente) | €3.910 | €7.160 | €12.450 |
| Tasse | €3.600 | €6.230 | €6.750 |
| **Netto founder** | **€1.080** | **€1.935** | **€7.585** |
| **Netto partner (cash)** | **€3.910** | **€7.160** | **€12.450** |

Nota: dall'Anno 3, con fatturato superiore a €40.000, è prevista la transizione a regime ordinario/SRL. Le tasse sono calcolate al ~35% sul reddito netto (non sul fatturato), il che rende deducibili i costi hardware e operativi.

**Scenario ottimistico — partner forte, conversione 30%, IC al 25% della base:**

| | Anno 1 | Anno 2 | Anno 3 |
|---|---|---|---|
| Nuovi clienti | 67 | 97 | 155 |
| Base installata cumulativa | 67 | 164 | 319 |
| Vendite prodotto | €23.383 | €37.330 | €57.680 |
| Assistenza PRO | €1.600 | €4.430 | €8.620 |
| Inner Circle | €2.990 | €7.380 | €15.200 |
| **Fatturato** | **€27.973** | **€49.140** | **€81.500** |
| Costi diretti + operativi | €11.050 | €22.130 | €38.250 |
| Compenso partner (20% prodotto + 35% ricorrente) | €6.284 | €11.600 | €19.873 |
| Tasse | €5.874 | €6.620 | €10.270 |
| **Netto founder** | **€4.765** | **€8.790** | **€13.107** |
| **Netto partner (cash)** | **€6.284** | **€11.600** | **€19.873** |

### Il confronto diretto: cosa cambia con il partner

| | Senza partner | Con partner (base) | Moltiplicatore |
|---|---|---|---|
| Clienti Anno 1 | 24 | 46 | 1,9x |
| Clienti Anno 3 | 108 | 191 | 1,8x |
| Fatturato Anno 1 | €7.200 | €17.150 | 2,4x |
| Fatturato Anno 3 | €22.000 | €49.650 | 2,3x |
| Netto founder Anno 3 | €3.600 | €7.585 | 2,1x |
| Fatturato cumulativo 3 anni | €42.700 | €96.450 | 2,3x |

Senza partner, l'Inner Circle non è attivabile (mancano le masterclass e la voce credibile). Il partner non solo raddoppia le vendite — abilita un intero flusso di ricavo (Inner Circle) che non esiste nella configurazione senza partner. Il moltiplicatore 2,1x sul netto founder riflette una struttura di compenso più generosa per il partner (20% prodotto + 35% ricorrente), calibrata sul suo contributo diretto alla crescita del ricavo ricorrente.

Il business funziona senza partner. Con il partner, decolla. Non è una dipendenza — è una leva che abilita un flusso di ricavo altrimenti impossibile.

### Vista cumulativa founder + partner (scenario base)

| | Anno 1 | Anno 2 | Anno 3 | Cumulativo |
|---|---|---|---|---|
| **Progetto** | | | | |
| Clienti (base installata) | 46 | 104 | 191 | — |
| Di cui Inner Circle | 9 | 18 | 38 | — |
| Fatturato | €17.150 | €29.650 | €49.650 | **€96.450** |
| Di cui ricorrente (PRO + IC) | €3.200 | €8.200 | €16.800 | €28.200 |
| **Founder** | | | | |
| Netto cash | €1.080 | €1.935 | €7.585 | **€10.600** |
| Equity detenuta | 97% | 88-94% | 88% | — |
| **Partner** | | | | |
| Cash (20% prodotto + 35% ricorrente) | €3.910 | €7.160 | €12.450 | **€23.520** |
| Equity maturata (milestone) | 3% | 6-12% | 12% | — |
| Valore equity stimato (12%) | €3.120 | €8.160 | €16.800 | — |
| **Totale partner (cash + equity)** | **€7.030** | **€15.320** | **€29.250** | **€39.520** |
| **Valore stimato progetto** | **€26.000** | **€68.000** | **€140.000** | — |

Nota sulla valutazione: multiplo 2x sul ricavo ricorrente annualizzato (€16.800 × 2 = €33.600) + valore base installata (191 × €200 = €38.200) + valore IP (€35.000) + valore community e brand (€33.200). Metodo conservativo per software B2B verticali con community attiva. Il ricavo ricorrente (PRO + Inner Circle) rappresenta il 34% del fatturato Anno 3 e cresce ogni anno — è il driver principale della valutazione.

L'equity del partner è legata a milestone concrete: 3% al completamento POC (GO al giorno 90), 3% al raggiungimento di 50 clienti attivi, 6% al primo accordo internazionale firmato. Se la POC fallisce: 0% equity, 0 costi.

---

## 11. Se va male

### Lo scenario peggiore

Tutto va male contemporaneamente. Il partner arriva in ritardo, la conversione è bassa, la Box non convince, tre Fondatori abbandonano la POC.

| | Valore |
|---|---|
| Clienti Anno 1 | 18-20 |
| Fatturato | ~€5.500 |
| Perdita netta | ~€700 |
| Perdita massima in cash | ~€2.000 |

Il business non chiude. Non genera debito. La perdita massima è il costo di un corso di formazione.

### La POC come meccanismo di protezione

Non arriviamo a 12 mesi alla cieca. Al giorno 90 abbiamo i dati per decidere.

| Risultato POC | Decisione |
|---|---|
| NPS sopra 50, ore admin dimezzate, 8+ attivi | GO |
| NPS 30-50, miglioramenti parziali | GO con cautela |
| NPS sotto 30, meno di 6 attivi | STOP |

Costo totale se ci fermiamo al giorno 90: 3 mesi di tempo e circa €1.000.

### Rischi specifici

**"I trainer non vogliono pagare per un software."** La POC include la misurazione della disponibilità a pagare prima di rivelare il prezzo. Se il dato esce basso, lo sappiamo con 10 persone, non con 100.

**"Il partner si disimpegna."** L'equity è a milestone — se non raggiunge i risultati, non matura. Il business parte anche senza partner — più lentamente, ma parte (vedi Configurazione A nelle proiezioni).

**"Un competitor copia."** Il database scientifico (500 esercizi, 940 relazioni, Safety Engine, nutrizione CREA) richiede 6+ mesi di lavoro specializzato. L'architettura locale non è replicabile da un SaaS senza riscrittura totale.

**"I rinnovi assistenza sono bassi."** Se il tasso è sotto il 40%, il contenuto dell'assistenza non ha abbastanza valore percepito. Lo misuriamo e lo correggiamo. Il business non dipende dai rinnovi nell'Anno 1.

---

## 12. Team e struttura organizzativa

### Anno 1: founder + Industry Partner

Il founder (Giacomo Verardo) copre sviluppo prodotto, vendite dirette, supporto clienti, marketing organico e gestione operativa.

L'Industry Partner è una figura con esperienza pluriennale nel settore fitness, un network attivo di professionisti, e la credibilità per presentare il prodotto come voce del settore. Il suo ruolo è commerciale e strategico: seleziona i Fondatori per la POC, presenta il prodotto al proprio network, conduce masterclass e webinar, e valida il posizionamento "PT Evoluto" nel mercato, e contribuisce all'arricchimento del database esercizi con varianti e progressioni validate dalla propria esperienza pratica. Impegno stimato: 8-10 ore al mese.

### Struttura di compenso del partner

Il partner non riceve un compenso fisso. Riceve una quota dei ricavi con struttura semplificata a due percentuali:

| Componente | Percentuale | Applicata a |
|---|---|---|
| Vendite prodotto | 20% | Tutte le licenze e Box, senza distinguere la fonte |
| Ricorrente + contenuto | 35% | PRO, Inner Circle, masterclass |

Due percentuali, nessuna zona grigia. Un lead arrivato dal webinar del partner ma convertito da un post LinkedIn del founder non genera dispute — il 20% si applica a tutte le vendite. Il 35% sul ricorrente riflette il contributo diretto del partner: il contenuto che giustifica il rinnovo è suo.

| | Anno 1 | Anno 2 | Anno 3 |
|---|---|---|---|
| Fatturato (scenario base) | €17.150 | €29.650 | €49.650 |
| Compenso partner (20% prodotto + 35% ricorrente) | €3.910 | €7.160 | €12.450 |
| Costo fisso partner | €0 | €0 | €0 |

In aggiunta, il partner riceve equity fino al 12%, legata a milestone concrete:

| Milestone | Equity | Quando |
|---|---|---|
| Completamento POC — decisione GO al giorno 90 | 3% | Mese 3 |
| 50 clienti attivi nella base installata | 3% | Quando accade |
| Primo accordo internazionale firmato | 6% | Quando accade |
| **Totale potenziale** | **12%** | — |

Se la POC fallisce: 0% equity, 0 costi. L'equity si guadagna con i risultati, non con la permanenza. Le 3 masterclass registrate durante la POC restano di proprietà condivisa e generano il 35% di revenue share standard ogni volta che un nuovo membro Inner Circle le fruisce.

L'analisi costi-benefici: il compenso partner nel triennio ammonta a €23.520 (scenario base). Il fatturato aggiuntivo rispetto alla configurazione senza partner è €53.750. Ritorno: 2,3x per ogni euro investito in compenso partner.

### Evoluzione del team

| Periodo | Team | Costo fisso aggiuntivo |
|---|---|---|
| Anno 1 | Founder + Industry Partner (equity + rev share) | €0 |
| Anno 2 | + Tirocinante/collaboratore part-time | €4.000-5.000/anno |
| Anno 3 | + Junior developer + ufficio/coworking | €12.000-16.000/anno |

### Chi è il founder

**Gestione di sistemi complessi.** Anni nella cantieristica navale e nelle operazioni offshore (SAIPEM), gestendo sistemi tecnici in ambienti ad alta pressione — navi, cantieri, operazioni in Brasile, Africa, Cina.

**Competenza tecnologica ereditata.** Due anni a fianco del padre, pioniere delle applicazioni di intelligenza artificiale in Italia. Sistemi di visione artificiale per l'industria.

**FitManager.** 6 mesi di sviluppo full-time. Prodotto completo e funzionante: 47.000+ righe di codice, 395 test automatici, 7 motori scientifici. In uso quotidiano da una professionista reale.

**Competenza di dominio.** Conoscenza diretta del settore fitness come praticante e istruttore. FitManager è l'intersezione tra competenza tecnica e conoscenza del dominio.

---

## 13. Piano di crescita

**Fase 1 — POC con percorso completo (mesi 1-3).** 10 Fondatori selezionati ricevono software/Box + Inner Circle incluso 12 mesi. Il partner conduce 3 masterclass durante la POC. Validazione simultanea di: prodotto, percorso formativo, concetto PT Evoluto, ruolo del partner. Risultato al mese 4: 10 storie reali, 10 testimonial, 3 masterclass registrate, dati aggregati, community funzionante.

**Fase 2 — Early Adopter con Inner Circle attivo (mesi 4-6).** Testimonial e contenuti della POC come leva di vendita. Il pitch ai nuovi clienti parte dal tangibile: "un click e il promemoria parte su WhatsApp. Vuoi vedere cosa fa il resto?" Il Fondatore che mostra a un collega come gestisce i promemoria con un click è il miglior venditore possibile — più efficace di qualunque demo tecnica. Network del partner apre le porte. Inner Circle disponibile per chi vuole il percorso completo. Webinar gratuito mensile come strumento di acquisizione (il partner conduce). Target: 15-20 clienti paganti, di cui 30% con Inner Circle.

**Fase 3 — Prezzo pieno e scala (mesi 7-12).** Tutti i canali attivi: contenuti educativi, community, webinar mensili, SEO, referral. Inner Circle consolidato con masterclass mensili esclusive. Il concetto PT Evoluto inizia a circolare nel settore. Target: 3-5 vendite al mese, base Inner Circle in crescita.

**Fase 4 — Espansione (Anno 2+).** Inner Circle a pieno regime. Presenza alle fiere di settore (RiminiWellness). Partnership con enti di formazione. Bundle Box + Tablet. Primo collaboratore operativo. Certificazione PT Evoluto come credenziale riconosciuta. Lancio versione inglese (Blocchi 1-2: interfaccia, esercizi, Safety Engine). Primi clienti internazionali tramite network del partner o canali diretti. Valutazione database nutrizionale per mercati target.

Il motore a lungo termine: il volano parte dalla POC, non dall'Anno 2. Le masterclass del partner creano il concetto di PT Evoluto. I Fondatori lo vivono e lo raccontano. I loro clienti notano la differenza. I colleghi chiedono "come fai?". Il passaparola parte. Ogni nuovo membro Inner Circle rafforza la community, che produce contenuto, che attrae nuovi membri. I costi di acquisizione scendono, il ricavo ricorrente sale. Dall'Anno 3 il ricorrente (PRO + Inner Circle) copre i costi operativi.

---

## 14. Cosa cerchiamo

### Industry Partner

Un professionista del settore fitness con esperienza, credibilità e un network attivo. Non un dipendente, non un consulente — un partner con incentivi allineati al progetto (equity + revenue share, zero costi fissi). Il suo ruolo: selezionare i Fondatori, presentare il prodotto al mercato, condurre masterclass, validare il posizionamento PT Evoluto.

### Sostenibilità personale del founder — NASpI anticipata

Il founder ha diritto alla liquidazione anticipata della NASpI (18-20 mesi residui, ~€900-1.000/mese). Dal 2026 l'erogazione avviene in due tranche (70% + 30%), per un totale netto stimato di €13.000-16.000. Questo importo copre interamente le riserve personali necessarie per i primi 24 mesi in tutti gli scenari, rendendo il business avviabile senza risparmi propri significativi. Dettaglio completo in `docs/business/FINANCIAL_MODEL.md` §8.

### Finanziamento (dopo la validazione della POC)

Dopo che i dati della POC confermano il modello (NPS, disponibilità a pagare, adozione), il canale prioritario è **Smart&Start Italia** (Invitalia): finanziamento a tasso zero fino a €1.5M, copertura 80-90%, a sportello (niente graduatorie). Richiede iscrizione come startup innovativa — FitManager qualifica per IP proprietaria (47K+ LOC, 7 motori scientifici) e spese R&D >15%.

Importo realistico: €50.000-100.000 per marketing strutturato, primo collaboratore, sviluppo Box, internazionalizzazione. Con dati POC reali, non con promesse. Roadmap: domanda al mese 6-7, erogazione al mese 10+.

La NASpI anticipata e Smart&Start sono cumulabili: la NASpI copre il founder, Smart&Start copre il business. Mappa completa dei fondi disponibili in `docs/business/FINANCIAL_MODEL.md` §9.

---

## Appendice

### A1 — Dettaglio prodotto

| Area | Cosa fa | Stato |
|---|---|---|
| CRM | Clienti, contratti, pagamenti, agenda, cassa — tutto in un profilo unico | Completo |
| Clinico | Anamnesi guidata 6 step, misurazioni, avatar 6 viste, punteggio prontezza | Completo |
| Allenamento | Workout builder 3 modalità, drag & drop, blocchi esercizi, export PDF. Database progettato per arricchimento continuo con contributi di professionisti certificati. | Completo |
| Nutrizione | 880 alimenti CREA, 210 ricette, 12 template LARN, piano settimanale | Completo |
| Operativo | Setup guidato, licenza HW-bound, backup/ripristino, diagnostica | Completo |
| Accesso | Portale anamnesi self-service, accesso remoto Tailscale | Completo |
| Comunicazione | WhatsApp semi-auto (wa.me), email SMTP automatiche, template messaggi | Completo |
| Portale Allenamento | Portale cliente: sessione del giorno, registrazione esecuzione, feedback, zero app | Completo |
| Workout Intelligence | Compliance, dose-response muscolo×muscolo, equilibri biomeccanici, alert predittivi | Completo |

500 esercizi, 940 relazioni (progressioni, regressioni, varianti), 47 condizioni cliniche, 80 regole Safety Engine.

### A2 — La FitManager Box

| Componente | Dettaglio |
|---|---|
| Hardware | Raspberry Pi 5, 4GB RAM, SD 64GB |
| Software | FitManager preinstallato |
| Connessione | WiFi + Ethernet, accesso remoto Tailscale |
| Consumo | ~5W (~€10/anno di corrente) |
| Backup | Automatico su chiavetta USB (notturno) |

| Voce | Valore |
|---|---|
| Costo totale per unità | ~€130-150 |
| Prezzo di vendita | €449 |
| Margine lordo | €299-319 (67-71%) |

Stato: architettura software compatibile ARM/Linux. Immagine Raspberry Pi dedicata richiede 2-3 settimane di sviluppo.

### A3 — P&L triennale dettagliato (scenario base)

**Ricavi (tre flussi):**

| Voce | Anno 1 | Anno 2 | Anno 3 |
|---|---|---|---|
| Licenze software | €4.278 | €5.727 | €7.719 |
| Box | €9.672 | €15.723 | €25.131 |
| Assistenza PRO | €950 | €3.700 | €7.300 |
| Inner Circle | €2.250 | €4.500 | €9.500 |
| **Fatturato totale** | **€17.150** | **€29.650** | **€49.650** |

**Costi diretti:**

| Voce | Anno 1 | Anno 2 | Anno 3 |
|---|---|---|---|
| Hardware Box | €3.600 | €5.250 | €8.400 |
| Installazione licenze | €660 | €575 | €465 |
| **Margine lordo** | **€12.890 (75%)** | **€23.825 (80%)** | **€40.785 (82%)** |

Il margine lordo migliora nel tempo perché il ricavo ricorrente (PRO + IC) ha margine 100% e cresce in percentuale del fatturato.

**Costi operativi:**

| Voce | Anno 1 | Anno 2 | Anno 3 |
|---|---|---|---|
| Fissi (commercialista, tool, varie) | €4.300 | €4.500 | €4.800 |
| Tirocinante/collaboratore | — | €4.000 | €9.200 |

Nota: ufficio/coworking (~€3.600) e marketing strutturato (~€2.400) sono previsti dalla Fase 4 (Anno 2+) e verranno inclusi quando i volumi lo giustificano. Non sono nelle proiezioni base per coerenza con le tabelle scenario.

**Riepilogo:**

| | Anno 1 | Anno 2 | Anno 3 |
|---|---|---|---|
| Fatturato | €17.150 | €29.650 | €49.650 |
| Margine lordo | €12.890 | €23.825 | €40.785 |
| Costi operativi | €4.300 | €8.500 | €14.000 |
| Compenso partner (20% prodotto + 35% ricorrente) | €3.910 | €7.160 | €12.450 |
| EBITDA | €4.680 | €8.165 | €14.335 |
| Tasse | €3.600 | €6.230 | €6.750 |
| **Netto founder** | **€1.080** | **€1.935** | **€7.585** |

### A4 — Le assunzioni chiave

| Codice | Assunzione | Stato | Validazione |
|---|---|---|---|
| P4 | PT perde 3-5h/sett in admin | Ipotesi | Questionario baseline POC |
| B7 | PT disposto a pagare €249-449 | Ipotesi critica | Willingness-to-pay POC |
| S4 | La Box risolve il problema mobile | Ipotesi forte | Test 2 Fondatori nella POC |
| G3 | Partner genera 8-12 lead/mese | Ipotesi | Primo trimestre partnership |
| G4 | Conversione demo-acquisto 20-25% | Ipotesi conservativa | Dati reali mesi 4-6 |
| B5 | Rinnovo assistenza 55-60% | Ipotesi | Dato reale Anno 2 |
| M2 | Segmento target 10-15.000 PT | Stima | Primi 6 mesi di vendita |
| IC1 | Inner Circle raggiunge 20% della base (base) | Ipotesi | Dato reale mesi 7-12 |
| IC2 | Le masterclass del partner generano adozione della categoria | Ipotesi forte | Metriche POC (vedi sezione 9) |
| WA1 | WhatsApp semi-auto riduce frizione iniziale e accelera adozione | Ipotesi forte | KPI attivazione POC (msg entro 24h) |
| WA2 | Trainer usano 15+ messaggi pre-compilati/settimana | Ipotesi | Dato reale POC giorni 15-75 |
| DB1 | Professionisti del settore disponibili a contribuire al database esercizi | Ipotesi forte | Primo contributo durante partnership/POC |
| INT1 | Versione inglese core (Blocchi 1-2) completabile entro 6 mesi dal lancio | Ipotesi | Valutazione tecnica in corso |
| WI1 | Clienti usano portale allenamento (7/10 attivi nella POC) | Ipotesi forte | Dato reale POC giorni 15-75 |
| WI2 | Workout Intelligence differenzia FitManager da ogni competitor | Ipotesi forte | Feedback POC + analisi competitor |

Ogni proiezione è conservativa. I ricavi Inner Circle sono inclusi dal mese 4 (post-POC) nelle configurazioni con partner. Senza partner, l'Inner Circle non è attivabile.

### A5 — Ecosistema community

La community ha tre livelli con identità nettamente separate: PRO mantiene il software vivo, Inner Circle fa crescere il professionista. Le masterclass e i webinar del partner sono esclusivi Inner Circle, non PRO.

**Livello 1 — Base (gratuita, inclusa nella licenza)**

Forum di supporto, knowledge base, annunci versioni, networking tra PT per città e specializzazione, onboarding guidato in 5 passi. Scopo: nessun licenziatario si sente solo.

**Livello 2 — PRO (€79/anno) — "Il tuo software resta vivo"**

| Contenuto | Frequenza |
|---|---|
| Aggiornamenti software (bugfix, miglioramenti) | Continui |
| Nuovi esercizi nel catalogo | Trimestrale (30-50 nuovi) |
| Nuovi alimenti nel database | Semestrale |
| Template schede scaricabili | Mensile (1-2 template) |
| Supporto prioritario (risposta <24h) | Sempre |
| Badge PRO nella community | Permanente |

Valore percepito: ~€300/anno per €79 (rapporto 3,8:1). Il motivo di rinnovo è pratico: il prodotto migliora. Se non rinnovi, il software funziona ancora ma smette di aggiornarsi.

Primi 30 clienti: 12 mesi inclusi. Dal 31° cliente: €79 parte all'acquisto. Primi rinnovi effettivi: dal mese 13.

**Livello 3 — Inner Circle (€249/anno) — "Diventa un PT Evoluto"**

Include tutto il PRO, più il percorso formativo condotto dall'Industry Partner:

| Contenuto | Frequenza | Conduce |
|---|---|---|
| Masterclass tematiche (45-60 min + Q&A) | Mensile | Industry Partner |
| Webinar "Chiedi all'esperto" | Mensile (alternato) | Industry Partner + ospiti |
| Mastermind group (max 30-50 membri) | Mensile (60-90 min) | Industry Partner |
| Casi studio dalla community | Mensile | Peer |
| Early access nuove feature | Ad ogni major release | Founder |
| Certificazione PT Evoluto | Annuale | Industry Partner |

Valore percepito: ~€800-900/anno per €249 (rapporto 3,4:1). Il motivo di acquisto è aspirazionale: crescita professionale, non aggiornamento software.

Attivo dal mese 4 (post-POC) per gli Early Adopter. Le masterclass partono durante la POC come contenuto per i 10 Fondatori (Inner Circle incluso nel prezzo Fondatore) e le registrazioni entrano nella libreria Inner Circle per i membri futuri.

**Il webinar gratuito mensile** resta come strumento di acquisizione anche quando l'Inner Circle è attivo. È il Touch 5 del funnel: il PT partecipa gratis, vede il valore, scopre che c'è un percorso più profondo. Non è in competizione con l'Inner Circle — è il suo meccanismo di alimentazione.

**Livello 4 — Mentorship (futuro, Anno 3+, €499-599/anno, max 15-20)**

Mentorship 1:1, co-creazione roadmap, eventi in presenza. Da definire quando la base Inner Circle raggiunge 30+ membri.

**Proiezione ricavi community (scenario base):**

| | Anno 1 | Anno 2 | Anno 3 |
|---|---|---|---|
| Membri PRO (paganti) | 12 | 47 | 92 |
| Membri Inner Circle | 9 | 18 | 38 |
| Ricavo PRO | €950 | €3.700 | €7.300 |
| Ricavo Inner Circle | €2.250 | €4.500 | €9.500 |
| **Totale ricorrente** | **€3.200** | **€8.200** | **€16.800** |
| % del fatturato totale | 19% | 28% | 34% |

Il ricorrente cresce dal 19% al 34% del fatturato in 3 anni. Questo è il pavimento che copre i costi operativi e rende il business progressivamente indipendente dalle nuove vendite.

### A6 — Piano B senza partner

POC ridotta a 5 Fondatori reclutati via LinkedIn e community fitness online. Go-to-market organico. Impatto: -40% volume vendite rispetto allo scenario base. ~24 clienti Anno 1. Fatturato ~€7.200. Il business non genera debito. Il partner accelera, non abilita.

### A7 — Struttura fiscale

**Anni 1-2:** P.IVA forfettaria. ATECO 62.10.00. Coefficiente redditività 67%. IRPEF 5% + INPS 26%. Carico effettivo ~21% del fatturato. Limite €85.000.

**Nota FitManager Box:** nel forfettario i costi hardware non sono deducibili. L'aliquota effettiva sul margine della Box (~31%) è più alta di quella sulla licenza software (~24%). Da valutare con il commercialista la separazione della vendita hardware o la transizione anticipata a regime ordinario.

**Anno 3+ (se fatturato >€30-40K):** transizione a regime ordinario o SRL. Costi deducibili, aliquota effettiva ~35%.

### A8 — Glossario

| Termine | Significato |
|---|---|
| ATECO | Classificazione attività economiche italiane |
| Box | Dispositivo dedicato basato su Raspberry Pi 5 per FitManager |
| CONI | Comitato Olimpico Nazionale Italiano |
| CREA | Ente che pubblica le tabelle nutrizionali ufficiali italiane |
| Cliff | Periodo minimo prima che l'equity maturi (12 mesi) |
| EBITDA | Utile prima di interessi, tasse e ammortamenti |
| Forfettario | Regime fiscale agevolato per P.IVA sotto €85.000 |
| LARN | Livelli di Assunzione di Riferimento di Nutrienti |
| NPS | Net Promoter Score — misura la raccomandabilità (-100/+100) |
| POC | Proof of Concept — test strutturato con 10 utenti |
| PT Evoluto | Categoria professionale proposta: trainer con scienza + dati + strumenti |
| Revenue share | Percentuale dei ricavi condivisa con il partner |
| Safety Engine | Motore che monitora 47 condizioni cliniche e segnala controindicazioni |
| SaaS | Software as a Service — modello con abbonamento e dati in cloud |
| Tailscale | Tecnologia di connessione sicura per accesso remoto |
| Vesting | Maturazione progressiva dell'equity nel tempo |
| WTP | Willingness to Pay — disponibilità a pagare |

---

*Business Plan FitManager Studio+ v4.3 — 27 marzo 2026*
*Tutti i numeri sono proiezioni basate su assunzioni dichiarate. Le assunzioni critiche verranno validate nella POC nei primi 90 giorni.*
