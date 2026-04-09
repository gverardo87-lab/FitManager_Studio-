# Security Audit Post-Hardening — Re-Test v2.0

**Data**: 2026-04-09
**Branch**: FitManager_Studio
**Build testato**: Post-hardening (4 step anti-RE completati)
**Baseline**: `SECURITY_AUDIT_BASELINE.md` (2026-04-01, v1.0.6)
**Obiettivo**: Verificare efficacia dei 4 step anti-RE e misurare TTC aggiornati

---

## Executive Summary

| Verdetto | Dettaglio |
|----------|-----------|
| **Rischio globale** | **ACCETTABILE** — un L2 richiede giorni/settimane, non minuti |
| **Miglioramento** | Da 4 FAIL + 1 FAIL CRITICO a 6 PASS + 1 PASS condizionato |
| **Anello piu' debole** | License bypass (richiede RE nativo, ~3+ giorni per L2) |
| **Anello piu' forte** | Database cataloghi (AES-256-GCM) + Frontend (source map vuote) |

---

## Confronto Pre/Post

| # | Test | TTC Pre-Hardening | TTC Post-Hardening | Delta | Verdetto |
|---|------|-------------------|--------------------|----|----------|
| 1 | PyInstaller bundle | **30 sec** | **N/A** (Nuitka nativo) | Vettore eliminato | **PASS** |
| 2 | Database cataloghi | **5 sec** | **> 1 settimana** | x120.000+ | **PASS** |
| 3 | Seed + Migrations | **0 sec** | **N/A** (rimossi) | Vettore eliminato | **PASS** |
| 4 | String extraction | PASS parziale | **PASS** (nativo) | Migliorato | **PASS** |
| 5 | Frontend build | 1-2 giorni | 1-2 giorni | Invariato | **PASS** |
| 6 | License bypass | **1-2 ore** | **> 3 giorni** | x36+ | PASS condizionato |
| 7 | Decompilation | **< 15 min** | **> 1 settimana** | x700+ | **PASS** |

---

## Test Results Dettagliati

### TEST 1: Bundle Analysis — PASS (vettore eliminato)

**Pre**: PyInstaller bundle con `.pyc` estraibili in 30 secondi via `pyinstxtractor`.
**Post**: Bundle Nuitka produce codice macchina x86-64 nativo. Zero `.pyc` nel bundle.

| Metrica | Pre | Post |
|---------|-----|------|
| PyInstaller magic | Trovato | **Assente** (non e' PyInstaller) |
| `.pyc` estraibili | 33+ file | **0** |
| `.py` in chiaro | 31 (Alembic) | **0** (rimossi) |
| `pyinstxtractor` | Funziona | **Fallisce** ("Not a PyInstaller archive") |
| Tipo binario | Bytecode Python | **Codice macchina nativo** |

**Verdetto**: **PASS** — il vettore PyInstaller e' completamente eliminato.

---

### TEST 2: Database Cataloghi — PASS

**Pre**: catalog.db e nutrition.db apribili con qualsiasi client SQLite in 5 secondi.
**Post**: Solo file `.db.enc` nel bundle (AES-256-GCM). Zero file `.db` plain.

| Metrica | Pre | Post |
|---------|-----|------|
| File distribuiti | `catalog.db`, `nutrition.db` (plain) | `catalog.db.enc`, `nutrition.db.enc` |
| `sqlite3 catalog.db.enc` | N/A | **"not a database"** |
| `file catalog.db.enc` | N/A | **"data"** (nessun header SQLite) |
| Chiave crittografica | N/A | PBKDF2-HMAC-SHA256 da seed embedded nel binario nativo |

**Attacco richiesto**: estrarre seed dal binario nativo (richiede RE assembly x86-64) → derivare chiave → decifrare. TTC: **> 1 settimana** per L2.

**Verdetto**: **PASS** — patrimonio scientifico protetto da crittografia AES-256-GCM con chiave embedded in codice nativo.

---

### TEST 3: Seed + Migrations — PASS (vettore eliminato)

**Pre**: 4 seed JSON (4 MB) + 30 migration Alembic in chiaro nel bundle.
**Post**: Zero seed JSON, zero Alembic nel bundle distribuito.

| File | Pre | Post |
|------|-----|------|
| `_internal/data/exercises/seed_*.json` | 4 file (4 MB) | **Assenti** |
| `_internal/alembic/` | 30 migration .py | **Assente** |
| `_internal/alembic.ini` | Presente | **Assente** |

**Verdetto**: **PASS** — vettore completamente eliminato.

---

### TEST 4: String Extraction — PASS

**Pre**: Stringhe nel PYZ bytecode (leggibili dopo decompilazione).
**Post**: Codice nativo — stringhe ottimizzate/inline nel codice macchina.

| Target | Pre | Post |
|--------|-----|------|
| `EMBEDDED_PUBLIC_KEY` | Nel PYZ (post decompilazione) | **Nel binario nativo** (richiede RE) |
| Module names (`api.services.xxx`) | Nel PYZ | **Ottimizzati** (Nuitka inlining) |
| `training_science` | Nel PYZ | **In codice macchina** |
| `_EMBEDDED_KEY_SEED` | Nel PYZ | **In codice macchina** |

**Verdetto**: **PASS** — stringhe non recuperabili senza RE del binario nativo.

---

### TEST 5: Frontend Build — PASS (invariato)

Nessun cambiamento al frontend. Source map vuote, TypeScript non recuperabile.

**Verdetto**: **PASS** — invariato rispetto al baseline.

---

### TEST 6: License Bypass — PASS condizionato

**Pre**: Dopo decompilazione PYZ (30 sec + 15 min), chiave pubblica e hash in chiaro → auto-firma licenze in 1-2 ore.
**Post**: Chiave pubblica e hash embedded in codice macchina nativo. Richiede RE assembly per trovarli e patcharli.

| Vettore | Pre | Post |
|---------|-----|------|
| Decompilazione → patch | 1-2 ore | **> 3 giorni** (RE nativo) |
| Env bypass `LICENSE_ENFORCEMENT_ENABLED` | Bloccato (ADR-005) | Bloccato (ADR-005) |
| Fingerprint bypass | Bloccato (fail-closed) | Bloccato (fail-closed) |

**Condizione**: un L3 (RE professionale) con IDA Pro/Ghidra e tempo dedicato potrebbe trovare e patchare la verifica. Ma il costo supera il valore del target (licenza EUR 249, nicchia italiana).

**Verdetto**: **PASS condizionato** — protezione adeguata per L2, non garantita per L3+.

---

### TEST 7: Decompilation Surface — PASS

**Pre**: 100% del codice Python recuperabile in < 15 minuti.
**Post**: Zero bytecode Python nel bundle. Solo codice macchina nativo.

| Strumento | Pre | Post |
|-----------|-----|------|
| `pyinstxtractor` | Estrae tutto | **Fallisce** |
| `decompyle3` | Decompila tutto | **Nulla da decompilare** |
| `uncompyle6` | Decompila tutto | **Nulla da decompilare** |
| Ghidra/IDA Pro | Non necessario | **Unica via** (RE assembly) |

**Attacco richiesto**: analisi statica del binario nativo con Ghidra o IDA Pro → ricostruzione manuale della logica da assembly x86-64. TTC: **> 1 settimana** per L2.

**Verdetto**: **PASS** — codice proprietario non piu' decompilabile con tool standard.

---

## Matrice TTC Aggiornata — Crown Jewels

| Crown Jewel | TTC Pre | TTC Post (Step 1-3) | TTC Post (Step 1-4) | Protezione |
|-------------|---------|---------------------|----------------------|------------|
| Schema 26 tabelle business | **0 sec** | > 1 giorno | **> 1 settimana** | Alembic rimosso + nativo |
| Catalogo 500 esercizi (43 col) | **5 sec** | > 1 giorno | **> 1 settimana** | AES-256-GCM + nativo |
| 880 alimenti CREA + template | **5 sec** | > 1 giorno | **> 1 settimana** | AES-256-GCM + nativo |
| Training Science (9K LOC) | **15 min** | 15 min | **> 1 settimana** | Nativo (zero bytecode) |
| Nutrition Science (2.5K LOC) | **15 min** | 15 min | **> 1 settimana** | Nativo (zero bytecode) |
| Safety Engine (80 rules) | **15 min** | 15 min | **> 1 settimana** | Nativo (zero bytecode) |
| License bypass | **1-2 ore** | 1-2 ore | **> 3 giorni** | Nativo + ADR-005 |
| Seed esercizi JSON | **0 sec** | N/A (rimosso) | **N/A** (rimosso) | Eliminato dal bundle |

---

## Gap Analysis Aggiornata — Anelli di Protezione

| Anello | Descrizione | Stato Pre | Stato Post |
|--------|-------------|-----------|------------|
| 1. Legal | NDA + non-compete | NON FIRMATO | **DA FIRMARE** (fuori scope tecnico) |
| 2. Licensing | JWT RS256 + HW binding | Buono (ADR-005) | **Buono** (invariato) |
| 3. Integrity | DB cifrati + hash chiave | Minimale | **Forte** (AES-256-GCM + PBKDF2) |
| 4. Obfuscation | Bundle sanitization | ASSENTE | **Implementato** (zero .py/.json/.pyc) |
| 5. Compilation | Codice nativo | ASSENTE | **Implementato** (Nuitka → C → x86-64) |
| 6. Environmental | Anti-debug runtime | ASSENTE | **Fuori scope Phase 1** |

---

## Verdetto Finale

**Rischio complessivo**: da **CRITICO** a **ACCETTABILE** per il target L2.

La protezione e' proporzionata al modello di business (licenza EUR 249, nicchia italiana):
- Un L2 con tool standard (pyinstxtractor, decompyle3, DB Browser) non puo' estrarre nulla
- Un L2 con competenze RE necessita di giorni/settimane e tool professionali (Ghidra, IDA Pro)
- Il costo dell'attacco supera ampiamente il valore del target

**Prossimi step** (trigger-based, non preventivi):
- NDA firmato prima della consegna al partner
- Code signing Authenticode se distribuzione > 50 clienti
- Anti-debug runtime se emerge evidenza di piracy

---

## Riferimenti

| Documento | Path |
|-----------|------|
| Audit Baseline (pre-hardening) | `docs/technical/SECURITY_AUDIT_BASELINE.md` |
| Strategia Anti-RE | `docs/security/ANTI_REVERSE_ENGINEERING_STRATEGY.md` |
| Security Model | `docs/technical/SECURITY_MODEL.md` |
| ADR-007 | `docs/adr/ADR-007-anti-reverse-engineering.md` |
| ADR-005 (license hardening) | `docs/adr/ADR-005-license-hardening-anti-tampering.md` |
