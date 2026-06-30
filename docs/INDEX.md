# docs/ — Indice documentazione

Ogni documento ha un dominio. Se non sai dove cercare, parti dalla directory del dominio.

> **Prima volta sul progetto?** Parti da `ARCHITECTURE.md` (root) — overview di sistema e bussola macro.
> Poi `CLAUDE.md` per le regole operative. Questo indice è il dispatcher per il dettaglio per dominio.

---

## business/ — Strategia, numeri, partner, legal

| File | Scopo | SSoT per |
|------|-------|----------|
| `BUSINESS_PLAN.md` | BP v4.3 — strategia, mercato, team, pricing, POC, community | Numeri, pricing, modello |
| `STRATEGY_PLAN.md` | Piano operativo lancio, category creation PT Evoluto, ruolo partner | Go-to-market |
| `FINANCIAL_MODEL.md` | Modello analitico — ogni euro tracciabile, formule, 3 scenari, NASpI (§8), fondi (§9) | Proiezioni finanziarie |
| `DOCUMENTO_OPERATIVO_PARTNER.md` | Accordo partner: compenso, equity, milestone, obblighi | Termini partnership |
| `LEGAL_REGULATORY_REPORT.md` | Report legale-regolamentare v1.3: GDPR (modello distribuito), fiscale, IP, EAA, SBOM, PSD2 | Compliance |
| `COMPETITIVE_ANALYSIS.md` | Competitor, posizionamento, differenziatori | Analisi mercato |
| `REVENUE_ACCELERATION_STRATEGY.md` | 5 leve per accelerare ricavi senza compromettere conquista mercato | Gap reddito founder, pricing internazionale, upsell |

**Gerarchia**: BP e' la fonte di verita' strategica. SP operativizza il BP. FM quantifica il BP. RAS identifica leve incrementali. Partner Doc e Legal sono satelliti.

---

## product/ — Roadmap, feature future, video

| File | Scopo |
|------|-------|
| `POST_LAUNCH_ROADMAP_90D.md` | Roadmap 90 giorni: PWA, mobile, Box, science nudges, GTM |
| `POST_LAUNCH_ISSUES.md` | Issue aperte post-lancio |
| `FITSCAN_ARCHITECTURE.md` | Spec tecnica FitScan: DB schema, Biomechanical Engine, Pose Provider |
| `VIDEO_GUIDE_STRATEGY.md` | Sistema video-guide contestuali: 4 livelli, mapping pagine |
| `VIDEO_PRODUCTION.md` | Pipeline video: manifest SSoT, flusso continuo, selettori |
| `RECURRING_SESSIONS_SPEC.md` | Spec sessioni ricorrenti (pianificazione, aderenza, calendario) |

---

## scientific/ — Certificazione motori deterministici

| File | Scopo | SSoT per |
|------|-------|----------|
| `PARAMETER_REGISTRY.md` | ~717 parametri con confidenza e fonti | Ogni numero nei 5 motori |
| `TRAINING_SCIENCE_CERTIFICATION.md` | Training Science + Intelligence + Diff | EMG, volume, balance, scoring, compliance |
| `SAFETY_ENGINE_CERTIFICATION.md` | Safety Engine | 47 condizioni, 80 regole, 5 farmaci |
| `NUTRITION_SCIENCE_CERTIFICATION.md` | Nutrition Science Engine | LARN, CREA, porzioni, scoring 3 assi |

**Gerarchia**: Registry e' la fondazione (ogni numero ha riga di codice). I 3 documenti di certificazione lo referenziano per i valori, aggiungono architettura, algoritmi e zone di incertezza.

---

## technical/ — Architettura, sicurezza, infrastruttura

| File | Scopo |
|------|-------|
| `SECURITY_MODEL.md` | **Reference unico sicurezza (vivo):** threat model + tassonomia attaccanti L0-L4, 6 livelli protezione (L1-L6 + L3b), network hardening, roadmap (cifratura crm.db = gate Tier-1 attivo G1). Gli audit storici e la strategia anti-RE sono in `docs/archive/` |
| `LICENSE_ACTIVATION.md` | Attivazione licenza, hardware binding, CLI admin |
| `TUNNEL_ARCHITECTURE.md` | **Sottosistema tunnel (riferimento unico):** design (problema, P1-P10, P2 data-blind), build (migrazione Tailscale→FRP, 4 fasi, gap analysis), operations (setup VPS edge, costi, DR). Consolida i 4 doc storici. |
| `TUNNEL_SECURITY_BOUNDARY.md` | **Confine di sicurezza + piano "Strada B":** acceptance criteria (confine JWT, rate limiter, apertura selettiva), piano implementazione (lockout, role JWT, guard, test e2e). Stato: approvato, non ancora implementato. |
| `DEPLOYMENT_PLAN.md` | Piano deploy: PyInstaller/Nuitka, standalone, Inno Setup |
| `NUTRITION_ENGINE_V3.md` | Architettura Nutrition Engine v3 |
| `PRE_DELIVERY_SECURITY_GATE.md` | Gate di sicurezza pre-consegna: 12 voci in 3 tier (G1-G12), stato annotato contro il codice reale. G1 (cifratura crm.db) attivo → ADR-013 |
| `EXERCISE_LIBRARY_STRATEGY.md` | Strategia libreria esercizi/media v2.2 (hosting centrale media §4ter). **Congelato 2026-06-16** (pivot security gate). Riferimento unico libreria esercizi |
| `FINANCIAL_DOMAIN_MODEL.md` | **SSoT del dominio finanziario (vincolante) — v1.3:** entità, 3 assi (tempo/crediti/denaro + netto via `totale_rimborsato`/`quota_stornata`, Strada B), 4 stati di vita (ATTIVO/SOSPESO/ESAURITO/CHIUSO), terminazione anticipata (§3.1/§7-G7), data_scadenza nullable (§2), vocabolario univoco (aperto≠attivo), invarianti anti-perdita (§9). `contract_state.py` lo deriva |
| `TASSONOMIA_FINANZIARIA.md` | **Vocabolario finanziario condiviso (vincolante su concetti e formule) — v1.2:** 3 assi (liquidità reale/cassa **bidirezionale**, competenza, pianificazione), predicato movimento contrattuale IN/OUT, `RIMBORSO_CONTRATTO` + 9 query da allineare (§7). `cash_categories.py` lo deriva |
| `SPEC_VOCABOLARIO_E_CLASSIFICAZIONE_CONTRATTI.md` | **Spec consumo-SSoT + vocabolario UI (vincolante sugli AC) — v1.1:** la classificazione degli stati contratto su tutte le superfici deriva da `contract_state`, non si reimplementa. Due assi mai fusi (vita × denaro), `is_insolvente` derivato, modulo `contract-status.tsx`. **Giro 1 fatto** (`/contratti` + dettaglio + backend) → **Giro 2 pendente** (`rinnovi-incassi` + `workspace_engine` + grep-guard) |
| `IMPL_PLAN_FINANCIAL_REALIGN.md` | **Unico piano attivo + RESUME POINT del filone finanziario** (workflow-verified). FATTI: Blocchi 0-3 + Prereq P + PREREQ-prezzo + Giro 1 vocabolario + data_scadenza-null + **G6** + **SPEC_REVISIONE_PRE_G7 (Sez. A+B)** + **terminazione G7.0→G7.4** (schema + conguaglio + endpoint terminate/settlement-preview/reopen + ritiro PUT chiuso + migrazione test + frontend). **✅ G7.5 + G7.6 FATTI (2026-06-25). PROSSIMO: G1 (cifratura).** §4 = blocco terminazione (G7.0-G7.4); §5/§5-bis/§5-ter = G7.5 (query-cassa + D4/D2); §7 = G7.6 runbook muti (data-driven) |
| `SPEC_REVISIONE_PRE_G7.md` | **Spec bridge Chat→Code — IMPLEMENTATA.** Sez. A convergenza del residuo a `contract_state.residuo()` (`6d5ba31`) + Sez. B copertura SOSPESO nel workspace `renewals_cash` (`38509e6`). Resta come design-record + AC. |
| `SPEC_G7.0_SCHEMA_TERMINAZIONE.md` | **Spec bridge Chat→Code — IMPLEMENTATA (G7.0).** Primo blocco dello scorporo G7 (G7.0→G7.6): 4 colonne terminazione (`totale_rimborsato`/`quota_stornata`/`data_chiusura`/`motivo_chiusura`) + indice + categoria `RIMBORSO_CONTRATTO` + marcatura `motivo_chiusura=COMPLETAMENTO` sui 2 auto-close (load-bearing per la reopen-allowlist G7.2) + response/TS. `residuo()` NON toccato (è G7.1). Zero comportamento di terminazione. Migrazione `d83abb993ea8` verificata su clone backup reale. La tabella §finale ha la sequenza G7.0→G7.6 |
| `AUDIT_PRE_G7.3_RAGGIO_STORNO.md` | **Audit code-grounded READ-ONLY (snapshot `d7bbcdc`, ratificato Bridge).** Mappa il raggio d'esplosione del primo storno (Classi A-D), l'inventario dei 16 test-scorciatoia `PUT chiuso=True` (1 presidio-NULL travestito), le discrepanze doc-vs-codice. Esiti: residuo Sez. A completa · invariante `versato==Σ ENTRATA` REGGE/additivo · `kpi_incassato` unico sovrastimante→netto in G7.3 · BLOCKER §4.7 parz. stale · confine G7.3/G7.5 (eccezione burn→cash-protection) · rinumerazione 9-query DA RATIFICARE in G7.5 · (le 6 decisioni esterne che bloccavano G7.3 sono risolte → **G7.3+G7.4 FATTI**). ⚠️ coordinate driftano: esiti durevoli, righe da riverificare. **Resta vivo come mappa-query per G7.5/6** (archiviare a chiusura di G7) |
| `SPEC_G7.3_TERMINAZIONE_ENDPOINT.md` | **Spec bridge Chat→Code — IMPLEMENTATA (G7.3, due commit `9acd2c5`+`3f1404b`).** Endpoint `POST /terminate` + `GET /settlement-preview` (Strada B): conguaglio puro G7.1 cablato (2 gambe conviventi: storno sempre + rimborso se overpaid), fonte-unica-importo, B-2-attiva (stato diretto, mai `_sync`), B-3 (soft-delete solo non-saldate), `kpi_incassato`→netto, esclusione-burn, microcopy "proposta ≠ obbligo legale", ritiro `chiuso` da `ContractUpdate` + migrazione 16 test (13 terminate/3 ORM) + frontend `TerminateContractDialog`. Sezione **0bis = 5 divergenze code-grounded** (motivo derivato; gambe conviventi; sedute=Completato; raffinamento §8 = 2 mini-presidi; entry-point ContractsTable). Suite 598 passed |
| `SPEC_TERMINAZIONE_BILATERALE_E_TUTELA_TRAINER.md` | **Spec bridge Chat->Code — ✅ IMPLEMENTATA (G7.9 2026-06-27 + G7.10 2026-06-28), ratificata da `ADR-018`. Corpo unificato (zero doppia-verità), design-record + AC.** Chiude la falla logica del recesso unilaterale: se `valore_servizio_reso > totale_versato`, il software non puo piu fare write-off implicito del saldo dovuto al trainer. Esito puro **balance-based** (`CREDITO_CLIENTE/TRAINER/PARI`); `credito_trainer > 0` obbliga una scelta esplicita: **`INCASSA_ORA`** (importo **editabile** `[0,R−V]` solo↓), **`RINUNCIA_ESPRESSA`** (nota obbl.) — **G7.9**; **`A_CREDITO`** (receivable `crediti_terminazione` fuori da `residuo()`, mai rata-fantasma) — **G7.10**. Nuova categoria `INCASSO_CONGUAGLIO_CONTRATTO`; `reopen` inverso esatto anche del nuovo incasso; audit strutturato; ramo `CREDITO_CLIENTE` byte-identico a G7.3 |
| `SPEC_INTEGRITA_CONTABILE_E_WALLET.md` | **Spec bridge Chat->Code — ✅ G8.1 + G8.1.1 + G8.2-prep IMPLEMENTATE (2026-06-28), ratificata `ADR-019`+`ADR-020`. Blocco G8.** Rende `reopen` **non-distruttivo**: la cassa mossa non si tocca, `residuo` **net-aware** (`P−netto−storno`), il contratto si **ricalcola** (S1–S7 → trattamento unico; rinnovo vivo → software-propone). Simmetria lato cliente: **rimborso editabile** `[0,credito_cliente]` + non-rimborsato → **wallet** (`crediti_cliente`) erogabile in cassa. **G8.1** (reopen-recompute + net-aware + wallet lean + rimborso editabile); **§14 = G8.1.1** (reconciliation + transparency, storico cassa/stato); **§15 = G8.2-prep / D1 forma-d** (fotografia netta per-contratto, `posizione_netta_contratto` + `assert_contract_invariants` I1/I4/I5 + harness, `reopen` riassorbe il wallet erogato → chiude **Bug-1** dell'audit posizione; delete-guard Bug-4; de-dup Bug-3). **G8.2** (wallet auto-cross-contratto) = elevazione **in panchina** (D2 aperta). Emenda G7.4 (true-to-ledger). Audit `AUDIT_REOPEN_SCENARIOS` + `AUDIT_POSIZIONE_FINANZIARIA_E_INVARIANTI_2026-06-28.md` |
| `SPEC_G9_FINANCIAL_COMMAND_LAYER.md` | **Spec bridge Chat→Code — DA IMPLEMENTARE (G9.0→G9.6), ratifica `ADR-022`.** Elevazione del **write-model**: dota il SSoT di lettura (`contract_state.py`) del gemello di **scrittura**. **G9.0** sensore invarianti ovunque (log-only) + reconciliation bidirezionale + 2 quick-win; **G9.1** penna unica `post_inflow`/`post_outflow` (I5 per costruzione); **G9.2** storno/fold come postings + `project_columns_from_ledger`; **G9.3** TransitionExecutor + FSM chiusura (router sottili); **G9.4** invarianti→409+rollback (flag) + grep-guard→test semantici; **G9.5** Hypothesis stateful machine; **G9.6** *(differito)* Money value-type. AC per gate + sequenza vincolante (strumenta-poi-imponi, branch sempre rilasciabile, behavior-preserving fino a G9.4). Audit `AUDIT_FINANCIAL_ARCHITECTURE_2026-06-30.md` |
| `AUDIT_POSIZIONE_FINANZIARIA_E_INVARIANTI_2026-06-28.md` | **Audit architetturale READ-ONLY (posizione finanziaria / invarianti / livelli CONTRATTO vs CLIENTE; trigger founder).** Tesi confermata sul **write-model decentralizzato** ma corretta: il **read-model è già centralizzato** (`contract_state.py`). Radice = nessun punto unico applica gli invarianti dopo le transizioni + nessuna posizione-CLIENTE di prima classe + clamp `max(0,…)` che silenziano. Money-bug **Bug-1** (reopen perdeva il wallet erogato) + Bug-3 (4 copie `stato_pagamento`) + Bug-4 (delete orfana la posizione). Fetta minima S0–S3 + D1 chiusa (forma-d) / D2 aperta. **→ implementato in G8.2-prep** (SPEC_INTEGRITA §15, ADR-019 Addendum II) |
| `SPEC_RINVIO_LIBERA_CREDITO.md` | **Spec bridge Chat→Code — DA IMPLEMENTARE (G7.8).** `Rinviato` non occupa il credito (occupazione = `Programmato + Completato`): corregge `contracts.py:149` (`+ rinviate` rimosso) + i siti credito. **`[Bridge Code 2026-06-26]`**: la v1 era esaustiva solo sui file in contesto → aggiunti 5 produttori `crediti_usati` mancati (`rates.py:565` auto-close `pay_rate` gemello payment-driven, `workspace_engine` ×3, `client_avatar`) + §3-bis overlap = CAMBIA. Asse denaro INVARIANTE (oracolo settlement byte-identico, §5). Copre `ADR-017`. Trigger: 2ª segnalazione Chiara |

> **Spec finanziarie implementate → `docs/archive/specs/`.** Le spec-feature SPEC_RINNOVO, SPEC_GESTIONE_FINANZIARIA_TEMPORALE e SPEC_RINNOVI_SCADUTI_E_RETENTION sono state implementate e il loro modello vive ora nel SSoT (FDM + TASSONOMIA + `contract_state.py`). Sono archiviate come design-record insieme ai rispettivi IMPL_PLAN. Il dominio finanziario vivo è: FDM + TASSONOMIA (SSoT) · SPEC_VOCABOLARIO (Giro 2 aperto) · SPEC_REVISIONE_PRE_G7 + SPEC_G7.0 + SPEC_G7.3 (implementate, design-record) · AUDIT_PRE_G7.3_RAGGIO_STORNO (mappa-query verificata, viva per G7.5/6) · IMPL_PLAN_FINANCIAL_REALIGN (piano attivo) · SPEC_RINVIO_LIBERA_CREDITO (G7.8, copre ADR-017) · SPEC_TERMINAZIONE_BILATERALE (G7.9 core + G7.10 differito, ✅ implementata, ratificata ADR-018) · SPEC_INTEGRITA_CONTABILE_E_WALLET (G8 reopen non-distruttivo + wallet cliente; G8.1+G8.1.1+G8.2-prep implementate 2026-06-28, ratificata ADR-019/020; G8.2 cross-contratto in panchina) · AUDIT_POSIZIONE_FINANZIARIA_E_INVARIANTI (audit posizione/invarianti → G8.2-prep) · ADR-014/015/016/017/018/019/020 (decisioni). **Archiviato 2026-06-27:** `SPEC_G7.7_R5_TRASPARENZA_E_AZIONI_FRONTEND.md` (task frontend chiuso, verifica visuale founder + `next build` verde) · `SPEC_RETRODATAZIONE_SCADENZA_E_AUDIT_LIFECYCLE.md` (task backend audit chiuso, 6+11 test verdi + `ruff check api/`). |

---

## operations/ — Procedure, release, supporto

| File | Scopo |
|------|-------|
| `AUDIT_TERMINAZIONE_BILATERALE_2026-06-27.md` | **Audit senior del gap residuo sul recesso bilaterale.** Dopo G7.7/G7.8 conferma che il calcolo su asse EROGATO regge, ma il ramo `servizio_reso > versato` resta sbilanciato: il codice materializza una rinuncia implicita del trainer invece di obbligare una scelta esplicita tra incasso contestuale e rinuncia auditata. Fondamento del blocco `SPEC_TERMINAZIONE_BILATERALE_E_TUTELA_TRAINER.md` (ADR-018) |
| `AUDIT_REOPEN_SCENARIOS_2026-06-28.md` | **Audit specifico sugli scenari di riapertura di un contratto terminato** (trigger founder). `reopen` è **sovraccaricato**: un verbo per 3 operazioni (undo / storno-correttivo / riattivazione), che soft-cancella scritture di cassa fiscalmente rilevanti scavalcando la protezione del mastro. Matrice S1–S7 + grounding fiscale (niente layer documentale → il `CashMovement` è il dato fiscale). **Principio unificante:** la cassa mossa non si tocca mai; reopen ricalcola; debito→contratto, credito→wallet; software-propone per le dipendenze a valle. Fonda **ADR-019** (mastro non-distruttivo) + **ADR-020** (wallet) |
| `AUDIT_PIANO_RATE_VS_RESIDUO_2026-06-29.md` | **Audit "il piano rate diverge dal residuo" (trigger: test di flusso del trainer reale Chiara Pais, contratto 35).** Un contratto SALDATO (`residuo()=0`) mostra una rata PARZIALE/scaduta con residuo-rata **fantasma** = un incasso **non-rata** (conguaglio/`incassa-residuo`) che abbassa `residuo()` ma non tocca il piano rate (riconciliato solo su reopen). Radice architetturale: **due ledger dell'obbligazione, SSoT solo su uno**; il read-model misura la divergenza (`piano_allineato=False`) e la spedisce alla UI. Legge mancante **INV-RATE** (`Σ residui-rata ≤ residuo()`) → **ADR-021** + `SPEC_INTEGRITA §17` (G8.3, stance C: riconcilia-ovunque + I6 harness + proiezione) |
| `AUDIT_INTEGRITA_RESIDUI_2026-06-29.md` | **Audit dei difetti residui di integrità DOPO G8.2-prep** (3° passaggio adversariale, verificato riga-per-riga). NON tocca l'aritmetica (asse DENARO regge) ma la **trasparenza/integrità amministrativa**: **P1** terminazione parziale = due verità sul rimborso nell'audit grezzo (`rimborso_out` vs `credito_cliente`); **P2** `DELETE force=true` aggira il guard sui crediti aperti → wallet/receivable orfani su contratto soft-deleted; **P3** lo storico reopen non spiega la cassa preservata (campo mai emesso). Tutti **completamenti di decisioni già accettate** (ADR-018/019), nessun nuovo ADR → **ADR-019 Addendum III** + **SPEC_INTEGRITA §16** (fix A/B/C falsificabili) |
| `AUDIT_FINANCIAL_ARCHITECTURE_2026-06-30.md` | **Audit architetturale READ-ONLY del write-model contrattuale-economico** (trigger founder post-G8.3; review multi-agente: 8 reader + 5 lenti senior + sintesi). Tesi confermata: `contract_state.py` è un ottimo SSoT di **lettura** ma **manca il gemello di scrittura** → il ledger `CashMovement` è **consultivo, non load-bearing**. Smoking gun: `quota_stornata` entra nel `residuo()` ma non ha posting; il fold R2-bis del reopen è una rettifica senza movimento; la `/reconciliation` è la diagnosi (audit post-facto e monco). Meta-pattern: gli 8 ADR (016→021) riscoprono la stessa legge. Strato mancante = **financial command layer** (penna unica + transition executor + invarianti imposti). Fonda **ADR-022** + `SPEC_G9_FINANCIAL_COMMAND_LAYER.md` (blocco G9) |
| `RELEASE_CHECKLIST.md` | Checklist release: preflight, build, verify, seal |
| `RUNTIME_DIAGNOSTICS_PLAYBOOK.md` | Diagnostica runtime: log, errori, recovery |
| `SUPPORT_RUNBOOK.md` | Runbook supporto: licenza, backup, restore, troubleshoot |
| `RUNBOOK_REMEDIATION_CONTRATTI_MUTI.md` | **G7.6** — bonifica contratti chiusi legacy (`motivo_chiusura=NULL`): diagnostica data-driven, albero decisionale per profilo (LEAVE/reopen/terminate), per-contratto, reversibile, mai bulk. Esecuzione trainer-driven via endpoint G7.3/G7.4 |
| `UPGRADE_PROCEDURE.md` | Procedura upgrade: in-place, fallback, checklist |
| `DEPLOYMENTS.md` | Registro consegne: chi ha quale versione, SHA-256, licenza |

---

## adr/ — Architecture Decision Records

20 ADR attivi (ADR-001 → ADR-022; ADR-002 rimossa come obsoleta, ADR-012 riservato). Ultimi: **ADR-022** (**financial command layer: il ledger diventa load-bearing** — il SSoT di lettura `contract_state.py` acquista il gemello di scrittura: penna unica di posting [I5 vero per costruzione] + transition executor [router sottili] + invarianti imposti [da log-only-su-reopen a gate su tutte le transizioni; grep-guard→test semantici + Hypothesis] + storno-ha-casa + Money differito; **consolida** [non supersede] il meta-pattern di ADR-016→021; strumenta-poi-imponi, evolvi non riscrivere; blocco G9 G9.0→G9.6, **accettata/pianificata zero-codice**, 2026-06-30); **ADR-021** (**piano rate = partizione del residuo** — `Σ residui-rata ≤ residuo()` [INV-RATE], riconciliazione su ogni path che muove il residuo + I6 nell'harness; generalizza D-RECONCILIA-RATE da reopen-only; blocco G8.3, 2026-06-29); **ADR-018** (terminazione bilaterale — incasso-editabile/rinuncia + credito differito `crediti_terminazione` fuori da `residuo()`, estende ADR-016; blocchi G7.9+G7.10, 2026-06-27); **ADR-019** (libro mastro **non-distruttivo** + `reopen` **ricalcola-e-instrada** — la cassa mossa non si tocca, `residuo` net-aware, debito→contratto/credito→wallet, software-propone per le dipendenze a valle; **emenda G7.4** reopen-inverso-esatto; 2026-06-28); **ADR-020** (**wallet del cliente** = customer credit balance — rimborso editabile + non-rimborsato/overpayment → credito spendibile/rimborsabile, completa il lato cliente di ADR-018; v1 lean; 2026-06-28). ADR-019/020 nascono dall'osservazione del founder su reopen (audit `AUDIT_REOPEN_SCENARIOS_2026-06-28.md`). Indice in `adr/README.md`.

## incidents/ — Post-mortem

| File | Scopo |
|------|-------|
| `INC-2026-03-28-safety-engine-blind-spot.md` | P0: Safety Engine blind spot durante demo investitore |
| `INC-2026-03-29-portal-url-origin-mismatch.md` | P1: Link portale clienti inaccessibili — URL hardcoded da PUBLIC_BASE_URL invece di browser origin |
| `INC-2026-03-30-portal-mobile-invisible-ui.md` | P1: Portale workout invisibile su mobile — CSS variables dark mode + rate limiter bloccante |
| `INC-2026-04-19-catalog-taxonomy-empty.md` | P0: catalog.db tassonomia vuota dopo consegna v1.0.7 — Safety Engine cieco, 6 tabelle vuote, gap pipeline seed/build |
| `INC-2026-06-08-kpi-fatturato-contratti-chiusi.md` | P1: KPI fatturato/incassato escludevano i contratti chiusi — metriche storiche errate (v1.0.9) |
| `INC-2026-06-15-installer-frpc-lock.md` | P2: upgrade installer bloccato (codice 5) da `frpc.exe` orfano — Job Object kill-on-close + installer chiude i processi (v1.0.12) |
| `INC-2026-06-18-fingerprint-partial-license-lockout.md` | P1: hash fingerprint parziale → falso `wrong_machine` → blocco CRM intermittente. Fail-closed + no cache dei fallimenti (v1.0.13) |

## learning/ — Diario di apprendimento personale

Formazione del founder-developer in parallelo allo sviluppo. Concetti tecnici studiati, diario cronologico, metodo di studio.

**NON vincolante per il codice** — materiale didattico personale, ignorato durante l'implementazione. Dettagli in `learning/README.md`.

| File | Ambito |
|------|--------|
| `LEARNING_METHOD.md` | Metodo di studio: 4 principi, flusso cattura/elaborazione, ponte con Claude Code |
| `BUILD_LOG.md` | Diario cronologico: cosa ho fatto e quando |
| `LEARNING_FASE1_BASI_TEORICHE.md` | Basi teoriche di programmazione e architettura |
| `LEARNING_PROGRAMMAZIONE.md` | Concetti di programmazione incontrati nel codebase |
| `LEARNING_APP_ARCHITECTURE.md` | Dominio nel codebase: rinnovo sequenziale, semantica date, convenzioni CRM |
| `LEARNING_LINUX_SYSADMIN.md` | Crittografia asimmetrica, chiavi SSH, passphrase |
| `LEARNING_NETWORKING.md` | Reti, DNS, TLS, SNI |
| `LEARNING_TUNNEL_MANAGER.md` | Babysitter frpc: subprocess, backoff, Job Object |
| `LEARNING_MEDIA_CLOUD_ARCHITECTURE.md` | Routing per classificazione del dato, hosting media centrale |
| `LEARNING_BUILD_DISTRIBUZIONE.md` | Build Nuitka, packaging, installer |
| `LEARNING_GIT_VERSIONAMENTO.md` | Git, branching, versionamento |

---

## Altre directory

| Directory | Contenuto |
|-----------|-----------|
| `archive/specs/` | Spec storiche frozen (non modificare): UPG storici + spec finanziarie implementate (SPEC_RINNOVO, SPEC_TEMPORALE, SPEC_RINNOVI_SCADUTI + i loro IMPL_PLAN, archiviati 2026-06-23) + `SPEC_G7.7_R5_TRASPARENZA_E_AZIONI_FRONTEND.md` e `SPEC_RETRODATAZIONE_SCADENZA_E_AUDIT_LIFECYCLE.md` (archiviate 2026-06-27) |
| `archive/` (root) | Snapshot storici: audit sicurezza pre/post-hardening, strategia anti-RE (implementata), pre-delivery audit 04-17, session handoff datati, DUAL_ENV, Tailscale |
| `archive/nutrition-v2-strategy.md` | Strategia nutrition v2 (obsoleta, 226 alimenti → ora 880) |
| `upgrades/` | Spec upgrade attive |
| `videos/` | Script video-pillole |
