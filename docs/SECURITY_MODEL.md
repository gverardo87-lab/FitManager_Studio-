# Security Model — FitManager AI Studio

Modello di sicurezza del prodotto. Copre: threat model, protezioni implementate,
limitazioni note, roadmap futuri interventi.

Ultimo aggiornamento: 2026-03-24 (ADR-005 hardening).

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
│  L3 — Anti-Tampering (frozen mode)                         │
│  Embedded key, integrity hash, env bypass block,           │
│  fingerprint fail-closed                                   │
├─────────────────────────────────────────────────────────────┤
│  L4 — Data Integrity                                       │
│  Soft delete, audit trail, atomic transactions, WAL        │
├─────────────────────────────────────────────────────────────┤
│  L5 — Build & Release Safety                               │
│  ADR-004 pipeline, 3 safety gates, smoke test, manifest    │
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
`docs/LICENSE_ACTIVATION.md`

---

## L3 — Anti-Tampering (frozen mode only)

Introdotto con ADR-005 (2026-03-24). Attivo SOLO in build PyInstaller.

### Cosa protegge
Manomissione del sistema licenza: sostituzione chiave, bypass via env var,
blocco fingerprint, patching bytecode.

### Meccanismi

| Vettore chiuso | Protezione | Effetto |
|---------------|-----------|--------|
| Sostituzione `license_public.pem` | Chiave pubblica embedded nel codice Python | File su disco ignorato in frozen |
| Env `LICENSE_ENFORCEMENT_ENABLED=false` | `is_license_enforcement_enabled()` ritorna sempre `True` in frozen | Env var ignorata |
| PowerShell bloccato / WMI disabilitato | Fingerprint `"unavailable"` → `wrong_machine` | Blocco con messaggio supporto |
| Bytecode patching della chiave embedded | SHA-256 integrity hash verificato a runtime | Chiave alterata → `unconfigured` → blocco |

### Invariante dev mode
In dev mode (non-frozen) tutto resta come prima: file/env resolution, enforcement toggle,
fingerprint graceful degradation. Zero impatto su workflow sviluppo.

### Limitazioni note
- Un reverse engineer esperto puo' decompilare il bytecode PyInstaller e patchare
  sia la chiave che l'hash. Richiede competenze significative e tempo.
- PyInstaller non e' un vero obfuscator — il bytecode Python e' recuperabile.
- Queste protezioni sono una barriera proporzionata contro copia opportunistica,
  non contro attaccanti dedicati.

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

### Meccanismi (ADR-004)

| Fase | Cosa verifica |
|------|--------------|
| PREFLIGHT | Git clean, pytest pass, ruff clean, next build OK |
| BUILD | 3 safety gates: CRM leak check, ISS ref check, nutrition integrity |
| VERIFY | Smoke test su exe: /health, invarianti |
| SEAL | manifest.json con SHA-256, commit, metadata |
| TAG | git tag vX.Y.Z |

---

## Threat model — rischi residui e prossimi interventi

### Rischio residuo attuale

| Rischio | Probabilita' | Impatto | Mitigazione attuale | Stato |
|---------|-------------|---------|-------------------|-------|
| Decompilazione PyInstaller + patching | Bassa | Alto | Integrity hash (L3) | Accettato |
| Copia crm.db su altra istanza | Media | Medio | Hardware binding blocca l'app, dati inutili senza app | Accettato |
| Keylogger/screen capture su PC trainer | Bassa | Alto | Fuori scope (sicurezza OS) | Accettato |
| Distribuzione installer a terzi | Media | Alto | NDA + hardware binding | Parziale |
| JWT replay (license.key copiata) | Bassa | Medio | machine_id impedisce uso su altra macchina | Mitigato |

### Roadmap sicurezza — prossimi interventi possibili

Ordinati per rapporto impatto/costo. Non tutti necessari — valutare in base all'evoluzione
del prodotto e del modello di distribuzione.

#### Fase 1 — Pre-lancio (gia' implementato)

- [x] JWT RS256 + hardware binding
- [x] Enforcement middleware
- [x] Embedded public key (anti file-replacement)
- [x] Env var bypass block (frozen mode)
- [x] Fingerprint fail-closed (frozen mode)
- [x] Integrity hash chiave pubblica
- [x] 5-phase release pipeline con safety gates

#### Fase 2 — Post-lancio (quando necessario)

| Intervento | Costo | Impatto | Quando |
|-----------|-------|---------|--------|
| **Nuitka compilation** | Medio | Alto — codice nativo, molto piu' difficile da decompilare | Se distribuzione cresce oltre trial partner |
| **License revocation list** | Basso | Medio — blacklist licenze compromesse (file locale o check opzionale) | Se emerge abuso licenze |
| **Telemetria anonima opt-in** | Medio | Medio — heartbeat periodico per rilevare cloni | Se modello diventa SaaS-like |
| **Code signing** (Authenticode) | Basso | Medio — certificato digitale sull'exe, previene tampering binario | Prima di distribuzione su larga scala |
| **Watermark nel DB** | Basso | Basso — record nascosto in crm.db per tracciare provenienza | Per trial partner specifici |

#### Fase 3 — Evoluzione architetturale (se il business lo richiede)

| Intervento | Costo | Impatto | Quando |
|-----------|-------|---------|--------|
| **License server** | Alto | Molto alto — verifica online, revoca remota, analytics | Se modello SaaS/subscription |
| **Encrypted SQLite** (SQLCipher) | Medio | Alto — DB illeggibile senza chiave | Se dati clinici diventano regolamentati |
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
| `api/services/license.py` | Servizio verifica licenza + hardening L3 |
| `api/services/machine_fingerprint.py` | Fingerprint hardware SHA-256 |
| `api/services/system_runtime.py` | Enforcement toggle + health |
| `api/main.py` | LicenseMiddleware |
| `tools/admin_scripts/generate_license.py` | CLI generazione licenze |
| `docs/LICENSE_ACTIVATION.md` | Guida operativa attivazione |
| `docs/adr/ADR-005-license-hardening-anti-tampering.md` | Decisione architetturale hardening |
| `tests/test_license_hardening.py` | 9 test copertura hardening |
| `tests/test_license_service.py` | 9 test servizio licenza |
| `tests/test_license_middleware.py` | 8 test middleware enforcement |
| `tests/test_license_roundtrip.py` | 3 test round-trip generazione→verifica |
