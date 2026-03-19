# ADR-003: Separazione architetturale 3 database

**Data**: 2026-03-19
**Stato**: Accettata
**Autori**: gvera + Claude Opus 4.6

## Contesto

FitManager usa 3 database SQLite con ruoli distinti. Fino al 2026-03-19,
le tabelle esercizi e tassonomia erano **duplicate** in crm.db e catalog.db,
con dati divergenti e rischio di corruzione durante backup/restore.

Il modello nutrition.db era gia' correttamente separato (catalogo alimenti
read-only, piani alimentari in crm.db con cross-DB ref).

## Decisione

Adottare il pattern nutrition.db per TUTTI i cataloghi scientifici:

```
crm.db (SACRO — dati business del trainer)
├── 33 tabelle: clienti, contratti, rate, agenda, cassa, workout, piani alimentari
├── trainer_id su ogni tabella business (multi-tenant)
├── Backup/restore = vita del trainer. MAI inquinare con dati di catalogo.
├── Cross-DB ref senza FK: esercizi_sessione.id_esercizio → catalog.db
│                           componenti_pasto.alimento_id → nutrition.db
└── Alembic: include_name() ESCLUDE catalog + nutrition tables

catalog.db (READ-ONLY — shipped con installer)
├── 10 tabelle: esercizi (500), muscoli, articolazioni, condizioni_mediche,
│   metriche, esercizi_muscoli, esercizi_articolazioni, esercizi_condizioni,
│   esercizi_relazioni, esercizi_media
├── Zero trainer_id. Catalogo globale condiviso.
├── Aggiornato con upgrade dell'app (non dal trainer).
├── NO Alembic — costruito da ORM seed + script popolazione offline.
└── FK intra-catalog solo application-level (no constraint ORM)

nutrition.db (READ-ONLY — shipped con installer)
├── 8 tabelle: categorie_alimenti, alimenti, porzioni_standard,
│   ricette_pietanze, plan_templates, template_plan_meals, template_plan_components
├── Alembic separato: alembic_nutrition.ini con include_name()
└── Aggiornato con upgrade dell'app
```

## Conseguenze

### Positive
- **crm.db protetto**: backup/restore non tocca mai cataloghi scientifici
- **Zero duplicazione**: ogni tabella esiste in UN solo DB
- **Upgrade safe**: nuova versione sostituisce catalog.db e nutrition.db senza toccare crm.db
- **Alembic protetto**: `include_name()` impedisce creazione accidentale di tabelle catalog in crm.db
- **Pattern uniforme**: nutrition e catalog seguono lo stesso pattern (read-only, shipped, cross-DB ref)

### Negative
- **No FK constraint cross-DB**: integrity applicativa (router verifica esistenza prima di INSERT)
- **Esercizi custom non supportati** (feature futura): richiede tabella separata in crm.db
- **Script popolazione offline**: populate_taxonomy/conditions/demand scrivono in catalog.db, non piu' in crm.db

## Implementazione

### Session factory
```python
get_session()            # crm.db — business
get_catalog_session()    # catalog.db — esercizi + tassonomia
get_nutrition_session()  # nutrition.db — alimenti + template
```

### Protezioni
- `create_db_and_tables()`: esclude `CATALOG_TABLE_NAMES | NUTRITION_TABLE_NAMES`
- `schema_sync()`: esclude `_EXCLUDED_TABLE_NAMES = CATALOG + NUTRITION`
- `alembic/env.py`: `include_name()` esclude catalog + nutrition
- Seed al startup: `catalog_engine` per esercizi, `engine` per business

### Cross-DB reference pattern
```python
# crm.db: esercizi_sessione
class WorkoutExercise(SQLModel, table=True):
    id_esercizio: int = Field(index=True)  # NO FK — cross-DB ref

# Router: verifica esistenza prima di INSERT
exercise = catalog_session.exec(select(Exercise).where(Exercise.id == body.id_esercizio)).first()
if not exercise:
    raise HTTPException(404, "Esercizio non trovato")
```

## File modificati (commit 425145e..4e52438)

- `api/database.py` — CATALOG_TABLE_NAMES +3, create_db_and_tables() con esclusione
- `api/models/exercise.py` — rimosso trainer_id
- `api/models/exercise_media.py` — rimosso trainer_id e FK
- `api/models/exercise_relation.py` — rimossi FK
- `api/models/muscle.py`, `joint.py`, `medical_condition.py` — rimossi FK
- `api/models/workout.py` — id_esercizio cross-DB ref
- `api/routers/exercises.py` — read-only da catalog_session
- `api/seed_exercises.py` — seed in catalog_engine
- `api/main.py` — seed con catalog_engine
- `alembic/env.py` — include_name() filtro
- 7 script popolazione → target catalog.db
