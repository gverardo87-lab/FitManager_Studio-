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
| `CATALOGO_SCENARI_PT.md` | **Fondamento product ADR-025 (vivo):** 96 scenari quotidiani reali del PT/chinesiologo (6 lenti + critic), copertura mappata sul modello attuale (15% piena · 51% parziale · 34% assente), 23 domande aperte per l'ADR. Base di conoscenza del futuro agente `pt-reality-auditor`. Gemello: `archive/RICERCA_COMPETITOR_WALLET_SEDUTE_SINGOLE_2026-07-07.md` (leggi W1-W11) |
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

## technical/ — SSoT evergreen (com'è FATTO il sistema)

**Solo riferimenti permanenti** (contratto di contesto in `CLAUDE.md`): zero SPEC_*/IMPL_PLAN_* (guard in
`check-all.sh`). Le spec aperte vivono in `docs/specs/`, le chiuse in `docs/archive/specs/`.

| File | Scopo |
|------|-------|
| `MATRICE_ASSI_SEMANTICI.md` | **Matrice assi×regole (ADR-024, vivo):** ogni asse di stato × le 4 regole del metodo + derivati-a-video + composizione protezioni. Un asse senza riga = non governato. Nata G9.7.0 (2026-07-07); a G9.7 chiuso deve essere tutta ✅ o rischio dichiarato |
| `SECURITY_MODEL.md` | **Reference unico sicurezza (vivo):** threat model + tassonomia attaccanti L0-L4, 6 livelli protezione (L1-L6 + L3b), network hardening, roadmap (cifratura crm.db = gate Tier-1 attivo G1). Gli audit storici e la strategia anti-RE sono in `docs/archive/` |
| `LICENSE_ACTIVATION.md` | Attivazione licenza, hardware binding, CLI admin |
| `TUNNEL_ARCHITECTURE.md` | **Sottosistema tunnel (riferimento unico):** design (problema, P1-P10, P2 data-blind), build (migrazione Tailscale→FRP, 4 fasi, gap analysis), operations (setup VPS edge, costi, DR). Consolida i 4 doc storici. |
| `TUNNEL_SECURITY_BOUNDARY.md` | **Confine di sicurezza + piano "Strada B":** acceptance criteria (confine JWT, rate limiter, apertura selettiva), piano implementazione (lockout, role JWT, guard, test e2e). Stato: approvato, non ancora implementato. |
| `DEPLOYMENT_PLAN.md` | Piano deploy: PyInstaller/Nuitka, standalone, Inno Setup |
| `NUTRITION_ENGINE_V3.md` | Architettura Nutrition Engine v3 |
| `PRE_DELIVERY_SECURITY_GATE.md` | Gate di sicurezza pre-consegna: 12 voci in 3 tier (G1-G12), stato annotato contro il codice reale. G1 (cifratura crm.db) attivo → ADR-013 |
| `EXERCISE_LIBRARY_STRATEGY.md` | Strategia libreria esercizi/media v2.2 (hosting centrale media §4ter). **Congelato 2026-06-16** (pivot security gate). Riferimento unico libreria esercizi |
| `FINANCIAL_DOMAIN_MODEL.md` | **SSoT del dominio finanziario (vincolante) — v1.3:** entità, 3 assi (tempo/crediti/denaro + netto via `totale_rimborsato`/`quota_stornata`, Strada B), 4 stati di vita (ATTIVO/SOSPESO/ESAURITO/CHIUSO), terminazione anticipata (§3.1/§7-G7), data_scadenza nullable (§2), vocabolario univoco (aperto≠attivo), invarianti anti-perdita (§9). `contract_state.py` lo deriva. ⚠️ da aggiornare: asse occupazione a 6 stati Event (G7.8-bis) |
| `TASSONOMIA_FINANZIARIA.md` | **Vocabolario finanziario condiviso (vincolante su concetti e formule) — v1.2:** 3 assi (liquidità reale/cassa **bidirezionale**, competenza, pianificazione), predicato movimento contrattuale IN/OUT, `RIMBORSO_CONTRATTO` + 9 query da allineare (§7). `cash_categories.py` lo deriva |

---

## specs/ — Fronte di lavoro APERTO (`ls docs/specs/` = work-queue)

Riga `Stato:` obbligatoria in testa. A chiusura blocco: consuntivo + `docs/archive/specs/` nello stesso
commit docs del gate (ciclo di vita: `AGENTS.md`).

| File | Stato | Scopo |
|------|-------|-------|
| `SPEC_COLLABORAZIONE_CLAUDE_CODEX.md` | 🟡 **APERTA — A0+A1 CHIUSI; A2+ NON AUTORIZZATI E SEPARATI DALLA v1.0.14** | Contratto docs-first agent-neutral: `AGENTS.md` nucleo unico, `CLAUDE.md` preservato come adapter Claude, nessun `CODEX.md`; runbook condiviso + Contract Smoke reali Claude/Codex PASS. Condizione per nuovo codice congiunto soddisfatta; migrazione futura fuori dalla coda prodotto v1.0.14 → P → G-MAC |
| `SPEC_FRONTEND_CORE_INTUITIVITA.md` | 🟡 **APERTA — FE-0 CHIUSO; FE-1.0 IN VALIDAZIONE LIVE** | Remediation audit frontend core. FE-0 privacy/truth state ✅; FE-1.0 Contextual Deep-Link Contract v1 implementato (`f678292`) e corretto per re-navigation App Router (`d382a4b`), con 149/149 test e MONEY AXIS PRESERVED; manca il retest LIVE founder prima della chiusura. FE-2..4 restano gated |
| `SPEC_G9_FINANCIAL_COMMAND_LAYER.md` | 🟢 G9.0→G9.5 CHIUSI · **resta G9.6 (differito)** | Write-model del dominio finanziario (ADR-022): penna unica ✅, ledger rettifiche ✅, TransitionExecutor+FSM ✅, enforcement ✅ + test semantici ✅ (grep ritirati), Hypothesis stateful ✅ (G9.5, 2026-07-05); resta SOLO **G9.6** Money centesimi (differito, gated) |
| `SPEC_G8.4_TRASPARENZA_FINANZIARIA_FE.md` | 🟡 **F1+F5 ✅ · F2+F6 ✅ · F3 ✅** — resta SOLO apertura G8.5 (DoD §8.5) | Trasparenza finanziaria frontend. Netto SSoT + `saldo_progressivo` + guard FE-no-money-math + split <300 (`5086045`..`1978572`) · disclosure D-1 + colore semantico (`0b80bc8`) · raccomandazione solo-visiva + advisory `azione_consigliata` + a11y + penali nel breakdown (`58c01ea`). D-2 «Saldo» ledger → **ADR-019 Add. IV**; ricerca `archive/RICERCA_COMPETITOR_TRASPARENZA_FINANZIARIA_2026-07-06.md`. Chiusura gated su apertura G8.5 (goodwill, ADR+spec) |
| `SPEC_G9.7_SEMANTICA_PER_CLASSE.md` | 🟢 **G9.7.0→G9.7.5 CHIUSI** · resta solo runbook orfani reali trainer-driven | Generalizzazione per-classe delle leggi semantiche (ADR-024): matrice assi×regole, mai-silenzio eventi, recupero esplicito, occupazione spiegabile, guard di classe, perimetro transizioni, birth-auditor e Hypothesis estesa. Tutti i gate di codice sono consuntivati; la spec resta nel work-queue esclusivamente per il recupero esplicito 640/641/643/647/649 |
| `SPEC_VOCABOLARIO_E_CLASSIFICAZIONE_CONTRATTI.md` | ✅ Giro 1 · **⏳ Giro 2 pendente** | Consumo-SSoT stati contratto su tutte le superfici: restano `rinnovi-incassi` + `workspace_engine` off-SSoT + grep-guard |
| `SPEC_P_PRESTAZIONI_SINGOLE_E_PORTAFOGLIO.md` | 🟡 **APERTA — P0 CHIUSO 2026-07-08** (P-D1..P-D6 ratificate, P-D6 rivista: Q9→G8.2+G8.5; riga matrice + birth-review: CP-1..CP-4 foldati) → **prossimo P1** | Blocco «P»: prestazione singola come classe economica di prima classe (7ª `ClasseContabile` col gemello, tabella `prestazioni_singole`, penna dedicata, invarianti IP1-IP4) · insoluto derivato fail-loud · compensazione wallet atomica · condono auditato · suggeritore prezzo spiegabile (W9) · pannello Portafoglio + `crediti_residui_attivi` (chiude P1-P5 audit FE). Gate P0..P6, interlock G9.7.2 (recupero 640/641) |

**Backlog (non-spec, censito qui):** G8.2 wallet auto-cross-contratto (in panchina, D2 aperta) + Q9
conversione singole→pacchetto (casa: G8.2+G8.5, P-D6 blocco P) · wallet
sotto-ledger append-only + forecast ponderato insolvenza (ROADMAP archiviata §1.1/§1.4, post-lancio) ·
punto tributarista: policy `pro_sedute` + penale nel recesso (PROVISIONAL) · FDM/TASSONOMIA asse 6-stati.

---

## operations/ — Procedure, release, supporto

| File | Scopo |
|------|-------|
| `AI_ASSISTED_DEVELOPMENT_WORKFLOW.md` | Runbook agent-neutral Claude Code + Codex: bootstrap, routing del contesto, metodo docs-first proporzionale, Delivery Loop, Contract Smoke read-only e stop conditions. Deriva da `AGENTS.md`, non modifica la coda prodotto |
| `AUDIT_TERMINAZIONE_BILATERALE_2026-06-27.md` | **Audit senior del gap residuo sul recesso bilaterale.** Dopo G7.7/G7.8 conferma che il calcolo su asse EROGATO regge, ma il ramo `servizio_reso > versato` resta sbilanciato: il codice materializza una rinuncia implicita del trainer invece di obbligare una scelta esplicita tra incasso contestuale e rinuncia auditata. Fondamento del blocco `SPEC_TERMINAZIONE_BILATERALE_E_TUTELA_TRAINER.md` (ADR-018) |
| `AUDIT_REOPEN_SCENARIOS_2026-06-28.md` | **Audit specifico sugli scenari di riapertura di un contratto terminato** (trigger founder). `reopen` è **sovraccaricato**: un verbo per 3 operazioni (undo / storno-correttivo / riattivazione), che soft-cancella scritture di cassa fiscalmente rilevanti scavalcando la protezione del mastro. Matrice S1–S7 + grounding fiscale (niente layer documentale → il `CashMovement` è il dato fiscale). **Principio unificante:** la cassa mossa non si tocca mai; reopen ricalcola; debito→contratto, credito→wallet; software-propone per le dipendenze a valle. Fonda **ADR-019** (mastro non-distruttivo) + **ADR-020** (wallet) |
| `AUDIT_PIANO_RATE_VS_RESIDUO_2026-06-29.md` | **Audit "il piano rate diverge dal residuo" (trigger: test di flusso del trainer reale Chiara Pais, contratto 35).** Un contratto SALDATO (`residuo()=0`) mostra una rata PARZIALE/scaduta con residuo-rata **fantasma** = un incasso **non-rata** (conguaglio/`incassa-residuo`) che abbassa `residuo()` ma non tocca il piano rate (riconciliato solo su reopen). Radice architetturale: **due ledger dell'obbligazione, SSoT solo su uno**; il read-model misura la divergenza (`piano_allineato=False`) e la spedisce alla UI. Legge mancante **INV-RATE** (`Σ residui-rata ≤ residuo()`) → **ADR-021** + `SPEC_INTEGRITA §17` (G8.3, stance C: riconcilia-ovunque + I6 harness + proiezione) |
| `AUDIT_INTEGRITA_RESIDUI_2026-06-29.md` | **Audit dei difetti residui di integrità DOPO G8.2-prep** (3° passaggio adversariale, verificato riga-per-riga). NON tocca l'aritmetica (asse DENARO regge) ma la **trasparenza/integrità amministrativa**: **P1** terminazione parziale = due verità sul rimborso nell'audit grezzo (`rimborso_out` vs `credito_cliente`); **P2** `DELETE force=true` aggira il guard sui crediti aperti → wallet/receivable orfani su contratto soft-deleted; **P3** lo storico reopen non spiega la cassa preservata (campo mai emesso). Tutti **completamenti di decisioni già accettate** (ADR-018/019), nessun nuovo ADR → **ADR-019 Addendum III** + **SPEC_INTEGRITA §16** (fix A/B/C falsificabili) |
| `AUDIT_FINANCIAL_ARCHITECTURE_2026-06-30.md` | **Audit architetturale READ-ONLY del write-model contrattuale-economico** (trigger founder post-G8.3; review multi-agente: 8 reader + 5 lenti senior + sintesi). Tesi confermata: `contract_state.py` è un ottimo SSoT di **lettura** ma **manca il gemello di scrittura** → il ledger `CashMovement` è **consultivo, non load-bearing**. Smoking gun: `quota_stornata` entra nel `residuo()` ma non ha posting; il fold R2-bis del reopen è una rettifica senza movimento; la `/reconciliation` è la diagnosi (audit post-facto e monco). Meta-pattern: gli 8 ADR (016→021) riscoprono la stessa legge. Strato mancante = **financial command layer** (penna unica + transition executor + invarianti imposti). Fonda **ADR-022** + `SPEC_G9_FINANCIAL_COMMAND_LAYER.md` (blocco G9) |
| `AUDIT_CENSIMENTO_ASSI_SEMANTICI_CASSA_2026-07-04.md` | **Censimento S1+S2 degli assi semantici finanziari** (trigger: INC-2026-07-03 falso allarme). 10 assi censiti (A10 occupazione = modello convergiuto; A2/A3 cassa a metà; A9 crediti/wallet senza SSoT), 8 interpreti cassa inventariati, **piano dei conti implicito ricostruito (6 classi)**, 8 finding (F1 mappa senza nome, F2 default silenzioso in lettura, F3 storno literal anche in scrittura). Fonda l'Addendum ADR-022 read-model + gate SPEC_G9 + charter agente semantic-birth-auditor |
| `AUDIT_PRE_RELEASE_2026-07-16.md` | **Triade auditor + runbook attivo v1.0.14.** **R1 CHIUSA** in `41d62e8` con 873 pytest, `check-all` e verifier **MONEY AXIS PRESERVED**. **OD-1 CHIUSO** sulla popolazione reale nota: backup Chiara PASS (205/205 movimenti classificabili, SQLite/FK integri, zero mutazioni); Alessio N/A su attestazione founder perché l'installazione consegnata non è usata in esercizio e non ha un database data-bearing noto. Prossimo gate: bump `v1.0.14` e pipeline ADR-004; restore Chiara resta gate della candidate |
| `RELEASE_CHECKLIST.md` | Checklist release: preflight, build, verify, seal |
| `RUNTIME_DIAGNOSTICS_PLAYBOOK.md` | Diagnostica runtime: log, errori, recovery |
| `SUPPORT_RUNBOOK.md` | Runbook supporto: licenza, backup, restore, troubleshoot |
| `RUNBOOK_REMEDIATION_CONTRATTI_MUTI.md` | **G7.6** — bonifica contratti chiusi legacy (`motivo_chiusura=NULL`): diagnostica data-driven, albero decisionale per profilo (LEAVE/reopen/terminate), per-contratto, reversibile, mai bulk. Esecuzione trainer-driven via endpoint G7.3/G7.4 |
| `UPGRADE_PROCEDURE.md` | Procedura upgrade: in-place, fallback, checklist |
| `DEPLOYMENTS.md` | Registro consegne: chi ha quale versione, SHA-256, licenza |

---

## adr/ — Architecture Decision Records

23 ADR accettati (ADR-001 → ADR-025; ADR-002 rimossa come obsoleta, ADR-012 riservato). Ultimi:
**ADR-025** (prestazione singola + Portafoglio cliente: fatto economico proprio, insoluto derivato
fail-loud, compensazione wallet come atto esplicito; blocco P) · **ADR-024** (semantica per-classe:
matrice assi×regole, fail-loud, perimetro transizioni, birth-auditor; G9.7) · **ADR-023**
(temporal fence: storia contabilizzata immutabile, varco unico `reopen`; G7.8-ter) · **ADR-022**
(financial command layer: penna unica, transition executor, invarianti imposti, read-model cassa,
rettifiche e Hypothesis; G9). ADR-019/020 restano la base del mastro non-distruttivo e del wallet;
Addendum recenti: ADR-017 Add. I (stati-penale) e ADR-022 Add. I/II (rettifiche + read-model).
Indice completo e autorevole in `adr/README.md`.

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
| `INC-2026-07-03-falso-allarme-entrate-negative-cassa.md` | P2 trasparenza (FALSO ALLARME): entrate nette −140,42 € percepite come bug rimborsi — calcolo esatto al centesimo, root cause = KPI netto opaco + read-model cassa decentralizzato. Origine del gate read-model G9 |

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
| `archive/specs/` | Spec storiche frozen (non modificare, **mai contesto di lavoro**): UPG storici + spec implementate. Batch 2026-07-03 (riordino): SPEC_G7.0, SPEC_G7.3, SPEC_REVISIONE_PRE_G7, SPEC_RINVIO (G7.8, superata da G7.8-bis), SPEC_TERMINAZIONE_BILATERALE (G7.9/10), SPEC_INTEGRITA (G8.1-G8.3), SPEC_LATE_CANCEL (G7.8-bis), IMPL_PLAN_FINANCIAL_REALIGN; 2026-07-04: SPEC_TEMPORAL_FENCE (G7.8-ter, ADR-023). Batch precedenti: SPEC_RINNOVO/TEMPORALE/RINNOVI_SCADUTI + IMPL_PLAN (06-23), G7.7_R5 + RETRODATAZIONE (06-27) |
| `archive/` (root) | Snapshot storici: audit sicurezza pre/post-hardening, strategia anti-RE, pre-delivery audit 04-17, session handoff, DUAL_ENV, Tailscale + (2026-07-03) AUDIT_PRE_G7.3, AUDIT_POSIZIONE_FINANZIARIA, ROADMAP_FINANCIAL_UPGRADES (fotografia foldata) |
| `archive/nutrition-v2-strategy.md` | Strategia nutrition v2 (obsoleta, 226 alimenti → ora 880) |
| `upgrades/` | 🗄️ **DISMESSO 2026-07-03** — assorbito da `learning/BUILD_LOG.md` (unico log di sviluppo); resta come storico UPG |
| `videos/` | Script video-pillole |
