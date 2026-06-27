# ADR-018 — Terminazione bilaterale: il ramo `servizio_reso > versato` esige una scelta esplicita + credito trainer che sopravvive alla chiusura

- Date: 2026-06-27
- Status: accepted
- Deciders: Giacomo Verardo (AVGV Technologies); analisi senior e bridge code-grounded di Claude Code
- Related upgrade ID: G7.9 (core: esito balance-based + incasso contestuale editabile + rinuncia) + G7.10 (credito differito: entità receivable)
- Spec di dettaglio (contratto d'implementazione): `docs/technical/SPEC_TERMINAZIONE_BILATERALE_E_TUTELA_TRAINER.md`
- Audit fondante: `docs/operations/AUDIT_TERMINAZIONE_BILATERALE_2026-06-27.md`
- Estende: `ADR-016` (asse EROGATO canonico) sul **ramo positivo del conguaglio**, lasciato collassare su `SALDO_A_PERDERE`
- Correlati: `ADR-017` (rinvio libera credito), `ADR-014` (gestione finanziaria, framing "proposta non obbligo"); modello vivo: `FINANCIAL_DOMAIN_MODEL.md`, `TASSONOMIA_FINANZIARIA.md`

## Context

`ADR-016` (2026-06-26) ha ratificato l'asse **EROGATO** (sedute `Completato`) come unica base monetaria del recesso — corretto al 100% sul **quanto vale il servizio reso**. Ma ha congelato, **per omissione**, anche la semantica dell'**azione** sul ramo positivo del conguaglio. L'audit senior del 2026-06-27 la rivela asimmetrica:

- `compute_settlement` tratta `conguaglio < 0` (versato > reso) come **RIMBORSO** → il software tutela il cliente in modo esplicito;
- tratta `conguaglio >= 0` (reso > versato) come **`SALDO_A_PERDERE`** → `terminate` lo traduce in **write-off implicito** del residuo (`TERMINAZIONE_DECADENZA`), **senza** chiedere al trainer se voglia incassare il dovuto o rinunciarvi.

**Prova economica** (P=1000, 10 sedute @100; cliente ne fa **7** → R=700 col pro_sedute; ha versato V=500). Oggi `terminate` fa `quota_stornata += residuo_pre = P−V = 500` → residuo 0, chiuso. Ma quei 500 fondono due realtà diverse:
- **300** = `P−R` → servizio mai erogato → storno legittimo;
- **200** = `R−V` → servizio **già reso e non pagato** → **credito reale del trainer, abbuonato in silenzio**.

Il software prende posizione (rinuncia) al posto del trainer. È un **bug di dominio**, non di UX: perdita silenziosa di credito + storico che non distingue più "servizio non erogato annullato" da "servizio erogato ma abbuonato".

Confine confermato dal modello vivo: il FDM (§7) aveva già visto il bivio (`conguaglio > 0` = "da incassare (G6) **oppure** STORNO"), ma il codice ha materializzato solo il write-off. Nessun modello esiste oggi per un credito che **sopravvive alla chiusura**: il FDM lega "da incassare" solo a contratti aperti/SOSPESO (G6).

## Decision Drivers

- **Simmetria di tutela**: proteggere il trainer sottopagato come il software protegge il cliente sovra-pagato.
- **Scelta esplicita e auditabile**: la rinuncia del trainer non può più essere il default implicito.
- **Invariante Strada B intatto**: `residuo()==0` su CHIUSO; lordo `totale_versato` immutabile; `netto_incassato()` derivato; `reopen` unico inverso esplicito.
- **"Proposta non obbligo" (ADR-014)**: la valorizzazione `pro_sedute` è **PROVISIONAL** (gated tributarista). Finché ha solo abbonato denaro il rischio era basso; ora determinerebbe un importo **fatturato** a un cliente reale → l'importo dev'essere una **proposta editabile**, mai una bolletta rigida.

## Considered Options

### Option A — Status quo (`SALDO_A_PERDERE` = write-off implicito)
- Contro: perdita silenziosa del credito trainer; storico indistinto; il software decide la rinuncia al posto dell'utente; contraddice il modello bilaterale già documentato nel FDM.

### Option B — Esito balance-based + scelta esplicita, importo fisso a `R−V`
- Pro: tutela il trainer, scelta auditabile (`INCASSA_ORA` / `RINUNCIA_ESPRESSA`), zero default implicito.
- Contro: nessuno sconto di goodwill (l'importo è rigido); nessun "chiudo oggi, incasso venerdì" → il binario incassa-subito / rinuncia-per-sempre è falso proprio nello scenario da tutelare.

### Option C — Option B + importo editabile (verso il basso) + credito differito come entità dedicata (scelta)
- Pro: copre goodwill (edit verso il basso) e "incasso dopo" (receivable che sopravvive a CHIUSO) **senza** rompere `residuo()==0`; il differito vive **fuori** da `residuo()` ed è ri-tracciato, non perso.
- Contro: superficie maggiore (nuova tabella, worklist, estensione `reopen`, predicati cassa G7.5) → si **spezza** in G7.9 (core, zero tabella) + G7.10 (entità receivable).

## Decision

**Option C.** L'esito puro torna **balance-based**; l'azione di rinuncia/incasso diventa una scelta esplicita del trainer, con importo proposto ed editabile; il credito differito è normato come entità dedicata fuori da `residuo()`. Decisioni founder vincolanti (2026-06-27):

1. **D-ESITO-PURO** — `contract_settlement.py` ritorna il **fatto economico**: `CREDITO_CLIENTE` / `CREDITO_TRAINER` / `PARI` (dead-zone ±0.009 nella classificazione, importi con `max(…,0)`). `SALDO_A_PERDERE` **esce** dal modulo puro → sopravvive solo come azione del router ("rinuncio al saldo a mio favore").
2. **D-SCELTA** — sul ramo `credito_trainer > 0`, `terminate` **rifiuta** (422) senza una scelta esplicita. Azioni: `INCASSA_ORA` / `RINUNCIA_ESPRESSA` (G7.9), `A_CREDITO` differito (G7.10).
3. **D-IMPORTO** — l'importo incassabile è una **proposta editabile**: default `R−V`, cap **`[0, R−V]` solo verso il basso**. Il non-erogato `P−R` resta **sempre** stornato, **mai** fatturabile (il trainer non può billare servizio non reso col metodo pro-rata). Editare verso il basso = sconto/abbuono parziale (la differenza diventa storno). `RINUNCIA_ESPRESSA` = incasso 0 (nota obbligatoria).
4. **D-CATEGORIA** — nuova categoria cassa **`INCASSO_CONGUAGLIO_CONTRATTO`** (in `CONTRACT_CASH_IN`), `id_rata = NULL`, cablata in **tutti** i predicati aggregati induriti in G7.5 (`kpi_incassato`, movement-stats, forecast, financial-trend, monthly_revenue) + grep-guard anti-omissione.
5. **D-CREDITO-DIFFERITO** — il credito del trainer può **sopravvivere a CHIUSO** come receivable in **tabella dedicata `crediti_terminazione`** (`importo`, `importo_incassato`, `stato APERTO/SALDATO/ANNULLATO`), **fuori** da `residuo()`. `quota_stornata` assorbe anche il differito (residuo resta 0); il credito è **ri-tracciato**, non perso. Worklist "Crediti da incassare (post-chiusura)" gemella di G6; incasso successivo → `ENTRATA INCASSO_CONGUAGLIO_CONTRATTO` + receivable SALDATO. Mai una Rate viva su contratto chiuso (no rata-fantasma).
6. **D-REOPEN** — `reopen` resta l'**inverso esatto**: inverte anche la nuova `ENTRATA` di conguaglio (decrementa `totale_versato` — **prima volta** che `reopen` tocca il lordo, eccezione sanzionata come `unpay_rate`) e annulla il receivable differito. Coordinare col guard H1 di `unpay_rate` (409 su terminato).
7. **D-MOTIVO** — `motivo_chiusura = TERMINAZIONE_SALDO_TRAINER` (nuovo) per il ramo trainer, a prescindere da incasso/rinuncia/differito; la distinzione vive nel payload audit. `TERMINAZIONE_DECADENZA` resta **legacy/storico**, non più emesso da `terminate` su contratti vivi.

**Invarianti che NON cambiano** (restano in vigore): asse EROGATO canonico per il denaro (ADR-016); `Rinviato` fuori dall'occupazione (ADR-017); forfeiture delle `Programmato` (le prenotate non riducono il conguaglio); Strada B (lordo immutabile, netto derivato); `residuo()==0` su CHIUSO; `reopen` unico inverso esplicito. Il ramo **`CREDITO_CLIENTE` (RIMBORSO)** resta **byte-identico** (semantica e importi invariati).

## Consequences

- **Positive**: tutela del trainer simmetrica a quella del cliente; storico che distingue non-erogato / incassato / rinunciato / differito; zero euro perso in silenzio; invariante `residuo()==0` preservato anche col credito differito; il founder può scontare (goodwill) o incassare dopo senza workaround manuali non auditabili.
- **Negative**: G7.9 tocca `contract_settlement` + `terminate` + `reopen` + predicati cassa + schema Pydantic + FE (dialog a 3 vie); G7.10 aggiunge tabella + worklist + endpoint incasso + estensione `reopen`; la nuova categoria **riapre la superficie predicati indurita in G7.5** (rischio regressione aggregati → test dedicato obbligatorio); `reopen` decrementa `totale_versato` per la prima volta (nuova eccezione Strada-B da coordinare col guard H1).
- **Follow-up actions**:
  - **G7.9** (core, zero tabella): esito balance-based + `INCASSA_ORA` (importo editabile) + `RINUNCIA_ESPRESSA` + categoria cassa + reopen esteso all'ENTRATA + FE 3-vie + grep-guard.
  - **G7.10** (credito differito): entità `crediti_terminazione` (additiva via `schema_sync`, **no alembic**) + worklist + endpoint incasso + reopen esteso al receivable.
  - A implementazione: aggiornare `FINANCIAL_DOMAIN_MODEL.md` (ramo `conguaglio > 0`), `api/CLAUDE.md`, `BUILD_LOG.md`.

## Rollback / Exit Strategy

- **G7.9**: cambio di esito (balance-based) + gamba `ENTRATA` + nuovo motivo + nuova categoria (TEXT, **no DDL**; enum additivo). Rollback = ripristino mapping `SALDO_A_PERDERE → TERMINAZIONE_DECADENZA` e rimozione della gamba `ENTRATA`; i movimenti `INCASSO_CONGUAGLIO_CONTRATTO` sono soft-deletabili via `reopen`. **Nessuna migrazione distruttiva.**
- **G7.10**: la tabella `crediti_terminazione` è additiva (`schema_sync`); il credito differito vive solo lì + nel ledger. Rollback = drop tabella + ripristino della sola coppia `INCASSA_ORA`/`RINUNCIA_ESPRESSA`; nessun dato business in altre tabelle alterato.

## Supersedes / Superseded By

- **Estende** `ADR-016`: l'asse EROGATO, la forfeiture e la riconciliazione display↔rimborso restano invariati; ADR-018 norma **l'azione** sul ramo `servizio_reso > versato` che ADR-016 aveva lasciato collassare su `SALDO_A_PERDERE`. Non emenda sezioni numerate di ADR-016.
- Superseded by: —
