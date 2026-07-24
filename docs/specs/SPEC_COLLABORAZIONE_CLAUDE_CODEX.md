# SPEC — Collaborazione agent-neutral Claude Code + Codex

**Stato:** 🟡 APERTA — A0+A1+A1.1 CHIUSI; SMOKE CLAUDE A1.1 DIFFERITO; A2+ NON AUTORIZZATI
**Data:** 2026-07-19
**Ratifica founder:** ACX-D1..D6 ratificate integralmente il 2026-07-19; ACX-D7+D8 ratificate il 2026-07-24
**Tipo:** governance di sviluppo e compatibilità tra agenti; nessuna policy di prodotto
**Autorità ereditata:** `AGENTS.md` → `MANIFESTO.md` → `LAUNCH_SCOPE.md` → documenti di layer
**Sequenza prodotto:** fuori dalla coda R0 → blocco P → candidate v1.0.15 → blocco G-MAC; non la modifica e non la blocca

---

## 0. Decisione proposta

FitManager deve poter essere sviluppato con Claude Code e Codex senza creare due metodi, due verità
operative o due code di lavoro.

La soluzione proposta è una **architettura a nucleo condiviso con adapter sottili**:

- `AGENTS.md` resta il contratto operativo unico e agent-neutral;
- `CLAUDE.md` resta l'entry point di Claude Code e, durante la migrazione, conserva il comportamento
  attuale;
- Codex usa nativamente `AGENTS.md`: **non si crea `CODEX.md`**;
- `.claude/` e l'eventuale `.codex/` contengono solo adapter/configurazioni specifiche del runtime,
  mai regole duplicate di dominio o processo;
- ADR, SPEC, SSoT evergreen e `BUILD_LOG.md` restano indipendenti dal vendor dell'agente.

Questa SPEC prescrive una migrazione **strangler**, gate per gate. Nessun taglio massivo di
`CLAUDE.md`, nessuna riscrittura degli auditor e nessuna modifica agli hook è ammessa nel gate A0.

## 1. Perché non creare `CODEX.md`

Codex scopre le istruzioni di progetto tramite `AGENTS.md`; il repository possiede già quel file e lo
ha ratificato come contratto operativo unico. Un secondo file root dedicato a Codex introdurrebbe:

1. duplicazione delle regole;
2. precedenze implicite diverse tra agenti;
3. drift non falsificabile finché un errore non emerge nel codice;
4. un terzo luogo da aggiornare oltre ad `AGENTS.md` e `CLAUDE.md`.

Il criterio è quindi: **nuovo file specifico di runtime solo quando contiene una capacità non
esprimibile nel nucleo condiviso**, mai come copia del nucleo.

Riferimento Codex ufficiale per discovery, scope e precedenza di `AGENTS.md`:
<https://learn.chatgpt.com/docs/agent-configuration/agents-md>.

## 2. Baseline verificata (fotografia A0, non SSoT evergreen)

Baseline letta sul branch `FitManager_Studio`, commit `b7423b2`, working tree pulito prima di A0:

| Superficie | Stato osservato | Conseguenza |
|---|---|---|
| `AGENTS.md` | presente, 9.588 byte | è già il nucleo operativo condiviso; resta sotto il limite Codex documentato di 32 KiB |
| `CLAUDE.md` root | presente, 34.452 byte | è un bootstrap Claude ricco e parzialmente duplicato; non va ridotto in un solo passaggio |
| `api/CLAUDE.md`, `frontend/CLAUDE.md`, `core/CLAUDE.md` | presenti | restano istruzioni di layer finché ogni responsabilità non ha una destinazione provata |
| `.claude/agents/` | 3 auditor read-only | capacità operative vive da preservare: money, docs-drift, semantic-birth |
| `.claude/settings.json` | permessi e hook PostToolUse Claude-specifici | contiene un path assoluto e un hook fail-open; è un rischio di portabilità, non scope A0 |
| `.codex/` | assente | non è un gap: si crea solo per una necessità runtime dimostrata |

La baseline è intenzionalmente una fotografia. Le verità vive restano nei file indicati dalla matrice
di ownership seguente.

## 3. Matrice di ownership: una responsabilità, una fonte

| Responsabilità | Fonte canonica | Adapter ammesso | Duplicazione vietata |
|---|---|---|---|
| Ordine delle fonti, Delivery Loop, guardrail, branch, gate, lifecycle docs | `AGENTS.md` | `CLAUDE.md` può solo indirizzare alla fonte | Copia divergente in file runtime |
| Principi di prodotto | `MANIFESTO.md` | nessuno | Regole inventate nei prompt agent |
| Perimetro di lancio | `LAUNCH_SCOPE.md` | nessuno | Roadmap implicita in `.claude/` o `.codex/` |
| Leggi di dominio | `docs/adr/` | link contestuali | Regola di dominio definita in una config agente |
| Lavoro aperto e AC | `docs/specs/` | sintesi di sessione | Piano concorrente fuori dalla work-queue |
| Sistema com'è fatto | `docs/technical/` | link contestuali | SPEC o piano di implementazione evergreen |
| Procedura condivisa Claude+Codex | futuro `docs/operations/AI_ASSISTED_DEVELOPMENT_WORKFLOW.md` | bootstrap runtime | Due procedure complete, una per vendor |
| Cronologia sviluppo | `docs/learning/BUILD_LOG.md` | nessuno | Log paralleli per agente |
| Bootstrap Claude | `CLAUDE.md` e file `*/CLAUDE.md` | `.claude/` | Copia dell'intero `AGENTS.md` a regime |
| Bootstrap Codex | `AGENTS.md` nativo | eventuale `.codex/config.toml` minimale | `CODEX.md` o fallback filename senza necessità |
| Charter auditor condivisi | futura casa agent-neutral, da ratificare ad A4 | adapter `.claude/agents/` / `.codex/agents/` | Due charter indipendenti con invarianti diversi |

## 4. Metodo docs-first condiviso

Il metodo non deve generare documentazione per ogni riga di codice. Deve depositare **prima** il
contratto minimo che rende falsificabile il cambiamento, in proporzione al rischio.

### 4.1 Classificazione obbligatoria del task

| Classe | Trigger | Deposito docs prima del codice |
|---|---|---|
| D — decisione di dominio | cambia una legge, un invariante, una policy prodotto | ADR/Addendum + SPEC aperta |
| B — comportamento o flusso | cambia comportamento osservabile, schema, write-path, più layer o percorso critico | SPEC aperta con AC e rollback |
| E — esecuzione circoscritta | applica una decisione già ratificata, fix locale o manutenzione senza nuova policy | impact map + update della SPEC esistente; nessun nuovo documento per inerzia |
| I — incidente | difetto in produzione o rischio critico emerso sul campo | incident doc + lezione/prevenzione secondo `AGENTS.md` |

Se la classificazione è dubbia, prevale temporaneamente la classe a rischio maggiore; il founder può
ridurla prima dell'implementazione.

### 4.2 Loop comune per Claude Code e Codex

1. **Orientamento:** leggere `AGENTS.md`, lo stato Git, la SPEC attiva e soltanto le fonti richieste
   dal layer.
2. **Impact map:** obiettivo, file/layer, invarianti, verifiche, esclusioni.
3. **Deposito docs:** creare o aggiornare ADR/SPEC solo quando richiesto dalla classe del task.
4. **Ratifica:** nessun codice se la SPEC contiene decisioni founder aperte o cambia dominio.
5. **Microstep:** una sola unità coesa e reversibile.
6. **Verifica immediata:** test proporzionati al rischio; sui money-path si applica il verifier
   adversariale previsto dal DoD.
7. **Fold-back:** stato/consuntivo SPEC, INDEX, SSoT interessate, `BUILD_LOG.md`, archiviazione se
   il blocco è chiuso.
8. **Checkpoint Git:** fold-back, commit e push del gate, con verifica dell'allineamento remoto.
9. **Handoff:** hash, cosa è cambiato, evidenze, rischi residui, stato Git e prossimo gate minimo.

L'agente cambia; il loop e le fonti non cambiano.

## 5. Strategia di migrazione a gate

Ogni gate è un'unità autonoma. Un gate non autorizza automaticamente il successivo.

### A0 — Deposito del contratto (questo microstep)

**Scope consentito:** questa SPEC, la sua riga in `docs/INDEX.md`, append a `BUILD_LOG.md`.

**Pass:** zero modifiche a codice, `AGENTS.md`, `CLAUDE.md`, file di layer, `.claude/` o `.codex/`;
cross-doc review verde; working diff limitato ai tre documenti previsti.

### A1 — Runbook condiviso minimo

Creare `docs/operations/AI_ASSISTED_DEVELOPMENT_WORKFLOW.md` derivato da questa SPEC e aggiungere
soltanto link espliciti dai bootstrap esistenti. Non rimuovere ancora contenuto da `CLAUDE.md`.

**Pass:** una sessione nuova Claude Code e una sessione nuova Codex eseguono il Contract Smoke di
§6 e producono le stesse cinque risposte operative. A1 è la condizione minima per iniziare nuovo
codice sviluppato con entrambi gli agenti.

**Consuntivo A1 — ✅ CHIUSO 2026-07-19:**

- creato `docs/operations/AI_ASSISTED_DEVELOPMENT_WORKFLOW.md`, derivato da `AGENTS.md`;
- aggiunti link soltanto additivi in root `AGENTS.md` e root `CLAUDE.md`: **zero righe rimosse** dai
  bootstrap, nessuna modifica ai file di layer, `.claude/` o `.codex/`;
- prompt smoke reso deterministico con allowlist di cinque fonti vive dopo che il primo tentativo
  non bounded aveva prodotto una ricerca workspace-wide patologica; `docs/archive/` resta vietato;
- Contract Smoke reale su sessioni nuove e read-only:
  - Claude Code `2.1.170`: **PASS**;
  - Codex CLI `0.144.5`: **PASS**;
- parità semantica provata su authority order, branch, coda meta/prodotto, quality gate docs/process
  e lifecycle documentale; nessuna policy inventata e nessuna fonte storica promossa ad autorità;
- verifiche applicative non eseguite: il gate non modifica codice o configurazione runtime;
- delivery: commit docs atomico A0+A1 autorizzato dal founder con messaggio
  `docs: ratifica workflow condiviso Claude Code e Codex`; push non autorizzato e non eseguito.

**Finding non bloccanti emersi dal test:**

1. `AGENTS.md` usa due sezioni numerate `7` (Quality Gates e lifecycle docs): difetto editoriale,
   nessuna divergenza di regola; fuori scope A1.
2. Codex CLI segnala la skill `.agents/skills/find-skills/SKILL.md` come priva di frontmatter perché
   una riga vuota precede il delimitatore YAML: la skill non era richiesta dallo smoke e il contratto
   A1 resta valido; fix da autorizzare come microstep separato prima di fare affidamento sulla skill.

### A1.1 — Protocollo Senior e checkpoint Git falsificabile

**Trigger founder 2026-07-24:** il metodo era applicato in modo meno rigoroso già in precedenza e il
calo è diventato evidente durante R0.1, quando un gate interamente verificato è rimasto non committato
mentre veniva analizzato il finding TLS del gate successivo.

**Root cause di processo:** `AGENTS.md` prescriveva il push dopo ogni step completato, ma il runbook
affermava che commit e push non erano impliciti. Mancavano inoltre definizioni univoche di gate vs
microstep, l'invariante di working tree tracked pulito tra gate e una tassonomia dei finding.

**Decisione ACX-D7 ratificata:**

- il microstep è verificato subito; il gate è la minima unità rilasciabile e l'unità di commit/push;
- il GO founder che apre un gate autorizza il checkpoint Git normale alla sua chiusura;
- nessun gate successivo si apre prima di push, delta remoto `0 0` e assenza di modifiche tracked
  attribuibili al gate precedente;
- file estranei dell'utente possono restare dirty solo se identificati, fuori scope e mai staged;
- un blocker in scope resta nel gate; un finding release-critical fuori scope apre HOLD/nuovo gate
  senza trattenere o contaminare il gate corrente già verde;
- docs gate decisionale e code gate sono distinti e il primo va pubblicato prima del secondo.

**Scope A1.1:** `AGENTS.md`, runbook condiviso, adapter root `CLAUDE.md`, `CONTRIBUTING.md`, riferimenti
del guard lifecycle, questa SPEC, `docs/INDEX.md` e `BUILD_LOG.md`. Nessuna policy prodotto, modifica
runtime applicativa, schema o dato persistente.

**Pass:** cross-doc review senza contraddizioni; Contract Smoke nuovo Claude Code/Codex equivalente
anche sul campo `DELIVERY_CHECKPOINT`; lifecycle guard coerente con la sezione univoca §11; diff
limitato ai file di governance; commit/push docs prima di aprire il gate TLS.

**Stato A1.1:** CHIUSO OPERATIVAMENTE SU WAIVER FOUNDER ACX-D8 — norme ratificate; Codex PASS dopo
remediation di un drift di coda; Claude Code non eseguibile per session limit fino alle 22:00 e
differito come follow-up obbligatorio. Il mancato verdetto non è registrato come PASS.

**Evidenze di verifica 2026-07-24:**

- Codex CLI `0.145.0-alpha.27`, sessione nuova read-only: primo run **FAIL** perché l'intestazione
  conservava la vecchia coda v1.0.14; corrette tutte le fonti vive senza riscrivere i consuntivi
  storici; secondo run **PASS** sui sei campi, incluso `DELIVERY_CHECKPOINT`;
- Claude Code `2.1.170`: entrambi i tentativi read-only (default e Haiku) fermati dal provider con
  `You've hit your session limit · resets 10pm`; nessun verdetto prodotto, quindi nessun PASS
  attribuito;
- waiver founder ACX-D8: procedere subito col checkpoint A1.1 e con R0.1.5, recuperando lo smoke
  Claude appena possibile. Eccezione one-shot: non modifica ACX-D7, il runbook o i pass criteria dei
  gate futuri e non autorizza a chiamare verde una verifica non eseguita;
- review deterministica: sezioni `AGENTS.md` univoche 1–11; zero marker contraddittori nelle fonti
  vive; 10/10 SPEC aperte indicizzate; zero SPEC/IMPL_PLAN in `docs/technical/`; zero SPEC
  implementate rimaste vive; link locali dei sei documenti Markdown toccati validi; `ruff check
  api/` e `git diff --check` verdi;
- `live-01-dashboard.png`, censito come file locale del founder fuori scope all'avvio, risulta assente
  al controllo finale; il founder ne ha confermato la rimozione. Variazione attribuita e stop
  condition chiusa; il file non è mai entrato nello stage.

### A2 — Inventario e riduzione controllata delle duplicazioni

Costruire una matrice riga-per-riga delle responsabilità duplicate tra `AGENTS.md`, `CLAUDE.md` e i
file di layer. Rimuovere una responsabilità per volta solo dopo averne provato la destinazione
canonica e il link dall'entry point Claude.

**Pass:** nessuna informazione operativa diventa meno raggiungibile; Contract Smoke pre/post
identico; rollback del singolo commit sufficiente. Da pianificare separatamente dalla coda prodotto
R0 → P → candidate v1.0.15 → G-MAC.

### A3 — Hook portabili e fail-loud

Sostituire path assoluti e logica silenziosamente fail-open con script repository-relative,
condivisi e testabili. Un auto-fix non deve mutare file senza rendere visibile esito e diff.

**Pass:** stessa verifica eseguibile manualmente, da Claude e da Codex; test su path con spazi;
fallimento simulato osservabile; nessun allargamento implicito dei permessi.

### A4 — Auditor: charter condiviso, adapter sottili

Estrarre i contratti dei tre auditor in una casa agent-neutral solo dopo aver definito formato,
invocazione e test di parità. Gli adapter Claude/Codex devono preservare: read-only, tassonomia,
invarianti, output contract e decisioni riservate al founder.

**Pass:** stesso diff di prova, stessi controlli minimi, stesso verdict class, zero scritture. Fino ad
allora `.claude/agents/` resta intatto e autorevole per Claude Code.

### A5 — Configurazione Codex solo se necessaria

Creare `.codex/config.toml` esclusivamente per un bisogno concreto non coperto da `AGENTS.md`.
Configurazione minima: niente copia di policy, niente path assoluti, niente modello fissato nel repo,
niente permessi più larghi dei quality gate necessari.

**Pass:** il bisogno è scritto e falsificabile; rimuovere `.codex/` non altera le regole di progetto.

### A6 — Learning agent-neutral

Aggiornare la documentazione didattica affinché distingua concetti di programmazione, metodo di
progetto e comandi specifici del singolo agente. Nessun learning viene acquisito automaticamente
come legge operativa senza review umana.

## 6. Contract Smoke Claude/Codex

Il smoke è read-only e si esegue in una sessione nuova, sullo stesso stato del gate, chiedendo a
ciascun agente di restituire con puntatore alla fonte:

1. ordine delle fonti autorevoli;
2. branch di sviluppo e divieto di feature branch non coordinate;
3. confine microstep/gate e checkpoint Git richiesto;
4. work-queue corrente e suo ordine;
5. quality gate richiesto per lo scope dichiarato;
6. lifecycle di ADR, SPEC, SSoT evergreen e `BUILD_LOG.md`.

**PASS:** le risposte sono semanticamente equivalenti e nessun agente attribuisce autorità a un
documento storico o inventa policy.

**FAIL:** divergenza di fonte, stato o gate. In caso di FAIL non si compensa aggiungendo una seconda
regola: si corregge la fonte canonica o l'adapter che non la raggiunge.

## 7. Guardrail pre-lancio

- Questa migrazione non entra nella sequenza prodotto R0 → P → candidate v1.0.15 → G-MAC.
- A0 e A1 sono docs-only; i gate A2-A6 hanno scheduling e commit separati.
- Mai combinare una migrazione di governance con un fix money-path, schema DB, release bump o build.
- Nessun gate può degradare l'operatività Claude Code già presente.
- Nessun gate può richiedere l'AI per il funzionamento del CRM.
- Il GO founder apre un solo gate e ne autorizza il checkpoint normale; ogni gate successivo richiede
  autorità propria, ma non una richiesta duplicata di commit/push per il gate già approvato.

## 8. Rollback e stop conditions

Ogni gate deve essere revertibile come unità coesa. Non sono ammessi reset distruttivi del lavoro
utente. Il gate si ferma prima di ulteriori modifiche se:

- il Contract Smoke diverge;
- una regola rimossa non ha fonte canonica raggiungibile;
- una modifica richiede permessi più ampi o path locali;
- emerge una nuova policy di prodotto o dominio non ratificata;
- il diff invade la coda release/P/G-MAC;
- il gate precedente non è pushato o lascia modifiche tracked attribuibili;
- Claude Code perde una capacità disponibile nella baseline A0.

## 9. Decisioni ratificate

| ID | Decisione | Esito founder 2026-07-19 |
|---|---|---|
| ACX-D1 | `AGENTS.md` unico nucleo; nessun `CODEX.md` | **✅ RATIFICATA** |
| ACX-D2 | Migrazione strangler; nessuna riduzione immediata di `CLAUDE.md` | **✅ RATIFICATA** |
| ACX-D3 | A1 prima di nuovo codice congiunto; A2+ separati dalla coda prodotto | **✅ RATIFICATA** |
| ACX-D4 | Auditor condivisi solo ad A4, dopo prova di parità | **✅ RATIFICATA** |
| ACX-D5 | `.codex/` nasce solo da un bisogno dimostrato | **✅ RATIFICATA** |
| ACX-D6 | Learning proposto dagli agenti, promosso a regola solo con review umana | **✅ RATIFICATA** |
| ACX-D7 | Gate unità di commit/push; GO iniziale autorizza il checkpoint; nessun gate successivo prima dell'allineamento remoto e tracked-clean | **✅ RATIFICATA 2026-07-24** |
| ACX-D8 | Waiver one-shot: A1.1 può essere pubblicato e R0.1.5 aperto con smoke Codex PASS e smoke Claude differito per quota; recupero Claude obbligatorio appena possibile, senza attribuirgli PASS | **✅ RATIFICATA 2026-07-24** |

## 10. Definition of Done A0

- [x] SPEC aperta con stato, scope, AC, rollback e decisioni esplicite.
- [x] Riga presente in `docs/INDEX.md`.
- [x] Append presente nel log unico `docs/learning/BUILD_LOG.md`.
- [x] Nessuna nuova ADR: A0 non cambia una legge di dominio o prodotto.
- [x] Nessuna modifica operativa a Claude Code o Codex.
- [x] ACX-D1..D6 ratificate dal founder il 2026-07-19.

**Prossimo gate della migrazione:** A2, **non autorizzato** e separato dalla coda prodotto (alla
chiusura A0 era v1.0.14; oggi è R0 → P → candidate v1.0.15 → G-MAC). La chiusura di A1 riporta il
lavoro alla coda prodotto ratificata.

## 11. Definition of Done A1

- [x] Runbook agent-neutral creato e indicizzato.
- [x] `AGENTS.md` e `CLAUDE.md` puntano al nucleo comune senza rimozioni.
- [x] Nessun `CODEX.md` e nessuna `.codex/` introdotti.
- [x] Prompt Contract Smoke bounded e ripetibile depositato nel runbook.
- [x] Sessione nuova Claude Code read-only: PASS.
- [x] Sessione nuova Codex read-only: PASS.
- [x] Cinque campi semanticamente equivalenti.
- [x] Cross-doc review e diff hygiene verdi.
- [x] Finding residui dichiarati, non corretti fuori scope.

**Condizione per nuovo codice congiunto Claude/Codex: SODDISFATTA.** Alla chiusura A1 la coda allora
vigente tornava autorevole; questa è una fotografia storica del 2026-07-19, superata dall'interlock
R0 ratificato il 2026-07-24. A2-A6 restano chiusi e richiedono un GO separato dalla coda prodotto
corrente R0 → P → candidate v1.0.15 → G-MAC.

## 12. Definition of Done A1.1

- [x] Contraddizione commit/push eliminata da nucleo, runbook e adapter.
- [x] Gate, microstep, HOLD e state machine definiti in modo falsificabile.
- [x] Invariante tracked-clean + remoto `0 0` prima del gate successivo.
- [x] Tassonomia finding in-scope / release-critical fuori scope / informativo.
- [x] Sezione lifecycle resa univoca come §11 e riferimento guard riallineato.
- [x] Contract Smoke Codex con campo `DELIVERY_CHECKPOINT`: PASS dopo remediation del drift coda.
- [ ] Contract Smoke Claude: differito su waiver founder ACX-D8; recupero obbligatorio appena
  possibile e prima di qualunque gate A2+.
- [x] Cross-doc review, lifecycle/link/diff hygiene e Ruff completati.
- [x] Commit e push docs autorizzati nel checkpoint di chiusura A1.1.

**Prossimo gate prodotto:** remediation TLS R0.1.5, apribile soltanto dopo il checkpoint pubblicato di
A1.1. A2-A6 restano non autorizzati e comunque bloccati fino al recupero dello smoke Claude.
