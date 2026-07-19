# Catalogo scenari reali — la giornata del PT/chinesiologo

**Data:** 2026-07-07 · **Scopo:** fondamento product di **ADR-025** (seduta singola, insoluto, listino, Portafoglio cliente) — principio del founder: «al PT serve PER DAVVERO». · **Metodo:** workflow 14 agenti — 6 lenti di generazione → dedup → mappatura copertura sul modello attuale (FDM + codice) → completeness critic (angolature italiane). **96 scenari** (S1-S79 catalogo + SC1-SC17 dal critic), **23 domande aperte** per l'ADR. Gemello di mercato: `docs/archive/RICERCA_COMPETITOR_WALLET_SEDUTE_SINGOLE_2026-07-07.md` (leggi W1-W11).

**Manutenzione:** vivo — ogni scenario nuovo incontrato sul campo si aggiunge qui; il futuro agente `pt-reality-auditor` valuta ogni spec contro questo catalogo.


---

## 1. TOP-15 — i più frequenti e scoperti (dove fa male OGGI)

| Id | Freq. | Scena | Copertura | Cosa serve |
|---|---|---|---|---|
| **S1** | quotidiana | Seduta singola pura — la cliente che non vuole vincoli | 🔴 assente | Creare dall'agenda una seduta SINGOLA con prezzo proprio, suggerito dallo storico di Federica ma libero; segnare pagata/non pagata in un tap con entrata in cassa automatica; storico sedute singole visibile nel profilo ac |
| **S2** | quotidiana | Le 21:30 del PT: quanto ho fatto oggi? | 🟡 parziale | Vista cassa «Oggi»: totale per metodo (contanti/POS/Satispay/bonifico), movimenti con nome cliente, ed evidenza delle sedute erogate oggi NON ancora pagate. Il rito di chiusura giornata in 30 secondi è la sensazione di c |
| **S3** | quotidiana | Contanti oggi, POS domani: il metodo cambia a ogni rata | 🟢 piena | Metodo di pagamento sul singolo movimento (mai sul contratto), registrazione dell'incasso in 10 secondi a bordo campo, cassa filtrabile per canale (contanti/POS/bonifico). |
| **S4** | quotidiana | «Quante me ne restano?» a fine seduta | 🟢 piena | Contatore crediti in tempo reale sul profilo — fatte / penali / residue, con le date — leggibile in 3 secondi, e resoconto inviabile via WhatsApp così PT e cliente hanno lo STESSO numero, con le sedute-penale esplicitate |
| **S5** | settimanale | «Ti pago giovedì» — seduta fatta, portafoglio a casa | 🔴 assente | Chiudere la seduta come EROGATA ma NON PAGATA in 2 tap, generando un insoluto con importo e data promessa. Alla seduta successiva dello stesso cliente il CRM deve mostrare il badge «45€ in sospeso da martedì 12» e propor |
| **S6** | settimanale | Valutazione iniziale del chinesiologo: €50 di servizio vero, non un'esca | 🔴 assente | La valutazione come voce di listino vendibile come seduta singola fuori contratto: incasso in cassa, evento agenda tipizzato, esito agganciato ad anagrafica/anamnesi. Deve restare visibile nello storico anche se poi nasc |
| **S7** | settimanale | Prova pagata €30 «che poi ti scalo dal pacchetto» | 🔴 assente | Registrare la prova come seduta singola con prezzo proprio (€30) incassata in cassa, e trasformare quell'importo in credito wallet spendibile sul contratto futuro: alla creazione del pacchetto il CRM segnala «Chiara ha € |
| **S8** | settimanale | «Quanto costa un pacchetto da 10?» — e il prezzo cambia a memoria | 🔴 assente | Un listino di riferimento (pacchetti, seduta singola, valutazione, prova) da cui partire per ogni preventivo, e lo storico dei prezzi realmente praticati per ciascun cliente. Il prezzo resta LIBERO, ma lo sconto diventa  |
| **S9** | settimanale | Domicilio con maggiorazione trasferta | 🔴 assente | Singola con prezzo base + voce maggiorazione domicilio dal listino (modificabile), totale chiaro in cassa con le due componenti, indirizzo/nota luogo sull'evento agenda; il prezzo pattuito con la Bianchi memorizzato e ri |
| **S10** | settimanale | Seduta online del cliente in trasferta | 🔴 assente | Seduta singola con modalità 'online' e prezzo proprio (voce di listino distinta dallo studio), incasso digitale legato alla seduta con stato in sospeso finché non arriva, e la seduta che conta nello storico allenamenti/a |
| **S11** | settimanale | Seduta di coppia: lei scala il credito, il marito integra | 🔴 assente | Un evento agenda con 2 partecipanti, ciascuno col proprio regime: credito contratto per Anna, singola da 25€ per Paolo; Paolo censito in 1 minuto con anagrafica e anamnesi minima (safety engine attivo anche su di lui); i |
| **S12** | settimanale | Mini-gruppo delle 18: tre quote, tre comportamenti di pagamento | 🔴 assente | Seduta con N partecipanti e quota individuale, stato pagamento PER TESTA (pagata / anticipata / insoluta); il prepagato di Elena come credito che si scala a presenza, il debito di Chiara visibile nel suo Portafoglio; il  |
| **S13** | settimanale | «Il bonifico te l'ho fatto ieri, giuro» | 🔴 assente | Stato intermedio della rata «dichiarato dal cliente — in attesa di riscontro» con data della dichiarazione: silenzia gli alert per 3-4 giorni lavorativi, poi, se l'incasso non è stato confermato, li riaccende con contest |
| **S14** | settimanale | «Tieni il resto» / «Non ho spicci» | 🔴 assente | Incasso a importo LIBERO sulla seduta con differenza esplicita e classificata in 1 tap: +5€ → «extra/mancia» in cassa (fuori dai conteggi contratto); −5€ → micro-insoluto oppure «abbuono» consapevole. La cassa deve ricon |
| **S15** | settimanale | La ricevuta al volo per la singola pagata in contanti | 🔴 assente | Dalla seduta singola già registrata, un click genera una ricevuta numerata (dati cliente, importo, data, metodo, dicitura forfettario) e la invia come PDF via WhatsApp; il movimento cassa nasce già collegato al documento |

---

## 2. CATALOGO COMPLETO (per lente)


### scenari:flussi-annessi (10 scenari)

**S2 — Le 21:30 del PT: quanto ho fatto oggi?** · *quotidiana* · 🟡 parziale
- **Scena:** Ultima seduta finita alle 21:00. Nel portafoglio ci sono 130€ in contanti, Satispay segna 90€, un bonifico «dovrebbe arrivare». Il PT in macchina vuole sapere tre cose: quanto ho incassato oggi, i contanti tornano, chi mancava all'appello?
- **Oggi (senza software):** Conta i contanti sul cruscotto e ricostruisce a memoria la giornata; se non torna, pazienza — non saprà mai dove ha perso il pezzo.
- **Cosa serve:** Vista cassa «Oggi»: totale per metodo (contanti/POS/Satispay/bonifico), movimenti con nome cliente, ed evidenza delle sedute erogate oggi NON ancora pagate. Il rito di chiusura giornata in 30 secondi è la sensazione di controllo quotidiana.
- **Rischio se manca:** Incassi in contanti che evaporano dalla memoria; sedute erogate e mai incassate scoperte settimane dopo, o mai.
- **Tocca:** cassa, agenda, sedute_singole, insoluto · **Copertura:** Il mastro movimenti_cassa è datato (data_effettiva) con metodo per movimento e stats/saldo esistono; mancano la vista-giornata per metodo e l'evidenza «erogato oggi non pagato» (le singole non esistono).

**S4 — «Quante me ne restano?» a fine seduta** · *quotidiana* · 🟢 piena
- **Scena:** Paolo, mentre si riveste: «quante me ne restano del pacchetto?». Il PT esita: nel conteggio ci sono anche un rinvio e un no-show con penale del mese scorso. Rispondere «boh, stasera controllo» davanti al cliente lo fa sembrare disorganizzato proprio sui soldi già incassati.
- **Oggi (senza software):** Quaderno con le crocette per cliente, o conteggio a memoria scrollando la chat WhatsApp delle prenotazioni.
- **Cosa serve:** Contatore crediti in tempo reale sul profilo — fatte / penali / residue, con le date — leggibile in 3 secondi, e resoconto inviabile via WhatsApp così PT e cliente hanno lo STESSO numero, con le sedute-penale esplicitate.
- **Rischio se manca:** Numeri diversi tra PT e cliente = discussione sulla penale e fiducia incrinata sul punto più sensibile: sedute già pagate.
- **Tocca:** contratto, agenda, comunicazioni · **Copertura:** crediti_usati è computed-on-read dal SSoT contract_state (occupazione = Programmato+Completato+penali, G7.8/ADR-017) con trasparenza erogato/occupazione nel dettaglio (R4/R5); manca solo l'invio del resoconto via WhatsApp.

**S15 — La ricevuta al volo per la singola pagata in contanti** · *settimanale* · 🔴 assente
- **Scena:** Martedì, 18:50. Marco finisce la seduta flash da 45€ e allunga i contanti negli spogliatoi: «mi fai la ricevuta che la tengo?». Il PT ha il blocchetto in macchina e il prossimo cliente alle 19:00.
- **Oggi (senza software):** Blocchetto ricevute cartaceo compilato a mano quando se lo ricorda, oppure «te la mando poi» e la lista degli incassi finisce in un messaggio WhatsApp a se stesso per il commercialista a fine mese.
- **Cosa serve:** Dalla seduta singola già registrata, un click genera una ricevuta numerata (dati cliente, importo, data, metodo, dicitura forfettario) e la invia come PDF via WhatsApp; il movimento cassa nasce già collegato al documento, mai due entità da riconciliare a mano.
- **Rischio se manca:** Ricevute promesse e mai emesse = figuraccia col cliente e buchi col commercialista; l'incasso in contanti dimenticato fa saltare la cassa di giornata.
- **Tocca:** sedute_singole, cassa, anagrafica, comunicazioni · **Copertura:** Nessuna entità documento/ricevuta né numerazione nel modello: il CashMovement non ha alcun riferimento a documenti fiscali.

**S16 — La fattura la fa il commercialista, non il CRM** · *settimanale* · 🔴 assente
- **Scena:** Il PT è forfettario e le fatture elettroniche le emette con l'app dell'Agenzia delle Entrate o col gestionale del commercialista. Nel CRM registra gli incassi, ma poi deve ricordare QUALI hanno già un documento e quali no; a fine mese manda al commercialista una lista scritta a mano. Variante: Sara col 10-sedute a rate chiede «mi mandi la fattura?» e il PT non sa se emettere per l'acconto, per ogni rata o una sola a saldo.
- **Oggi (senza software):** Doppia contabilità mentale CRM / blocchetto / app fatture, con buchi in mezzo e riconciliazione a memoria.
- **Cosa serve:** Il CRM non deve pretendere di essere il registro fiscale: su ogni movimento un flag «documento emesso» + riferimento esterno, e la lista mensile «incassi senza documento» pronta da girare al commercialista. Deve incastrarsi nel flusso fiscale esistente del PT, non sostituirlo.
- **Rischio se manca:** Incassi mai fatturati o fatturati due volte; e un PT che ABBANDONA il CRM se lo costringe a cambiare il rapporto col proprio commercialista.
- **Tocca:** cassa, rate, sedute_singole, contratto · **Copertura:** Nessun flag «documento emesso»/riferimento esterno su CashMovement, né vista «incassi senza documento» per contratto o periodo.

**S24 — «Quanto ti devo in tutto?» — il conto netto** · *settimanale* · 🟡 parziale
- **Scena:** Prima delle ferie Davide vuole «fare i conti»: una rata da 150€ scaduta, 2 singole extra mai pagate (90€), ma anche 30€ di wallet da un vecchio conguaglio. Il PT impiega dieci minuti tra quaderno e chat per arrivare a «fanno... 210€, credo».
- **Oggi (senza software):** Ricostruzione manuale su carta, spesso arrotondando «a favore del cliente per sicurezza» — cioè perdendo soldi per non litigare.
- **Cosa serve:** Il pannello Portafoglio deve dare UNA cifra netta: dovuto (rate scadute + insoluti da singole) meno wallet, con dettaglio esplodibile voce per voce, condivisibile via WhatsApp come mini-estratto conto.
- **Rischio se manca:** Arrotondamenti sistematici a perdere; oppure una cifra sbagliata in eccesso che scatena la contestazione.
- **Tocca:** wallet, insoluto, rate, sedute_singole, comunicazioni · **Copertura:** Rate scadute (overdue-rates) e wallet (GET /clients/{id}/crediti + rimborsi-da-erogare) esistono come viste separate; nessun pannello Portafoglio con cifra netta, e gli insoluti da singole non esistono.

**S25 — Il bonifico «SALDO ALLENAMENTI» da decifrare** · *settimanale* · 🟡 parziale
- **Scena:** Sul conto arrivano 175€ da «ROSSI LUCIA», causale «saldo». Il PT ha due Rossi tra i clienti, e Lucia è la mamma di un ragazzo che si allena. È la rata 2 di Matteo? Un anticipo? Il bonifico resta non attribuito per 4 giorni.
- **Oggi (senza software):** Scrolla l'home banking e incrocia a memoria; nei casi peggiori chiede al cliente «scusa, quel bonifico era per...?» — imbarazzante per entrambi.
- **Cosa serve:** Rate attese con importo e stato «in attesa bonifico»; associare l'accredito a rata/cliente in 10 secondi; vista «incassi attesi» per riconoscere al volo gli importi in arrivo, incluso il caso pagatore ≠ cliente.
- **Rischio se manca:** Bonifici accreditati ma mai registrati → rate che risultano scadute e solleciti a chi ha GIÀ pagato: il danno di fiducia peggiore del mancato incasso.
- **Tocca:** rate, cassa, anagrafica, comunicazioni · **Copertura:** Le rate attese con importo/scadenza e il forecast (entrate certe per mese) esistono; manca una vista riconciliazione «incassi attesi vs accrediti» e il pagatore≠cliente non è rappresentato.

**S38 — Il prezzo di favore che non deve girare** · *mensile* · 🔴 assente
- **Scena:** A Stefano, amico da dieci anni, il PT fa 35€ invece di 45€. Un giorno in sala Stefano chiacchiera con un cliente nuovo, che poi chiede: «ma quindi la seduta quanto costa DAVVERO?». Intanto il PT stesso, mesi dopo, non ricorda più a chi fa quale favore né perché lo aveva concesso.
- **Oggi (senza software):** Tutto a memoria: i prezzi di favore sono la regola non scritta più diffusa della categoria, e la più fonte di figuracce.
- **Cosa serve:** Prezzo per cliente con nota privata del motivo («amico storico», «mi ha portato 3 clienti»), visibile SOLO al PT; documenti e resoconti mostrano solo il prezzo di QUEL cliente, mai il listino generale. Il PT deve poter rispondere con coerenza in un secondo.
- **Rischio se manca:** Incoerenze imbarazzanti tra clienti che si parlano; sconti dimenticati che si perpetuano per anni senza più motivo, erodendo il margine.
- **Tocca:** listino, anagrafica, sedute_singole, contratto · **Copertura:** Nessun prezzo-per-cliente con motivo: solo note_interne libere che non alimentano alcun suggerimento né resoconto.

**S55 — «Mi mandi tutto quello che ti ho pagato quest'anno?»** · *mensile* · 🟡 parziale
- **Scena:** A novembre Chiara chiede l'elenco di tutti i pagamenti dell'anno «per i conti di casa» (o perché sospetta di aver pagato più del dovuto). Sono 2 pacchetti, 7 rate e 3 singole sparsi su 11 mesi e tre metodi di pagamento.
- **Oggi (senza software):** Il PT ricostruisce da WhatsApp e home banking, ci mette una sera intera e non è sicuro di aver preso tutto.
- **Cosa serve:** Estratto conto cliente per periodo — data, importo, metodo, riferimento (rata di quale contratto / singola di quale giorno) — un click, PDF, WhatsApp. Rispondere in un'ora invece che in tre giorni È la percezione di professionalità.
- **Rischio se manca:** Risposta lenta o bucata = sembrare disorganizzato proprio sul denaro; ogni discrepanza trovata dal cliente gioca contro il PT.
- **Tocca:** anagrafica, cassa, rate, sedute_singole, contratto, comunicazioni · **Copertura:** Ogni incasso è nel mastro legato a contratto/rata (+ GET /contracts/{id}/history e movimenti F1 per contratto); manca l'estratto conto per cliente/periodo esportabile in un click.

**S56 — «Perché me l'hai scalata se non sono venuto?» — la penale contestata** · *mensile* · 🟡 parziale
- **Scena:** Lorenzo avvisa alle 8:40 per la seduta delle 9:00: cancellazione tardiva, penale, credito scalato — policy detta a voce alla firma. Se ne accorge al rinnovo, dal conteggio: «mi hai fregato una seduta». Il PT deve difendere la regola senza passare per esattore.
- **Oggi (senza software):** Memoria contro memoria sull'orario del messaggio; nella maggior parte dei casi il PT regala la seduta per quieto vivere.
- **Cosa serve:** Lo stato Cancellato_Tardivo/No_Show con timestamp deve comparire nel resoconto crediti («seduta del 12/5: annullata alle 8:40 → penale da policy») e la policy scritta nel riepilogo contratto, mostrabile al cliente. La regola applicata da un sistema neutro pesa meno sul rapporto personale.
- **Rischio se manca:** Sedute-penale regalate sistematicamente (erosione silenziosa del margine) o un litigio da 40€ che brucia un cliente da 1.500€/anno.
- **Tocca:** agenda, contratto, comunicazioni · **Copertura:** Cancellato_Tardivo/No_Show occupano credito via SSoT (STATI_OCCUPAZIONE_CREDITO, G7.8-bis) con audit timestamp e trasparenza erogato/occupazione (R4/R5); manca un resoconto crediti condivisibile con la policy scritta.

**S78 — Gennaio: il commercialista vuole i numeri dell'anno** · *rara* · 🟡 parziale
- **Scena:** Il 20 gennaio il commercialista chiede il totale incassato 2026, possibilmente per mese, e quanto in contanti vs tracciato. Il PT ha l'agenda cartacea, i movimenti Satispay sull'app, i bonifici sull'home banking e un Excel abbandonato a marzo.
- **Oggi (senza software):** Un weekend intero a ricostruire incrociando quattro fonti; il numero finale è «verosimile», non certo.
- **Cosa serve:** Export incassi per periodo (anno/mese) con totali per metodo e per tipo (pacchetti / rate / singole), CSV + PDF, che torni col conto corrente senza archeologia. In regime forfettario l'incassato È la variabile fiscale: qui il PT non può permettersi «circa».
- **Rischio se manca:** Numeri sbagliati in dichiarazione, ore perse ogni anno, e la sensazione strisciante di non avere in mano la propria attività.
- **Tocca:** cassa, contratto, rate, sedute_singole · **Copertura:** Il mastro è completo (data_effettiva, metodo, categoria, tipo — asse cassa TASSONOMIA) con stats/andamento per periodo; manca l'export CSV/PDF con totali per metodo/tipo pronto per il commercialista.


### scenari:fuori-schema (13 scenari)

**S1 — Seduta singola pura — la cliente che non vuole vincoli** · *quotidiana* · 🔴 assente
- **Scena:** Federica, 42 anni, insegnante, viene 'quando riesce': una seduta ogni 10-15 giorni a 55€, e alla proposta del pacchetto risponde 'non farmi firmare niente'. Paga in contanti a fine seduta, a volte con Satispay. Per un PT con 30 clienti ce ne sono sempre 3-4 così: una singola al giorno è la norma, non l'eccezione.
- **Oggi (senza software):** Appuntamento fissato su WhatsApp, il contante finisce nel portafoglio insieme al resto della giornata; a fine mese il PT ricostruisce a memoria quante sedute ha fatto Federica per capirci qualcosa in fattura.
- **Cosa serve:** Creare dall'agenda una seduta SINGOLA con prezzo proprio, suggerito dallo storico di Federica ma libero; segnare pagata/non pagata in un tap con entrata in cassa automatica; storico sedute singole visibile nel profilo accanto ai vecchi contratti, così il fatturato per cliente è vero.
- **Rischio se manca:** Sedute dimenticate = incasso non registrato o non riscosso; il PT non sa dire quanto gli rende Federica in un anno e la cassa di fine giornata non quadra mai con l'agenda.
- **Tocca:** sedute_singole, agenda, cassa, listino, anagrafica · **Copertura:** Non esiste seduta con prezzo proprio fuori contratto: l'evento agenda senza id_contratto è possibile (event.py) ma non genera cassa né stato pagamento — è esattamente il buco che ADR-025 sta progettando.

**S9 — Domicilio con maggiorazione trasferta** · *settimanale* · 🔴 assente
- **Scena:** La signora Bianchi, 68 anni, post-protesi d'anca, si allena a casa sua: 50€ di seduta + 15€ di trasferta (20 minuti d'auto a tratta). Ogni tanto il figlio scrive per fissare 'due sedute questa settimana' e chiede conferma del prezzo.
- **Oggi (senza software):** Prezzo tutto-compreso detto a voce mesi fa; il PT non distingue mai quota seduta da quota trasferta e a fine mese fattura una cifra tonda 'a occhio'.
- **Cosa serve:** Singola con prezzo base + voce maggiorazione domicilio dal listino (modificabile), totale chiaro in cassa con le due componenti, indirizzo/nota luogo sull'evento agenda; il prezzo pattuito con la Bianchi memorizzato e riproposto a ogni nuova seduta.
- **Rischio se manca:** Maggiorazione dimenticata quando prenota il figlio ('erano 50 o 65?'): su 8 domicili al mese sono 120€ di margine eroso in silenzio, più figuracce sul prezzo.
- **Tocca:** sedute_singole, agenda, cassa, listino, anagrafica · **Copertura:** Nessun listino né componenti di prezzo (base+trasferta), nessuna seduta con prezzo; l'evento agenda ha solo note libere.

**S10 — Seduta online del cliente in trasferta** · *settimanale* · 🔴 assente
- **Scena:** Davide è a Francoforte 2 settimane per lavoro: giovedì fanno una seduta su Meet a 40€ invece dei 55€ in studio (prezzo diverso, stessa persona). Paga con Satispay dopo la call, quando si ricorda. Per il motore scientifico quella seduta è allenamento a tutti gli effetti.
- **Oggi (senza software):** Appuntamento sul Google Calendar personale, il pagamento digitale arriva sul conto slegato da tutto; la seduta online non entra in nessun conteggio, né economico né di allenamento.
- **Cosa serve:** Seduta singola con modalità 'online' e prezzo proprio (voce di listino distinta dallo studio), incasso digitale legato alla seduta con stato in sospeso finché non arriva, e la seduta che conta nello storico allenamenti/aderenza come le altre.
- **Rischio se manca:** Pagamenti digitali orfani impossibili da riconciliare; sedute online invisibili allo storico = analisi del carico e compliance falsate.
- **Tocca:** sedute_singole, agenda, cassa, listino, comunicazioni · **Copertura:** Solo l'evento agenda esiste (e conta per storico/recency); tutto il lato economico — prezzo per modalità, incasso legato alla seduta, stato in sospeso — è assente.

**S11 — Seduta di coppia: lei scala il credito, il marito integra** · *settimanale* · 🔴 assente
- **Scena:** Anna è cliente con pacchetto; il marito Paolo si aggrega 'ogni tanto' e si allenano insieme. La seduta di coppia vale 70€: Anna scala il suo credito da 45€ e Paolo dovrebbe integrare 25€. Paolo non è nemmeno censito nel CRM e non ha mai compilato un'anamnesi.
- **Oggi (senza software):** Mental math e WhatsApp: 'tu mi devi 25'. Paolo paga quando si ricorda, il PT segna su carta o non segna; l'anamnesi di Paolo semplicemente non esiste.
- **Cosa serve:** Un evento agenda con 2 partecipanti, ciascuno col proprio regime: credito contratto per Anna, singola da 25€ per Paolo; Paolo censito in 1 minuto con anagrafica e anamnesi minima (safety engine attivo anche su di lui); incassi e insoluti separati per persona.
- **Rischio se manca:** Responsabilità professionale (Paolo si fa male senza screening) e integrazioni mai riscosse che a fine anno sono centinaia di euro; il pacchetto di Anna che assorbe di nascosto il costo di due persone.
- **Tocca:** sedute_singole, contratto, agenda, cassa, anagrafica, insoluto · **Copertura:** Event ha un solo id_cliente (event.py) e il denaro passa solo da contratti/rate: nessun secondo partecipante con regime proprio né quota integrativa.

**S12 — Mini-gruppo delle 18: tre quote, tre comportamenti di pagamento** · *settimanale* · 🔴 assente
- **Scena:** Ogni martedì alle 18 il PT tiene un mini-gruppo con Sara, Elena e Chiara: 90€ a seduta, 30€ a testa. Elena paga il mese anticipato, Chiara paga volta per volta e stasera 'non ho contante, ti giro dopo', Sara ha anche un pacchetto individuale che NON c'entra col gruppo e non va contaminato.
- **Oggi (senza software):** Foglio Excel (o quaderno) con presenze del gruppo e crocette su chi ha pagato; la quota di Chiara resta appesa e viene chiesta con imbarazzo settimane dopo, quando ormai il conto è confuso.
- **Cosa serve:** Seduta con N partecipanti e quota individuale, stato pagamento PER TESTA (pagata / anticipata / insoluta); il prepagato di Elena come credito che si scala a presenza, il debito di Chiara visibile nel suo Portafoglio; il pacchetto individuale di Sara isolato dal gruppo.
- **Rischio se manca:** Il PT incassa 60€ su 90€ e non se ne accorge; le quote perse nel mucchio diventano soldi condonati e la richiesta tardiva avvelena il clima del gruppo.
- **Tocca:** sedute_singole, agenda, cassa, insoluto, wallet, comunicazioni · **Copertura:** Nessun evento multi-partecipante né quota/stato pagamento per testa; il prepagato di gruppo non è rappresentabile (wallet solo da terminazione, insoluto inesistente).

**S21 — Le sedute ponte a pacchetto esaurito, rinnovo non ancora firmato** · *settimanale* · 🟡 parziale
- **Scena:** Giulia ha bruciato mercoledì la dodicesima e ultima seduta del trimestrale, il rinnovo lo firma 'dopo le vacanze', ma vuole allenarsi lunedì e giovedì della settimana ponte. Due sedute nel limbo: il vecchio contratto è esaurito, il nuovo non esiste ancora. Su 30 clienti c'è SEMPRE qualcuno tra due contratti.
- **Oggi (senza software):** Il PT le fa fare lo stesso e 'le mettiamo nel prossimo pacchetto', segnato su un post-it o da nessuna parte; al rinnovo nessuno ricorda se erano 1 o 2, e si decide a sensazione.
- **Cosa serve:** Scelta esplicita alla creazione: singola pagata subito OPPURE singola 'da assorbire nel prossimo contratto' che resta tracciata come pendenza; alla creazione del rinnovo il CRM ripropone le sedute ponte da conteggiare (scalarle dai crediti o farsele pagare), decisione registrata.
- **Rischio se manca:** Sedute regalate involontariamente (2 × 45€ = 90€ evaporati ogni volta) o litigio 'quelle due le avevamo già contate' proprio nel momento delicato del rinnovo.
- **Tocca:** sedute_singole, contratto, insoluto, agenda, comunicazioni · **Copertura:** L'evento PT senza contratto esiste (escape hatch del credit guard in create_event); la pendenza economica delle sedute ponte e il riassorbimento nel rinnovo non sono tracciati.

**S40 — Il no-show sulla seduta singola (nessun credito da bruciare)** · *mensile* · 🟡 parziale
- **Scena:** Ilaria, cliente saltuaria a sedute singole, prenota il martedì 18:30 e non si presenta, telefono muto. Nel pacchetto la penale scala il credito; qui non c'è NESSUN credito da scalare. Il PT ha perso un'ora da 55€ e deve decidere: gliela addebita? Sorvola? Metà penale?
- **Oggi (senza software):** Sfogo su WhatsApp e nessuna regola: alla prima si sorvola, alla seconda 'la prossima me la paghi doppia' detto a sentimento, con criteri diversi per ogni cliente.
- **Cosa serve:** Stato No_Show anche sulla singola con scelta esplicita e tracciata: condonata / addebitata come insoluto a importo pieno / penale ridotta da listino; contatore no-show nel profilo per decidere con dati e applicare a tutti la stessa policy.
- **Rischio se manca:** Politica incoerente tra clienti (che tra loro parlano) percepita come ingiustizia; ore perse mai quantificate, quindi mai difese.
- **Tocca:** sedute_singole, insoluto, agenda, comunicazioni, listino · **Copertura:** Lo stato No_Show è marcabile anche su eventi senza contratto (campo stato generico), ma senza credito da bruciare non ha alcuna conseguenza economica: né penale a listino né insoluto fuori contratto.

**S41 — Doppia seduta pre-partenza: una a credito, una fuori** · *mensile* · 🟡 parziale
- **Scena:** Marco parte 3 settimane per lavoro e chiede il sabato una doppia: 9:00 e 10:00 back-to-back. Nel pacchetto gli resta 1 solo credito: la prima seduta scala il credito, la seconda è fuori schema. Il PT decide al volo: prezzo pieno 55€ o 'la seconda te la faccio a 40'?
- **Oggi (senza software):** Prezzo deciso a voce sul momento, incasso contante unico mischiato al resto della giornata; in agenda personale c'è un solo blocco da 2 ore senza distinzione.
- **Cosa serve:** Nella stessa giornata una seduta a scalare dal contratto e una SINGOLA con prezzo libero (consigliato dallo storico), due righe distinte in agenda e in cassa; nel profilo di Marco deve essere ovvio quale seduta ha scalato cosa.
- **Rischio se manca:** La seconda seduta segnata per errore sul contratto: crediti che vanno in negativo o bruciano il rinnovo, e 40€ incassati che non corrispondono a nessuna riga — conteggi e cassa sballati.
- **Tocca:** sedute_singole, contratto, agenda, cassa, listino · **Copertura:** La prima scala il contratto (credit guard) e la seconda può già essere evento senza contratto (escape hatch); ma la seconda non ha prezzo/incasso collegato — 40€ senza riga di cassa riconciliabile.

**S42 — La seduta regalata per farsi perdonare** · *mensile* · 🟡 parziale
- **Scena:** Il PT annulla alle 7:40 la seduta delle 8:00 di Roberta per un'emergenza familiare. Per scusarsi le scrive 'la prossima te la offro io'. Quella seduta omaggio va erogata davvero, ma NON deve scalare crediti del pacchetto né generare un incasso fantasma.
- **Oggi (senza software):** Promessa a voce su WhatsApp; tre settimane dopo nessuno dei due ricorda se l'omaggio è già stato consumato, e nel dubbio o si regala due volte o si scala un credito pagato.
- **Cosa serve:** Seduta singola a 0€ con motivo esplicito ('omaggio compensativo'), che non tocca i crediti contratto e non sporca la cassa ma resta nello storico allenamenti; promemoria 'Roberta ha 1 omaggio da consumare' nel profilo, log nel registro comunicazioni.
- **Rischio se manca:** Omaggio consumato due volte, oppure credito del pacchetto scalato per una seduta promessa gratis: pochi euro, ma è esattamente il tipo di errore che incrina la fiducia.
- **Tocca:** sedute_singole, agenda, contratto, comunicazioni · **Copertura:** Un evento senza contratto non scala crediti e non tocca la cassa (il comportamento giusto); mancano la causale «omaggio» e il promemoria «da consumare» sul profilo.

**S43 — Lo scambio col fisioterapista (barter)** · *mensile* · 🟡 parziale
- **Scena:** Il PT allena Stefano, fisioterapista, il lunedì alle 7:00; in cambio Stefano gli tratta la spalla il giovedì. Zero euro che girano, ma lo slot è uno slot vero da 55€ e Stefano è un cliente vero, con anamnesi e progressi da tracciare.
- **Oggi (senza software):** Nessuna traccia: appuntamenti a voce, il 'saldo scambi' vive nella testa di entrambi ('mi deve ancora un trattamento') finché uno dei due non ha la sensazione di rimetterci.
- **Cosa serve:** Seduta singola a 0€ con causale 'scambio/prestazione reciproca' che non sporca la cassa ma resta nello storico e occupa l'agenda come slot pieno; nota libera sul controvalore; il PT deve poter vedere quante ore l'anno regala in scambi.
- **Rischio se manca:** 2 scambi al mese = ~1.300€/anno di valore erogato senza consapevolezza; squilibrio dello scambio invisibile finché non diventa risentimento tra colleghi.
- **Tocca:** sedute_singole, agenda, anagrafica, cassa · **Copertura:** L'evento senza contratto occupa agenda e storico del cliente; nessuna causale «scambio» né report del valore/ore regalate.

**S46 — Il prezzo vecchio del cliente che torna: 45€ contro listino 60€** · *mensile* · 🟡 parziale
- **Scena:** Il listino è salito da 45€ a 60€ in due anni. Torna Giorgio, fermo dal 2024, per una singola: lui è rimasto ai 45€ ('come l'altra volta, no?'). Il PT deve decidere in 3 secondi al telefono se difendere i 60€ o concedere il prezzo storico. Variante: da settembre la singola sale ma a 3 clienti storici il PT vuole tenere il prezzo bloccato «a vita».
- **Oggi (senza software):** Decide d'impulso, quasi sempre al ribasso, e il prezzo concordato non viene scritto: alla singola successiva la cifra è di nuovo in discussione da capo.
- **Cosa serve:** Alla creazione della singola il CRM mostra insieme il listino attuale E lo storico prezzi di Giorgio (contratti e singole passate); importo libero come da decisione founder, ma la cifra scelta viene memorizzata e riproposta come riferimento per le prossime.
- **Rischio se manca:** Erosione silenziosa del listino (ogni ritorno rinegozia al ribasso) e incoerenze tra clienti che si parlano — il PT scopre di avere 5 prezzi diversi per la stessa ora.
- **Tocca:** sedute_singole, listino, anagrafica, cassa · **Copertura:** Lo storico contratti (con prezzo_totale) è consultabile per cliente; nessun listino con validità temporale né prezzo consigliato/memorizzato per la singola (che non esiste).

**S58 — Il 'pacchettino' a voce: 3 sedute a 150€, né contratto né singole** · *mensile* · 🟢 piena
- **Scena:** Cristina non vuole il trimestrale ma nemmeno pagare volta per volta: 'facciamo 3 sedute a 150€ e vediamo come va'. Paga 150€ subito in contanti. Non è un contratto vero (niente scadenza, niente rate) ma nemmeno tre singole slegate: è la terra di nessuno in cui i software affondano.
- **Oggi (senza software):** 150€ in cassa (o in tasca), il conto delle 3 sedute su un post-it o ricostruito in chat ('questa è la seconda, giusto?'); la terza a volte si regala nel dubbio.
- **Cosa serve:** Una via a 1 tap: micro-contratto istantaneo (3 crediti, 150€, zero burocrazia) OPPURE prepagato wallet da 150€ che le tre singole scalano; in entrambi i casi contatore residuo sempre visibile al PT e comunicabile a Cristina, incasso anticipato riconciliato con l'erogato.
- **Rischio se manca:** La terza seduta contesa o regalata; 150€ incassati subito che non corrispondono a nulla di tracciato = cassa gonfia oggi, seduta dovuta domani, e nessuno che se lo ricorda.
- **Tocca:** sedute_singole, contratto, wallet, cassa, agenda · **Copertura:** È già un contratto normale del modello attuale: 3 crediti, prezzo 150, acconto pieno (ENTRATA atomica), senza scadenza — contatore residuo e cassa coerenti per costruzione; resta solo la UX «1 tap».

**S63 — Open day con gettone prova scalabile** · *rara* · 🔴 assente
- **Scena:** Sabato mattina open day: 6 persone, 10€ a testa di 'gettone prova', con la promessa 'se ti iscrivi entro 7 giorni te li scalo dal pacchetto'. Il PT incassa 60€ in contanti nel marsupio; due partecipanti firmano la settimana dopo.
- **Oggi (senza software):** Lista nomi su un foglio, contanti alla rinfusa, la promessa del gettone affidata alla memoria; al momento della firma è il cliente a dover dire 'avevi detto che i 10€ me li scalavi'.
- **Cosa serve:** Evento di gruppo con N partecipanti prospect e quota a testa in cassa; per chi firma, il gettone diventa automaticamente credito wallet applicato al contratto; per gli altri, contatto e follow-up tracciati.
- **Rischio se manca:** Gettoni promessi e dimenticati = figuraccia proprio in fase di firma; 60€ di contanti da evento mai riconciliati con la cassa.
- **Tocca:** sedute_singole, cassa, wallet, anagrafica, contratto, comunicazioni · **Copertura:** Né eventi multi-partecipante, né prospect, né wallet caricabile da incasso: nulla dell'open day è rappresentabile oggi.


### scenari:interruzioni-chiusure (16 scenari)

**S23 — Lombalgia, «mi fermo 3 settimane»: scadenza e rate congelate insieme** · *settimanale* · 🟡 parziale
- **Scena:** Elena si blocca con una lombalgia acuta: il medico prescrive 3 settimane di stop. Il suo trimestrale scade fra 5 settimane con 9 sedute residue, e fra 10 giorni scade una rata da €200. Se tutto continua a correre, Elena perde sedute pagate E riceve un sollecito mentre è a letto col Voltaren.
- **Oggi (senza software):** «Tranquilla, allunghiamo e la rata la vediamo quando torni» — non scritto da nessuna parte. Alla ripresa si discute su quanto fosse l'accordo, e su una base di 30 clienti c'è sempre qualcuno in pausa: le proroghe verbali si accumulano.
- **Cosa serve:** Sospensione breve con data di ripresa che slitta INSIEME scadenza contratto e piano rate, congela penali e prenotazioni e mette in pausa i solleciti. Alla ripresa tutto riparte esattamente da dov'era, per iscritto.
- **Rischio se manca:** Il sollecito arrivato a una cliente ferma per infortunio è il modo più rapido per passare da professionista a esattore. E la nebbia delle proroghe verbali su 30 clienti è esattamente il punto in cui il PT smette di sentirsi in controllo.
- **Tocca:** contratto, rate, agenda, comunicazioni · **Copertura:** Estensione data_scadenza (auditata, con auto-cap rate) e spostamento della singola rata esistono come atti separati; nessuna sospensione one-gesture che congeli insieme scadenza, rate e solleciti.

**S52 — Sparito da 5 settimane: ha consumato più di quanto ha pagato** · *mensile* · 🟡 parziale
- **Scena:** Andrea ha fatto 12 sedute su 20 ma versato solo €400 su €800 (2 rate su 4): ha già consumato €80 di lavoro mai pagato, più 8 crediti teoricamente ancora prenotabili. Non risponde a 3 WhatsApp e a una chiamata da 5 settimane.
- **Oggi (senza software):** Il PT scrolla la chat per ricostruire quante sedute ha fatto davvero, tiene il conto a memoria e dopo il terzo messaggio a vuoto rinuncia. Il contratto resta «aperto» sul quaderno per mesi, come una finestra spalancata.
- **Cosa serve:** Una vista esposizione (valore consumato vs versato) che dica QUANTO gli deve davvero; terminazione d'ufficio con la differenza in crediti-da-incassare; e lo stato insoluto che riemerge da solo se Andrea un giorno riprenota.
- **Rischio se manca:** Senza il numero esatto il PT o lascia perdere (regala €80-200 a episodio, e succede ogni mese) o sollecita la cifra sbagliata. E se Andrea torna fra un anno, nessuno ricorda che se n'era andato col debito.
- **Tocca:** contratto, rate, insoluto, agenda, comunicazioni · **Copertura:** GET /settlement-preview espone consumato-vs-versato e la terminazione A_CREDITO crea il receivable crediti_terminazione (worklist aging crediti-da-incassare, G7.10); manca la riemersione automatica del sospeso alla riprenotazione.

**S53 — Febbre a 38.5: saltano le 6 sedute di domani** · *mensile* · 🟡 parziale
- **Scena:** Martedì sera il PT ha la febbre: mercoledì saltano 6 sedute (Anna alle 8, Piero alle 9:30, e così via). Nessuna deve scalare crediti né generare penali, tutte vanno riprogrammate, e due clienti vanno avvisati subito perché arrivano da fuori città.
- **Oggi (senza software):** Sei messaggi WhatsApp scritti a mano dal letto, sedute cancellate «poi sistemo». Il giovedì il PT non ricorda più a chi doveva la riprogrammazione: una delle sei finisce dimenticata.
- **Cosa serve:** Cancellazione della giornata in un gesto con causale «PT indisponibile» (zero penali, zero crediti scalati), una lista «da riprogrammare» che resta accesa finché ogni seduta non ha una nuova data, e messaggi di avviso precompilati.
- **Rischio se manca:** La seduta dimenticata è quella del cliente che ci resta male in silenzio e non lo dice. E se per errore il credito viene scalato lo stesso, il PT scopre il buco solo quando il cliente protesta a fine pacchetto — figuraccia doppia.
- **Tocca:** agenda, comunicazioni, contratto · **Copertura:** La cancellazione senza penale esiste per-evento (Cancellato/Rinviato liberano il credito, ADR-017) e i template WhatsApp ci sono; nessun gesto di giornata né lista «da riprogrammare» persistente.

**S60 — «Le mie 4 sedute ci sono ancora?»: riaprire il contratto chiuso** · *mensile* · 🟢 piena
- **Scena:** Cristina aveva chiuso a febbraio per un cambio turni, con 4 sedute residue rimaste in sospeso. A giugno torna: «riprendiamo? Avevo ancora delle sedute, no?». Il PT deve decidere se riaprire il vecchio contratto ripristinando i crediti o proporle qualcosa di nuovo.
- **Oggi (senza software):** «Mi pare fossero 3… o 4?» — controllo sul quaderno vecchio e, per non litigare, ci si fida della memoria della cliente (che ricorda sempre una seduta in più).
- **Cosa serve:** Riapertura del contratto con ripristino ESATTO dello stato fotografato alla chiusura (crediti, versato, conguagli già erogati), oppure conversione consapevole del residuo in wallet o sedute singole — con lo storico immutabile a fare da arbitro.
- **Rischio se manca:** Ogni «mi pare fossero 4» a favore del cliente è una seduta regalata (~€45), e capita ogni mese. Nell'altra direzione, una seduta negata per sbaglio a una cliente onesta vale la disdetta e una recensione avvelenata.
- **Tocca:** contratto, wallet, sedute_singole, agenda · **Copertura:** POST /reopen è l'inverso esplicito state-driven (rate ripristinate via chiusa_da_terminazione, residuo ricalcolato net-aware, receivable/wallet annullati) con GET /reopen-preview e storico/cassa immutabili (ADR-019).

**S64 — Due settimane di ferie del PT: le scadenze devono dormire con lui** · *rara* · 🔴 assente
- **Scena:** Il PT chiude dal 10 al 24 agosto. Nessuno deve perdere niente: zero penali, zero crediti scalati, e i 6 contratti con scadenza nel periodo devono slittare di 2 settimane senza che nessun cliente debba chiederlo.
- **Oggi (senza software):** Blocco agenda a memoria, messaggio broadcast su WhatsApp, e a settembre il conto delle estensioni «a occhio» — di solito a favore del cliente, mai del PT.
- **Cosa serve:** Un periodo di chiusura dichiarato UNA volta che blocca le prenotazioni, protegge i crediti e slitta automaticamente le scadenze di tutti i contratti attivi. Al rientro l'agenda riparte pulita, senza code da sistemare.
- **Rischio se manca:** Ogni ferie non gestita erode 1-2 settimane di valore contrattuale spalmato su tutti i clienti attivi: centinaia di euro l'anno di lavoro regalato senza che nessuno se ne accorga — PT compreso.
- **Tocca:** agenda, contratto, rate · **Copertura:** Nessun periodo di chiusura dichiarabile che sposti scadenze in blocco; esistono solo estensioni manuali contratto per contratto (update data_scadenza).

**S65 — Crociato rotto a metà pacchetto: sospendere o chiudere?** · *rara* · 🟡 parziale
- **Scena:** Marco, 34 anni, si rompe il crociato a calcetto. Ha un pacchetto da 24 sedute a €960: ne ha fatte 10 e ha versato 2 rate su 4 (€480). L'ortopedico parla di 7-8 mesi di stop. Marco chiede al PT: «e i miei soldi? E le rate che ti devo ancora?»
- **Oggi (senza software):** WhatsApp «ci sentiamo quando stai meglio», un post-it «Marco: restano 14, ha pagato metà» che dopo 8 mesi non si trova più. Le 2 rate rimanenti restano in un limbo verbale.
- **Cosa serve:** Poter scegliere tra due strade chiare: sospensione lunga (scadenza e piano rate congelati, crediti intatti, data ripresa indicativa) oppure terminazione con conguaglio pro-rata delle 14 sedute residue (rimborso, wallet o crediti-da-incassare). Lo stato deve essere fotografato e leggibile identico fra 8 mesi.
- **Rischio se manca:** Dopo 8 mesi nessuno ricorda l'accordo: Marco pretende 14 sedute, il PT ne ricorda 12, e le 2 rate mai versate diventano una discussione che brucia un cliente affezionato. O il PT regala ~€100 di sedute, o perde il cliente al rientro.
- **Tocca:** contratto, rate, wallet, agenda, comunicazioni · **Copertura:** La strada terminazione è completa (conguaglio pro-sedute + rimborso/wallet/receivable, G7.3-G7.10); la sospensione lunga con congelamento di scadenza e rate non esiste (solo Estendi manuale).

**S66 — Gravidanza: due mesi adattati, poi stop fino a data ignota** · *rara* · 🟡 parziale
- **Scena:** Giulia, 31 anni, comunica la gravidanza al 3° mese, a metà di un annuale da €1.800 pagato al 60%. Vuole continuare 8 settimane con lavoro adattato, poi fermarsi fino a dopo il parto — ripresa «boh, marzo? aprile?». E l'anamnesi cambia da subito, non alla ripresa.
- **Oggi (senza software):** Accordo a voce, nota sul quaderno «Giulia riprende in primavera», rate rimanenti «ne riparliamo». L'anamnesi aggiornata vive solo nella testa del PT durante le 8 settimane adattate.
- **Cosa serve:** Sospensione a data aperta con scadenza contratto e rate congelate; aggiornamento anamnesi che il safety engine usa GIÀ nelle settimane adattate; un promemoria di ricontatto a mesi di distanza, senza dover ricordare nulla a memoria.
- **Rischio se manca:** La scadenza annuale corre durante lo stop e a marzo il contratto risulta «scaduto» con ~€700 di sedute non godute: o il PT regala mesi di valore, o incrina la fiducia di una cliente che sarebbe tornata con il passaparola delle neomamme.
- **Tocca:** contratto, rate, anagrafica, agenda, comunicazioni · **Copertura:** L'anamnesi aggiornabile alimenta subito il safety engine e l'estensione scadenza manuale esiste (poi il SOSPESO ha comunque una worklist); nessuna sospensione a data aperta con pausa rate/solleciti né promemoria di ricontatto a mesi.

**S67 — Trasferimento a Milano: rimborso, wallet o «le tengo se torno»?** · *rara* · 🟡 parziale
- **Scena:** Luca ha pagato per intero un pacchetto 20 sedute da €700 e viene trasferito a Milano con 9 sedute residue (valore pro-rata €315). Al bancone chiede: «mi ridai i soldi o me le tieni buone per quando scendo?». Il PT propone €150 di bonifico subito e €165 di credito se torna.
- **Oggi (senza software):** Calcolo sulla calcolatrice del telefono, bonifico arrotondato «a sentimento», il credito residuo scritto in una chat WhatsApp che tra 6 mesi è sepolta sotto duemila messaggi.
- **Cosa serve:** Terminazione con conguaglio pro-rata calcolato dal sistema, split esplicito rimborso (USCITA di cassa tracciata) + wallet, e il wallet visibile per sempre nel Portafoglio di Luca — anche quando ricompare dopo un anno.
- **Rischio se manca:** L'arrotondamento a sentimento costa 20-50€ a episodio; il credito promesso a voce o viene dimenticato (cliente bruciato al ritorno) o viene ricordato più alto di quanto era (il PT paga due volte la stessa cosa).
- **Tocca:** contratto, wallet, cassa, comunicazioni · **Copertura:** La terminazione CREDITO_CLIENTE copre esattamente lo split: rimborso editabile [0..credito] in USCITA tracciata + resto a wallet crediti_cliente visibile per sempre (G8.1/ADR-020); manca solo l'applicazione del wallet a futuri acquisti (G8.2 in panchina).

**S68 — Recesso dopo 5 sedute: a che prezzo conto quelle fatte?** · *rara* · 🟡 parziale
- **Scena:** Federica ha firmato un 30 sedute a €1.500 (€50/seduta) e versato €800 tra acconto e prima rata. Dopo 5 sedute molla: «non fa per me, rivoglio i soldi». Il PT vuole contare le 5 sedute consumate a €65 (prezzo della singola), non a €50: rimborso €475, non €550. Federica non è d'accordo.
- **Oggi (senza software):** Trattativa a voce al bancone, due calcoli diversi su due telefoni, e il PT che cede €75 pur di chiudere la scena imbarazzante davanti agli altri clienti.
- **Cosa serve:** Conguaglio di terminazione parametrico (sedute consumate a prezzo pieno di listino vs pro-rata pacchetto), un prospetto chiaro da mostrare o inviare che espliciti il calcolo, e l'uscita di cassa o il wallet registrati con quella causale.
- **Rischio se manca:** Senza un calcolo «del sistema» da mostrare, ogni recesso è una trattativa personale: il PT perde 50-100€ a episodio o passa per tirchio — e un recesso raccontato male in giro costa più del rimborso stesso.
- **Tocca:** contratto, listino, rate, cassa, wallet · **Copertura:** compute_settlement + GET /settlement-preview danno il prospetto e il rimborso/wallet sono tracciati; ma la valorizzazione (listino pieno vs pro-rata) è DECISIONE APERTA — policy pro_sedute PROVISIONAL gated dal tributarista (FDM §3.1), e il listino non esiste.

**S69 — Agosto: 8 clienti su 15 si fermano tra le 3 e le 6 settimane** · *rara* · 🟡 parziale
- **Scena:** Tra fine luglio e settembre 8 clienti sospendono in date diverse: chi 3 settimane in Salento, chi tutto agosto, chi «torno dopo il 10 settembre, forse». Quattro hanno contratti con scadenza che continuerebbe a correre e due hanno rate in scadenza a Ferragosto.
- **Oggi (senza software):** Mappa mentale più chat WhatsApp sparse. A settembre il PT «fa finta di niente» sulle scadenze sforate regalando estensioni, e insegue a voce le rate di agosto.
- **Cosa serve:** Sospendere N contratti ciascuno con le proprie date, con slittamento automatico di scadenze e rate, e una vista «chi rientra quando» per ricostruire l'agenda di settembre in un pomeriggio invece che in una settimana.
- **Rischio se manca:** Quattro scadenze regalate = 3-4 settimane di lavoro non pagato ogni anno, invisibili perché spalmate. E il cliente dimenticato al rientro («non mi hai più scritto») è esattamente quello che a ottobre non rinnova.
- **Tocca:** contratto, rate, agenda, comunicazioni · **Copertura:** Estensioni scadenza e spostamenti rate esistono solo per singolo contratto (e il SOSPESO finisce comunque in worklist); nessuna sospensione multipla né vista «chi rientra quando».

**S71 — «Le mie sedute le fa mia moglie»: il residuo che cambia corpo** · *rara* · 🟡 parziale
- **Scena:** Sandro si opera alla cuffia dei rotatori con 10 sedute residue già pagate (valore €400). Chiede: «le fa Paola, mia moglie, così non buttiamo i soldi». Paola non è mai stata cliente: zero anagrafica, zero anamnesi — e una tiroidite che il PT scoprirebbe per caso alla terza seduta.
- **Oggi (senza software):** Il PT accetta a voce e spunta le sedute di Paola sul conteggio di Sandro: la contabilità di Sandro è falsata e Paola resta invisibile al sistema e al safety engine.
- **Cosa serve:** Chiudere il contratto di Sandro convertendo il residuo in €400 di wallet, spendibili su un contratto o su sedute singole intestate a PAOLA — che nasce come cliente vera con la propria anamnesi — mantenendo tracciata la provenienza dei soldi.
- **Rischio se manca:** Allenare una persona senza anamnesi «perché tanto sono le sedute del marito» è il peggior buco di safety possibile. E a fine giro nessuno sa più se le 10 sedute erano di Sandro, di Paola o di tutti e due.
- **Tocca:** contratto, wallet, sedute_singole, anagrafica, agenda · **Copertura:** La terminazione converte il residuo in wallet, ma crediti_cliente è vincolato al cliente d'origine (id_cliente): nessun trasferimento del credito a un'altra anagrafica né spesa su contratti altrui.

**S72 — Il fantasma ricompare: «posso riprendere?» (con €200 di sospeso)** · *rara* · 🟡 parziale
- **Scena:** Andrea, sparito 4 mesi fa con €200 di lavoro consumato e mai pagato, riscrive come niente fosse: «ciao coach! Riprendiamo a settembre?». Il PT è contento di riaverlo, ma il sospeso c'è — e la cifra esatta non la ricorda più nemmeno lui.
- **Oggi (senza software):** Scroll archeologico della chat e del quaderno dell'anno prima per ricostruire il numero. Metà delle volte il PT, in imbarazzo, riparte da zero e condona in silenzio.
- **Cosa serve:** Alla creazione della nuova seduta o contratto, il Portafoglio deve alzare la mano da solo: «insoluto €200 dal contratto chiuso il 12/03» — con la scelta esplicita e tracciata di incassarlo subito, spalmarlo sul nuovo o condonarlo consapevolmente.
- **Rischio se manca:** Il condono involontario è il più costoso: non è generosità, è smemoratezza — e insegna al cliente che sparire azzera i debiti. Con la cifra sotto gli occhi, anche il condono diventa una scelta del PT, non una sconfitta subita.
- **Tocca:** insoluto, sedute_singole, contratto, wallet, comunicazioni · **Copertura:** Il receivable resta visibile (worklist crediti-da-incassare con aging, G7.10) con incasso anche parziale e condono tracciato (POST /annulla); non riemerge da solo alla creazione di una nuova seduta/contratto.

**S73 — Il decesso del sig. Franco: chiudere tutto con rispetto, subito** · *rara* · 🟡 parziale
- **Scena:** Il sig. Franco, 68 anni, cliente da 3 anni, muore d'infarto nel weekend con 7 sedute residue di un pacchetto interamente pagato. La figlia avvisa il PT lunedì. Le sedute del martedì sono ancora in agenda e tra 3 settimane il sistema suggerirebbe gli auguri di compleanno.
- **Oggi (senza software):** Il PT cancella le sedute a mano una per una e vive nel terrore del promemoria o del messaggio precompilato partito per errore. L'eventuale rimborso alla famiglia lo fa in contanti, senza traccia.
- **Cosa serve:** Chiusura con causale decesso in UN gesto: contratto terminato, agenda ripulita, OGNI comunicazione suggerita o automatica silenziata per sempre, ed eventuale rimborso agli eredi (€245 pro-rata) registrato come uscita di cassa con causale.
- **Rischio se manca:** Un solo «Tanti auguri Franco!» arrivato alla famiglia distrugge in 3 secondi la reputazione umana del PT — l'errore che i clienti si raccontano per anni. E il rimborso in nero agli eredi è un buco di cassa non spiegabile.
- **Tocca:** contratto, anagrafica, agenda, comunicazioni, cassa · **Copertura:** Terminazione con rimborso in USCITA tracciata (o wallet erogabile) copre la parte economica; mancano la chiusura one-gesture con causale decesso e il silenziamento globale delle comunicazioni suggerite (compleanni inclusi).

**S74 — Il PT si rompe lo scafoide: 3 settimane, 45 sedute, 15 clienti** · *rara* · 🟡 parziale
- **Scena:** Caduta in moto, gesso al polso: il PT si ferma 3 settimane. In agenda ci sono circa 45 sedute di 15 clienti; 3 contratti scadono proprio in quel periodo e 2 clienti hanno rate agganciate a sedute che non avverranno.
- **Oggi (senza software):** Una sera intera al telefono a cancellare uno per uno, un Excel improvvisato «sedute che devo a…», e al rientro qualche seduta regalata come scusa perché il conto non torna mai.
- **Cosa serve:** Cancellazione e riprogrammazione massiva senza penali e senza scalare crediti, estensione in blocco delle scadenze coinvolte, e una vista «debito sedute per cliente» che sopravviva intatta alle 3 settimane di stop.
- **Rischio se manca:** 45 sedute ricostruite a memoria = 3-4 sedute perse o regalate (€150-250) e almeno un cliente convinto di essere stato dimenticato. Con la scadenza non estesa, il danno lo paga il cliente incolpevole — e la fiducia crolla.
- **Tocca:** agenda, contratto, rate, comunicazioni · **Copertura:** Cancellazione senza penale per-evento (Cancellato libera il credito) ed estensione scadenza per contratto esistono; nessuna operazione massiva, estensione in blocco né vista «debito sedute per cliente».

**S75 — Il ristoratore stagionale: chiude a maggio, torna a ottobre, ogni anno** · *rara* · 🟡 parziale
- **Scena:** Gigi ha il ristorante al mare: da maggio a settembre sparisce, ogni ottobre torna e ricompra. L'anno scorso aveva un 16-sedute a €640; quest'anno il PT ha ritoccato i prezzi ma non ricorda cosa faceva pagare a Gigi né com'era finita (era avanzata una seduta? due?).
- **Oggi (senza software):** Quaderni di due anni diversi, prezzi ricostruiti «mi pare ti facevo 40», e la trattativa che riparte ogni ottobre da zero con la sensazione di improvvisare davanti a un cliente fedele.
- **Cosa serve:** Storico contratti del cliente come base del prezzo consigliato al riacquisto, chiusure di stagione pulite (residui convertiti in wallet, mai lasciati nel limbo), e la certezza che a ottobre bastino 2 minuti per riproporre le condizioni giuste.
- **Rischio se manca:** Improvvisare il prezzo ogni anno o scontenta il fedele («l'anno scorso pagavo meno!») o lascia sul tavolo l'adeguamento di listino che il PT si era ripromesso. Su 4-5 clienti stagionali sono centinaia di euro l'anno, in una direzione o nell'altra.
- **Tocca:** contratto, listino, wallet, anagrafica · **Copertura:** Lo storico contratti del cliente c'è e la chiusura pulita con residuo→wallet esiste (terminazione); prezzo consigliato al riacquisto e listino con adeguamenti non esistono.

**S79 — Litigio sulla penale: se ne va con 3 sedute residue e una rata scoperta** · *rara* · 🟢 piena
- **Scena:** Stefano manda «non vengo» due ore prima per la terza volta; il PT applica il cancellato tardivo e la seduta scala. Stefano esplode in chat e se ne va: non pagherà mai la rata finale da €150 e restano 3 crediti residui che non userà.
- **Oggi (senza software):** Il PT archivia la chat, rimugina una settimana e cancella mentalmente i €150 «per non pensarci più» — ma il nome gli riappare in rubrica e in dashboard per anni.
- **Cosa serve:** Terminare d'ufficio fotografando lo stato (3 crediti decaduti, €150 in crediti-da-incassare), archiviare il cliente togliendolo dalle viste operative SENZA cancellare storico e sospeso, e ritrovare tutto intatto se un giorno ricompare.
- **Rischio se manca:** Cancellare tutto per rabbia significa perdere anche la prova di come sono andate le cose; tenerlo «attivo» significa vederlo ogni giorno. Senza una via di mezzo il PT sceglie la rabbia, e i €150 spariscono dalla contabilità come se non fossero mai esistiti.
- **Tocca:** contratto, insoluto, anagrafica, agenda, comunicazioni · **Copertura:** Terminazione bilaterale ADR-018: crediti decaduti (storno) + saldo trainer A_CREDITO nel receivable crediti_terminazione con worklist e condono esplicito; storico/audit intatti e cliente marcabile Inattivo/esito «non rinnova».


### scenari:pagamenti-irregolari (14 scenari)

**S5 — «Ti pago giovedì» — seduta fatta, portafoglio a casa** · *settimanale* · 🔴 assente
- **Scena:** Martedì ore 18:00, seduta singola da 45€ con Davide, cliente storico senza contratto attivo. A fine seduta tira fuori il telefono: «Non ho contanti e la carta è rimasta nella borsa di mia moglie, te li porto giovedì». Giovedì Davide si allena, paga i 45€ di giovedì, e nessuno dei due si ricorda più dei 45€ di martedì.
- **Oggi (senza software):** Promemoria mentale, nota sul telefono, a volte un WhatsApp a se stesso. Dopo due settimane il PT si vergogna a chiedere la cifra e la lascia perdere.
- **Cosa serve:** Chiudere la seduta come EROGATA ma NON PAGATA in 2 tap, generando un insoluto con importo e data promessa. Alla seduta successiva dello stesso cliente il CRM deve mostrare il badge «45€ in sospeso da martedì 12» e proporre di incassare entrambe insieme.
- **Rischio se manca:** 45-90€/mese evaporati in micro-crediti dimenticati; peggio ancora, chiederli due volte o alla persona sbagliata → figura da contabile approssimativo davanti al cliente.
- **Tocca:** sedute_singole, insoluto, cassa, agenda, anagrafica · **Copertura:** Né seduta singola né insoluto fuori contratto esistono: nessuna entità rappresenta «45€ dovuti da martedì» fuori da rate/contratti (crediti_terminazione nasce solo da terminazione).

**S13 — «Il bonifico te l'ho fatto ieri, giuro»** · *settimanale* · 🔴 assente
- **Scena:** Rata da 200€ scaduta lunedì. Martedì Elisa scrive: «fatto ora!». Mercoledì e giovedì sul conto non c'è nulla (bonifico ordinario, weekend di mezzo). Il PT controlla l'home banking quattro volte al giorno senza sapere se sollecitare di nuovo o aspettare.
- **Oggi (senza software):** Screenshot della chat come «prova», controlli ossessivi del conto, e la regola non scritta di non chiedere due volte per non offendere.
- **Cosa serve:** Stato intermedio della rata «dichiarato dal cliente — in attesa di riscontro» con data della dichiarazione: silenzia gli alert per 3-4 giorni lavorativi, poi, se l'incasso non è stato confermato, li riaccende con contesto («dichiarato il 12, mai riscontrato»).
- **Rischio se manca:** Doppio sollecito a chi ha davvero pagato (offende) o silenzio infinito verso chi ha solo DETTO di aver pagato: paga sempre chi si fida.
- **Tocca:** rate, cassa, insoluto, comunicazioni · **Copertura:** La rata conosce solo PENDENTE/PARZIALE/SALDATA (rate.py): nessuno stato «dichiarato, in attesa di riscontro» che silenzi temporaneamente gli alert overdue.

**S14 — «Tieni il resto» / «Non ho spicci»** · *settimanale* · 🔴 assente
- **Scena:** Seduta singola da 45€. Lunedì Franca dà 50€: «lascia stare il resto». Mercoledì Piero dà 40€: «non ho spicci, i 5 te li porto la prossima» (non arrivano mai). In cassa entrano 50 e 40, ma le sedute valgono 45.
- **Oggi (senza software):** Nessuna: il contante entra in tasca e la differenza sparisce. A fine mese la cassa non riconcilia mai con le sedute fatte, di 5-10€ ogni volta.
- **Cosa serve:** Incasso a importo LIBERO sulla seduta con differenza esplicita e classificata in 1 tap: +5€ → «extra/mancia» in cassa (fuori dai conteggi contratto); −5€ → micro-insoluto oppure «abbuono» consapevole. La cassa deve riconciliare con il reale, non con il teorico.
- **Rischio se manca:** Cassa che non torna mai e PT che smette di fidarsi dei propri numeri — l'esatto contrario di «sicuro e in controllo».
- **Tocca:** sedute_singole, cassa, insoluto, wallet · **Copertura:** Le sedute singole non esistono e sul contratto pay_rate blocca l'overpayment (guard B-bis/B-ter): la differenza (mancia/micro-insoluto/abbuono) non ha alcuna classificazione.

**S27 — 100€ ora, «il resto venerdì» — rata pagata a pezzi** · *settimanale* · 🟢 piena
- **Scena:** Rata da 150€ in scadenza. Sara arriva con 100€ in contanti: «È fine mese, ti do questi e 50 venerdì». Venerdì porta 30€. La rata ora è pagata 130 su 150, in due tranche cash, e nessuno ha scritto niente da nessuna parte. Variante: metà contanti subito, il resto su Satispay stasera.
- **Oggi (senza software):** Foglietto nel borsone o nota sul cellulare tipo «Sara −50 poi −20». Alla terza tranche il conteggio del PT e quello della cliente divergono.
- **Cosa serve:** Incassi PARZIALI multipli sulla stessa rata, ciascuno con data e metodo, con residuo calcolato e sempre visibile («Rata 2: 130/150 — mancano 20€»). Il residuo deve comparire nel Portafoglio del cliente e nel testo del sollecito.
- **Rischio se manca:** Perdere il filo dopo 2-3 tranche; contestazione inevitabile («te li ho già dati venerdì!») senza uno storico da mostrare.
- **Tocca:** rate, cassa, insoluto, comunicazioni · **Copertura:** Stato rata PARZIALE + N CashMovement per rata (ciascuno con data/metodo) + payment history cronologico per rata; il residuo-rata alimenta aging e overdue-rates.

**S29 — Rata del 10 saltata in silenzio** · *settimanale* · 🟢 piena
- **Scena:** Il contratto di Giulia (12 sedute, 600€) prevede 3 rate da 200€ il 10 di ogni mese. Il 10 marzo il bonifico non arriva. Giulia continua ad allenarsi regolarmente, sorridente. Il PT se ne accorge il 26, mentre paga l'affitto della sala.
- **Oggi (senza software):** Controlla l'home banking «quando si ricorda» e ricostruisce a memoria chi ha pagato cosa. Il sollecito parte tardi e in imbarazzo: «scusa, forse mi è sfuggito, ma...».
- **Cosa serve:** Alert automatico il giorno dopo la scadenza («Rata 2/3 di Giulia scaduta ieri — 200€») con template WhatsApp di sollecito gentile pre-compilato con importo e riferimento. Lo stato rate del cliente deve essere visibile a colpo d'occhio PRIMA di ogni sua seduta in agenda.
- **Rischio se manca:** Settimane di scoperto non visto mentre le sedute si erogano; il sollecito tardivo suona come un'accusa e a fine contratto mancano 200€ senza che nessuno sappia più perché.
- **Tocca:** rate, contratto, insoluto, comunicazioni, agenda · **Copertura:** GET /dashboard/overdue-rates + alert dashboard + template waRateReminder precompilato + communication_log del sollecito («già sollecitata il 2/7»); session_prep porta lo stato contratti prima della seduta.

**S31 — La mamma paga per il figlio sedicenne** · *mensile* · 🔴 assente
- **Scena:** Tommaso, 16 anni, si allena martedì e giovedì. Il contratto da 480€ lo paga la madre, Paola, con bonifico dal proprio conto. Solleciti e ricevute devono andare a Paola; scheda, anamnesi e agenda sono di Tommaso. Quando il bonifico arriva con causale vuota, va indovinato a quale contratto attribuirlo. Variante quotidiana: il marito che paga per la moglie e arrotonda pure.
- **Oggi (senza software):** Rubrica WhatsApp con «Paola mamma Tommy» e memoria su chi paga per chi. Con due fratelli iscritti l'attribuzione del bonifico diventa una lotteria.
- **Cosa serve:** PAGATORE distinto dal cliente sul contratto: anagrafica collegata con il suo telefono. Gli incassi si attribuiscono al contratto di Tommaso ma il sollecito WhatsApp parte verso il numero di Paola, e lo storico dice «pagato da Paola». Mai, mai chiedere soldi a un sedicenne.
- **Rischio se manca:** Sollecitare il minore (figuraccia con la famiglia) o attribuire il bonifico al contratto sbagliato quando i figli iscritti sono due.
- **Tocca:** anagrafica, contratto, rate, cassa, comunicazioni · **Copertura:** Nessuna entità pagatore su contratto o movimento: il CashMovement di rata è intestato al cliente del contratto e MovementManualCreate vieta perfino id_cliente; solleciti e ricevute puntano solo al cliente.

**S32 — «Tieni questi 300€, poi scaliamo»** · *mensile* · 🔴 assente
- **Scena:** Nadia fa la turnista e non può impegnarsi su orari fissi: lascia 300€ in contanti al PT: «non farmi fare un contratto, scala tu ogni volta che vengo». Verrà 1-2 volte a settimana, quando può, a 40€ a seduta. Variante: la mamma di Tommaso prepaga 5 sedute estive del figlio con bonifico unico.
- **Oggi (senza software):** Quadernetto col conto a scalare «Nadia: 300 → 260 → 220...». Se salta una registrazione il conto diverge, e quando arriva vicino a zero nessuno dei due sa se è zero davvero.
- **Cosa serve:** Caricare il WALLET con un incasso anticipato (i 300€ entrano in cassa SUBITO, con data e metodo) e scalarlo a ogni seduta singola, con saldo sempre visibile a entrambi («restano 140€ — 3,5 sedute») e avviso quando sta per esaurirsi.
- **Rischio se manca:** È denaro ALTRUI in tasca al PT senza contabilità: sbagliare un conto a scalare qui non è un errore, è una scorrettezza percepita.
- **Tocca:** wallet, cassa, sedute_singole, agenda · **Copertura:** Il wallet crediti_cliente non è caricabile con un incasso anticipato: nasce esclusivamente da una terminazione (ADR-020) e si può solo EROGARE in uscita, mai scalare su sedute.

**S48 — Sconto strappato a voce al rinnovo** · *mensile* · 🟡 parziale
- **Scena:** Rinnovo del pacchetto da 550€ di Marco. Sul divanetto dell'ingresso: «Dai, sono due anni che vengo, facciamo 500 tondi». Il PT accetta con una stretta di mano. Le rate erano pensate su 550: ora due da 200 e una da... 150? 100? La sera a casa il PT non ricorda cosa ha promesso.
- **Oggi (senza software):** Stretta di mano e memoria, a volte un vocale WhatsApp. Le rate si ricalcolano a spanne e il totale non torna mai con il listino mentale.
- **Cosa serve:** Applicare uno sconto sul contratto al momento della creazione/rinnovo con motivo annotato («fedeltà 2 anni»), ricalcolo automatico del piano rate, e prezzo pieno + prezzo scontato ENTRAMBI conservati: così lo storico prezzi resta onesto e il futuro prezzo-consigliato della seduta singola non si inquina.
- **Rischio se manca:** Rate che non quadrano col totale; al rinnovo successivo il PT non sa se 500 era il prezzo «vero» o l'eccezione, e lo sconto una tantum diventa permanente senza averlo mai deciso.
- **Tocca:** contratto, rate, listino, comunicazioni · **Copertura:** Prezzo contrattuale libero + generate_payment_plan ricalcolano il piano sul prezzo reale (INV-RATE garantisce coerenza col residuo); prezzo pieno+scontato e motivo dello sconto non sono tracciati.

**S49 — L'acconto promesso che non arriva mai** · *mensile* · 🟡 parziale
- **Scena:** Firma del contratto da 720€ con Luca: «Ti porto 200€ di acconto sabato». Il PT attiva il contratto, le sedute partono lunedì. Sabato Luca non passa; l'acconto scivola di settimana in settimana e dopo un mese sono state erogate 5 sedute con incasso ZERO.
- **Oggi (senza software):** Il PT «tiene a mente» che manca l'acconto; sul quaderno il contratto risulta partito con acconto perché era pattuito. Chiederlo dopo un mese è umiliante, quindi spesso non lo chiede.
- **Cosa serve:** Distinzione netta tra acconto PATTUITO e acconto INCASSATO: il contratto può partire lo stesso, ma l'acconto non versato resta un insoluto vistoso in dashboard e nel Portafoglio («Acconto 200€ pattuito il 3/5, mai versato — 5 sedute già erogate»), con sollecito pre-compilato.
- **Rischio se manca:** Erogare mezzo pacchetto gratis. È il buco più grosso e più invisibile: non è una rata scaduta né una seduta non pagata — oggi non è «niente» da nessuna parte.
- **Tocca:** contratto, cassa, insoluto, rate, comunicazioni · **Copertura:** L'acconto registrato genera sempre l'ENTRATA (pattuito=incassato per costruzione); il non-versato resta visibile solo come residuo generico («da pianificare»), mai come acconto-pattuito-mai-versato con evidenza dedicata.

**S50 — Un bonifico da 500€ per due contratti (marito e moglie)** · *mensile* · 🟡 parziale
- **Scena:** Anna e Stefano si allenano entrambi, contratti separati: rata di lei 280€, di lui 220€. Stefano fa UN bonifico da 500€ con causale «palestra». Il PT deve spezzarlo su due clienti e due rate diverse.
- **Oggi (senza software):** Calcolo mentale al momento, nessuna traccia dello split. Tre mesi dopo, davanti all'estratto conto, nessuno sa più come erano stati divisi quei 500€.
- **Cosa serve:** Registrare un incasso unico e RIPARTIRLO su più contratti/rate in un solo passaggio, con entrambe le quote marcate «pagate col bonifico unico di Stefano del 4/6» — riconciliazione banca→CRM in un gesto solo.
- **Rischio se manca:** Una delle due rate risulta scoperta per errore e il PT sollecita Anna, che «ha già pagato» tramite il marito: imbarazzo doppio, davanti a una coppia.
- **Tocca:** cassa, rate, contratto, anagrafica · **Copertura:** Si registrano due pagamenti rata separati (ognuno con metodo e nota che cita il bonifico unico); nessuno split guidato di un accredito unico su più contratti.

**S51 — I 20€ «per il tuo lavoro» a Natale** · *mensile* · 🟡 parziale
- **Scena:** Ultima seduta dell'anno, vigilia di Natale. La signora Bianchi, cliente da 4 anni, oltre alla rata lascia una busta con 20€: «per tutto quello che fai per me». Non è una rata, non è una seduta, non è un acconto.
- **Oggi (senza software):** In tasca e via, invisibile a qualsiasi conteggio; oppure finisce mescolata al contante della rata e a fine giornata la cassa «avanza» 20€ inspiegabili.
- **Cosa serve:** Movimento di cassa ENTRATA a categoria libera («extra/omaggio») agganciato al cliente ma FUORI da contratti e rate: la cassa quadra al centesimo, i conteggi del contratto restano puliti, e nello storico del cliente resta la traccia (che fa anche piacere ritrovare).
- **Rischio se manca:** Piccolo in euro, grande in fiducia: ogni volta che la cassa «avanza» soldi non spiegati, il PT smette di credere ai propri totali.
- **Tocca:** cassa, anagrafica · **Copertura:** L'ENTRATA manuale con categoria libera/metodo/note esiste e fa quadrare la cassa, ma MovementManualCreate vieta id_cliente: l'extra non è agganciabile al cliente.

**S59 — «Quella rata l'ho pagata a gennaio, in contanti»** · *mensile* · 🟢 piena
- **Scena:** Il PT sollecita una rata da 180€. Roberta, in perfetta buona fede, è sicura di averla pagata: «in contanti, dopo la seduta del giovedì, ti ricordi?». Il PT non se lo ricorda. Non esiste traccia scritta da nessuna parte. È memoria contro memoria.
- **Oggi (senza software):** Senza prove il PT quasi sempre cede («avrò segnato male io») e perde 180€, oppure insiste e incrina un rapporto pluriennale.
- **Cosa serve:** Registro incassi per cliente con data, importo, metodo e rata collegata, mostrabile in 5 secondi dal telefono: «Guarda: il 9 gennaio, 180€ in contanti, rata 1. Questa è la rata 2». Il conflitto si spegne davanti a un registro, non davanti a un ricordo.
- **Rischio se manca:** 180€ persi OPPURE un cliente perso; ogni contestazione gestita a memoria erode l'autorevolezza professionale del PT.
- **Tocca:** rate, cassa, contratto, comunicazioni · **Copertura:** Payment history per rata (ogni CashMovement con data/importo/metodo, cronologico) + GET /contracts/{id}/history + audit trail: la prova neutra da mostrare insieme esiste.

**S76 — L'azienda che paga a 60 giorni per il dipendente** · *rara* · 🟡 parziale
- **Scena:** La ditta di famiglia copre il pacchetto da 800€ di Matteo (o un piccolo welfare aziendale). L'azienda vuole una nota intestata e paga a 30-60 giorni. Matteo intanto si allena da subito, come è giusto.
- **Oggi (senza software):** Il PT avvia il pacchetto sulla fiducia, si segna su carta di mandare la nota, e l'incasso arriva quando arriva. Nessuno glielo ricorda in faccia come farebbe un cliente.
- **Cosa serve:** Pagatore = AZIENDA (anagrafica con ragione sociale e persona di riferimento), scadenza di incasso lunga e dichiarata (60gg) che NON generi un alert «rata scaduta» ogni giorno, ma che — scaduta davvero — diventi insoluto verso l'azienda, mai verso Matteo.
- **Rischio se manca:** Dimenticarsi di incassare dall'azienda (l'insoluto più silenzioso che esista) oppure, peggio, sollecitare Matteo che non c'entra nulla.
- **Tocca:** anagrafica, contratto, insoluto, cassa, comunicazioni · **Copertura:** Una rata con scadenza lunga è possibile (entro la data_scadenza contratto — rate date boundary) e l'alert scatta solo a scadenza; nessun pagatore-azienda né sollecito indirizzabile a un terzo.

**S77 — Il bonifico doppio (o i 20€ in più)** · *rara* · 🟡 parziale
- **Scena:** Rata da 180€. Il marito di Carla la paga; due giorni dopo la paga anche Carla: 360€ per una rata da 180. Variante: Gino, andando a memoria, bonifica 200€ invece di 180€. L'eccedenza finisce in un limbo.
- **Oggi (senza software):** Il PT se ne accorge (forse) dall'estratto conto. «Te li tolgo dalla prossima» detto a voce e affidato alla memoria di entrambi.
- **Cosa serve:** L'eccedenza rilevata alla registrazione dell'incasso deve finire nel WALLET in modo esplicito («+20€ a credito di Gino»), visibile nel pannello Portafoglio e SUGGERITA in automatico alla prossima rata o seduta; in alternativa, rimborso tracciato come uscita di cassa.
- **Rischio se manca:** Tenere soldi non dovuti senza saperlo — e il cliente che lo scopre dal proprio estratto conto prima di te. Sulla fiducia, il denaro in eccesso pesa più di quello mancante.
- **Tocca:** cassa, rate, wallet, contratto · **Copertura:** I guard B-bis/B-ter bloccano l'overpayment (mai soldi orfani sul contratto) e il wallet ha la causale OVERPAYMENT predisposta ma non alimentata dai guard (ADR-020): l'eccedenza reale va gestita a mano.


### scenari:primo-contatto (16 scenari)

**S6 — Valutazione iniziale del chinesiologo: €50 di servizio vero, non un'esca** · *settimanale* · 🔴 assente
- **Scena:** Ad Anna, 52 anni, mal di schiena cronico, Paolo (chinesiologo) propone il suo standard: valutazione funzionale di 75 minuti a €50 — test posturali, anamnesi completa, report finale. Anna paga con bonifico, ma non è detto che compri il percorso: la valutazione è un prodotto a sé.
- **Oggi (senza software):** Appuntamento su calendar, €50 annotati su un quaderno «da fatturare», report in Word mandato per mail. Se Anna compra il percorso, la valutazione sparisce dalla storia contabile.
- **Cosa serve:** La valutazione come voce di listino vendibile come seduta singola fuori contratto: incasso in cassa, evento agenda tipizzato, esito agganciato ad anagrafica/anamnesi. Deve restare visibile nello storico anche se poi nasce un contratto.
- **Rischio se manca:** Incassi da €150-200/mese (3-4 valutazioni) invisibili al gestionale; il posizionamento professionale «la mia valutazione si paga» indebolito dal non avere nemmeno una registrazione ordinata.
- **Tocca:** sedute_singole, listino, cassa, agenda, anagrafica · **Copertura:** Nessuna voce vendibile fuori contratto: l'incasso finirebbe come movimento manuale slegato (MovementManualCreate vieta perfino id_cliente, financial.py:600).

**S7 — Prova pagata €30 «che poi ti scalo dal pacchetto»** · *settimanale* · 🔴 assente
- **Scena:** Davide fa pagare la prova €30 «così vengono solo quelli seri», con la promessa: «se prendi il pacchetto te li scalo». Chiara paga in contanti venerdì, ci pensa dieci giorni, e quando firma il pacchetto da €450 Davide deve ricordarsi dello sconto promesso — e di dove sono finiti quei 30 euro.
- **Oggi (senza software):** I 30€ finiscono nel portafoglio, la promessa nella memoria. Se passa tempo, o se ne dimentica (cliente irritata alla firma) o li scala due volte (rimette lui).
- **Cosa serve:** Registrare la prova come seduta singola con prezzo proprio (€30) incassata in cassa, e trasformare quell'importo in credito wallet spendibile sul contratto futuro: alla creazione del pacchetto il CRM segnala «Chiara ha €30 di wallet, li scalo?». Suggerito, mai automatico.
- **Rischio se manca:** Soldi incassati che non esistono da nessuna parte (nero involontario) e promesse di sconto dimenticate che bruciano la fiducia nel momento esatto della firma.
- **Tocca:** sedute_singole, cassa, wallet, contratto, listino · **Copertura:** Il wallet crediti_cliente nasce SOLO da terminazione (causale RIMBORSO_DIFFERITO/OVERPAYMENT, ADR-020): non è caricabile da un incasso-prova né applicabile in sconto alla creazione di un contratto (G8.2 in panchina).

**S8 — «Quanto costa un pacchetto da 10?» — e il prezzo cambia a memoria** · *settimanale* · 🔴 assente
- **Scena:** Nella stessa settimana Davide riceve la domanda da tre persone: al collega della moglie dice €400, alla ragazza arrivata da Instagram €450, al cliente storico che chiede per la sorella «facciamo 380, dai». Nessuna delle tre cifre è scritta da nessuna parte. Un mese dopo due di loro si incontrano in sala e confrontano i prezzi.
- **Oggi (senza software):** Il listino vive nella testa; qualche cifra su un Excel vecchio di due anni o su un volantino. Gli sconti sono decisi al volo e mai tracciati.
- **Cosa serve:** Un listino di riferimento (pacchetti, seduta singola, valutazione, prova) da cui partire per ogni preventivo, e lo storico dei prezzi realmente praticati per ciascun cliente. Il prezzo resta LIBERO, ma lo sconto diventa una scelta consapevole invece di un'amnesia.
- **Rischio se manca:** Erosione silenziosa del margine (10-15% regalato senza accorgersene) e figuraccia quando due clienti scoprono di pagare cifre diverse senza motivo.
- **Tocca:** listino, contratto, sedute_singole, comunicazioni · **Copertura:** Nessuna entità listino nel modello (ADR-025 la prevede); i prezzi praticati esistono solo come prezzo_totale nei singoli contratti, mai esposti come riferimento di preventivo.

**S17 — Lead da Instagram: «Ciao, info sui prezzi?»** · *settimanale* · 🔴 assente
- **Scena:** Martedì sera, mentre cena, a Davide arriva un DM su Instagram da Martina, 29 anni: «Ciao! Quanto costa allenarsi con te?». Lui risponde dal divano, la conversazione muore lì e Martina si rifà viva tre giorni dopo chiedendo una prova. Nel frattempo sono arrivati altri 2 messaggi simili e Davide non ricorda più a chi ha detto cosa.
- **Oggi (senza software):** Le chat WhatsApp/Instagram sono l'unico archivio: scrolla le conversazioni per ricostruire chi era interessato, a volte si segna il nome nelle note del telefono. I lead tiepidi si perdono nel feed.
- **Cosa serve:** Creare un'anagrafica lead/prospect in 30 secondi (nome, telefono, provenienza, cosa ha chiesto) SEPARATA dai clienti attivi, con nota libera e promemoria di ricontatto. Una vista «persone da risentire» che non si mescola con la lista clienti.
- **Rischio se manca:** Lead da €400-500 di pacchetto che evaporano perché la chat scorre giù. Peggio: ricontattare la stessa persona due volte o farle due prezzi diversi.
- **Tocca:** anagrafica, comunicazioni · **Copertura:** Nessuna entità lead/prospect: esiste solo Client (stato Attivo/Inattivo, client.py) e creare un cliente per ogni DM inquina l'anagrafica; nessun promemoria di ricontatto agganciato alla persona.

**S18 — «Ci devo pensare» — e il follow-up che non parte mai** · *settimanale* · 🔴 assente
- **Scena:** Dopo la prova, Matteo è tiepido: «Bello, ci penso e ti faccio sapere». Davide sa per esperienza che se non lo risente entro 3-4 giorni è perso, ma tra 30 clienti e la vita se ne ricorda dopo due settimane, quando Matteo si è già iscritto al corso di crossfit.
- **Oggi (senza software):** Memoria e buoni propositi; qualcuno usa le sveglie del telefono o si autoinvia messaggi WhatsApp. Il follow-up parte una volta su tre.
- **Cosa serve:** Sul prospect uno stato «in decisione» e un promemoria di ricontatto a data che riemerge in dashboard, con template WhatsApp pronto e log del contatto. Deve essere più veloce del post-it, altrimenti non verrà usato.
- **Rischio se manca:** Il momento più caldo del funnel è gestito peggio di tutti: ogni follow-up mancato è un pacchetto da €400-500 lasciato sul tavolo — 3-4 l'anno fanno una mensilità intera.
- **Tocca:** comunicazioni, anagrafica · **Copertura:** Nessuno stato «in decisione» né promemoria a data sulla persona; todos generici e communication_log esistono ma non sono agganciati a un funnel prospect.

**S19 — Seduta di prova gratuita: uno slot vero occupato da un non-cliente** · *settimanale* · 🟡 parziale
- **Scena:** Giovedì alle 18 Davide blocca un'ora per la prova gratuita di Luca, arrivato da un post Facebook. Luca non è un cliente: niente contratto, niente pagato, ma occupa lo slot migliore della giornata. Davide vorrebbe anche sapere PRIMA se ha problemi fisici, non scoprirlo a metà squat.
- **Oggi (senza software):** Evento sul Google Calendar personale con scritto «Luca prova», telefono nella chat. Anamnesi fatta a voce nei primi 10 minuti, appunti su un blocco note.
- **Cosa serve:** Creare un prospect con evento agenda a costo zero (tipo «prova», nessun credito scalato, nessun contratto), mandargli prima il link anamnesi self-service, vedere in agenda che quello slot è una prova (tipo/colore diverso) e convertirlo in cliente in un click se firma.
- **Rischio se manca:** Slot premium bruciati senza mai conoscere il proprio tasso di conversione; red flag fisiche scoperte in corsa; se il prospect svanisce, di tre ore di lavoro commerciale non resta nulla.
- **Tocca:** agenda, anagrafica, sedute_singole, comunicazioni · **Copertura:** Evento senza contratto a costo zero + link anamnesi self-service (share_tokens + waWelcome) esistono; mancano l'entità prospect, il tipo «prova» in agenda e la conversione 1-click.

**S20 — Dopo la prova, Giulia firma: €100 di acconto in contanti a bordo sala** · *settimanale* · 🟡 parziale
- **Scena:** Finita la prova, Giulia dice «ok, partiamo»: pacchetto 12 sedute a €480, lascia €100 in contanti seduta stante, «il resto con due bonifici». Davide ha 5 minuti prima del cliente successivo e deve anche fissarle le prime due sedute.
- **Oggi (senza software):** I 100€ in tasca, l'accordo a voce, «stasera mi segno tutto» — e stasera si segna metà. Le rate promesse vivono su WhatsApp.
- **Cosa serve:** Contratto + acconto in cassa + piano rate (2 bonifici) + primi eventi agenda in un flusso UNICO di 2-3 minuti, non quattro schermate separate. La conversione prospect→cliente deve portarsi dietro anamnesi e note della prova.
- **Rischio se manca:** Acconti in contanti ricordati male («ti avevo dato 100 o 150?») e rate promesse a voce mai formalizzate, che diventano insoluti impliciti dal giorno uno.
- **Tocca:** contratto, rate, cassa, agenda, anagrafica · **Copertura:** Contratto con acconto (ENTRATA atomica) + generate_payment_plan + eventi esistono tutti, ma come flussi separati; nessuna conversione prospect→cliente che porti con sé anamnesi/note della prova.

**S33 — «Porta un amico»: la seduta omaggio promessa a Marco** · *mensile* · 🔴 assente
- **Scena:** Davide promette: «Se mi porti un amico che firma, ti regalo una seduta». Marco porta Luca, Luca firma un pacchetto da €450 a fine mese. Tre settimane dopo Marco, a fine allenamento: «Oh, e la mia seduta omaggio?». Davide non ricorda se gliel'ha già data.
- **Oggi (senza software):** Promessa a voce, mantenuta se e quando qualcuno se la ricorda. A volte il PT la regala due volte per imbarazzo.
- **Cosa serve:** Alla firma di Luca (provenienza «portato da Marco»), poter accreditare a Marco 1 credito-seduta omaggio o €X di wallet con causale: il bonus esiste, si vede nel pannello Portafoglio di Marco e si consuma una volta sola.
- **Rischio se manca:** Il canale di acquisizione più economico che esista (referral) sabotato da promesse dimenticate: Marco smette di portare amici, e il PT non sa nemmeno quanti clienti gli ha portato negli anni.
- **Tocca:** wallet, sedute_singole, anagrafica, contratto · **Copertura:** Nessun credito omaggio accreditabile: il wallet nasce solo da terminazione, i crediti-seduta solo da contratto, e la provenienza referral non è un campo del modello.

**S34 — Due amiche, un pacchetto «di coppia» — e poi una molla** · *mensile* · 🔴 assente
- **Scena:** Sara e Anna vogliono allenarsi insieme: seduta di coppia a €50 invece di 35+35, pacchetto 10 sedute €500, €250 a testa. Sara paga subito con bonifico, Anna «a fine mese». Al quarto mese Anna si trasferisce per lavoro e restano 6 sedute a metà.
- **Oggi (senza software):** Un unico accordo verbale, i conti su WhatsApp. Quando Anna molla, il conguaglio è una trattativa imbarazzante fatta a occhio: quanto vale la mezza-seduta rimasta a Sara che ora si allena da sola?
- **Cosa serve:** Due paganti sullo stesso percorso con posizioni SEPARATE (chi ha versato cosa, quote di ciascuna) e un evento agenda condiviso che scala da entrambe. Se una esce: conguaglio pro-rata sulla SUA quota, wallet o rimborso, senza toccare la posizione dell'altra.
- **Rischio se manca:** Soldi di due persone in un calderone unico: quando la coppia si rompe (succede spesso), il PT rimborsa a spanne e ci rimette, oppure tira dritto e perde entrambe.
- **Tocca:** contratto, rate, wallet, agenda, cassa, anagrafica · **Copertura:** Contract ha un solo id_cliente e Event un solo partecipante: niente quote per pagante né conguaglio sulla singola quota.

**S35 — L'amico che accompagna: in due sullo slot di uno** · *mensile* · 🔴 assente
- **Scena:** Martedì Marco (pacchetto da 20) si presenta con l'amico Luca: «Gli ho detto che sei un mostro, può provare con me oggi?». Davide li allena insieme: Marco fa la sua seduta normale, Luca prova gratis. La settimana dopo Luca chiede di tornare «ancora una volta con Marco».
- **Oggi (senza software):** Nessuna traccia: la seduta scala il credito di Marco come sempre, Luca non esiste da nessuna parte se non nella memoria del PT.
- **Cosa serve:** Aggiungere al volo un secondo partecipante prospect a un evento agenda esistente, senza toccare i crediti del titolare: Luca nasce come lead con provenienza «amico di Marco» e la sua prova è tracciata. Alla seconda richiesta il CRM mostra che una prova l'ha già avuta.
- **Rischio se manca:** Prove gratuite infinite non tracciate (Luca si allena 4 volte a scrocco della seduta di Marco) e referral mai capitalizzati: nessuno si accorge che il 30% dei clienti arriva da Marco.
- **Tocca:** agenda, anagrafica, sedute_singole · **Copertura:** Event è mono-cliente: nessun secondo partecipante prospect agganciabile a un evento esistente, né entità lead con provenienza.

**S36 — La palestra gira un cliente — e vuole il suo 20%** · *mensile* · 🔴 assente
- **Scena:** La palestra dove Davide affitta lo spazio gli passa Elisa: «Cerca un PT tre volte a settimana». Accordo: il 20% di quello che Elisa paga va alla palestra. Elisa firma un pacchetto da €600, quindi €120 da girare — ma quando? Sul firmato o sull'incassato, visto che Elisa paga in 3 rate?
- **Oggi (senza software):** Conto a mente o su un foglio: «devo 120 a Franco». Con le rate, la percentuale viene girata a sentimento, e a fine anno nessuno dei due sa più chi deve cosa a chi.
- **Cosa serve:** Provenienza (palestra/partner) e percentuale dovuta segnate sul contratto, con l'uscita di cassa collegata e calcolata sugli incassi REALI: quando entra la rata da €200, il CRM ricorda «€40 da girare alla palestra». Riepilogo per partner a fine mese.
- **Rischio se manca:** Percentuali pagate due volte o mai pagate: nel primo caso perde margine, nel secondo perde la palestra — cioè il canale che porta 5-6 clienti l'anno e le chiavi della sala.
- **Tocca:** contratto, rate, cassa, anagrafica · **Copertura:** Nessun campo provenienza/percentuale partner sul contratto; l'uscita verso la palestra sarebbe solo un movimento manuale slegato dagli incassi reali.

**S39 — Il ritorno del cliente storico: 3 sedute flash senza riaprire il contratto (caso canonico)** · *mensile* · 🟡 parziale
- **Scena:** Andrea, cliente per due anni, trasferito a Milano da 6 mesi (contratto chiuso con conguaglio, gli erano rimasti €50 di wallet), scrive lunedì: «Sono giù questa settimana, mi fai fare 2-3 sedute?». Nei pacchetti pagava €38 a seduta. Vuole pagare a seduta, cash o Satispay, e giovedì riparte. Ha anche una lombalgia in anamnesi da rispettare.
- **Oggi (senza software):** Davide fissa a voce, incassa contanti, ricorda vagamente «forse gli dovevo qualcosa dal vecchio pacchetto» ma non ha il numero: o lascia perdere (rimette Andrea) o spara una cifra (rimette lui). Le sedute non scalano niente e non esistono da nessuna parte.
- **Cosa serve:** Seduta singola con prezzo LIBERO ma consigliato dallo storico contratti (€38), scelta esplicita singola-vs-contratto alla creazione, segnalazione del wallet («Andrea ha €50: li scalo dalla prima?») e pannello Portafoglio che mostra tutto in una schermata. Anagrafica, anamnesi e safety engine restano agganciati come sempre. Se non paga → insoluto fuori contratto.
- **Rischio se manca:** Il caso canonico: o si riapre un contratto finto (sporcando lo storico e le metriche) o si incassa fuori da tutto — nero contabile più wallet dimenticato, cioè fiducia incrinata con il miglior ambassador del PT.
- **Tocca:** sedute_singole, wallet, listino, cassa, agenda, insoluto, anagrafica · **Copertura:** Anagrafica/anamnesi/safety restano agganciate a qualunque evento e il wallet è visibile (crediti_cliente + worklist rimborsi-da-erogare); mancano la seduta singola con prezzo/incasso, il suggerimento di scalare il wallet (G8.2 in panchina) e l'insoluto fuori contratto — il cuore di ADR-025.

**S44 — No-show alla prova gratuita: buca il sabato mattina e riprenota** · *mensile* · 🟡 parziale
- **Scena:** Sara prenota la prova per sabato alle 9, lo slot più richiesto. Alle 9:20 Davide le scrive, alle 10 lei risponde «scusa, mi sono dimenticata! Possiamo rifare?». Lui aveva rifiutato un cliente pagante per quello slot, e tra un mese non ricorderà che Sara ha già bucato una volta.
- **Oggi (senza software):** Nessuna traccia: la chat scorre via e Sara riprenota come se niente fosse. Qualche PT tiene una lista nera mentale che dura una settimana.
- **Cosa serve:** Marcare il no-show anche su un evento prova SENZA contratto (oggi il no-show vive solo dentro i crediti contratto), con storico visibile sul prospect: alla seconda richiesta il CRM mostra «1 prova bucata il 14/06». Il PT decide, ma informato — magari stavolta prova pagata anticipata.
- **Rischio se manca:** Slot premium regalati due volte alla stessa persona; i prospect seriali di prove bucate costano più dei clienti che rendono.
- **Tocca:** agenda, anagrafica, sedute_singole, comunicazioni · **Copertura:** Lo stato No_Show è marcabile su eventi senza contratto; manca l'entità prospect con contatore prove bucate che riemerga alla riprenotazione.

**S45 — Il fisioterapista manda una paziente «da finire di rimettere in piedi»** · *mensile* · 🟡 parziale
- **Scena:** Il fisioterapista Bianchi dimette Rosa, 61 anni, dopo la riabilitazione per protesi d'anca, e la manda da Paolo (chinesiologo) «per il ricondizionamento». Rosa arriva con referti e paure; Bianchi vuole essere aggiornato e continuerà a mandare pazienti solo se il primo caso va bene.
- **Oggi (senza software):** Passaggio di consegne per telefono, referti fotografati su WhatsApp, provenienza annotata da nessuna parte. Dopo un anno il PT non sa dire quanti clienti gli ha mandato Bianchi.
- **Cosa serve:** Campo provenienza «inviato da» sul cliente con vista aggregata per fonte (quanto vale il canale Bianchi), anamnesi con red flag chirurgiche compilata PRIMA della prima seduta via link self-service, e prima seduta di valutazione a listino. Il safety engine deve avere i dati dal minuto zero.
- **Rischio se manca:** Il canale referral sanitario — quello con i clienti più fedeli e meno sensibili al prezzo — coltivato alla cieca; un errore su Rosa per anamnesi frettolosa e Bianchi non manda più nessuno.
- **Tocca:** anagrafica, comunicazioni, agenda, sedute_singole, listino · **Copertura:** Il link anamnesi self-service pre-seduta esiste (share_tokens + waWelcome) e il safety engine si attiva subito; mancano provenienza «inviato da», vista per fonte e valutazione a listino.

**S61 — Buono regalo di Natale: paga la moglie, si allena il marito** · *rara* · 🔴 assente
- **Scena:** Il 20 dicembre Federica compra 5 sedute per il marito Gianni: paga €225 con bonifico e chiede «qualcosa di carino da mettere sotto l'albero». Gianni si presenta la prima volta a febbraio, e a quel punto non è nemmeno anagrafato. A marzo Federica chiede: «Quante gliene restano?».
- **Oggi (senza software):** Un PDF fatto con Canva come buono, i €225 sul quaderno sotto dicembre, le sedute di Gianni contate a memoria o su WhatsApp («fatte 2, ne restano 3»).
- **Cosa serve:** Incassare oggi da una persona (cassa a dicembre, intestata a Federica) e agganciare i crediti-sedute a un'altra anche dopo settimane: buono come pacchetto prepagato con beneficiario assegnabile in seguito, scadenza opzionale, e risposta immediata a «quante ne restano». Chi ha pagato resta sempre visibile.
- **Rischio se manca:** Incasso di dicembre disallineato dalle sedute erogate a febbraio-aprile (caos fiscale); una seduta regalo contata male è una lite con DUE persone, non una.
- **Tocca:** cassa, contratto, wallet, anagrafica, agenda · **Copertura:** Il contratto richiede id_cliente alla creazione: nessun pagatore terzo né beneficiario assegnabile dopo, nessuna entità buono/voucher.

**S62 — «Con il mio vecchio trainer avevo ancora 4 sedute pagate»** · *rara* · 🔴 assente
- **Scena:** Simone arriva da un collega che ha smesso per infortunio: «Avevo un pacchetto da 10, me ne restano 4 già pagate. Roberto ha detto che ti gira lui i soldi». Il pacchetto era verbale, Roberto è vago, e Simone si aspetta di allenarsi da subito senza riaprire il portafoglio.
- **Oggi (senza software):** Il PT si fida, allena Simone 4 volte «gratis» e insegue Roberto a voce per €120. Metà delle volte quei soldi non arrivano mai, e non c'è niente di scritto.
- **Cosa serve:** Anagrafare Simone con 4 crediti-sedute a origine tracciata («trasferimento da collega, €120 attesi da Roberto»): un credito da incassare verso un TERZO, visibile e sollecitabile, separato dalla posizione di Simone che deve risultare pulita. Se Roberto non paga, il PT decide consapevolmente se assorbire la perdita.
- **Rischio se manca:** Lavorare 4 ore gratis senza nemmeno saperlo formalmente, oppure rovinare la relazione con Simone chiedendo a lui soldi per un problema che è di Roberto.
- **Tocca:** anagrafica, contratto, insoluto, cassa, comunicazioni · **Copertura:** Nessun credito verso terzi: crediti_terminazione nasce solo da una terminazione propria e resta intestato al cliente, mai a un collega debitore.


### scenari:vita-pacchetto (10 scenari)

**S3 — Contanti oggi, POS domani: il metodo cambia a ogni rata** · *quotidiana* · 🟢 piena
- **Scena:** Marco paga la rata di ottobre da €120 in contanti a fine seduta; a novembre passa col POS; a dicembre fa un bonifico dal telefono nello spogliatoio. Stesso contratto, tre canali diversi in tre mesi.
- **Oggi (senza software):** Contanti nel portafoglio, scontrino POS in borsa, screenshot del bonifico su WhatsApp: la sera il PT prova a ricomporre tutto su un foglio o un Excel.
- **Cosa serve:** Metodo di pagamento sul singolo movimento (mai sul contratto), registrazione dell'incasso in 10 secondi a bordo campo, cassa filtrabile per canale (contanti/POS/bonifico).
- **Rischio se manca:** La cassa contanti non torna a fine mese; per il commercialista il PT non sa ricostruire quanto è entrato per canale e da chi.
- **Tocca:** rate, cassa · **Copertura:** CashMovement.metodo vive sul singolo movimento e ogni pagamento rata registra data/metodo (payment history per rata, anche N pagamenti con metodi diversi); il ledger è consultabile per data.

**S22 — Rinnovo anticipato con sedute residue: «le perdo?»** · *settimanale* · 🟡 parziale
- **Scena:** Ad Anna restano 3 sedute e 10 giorni di validità, ma è motivata e vuole rinnovare subito col pacchetto da 20. Domanda inevitabile: 'Le 3 che avanzano le perdo?'. Il PT: 'No no, le accodiamo'.
- **Oggi (senza software):** Le 3 sedute residue vivono nella testa del PT: a volte le regala per sbaglio contandole due volte nel nuovo pacchetto, a volte le dimentica del tutto.
- **Cosa serve:** Rinnovo agganciato al contratto precedente (catena rinnovi) con gestione esplicita dei crediti residui: accodati, convertiti o azzerati, ma con una decisione tracciata e visibile a entrambi.
- **Rischio se manca:** Crediti fantasma: la cliente conta 23 sedute, il PT 20. La discussione a metà pacchetto brucia più fiducia di quanto valgano i 3 crediti.
- **Tocca:** contratto, rate, agenda · **Copertura:** La catena rinnovi esiste (rinnovo_di + POST /renew) ma i crediti residui del vecchio non hanno gestione esplicita accoda/converti/azzera: il vecchio finisce SOSPESO in worklist finché una decisione separata (estendi/decadi) lo regola.

**S26 — Acconto alla firma, saldo a rate** · *settimanale* · 🟢 piena
- **Scena:** Lunedì sera Sara, nuova cliente, firma un pacchetto da 10 sedute a €450. Ha in borsa €150 in contanti e li lascia come acconto; il resto in due rate da €150 il 1° dei prossimi due mesi. Tutto deciso in piedi, tra una seduta e l'altra.
- **Oggi (senza software):** Appunto sul quaderno o nota sul telefono: 'Sara 150 dati, mancano 300'. Il piano rate vive nella memoria del PT e in un vocale WhatsApp.
- **Cosa serve:** Creare il contratto con acconto registrato subito in cassa (contanti) e piano rate residuo auto-generato con date; vedere a colpo d'occhio versato/residuo per contratto.
- **Rischio se manca:** Acconto in contanti dimenticato o registrato due volte; a fine mese il PT non ricorda se Sara deve €300 o €450 e chiedere la cifra sbagliata è imbarazzante.
- **Tocca:** contratto, rate, cassa · **Copertura:** ContractCreate registra l'acconto con ENTRATA in cassa atomica, generate_payment_plan crea il piano rate con date, e versato/residuo derivano dal SSoT contract_state.residuo().

**S28 — «Questo mese la rata te la do il 20»** · *settimanale* · 🟢 piena
- **Scena:** Il 2 del mese Giulia scrive su WhatsApp: 'Scusa, questo mese ho l'assicurazione dell'auto, la rata te la porto il 20'. Il PT ovviamente dice sì. Il 20 arriva e nessuno dei due se lo ricorda. Variante: «la pago il 10 del prossimo, insieme all'altra».
- **Oggi (senza software):** Il messaggio affonda nella chat; il PT si affida alla buona fede e alla propria memoria, cioè a niente.
- **Cosa serve:** Spostare la scadenza della singola rata (senza toccare le altre) con traccia dello spostamento, e farla riemergere come promemoria alla nuova data.
- **Rischio se manca:** La rata slitta di mese in mese finché si somma alla successiva: chiedere €240 in un colpo solo diventa imbarazzante e spesso si lascia perdere. Soldi persi per quieto vivere.
- **Tocca:** rate, comunicazioni, insoluto · **Copertura:** update_rate consente di spostare data_scadenza della singola rata (sempre modificabile) con audit trail e sync dei movimenti; gli alert overdue seguono la nuova data.

**S30 — Pacchetto scaduto con sedute avanzate** · *settimanale* · 🟢 piena
- **Scena:** Il pacchetto di Roberta (10 sedute, 3 mesi) scade venerdì e ne ha usate solo 7: tra influenza e trasferte ha saltato tre settimane. Chiede: 'Le altre 3 le posso fare la settimana prossima, vero?'.
- **Oggi (senza software):** Il PT allunga la scadenza a voce e basta: la data scritta sul foglio smette di contare per chiunque.
- **Cosa serve:** Proroga esplicita e tracciata della scadenza, oppure conversione delle sedute residue in wallet/conguaglio: regola flessibile ma decisa caso per caso dal PT, con lo storico delle proroghe visibile.
- **Rischio se manca:** Se le scadenze sono sempre elastiche sparisce l'urgenza del rinnovo; se sono rigide senza strumento di proroga il PT passa per rigido e perde la cliente.
- **Tocca:** contratto, agenda, wallet · **Copertura:** È il SOSPESO del FDM §6: worklist «Contratti sospesi» con le tre azioni Estendi (auditata) / chiudi-con-conguaglio / decadi — la proroga è esplicita e tracciata.

**S37 — Lo sconto promesso a voce quattro mesi prima** · *mensile* · 🔴 assente
- **Scena:** A marzo, per trattenere Luisa indecisa, il PT le dice: 'Al prossimo rinnovo ti faccio €400 invece di €450'. A luglio, al rinnovo, Luisa se lo ricorda benissimo; il PT no, e sul momento non ha nessun modo di verificare.
- **Oggi (senza software):** Promesse commerciali affidate alla memoria o sepolte in chat WhatsApp di mesi prima; nel dubbio il PT concede sempre (perde margine) o nega (perde fiducia).
- **Cosa serve:** Nota commerciale / prezzo concordato futuro sull'anagrafica cliente che riemerge al momento del rinnovo, e prezzo consigliato che parte dallo storico reale (quanto ha pagato davvero l'ultima volta e con che sconto).
- **Rischio se manca:** Erosione silenziosa del margine e figuracce: il prezzo diventa una trattativa a memoria in cui il PT parte sempre sconfitto.
- **Tocca:** anagrafica, listino, contratto, comunicazioni · **Copertura:** Solo note_interne libere sul cliente: nessun prezzo-concordato-futuro strutturato che riemerga al rinnovo, nessun prezzo consigliato dallo storico.

**S47 — Paga tutto subito e strappa lo sconto** · *mensile* · 🟡 parziale
- **Scena:** Luca, dirigente, odia le rate: 'Quanto viene se ti pago tutto ora?'. Pacchetto da 20 sedute a listino €900, chiudono a €850 con bonifico immediato. Il piano rate previsto non nasce mai.
- **Oggi (senza software):** Il PT dice un numero a braccio, poi non ricorda più se lo sconto era 50 o 80 euro; il prezzo 'vero' del pacchetto si perde per sempre.
- **Cosa serve:** Saldo integrale alla firma senza creare rate fittizie da marcare pagate una a una; prezzo di listino e prezzo praticato entrambi tracciati, con lo sconto visibile come tale.
- **Rischio se manca:** Sconti a braccio non tracciati erodono il margine; al rinnovo Luca pretende 'il prezzo dell'altra volta' e il PT non ha memoria per contrattare.
- **Tocca:** contratto, rate, cassa, listino · **Copertura:** Il saldo integrale senza rate fittizie è già possibile (acconto = prezzo intero, o incassa-residuo G6); prezzo di listino vs praticato e lo sconto come dato non esistono (listino assente).

**S54 — Upgrade a metà pacchetto con conguaglio al volo** · *mensile* · 🟡 parziale
- **Scena:** Dopo 4 sedute del pacchetto da 10 (€450), Federica decide di passare a 2 sedute a settimana e vuole il pacchetto da 20 (€800). Ha già versato €250. Il PT deve calcolare davanti a lei quanto valgono le 4 sedute consumate e quanto del versato migra sul nuovo.
- **Oggi (senza software):** Calcolo a mente al volo, spesso arrotondato a favore della cliente pur di chiudere; nessuna traccia di come si è arrivati al numero finale.
- **Cosa serve:** Trasformazione del contratto con conguaglio pro-rata guidato: sedute consumate al prezzo unitario del vecchio, eccedenza versata portata sul nuovo (o a wallet), con il calcolo spiegato in chiaro da mostrare alla cliente.
- **Rischio se manca:** Conguagli sistematicamente sbagliati a sfavore del PT; oppure, mesi dopo, le due parti ricordano numeri diversi e non esiste una versione dei fatti.
- **Tocca:** contratto, rate, wallet, cassa · **Copertura:** I pezzi esistono tutti (terminazione con conguaglio pro-sedute + settlement-preview + wallet + nuovo contratto in catena rinnovo_di); manca il flusso «trasforma contratto» unico col calcolo spiegato.

**S57 — Carnet senza scadenza per la cliente turnista** · *mensile* · 🟢 piena
- **Scena:** Carla, infermiera turnista, compra un carnet da 10 sedute a €500 senza scadenza e viene 'quando può': 3 volte in un mese, poi sparisce per sei settimane. Dopo 8 mesi le restano 4 sedute — o forse 5, nessuno dei due lo sa con certezza.
- **Oggi (senza software):** Tacche su un foglio in ufficio o conteggio a memoria; ogni tanto si riscorrono insieme i messaggi WhatsApp per ricostruire le presenze.
- **Cosa serve:** Contratto senza scadenza come cittadino di prima classe (niente date fittizie), contatore crediti sempre esatto scalato dagli eventi agenda, saldo mostrabile alla cliente in un tap.
- **Rischio se manca:** 'Per me ne mancavano 5': la singola seduta contesa vale €50 e un rapporto. In più i carnet eterni sono ricavi già incassati con un debito di servizio invisibile.
- **Tocca:** contratto, agenda · **Copertura:** data_scadenza NULL è first-class («pacchetto senza termine», FDM §2, boundary aperto 2026-06-23 con checkbox UI) e crediti_usati è computed-on-read: il contatore è sempre esatto.

**S70 — Downgrade per difficoltà economiche (tenere il cliente)** · *rara* · 🟡 parziale
- **Scena:** A gennaio Stefano perde il secondo lavoro e chiede di passare da 2 sedute a settimana a 1: 'Non ce la faccio più con €300 al mese'. Il PT vuole tenerlo, non perderlo, e riscrive l'accordo al volo.
- **Oggi (senza software):** Rinegoziazione a voce: il vecchio foglio firmato viene ignorato e si va avanti 'a fiducia' con cifre nuove mai messe per iscritto.
- **Cosa serve:** Ridurre il contratto (o chiuderlo con conguaglio pro-rata e aprirne uno più piccolo nella stessa catena) mantenendo lo storico intatto: quanto pagato, quante sedute fatte, cosa vale il residuo.
- **Rischio se manca:** Contratto sulla carta e realtà divergono in modo permanente; se il rapporto si incrina non esiste una versione condivisa di chi deve cosa.
- **Tocca:** contratto, rate, wallet · **Copertura:** La via «chiudi con conguaglio (chiusura_consensuale) + nuovo contratto in catena» esiste e preserva lo storico; nessun flusso di riduzione/trasformazione in un solo atto.


---

## 3. SCENARI AGGIUNTI DAL CRITIC (SC1-SC17 — angolature mancate dalle lenti)

**SC1 — Il tetto del forfettario: quanto ho incassato quest'anno, PER CASSA?** · *mensile, quotidiana in Q4*
- **Scena:** PT in regime forfettario (85.000€ di tetto): a ottobre vuole sapere quanto ha incassato nell'anno solare e quanto margine gli resta prima di sforare; a dicembre valuta se chiedere al cliente di pagare la rata a gennaio. Nel forfettario conta l'INCASSATO (principio di cassa), non il maturato: la distinzione cassa/competenza di ADR-014 qui è fiscale, non solo gestionale.
- **Cosa serve:** KPI incassato-anno-solare per cassa (tutte le fonti: rate, singole, acconti, wallet applicato NO perché non è incasso nuovo), proiezione fine anno, e chiarezza su cosa conta come incasso fiscale vs movimento interno.

**SC2 — «Me la fai la fattura col codice fiscale? Così la detraggo»** · *mensile (picco a fine anno)*
- **Scena:** Cliente convinto che le sedute del chinesiologo siano detraibili come spese sanitarie (non lo sono: il chinesiologo non è professione sanitaria). Chiede fattura con CF, a volte chiede di 'farla passare' come altro. Il PT deve dire no senza perdere il cliente e comunque emettere documento corretto.
- **Cosa serve:** Campo CF/dati fiscali sul cliente, natura prestazione chiara nell'export per il commercialista, e NESSUNA feature che assecondi la riclassificazione — il confine va deciso, non subito.

**SC3 — La marca da bollo da 2€ sopra i 77,47€** · *quotidiana (ogni incasso sopra soglia)*
- **Scena:** Ogni ricevuta/fattura forfettario sopra 77,47€ vuole il bollo da 2€: praticamente OGNI incasso di rata o pacchetto. Chi lo paga? È dentro il prezzo del pacchetto o si aggiunge? Il PT lo scopre dal commercialista a cose fatte e i conti non tornano di 2€ a documento.
- **Cosa serve:** Decisione esplicita se il CRM ne sa qualcosa (promemoria/flag) o se dichiara il confine 'documenti = commercialista'. Oggi il confine è implicito.

**SC4 — «Facciamo senza ricevuta?» — la verità operativa vs la contabilità fiscale** · *settimanale (realtà del settore)*
- **Scena:** Cliente propone contanti senza documento. Qualunque cosa il PT decida, la seduta è avvenuta e il credito è scalato: il CRM DEVE registrare la verità operativa (agenda, crediti, portafoglio), ma i suoi numeri non coincideranno mai col fiscale. Se il CRM pretende di essere il registro fiscale, il PT smette di registrare gli incassi scomodi e TUTTO il dato finanziario si corrompe.
- **Cosa serve:** Dichiarazione di design: il CRM è registro OPERATIVO, non fiscale. Nessuna feature 'nero', ma nessun accoppiamento rigido incasso↔documento che spinga il trainer a falsificare o omettere.

**SC5 — Satispay alle 19:47: notifica sul telefono, nessuna causale** · *quotidiana (Satispay è ovunque tra i 20-40enni italiani)*
- **Scena:** Il cliente paga la singola con Satispay a fine seduta. A fine mese il PT ha 23 movimenti Satispay/PayPal/bonifico sull'estratto e deve capire quale corrisponde a quale rata/singola. S3 copre il metodo che cambia; manca la RICONCILIAZIONE: vista incassi per metodo e periodo da affiancare all'estratto conto.
- **Cosa serve:** Metodo di pagamento come dimensione obbligatoria di ogni incasso (incluse le singole), vista/export 'incassi per metodo nel periodo' per riconciliare in 10 minuti.

**SC6 — Il bonifico vero ma in transito: né pagato né insoluto per 48 ore** · *settimanale*
- **Scena:** S13 copre la bugia; qui il bonifico è REALE ma SEPA ordinario: arriva tra 1-2 giorni. La seduta singola è stata fatta oggi. Per 48h il sistema la mostra come insoluta? Il cliente storico se lo vede contestare si offende. Serve una semantica per il limbo.
- **Cosa serve:** Decisione: esiste uno stato 'dichiarato/in transito' (con data attesa) o resta non-pagato fino a conferma? Se resta non-pagato, l'UI deve distinguere 'insoluto vero' da 'bonifico dichiarato ieri' — sennò i solleciti partono a sproposito.

**SC7 — Il POS si mangia l'1,8%: incassati 60€, arrivati 58,92€** · *mensile (ogni riconciliazione)*
- **Scena:** Fine mese: la cassa CRM dice 2.400€ via POS, l'estratto SumUp/Nexi dice 2.356,80€. Il PT non capisce se ha perso un incasso o sono le commissioni. Nessuno dei 79 scenari tocca il lordo/netto per metodo.
- **Cosa serve:** Decisione esplicita: la cassa è AL LORDO (probabile), documentato in UI; eventualmente un totale commissioni stimato per metodo come voce informativa, mai come movimento.

**SC8 — Il corso posturale over-65 del martedì e giovedì: 60€ al mese, senza contare le presenze** · *quotidiana per chi fa ginnastica di gruppo (metà dei chinesiologi)*
- **Scena:** Il chinesiologo tiene ginnastica dolce in piccolo gruppo: si paga a MESE (flat, a frequenza), non a crediti. Nessun conteggio presenze, rinnovo tacito mensile. Il modello contratto+crediti non lo rappresenta: o crediti finti (12 crediti/mese che nessuno scala) o resta fuori dal CRM. È il TERZO modello commerciale reale accanto a pacchetto e singola, e non compare né nei 79 scenari né nella ricerca.
- **Cosa serve:** ADR-025 deve almeno DECIDERE se l'abbonamento flat è in scope, differito o esplicitamente fuori — oggi è in un limbo non dichiarato.

**SC9 — Il pacchetto misto del chinesiologo: valutazione 60€ + 10 rieducazione + retest incluso** · *settimanale per il chinesiologo*
- **Scena:** Percorso tipico: valutazione posturale iniziale (prezzo proprio), 10 sedute di rieducazione, retest finale incluso che NON scala crediti. Righe eterogenee con valori diversi dentro un contratto. S6 copre la valutazione singola e S54 l'upgrade, ma nessuno il contratto composito — che al recesso (ADR-016, valorizzazione erogato) esplode: a che prezzo conto la valutazione già fatta?
- **Cosa serve:** Decidere se il contratto resta monoprezzo/monotipo (e il misto si modella come contratto+singola collegata) o se servono tipi di seduta con valore proprio. Impatta direttamente la valorizzazione pro-rata.

**SC10 — La figlia che gestisce i soldi della mamma di 78 anni** · *settimanale*
- **Scena:** Inverso di S31: cliente anziana, niente smartphone né WhatsApp, paga in contanti anticipati o paga la figlia con bonifico. Promemoria rate, ricevute e comunicazioni vanno alla figlia; l'anamnesi e le sedute sono della madre. Con l'invecchiamento della clientela chinesiologica è il caso standard, non l'eccezione.
- **Cosa serve:** Contatto amministrativo/pagatore distinto dal cliente (nome, telefono, canale), a cui instradare template WhatsApp finanziari; il portale pubblico resta opzionale (cliente offline).

**SC11 — «Cancella tutti i miei dati» — ma ha 180€ di insoluto e 3 anni di storia contabile** · *rara ma legalmente obbligata (e il primo caso arriverà)*
- **Scena:** Ex cliente esercita il diritto GDPR alla cancellazione. Il PT ha obbligo di conservazione decennale delle scritture (art. 2220 c.c.) e un credito da esigere. Cancellare il cliente oggi orfanizza movimenti cassa, contratti, ledger — o li distrugge (vietato da ADR-019). Nessuno scenario e nessuna ricerca tocca il conflitto erasure vs retention contabile.
- **Cosa serve:** Policy di anonimizzazione parziale: anagrafica/anamnesi cancellabili, spina dorsale finanziaria conservata pseudonimizzata; blocco o warning esplicito se ci sono partite aperte.

**SC12 — Gli eredi e le 7 sedute pagate del sig. Franco** · *rara ma critica (reputazione e rispetto)*
- **Scena:** Seguito di S73: settimane dopo il decesso, la famiglia chiede il rimborso delle sedute pagate e non godute. Il conguaglio va fatto verso un NON-cliente (l'erede), con documentazione seria. Il wallet non ha senso (non c'è contratto futuro); serve l'uscita di cassa pulita e la chiusura definitiva.
- **Cosa serve:** Percorso di chiusura con rimborso a terzi: beneficiario del rimborso ≠ cliente, causale documentata, cliente sigillato dopo.

**SC13 — Il certificato medico scaduto e la seduta singola di domani** · *settimanale*
- **Scena:** Il cliente storico del caso canonico S39 torna dopo 6 mesi: l'aggancio a 'TUTTO' include anche il certificato medico non agonistico scaduto e l'anamnesi vecchia. Il PT lo scopre (forse) a seduta iniziata. Nessuno dei 79 scenari collega compliance documentale e prenotazione.
- **Cosa serve:** Warning (non blocco) alla creazione di seduta — singola O a credito — se certificato scaduto/assente o anamnesi più vecchia di N mesi. È il complemento operativo del principio 'agganciato a tutto'.

**SC14 — Settembre: 9 nuovi in 12 giorni** · *stagionale (2 picchi/anno), intensità quotidiana nel picco*
- **Scena:** S69/S75 coprono la stagionalità in USCITA (agosto, stagionali); manca quella in ENTRATA: settembre e gennaio portano ondate di prove, contratti, acconti, listino promo con scadenza. Il PT fa data entry alle 22 e sbaglia i prezzi promo dopo il 30 settembre.
- **Cosa serve:** Creazione contratto rapida da template/listino, prezzi promo con finestra di validità, e che il suggeritore prezzi non proponga il prezzo promo a novembre.

**SC15 — L'aumento di gennaio: da 45€ a 50€, ma non per i 6 storici** · *annuale, ma gli effetti durano 12 mesi*
- **Scena:** S46 copre il singolo cliente col prezzo vecchio; manca la MECCANICA dell'aumento: il PT alza il listino per i nuovi, mantiene (grandfathering) alcuni storici, deve comunicarlo e ricordarsi chi ha quale prezzo. Con prezzo 'consigliato dallo storico' l'aumento non attecchisce mai: lo storico suggerisce sempre il prezzo vecchio.
- **Cosa serve:** Listino versionato con decorrenza + prezzo-per-cliente esplicito che vince sul listino; il suggeritore deve dichiarare QUALE fonte sta usando (storico cliente vs listino corrente).

**SC16 — Il voucher welfare: la seduta la paga Fitprime a 38€, non il cliente a 60€** · *rara oggi per l'1:1, in crescita rapida*
- **Scena:** Cliente arriva con app welfare aziendale (Wellhub/Fitprime): check-in in app, il PT incassa a fine mese dall'aggregatore a tariffa convenzionata, inferiore al listino. È una singola con payer terzo, prezzo imposto e incasso differito aggregato. S76 copre la B2B diretta a 60 giorni, non l'aggregatore per-visita.
- **Cosa serve:** Payer terzo istituzionale, tariffa convenzionata che NON inquina lo storico prezzi del cliente, riconciliazione di N sedute contro un incasso mensile unico.

**SC17 — Il ripensamento a 14 giorni: contratto firmato in salotto, disdetto dopo 5** · *rara ma legalmente non negoziabile*
- **Scena:** Contratto concluso fuori dai locali commerciali (a domicilio, online): il Codice del Consumo dà 14 giorni di recesso con rimborso integrale se il servizio non è iniziato. S68 copre il recesso pro-rata a percorso avviato; il ripensamento pieno pre-avvio è un istituto diverso con esito diverso (rimborso 100%, zero valorizzazione).
- **Cosa serve:** Nel flusso di terminazione, un esito 'ripensamento entro 14gg' con rimborso integrale d'ufficio; e consapevolezza che le penali no-show verso consumatori rischiano la vessatorietà (art. 33) se non firmate.


---

## 4. DOMANDE APERTE PER ADR-025

Le domande che l'ADR deve rispondere PRIMA che una riga di codice venga scritta. Ognuna nasce da uno o più scenari del catalogo.

1. **Q1 — Natura semantica della singola.** La seduta singola è una nuova CLASSE semantica ai sensi di ADR-024 o un contratto degenere da 1 credito? Quali assi di stato ha (pagato/erogato/insoluto) e qual è la sua macchina a stati completa — incluso cosa significano Rinviato e Cancellato_Tardivo quando non c'è un credito da liberare (ADR-017 non si applica)?

2. **Q2 — Ontologia dell'insoluto.** L'insoluto è un'entità di prima classe nel ledger (ADR-022) o un derivato calcolato (seduta Completata − incassi collegati)? Chi lo fa nascere: il completamento della seduta, la mezzanotte, o un atto esplicito del trainer? E chi lo può estinguere oltre al pagamento (rinuncia, stralcio)?

3. **Q3 — Wallet negativo o compensazione esplicita.** Il wallet (ADR-020) può andare negativo, o wallet e insoluto restano due contatori separati a compensazione ESPLICITA? Se il cliente ha 50€ di wallet e 60€ di insoluto, il Portafoglio mostra −10€, oppure due righe e un'azione «compensa» che scrive entrambi i ledger atomicamente?

4. **Q4 — Pagamento parziale sulla singola.** È ammesso il pagamento parziale su una singola (30€ su 60€)? Se sì, il resto è insoluto immediato o «saldo aperto» senza sollecito? Se no, come si registra il cliente che materialmente ti ha dato metà (S27 lo prova per le rate — la pressione arriverà anche qui)?

5. **Q5 — Unpay misto wallet+contanti.** Unpay di una singola pagata 50% wallet + 50% contanti: l'invalidazione simmetrica ripristina il wallet nello stesso movimento atomico? E se nel frattempo il wallet è stato speso su un altro contratto — si va negativi, si blocca l'unpay, o si genera insoluto?

6. **Q6 — Algoritmo del prezzo consigliato.** Qual è l'ALGORITMO del prezzo consigliato dallo storico: ultimo prezzo implicito (prezzo_totale/crediti dell'ultimo contratto)? Media pesata? Filtra per modalità (domicilio/online/studio)? Cosa propone a storico vuoto (listino? niente?)? Ed è spiegabile in UI («consigliato perché…») come impone la regola del determinismo?

7. **Q7 — Le singole a prezzo zero.** Le singole a prezzo ZERO (prova gratuita S19, omaggio S42, barter S43, recupero regalato) sono entità legittime della stessa classe? Come si marca il motivo del prezzo zero e come si ESCLUDONO dallo storico del suggeritore e dai KPI di fatturato senza sporcarli?

8. **Q8 — Penale monetaria su no-show singola.** No-show su singola non prepagata (S40): nasce una PENALE MONETARIA? A che importo (prezzo pieno, quota fissa, percentuale)? Finisce negli insoluti o in un registro penali distinto? E la penale non firmata da un consumatore è esigibile o solo memoranda (vessatorietà art. 33 Cod. Consumo)?

9. **Q9 — Conversione prova/singole → pacchetto.** Conversione prova/singole → pacchetto (S7, S20, S63): lo scalo del già-pagato passa dal wallet, da uno sconto sul prezzo del contratto, o da una riga di conguaglio dedicata? Ognuna delle tre scrive numeri diversi nel ledger e nel fatturato — quale racconta la verità?

10. **Q10 — Insoluto, temporal fence e write-off.** Un insoluto entra nel temporal fence (ADR-023)? Un insoluto di 18 mesi è liquidabile/congelabile? E il write-off: come si stralcia un credito inesigibile SENZA distruggere il libro mastro (ADR-019) e senza che sparisca dai totali storici?

11. **Q11 — KPI e pitfall #14.** Una singola erogata ma non pagata è «fatturato»? L'insoluto vive in cassa (no per definizione), in competenza, nei KPI cumulativi o operativi? Ogni nuovo KPI del Portafoglio deve nascere col commento inline «stato» vs «cumulativo» — chi lo impone nella spec?

12. **Q12 — Il listino come entità.** Il listino è un'ENTITÀ (versionata, con decorrenza, con override per-cliente) o un default di form? Come rappresenta il prezzo di favore riservato (S38: visibile solo al trainer, mai stampato) e l'aumento di massa di gennaio con grandfathering dei clienti storici?

13. **Q13 — Chi è il PAGATORE?** Il ledger registra un payer distinto dal cliente (madre S31, figlia del cliente anziano, coniuge S50/S61, azienda S76, aggregatore welfare)? A chi si intesta la ricevuta e a chi vanno i template WhatsApp di sollecito?

14. **Q14 — Portafoglio e regola 1 (privacy).** Il pannello Portafoglio è SOLO trainer o una parte va nel portale pubblico? «Quante me ne restano» (S4) è il dato che il cliente vuole, ma la regola 1 vieta dati finanziari in viste pubbliche: crediti-sedute sì e saldi € no? La linea va tracciata nell'ADR, non lasciata al frontend.

15. **Q15 — GDPR vs contabilità.** Cancellazione di un cliente con insoluto aperto o storia finanziaria — cosa si anonimizza, cosa si conserva 10 anni, cosa si blocca? L'insoluto crea un legittimo interesse a conservare l'anagrafica? Serve una risposta PRIMA che l'entità insoluto esista.

16. **Q16 — Migrazione e retroattività.** Gli squilibri già esistenti (S52: consumato più di quanto pagato dentro contratti) vengono riclassificati come insoluti retroattivi al boot, o il concetto vale solo in avanti? Cosa fa schema_sync sul DB reale deployato di Chiara e su una fresh install — e il classify OD-1 pre-upgrade copre anche questo? Alessio è N/A: l'installazione consegnata non è usata in esercizio e non ha un database data-bearing noto (attestazione founder 2026-07-19).

17. **Q17 — Confine fiscale del CRM.** Qual è il confine fiscale del CRM: la singola genera un documento (numerazione, bollo) o il CRM è dichiaratamente registro operativo e delega TUTTO al commercialista (S15/S16)? La non-decisione qui produce o un fatturatore abusivo o buchi di riconciliazione — va scritta nell'ADR in ogni caso.

18. **Q18 — Sovrapagamento sulla singola.** Dà 70€ per 60€, «tieni il resto» (S14/S51): il delta va a wallet (coerente con ADR-020 anti-clamp), è mancia fuori cassa, o si alza il prezzo della seduta? Serve UN default deterministico e la risposta cambia fatturato e suggeritore prezzi.

19. **Q19 — Upsell nudge verso il pacchetto.** Dopo quante singole consecutive il sistema suggerisce il pacchetto (upsell nudge sul caso S39 che si ripete)? È in scope ADR-025 o esplicitamente rimandato — e se rimandato, il modello dati di oggi lo rende possibile domani (le singole sono interrogabili come serie per cliente)?

20. **Q20 — Freshness check su cliente fermo.** La singola su cliente fermo da 6+ mesi (caso canonico): forza una rivalidazione dell'anamnesi o almeno un warning safety («anamnesi di 14 mesi fa»)? Qual è la soglia di stantio e chi la decide? «Agganciato a TUTTO» senza freshness check è un aggancio a dati potenzialmente falsi.

21. **Q21 — Abbonamento mensile flat.** L'abbonamento mensile flat (corso posturale di gruppo, senza crediti) è dichiarato DENTRO o FUORI da ADR-025? Se fuori, l'ADR deve dirlo esplicitamente e indicare dove vivrà la decisione — altrimenti il terzo modello commerciale del chinesiologo resta per sempre modellato con crediti finti.

22. **Q22 — Il «pacchettino a voce».** Il «pacchettino a voce» (S58: 3 sedute a 150€) è un contratto minimo o 3 singole collegate da un prezzo bloccato? Se ADR-025 introduce la singola senza rispondere, ogni trainer sceglierà a caso e i dati diventeranno inconfrontabili: serve una regola di soglia o una guida esplicita contratto-vs-singole nella scelta di creazione.

23. **Q23 — Bonifico in transito.** *(da SC6)* Esiste uno stato «dichiarato/in transito» con data attesa, o la singola/rata resta non-pagata fino a conferma? Se resta non-pagata, l'UI deve distinguere «insoluto vero» da «bonifico dichiarato ieri» — sennò i solleciti partono a sproposito e offendono chi ha già pagato.

---

## 5. STATISTICHE

### 5.1 Numeri del catalogo

| Metrica | Valore |
|---|---|
| Scenari totali | **96** (79 catalogo + 17 aggiunti dal critic SC1–SC17) |
| Domande aperte per ADR-025 | **23** |
| Lenti | 6 (primo-contatto 16 · interruzioni-chiusure 16 · pagamenti-irregolari 14 · fuori-schema 13 · vita-pacchetto 10 · flussi-annessi 10) |

### 5.2 Ripartizione copertura (sui 79 scenari base)

| Copertura | N | % | Lettura |
|---|---:|---:|---|
| 🟢 Piena | 12 | 15,2% | Il modello contratto+rate+cassa attuale è solido dove è stato costruito (G6–G9): rate parziali, metodi per movimento, riapertura, carnet senza scadenza, terminazione bilaterale |
| 🟡 Parziale | 40 | 50,6% | I pezzi esistono (terminazione, wallet, worklist, escape hatch) ma mancano il collante e le entità di raccordo: Portafoglio, pendenze, sospensioni, viste aggregate |
| 🔴 Assente | 27 | 34,2% | Concentrata quasi interamente sui 4 assi nuovi di ADR-025: seduta singola, insoluto, listino, wallet caricabile — più prospect/pagatore terzo |

**Cross-tab copertura × frequenza** (dove fa più male):

| Frequenza | N | 🟢 Piena | 🟡 Parziale | 🔴 Assente |
|---|---:|---:|---:|---:|
| Quotidiana | 4 | 2 | 1 | **1** |
| Settimanale | 26 | 5 | 7 | **14** |
| Mensile | 30 | 4 | 18 | 8 |
| Rara | 19 | 1 | 14 | 4 |

> Il dato più duro: **14 scenari SETTIMANALI su 26 sono completamente scoperti**. Il buco di ADR-025 non è un caso limite: è la settimana tipo del PT.

### 5.3 Assi più toccati (sui 79 scenari base)

| Asse | Tocchi | Note |
|---|---:|---|
| contratto | 52 | La spina dorsale: quasi tutto vi orbita attorno |
| cassa | 43 | Ogni scenario economico finisce nel mastro — che oggi non conosce le singole |
| agenda | 41 | La seduta è l'unità di lavoro: l'agenda è dove il denaro nasce |
| comunicazioni | 40 | Sollecito, resoconto, promemoria: metà del valore è dire il numero giusto al cliente |
| sedute_singole | 35 | **Asse nuovo ADR-025** — 35 tocchi per un'entità che non esiste |
| anagrafica | 35 | Prospect, pagatore terzo, provenienza: l'anagrafica attuale è mono-ruolo |
| rate | 32 | L'area più matura del sistema (5 delle 12 coperture piene) |
| wallet | 22 | **Asse nuovo** — esiste (ADR-020) ma solo in uscita da terminazione: mai caricabile, mai spendibile |
| insoluto | 19 | **Asse nuovo** — 19 scenari lo richiedono, zero entità lo rappresentano fuori contratto |
| listino | 17 | **Asse nuovo** — 17 scenari; senza listino il «prezzo consigliato» non ha fonte dichiarabile |

### 5.4 Sintesi per ADR-025

I 4 assi nuovi (sedute_singole 35 + wallet 22 + insoluto 19 + listino 17 = **93 tocchi**) attraversano 27 scenari a copertura assente e la maggioranza dei 40 parziali. Il pattern è costante in tutte le lenti: **il denaro che non passa da un contratto oggi non esiste** — e per il PT reale quel denaro è quotidiano (S1), settimanale (S5–S16) e canonico (S39). Il pannello Portafoglio (S24, S39, S72) è il punto di convergenza UI di tutti e quattro gli assi; le 23 domande aperte sono il perimetro decisionale minimo perché nasca deterministico, auditabile e coerente con ADR-017/019/020/022/023/024 e con il pitfall #14.

*Fine documento — CATALOGO SCENARI REALI, 2026-07-07.*
