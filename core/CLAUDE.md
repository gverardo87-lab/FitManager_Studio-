# Core — AI & Business Logic Layer (Dormiente)

Moduli AI e workout in attesa di essere esposti via API endpoints.

## Stato attuale

I moduli AI sono **dormenti**: funzionano in isolamento ma non hanno endpoint API.
Saranno wrappati da `api/routers/` quando l'AI diverra' attiva nel prodotto.

**Pulizia 2026-03-25**: rimossi 9 repository legacy + tests/legacy/ + db_migrations.py + financial_analytics.py + backup_service.py (~4,630 LOC di dead code). I moduli che importavano dai repository (exercise_archive.py, pattern_extractor.py) sono stati aggiornati con placeholder.

## Moduli AI (dormenti, da esporre via API)

| Modulo | LOC | Funzione |
|--------|-----|----------|
| exercise_archive.py | 1,132 | Database 174+ esercizi, scoring, fuzzy match |
| workout_generator.py | 458 | Generazione programmi (3 modi: archive, dna, combined) |
| session_template.py | 341 | Struttura sessione (slot-based, max 8 esercizi) |
| periodization_models.py | 688 | 5 strategie periodizzazione (Linear, UL, PPL, Deload, Block) |
| card_parser.py | 1,092 | Parser Excel/Word → schede strutturate |
| pattern_extractor.py | 328 | LLM pattern extraction (Trainer DNA) |
| workout_ai_pipeline.py | 383 | Pipeline completa: assessment → DNA → generazione → LLM |
| knowledge_chain.py | 302 | Hybrid RAG (teoria + anatomia + fallback ExerciseArchive) |
| methodology_chain.py | 171 | RAG separato per pattern metodologici |
| document_manager.py | 82 | Scanner documenti knowledge_base/ |

## Fondamenta (usate dai moduli dormenti)

| File | LOC | Funzione |
|------|-----|----------|
| config.py | 72 | Path, DB, modelli LLM, embedding model |
| constants.py | 79 | Enum (EventStatus, RateStatus, MovementType) |
| error_handler.py | 284 | Logger, @safe_operation, eccezioni custom |

## Regole

- **Zero import streamlit** in tutta la cartella
- **Zero import da api/** — i due layer sono indipendenti
- Logger da error_handler.py, mai print()
- Config centralizzata in config.py, mai path hardcoded
- **Zero logica movimenti denaro in core/**: saldo, cassa, storni e ledger sono di esclusiva competenza `api/`
