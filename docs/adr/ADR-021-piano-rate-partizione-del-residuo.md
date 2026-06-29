# ADR-021 — Il piano rate è una partizione del residuo (proiezione del SSoT, mai obbligazione indipendente)

- Date: 2026-06-29
- Status: accepted
- Deciders: Giacomo Verardo (AVGV Technologies); diagnosi senior code-grounded di Claude Code
- Audit fondante: `docs/operations/AUDIT_PIANO_RATE_VS_RESIDUO_2026-06-29.md`
- Generalizza: **D-RECONCILIA-RATE** (ADR-019 Addendum I), oggi cablata **solo su reopen** → su **ogni** path che muove il residuo
- Correlati: `ADR-019` (residuo net-aware, cassa-immutabile), `FINANCIAL_DOMAIN_MODEL.md`; blocco **G8.3**

## Context

G8.1 ha eletto `residuo()` (net-aware) a SSoT del "quanto è dovuto" **a livello contratto**. Ma il **piano
rate** resta un **secondo ledger** dell'obbligazione (`importo_previsto` vs `importo_saldato`, stato per-rata,
scaduta per-rata) che la UI legge direttamente ("rate pagate N/M", "X scaduta"). I due ledger sono riconciliati
**solo su reopen** (`_reconcile_rate_plan`). Ogni canale che abbassa il residuo **senza passare da una rata**
(`incassa-residuo` G6, conguaglio G7.9/G7.10) lascia il piano rate **stale** → un contratto SALDATO (`residuo()=0`)
può mostrare una rata PARZIALE/scaduta con un **residuo-rata fantasma** pari all'incasso non-rata (audit fondante:
contratto reale 35 di Chiara Pais — saldato a 400 = 280 rata + 120 conguaglio, rata `previsto 400` → fantasma 120).
Il read-model **misura** la divergenza (`piano_allineato=False`, `disallineamento=−120`) ma la spedisce alla UI
come contraddizione invece di risolverla.

## Decision Drivers

- **Un solo SSoT del dovuto:** se `residuo()` è la verità, il piano rate non può esprimerne una seconda.
- **Chiudere la CLASSE, non l'istanza:** ogni nuovo canale di incasso non-rata ha riaperto lo stesso buco →
  serve un invariante imposto, non l'ennesima riconciliazione ad-hoc al transition point.
- **Correttezza del dato, non solo del display:** una rata che esige più del dovuto è un dato sbagliato.
- **Non regredire le decisioni vive:** asse DENARO (`residuo()`, Strada B, cassa-immutabile ADR-019), la
  sotto-copertura legittima "da pianificare" (F2-bis: mai fabbricare una rata-fantasma).

## Decision

**Il piano rate è una proiezione (partizione) del residuo, mai un'obbligazione indipendente.** Legge vincolante:

> **INV-RATE** — per un contratto **non chiuso**: `Σ(importo_previsto − importo_saldato)` sulle rate attive
> non-saldate **≤ `residuo()`**. *Eccedenza* (`Σ > residuo`) = denaro-fantasma → **vietata**. *Sotto-copertura*
> (`Σ < residuo`) = legittima ("da pianificare", invariata da F2-bis). *Pari* = round-trip esatto.

Adozione **stance C** (decisione founder 2026-06-29), tre leve complementari:

1. **D-RICONCILIA-OVUNQUE** (generalizza D-RECONCILIA-RATE). `_reconcile_rate_plan` — che **già** taglia
   l'eccedenza al residuo (ramo ECCEDENZA: cut cronologico, mai sotto il saldato) — viene invocata su **ogni**
   path che abbassa il `residuo()` di un contratto **aperto con rate attive**. Manca oggi su **`incassa-residuo`
   (G6)**; il `reopen` la chiama già. La rata stale diventa SALDATA **per conseguenza**, mai a mano.
2. **D-INVARIANTE-NELL-HARNESS.** Nuovo invariante **I6 (INV-RATE)** in `contract_state.assert_contract_invariants`
   (`Σ residui-rata ≤ residuo()` sui non-chiusi), esercitato dall'harness su **sequenze composte** (terminate →
   incassa → reopen → paga). Un futuro path che riapre il buco fa **fallire un test** (chiude la CLASSE).
3. **D-PROIEZIONE-DIFESA.** Nel read-model (`_to_response_with_rates`) `is_scaduta`/residuo-rata **non possono
   contraddire** `residuo()` (un contratto saldato non ha rate scadute): copre a vista i dati **già stale** (es.
   contratto 35) finché D-RICONCILIA-OVUNQUE non li sana al prossimo tocco.

**Invarianti che NON cambiano:** `residuo()` net-aware, Strada B, cassa-immutabile (ADR-019), asse EROGATO
(ADR-016), bilateralità (ADR-018), `residuo==0 ⟺ saldato`, sotto-copertura "da pianificare" (F2-bis). Backend-only,
**zero schema-change**.

## Considered Options

- **A — solo proiezione** (display non contraddice il residuo): leggero, ma lascia in DB il dato sbagliato.
- **B — solo riconciliazione ovunque:** corregge il dato, ma senza invariante un futuro path riapre il buco in
  silenzio.
- **C — A+B+INV-RATE nell'harness (scelta):** corregge il dato (B), difende il display per lo stale (A), e
  **impedisce la regressione** (invariante). Chiude la classe, non l'istanza.

## Consequences

- **Positive:** un solo SSoT del dovuto reso vero **anche a livello rata**; i contratti saldati non mostrano più
  rate scadute fantasma; il piano rate si auto-corregge su ogni incasso non-rata; l'harness intercetta ogni
  futura divergenza.
- **Costo:** `_reconcile_rate_plan` chiamata su un path in più (`incassa-residuo`); `assert_contract_invariants`
  guadagna un parametro (le rate attive) + I6; il read-model guadagna un clamp di proiezione. Dati **già stale**
  (contratto 35): sanati alla vista da A subito, nel dato da B al prossimo incasso/reopen (o riconciliazione
  one-shot se serve).
- **Follow-up:** a implementazione aggiornare `FINANCIAL_DOMAIN_MODEL.md` (INV-RATE), `api/CLAUDE.md`,
  `BUILD_LOG.md`. Estensione naturale futura: cablare `assert_contract_invariants` (con I6) su **tutti** i path
  finanziari (oggi solo reopen, log-only) — fuori scope G8.3, è il rollout già differito da G8.2-prep.

## Supersedes / Superseded By

- **Generalizza D-RECONCILIA-RATE** (ADR-019 Addendum I) da "reopen riconcilia il piano rate" a "il piano rate è
  **sempre** una partizione del residuo, riconciliata su ogni path che lo muove". **Estende ADR-019.**
- Superseded by: —

## Stato implementazione (2026-06-29): ⏳ DECISIONE PRESA, codice PENDENTE.

AC falsificabili in `SPEC_INTEGRITA §17` (G8.3). È **chiusura della classe «piano rate ≠ residuo»**, non un nuovo
prodotto.
