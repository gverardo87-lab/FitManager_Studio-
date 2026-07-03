# SPEC_TERMINAZIONE_BILATERALE_E_TUTELA_TRAINER

**Tipo:** specifica prescrittiva (cosa-deve-essere-vero; silente sul come). Bridge Chat->Code.  
**Data:** 2026-06-27 · **Branch:** `FitManager_Studio`  
**Stato:** ✅ **IMPLEMENTATO** (G7.9 il 2026-06-27 · G7.10 il 2026-06-28) · ratificata da **ADR-018** (accepted)  
**Blocchi:** **G7.9** ✅ (core: esito balance-based + incasso contestuale *editabile* + rinuncia) · **G7.10** ✅ (credito differito: entità `crediti_terminazione` + worklist + incasso/annulla + reopen esteso). Post G7.7/G7.8. Resta come design-record + AC.  
**Mappa di verita:** `docs/adr/ADR-018-terminazione-bilaterale-credito-trainer.md` · `docs/operations/AUDIT_TERMINAZIONE_BILATERALE_2026-06-27.md` · `docs/technical/FINANCIAL_DOMAIN_MODEL.md` v1.3 · `docs/archive/specs/SPEC_G7.3_TERMINAZIONE_ENDPOINT.md` · `api/services/contract_settlement.py` · `api/routers/contracts.py` · `api/services/contract_state.py`

## Impact map

- **Obiettivo:** rendere la terminazione davvero bilaterale. Oggi il software tutela solo il cliente quando `versato > servizio_reso`; deve tutelare anche il trainer quando `servizio_reso > versato`, senza perdere auditabilita ne rompere gli invarianti G6/G7.
- **Layer toccati (G7.9):** backend come scope primario (`contract_settlement`, `contracts.py`, `cash_categories.py`, schema Pydantic, audit, reopen, test); frontend come consumer sottile (`TerminateContractDialog`, tipi API, copy di preview e conferma).
- **Layer toccati (G7.10):** entità `crediti_terminazione` (tabella additiva via `schema_sync`), worklist "Crediti da incassare (post-chiusura)", endpoint di incasso del differito, estensione `reopen`, frontend (worklist + dialog incasso).
- **Invarianti da preservare:** asse EROGATO = soli eventi PT `Completato`; `Rinviato` non muove denaro (ADR-017); Strada B (`totale_versato` lordo immutabile, `totale_rimborsato` separato, `netto_incassato()` derivato); `CHIUSO` resta a `residuo == 0` (anche col credito differito); `reopen` resta l'inverso esplicito esatto della terminazione; nessuna rata/futuro servizio fantasma su contratto chiuso; ramo `CREDITO_CLIENTE`/RIMBORSO **byte-identico** a G7.3.

**Tesi falsificabile:** un contratto in cui il cliente ha ricevuto piu servizio di quanto ha pagato non puo piu essere chiuso con una **rinuncia implicita del trainer**. Il sistema deve obbligare una scelta esplicita e auditabile tra:

1. **incassare contestualmente** il dovuto (importo proposto ed editabile) e poi chiudere, oppure
2. **rinunciare esplicitamente** (con nota) a quel dovuto e poi chiudere, oppure
3. **mettere a credito** il dovuto — il cliente paga dopo — e poi chiudere (entità dedicata, **G7.10**).

Se il trainer non sceglie, `terminate` rifiuta la richiesta (422). Dopo il commit, `residuo == 0`, il mastro e il Contract restano riconciliati, e `reopen` ricostruisce esattamente lo stato pre-terminazione.

---

## 0. Problema reale da correggere

Lo stato attuale e' asimmetrico:

- `compute_settlement()` tratta `conguaglio < 0` come **RIMBORSO** al cliente (`contract_settlement.py`);
- tratta `conguaglio >= 0` come **`SALDO_A_PERDERE`** → `terminate` lo mappa su **`TERMINAZIONE_DECADENZA`** (`contracts.py`), cioe' un **write-off implicito** del residuo, senza chiedere se il trainer voglia incassare il dovuto o rinunciarvi.

Questo comprime in un solo esito tre realta economicamente diverse: il **fatto contabile** (il cliente deve ancora denaro per servizio gia reso), e le **azioni operative** (incasso / rinuncia / metto a credito). Fatto economico e azione sono fusi → la rinuncia del trainer diventa il **default implicito**, non una decisione.

**Prova economica** (P = 1000, 10 sedute @100; cliente ne fa **7** → `R` = 700 col pro_sedute; ha versato `V` = 500). Oggi `terminate` esegue `quota_stornata += residuo_pre = P − V = 500` → residuo 0, chiuso. Ma quei 500 fondono due cose diverse:

- **300** = `P − R` → servizio **mai erogato** → storno legittimo;
- **200** = `R − V` → servizio **gia reso e non pagato** → **credito reale del trainer, abbuonato in silenzio**.

E' una falla di **dominio**, non di UX: perdita silenziosa di un credito; storico che non distingue piu "servizio non erogato annullato" da "servizio erogato ma abbuonato"; impossibilita di dimostrare a posteriori se il trainer abbia scelto davvero la rinuncia.

**Vincolo trasversale (ADR-014):** la valorizzazione del servizio reso (`pro_sedute`) e' **PROVISIONAL** (gated tributarista). Finche' decideva solo un abbuono, un errore era a sfavore del trainer. Ora determinerebbe un importo **fatturato a un cliente reale** → l'importo incassabile dev'essere una **proposta editabile**, mai una bolletta rigida. La correzione qui non tocca la matematica del servizio reso: cambia la **semantica del ramo positivo del conguaglio**.

---

## 1. Cio che NON cambia

Restano vincolanti (non re-litigare):

- **EROGATO canonico (ADR-016):** il valore del servizio reso si basa solo sugli eventi PT `Completato`.
- **Occupazione != denaro (ADR-017):** `Programmato` e `Rinviato` non entrano nel calcolo economico del recesso (forfeiture delle prenotate inclusa).
- **Strada B:** il rimborso al cliente passa da `totale_rimborsato` + movimento `USCITA`; il lordo `totale_versato` non viene mai riscritto a ritroso (cresce-solo sul forward).
- **Contratto chiuso = niente residuo operativo:** un contratto terminato non lascia rate attive, credito-servizio-futuro, o residuo contrattuale ancora incassabile. **`residuo() == 0` su `CHIUSO` vale anche col credito differito** (che vive fuori da `residuo()`).
- **Inversione unica:** ogni effetto della terminazione e' reversibile solo via `POST /contracts/{id}/reopen`, mai con scorciatoie sparse.
- **Ramo cliente invariato:** `CREDITO_CLIENTE` (ex `RIMBORSO`) resta **byte-identico** a G7.3 (semantica e importi).

---

## 2. Modello di dominio: esito puro != azione scelta

Il modulo puro di settlement smette di etichettare `conguaglio > 0` come `SALDO_A_PERDERE` (che e' gia un giudizio d'azione). Restituisce il **fatto economico puro**:

- `CREDITO_CLIENTE` se `versato > valore_servizio_reso`
- `CREDITO_TRAINER` se `valore_servizio_reso > versato`
- `PARI` se `valore_servizio_reso ~= versato`

Il write-off del saldo dovuto al trainer **non** e' piu il default del modulo: diventa una scelta del caller, esplicita e tracciata.

### 2.1 Nomenclatura del modulo puro

`api/services/contract_settlement.py` evolve da esiti action-based a esiti **balance-based**:

- `SettlementEsito.CREDITO_CLIENTE`
- `SettlementEsito.CREDITO_TRAINER`
- `SettlementEsito.PARI`

`SALDO_A_PERDERE` **esce** dal modulo puro. Sopravvive solo come **azione facoltativa del trainer** nel router ("rinuncio al saldo a mio favore").

### 2.2 Grandezze pure esposte

Con `P = prezzo_totale`, `V = totale_versato` pre-terminate, `R = valore_servizio_reso`:

```text
conguaglio        = round(R − V, 2)          # firmato, classificato con dead-zone ±0.009
credito_cliente   = max(V − R, 0)
credito_trainer   = max(R − V, 0)
quota_non_erogata = max(P − R, 0)
residuo_pre       = max(P − V, 0)            # == contract_state.residuo() PRE-storno
```

Identita utile (con `V <= P`, garantito dai guard overpayment): `residuo_pre = quota_non_erogata + credito_trainer − credito_cliente`. Nel ramo trainer (`R > V`): `residuo_pre = quota_non_erogata + credito_trainer`.

**Classificazione (dead-zone):** `conguaglio < −0.009 → CREDITO_CLIENTE`; `conguaglio > +0.009 → CREDITO_TRAINER`; altrimenti `PARI`. Gli importi usano `max(…, 0)`; la classificazione usa la dead-zone (mai confondere i due piani).

---

## 3. Regola centrale: il ramo trainer richiede una scelta esplicita

Se `credito_trainer == 0`, il comportamento resta lineare:

- `CREDITO_CLIENTE` -> rimborso al cliente + storno del non incassato;
- `PARI` -> nessun movimento di cassa + storno della quota non erogata.

Se `credito_trainer > 0`, `terminate` **rifiuta** (422) a meno che il trainer selezioni una di queste azioni. Sia `X` l'importo scelto, **editabile** in `[0, credito_trainer]` (default `credito_trainer = R − V`, **solo verso il basso**: il non-erogato `P − R` non e' mai fatturabile col metodo pro-rata; editare `X` sotto il default = abbuono parziale, la differenza confluisce nello storno).

1. **`INCASSA_ORA`** (G7.9)
   - il trainer incassa contestualmente l'importo `X` per il servizio gia reso;
   - l'incasso entra nello **stesso commit** della terminazione (movimento `ENTRATA` diretto, vedi §4.2);
   - viene stornata la quota non erogata **piu** l'eventuale parte abbuonata via edit.

2. **`RINUNCIA_ESPRESSA`** (G7.9) — caso `X = 0`
   - il trainer abbuona volontariamente l'intero saldo a suo favore;
   - nessun movimento di cassa; il residuo contrattuale viene azzerato come write-off;
   - la rinuncia e' esplicita, **motivata (nota obbligatoria)** e auditata.

3. **`A_CREDITO`** (G7.10) — "chiudo oggi, il cliente paga dopo"
   - l'importo `X` (qui chiamato `D`) diventa un **receivable** dedicato (`crediti_terminazione`), **fuori** da `residuo()`;
   - nessun movimento di cassa al momento della chiusura; il contratto chiude con `residuo == 0`;
   - l'incasso (anche parziale) avviene dopo, via l'endpoint dedicato (§8). Normato nel blocco **G7.10**.

**Percorso vietato:** `credito_trainer > 0` + nessuna azione → mai chiusura silenziosa.

### 3.1 Guardie richieste

- `terminate` con `credito_trainer > 0` e senza azione -> **422**.
- `INCASSA_ORA` senza `metodo_pagamento` -> **422**.
- `INCASSA_ORA` / `A_CREDITO` con `importo_incassato` fuori da `[0, R − V]` (oltre il default verso l'alto, o negativo) -> **422**.
- `RINUNCIA_ESPRESSA` senza `note` non vuote -> **422**.

La nota obbligatoria nella rinuncia non e' cosmesi: e' parte del presidio auditabile.

---

## 4. Formule canoniche

Il sistema resta coerente su cassa, netto e residuo finale. Per ogni ramo, `residuo() == 0` al commit.

### 4.1 Credito cliente (`V > R`) — invariato da G7.3

- **Movimento cassa:** `USCITA` categoria `RIMBORSO_CONTRATTO`, importo `V − R`
- **Delta Contract:** `totale_rimborsato += V − R`
- **Storno:** `quota_stornata += residuo_pre` (`= P − V`)
- **Post-invariante:** `netto_incassato == R` e `residuo == 0`

### 4.2 Credito trainer + `INCASSA_ORA` (`R > V`), importo `X ∈ [0, R − V]`

- **Movimento cassa:** `ENTRATA` diretta su contratto, `id_rata = NULL`, categoria **`INCASSO_CONGUAGLIO_CONTRATTO`**, importo `X`
- **Delta Contract:** `totale_versato += X`
- **Storno:** `quota_stornata += residuo_pre − X` (`= (P − R) + (R − V − X)`: non-erogato sempre + parte abbuonata)
- **Post-invariante:** `residuo == 0` sempre; `netto_incassato == V + X` (`== R` solo se `X = R − V`, incasso pieno)
- **Derivazione `residuo == 0`:** `P − (V + X) − (residuo_pre − X) = P − V − residuo_pre = 0`.

### 4.3 Credito trainer + `RINUNCIA_ESPRESSA` (`R > V`, `X = 0`)

- **Movimento cassa:** nessuno
- **Storno:** `quota_stornata += residuo_pre` (`= P − V`)
- **Dato audit obbligatorio:** `saldo_trainer_rinunciato = R − V`
- **Post-invariante:** `residuo == 0` e `netto_incassato + saldo_trainer_rinunciato == R`

Mantiene il comportamento economico attuale, ma lo rende **intenzionale e tracciato**.

### 4.4 Credito trainer + `A_CREDITO` (`R > V`), differito `D ∈ [0, R − V]` — G7.10

- **Movimento cassa (al terminate):** nessuno
- **Receivable:** record `crediti_terminazione` `{ importo = D, importo_incassato = 0, stato = APERTO }`, legato al contratto, **fuori** da `residuo()`
- **Storno:** `quota_stornata += residuo_pre` (`= P − V`: assorbe non-erogato + differito + eventuale abbuono; il differito `D` e' ri-tracciato nel receivable, **non** perso)
- **Incasso successivo** (endpoint §8, anche parziale `d <= D − importo_incassato`): `ENTRATA INCASSO_CONGUAGLIO_CONTRATTO` importo `d` + `totale_versato += d` + `importo_incassato += d`; a saldo `stato = SALDATO`
- **Post-invariante (al terminate e dopo ogni incasso):** `residuo == 0` (clamp); `netto_incassato == V + importo_incassato`

### 4.5 Pari (`R ~= V`, entro la dead-zone)

- **Movimento cassa:** nessuno
- **Storno:** `quota_stornata += residuo_pre`
- **Post-invariante:** `netto_incassato == R` e `residuo == 0`

---

## 5. Contratti aperti (G6) vs contratti da terminare

### 5.1 Contratto aperto e scaduto (`SOSPESO` / `ESAURITO`)

Il trainer puo ancora estendere, continuare a erogare, **incassare il residuo** con i flussi esistenti, o terminare. **Questa spec NON cambia G6.** `incassa_residuo` resta il percorso di recupero su contratto **aperto**, e non va riusato per simulare una terminazione: l'importo da recuperare in G6 (residuo contrattuale) e l'importo dovuto sul servizio gia reso (`R − V`) sono concetti diversi.

### 5.2 Contratto che si vuole chiudere adesso

Se il trainer termina, il sistema regola il contratto in modo completo nello stesso atto, con una delle tre azioni del §3. Il **core G7.9** copre incasso contestuale e rinuncia; il **differito** ("chiudo oggi, incasso dopo") e' normato in **G7.10** con **entità propria** (`crediti_terminazione`).

**Vincolo di design ferreo (G7.10):** il credito differito **non** puo riapparire dentro `residuo()` di un contratto `CHIUSO` (romperebbe `residuo == 0`) ne essere simulato con una Rate viva sul chiuso (rata-fantasma). Vive **fuori** da `residuo()` come receivable; `quota_stornata` assorbe il differito, che resta ri-tracciato nel receivable.

---

## 6. Semantica di chiusura e audit

### 6.1 `motivo_chiusura`

Enum `MotivoChiusura` esteso (additivo):

- `TERMINAZIONE_RIMBORSO` per `CREDITO_CLIENTE`
- `TERMINAZIONE_SALDO_TRAINER` (**nuovo**) per `CREDITO_TRAINER`, a prescindere da `INCASSA_ORA` / `RINUNCIA_ESPRESSA` / `A_CREDITO`
- `CONSUNZIONE` per il ramo `PARI` (invariato in questa iterazione)
- `TERMINAZIONE_DECADENZA` resta **legacy/storico**: non piu emesso dal nuovo `terminate` per contratti vivi

La distinzione incasso / rinuncia / differito **non** vive nel `motivo_chiusura`, ma nel payload audit (§6.2). `TERMINAZIONE_SALDO_TRAINER`, come gli altri `TERMINAZIONE_*`, **non** si auto-riapre (reopen-allowlist G7.2: solo `COMPLETAMENTO`); va aggiunto al forward-guard e al grep-guard `check-all.sh`.

### 6.2 Audit payload minimo obbligatorio

Ogni terminazione registra almeno:

- `settlement.esito_balance`
- `settlement.credito_cliente`
- `settlement.credito_trainer`
- `settlement.quota_non_erogata`
- `settlement.azione_credito_trainer` (se ramo trainer)
- `settlement.importo_incassato` (se `INCASSA_ORA`) / `settlement.importo_differito` (se `A_CREDITO`)
- `settlement.saldo_trainer_rinunciato` (parte abbuonata: `R − V − X`)
- `settlement.movimento_cassa_id` (se creato)

Scopo: rendere ricostruibile a posteriori se il trainer ha incassato, messo a credito o abbuonato il saldo dovuto.

---

## 7. Perimetro backend — G7.9 (core)

File e zone:

- `api/services/contract_settlement.py`
  - esito puro balance-based (`CREDITO_CLIENTE` / `CREDITO_TRAINER` / `PARI`)
  - esposizione di `credito_cliente`, `credito_trainer`, `quota_non_erogata`, `residuo_pre`
- `api/routers/contracts.py`
  - preview arricchita (esito balance + `credito_trainer` + `azioni_permesse`)
  - `terminate` con scelta obbligatoria nel ramo trainer + importo editabile validato server-side (`<= R − V`)
  - nuovo incasso contestuale diretto sul contratto (`INCASSA_ORA`)
  - nuovo mapping `motivo_chiusura` (`_motivo_from_esito`)
  - `reopen` come inverso esatto anche del nuovo incasso
- `api/services/cash_categories.py`
  - nuova categoria `INCASSO_CONGUAGLIO_CONTRATTO` in `CONTRACT_CASH_IN`
  - inclusione nei predicati di inflow contrattuale + in **tutti** gli aggregati induriti in G7.5
- `api/schemas/financial.py`
  - `ContractTerminate` (+ `azione_credito_trainer`, `+ importo_incassato`, `+ metodo_pagamento`; `extra: "forbid"`)
  - `ContractSettlementPreview` (esito balance + `credito_trainer` + `azioni_permesse`)
- `api/routers/_audit.py`
  - payload strutturato del ramo trainer (§6.2)
- `tools/scripts/check-all.sh`
  - grep-guard: `INCASSO_CONGUAGLIO_CONTRATTO` presente in ogni predicato di inflow; `TERMINAZIONE_SALDO_TRAINER` nel forward-guard reopen

### 7.1 `reopen` resta l'inverso esatto (G7.9)

Se `terminate` crea un `ENTRATA` `INCASSO_CONGUAGLIO_CONTRATTO`, `reopen` deve:

- soft-deletare quel movimento (via ORM, come gia fa per `RIMBORSO_CONTRATTO`);
- **decrementare `totale_versato`** dello stesso importo (prima volta che `reopen` tocca il lordo: eccezione sanzionata, gemella di `unpay_rate`);
- azzerare la quota di storno scritta da quel terminate;
- ripristinare le rate marcate `chiusa_da_terminazione` (come G7.7-M1).

Coordinare col guard **H1** di `unpay_rate` (409 su terminato): `reopen` resta l'unico path che annulla l'incasso di conguaglio. Nessun incasso "one-way" non invertibile dal percorso canonico.

### 7.2 Nessuna riapertura di rate o percorsi larghi

La nuova logica non deve: riaprire `pay_rate` su contratti chiusi; aggirare `update_rate` / `unpay_rate` / `generate_payment_plan`; reintrodurre un debito dentro `residuo()` di un contratto chiuso. Il nuovo incasso e' un movimento diretto di settlement, non una rata mascherata.

---

## 8. Perimetro backend — G7.10 (credito differito)

Blocco **successivo e separato**. Introduce l'entità che permette "chiudo oggi, incasso dopo" senza violare `residuo == 0`.

- **Entità `crediti_terminazione`** (tabella dedicata, additiva via `schema_sync`, **no alembic** — vedi learning "`alembic_version` FROZEN"): `id`, `trainer_id`, `id_contratto`, `importo`, `importo_incassato` (default 0), `stato` (`APERTO` / `SALDATO` / `ANNULLATO`), `data_creazione`, `data_chiusura`, `deleted_at`. **Mai** una Rate viva su contratto chiuso.
- **Azione `A_CREDITO` in `terminate`:** crea il receivable `{ importo = D, stato = APERTO }`; `quota_stornata` assorbe il differito (§4.4); `residuo == 0`.
- **Worklist "Crediti da incassare (post-chiusura)":** gemella di G6 (`is_residuo_incassabile_diretto`), elenca i `crediti_terminazione` `APERTO`. Aging-driven.
- **Endpoint di incasso del differito:** `POST` dedicato → `ENTRATA INCASSO_CONGUAGLIO_CONTRATTO` (importo `d`, anche parziale) + `totale_versato += d` + `importo_incassato += d`; a saldo `stato = SALDATO`. Bouncer ownership; cap `d <= importo − importo_incassato` (422).
- **`reopen` esteso:** se esiste un `crediti_terminazione` legato alla chiusura, `reopen` annulla anche il receivable (`stato = ANNULLATO`) e inverte gli eventuali incassi parziali gia registrati (soft-delete dei loro `ENTRATA` + `totale_versato −=`).
- **Predicati cassa:** gli incassi del differito usano la stessa categoria `INCASSO_CONGUAGLIO_CONTRATTO` → gia coperti dai predicati di G7.9.

---

## 9. Perimetro frontend

Il frontend non ricalcola nulla: espone la scelta obbligatoria quando il backend segnala `credito_trainer > 0`.

`TerminateContractDialog` (G7.9):

- mostra se il saldo e' a favore del cliente o del trainer;
- nel ramo `credito_trainer > 0`, rende selezionabile **Incassa ora e chiudi** / **Rinuncia e chiudi** (G7.9) e — quando G7.10 e' attivo — **Metti a credito e chiudi**;
- in `INCASSA_ORA` espone l'importo come **campo editabile** (default `R − V`, max `R − V`) + `metodo_pagamento`;
- in `RINUNCIA_ESPRESSA` richiede una **nota**;
- vieta la conferma senza scelta esplicita;
- mantiene il framing G7.3: il software **propone** un calcolo, non afferma un obbligo legale.

Worklist "Crediti da incassare (post-chiusura)" + dialog di incasso parziale (G7.10), riusando i pattern di `IncassaResiduoDialog` (G6). Nessuna formula client-side, nessun fallback implicito.

---

## 10. Test di accettazione

### 10.1 Settlement puro (G7.9)

1. `compute_settlement` con `R < V` -> `CREDITO_CLIENTE`, `credito_cliente > 0`, `credito_trainer == 0`
2. `compute_settlement` con `R > V` -> `CREDITO_TRAINER`, `credito_trainer > 0`, `credito_cliente == 0`
3. `compute_settlement` con `R ~= V` (entro ±0.009) -> `PARI`

### 10.2 Preview (G7.9)

4. `GET /settlement-preview` su `credito_trainer > 0` non scrive nulla e ritorna `esito_balance = CREDITO_TRAINER`, `credito_trainer`, `azioni_permesse` (incl. `A_CREDITO` solo se G7.10 attivo)
5. La preview su overpaid resta coerente con G7.3, salvo il nuovo naming dell'esito puro

### 10.3 Terminate (G7.9)

6. `terminate` con `credito_trainer > 0` e senza scelta -> **422**
7. `INCASSA_ORA` con `X = R − V` (incasso pieno): un solo `ENTRATA INCASSO_CONGUAGLIO_CONTRATTO`; `totale_versato += X`; `quota_stornata == P − R`; `chiuso == True`; `residuo == 0`; `netto_incassato == R`
8. `INCASSA_ORA` con `X < R − V` (abbuono parziale): `ENTRATA` importo `X`; `quota_stornata == P − R + (R − V − X)`; audit `saldo_trainer_rinunciato == R − V − X`; `residuo == 0`
9. `INCASSA_ORA` con `X > R − V` -> **422**
10. `RINUNCIA_ESPRESSA`: nessun `ENTRATA`; `quota_stornata == P − V`; audit `saldo_trainer_rinunciato == R − V`; `chiuso == True`; `residuo == 0`
11. `RINUNCIA_ESPRESSA` senza nota -> **422**
12. `CREDITO_CLIENTE` invariato: rimborso cassa corretto; `quota_stornata == P − V`; `netto_incassato == R`

### 10.4 Reopen (G7.9)

13. `reopen` dopo `INCASSA_ORA`: movimento `INCASSO_CONGUAGLIO_CONTRATTO` annullato; `totale_versato` tornato al pre-terminate; `quota_stornata` ripristinata; rate ripristinate solo se marcate
14. `reopen` dopo `RINUNCIA_ESPRESSA`: rimuove il write-off e riporta al pre-terminate, senza movimenti fantasma

### 10.5 Regressioni e reportistica (G7.9)

15. I predicati di inflow contrattuale includono il nuovo incasso di conguaglio
16. Nessun report scambia il nuovo incasso per rimborso o spesa
17. `kpi_incassato`, `movement-stats`, `financial-trend`, `monthly_revenue` restano coerenti dopo un terminate con `INCASSA_ORA`
18. La suite legacy G7.3/G7.4/G7.7/G7.8 resta verde

### 10.6 Legacy safety (G7.9)

19. Golden-fixture legacy: un contratto "muto" o con `crediti_totali = NULL` non crasha e produce preview/terminate coerenti nel ramo trainer (per `crediti_totali = NULL`, `R = P` → `credito_trainer = residuo_pre` → forza la scelta)

### 10.7 Credito differito (G7.10)

20. `A_CREDITO` con `D`: nessun `ENTRATA` al terminate; receivable `{ importo = D, stato = APERTO }`; `quota_stornata == P − V`; `residuo == 0`
21. Incasso parziale del differito: `ENTRATA` importo `d`; `importo_incassato += d`; `residuo == 0`; a saldo `stato == SALDATO`
22. Incasso oltre il residuo del differito (`d > importo − importo_incassato`) -> **422**
23. `reopen` dopo `A_CREDITO`: receivable `ANNULLATO`, eventuali incassi parziali invertiti, `totale_versato` ripristinato, stato pre-terminate esatto

---

## 11. Sequenza di implementazione

### G7.9 — core (zero tabella nuova)

**Step 1 — modulo puro + unit test.** Converti `SettlementEsito` ad balance-based; esponi le grandezze pure; test sul ramo `CREDITO_TRAINER`. **Gate:** unit test verdi su `contract_settlement.py`.

**Step 2 — preview + terminate.** Estendi `settlement-preview` (esito balance + `credito_trainer` + `azioni_permesse`); introduci la scelta obbligatoria + importo editabile nel payload `terminate`; implementa `INCASSA_ORA` e `RINUNCIA_ESPRESSA`; nuovo `motivo_chiusura`. Non toccare ancora il FE. **Gate:** test endpoint verdi.

**Step 3 — reopen + audit.** Rendi `reopen` inverso esatto anche del nuovo incasso; arricchisci l'audit; verifica round-trip e riconciliazione mastro/Contract. **Gate:** test round-trip verdi.

**Step 4 — predicati cassa + regressioni aggregate.** Aggiungi la categoria ai predicati contrattuali + grep-guard; rerun report finanziari/aggregati. **Gate:** suite backend + `ruff check api/` verdi.

**Step 5 — consumer frontend.** Aggiorna tipi API + `TerminateContractDialog` (scelta 3-vie, importo editabile, nota); verifica zero default implicito. **Gate:** `next build` verde.

**Step 6 — quality gate finale.** Test backend pertinenti + `ruff check api/` + `next build`; aggiorna `FINANCIAL_DOMAIN_MODEL.md`, `api/CLAUDE.md`, `BUILD_LOG.md` **solo dopo** implementazione reale.

### G7.10 — credito differito

**Step 7 — entità + terminate.** Tabella `crediti_terminazione` (schema_sync); azione `A_CREDITO` in `terminate` + preview. **Gate:** test entità + terminate verdi.

**Step 8 — worklist + endpoint incasso.** Worklist "Crediti da incassare (post-chiusura)" + endpoint di incasso (anche parziale). **Gate:** test worklist/incasso verdi.

**Step 9 — reopen esteso + FE.** `reopen` annulla il receivable + inverte gli incassi parziali; FE worklist + dialog incasso. **Gate:** round-trip + `next build` verdi.

**Step 10 — quality gate finale G7.10.** Suite + `ruff` + `next build`; aggiorna doc vivi.

---

## 12. Confine di scope

**In G7.10** (non in G7.9): l'entità `crediti_terminazione`, la worklist di recupero su contratti chiusi, l'endpoint di incasso del differito, l'estensione di `reopen`.

**Fuori da entrambi i blocchi:**

- la combinazione di piu azioni in una sola terminazione (es. "incasso 100 ora + 100 a credito"): in v1 **una azione per terminazione** (il caso misto si ottiene con `A_CREDITO` + incasso parziale del receivable);
- la ridefinizione completa dei motivi storici `CONSUNZIONE` / `TERMINAZIONE_DECADENZA`;
- nuove policy legali o fiscali sul recesso del consumatore;
- la chiusura della decisione tributarista sulla valorizzazione `pro_sedute` (resta PROVISIONAL; G7.9 la mitiga rendendo l'importo una **proposta editabile**);
- qualsiasi calcolo client-side del settlement.

**Vincolo ferreo permanente:** il credito differito non si forza dentro `residuo()` e non si simula con una Rate su contratto chiuso. `residuo == 0` su `CHIUSO` resta invariante.

---

## 13. Definizione di fatto

**G7.9** e' finito quando:

1. il ramo `credito_trainer > 0` non puo piu chiudere un contratto senza una scelta esplicita;
2. `terminate` supporta `INCASSA_ORA` (importo editabile) e `RINUNCIA_ESPRESSA` in un solo commit coerente;
3. `reopen` e' l'inverso esatto anche del nuovo incasso;
4. mastro, `totale_versato`, `totale_rimborsato`, `quota_stornata`, `netto_incassato` e `residuo()` restano riconciliati;
5. il FE obbliga la scelta ma non ricalcola nulla;
6. i test target G7.9 sono verdi e i quality gate del repo passano.

**G7.10** e' finito quando:

7. `A_CREDITO` chiude il contratto con `residuo == 0` e un receivable tracciato fuori da `residuo()`;
8. l'incasso del differito (anche parziale) e' auditabile e riconciliato col mastro;
9. `reopen` annulla anche il receivable e i suoi incassi parziali, ricostruendo lo stato pre-terminate;
10. i test target G7.10 sono verdi e i quality gate del repo passano.

Se uno solo di questi punti manca, la tutela del trainer resta incompleta.
