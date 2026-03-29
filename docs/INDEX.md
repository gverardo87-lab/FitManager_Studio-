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

**Gerarchia**: BP e' la fonte di verita' strategica. SP operativizza il BP. FM quantifica il BP. Partner Doc e Legal sono satelliti.

---

## product/ — Roadmap, feature future, video

| File | Scopo |
|------|-------|
| `POST_LAUNCH_ROADMAP_90D.md` | Roadmap 90 giorni: PWA, mobile, Box, science nudges, GTM |
| `POST_LAUNCH_ISSUES.md` | Issue aperte post-lancio |
| `FITSCAN_ARCHITECTURE.md` | Spec tecnica FitScan: DB schema, Biomechanical Engine, Pose Provider |
| `VIDEO_GUIDE_STRATEGY.md` | Sistema video-guide contestuali: 4 livelli, mapping pagine |
| `VIDEO_PRODUCTION.md` | Pipeline video: manifest SSoT, flusso continuo, selettori |

---

## technical/ — Architettura, sicurezza, infrastruttura

| File | Scopo |
|------|-------|
| `SECURITY_MODEL.md` | Threat model, 5 livelli protezione, roadmap sicurezza |
| `LICENSE_ACTIVATION.md` | Attivazione licenza, hardware binding, CLI admin |
| `TAILSCALE_FUNNEL_SETUP.md` | Setup Tailscale Funnel, proxy, troubleshooting |
| `DEPLOYMENT_PLAN.md` | Piano deploy: PyInstaller, standalone, Inno Setup |
| `NUTRITION_ENGINE_V3.md` | Architettura Nutrition Engine v3 |
| `nutrition-v2-strategy.md` | Strategia migrazione nutrition v2 (storico) |

---

## operations/ — Procedure, release, supporto

| File | Scopo |
|------|-------|
| `RELEASE_CHECKLIST.md` | Checklist release: preflight, build, verify, seal |
| `RUNTIME_DIAGNOSTICS_PLAYBOOK.md` | Diagnostica runtime: log, errori, recovery |
| `SUPPORT_RUNBOOK.md` | Runbook supporto: licenza, backup, restore, troubleshoot |
| `UPGRADE_PROCEDURE.md` | Procedura upgrade: in-place, fallback, checklist |

---

## adr/ — Architecture Decision Records

9 ADR attivi. Indice in `adr/README.md`.

## incidents/ — Post-mortem

| File | Scopo |
|------|-------|
| `INC-2026-03-28-safety-engine-blind-spot.md` | P0: Safety Engine blind spot durante demo investitore |

## Altre directory

| Directory | Contenuto |
|-----------|-----------|
| `archive/specs/` | 100+ spec storiche (frozen, non modificare) |
| `upgrades/` | Spec upgrade attive |
| `videos/` | Script video-pillole |
