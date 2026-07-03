# SPEC G7.3 — Endpoint terminazione + conguaglio cablato (Strada B)

**Tipo:** specifica prescrittiva (cosa-deve-essere-vero; silente sul come). Bridge Chat→Code.
**Data:** 2026-06-24 · **Branch:** `FitManager_Studio` · **Predecessori chiusi:** G7.0→G7.2 (586 passed / 0 xfailed).
**Stato:** ✅ **IMPLEMENTATA** (2026-06-24) in **due commit**: `9acd2c5` (G7.3a core) + `3f1404b` (G7.3b ritiro PUT chiuso + migrazione test + frontend). Suite **598 passed / 0 xfailed**, check-all verde. I delta/conferme della verifica sul codice sono marcati `[Bridge Code 2026-06-24]`.
**Mappa di verità:** `AUDIT_PRE_G7.3_RAGGIO_STORNO.md` (snapshot ratificato — coordinate riverificate sul vivo) · `FINANCIAL_DOMAIN_MODEL.md` Strada B §2/§9.5 · `contract_settlement.py` (modulo puro, G7.1) · `contract_state.py` (SSoT residuo/netto, G7.1).
**Tesi falsificabile:** *esiste un endpoint che termina un contratto vivo producendo UN atto atomico — conguaglio calcolato + scritture cassa + stato terminale — senza violare l'invariante `totale_versato == Σ ENTRATA`, senza riaprirsi da solo, legacy-safe su contratti-muti arbitrari, e senza che il software affermi mai un obbligo legale.*

> ⚠️ **Primo passo obbligatorio (come per G7.2): ricognizione call-site sul codice vivo PRIMA di scrivere.** Questa spec mappa il perimetro dall'audit ratificato, ma l'audit è uno snapshot. Verifica sul codice reale: (a) la firma attuale di `compute_settlement` e quali argomenti vuole; (b) il cascade di `delete_contract` e quali rate/movimenti tocca; (c) il punto esatto in cui `_sync_contract_chiuso` viene chiamato dagli altri flussi (per NON imitarlo); (d) la forma reale dei contratti-muti id 4/9/13 sul crm.db dev. Se il codice smentisce un punto di questa spec, **il codice vince** e me lo segnali — non adattare il codice alla spec.

---

## 0bis. Esito dell'implementazione `[Bridge Code 2026-06-24]`

Ricognizione call-site eseguita sul vivo prima di scrivere; spec accurata sul perimetro. **5 divergenze/raffinamenti code-grounded** rispetto alla prosa della spec (il codice/AC vincono, da portare a Bridge per G7.4):

1. **`motivo_chiusura` DERIVATO dall'esito, NON passato dal trainer.** Conflitto §1 ("riceve il motivo scelto dal trainer") vs §9/AC-7.3-9 ("mappatura esito→motivo"): vince l'AC (criterio falsificabile). Il body `ContractTerminate` ha solo `metodo_rimborso?`/`note?`/`data_chiusura?` — mai il motivo. Mappa: RIMBORSO→`TERMINAZIONE_RIMBORSO`, SALDO_A_PERDERE→`TERMINAZIONE_DECADENZA`, NULLO→`CONSUNZIONE`. **Mai COMPLETAMENTO.** Confermato dal founder (scelta esplicita).
2. **Le "due gambe" CONVIVONO**, non sono mutuamente esclusive come legge la prosa di §1. Il modulo G7.1 ritorna `quota_da_stornare = residuo_corrente` **sempre** + `importo_rimborso` solo se overpaid. Esempio: prezzo 1000, versato 500, 2 sedute su 10 → reso 200 → **rimborso 300 E storno 500** → `netto_incassato=200=reso`, `residuo()=0`. È il comportamento (già testato) del modulo, non un cambio. Implementato: storno SEMPRE + gamba rimborso condizionale.
3. **`sedute_erogate` = Event `Completato`** (servizio reso, IMPL_PLAN §4.2), NON `!= "Cancellato"` (che è `crediti_usati` dell'auto-close). La nota di ricognizione che le aveva confuse è stata corretta: il conguaglio valuta ciò che è stato RESO, non ciò che è solo prenotato.
4. **Raffinamento a §8 (migrazione test):** oltre al presidio-NULL (decisione A, ORM), **2 mini-presidi** — `test_aging_excludes_closed_contracts` e `test_pending_rate_on_closed_contract_is_phantom_excluded` — sono andati a **ORM, non a terminate**: testano il *filtro-chiuso* (esclusione di un contratto chiuso che MANTIENE una rata viva), e il soft-delete di terminate rimuoverebbe la rata → l'esclusione passerebbe per la cancellazione, mascherando il filtro. Discriminante: il test ha bisogno che la rata **sopravviva** alla chiusura? → ORM. Gli basta lo stato chiuso? → terminate. Gli altri 13 → terminate (canale canonico) perché lì l'esclusione è lifecycle-based.
5. **Entry-point UI oltre i 2 bottoni del Blocco 3:** aggiunto "Termina" al dropdown `ContractsTable` per ogni contratto non-chiuso — senza, il caso d'uso PRINCIPALE (§5, recesso anticipato di un ATTIVO) non avrebbe avuto un punto d'accesso (la `SuspendedCard` copre solo i SOSPESO). I due bottoni del Blocco 3 ("Chiudi con conguaglio" + "Decadi") sono diventati **un** "Termina": l'endpoint unico copre entrambi gli esiti (l'esito derivato distingue rimborso da decadenza).

**Conferme della ricognizione:** cascade `delete_contract` tocca TUTTE le rate (incl. SALDATE) + tutti i CashMovement → NON riusabile verbatim (B-3); `_sync_contract_chiuso` allowlist G7.2 protegge le riaperture, ma terminate non lo chiama comunque (B-2-attiva); `cash_categories.is_contract_outflow`/`CATEGORIA_RIMBORSO_CONTRATTO` esistenti; `ContractResponse` ha già le 4 colonne + `netto_incassato` computed; `compute_settlement` firma confermata. **Lezione livello-3** (in `BUILD_LOG.md`): la migrazione meccanica può lasciare un test *verde ma morto* per ogni presidio di un filtro-su-stato che mantiene viva la condizione esclusa.

---

## §0 — Sblocco del blocco esterno: la policy diventa default dichiarato, non numero cablato

G7.3 era bloccato su 6 decisioni esterne. **4 sono neutralizzate** da una decisione di design del founder (ratificata): la `SettlementPolicy` non è un valore da concordare col tributarista prima di poter scrivere — è **configurazione con un default difendibile + avviso**. Le altre 2 (#3, #5) sono decisioni-sui-dati prese dal founder e cablate qui sotto.

**Il principio non-negoziabile (confine di posizionamento, eredita ADR-014).** Il software **calcola un conguaglio proposto** con un metodo standard; **non afferma mai** che l'importo sia l'obbligo legale del trainer verso il cliente. È un *downgrade epistemico deliberato*: da "ti dico quanto devi restituire per legge" a "ti propongo un calcolo pro-rata sulle sedute; verifica con le condizioni del tuo contratto". Questo downgrade è ciò che rende G7.3 simultaneamente **sicuro legalmente** e **costruibile subito**. La label e il microcopy sono **load-bearing quanto il numero**: una preview che dicesse "Importo da rimborsare: €X" senza il framing di proposta sarebbe una regressione di posizionamento, non un dettaglio estetico.

**Default:** `SettlementPolicy.mode = 'pro_sedute'` (già il default PROVISIONAL del modulo, ora promosso a default *dichiarato*). Conguaglio pro-rata sulle sedute erogate — il metodo neutro e trasparente riconosciuto nel settore.

**Fuori-scope esplicito (giro successivo, NON G7.3):** la pagina Impostazioni che espone l'override della policy (cambio `mode`, percentuali custom, "rimborso integrale" / "nessun rimborso"). G7.3 nasce con `pro_sedute` come default hard-coded + microcopy che dichiara il default + preview che mostra l'esito. **Il pacchetto G7.3 non tocca alcuna pagina Impostazioni.**

---

## §1 — L'endpoint: due gambe, un atto atomico

Un endpoint `terminate` (più un `preview`/dry-run — vedi §4) sul contratto. Riceve il `motivo_chiusura` scelto dal trainer e produce, in **un solo commit**, l'esito calcolato da `compute_settlement`.

> `[Bridge Code]` Il `motivo_chiusura` NON è scelto dal trainer: è **derivato** dall'esito (vedi 0bis.1 + §9/AC-7.3-9). Il body non lo contiene.

Le **due gambe** sono i due esiti monetari che il modulo già distingue (G7.1):
- **RIMBORSO** (`versato > valore_servizio_reso`): il cliente ha pagato più di quanto consumato → scrittura di una USCITA `RIMBORSO_CONTRATTO` + incremento di `totale_rimborsato`.
- **SALDO_A_PERDERE / write-off** (`versato ≤ valore_servizio_reso`): il cliente ha consumato almeno quanto versato → nessun movimento di cassa, ma il residuo va azzerato → incremento di `quota_stornata`.
- (**NULLO**: conguaglio esattamente 0 → nessuna scrittura monetaria; il contratto si chiude comunque.)

> `[Bridge Code]` Le due gambe **convivono** (0bis.2): lo **storno** dell'attuale residuo avviene SEMPRE (azzera `residuo()`), il **rimborso** si aggiunge solo se l'esito è RIMBORSO.

**Atomicità:** un singolo `commit`. Se una qualsiasi scrittura fallisce, nessuna parte dell'atto persiste. Specchio del flusso di `incassa_residuo` (G6), che è il gemello-in-entrata di questo.

---

## §2 — Fonte-unica-importo (vincolo §4.6, load-bearing)

`compute_settlement` riceve il residuo dal caller in **una sola variabile**. G7.3 deve:
1. calcolare `residuo_corrente = contract_state.residuo(contract)` **PRE-storno** (cioè prima di scrivere `quota_stornata`, quando `quota_stornata` è ancora 0);
2. passare quel singolo valore a `compute_settlement` come `residuo_corrente`;
3. usare **lo stesso identico importo** restituito (`importo_rimborso` per la gamba RIMBORSO; `quota_da_stornare` per il write-off) sia per il `CashMovement` **sia** per l'incremento del campo (`totale_rimborsato +=` o `quota_stornata +=`).

**Mai** ricalcolare l'importo una seconda volta per il movimento e un'altra per il campo. Un solo importo, una sola fonte, due usi. (È la lezione del residuo-inline che driftava: un secondo calcolo "byte-identico oggi" diverge domani.)

**AC-7.3-1.** Test: dopo un RIMBORSO, `CashMovement.importo == totale_rimborsato_delta` esattamente (stesso valore al centesimo). Dopo un write-off, `quota_stornata_delta == residuo_corrente_pre_storno` esattamente. `[Bridge Code] ✅ test_terminate_rimborso_fonte_unica_importo + test_terminate_write_off_fonte_unica.`

---

## §3 — BLOCKER vivi (dall'audit ratificato — questi vivono DENTRO l'endpoint)

### §3.1 — B-2-attiva: terminate setta lo stato DIRETTAMENTE, mai via `_sync_contract_chiuso`

`terminate` scrive `chiuso`/`motivo_chiusura`/`data_chiusura` **direttamente** sul contratto. **Non chiama mai** `_sync_contract_chiuso`.

**Perché (meccanismo esatto):** un SOSPESO terminato (saldato, ma con crediti residui) ha `should_be_chiuso == False` secondo la logica di auto-close (è saldato ma i crediti non sono esauriti). Se `terminate` chiamasse `_sync` ingenuamente "per sincronizzare", `_sync` vedrebbe `should_be_chiuso == False` e **resetterebbe `chiuso=False` nello stesso commit**, auto-annullando la terminazione appena scritta. La guardia allowlist G7.2 lo fermerebbe *solo se* il motivo fosse già scritto prima della chiamata — ma far dipendere la sicurezza dall'ordine è fragile. La regola pulita: terminate **non imbocca affatto** quella via.

**AC-7.3-2 (test dedicato, load-bearing).** Termina un contratto **SOSPESO** (`lifecycle == SOSPESO` PRIMA della terminazione). Verifica che dopo il commit il contratto sia **ancora `chiuso=True`**. `[Bridge Code] ✅ test_terminate_sospeso_resta_chiuso.`

### §3.2 — B-3: soft-delete selettivo, mai le SALDATE né i loro CashMovement

`terminate` soft-elimina **SOLO le rate non-saldate** (PENDENTE/PARZIALE). **Non tocca** le rate SALDATE, **né** i loro `CashMovement` ENTRATA.

**Perché (meccanismo esatto):** l'invariante-àncora è `totale_versato == Σ ENTRATA`. `totale_versato` è LORDO immutabile (Strada B). Se terminate soft-eliminasse una rata SALDATA e il suo CashMovement ENTRATA, `Σ ENTRATA` scenderebbe ma `totale_versato` resterebbe lordo → **divergenza permanente**. E **NON riusare verbatim il cascade di `delete_contract`**: quel cascade tocca *tutte* le rate (incl. SALDATE) e *tutti* i CashMovement — terminate **non** soft-elimina il contratto, quindi riusarlo darebbe `Σ ENTRATA < totale_versato` permanente.

**AC-7.3-3 (riconciliazione, gemello del canarino G6).** Dopo una terminazione con write-off di rate non-saldate: `Σ ENTRATA (dal mastro reale) == totale_versato` ancora regge. E la nuova leg: `Σ USCITA RIMBORSO == totale_rimborsato`. Il test interroga il **mastro reale** (CashMovement). `[Bridge Code] ✅ test_terminate_reconciliation_e_soft_delete_selettivo (verifica anche SALDATA + suo CashMovement sopravvivono).`

---

## §4 — Preview / dry-run: l'esito è visibile PRIMA della conferma

Il trainer deve vedere l'esito calcolato (quale delle tre gambe, quale importo) **prima** di confermare. Il default `pro_sedute` **non esegue mai silenziosamente** — propone, l'utente ratifica.

Serve un percorso `preview` (dry-run) che, dato il contratto + il `motivo_chiusura` candidato, restituisce il `Settlement` calcolato (esito + importo + base di calcolo: sedute fatte / sedute totali) **senza scrivere nulla**. Il `terminate` reale esegue ciò che la preview ha mostrato.

**Il microcopy è parte della spec, non cosmesi (eredita §0).** La preview presenta l'importo come **proposta** (es. *"Conguaglio calcolato (metodo pro-rata sedute): €X. Verifica con le condizioni del contratto."*), **mai** come obbligo (*"Da rimborsare: €X"* è vietato). I tre esiti hanno tre framing distinti e leggibili:
- RIMBORSO → "risulta un rimborso di €X a favore del cliente";
- SALDO_A_PERDERE → "il cliente ha già consumato il servizio; nessun rimborso, il residuo di €Y viene azzerato";
- NULLO → "nessun conguaglio".

> `[Bridge Code]` Il backend ritorna `ContractSettlementPreview` con campo `messaggio` (framing di proposta server-side, così non si può perdere lato FE) + `metodo_rimborso_richiesto`. `GET /contracts/{id}/settlement-preview`.

**AC-7.3-4.** La preview non produce alcuna scrittura (zero CashMovement, zero mutazione di `quota_stornata`/`totale_rimborsato`/`chiuso`). `[Bridge Code] ✅ test_settlement_preview_no_writes.`

---

## §5 — Legacy-safe: l'endpoint regge su contratti-muti arbitrari (#3 del founder, forma forte)

**Decisione founder #3:** `terminate` **accetta contratti con scadenza FUTURA** — è il caso d'uso principale (recesso anticipato). Coerente col modello: la terminazione è l'atto che interrompe l'asse-tempo prima della scadenza naturale.

**Ma la forma forte della decisione (logica sacra di retrocompatibilità):** `terminate` deve essere **null-safe e legacy-safe su contratti che un crm.db pre-modifica produce** — campi a NULL, date incoerenti, rate strane. **La correttezza di `terminate` non deve MAI dipendere dall'aver pre-bonificato il contratto.** Ragione: sul DB di Chiara i contratti-muti arrivano com'è all'aggiornamento; se terminate assumesse campi bonificati, si romperebbe sul legacy reale.

Implicazioni cablate:
- il calcolo `pro_sedute` deve avere comportamento dichiarato quando `crediti_totali` è NULL (il modulo già fa "tutto-reso se senza monte-sedute") — e quel ramo va **testato sul caso legacy**, non solo sul pulito;
- `residuo()` è già `getattr`-safe (G7.1); terminate non deve introdurre nuove assunzioni di non-null;
- nessuna guardia di terminate deve rifiutare un contratto solo perché ha la *forma* di un muto legacy.

**AC-7.3-5 (golden-fixture da clone reale, lezione già applicata 2× nel progetto).** Il test del caso-muto va esercitato su un fixture **derivato da ORM/clone reale**, **non** costruito da `ContractCreate` (il boundary attuale *rifiuta* ciò che rende muto un contratto). Verifica: terminate su un muto-legacy (scadenza futura, campi sparsi a NULL) produce un esito coerente senza crash e senza violare gli invarianti. `[Bridge Code] ✅ test_terminate_legacy_muto_crediti_none (Contract via ORM, crediti_totali=None → tutto-reso).`

**Boot-align di Chiara (non-azione, da preservare):** l'allineamento al boot porta **schema, non atti**. I muti di Chiara dopo l'aggiornamento restano contratti aperti con le 4 colonne G7.0 a default — diventano legacy-NULL, mai terminati da nessuno finché Chiara non clicca terminate. **G7.3 non aggiunge alcuna logica che termini contratti automaticamente al boot.**

---

## §6 — `kpi_incassato` → `netto_incassato()` (HIGH, dentro G7.3)

L'unico vero sovrastimante aggregato. Oggi `kpi_incassato` somma `totale_versato` (incl. chiusi) → sotto G7.3 la card "Incassato" sovrastima di Σ rimborsato (mente). Il rimpiazzo `netto_incassato()` è **già pronto e inutilizzato** (G7.1).

**Edit obbligatorio in G7.3** (non G7.5): `kpi_incassato` deve sommare `netto_incassato(c)` invece di `totale_versato`. Si rompe nell'**istante del primo storno**, quindi vive qui.

**AC-7.3-6.** Dopo un terminate con RIMBORSO, la card "Incassato" riflette il **netto**. `[Bridge Code] ✅ (`contracts.py` kpi_incassato → Σ cstate.netto_incassato; byte-invariante finché rimborsato=0, coperto da suite 598).`

**Confine — NON toccare gli altri aggregati cassa.** `dashboard.py` ledger-alert/`divergent_count` e `get_reconciliation` **REGGONO** sotto G7.3 (refund=USCITA fuori dal JOIN ENTRATA). Usare `netto` lì li **romperebbe**. L'intervento sull'àncora è solo ADDITIVO. `kpi_fatturato` è invariante (legge `prezzo_totale`) — non si tocca.

---

## §7 — Esclusione-burn (DENTRO G7.3 — unica esclusione-cassa che entra ora)

La catena `_compute_variable_burn_rate` → `_build_cash_protection` è l'**unica** query con profilo-**ALLARME**: un RIMBORSO_CONTRATTO è una USCITA con `id_spesa_ricorrente` nullo → matcha il filtro burn-variabile → gonfia `costo_operativo` → può flippare la protezione-cassa a **CRITICO falso** nell'istante del primo storno. Non è drift cosmetico — è un allarme falso su dati di trainer reali.

**Edit in G7.3:** escludere `RIMBORSO_CONTRATTO` dal filtro USCITA-variabili del burn, via il predicato **già esistente** `cash_categories.is_contract_outflow` (P0). One-liner. È **no-op finché non esiste un rimborso reale**, ed è **esercitabile end-to-end nello stesso test del primo terminate** → niente dead code non testabile.

**Criterio di confine adottato (lezione di scope):** la linea G7.3/G7.5 è *ciò che il primo storno reale attiva e quindi rende testabile ORA* (la burn-exclusion) *vs ciò che richiede un rimborso simulato* (le altre ~7 esclusioni → G7.5).

**`_build_cash_protection` è risanata in G7.3 GRATIS** (dipendenza a valle dal burn — ingresso-burn unico, `[Bridge ratify 2026-06-24]`). Nessun fix proprio in G7.3; in G7.5 resterà solo da *verificare* che non legga il rimborso per un'altra via.

**AC-7.3-7.** Nel test del primo terminate-con-RIMBORSO: `_compute_variable_burn_rate` **non** include il RIMBORSO_CONTRATTO. `[Bridge Code] ✅ test_terminate_burn_esclude_rimborso (rimborso datato mese-scorso per cadere nella finestra burn; coalesce null-safe).`

---

## §8 — Migrazione delle scorciatoie test + presidio-NULL (#5 del founder)

`chiuso` sparisce da `ContractUpdate` → i 16 payload `PUT {"chiuso": True}` daranno 422. Vanno migrati al canale definitivo (`terminate`) — **una volta sola**.

**Distinzione (dall'audit):**
- **~13 scorciatoie** = chiusure usate come *setup* per testare altro. Migrazione meccanica a `terminate`.
- I **2 forward-guard ORM** (`test_lifecycle_audit:200/:224`) **non si toccano** — scrivono già via ORM.
- **1 presidio travestito** (`test_lifecycle_audit:164`, ramo NULL della reopen-allowlist) → **decisione #5, NON meccanica.**

**Decisione founder #5: ricondurre a simulazione ORM (opzione A).** Il test va riscritto perché costruisca lo stato `chiuso=True ∧ motivo=NULL` **direttamente sulla sessione ORM**, non via API. Continua a esercitare il ramo NULL — fabbricando il NULL a mano.

**Perché A (non ritiro):** post-G7.3 lo stato `chiuso=True ∧ motivo=NULL` non è più producibile via API (terminate setta sempre un motivo) → diventa esclusivamente uno stato **legacy**. Ma il ramo NULL della allowlist **è ancora load-bearing**: protegge quei contratti legacy dall'essere riaperti da un edit d'agenda. Migrarlo *meccanicamente* a `terminate(CONSUNZIONE)` lo lascerebbe verde ma morto.

**Vincolo collegato:** la migrazione NON deve introdurre una bonifica retroattiva dei contratti legacy-NULL. I legacy-NULL restano NULL; il loro ramo li protegge.

> `[Bridge Code]` **Raffinamento §8 (0bis.4):** oltre al presidio-NULL, **2 mini-presidi** (`test_aging_excludes_closed_contracts`, `test_pending_rate_on_closed_contract_is_phantom_excluded`) sono andati a **ORM, non a terminate** — testano il filtro-chiuso MANTENENDO una rata viva, che il soft-delete di terminate rimuoverebbe (presidio mascherato). Migrazione finale: **13 → terminate, 3 → ORM**. `test_close_contract_via_update` → riscritto come `test_close_contract_via_terminate` (test del canale nuovo).

**AC-7.3-8.** `test_lifecycle_audit:164` riscritto via ORM: esercita ancora `chiuso=True ∧ motivo=NULL` + edit-agenda → non riapre. Verde **e** vivo. Le ~13 scorciatoie migrate; suite verde. `[Bridge Code] ✅ suite 598 passed.`

---

## §9 — Decisione #2 (semantica enum) — input founder con default

I 4 valori di `MotivoChiusura` **esistono** (G7.0/G7.1). Ciò che #2 fissa è la **semantica d'assegnazione** dell'endpoint:
- RIMBORSO calcolato → `TERMINAZIONE_RIMBORSO`;
- write-off calcolato → `TERMINAZIONE_DECADENZA`;
- chiusura **money-neutral** (conguaglio ~ 0) → **CONSUNZIONE** (default).

**(COMPLETAMENTO resta riservato all'auto-close: terminate non lo assegna mai, altrimenti la reopen-allowlist G7.2 riaprirebbe le terminazioni.)**

**AC-7.3-9.** terminate non assegna mai `COMPLETAMENTO`. La mappatura esito→motivo è coerente. `[Bridge Code] ✅ test_terminate_mai_completamento + test_terminate_{rimborso,write_off,nullo} verificano la mappa. NB: il motivo è DERIVATO server-side (0bis.1), non scelto.`

---

## §10 — Cosa G7.3 NON tocca (anti-scope-creep)

- **Le ~7 esclusioni-cassa residue** (movement-stats, le 2 forecast, financial-trend, monthly_revenue, flow_hint **+ flow_filter in coppia**, past_var/past_total) → **G7.5**.
- **BLOCKER B-4** (financial-trend doppia decomposizione) → **G7.5**.
- **`_build_cash_protection`** fix proprio → non esiste (risanato a monte via burn in §7).
- **La rinumerazione "8+8 query"** → da ratificare in **G7.5** (governance: `api/CLAUDE.md`=8 vs altri=9). **Non** consolidare un numero qui.
- **La pagina Impostazioni / override policy** → giro successivo (§0).
- **`reopen`/`unterminate`** → **G7.4**.
- **Giro 2 vocabolario** → dopo G7.
- **Gli aggregati-àncora che REGGONO** (ledger-alert, reconciliation, kpi_fatturato) → non toccare (§6).

---

## §11 — Definizione di "fatto" per G7.3

1. Endpoint `terminate` + `preview` (due gambe, atomico, fonte-unica-importo) — AC-1, AC-4. `[✅]`
2. B-2-attiva (setta diretto, mai `_sync`) — AC-2. `[✅]`
3. B-3 (soft-delete selettivo, invariante-àncora regge) — AC-3. `[✅]`
4. Legacy-safe su muti-arbitrari, golden-fixture da clone reale — AC-5. `[✅]`
5. `kpi_incassato`→netto — AC-6. `[✅]`
6. Esclusione-burn dentro G7.3 — AC-7. `[✅]`
7. Presidio-NULL ricondotto a ORM + ~13 scorciatoie migrate — AC-8. `[✅ + 2 mini-presidi a ORM, 0bis.4]`
8. Mappatura esito→motivo, mai COMPLETAMENTO — AC-9. `[✅ motivo derivato]`
9. Microcopy "calcolo proposto ≠ obbligo legale" nella preview — §0/§4. `[✅ campo messaggio backend]`
10. Suite verde; check-all verde; primo storno reale verificato end-to-end. `[✅ 598 passed]`

**Commit:** scelta founder = **due commit** (G7.3a core `9acd2c5` + G7.3b ritiro/migrazione/frontend `3f1404b`), entrambi rilasciabili. Diario: `BUILD_LOG.md` 2026-06-24 "G7.3".
