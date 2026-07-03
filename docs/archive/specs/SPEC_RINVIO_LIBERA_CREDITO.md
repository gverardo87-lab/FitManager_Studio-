# SPEC_RINVIO_LIBERA_CREDITO

**Stato:** ✅ **IMPLEMENTATA** (G7.8, `f4101c4`, 2026-06-27) — **ESTESA da G7.8-bis** (2026-07-03,
`4944a49`+`db322eb`, ADR-017 Addendum I): l'occupazione è ora un SSoT a **4 stati**
(`contract_state.STATI_OCCUPAZIONE_CREDITO`, penali `Cancellato_Tardivo`/`No_Show` incluse) — il
predicato a 2 stati prescritto qui sotto è SUPERATO. Vedi `docs/archive/specs/SPEC_LATE_CANCEL_NO_SHOW.md`.

> Blocco: **G7.8** · ADR di copertura: **ADR-017** (emenda ADR-016 §1, **accepted** 2026-06-26)
> Provenienza: segnalazione trainer reale (Chiara) — "i crediti delle sedute rinviate vengono scalati
> come se fossero state svolte". Decisioni di dominio ratificate dal founder il 2026-06-26.
> Stile: prescrittivo (bridge Chat→Code). Dice **cosa deve essere vero**, non **come**.
> La ground truth è il codice reale; se diverge da questo documento, **vince il codice**.

> **[Bridge Code 2026-06-26] — verifica code-grounded su HEAD `324be75`.** Esito:
> - **Tesi T1 confermata** e bug riprodotto: `contracts.py:149` somma `+ rinviate`, il commento dello
>   schema `financial.py:404` no → `crediti_residui` sottostimato.
> - **Asse denaro invariante per costruzione** (§5/§6 verificati): `compute_settlement` non legge mai
>   `!= Cancellato`.
> - **Inventario §3 incompleto.** La spec v1 era esaustiva **solo sui file in contesto** (`clients/agenda/
>   contracts/dashboard`, tutti classificati **correttamente**). Il bridge ha trovato **5 produttori di
>   `crediti_usati` mancati** (`rates.py:565`, `workspace_engine.py:1247/1389/2145`, `client_avatar.py:430`)
>   → integrati in §3.1. Senza, D-AUTO-CLOSE si rompe sul ramo `pay_rate` e le worklist del cockpit
>   restano sbagliate.
> - **§3-bis risolto = CAMBIA** (decisione founder): `_check_overlap` (`agenda.py:198`) esclude `Rinviato`.
> - Siti `LASCIA` verificati ed elencati in §3.3 (con allowlist). Borderline classificati.

---

## 0. Tesi unica (falsificabile)

> **T1 — `Rinviato` non è occupazione.**
> Una seduta in stato `Rinviato` rappresenta uno slot **liberato**: non consuma il credito,
> non blocca la creazione di nuove sedute, non concorre all'auto-close, non pesa nel FIFO.
> Per ogni contratto vale:
>
> ```
> crediti_residui = crediti_totali − (sedute Completato + sedute Programmato)
> ```
>
> **con `Rinviato` escluso dal conteggio**, e **nessun importo in euro cambia** in nessun
> path (preview, terminate, reopen, KPI, riconciliazione ledger).

Falsificabile su due fronti opposti, entrambi obbligatori:
1. Costruisci un contratto con almeno una seduta `Rinviato`: i `crediti_residui` mostrati
   da tutte le viste devono **risalire** della quantità di rinviate (oggi le scalano).
2. L'**oracolo settlement** (§5) deve restare **byte-identico** prima/dopo su tutti i contratti.

---

## 1. Modello ratificato (decisioni di dominio, vincolanti)

Tre stati di **consumo del credito** (non due):

| Stato Event PT | Effetto sul credito | Note |
|----------------|--------------------|------|
| `Completato` | **consumato definitivo** — non torna mai | servizio reso, vale euro (asse EROGATO) |
| `Programmato` | **impegnato** — slot tenuto, reversibile | capacità prenotata, non servizio reso |
| `Rinviato` | **liberato** — il credito torna spendibile | l'atto di rinviare libera lo slot impegnato |
| `Cancellato` | **liberato** | già escluso oggi |

`Rinviato` e `Cancellato` hanno lo **stesso effetto aritmetico** sul pool crediti (entrambi
non occupano), ma restano **stati distinti** per tracciabilità ("rinviata, da riprogrammare"
≠ "cancellata, non avverrà"). Modello standard del settore (Mindbody/TrueCoach: *early cancel*
libera il credito; *no-show/late cancel* lo brucia — quest'ultimo fuori scope, §9).

**Decisioni founder 2026-06-26:**
- **D-AUTO-CLOSE:** un contratto saldato con **tutte** le sedute rinviate (zero `Completato`)
  **resta APERTO**. Conseguenza automatica del conteggio corretto: se le rinviate non contano come
  usate, `crediti_residui > 0`, quindi `contract_lifecycle` non diventa `ESAURITO` e
  `_sync_contract_chiuso` non chiude. **Non serve codice speciale** — *a condizione che TUTTI i
  produttori di `crediti_usati` siano corretti* (vedi `[Bridge Code]` §3.1: `rates.py:565` è uno di
  questi e la spec v1 lo aveva mancato).
- **D-MODELLO:** modello **semplice** — il rinvio libera **sempre** il credito (nessuna finestra
  di preavviso in questa iterazione; §9 per l'estensione futura).
- **D-GUARD:** una rinviata libera lo slot → si può **riprenotare** (il credit guard in
  `create_event` non deve più bloccare).

**Decisione §3-bis — RISOLTA `[Bridge Code 2026-06-26]` = CAMBIA:** `Rinviato` libera anche lo
**slot calendario** (`_check_overlap`), coerente con D-GUARD. Entra in T1.

---

## 2. Predicato canonico post-fix

Definizione operativa unica dell'**occupazione-credito**:

```
OCCUPAZIONE_CREDITO ⟺ Event.categoria == 'PT'
                   AND Event.deleted_at IS NULL
                   AND Event.stato IN ('Programmato', 'Completato')
```

Sostituisce, **sui soli siti dell'asse credito** (§3.1) e su `_check_overlap` (§3-bis), il predicato
attuale `Event.stato != 'Cancellato'` (che include erroneamente `Rinviato`).

Resa nei due idiomi presenti nel codice:
- SQLModel: `Event.stato.in_(["Programmato", "Completato"])`
- SQL raw: `e.stato IN ('Programmato', 'Completato')`

---

## 3. Inventario completo dei siti

Ancora di ricerca: `grep -rn "Cancellato" api/`. Ogni occorrenza va **classificata**, non
sostituita alla cieca.

### 3.1 — Siti da CAMBIARE (asse credito/occupazione)

| File:riga | Funzione | Asse |
|------|----------|------|
| `clients.py:309` (+ commento `:285`) | `_calc_credits_batch` (Query 2 `usage_rows`) | **credito — sito di Chiara (lista clienti)** |
| `agenda.py:282` | `_auto_assign_contract` (`usage_rows`) | credito (FIFO) |
| `agenda.py:317` | `_sync_contract_chiuso` (`crediti_usati`) | credito (auto-close credit-driven → D-AUTO-CLOSE) |
| `agenda.py:482` | `create_event` Bouncer 2c (credit guard) | credito (guard → D-GUARD) |
| `contracts.py:265` | `list_contracts` (`open_credit_rows`) | credito (lifecycle SOSPESO/ESAURITO) |
| `contracts.py:383` | `list_contracts` (`credit_rows` → `credits_used_map`) | credito (display lista) |
| `contracts.py:529` | `get_contract` (`chain_credits`) | credito (catena rinnovi) |
| `contracts.py:756` | `delete_contract` RESTRICT 2 | credito |
| `dashboard.py:388` | `get_expiring_contracts` (`credit_rows` raw SQL) | credito |
| `dashboard.py:542` | `_crediti_usati_map` | credito (lapsed/sospesi) |
| `dashboard.py:993` | `get_dashboard_alerts` (`expiring_rows` raw SQL) | credito |

**`[Bridge Code 2026-06-26]` — siti mancati dalla v1, da AGGIUNGERE a §3.1 (asse credito):**

| File:riga | Funzione | Perché era mancato / criticità |
|------|----------|-------------|
| 🔴 `rates.py:565` | `pay_rate` auto-close (`crediti_usati`) | **gemello payment-driven di `_sync_contract_chiuso`** (commento `agenda.py:307` lo documenta: "Simmetrico con auto-close in create_event e pay_rate"). Senza, un saldato all-rinviate **si auto-chiude COMPLETAMENTO al pagamento ultima rata → D-AUTO-CLOSE violata**. |
| 🔴 `workspace_engine.py:1247` | cockpit `COUNT(*) as usati` (raw SQL) | produttore `crediti_usati` indipendente, fuori dal contesto v1 |
| 🔴 `workspace_engine.py:1389` | cockpit `COUNT(*) as usati` (raw SQL) | idem |
| 🔴 `workspace_engine.py:2145` | `COUNT(*)` PT per contratto (raw SQL) | idem |
| 🟠 `client_avatar.py:430` | `credit_rows` crediti per contratto (avatar) | display crediti dell'avatar |

> La premessa della spec — "correggi §3.1 e `contract_state` eredita" — regge **solo** se l'elenco
> §3.1 include questi 5: `workspace_engine`/`rates`/`client_avatar` hanno produttori di `crediti_usati`
> propri, non derivati da `contract_state`. Lezione del progetto: *enumerazione manuale ≠ enforcement*.

### 3.2 — Sito con QUERY invariata ma COMPUTO da cambiare

| File:riga | Funzione | Cosa cambia |
|------|----------|-------------|
| `contracts.py:487` (query) + `:149` (somma) | `get_contract` (`credit_breakdown` GROUP BY) | La **query resta** (`:487` raggruppa per stato escludendo solo `Cancellato`: serve ancora il conteggio `Rinviato` per `sedute_rinviate` di display). Cambia **solo la somma** in `_to_response_with_rates` `:149`: `crediti_usati_computed = programmate + completate + rinviate` → **`programmate + completate`**. `[Bridge: verificato — `:175` deriva `crediti_residui` da questa somma]`. |

### 3.3 — Siti da NON toccare (NON sono asse credito) — esclusione esplicita / allowlist

Contengono `!= "Cancellato"` ma riguardano **attività/calendario/scheduling/recency**, non il credito.

| File:riga | Cosa | Perché resta |
|------|----------|--------------|
| `agenda.py:40` | `VALID_STATUSES` (costante) | set degli stati validi — `Rinviato` resta uno stato legittimo |
| `clients.py:399,546,746` | `last_event` / `recent_events` / MAX(data) | recency: una rinviata è comunque interazione reale |
| `clients.py:498` | dossier `next_scheduled_session` | scheduling display |
| `dashboard.py:135` | `todays_appointments` | conteggio calendario del giorno |
| `dashboard.py:823,842,846,1077` | inactive-clients / inactive_count | recency attività |
| `workspace_engine.py:302,686` | readiness upcoming / range eventi | attività/calendario |
| `workspace_engine.py:1611,1633,1637,2301` | lapsed recency / last_event | recency attività |
| `session_prep.py:188` | sessioni del giorno | calendario prep |
| `client_avatar.py:655` | cancellazioni 30d (`== Cancellato`) | predicato diverso, N/A |

**Borderline `[Bridge Code]` — LASCIA in T1 (non sono asse credito né denaro), eventuale raffinamento display futuro:**
- `clients.py:465` (`total_pt_sessions`, stat dossier "sedute PT totali") — display attività, non `crediti_residui`.
- `client_avatar.py:581,611` ("PT scheduled 30/60d", segnale di engagement) — forecast attività.
- `session_prep.py:227` (PT events per clienti nel prep) — contesto cockpit/calendario.

### 3-bis — `_check_overlap` (asse calendario) — RISOLTO = CAMBIA `[Bridge Code 2026-06-26]`

`agenda.py:198` (`_check_overlap`) usa `Event.stato != "Cancellato"`. Decisione founder = **CAMBIA**:
applicare il predicato canonico → una rinviata libera lo slot orario, un nuovo evento sullo stesso
orario **non** dà 409. Diventa parte di T1 (coerente con D-GUARD).

---

## 4. Convergenza codice ↔ commento

Il response schema documenta **già** il comportamento corretto, ma il codice no:

- `api/schemas/financial.py:404` → `crediti_residui` commento `# crediti_totali - programmate - completate`
  (già **senza** rinviate). `[Bridge: confermato]`
- `api/routers/contracts.py:149` → `crediti_usati_computed = programmate + completate + rinviate`
  (**con** rinviate). `[Bridge: confermato — è il bug]`

T1 fa convergere il **codice al commento** (non viceversa). Allineare anche il commento di
`clients.py:285` (`sedute_PT_usate: COUNT ... stato!='Cancellato'`).

---

## 5. Oracolo di non-regressione (asse denaro = INVARIANTE)

Prima di toccare codice, catturare lo stato monetario; dopo, diffare. **Qualsiasi delta = regressione.**

```bash
# PRIMA del fix — su crm.db reale, per ogni contratto aperto:
#   GET /contracts/{id}/settlement-preview   → salva JSON
#   GET /contracts (KPI: kpi_incassato, kpi_residuo)
#   per ogni contratto: netto_incassato, residuo
# DOPO il fix — ripetere e diffare.
```

Invarianti che **devono** reggere byte-identiche:
- `settlement-preview` (esito, importo_rimborso, quota_da_stornare, valore_servizio_reso,
  sedute_erogate) su **tutti** i contratti.
- `netto_incassato`, `residuo`, `kpi_incassato`, `kpi_residuo`, `kpi_da_pianificare`,
  `kpi_da_incassare_scaduto`.
- Riconciliazione ledger (`/dashboard/reconciliation`): nessun nuovo divergente.

Razionale strutturale `[Bridge: verificato]`: `compute_settlement` riceve `_count_sedute_erogate`
(`== 'Completato'`) e `residuo()` (prezzo/versato/quota_stornata). **Nessuno dei due legge
`!= 'Cancellato'`** → invarianza garantita per costruzione, non per fortuna.

---

## 6. Sezione "NON tocca" (anti-scope-creep)

T1 **non modifica**:
- `api/services/contract_settlement.py` — `compute_settlement`, `valore_servizio_reso`. La barriera
  strutturale EROGATO è intatta.
- La gamba RIMBORSO e la gamba STORNO di `terminate`, il tetto `totale_rimborsato ≤ totale_versato`,
  le àncore `totale_versato == Σ ENTRATA` / `totale_rimborsato == Σ RIMBORSO`.
- `_count_sedute_erogate` (`== 'Completato'`) e `_count_sedute_prenotate` (`== 'Programmato'`, display
  preview) — la **forfeiture delle prenotate** (ADR-016 §2) resta. Invariati.
- `api/services/contract_state.py` — **non si modifica, si nutre**. Riceve `crediti_usati` dal caller;
  correggendo i siti che lo *producono* (§3.1, **inclusi i 5 del bridge**), lifecycle/SOSPESO/ESAURITO
  ereditano automaticamente la definizione corretta. **Non aggiungere logica qui.**
- Qualsiasi importo in euro, `CashMovement`, `reopen`, `unpay_rate`, `update_rate`.
- Il **frontend** (legge dal backend, il numero si corregge da solo). La riconciliazione display
  lista/profilo = G7.7-R4/R5, blocco separato, fuori da T1.

---

## 7. Accertamento dati esistenti (read-only, NON modifica)

Al deploy i `crediti_residui` dei clienti con eventi `Rinviato` preesistenti **salgono** (è il fix che
si manifesta — §11). Caso insidioso: contratti **già auto-chiusi `COMPLETAMENTO`** la cui chiusura è
scattata solo perché le rinviate riempivano il monte-sedute → post-fix sarebbero `SOSPESO`. Query di
identificazione (decisione **umana** caso per caso, nessuna riapertura automatica):

```sql
SELECT c.id, c.crediti_totali,
       SUM(CASE WHEN e.stato='Completato' THEN 1 ELSE 0 END) AS completate,
       SUM(CASE WHEN e.stato='Programmato' THEN 1 ELSE 0 END) AS programmate,
       SUM(CASE WHEN e.stato='Rinviato'   THEN 1 ELSE 0 END) AS rinviate
FROM contratti c
LEFT JOIN agenda e
       ON e.id_contratto = c.id AND e.categoria='PT' AND e.deleted_at IS NULL
WHERE c.deleted_at IS NULL AND c.chiuso = 1 AND c.motivo_chiusura = 'COMPLETAMENTO'
GROUP BY c.id
HAVING (completate + programmate) < c.crediti_totali;
```

Per ciascuno: valutare `POST /contracts/{id}/reopen` (G7.4). Popolazione **distinta** dai 7 "muti"
`motivo NULL` dell'audit M4. Coordinare col runbook G7.6 (`RUNBOOK_REMEDIATION_CONTRATTI_MUTI.md`).

---

## 8. Criteri di accettazione

- **AC-1 (oracolo §5):** `settlement-preview` e tutti i KPI euro byte-identici pre/post su 35
  contratti. *Falsificabile: qualsiasi diff.*
- **AC-2 (conteggio):** contratto con `crediti_totali=N`, `C` Completate, `P` Programmate,
  `R` Rinviate (`R>0`) → `crediti_residui == N − C − P` in: lista clienti, dettaglio cliente,
  lista contratti (`crediti_usati == C+P`), dettaglio contratto (hero), **cockpit/worklist** (bridge).
- **AC-3 (D-AUTO-CLOSE):** contratto saldato, 0 Completate, N Rinviate → `chiuso=False`,
  `lifecycle != esaurito`. **Verificare su ENTRAMBI i rami: pagamento ultima rata (`pay_rate`) e
  modifica evento (`_sync`)** `[Bridge]`.
- **AC-4 (D-GUARD):** contratto con `N` sedute prenotate poi tutte rinviate → `POST /events`
  PT va a buon fine (no 400 "Crediti esauriti").
- **AC-5 (overlap, §3-bis = CAMBIA):** evento `Rinviato` su uno slot → un nuovo evento sullo stesso
  orario **non** dà 409.

---

## 9. Fuori scope (estensione futura, NON in T1)

**Finestra di preavviso + `NO_SHOW`** (modello Mindbody completo): rinvio entro soglia → credito torna
(early cancel); rinvio tardivo / no-show → credito bruciato (late cancel). Richiederebbe campo
data/ora di preavviso, policy per-trainer, e un **nuovo stato** `NO_SHOW` distinto da `Rinviato`.
Progettare l'enum stati Event perché `NO_SHOW` sia aggiunta **non distruttiva**. Per ora modello
**semplice** (D-MODELLO): rinvio libera sempre.

---

## 10. Governance — ADR-017 + grep-guard

**ADR-017 emenda ADR-016 §1** — `[Bridge Code]` status = **accepted** (2026-06-26, founder ha ratificato
modello di dominio + i 3 fork). ADR-016 §1 prende il pointer "emendato da ADR-017".

> OCCUPAZIONE-CREDITO = `Programmato + Completato` (**`Rinviato` escluso**). Il rinvio libera lo slot
> impegnato e restituisce il credito al pool spendibile. Asse EROGATO, barriera strutturale di
> `compute_settlement` e forfeiture delle prenotate (ADR-016 §2) **invariati**.

**Grep-guard** (`tools/scripts/check-all.sh`): il guard "euro-da-crediti" di ADR-016 difende l'asse
**denaro** → resta valido, T1 non lo tocca. Aggiungere un guard che impedisca il **ritorno** di
`!= 'Cancellato'` sui siti credito di §3.1 (allowlist per i siti calendario/attività di §3.3).

A implementazione: aggiornare `FINANCIAL_DOMAIN_MODEL.md` (definizione occupazione), `api/CLAUDE.md`,
`BUILD_LOG.md`.

---

## 11. Comunicazione a Chiara

Dopo il deploy i `crediti_residui` di alcuni clienti **aumentano**: è la correzione del rinvio, non un
errore. Le sedute rinviate tornano disponibili per riprogrammare. **Il calcolo dei rimborsi non cambia**
(quello era già corretto): si basa sulle sole sedute effettivamente svolte.

---

## 12. Sequencing

`[Bridge Code 2026-06-26]` — ordine deciso dal founder: **H1 (G7.7-R1) → G7.8 (questo) → resto G7.7**.

T1 è un blocco **isolato e rilasciabile** in un commit (una tesi falsificabile; cambio funzionale
validato contro l'oracolo settlement). Include il fix overlap §3-bis. La centralizzazione del predicato
in una costante condivisa, se desiderata, è un **commit separato** di hardening successivo (refactoring
puro). La riconciliazione display lista/profilo (G7.7-R4/R5) resta separata.
