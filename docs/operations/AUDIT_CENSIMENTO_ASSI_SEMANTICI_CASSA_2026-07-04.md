# AUDIT — Censimento assi semantici del dominio finanziario (S1) + interpreti della cassa (S2)

- **Data**: 2026-07-04
- **Trigger**: `INC-2026-07-03-falso-allarme-entrate-negative-cassa.md` (falso allarme entrate nette −140,42 €) + decisione founder: metodo "anticipare per struttura" (4 regole), perimetro finanziario
- **Natura**: READ-ONLY, code-grounded (grep + lettura mirata, ogni sito `file:riga`). Zero modifiche.
- **Scopo**: input diretto per (a) Addendum ADR-022 "read-model della cassa = gemello di lettura della penna", (b) sezione SPEC_G9 del gate read-model, (c) charter dell'agente `semantic-birth-auditor` (controlli S1-S5)
- **Definizioni**: *asse semantico* = dominio enumerabile di valori che determina il trattamento contabile; *interprete* = sito di lettura che decide il trattamento di un asse; *implicito* = interprete che branca su valori grezzi fuori dal modulo SSoT; *gemello di esaustività* = test che fallisce alla nascita di un membro senza trattamento dichiarato (≠ test di regressione, che protegge solo i membri già noti)

---

## 1. Tesi (confermata dal censimento)

Il dominio ha **un asse convergiuto al metodo completo** (occupazione credito: set chiuso + interprete unico + zero re-inline + test che vieta il re-inline) che dimostra che il metodo funziona, e **un asse critico a metà strada** (classificazione di lettura della cassa: costanti SSoT esistono, ma la *mappa categoria→classe contabile* vive inline, ripetuta e leggermente variata, in 7 superfici backend + 1 frontend). Il "piano dei conti" del sistema **esiste già de-facto** (6 classi, §4) ma nessuna funzione lo nomina: è ricostruibile solo leggendo tutte le superfici — esattamente ciò che è successo nell'INC.

---

## 2. S1 — Censimento assi

| # | Asse | Membri | SSoT modulo | Gemello di test | Verdetto |
|---|------|--------|-------------|-----------------|----------|
| A1 | `CashMovement.tipo` | ENTRATA · USCITA | nessuna costante (ORM + `MOVEMENT_TYPES` solo FE `types/api.ts:30`) | — | Binario, congelato da sempre: rischio basso. ~40 siti literal. `classify()` lo assorbe |
| A2 | Categoria **contrattuale** | ACCONTO_CONTRATTO · PAGAMENTO_RATA · INCASSO_CONGUAGLIO_CONTRATTO (IN) · RIMBORSO_CONTRATTO (OUT) | ✅ `cash_categories.py` (`CONTRACT_CASH_IN/OUT`, predicati, `signed_contractual_amount`) | ✅ `test_cash_categories.py` (semantica asse) · `test_g75_cash_alignment.py` (5 superfici) — **ma di regressione, non di esaustività** | Scrittura fail-loud via penna (G9.1 `ValueError`). Lettura: costanti consumate ✓ ma mappa di classe implicita nei siti |
| A3 | Categoria **rettifica spese** | STORNO_SPESA_FISSA | ⚠️ costante `CATEGORIA_STORNO_SPESA_FISSA` esiste ma **NON consumata** | esclusione testata in `test_financial_trend.py` (regressione) | **Literal grezzo in 6 siti**, di cui 2 in SCRITTURA (F3) |
| A4 | Categoria **spese libere** | testo libero (Affitto, Trasporto, SPESA_FISSA, …) | — asse dichiaratamente APERTO | — | ✅ Sano: mai usato per classificazione — la classe la dà la partizione strutturale (A5), non la stringa |
| A5 | **Partizione strutturale** | `id_contratto` / `id_rata` / `id_spesa_ricorrente` NULL-ness | documentata in TASSONOMIA §2 ("esaustiva per costruzione"); nel codice inline | — | ✅ Il pattern robusto già in uso (monthly_revenue, trend). Da NOMINARE dentro `classify()`, non da cambiare |
| A6 | Stato **Rate** | PENDENTE · PARZIALE · SALDATA | `VALID_RATE_STATUSES` (`schemas/financial.py:35`) — solo validazione | harness (indiretto) | ~25 siti literal (`!= "SALDATA"`, `in_(["PENDENTE","PARZIALE"])`), incluso `contract_state.py:182/191`. Set stabile: rischio medio-basso |
| A7 | `stato_pagamento` contratto | PENDENTE · PARZIALE · SALDATO | ✅ writer unico `recompute_stato_pagamento` (`contract_state.py:260`) | harness invarianti | Convergiuto lato scrittura (G8.2-prep de-dup 4 copie) |
| A8 | `motivo_chiusura` | COMPLETAMENTO · CONSUNZIONE · TERMINAZIONE_RIMBORSO · TERMINAZIONE_SALDO_TRAINER · (legacy: TERMINAZIONE_DECADENZA, NULL) | ✅ enum `MotivoChiusura` (`contract_settlement.py:26-28`) + FSM esplicita (`transitions.py:54-57`) | FSM coperta in transitions | Prefix-matching `startswith("TERMINAZIONE_")` (`contract_state.py:414`, `rates.py:648`) = **forward-guard dichiarato** (G7.2): un nuovo motivo di terminazione è auto-incluso by-design ✓ |
| A9 | Stato **crediti/wallet** (`crediti_terminazione` + `crediti_cliente`) | APERTO · SALDATO · ANNULLATO | ❌ **nessun modulo** — solo commenti nei modelli (`credito_terminazione.py:34`, `credito_cliente.py:34`) | harness (parziale) | **Literal in ~24 siti** su 6 file (clients, contracts, dashboard, transitions, contract_state via `getattr`, ledger) — asse condiviso da 2 tabelle senza costanti (F4) |
| A10 | **Occupazione credito** (Event) | Programmato · Completato · Cancellato_Tardivo · No_Show (credito) / Programmato · Completato (slot) | ✅ `STATI_OCCUPAZIONE_CREDITO/SLOT` (`contract_state.py:33/42`) | ✅ `test_occupazione_ssot.py` — **vieta il re-inline** | 🏆 **ASSE MODELLO**: 17 siti tutti via simbolo, esenzioni dichiarate (DISPLAY-EXEMPT), doppio asse esplicito. Il target a cui portare A2/A3 |

---

## 3. S2 — Inventario interpreti della cassa

### Backend (superfici di aggregazione)

| # | Superficie | Siti chiave | Classificazione fatta inline | Stato |
|---|-----------|-------------|------------------------------|-------|
| I1 | `get_movement_stats` (`movements.py:1110-1234`) | 1141-1172 (4 sommatorie), 1186-1216 (chart + doppia normalizzazione ribalta-segno) | storno (LITERAL) riduce fisse · rimborso (costante) contra-ricavo · fisse/variabili via A5 · **chart ri-bucketizza i negativi in silenzio** | ❌ implicito — l'interprete più ricco, origine dell'INC |
| I2 | `_compute_variable_burn_rate` (`movements.py:291-316`) | 302-311 | USCITA ∧ non-fissa ∧ non-rimborso = burn | ❌ implicito |
| I3 | `get_balance` (`movements.py:378-445`) + `_signed_importo` (`:67-70`) + saldo periodo (`:1061-1068`) | 395-421 | **cassa PURA**: nessun netting, somma per solo `tipo` | ⚠️ semantica corretta ma **non dichiarata** (F7): è l'altra "lingua" del falso allarme |
| I4 | `get_forecast` (`movements.py:1433-1606`) | 1513-1526 (burn proiezione), 1552-1565 (burn KPI) | 2 query gemelle: USCITA non-fissa non-rimborso | ❌ implicito (duplicazione interna) |
| I5 | `get_financial_trend` (`movements.py:1616-1780`) | 1670 (storno LITERAL), 1673 (partizione A5), 1681 (acconti/rate), 1707-1725 (contra-linea) | esclusione storno · partizione id_contratto · contra-linea rimborsi SEPARATA e additiva | 🏆 **modello di trasparenza**: unica superficie che espone lordo + contra + netto (`rimborsi_contratti`, `cash_flow_reale`) — BLOCKER-4 "nessun numero che sparisce" già rispettato |
| I6 | `dashboard.get_summary` → `monthly_revenue` (`dashboard.py:76-110`) | 87-110 | inflow per partizione A5 (✓ strutturale) − rimborsi per costante | ⚠️ semi-strutturale, netting senza esporre il lordo |
| I7 | `dashboard.get_reconciliation` (`dashboard.py:178-230`) + `ledger.project_columns_from_ledger` + `invariant_gate.py:48` | raw SQL CASE / SELECT con costante | ancore I5 (versato/rimborsato/stornato) | ✅ consumer del SSoT (sensori G9.0) |
| I8 | `recurring_expenses.py` chiusura/rettifica | :51 (signed case duplicato di `_signed_importo`), :357-373, :536-567 (logica storno), **:578/:592 storno LITERAL in SCRITTURA** | storno attivo/rimosso per cutoff | ❌ scrive la categoria-rettifica bypassando la costante: **la "penna" delle spese non esiste** (F3) |

### Frontend

| Superficie | Sito | Natura |
|-----------|------|--------|
| Card KPI "Entrate" (`cassa/page.tsx` `KpiCards`) | consuma `stats.totale_entrate` | ❌ mostra il **netto nudo** (trigger INC) — la response non le dà i componenti |
| `MovementsTable.tsx:93` | running balance a ritroso da `saldo_fine_periodo` | asse cassa-pura (solo `tipo`) — coerente con I3 |
| `ContractHistoryTab.tsx:84` | segno per timeline | display, solo `tipo` ✓ |
| `SplitLedgerView.tsx:66/71` | 2 query delegate al backend con param `tipo` | ✅ delega, zero ricalcolo |
| `AndamentoTab.tsx` | consuma trend (contra-linea inclusa) | ✅ delega |

---

## 4. Il piano dei conti implicito (ricostruito — oggi non ha nome nel codice)

Sei classi, definite da **partizione strutturale (A5) + categoria (A2/A3)**. Ogni superficie ne re-implementa un sottoinsieme:

| Classe | Predicato de-facto | Chi la usa |
|--------|--------------------|------------|
| `RICAVO_CONTRATTUALE` | ENTRATA ∧ `id_contratto≠NULL` | I1 I3 I5 I6 |
| `ALTRO_INCASSO` | ENTRATA ∧ `id_contratto=NULL` ∧ ≠storno | I1 I5 |
| `RETTIFICA_COSTO_FISSO` | ENTRATA ∧ `id_spesa≠NULL` ∧ =storno | I1 (riduce fisse) · I5/I6 (esclusa) |
| `CONTRA_RICAVO` | USCITA ∧ =RIMBORSO_CONTRATTO (con o senza `id_contratto`: include erogazione wallet) | I1 I2 I4 I5 I6 (4 trattamenti diversi ma coerenti) |
| `COSTO_FISSO` | USCITA ∧ `id_spesa≠NULL` | I1 I4 |
| `COSTO_VARIABILE` | USCITA ∧ `id_spesa=NULL` ∧ ≠rimborso | I1 I2 I4 |

**Il default silenzioso (cuore del problema):** una futura categoria ENTRATA cade in `RICAVO`/`ALTRO_INCASSO`, una USCITA in `COSTO_VARIABILE` — *per esclusione, senza rumore*. I test G7.5 sono gemelli di **regressione** (proteggono i membri noti sulle superfici note): non possono scattare alla **nascita** di un membro nuovo. Il gemello di esaustività non esiste per quest'asse.

---

## 5. Findings

| # | Severità | Finding | Evidenza |
|---|----------|---------|----------|
| F1 | **ALTA** | La mappa categoria→classe contabile non ha una funzione che la nomini: vive ripetuta in I1/I2/I4/I5/I6 con micro-varianti. Ogni categoria nuova = N revisioni manuali non enumerate (la "rincorsa") | §3, §4 |
| F2 | **ALTA** | Default silenzioso in lettura: categoria ignota classificata per esclusione. Asimmetria con la scrittura (penna fail-loud, `ledger.py:50/88`) | §4 |
| F3 | **MEDIA** | `CATEGORIA_STORNO_SPESA_FISSA` dichiarata nel SSoT ma mai consumata: literal in `movements.py:1143/1159/1191/1670` e — peggio — in **scrittura** `recurring_expenses.py:578/592`. Il flusso storno-spese non passa da alcuna penna | grep A3 |
| F4 | **MEDIA** | Asse A9 (APERTO/SALDATO/ANNULLATO, 2 tabelle) senza modulo costanti: ~24 siti literal in 6 file, incluso `contract_state.py:346/428` via `getattr` | grep A9 |
| F5 | **MEDIA** | `MovementStatsResponse` non espone i bucket (lordo/contra/rettifiche) → la card Entrate mostra il netto nudo. Trigger diretto dell'INC. Il modello già esiste in casa: I5 (financial-trend) | I1 vs I5 |
| F6 | BASSA | A6 (stato Rate): set di validazione esiste, letture a literal in ~25 siti. Stabile da sempre, ma fuori dal metodo | grep A6 |
| F7 | BASSA | I3 (`/balance`) usa la semantica "cassa pura" (nessun netting) — corretta per un saldo, ma non dichiarata. La coppia I3-lingua-cassa vs I1-lingua-economica è esattamente il bilinguismo non segnalato del falso allarme | §3 |
| F8 | INFO | Duplicazione: `_signed_importo` (`movements.py:67`) ≡ case inline (`recurring_expenses.py:51`); burn calcolato 3 volte (I2 + I4×2) con lo stesso predicato ricopiato | §3 |

**Conferme positive:** A10 dimostra il metodo end-to-end (è il target-shape) · A5 è la partizione esaustiva-per-costruzione da formalizzare, non da inventare · A8 ha il forward-guard giusto · I5 è la superficie-modello per la trasparenza · I7 (sensori G9.0) già consuma il SSoT.

---

## 6. Implicazioni operative (input per Addendum ADR-022 + SPEC_G9)

1. **`classify_cash_movement(m) → ClasseContabile`** in `cash_categories.py`: enum chiuso a 6 classi (§4), predicato = partizione strutturale A5 + categorie A2/A3. **Totale per costruzione** sulla partizione (tipo × FK-ness); **fail-loud** dove la categoria è vincolata dalla cella strutturale (es. USCITA con `id_contratto` che non è RIMBORSO → errore, non costo variabile). Il design fine (dove esattamente fallire vs default dichiarato) è materia della SPEC.
2. **Migrazione delle superfici** (ordine per rischio): I1 stats → I2 burn → I4 forecast → I6 monthly_revenue → I5 trend (già conforme nei numeri, adotta i simboli) → I8 recurring (consumo costante storno, lato R e W). I3 resta cassa-pura ma la dichiara (docstring + campo `semantica: "cassa"` se si vuole). Behavior-preserving: i numeri di oggi sono giusti — cambia chi li interpreta.
3. **Gemello di esaustività**: test che enumeri le categorie note (costanti + eventuale scan dei valori distinti nel DB di test) e asserisca che `classify()` assegna una e una sola classe, e che le superfici consumino `classify()` (pattern `test_occupazione_ssot.py`: vietato il re-inline). Sostituisce/assorbe i grep-guard di area cassa in G9.4, coerente con D-INVARIANTI-IMPOSTI.
4. **Trasparenza**: `MovementStatsResponse` espone `entrate_lorde`, `rimborsi_contratti`, `storno_fisse` (F5) — la card Entrate mostra il sub-label. Diventa un sottoprodotto della classificazione, non un cerotto.
5. **Quick-win indipendenti dal gate** (possono viaggiare da soli): F3 (consumare `CATEGORIA_STORNO_SPESA_FISSA` nei 6 siti) · F4 (modulo costanti stati credito, es. in `credito_terminazione.py` condiviso, o `contract_state`) · F8 (de-dup signed case).
6. **Charter agente `semantic-birth-auditor`**: i controlli S1/S2 di questo audit diventano i suoi controlli permanenti; S3 (totalità sul diff), S4 (netto nudo), S5 (rito di nascita: membro nuovo senza SPEC/ADR/learning). Metrica di successo: findings in calo; ogni finding confermato si converte in struttura (registrazione + test), mai in babysitting.
