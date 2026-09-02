# AUDIT_FINANCIAL_ARCHITECTURE — write-model del dominio contrattuale-economico

> **ARCHIVIATO 2026-09-02** — audit fondante di ADR-022; filone G9 chiuso 2026-07-05. Riferimento
> storico, mai contesto di lavoro.

**Tipo:** audit architetturale **READ-ONLY** (mappa lo stato, non muta codice). **Data:** 2026-06-30 ·
**Branch:** `FitManager_Studio` (post-G8.3).
**Trigger:** osservazione del founder dopo G8.3 — «continuano a uscire scenari secondari che gestiamo
singolarmente; le SSoT non sono come dovrebbero, mancano strati che unifichino le variabili».
**Metodo:** review multi-agente code-grounded — 8 reader paralleli (una facet ciascuno, evidenza `file:riga`)
+ 5 lenti senior indipendenti (billing/ledger, DDD/state-machine, reliability/invarianti, numerics,
evolvibilità) + sintesi. **Fonda:** `ADR-022` + `SPEC_G9_FINANCIAL_COMMAND_LAYER.md`.

> Le coordinate `file:riga` sono lo snapshot 2026-06-30: **esiti durevoli, righe da riverificare**.

---

## 0. Tesi (confermata)

Il problema di altitudine **non è** «le colonne divergono dal ledger». È che **`contract_state.py` è un SSoT
di *lettura* (puro, corretto, net-aware) senza il suo gemello di *scrittura*** — e di conseguenza **il ledger
`CashMovement` non è load-bearing, è consultivo**. Gli 8 ADR del dominio (014-021) sono istanze della stessa
legge riscoperta scenario per scenario; il treadmill è l'assenza dello strato di scrittura, non incompetenza.

## 1. Le due prove provate (smoking guns)

1. **`quota_stornata` è l'unico euro nella formula del `residuo()` senza alcun posting nel ledger**
   (`contracts.py:1751`): è un memorandum puro. `residuo = prezzo − netto − quota_stornata`, ma `quota_stornata`
   non è una somma su `CashMovement` — è una colonna scritta a mano.
2. **Il fold R2-bis del reopen è una ri-attribuzione contabile senza movimento** (`contracts.py:2038`):
   `totale_rimborsato += wallet_erogato_riassorbito` esiste **solo per far tornare la formula** net-aware,
   non corrisponde a una scrittura di cassa.

E il corollario diagnostico: la **`/reconciliation`** (`dashboard.py:193-201`) **è la diagnosi stessa** — un
audit *post-facto* che ammette che la verità è il ledger ma la scopre dopo, ed è pure **monca** (verifica solo
`totale_versato == Σ ENTRATA`, mai il lato `rimborsato`).

## 2. Mappa delle facet (8 reader)

| Facet | Stato attuale | Smell principale |
|-------|---------------|------------------|
| **SSoT topology** | `residuo`/`netto`/`stato_pagamento` derivati dal SSoT puro, MA `residuo` ricomputato anche in 2 DTO con formula inline copiata (`financial.py:274-275`, `:296-297`) e KPI gross-SQL in `dashboard.py` | tripla derivazione del residuo; nessun guard impedisce la 5ª copia |
| **Ledger ↔ colonne** | `CashMovement` «sacro» ma `totale_versato`/`totale_rimborsato`/`quota_stornata` sincronizzate a mano in ~7 siti (`contracts.py:1663/1724/1751/2038`, `rates.py` pay/unpay, `incassa-residuo`) | doppia verità; I5 e `/reconciliation` esistono per **controllare** la sync invece di **impedirla** |
| **Transizioni** | terminate ~256 righe (`:1573-1828`), reopen ~182 (`:1916-2098`) inline nei router; passi ripetuti (penna+rate+reconcile+audit+lifecycle+sync+invarianti); auto-close duplicato (`rates.py` vs `agenda.py:301`) | nessun transition executor; «MAI … senza chiamare …» = disciplina al posto di garanzia |
| **Invarianti** | `assert_contract_invariants` I1/I4/I5/I6 completo/corretto (`contract_state.py:329-426`) ma cablato runtime **solo su reopen** (`:2094`, log-only) | invarianti osservati, non imposti; 4 grep-guard testuali (`check-all.sh:40-84`) impongono via stringa |
| **Numerics** | denaro float; ~150 dead-zone (`±0.009`/`±0.01`) + `round(·,2)` sparsi | contraddizione `is_saldato` (≤0.01) vs `money_substate` (≤0.009) |
| **Read-model / KPI** | `dashboard.py` (~980 LOC) + trend + worklist; classificazione ri-derivata N volte; `rinnovi-incassi` + `workspace_engine` ancora off-SSoT (Giro 2 pendente) | nessuna separazione write↔read; pitfall #14 (cumulativo vs stato) è un sintomo |
| **Governance** | 8 ADR + ~10 spec per 1 bounded context | ogni ADR re-scopre «una grandezza deve restare derivabile / una transizione deve preservare un'àncora» |
| **Test** | crescita per-scenario (586→718); 1 harness invariante×transizione | strategia reattiva (un test per bug) vs generativa (leggi su tutto lo spazio stati×transizioni) |

## 3. Convergenza delle 5 lenti senior

| Lente | La sua UNA mossa |
|-------|------------------|
| Billing/ledger (Stripe/Chargebee) | invertire la direzione della verità: `project_columns_from_ledger` + promuovere l'invariante da osservatore a gate |
| Reliability / property-based | cablare `assert_contract_invariants` su tutte le transizioni, log-only |
| Evolvibilità (lead solo-founder) | punto unico di scrittura del ledger (`post_inflow`/`post_outflow`) |
| DDD / state-machine | TransitionExecutor che tiene i router sottili |
| Numerics | `Money` value-type dietro i moduli puri |

**Tre lenti su cinque puntano allo stesso punto: il lato-scrittura.** Tutte e cinque dicono *evolvi, non
riscrivere*.

## 4. Lo strato mancante (sintesi)

Un **financial command layer** in due metà che rende il ledger load-bearing: **(A) penna unica** di posting
(unico punto che muta le colonne cassa) + **(B) transition executor** (unico punto che applica una transizione
e ne asserisce gli invarianti). Con questi, I5 diventa vero **per costruzione** e «aggiungere uno scenario»
diventa «aggiungere una posting-rule + una transizione». → Decisione: `ADR-022`. → Build: `SPEC_G9` (G9.0→G9.6,
strumenta-poi-imponi, branch sempre rilasciabile).

## 5. Scope / non-scope

- **Read-only:** questo audit non muta codice. La rete di sicurezza dell'evoluzione (`contract_state.py`/
  `contract_settlement.py` puri, harness, 718 test) è confermata sana.
- **Asse DENARO invariato:** G9 non cambia *cosa* il sistema calcola — cambia *chi e come lo scrive*. Tutte
  le decisioni ADR-016→021 restano valide.
- **Fuori scope:** G1 (cifratura crm.db, ADR-013) è filone indipendente, in stand-by; la priorità relativa
  G9↔G1 è scelta del founder.
