# Security Audit Baseline — Red Team Test v1.0.6

**Data**: 2026-04-01
**Branch**: FitManager_Studio
**Build testato**: dist/fitmanager/ (v1.0.6, 105 MB)
**Obiettivo**: Misurare il Time-to-Crack (TTC) per ogni Crown Jewel prima della consegna al partner

---

## Executive Summary

| Verdetto | Dettaglio |
|----------|-----------|
| **Rischio globale** | **CRITICO** — un L2 (sviluppatore esperto) estrae tutto in < 1 giorno |
| **Anello più debole** | Database cataloghi (5 secondi) e migrations Alembic (in chiaro nel bundle) |
| **Anello più forte** | Frontend standalone (source map vuote, no sorgente recuperabile) |
| **Azione raccomandata** | Implementare Anelli 4-5 (obfuscation + compilation) prima della consegna |

---

## Threat Model

**Attaccante target**: Alessio Crociani (partner) o sviluppatore da lui ingaggiato.
**Livello stimato**: L1-L2 (tecnico con competenze Python, accesso al software installato).
**Motivazione**: Clonare il prodotto, bypassare licenza, estrarre patrimonio scientifico.
**Accesso**: Software installato su PC del partner (accesso completo ai file).

---

## Test Results

### TEST 1: PyInstaller Bundle Analysis — FAIL

**Cosa**: Analisi della struttura del bundle distribuito.

| Metrica | Valore |
|---------|--------|
| Dimensione bundle | 105 MB |
| Cipher PyInstaller | **None** (zero cifratura) |
| PyInstaller magic | Trovato a offset -88 da EOF |
| base_library.zip | 155 file .pyc (stdlib) |
| .pyc nel bundle | 33 file (migrations compilate) |
| .py in chiaro | **31 file** (migrations + alembic env) |

**TTC**: 30 secondi con `pyinstxtractor` per estrarre tutto il bytecode dal .exe.

**Evidenza**:
```
fitmanager.exe: 16,126,513 bytes
PyInstaller magic found at offset -88
→ Estraibile con pyinstxtractor in ~30 secondi
```

**Verdetto**: **FAIL** — zero protezione sull'archivio PyInstaller.

---

### TEST 2: Database Cataloghi — FAIL CRITICO

**Cosa**: Accesso diretto ai database SQLite shipped con l'installer.

#### catalog.db (3.2 MB)
| Tabella | Righe | Contenuto |
|---------|-------|-----------|
| esercizi | **500** | 43 colonne: nome, biomeccanica, coaching cues, errori, sicurezza, demand vector 10D |
| esercizi_muscoli | **7.955** | Relazioni esercizio-muscolo (EMG data) |
| esercizi_condizioni | **6.020** | Controindicazioni per condizione medica |
| esercizi_articolazioni | **1.605** | Stress articolare per esercizio |
| esercizi_media | **750** | Riferimenti a foto/video |
| esercizi_relazioni | **894** | Progressioni e varianti |
| muscoli | 53 | Tassonomia muscolare completa |
| condizioni_mediche | 47 | Condizioni del Safety Engine |
| articolazioni | 15 | Tassonomia articolazioni |

#### nutrition.db (450 KB)
| Tabella | Righe | Contenuto |
|---------|-------|-----------|
| alimenti | **880** | Dati CREA 2019 completi (kcal, macro, micro) |
| porzioni_standard | **1.610** | Porzioni LARN per alimento |
| ricette_pietanze | **512** | Composizione pietanze |
| plan_templates | **12** | Template dieta LARN (8 con dieta completa) |
| template_plan_meals | **280** | Pasti per template |
| template_plan_components | **784** | Componenti per pasto |

**TTC**: **5 secondi** — aprire con DB Browser for SQLite, qualsiasi client SQLite, o `sqlite3` CLI.

**Evidenza**:
```
sqlite3 catalog.db "SELECT * FROM esercizi LIMIT 1"
→ (1, 'Squat Bilanciere', 'Back Squat', 'compound', 'squat', 'push', ...)
→ TUTTE le 43 colonne leggibili, inclusi coaching_cues, demand vector, controindicazioni
```

**Verdetto**: **FAIL CRITICO** — l'intero patrimonio scientifico (costruito in mesi) accessibile in 5 secondi. Nessuna cifratura.

---

### TEST 3: Seed Data + Alembic Migrations — FAIL

**Cosa**: File JSON e migrations Python distribuiti IN CHIARO nel bundle.

#### Seed JSON (4 MB totali nel bundle)
```
_internal/data/exercises/seed_exercises.json        ← 500 esercizi completi
_internal/data/exercises/seed_exercise_media.json    ← 750 riferimenti media
_internal/data/exercises/seed_exercise_progressions.json
_internal/data/exercises/seed_exercise_relations.json  ← 894 relazioni
```

#### Alembic Migrations (30 file .py in chiaro)
```
_internal/alembic/versions/
  ├── 05243b21aca1_add_communication_log_table.py     ← schema communication_log
  ├── 949f3f3fd5ed_add_taxonomy_schema.py              ← schema tassonomia
  ├── f3f3eedfebd0_add_workout_plan_tables.py          ← schema schede
  ├── a9f1e2b3c4d5_add_nutrition_plans_tables.py       ← schema nutrizione
  └── ... (30 file totali)
```

**TTC**: **0 secondi** — i file sono in chiaro, leggibili con un text editor.

**Evidenza** (campione migration):
```python
# Espone COMPLETAMENTE lo schema crm.db:
op.create_table('communication_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('trainer_id', sa.Integer(), nullable=False),
    sa.Column('id_cliente', sa.Integer(), nullable=False),
    sa.Column('canale', sa.String(), nullable=False),
    ...
```

**Verdetto**: **FAIL** — schema completo del database business esposto in chiaro. Un competitor può ricostruire l'intero modello dati in 15 minuti.

---

### TEST 4: String Extraction — PASS PARZIALE

**Cosa**: Estrazione stringhe sensibili dal binario .exe.

| Target | Trovato? | Note |
|--------|----------|------|
| EMBEDDED_PUBLIC_KEY | No nel .exe | È nel PYZ bytecode (richiede decompilazione) |
| Module names (api.services.xxx) | No nel .exe | Compilati nel PYZ |
| training_science | No nel .exe | Idem |
| JWT_SECRET / password | No nel .exe | Non hardcoded |

**TTC**: N/A per strings dirette. Ma dopo decompilazione PYZ (TEST 1), tutto diventa leggibile.

**Verdetto**: **PASS parziale** — le stringhe non sono in chiaro nel .exe, ma sono nel bytecode decompilabile.

---

### TEST 5: Frontend Build — PASS

**Cosa**: Esposizione codice sorgente dal bundle Next.js standalone.

| Metrica | Valore |
|---------|--------|
| Source maps nel standalone | 32 (tutti stub vuoti: `{"sources":[],"sections":[]}`) |
| Source maps static (client JS) | 1 (solo polyfill, irrilevante) |
| Sorgente TypeScript recuperabile | **No** |
| WhatsApp templates nei chunk | 7 chunk (stringhe leggibili ma contesto perso) |
| Route manifest | Espone 34 route (basso impatto — route sono auth-protected) |

**TTC**: 1-2 giorni per ricostruire logica business da JS minificato. Impraticabile per replicare.

**Verdetto**: **PASS** — il frontend è adeguatamente protetto dalla minificazione. Source map vuote nel standalone.

---

### TEST 6: License Bypass Vectors — PASS CONDIZIONATO

**Cosa**: Facilità di trovare e patchare il sistema di licenza.

| Vettore | Stato | Note |
|---------|-------|------|
| Chiave pubblica in .pem | Non nel bundle | ADR-005: embedded in bytecode, file ignorato |
| Hash chiave in chiaro | Non trovato in grep | È nel PYZ bytecode compilato |
| LICENSE_ENFORCEMENT bypass | Bloccato | sys.frozen → always ON |
| Fingerprint bypass | Bloccato | Fail-closed in frozen mode |

**MA**: dopo decompilazione PYZ (TEST 1), la chiave pubblica e l'hash sono in chiaro nel sorgente Python ricostruito. Patch entrambi → auto-firma licenze.

**TTC**: 1-2 ore (30s estrazione + 30min decompilazione + 30min patch + test).

**Verdetto**: **PASS condizionato** — ADR-005 è solido SE il bytecode non è decompilabile. Crolla se TEST 1 fallisce (e fallisce).

---

### TEST 7: Decompilation Surface — FAIL

**Cosa**: Superficie totale di codice estraibile dal bundle.

| Categoria | File | Stato |
|-----------|------|-------|
| .py sorgente in chiaro | 31 | Migrations Alembic + env.py |
| .pyc compilati (decompilabili) | 33 | Migrations compilate |
| base_library.zip (.pyc stdlib) | 155 | Standard library |
| PYZ archive (codice app) | **TUTTO api/** | Estraibile con pyinstxtractor |
| Seed JSON | 4 file, 4 MB | Esercizi completi in chiaro |

**Attacco completo**:
```
1. pyinstxtractor fitmanager.exe          → 30 secondi
2. decompyle3 api/*.pyc                   → 5-10 minuti
3. Risultato: 100% del codice Python leggibile
   - Training Science Engine (9K LOC)
   - Nutrition Science Engine (2.5K LOC)
   - Safety Engine (80 rules)
   - Contract Integrity (12 livelli)
   - Tutti i router, modelli, servizi
```

**TTC**: **< 15 minuti** per un L2 con pyinstxtractor + decompyle3.

**Verdetto**: **FAIL** — il codice proprietario è completamente recuperabile.

---

## Matrice Riassuntiva

| # | Test | Target | TTC Attuale | TTC Target (L2) | Verdetto |
|---|------|--------|-------------|------------------|----------|
| 1 | PyInstaller bundle | Bytecode Python | **30 sec** | > 4 ore | **FAIL** |
| 2 | Database cataloghi | Patrimonio scientifico | **5 sec** | > 1 ora | **FAIL CRITICO** |
| 3 | Seed + Migrations | Schema + dati esercizi | **0 sec** | > 1 ora | **FAIL** |
| 4 | String extraction | Stringhe sensibili | N/A (post-PYZ) | N/A | PASS parziale |
| 5 | Frontend build | Codice TypeScript | 1-2 giorni | 1-2 giorni | **PASS** |
| 6 | License bypass | Sistema licenza | **1-2 ore** | > 8 ore | PASS condizionato |
| 7 | Decompilation | Codice proprietario | **< 15 min** | > 1 giorno | **FAIL** |

---

## Gap Analysis — Anelli di Protezione

| Anello | Descrizione | Stato | Gap |
|--------|-------------|-------|-----|
| 1. Legal | NDA + non-compete + penale | **NON FIRMATO** | Bloccante per consegna |
| 2. Licensing | JWT RS256 + HW binding | Buono (ADR-005) | OK se bytecode protetto |
| 3. Integrity | Verifica integrità binario | Minimale (hash chiave) | Serve CRC/self-hash |
| 4. Obfuscation | Codice illeggibile | **ASSENTE** | Serve PyArmor o Nuitka |
| 5. Virtualization | Compilazione nativa | **ASSENTE** | Nuitka elimina il vettore |
| 6. Environmental | Anti-debug runtime | **ASSENTE** | Bassa priorità per L2 |

---

## Crown Jewels Exposure Map

| Crown Jewel | LOC | Dove si trova | TTC estrazione |
|-------------|-----|---------------|----------------|
| Training Science Engine | ~9.000 | PYZ → api/services/training_science/ | 15 min |
| Nutrition Science Engine | ~2.500 | PYZ → api/services/nutrition_science/ | 15 min |
| Safety Engine (80 rules) | ~250 | PYZ → api/services/condition_rules.py | 15 min |
| Catalogo 500 esercizi | 500 righe × 43 col | catalog.db (SQLite in chiaro) | 5 sec |
| Demand Vector 10D | parte di esercizi | catalog.db + PYZ | 5 sec |
| 880 alimenti CREA | 880 righe | nutrition.db (SQLite in chiaro) | 5 sec |
| 12 template LARN | 12 + 280 + 784 righe | nutrition.db | 5 sec |
| Schema business (26 tab) | 30 migration | _internal/alembic/ (plaintext .py) | 0 sec |
| Contract Integrity Engine | ~500 | PYZ → api/services/ | 15 min |
| EMG Matrix 18×15 | parte di training_science | PYZ | 15 min |

---

## Raccomandazioni Prioritizzate

### P0 — Bloccanti (prima della consegna)

1. **NDA + clausola non-compete + penale** firmati
2. **Cifratura catalog.db e nutrition.db** (SQLCipher o AES at-rest)
3. **Rimozione migrations Alembic dal bundle** (eseguire pre-build, non distribuire)
4. **Rimozione seed JSON dal bundle** (dati già in catalog.db, non servono nel bundle distribuito)

### P1 — Critici (entro prima release pubblica)

5. **Nuitka compilation** del backend (Python → C → binario nativo, non decompilabile)
6. **PyArmor** come alternativa rapida se Nuitka richiede troppo tempo
7. **Rimozione/cifratura seed_exercises.json** dal bundle distribuito

### P2 — Importanti (entro 50 clienti)

8. **Code signing Authenticode** (tamper detection a livello OS)
9. **License revocation list** (bloccare licenze compromesse)
10. **Self-integrity check** (CRC32 su sezioni critiche del binario)

### P3 — Futuri (se emerge piracy)

11. **Anti-debug runtime** (rilevamento Frida, debugger attach)
12. **License server** opzionale (phone-home periodico)
13. **Code virtualization** su Crown Jewels (VMProtect-like)

---

## Note Metodologiche

Questo audit segue il framework:
- **Threat Modeling**: 5 livelli attaccante (L0-L4), target L2
- **Measurement**: Time-to-Crack (TTC) per Crown Jewel
- **Layered Defense**: 6 anelli (Legal → Licensing → Integrity → Obfuscation → Virtualization → Environmental)
- **Skill di riferimento**: `anti-reversing-techniques` (3.5K install), `ctf-reverse` (1.1K install)
- **Standard di riferimento**: OWASP MASVS-R (adattato da mobile a desktop)

Il re-test post-hardening sarà documentato in `SECURITY_AUDIT_POST_HARDENING.md`.
