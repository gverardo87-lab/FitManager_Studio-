# ADR-009 — Portale Cliente Interattivo: Scheda Allenamento Self-Tracking

- Date: 2026-03-29
- Status: accepted
- Deciders: gvera
- Related: ADR-003 (3 DB), ADR-005 (license hardening), ADR-008 (builder full-screen), Tailscale Funnel

## Context

FitManager ha un portale pubblico funzionante (`/public/anamnesi/[token]`) per la compilazione self-service dell'anamnesi. Il pattern e' provato in produzione: share token UUID4, rate-limit IP, name masking, Tailscale Funnel.

**Il problema**: l'aderenza alla scheda allenamento e' oggi un compito del trainer. Il trainer deve chiedere al cliente cosa ha fatto, inserire i dati manualmente, e verificare la compliance. Questo:

1. **Scala male**: con 15-30 clienti attivi, il tracking manuale diventa insostenibile
2. **Perde dati**: il cliente dimentica carichi e sensazioni dopo 24h
3. **Non differenzia**: qualsiasi PT puo' dare un PDF — nessuno da' una scheda interattiva
4. **Spreca il motore**: il sistema di schedule (`workout_schedule` + `allenamenti_eseguiti`) esiste ma e' alimentato solo dal trainer

**L'insight strategico**: il primo a voler inserire i dati e' il cliente stesso. Sapere che il proprio PT ha un sistema professionale di tracking e' il vero motore del word-of-mouth. Il cliente "vive" l'esperienza del PT evoluto, non la subisce.

## Decision Drivers

1. **Il cliente e' il data-entry naturale**: logga i propri dati a fine sessione, quando ha carico e sensazioni fresche
2. **Il pattern esiste gia'**: share token + Tailscale Funnel + public route sono in produzione
3. **Il modello dati e' quasi pronto**: `esercizi_sessione` ha serie/reps/carico pianificati, mancano solo i campi "actual"
4. **Marketing organico**: il cliente che usa il portale e' un ambassador naturale — mostra il sistema agli amici in palestra
5. **Valore percepito**: la scheda interattiva giustifica il premium del trainer che usa FitManager
6. **Privacy-first**: i dati restano sul PC del trainer, il cliente accede via Tailscale (zero cloud terzi)

## Considered Options

### Option A — Estensione del portale anamnesi (token monouso)

- Pro: riuso totale del pattern esistente, zero nuovi modelli
- Contro: token monouso = il cliente deve chiedere un nuovo link ogni giorno. Insostenibile. L'anamnesi si compila 1 volta, la scheda si usa ogni giorno per 4-8 settimane.

### Option B — Portale dedicato con token multi-uso a scadenza (scelta)

- Pro: un link per tutta la durata della scheda. Il cliente salva il bookmark. Token con scadenza allineata a `data_fine` della scheda + 7 giorni di grace. Riuso del 90% dell'infrastruttura (route, rate-limit, masking).
- Contro: richiede estensione del modello ShareToken (scope, multi-uso). Serve nuova tabella per i dati actual per-esercizio.

### Option C — Login cliente con credenziali

- Pro: autenticazione completa, sessione persistente
- Contro: over-engineering per il caso d'uso. Il trainer dovrebbe gestire credenziali per ogni cliente. Complessita' sproporzione. Il link e' piu' semplice e altrettanto sicuro (UUID4 = 122 bit entropy).

## Decision

**Option B — Portale dedicato con token multi-uso a scadenza.**

Il trainer genera un link per la scheda attiva del cliente. Il cliente accede da smartphone, vede le sessioni programmate, e dopo ogni allenamento inserisce i dati reali (serie, ripetizioni, carico effettivi + note). Il trainer vede tutto in tempo reale nella pagina aderenza.

---

## Architettura

### 1. Flusso utente

```
TRAINER (dashboard)                          CLIENTE (smartphone)
─────────────────                            ─────────────────────
1. Crea scheda + schedule
2. Click "Condividi con cliente"
3. Copia link / invia via WhatsApp ────────> 4. Apre link (Tailscale HTTPS)
                                             5. Vede sessioni programmate
                                             6. Dopo l'allenamento:
                                                - Seleziona sessione del giorno
                                                - Per ogni esercizio:
                                                  [serie_eff] × [reps_eff] @ [carico_eff]
                                                  + note facoltative
                                                - Click "Salva sessione"
                                             7. Vede aderenza aggiornata

8. Vede dati reali in pagina aderenza  <──── (dati salvati su crm.db)
9. Vede note cliente per esercizio
10. Compliance calcolata automaticamente
```

### 2. URL e routing

```
https://nome.ts.net/public/scheda/{token}

Frontend: /public/scheda/[token]/page.tsx

Backend:
  POST   /clients/{client_id}/share-workout              (trainer, genera token)
  GET    /api/public/workout/validate?token={token}       (pubblico, valida token)
  GET    /api/public/workout/sessions?token={token}       (pubblico, lista sessioni + schedule)
  GET    /api/public/workout/session/{slot_id}/exercises?token={token}  (pubblico, esercizi della sessione)
  POST   /api/public/workout/session/{slot_id}/log        (pubblico, salva dati actual)
```

### 3. Diagramma architetturale

```
Cliente (smartphone, 4G/WiFi)
  │
  │ HTTPS (Tailscale Let's Encrypt)
  ↓
┌─────────────────────────────────────────────────────────┐
│  Tailscale Funnel → porta 3000 (Next.js)                │
│                                                         │
│  /public/scheda/[token]                                 │
│  ┌───────────────────────────────────────────────────┐  │
│  │  ┌─ Header ─────────────────────────────────┐     │  │
│  │  │  🏋️ Scheda: "Full Body 3x"  │  Marco R.  │     │  │
│  │  │  Aderenza: ████████░░ 8/12 (67%)         │     │  │
│  │  └──────────────────────────────────────────┘     │  │
│  │                                                   │  │
│  │  ┌─ Sessione odierna ───────────────────────┐     │  │
│  │  │  Sessione A — Lunedi 31 Marzo            │     │  │
│  │  │                                          │     │  │
│  │  │  1. Panca piana                          │     │  │
│  │  │     Programmato: 3×10 @ 60kg             │     │  │
│  │  │     Eseguito:  [3]×[10] @ [62] kg  ✓    │     │  │
│  │  │     Note: [ultimo set faticoso____]      │     │  │
│  │  │                                          │     │  │
│  │  │  2. Rematore bilanciere                  │     │  │
│  │  │     Programmato: 4×8 @ 40kg              │     │  │
│  │  │     Eseguito:  [_]×[_] @ [_] kg         │     │  │
│  │  │     Note: [________________________]     │     │  │
│  │  │                                          │     │  │
│  │  │  3. Squat                                │     │  │
│  │  │     Programmato: 4×6 @ 80kg              │     │  │
│  │  │     Eseguito:  [_]×[_] @ [_] kg         │     │  │
│  │  │     Note: [________________________]     │     │  │
│  │  │                                          │     │  │
│  │  │        [💾 Salva sessione]               │     │  │
│  │  └──────────────────────────────────────────┘     │  │
│  │                                                   │  │
│  │  ┌─ Prossime sessioni ─────────────────────┐     │  │
│  │  │  ○ Mer 02 Apr — Sessione B (Upper)      │     │  │
│  │  │  ○ Ven 04 Apr — Sessione C (Lower)      │     │  │
│  │  │  ● Lun 07 Apr — Sessione A (Full Body)  │     │  │
│  │  └──────────────────────────────────────────┘     │  │
│  │                                                   │  │
│  │  ┌─ Sessioni completate ───────────────────┐     │  │
│  │  │  ✓ Lun 24 Mar — Sessione A  ──> dettagli│     │  │
│  │  │  ✓ Mer 26 Mar — Sessione B  ──> dettagli│     │  │
│  │  │  ✗ Ven 28 Mar — Sessione C  (saltata)   │     │  │
│  │  └──────────────────────────────────────────┘     │  │
│  └───────────────────────────────────────────────────┘  │
│       │                                                 │
│       ↓ POST /api/public/workout/session/{slot_id}/log  │
│  ┌──────────────────────────────────────────────────┐   │
│  │  FastAPI (public endpoints, rate-limited)         │   │
│  │  → Valida token (scope=workout, non scaduto)      │   │
│  │  → Salva ExerciseLog per ogni esercizio           │   │
│  │  → Aggiorna slot.stato = completato               │   │
│  │  → Crea WorkoutLog (record esecuzione)            │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 4. Data model changes

#### 4a. Nuova tabella: `exercise_logs` (crm.db)

Dati effettivi per-esercizio inseriti dal cliente. Separata da `esercizi_sessione` per non inquinare il piano del trainer.

```
exercise_logs
├── id                  INT PK
├── id_schedule_slot    INT FK → workout_schedule.id   (quale slot)
├── id_esercizio_sessione INT FK → esercizi_sessione.id (quale esercizio del piano)
├── serie_effettive     INT?                            (NULL = non compilato)
├── ripetizioni_effettive STR?                          (es. "10,10,8" o "10")
├── carico_effettivo_kg FLOAT?                          (NULL = bodyweight)
├── rpe                 FLOAT?                          (0-10, percezione sforzo)
├── note_cliente        STR?                            (feedback libero)
├── created_at          DATETIME
├── updated_at          DATETIME
└── deleted_at          DATETIME?                       (soft delete)
```

**Perche' tabella separata** (non campi su `esercizi_sessione`):
- `esercizi_sessione` e' il PIANO del trainer — sacro, immutabile dal cliente
- Un esercizio puo' avere N log (se la scheda cicla: stessa sessione ripetuta settimana dopo settimana)
- Relazione: 1 esercizio_sessione → N exercise_logs (1 per ogni slot in cui viene eseguito)
- Il trainer puo' confrontare l'evoluzione dello stesso esercizio nel tempo

#### 4b. Estensione ShareToken: scope "workout"

```python
# Nuovi valori scope:
scope: "anamnesi"  # esistente — monouso, 48h
scope: "workout"   # NUOVO — multi-uso, scadenza = data_fine scheda + 7gg

# Nuovi campi:
id_scheda: Optional[int]  # FK → schede_allenamento.id (solo per scope=workout)
```

**Token lifecycle per scope=workout**:
- Generato dal trainer: `POST /clients/{client_id}/share-workout`
- Scadenza: `workout.data_fine + 7 giorni` (grace period)
- Multi-uso: `used_at` NON viene settato al primo accesso
- Revocabile: il trainer puo' eliminarlo
- 1 token attivo per scheda (generarne uno nuovo invalida il precedente)

#### 4c. Schema completo relazioni

```
WorkoutPlan (schede_allenamento)
  ├── WorkoutSession (sessioni_scheda)
  │     ├── SessionBlock (blocchi_sessione)
  │     │     └── WorkoutExercise (esercizi_sessione)
  │     │           └── ExerciseLog (exercise_logs) ← NUOVO, N per slot
  │     └── WorkoutExercise (straight, no block)
  │           └── ExerciseLog (exercise_logs) ← NUOVO, N per slot
  │
  ├── WorkoutScheduleSlot (workout_schedule)
  │     ├── WorkoutLog (allenamenti_eseguiti) — via id_log FK
  │     └── ExerciseLog (exercise_logs) — via id_schedule_slot FK ← NUOVO
  │
  └── ShareToken (share_tokens) — via id_scheda FK ← NUOVO campo
```

### 5. API Endpoints

#### 5a. Endpoint protetti (trainer)

```
POST /clients/{client_id}/share-workout
  Body: { "id_scheda": int }
  Response: { "token": str, "url": str, "expires_at": datetime, "client_name": str }
  Logic:
    1. Bouncer: client.trainer_id == trainer.id
    2. Bouncer: workout.trainer_id == trainer.id AND workout.id_cliente == client_id
    3. Verifica: workout ha schedule generato (almeno 1 slot)
    4. Verifica: workout.data_fine esiste
    5. Invalida token precedente per stessa scheda
    6. Crea token: scope="workout", expires_at = workout.data_fine + 7gg, id_scheda = workout.id
    7. Genera URL con PUBLIC_BASE_URL
```

#### 5b. Endpoint pubblici (cliente, rate-limited)

```
GET /api/public/workout/validate?token={token}
  Response: {
    "client_name": "Marco R.",
    "trainer_name": "Chiara B.",
    "workout_name": "Full Body 3x Settimana",
    "data_inizio": "2026-04-01",
    "data_fine": "2026-04-21",
    "sessioni_per_settimana": 3,
    "total_slots": 9,
    "completed_slots": 3,
    "scope": "workout"
  }

GET /api/public/workout/sessions?token={token}
  Response: {
    "slots": [
      {
        "id": 1,
        "data_pianificata": "2026-04-01",
        "stato": "completato",
        "sessione_nome": "Sessione A — Full Body",
        "focus_muscolare": "full body",
        "has_log": true
      },
      {
        "id": 2,
        "data_pianificata": "2026-04-03",
        "stato": "pianificato",
        "sessione_nome": "Sessione B — Upper",
        "focus_muscolare": "upper body",
        "has_log": false
      }
    ]
  }

GET /api/public/workout/session/{slot_id}/exercises?token={token}
  Response: {
    "slot_id": 2,
    "data_pianificata": "2026-04-03",
    "stato": "pianificato",
    "sessione_nome": "Sessione B — Upper",
    "exercises": [
      {
        "id": 15,                          # esercizi_sessione.id
        "nome_esercizio": "Panca piana",   # da catalog.db
        "gruppo_muscolare": "Pettorali",   # da catalog.db
        "ordine": 1,
        "serie": 3,
        "ripetizioni": "10",
        "carico_kg": 60.0,
        "tempo_riposo_sec": 90,
        "note_trainer": "Controllare gomiti",
        "blocco_nome": null,               # null = straight set
        "log": null                         # null = non ancora compilato
        # oppure:
        # "log": {
        #   "serie_effettive": 3,
        #   "ripetizioni_effettive": "10,10,8",
        #   "carico_effettivo_kg": 62.0,
        #   "rpe": 8.5,
        #   "note_cliente": "Ultimo set faticoso"
        # }
      }
    ]
  }

POST /api/public/workout/session/{slot_id}/log
  Body: {
    "token": str,
    "exercises": [
      {
        "id_esercizio_sessione": 15,
        "serie_effettive": 3,
        "ripetizioni_effettive": "10,10,8",
        "carico_effettivo_kg": 62.0,
        "rpe": 8.5,
        "note_cliente": "Ultimo set faticoso"
      }
    ],
    "note_sessione": "Buona sessione, energia alta"
  }
  Response: { "success": true, "message": "Sessione salvata! 💪", "completion_pct": 44 }
  Logic:
    1. Valida token (scope=workout, non scaduto)
    2. Verifica slot appartiene alla scheda del token
    3. Verifica slot.data_pianificata <= oggi + 1 (non loggare sessioni future lontane)
    4. Per ogni esercizio: crea/aggiorna ExerciseLog (upsert per slot+esercizio)
    5. Crea WorkoutLog se non esiste per questo slot
    6. Aggiorna slot.stato = "completato" (o "parziale" se non tutti compilati)
    7. Commit atomico
```

### 6. Frontend: pagina pubblica

```
/public/scheda/[token]/page.tsx

Componenti:
├── WorkoutPortalHeader       # Nome scheda, nome cliente (masked), barra aderenza
├── TodaySession              # Sessione odierna (o prossima) con form interattivo
│   └── ExerciseLogForm       # Per-esercizio: inputs serie/reps/carico + note + RPE slider
├── UpcomingSessions          # Lista prossime sessioni (read-only, countdown)
├── CompletedSessions         # Storico con accordion espandibile per dettagli
└── WorkoutPortalFooter       # "Powered by FitManager" + link trainer
```

**UX principles**:
- **Mobile-first**: 100% del traffico sara' da smartphone
- **Pre-fill smart**: i campi "actual" pre-compilati col valore pianificato. Il cliente modifica solo cio' che differisce.
- **Salvataggio parziale**: il cliente puo' salvare anche se non compila tutti gli esercizi (stato = "parziale")
- **Feedback immediato**: dopo il salvataggio, barra aderenza si aggiorna + messaggio motivazionale
- **Zero login**: il link e' l'autenticazione. Bookmark-friendly.
- **Offline-resilient**: se il salvataggio fallisce, mostrare messaggio chiaro con retry

### 7. Sicurezza

| Layer | Controllo | Dettaglio |
|-------|-----------|-----------|
| **Token** | Multi-uso, scadenza scheda | Non monouso, ma scadenza = data_fine + 7gg |
| **Rate limit** | IP-based | 10 req/min, 30 req/h (stesso dell'anamnesi) |
| **Scope isolation** | Token lega a 1 scheda | Il cliente vede SOLO la scheda associata al token |
| **Write scope** | Solo ExerciseLog | Il cliente puo' SOLO creare/aggiornare i propri log. Mai modificare piano, sessioni, esercizi |
| **Time guard** | data_pianificata <= oggi + 1 | Non puo' loggare sessioni future lontane |
| **Name masking** | Cognome iniziale | "Marco R." (come anamnesi) |
| **No PII in URL** | Solo token UUID4 | Nessun ID cliente o trainer nell'URL |
| **Audit** | Log su ogni write | Tracciabilita' completa |

### 8. Impatto sulla pagina aderenza del trainer

La pagina aderenza esistente (trainer-side) mostra gia' `workout_schedule` slots. Con questa feature:

- **Nuova colonna/indicatore**: "Compilato dal cliente" (badge) vs "Segnato dal trainer"
- **Dettaglio per-esercizio**: click su slot completato → vede serie/reps/carico effettivi + note cliente
- **Delta visualizzato**: differenza tra pianificato e actual (es. "+2kg", "-2 reps")
- **Note cliente in evidenza**: il trainer legge il feedback del cliente inline
- **Source badge**: distinguere "compilato da cliente" vs "segnato da trainer" (campo `source` su ExerciseLog)

### 9. Template WhatsApp

Nuovo template `waWorkoutPortal`:

```
Ciao {nome}! 🏋️

La tua scheda "{nomeScheda}" e' pronta con il calendario delle sessioni.

Dopo ogni allenamento, apri questo link e inserisci i tuoi dati:
{url}

Il link e' valido fino al {dataFine}. Buon allenamento!

— {firma}
```

---

## Implementation Plan

### Fase 1 — Backend (2 step)

**Step 1: Migrazione + Modelli**
- [ ] Creare modello `ExerciseLog` in `api/models/exercise_log.py`
- [ ] Aggiungere campo `id_scheda` a `ShareToken`
- [ ] Migrazione Alembic: `exercise_logs` table + `share_tokens.id_scheda` column
- [ ] Aggiornare `_delete_sessions_cascade` per includere `exercise_logs`
- [ ] Aggiornare `create_db_and_tables()` se necessario

**Step 2: Endpoint pubblici**
- [ ] Estendere `api/routers/public_portal.py` con 4 endpoint workout
- [ ] Creare schemas in `api/schemas/public.py` (workout validate/sessions/exercises/log)
- [ ] Endpoint trainer: `POST /clients/{client_id}/share-workout`
- [ ] Token multi-uso logic (no `used_at` set on access)
- [ ] Cross-DB query: nome esercizio + gruppo muscolare da catalog.db

### Fase 2 — Frontend (2 step)

**Step 3: Pagina pubblica cliente**
- [ ] `/public/scheda/[token]/page.tsx` — pagina mobile-first
- [ ] Componenti: header, today session, exercise form, upcoming, completed
- [ ] Pre-fill smart, salvataggio parziale, feedback motivazionale
- [ ] Rate-limit error handling, offline-resilient UX

**Step 4: Integrazione trainer-side**
- [ ] Pulsante "Condividi con cliente" nel builder/aderenza
- [ ] Template WhatsApp `waWorkoutPortal`
- [ ] Badge "compilato dal cliente" nella pagina aderenza
- [ ] Dettaglio per-esercizio con delta (planned vs actual)

### Fase 3 — Quality gate

- [ ] Test backend: token multi-uso, scope workout, exercise log CRUD, cascade delete
- [ ] Test frontend: vitest per pagina pubblica
- [ ] `bash tools/scripts/check-all.sh`
- [ ] Test manuale end-to-end via Tailscale Funnel

---

## Consequences

### Positive

- **Il cliente diventa data-entry**: il trainer risparmia 5-10 min per cliente per sessione
- **Dati piu' accurati**: il cliente logga subito dopo, non a memoria il giorno dopo
- **Marketing organico**: il cliente mostra il sistema in palestra → word-of-mouth
- **Valore percepito**: scheda interattiva >> PDF statico
- **Compliance automatica**: zero calcolo manuale, il sistema sa chi ha fatto cosa
- **Riuso infrastruttura**: 90% del pattern gia' in produzione (token, funnel, rate-limit)

### Negative

- **Dipendenza Tailscale**: senza Funnel attivo, il cliente non accede (mitigato: FitManager Box in roadmap)
- **PC trainer deve essere acceso**: il server e' locale (mitigato: FitManager Box always-on)
- **Token sharing**: il cliente potrebbe condividere il link (mitigato: il link mostra solo la propria scheda, dati non sensibili a parte il nome mascherato)

### Follow-up actions

- Aggiungere `ExerciseLog` al cascade delete (pitfall #10)
- Aggiornare CLAUDE.md con il nuovo pattern
- Valutare notifica push al trainer quando il cliente compila (fase futura)
- Valutare grafici progressione carico nel tempo (fase futura)
- Template WhatsApp con deep-link diretto alla sessione del giorno (fase futura)

## Rollback / Exit Strategy

- La feature e' completamente opt-in: il trainer deve generare il link
- Se disattivata: basta non generare token scope=workout. I dati ExerciseLog restano in crm.db
- La tabella `exercise_logs` non ha impatto sulle tabelle esistenti (additive only)
- Il campo `id_scheda` su ShareToken e' nullable (backwards-compatible)

## Supersedes / Superseded By

- Supersedes: nessuno
- Superseded by: nessuno
