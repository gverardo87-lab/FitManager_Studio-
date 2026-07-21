# SPEC — Frontend core intuitivo, affidabile e distintivo

**Stato:** 🟡 IN CORSO — FE-0.1 privacy/worklist + FE-0.2a profilo Cliente completati 2026-07-21;
FE-0.2b dettaglio Contratto/Cassa è il prossimo microstep
**Data:** 2026-07-21
**Branch:** `FitManager_Studio`
**Tipo:** remediation frontend e read-model additivi; nessuna nuova policy di prodotto
**Audit fondante:** `docs/archive/AUDIT_FRONTEND_CORE_INTUITIVITA_2026-07-21.md`
**Autorità:** `AGENTS.md` → `MANIFESTO.md` → `LAUNCH_SCOPE.md` → `frontend/CLAUDE.md` → ADR/SSoT finanziarie
**Sequenza preesistente:** v1.0.14 ✅ → blocco P → G-MAC
**Decisione di scheduling:** founder 2026-07-21 — `v1.0.15` contiene blocco P + FE-0 completo +
criticità FE-1; ottimizzazioni/redesign estesi restano fuori release; G-MAC apre dopo validazione e
consegna della `v1.0.15`.

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

## 4. FE-1 — Operabilità e accessibilità core

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
