# SPEC_G8.4_TRASPARENZA_FINANZIARIA_FE

**Tipo:** specifica prescrittiva (cosa-deve-essere-vero; silente sul come dove possibile). Bridge Chat→Code.
**Data:** 2026-06-30 · **Branch:** `FitManager_Studio`
**Stato:** 🟡 **IN CORSO** — **fetta-RIGORE (F1+F5) ✅ COMPLETATA 2026-07-06**: F1 `5086045` (netto SSoT + `saldo_progressivo` + guard semantico FE-no-money-math) · F5.a `4f2d07c` (page 511→280 + EventsTable condivisa) · F5.b `ab38c90` (dialog 357→192, table 370→166) · F5.c `1978572` (PaymentPlanTab 897→198). Suite full **836**, verifica Playwright LIVE su crm.db reale (lista+dettaglio+Storico «Saldo» per riga+dialog Termina, zero submit). **fetta-UX-presentazionale (F2+F6) ✅ COMPLETATA 2026-07-07** (`0b80bc8`): hero con disclosure D-1 (collassati SOLO Acconto · Da Rateizzare-se-coperto · riga Crediti; segnali e sub-label lordo−rimborsi SEMPRE visibili; Da Rateizzare resta fuori dal toggle quando il piano non copre), righe ledger collassabili alla coda-6 (footer sempre), token decorativi → zinc (F6); AC-G84-5 = 3 render-test vitest (85/85), verifica visiva LIVE. **Resta: fetta-comportamentale (F3.a/c/d/e — F3.f GIÀ in codice) + apertura G8.5**. RI-GROUNDATA sul codice vivo 2026-07-06 (§0-bis). **Decisioni founder ratificate 2026-06-30:** D-3 = rimborso *goodwill* del non-svolto (scorporato in **G8.5**, nuovo money-path con ADR proprio) · sequenza = tutte le fette UX-pure ora (F1/F2/F3/F5/F6), F4 governance-first · collocazione = file dedicato (questo). **Decisioni founder ratificate 2026-07-06** (evidenza: `docs/archive/RICERCA_COMPETITOR_TRASPARENZA_FINANZIARIA_2026-07-06.md`, leggi L1-L6): **D-1 EMENDATA** = lista always-visible §F2 confermata + breakdown «lordo − rimborsi» promosso a **sub-label always-visible** (pattern G9.4-bis.3, legge L2) · **D-2** = colonna **«Saldo»** per riga + footer **«Saldo movimenti del contratto»** (mai "netto" sul ledger, legge L1) → **ADR-019 Addendum IV** (D-LEDGER-SALDO).
**Blocco proposto:** **G8.4** — remediation UX/rigore della *presentazione* finanziaria sul frontend (estende il programma G8 «integrità contabile + trasparenza CRM-grade»). Conseguenza di decisioni già accettate (ADR-016 EROGATO · ADR-017 rinvio-libera-credito · ADR-018 bilateralità · ADR-019 cassa-immutabile/reopen-ricalcola · ADR-020 wallet · ADR-021 INV-RATE); **nessun nuovo ADR**, candidato Addendum ad ADR-019 (relabel ledger) se necessario.
**Mappa di verità:** `docs/adr/ADR-019-*.md` (D-CASSA-VISIBILE) · `docs/adr/ADR-018-*.md` (D-SCELTA) · `docs/adr/ADR-016-*.md` (EROGATO) · `docs/technical/FINANCIAL_DOMAIN_MODEL.md` · `docs/archive/specs/SPEC_INTEGRITA_CONTABILE_E_WALLET.md` (programma G8) · `frontend/src/lib/contract-status.tsx` (SSoT vocabolario colore/stato) · `api/services/contract_state.py` · `api/routers/contracts.py` · `tools/scripts/check-all.sh`.

> **Nota sulle coordinate.** I riferimenti `file:riga` sono lo snapshot del 2026-06-30 (audit FE finanziario + workflow di grounding `wf_97b319ca-997`). Gli esiti sono durevoli; le righe vanno riverificate a implementazione (prassi `AUDIT_PRE_G7.3`).

---

## Impact map

- **Obiettivo:** rendere il frontend finanziario *terra-terra* (zero complessità percepita dal PT non-contabile) **senza toccare l'asse DENARO** — eliminando i ricalcoli di denaro lato client, nascondendo la profondità contabile dietro progressive-disclosure (mai i segnali critici), e disciplinando colore/accessibilità. Surfacing del SSoT esistente, non nuova logica.
- **Layer toccati:** frontend (componenti contratto, dialog terminazione, storico, vocabolario colore); backend SOLO additivo e read-model (campo `saldo_progressivo` su `ContractMovementItem`, campo advisory `azione_consigliata` su settlement-preview); test; `check-all.sh` (grep-guard FE «no money-math»).
- **Invarianti da preservare (asse DENARO byte-identico):** `residuo()` net-aware · `residuo == 0 ⟺ saldato` · `totale_versato == Σ ENTRATA[id_contratto]` (Strada B, lordo immutabile) · cassa-immutabile / integrità di periodo (ADR-019) · asse EROGATO/forfeiture (ADR-016/018) · `Rinviato` fuori occupazione (ADR-017) · gate bilaterale 422 (ADR-018 D-SCELTA) · INV-RATE (ADR-021) · reopen esplicito / reopen-allowlist.

**Tesi falsificabile:** dopo G8.4, (1) nessuna superficie finanziaria mostra due numeri "netto" divergenti per lo stesso contratto; (2) nessun segnale finanziario *critico/warning* è nascosto dietro un toggle; (3) l'asse DENARO è byte-identico — zero `CashMovement` creati/modificati, zero variazione di `residuo()`/`netto_incassato()`/conteggi su qualunque DB reale.

---

## 0. Problema reale da correggere (sintesi audit 2026-06-30)

La logica G7/G8 è grado-enterprise e corretta sull'asse DENARO; il difetto è che **la profondità trapela al PT** e in due punti il FE **ricalcola denaro** invece di leggere il SSoT.

1. **Doppio "netto" sulla stessa entità (RIGORE).** Il FE deriva l'"incassato netto" in almeno 4 punti (`ContractFinancialHero.tsx:42`, `ContractsTable.tsx:181`, `PaymentPlanTab.tsx:227-228`, `ContrattiTab.tsx`) come `versato − rimborsato`, mentre il backend lo espone **già** come SSoT (`netto_incassato`, `api/schemas/financial.py:152-159` → `contract_state.py:90-95`; presente in `types/api.ts:748`). In parallelo lo Storico (`ContractHistoryTab.tsx:81-90`) ricostruisce un **saldo progressivo** sommando `contract.movimenti` e ne deriva un *secondo* "Netto incassato". Rischio: numeri "netto" diversi sulla stessa pagina/entità.
2. **Profondità contabile esposta di default (TERRA-TERRA).** Hero a 6-10 KPI + banner di riconciliazione + Storico a doppio ledger CRM-grade: corretto, ma è densità da gestionale di palestra mostrata sempre.
3. **Settlement bilaterale = quiz a 3 vie nel momento peggiore (TERRA-TERRA).** `TerminateContractDialog.tsx:256-283` chiede al PT una decisione contabile (incassa/credito/rinuncia) senza una raccomandazione, su un controllo che comunica la selezione **solo col colore** (manca `aria-pressed`).
4. **Workaround manuale esposto come istruzione (TERRA-TERRA).** `ContractFinancialHero.tsx:202-210` istruisce il PT a una corvée a due passi: *«Per rimborsare il non svolto: usa Riapri e poi Termina»*.
5. **Violazioni LOC + import a metà file (RIGORE).** `PaymentPlanTab.tsx` (897 LOC), `contratti/[id]/page.tsx` (511 LOC, con import inline a riga 299/409/410/411), `TerminateContractDialog.tsx` (357 LOC) superano il comandamento sacro dei 300 LOC. *(Correzione all'audit: in `TerminateContractDialog` gli import sono già tutti top-of-file 16-41; l'import-a-metà-file è in `contratti/[id]/page.tsx`.)*
6. **Colore semi-semantico (TERRA-TERRA).** L'hero mischia colore-valenza (emerald/amber/red) e colore-decorativo di categoria (violet/blue/indigo su Valore/Acconto/Crediti) → diluisce il semaforo su un pannello finanziario.

---

## 0-bis. Ri-grounding 2026-07-06 (codice vivo post G9 / G9.4-bis / G7.8-bis)

Verifica adversariale su codice vivo (2 agenti read-only) + ricerca competitor su fonti ufficiali
(`docs/archive/RICERCA_COMPETITOR_TRASPARENZA_FINANZIARIA_2026-07-06.md`). Esiti che EMENDANO questa spec:

1. **F1 confermata, ma perimetro corretto:** i ricalcoli inline vivi sono `ContractFinancialHero.tsx:42-45`,
   `ContractsTable.tsx:181-183` (netto + ratio derivata) e `ContractHistoryTab.tsx:81-90` (accumulo saldo in
   `useMemo` + footer «Netto incassato»). **`PaymentPlanTab.tsx` NON viola F1** (legge già i campi SSoT
   `importo_da_rateizzare`/`somma_rate_pendenti`; l'accusa dell'audit 2026-06-30 era errata — resta solo la
   violazione LOC). `TerminateContractDialog` è conforme (il `walletResto` a riga ~94 è cap-locale legittimo).
2. **F1.d cambia forma: test semantico, non grep-guard.** G9.4-b (2026-07-05) ha ritirato i grep-guard ADR a
   favore di `tests/test_semantic_guards.py` (eseguito da `check-all.sh`); il guard «FE no money-math» nasce
   direttamente in quella forma (pattern-scan sorgenti FE con allowlist delle eccezioni cap-locali, dentro un
   test collectable — non una riga bash).
3. **Template interno già shippato:** la card Entrate di `/cassa` (G9.4-bis.3, `cassa/page.tsx:817-823`) mostra
   `Lorde X · Rimborsi −Y` come sub-label — è il pattern che F1/F2 riusano per il netto-POSIZIONE (D-1 emendata).
4. **F5 perimetro aggiornato:** `ContractsTable.tsx` è a **370 LOC** ed entra nello split;
   `ContractFinancialHero` è a 263 LOC (conforme). Violazioni LOC (pre-F5): PaymentPlanTab 897 ·
   contratti/[id]/page.tsx 511 · ContractsTable 370 · TerminateContractDialog 357.
   *(Correzione 2026-07-06 sera: il ri-grounding iniziale affermava che gli import inline di
   `[id]/page.tsx` fossero già spariti — FALSO, erano ancora a riga 299/409-411; l'audit originale
   aveva ragione. Risolti dallo split F5.a. Lezione: anche il ri-grounding va verificato sul file.)*
5. **Scope IN (residui già assegnati a G8.4 da INDEX/G7.8-bis):**
   - **display `sedute_penali`** — il backend lo espone già su `ContractSettlementPreview` (G7.8-bis);
     manca il sync in `types/api.ts` e il display nel breakdown del dialog Termina (→ F3.e);
   - **validazione nota-abbuono** — ADR-018 D-IMPORTO: `RINUNCIA_ESPRESSA` = nota obbligatoria; il dialog FE
     deve bloccare il submit senza nota (il backend resta autorità 422) (→ F3.f).
6. **Backend confermato pronto:** `netto_incassato` computed_field su tutte le response (`financial.py:152-159`),
   `residuo` sul wire (`ContractListResponse:462`), movimenti ordinati `data_effettiva, id` con esclusione
   corretta delle USCITA wallet `id_contratto=None` (la divergenza F1.b regge), `sedute_penali` e
   `azioni_permesse` sul preview. Manca SOLO `saldo_progressivo` (additivo) — la convenzione di segno da
   riusare è quella del mastro (`ledger.signed_importo_case`).

---

## 1. Ciò che NON cambia

- **L'asse DENARO è intoccato.** G8.4 è surfacing del read-model: nessun `CashMovement`, nessuna mutazione di `totale_versato`/`totale_rimborsato`/`quota_stornata`, nessuna modifica a `residuo()`/`netto_incassato()`.
- **`netto_incassato` resta DERIVATO** dalle due colonne immutabili (`max(versato − rimborsato, 0)`). MAI storarlo come colonna (romperebbe `/reconciliation` e l'invariante Strada B).
- **Il gate bilaterale 422 (ADR-018 D-SCELTA)** resta fail-closed: nessuna pre-selezione FE può degradare in scelta silenziosa.
- **Il footer di riconciliazione del residuo (ADR-019 D-CASSA-VISIBILE)** resta visibile: è la prova-a-vista del residuo net-aware.
- **Forfeiture (ADR-016/018):** le sedute `Programmato` NON riducono il conguaglio. Resta vero.
- **`frontend/src/lib/contract-status.tsx`** resta SSoT UNICO del vocabolario colore/stato (lifecycle + money_substate). G8.4 vi si allinea, non crea un secondo sistema.

---

## 2. Il principio (conseguenza di ADR esistenti)

> **Il frontend legge il SSoT, non lo ricalcola; e mostra la profondità senza imporla.**

Due corollari, entrambi conseguenza di decisioni già ratificate (nessuna nuova decisione architetturale):

- **R-SSOT-FE** (conseguenza di Strada B + ADR-019): ogni cifra di denaro mostrata dal FE è un campo del backend formattato, mai un'aritmetica client su `versato`/`rimborsato`/`movimenti`. *Eccezione legittima:* validazioni di input cap-locali nei dialog (`incassoNum <= creditoTrainer + ε`), che NON producono cifre canoniche ma vincolano l'editing — il backend resta l'autorità (422).
- **R-DISCLOSURE** (conseguenza del pitfall FE #9 generalizzato + reminder-first + ADR-019 D-CASSA-VISIBILE): la profondità può stare dietro progressive-disclosure **solo se non è un segnale critico/warning né la prova-a-vista del residuo**.

Se in implementazione emerge che un punto richiede una *nuova* decisione (non riconducibile a un ADR esistente) → STOP, governance docs-only prima (Addendum/ADR), poi codice.

---

## 3. Findings e decisioni

Severità: **[HIGH]** rigore/correttezza · **[MED]** UX. Asse: trasparenza | correttezza | accessibilità.

### F1 — Netto unico per superficie, ledger ri-etichettato **[HIGH, correttezza]**

Il FE ricalcola un netto che il backend espone già; e tratta come "stesso netto" due concetti diversi.

- **Netto-POSIZIONE** = `netto_incassato = max(versato − totale_rimborsato, 0)` (SSoT, `contract_state.py:90-95`). È il netto di hero / lista / profilo.
- **Netto-LEDGER** = saldo progressivo riga-per-riga su `contract.movimenti` = `Σ ENTRATA[id_contratto] − Σ USCITA[id_contratto]`. **Diverge legittimamente** dal netto-POSIZIONE di `Σ erogato wallet riassorbito` dopo un reopen (ADR-019 Addendum II, R2-bis): quelle USCITA hanno `id_contratto=None` e **non sono** in `contract.movimenti`.

**Decisioni:**
- **F1.a (D-NETTO-PER-SUPERFICIE):** hero, `ContractsTable`, `PaymentPlanTab`, `ContrattiTab` consumano **`contract.netto_incassato`**; si eliminano TUTTI i ricalcoli inline `versato − rimborsato`. Un grep esaustivo `versato.*rimborsato` su `frontend/src` precede l'implementazione (lo scope NON sono solo i 2 file citati nell'audit).
- **F1.b (D-LEDGER-RIGA):** il footer dello Storico **NON** usa `netto_incassato`. Resta row-derived (riconcilia con le righe mostrate) ma il backend lo serve già-pronto: nuovo campo additivo **`saldo_progressivo: float`** su `ContractMovementItem` (`financial.py:477-490`), calcolato in `get_contract` (`contracts.py:570-579`) con la stessa convenzione di segno (ENTRATA +, USCITA −) e lo stesso ordinamento (`data_effettiva, id`) di oggi. `CashLedgerCard` legge `m.saldo_progressivo` invece di accumulare nel `useMemo`.
- **F1.c (D-LEDGER-LABEL) — ✅ RATIFICATA 2026-07-06 (D-2):** colonna/valore **«Saldo»** su ogni riga dello storico (dal campo `saldo_progressivo`) + footer **«Saldo movimenti del contratto»**. L'etichetta «Netto incassato» resta ESCLUSIVA del netto-POSIZIONE. Registrata in **ADR-019 Addendum IV** (D-LEDGER-SALDO), evidenza L1 (QBO/Xero/WellnessLiving/Square/Stripe: il ledger si chiama "Balance"/"Running Balance", mai "net").
- **F1.d (guard) — forma aggiornata 2026-07-06:** il presidio «FE no money-math» nasce come **test semantico** in `tests/test_semantic_guards.py` (già eseguito da `check-all.sh`), NON come grep bash — allineato al ritiro dei grep-guard di G9.4-b. Il test scandisce i sorgenti FE per pattern di aritmetica su `versato`/`rimborsato`/`movimenti` con allowlist esplicita delle eccezioni cap-locali (R-SSOT-FE), + asserzione gemella che hero/lista leggono il campo SSoT.

### F2 — Progressive-disclosure SENZA nascondere i segnali **[MED, trasparenza]**

**Decisione (D-DISCLOSURE) — ✅ RATIFICATA 2026-07-06 (D-1, EMENDATA dalla ricerca competitor):** collassabile dietro «Mostra dettaglio» SOLO il dettaglio puramente informativo. **Sempre visibili (mai dietro toggle):**

| Sempre visibile (warning/prova) | Collassabile (informativo) |
|---|---|
| Rate Scadute > 0 (`hero 150-154`) | Acconto |
| Amber «N prenotate non erogate» (`hero 203-210`) | Da Rateizzare (se piano completo) |
| Residuo > 0 | Riga «Crediti Sedute» (4 card, `hero 158-200`) |
| Footer riconciliazione ledger (netto/residuo) | Righe dettaglio del ledger (`history 110-150`) |
| **Breakdown «lordo − rimborsi» come sub-label compatta** quando `totale_rimborsato > 0` (pattern card Entrate `/cassa`, G9.4-bis.3) | |

**Emendamento D-1 (2026-07-06):** il breakdown «lordo − rimborsi» era proposto collassabile — la legge L2 della ricerca (Stripe: net raggruppato per fees/refunds *by default*; Xero/QBO: credit note = riga visibile) e il nostro stesso D-NESSUN-NETTO-NUDO (ADR-022 Add. II) lo promuovono ad **always-visible in forma di sub-label**: mai un netto nudo inspiegabile a video. Coordinamento con F4: finché F4 non sostituisce il workaround, l'amber «Riapri e poi Termina» resta always-visible (è l'unico punto che oggi indirizza l'azione correttiva).

### F3 — Settlement come raccomandazione branch-aware, accessibile **[MED, accessibilità]**

`compute_settlement` ritorna il fatto puro, mai un'azione («le azioni le sceglie il caller», `contract_settlement.py:116-117`); `settlement-preview` ritorna solo `azioni_permesse` (lista). ADR-018 D-SCELTA: sul ramo `credito_trainer > 0`, `terminate` rifiuta 422 senza scelta esplicita.

**Decisioni:**
- **F3.a (D-RACCOMANDAZIONE-VISIVA, ramo TRAINER):** la raccomandazione è **solo visiva** (badge «Consigliato» + enfasi + icona check sul bottone suggerito). `azione` resta `''` e `canSubmit` resta `false` finché l'utente **non clicca davvero**. `aria-pressed` riflette lo stato REALE — nessun bottone `pressed` all'apertura. La pre-selezione attiva è **vietata** sul ramo trainer (sarebbe il default implicito che ADR-018 rifiuta). `RINUNCIA_ESPRESSA` non è MAI il bottone suggerito.
- **F3.b (D-PREFILL-CLIENTE, ramo CLIENTE/rimborso):** il pre-riempimento `default = credito_cliente` resta ammesso — è già sancito da ADR-020 D-RIMBORSO-EDITABILE e il codice lo fa (`98-102`).
- **F3.c (advisory backend, opzionale):** se serve un suggerimento computato, `settlement-preview` espone un campo **advisory** `azione_consigliata` (es. `INCASSA_ORA` quando `credito_trainer>0` — l'opzione che tutela il trainer), popolato in `_build_settlement_preview` (`contracts.py:1451-1488`). È advisory: non cambia il gate 422.
- **F3.d (accessibilità):** i 3 `<Button>` diventano un gruppo a scelta singola accessibile (`role="radiogroup"` + `role="radio"`/`aria-checked`, oppure `aria-pressed` per bottone) con marcatore non-cromatico sul selezionato. *(Conferma W3C APG: radiogroup con stato iniziale tutto-deselezionato è pattern riconosciuto — legge L5.)*
- **F3.e (display `sedute_penali`, residuo G7.8-bis — aggiunto 2026-07-06):** il breakdown del dialog Termina mostra le sedute penali quando `sedute_penali > 0` (conteggio SEPARATO dalle erogate, mai sommato a video: «N erogate + M penali» — coerente con l'audit conteggi separati di G7.8-bis). Richiede il sync di `sedute_penali` in `types/api.ts` (`ContractSettlementPreview`).
- **F3.f (nota-abbuono obbligatoria lato FE — aggiunto 2026-07-06, da INDEX/roadmap 2026-07-03): ✅ GIÀ IN CODICE** (scoperto durante F5.b): il gating `trainerSceltaValida` richiede `nota.trim().length > 0` su `RINUNCIA_ESPRESSA` → submit disabilitato senza nota (AC-G84-8 già vero). Il backend resta autorità (422). Resta solo da coprire con test Playwright in fetta-comportamentale.

### F4 — Rimborso *goodwill* del non-svolto → SCORPORATO in G8.5 **[money-path, governance-first]**

**Decisione founder (D-3, ratificata 2026-06-30): opzione B — rimborso goodwill.** Il trainer, alla terminazione, può *volontariamente* rimborsare il valore delle sedute prenotate-ma-non-erogate. Questo **non** è una modifica UX: è un **nuovo money-path** (crea cassa) → fuori da G8.4, scorporato nel blocco sibling **G8.5** con governance-first (nuovo ADR proposed→accepted + spec, poi codice — regola del filone).

**Modello (da ratificare in G8.5, non in G8.4):** il goodwill è ADDITIVO e discrezionale — **non** tocca il conguaglio (forfeiture ADR-016/018 resta il default; le prenotate continuano a non ridurre il conguaglio). È un'USCITA esplicita ed editabile, sull'asse del rimborso (parallelo ad ADR-020 D-RIMBORSO-EDITABILE), invertita dal reopen come ogni altra cassa di terminazione (ADR-019 non-distruttivo). Decisioni founder che G8.5 deve chiudere: (i) destinazione = cassa vs wallet vs scelta editabile; (ii) base importo = `sedute_prenotate × prezzo/seduta` come cap `[0, valore]`, solo editabile in giù; (iii) nuova categoria cassa (es. `RIMBORSO_GOODWILL_CONTRATTO`) vs riuso `RIMBORSO_CONTRATTO` con `motivo` distinto; (iv) inversione al reopen.

**Cosa resta in G8.4 su questo punto:**
- l'amber «N prenotate non erogate» (`hero 203-210`) resta **always-visible** (F2) finché G8.5 non shippa — è l'unico segnale dell'azione recuperabile;
- quando G8.5 esiste, il dialog Termina espone l'azione esplicita «rimborsa il non-svolto (goodwill)» **al posto** del workaround «Riapri poi Termina», che viene rimosso.

Vietato in ogni caso (anche in G8.5): ridurre il conguaglio con le prenotate (romperebbe EROGATO) o riaprire in modo implicito (scavalca reopen-allowlist). Il goodwill è una cassa *in più*, mai un ricalcolo del dovuto.

### F5 — Split presentazionale <300 LOC + import top-of-file **[HIGH, rigore]**

**Decisione (D-SPLIT)** *(perimetro aggiornato 2026-07-06, §0-bis punto 4)*:
- `TerminateContractDialog.tsx` (357→<300): estrarre `SettlementBreakdown` (dl `176-214`), `ClientRefundBranch` (`216-253`), `TrainerCreditBranch` (`255-336`) come **componenti presentazionali controllati** (props in, callback out). **TUTTO lo stato e la gating-logic** (`azione`, `incasso`, `rimborso`, `metodo`, `nota`, i sync in-render `prevOpen`/`prevPreviewKey`, `trainerSceltaValida`/`clienteSceltaValida`/`canSubmit`) **restano nel container**. I figli non possiedono stato di gating.
- `contratti/[id]/page.tsx` (511): ~~import inline~~ *(già risolti — top-of-file righe 16-30)*; estrarre `RenewalChainSection`/`SessioniTab`/`DettagliTab` in moduli per rientrare <300.
- `PaymentPlanTab.tsx` (897): è la violazione più grande; split in sotto-componenti (`RateCard`/`PayRateForm`/`PaymentHistory`/`AddRateForm` sono già citati in `frontend/CLAUDE.md`). *Può essere un proprio commit nella fetta-RIGORE.*
- `ContractsTable.tsx` (370, **aggiunto 2026-07-06** — la spec originale non lo censiva): split della riga/celle finanziarie in sotto-componente presentazionale per rientrare <300.
- **Gate:** il test Playwright LIVE del flusso terminate/reopen (gate di G8.1.1) ri-passa dopo lo split.

### F6 — Disciplina colore allineata al SSoT **[MED, accessibilità]**

**Decisione (D-COLORE):** token-map esplicita a 3 categorie, allineata a `contract-status.tsx` (non un secondo vocabolario):
- **valenza:** `emerald`=positivo/saldato · `amber`=attenzione · `red`=critico/scaduto.
- **identità-stato:** governata da `lifecycle`/`money_substate` badge (es. `amber`=Sospeso è valenza-di-stato, lecito; `sky`=parziale, `zinc`=chiuso — restano dove il SSoT li definisce).
- **decorativo (da neutralizzare → `zinc`/`slate`):** i tint KPI senza valenza nell'hero — `violet` Valore Contratto (`62-63`), `blue` Acconto/Rate Pagate/Programmate (`68-72, 123-124, 168-172`), `indigo` Crediti Totali (`162-163`).

L'hero finanziario usa il colore SOLO per segnalare stato; l'identità di categoria non è veicolata dal colore.

---

## 4. Perimetro

- **Backend (additivo, read-model):** `ContractMovementItem.saldo_progressivo` (`financial.py`), calcolo in `get_contract` (`contracts.py:570-579`); opzionale `ContractSettlementPreview.azione_consigliata` advisory (`contracts.py:1451-1488`). Nessuna modifica a colonne/ledger/residuo.
- **Frontend:** `ContractFinancialHero`, `ContractHistoryTab`, `TerminateContractDialog` (+ nuovi figli `terminate/*`), `ContractsTable`, `PaymentPlanTab`, `ContrattiTab`, `contratti/[id]/page.tsx`, `lib/contract-status.tsx`, `types/api.ts` (campo `saldo_progressivo`, eventuale `azione_consigliata`).
- **`tools/scripts/check-all.sh`:** grep-guard «FE no money-math» (F1.d) + test gemello.

---

## 5. Test di accettazione (G8.4)

1. **AC-G84-1 (F1, netto unico):** su un contratto con `totale_rimborsato>0`, il "netto" mostrato da hero, lista contratti e profilo è **identico** e uguale a `contract.netto_incassato`. **Fail:** una qualunque superficie mostra un netto ricalcolato divergente. *(test: guard semantico «FE no money-math» in `tests/test_semantic_guards.py` — forma aggiornata 2026-07-06, §0-bis punto 2.)*
2. **AC-G84-2 (F1.b, ledger riconcilia con le righe):** dopo un reopen con riassorbimento wallet, il footer del ledger = ultimo `saldo_progressivo` (row-derived) e **può** differire da `netto_incassato`; entrambi coerenti con la propria definizione. **Fail:** il footer del ledger non riconcilia con le righe mostrate. *(test: `test_saldo_progressivo_reconciles_rows`.)*
3. **AC-G84-3 (no-regressione DENARO):** su qualunque crm.db reale, prima/dopo G8.4, `residuo()`, `netto_incassato()`, conteggi e `Σ movimenti` sono **byte-identici**; zero `CashMovement` creati/modificati. **Fail:** una qualunque cifra DENARO cambia. *(test: snapshot finanziario + `assert_contract_invariants` invariati.)*
4. **AC-G84-4 (F3, gate bilaterale intatto):** all'apertura del dialog Termina su un ramo `credito_trainer>0`, `canSubmit=false` e nessun bottone è `aria-pressed`; il submit resta impossibile finché l'utente non sceglie. **Fail:** una pre-selezione rende `canSubmit=true` senza click. *(test: Playwright `terminate_trainer_credit_requires_explicit_choice`.)*
5. **AC-G84-5 (F2, segnali sempre visibili):** con Rate Scadute>0 o prenotate-non-erogate>0 o Residuo>0, il segnale è renderizzato **senza** interazione di disclosure. **Fail:** un segnale critico/warning è dietro «Mostra dettaglio». *(test: render `hero_critical_signals_always_visible`.)*
6. **AC-G84-6 (F5, LOC + Playwright):** i file toccati sono <300 LOC (logica); il flusso terminate/reopen Playwright LIVE ri-passa. **Fail:** un file logica resta >300 o il flusso regredisce.
7. **AC-G84-7 (F3.e, penali visibili — aggiunto 2026-07-06):** su un settlement-preview con `sedute_penali > 0`, il breakdown del dialog Termina mostra le penali come conteggio SEPARATO dalle erogate. **Fail:** penali invisibili o sommate alle erogate a video.
8. **AC-G84-8 (F3.f, nota-abbuono — aggiunto 2026-07-06):** con `azione = RINUNCIA_ESPRESSA` e nota vuota, il submit è disabilitato; compilata la nota, si abilita. **Fail:** submit possibile senza nota (anche se il backend poi rifiuta 422).

---

## 6. Sequenza dei gate (3 fette — vincolante)

Profili di rischio opposti → **non una spec/commit unico** (violerebbe «ogni commit lascia il branch rilasciabile»). Tutte le fette G8.4 sono FE-only/read-model, zero schema-change sull'asse DENARO → **ortogonali a G1** (cifratura) e **G8.2** (wallet cross-contratto, in panchina). **Scelta founder: tutte e 3 le fette ora** (F1/F2/F3/F5/F6 pure); **F4 esce in G8.5** (money-path, governance-first).

| Fetta | Contenuto | Rischio | Quando |
|---|---|---|---|
| **fetta-RIGORE** | **F1** (consumo `netto_incassato` su TUTTE le superfici + `saldo_progressivo` + grep-guard) + **F5** (split <300, stato nel container, Playwright) | Basso/meccanico | **Ora** (1ª — sblocca il doppio-netto) |
| **fetta-UX-presentazionale** | **F2** (disclosure con liste always-visible ratificate) + **F6** (token-map allineata a `contract-status.tsx`) | Basso giudizio | **Ora** (2ª) |
| **fetta-UX-comportamentale** | **F3** (raccomandazione visiva + a11y) — ramo trainer senza default attivo, pre-fill solo ramo cliente | Medio giudizio | **Ora** (3ª) |
| **G8.5 (sibling)** | **F4** rimborso goodwill = nuovo money-path | Alto / money | Governance-first (ADR + spec) **prima** del codice; UX-hook in Termina dopo |

**Step 1 — governance docs-only.** Questa SPEC + (se serve) Addendum ADR-019 per F1.c + deposito audit + **apertura G8.5** (nuovo ADR proposed + spec). **Gate:** doc allineati, ratifica founder (D-1 lista always-visible).
**Step 2 — fetta-RIGORE.** **Gate:** suite verde, AC-G84-1/2/3/6, grep-guard attivo, byte-identico.
**Step 3 — fetta-UX-presentazionale.** **Gate:** `next build`, AC-G84-5, liste ratificate.
**Step 4 — fetta-UX-comportamentale (F3).** **Gate:** `next build`, AC-G84-4.
**Step 5 — G8.5 (separato):** ADR goodwill accepted → backend money-path → UX-hook in Termina (rimuove il workaround). Non blocca G8.4.
**Quality gate (ogni fetta):** `pytest` + `ruff check api/` + `next build` + grep-guard; aggiorno FDM/TASSONOMIA/api-CLAUDE/BUILD_LOG/INDEX/adr-README.

---

## 7. Fuori scope (dichiarato)

- **Rimborso goodwill del non-svolto** (F4): scelto dal founder, ma è un nuovo money-path → **blocco G8.5** con ADR + spec dedicata, non G8.4. G8.4 ne tiene solo il segnale always-visible e lo slot UX nel dialog.
- **Wallet cross-contratto auto** (G8.2, in panchina/D2).
- **Cifratura crm.db** (G1, track sicurezza parallelo).
- **Rollout `assert_contract_invariants` come enforcement** (G9, command layer).
- Qualunque modifica all'asse DENARO, alle colonne cassa, al gate 422, alla forfeiture.

---

## 8. Definizione di fatto

G8.4 è finito quando: (1) nessuna superficie mostra un netto ricalcolato divergente (F1, grep-guard verde); (2) lo Storico legge `saldo_progressivo` dal wire e riconcilia con le righe; (3) nessun segnale critico/warning è dietro toggle (F2); (4) il settlement trainer resta a scelta esplicita con raccomandazione solo-visiva e a11y (F3); (5) F4 è scorporato in G8.5 (governance aperta), e in G8.4 l'amber prenotate resta always-visible; (6) i file toccati sono <300 LOC; (7) asse DENARO byte-identico su crm.db reale; (8) suite + `ruff` + `next build` + Playwright LIVE verdi.

## Follow-up a implementazione

A chiusura di ogni fetta: `FINANCIAL_DOMAIN_MODEL.md` (nota sui due netti, se F1.c), `api/CLAUDE.md` (pattern «FE legge netto_incassato»), `BUILD_LOG.md` (entry `### 2026-… — G8.4 / trasparenza FE`), `docs/INDEX.md`, `docs/adr/README.md` (se Addendum ADR-019), `tools/scripts/check-all.sh` (grep-guard). Depositare l'audit fondante `docs/operations/AUDIT_FRONTEND_FINANZIARIO_2026-06-30.md`. Aggiornare MEMORY `project_financial_workstream.md` (riga di stato G8.4) tenendo l'index a una riga.
