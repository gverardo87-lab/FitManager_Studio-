# Changelog

Tutte le modifiche rilevanti al progetto FitManager AI Studio sono documentate in questo file.

Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.1.0/)
e il progetto aderisce a [Semantic Versioning](https://semver.org/lang/it/).

<!-- TEMPLATE per nuove release (copiare e compilare):

## [X.Y.Z] — YYYY-MM-DD

### Aggiunto
### Modificato
### Corretto
### Sicurezza

### Upgrade (da vA.B.C)
- **DB**: schema_sync aggiunge automaticamente N colonne / nessuna migrazione
- **Backup**: automatico al primo avvio
- **Azioni manuali**: nessuna / descrivere
- **Breaking**: nessuno / descrivere
- **Licenza**: compatibile / richiede rinnovo
-->

## [1.0.13] — 2026-06-18

### Corretto
- Fingerprint hardware parziale bloccava l'accesso al CRM in modo intermittente (INC-2026-06-18): una query WMI vuota a intermittenza (sistema sotto carico, antivirus, risveglio da sleep) produceva un fingerprint diverso dal `machine_id` firmato → falso "wrong_machine" → richiesta ripetuta della `license.key`. Fix: mai hash su set parziale (`unavailable` fail-closed), cache solo del fingerprint completo 3/3 (auto-heal alla richiesta successiva), retry sui vuoti transitori. L'hash 3/3 resta invariato → licenze esistenti valide.

### Modificato
- Build backend Nuitka via MSVC (Visual Studio) invece di MinGW64 (gcc winlibs corrente incompatibile con Nuitka)

### Upgrade (da v1.0.12)
- **DB**: nessuna migrazione (schema_sync invariato)
- **Backup**: automatico al primo avvio
- **Azioni manuali**: nessuna
- **Breaking**: nessuno
- **Licenza**: compatibile — il fingerprint 3/3 è invariato, le licenze già firmate restano valide

> Nota: le release 1.0.9–1.0.12 non hanno una sezione dedicata in questo file (debito changelog pregresso). Storico tecnico completo in `docs/learning/BUILD_LOG.md` e `docs/operations/DEPLOYMENTS.md`.

## [1.0.8] — 2026-04-19

### Aggiunto
- Deployment registry (`docs/operations/DEPLOYMENTS.md`) per tracciamento consegne
- Rate limiter riusabile per endpoint auth (5 req/min, 20 req/h) e portale (30 req/min, 120 req/h)
- Security headers: HSTS, Referrer-Policy, Permissions-Policy, X-Content-Type-Options, X-Frame-Options
- CORS esteso a HTTPS per Tailscale Funnel
- Version masking in `/health` in compiled mode

### Modificato
- Backend bind su `127.0.0.1` in produzione (non più `0.0.0.0`)
- Reset password ora richiede `current_password` (cambio password con verifica, non reset cieco)
- Registrazione: errore generico 400 per prevenire email enumeration

### Corretto
- catalog.db consegnato con 6 tabelle tassonomiche vuote (INC-2026-04-19) — seed strutturale aggiunto
- Smoke test falliva per version masking in compiled mode

### Sicurezza
- Swagger/Redoc/OpenAPI disabilitati in compiled mode
- 9 interventi pre-Funnel network hardening (P0/P1/P2)

### Upgrade (da v1.0.7)
- **DB**: schema_sync automatico, nessuna migrazione manuale
- **Backup**: automatico al primo avvio
- **Azioni manuali**: reinstallare da nuovo installer (sovrascrive exe + frontend + catalog.db)
- **Breaking**: nessuno
- **Licenza**: compatibile (non richiede rinnovo)

## [1.0.7] — 2026-04-19

### Aggiunto
- Trasparenza motore scientifico: 6 sezioni "Perche' questo piano?" (reasoning, copertura, equilibrio, recupero, safety, azioni)
- Documentazione certificabile per 3 motori scientifici (Training Science, Safety Engine, Nutrition Science)
- Parameter Registry (~850 parametri documentati su ~13.500 LOC)
- Anti-reverse engineering 4 step (ADR-007): bundle sanitization, DB encryption AES-256-GCM, Nuitka native compilation
- Red Team audit baseline + post-hardening audit

### Modificato
- Rimozione modulo nutrizione dal frontend (scelta di posizionamento prodotto — backend preservato)
- 34 esercizi soft-deleted dopo audit classificazione catalogo
- Aderenza: completamento trainer con dati effettivi + fix ripianificazione duplicati

### Corretto
- Training Science Engine: 6 fix EMG + balance ratios + pattern isolation
- Seed metriche in catalog.db — BodyReportMap invisibile
- Build-media: query diretta su esercizi (non relazioni), count 466 attivi
- Build scripts: usano venv python (cryptography disponibile)
- Encrypted DB: fallback a temp file quando `deserialize` non disponibile
- Tailscale Funnel dev stability: mock WebSocket HMR + local fonts

### Primo deployment
- v1.0.7 consegnata ad Alessio Crociani (primo partner, tier PRO)

### Upgrade (da v1.0.6)
- **DB**: schema_sync automatico, nessuna migrazione manuale
- **Backup**: automatico al primo avvio
- **Azioni manuali**: nessuna (prima installazione per tutti i deployment)
- **Breaking**: UI nutrizione rimossa (backend preservato)
- **Licenza**: prima attivazione (non applicabile upgrade)

## [1.0.6] — 2026-03-30

### Corretto
- Portale workout mobile: colori espliciti (no CSS variables tema), rate limiter sizing (INC-2026-03-30)
- Media URL relative + `allowedDevOrigins` per Tailscale Funnel
- Test `workspace_today` reso time-insensitive con `reference_dt` relativo

## [1.0.5] — 2026-03-24

### Aggiunto
- License hardening anti-tampering (ADR-005): chiave RSA embedded, env bypass bloccato, fingerprint fail-closed
- Security model documentato (6 livelli protezione L1-L6)
- Identity fields nella licenza JWT (nome, cognome, data nascita, email)
- Stale cookie cleanup su fresh install (AuthGuard + login + setup)
- Video guide: infrastruttura 10 pillole (VideoGuideCard, VideoGuidePopover, VideoGuideInline)
- Pipeline produzione video con ElevenLabs (Daniel voice + acoustic calm)

### Corretto
- Clinical readiness test reso date-insensitive

## [1.0.4] — 2026-03-22

### Aggiunto
- Release pipeline sicuro 5 fasi (ADR-004): preflight, build, verify, seal, tag
- Version SSoT in `api/__init__.py` con sync check frontend/backend
- Smoke test su porta effimera 9999 con 5 health invariants
- Manifest.json con SHA-256 su ogni release

### Corretto
- 3 test fragili stabilizzati
- Purge WAL stale su cataloghi read-only al startup
- ISCC escape per Git Bash MSYS path conversion
- Nomi tabelle nutrition.db nei safety gate

## [1.0.3] — 2026-03-21

### Corretto
- 4 bug nel build pipeline (installer, media staging, safety gates)

## [1.0.2] — 2026-03-11

### Aggiunto
- Setup wizard connettivita' guidato (Tailscale Funnel)
- Portale anamnesi: validazione link pubblici
- Pagina "Oggi" Mission Control: hero briefing, pre-flight engine, cockpit 2 colonne
- Rinnovi & Incassi: sistema rinnovo con FK chain e azioni inline
- Contract renewal system con pre-fill
- Password reset dialog
- Sidebar tooltips su tutti gli item navigazione
- Runtime diagnostics playbook
- Support recovery runbook
- Upgrade procedure guide
- Competitive analysis

### Modificato
- Workout builder: upgrade visuale con MUSCLE_COLORS map
- UX audit sistematico: hover feedback, mobile scroll, CTA specificity

### Corretto
- SSR hydration mismatch in AuthGuard, CommandPalette, ReactQueryDevtools
- Nested button hydration error in TrainingPlanRow

## [1.0.1] — 2026-03-10

### Aggiunto
- Installation health surface + ops plan
- Support snapshot diagnostics
- Next.js middleware migrato a proxy pattern
- Release preflight pipeline

## [1.0.0-rc1] — 2026-03-10

### Release candidata
Prima release candidata con feature set completo:

- **CRM completo**: Clienti, Contratti, Rate, Agenda, Cassa, Monitoraggio
- **Workout Builder**: 3-tab, drag-and-drop, blocchi, export PDF
- **500 esercizi** con tassonomia scientifica (muscoli, articolazioni, condizioni)
- **Training Science Engine**: periodizzazione, EMG, volume MEV/MAV/MRV (~3500 LOC)
- **Safety Engine**: 47 condizioni, 80 pattern rules
- **Portale Anamnesi Self-Service**: share token + kiosk mobile
- **Dashboard reminder-first**: hero actions, clinical readiness, timeline
- **Client Avatar**: 6 dimensioni, semaforo, readiness_score
- **Command Palette** (Ctrl+K): fuzzy search, preview panel
- **SpotlightTour**: 19 passi cross-page + hub /guida
- **Login JWT** con multi-tenant safety (trainer_id isolation)
- **3 database separati**: crm.db (business) + catalog.db (esercizi) + nutrition.db (alimenti)
- **361+ test backend** + 69 vitest frontend

[1.0.8]: https://github.com/gverardo87-lab/FitManager_Studio-/compare/v1.0.7...v1.0.8
[1.0.7]: https://github.com/gverardo87-lab/FitManager_Studio-/compare/v1.0.6...v1.0.7
[1.0.6]: https://github.com/gverardo87-lab/FitManager_Studio-/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/gverardo87-lab/FitManager_Studio-/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/gverardo87-lab/FitManager_Studio-/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/gverardo87-lab/FitManager_Studio-/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/gverardo87-lab/FitManager_Studio-/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/gverardo87-lab/FitManager_Studio-/compare/v1.0.0-rc1...v1.0.1
[1.0.0-rc1]: https://github.com/gverardo87-lab/FitManager_Studio-/releases/tag/v1.0.0-rc1
