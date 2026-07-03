# ADR-017 — Il rinvio libera il credito: `Rinviato` fuori dall'asse OCCUPAZIONE (emenda ADR-016 §1)

- Date: 2026-06-26
- Status: accepted
- Deciders: Giacomo Verardo (AVGV Technologies); analisi e bridge code-grounded di Claude Code
- Related upgrade ID: G7.8 (rinvio → libera credito)
- Spec di dettaglio (contratto d'implementazione): `docs/archive/specs/SPEC_RINVIO_LIBERA_CREDITO.md`
- Emenda: `ADR-016` §1 (definizione dell'asse OCCUPAZIONE)
- Correlati: `ADR-014` (gestione finanziaria); modello vivo: `FINANCIAL_DOMAIN_MODEL.md`, `TASSONOMIA_FINANZIARIA.md`

## Context

`ADR-016` (2026-06-26) ha ratificato l'asse **EROGATO** come unica base monetaria del recesso (corretto
al 100%) e ha, **per omissione**, congelato anche la definizione dell'asse OCCUPAZIONE come
`!= Cancellato` = `Programmato + Completato + Rinviato`. L'audit da cui nasce ADR-016 era focalizzato
sull'asse denaro e non ha messo in discussione la semantica dell'occupazione pre-esistente.

Una **seconda segnalazione del trainer reale (Chiara)** la rivela errata: *"i crediti delle sedute
rinviate vengono scalati come se fossero state svolte"*. Verifica code-grounded (bridge):
- **Bug confermato.** `api/routers/contracts.py:149` calcola `crediti_usati_computed = programmate +
  completate + rinviate`, mentre lo schema che serve (`api/schemas/financial.py:404`) documenta
  `# crediti_totali - programmate - completate` — **senza** rinviate. Il codice contraddice il proprio
  contratto: `crediti_residui` è **sottostimato** della quantità di sedute rinviate.
- **Asse denaro strutturalmente invariante.** `compute_settlement` riceve `sedute_erogate` (`Completato`)
  e `residuo_corrente` (prezzo/versato); **nessuno dei due** legge il predicato `!= Cancellato`. Il
  rimborso/conguaglio **non cambia** (forfeiture delle prenotate inclusa). Il fix è solo sull'asse credito.

Modello di dominio (standard del settore — Mindbody/TrueCoach: *early cancel* libera il credito): una
seduta **rinviata** è uno **slot liberato**, non servizio reso né capacità ancora impegnata.

## Decision Drivers

- **Correttezza di dominio**: il rinvio restituisce il credito; contarlo come usato è una perdita
  silenziosa di credito per il cliente (specchio dell'invariante anti-perdita di ADR-015, lato sedute).
- **Determinismo / SSoT**: un solo predicato di occupazione-credito, derivato in `contract_state`.
- **Non distruttività**: `Rinviato` resta uno stato distinto da `Cancellato` (tracciabilità "da
  riprogrammare" ≠ "non avverrà"), pur avendo lo stesso effetto aritmetico sul pool crediti.

## Considered Options

### Option A — Lasciare `Rinviato` nell'occupazione (status quo, ADR-016 §1)
- Contro: i crediti rinviati restano scalati come svolti; `crediti_residui` sottostimato ovunque;
  contraddice la realtà operativa segnalata da un cliente reale.

### Option B — `Rinviato` libera il credito (sempre), resta stato distinto (scelta)
- Pro: `crediti_residui` corretto; `contract_state` (SOSPESO/ESAURITO/auto-close) eredita la definizione
  giusta una volta corretti **tutti** i produttori di `crediti_usati`; zero impatto sull'asse denaro.
- Contro: tocca molti siti (predicato sparso); richiede inventario esaustivo (vedi bridge §3 sotto).

### Option C — Modello Mindbody completo (finestra di preavviso + `NO_SHOW`)
- Pro: distingue *early cancel* (credito reso) da *late cancel/no-show* (credito bruciato).
- Contro: richiede campo preavviso + policy per-trainer + nuovo stato → **differito** (spec §9), non in
  questa iterazione (decisione founder D-MODELLO: modello semplice, il rinvio libera sempre).

## Decision

**Option B.** Si emenda `ADR-016` §1: l'asse **OCCUPAZIONE-CREDITO** =

```
Event.categoria == 'PT' AND Event.deleted_at IS NULL AND Event.stato IN ('Programmato','Completato')
```

`Rinviato` (come `Cancellato`) **non occupa** il credito. Decisioni founder vincolanti (2026-06-26):

1. **D-MODELLO** — il rinvio libera **sempre** il credito (nessuna finestra di preavviso in questa
   iterazione; `NO_SHOW`/credito-bruciato = estensione futura non distruttiva, spec §9).
2. **D-AUTO-CLOSE** — un contratto saldato con tutte le sedute rinviate (zero `Completato`) **resta
   aperto**: conseguenza automatica del conteggio corretto (`crediti_residui > 0` → non `ESAURITO`),
   **a patto che TUTTI i produttori di `crediti_usati` siano corretti** (vedi bridge sotto).
3. **D-GUARD** — una rinviata libera lo slot → si può riprenotare (il credit guard di `create_event`
   non blocca più). Per coerenza, **anche `_check_overlap` esclude `Rinviato`** (lo slot orario torna
   libero, §3-bis della spec deciso = CAMBIA).

**Invarianti che NON cambiano** (ADR-016 restano in vigore): asse EROGATO canonico per il denaro,
barriera strutturale di `compute_settlement`, forfeiture delle sedute `Programmato` (le prenotate non
riducono il rimborso). L'oracolo settlement deve restare **byte-identico** pre/post (spec §5).

### Esito del bridge code-grounded (vince il codice — correzione alla spec v1)

L'inventario §3 della spec era esaustivo **solo sui file in contesto** (`clients/agenda/contracts/
dashboard`, classificati correttamente). Il bridge ha trovato **5 produttori di `crediti_usati`
mancanti** negli altri file — la cui omissione romperebbe D-AUTO-CLOSE e le worklist del cockpit:
`rates.py:565` (auto-close di `pay_rate`, **gemello payment-driven** di `_sync_contract_chiuso` —
documentato dal commento `agenda.py:307`), `workspace_engine.py:1247/1389/2145`, `client_avatar.py:430`.
Più `_check_overlap` (`agenda.py:198`) per D-GUARD. Dettaglio e classificazione completa (CAMBIA/LASCIA)
nella spec, marcati `[Bridge Code 2026-06-26]`.

## Consequences

- **Positive**: `crediti_residui` corretto in ogni vista; D-AUTO-CLOSE retta su **entrambi** i rami di
  chiusura (credit-driven + payment-driven); cockpit/worklist coerenti; zero euro spostato (asse denaro
  invariante per costruzione).
- **Negative**: predicato da correggere su ~16+5 siti credito; sui `crm.db` reali con eventi `Rinviato`
  preesistenti i `crediti_residui` **risalgono** al deploy (è il fix che si manifesta — comunicazione a
  Chiara, spec §11); alcuni contratti auto-chiusi `COMPLETAMENTO` per rinviate andranno rivisti
  (read-only, decisione umana caso per caso, spec §7 — popolazione distinta dai muti M4 dell'audit).
- **Follow-up actions** (blocco G7.8, `SPEC_RINVIO_LIBERA_CREDITO.md`):
  - Implementare T1 in un commit isolato validato contro l'oracolo settlement; overlap (§3-bis) incluso.
  - Estendere il grep-guard di ADR-016 con un check anti-ritorno di `!= 'Cancellato'` sui siti credito
    (allowlist per i siti calendario/attività di §3.3).
  - A implementazione: aggiornare `FINANCIAL_DOMAIN_MODEL.md` (definizione occupazione), `api/CLAUDE.md`,
    `BUILD_LOG.md`.

## Rollback / Exit Strategy

T1 è puro cambio di predicato + correzione di una somma (`contracts.py:149`): **nessuna migrazione,
nessuno schema**. Rollback = ripristino del predicato `!= 'Cancellato'` sui siti credito; ADR-016 §1
tornerebbe la definizione vigente. Nessun dato alterato.

## Supersedes / Superseded By

- Supersedes: emenda `ADR-016` §1 (definizione dell'asse OCCUPAZIONE). L'asse EROGATO e la forfeiture
  (ADR-016 §1 prima parte e §2) restano invariati.
- Superseded by: —

---

## Addendum I (2026-07-03) — Late Cancel & No Show: completamento dell'Opzione C (G7.8-bis)

**Stato: accepted** (ratifica founder 2026-07-03, sequenza Step 0→1). Spec prescrittiva:
`docs/archive/specs/SPEC_LATE_CANCEL_NO_SHOW.md` (+ §6 bridge code-grounded).

L'ADR originale scartò l'Opzione C ("Modello Mindbody" — stati-penale che occupano il credito) SOLO
per scope pre-lancio, non nel merito. La richiesta del PT reale la riporta in scope. Decisioni:

- **D-STATI-PENALE**: due nuovi stati Event PT — `Cancellato_Tardivo` (annullata fuori tempo massimo)
  e `No_Show` (mancata presentazione). Semantica a 3 assi: **occupano il credito** (come Completato,
  definitivi), **contabilizzano nel conguaglio di recesso** (penale dovuta al trainer, ADR-016
  asse-EROGATO esteso a asse-CONTABILIZZABILE), **NON sono performance** (Training Science li ignora).
  `Rinviato`/`Cancellato` continuano a liberare (il cuore di questo ADR resta invariato).
- **D-SSOT-PREDICATO (Step 0, behavior-preserving — FATTO)**: il predicato occupazione è estratto a
  simbolo unico `contract_state.STATI_OCCUPAZIONE_CREDITO`; i 17 siti di conteggio (ORM + raw SQL)
  consumano il simbolo; il test semantico `tests/test_occupazione_ssot.py` vieta i literal
  (enforcement al posto dell'enumerazione — lezione Giro-2). Aggiungere uno stato = 1 riga.
- **D-CONTEGGI-SEPARATI**: nel settlement, `count_sedute_erogate` resta SOLO-Completato (nome onesto);
  `count_sedute_penali` conta gli stati-penale; il conguaglio riceve la SOMMA (contabilizzabile);
  l'audit snapshot registra i due numeri SEPARATI. Il modulo puro `contract_settlement.py` resta
  cieco all'occupazione (ADR-016) — firma invariata.
- **D-DENYLIST-INTATTE**: i 21 siti calendario/recency a denylist `!= 'Cancellato'` NON cambiano
  (censimento e razionale in SPEC §6.2): un No_Show è un appuntamento reale della relazione.
  Escluderlo da una metrica sarà sempre una decisione esplicita per-sito, mai un default.
- **D-PENALE-PROVISIONAL**: la trattenuta della penale nel conguaglio di recesso è esigibile solo se
  pattuita nel contratto col cliente — stesso trattamento di `pro_sedute` (PROVISIONAL, gated dal
  tributarista); il software propone, il microcopy resta proposta-non-obbligo.

Consequences: l'auto-close scatta anche a saturazione con penali (via `sync_contract_chiuso`, un solo
sito post-G9.3); il credit_breakdown espone i nuovi stati (display pieno in G8.4); FSM Event: il guard
"Bouncer 4" resta scope-ristretto a `→Rinviato` (G7.8#2), le transizioni fra stati non-performance e
`Completato→penale` (correzione) sono permesse.
