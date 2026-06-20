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

## security/ — Strategia anti-reverse engineering

| File | Scopo |
|------|-------|
| `ANTI_REVERSE_ENGINEERING_STRATEGY.md` | Strategia anti-RE v2.0: 4 step, 6 anelli, threat model, TTC, checklist (implementato) |

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
| `SECURITY_MODEL.md` | Threat model, 6 livelli protezione (L1-L6 + L3b), network hardening pre-Funnel, roadmap sicurezza |
| `SECURITY_AUDIT_BASELINE.md` | Red Team audit pre-hardening (7 test, TTC per Crown Jewel) |
| `SECURITY_AUDIT_POST_HARDENING.md` | Re-test post-hardening (4 step anti-RE, confronto pre/post) |
| `LICENSE_ACTIVATION.md` | Attivazione licenza, hardware binding, CLI admin |
| `TUNNEL_ARCHITECTURE.md` | **Sottosistema tunnel (riferimento unico):** design (problema, P1-P10, P2 data-blind), build (migrazione Tailscale→FRP, 4 fasi, gap analysis), operations (setup VPS edge, costi, DR). Consolida i 4 doc storici. |
| `TUNNEL_SECURITY_BOUNDARY.md` | **Confine di sicurezza + piano "Strada B":** acceptance criteria (confine JWT, rate limiter, apertura selettiva), piano implementazione (lockout, role JWT, guard, test e2e). Stato: approvato, non ancora implementato. |
| `DEPLOYMENT_PLAN.md` | Piano deploy: PyInstaller/Nuitka, standalone, Inno Setup |
| `NUTRITION_ENGINE_V3.md` | Architettura Nutrition Engine v3 |
| `PRE_DELIVERY_AUDIT_2026_04_17.md` | Audit tecnico 360° pre-consegna ad Alessio (2026-04-17) |
| `PRE_DELIVERY_SECURITY_GATE.md` | Gate di sicurezza pre-consegna: 12 voci in 3 tier (G1-G12), stato annotato contro il codice reale |
| `TASSONOMIA_FINANZIARIA.md` | **Vocabolario finanziario condiviso (vincolante su concetti e formule):** 3 assi (liquidità reale/cassa, posizione commerciale/competenza, stato di pianificazione), esclusioni dalla cassa, riconciliazione. Referenziato dalle 2 spec finanziarie |
| `SPEC_RINNOVO_E_CONTRATTI_DA_PIANIFICARE.md` | Spec: flusso di rinnovo (eredità dati + percorso guidato al piano rate) + vista Contract-first "contratti da pianificare" (denaro dovuto oggi invisibile all'aging) |
| `SPEC_GESTIONE_FINANZIARIA_TEMPORALE.md` | Spec: asse temporale della finanza — aggregazione per periodo (cassa), trend + competenza affiancata, composizione (nuovi/rinnovi, acconti/rate) |
| `IMPL_PLAN_SPEC_RINNOVO.md` | Piano d'implementazione di SPEC_RINNOVO (ancorato al codice, decisioni bloccate, sequenza step). Materiale di lavoro — superato dal codice a implementazione conclusa |
| `IMPL_PLAN_SPEC_TEMPORALE.md` | Piano d'implementazione di SPEC_GESTIONE_FINANZIARIA_TEMPORALE (tab Andamento in /cassa, L1 periodo+altri incassi, L2 trend+competenza, L3 composizione, fix monthly_revenue). Materiale di lavoro |
| `SPEC_RINNOVI_SCADUTI_E_RETENTION.md` | Spec (v1.1, client-aware): i clienti lapsed non spariscono — vista "clienti da recuperare" (cliente senza contratti attivi) + esito "non rinnova"+motivo; anti-perdita silenziosa. ADR-015 |
| `IMPL_PLAN_RINNOVI_SCADUTI.md` | Piano: stato `esito_rinnovo_*`, endpoint `clients-to-recover` (scaduti EXCEPT attivi), azione renewal-outcome, alert + sezione UI in /rinnovi-incassi (conteggio clienti). Materiale di lavoro |

---

## operations/ — Procedure, release, supporto

| File | Scopo |
|------|-------|
| `RELEASE_CHECKLIST.md` | Checklist release: preflight, build, verify, seal |
| `RUNTIME_DIAGNOSTICS_PLAYBOOK.md` | Diagnostica runtime: log, errori, recovery |
| `SUPPORT_RUNBOOK.md` | Runbook supporto: licenza, backup, restore, troubleshoot |
| `UPGRADE_PROCEDURE.md` | Procedura upgrade: in-place, fallback, checklist |
| `DEPLOYMENTS.md` | Registro consegne: chi ha quale versione, SHA-256, licenza |

---

## adr/ — Architecture Decision Records

13 ADR attivi (ADR-001 → ADR-015; ADR-002 rimossa come obsoleta, ADR-012 riservato). Ultimo: ADR-015 (funnel Rinnovi & Retention — nessuna perdita silenziosa di contratti scaduti, accettata 2026-06-20). Indice in `adr/README.md`.

## incidents/ — Post-mortem

| File | Scopo |
|------|-------|
| `INC-2026-03-28-safety-engine-blind-spot.md` | P0: Safety Engine blind spot durante demo investitore |
| `INC-2026-03-29-portal-url-origin-mismatch.md` | P1: Link portale clienti inaccessibili — URL hardcoded da PUBLIC_BASE_URL invece di browser origin |
| `INC-2026-03-30-portal-mobile-invisible-ui.md` | P1: Portale workout invisibile su mobile — CSS variables dark mode + rate limiter bloccante |
| `INC-2026-04-19-catalog-taxonomy-empty.md` | P0: catalog.db tassonomia vuota dopo consegna v1.0.7 — Safety Engine cieco, 6 tabelle vuote, gap pipeline seed/build |
| `INC-2026-06-08-kpi-fatturato-contratti-chiusi.md` | P1: KPI fatturato/incassato escludevano i contratti chiusi — metriche storiche errate (v1.0.9) |
| `INC-2026-06-15-installer-frpc-lock.md` | P2: upgrade installer bloccato (codice 5) da `frpc.exe` orfano — Job Object kill-on-close + installer chiude i processi (v1.0.12) |

## learning/ — Diario di apprendimento personale

Formazione del founder-developer in parallelo allo sviluppo. Concetti tecnici studiati, diario cronologico, metodo di studio.

**NON vincolante per il codice** — materiale didattico personale, ignorato durante l'implementazione. Dettagli in `learning/README.md`.

| File | Ambito |
|------|--------|
| `LEARNING_METHOD.md` | Metodo di studio: 4 principi, flusso cattura/elaborazione, ponte con Claude Code |
| `BUILD_LOG.md` | Diario cronologico: cosa ho fatto e quando (Fase 0 tunnel in corso) |
| `LEARNING_LINUX_SYSADMIN.md` | Concetti: crittografia asimmetrica, chiavi SSH, passphrase |
| `LEARNING_APP_ARCHITECTURE.md` | Dominio nel codebase: rinnovo sequenziale, semantica date, convenzioni CRM |

---

## Altre directory

| Directory | Contenuto |
|-----------|-----------|
| `archive/specs/` | 100+ spec storiche (frozen, non modificare) |
| `archive/nutrition-v2-strategy.md` | Strategia nutrition v2 (obsoleta, 226 alimenti → ora 880) |
| `upgrades/` | Spec upgrade attive |
| `videos/` | Script video-pillole |
