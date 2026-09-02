# Audit Senior — Logica Crediti / Contratti / Clienti (focus rimborso da recesso)

> **ARCHIVIATO 2026-09-02** — H1 + M1-M3 foldati nella remediation G7.7/G7.8 (chiusa); fondante per
> ADR-016. Riferimento storico, mai contesto di lavoro.

> **Provenienza:** audit multi-agente L0–L5 (8 finder paralleli + grounding su `data/crm.db` reale + coverage test → verifica avversariale refute-by-default per ogni finding → sintesi). 54 finding grezzi → **34 confermati**. Eseguito 2026-06-26 su HEAD `324be75`.
> **Trigger:** segnalazione trainer reale (Chiara) su "errore logico" nei crediti residui usati per il rimborso da recesso anticipato.
> **Nota metodo:** 10 verifiche dello strato L0 (modello/doc) sono fallite per session limit → le invarianti L0 sono confermate indirettamente dagli strati L1–L5 + DATA; un ri-pass mirato L0 è opportuno se si vuole chiudere anche la coerenza doc↔codice formalmente.

**Scope:** catena finanziaria G6→G7.0-G7.6 · HEAD `324be75` · branch FitManager_Studio
**Modalità:** sola lettura (codice + `data/crm.db` reale, 35 contratti)
**Decisione di modello ratificata (vincolante):** l'asse canonico del rimborso è **EROGATO** = solo Event PT `Completato`. Verificata, non contestata.

---

## 1. Executive summary

La logica di rimborso è **strutturalmente solida**: ogni path monetario (preview, terminate, reopen, KPI, frontend) deriva il valore reso dall'asse EROGATO (`_count_sedute_erogate` → `valore_servizio_reso`), mai dall'occupazione; `compute_settlement` ha una firma che rende l'asse occupazione *strutturalmente irraggiungibile* dal calcolo. Sul DB reale **zero violazioni** di non-negatività, tetto e conservazione del ledger (I2/I3/I5 reggono su tutti i 35 contratti e sulle 2 terminazioni reali id=39/21).

**Risposta diretta alla segnalazione di Chiara:** la divergenza che percepisce — "crediti residui 4" ma rimborso calcolato su 2 sedute — è **by-design e corretta**. Una seduta solo *prenotata* (Programmato) occupa uno slot ma non è servizio reso, quindi giustamente non aumenta il rimborso. Il problema **non è il calcolo, è la trasparenza**: la riconciliazione occupazione↔erogato esiste *solo* dentro il dialog di terminazione (microcopy G7.5c), mentre lista contratti, scheda dettaglio e profilo cliente mostrano l'asse occupazione **senza affiancare l'erogato**, inducendo un modello mentale errato *prima* che il trainer apra la terminazione.

**Un solo difetto che muove denaro/stato in modo errato** è emerso: `unpay_rate` non ha guardia sui contratti terminati → può corrompere il ledger e mascherare un over-rimborso reale (HIGH). Tutto il resto è debito SSoT / gap di trasparenza / igiene di test.

---

## 2. Verdetto sulle 7 invarianti

| Inv. | Esito | Motivazione (una riga) |
|------|-------|------------------------|
| **I1** Unicità del consumo (rimborso=erogato) | **REGGE** | Confermata a tutti gli strati L1→L5 + DATA; `compute_settlement` non può ricevere l'asse occupazione per costruzione. |
| **I2** Non-negatività | **REGGE** | `residuo`/`netto` clampati; 0 violazioni sui 35 contratti reali; `quota_stornata`/`totale_rimborsato` additivi. |
| **I3** Tetto rimborso ≤ netto incassato | **VIOLATA (edge)** | Regge per costruzione in `compute_settlement`, ma `unpay_rate` su contratto terminato-rimborsato fa scendere `versato` sotto `rimborsato` → tetto rotto, clamp lo maschera. |
| **I4** Chiusura coerente (residuo==0) | **REGGE** | `quota_da_stornare == residuo_corrente` azzera deterministicamente; copertura test ridondante su 5 rami. |
| **I5** Conservazione ledger | **REGGE (con caveat)** | Forward path conservativo, write-site unico, zero entrate-fantasma; àncore `versato==ΣENTRATA` e `rimborsato==ΣRIMBORSO` reggono anche nell'edge unpay (è I3/cassa a rompersi, non le àncore). |
| **I6** Coerenza display↔rimborso | **DA-RATIFICARE** | Riconciliata solo nel dialog terminate; lista/scheda/profilo mostrano occupazione senza erogato; `ContrattiTab` ricalcola un badge off-SSoT che collassa Sospeso→Attivo. |
| **I7** Edge auto-close vs rimborso | **REGGE (con caveat)** | Nessuno stato-zombie sul DB reale; reopen-allowlist coerente; ma `reopen` over-restora le rate (asimmetria) e l'auto-close etichetta COMPLETAMENTO un servizio non erogato. |

---

## 3. Findings per severità

### BLOCKER
Nessuno. Nessun denaro si muove in modo errato nel flusso normale; nessuna violazione sui dati reali.

### HIGH

**H1 — `unpay_rate` privo di guardia su contratto terminato → `totale_rimborsato > totale_versato` (rompe I3, sbilancia la cassa)**
`api/routers/rates.py:615-710` (manca guard; decremento a `:656`; allowlist `:670-674`)
*Descrizione:* `terminate()` soft-elimina solo le rate **non-saldate**; le SALDATE e i loro `CashMovement` ENTRATA sopravvivono. `unpay_rate` non ha la guardia `if contract.chiuso` presente in `create_rate` (`:307`) e `generate_payment_plan` (`:736`); il bouncer trova le SALDATE superstiti di un contratto terminato e procede. La reopen-allowlist mantiene correttamente `chiuso=True` (motivo `TERMINAZIONE_*`≠COMPLETAMENTO) ma **non blocca il decremento di `totale_versato`**, mentre `totale_rimborsato` resta invariato.
*Impatto monetario:* prezzo 1000, 2 rate SALDATE 500+500, 2 erogate → terminate: reso 200, rimborso pagato 800, `totale_rimborsato=800`. Unpay di una rata 500 → `totale_versato=500`, ENTRATA da 500 soft-deletata, `totale_rimborsato` resta 800. `netto_incassato()=max(500-800,0)=0` **clampa e nasconde** un over-rimborso reale di 300 e un mastro con ΣRIMBORSO(800) > ΣENTRATA(500). Cassa già uscita, KPI `kpi_incassato` sottostimato.
*Categoria:* **BUG_MONETARIO**
*Remediation:* guardia mirata in `unpay_rate` (NON blanket `if chiuso`, regredirebbe l'auto-reopen da COMPLETAMENTO): rifiutare 400/409 se `motivo_chiusura` inizia con `TERMINAZIONE_` oppure `totale_rimborsato>0`/`quota_stornata>0` ("riapri prima il contratto"). In alternativa instradare la revoca dal percorso reopen che riallinea atomicamente. *(I due finding L3 + TEST descrivono lo stesso difetto — deduplicati qui.)*

### MEDIUM

**M1 — `reopen` over-restora le rate: ripristina TUTTE le non-saldate soft-eliminate, non solo quelle del terminate**
`api/routers/contracts.py:1386-1399`
*Descrizione:* `terminate` non traccia *quali* rate ha soft-eliminato; `reopen` seleziona `Rate.stato IN (PENDENTE,PARZIALE) AND deleted_at != None` senza scope temporale/batch. Una rata cancellata manualmente (`delete_rate`) o da `generate_payment_plan` **prima** della terminazione viene resuscitata. Sul DB reale: contratto 20 ha 30 rate non-saldate soft-eliminate, contratto 17 ne ha 3 → terminate+reopen le resusciterebbe tutte come PENDENTI.
*Impatto:* nessuna cassa (`residuo()` è prezzo-based); rate-fantasma rientrano nel forecast "entrate certe", falsano `money_substate`/`ha_rate_scadute`, possibile `is_insolvente` fantasma, ricomparsa in worklist "da pianificare".
*Categoria:* **DEBITO_SSOT**
*Remediation:* rendere `reopen` l'inverso *esatto*: marcare in terminate le rate eliminate (flag `closed_by_termination` o timestamp), ripristinare solo quelle. Evitare il select aperto su `deleted_at != None`.

**M2 — `_cap_rateizzabile` ignora `quota_stornata` + `update_rate` privo di guard `chiuso`: rata SALDATA su contratto terminato può tornare PARZIALE**
`api/routers/rates.py:71-99` (`_cap_rateizzabile`), `:349-441` (`update_rate`)
*Descrizione:* il cap è derivato dal LORDO (`prezzo - acconto`) senza sottrarre `quota_stornata`. Su contratto non terminato è inerte (`quota_stornata==0`); ma `update_rate` non ha guard `chiuso` e il bouncer trova le SALDATE superstiti. Alzando `importo_previsto`, la validazione passa e ricrea spazio già scritto-off → rata torna PARZIALE con residuo-fantasma.
*Impatto:* nessuna cassa; `residuo()` del contratto resta 0 (sottrae `quota_stornata`); tutti i consumatori del residuo-rata filtrano `chiuso==False`. Artefatto cosmetico nel solo dettaglio contratto. Diventerebbe money-bug se un futuro consumatore dimenticasse il filtro `chiuso`.
*Categoria:* **DEBITO_SSOT**
*Remediation:* aggiungere guard `if contract.chiuso` a `update_rate` (allineata a `create_rate`); far derivare il cap dallo stesso asse di `contract_state.residuo()` (sottrarre `quota_stornata`) → una sola SSoT.

**M3 — `ContrattiTab` (profilo cliente) ricalcola un badge a 3 stati inline, collassa Sospeso/Esaurito in "Attivo"**
`frontend/src/components/clients/profile/ContrattiTab.tsx:61-72`
*Descrizione:* reimplementa `c.chiuso?Chiuso : c.ha_rate_scadute?Rate in Ritardo : Attivo(verde)` invece di usare `ContractLifecycleBadge`/`ContractMoneyBadge` (i dati SSoT `lifecycle`/`money_substate` sono disponibili nel payload). Un contratto scaduto con crediti residui (Sospeso) appare verde "Attivo" nel profilo, mentre `/contratti` lo mostra correttamente "Sospeso".
*Impatto:* nessuna cassa; due viste dello stesso contratto divergono in silenzio (I6). È esattamente l'off-SSoT recompute che SPEC_VOCABOLARIO Giro 2 vuole eliminare.
*Categoria:* **DEBITO_SSOT**
*Remediation:* sostituire la cascata con i due badge SSoT; aggiungere `ContrattiTab` all'elenco consumatori migrati Giro 2.

**M4 — Auto-close su occupazione: 7 contratti chiusi COMPLETAMENTO con erogato<crediti (label fuorviante)**
`api/routers/agenda.py:313-325`
*Descrizione:* `_sync_contract_chiuso` conta `Event != Cancellato` (include Programmato/Rinviato) → un contratto saldato con monte-sedute interamente *prenotato* si auto-chiude COMPLETAMENTO prima della consegna. Sul DB reale 7 contratti (id 4/9/11/13/26/28/29) hanno erogato<crediti pur chiusi (i "contratti muti" pre-G7, motivo NULL). Il label COMPLETAMENTO comunica "tutto erogato" mentre significa "tutto prenotato + saldato".
*Impatto:* nessuna cassa errata; rimborso pienamente recuperabile (reopen→terminate); ma il trainer non ha segnale che su un COMPLETAMENTO il servizio non sia stato reso e sia dovuto un rimborso in caso di recesso. Nessuno stato-zombie (I7 regge).
*Categoria:* **GAP_TRASPARENZA**
*Remediation:* sui contratti chiusi COMPLETAMENTO con erogato<crediti esporre indicatore riconciliativo ("N sedute prenotate non erogate alla chiusura") + hint "rimborso via Riapri→Termina". Coordinare con runbook G7.6. Valutare sotto-stato `COMPLETAMENTO_PRENOTATO` vs `COMPLETAMENTO_EROGATO`.

### LOW

**L1 — Lista/scheda contratto mostrano l'occupazione senza affiancare l'erogato (radice della percezione di Chiara)**
`api/routers/contracts.py:149,1101-1127` + `ContractFinancialHero.tsx:173-190`
*Descrizione:* 9 contratti aperti reali hanno occupazione≠erogato (es. id=22: display `crediti_residui=0` ma erogato=22, 8 sedute pagate-non-erogate = 320€ di servizio non reso invisibili; id=37: "24 residue" ma erogato=0). La card "Residui" è enfatizzata amber senza dichiarare che il rimborso si baserebbe sulle sole "Completate". Riconciliazione presente solo nel dialog terminate. Il dato erogato (`sedute_completate`) è già nel payload detail (`financial.py:402`).
*Impatto:* nessuna cassa (asse erogato corretto e ratificato); aspettativa errata del trainer prima di aprire la terminazione.
*Categoria:* **GAP_TRASPARENZA**
*Remediation:* affiancare a `crediti_residui` la componente "erogate" con micro-riconciliazione ("N prenotate non ancora svolte"), replicando il framing della microcopy G7.5c fuori dal solo dialog. Per la lista, aggiungere `sedute_completate` a `ContractListResponse`.

**L2 — `SettlementEsito.NULLO` mappa su `MotivoChiusura.CONSUNZIONE`, documentato come "(riservato) residuo post-scadenza"**
`api/routers/contracts.py:1130-1137` + enum `contract_settlement.py:25`
*Descrizione:* una terminazione a conguaglio ~0 produce motivo CONSUNZIONE, etichettato come "riservato" anziché un motivo dedicato di terminazione. `financial.py:207` però già elenca CONSUNZIONE tra i motivi di terminazione → contraddizione di vocabolario, commento enum non aggiornato.
*Impatto:* nessuno (etichetta semantica, non guida movimenti; non in allowlist auto-reopen). Confonde reportistica/audit.
*Categoria:* **IGIENE**
*Remediation:* introdurre `TERMINAZIONE_PARI` o aggiornare il commento enum per riconoscere il doppio uso; documentare in SPEC_G7.0 §2.

**L3 — Gap di copertura test (4 lacune, nessuna corregge comportamento)**
*Categoria:* **IGIENE**
- Nessun test E2E `unpay` su `TERMINAZIONE_RIMBORSO` con rata SALDATA superstite → **è il test che avrebbe colto H1** (priorità alta nonostante severità test = igiene).
- Nessun test property-based sul tetto `importo_rimborso <= totale_versato` (`test_contract_settlement.py`) — regge per costruzione ma un refactor della formula passerebbe muto.
- Prenotate-non-riducono-rimborso provato solo su preview (GET), non sul POST `/terminate` committato (path condiviso `_settlement_for`, basso rischio).
- Nessun test E2E che cuce auto-close COMPLETAMENTO erogato=0 → reopen → settlement-preview = rimborso pieno (seam già coperto a pezzi).

---

## 4. Piano di remediation ordinato

| # | Azione | Severità/Rischio | Note |
|---|--------|------------------|------|
| **1** | **Guardia `unpay_rate` su contratti terminati** (H1) + test sentinella `totale_rimborsato <= totale_versato` | HIGH — denaro/ledger | Unico fix che ferma una corruzione monetaria reale. Guardia *mirata* su `motivo_chiusura TERMINAZIONE_*`/`totale_rimborsato>0`, mai blanket `if chiuso`. Rischio regressione basso se si preserva l'auto-reopen COMPLETAMENTO. |
| **2** | **`reopen` inverso esatto del terminate** (M1): marcare/scope le rate eliminate dalla terminazione | MEDIUM — SSoT/forecast | Toccare solo la gamba E di reopen; test: rate pre-eliminate non resuscitano. |
| **3** | **Guard `chiuso` + cap su asse residuo in `update_rate`/`_cap_rateizzabile`** (M2) | MEDIUM — SSoT | Allineamento a `create_rate`; chiude il residuo-fantasma a livello rata. |
| **4** | **Riconciliazione display↔erogato in lista/scheda/profilo** (L1, M4, M3): affiancare "erogate" a "residui", badge SSoT in `ContrattiTab`, indicatore sui COMPLETAMENTO-prenotati | MEDIUM/LOW — trasparenza | Risolve la radice della percezione di Chiara. Coordinare con Giro 2 vocabolario + runbook G7.6. |
| **5** | **Igiene vocabolario** (L2) + **gap di test** (L3) | LOW — igiene | Il test E2E unpay-post-terminate va aggiunto *insieme* al fix #1. |

---

## 5. Raccomandazione ADR

**Sì, serve un ADR** che ratifichi formalmente quanto oggi è solo implicito nel codice e nelle microcopy. Tre decisioni vanno congelate per evitare regressioni e off-SSoT recompute futuri.

> **Titolo proposto:** ADR-016 — Asse EROGATO canonico per la valorizzazione del recesso, forfeiture delle sedute prenotate, e riconciliazione display↔rimborso
>
> **Decisione (bozza):**
> 1. **Asse canonico.** Il valore del servizio reso (e quindi ogni rimborso/conguaglio da recesso) si calcola **esclusivamente** sulle sedute `Completato` (asse EROGATO). L'asse OCCUPAZIONE (`!= Cancellato`: Programmato+Completato+Rinviato) pilota *solo* occupazione, auto-close, credit/delete guard e display crediti — **mai** un importo in euro. `compute_settlement` mantiene una firma che non accetta grandezze di occupazione (barriera strutturale).
> 2. **Forfeiture delle prenotate.** Le sedute solo prenotate (Programmato) **non riducono** il rimborso: rappresentano capacità impegnata ma non servizio reso. Questo è disegno intenzionale, non un difetto.
> 3. **Riconciliazione (I6).** Ovunque sia mostrato l'asse OCCUPAZIONE (`crediti_residui`), l'UI deve rendere riconciliabile l'asse EROGATO (sedute completate) come base del rimborso — non solo nel dialog di terminazione. Vietato il recompute off-SSoT degli stati lifecycle/money nei consumatori secondari.
>
> **Conseguenze:** chiude il seam centrale come decisione esplicita; rende `unpay_rate`/`reopen`/`update_rate` soggetti all'invariante di tetto e simmetria; abilita un grep-guard "euro-da-crediti" in `check-all.sh`.

---

## 6. Test di regressione da aggiungere

1. **I3/H1:** `terminate(RIMBORSO)` su rata SALDATA superstite → `unpay` quella rata → asserire `totale_rimborsato <= totale_versato` **e** che `unpay` sia rifiutato (o riallinei) — niente clamp che maschera.
2. **I7/M1:** contratto con rate PENDENTE già soft-eliminate (piano rigenerato) → `terminate` → `reopen` → asserire che le rate storiche **non** vengano resuscitate, solo quelle del terminate.
3. **I4/M2:** rata SALDATA su contratto terminato (`quota_stornata>0`) → `PUT /rates/{id}` aumentando `importo_previsto` → asserire che **non** torni PARZIALE (o che `update_rate` rifiuti su `chiuso`).
4. **I3 (property):** griglia `(sedute_erogate, prezzo, crediti, versato)` incl. overpayment → `compute_settlement(...).importo_rimborso <= (totale_versato or 0) + 1e-9`.
5. **I1 (write-path):** `POST /terminate` con 2 Completato + 3 Programmato → asserire `totale_rimborsato==reso_su_2` e `Σ USCITA RIMBORSO == reso_su_2` (le prenotate non muovono il denaro scritto, non solo la preview).
6. **I6:** snapshot test che `ContrattiTab` e `ContractsTable` rendano lo **stesso** lifecycle per un contratto Sospeso (no divergenza badge).

---

## Cosa è già solido (conferme di invariante — risultati preziosi)

- **`valore_servizio_reso`** (`contract_settlement.py:48-67`): asse EROGATO puro, `0 <= reso <= prezzo` per costruzione (clamp `max(sedute,0)` + cap `min(.,prezzo)`) → lemma che garantisce `rimborso <= versato`. (I1/I2/I3-feeder)
- **Azzeramento residuo** (`:119` + `contracts.py:1268`): `quota_da_stornare == residuo_pre`, `+=` additivo da SSoT → `residuo()==0` deterministico anche con `quota_stornata` preesistente e in overpayment. (I4)
- **Terminate atomico** (`contracts.py:1267-1316`): stato terminale inline (mai via `_sync`), commit unico, LORDO immutabile (Strada B), rimborso non perturba `residuo()`. (I4)
- **Ledger conservativo** (`:1252-1265,1367-1381`): write-site unico per `totale_rimborsato`, fonte-unica-importo, reopen simmetrico con clamp; SALDATE e loro ENTRATA mai toccate → `versato==ΣENTRATA` intatto. (I5)
- **reopen-allowlist** (`agenda.py:333`, `rates.py:670-674`): allowlist *positiva* `==COMPLETAMENTO`; terminate non emette mai COMPLETAMENTO → nessuno stato-zombie `chiuso=False ∧ quota_stornata>0`. (I7)
- **Consumatori KPI L4** (`dashboard.py`, `movements.py`): tutti i valori euro dal SSoT (`netto_incassato`/`residuo`); `RIMBORSO_CONTRATTO` trattato come contra-ricavo single-treatment, mai entrata né costo operativo; `chiuso==False` filtra le entrate-fantasma. (I1/I5, pitfall #14 rispettato)
- **Frontend monetario** (`TerminateContractDialog`, `ContractsTable`, `ContractFinancialHero`): zero calcoli finanziari client-side, legge backend; microcopy G7.5c "le prenotate non riducono il rimborso" presente nel dialog. (I1/I6 nel punto di decisione)
- **`delete_client` guard** (`clients.py:980-993`): blocca su `chiuso==False` (flag SSoT), coerente col post-terminazione; soft-delete preserva lo storico ledger. (I7)
- **DB reale (35 contratti, 2 terminazioni id=39/21):** zero violazioni I2/I3/I5/I7; riconciliazione ledger entro 1 cent.
