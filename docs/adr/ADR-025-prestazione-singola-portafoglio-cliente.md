# ADR-025 — Prestazione singola e Portafoglio cliente

**Stato:** Accettata (2026-07-08) — decisioni ratificate dal founder una a una (sessioni 2026-07-07
e 2026-07-08: Q1-Q5, Q13, Q17 percorse insieme + 4 ratifiche del giro precedente).
**Blocco:** **«P» (Portafoglio & Prestazioni singole)** — spec dedicata da aprire (P0..Pn).
**Fondamenta:** `docs/product/CATALOGO_SCENARI_PT.md` (96 scenari, 23 domande; 14/26 scenari
settimanali oggi scoperti) + `docs/archive/RICERCA_COMPETITOR_WALLET_SEDUTE_SINGOLE_2026-07-07.md`
(11 vendor, leggi W1-W11). Si appoggia a: ADR-020 (wallet), ADR-022 (penna/classify), ADR-024
(nascita per-classe), ADR-017/019/023 (assi evento, ledger, fence).

## Context

Il modello attuale è contratto-centrico: la seduta fuori contratto non esiste come fatto economico
(caso canonico: cliente storico di passaggio che vuole 2-3 sedute flash — oggi nasce un evento
orfano fail-silent). Il catalogo dimostra che NON è un caso limite: seduta singola, insoluto,
listino e wallet caricabile concentrano il 34% di scenari scoperti, in gran parte settimanali.
Visione founder: «portafoglio cliente che include TUTTO — sicuro e in controllo»; differenziatore
di mercato confermato da W9 (nessun vendor ha il prezzo suggerito dallo storico).

## Decisions

1. **D-CLASSE-PRESTAZIONE** *(Q1)* — La seduta singola è una **classe semantica nuova di prima
   classe** («prestazione singola»), NON un contratto degenere: entità economica propria
   (importo, incassi collegati) agganciata all'evento agenda, che resta puro scheduling coi suoi
   6 stati. Nasce col protocollo ADR-024: riga in matrice, penna dedicata, classify, gemelli di
   esaustività, Hypothesis. Rinviato/Cancellato non hanno crediti da liberare (ADR-017 non si
   applica): Cancellato nei termini = nessun fatto economico. Conforme W1 (11/11 vendor: la
   singola è un prezzo contestuale all'atto, mai un prodotto a listino).
2. **D-SCELTA-ALLA-CREAZIONE** *(ratifica 2026-07-07)* — Alla creazione di un evento PT per
   cliente senza contratto agganciabile, il form offre la **scelta esplicita** «Prestazione
   singola (€X)» — lo stato diventa voluto, mai subìto. Sostituisce il warning-ansia di G9.7.1.
3. **D-PREZZO-LIBERO-CONSIGLIATO** *(ratifica 2026-07-07 + W9)* — Importo **libero**, con
   **suggerimento deterministico e spiegabile** derivato dallo storico del cliente («consigliato
   perché…»); algoritmo definito in spec (Q6), mai un gate. È il differenziatore: non esiste in
   nessun vendor esaminato.
4. **D-INSOLUTO-DERIVATO** *(Q2)* — L'insoluto è un **derivato fail-loud**, mai un'entità
   parallela: `insoluto = prestazione EROGATA − Σ incassi collegati`. Nasce al **Completato**
   (il servizio reso non pagato È l'insoluto), si estingue con pagamento o **condono esplicito
   auditato** (rettifica dedicata, pattern `quota_stornata`; W8: il write-off è un atto, mai
   un'omissione). Due viste di UN derivato (W7): per-prestazione riconciliabile + aggregato
   per-cliente.
5. **D-WALLET-SEPARATO-COMPENSA** *(Q3 + W5)* — Wallet e insoluto restano **grandezze separate**;
   il wallet non va MAI negativo. La compensazione è un **atto esplicito atomico** (scrive
   entrambi i ledger nella stessa transazione, via penna) che il Portafoglio **suggerisce**
   («Compensa €X») — applicazione della legge *segnale ⇒ azione*.
6. **D-PARZIALE-AMMESSO** *(Q4)* — Pagamento parziale ammesso sulla prestazione singola; il
   residuo è insoluto per costruzione (dal derivato). Un solo concetto di pendenza; il tono del
   sollecito è UX, non semantica.
7. **D-UNPAY-FLOOR** *(Q5)* — L'unpay di un pagamento misto ripristina wallet+cassa
   atomicamente; se il ripristino manderebbe il wallet negativo (credito già speso a valle) →
   **409 esplicito con l'azione** («annulla prima l'applicazione su X»). Stesso principio del
   floor-unpay post-reopen (G9.4): a ritroso si ripercorrono i passi, mai scavalcarli. Vietato
   l'insoluto sintetico.
8. **D-PAGATORE-LEGGERO** *(Q13)* — Campo `pagatore` **opzionale** sul movimento di cassa
   (riferimento ad altro cliente o testo libero): ricevute intestate e solleciti indirizzati al
   pagatore quando presente. L'entità Payer completa (corporate/família) è **fuori scope
   dichiarato**, forward-compatible.
9. **D-REGISTRO-OPERATIVO** *(Q17)* — FitManager è **registro operativo dichiarato**: traccia
   incassi, insoluti e riepiloghi; NON emette documenti fiscali; vocabolario UI mai fiscale
   (mai «fattura» — «riepilogo», «registrazione»); export pulito per il commercialista.
   Validazione nella **call tributarista unica** già pendente (policy `pro_sedute` PROVISIONAL +
   penali consumatore art. 33 + questo confine).
10. **D-PORTAFOGLIO** *(ratifica 2026-07-07 + W7/W10)* — Pannello «Portafoglio» nel profilo
    cliente: crediti sedute SCALABILI (soli contratti attivi), wallet €, crediti da incassare,
    insoluti — ogni riga con la sua azione. Le worklist globali restano per l'azione
    cross-cliente: due viste, un solo interprete backend.
11. **D-SEGNALE-AZIONE** — Legge trasversale (nata dalla cattura del 2026-07-07, raffina
    D-MAI-SILENZIO-IN-SCRITTURA di ADR-024): **ogni segnale porta con sé l'azione** che lo
    risolve. Un warning senza scelta non dà controllo: dà ansia.

## Dispatch delle domande restanti del catalogo (Q6-Q23)

**In spec (discendenti tecniche, dentro le decisioni di cui sopra):** Q6 algoritmo suggeritore
(deterministico+spiegabile; base: prezzo implicito per-seduta dallo storico recente, fallback
dichiarato) · Q7 prezzo zero con `motivo` obbligatorio, escluso da suggeritore e KPI ricavo ·
Q9 conversione singole→pacchetto via wallet (un solo veicolo) · Q10 condono=rettifica auditata
dentro il fence · Q11 ogni KPI nuovo nasce col commento «stato vs cumulativo» (pitfall #14) ·
Q20 freshness warning su anamnesi stantia alla singola su cliente fermo · Q22 guida esplicita
contratto-vs-singole nella scelta di creazione · Q23 «bonifico dichiarato» = stato informativo
sul sollecito, non terza semantica.
**Differite con casa dichiarata:** Q8 penale monetaria su singola → **gated tributarista** ·
Q12 listino-entità versionata → post-lancio (il suggeritore non lo richiede) · Q14 portale
pubblico: crediti-sedute sì, saldi € MAI (regola 1; la linea esatta in spec) · Q15 GDPR
conservazione insoluti → Tier-3 legale (G9-G12 security gate) · Q16 nessuna riclassificazione
retroattiva: il concetto vale in avanti (OD-1 invariato) · Q19 upsell nudge → fuori scope, ma le
singole nascono interrogabili come serie per cliente · Q21 abbonamento flat mensile → fuori
scope DICHIARATO, ADR dedicato futuro (mai modellarlo con crediti finti).

## Consequences

- Nuovo money-path: nasce SOLO attraverso la macchina G9 (penna unica, classify 6+ classi —
  la classe della prestazione singola va aggiunta a `ClasseContabile` con gemello di
  esaustività —, invariant gate, Hypothesis estesa) e la checklist ADR-024.
- Il «cliente senza contratto attivo» smette di essere un ramo d'errore: è un cliente con
  Portafoglio. G9.7.2 (recupero orfani) si allinea: gli eventi 640/641 del founder diventano
  prestazioni singole o si agganciano al contratto — scelta esplicita, mai limbo.
- KPI: i ricavi da singole entrano nei cumulativi con classe propria (mai fusi coi contrattuali
  — ADR-014 resta: categorie contrattuali distinte).
- Asse DENARO esistente: byte-identico. Tutto è additivo.

## Rollback / Exit

La prestazione singola è additiva (tabella nuova + classe nuova): disattivabile da feature-flag
di creazione senza toccare i contratti. Il derivato-insoluto non scrive colonne: spegnerlo =
togliere le viste.
