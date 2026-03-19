Esegui la pipeline completa di popolazione catalog.db.

## Pipeline (esegui in ordine)

Questi script popolano le tabelle di tassonomia e relazioni in catalog.db.
Sono tutti deterministici (zero Ollama), idempotenti, e safe da rieseguire.

```bash
# 1. Tassonomia muscolare + articolare (muscoli, articolazioni, biomeccanica)
python -m tools.admin_scripts.populate_taxonomy --db data/catalog.db

# 2. Condizioni mediche (safety engine)
python -m tools.admin_scripts.populate_conditions --db data/catalog.db

# 3. Relazioni esercizi (progressioni, regressioni, varianti)
python -m tools.admin_scripts.populate_exercise_relations --db data/catalog.db

# 4. Demand vector 10D (costo biomeccanico per esercizio)
python -m tools.admin_scripts.populate_demand --db data/catalog.db

# 5. Gap filling (muscoli secondari, tempo consigliato)
python -m tools.admin_scripts.fill_subset_gaps --db data/catalog.db

# 6. Quality check finale
python -m tools.admin_scripts.verify_exercise_quality --db data/catalog.db
```

## Post-pipeline

Dopo l'esecuzione:
1. Verifica l'output di ogni step (zero errori)
2. Riporta conteggi finali (esercizi attivi, relazioni, condizioni)
3. Se ci sono WARNING, elencali con contesto

## Quando usare

- Dopo aver attivato nuovi esercizi (activate_batch.py)
- Dopo aver modificato catene di progressione
- Dopo upgrade dello script di tassonomia
- Come verifica periodica di integrita'
