# Security Model — FitManager AI Studio

Modello di sicurezza del prodotto. Copre: threat model, protezioni implementate,
limitazioni note, roadmap futuri interventi.

Ultimo aggiornamento: 2026-04-09 (ADR-007 anti-reverse engineering).

## Principi

1. **Privacy-first**: dati clinici e finanziari mai esposti in viste pubbliche
2. **Local-only data**: zero cloud obbligatorio, dati sul PC del professionista
3. **Defense in depth**: piu' livelli indipendenti, nessun single point of failure
4. **Fail-closed**: in caso di dubbio, blocca (non degrada silenziosamente)
5. **Proporzionalita'**: protezione adeguata al rischio reale, non over-engineering

## Livelli di protezione

```
┌─────────────────────────────────────────────────────────────┐
│  L1 — Autenticazione & Autorizzazione                      │
│  JWT + bcrypt, Bouncer Pattern, Deep Relational IDOR       │
├─────────────────────────────────────────────────────────────┤
│  L2 — Licenza & Hardware Binding                           │
│  JWT RS256, machine fingerprint SHA-256, enforcement       │
├─────────────────────────────────────────────────────────────┤
│  L3 — Anti-Tampering (compiled mode)                       │
│  Embedded key, integrity hash, env bypass block,           │
│  fingerprint fail-closed (PyInstaller + Nuitka)            │
├─────────────────────────────────────────────────────────────┤
│  L3b — Database Encryption                                 │
│  AES-256-GCM su catalog.db + nutrition.db,                 │
│  PBKDF2-HMAC-SHA256, in-memory loading via deserialize()   │
├─────────────────────────────────────────────────────────────┤
│  L4 — Data Integrity                                       │
│  Soft delete, audit trail, atomic transactions, WAL        │
├─────────────────────────────────────────────────────────────┤
│  L5 — Build & Release Safety                               │
│  ADR-004 pipeline, 3 safety gates, bundle sanitization,    │
│  Nuitka native compilation, smoke test, manifest           │
├─────────────────────────────────────────────────────────────┤
│  L6 — Anti-Reverse Engineering                             │
│  Bundle sanitization (zero Alembic/seed/pyc),              │
│  DB encryption (AES-256-GCM), Nuitka (Python→C→x86-64)    │
└─────────────────────────────────────────────────────────────┘
```

---

## L1 — Autenticazione & Autorizzazione

### Cosa protegge
Accesso non autorizzato ai dati del trainer (clienti, contratti, dati clinici, finanziari).

### Meccanismi

| Meccanismo | Implementazione | File chiave |
|-----------|----------------|-------------|
| Password hashing | bcrypt (salted) | `api/auth/service.py` |
| Session token | JWT HS256 con expiry | `api/auth/service.py` |
| Ownership check | Bouncer Pattern su ogni endpoint | `api/routers/*.py` |
| Deep IDOR | Catena FK per ownership (Rate → Contract → `trainer_id`) | `api/routers/rates.py` |
| Mass assignment | `extra: "forbid"`, `trainer_id`/`id` mai in Create schema | `api/schemas/*.py` |
| Error masking | 404 (mai 403) per dati non propri | Tutti i bouncer |

### Regole non negoziabili
- Ogni query filtra per `trainer_id` — mai bypassare ownership
- Non trovato = 404, mai 403 (non rivelare esistenza dati altrui)
- `trainer_id` e `id` mai accettati in payload Create

---

## L2 — Licenza & Hardware Binding

### Cosa protegge
Utilizzo non autorizzato del software su macchine non licenziate.

### Meccanismi

| Meccanismo | Implementazione | File chiave |
|-----------|----------------|-------------|
| Firma digitale | JWT RS256 (RSA 2048-bit) | `api/services/license.py` |
| Hardware binding | SHA-256 di CPU+Board+BIOS (PowerShell WMI) | `api/services/machine_fingerprint.py` |
| Enforcement middleware | Blocco 403 su rotte protette | `api/main.py` (LicenseMiddleware) |
| Key management | Private key offline (`~/.fitmanager/`), public key nell'installer | CLI + installer |
| Expiry | Claim `exp` nel JWT, verificato a ogni request | `api/services/license.py` |

### Flusso di verifica

```
Request → LicenseMiddleware → check_license()
  1. File license.key presente?          → missing se no
  2. Chiave pubblica disponibile?        → unconfigured se no
  3. Firma JWT valida?                   → invalid se no
  4. Token non scaduto?                  → expired se no
  5. machine_id nel JWT == fingerprint?  → wrong_machine se no
  6. Tutto OK                            → valid
```

### Documentazione operativa
Guida completa per generazione, attivazione, trasferimento e rinnovo:
`docs/technical/LICENSE_ACTIVATION.md`

---

## L3 — Anti-Tampering (compiled mode)

Introdotto con ADR-005 (2026-03-24). Attivo in compiled mode (PyInstaller o Nuitka).

### Cosa protegge
Manomissione del sistema licenza: sostituzione chiave, bypass via env var,
blocco fingerprint, patching.

### Meccanismi

| Vettore chiuso | Protezione | Effetto |
|---------------|-----------|--------|
| Sostituzione `license_public.pem` | Chiave pubblica embedded nel codice | File su disco ignorato in compiled mode |
| Env `LICENSE_ENFORCEMENT_ENABLED=false` | `is_license_enforcement_enabled()` ritorna sempre `True` in compiled mode | Env var ignorata |
| PowerShell bloccato / WMI disabilitato | Fingerprint `"unavailable"` → `wrong_machine` | Blocco con messaggio supporto |
| Patching chiave embedded | SHA-256 integrity hash verificato a runtime | Chiave alterata → `unconfigured` → blocco |

### Detection compiled mode
Helper `is_compiled()` in `api/config.py` rileva sia PyInstaller (`sys.frozen`) che Nuitka (`__compiled__`). Usato da tutti i componenti di enforcement.

### Invariante dev mode
In dev mode (non-compiled) tutto resta come prima: file/env resolution, enforcement toggle,
fingerprint graceful degradation. Zero impatto su workflow sviluppo.

---

## L3b — Database Encryption (AES-256-GCM)

Introdotto con ADR-007 (2026-04-09). Protegge catalog.db e nutrition.db.

### Cosa protegge
Patrimonio scientifico (500 esercizi × 43 colonne, 880 alimenti CREA, 12 template LARN) da estrazione diretta con client SQLite.

### Meccanismi

| Meccanismo | Implementazione | File chiave |
|-----------|----------------|-------------|
| Cifratura | AES-256-GCM (nonce 12B, tag 16B) | `api/services/db_crypto.py` |
| Key derivation | PBKDF2-HMAC-SHA256 (100K iter) da seed embedded | `api/services/db_crypto.py` |
| Seed integrity | SHA-256 hash del seed verificato prima di ogni derivazione | `api/services/db_crypto.py` |
| In-memory loading | `sqlite3.deserialize()` → StaticPool engine | `api/database.py` |

### Architettura

```
BUILD TIME:  catalog.db  ──encrypt_db()──> catalog.db.enc  (shipped nell'installer)
RUNTIME:     catalog.db.enc ──decrypt()──> sqlite3.deserialize() ──> in-memory SQLAlchemy engine
DEV MODE:    catalog.db (plain) ──> engine normale (zero cambiamenti)
```

### Formato file .enc

```
[salt: 16 bytes][nonce: 12 bytes][ciphertext: N bytes (include GCM tag)]
```

### Invariante dev mode
In dev mode i file `.db` plain sono usati direttamente. La cifratura e' attiva solo in compiled mode quando i file `.enc` esistono.

---

## L4 — Data Integrity

### Cosa protegge
Perdita, corruzione o cancellazione accidentale di dati business.

### Meccanismi

| Meccanismo | Implementazione | File chiave |
|-----------|----------------|-------------|
| Soft delete | `deleted_at` su tutte le tabelle business | `api/models/*.py` |
| Audit trail | `log_audit()` su CREATE/UPDATE/DELETE | `api/routers/_audit.py` |
| Atomic transactions | Singolo `session.commit()` per operazioni multi-tabella | `api/routers/*.py` |
| WAL mode | `journal_mode=WAL` su tutti e 3 i DB | `api/database.py` |
| Backup automatico | Backup crm.db al startup (solo prod) | `api/main.py` |
| Contract Integrity Engine | 12 livelli di protezione finanziaria | `api/routers/contracts.py`, `rates.py` |
| Cataloghi read-only | catalog.db e nutrition.db shipped con installer, mai modificati | ADR-003 |

---

## L5 — Build & Release Safety

### Cosa protegge
Rilascio di build corrotte, con dati sensibili o con componenti mancanti.

### Meccanismi (ADR-004 + ADR-007)

| Fase | Cosa verifica |
|------|--------------|
| PREFLIGHT | Git clean, pytest pass, ruff clean, next build OK |
| BUILD | Backend Nuitka (Python → C → nativo), frontend standalone, 3 safety gates |
| VERIFY | Smoke test su exe: /health, invarianti |
| SEAL | manifest.json con SHA-256, commit, metadata |
| TAG | git tag vX.Y.Z |

### Bundle sanitization (ADR-007)
- Zero Alembic migrations nel bundle (rimossi da spec)
- Zero seed JSON nel bundle (rimossi da spec + ISS)
- Zero `.db` plain per cataloghi (solo `.db.enc` cifrati)

---

## L6 — Anti-Reverse Engineering

Introdotto con ADR-007 (2026-04-09). Difesa stratificata contro estrazione IP.

### Cosa protegge
Proprieta' intellettuale: codice sorgente (Training Science ~9K LOC, Nutrition Science ~2.5K LOC, Safety Engine 80 rules) e patrimonio scientifico (cataloghi DB).

### Meccanismi (4 step indipendenti)

| Step | Protezione | Effetto |
|------|-----------|--------|
| 1. Bundle sanitization (Alembic) | Rimossi migrations dal bundle | Schema DB nascosto |
| 2. Bundle sanitization (Seed) | Rimossi JSON dal bundle | Dati esercizi non in chiaro |
| 3. DB encryption | AES-256-GCM su catalog.db + nutrition.db | Cataloghi illeggibili |
| 4. Native compilation | Nuitka (Python → C → x86-64) | Zero bytecode decompilabile |

### Impatto TTC (Time-to-Crack)

| Asset | Pre-hardening | Post-hardening |
|-------|--------------|----------------|
| Catalogo 500 esercizi | 5 sec | > 1 settimana |
| 880 alimenti CREA | 5 sec | > 1 settimana |
| Training Science (9K LOC) | 15 min | > 1 settimana |
| License bypass | 1-2 ore | > 3 giorni |

Audit completo: `docs/technical/SECURITY_AUDIT_POST_HARDENING.md`

---

## Threat model — rischi residui e prossimi interventi

### Rischio residuo attuale

| Rischio | Probabilita' | Impatto | Mitigazione attuale | Stato |
|---------|-------------|---------|-------------------|-------|
| RE binario nativo (Ghidra/IDA) | Molto bassa | Alto | Nuitka nativo + crittografia DB (L6) | Accettato |
| Copia crm.db su altra istanza | Media | Medio | Hardware binding blocca l'app, dati inutili senza app | Accettato |
| Keylogger/screen capture su PC trainer | Bassa | Alto | Fuori scope (sicurezza OS) | Accettato |
| Distribuzione installer a terzi | Media | Alto | NDA + hardware binding + codice nativo | Mitigato |
| JWT replay (license.key copiata) | Bassa | Medio | machine_id impedisce uso su altra macchina | Mitigato |

### Roadmap sicurezza — prossimi interventi possibili

Ordinati per rapporto impatto/costo. Non tutti necessari — valutare in base all'evoluzione
del prodotto e del modello di distribuzione.

#### Fase 1 — Pre-lancio (IMPLEMENTATO)

- [x] JWT RS256 + hardware binding (L2)
- [x] Enforcement middleware (L2)
- [x] Embedded public key anti file-replacement (L3)
- [x] Env var bypass block in compiled mode (L3)
- [x] Fingerprint fail-closed in compiled mode (L3)
- [x] Integrity hash chiave pubblica (L3)
- [x] AES-256-GCM su catalog.db + nutrition.db (L3b)
- [x] Bundle sanitization — zero Alembic/seed/pyc (L5/L6)
- [x] Nuitka native compilation — Python → C → x86-64 (L5/L6)
- [x] 5-phase release pipeline con safety gates (L5)

#### Fase 2 — Post-lancio (trigger-based)

| Intervento | Costo | Impatto | Quando |
|-----------|-------|---------|--------|
| **Code signing Authenticode** | Basso | Medio — certificato digitale sull'exe, previene tampering binario | Prima di distribuzione > 50 clienti |
| **License revocation list** | Basso | Medio — blacklist licenze compromesse (file locale o check opzionale) | Se emerge abuso licenze |
| **Telemetria anonima opt-in** | Medio | Medio — heartbeat periodico per rilevare cloni | Se modello diventa SaaS-like |
| **Watermark nel DB** | Basso | Basso — record nascosto in crm.db per tracciare provenienza | Per trial partner specifici |

#### Fase 3 — Evoluzione architetturale (se il business lo richiede)

| Intervento | Costo | Impatto | Quando |
|-----------|-------|---------|--------|
| **License server** | Alto | Molto alto — verifica online, revoca remota, analytics | Se modello SaaS/subscription |
| **Anti-debug runtime** (Frida detection) | Medio | Alto — Anello 6 ambientale | Se emerge piracy attiva |
| **SQLCipher su crm.db** | Medio | Alto — DB illeggibile senza chiave | Se dati clinici diventano regolamentati |
| **DRM nativo** (Widevine/custom) | Alto | Molto alto — protezione a livello OS | Probabilmente mai necessario |

---

## Protezione legale (complementare al tecnico)

Le protezioni tecniche sono una barriera, non una garanzia. Per tutela completa:

1. **NDA**: da firmare PRIMA di qualsiasi installazione su macchina di terzi
2. **Evaluation Agreement**: licenza di valutazione temporanea con clausole di proprieta'
3. **Prova di anteriorita'**: PEC a se stessi con archivio codice sorgente (data certa legale)
4. **Deposito SIAE** (Sezione OLAF): prova formale di paternita' (~100-200 EUR)
5. **Copyright automatico**: in Italia/EU il diritto d'autore sul software nasce con la creazione;
   la git history e' una prova forte di paternita'

---

## File di riferimento

| File | Contenuto |
|------|----------|
| `api/services/license.py` | Servizio verifica licenza JWT RSA (4-tier key resolution) |
| `api/services/machine_fingerprint.py` | Fingerprint hardware SHA-256 |
| `api/services/system_runtime.py` | Enforcement toggle + health |
| `api/services/db_crypto.py` | AES-256-GCM encrypt/decrypt per cataloghi |
| `api/config.py` | `is_compiled()` helper + path encrypted DB |
| `api/database.py` | `_load_encrypted_db()` + engine condizionale |
| `api/main.py` | LicenseMiddleware |
| `tools/build/build-backend-nuitka.sh` | Build script Nuitka |
| `tools/build/fitmanager.spec` | Build spec PyInstaller (backup/rollback) |
| `tools/admin_scripts/generate_license.py` | CLI generazione licenze |
| `docs/technical/LICENSE_ACTIVATION.md` | Guida operativa attivazione |
| `docs/security/ANTI_REVERSE_ENGINEERING_STRATEGY.md` | Strategia anti-RE completa |
| `docs/technical/SECURITY_AUDIT_BASELINE.md` | Audit pre-hardening |
| `docs/technical/SECURITY_AUDIT_POST_HARDENING.md` | Audit post-hardening |
| `docs/adr/ADR-005-license-hardening-anti-tampering.md` | Decisione architetturale hardening licenza |
| `docs/adr/ADR-007-anti-reverse-engineering.md` | Decisione architetturale anti-RE |
| `tests/test_license_hardening.py` | 9 test copertura hardening |
| `tests/test_license_service.py` | 9 test servizio licenza |
| `tests/test_license_middleware.py` | 8 test middleware enforcement |
| `tests/test_license_roundtrip.py` | 3 test round-trip generazione→verifica |
