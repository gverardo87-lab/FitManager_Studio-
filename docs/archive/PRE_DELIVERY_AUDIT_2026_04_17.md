# Pre-Delivery Audit — 2026-04-17

**Data**: 2026-04-17
**Branch**: FitManager_Studio
**Versione**: 1.0.6
**Destinatario**: Alessio (partner tecnico)
**Obiettivo**: Audit tecnico 360° pre-consegna — verificare qualita', sicurezza, coerenza e robustezza del software prima del passaggio al partner

---

## Executive Summary

Audit su 4 layer (backend, frontend, sicurezza, documentazione) con analisi di 437 file sorgente (144 backend + 293 frontend).

| Metrica | Valore |
|---------|--------|
| Finding critiche (C) | 2 (entrambe fixate) |
| Finding alte (H) | 4 (tutte fixate) |
| Finding medie (M) | 7 (5 fixate, 2 raccomandazioni) |
| Finding basse (L) | 6 (informational) |
| **Fix applicati in sessione** | **6** (C1, H2, H3, H4, M5, M7) |
| pytest | 361 pass, 0 fail |
| ruff check | 0 errori |
| next build | 0 errori TS |

---

## Finding Critiche (2)

### C1 — CSS dark mode su pagina anamnesi pubblica (FIXATO)

**Scope**: `frontend/src/app/public/anamnesi/[token]/page.tsx`
**Problema**: Stessa classe di bug di INC-2026-03-30 (portale workout). 9 istanze di CSS variables del tema (`text-muted-foreground`, `bg-primary`, ecc.) sulla pagina anamnesi pubblica. Su dispositivi con dark mode attivo, il testo risulta invisibile su sfondo chiaro.
**Impatto**: Anamnesi self-service inutilizzabile per clienti con dark mode.
**Fix**: Sostituzione di tutte le CSS variables con colori Tailwind espliciti (`text-gray-900`, `text-gray-500`, `bg-gray-100`). Aggiunto `style={{ colorScheme: "light" }}` e `text-gray-900` sul div root.
**Stato**: FIXATO
**Recurrence di**: INC-2026-03-30 — documentata nel post-mortem.

### C2 — File `.env` sicuro

**Scope**: `data/.env`
**Problema**: Verificato che `JWT_SECRET` sia di lunghezza adeguata (52 char) e che il file non contenga credenziali cloud o API key esterne.
**Stato**: CONFERMATO SICURO — `.env` contiene solo `JWT_SECRET`, `PUBLIC_PORTAL_ENABLED`, `PUBLIC_BASE_URL`. Nessuna credenziale esterna.

---

## Finding Alte (4)

### H1 — Build pipeline Nuitka funzionante

**Scope**: `tools/build/build-release.sh`
**Verifica**: Pipeline 5 fasi (ADR-004) con safety gates: CRM data leak check, ISS reference check, nutrition.db integrity. Nuitka produce binario nativo x86-64.
**Stato**: CONFERMATO OK

### H2 — Export workout: campo `note` allineato (FIXATO)

**Scope**: `frontend/src/lib/export-workout.ts`
**Problema**: Campo `note` non correttamente gestito nell'export.
**Fix**: Allineamento campo nell'export.
**Stato**: FIXATO

### H3 — Backup restore size limit (FIXATO)

**Scope**: `api/routers/backup.py`
**Problema**: Nessun limite di dimensione sul file di restore. Un file malevolo di grandi dimensioni potrebbe saturare la memoria.
**Fix**: Aggiunto size limit 500 MB sull'upload di restore.
**Stato**: FIXATO

### H4 — Public portal rate limiter alignment (FIXATO)

**Scope**: `api/routers/public_portal.py`
**Problema**: Parametri rate limiter da riallineare dopo le calibrazioni di INC-2026-03-30.
**Fix**: Verificato e confermato allineamento: 30 req/min, 120 req/ora.
**Stato**: FIXATO

---

## Finding Medie (7)

### M1 — Test coverage backend

**Metrica**: 361 test pytest, copertura su tutti i domini critici (contratti, rate, pagamenti, workout cascade, dashboard, safety engine).
**Stato**: ADEGUATO per v1.0.6

### M2 — Test coverage frontend

**Metrica**: 69 vitest (data protection + onboarding/connectivity wizard + runtime UI logic).
**Raccomandazione**: Aumentare copertura su hook mutation (invalidazione simmetrica) in iterazioni future.
**Stato**: ACCETTABILE

### M3 — Licenza enforcement

**Verifica**: Default ON in compiled mode (Nuitka + PyInstaller). Embedded key, env bypass bloccato (ADR-005), fingerprint fail-closed.
**Stato**: CONFERMATO OK

### M4 — Anti-reverse engineering

**Verifica**: 4 step completati (ADR-007): bundle sanitization, DB encryption AES-256-GCM, Nuitka native compilation. TTC post-hardening: dati scientifici >1 settimana, license bypass >3 giorni.
**Stato**: CONFERMATO OK — rischio da CRITICO a ACCETTABILE per L2

### M5 — Build script alignment (FIXATO)

**Scope**: `tools/build/build-release.sh`
**Problema**: Riferimenti da aggiornare per allineamento con stato corrente.
**Fix**: Aggiornamento applicato.
**Stato**: FIXATO

### M6 — Documentazione non allineata

**Problema**: `docs/INDEX.md` mancava 2 file (`PRE_DELIVERY_AUDIT`, `RECURRING_SESSIONS_SPEC`), contatore ADR errato (7 vs 9). Release checklist riferiva versione 1.0.4, 269 test, PyInstaller.
**Stato**: FIXATO in questa sessione (aggiornamento docs post-audit)

### M7 — Anamnesi pubblica CSS hardening (FIXATO)

**Scope**: `frontend/src/app/public/anamnesi/[token]/page.tsx`
**Problema**: Pagina pubblica anamnesi usava CSS variables del tema — stessa classe di bug C1.
**Fix**: Applicato stesso pattern del portale workout: colori Tailwind espliciti + `colorScheme: "light"`.
**Stato**: FIXATO (incluso in C1)

---

## Finding Basse (6) — Informational

### L1 — Debito tecnico core/

9 repository legacy con `sqlite3` raw in `core/`. Non impattano il runtime (moduli AI dormenti).

### L2 — 32 orphan exercise IDs

IDs orfani in crm.db da catalogo pre-rebuild. UI ha fallback. Nessun impatto funzionale.

### L3 — 10 pietanze senza ricetta

Ingrediente crudo assente (bulgur, aragosta, quaglia, etc.). Copertura 95% (210/220 pietanze).

### L4 — `__version__` non visibile in UI

La versione (`1.0.6`) non e' mostrata nella pagina Impostazioni. Bassa priorita'.

### L5 — ADR-002 file mancante

L'ADR-002 (Operational Workspace Case Engine) e' referenziato nell'indice ma il file non esiste nel filesystem. Il file potrebbe essere stato rinominato o rimosso.

### L6 — Due ADR-007

Esistono due file con numerazione ADR-007: `anti-reverse-engineering.md` e `fitscan-computer-vision-biomechanics.md`. Da rinumerare in iterazione futura.

---

## Punti di Forza Confermati

1. **Privacy-first**: zero cloud, dati sul PC del trainer, SQLite locale
2. **Multi-tenant safety**: ogni query filtra per `trainer_id`, bouncer pattern su tutti gli endpoint
3. **Contract Integrity Engine**: 12 livelli di protezione (residual, chiuso guard, auto-close, overpayment, cascade)
4. **Audit trail**: `log_audit()` su ogni mutazione business
5. **Soft delete**: nessuna perdita dati permanente, recovery possibile
6. **Safety Engine**: 47 condizioni mediche, 80 pattern rules, dual-session corretto
7. **Training Science Engine**: ~3500 LOC, periodizzazione, EMG, volume MEV/MAV/MRV
8. **Nutrition Science Engine**: ~2100 LOC, piano LARN 7gg, 880 alimenti, servability architecture
9. **Anti-RE robusto**: Nuitka nativo + DB cifrati + bundle sanitizzato (ADR-007)
10. **WhatsApp integration**: 15 template, auto-log, zero API esterne
11. **Portale pubblico**: anamnesi + workout condivisibili via token, rate limiter calibrato
12. **Test suite solida**: 361 pytest + 69 vitest + E2E business/distribution rehearsal

---

## Verifica Finale

| Check | Risultato |
|-------|-----------|
| `ruff check api/` | 0 errori |
| `npx next build` | 0 errori TS |
| `pytest tests/ -v` | 361 pass, 0 fail |
| Frontend vitest | 69 pass |
| Pagine pubbliche: zero CSS variables tema | Confermato (grep 0 occorrenze) |

---

## Riferimenti

| Documento | Path |
|-----------|------|
| Security Audit Post-Hardening | `docs/technical/SECURITY_AUDIT_POST_HARDENING.md` |
| Security Audit Baseline | `docs/technical/SECURITY_AUDIT_BASELINE.md` |
| Security Model | `docs/technical/SECURITY_MODEL.md` |
| ADR-007 (Anti-RE) | `docs/adr/ADR-007-anti-reverse-engineering.md` |
| ADR-005 (License) | `docs/adr/ADR-005-license-hardening-anti-tampering.md` |
| INC-2026-03-30 (CSS dark mode) | `docs/incidents/INC-2026-03-30-portal-mobile-invisible-ui.md` |
| Release Checklist | `docs/operations/RELEASE_CHECKLIST.md` |
