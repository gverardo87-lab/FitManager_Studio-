# Audit — Il piano rate diverge dal residuo (denaro-fantasma a livello rata)

> **Provenienza:** test di flusso del trainer reale (Chiara Pais, contratto 35) → diagnosi senior code-grounded
> sul DB reale (`data/crm.db`, read-only). **Data:** 2026-06-29.
> **Trigger founder:** «contratto saldato ma la rata è ancora segnalata in ritardo — stiamo andando a tentativi,
> serve capire l'errore architetturale e di metodo che perseveriamo».
> **Esito:** una **legge mancante** (INV-RATE) → **ADR-021** + `SPEC_INTEGRITA §17` (blocco **G8.3**, stance C).

## 1. Il sintomo (ground truth)

Contratto 35 (10 Lezioni, 400€), DB reale:
- `prezzo 400 · versato 400 · rimborsato 0 · storno 0` → **`residuo()=0`, SALDATO, Attivo**.
- versato da **due canali**: 280 via **rata** (`mov 223`, `PAGAMENTO_RATA`, `id_rata=106`) + 120 via **conguaglio**
  (`mov 221`, `INCASSO_CONGUAGLIO_CONTRATTO`, **`id_rata=None`**, da un `credito_trainer` terminato e incassato).
- **rata 106:** `previsto 400 · saldato 280` → **PARZIALE**, residuo-rata **120**, scad 2026-06-15 → **"scaduta"**.

La UI mostra `RESIDUO 0,00 €` **e** `RATE PAGATE 0/1` **e** `1 scaduta`. Il residuo-rata fantasma (120) è
**esattamente** il conguaglio (120). Il cliente "deve" 120 su un contratto da 400 già pagato (pagherebbe 520).

## 2. La pistola fumante (il sistema misura la propria contraddizione)

`_to_response_with_rates` (`contracts.py`) calcola **da due ledger diversi**:
- `residuo` (riga 174/199) ← **SSoT contratto** `cstate.residuo()` net-aware = **0**.
- `rate_scadute` (riga 152/209) ← **ledger rata** `is_scaduta = stato!='SALDATA' and data_scadenza<today` = **1**.
- `rate_pagate` (riga 160/208) ← **ledger rata** (SALDATA?) = **0/1**.
- `piano_allineato` (riga 178/205) = `abs(residuo − Σ residui-rata) < 0.01` = `abs(0 − 120)` → **False**,
  `importo_disallineamento = −120`.

**Il sistema sa** che il piano non torna (`piano_allineato=False`) e spedisce alla UI **entrambe le verità**
senza risolverle né bloccare. Non è un glitch di display: la rata `previsto 400` è un **dato sbagliato** (vuole
400 da un canale che dovrebbe incassarne 280).

## 3. L'errore ARCHITETTURALE (la radice che perseveriamo)

**Esistono due libri mastri dell'obbligazione e ne abbiamo reso SSoT solo uno.**
- G8.1 ha eletto `residuo()` (net-aware) a SSoT del "quanto è dovuto" — a livello **contratto**.
- Il **piano rate** è un **secondo ledger** parallelo (`previsto` vs `saldato`, stato, scaduta per-rata) che la
  UI **legge ancora** ("rate pagate N/M", "X scaduta").
- I due vengono riconciliati **in un solo punto**: `_reconcile_rate_plan` **su reopen**. Ogni **altro** canale
  che abbassa il residuo **senza passare da una rata** — `incassa-residuo` (G6), conguaglio (G7.9/G7.10) —
  lascia il piano rate **stale**. Ogni nuovo canale di incasso non-rata ha riaperto lo stesso buco.

In una frase: **abbiamo centralizzato il residuo ma non il piano rate**; il piano è la *promessa di come*
incasserai il residuo, e quando incassi per un'altra strada nessuno aggiorna la promessa.

## 4. L'errore di METODO (perché andiamo a tentativi)

1. **Test su operazioni isolate, non sequenze reali composte.** Il bug richiede `terminate(A_CREDITO) → incassa
   conguaglio → reopen → paga rata` sullo **stesso** contratto. Nessun test esercita l'effetto di un incasso
   **non-rata** sul piano rate.
2. **L'harness `assert_contract_invariants` (I1/I4/I5) non copre l'invariante cross-ledger** "Σ residui-rata vs
   residuo". La rete strutturale ha il buco **proprio qui** (ed è cablata solo su reopen, log-only).
3. **Patchiamo i transition point invece di imporre un invariante.** `_reconcile_rate_plan` su reopen,
   `_cap_rateizzabile` su create/update: riconciliazione ad-hoc. Aggiungiamo *capability*, non *correttezza*.
4. **Ignoriamo un segnale che già calcoliamo** (`piano_allineato=False`): nessun blocco, nessuna
   auto-riconciliazione, nessun alert risolutivo — la contraddizione finisce in UI.

## 5. La legge mancante + la decisione (stance C)

> **INV-RATE:** per un contratto **non chiuso**, `Σ(previsto − saldato)` sulle rate attive non-saldate **≤
> `residuo()`**. Il piano rate è una **partizione del residuo** (proiezione del SSoT), mai un'obbligazione
> indipendente. *Eccedenza* (`Σ > residuo`) = denaro-fantasma → **vietata**. *Sotto-copertura* (`Σ < residuo`)
> = legittima ("da pianificare"). Confermata dal founder come legge mancante corretta.

**Stance C (founder, 2026-06-29) — chiude la CLASSE, non l'istanza:**
- **(B) Riconciliazione ovunque.** `_reconcile_rate_plan` (che già taglia l'eccedenza) viene chiamata su **ogni**
  path che abbassa il residuo su un contratto aperto con rate attive — oggi manca su `incassa-residuo` (G6); il
  reopen la chiama già. Corregge il **dato** (rata 106 → `previsto 280`/SALDATA come *conseguenza*, non a mano).
- **(invariante) INV-RATE nell'harness.** Nuovo `I6` in `assert_contract_invariants` (`Σ residui-rata ≤ residuo`),
  esercitato dall'harness su **sequenze composte** → un futuro path che riapre il buco fa **fallire un test**.
- **(A) Proiezione difesa-in-profondità.** Nel read-model, `is_scaduta`/residuo-rata non possono contraddire
  `residuo()==0` — copre i dati **già stale** (contratto 35) a vista, mentre B sana il dato al prossimo tocco.

## 6. Output → governance

**ADR-021** (piano rate = partizione del residuo; generalizza D-RECONCILIA-RATE da reopen-only a *ogni path*;
formalizza INV-RATE; estende ADR-019). AC falsificabili in `SPEC_INTEGRITA §17` (G8.3). **Limite dichiarato:**
diagnosi + decisione; la validazione runtime è in fase implementativa (harness compound-sequence + Playwright sul
contratto 35 reale). **Confine:** asse DENARO invariato (`residuo()`/Strada B/cassa-immutabile intatti) — questo
giro tocca solo la **coerenza del piano rate** col residuo, non il calcolo del residuo.
