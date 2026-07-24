# Runbook — Sviluppo assistito con Claude Code e Codex

**Stato:** ATTIVO — validato dal gate A1 (Contract Smoke Claude/Codex PASS, 2026-07-19)
**Data:** 2026-07-19
**Ambito:** procedura operativa agent-neutral per analisi, documentazione, implementazione e verifica
**Autorità:** deriva da `AGENTS.md`; non lo sostituisce e non può contraddirlo
**Non-scope:** configurazione runtime, scelta modello, policy di prodotto, leggi di dominio

---

## 1. Contratto in una frase

Claude Code e Codex possono avere bootstrap e strumenti diversi, ma devono usare **le stesse fonti,
la stessa work-queue, gli stessi invarianti e la stessa Definition of Done**.

Se questo runbook diverge da `AGENTS.md`, prevale `AGENTS.md` e il runbook deve essere corretto. Se
una decisione cambia prodotto o dominio, il runbook non può sancirla: serve ADR/Addendum e, per il
lavoro aperto, una SPEC.

## 2. Bootstrap: cosa legge ciascun agente

| Agente | Entry point | Percorso comune | Superficie specifica |
|---|---|---|---|
| Claude Code | root `CLAUDE.md` | link a `AGENTS.md` → questo runbook → fonti del task | root/layer `CLAUDE.md`, `.claude/` |
| Codex | `AGENTS.md` caricato nativamente | `AGENTS.md` → questo runbook → fonti del task | eventuale `.codex/` solo se un gate futuro ne prova la necessità |

Regole:

- non creare `CODEX.md`;
- non copiare l'intero `AGENTS.md` dentro `CLAUDE.md` o configurazioni runtime;
- non usare `.claude/` o `.codex/` come fonte di policy di prodotto/dominio;
- leggere i file `api/CLAUDE.md`, `frontend/CLAUDE.md`, `core/CLAUDE.md` solo quando il task tocca
  il relativo layer;
- non caricare `docs/archive/` come contesto di lavoro.

Codex documenta `AGENTS.md` come guidance durevole caricata automaticamente e raccomanda di
referenziare documenti specifici quando il file principale cresce:
<https://learn.chatgpt.com/docs/agent-configuration/agents-md>.

## 3. Protocollo di avvio sessione

Prima di proporre modifiche, l'agente esegue in ordine:

1. Legge `AGENTS.md` e identifica le istruzioni di layer applicabili.
2. Controlla branch, commit e working tree senza modificarli.
3. Attribuisce ogni file modificato: se restano modifiche tracked del gate precedente si ferma; file
   estranei dell'utente sono ammessi solo se identificati, preservati e mai staged.
4. Identifica la SPEC assegnata e ne legge stato, decisioni aperte, AC, esclusioni e prossimo gate.
5. Carica soltanto ADR/SSoT/runbook necessari al task; i documenti storici restano fuori contesto.
6. Produce una impact map breve:
   - obiettivo;
   - file e layer;
   - invarianti;
   - verifiche;
   - esclusioni.
7. Classifica il task secondo §4.
8. Se manca autorità per una decisione materiale, si ferma prima del codice e chiede il GO founder.

Il working tree può contenere modifiche del founder o di un altro agente: sono input da preservare,
non rumore da cancellare. Nessun reset, checkout distruttivo o sovrascrittura è implicito.

## 4. Classificazione docs-first proporzionale

| Classe | Quando si applica | Deposito richiesto prima del codice |
|---|---|---|
| D — decisione di dominio | nuova legge, invariante o policy prodotto | ADR/Addendum + SPEC aperta |
| B — comportamento/flusso | comportamento osservabile, schema, write-path, più layer o percorso critico | SPEC aperta con AC, esclusioni e rollback |
| E — esecuzione circoscritta | decisione già ratificata, fix locale, manutenzione senza nuova policy | impact map + update della SPEC esistente; nessun nuovo doc per inerzia |
| I — incidente | difetto di produzione o rischio critico emerso sul campo | incident doc e prevenzione secondo `AGENTS.md` |

La documentazione precede il codice quando deve fissare una decisione o rendere falsificabile un
cambiamento. Non è un fine autonomo: una modifica locale già governata non giustifica una nuova SPEC.

## 5. Delivery Loop condiviso

Il contratto vincolante è la state machine del Protocollo Senior in `AGENTS.md` §2:

```
ORIENTATO → AUTORIZZATO → RED* → GREEN → VERIFICATO → FOLD-BACK
           → COMMITTATO → PUSHATO → CHECKPOINT PULITO
```

Il **microstep** si verifica subito; il **gate** è la minima unità rilasciabile e costituisce il
confine di commit/push. Un HOLD blocca il gate successivo, non la pubblicazione di quello corrente
già verificato.

### 5.1 Docs gate

Prima del codice, quando richiesto dalla classificazione:

1. depositare o aggiornare ADR/SPEC;
2. esplicitare decisioni founder e stato di ratifica;
3. definire AC osservabili, non intenzioni;
4. definire non-scope e rollback;
5. allineare `docs/INDEX.md` e appendere `docs/learning/BUILD_LOG.md` quando il gate lo richiede;
6. ottenere il GO prima di implementare una decisione ancora aperta.

Un docs gate che ratifica il code gate successivo viene verificato, committato e pushato prima di
toccare il codice. La ratifica del primo non fonde i due gate.

### 5.2 Code gate

Per ogni microstep autorizzato:

1. modificare la minima unità coesa;
2. preservare gli invarianti del layer e della SPEC;
3. non introdurre refactor o astrazioni non richieste;
4. verificare immediatamente il microstep;
5. fermarsi se il risultato falsifica una decisione ratificata o allarga lo scope.

Quando pratico, il fix parte da un canary rosso. Se il RED non è applicabile, il motivo entra nel
report di verifica.

### 5.3 Verification gate

La verifica è proporzionale al rischio e segue la tabella Quality Gates di `AGENTS.md`:

- docs/process: cross-doc review, lifecycle, link e diff hygiene;
- DB/schema: migrazione e test backend pertinenti;
- cash/ledger: integrità contabile e financial-invariant-verifier;
- safety engine: QA clinica dedicata;
- backup/installer: backup → mutate → restore;
- frontend: type sync, stati loading/error/empty e gate richiesti dal layer;
- pre-release: pipeline ADR-004 completa.

Una suite verde non dimostra un path che nessun test esercita. Sui percorsi critici la verifica deve
includere il gemello/oracolo richiesto dalla SPEC e l'auditor adversariale previsto dal DoD.

### 5.4 Fold-back e handoff

Prima di dichiarare un gate concluso:

1. consuntivare stato, commit e verifiche nella SPEC;
2. aggiornare gli SSoT evergreen realmente toccati;
3. aggiornare `docs/INDEX.md`;
4. appendere `docs/learning/BUILD_LOG.md`;
5. archiviare la SPEC nello stesso gate se il blocco è interamente chiuso;
6. riportare cambiamenti, evidenze, rischi residui e prossimo passo minimo.

Prima di agire su un finding, classificarlo: un blocker in scope resta nel gate; un rischio
release-critical fuori scope apre HOLD/nuovo gate; un finding informativo entra nel backlog. Gli
ultimi due non allargano il diff corrente.

### 5.5 Checkpoint Git obbligatorio

Nel workflow normale su `FitManager_Studio`, il GO founder che apre il gate autorizza anche commit e
push alla sua chiusura. Non si chiede una seconda autorizzazione, salvo cambio di scope, branch,
remoto, policy o azione esterna diversa dal push previsto.

Il checkpoint richiede, in ordine:

1. `git diff --check`, stato e lista esatta dei file attribuiti al gate;
2. stage di path espliciti e review di diff/stat staged; mai `git add .` con file estranei;
3. commit atomico che lascia il branch rilasciabile per lo scope;
4. push immediato su `origin/FitManager_Studio`;
5. verifica che il delta `origin/FitManager_Studio...FitManager_Studio` sia `0 0` e che non restino
   modifiche tracked del gate;
6. handoff con hash, test, rischi/HOLD, stato Git e prossimo gate minimo.

Se il consuntivo deve citare l'hash dell'implementazione, sono ammessi due commit nello stesso gate:
implementazione verificata, poi fold-back con hash esatto; si pushano insieme e non si apre altro
lavoro tra i due. Un docs-only non crea un commit vuoto per auto-citare il proprio hash.

## 6. Routing minimo del contesto

| Domanda | Prima fonte da leggere |
|---|---|
| Quali regole operative valgono? | `AGENTS.md` |
| Qual è la missione o il limite di lancio? | `MANIFESTO.md`, `LAUNCH_SCOPE.md` |
| Cosa è aperto adesso? | stato in `docs/specs/` + `docs/INDEX.md` |
| Qual è la legge di dominio? | ADR indicizzata in `docs/adr/README.md` |
| Com'è fatto oggi il sistema? | SSoT pertinente in `docs/technical/` + codice/test |
| Come si esegue una procedura? | runbook pertinente in `docs/operations/` |
| Cosa è successo cronologicamente? | `docs/learning/BUILD_LOG.md`, senza promuoverlo a legge |
| Perché una vecchia scelta era stata proposta? | `docs/archive/`, solo su richiesta storica esplicita |

La posizione è lo stato. Il codice e i test sono il ground truth dell'implementazione; ADR e policy
ratificate governano ciò che il codice **deve** fare. Se divergono, l'agente segnala il conflitto:
non riscrive la policy per adattarla silenziosamente al codice.

## 7. Contract Smoke Claude Code/Codex

### 7.1 Quando eseguirlo

Obbligatorio:

- alla chiusura A1;
- prima e dopo ogni gate che riduce o sposta contenuto da un bootstrap;
- dopo una modifica alla precedenza delle fonti, al lifecycle docs o ai quality gate;
- dopo una modifica al Protocollo Senior o al checkpoint Git;
- quando Claude Code e Codex producono indicazioni operative divergenti.

### 7.2 Prompt canonico

Eseguire dalla root del repository, in una sessione nuova e read-only, lo stesso prompt:

```text
CONTRACT SMOKE — READ ONLY. Non modificare file, configurazioni o stato Git e non creare piani.
Scope dichiarato: <SCOPE_DICHIARATO>.

Limita le letture a: AGENTS.md, prime istruzioni del root CLAUDE.md,
docs/specs/SPEC_COLLABORAZIONE_CLAUDE_CODEX.md,
docs/operations/AI_ASSISTED_DEVELOPMENT_WORKFLOW.md e sezione specs di docs/INDEX.md.
Non eseguire ricerche workspace-wide e non leggere docs/archive/.

Leggi le istruzioni effettive del repository e restituisci ESATTAMENTE questi campi, con puntatori
file/sezione:
AUTHORITY_ORDER: ordine delle fonti autorevoli
DEVELOPMENT_BRANCH: branch normale di sviluppo e regola sui feature branch
DELIVERY_CHECKPOINT: confine tra microstep e gate, autorizzazione commit/push e condizione per aprire il gate successivo
ACTIVE_QUEUE: gate meta corrente e sequenza prodotto, distinguendoli
QUALITY_GATE_DOCS_PROCESS: verifiche richieste per questo scope e cosa non serve eseguire
DOCUMENT_LIFECYCLE: casa/stato di ADR, SPEC, SSoT evergreen, AUDIT/ROADMAP, BUILD_LOG e archive
SOURCE_POINTERS: fonti usate; separa vincolanti, operative e storiche
VERDICT: PASS oppure FAIL seguito da una motivazione di una riga

Non inventare policy. Non trattare docs/archive come contesto di lavoro. Se due fonti divergono,
applica la precedenza e restituisci FAIL descrivendo la divergenza.
```

Per la chiusura A1, `<SCOPE_DICHIARATO>` è stato istanziato come
`docs/process, gate A1 della SPEC_COLLABORAZIONE_CLAUDE_CODEX`. Nei run successivi si sostituisce
solo il placeholder con il gate realmente in verifica: lo stato non va hardcodato nel prompt.

### 7.3 Invocazioni di riferimento

Windows, dalla root del repository:

```powershell
# Se la execution policy blocca claude.ps1, invocare il wrapper claude.cmd.
claude.cmd -p --permission-mode plan --tools "Read,Glob,Grep" --no-session-persistence "<PROMPT_CANONICO>"

codex exec --ephemeral --sandbox read-only "<PROMPT_CANONICO>"
```

I comandi sono esempi operativi, non configurazioni da persistere. Non usare bypass dei permessi.

### 7.4 Oracolo semantico

Il confronto non richiede testo identico, ma questi fatti devono coincidere:

| Campo | Oracolo minimo |
|---|---|
| `AUTHORITY_ORDER` | runtime → `AGENTS.md` → `MANIFESTO.md` → `LAUNCH_SCOPE.md` → layer `CLAUDE.md` applicabili → `POSTMORTEMS.md` → altre docs necessarie |
| `DEVELOPMENT_BRANCH` | `FitManager_Studio`; niente feature branch senza coordinamento esplicito |
| `DELIVERY_CHECKPOINT` | microstep verificato subito; gate come unità di commit/push; il GO iniziale autorizza il checkpoint; nessun gate successivo prima di push, delta remoto `0 0` e zero modifiche tracked del gate precedente |
| `ACTIVE_QUEUE` | stesso stato meta e stessa sequenza prodotto letti dalle fonti vive, esplicitamente distinti; nessun gate futuro è aperto per inferenza |
| `QUALITY_GATE_DOCS_PROCESS` | cross-doc review + lifecycle/link/diff hygiene + Contract Smoke; nessun test applicativo se non cambia codice |
| `DOCUMENT_LIFECYCLE` | ADR legge/addendum; SPEC aperta→consuntivo→archive; technical evergreen; audit/roadmap fotografia→fold→archive; BUILD_LOG unico append-only; archive non contesto di lavoro |

**PASS:** tutti e sei i campi sono semanticamente equivalenti, le fonti sono puntate e nessun
agente inventa una policy.

**FAIL:** diverge anche un solo fatto vincolante. Correggere fonte o link, aprire due sessioni nuove e
ripetere entrambi gli smoke. Non aggiungere una seconda regola per mascherare il drift.

## 8. Stop conditions

L'agente si ferma e chiede direzione quando:

- manca una decisione founder che cambierebbe sostanzialmente il risultato;
- la richiesta allargherebbe la coda prodotto o le autorizzazioni;
- working tree e scope si sovrappongono a modifiche non attribuibili con sicurezza;
- il gate precedente non è pushato o lascia modifiche tracked attribuibili;
- una verifica critica non è eseguibile o non ha oracolo;
- emerge drift tra bootstrap, `AGENTS.md`, ADR/SPEC e codice;
- servirebbe indebolire privacy, multi-tenant safety, auditabilità o determinismo.

Un blocco operativo va riportato con evidenze e prossimo passo minimo; non autorizza workaround
silenziosi.

## 9. Manutenzione del runbook

- Cambi di processo: aggiornare prima la SPEC di collaborazione; ADR solo se cambia una legge di
  prodotto/dominio.
- Cambi al checkpoint Git: aggiornare `AGENTS.md`, questo runbook e gli adapter nello stesso gate,
  poi eseguire il Contract Smoke Claude/Codex.
- Cambi additivi ai link: Contract Smoke dopo la modifica.
- Rimozioni/spostamenti dai bootstrap: gate dedicato con smoke pre/post e rollback atomico.
- Il runbook resta agent-neutral: esempi specifici di CLI stanno solo nelle sezioni di invocazione.
- Versioni client e risultati delle esecuzioni appartengono al consuntivo SPEC/BUILD_LOG, non a questo
  documento evergreen operativo.
