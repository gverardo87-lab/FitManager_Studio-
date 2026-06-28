# SPEC_INTEGRITA_CONTABILE_E_WALLET

**Tipo:** specifica prescrittiva (cosa-deve-essere-vero; silente sul come). Bridge Chat->Code.  
**Data:** 2026-06-28 · **Branch:** `FitManager_Studio`  
**Stato:** ✅ **G8.1 IMPLEMENTATA** (2026-06-28; commit `f84d345`→`a51d180`). ✅ **G8.1.1 IMPLEMENTATA** (2026-06-28; reconciliation + transparency, §14/§14.6): F2 reopen riallinea le rate al residuo · F3/F4 cap/`stato_pagamento` net-aware (`is_saldato()`) · F1/F5 storico cassa unificato sul dettaglio (tab "Storico", saldo progressivo) · F6 storico stato `GET /{id}/history` (eventi curati da `audit_log`, dedup companion). Suite **691** verde, ruff + grep-guard ADR-019 + next build verdi. G8.2 (wallet auto-spendibile cross-contratto) su domanda. · ratificata da **ADR-019** + **ADR-020**  
**Blocco proposto:** **G8** (programma post-G7 "integrita' contabile + completamento bilaterale"). **Fetta 1 = G8.1** (reopen non-distruttivo + residuo net-aware + wallet lean + rimborso editabile + UX-propone). **Fetta 2 = G8.2** (wallet auto-spendibile cross-contratto). G1 in stand-by.  
**Mappa di verita:** `docs/adr/ADR-019-libro-mastro-non-distruttivo-reopen-ricalcola.md` · `docs/adr/ADR-020-wallet-cliente-customer-credit-balance.md` · `docs/operations/AUDIT_REOPEN_SCENARIOS_2026-06-28.md` · `docs/technical/FINANCIAL_DOMAIN_MODEL.md` · `api/services/contract_state.py` · `api/routers/contracts.py`

## Impact map

- **Obiettivo:** rendere `reopen` **non-distruttivo e scenario-aware** (la cassa mossa non si tocca; si ricalcola), completare la **simmetria bilaterale** lato cliente (rimborso editabile + wallet), e non perdere mai un credito del cliente.
- **Layer toccati (G8.1):** backend primario (`contract_state.residuo()`, `contracts.py` terminate/reopen + nuovi endpoint wallet, nuova entita' `crediti_cliente`, schema, audit, predicati cassa, test); frontend consumer (dialog reopen full-impact + propone, dialog rimborso editabile, worklist wallet, dialog eroga-rimborso, tipi, hook).
- **Invarianti da preservare:** asse EROGATO (ADR-016); `Rinviato` fuori occupazione (ADR-017); Strada B (`totale_versato` lordo immutabile, `netto_incassato` derivato); `residuo == 0 ⟺ saldato`; **la cassa mossa non si cancella mai** (integrita' di periodo/fiscale); le ancore `totale_versato == Σ ENTRATA` e `totale_rimborsato == Σ USCITA RIMBORSO`.

**Tesi falsificabile:** dopo G8.1, **nessun `reopen` cancella un `CashMovement`**. `reopen` lascia ferme le scritture, azzera lo storno, annulla i ledger di credito (receivable trainer + wallet cliente) di quella terminazione, ripristina le rate marcate, e il `residuo` (net-aware) si ricalcola **corretto** rispetto alla cassa reale. Un terminate `INCASSA_ORA` (incasso reale) riaperto **non fa sparire** quell'incasso: resta, e diventa pagamento sul contratto. Un rimborso lato cliente puo' essere **parziale o zero**, e il non-rimborsato vive in un **wallet** che non si perde.

---

## 0. Problema reale da correggere

1. **`reopen` e' distruttivo e cieco** (`AUDIT_REOPEN_SCENARIOS`): soft-cancella i `CashMovement` di terminazione (gambe C/C-bis), **scavalcando** la protezione del mastro (`delete_movement` vieta — 400 — di eliminare un movimento con `id_contratto`), mutando periodi dichiarati e facendo **sparire reddito reale incassato**. Un solo trattamento per scenari diversi (S1–S7).
2. **Il rimborso lato cliente e' rigido**: `terminate` ramo `CREDITO_CLIENTE` forza rimborso pieno, contanti, subito. Niente parziale/differito.
3. **`residuo` perde gli overpayment**: il clamp `max(...,0)` scarta in silenzio un eventuale credito del cliente; e usa il versato **lordo**, sbagliando appena un rimborso "resta" su un contratto riaperto.

---

## 1. Cio che NON cambia

- **EROGATO canonico** (ADR-016), **`Rinviato` fuori occupazione** (ADR-017), **terminazione bilaterale** (ADR-018): il calcolo del conguaglio resta intatto.
- **Strada B**: `totale_versato` lordo, `totale_rimborsato` separato, `netto_incassato()` derivato.
- **`residuo == 0 ⟺ saldato`**; terminate atomico; `crediti_terminazione` (receivable trainer, G7.10) resta com'e'.
- **Le ancore di riconciliazione** `totale_versato == Σ ENTRATA` e `totale_rimborsato == Σ USCITA RIMBORSO` (anzi, reggono **meglio**: reopen non cancella piu' nulla).

---

## 2. Il principio (ADR-019)

La posizione di un cliente su un contratto e' **sempre** una di due:
- **DEBITO** (il cliente deve ancora) -> vive **dentro il contratto** (`residuo`). Si ricalcola.
- **CREDITO** (qualcuno e' in credito) -> vive in un **ledger**: **wallet** lato cliente (`crediti_cliente`), **receivable** lato trainer (`crediti_terminazione`).

Regola d'oro: **la cassa mossa non si tocca mai.** `terminate` e `reopen` **ricalcolano e instradano** (debito->contratto, credito->ledger), non spostano denaro a ritroso.

---

## 3. `residuo` net-aware (SSoT)

`api/services/contract_state.py::residuo()` cambia da lordo a **netto**:

```text
residuo = round(max(prezzo_totale − netto_incassato − quota_stornata, 0.0), 2)
   con   netto_incassato = max(totale_versato − totale_rimborsato, 0)
```

(oggi: `prezzo − totale_versato − quota_stornata`). **Backward-compatible**: con `totale_rimborsato == 0` (ovunque oggi tranne i terminati) e' **byte-identica**. Cambia solo dove un rimborso "resta" su un contratto **aperto** (possibile solo dopo `reopen`, §4): li' il residuo deve includere il rimborso (il cliente ha riavuto denaro -> deve di piu'). E' l'unico punto SSoT toccato; ~15 consumer ne ereditano la correzione.

---

## 4. `reopen` ricalcola-e-instrada (G8.1)

`reopen` **non cancella** scritture di cassa. Le gambe diventano:

- **R1 — Cassa IMMUTABILE.** NON soft-cancella i `CashMovement` USCITA `RIMBORSO_CONTRATTO` ne' ENTRATA `INCASSO_CONGUAGLIO_CONTRATTO`. **`totale_versato` e `totale_rimborsato` NON si decrementano.** Le gambe C e C-bis attuali (delete) **spariscono**.
- **R2 — Storno inverso.** `quota_stornata = 0`.
- **R3 — Receivable trainer.** `crediti_terminazione` del contratto -> `ANNULLATO` (gia' fa C-ter; resta, e' non-cash). L'eventuale incasso parziale gia' registrato **resta** (R1) -> e' un pagamento.
- **R4 — Wallet cliente (NEW).** `crediti_cliente` (credito a wallet creato da QUESTA terminazione) -> `ANNULLATO`. L'eventuale erogazione parziale gia' fatta (USCITA) **resta** (R1). Il credito differito si riassorbe nel contratto.
- **R5 — Rate.** Ripristino delle sole rate marcate `chiusa_da_terminazione` (invariato).
- **R6 — Stato.** `chiuso=False`, `motivo_chiusura=None`, `data_chiusura=None`.
- **R7 — Residuo.** Ricalcolato **automaticamente** dal SSoT net-aware (§3): `residuo = P − netto − 0`. La cassa che resta (rimborso uscito, conguaglio incassato) e' gia' dentro `netto`.
- **R8 — Classifica + propone (S5).** Se esiste un **rinnovo figlio** vivo (`rinnovo_di == id` AND `chiuso==False` AND non eliminato), `reopen-preview` lo **segnala** e il FE **propone** (avviso esplicito, conferma richiesta). S4 (wallet speso) non si presenta in G8.1 (il wallet non e' ancora spendibile su contratti -> G8.2).

**Conseguenza:** un terminate con incasso/rimborso reale, riaperto, **conserva** quelle scritture; il `residuo` ricalcolato e' corretto; nessun reddito sparisce; integrita' di periodo automatica.

### 4.1 `GET /contracts/{id}/reopen-preview` (NEW, dry-run)

Ritorna l'impatto pieno **prima** della conferma (gemello di `settlement-preview`): `residuo_dopo` (ricalcolato), `rimborso_che_resta`, `incasso_che_resta`, `rate_da_ripristinare`, `receivable_da_annullare`, `wallet_da_annullare`, `ha_rinnovo_vivo` (+ id), `messaggio`. **Zero scritture.**

---

## 5. Rimborso editabile + wallet (G8.1)

`terminate` ramo `CREDITO_CLIENTE` diventa **simmetrico** al ramo trainer:

- **Importo rimborso EDITABILE** `X ∈ [0, credito_cliente]` (default `credito_cliente`). `metodo_rimborso` obbligatorio **solo se `X > 0`**.
- Il **non rimborsato** `(credito_cliente − X)`, se `> 0.009`, diventa un **credito a wallet** del cliente (`crediti_cliente`, causale `RIMBORSO_DIFFERITO`).
- **Niente "rinuncia" lato cliente** (asimmetria corretta, ADR-020): il trainer non puo' abbuonare denaro che deve al cliente. Le due gambe lato cliente sono: rimborsa `X` (cassa) + metti a wallet il resto.
- **Storno** invariato: `quota_stornata += residuo_pre` (la quota non-erogata resta stornata; il credito cliente e' un fatto separato, fuori dal residuo).
- **Post-invariante:** `residuo == 0`; movimento USCITA solo se `X > 0`; `crediti_cliente` creato solo se `(credito_cliente − X) > 0.009`.

### 5.1 Formule (ramo CREDITO_CLIENTE, ADR-020)

```text
X = importo_rimborso scelto ∈ [0, credito_cliente]   (default credito_cliente)
USCITA RIMBORSO_CONTRATTO di importo X   (solo se X>0; metodo obbligatorio)
totale_rimborsato += X
wallet_credit = round(credito_cliente − X, 2)   (-> crediti_cliente APERTO se >0.009)
quota_stornata += residuo_pre
Post: residuo == 0; netto_incassato == versato − X; il cliente e' "owed" wallet_credit (fuori da residuo)
```

---

## 6. Wallet del cliente — entita' + operazioni (G8.1, lean)

### 6.1 Entita' `crediti_cliente` (tabella nuova, additiva via `create_db_and_tables`)

Campi: `id`, `trainer_id` (FK), `id_cliente` (FK), `importo` (credito a favore del cliente), `importo_erogato` (default 0, ≤ importo), `stato` (`APERTO`/`SALDATO`/`ANNULLATO`), `causale` (`RIMBORSO_DIFFERITO` | `OVERPAYMENT`), `id_contratto_origine` (FK, da quale terminazione nasce), `data_creazione`, `data_chiusura?`, `deleted_at?`. **Residuo del credito** = `importo − importo_erogato` (derivato). **Distinto** da `crediti_terminazione` (receivable trainer). Migrazione Alembic = record formale.

### 6.2 Operazioni G8.1 (manuali, "applicato a mano")

- **`GET /dashboard/rimborsi-da-erogare`** — worklist dei `crediti_cliente` `APERTO` (gemella di `crediti-da-incassare`): cliente, residuo, aging, contratto d'origine.
- **`POST /clients/{id}/crediti/{credito_id}/eroga`** — eroga (anche parziale) il credito in **cassa**: `USCITA RIMBORSO_CONTRATTO` (importo ≤ residuo del credito, 422 oltre) + `importo_erogato +=`; a saldo -> `SALDATO`. Atomico, bouncer ownership.
- **`GET /clients/{id}/crediti`** — lista crediti del cliente (per il profilo).
- **Reopen (R4)** annulla i `crediti_cliente` della terminazione riaperta (con erogazioni parziali che restano, R1).

> **NON in G8.1:** applicare il credito a un **contratto futuro** (acconto/sconto) -> G8.2 (§11). La causale `OVERPAYMENT` e' predisposta ma in G8.1 non c'e' sorgente attiva di overpayment (i guard di pagamento lo prevengono); il campo esiste per non perdere il caso quando emergera'.

---

## 7. Frontend (G8.1)

- **`ReopenContractDialog`**: da avviso parziale a **impatto pieno** dal `reopen-preview` — mostra residuo-dopo + le scritture che **restano** (non "annullate") + rate + ledger annullati; se `ha_rinnovo_vivo` -> avviso esplicito + conferma. Zero calcolo client.
- **`TerminateContractDialog`** ramo cliente: importo rimborso **editabile** `[0, credito_cliente]` (default pieno) + metodo (solo se >0) + microcopy "il non rimborsato resta come credito del cliente".
- **Worklist "Rimborsi da erogare"** su `/rinnovi-incassi` (gemella di `CreditiDaIncassareCard`) + **`EroghaRimborsoDialog`** (gemello di `IncassaCreditoDialog`).
- **Profilo cliente**: badge/sezione "Credito wallet: €X" (sola lettura) con link alla worklist.

---

## 8. Perimetro backend (G8.1)

- `api/services/contract_state.py` — `residuo()` net-aware (§3).
- `api/models/credito_cliente.py` — nuova entita' + registrazione in `models/__init__.py` + migrazione.
- `api/routers/contracts.py` — `reopen` ricalcola (R1–R8, niente delete cassa); `reopen-preview`; `terminate` ramo cliente editabile + crea `crediti_cliente`.
- `api/routers/clients.py` (o `contracts.py`) — `eroga` + `list crediti`.
- `api/routers/dashboard.py` — worklist `rimborsi-da-erogare`.
- `api/schemas/financial.py` — `ContractTerminate` (+`importo_rimborso` editabile, validato `≤ credito_cliente`); `ReopenPreview`; `CreditoClienteResponse`.
- `api/routers/_audit.py` — payload reopen (cosa resta / cosa si annulla) + erogazione.
- `tools/scripts/check-all.sh` — grep-guard: `reopen` non deve contenere `deleted_at = now` su `CashMovement` (anti-ritorno alla cancellazione della cassa).

---

## 9. Test di accettazione (G8.1)

### 9.1 residuo net-aware
1. `residuo()` con `rimborsato=0` -> byte-identico al lordo (griglia di contratti esistenti).
2. `residuo()` con un rimborso che resta (`rimborsato>0`, contratto aperto) -> `P − (versato−rimborsato) − storno`.

### 9.2 reopen non-distruttivo
3. reopen dopo `INCASSA_ORA` (incasso €300): il `CashMovement` ENTRATA **NON e' soft-deleted** (ancora attivo); `totale_versato` **invariato**; `residuo` ricalcolato = `P − netto`; `quota_stornata=0`.
4. reopen dopo rimborso (€500 USCITA): il movimento USCITA **resta**; `totale_rimborsato` invariato; `residuo = P − (versato−500)`.
5. reopen dopo `A_CREDITO` con incasso parziale: l'ENTRATA parziale **resta**; il receivable -> `ANNULLATO`; `residuo` ricalcolato.
6. reopen dopo rimborso-differito (wallet): il `crediti_cliente` -> `ANNULLATO`; l'eventuale erogazione parziale (USCITA) resta; `residuo` ricalcolato.
7. **Ancore**: dopo ogni reopen, `totale_versato == Σ ENTRATA` e `totale_rimborsato == Σ USCITA RIMBORSO` (nessuna cancellazione).
8. reopen con **rinnovo vivo**: `reopen-preview.ha_rinnovo_vivo == True` (+ id); reopen procede solo con conferma esplicita (il blocco non e' silenzioso ne' automatico).

### 9.3 rimborso editabile + wallet
9. terminate `CREDITO_CLIENTE` con `X = credito_cliente` (pieno): USCITA piena, nessun `crediti_cliente`, `residuo==0`, `netto==R`.
10. terminate con `X` parziale: USCITA `X`, `crediti_cliente` APERTO di `credito_cliente − X`, `residuo==0`.
11. terminate con `X = 0`: nessuna USCITA (metodo non richiesto), `crediti_cliente` = `credito_cliente`, `residuo==0`.
12. terminate con `X > credito_cliente` -> **422**.
13. `eroga` parziale -> USCITA, `importo_erogato +=`, stato APERTO; a saldo -> `SALDATO`; oltre il residuo -> **422**.
14. worklist `rimborsi-da-erogare` elenca i `crediti_cliente` APERTO; esce a SALDATO/ANNULLATO.

### 9.4 regressioni
15. La suite G7.3/G7.4/G7.9/G7.10 viene **migrata** (i test reopen "movimenti spariti" diventano "movimenti fermi + residuo ricalcolato"), non semplicemente cancellata.
16. Aggregati cassa coerenti (nessuna nuova categoria di esclusione: la cassa non viene piu' toccata da reopen -> meno superficie, non piu').

---

## 10. Sequenza di implementazione (G8.1)

**Step 1 — `residuo` net-aware (SSoT).** Cambio `contract_state.residuo()` + AC 1/2 + verifica byte-identicita' sulla suite esistente. **Gate:** suite verde, byte-identica dove `rimborsato=0`.

**Step 2 — reopen ricalcola.** Rimuovo le gambe delete (C/C-bis); reopen = R2–R7; `reopen-preview` + R8 (rinnovo). Migro i test reopen. **Gate:** AC 3–8 + ancore.

**Step 3 — rimborso editabile + entita' wallet.** `crediti_cliente` + migrazione; `terminate` ramo cliente editabile + crea wallet credit; R4 in reopen. **Gate:** AC 9–12.

**Step 4 — worklist + eroga.** `rimborsi-da-erogare` + `eroga` + `list crediti`. **Gate:** AC 13–14.

**Step 5 — frontend.** reopen full-impact + propone; terminate cliente editabile; worklist + EroghaRimborsoDialog; profilo wallet. **Gate:** `next build`.

**Step 6 — quality gate.** suite + `ruff` + `next build` + grep-guard; aggiorno FDM/api-CLAUDE/BUILD_LOG.

---

## 11. Fetta 2 — wallet auto-spendibile cross-contratto (G8.2, su domanda)

Scope (NON in G8.1): applicare un credito `crediti_cliente` come **acconto/sconto su un contratto futuro** (creazione/rinnovo) -> debit del wallet (causale `APPLICATO_CONTRATTO`, link `id_contratto_uso`). Introduce **consistenza di stato distribuito** (scenario S4: reopen di un contratto il cui wallet e' stato speso su un altro -> `reopen-preview` lo rileva e **propone** la gestione). Si apre con un blocco dedicato quando c'e' domanda reale; G8.1 lascia il credito **tracciato, erogabile in cassa, e visibile**.

---

## 12. Fuori scope (G8.1 e G8.2)

- Layer documentale fiscale (fattura / nota di credito): il `CashMovement` resta il dato fiscale; G8 garantisce solo che non venga **mai cancellato**.
- "Rinuncia del cliente al proprio credito" (azione esplicita lato cliente): futura.
- Scritture compensative per la correzione **diretta** di un movimento errato: concern separato (G8 risolve `reopen` col ricalcolo, non con le compensative).
- Auto-cancellazione di un rinnovo da `reopen`: G8.1 **propone**, non agisce; l'azione resta manuale.

---

## 13. Definizione di fatto

**G8.1** e' finito quando:
1. nessun `reopen` cancella un `CashMovement` (grep-guard + AC 3–7);
2. `residuo` e' net-aware e byte-identico dove `rimborsato=0`;
3. il rimborso lato cliente e' editabile `[0, credito_cliente]` e il non-rimborsato vive in `crediti_cliente`;
4. il wallet e' tracciato, **erogabile in cassa** (worklist + eroga) e visibile sul profilo;
5. reopen propone (non agisce) su rinnovo vivo;
6. le ancore reggono; la suite (migrata) e i quality gate passano.

**G8.2** e' finito quando il credito wallet e' applicabile a un contratto futuro, con `reopen-preview` che rileva e propone la dipendenza a valle (S4).

---

## 14. G8.1.1 — reopen reconciliation + transparency (follow-up audit, 2026-06-28)

**Origine:** test del flusso da parte del founder dopo G8.1 shippato. Il **calcolo** del residuo
net-aware è corretto, ma il **contorno** (presentazione movimenti + piano rate + guard cap/stato) non si
è allineato. **Emerge SOLO quando della cassa resta** dopo reopen (rimborso o conguaglio incassato); il
reopen di una terminazione senza cassa (rinuncia / storno puro) ripristina tutto correttamente. Ratifica:
**ADR-019 Addendum 2026-06-28**. È **hardening** (completamento del recepimento del principio), non nuovo blocco.

### 14.1 Findings (code-grounded)

- **F1 — movimenti contratto invisibili sul dettaglio [HIGH, trasparenza].** `get_contract` costruisce
  `receipt_map` solo dai `CashMovement` con `id_rata` set → acconto, rimborso (`RIMBORSO_CONTRATTO`),
  conguaglio (`INCASSO_CONGUAGLIO_CONTRATTO`) — tutti `id_rata=None` — non compaiono. Il `residuo`
  net-aware "non torna" dai pagamenti visibili.
- **F2 — rate restaurate ≠ nuovo residuo [HIGH, correttezza/UX].** `reopen` R5 ripristina le rate
  `chiusa_da_terminazione` AS-IS (dimensionate al residuo PRE-terminate). Con cassa che resta, residuo
  ricalcolato ≠ pre-terminate → conguaglio: rate > residuo → `pay_rate` blocca l'ultima rata (422);
  rimborso: rate < residuo → buco. (L'inverso-esatto M1/G7.7 assumeva reopen = inverso esatto.)
- **F3 — `_cap_rateizzabile` non net-aware [MED-HIGH, consistenza].** `cap = prezzo − (totale_versato −
  saldato) − quota` usa il LORDO. Dopo reopen-rimborso, `pay_rate` (net, delega `residuo()`) permette di
  pagare il residuo pieno ma create/update_rate (lordo) non permette di **pianificarlo** → i due guard si
  contraddicono di `totale_rimborsato`.
- **F4 — `stato_pagamento`/auto-close LORDO [MED-HIGH, può violare `residuo==0` su CHIUSO].** `SALDATO se
  totale_versato ≥ prezzo`. Dopo reopen-rimborso, ri-incassando, `versato` tocca `prezzo` mentre
  `residuo()` net > 0 → SALDATO + eventuale auto-close prematuro con residuo ≠ 0.

**Sani (già net-aware):** `pay_rate` B-ter e `generate_payment_plan` delegano a `cstate.residuo()`.

### 14.2 Decisioni

- **F1 (D-CASSA-VISIBILE):** il dettaglio espone uno **storico movimenti del contratto** (tutti i
  `CashMovement` con `id_contratto`, ENTRATA+USCITA, cronologico) — backend nel response + FE timeline.
- **F2 (D-RECONCILIA-RATE) — riallineo AUTOMATICO (founder):** `reopen`, dopo aver ripristinato le rate e
  ricalcolato il residuo, **riconcilia il piano**: se Σ residui-rata > `residuo()` taglia cronologicamente
  (l'ultima rata a cavallo ridotta a coprire l'esatto residuo; le successive con `importo_saldato==0` →
  soft-delete, con `importo_saldato>0` → `importo_previsto=importo_saldato` = SALDATA, **mai sotto il
  saldato**); se Σ < `residuo()`, lascia il resto "da pianificare" (nessuna rata-fantasma). Nessun banner:
  il piano esce già coerente.
- **F3 (D-NET-AWARE):** `_cap_rateizzabile` usa `cstate.netto_incassato(contract)` al posto di
  `totale_versato`. Backward-compat (`rimborsato=0` → byte-identico).
- **F4 (D-NET-AWARE):** `stato_pagamento = SALDATO ⟺ cstate.residuo(contract) ≤ 0.01` (non `versato ≥
  prezzo`). Backward-compat. L'auto-close resta `SALDATO AND crediti esauriti`.

### 14.3 Test di accettazione (G8.1.1)

1. **F1:** dopo reopen-con-rimborso, `GET /contracts/{id}` espone i movimenti contratto (acconto +
   rimborso USCITA + eventuale conguaglio ENTRATA) con importo/segno/data; Σ riconcilia con `netto_incassato`.
2. **F2-over:** terminato con conguaglio incassato (residuo ricalcolato < Σ rate restaurate) → reopen → Σ
   residui-rata == `residuo()`; l'ultima a cavallo ridotta; le eccedenti soft-deleted; una PARZIALE
   eccedente diventa SALDATA (mai sotto `importo_saldato`).
3. **F2-under:** terminato con rimborso (residuo ricalcolato > Σ rate) → reopen → rate invariate,
   `residuo() − Σ` resta "da pianificare" (`money_substate` PARZIALE/DA_PIANIFICARE).
4. **F2-no-cash:** reopen di rinuncia/storno-puro (residuo == pre-terminate) → rate ripristinate identiche,
   nessuna riconciliazione (il round-trip resta esatto dove non c'è cassa).
5. **F3:** dopo reopen-rimborso, `_cap_rateizzabile` consente di pianificare fino a `residuo()` net (non si
   ferma a `prezzo − versato`); byte-identico con `rimborsato=0`.
6. **F4:** dopo reopen-rimborso, collezionando via rate fino a `versato == prezzo` ma `residuo() > 0`,
   `stato_pagamento` NON è SALDATO e l'auto-close NON scatta; SALDATO solo a `residuo() == 0`.

### 14.4 Perimetro

- `api/routers/contracts.py` — `reopen` (R5 + riconciliazione rate F2); `get_contract` /
  `_to_response_with_rates` + schema `financial.py` (movimenti contratto F1).
- `api/routers/rates.py` — `_cap_rateizzabile` net-aware (F3); `stato_pagamento` net-aware (F4, + siti
  gemelli `unpay_rate`/`update_rate` se condividono la condizione lordo).
- `api/services/contract_state.py` — eventuale helper `is_saldato(contract)` (SSoT della condizione F4).
- Frontend — sezione "Movimenti del contratto" sul dettaglio (F1); il piano rate riflette già il riallineo
  (F2, nessun nuovo componente).
- Test: `tests/test_contract_reopen.py` (F2 over/under/no-cash) + `test_rate_guards.py` (F3/F4) +
  integrazione (F1).

### 14.5 Sequenza

(1) governance [questo §14 + ADR-019 Addendum + FDM] → (2) F3+F4 net-aware (SSoT, piccoli) → (3) F2
reopen-reconcile + test scenari → (4) **F1+F5** (storico cassa unificato, backend+FE) + **F6** (storico
stato, `GET /{id}/history` + FE) → (5) gate (suite + check-all + next build) + verifica Playwright.

### 14.6 F5/F6 — storico cassa unificato + storico stato (CRM-grade, follow-up founder 2026-06-28)

Il lato FRONTEND di F1 era sotto-specificato ("una sezione") e mancava lo **storico di stato**. Entrambi
si appoggiano a dati **già registrati** (CashMovement `id_contratto`; `audit_log` `entity_type='contract'`
con `created_at` + `changes` JSON, già scritto da `log_contract_lifecycle_transition` + payload terminate)
→ gap di *surfacing*, non di modello.

**F5 — Storico cassa del contratto, unificato [HIGH, trasparenza/CRM].**
- Oggi il dettaglio mostra solo i pagamenti per-rata (`receipt_map` `id_rata`-linked); acconto, rimborso,
  conguaglio (`id_rata=None`) invisibili.
- **Decisione:** il backend (F1 esteso) espone TUTTI i `CashMovement` del contratto (`id_contratto` set,
  ENTRATA+USCITA, cronologico) con `tipo`/`categoria`/`importo`/`data_effettiva`/`metodo`/`id_rata`. Il FE
  rende una **timeline cassa unificata**: causale (Acconto · Pagamento rata · **Rimborso** − · **Conguaglio**
  +) con icona/colore, segno ±, **saldo netto progressivo** (versato−rimborsato), footer di riconciliazione
  `Versato lordo €X − Rimborsato €Y = Netto €Z · Residuo €R`. Fa quadrare il residuo a vista.
- **Confine di modello:** l'erogazione wallet (`id_contratto=None`, cassa a livello CLIENTE) NON entra in
  questa timeline → vive nella sezione wallet del profilo (coerente con Step 4 / ADR-020).

**F6 — Storico stato/lifecycle del contratto (activity timeline) [MED-HIGH, CRM-grade].**
- Oggi nessuna vista dello storico stato, benché l'`audit_log` lo registri (CREATE; transizioni `chiuso`
  con motivo+rimborso+residuo_annullato+data; transizioni lifecycle aperto ATTIVO/SOSPESO/ESAURITO; update).
- **Decisione (eventi CURATI, default founder):** nuovo `GET /contracts/{id}/history` (read-only, bouncer)
  che parsa l'`audit_log` del contratto in **eventi leggibili curati** — Creato · Terminato (esito + rimborso
  + motivo) · Riaperto · Saldato (auto-close completamento) · Scadenza modificata — ordinati per `created_at`.
  L'audit grezzo completo resta in `/movements/audit-log`. Il FE rende una **timeline attività** sul dettaglio.

**AC (F5/F6):**
7. **F5:** dopo reopen-con-rimborso, il dettaglio espone i movimenti contratto (acconto + rimborso USCITA +
   eventuale conguaglio ENTRATA) con segno/data/causale; Σ con segno == `netto_incassato`.
8. **F5-confine:** un'erogazione wallet (`id_contratto=None`) NON compare nella timeline del contratto.
9. **F6:** un contratto terminato-poi-riaperto espone in `/history` gli eventi in ordine: Creato → Terminato
   (con esito+importo+motivo) → Riaperto; un auto-close COMPLETAMENTO appare come "Saldato".
10. **F6-tenant:** `/history` è multi-tenant (404 su contratto altrui), zero scritture.

**Perimetro aggiuntivo:** `contracts.py` (`get_contract`/response F1+F5 · nuovo `GET /{id}/history` F6) +
`schemas/financial.py` (`ContractMovementItem`, `ContractHistoryEvent`); FE: timeline cassa (F5) + timeline
stato (F6) sul dettaglio (riuso pattern `PaymentHistory`/`CashAuditSheet`). Test: integrazione (F5
movimenti + confine wallet) + nuovo `test_contract_history.py` (F6).
