# SPEC_G9_FINANCIAL_COMMAND_LAYER

**Tipo:** specifica prescrittiva (cosa-deve-essere-vero; silente sul come dove possibile). Bridge Chat→Code.
**Data:** 2026-06-30 · **Branch:** `FitManager_Studio`
**Stato:** ⏳ **DA IMPLEMENTARE** (G9.0→G9.6). Governance docs-only. Zero codice prodotto. **G9.0 design di
dettaglio pronto-da-implementare → Appendice A** (sensore totale-per-costruzione [niente `except Exception`,
A.1-bis] + agganci + reconciliation bidirezionale + quick-win + Reperto #1 log-only).
**Blocco proposto:** **G9** — elevazione del write-model del dominio contrattuale-economico. Ratifica
`ADR-022`. Sette gate sequenziali, branch sempre rilasciabile.
**Mappa di verità:** `docs/adr/ADR-022-financial-command-layer-ledger-load-bearing.md` ·
`docs/technical/FINANCIAL_DOMAIN_MODEL.md` · `docs/technical/TASSONOMIA_FINANZIARIA.md` ·
`api/services/contract_state.py` · `api/services/contract_settlement.py` · `api/services/cash_categories.py` ·
`api/routers/contracts.py` · `api/routers/rates.py` · `tests/test_financial_invariants_harness.py`

> **Nota sulle coordinate.** I riferimenti `file:riga` sono lo snapshot 2026-06-30 (post-G8.3); gli **esiti
> sono durevoli, le righe vanno riverificate** a implementazione (come da prassi `AUDIT_PRE_G7.3`). Ogni gate
> è behavior-preserving fino a **G9.4** (primo gate che cambia comportamento osservabile, e solo dietro
> feature-flag).

---

## Impact map

- **Obiettivo:** rendere il **ledger `CashMovement` load-bearing** (fonte di verità della cassa) e dotare il
  SSoT di lettura (`contract_state.py`) del suo **gemello di scrittura** — penna unica di posting +
  transition executor + invarianti imposti — così che gli scenari secondari si **assorbano per costruzione**
  invece di richiedere una toppa + un ADR ciascuno.
- **Layer toccati:** backend (nuovo package `api/services/financial/`: `ledger.py`, `transitions.py`,
  `invariant_gate.py`; `contract_state.py`/`contract_settlement.py` **collaboratori intatti**; router
  `contracts.py`/`rates.py` **assottigliati**; `dashboard.py` reconciliation bidirezionale; `check-all.sh`
  grep→test semantici; `api/types/money.py` a G9.6). Frontend: **invariato** (HTTP identico fino a G9.4; a
  G9.4 solo nuovi 409 dietro flag).
- **Invarianti da preservare (asse DENARO e dominio):** `residuo()` net-aware, Strada B, `residuo == 0 ⟺
  saldato`, cassa-immutabile/integrità di periodo (ADR-019), asse EROGATO (ADR-016), `Rinviato` fuori
  occupazione (ADR-017), bilateralità (ADR-018), INV-RATE (ADR-021), wallet/receivable fuori da `residuo()`
  (ADR-020). **G9 non cambia cosa il sistema calcola — cambia chi e come lo scrive.**

**Tesi falsificabile (fine G9):** (1) **nessun endpoint scrive `contract.totale_versato +=` o
`totale_rimborsato +=` a mano** — l'unico scrittore è la penna (`post_inflow`/`post_outflow`); (2)
`project_columns_from_ledger(id)` riproduce `totale_versato`/`totale_rimborsato` **al centesimo** da
`Σ` postings su **ogni** contratto reale; (3) `assert_contract_invariants` gira a runtime su **tutte** le
transizioni denaro (non solo reopen); (4) i **4 grep-guard** di `check-all.sh` sono stati sostituiti da
test semantici sul simbolo; (5) un `Hypothesis RuleBasedStateMachine` esplora migliaia di sequenze
stato×transizione senza violare un invariante; (6) la `/reconciliation` su un DB sano riporta **0
divergenti** by-construction (non più audit load-bearing).

---

## 0. Problema reale da correggere (sintesi audit)

1. **Ledger consultivo, non load-bearing.** Le colonne `totale_versato`/`totale_rimborsato`/`quota_stornata`
   sono una seconda verità sincronizzata a mano in ~7 siti (`contracts.py:1663/1724/1751/2038`, `rates.py`
   pay/unpay, `incassa-residuo`). `quota_stornata` (`:1751`) **entra nel `residuo()` ma non ha posting**; il
   fold R2-bis del reopen (`:2038`) è una rettifica **senza movimento**.
2. **Coreografia nei router.** terminate ~256 righe (`:1573-1828`), reopen ~182 (`:1916-2098`); auto-close
   duplicato (`rates.py` inline vs `agenda.py:301`).
3. **Invarianti osservati, non imposti.** `assert_contract_invariants` cablato solo su reopen (`:2094`,
   log-only); 4 grep-guard testuali (`check-all.sh:40-84`); `/reconciliation` post-facto e monca
   (`dashboard.py:193-201`, solo lato versato).
4. **Denaro in float.** ~150 dead-zone/`round`, contraddizione `is_saldato` (≤0.01) vs `money_substate`
   (≤0.009).

## 1. Ciò che NON cambia

- I **moduli puri** `contract_state.py` e `contract_settlement.py` restano il cuore e **non cambiano firma**
  (diventano i collaboratori del layer). `residuo()` net-aware, `compute_settlement`, gli enum.
- Tutte le **decisioni di dominio** ADR-016→021 (asse EROGATO, rinvio-libera-credito, bilateralità,
  cassa-immutabile, residuo net-aware, wallet/receivable fuori da residuo, INV-RATE).
- Le **ancore** `totale_versato == Σ ENTRATA` / `totale_rimborsato == Σ USCITA RIMBORSO + Σ wallet
  riassorbito` (I5): reggono **meglio** (diventano vere per costruzione).
- Il **frontend** (HTTP identico fino a G9.4; a G9.4 solo nuovi 409 dietro flag, su violazioni che oggi sono
  già bug).

## 2. Il principio (ADR-022)

Il SSoT di **lettura** (`contract_state.py`) ha bisogno del suo gemello di **scrittura**, in due metà:
**(A) penna unica** — l'unico punto che muta le colonne cassa; **(B) transition executor** — l'unico punto
che applica una transizione e ne asserisce gli invarianti. Con questi, il **ledger è load-bearing**: le
colonne sono proiezioni verificate, non verità parallele. *Strumenta-poi-imponi; evolvi, non riscrivere.*

---

## G9.0 — Sensore invarianti ovunque (log-only) + riconciliazione bidirezionale

**Mossa a leva più alta / rischio più basso. Zero cambio di comportamento.** Il checker è già scritto e
corretto su I1-I6; gli manca solo di girare su più di 1 transizione.

- **G9.0-a — sensore ovunque.** Estrarre l'helper oggi locale a `contracts.py` (`_log_invariant_violations`,
  cablato a runtime solo su reopen `:2094`) in `api/services/financial/invariant_gate.py` e invocarlo,
  **ancora log-only**, in coda a **tutte** le transizioni denaro: `terminate`, `pay_rate`, `unpay_rate`,
  `incassa-residuo`, `eroga` wallet, `incassa`/`annulla` `credito_terminazione`. Emette un log strutturato
  per violazione (codice I*, transizione, `contract_id`) → **telemetria** che de-risca G9.4.
- **G9.0-b — reconciliation bidirezionale.** Completare `/reconciliation` (`dashboard.py:193-201`) col lato
  mancante `totale_rimborsato == Σ USCITA RIMBORSO[id_contratto]` (oggi controlla solo il versato).
- **G9.0-c — quick-win gratuiti (stesso gate, costo ~0):** (1) collassare le **due formule `residuo`
  duplicate** dei DTO (`financial.py:274-275` `CreditoTerminazioneResponse`, `:296-297`
  `CreditoClienteResponse`) in un helper puro condiviso; (2) correggere il **KPI gross-SQL** di
  `dashboard.py` (confronto `prezzo > versato` LORDO) a net-aware riusando `cstate`.

**AC-G90-1:** `assert_contract_invariants` viene invocato a runtime al termine di **ognuna** delle ~7
transizioni denaro; un test verifica la presenza della chiamata (o, meglio, che una violazione I1 iniettata
produca il log atteso) per ciascuna. **AC-G90-2:** `/reconciliation` segnala una divergenza
`totale_rimborsato` iniettata (oggi invisibile). **AC-G90-3:** le due formule `residuo` dei DTO derivano da
un unico helper (test: stesso input → stesso output, e modificare l'helper cambia entrambi). **AC-G90-4:**
comportamento HTTP **invariato** (nessun 409 nuovo); suite verde; ruff + next build verdi.

**Rischio:** basso. **Sforzo:** basso. **Behavior-preserving:** sì.

---

## G9.1 — Penna unica di posting (ledger load-bearing)

`api/services/financial/ledger.py`:

```text
post_inflow(session, *, contract, importo, categoria, metodo, data_effettiva, id_rata=None, note) -> CashMovement
post_outflow(session, *, contract, importo, categoria, metodo, data_effettiva, note) -> CashMovement
```

Ogni funzione, in **una** unità: (1) crea il `CashMovement` (tipo ENTRATA/USCITA, `trainer_id`,
`id_contratto`, ecc.); (2) applica il **delta-colonna** mappato via `cash_categories.signed_contractual_amount`
(`:53-62`) — `totale_versato += importo` per gli inflow contrattuali, `totale_rimborsato += importo` per
`RIMBORSO_CONTRATTO`; (3) richiama `cstate.recompute_stato_pagamento(contract)`. **Nessun endpoint scrive più
la colonna a mano.**

Adozione **endpoint-per-endpoint** (strangler-fig, branch sempre rilasciabile): **`pay_rate`** per primo (il
più semplice), poi **`incassa-residuo`**, poi i rami di **`terminate`** (rimborso USCITA, incasso conguaglio
ENTRATA) e l'erogazione **wallet** (`clients.py` eroga; nota: `id_contratto=None` per non toccare l'àncora di
contratto — la penna rispetta il parametro). A ogni passo i 718 test e i grep-guard restano verdi.

**AC-G91-1:** dopo la migrazione di un endpoint, `grep` di `totale_versato +=`/`totale_rimborsato +=` in quel
file → **0** occorrenze fuori da `ledger.py`. **AC-G91-2:** per ogni endpoint migrato, un test verifica che
`post_inflow/out` abbia creato il movimento **e** aggiornato la colonna **e** ricalcolato `stato_pagamento`
in un solo commit atomico (tutto-o-niente). **AC-G91-3:** `I5` (`totale_versato == Σ ENTRATA`) verificato
vero **per costruzione** sui path migrati (la telemetria G9.0 non logga più violazioni I5 su quei path).
**AC-G91-4:** HTTP invariato; i ~15 consumer di lettura **non toccati**.

**Rischio:** basso. **Sforzo:** medio. **Behavior-preserving:** sì.

---

## G9.2 — Dare casa nel ledger alle grandezze non-cash + `project_columns_from_ledger`

- **✅ G9.2-a (FATTO, `97b4463`) — `project_columns_from_ledger(session, contract_id) -> {versato, rimborsato}`**
  (inverso per-contratto di `/reconciliation`) + ancora **ledger-versato** nel sensore (`totale_versato == Σ
  ENTRATA`; il lato rimborso era già I5). Log-only.
- **G9.2-b — storno in un ledger SEPARATO `rettifiche_contratto` (decisione founder: Opzione A, ADR-022 Addendum I).**
  ⚠️ Revisione del piano originale: mettere lo storno nel **mastro cassa** riapriva la superficie scartata da
  ADR-019 (categoria-storno da escludere ovunque). Lo storno è **non-cash** → ledger dedicato. **`quota_stornata
  = Σ importo[rettifiche_contratto]`** (importo firmato: + storno, − reversal, append-only). Terza penna
  `post_adjustment` (rettifica + colonna in un atto, gemello non-cash di post_inflow/out, NON tocca
  `movimenti_cassa`). `terminate`→+storno, `incassa_credito`→−importo (Reperto #1), `reopen`→−quota (a 0).
  **`residuo()` BYTE-IDENTICO** (legge `quota_stornata`, ora proiezione verificabile di `Σ rettifiche`, come
  `versato` lo è di `Σ ENTRATA`). Backfill idempotente del `quota_stornata` legacy (boot, `BACKFILL_LEGACY`).
- **✅ G9.2-c (di fatto GIÀ FATTO da G9.1) — wallet/receivable sono GIÀ postings.** `crediti_cliente` (erogazione
  = USCITA RIMBORSO) e `crediti_terminazione` (incasso = ENTRATA INCASSO_CONGUAGLIO) producono già `CashMovement`
  via la penna; `project_columns_from_ledger` conta già l'erogato wallet riassorbito. Nessun lavoro residuo.

**AC-G92-1:** `project_columns_from_ledger` riproduce `totale_versato`/`totale_rimborsato` al centesimo su
ogni contratto del DB di test (e, in validazione, sul clone backup reale). **AC-G92-2:** `quota_stornata ==
Σ postings di storno` per ogni contratto; `residuo()` resta byte-identico al pre-G9.2 (lo storno-posting
**non cambia** il valore, **cambia** la sua derivazione). **AC-G92-3:** il fold R2-bis del reopen produce un
posting esplicito; la telemetria I5 resta pulita; `residuo` post-reopen invariato. **AC-G92-4:** harness
invariante×transizione verde (incl. sequenze composte terminate→incassa→reopen).

**Rischio:** medio. **Sforzo:** alto. **Behavior-preserving:** sì (valori invariati; cambia la derivazione).

---

## G9.3 — TransitionExecutor + FSM di chiusura esplicita

`api/services/financial/transitions.py`: command-handler tipati per transizione su un comando DTO + la penna
di G9.1. Spostare i corpi di **terminate** (`contracts.py:1573-1828`) e **reopen** (`:1916-2098`) in
`execute_terminate(ctx)` / `execute_reopen(ctx)` (strangler-fig, **una transizione alla volta**,
rilocazione quasi-verbatim → HTTP identico, suite verde al primo passaggio). `compute_settlement` e
`contract_state` restano collaboratori puri dove sono.

Pattern dell'executor (post-condizione obbligatoria):
```text
carica stato → decisione pura (compute_settlement / contract_state) → emette postings (penna G9.1)
→ project_columns_from_ledger == colonne scritte (G9.2-a) → assert_contract_invariants (gate, G9.4)
→ audit + lifecycle transition → commit atomico
```
Router → **~30 righe** (bouncer + parse comando + delega + serialize). **FSM esplicita** di
`chiuso`/`motivo_chiusura` (tabella stati×transizioni). **Unificare l'auto-close duplicato**: il path
payment-driven (`rates.py` inline) e credit-driven (`agenda.py:301` `_sync_contract_chiuso`, già con la
reopen-allowlist G7.2) convergono su un'unica transizione.

**AC-G93-1:** terminate/reopen vivono in `transitions.py`; i router `contracts.py` relativi sono ≤ ~40 righe
ciascuno. **AC-G93-2:** la suite 718 (+ nuovi) resta verde al primo passaggio (behavior-preserving);
risposta HTTP byte-identica su una matrice di scenari registrati. **AC-G93-3:** l'auto-close è **un solo**
percorso logico (test: payment-driven e credit-driven producono lo stesso stato terminale a parità di
condizioni). **AC-G93-4:** la post-condizione `project_columns == colonne` è asserita in ogni handler.

**Rischio:** medio. **Sforzo:** medio. **Behavior-preserving:** sì.

---

## G9.4 — Promuovere invarianti a gate (409 + rollback) + ritiro grep-guard + test semantici

- **G9.4-a — enforcement graduale.** Con la **telemetria di G9.0** e la cucitura di G9.3: promuovere
  **I1/I4** a **409 + rollback** dentro la post-condizione dell'executor (I5/I6 in **warn** finché la
  riconciliazione è provata pulita in prod), via feature-flag **`INVARIANT_ENFORCEMENT`** (`raise` in
  CI/dev/test, `log` in prod inizialmente, poi `raise` quando la telemetria è verde).
- **G9.4-b — ritiro grep-guard.** Convertire i **4 grep-guard testuali** (`check-all.sh:40-84`,
  ADR-016/017/018/019) in **test semantici sul simbolo reale**: es. `assert
  CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO in CONTRACT_CASH_IN`; un `import-linter` che vieta a
  `contract_settlement` di importare i predicati di occupazione (presidio ADR-016). I grep si rimuovono
  **solo dopo** che i test semantici sono verdi (no buco).

**AC-G94-1:** con `INVARIANT_ENFORCEMENT=raise`, una transizione che violerebbe I1/I4 ritorna **409 +
rollback** (zero scrittura) — test per ciascun invariante. **AC-G94-2:** con flag a `log`, comportamento
identico a oggi (rollback sicuro della decisione). **AC-G94-3:** i 4 grep-guard rimossi da `check-all.sh`
hanno un test semantico gemello che fallisce sullo stesso scenario (es. togliere
`INCASSO_CONGUAGLIO_CONTRATTO` da `CONTRACT_CASH_IN` rompe un test, non un grep). **AC-G94-4:** la
telemetria G9.0 mostra **0** violazioni I1/I4 in CI prima di accendere il `raise`.

**Rischio:** medio (mitigato dal flag e dalla telemetria). **Sforzo:** medio. **Behavior-preserving:** no
(introduce 409 dietro flag — su stati che oggi sono già bug silenziosi).

---

## G9.5 — Hypothesis stateful machine (property-based testing)

`RuleBasedStateMachine` (dipendenza **solo-test**, seed pinnato per determinismo CI) che riusa i builder
dell'harness (`tests/test_financial_invariants_harness.py`) come `rule()` (pay, unpay, terminate, incassa,
eroga, reopen, …) e `assert_contract_invariants` come **invariante post-mossa**. Da ~12 path manuali a
**migliaia di sequenze generate**. `@example` per i canary noti (es. `eroga_wallet → reopen` = Bug-1).

**AC-G95-1:** la macchina esplora sequenze casuali di transizioni mantenendo I1-I6 ad ogni passo; un bug
iniettato (regressione di un invariante) la fa fallire. **AC-G95-2:** seed pinnato → run deterministico in
CI. **AC-G95-3:** zero impatto runtime (test-only). **AC-G95-4:** i canary noti sono `@example` espliciti.

**Rischio:** basso. **Sforzo:** medio. **Behavior-preserving:** sì (test-only).

---

## G9.6 — (Differito, gated) Money value-type — centesimi interi

`api/types/money.py` (Decimal o interi-centesimi; **un solo** rounding mode dichiarato; non-negativo dove
dovuto), rifattorizzato **dietro** `contract_state.py` + `contract_settlement.py` lasciando le firme
`float→float` **invariate** (i ~15 consumer non cambiano una riga). Collassa le ~150 dead-zone sparse
(`±0.009`/`±0.01`) in **una costante unica** e risolve la contraddizione `is_saldato` (≤0.01) vs
`money_substate` (≤0.009). **Fase storage (ultimo miglio, separata):** colonne monetarie + `CashMovement.importo`
→ INTEGER centesimi via `schema_sync` (Alembic FROZEN sui DB deployati — vedi precedente
`schema_sync._fix_cross_db_fk`).

**Procedura sicura:** introdurre ai confini dei 2 moduli puri **side-by-side** coi float; girare un
**golden test Money-vs-float** che prova la **byte-identità** sui 12 scenari dell'harness; **solo dopo** la
verde, stringere deliberatamente `0.009 → 0.005` (mezzo centesimo, il confine corretto per EUR), preceduto da
uno **scan dei contratti reali** nella banda riclassificata.

**AC-G96-1:** golden test Money-vs-float byte-identico sui 12 scenari prima di qualunque cambio di
comportamento. **AC-G96-2:** un'unica costante epsilon (o nessuna, con interi); `is_saldato` e
`money_substate` usano lo **stesso** confine. **AC-G96-3:** la fase-storage (se eseguita) migra via
`schema_sync`, idempotente, verificata su clone backup reale; `Σ ENTRATA == totale_versato` diventa un `==`
**stretto**. **AC-G96-4:** la `/reconciliation` perde la sua ragion d'essere (divergenze impossibili per
costruzione) → declassata a rete di sicurezza periodica.

**Rischio:** basso (dietro firme invariate + oracolo). **Sforzo:** alto. **Behavior-preserving:** sì fino
allo stringimento deliberato dell'epsilon (gated, post-scan).

---

## Sequenza dei gate (vincolante)

| Gate | Goal | Dipende da | Rischio/Sforzo | Behavior |
|------|------|-----------|----------------|----------|
| **G9.0** | Sensore invarianti ovunque (log-only) + reconciliation bidirezionale + 2 quick-win | — | basso / basso | invariato |
| **G9.1** | Penna unica `post_inflow`/`post_outflow` (adozione endpoint-per-endpoint) | G9.0 (baseline telemetria) | basso / medio | invariato |
| **G9.2** | Storno/fold come postings + `project_columns_from_ledger` | G9.1 | medio / alto | invariato (valori) |
| **G9.3** | TransitionExecutor + FSM chiusura + unifica auto-close | G9.1, G9.2 | medio / medio | invariato |
| **G9.4** | Invarianti → 409+rollback (flag) + ritiro grep-guard → test semantici | G9.0, G9.3 | medio / medio | **nuovi 409 (flag)** |
| **G9.5** | Hypothesis RuleBasedStateMachine | G9.3 | basso / medio | invariato (test-only) |
| **G9.6** | *(differito)* Money value-type + fase-storage | G9.3 (gated, non blocca) | basso / alto | invariato fino a epsilon-tighten |

**Regola d'oro della sequenza:** non si costruisce l'executor (G9.3) prima della penna (G9.1); non si accende
l'enforcement (G9.4) prima della telemetria (G9.0); non si parte da Money (G9.6 ultimo). Ogni gate lascia il
branch **rilasciabile** e la suite **verde**; G9.0-G9.3 e G9.5-G9.6(calcolo) sono behavior-preserving, G9.4 è
l'unico che cambia comportamento e solo dietro flag.

## Follow-up a implementazione

A chiusura dei gate, aggiornare: `FINANCIAL_DOMAIN_MODEL.md` (ledger load-bearing; `residuo` come somma di
postings; storno-posting), `TASSONOMIA_FINANZIARIA.md` (categoria storno contra-ricavo non-cash; predicati
penna), `api/CLAUDE.md` (Contract Integrity Engine → financial command layer; penna unica come punto-di-
scrittura; invariant gate), `BUILD_LOG.md` (cronologia G9.x), e l'indice `docs/INDEX.md` / `docs/adr/README.md`.
Depositare l'audit fondante `docs/operations/AUDIT_FINANCIAL_ARCHITECTURE_2026-06-30.md`.

---

## Appendice A — G9.0: design di dettaglio (implementation-ready, 2026-06-30)

Design del solo G9.0, ancorato al codice vivo (snapshot post-G8.3). Esito di una lettura code-grounded dei
~7 punti d'aggancio. **Tutto behavior-preserving; nessun 409 nuovo.** Decisioni founder 2026-06-30: *bake nel
SPEC prima dell'implementazione* (questa appendice è il design-record); *Reperto #1 log-only, triage col dato*.

### A.0 — Scoperta che orienta il gate

`_log_invariant_violations` (`contracts.py:77-102`) **è già auto-contenuto**: prende solo `(session, contract,
motivo)` e batch-fetcha da sé `crediti_cliente` (I5), `Σ USCITA RIMBORSO` diretto (I5 ancora-ledger) e
`rate_attive` (I6). G9.0-a NON è "scrivere un sensore" — è **spostarlo di layer + ~6 chiamate da una riga**.
Ogni transizione ha già `session` + `contract` in scope e committa in fondo.

### A.1 — Nuovo modulo `api/services/financial/invariant_gate.py`

Si sposta il wrapper da `contracts.py` (router) a `services/` (è dominio, non routing). **NESSUN
`try/except`** (correzione di review 2026-06-30, vedi A.1-bis): il sensore è **totale per costruzione**, non
*fail-safe-by-catch*.

```python
# api/services/financial/invariant_gate.py
def log_invariant_violations(session, contract, *, motivo: str) -> None:
    """Sensore osservabile (log-only) degli invarianti I1/I4/I5/I6 in coda a una transizione denaro.

    NESSUN try/except: `assert_contract_invariants` è TOTALE per costruzione (pura, getattr-default →
    non solleva su un Contract ben tipato) e le 3 query sono quelle che gli endpoint già eseguono. Se
    questo solleva è un BUG del sensore → deve fallire RUMOROSAMENTE (dev/CI lo catturano via AC-G90-1),
    MAI essere inghiottito: un sensore nato per chiudere i fallimenti silenziosi non può diventarne uno
    (regola #6 Determinismo). Parità con la call esistente di `reopen` (contracts.py:2094), che già non
    si protegge."""
    crediti = session.exec(select(CreditoCliente).where(
        CreditoCliente.id_contratto_origine == contract.id)).all()
    rimborso_diretto = round(sum(m.importo for m in session.exec(select(CashMovement).where(
        CashMovement.id_contratto == contract.id,
        CashMovement.tipo == "USCITA",
        CashMovement.categoria == CATEGORIA_RIMBORSO_CONTRATTO,
        CashMovement.deleted_at == None)).all()), 2)
    rate_attive = session.exec(select(Rate).where(
        Rate.id_contratto == contract.id, Rate.deleted_at == None)).all()
    for v in cstate.assert_contract_invariants(
            contract, crediti, rimborso_cassa_diretto=rimborso_diretto, rate_attive=rate_attive):
        logger.warning("Invariante %s violato dopo '%s' sul contratto %s: %s",
                       v.code, motivo, contract.id, v.message)
```

Unico delta rispetto all'originale: il **cambio di layer** router→service (zero cicli: importa solo
`models`/`contract_state`/`cash_categories`, mai router). In `contracts.py` resta un thin re-export per non
rompere la call esistente di `reopen`. Il corpo è **byte-identico** all'helper `_log_invariant_violations`
attuale (`contracts.py:77-102`) — niente `try/except` lì, niente qui.

### A.1-bis — Perché NIENTE `try/except` (lezione di codice, 2026-06-30)

La prima stesura avvolgeva il sensore in `except Exception: logger.exception(...)` per "garantire" che il
log-only non rompesse mai la transazione. **È l'errore opposto a quello che G9 vuole chiudere.** Tre ragioni,
code-grounded:

1. **Auto-contraddizione.** Un `except Exception` largo degrada un fallimento DURO in una riga di log che
   nessuno legge — il "fallimento silenzioso" vietato dalla regola non-negoziabile #6 (Determinismo) e dai
   pitfall #2/#7 ("422 silenzioso", "500 mascherato"). Un *sensore di invarianti* nato per **chiudere** i
   fallimenti silenziosi, se avvolto nel catch largo, **ne diventa uno**: un bug di refactor del sensore (un
   attributo rinominato, una query sbagliata) verrebbe inghiottito e mai surfacato.
2. **Non è lo stile del progetto.** L'**unico** `try/except` in `contracts.py` (~2.600 righe) cattura solo
   l'eccezione **specifica attesa**: `except (ValueError, TypeError)` su un `json.loads`. Mai un
   `except Exception` largo per controllo di flusso. E la call esistente del sensore (`reopen`,
   `contracts.py:2094`) **non ha alcun guard** — il `try/except` era una mia deviazione, non un allineamento.
3. **Non serve.** `assert_contract_invariants` è pura + `getattr(...,0)` → **non solleva** su un Contract ben
   tipato; le 3 query sono `SELECT` identici a quelli già eseguiti dagli endpoint (se sollevano, è un DB rotto
   → la transazione è comunque condannata, stesso destino del `commit()`). Non c'è nulla da catturare.

**Principio (correctness by construction):** non "gestisci l'eccezione" ma "rendi il codice incapace di
sollevarla". Se in futuro servisse hardening extra per la sicurezza-sui-dati-reali, la mossa giusta NON è un
catch ma il **disaccoppiamento post-commit** (A.1-ter), mai un `except Exception` che inghiotte.

### A.1-ter — Hardening (G9.3): osservazione post-commit, non guard

G9.0 è **osservazione**; l'osservazione appartiene **dopo** il fatto, sulla verità **committata**. Eseguire il
sensore **post-commit** (idealmente via listener SQLAlchemy `after_commit`, isolato dall'ORM) lo disaccoppia
**per costruzione** dalla scrittura: un suo fallimento non può fare rollback del denaro (è già durevole). È la
separazione che lo SPEC già distingue — **sensore = post-commit/osserva (G9.0)** vs **gate =
pre-commit/blocca-rollback (G9.3/G9.4)**. Per G9.0 minimale si tiene la **parità pre-commit** con `reopen`
(totale-per-costruzione); il disaccoppiamento post-commit atterra naturalmente con il **TransitionExecutor
(G9.3)**, dove l'osservazione diventa una fase post-commit esplicita. Se mai un sensore post-commit non
dovesse poter 500-are l'utente, il tool corretto è un guard **fail-loud-in-CI flag-gated** (re-raise salvo
`INVARIANT_SENSOR_STRICT` off, default ON in dev/test — riusa l'interruttore `INVARIANT_ENFORCEMENT` di
G9.4), **mai** un `except Exception` silenzioso.

### A.2 — Agganci (chiamata **immediatamente prima di `session.commit()`**, come reopen)

Il sensore vede lo stato post-mutazione: l'oggetto `contract` ha i nuovi valori in memoria e l'**autoflush**
di SQLModel materializza i `CashMovement`/wallet pendenti prima delle query del sensore.

| # | Transizione | File:riga (commit) | `motivo=` | Resa attesa |
|---|---|---|---|---|
| 1 | `reopen_contract` | `contracts.py:2095` | `"reopen"` | ✅ già cablato (`:2094`) |
| 2 | `terminate_contract` | `contracts.py:~1825` | `"terminazione"` | I1 deve reggere (chiuso ⟹ residuo 0) |
| 3 | `pay_rate` | `rates.py:~621` | `"pagamento"` | atteso pulito |
| 4 | `unpay_rate` | `rates.py:~735` | `"revoca_pagamento"` | atteso pulito |
| 5 | `incassa_residuo` | `contracts.py:~1445` | `"incassa_residuo"` | atteso pulito (già riconcilia le rate) |
| 6 | `incassa_credito_terminazione` | `contracts.py:~2323` | `"incassa_credito_differito"` | ⚠️ **Reperto #1 (A.3)** |
| 7 | `eroga_credito_cliente` | `clients.py:~1159` | `"eroga_wallet"` | basso-rendimento: usa `credito.id_contratto_origine` (l'`eroga` ha `id_contratto=None`, colonne intatte) |
| (8) | `annulla_credito_terminazione` | `contracts.py:~2350` | `"annulla_credito_differito"` | **opzionale**: zero-cassa, colonne intatte |

Gli agganci ad alto valore sono **#2–#6 + #7**; #8 è opzionale (zero-cassa). Per #7 il contratto da verificare
è `credito.id_contratto_origine` (non c'è un `contract` in scope nell'endpoint wallet).

### A.3 — ⚠️ Reperto #1: il sensore accenderà **I1** su `incassa_credito_terminazione` (atteso, log-only)

Per **analisi statica** (non eseguito), cablare #6 farà loggare I1 su ogni incasso di credito differito:

1. `terminate` ramo `A_CREDITO` (G7.10): `quota_stornata += residuo_pre` (storna **tutto** il residuo per
   forzare `residuo()==0` su CHIUSO) **e** traccia `credito_trainer` come receivable fuori da `residuo()`.
2. `incassa_credito_terminazione` (`contracts.py:2304`): `totale_versato += importo`, ma **`quota_stornata`
   non viene mai ridotta**.
3. `residuo_raw = prezzo − netto − quota_stornata` diventa **negativo** → `residuo()` resta 0 (clamp `max(·,0)`
   → check I1 "res>0" passa) ma il check **`residuo_raw < −0.01`** (`contract_state.py:382`) **scatta**.

**È G9.0 che funziona il primo giorno.** È *o* un over-reporting latente (la `quota_stornata` gonfiata
sovrastima gli storni nel `financial-trend`) *o* un artefatto benigno del clamp. **Decisione founder: log-only,
triage col dato** — G9.0 lo OSSERVA soltanto; il fix (probabile candidato: `incassa_credito_terminazione`
riduce `quota_stornata` di pari importo, oppure il modello accetta il raw-negativo come dichiarato) è un
mini-blocco successivo, deciso con la telemetria in mano. **G9.0 non aggiunge logica di fix.** Si documenta con
un test `@example`-style (terminate A_CREDITO → incassa → assert I1-raw loggato) così è **atteso, non sorpresa**.

**✅ RISOLTO (mini-blocco post-G9.0c, 2026-06-30).** Esame del blast radius: `quota_stornata` **NON è sommata in
alcun KPI/financial-trend** (grep esaustivo) → nessun over-reporting nelle dashboard, più stretto del temuto. Ma
DUE impatti reali oltre il segnale I1: (a) il valore-colonna `quota_stornata` sovrastimato; (b) **`reopen-preview`
sovrastimava `residuo_dopo`** del differito incassato (`contracts.py:2111` legge `quota_stornata`). Causa: il
terminate `A_CREDITO` storna l'INTERO `residuo_pre` (obbligatorio per tenere `residuo()==0` su CHIUSO), inclusa la
parte differita (`credito_trainer`) che è un DIFFERIMENTO, non un write-off. **Fix:** `incassa_credito_terminazione`
REVERTE lo storno provvisorio (`quota_stornata −= importo`) → `quota_stornata` converge a `quota_non_erogata` (P−R),
`residuo()==0` tenuto (il + su versato e il − su quota si compensano), `residuo_raw==0` (I1 chiuso), reopen-preview
corretto. La "monotonicità" di `quota_stornata` non era reale (reopen la azzera già) → raffinamento documentato in
`contract.py`. L'invariante I1 **non cambia** (era giusto a segnalare: si corregge il DATO, non si silenzia il
detector). L'`xfail(strict)` di A.6 è ora un test che PASSA (`test_reperto1_fix_incassa_credito_differito_invarianti_ok`);
+2 assert `quota_stornata` in `test_credito_differito`.

### A.4 — G9.0-b: `/reconciliation` bidirezionale

La query attuale (`dashboard.py:193-201`) confronta solo `totale_versato == Σ ENTRATA[id_contratto]`. Il lato
mancante NON è un semplice `Σ USCITA`: la forma **I5 raffinata** (D1 forma-d) è
`totale_rimborsato == Σ USCITA RIMBORSO_CONTRATTO[id_contratto] + Σ importo_erogato wallet ANNULLATO[id_contratto_origine]`
(il secondo addendo nasce dal fold R2-bis del reopen). SQL esteso:

```sql
SELECT c.id, cl.nome, cl.cognome, c.totale_versato, c.totale_rimborsato,
  COALESCE(SUM(CASE WHEN m.tipo='ENTRATA' THEN m.importo ELSE 0 END),0) AS ledger_entrate,
  COALESCE(SUM(CASE WHEN m.tipo='USCITA' AND m.categoria='RIMBORSO_CONTRATTO'
                    THEN m.importo ELSE 0 END),0) AS ledger_rimborsi_diretti,
  COALESCE((SELECT SUM(cc.importo_erogato) FROM crediti_cliente cc
            WHERE cc.id_contratto_origine = c.id AND cc.stato='ANNULLATO'
              AND cc.deleted_at IS NULL),0) AS wallet_riassorbito
FROM contratti c
LEFT JOIN clienti cl ON cl.id = c.id_cliente
LEFT JOIN movimenti_cassa m ON m.id_contratto = c.id AND m.deleted_at IS NULL
WHERE c.trainer_id = :tid AND c.deleted_at IS NULL
GROUP BY c.id
```

`delta_rimborsi = round(totale_rimborsato − (ledger_rimborsi_diretti + wallet_riassorbito), 2)`, flag se
`abs > 0.01`. Estendere `ReconciliationItem`/`ReconciliationResponse` (`financial.py`) coi campi rimborso
(additivo, response-only). NB: in **G9.2** questa derivazione diventerà una chiamata a
`project_columns_from_ledger` (unica fonte); per G9.0 l'estensione SQL è il taglio minimo a basso rischio.

### A.5 — G9.0-c: quick-win

- **QW1 — de-dup delle 2 formule `residuo` dei DTO** ✅. `CreditoTerminazioneResponse.residuo`
  (`financial.py:274`) e `CreditoClienteResponse.residuo` (`financial.py:296`) sono identiche
  (`round(max(importo − consumato, 0.0), 2)`). Helper puro in `contract_state.py`:
  `def residuo_credito(importo, consumato) -> float`. Entrambi i DTO lo chiamano. Test: parametrico +
  meta-test (toccare l'helper cambia entrambi).
- **QW2 — KPI gross-SQL: RE-SCOPED, non "corretto".** Il `prezzo_totale > totale_versato`
  (`dashboard.py:463`, helper `_contracts_to_plan_candidates`) è un **pre-filtro Step-1 deliberato della
  Sezione A** (`6d5ba31`): over-seleziona, la decisione finale la prende il SSoT `is_rate_planificabile` a
  valle (`dashboard.py:450`). "Correggerlo" net-aware contraddirebbe quella decisione e re-implementerebbe il
  SSoT in SQL. L'**unico rischio reale** è di **under-selezione** (un riaperto-con-rimborso: `rimborsato>0`,
  `prezzo ≤ versato` lordo ma `residuo()` net-aware > 0, escluso allo Step-1, mai raggiunge il SSoT).
  **Coerente con strumenta-poi-imponi: G9.0 NON lo tocca**; si lascia che la telemetria A.2 (o una query
  mirata) confermi se esiste un contratto reale così. Se confermato, il fix minimale è un **allargamento
  sicuro** del pre-filtro (`OR COALESCE(totale_rimborsato,0) > 0` — può solo *aggiungere* candidati al SSoT,
  mai escludere), non un rewrite. Rispetta la Sezione A e il principio.

### A.6 — Test plan (mappa agli AC §G9.0)

| AC | Test |
|---|---|
| **AC-G90-1** | per ognuna delle transizioni #2-#7: stato che viola I1/I4 iniettato → log `warning` col codice atteso (`caplog`) **e** commit avviene comunque (il sensore OSSERVA, non blocca). + test di **totalità**: su stati normali il sensore non solleva mai (è la garanzia che sostituisce il `try/except`; un suo bug fallisce-rumoroso nella suite, non viene inghiottito). |
| **AC-G90-2** | divergenza `totale_rimborsato` iniettata → `/reconciliation` la riporta in `delta_rimborsi`; + caso wallet-riassorbito che **non** è divergenza (regge l'I5 raffinata). |
| **AC-G90-3** | `residuo_credito` helper unico (parametrico + meta-test). |
| **AC-G90-4** | HTTP invariato su matrice scenari registrati; suite + `ruff` + `next build` verdi; **zero 409 nuovi**. |
| **Reperto #1** | ✅ RISOLTO (mini-blocco): terminate A_CREDITO → incassa → invarianti REGGONO (`quota_stornata` revertita, residuo_raw==0). Era `xfail(strict)`, ora passa. Vedi §A.3 (✅ RISOLTO). |

Nuovo `tests/test_invariant_gate.py` (sensore + fail-safe + Reperto #1) + estensione di
`test_reconciliation`/`test_dashboard` (AC-G90-2) + un test per QW1.

### A.7 — Piano di commit (3 commit atomici, branch sempre verde)

1. `feat: G9.0a — invariant sensor ovunque (log-only, totale-per-costruzione) + estrazione invariant_gate.py`
2. `feat: G9.0b — /reconciliation bidirezionale (lato rimborso, I5 raffinata)`
3. `refactor: G9.0c — de-dup residuo_credito (DTO) + nota under-select KPI da telemetria`

Ognuno passa `check-all.sh`. Reperto #1 resta **log-only** (zero blocco), in coda di triage.
