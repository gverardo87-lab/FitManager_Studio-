# SPEC — Frontend core intuitivo, affidabile e distintivo

**Stato:** 🟡 IN CORSO — FE-0 Integrità completato; FE-1.0 implementato (`f678292`), fix
router-only (`d382a4b`) integrato dal coordinamento scroll/cache (`8f5ca45`), in retest LIVE founder
**Data:** 2026-07-21
**Branch:** `FitManager_Studio`
**Tipo:** remediation frontend e read-model additivi; nessuna nuova policy di prodotto
**Audit fondante:** `docs/archive/AUDIT_FRONTEND_CORE_INTUITIVITA_2026-07-21.md`
**Autorità:** `AGENTS.md` → `MANIFESTO.md` → `LAUNCH_SCOPE.md` → `frontend/CLAUDE.md` → ADR/SSoT finanziarie
**Sequenza preesistente:** v1.0.14 ✅ → blocco P → G-MAC
**Decisione di scheduling:** founder 2026-07-21/22 — `v1.0.15` contiene blocco P + FE-0 completo +
criticità FE-1; FE-1.0 entra subito dopo il test LIVE FE-0 e prima di P1. Ottimizzazioni/redesign
estesi restano fuori release; G-MAC apre dopo validazione e consegna della `v1.0.15`.

> La presente SPEC è la casa del lavoro aperto. A chiusura dell'ultimo gate: consuntivo, fold-back
> negli evergreen realmente toccati, append a `docs/learning/BUILD_LOG.md` e spostamento in
> `docs/archive/specs/` nello stesso commit docs del gate finale.

## 1. Impact map

- **Obiettivo:** rendere il ciclo Clienti → Contratti → Agenda → Incassi → Cassa comprensibile,
  veritiero e veloce senza esporre la complessità del motore.
- **Layer:** frontend; backend solo per read-model additivi/paginazione quando il FE non può garantire
  completezza senza duplicare logica.
- **Invarianti:** privacy-first; finanze nei contesti dedicati; nessun money-math nuovo nel FE;
  ownership multi-tenant; audit trail e transizioni finanziarie invariati; query inverse simmetriche;
  loading/error/empty distinti; CRM utilizzabile senza AI.
- **Non-obiettivo:** redesign generale, nuova macro-feature, nuova semantica finanziaria, modifica di
  ledger/residuo/wallet, nuova home decisa per gusto estetico.

### Tesi falsificabile

Dopo il blocco:

1. nessun errore core appare come empty, not-found o stato positivo;
2. nessun importo finanziario appare nella overview Clienti;
3. i journey core sono completabili da tastiera e comunicano sempre esito/prossimo passo;
4. oltre 200 clienti/contratti ricerca e conteggi restano completi;
5. un utente pilota identifica senza aiuto dove pianificare, incassare e controllare la cassa.

## 2. Perché e quando inserirlo

### Decisione senior

Il lavoro non entra come refactor monolitico. Entra per gate indipendenti e verificabili.

| Ordine | Gate | Quando | Perché |
|---:|---|---|---|
| 1 | **FE-0 Integrità** | Primo gate della `v1.0.15`, prima di P1 | Chiude privacy ed errori che possono mentire sui money-path; riduce rischio prima di aggiungere prestazioni singole/wallet |
| 2 | **FE-1 Operabilità** | Nella `v1.0.15` limitatamente alle criticità e coordinato con P sui file condivisi | Evita doppio lavoro su form, contratto, incassi e profilo cliente |
| 3 | **FE-2 Modello mentale** | Fuori dalla `v1.0.15`; rivalutazione dopo consegna, senza ritardare G-MAC | Stabilizza ownership e copy su entità complete solo se l'evidenza LIVE lo richiede |
| 4 | **FE-3 Scalabilità** | Dopo FE-0; parallelizzabile solo su file/API non condivisi con P | Corregge completezza >200 e costo di caricamento senza cambiare dominio |
| 5 | **FE-4 Distintività LIVE** | Dopo FE-0..3 e su build stabile | Il visual polish deve amplificare un modello corretto, non mascherarne i difetti |

**Regola di coordinamento con P:** nessun gate FE modifica in parallelo gli stessi file/money-path di
`SPEC_P_PRESTAZIONI_SINGOLE_E_PORTAFOGLIO.md`. Se P1 apre prima di FE-0, i finding sovrapposti sono
assorbiti nei suoi microstep e verificati anche con gli AC di questa SPEC; non si crea un secondo ramo.

**Ratifica:** il founder ha autorizzato il 2026-07-21 l'inserimento di FE-0 prima di P1 e la nuova
sequenza `v1.0.14 → v1.0.15 (FE-0 + criticità FE-1 + P) → G-MAC`. L'autorizzazione riguarda lo
scheduling; ogni gate conserva impact map, verifiche e GO operativo previsti dal Delivery Loop.

## 3. FE-0 — Integrità percettiva e privacy

**Scope minimo:** niente redesign, niente nuova semantica, niente calcoli monetari.

### Criteri di accettazione

- **AC-FE0-1 Privacy:** lista Clienti senza prezzo, versato, residuo o crediti. Eventuale segnale
  amministrativo è non monetario e porta a Contratti/Rinnovi & Incassi.
- **AC-FE0-2 Verità:** Rinnovi & Incassi non mostra KPI/«Tutto in regola» se una fonte è in errore;
  rende fonte fallita e retry.
- **AC-FE0-3 Not-found:** profilo Cliente/Contratto usa «non trovato» solo su 404; rete/5xx hanno
  error state e retry.
- **AC-FE0-4 Sezioni parziali:** Contratti, Sessioni e Movimenti del profilo distinguono loading,
  error, empty e ready.
- **AC-FE0-5 Cassa:** saldo/statistiche/andamento non spariscono in errore; ogni blocco dichiara
  indisponibilità senza inventare zero.
- **AC-FE0-6 Dipendenze form:** select Cliente in Contratto/Evento espone loading/error e non presenta
  un menu vuoto ambiguo.
- **AC-FE0-7 Test:** render/integration test coprono successo vuoto, 404, 500, rete e fallimento
  parziale; canary specifico impedisce «Tutto in regola» su query fallita.

### Verifica FE-0

- Vitest mirati sui componenti/query state;
- lint file toccati + `next build`;
- suite backend pertinente solo se cambia un read-model;
- `tools/scripts/check-all.sh`;
- test LIVE autenticato desktop: errore simulato per ciascuna fonte, zero submit finanziari reali;
- review privacy della lista Clienti.

### Consuntivo parziale FE-0.1 — 2026-07-21

- **AC-FE0-1 chiuso:** lista Clienti senza importi/prezzo/crediti; resta solo «Azione
  amministrativa» non monetaria con accesso a Rinnovi & Incassi.
- **AC-FE0-2 chiuso:** Rinnovi & Incassi aggrega sei fonti (incluse worklist crediti/rimborsi),
  blocca KPI/empty positivo se una fonte fallisce, nomina i dati indisponibili e offre retry.
- Card crediti/rimborsi rese presentazionali: la pagina possiede query state e conteggio, senza
  doppia sottoscrizione React Query.
- Test aggiunti: privacy overview + errore mai «Tutto in regola» + worklist credito inclusa.
- Evidenza: **107/107 Vitest**, lint mirato zero warning/error, `next build` verde (TypeScript + 20
  pagine). Warning preesistenti non bloccanti: fixture `edge-cases.test.ts` su assegnazione a const;
  convenzione Next middleware deprecata.
- **Asse DENARO invariato:** nessuna formula, mutation, invalidazione o transizione modificata.

### Consuntivo parziale FE-0.2a — 2026-07-21

- **AC-FE0-3 Cliente chiuso:** «Cliente non trovato» è riservato a ID invalido/HTTP 404; rete, 5xx
  o risposta senza dato producono errore con retry. Il dettaglio Contratto resta in FE-0.2b.
- **AC-FE0-4 chiuso sul profilo Cliente:** Contratti, Sessioni e Movimenti distinguono loading,
  error, empty e ready; anche il wallet dichiara l'indisponibilità senza sparire.
- Contratti/sessioni/readiness falliti non alimentano più checklist, path consigliato o completion
  dot: il profilo anagrafico resta visibile con banner «dati parziali» e retry aggregato.
- Utility condivisa `isNotFoundError` introdotta per riuso sul dettaglio Contratto.
- Evidenza: 4 canary nuovi verdi; suite frontend **111/111**; lint mirato pulito; `next build` verde.
- **Asse DENARO invariato:** sole query read-only e stati render; zero mutation/formula/invalidation.

### Consuntivo parziale FE-0.2b — 2026-07-21

- **AC-FE0-3 Contratto chiuso:** «Contratto non trovato» è riservato a ID invalido/HTTP 404; rete,
  5xx o risposta senza dato hanno errore e retry.
- Sessioni del contratto distinguono error da empty; nello Storico il ledger già verificato dal
  read-model principale resta visibile mentre un errore timeline è dichiarato come degradazione
  parziale, mai «Nessuna attività».
- `DataErrorState` promosso da helper del profilo a primitive UI condivisa, senza cambiare resa o
  comportamento dei microstep precedenti.
- Evidenza: 2 canary nuovi + regressione profilo; suite frontend **113/113**; lint mirato pulito;
  `next build` verde.
- **Asse DENARO invariato:** ledger solo renderizzato dal wire; zero calcolo, mutation o invalidazione.

### Consuntivo parziale FE-0.3 — 2026-07-21

- **AC-FE0-5 chiuso:** hero e contesto di saldo, che dipendono da due fonti, dichiarano le sorgenti
  non disponibili con retry; KPI e grafico mensili dipendono solo dalle statistiche e restano
  visibili se fallisce il solo saldo. Nessun blocco sparisce o inventa zeri; il libro mastro resta
  indipendente quando la sua query è verificata.
- Andamento non usa più fallback monetari a zero su errore. Entrate/Uscite espongono errori per
  colonna; il fallimento del filtro clienti non cancella i movimenti già verificati.
- Spese fisse distinguono configurazione vuota da query fallita e sospendono il form di modifica
  finché la lista non è verificata. Anche spese da confermare, scadenze e previsioni hanno retry;
  il badge pending usa `?`, mai zero implicito, se la fonte fallisce.
- Evidenza: 5 canary nuovi; suite frontend **118/118**; lint mirato pulito; `next build` verde
  (TypeScript + 20 pagine). Il lint globale resta rosso per 17 errori preesistenti fuori scope,
  nessuno nei file FE-0.3.
- Verifica avversariale: il primo pass ha rilevato che un errore del solo saldo nascondeva anche KPI
  mensili validi; dipendenze separate e canary speculare aggiunto prima del gate finale. Riesame
  conclusivo `financial-invariant-verifier`: **PASS**, nessun blocker; soli gap LOW su retry aggregato,
  loading del filtro clienti split e copertura click dei retry secondari.
- **Asse DENARO invariato:** sole query read-only e stati render; zero formula, mutation,
  invalidazione o transizione finanziaria modificata.

### Consuntivo FE-0.4 e chiusura FE-0 — 2026-07-22

- **AC-FE0-6 chiuso:** i selettori Cliente di Contratto ed Evento distinguono loading, errore e
  lista realmente vuota; il menu è disabilitato finché la dipendenza non è verificata e ogni errore
  offre retry.
- La creazione Contratto e il write-path PT sono sospesi quando il Cliente obbligatorio non è
  disponibile. Modifica/rinnovo con relazione già fissata e categorie Evento senza Cliente non sono
  bloccati impropriamente; regole B4/B5 e warning soft restano invariati.
- `watch()` sostituito con `useWatch()` nei due form toccati: stesso valore osservato, nessun warning
  React Compiler e nessuno stato derivato aggiuntivo.
- **AC-FE0-7 consolidato:** 7 canary nuovi per loading/error/empty/retry e non-blocco dei flussi
  indipendenti; regressione B4/B5 verde. Suite frontend **125/125**, lint mirato zero warning/error,
  `next build` verde (20 pagine).
- Verifica avversariale: il primo pass ha rilevato il blocco improprio del PT in modifica con Cliente
  persistito e lookup KO; condizione ristretta ai soli PT che devono ancora scegliere un Cliente e
  canary regressivo aggiunto prima del gate finale. Riesame conclusivo: **PASS**, nessun blocker;
  associazione label/Select e live-region dell’errore restano gap LOW già assorbiti da FE-1.
- **FE-0 completato:** AC-FE0-1..7 consuntivati nei quattro microstep; nessuna policy, formula
  monetaria, mutation, invalidazione o transizione finanziaria modificata.

## 4. FE-1 — Operabilità e accessibilità core

### FE-1.0 — Contextual Deep-Link Contract v1

**Evidenza fondante:** nel test LIVE founder del 2026-07-22, «Azione amministrativa» dalla lista
Clienti ha raggiunto correttamente Rinnovi & Incassi, ma ha perso il contesto e aperto la pagina
dall'inizio. Il difetto è ricorrente per le CTA cross-page: raggiungere la superficie corretta non è
sufficiente se l'operatore deve ricercare di nuovo cliente e azione.

**Decisione founder:** adottare un contratto di navigazione contestuale URL-based. Non è una nuova
regola di dominio e non richiede ADR: preserva intenzione e identità durante una navigazione già
lecita, senza cambiare calcoli, ownership, transizioni o audit finanziari.

#### Quando e perimetro

- **Ora:** FE-1.0 è il primo microgate dopo FE-0 e precede P1. È read-only, chiude un finding LIVE e
  tocca una sorgente/destinazione già stabilizzate da FE-0.
- **Vertical slice v1.0.15:** solo `Clienti → Rinnovi & Incassi → rata scaduta`.
- **Dopo 2–3 destinazioni reali:** estrarre l'eventuale helper/hook comune. FE-1.0 non introduce un
  router parallelo, registry globale o astrazione generalizzata non ancora provata.
- **Coordinamento P:** nessuna apertura automatica di dialog finanziari e nessuna modifica ai
  write-path. Se P apre prima della replica su altre superfici, le estensioni attendono il relativo
  gate per evitare conflitti.

#### Contratto URL v1

```text
/rinnovi-incassi?focus=overdue-rate&client_id=<positive-int>
/rinnovi-incassi?focus=overdue-rate&client_id=<positive-int>&rate_id=<positive-int>
```

- `focus` esprime l'intenzione semantica; `client_id` identifica il soggetto; `rate_id`, quando la
  sorgente lo conosce, identifica l'azione esatta.
- L'URL contiene solo enum e ID: vietati nome, telefono, email, importo, note o altri dati personali
  e finanziari.
- Parametri assenti, non supportati o non interi positivi non devono causare crash né selezionare un
  target diverso: la pagina resta nel proprio stato ordinario.
- Se sono presenti `rate_id` e `client_id`, il target è valido solo se entrambi appartengono allo
  stesso item già restituito dal read-model autorizzato. Nessun fetch o bypass ownership dedicato.
- La sorgente Clienti v1 conosce soltanto `ha_rate_scadute` e `client_id`: la destinazione risolve le
  rate di quel cliente. Se sono multiple, porta alla prima nel loro ordine canonico e comunica
  esplicitamente «prima di N», senza aprire o scegliere un pagamento.
- L'URL semantico resta copiabile e resistente a reload/back-forward; si consuma soltanto
  l'evidenziazione transitoria, non il parametro.

#### Comportamento della destinazione

1. Durante loading la pagina conserva l'intenzione e non tenta letture DOM premature.
2. In errore resta valido il truth state FE-0; dopo retry riuscito il focus contestuale riprende.
3. A dati verificati, il target viene portato nel viewport con offset compatibile con header sticky,
   riceve focus programmatico (`tabIndex=-1`) e una marcatura testuale temporanea oltre al colore.
4. Lo scroll è `smooth` solo se `prefers-reduced-motion` non richiede riduzione; altrimenti è
   immediato. Il focus usa `preventScroll` per evitare un secondo salto.
5. Una live region `polite` annuncia esito e molteplicità senza spostare il lettore di schermo.
6. Se il target non esiste più, la pagina non cade silenziosamente in alto: mostra «Questa azione
   non è più presente; potrebbe essere già stata risolta» e mantiene visibile la worklist verificata.
7. Il deep-link non apre dialog, non precompila importi e non invoca mutation. L'ultimo comando sui
   money-path resta esplicito, consapevole e auditabile.
8. Nessun timeout arbitrario governa il ritrovamento del target: l'effetto dipende da dati verificati
   e ref DOM effettivamente montato; timer ammessi solo per rimuovere la marcatura transitoria.

#### Criteri di accettazione FE-1.0

- **AC-FE1-0a:** la CTA privacy-safe genera URL con `focus=overdue-rate` e `client_id`, senza PII né
  valori monetari.
- **AC-FE1-0b:** con una rata del cliente, la card corretta riceve scroll, focus e indicatore non
  cromatico; nessuna mutation viene eseguita.
- **AC-FE1-0c:** con più rate dello stesso cliente, l'esito dichiara la molteplicità e non presenta
  una scelta arbitraria come azione univoca.
- **AC-FE1-0d:** target assente/stale, parametri invalidi e query in errore hanno fallback distinti;
  il retry conserva l'intenzione.
- **AC-FE1-0e:** reload/back-forward conservano il deep-link; motion ridotta, tastiera e live region
  sono verificati automaticamente e LIVE.
- **AC-FE1-0f:** viewport mobile/tablet/desktop non coprono il target e non introducono scroll
  orizzontale.
- **AC-FE1-0g:** su navigazione client già in cache, il secondo e i successivi click sullo stesso
  deep-link rieseguono scroll, focus e marker senza refresh. Il link sorgente cede esplicitamente
  alla destinazione la gestione dello scroll; la destinazione attende un nodo target connesso al DOM
  e il frame successivo prima di applicare focus e scroll.

#### Verifica FE-1.0

- Vitest: href sorgente, parser parametri, target singolo/multiplo/assente, attesa loading,
  errore→retry, focus DOM, `prefers-reduced-motion`, zero chiamate a `usePayRate().mutate`;
- lint mirato + suite frontend completa + `next build`;
- review Web Interface Guidelines sui file toccati;
- test LIVE founder: singola rata, più rate e azione già risolta, desktop + viewport mobile;
- `financial-invariant-verifier`: conferma asse DENARO preservato, pur trattandosi di sola
  navigazione/read-model.

#### Consuntivo tecnico FE-1.0 — 2026-07-22 (LIVE pendente)

- **Docs-first:** contratto, timing e AC ratificati prima del runtime nel commit `724b74a`.
- **Implementazione:** commit `f678292`; CTA Clienti con URL privacy-safe, parser fail-closed,
  risoluzione `client_id`/`rate_id`, focus e scroll contestuali, marker testuale, live region
  persistente, reduced motion e fallback stale. Nessun dialog o pagamento automatico.
- **Verifier avversariale:** il primo pass ha trovato un blocker React StrictMode (il cleanup
  cancellava il primo `requestAnimationFrame` lasciando l'esito consumato) e un gap HIGH sulla live
  region montata già popolata dopo loading/error. Corretti con dipendenze primitive idempotenti e
  nodo `role=status` persistente nei tre truth-state; parser irrigidito anche sui parametri duplicati.
- **Canary:** 13 test del contratto URL + 10 test di integrazione focus + 3 test di navigazione
  ripetuta/cache; coperti singolo, multiplo, target esatto/mismatch, stale, loading→ready, error→retry,
  StrictMode, popstate, reduced motion, away/back sullo stesso deep-link e zero
  `usePayRate().mutate`.
- **Evidenza automatica:** suite frontend **151/151**; lint mirato zero warning/error; `next build`
  verde (TypeScript + 20 pagine); pre-commit reale verde (`ruff check api/` + build Next).
- **Verifica finanziaria:** `financial-invariant-verifier` **MONEY AXIS PRESERVED** — zero file,
  simboli, formule, payload, mutation o invalidazioni money-mutating modificati; `handlePay`
  byte-identico alla base. Zero MONEY-REGRESSION/COVERAGE-GAP/INVARIANT-UNGUARDED.
- **Limite host dichiarato:** Bash non installato e launcher Python della venv non più disponibile;
  `check-all.sh`/harness backend non avviabili. Il verifier ha sostituito il controllo con diff
  differenziale, scan writer/simboli, hash del payload e integrità statica di guard/anchor invariati.
- **Finding LIVE e root cause:** il primo utilizzo riusciva, il secondo no. L'hook leggeva
  `window.location.search` soltanto al mount e ascoltava `popstate`; la navigazione client di Next
  App Router riusa la pagina/cache e non emette `popstate`, quindi intent e dipendenze restavano
  invariati al ritorno sullo stesso cliente.
- **Remediation `d382a4b`:** pathname e query arrivano dagli hook reattivi di Next; il lifecycle del
  focus include la route completa. Il canary specifico ha fallito contro il codice precedente
  (secondo `scrollIntoView` assente) ed è verde dopo il fix. Verifier finale **PASS**, zero finding e
  **MONEY AXIS PRESERVED**; restano solo gap di test LOW non bloccanti sulla combinazione
  repeat+StrictMode e sulla sequenza esplicita della live region.
- **Finding LIVE #2 — 2026-07-23:** `d382a4b` è necessario ma non sufficiente. Dal secondo click la
  navigazione aggiorna correttamente l'URL ma non porta il target nel viewport; un refresh usa lo
  stesso URL e completa subito lo scroll. Questo falsifica un errore di parsing/router e isola un
  race di commit/scroll sulla navigazione cached.
- **Root cause confermata:** il canary di `d382a4b` manteneva il target DOM montato durante la finta
  permanenza su `/clienti`, mentre il runtime reale lo scollega e lo rimonta. Soprattutto, il layout
  dashboard ripristina `scroll:/rinnovi-incassi` con retry a 0/50/100/250/500/1000/2000 ms: con
  cache calda questi timer sovrascrivevano lo scroll contestuale eseguito una sola volta. Il refresh
  salta il restore perché il pathname iniziale non cambia, spiegando integralmente l'evidenza LIVE.
- **Remediation `8f5ca45`:** la CTA usa `scroll={false}` e, prima della navigazione, applica il
  contratto esistente `clearPageState("/rinnovi-incassi")`; il layout non programma quindi restore
  concorrenti. La callback ref rende reattivo il remount tardivo della card; scroll, focus, marker e
  relativo timeout partono nel frame successivo solo su nodo connesso. La live region resta vuota
  durante loading/error cached e si popola insieme al focus verificato dopo retry.
- **Canary rosso→verde:** restore key non consumata, target DOM tardivo, durata marker con RAF
  sospeso e cached-data+errore su altra fonte hanno fallito prima delle rispettive patch. Pacchetto
  mirato **30/30**, suite **151/151**, build e pre-commit verdi; verifier **PASS**, zero finding e
  **MONEY AXIS PRESERVED**.
- **Gate residuo:** ripetere LIVE due volte consecutive il target presente, poi verificare desktop +
  viewport mobile sui casi più rate e target già risolto. FE-1.0 resta aperto fino a evidenza LIVE;
  nessun evergreen viene aggiornato prima della stabilizzazione del pattern su ulteriori
  destinazioni.

### Criteri di accettazione

- **AC-FE1-1:** promemoria Agenda apribile/chiudibile da tastiera con primitive semantica e focus
  restituito all'origine.
- **AC-FE1-2:** Link e toggle Sidebar sono controlli separati; toggle ha `aria-expanded`,
  `aria-controls` e focus visibile.
- **AC-FE1-3:** importo, metodo, data e motivazione in ogni money-path hanno label associata,
  descrizione/errori accessibili e focus sul primo errore.
- **AC-FE1-4:** skip link presente; un solo `h1` logico per pagina.
- **AC-FE1-5:** filtri selezionabili espongono `aria-pressed`/`aria-selected`; icon button nominati;
  loading annunciati; stato mai solo cromatico.
- **AC-FE1-6:** `transition-all` sostituito sui file toccati e motion non essenziale rispetta
  `prefers-reduced-motion`.

### Verifica FE-1

- audit tastiera completo su Cliente, Contratto, Evento e Incasso;
- axe/WCAG automatico come supporto, non come unico oracolo;
- test focus open/close e submit invalido;
- viewport desktop e tablet/mobile sui controlli toccati.

## 5. FE-2 — Modello mentale e ownership

### Decisioni da validare con test, non da imporre dal documento

- Cliente = situazione e prossimo passo, senza numeri finanziari;
- Contratto = accordo, piano e storia del rapporto;
- Rinnovi & Incassi = worklist amministrativa;
- Cassa = registro, audit e controllo;
- Agenda = tempo, sessioni e relazione contrattuale;
- una sola home operativa primaria tra `Oggi` e `Dashboard`.

### Criteri di accettazione

- **AC-FE2-1:** il path cliente non disabilita azioni lecite; distingue requisito, raccomandazione,
  completato e disponibile.
- **AC-FE2-2:** CTA «Incassa rata» conduce al money-path canonico; «Registra movimento» resta azione
  di Cassa e non è sinonimo di incasso contrattuale.
- **AC-FE2-3:** ogni superficie ha una frase-scopo univoca e la navigazione evita duplicazioni.
- **AC-FE2-4:** ricerca Clienti include telefono normalizzato oltre a nome/email.
- **AC-FE2-5:** test osservativo con almeno un founder e un PT pilota: dato uno scenario, entrambi
  scelgono la superficie corretta senza istruzioni; tempi/errori sono registrati.

**Stop condition:** se la revisione richiede una nuova regola di dominio o cambia la semantica di una
transizione finanziaria, FE-2 si ferma e apre ADR/Addendum + SPEC dedicata.

## 6. FE-3 — Completezza e performance percepita

### Criteri di accettazione

- **AC-FE3-1:** Clienti/Contratti usano paginazione e ricerca server-side; test con >200 record prova
  completezza di risultati, conteggio e filtri.
- **AC-FE3-2:** query key parametriche e `keepPreviousData` evitano blank/skeleton distruttivi al
  cambio filtro; `isFetching` comunica aggiornamento non bloccante.
- **AC-FE3-3:** tab analitici, grafici e dialog pesanti sono caricati condizionalmente dove misurato
  utile; niente regressione sul primo task.
- **AC-FE3-4:** profilo usa summary/read-model per presenza e readiness invece di dataset completi,
  se il backend può fornirlo senza duplicare logica.
- **AC-FE3-5:** Todo Agenda ha range/summary server-side; scaduti/oggi restano completi.
- **AC-FE3-6:** invalidazioni money-path restano corrette e simmetriche; ogni riduzione è coperta da
  test di coerenza e verifier finanziario.

### Misure minime

- bundle analyzer prima/dopo sui route chunk core;
- numero richieste e byte trasferiti per apertura Cliente/Cassa;
- tempo ricerca con dataset >200;
- refetch count dopo incasso, unpay, rinnovo ed evento;
- nessuna ottimizzazione accettata se riduce auditabilità o consistenza.

## 7. FE-4 — Coerenza e distintività

FE-4 usa il design system esistente, non ne crea uno concorrente.

### Criteri di accettazione

- teal come accento primario; neutral/amber/red con significato coerente;
- nessun blue/violet/rose/emerald decorativo sui file core toccati;
- gerarchia orientata a prossimo passo, non a quantità di KPI;
- progressive disclosure senza nascondere warning o segnali critici;
- verifica desktop, tablet e mobile reale;
- confronto prima/dopo basato su task completion, errori e comprensione, non su preferenza estetica.

## 8. File/layer probabili e coordinamento

| Gate | Superfici principali | Rischio conflitto |
|---|---|---|
| FE-0 | Clienti, profilo, Rinnovi & Incassi, Cassa, hook query | Alto con P su contratto/wallet |
| FE-1 | Sidebar, layout, Agenda Todo, dialog finanziari | Medio con P sui dialog money-path |
| FE-2 | Panoramica cliente, navigazione, copy Contratti/Rinnovi/Cassa | Alto: richiede test e ratifica, non parallelizzare alla cieca |
| FE-3 | hook Clienti/Contratti/Todo, endpoint read-model, lazy import | Medio cross-layer |
| FE-4 | surface-role, pagine core, responsive | Basso solo dopo stabilizzazione |

Per ogni microstep: impact map locale → implementazione minima → test immediato → report rischio/gap →
commit coeso. Nessun feature branch salvo coordinamento esplicito; push solo su ok founder secondo il
workflow vigente.

## 9. Fuori scope

- prestazioni singole e portafoglio (SPEC_P);
- G-MAC e distribuzione;
- goodwill G8.5;
- modifica di ledger, residuo, netto, crediti, rate o transizioni;
- nuova dashboard o nuova macro-feature;
- PWA/mobile post-launch, salvo verifica responsive dei file toccati;
- refactor generalizzato di componenti non necessari agli AC.

## 10. Definition of Done del blocco

1. AC-FE0..4 verificati con evidenza reale;
2. full suite raccolta verde per i layer toccati;
3. `ruff check api/` se backend toccato, lint/build frontend, `check-all.sh`;
4. financial-invariant-verifier per ogni money-path/read-model finanziario toccato;
5. test LIVE autenticato desktop + tablet/mobile, con dataset >200 per FE-3;
6. consuntivo per gate con commit e suite;
7. fold-back solo negli evergreen realmente modificati;
8. append al `BUILD_LOG.md` e archiviazione della SPEC nello stesso commit docs finale.
