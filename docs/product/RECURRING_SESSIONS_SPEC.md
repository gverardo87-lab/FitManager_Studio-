# Sedute Ricorrenti — Specifica Tecnica

> **Stato**: Approvato | **Priorita'**: Alta | **Richiesto da**: Chiara Bassani
> **Data**: 2026-04-09 | **Versione**: 1.0

---

## 1. Problema

I clienti nel settore fitness prediligono schemi settimanali fissi dovuti a impegni lavorativi e familiari (es. "tutti i martedi e venerdi perche' il figlio e' a scuola fino alle 16"). Attualmente ogni seduta in agenda va creata manualmente — un processo ripetitivo e soggetto a errori per il trainer.

## 2. Benchmark competitivo

| Piattaforma | Ricorrenza | Modello | Preview conflitti | Warning crediti |
|-------------|-----------|---------|-------------------|-----------------|
| **Mindbody** | Weekly/biweekly/monthly | Edit Series (iCal-like) | Si | Si |
| **PTminder** | Weekly/biweekly/monthly | Batch Generate | Si | Si |
| **My PT Hub** | Weekly/biweekly | Batch Generate | No | Si |
| **Vagaro** | Daily/weekly/biweekly/monthly | Edit Series | Si | Si |
| **Glofox** | Weekly/biweekly | Program-linked | No | No |
| **Trainerize** | Weekly/biweekly | Program-linked | No | No |
| **Acuity** | Every N days/weeks/months | Edit Series | Si | Si |

**Conclusione**: i CRM piu' adatti a PT singoli (PTminder, My PT Hub) usano il modello **Batch Generate** — genera N eventi concreti indipendenti da un pattern. Semplice, nessuna complessita' iCalendar, pieno controllo su ogni singola seduta.

## 3. Soluzione: "Pianifica Ricorrenza"

### 3.1 Modello architetturale

**Batch Generate** allineato al pattern esistente di `ScheduleSetupDialog` (workout schedule):

```
                          ┌─────────────────────────────────────┐
  RecurringEventDialog    │         POST /events/recurring      │
  ┌────────────────────┐  │                                     │
  │ 1. Configura       │──│─► mode: "preview"                  │
  │    - Cliente       │  │   → RecurringPreviewResponse        │
  │    - Giorni        │  │     (items, conflicts, credits)     │
  │    - Orario        │  │                                     │
  │    - Durata        │  │─► mode: "commit"                   │
  │                    │  │   → N x Event records               │
  │ 2. Preview         │  │     (gruppo_ricorrenza UUID)        │
  │    - Conflitti     │  │   → _sync_contract_chiuso()         │
  │    - Crediti       │  │   → log_audit() x N                │
  │                    │  │                                     │
  │ 3. Conferma        │  └─────────────────────────────────────┘
  └────────────────────┘
```

### 3.2 Principi di design

1. **Batch Generate, non Rules**: ogni seduta e' un `Event` indipendente. Modificabile, spostabile, cancellabile senza influenzare le altre.
2. **Preview server-side**: il backend calcola conflitti e crediti — il frontend non ha visibilita' completa sugli eventi esistenti.
3. **gruppo_ricorrenza UUID**: campo nullable che collega gli eventi della stessa serie. Abilita "Elimina futuri" e "Visualizza serie" senza schema aggiuntivi.
4. **Overlap batch ottimizzato**: 1 query per l'intero range temporale, match in Python — non N query individuali.
5. **Credit safety**: preview advisory, commit ri-verifica. `_sync_contract_chiuso()` chiamato UNA volta dopo tutti gli insert.

## 4. UX Flow

### 4.1 Wizard "Pianifica Ricorrenza" (target: 3-4 click)

**Step 1 — Configurazione**:
- Selettore cliente (Select con ricerca, come EventSheet)
- Categoria (PT / SALA / CORSO / COLLOQUIO / PERSONALE)
- Titolo seduta
- Giorni della settimana: toggle buttons L M M G V S D (pattern `ScheduleSetupDialog`)
- Orario: ora_inizio + ora_fine (input type="time")
- Durata — 3 modalita' radio:
  - "Per N settimane" + input numerico (1-52)
  - "Fino al [data]" + DatePicker
  - "Fino a esaurimento sedute" (solo PT + cliente con contratto attivo)

**Step 2 — Preview**:
- Lista scrollabile delle sedute generate
- Per ogni seduta: giorno della settimana + data + orario
- Badge conflitto (rosso) su sedute con sovrapposizione — dettaglio evento sovrapposto
- Summary bar: "N sessioni in N settimane"
- Banner warning crediti (amber): "Sedute rimanenti: 8 / Pianificate: 12"
- Banner conflitti (rosso): "3 sessioni con sovrapposizione (verranno saltate)"

**Step 3 — Conferma**:
- Bottone "Pianifica N sessioni" (disabilitato se 0 sessioni valide)
- Toast successo: "8 sessioni pianificate" + eventuale "2 sessioni saltate per sovrapposizione"
- Offerta WhatsApp: "Invia calendario al cliente" con template pre-compilato

### 4.2 Indicatori visivi in calendario

- Icona **Repeat** (lucide-react) accanto al titolo di eventi con `gruppo_ricorrenza`
- **EventSheet**: info banner "Questo evento fa parte di una serie di N sessioni" + bottone "Elimina sessioni future"

### 4.3 Gestione eccezioni

- Ogni evento e' indipendente: drag-and-drop, modifica orario, cancella singolarmente
- "Elimina sessioni future": soft-delete tutti gli eventi futuri con stato "Programmato" nello stesso gruppo
- Nessuna funzionalita' "Modifica tutti i futuri" in v1 (potenziale v2)

## 5. Specifiche tecniche

### 5.1 Data model

```python
# api/models/event.py — campo aggiunto
class Event(SQLModel, table=True):
    # ... campi esistenti ...
    gruppo_ricorrenza: Optional[str] = Field(default=None, index=True)
```

Migrazione Alembic: `ADD COLUMN gruppo_ricorrenza VARCHAR` + `CREATE INDEX ix_agenda_gruppo_ricorrenza`.

### 5.2 API Endpoints

#### `POST /events/recurring` — Genera sedute ricorrenti

**Request** (`RecurringEventRequest`):
```json
{
  "categoria": "PT",
  "titolo": "Personal Training",
  "id_cliente": 42,
  "id_contratto": null,
  "note": null,
  "ora_inizio": "16:00",
  "ora_fine": "17:00",
  "pattern_giorni": [1, 4],
  "data_inizio": "2026-04-14",
  "settimane": 4,
  "data_fine_ricorrenza": null,
  "fino_esaurimento": false,
  "mode": "preview"
}
```

**Response (preview)** (`RecurringPreviewResponse`):
```json
{
  "items": [
    {"data_inizio": "2026-04-15T16:00", "data_fine": "2026-04-15T17:00", "has_conflict": false, "conflict_detail": null},
    {"data_inizio": "2026-04-18T16:00", "data_fine": "2026-04-18T17:00", "has_conflict": true, "conflict_detail": "Sovrapposizione con PT Mario Rossi (16:00-17:00)"}
  ],
  "total": 8,
  "conflicts": 1,
  "crediti_rimasti": 10,
  "sessioni_pianificate": 8,
  "warning_crediti": null
}
```

**Response (commit)** (`RecurringCommitResponse`):
```json
{
  "created": 7,
  "skipped_conflicts": 1,
  "gruppo_ricorrenza": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "warning_crediti": null
}
```

#### `DELETE /events/group/{gruppo_id}` — Elimina sedute future del gruppo

Soft-delete tutti gli eventi con `gruppo_ricorrenza = gruppo_id`, `stato = "Programmato"`, `data_inizio > now`. Richiama `_sync_contract_chiuso()` per ogni contratto coinvolto.

### 5.3 Backend — Router separato

File: `api/routers/agenda_recurring.py` (~250 LOC)

Router separato per non gonfiare `agenda.py` (611 LOC). Montato con stesso prefix `/events` in `main.py`.

**Helper importati da `agenda.py`**:
- `_auto_assign_contract()` — logica FIFO crediti
- `_sync_contract_chiuso()` — auto-close/reopen contratto
- `_load_client_names_batch()` — batch load nomi clienti

**Ottimizzazione overlap batch**: 1 query per tutti gli eventi nel range `[min(data_inizio), max(data_fine)]`, poi check in Python:
```python
existing_events = session.exec(
    select(Event).where(
        Event.trainer_id == trainer.id,
        Event.data_inizio < max_data_fine,
        Event.data_fine > min_data_inizio,
        Event.stato != "Cancellato",
        Event.deleted_at == None,
    )
).all()
```

### 5.4 Frontend — Componenti

| Componente | File | LOC |
|-----------|------|-----|
| RecurringEventDialog | `components/agenda/RecurringEventDialog.tsx` | ~280 |
| Hook preview/commit/delete | `hooks/useAgenda.ts` | +60 |
| Icona repeat | `components/agenda/CustomEvent.tsx` | +5 |
| Banner serie | `components/agenda/EventSheet.tsx` | +20 |
| Bottone agenda | `app/(dashboard)/agenda/page.tsx` | +10 |
| Template WhatsApp | `lib/whatsapp-templates.ts` | +15 |
| Tipi API | `types/api.ts` | +30 |

### 5.5 Integrazione sistema crediti

| Scenario | Comportamento |
|----------|--------------|
| PT senza contratto esplicito | `_auto_assign_contract()` FIFO |
| Crediti sufficienti | Genera tutte le sessioni |
| Crediti insufficienti | Warning in preview, genera tutte comunque (il trainer decide) |
| "Fino a esaurimento" | Calcola `crediti_totali - crediti_usati`, genera esattamente quel numero |
| Ultimo credito consumato + SALDATO | `_sync_contract_chiuso()` chiude il contratto |
| Delete evento della serie | `_sync_contract_chiuso()` riapre se necessario |

### 5.6 Template WhatsApp

Nuovo template `waRecurringSchedule`:
```
Ciao {nome}! Ho pianificato le tue prossime {N} sessioni:

{lista_date}

Se hai bisogno di modificare qualcosa, contattami!

{firma_trainer}
```

## 6. File coinvolti

| File | Azione |
|------|--------|
| `api/models/event.py` | +1 campo `gruppo_ricorrenza` |
| `alembic/versions/xxxx_add_gruppo_ricorrenza.py` | **NUOVA** migrazione |
| `api/routers/agenda_recurring.py` | **NUOVO** router (~250 LOC) |
| `api/routers/agenda.py` | Export helper per import |
| `api/main.py` | Mount nuovo router |
| `frontend/src/types/api.ts` | +campo + nuovi tipi |
| `frontend/src/hooks/useAgenda.ts` | +3 hook |
| `frontend/src/components/agenda/RecurringEventDialog.tsx` | **NUOVO** (~280 LOC) |
| `frontend/src/app/(dashboard)/agenda/page.tsx` | +bottone + dialog state |
| `frontend/src/components/agenda/CustomEvent.tsx` | +icona repeat |
| `frontend/src/components/agenda/EventSheet.tsx` | +banner serie + delete futuri |
| `frontend/src/lib/whatsapp-templates.ts` | +1 template |
| `tests/test_recurring_events.py` | **NUOVO** (~12 test) |

## 7. Pattern riusati

| Pattern | Sorgente | Riuso |
|---------|----------|-------|
| Toggle giorni settimana | `ScheduleSetupDialog.tsx` | `GIORNI_SETTIMANA`, toggle buttons, preview |
| Credit guard FIFO | `agenda.py::_auto_assign_contract` | Assegnazione contratto automatica |
| Contract sync | `agenda.py::_sync_contract_chiuso` | Auto-close/reopen |
| Overlap detection | `agenda.py::_check_overlap` | Refactored per batch |
| Client selector | `EventSheet.tsx` | Select con ricerca |
| WhatsApp template | `whatsapp-templates.ts` | Struttura template |
| Bouncer pattern | Tutti i router | Ownership verification |

## 8. Rischi e mitigazioni

| Rischio | Impatto | Mitigazione |
|---------|---------|-------------|
| `agenda.py` troppo lungo | Manutenibilita' | Router separato `agenda_recurring.py` |
| N query overlap per N eventi | Performance | 1 query batch + match Python |
| Race condition crediti preview/commit | Overbooking | Commit ri-verifica crediti |
| Auto-close contratto durante batch | Chiusura prematura | `_sync_contract_chiuso()` UNA volta a fine batch |
| 52 settimane × 7gg = 364 INSERT | Performance SQLite | WAL mode, singolo commit atomico — nessun problema |

## 9. Test plan

### 9.1 Test automatici (`tests/test_recurring_events.py`, 12 test)

| # | Test | Verifica |
|---|------|----------|
| 1 | Preview basic | 3gg/sett x 4 sett = 12 items |
| 2 | Preview conflitti | Evento sovrapposto → `has_conflict=true` |
| 3 | Commit basic | N eventi con stesso `gruppo_ricorrenza` |
| 4 | Commit skip conflitti | Slot sovrapposto non creato |
| 5 | Credit warning | 5 crediti, 8 sessioni → warning |
| 6 | Fino esaurimento | Genera esattamente `crediti_rimasti` |
| 7 | Auto-assign FIFO | PT senza contratto → FIFO |
| 8 | Auto-close contract | Crediti esauriti post-batch → chiuso |
| 9 | Bouncer ownership | Cliente altrui → 404 |
| 10 | Mass assignment | `trainer_id` in payload → 422 |
| 11 | Delete future group | Soft-delete solo futuri Programmato |
| 12 | Empty pattern | 0 giorni selezionati → 422 |

### 9.2 Test manuali

1. Agenda → "Pianifica Ricorrenza" → cliente PT → Mar+Ven 16:00-17:00 × 4 settimane → preview → conferma → 8 eventi con icona repeat
2. Creare evento singolo, poi ricorrenza sovrapposta → preview conflitto rosso → commit skippa
3. Cliente con 3 crediti residui → "Fino a esaurimento" → genera 3 sessioni
4. Click evento serie → banner "Serie di N sessioni" → "Elimina futuri" → conferma → soft-delete
5. Drag-and-drop singolo evento della serie → si sposta senza influenzare gli altri

### 9.3 Regressione

- `pytest tests/ -v` — 349+ test pass (zero regressioni)
- `bash tools/scripts/check-all.sh` — ruff + next build clean
