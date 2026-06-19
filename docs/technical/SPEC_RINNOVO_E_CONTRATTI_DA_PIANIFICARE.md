# SPEC — Rinnovo contratto + Cruscotto "Contratti da pianificare"

**Versione:** 1.2
**Stato:** Vincolante sui criteri di accettazione — **non vincolante sull'implementazione**
**Owner:** Giacomo Verardo (AVGV Technologies)
**Destinatario:** Claude Code (architetto finale nel codebase)
**Collocazione:** `docs/technical/`
**Data:** 2026-06-19
**Tassonomia di riferimento:** `TASSONOMIA_FINANZIARIA.md` (vocabolario condiviso, vincolante)

> **Nota di versione 1.2 (2026-06-19):** secondo giro di rilievi Claude Code — chiarito che nella
> formula "Da pianificare" (§B.4) "rate non saldate" = `stato ∈ {PENDENTE, PARZIALE}` (non solo
> PENDENTE), allineato all'aging report; va sottratto anche il residuo delle rate PARZIALI. Vedi
> `TASSONOMIA_FINANZIARIA.md` §1 Asse 3.

> **Nota di versione 1.1 (2026-06-19):** corretto il rilievo di Claude Code sulla formula
> "Da pianificare" (§B.4) — la versione 1.0 usava "Booked − Billed" letterale, che doppia-conta
> acconti e rate saldate. La formula corretta è sul **residuo** (vedi §B.4 e
> `TASSONOMIA_FINANZIARIA.md` §1 Asse 3). Aggiunto rimando alla tassonomia condivisa per il naming.

> **Natura del documento.** Questo è un documento prescrittivo su *cosa deve essere vero* e
> deliberatamente silenzioso su *come ottenerlo*. I criteri di accettazione sono vincolanti.
> Ogni decisione implementativa (nomi di funzioni, struttura dei componenti, forma delle query,
> naming UI) spetta a Claude Code, che si adatta alla struttura reale del codebase — **fonte di
> verità sopra qualsiasi assunzione contenuta qui**. Dove questo documento cita codice esistente,
> lo fa per ancorare i criteri a ground-truth, non per imporre quel codice.

---

## 0. Perché esiste questo documento

Due lacune operative emerse da un caso utente reale (contratti di una trainer, "Chiara", aperti
ma privi di piano di rateizzazione) e dal flusso di rinnovo attuale. Entrambe convergono su una
stessa radice: **il sistema tratta "contratto attivo senza piano rate" come uno stato neutro,
quando invece è uno stato che richiede un'azione del trainer.**

Il bersaglio è un primo cliente reale — un personal trainer *efficienza-driven*, poco tempo,
che giudicherà il prodotto sulla fluidità del flusso economico-clienti. Per questo profilo, un
flusso che s'inceppa a metà o del denaro dovuto che il sistema non sollecita mai sono i difetti
peggiori possibili: erodono fiducia esattamente dove il prodotto promette controllo.

---

## 1. Ground-truth: cosa esiste già (NON va re-implementato)

L'analisi del codice reale (`contract.py`, `rate.py`, `routers/contracts.py`, `routers/rates.py`)
ha accertato che **buona parte dell'infrastruttura necessaria esiste già e funziona**. Va riusata,
non duplicata.

| Capacità | Dove vive | Stato |
|---|---|---|
| Stati economici sul contratto (`prezzo_totale`, `totale_versato`, `stato_pagamento`) | `Contract` | ✅ Esistono sul contratto, non servono le Rate per averli |
| Fatturato totale sui contratti aperti (anche senza rate) | `list_contracts` → `kpi_fatturato` | ✅ Già aggrega `prezzo_totale` |
| Cruscotto a stati billed/scaduto/in-arrivo (aging report) | `GET /rates/aging` | ✅ Bucket per fasce di giorni, totali, clienti con scaduto |
| Renewal chain (lettura padre + figli) | `get_contract` → `contratto_originale`, `rinnovi_successivi`, campo `rinnovo_di` | ✅ Il contratto sa già leggere la catena di rinnovo |
| Guardrail ownership (`trainer_id` dal JWT, mai dal body) | `create_contract`, `_check_client_ownership`, `_bouncer_contract` | ✅ Pattern consolidato, regola 404 mai 403 |
| Misura del disallineamento piano-rate vs residuo | `_to_response_with_rates` → `piano_allineato`, `importo_disallineamento` | ✅ Il sistema già calcola quando le rate non coprono il residuo |

**Conseguenza diretta:** questa spec è più snella di quanto sembri. Non introduce un nuovo motore
finanziario. Aggiunge **una vista mancante** e **ricuce un flusso esistente**, riusando i campi e
i pattern già presenti.

---

## 2. Fatto accertato che corregge un'assunzione

**La rateizzazione parziale è permessa dal codice.** `_cap_rateizzabile()` calcola lo *spazio
disponibile* per le rate e `create_rate` valida solo che l'importo non lo *superi* — nessun vincolo
impone di *riempirlo*. È legittimo creare rate per €500 su €2000 di residuo e fermarsi. Il campo
`importo_disallineamento` esiste proprio per misurare questo scarto.

Ne segue che i contratti aperti si distribuiscono su **tre** stati di pianificazione, non due:

1. **Pianificato** — somma rate ≈ residuo (`piano_allineato == True`).
2. **Parzialmente pianificato** — esistono rate ma non coprono il residuo (`piano_allineato == False`, rate presenti).
3. **Non pianificato** — zero rate, residuo intero da cadenzare.

Questa iterazione affronta **solo lo stato 3** (decisione founder, 2026-06-19). Lo stato 2 è
**fuori perimetro per scelta consapevole** — vedi §6.

---

## 3. Criterio A — Flusso di rinnovo

### A.1 Cosa deve essere vero

Il rinnovo di un contratto deve creare il contratto-figlio **ereditando i dati del padre**, senza
costringere il trainer a re-immettere informazioni che il sistema già conosce, e deve condurlo
**senza interruzione** alla definizione del piano rate.

### A.2 Criteri di accettazione

- Alla conferma del rinnovo, il contratto-figlio è creato con `rinnovo_di` = id del padre.
- Il figlio **pre-popola dal padre** i campi tipicamente invariati: `tipo_pacchetto`,
  `prezzo_totale`, e la `data_scadenza` derivata dalla durata del padre. Tutti i campi pre-popolati
  restano **modificabili** dal trainer prima della conferma.
- I crediti **non si trasferiscono**: il figlio nasce con i propri `crediti_totali` e
  `crediti_usati = 0`, indipendenti dal padre. (Decisione di prodotto, 2026-06-19.)
- **Sicurezza — vincolo di non-regressione:** il flusso di rinnovo segue lo **stesso pattern di
  sicurezza già implementato in `create_contract`** — `trainer_id` iniettato dal JWT del trainer
  autenticato (mai dal body, mai copiato ciecamente dal padre), verifica di ownership sul cliente
  via `_check_client_ownership`, regola **404 mai 403**. La semplificazione del flusso UX **non
  rilassa** l'ownership check. *Razionale: l'ownership della Rate è derivata via
  `Rate.id_contratto → Contract.trainer_id`; se il contratto-figlio nascesse con `trainer_id`
  errato o nullo, ogni Rata a valle erediterebbe il buco di tenancy.*
- Dopo la conferma, il trainer è condotto **direttamente** alla definizione del piano di
  rateizzazione come passo consequenziale immediato — non un'azione separata da ricordare.

### A.3 Stato attuale del flusso (diagnosi)

Oggi il rinnovo apre la schermata del piano rate **senza ulteriori azioni o suggerimenti**:
il trainer resta solo davanti a un form. La frizione non si risolve comprimendo tutto in un
click, ma rendendo il passo "definisci piano rate" **guidato e inevitabile** invece che sparso.

### A.4 Esplicitamente lasciato a Claude Code

Quante schermate esistono e come accorparle; la forma del payload di rinnovo; il meccanismo di
pre-popolamento; come rendere "guidato" il passaggio al piano rate. Il criterio è *eredità dei
dati + percorso consequenziale + pattern di sicurezza invariato*.

---

## 4. Criterio B — Vista "Contratti da pianificare" (la parte sostanziale)

### B.1 Il buco, con precisione

Il sistema di orizzonte finanziario (`GET /rates/aging`) è costruito su
`select(Rate).join(Contract)`: **itera sulle rate**. Un contratto **senza rate non produce righe**
in quella query — è strutturalmente invisibile all'intero sottosistema di solleciti
(scadute / in arrivo). Il fatturato totale (`kpi_fatturato`) lo conta, ma il trainer **non viene
mai avvisato** di andare a incassarlo. È denaro dovuto che il software tace.

Questo è il vero caso di Chiara: il contratto c'è, il numero lo include, ma siccome non ha rate
non entra in nessun promemoria.

### B.2 Cosa deve essere vero

Un contratto attivo con denaro residuo e **senza piano rate** non deve mai essere uno stato
invisibile. Deve comparire in una vista esplicita e azionabile, accanto a "rate scadute" e
"rate in arrivo".

### B.3 Criteri di accettazione

- Esiste una vista/aggregato **"contratti da pianificare"** che parte dal **contratto**, non dalla
  rata (Contract-first, non Rate-first — **deve restare separata dall'aging report**, che è
  strutturalmente cieco a questi contratti).
- La vista seleziona i contratti che soddisfano **tutte** le condizioni:
  - aperti (`chiuso == False`),
  - non eliminati (`deleted_at == None`),
  - appartenenti al trainer autenticato (`trainer_id`),
  - con residuo positivo (`prezzo_totale > totale_versato`),
  - **con zero rate associate** (nessuna `Rate` non eliminata sul contratto).
- L'importo mostrato per ciascun contratto è il **residuo** (`prezzo_totale − totale_versato`),
  coerente con il calcolo già usato altrove nel codice.
- Questi contratti entrano nel **sistema di solleciti** come categoria a sé, con un richiamo
  all'azione che porti il trainer a definire il piano rate.
- **Nessuna migrazione dati.** I contratti esistenti di Chiara compaiono automaticamente appena la
  vista sa cercarli, leggendo `prezzo_totale` / `totale_versato` già presenti.

### B.4 Cruscotto — scomposizione del fatturato (chiarezza)

> **CORREZIONE v1.1 (rilievo Claude Code).** La v1.0 definiva "Da pianificare" come
> "Booked − Billed" letterale (`prezzo_totale − rate pendenti`). **Errato:** acconti e rate **già
> saldate** non stanno né in Booked né in Billed, quindi finivano dentro "Da pianificare",
> contando come *da cadenzare* denaro **già incassato**. Inoltre confliggeva con §B.3 (che usa il
> residuo). La formula corretta è **sul residuo**, di seguito.

Il fatturato sui contratti aperti va presentato scomposto. Il vocabolario è fissato in
`TASSONOMIA_FINANZIARIA.md` (§1); qui la mappatura sui campi reali:

| Nozione | Origine dati / formula | Significato per il trainer |
|---|---|---|
| **Venduto (contratti aperti)** | `Contract.prezzo_totale` sui contratti aperti | Quanto ho venduto |
| **A rate (residuo a scadenza)** | somma dei **residui** delle `Rate` **non saldate** — `stato ∈ {PENDENTE, PARZIALE}` — (`importo_previsto − importo_saldato`) | Quanto ho già messo a scadenza, ancora da incassare |
| **Da pianificare** | `(prezzo_totale − totale_versato) − somma(residui rate non saldate)` | Quanto **resta** da mettere a rata |

- **"Rate non saldate" = `stato ∈ {PENDENTE, PARZIALE}`** (chiarifica v1.2), come l'aging report
  (`Rate.stato.in_(["PENDENTE", "PARZIALE"])`). Va sottratto anche il residuo delle rate PARZIALI:
  è denaro già messo a scadenza, non "da pianificare". In contratti parzialmente pianificati la
  formula coincide con `importo_disallineamento` già calcolato in `_to_response_with_rates`.
- Per i contratti a **zero rate** (il caso Chiara, §5 decisione #4) "Da pianificare" collassa sul
  **residuo pieno** (`prezzo_totale − totale_versato`), coerente con §B.3.
- La voce "Da pianificare" è il numero **nuovo** e dà sia la chiarezza del cruscotto sia la base
  dell'alert di §B.3.
- **Coerenza con la liquidità reale:** questa scomposizione vive accanto alle nozioni di cassa
  (Incassi da contratti / Altri incassi / Cash flow reale) definite in `TASSONOMIA_FINANZIARIA.md`.
  Stesso vocabolario, stessa UI.

### B.5 Esplicitamente lasciato a Claude Code

Se "contratti da pianificare" è un endpoint dedicato, un'estensione dell'aging response, o un
aggregato nel dashboard router; la forma della query Contract-first; dove si innesta nella UI dei
solleciti; il **naming UI in italiano** (regola 9 CLAUDE.md — es. "Da pianificare", "Contratti
aperti", "Da cadenzare": scelta riservata a Claude Code e all'orecchio nativo di Giacomo).

---

## 5. Decisioni di prodotto fissate (input di Giacomo)

| # | Decisione | Valore |
|---|---|---|
| 1 | Crediti su rinnovo | **Separati**, nessun travaso. Figlio parte da `crediti_usati = 0`. |
| 2 | Importo rata su rinnovo | Scelto **dopo** la creazione del contratto, nello step piano rate. |
| 3 | Data scadenza rata | Pre-popolata dalla durata del padre, **modificabile**. |
| 4 | Soglia alert "da pianificare" | **Caso 1 soltanto**: contratto attivo con residuo e **zero** rate. |
| 5 | Distinzione billed vs da-pianificare nel cruscotto | **Sì** (booked / billed / da pianificare). |

---

## 6. Perimetro: cosa è FUORI da questa iterazione (per scelta)

- **Stato "parzialmente pianificato"** (rate presenti ma `piano_allineato == False`): contratti con
  rate per un importo inferiore al residuo. **Fuori per scelta consapevole.** L'alert "solo se zero
  rate" lo lascia scoperto, e ciò è accettato. **Il segnale per chiuderlo in futuro esiste già:**
  `piano_allineato == False` / `importo_disallineamento > 0` in `_to_response_with_rates` è
  esattamente "questo contratto ha rate ma non coprono il residuo". Estensione nota, non buco
  involontario.
- **Cifratura dei backup automatici (G1/G5).** `_auto_backup_on_startup` produce oggi copie **in
  chiaro** del DB (`sqlite3.backup()` → `auto_*.sqlite`) contenenti dati atleta. È una tensione
  reale del `PRE_DELIVERY_SECURITY_GATE` (G5 deve essere cifrato allo standard di G1), **ma è una
  traccia separata** e non rientra in questa spec. Annotato qui solo per non perderlo.

---

## 7. Nota di conformità — regime forfettario

I tre stati (booked / billed / da pianificare) sono una **distinzione gestionale operativa**, non
*revenue recognition* GAAP. AVGV opera in **forfettario, fatturazione per cassa**: non si applica
il trattamento contabile per competenza (no *deferred revenue* come passività di bilancio). Si
adotta **solo la distinzione di stato** (firmato → messo a rata → incassato), che è utile al
trainer. Se questi numeri vengono mai esposti come "fatturato", devono restare coerenti con il
principio di cassa del forfettario.

---

## 8. Checklist di accettazione (sintesi verificabile)

**Rinnovo (A):**
- [ ] Figlio creato con `rinnovo_di` valorizzato.
- [ ] Pre-popolamento da padre (`tipo_pacchetto`, `prezzo_totale`, `data_scadenza` derivata), modificabile.
- [ ] Crediti azzerati sul figlio (no travaso).
- [ ] `trainer_id` dal JWT + `_check_client_ownership` sul cliente + 404 mai 403 (pattern `create_contract`).
- [ ] Conferma → passaggio guidato e immediato al piano rate.

**Contratti da pianificare (B):**
- [ ] Vista Contract-first separata dall'aging, con i 5 criteri di selezione (§B.3).
- [ ] Importo = residuo (`prezzo_totale − totale_versato`).
- [ ] Integrazione nel sistema di solleciti come categoria distinta.
- [ ] Scomposizione cruscotto venduto / a rate (residuo) / da pianificare — **formula sul residuo** (v1.1), coerente con `TASSONOMIA_FINANZIARIA.md`.
- [ ] Zero migrazione: i contratti esistenti compaiono automaticamente.

**Perimetro e conformità:**
- [ ] Stato "parzialmente pianificato" NON gestito (documentato come estensione futura).
- [ ] Nessuna pretesa di revenue recognition GAAP (coerenza forfettario).

---

## 9. Bridge rule

Output non banale di Claude Code derivato da questa spec (scelte architetturali sulla vista
Contract-first, sul flusso di rinnovo, sull'integrazione nei solleciti) va ricondotto a una
*learning capture* digerita in chat, e — se introduce o modifica decisioni vincolanti — riflesso
in `BUILD_LOG.md` con i consueti cross-reference.
