# SPEC_RETRODATAZIONE_SCADENZA_E_AUDIT_LIFECYCLE

**Tipo:** specifica prescrittiva (backend-only, audit/observability).
**Data:** 2026-06-27.
**Stato:** ✅ **IMPLEMENTATA** (2026-06-27) e archiviata come design-record.
**Origine:** debt emerso durante l'audit G7.7-R5 sul flusso contratti: la retrodatazione di `data_scadenza` puo' cambiare il lifecycle effettivo di un contratto senza lasciare una traccia semantica dedicata nel log di audit.
**SSoT di dominio:** `FINANCIAL_DOMAIN_MODEL.md` §2/§4/§6 · `IMPL_PLAN_FINANCIAL_REALIGN.md` §2 Blocco 3 (`ESTENDI = PUT /contracts/{id}`) · `contract_state.py` · `api/routers/contracts.py:update_contract`.
**Spec sorella di superficie:** la spec frontend del follow-up G7.7-R5 ha presidiato il lato trainer/UI; questo design-record copre il lato backend/audit.
**Verifica finale:** `pytest tests/test_contract_expiry_lifecycle_audit.py -v` (6/6 verdi) + `pytest tests/test_suspended_contracts.py -v` (11/11 verdi) + `ruff check api/` verde.

> Questa spec NON introduce un nuovo endpoint `suspend` o `unsuspend`. Il modello resta invariato: il lifecycle continua a essere DERIVATO da tempo + crediti + `chiuso`. Qui si rende esplicita l'auditabilita' della transizione quando il trigger e' una modifica di `data_scadenza`.

---

## 0. Tesi unica (falsificabile)

> **T1 — una modifica di `data_scadenza` che sposta un contratto aperto attraverso il confine temporale del SSoT deve produrre una traccia di audit lifecycle dedicata, non solo un diff generico di campo.**

Tradotto:
- se il contratto passa da **vigente** a **scaduto** per effetto dell'update, il sistema deve loggare la transizione di lifecycle;
- se il contratto passa da **scaduto** a **vigente** per effetto dell'update, il sistema deve loggare la transizione opposta;
- se il lifecycle NON cambia, il diff generico di `data_scadenza` resta sufficiente e non si emette un evento lifecycle dedicato.

La tesi e' falsificata se accade anche uno solo di questi casi:
- un contratto ATTIVO viene retrodatato nel passato e diventa `SOSPESO` o `ESAURITO`, ma l'audit contiene solo il diff di `data_scadenza`;
- un contratto `SOSPESO` o `ESAURITO` torna `ATTIVO` tramite estensione della scadenza, ma l'audit non registra la riattivazione di lifecycle;
- la soluzione introduce un nuovo endpoint o una nuova semantica di dominio invece di presidiare l'endpoint esistente.

---

## 1. Problema osservato (code-grounded)

### 1.1 — `update_contract` oggi valida il dato, ma non la semantica lifecycle

L'endpoint `update_contract`:
- carica il contratto;
- valida solo ordine date e rate orfane;
- applica il diff campo-per-campo;
- registra un audit generico `UPDATE` con `changes`;
- committa.

Questo e' corretto per un update CRUD generico, ma NON e' sufficiente quando il campo modificato e' `data_scadenza`, perche' quel campo cambia il lifecycle reale del contratto.

### 1.2 — Il SSoT temporale e' netto, ma oggi non viene audito come transizione

Il modello di dominio e' gia' chiaro:
- `is_scaduto = data_scadenza < today`
- `is_vigente = data_scadenza is null or data_scadenza >= today`

Quindi:
- `data_scadenza == oggi` NON rende il contratto scaduto;
- `data_scadenza < oggi` rende il contratto immediatamente scaduto;
- il lifecycle risultante fra `SOSPESO` e `ESAURITO` dipende dai crediti residui, non da una scelta manuale separata.

La lacuna non e' nel modello. La lacuna e' che il passaggio di lifecycle causato da quella data oggi non ha una traccia audit dedicata.

### 1.3 — Il debt e' separato dal fix frontend

La spec frontend gemella presidia il trainer prima del submit (warning, conferma, chiarezza su `oggi` vs `passato`).
Questa spec presidia il sistema DOPO il submit: anche se il trainer conferma consapevolmente, il backend deve lasciare una traccia semanticamente leggibile del fatto che l'update ha cambiato il lifecycle.

---

## 2. Decisioni vincolanti backend

### 2.1 — Nessun nuovo endpoint: si resta su `PUT /contracts/{id}`

Decisione:
- la retrodatazione/estensione della scadenza continua a passare da `update_contract`;
- non si introduce un endpoint `suspend`, `expire`, `reactivate` o equivalente in questa iterazione.

Razionale:
- il modello attuale e' derivato, non command-based;
- il debito emerso e' di auditabilita', non di mancanza di API;
- il Blocco 3 documenta gia' `ESTENDI = PUT /contracts/{id}` come riuso puro: questa spec lo rafforza, non lo ribalta.

### 2.2 — L'audit generico resta, ma non basta piu' da solo

Decisione:
- l'audit generico del diff (`data_scadenza old -> new`) resta invariato;
- quando il lifecycle effettivo cambia, si aggiunge una seconda entry di audit dedicata alla transizione lifecycle.

Razionale:
- il diff generico serve per sapere *quale campo* e' cambiato;
- la transizione dedicata serve per sapere *che cosa ha significato* quel cambiamento sul contratto.

### 2.3 — Niente overload del helper G7: helper fratello dedicato

Decisione:
- NON si sovraccarica `log_contract_lifecycle_transition()` per questo caso;
- si introduce un helper fratello dedicato alle transizioni di lifecycle derivate da `data_scadenza`.

Razionale:
- il helper esistente e' semanticamente centrato sulle transizioni del flag `chiuso` e sui flussi G6/G7 (`motivo`, `rimborso`, `residuo_annullato`, `data_chiusura`);
- usare lo stesso helper per ATTIVO/SOSPESO/ESAURITO mischierebbe due famiglie di eventi diverse;
- separare i due helper mantiene leggibile il contratto tecnico dell'audit.

### 2.4 — Il sistema audita i lifecycle reali, non la parola "sospensione"

Decisione:
- l'audit non deve usare una semantica ambigua tipo "sospensione manuale" come fatto di sistema;
- l'audit deve registrare i lifecycle effettivi (`attivo`, `sospeso`, `esaurito`) e il trigger dell'update su `data_scadenza`.

Conseguenza:
- se la retrodatazione porta a `SOSPESO`, il log lo dice esplicitamente;
- se porta a `ESAURITO`, il log lo dice esplicitamente;
- il trigger puo' essere etichettato come `scadenza_retrodatata` o `scadenza_estesa`, ma il nuovo lifecycle deve essere registrato come valore esplicito.

---

## 3. Inventario dei siti

### 3.1 — Siti da CAMBIARE

| File | Ruolo | Cosa deve cambiare |
|------|------|--------------------|
| `api/routers/contracts.py` | `update_contract` | calcola old/new lifecycle attorno alla modifica di `data_scadenza` e, se c'e' crossing reale, emette audit lifecycle dedicato |
| `api/routers/_audit.py` | helper audit | aggiunge un helper fratello dedicato alle transizioni di lifecycle derivate da update su scadenza |
| `tests/` | copertura regressione | aggiunge test dedicati per retrodatazione, estensione e no-op lifecycle |

### 3.2 — Siti da LASCIARE invariati

| File | Perche' resta |
|------|---------------|
| `api/services/contract_state.py` | il modello temporale e lifecycle e' gia' il SSoT corretto; non va cambiato |
| `api/schemas/financial.py` | nessun cambio di contratto API richiesto |
| `frontend/` | la UI e' coperta dalla spec sorella, non da questa |

---

## 4. Regole di implementazione

### 4.1 — La transizione va derivata col SSoT, non con condizioni inline

L'old/new lifecycle deve essere derivato con `contract_state.contract_lifecycle(...)`, non con `if data_scadenza < today` scritto a mano dentro `update_contract`.

Vincolo:
- si puo' usare `data_scadenza` come trigger per decidere SE controllare il lifecycle;
- NON si puo' usare `data_scadenza` da sola per decidere QUALE lifecycle auditare.

Razionale:
- la scelta fra `SOSPESO` e `ESAURITO` dipende anche dai crediti residui;
- ricreare inline la logica aprirebbe subito drift dal SSoT.

### 4.2 — L'audit dedicato scatta solo se il lifecycle cambia davvero

Se `data_scadenza` cambia ma il lifecycle effettivo resta identico, NON si emette un evento lifecycle dedicato.

Esempi:
- futura -> futura, resta `ATTIVO` -> niente entry lifecycle;
- passata -> altra passata, resta `SOSPESO` o `ESAURITO` -> niente entry lifecycle;
- chiuso -> chiuso, cambia solo la data storica -> niente entry lifecycle.

Il diff generico di campo resta sufficiente in questi casi.

### 4.3 — Il nuovo audit deve dire trigger + old/new lifecycle

L'entry dedicata deve contenere almeno:
- `lifecycle.old`
- `lifecycle.new`
- `trigger = data_scadenza_update`
- `motivo = scadenza_retrodatata` oppure `motivo = scadenza_estesa`

Nota:
- `motivo` qui NON e' `motivo_chiusura` del dominio G7;
- e' un motivo audit tecnico della transizione lifecycle.

### 4.4 — La retrodatazione non deve creare una nuova "via a CHIUSO"

Questa spec NON riapre la vecchia semantica di `chiuso` via update.

Vincoli:
- `update_contract` continua a NON poter chiudere manualmente il contratto;
- l'hardening audit riguarda solo transizioni fra `ATTIVO`, `SOSPESO`, `ESAURITO` su contratti aperti;
- `CHIUSO` continua a essere presidio dei flussi gia' esistenti (`pay_rate`, `_sync_contract_chiuso`, `terminate`, `reopen`).

### 4.5 — L'estensione in avanti diventa riattivazione esplicita nel log

Il path `ESTENDI` del Blocco 3 resta `PUT /contracts/{id}`.
La differenza e' che se l'estensione riporta il contratto da scaduto a vigente, il log deve contenere una entry di riattivazione lifecycle, non solo il diff di data.

---

## 5. Acceptance criteria

### AC-1 — Retrodatazione verso `SOSPESO`

Dato un contratto aperto e vigente con crediti residui, impostando `data_scadenza` nel passato:
- il lifecycle passa da `attivo` a `sospeso`;
- l'audit contiene il diff generico di `data_scadenza`;
- l'audit contiene una entry dedicata con `lifecycle old=attivo, new=sospeso`, trigger `data_scadenza_update`, motivo `scadenza_retrodatata`.

### AC-2 — Retrodatazione verso `ESAURITO`

Dato un contratto aperto e vigente senza crediti residui, impostando `data_scadenza` nel passato:
- il lifecycle passa da `attivo` a `esaurito`;
- l'audit contiene la transizione dedicata corrispondente.

### AC-3 — Estensione verso `ATTIVO`

Dato un contratto aperto e scaduto (`sospeso` o `esaurito`), spostando `data_scadenza` nel futuro:
- il lifecycle passa a `attivo`;
- l'audit contiene una entry dedicata con trigger `data_scadenza_update`, motivo `scadenza_estesa`.

### AC-4 — Nessun falso positivo

Se `data_scadenza` cambia ma il lifecycle resta invariato, NON si crea una entry lifecycle dedicata.

### AC-5 — Nessun cambio API o modello

L'endpoint resta `PUT /contracts/{id}`. Nessun nuovo endpoint. Nessuna modifica al calcolo SSoT di lifecycle.

### AC-6 — Nessun conflitto con l'audit G6/G7

Le transizioni di `chiuso` continuano a usare `log_contract_lifecycle_transition()` senza regressioni; il nuovo helper copre solo il lifecycle derivato da update su `data_scadenza`.

---

## 6. Piano di verifica

### 6.1 — Test mirati

1. `ATTIVO -> SOSPESO` per retrodatazione
2. `ATTIVO -> ESAURITO` per retrodatazione
3. `SOSPESO -> ATTIVO` per estensione
4. `ESAURITO -> ATTIVO` per estensione
5. `ATTIVO -> ATTIVO` (futuro -> altro futuro) senza entry lifecycle
6. `SOSPESO -> SOSPESO` (passato -> altro passato) senza entry lifecycle

### 6.2 — Gate

- `pytest tests/test_contract_expiry_lifecycle_audit.py -v`
- `pytest tests/test_suspended_contracts.py -v`
- `ruff check api/`

---

## 7. Confini espliciti

### 7.1 — Cosa NON toccare

- nessun endpoint nuovo `suspend` / `reactivate`;
- nessuna modifica al SSoT `is_scaduto = data_scadenza < today`;
- nessun cambio alla semantica di `ESTENDI` come riuso di `update_contract`;
- nessuna modifica frontend in questa spec;
- nessun cambio ai flussi G7 di `chiuso` / `motivo_chiusura`.

### 7.2 — Rischio principale

Il rischio tecnico e' introdurre una terza variante di logica lifecycle dentro `update_contract` invece di derivare col SSoT.

Mitigazione:
- trigger su `data_scadenza`, ma decisione old/new lifecycle via `contract_state`;
- helper audit separato da quello di `chiuso`;
- test espliciti sui quattro crossing reali.

---

## 8. Condizione di archiviazione

Questa spec esce da `docs/technical/` quando sono veri tutti i punti:
- `update_contract` emette audit lifecycle dedicato sui crossing reali indotti da `data_scadenza`;
- i test dei quattro crossing e dei due no-op sono verdi;
- `pytest tests/ -v` e `ruff check api/` sono stati eseguiti e registrati nel `BUILD_LOG.md`.

Una volta chiusa, la spec va archiviata in `docs/archive/specs/` come design-record del hardening audit backend del path `update_contract`.