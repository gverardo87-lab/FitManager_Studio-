# AUDIT PRE-RELEASE 2026-07-16 — Triade auditor sul batch v1.0.13 → HEAD (candidata v1.0.14)

**Tipo:** audit read-only, evidenza del release gate (step 1 del runbook ratificato dal founder).
**Data:** 2026-07-16 · **Branch:** `FitManager_Studio` · **Base:** `9ab426e` (v1.0.13, 2026-06-18)
→ **Target:** `b888a0a`. **Batch:** 206 commit = l'intero filone finanziario G6→G9.7 (terminazione
bilaterale, penali, wallet, reopen non-distruttivo, ledger rettifiche, penna unica, enforcement,
read-model cassa, Hypothesis, semantica per-classe). 30 file `api/` toccati, +5.269 righe sull'asse.
**Trigger:** decisione founder — rilasciare al confine di blocco (G9.7 chiuso stasera) PRIMA di
aprire P1: batch già grande (rischio di release superlineare), valore verificato ma non consegnato
(Chiara su v1.0.10 col bug fingerprint), OD-2 affamato di telemetria di campo.
**Metodo:** triade auditor read-only in parallelo — `financial-invariant-verifier` (asse denaro) ·
`docs-code-drift-auditor` (governance ⇄ codice) · `semantic-birth-auditor` (assi semantici,
**prima corsa assoluta** — collaudo pre-P1). Zero mutazioni. I tre report completi vivono nella
sessione; questo documento è il consolidato e la SSoT dell'evidenza.

---

## 1. Verdetti

| Auditor | Verdetto | HIGH | MEDIUM | LOW |
|---|---|---|---|---|
| financial-invariant-verifier | **MONEY AXIS PRESERVED** | 0 | 0 | 1 (F1) |
| docs-code-drift-auditor | 8 divergenze, tutte docs-layer | 2 | 4 | 2 |
| semantic-birth-auditor | **SEMANTIC BIRTH AT RISK** | 0 | 4 | 7 |

**Lettura di gate:** nessun finding tocca l'aritmetica del denaro o l'integrità dei test. UN buco
comportamentale reale (M1-sem, sotto) con fix chirurgico dentro dottrina già ratificata. Il taglio
della release è **sbloccato a valle della fetta R1** (§5).

## 2. Asse denaro (financial-invariant-verifier) — PRESERVED

- **V1-V5 tutti verdi:** 394 test money-band (0 fail), harness 13 scenari I1/I4/I5/I6, ancore
  ledger (`totale_versato == Σ ENTRATA`, I5 rimborso raffinata), `check-all` TUTTO OK, gemelli
  `test_semantic_guards.py` vivi e non vacui (anti-vacuità presenti).
- **V3 (il crux):** ogni simbolo money-mutating del batch ha un oracolo che lo esercita. Tutte le
  scritture confinate nella penna unica (`post_inflow`/`post_outflow`/`post_adjustment`) + i 2
  siti sanzionati (fold reopen in `transitions.py`, unpay diretto in `rates.py` con guard H1).
  Sweep «5 produttori»: `crediti_usati` ha solo LETTORI; `PERIMETRO_TRANSIZIONE` + set-equality
  dal metadata ORM chiudono strutturalmente la classe.
- **Sanctioned changes verificati (non regressioni):** `residuo()` net-aware (ADR-019, oracoli
  dedicati presenti); gate invarianti `raise` in dev/CI e `log` in compiled (OD-2, deliberato).
- **F1 (LOW, COVERAGE-GAP bounded):** `posizione_netta_contratto` + `PosizioneContrattoCliente`
  (`contract_state.py`) = **oracolo money MORTO** — zero call-site, zero test (evidenza:
  `grep -rn` su api/ tests/ frontend → solo le 3 righe di auto-definizione). Era il «gradino per
  G8.2» (oggi in panchina). Non muove euro perché nessuno lo chiama; può marcire in silenzio.
  → decisione founder in §6 (raccomandazione: PIN con unit-oracle).

## 3. Governance ⇄ codice (docs-code-drift-auditor) — 8 finding, tutti docs-layer

| # | Sev | Finding | Lato stale |
|---|---|---|---|
| H1 | HIGH | `INDEX.md:83` dà SPEC_G9.7 come «APERTA — DA IMPLEMENTARE»; la spec è 🟢 tutti-i-gate-chiusi (presidi tutti collezionabili) | INDEX |
| H2 | HIGH | `INDEX.md:115` sezione ADR ferma a «20 ADR / →022»: ADR-024 e ADR-025 (accepted, load-bearing del batch) assenti dalla narrativa; `adr/README.md` è invece completo →025 | INDEX |
| M1 | MED | `api/CLAUDE.md:445` «tests/, 361 test» — la suite collezionabile è **860** | doc |
| M2 | MED | `CLAUDE.md:63` «69 vitest» — sono **103** | doc |
| M3 | MED | `INC-2026-03-29-portal-url-origin-mismatch` (P1) senza traccia in POSTMORTEMS/learning — gemello C4 mancante. **ESCALATE**: policy founder (fix same-day = catalogo-only?) | — |
| M4 | MED | `CLAUDE.md:10` «frontend/ (350 file)» — `git ls-files` = **372** (api 178 ✓, core 15 ✓) | doc |
| L1 | LOW | «29 tabelle business» accusato di three-way mismatch — **CONFUTATO in triage**: dalla sua stessa evidenza 31 nomi − 2 infra (`alembic_version`, `_schema_version`) = **29 → CLAUDE.md è CORRETTO**; l'aritmetica dell'agente era errata («28»). Stale è semmai la memoria di sessione («26», pre G7.10/G8.1/G9.2b: 26+3=29 ✓) | (falso positivo) |
| L2 | LOW | `SPEC_VOCABOLARIO` riga 7 «Collocazione: docs/technical/» ma vive (correttamente) in `docs/specs/` | breadcrumb |

Nota utile emersa: il guard lifecycle di `check-all.sh` chiave su `**Stato:** ✅` a inizio riga —
il 🟢 di SPEC_G9.7 e il «✅ Giro 1» inline non lo attivano. Osservazione di sensibilità, non drift
(decisione minore in §6).

## 4. Assi semantici (semantic-birth-auditor, prima corsa) — AT RISK: 0 HIGH · 4 MEDIUM · 7 LOW

**Perimetro verificato:** tutte le nascite del batch (stati evento 4→6, STATI_PENALE /
OCCUPAZIONE_SLOT / SERVIZIO_CONTABILIZZATO, ClasseContabile 6, STATO_CREDITO_*,
`rettifiche_contratto`+CAUSALI, MotivoChiusura, aggancio eventi×contratto, lifecycles
crediti/wallet, PERIMETRO_TRANSIZIONE). 148 gemelli collezionati meccanicamente. **Riti S5
sostanzialmente completi** su ogni nascita; CP: il deadlock canonico ha uscita costruita e
testata; S4: zero netti nudi nuovi. Rischi già ACCETTATI correttamente non ri-flaggati (R1/R2
matrice→P5, DISPLAY-EXEMPT, SALDATO fuori rete, OD-2, crediti client-level→P4).

### M1-sem — TOTALITÀ-VIOLATA: `CONSUNZIONE` buca il guard H1 di `unpay_rate` ⚡ il finding che gates
- **Side-A (legge):** dottrina G7.7/H1 + FSM `transitions.py`: contratto terminato
  (`TERMINAZIONE_*` **e** `CONSUNZIONE`) rifiuta la revoca-pagamento → 409; path canonico = reopen.
- **Side-B (codice):** il guard B-bis di `unpay_rate` (`api/routers/rates.py`) classifica la
  famiglia con `quota_stornata>0 OR totale_rimborsato>0 OR motivo.startswith("TERMINAZIONE_")`.
  Un chiuso con esito PARI (`motivo=CONSUNZIONE`, zero storno, zero rimborso, rate SALDATE
  sopravvissute) **non matcha nessuna delle tre** → la revoca procede → `residuo()>0` su un
  CHIUSO che l'allowlist (`{"COMPLETAMENTO"}`) non riapre.
- **Evidenza meccanica:** `grep -rn 'startswith("TERMINAZIONE_' api/` → esattamente 2 interpreti
  della stessa famiglia: `rates.py` (guard, ESCLUDE Consunzione) e `contract_state.py`
  (predicato I1, la INCLUDE) — divergenza viva tra interpreti.
- **Perché 860 test non l'hanno visto:** in dev/CI il gate invarianti (`raise`) intercetta con un
  409 generico → comportamento mascherato; **in produzione il gate è log-only (OD-2) → la
  mutazione committa** e lo stato incoerente persiste (solo telemetria warn).
- **Severità:** MEDIUM (precondizioni strette, exit esiste via reopen esplicito) ma **da fixare
  pre-release**: rende totale una dottrina già ratificata, costo ~1 riga + gemello.

### M2-sem — INTERPRETE-IMPLICITO: `sedute_penali` a literal nel dettaglio contratto
`_to_response_with_rates` (`contracts.py:184`): `cb.get("Cancellato_Tardivo",0)+cb.get("No_Show",0)`
— appartenenza a STATI_PENALE ri-derivata a literal (la riga sotto usa il pattern corretto sul
frozenset). Il gemello anti-literal di `test_occupazione_ssot` matcha solo il paio
`["Programmato","Completato"]` → gli sfugge per costruzione. Un 3° stato-penale futuro romperebbe
a video l'equazione del banner D1 (dettaglio sottoconta, worklist conta).

### M3-sem — TOTALITÀ-VIOLATA (latente, casa P1): read-model ClasseContabile con else silenziosi
`get_movement_stats`: `entrate_lorde` = whitelist di 2 classi + `else` che somma **alle uscite del
grafico**; `get_financial_trend`: `else` bucket-altri. Una 7ª classe (P1) compilerebbe verde
finendo classificata male. Zero test pinnano la cardinalità dell'enum
(`grep "list(ClasseContabile)|for classe in ClasseContabile" tests/` → vuoto). La matrice assegna
già i «gemelli 7 classi» a P1 ma NON nomina la forma read-model del buco → **precisazione
depositata in SPEC_P §P1** (stesso giro di questo audit).

### M4-sem — INTERPRETE-IMPLICITO: `crediti_residui` inline nella worklist orfani
`get_orphan_events` (`dashboard.py`): `(crediti_totali or 0) − usage` **senza clamp** e con query
usage propria, invece di `cstate.crediti_residui()` + delega a `_crediti_usati_map` (dichiarato
«unico interprete» tre funzioni sotto, G9.7.3/D5). Un sovra-occupato produrrebbe residuo negativo
sul wire che il FE (per guard G9.7.4!) DEVE leggere. Sovra-dichiara la cella R2 ✅ della matrice.

### LOW (igiene, annotazioni)
- **L1-sem** commento su `Contract.motivo_chiusura`: «enum chiuso a 4» — sono 5 (manca
  `TERMINAZIONE_SALDO_TRAINER`, ADR-018).
- **L2-sem** `core/constants.py::EventStatus` fermo a 4 stati + claim «mirror» in agenda.py oggi
  falso (mitigato: core/ dormiente, mai importato da api/ — verificato). Casa: risveglio core.
- **L3-sem** puntatore «DISPLAY-EXEMPT ADR-017 §3.2» NON risolve (ADR-017 non ha §3.2 né il
  token); il record vero = **ADR-017 Addendum I D-DENYLIST-INTATTE** + censimento
  `SPEC_LATE_CANCEL_NO_SHOW §6.2` (in archive). Accettazione ESISTE, puntatore da correggere.
- **L4-sem** commento in contracts.py cita il «grep-guard ADR-017 in check-all.sh» — ritirato in
  G9.4-b; il presidio vero è `test_adr017_rinviato_fuori_occupazione_ma_nel_breakdown`.
- **L5-sem** `schema_sync._backfill_quota_stornata_rettifiche` scrive la causale
  `'BACKFILL_LEGACY'` come **literal raw-SQL** bypassando la costante (secondo scrittore fuori
  penna, sanzionato ma non parametrizzato) + docstring modello da emendare.
- **L6-sem** matrice, riga «Stati crediti/wallet»: celle R3/DV/CP a ⚠️ **senza gate indicato**
  (la legenda lo impone). Casa da dichiarare: P4/P5 (portafoglio).
- **L7-sem** `frontend/src/components/agenda/calendar-setup.ts` hardcoda le label penali invece
  di consumare `EVENT_STATUS_LABELS` (due copie divergibili).

## 5. Piano ratificando — fetta R1 (pre-bump, un commit fix + un commit docs)

### R1-code (fix chirurgici dentro dottrina già ratificata — NESSUN nuovo ADR)
| # | Fonte | Fix (shape) | Gemello/AC |
|---|---|---|---|
| R1.1 | M1-sem | Predicato-famiglia SSoT `is_chiusura_da_terminazione(motivo)` in `transitions.py` accanto a `AUTO_REOPEN_ALLOWLIST`; consumato dal guard B-bis di `unpay_rate` E dal predicato I1 di `contract_state` (2 interpreti → 1) | unpay su CHIUSO `CONSUNZIONE` (PARI, rata SALDATA) → **409 col messaggio curato**; test di totalità: ogni membro `MotivoChiusura` classificato. **Provato ROSSO sul codice attuale** |
| R1.2 | M2-sem | `sedute_penali = Σ cb.get(s,0) for s in cstate.STATI_PENALE` | gemello esistente lista==dettaglio resta verde; grep literal → 0 |
| R1.3 | M4-sem | `get_orphan_events` delega a `_crediti_usati_map` + `cstate.crediti_residui` (clamp) | worklist coerente col SSoT (test esistenti) |
| R1.4 | L5-sem | costante `CAUSALE_BACKFILL_LEGACY` consumata dal raw-SQL del backfill + docstring modello «…più il backfill boot» | test backfill esistenti verdi |
| R1.5 | F1-money | **[decisione founder §6]** PIN raccomandato: unit-oracle su `posizione_netta_contratto` (net = versato − rimborsato − erogato-vivi) | oracolo collezionabile o simbolo rimosso |

**Quality gate R1-code:** full suite (diff tocca `api/` money-adjacent) + check-all +
`financial-invariant-verifier` mirato sul diff R1.

### R1-docs (un commit)
H1+H2 (INDEX: riga SPEC_G9.7 + sezione ADR →025) · M1/M2/M4-drift (conteggi 860/103/372, idioma
soft-SSoT dove sensato) · L2-drift (breadcrumb collocazione) · L1-sem (commento enum 5) ·
L3-sem (puntatore → ADR-017 Add. I D-DENYLIST-INTATTE) · L4-sem (commento guard ritirato) ·
L6-sem (celle wallet: casa P4/P5 dichiarata).

## 6. Deferral e decisioni founder (nessuna blocca R1)
1. **F1 pin-vs-delete** (`posizione_netta_contratto`): PIN raccomandato (15 righe, conserva il
   gradino G8.2 registrato); DELETE difendibile (YAGNI, git conserva). → R1.5.
2. **INC-2026-03-29 senza postmortem** (M3-drift): policy da decidere (P1 fixato same-day =
   catalogo-only in INDEX?). In coda, non release-relevant.
3. **Sensibilità guard lifecycle check-all** (`**Stato:** ✅` literal vs 🟢/inline): decidere se
   estendere il pattern o ratificare l'emoji-convention fuori guard. Minore.
4. **M3-sem → P1** (depositato in SPEC_P §P1): il gemello 7-classi copre ANCHE gli interpreti
   read-model, non solo `classify`. · **L2-sem/L7-sem** → risveglio core / P5.

## 7. Gate di release — conclusione
**Taglio SBLOCCATO a valle di R1.** Denaro preservato con evidenza meccanica; drift solo
documentale; l'unico buco comportamentale (M1-sem) è prod-only su path stretto, con fix che rende
totale una legge già scritta. Dopo R1: **step 2 runbook = OD-1** (convalida `classify` read-only
sui backup di Alessio E Chiara — salto doppio v1.0.10→v1.0.14) → bump versione → pipeline ADR-004
→ consegna e verifica sul campo → **allineamento `main` col trigger giusto del modello B**.

## 8. Calibrazione prima corsa `semantic-birth-auditor`
- **Segnale:** 1 buco comportamentale reale (M1, invisibile a 860 test perché mascherato dal gate
  in dev) + 2 drift reali **nel codice del suo stesso autore** (M2/M4, scritti in G9.7.2/3) +
  zero rumore sui rischi accettati. Il sistema di enforcement ha beccato chi l'ha costruito:
  funziona.
- **Rumore:** zero falsi positivi suoi. L'unico falso positivo della triade è del *drift-auditor*
  (L1 tabelle, errore aritmetico) — **lezione di triage: i conteggi degli agenti si ri-verificano
  sulla loro stessa evidenza prima di correggere un doc.**
- Verdetto «AT RISK» con 0 HIGH = severo per costruzione (*when in doubt, report*): corretto — il
  gate umano resta il triage, l'agente non deve assolvere.
