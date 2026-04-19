# docs/ — Indice documentazione

Ogni documento ha un dominio. Se non sai dove cercare, parti dalla directory del dominio.

---

## business/ — Strategia, numeri, partner, legal

| File | Scopo | SSoT per |
|------|-------|----------|
| `BUSINESS_PLAN.md` | BP v4.3 — strategia, mercato, team, pricing, POC, community | Numeri, pricing, modello |
| `STRATEGY_PLAN.md` | Piano operativo lancio, category creation PT Evoluto, ruolo partner | Go-to-market |
| `FINANCIAL_MODEL.md` | Modello analitico — ogni euro tracciabile, formule, 3 scenari, NASpI (§8), fondi (§9) | Proiezioni finanziarie |
| `DOCUMENTO_OPERATIVO_PARTNER.md` | Accordo partner: compenso, equity, milestone, obblighi | Termini partnership |
| `LEGAL_REGULATORY_REPORT.md` | Normativa, certificazioni, privacy, requisiti legali | Compliance |
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
| `TAILSCALE_FUNNEL_SETUP.md` | Setup Tailscale Funnel, proxy, troubleshooting |
| `DEPLOYMENT_PLAN.md` | Piano deploy: PyInstaller/Nuitka, standalone, Inno Setup |
| `NUTRITION_ENGINE_V3.md` | Architettura Nutrition Engine v3 |
| `PRE_DELIVERY_AUDIT_2026_04_17.md` | Audit tecnico 360° pre-consegna ad Alessio (2026-04-17) |
| `nutrition-v2-strategy.md` | Strategia migrazione nutrition v2 (storico) |

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

9 ADR attivi. Indice in `adr/README.md`.

## incidents/ — Post-mortem

| File | Scopo |
|------|-------|
| `INC-2026-03-28-safety-engine-blind-spot.md` | P0: Safety Engine blind spot durante demo investitore |
| `INC-2026-03-29-portal-url-origin-mismatch.md` | P1: Link portale clienti inaccessibili — URL hardcoded da PUBLIC_BASE_URL invece di browser origin |
| `INC-2026-03-30-portal-mobile-invisible-ui.md` | P1: Portale workout invisibile su mobile — CSS variables dark mode + rate limiter bloccante |
| `INC-2026-04-19-catalog-taxonomy-empty.md` | P0: catalog.db tassonomia vuota dopo consegna v1.0.7 — Safety Engine cieco, 6 tabelle vuote, gap pipeline seed/build |

## Altre directory

| Directory | Contenuto |
|-----------|-----------|
| `archive/specs/` | 100+ spec storiche (frozen, non modificare) |
| `upgrades/` | Spec upgrade attive |
| `videos/` | Script video-pillole |
