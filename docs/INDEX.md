# docs/ — Indice documentazione

Ogni documento ha un dominio. Se non sai dove cercare, parti dalla directory del dominio.

> **Prima volta sul progetto?** Parti da `ARCHITECTURE.md` (root) — overview di sistema e bussola macro.
> Poi `CLAUDE.md` per le regole operative. Questo indice è il dispatcher per il dettaglio per dominio.

---

## business/ — Numeri, mercato e legal

| File | Scopo | SSoT per |
|------|-------|----------|
| `BUSINESS_PLAN.md` | BP v4.3 — baseline marzo; struttura partner superseded 2026-08-29; non governa prodotto o scheduling | Numeri e assunzioni storiche pre-validazione |
| `FINANCIAL_MODEL.md` | Modello analitico marzo; formule partner e viste founder+partner superseded; da sostituire col reset commerciale | Proiezioni storiche pre-validazione |
| `LEGAL_REGULATORY_REPORT.md` | Report legale-regolamentare v1.4: GDPR, fiscale, IP, EAA, SBOM, PSD2, exit partner | Compliance |
| `PRODUCT_MARKETING_CONTEXT.md` | 🟢 **SSoT verità commerciale (A0, 2026-09-03):** ICP, posizionamento, claims matrix 🟢/🟡/🔴, obiezioni, canali ORB, vincoli. Solo le righe 🟢 sono claim esterni autorizzati | Claim commerciali |
| `LEGGI_COMPETITOR.md` | Conoscenza competitor VIVA estratta dagli archivi (A0): leggi W1-W11 + L1-L6 + lacune N-1..N-8 (guardrail: niente assoluti «nessun competitor italiano» finché N-1 aperta) | Mercato e benchmark |
| `kit/ONE_PAGER_DESIGN_PARTNER.html` | **Kit design partner, pezzo 1:** one-pager A4 print-ready (Chrome → Salva come PDF). Solo righe 🟢 della claims matrix, zero prezzi, identità visiva MANIFESTO. Ogni claim nuovo passa PRIMA dalla matrix | Materiale di partenza |
| `kit/DEMO_SCRIPT.md` + `DEMO_DATASET.md` + `DEMO_CHECKLIST.md` | **Kit pezzo 2 (DP.1, bozza):** copione demo 15' (8 beat mappati sulle card del one-pager), specifica dataset sintetico (6 personaggi-segnale, date relative, tel=founder), checklist pre-demo + piani B. ⏸️ DP.2 seeder via API e DP.3 collaudo CONGELATI fino a checkpoint S1/G1 | Demo founder-led |

**Gerarchia:** `SPEC_PRE_POC.md` governa il lavoro corrente; `SPEC_EXIT_ALESSIO.md` governa il blocco
di uscita partner. BP/FM conservano assunzioni e numeri pre-validazione, ora superseded per la
struttura partner; Legal governa il proprio dominio. Strategie, roadmap e materiali partner
superseded vivono in `docs/archive/` e non sono contesto operativo.

**Contratto di specie (G-DOC.3, 2026-09-02):** `docs/business/` è la casa del dominio COMMERCIALE.
Tre specie ammesse: **(a) verità commerciale CORRENTE** — depositata con A0 (2026-09-03):
`PRODUCT_MARKETING_CONTEXT.md` (context + claims matrix) e `LEGGI_COMPETITOR.md` (estrazione viva
dagli archivi); il kit design partner nasce qui; **(b) baseline storiche ANNOTATE** (BP/FM con
delta di verità in header); **(c) compliance** (Legal). Le fotografie superseded →
`docs/archive/business/`. **Nessun claim esterno nasce fuori da questa casa.**

---

## product/ — Roadmap, feature future, video

| File | Scopo |
|------|-------|
| `CATALOGO_SCENARI_PT.md` | **Fondamento product ADR-025 (vivo):** 96 scenari quotidiani reali del PT/chinesiologo (6 lenti + critic), copertura mappata sul modello attuale (15% piena · 51% parziale · 34% assente), 23 domande aperte per l'ADR. Base di conoscenza del futuro agente `pt-reality-auditor`. Gemello: `archive/RICERCA_COMPETITOR_WALLET_SEDUTE_SINGOLE_2026-07-07.md` (leggi W1-W11) |
| `POST_LAUNCH_ISSUES.md` | Issue aperte post-lancio |
| `FITSCAN_ARCHITECTURE.md` | Spec tecnica FitScan (pre-implementazione, roadmap ADR-010): DB schema, Biomechanical Engine, Pose Provider |
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
| `SECURITY_MODEL.md` | **Reference unico sicurezza (vivo):** threat model + tassonomia attaccanti L0-L4, 6 livelli protezione (L1-L6 + L3b), hardware binding Windows/macOS con primitive raw confinate, network hardening, roadmap (cifratura crm.db = gate Tier-1 attivo G1). Gli audit storici e la strategia anti-RE sono in `docs/archive/` |
| `LICENSE_ACTIVATION.md` | Attivazione licenza e hardware binding Windows/macOS; fingerprint completo confinato al canale amministrativo |
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
| `SPEC_PRE_POC.md` | 🟡 **IN CORSO — D0+C0.0+G-MAC.1+C0.1 GREEN+FT.0+E0+D11+A0+S1.0+S1.1 CHIUSI; PROSSIMO FOUNDER E1; PROSSIMO TECNICO S1.2; C0.2/G-MAC.2–5 HOLD** | Unica regia pre-POC: v1.0.15 Windows security/readiness, portability hedge pre-S1 chiuso, Financial Truth e percorso founder-led; prima POC Windows, distribuzione Mac pull-based dopo trigger diretto |
| `SPEC_S1_G1_G5_CIFRATURA_CRM.md` | 🟡 **APERTA E RATIFICATA — S1.0 CHIUSO; S1.1 GREEN `efda1fe`; PROSSIMO S1.2** | Contratto esecutivo G1+G5: owner unico, SQLCipher password-bound, envelope DEK–KEK, engine late-bound, recovery, migrazione atomica e backup/restore cifrati |
| `SPEC_EXIT_ALESSIO.md` | 🟡 **E0 STRATEGIA RATIFICATA; E1 TESTO DA COSTRUIRE; E2–E4 NON ESEGUITI** | Exit commerciale/contrattuale/operativa: comunicazione separata, verifica NDA, export/no-data, licenza/tunnel, fold-back e reset commerciale; nessuna revoca implicita |
| `SPEC_G8.4_TRASPARENZA_FINANZIARIA_FE.md` | 🟡 **G8.4 ORIGINALE CHIUSO · FT.0 ✅ · FT.1–FT.5 APERTI** | Casa tecnica Financial Truth: FT.1 grafico cash-direction; FT.2 trend/empty/conguagli; FT.3 audit flow; FT.4 cache symmetry; FT.5 bonifica legacy per-record. F0 HOLD su FT.1–FT.4; Real-data GO del DB interessato HOLD su FT.5. G8.5 goodwill resta separato |
| `SPEC_G-MAC_CONSEGNA_MACOS.md` | 🟡 **C0.0+G-MAC.1+C0.1 GREEN CHIUSI; C0.2/G-MAC.2–5 HOLD** | Run `33772591605`: build `macos-15` e smoke stesso artefatto `macos-26` success, zero finding; target exact e distribuzione Mac soltanto dopo R1-WIN e trigger D11 |

### specs/hold/ — Spec CONGELATE (posizione=stato anche per il freeze)

Vive ma non nel fronte di lavoro: riaprono SOLO col trigger dichiarato nel loro Stato.

| File | Trigger di riapertura |
|------|----------------------|
| `SPEC_FRONTEND_CORE_INTUITIVITA.md` | Finding osservato da rehearsal/pilota (D7); FE-2..4 |
| `SPEC_P_PRESTAZIONI_SINGOLE_E_PORTAFOGLIO.md` | Evidenze Wave 0 + nuovo GO founder (D6); P1–P6 |
| `SPEC_VOCABOLARIO_E_CLASSIFICAZIONE_CONTRATTI.md` | Giro 2 (rinnovi-incassi + workspace_engine off-SSoT + grep-guard); fuori scope v1.0.15 |
| `SPEC_COLLABORAZIONE_CLAUDE_CODEX.md` | GO founder su A2+ (smoke Claude A1.1 da recuperare prima) |

Archiviate 2026-09-02 (G-DOC.2) con consuntivo: `SPEC_G9` (resta solo G9.6 differito, prescritto
nella spec archiviata), `SPEC_G9.7` (runbook orfani → `operations/RUNBOOK_RECUPERO_ORFANI.md`),
`SPEC_FINGERPRINT` (T2/binding = gate C0.2/G-MAC.4 di SPEC_G-MAC).

**Backlog (non-spec, censito qui):** G8.2 wallet auto-cross-contratto (in panchina, D2 aperta) + Q9
conversione singole→pacchetto (casa: G8.2+G8.5, P-D6 blocco P) · wallet
sotto-ledger append-only + forecast ponderato insolvenza (ROADMAP archiviata §1.1/§1.4, post-lancio) ·
punto tributarista: policy `pro_sedute` + penale nel recesso (PROVISIONAL) · FDM/TASSONOMIA asse 6-stati.

**Backlog post-v1.0.15 da aprire con SPEC dedicata, non autorizzato ora:** bonifica obsolescenza
(cluster FE morti; soli rami workspace list/detail orfani; wire/query/pin non consumati; triage dei
34 sorgenti `crm_dev`; decisione su mount Nutrition/Training e dismissione completa Tailscale Fase 3).

---

## operations/ — Procedure, release, supporto

| File | Scopo |
|------|-------|
| `AI_ASSISTED_DEVELOPMENT_WORKFLOW.md` | Runbook agent-neutral Claude Code + Codex: bootstrap, routing del contesto, metodo docs-first proporzionale, Protocollo Senior, checkpoint Git obbligatorio, Contract Smoke read-only e stop conditions. Deriva da `AGENTS.md`, non modifica la coda prodotto |
| `RELEASE_CHECKLIST.md` | Checklist release: preflight, build, verify, seal |
| `RUNTIME_DIAGNOSTICS_PLAYBOOK.md` | Diagnostica runtime: log, errori, recovery |
| `SUPPORT_RUNBOOK.md` | Runbook supporto: licenza, backup, restore, troubleshoot |
| `RUNBOOK_REMEDIATION_CONTRATTI_MUTI.md` | **G7.6** — bonifica contratti chiusi legacy (`motivo_chiusura=NULL`): diagnostica data-driven, albero decisionale per profilo (LEAVE/reopen/terminate), per-contratto, reversibile, mai bulk. Esecuzione trainer-driven via endpoint G7.3/G7.4 |
| `RUNBOOK_RECUPERO_ORFANI.md` | 🟡 **PENDENTE** — recupero orfani reali 640/641/643 + 647/649 (da SPEC_G9.7 archiviata), trainer-driven via endpoint auditati, mai a mano nel DB |
| `UPGRADE_PROCEDURE.md` | Procedura upgrade: in-place, fallback, checklist |
| `DEPLOYMENTS.md` | Registro consegne: chi ha quale versione, SHA-256, licenza |
| `AUDIT_DEEPLINK_CROSS_PAGE_2026-07-24.md` | 🟡 Unica fotografia con remediation APERTA (fasce A/B/C, coordinata col blocco P in HOLD); a fold-back avvenuto → `archive/operations/` |

Le fotografie audit foldate (11 file, 2026-06 → 2026-07) sono in `docs/archive/operations/` con
header di esito: gli esiti vivono negli ADR-016→024 e nei gate chiusi, mai nella fotografia.

---

## adr/ — Architecture Decision Records

24 ADR accettati (ADR-001 → ADR-026; ADR-002 rimossa come obsoleta, ADR-012 riservato). Ultimi:
**ADR-026 + Addendum I/II** (macOS ARM64: build evidence separata dalla compatibilità target; C0.1
GREEN protegge G1 e apre S1; C0.2/distribuzione pull-based dopo R1-WIN e trigger diretto, con release
Mac distinta) · **ADR-013 + Addendum I** (G1/G5: owner unico compiled; engine candidato pubblicato
solo dopo unwrap + verifica bcrypt/account; nessun downgrade plaintext) · **ADR-025** (prestazione singola + Portafoglio cliente: fatto economico proprio, insoluto derivato
fail-loud, compensazione wallet come atto esplicito; blocco P) · **ADR-024** (semantica per-classe:
matrice assi×regole, fail-loud, perimetro transizioni, birth-auditor; G9.7) · **ADR-023**
(temporal fence: storia contabilizzata immutabile, varco unico `reopen`; G7.8-ter) · **ADR-022**
(financial command layer: penna unica, transition executor, invarianti imposti, read-model cassa,
rettifiche e Hypothesis; G9). ADR-019/020 restano la base del mastro non-distruttivo e del wallet;
Addendum recenti: ADR-011 Add. I (ACME HTTP-01 ristretto via FRP), ADR-017 Add. I
(stati-penale) e ADR-022 Add. I/II (rettifiche + read-model).
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
| `INC-2026-08-05-grafico-cassa-netting-rimborsi.md` | P1 rappresentazione finanziaria: il 24/07 inflow 333,25 € + rimborsi 537,50 € diventavano nel grafico Entrate 0 + Uscite 204,25 €. Ledger/saldo corretti; remediation FT.1–FT.5 aperta |

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
| `archive/specs/` | Spec storiche frozen (non modificare, **mai contesto di lavoro**): UPG storici + spec implementate. Chiusura 2026-07-28: SPEC_R0_PROTEZIONE_RELEASE_V1_0_15. Batch 2026-07-03 (riordino): SPEC_G7.0, SPEC_G7.3, SPEC_REVISIONE_PRE_G7, SPEC_RINVIO (G7.8, superata da G7.8-bis), SPEC_TERMINAZIONE_BILATERALE (G7.9/10), SPEC_INTEGRITA (G8.1-G8.3), SPEC_LATE_CANCEL (G7.8-bis), IMPL_PLAN_FINANCIAL_REALIGN; 2026-07-04: SPEC_TEMPORAL_FENCE (G7.8-ter, ADR-023). Batch precedenti: SPEC_RINNOVO/TEMPORALE/RINNOVI_SCADUTI + IMPL_PLAN (06-23), G7.7_R5 + RETRODATAZIONE (06-27) |
| `archive/` (root) | Snapshot storici: audit sicurezza pre/post-hardening, strategia anti-RE, pre-delivery audit 04-17, session handoff, DUAL_ENV, Tailscale + AUDIT_PRE_G7.3, AUDIT_POSIZIONE_FINANZIARIA, ROADMAP_FINANCIAL_UPGRADES e AUDIT_OBSOLESCENZA_POST_MIGRAZIONI (foldato nella SPEC R0 archiviata) |
| `archive/nutrition-v2-strategy.md` | Strategia nutrition v2 (obsoleta, 226 alimenti → ora 880) |
| `archive/operations/` | Fotografie audit foldate (11 file, spostate 2026-09-02) + eventuali future; esiti negli ADR e nei gate |
| `archive/upgrades/` | 🗄️ Dismesso 2026-07-03 (assorbito da `learning/BUILD_LOG.md`), spostato in archivio 2026-09-02 — storico UPG |
| `videos/` | Script video-pillole |
