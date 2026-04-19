# INC-2026-04-19 — catalog.db tassonomia vuota dopo consegna v1.0.7

- **Data**: 2026-04-19
- **Gravita'**: CRITICA (P0)
- **Impatto**: Safety Engine cieco — zero associazioni esercizi-condizioni sul prodotto consegnato al primo partner
- **Scope**: catalog.db (6 tabelle tassonomiche vuote) + pipeline build/seed
- **Durata disservizio**: dalla consegna v1.0.7 (2026-04-19) a fix (2026-04-19) = stesso giorno
- **Rilevato da**: Giacomo Vera durante verifica post-consegna

---

## Executive Summary

Sei tabelle tassonomiche di catalog.db sono state consegnate vuote ad Alessio Crociani (primo partner, v1.0.7). Il Safety Engine rilevava correttamente le condizioni cliniche dal campo anamnesi del cliente, ma non trovava NESSUN esercizio associato a quelle condizioni — rendendo le note di sicurezza completamente vuote. Il prodotto installato dal primo partner aveva il motore di sicurezza cieco.

L'errore e' stato causato da un **gap nella pipeline di build**: i 3 script che popolano tassonomia e condizioni (`seed_taxonomy`, `populate_taxonomy`, `populate_conditions`) non erano ne' nel seed automatico al startup ne' nel build pipeline. Ogni rebuild di catalog.db produceva un DB con esercizi ma senza tassonomia.

---

## Cronologia

| Ora | Evento |
|-----|--------|
| 2026-04-17 | Audit pre-consegna completato (`PRE_DELIVERY_AUDIT_2026_04_17.md`) |
| 2026-04-19 mattina | Audit esercizi v1.0.7: catalog.db ricostruito/ricreato |
| 2026-04-19 mattina | Seed automatico al startup ripopola esercizi (500), relazioni (940), media (1788) |
| 2026-04-19 mattina | **I 3 script manuali di tassonomia NON vengono rieseguiti** |
| 2026-04-19 | Build v1.0.7 + consegna installer ad Alessio con catalog.db incompleto |
| 2026-04-19 sera | Giacomo rileva Safety Engine cieco durante verifica post-consegna |
| 2026-04-19 sera | Root cause analysis, ripopolamento, fix strutturale |

---

## Root Cause Analysis

### Causa primaria — Gap nella pipeline seed/build

Il seed al startup (`api/main.py` lifespan) copriva solo 4 tabelle di catalog.db:

| Tabella | Seed automatico | Script manuale |
|---------|:---:|:---:|
| `esercizi` (500) | `seed_exercises.py` | — |
| `esercizi_relazioni` (940) | `seed_exercises.py` | — |
| `esercizi_media` (1788) | `seed_exercises.py` | — |
| `metriche` (22) | `seed_metrics.py` | — |
| **`muscoli`** (53) | **NESSUNO** | `seed_taxonomy.py` |
| **`articolazioni`** (15) | **NESSUNO** | `seed_taxonomy.py` |
| **`condizioni_mediche`** (47) | **NESSUNO** | `seed_taxonomy.py` |
| **`esercizi_muscoli`** (~7000) | **NESSUNO** | `populate_taxonomy.py` |
| **`esercizi_articolazioni`** (~1500) | **NESSUNO** | `populate_taxonomy.py` |
| **`esercizi_condizioni`** (~5000) | **NESSUNO** | `populate_conditions.py` |

I 3 script manuali (`tools/admin_scripts/`) erano eseguibili solo da CLI e non erano documentati come step obbligatorio ne' nel build pipeline ne' nella release checklist.

### Perche' non rilevato

1. **Nessun check nel build pipeline**: `build-release.sh` verificava esercizi, template nutrizionali e alimenti, ma NON verificava muscoli/articolazioni/condizioni
2. **Audit pre-consegna incompleto**: l'audit del 2026-04-17 verificava esercizi attivi e media, ma non le tabelle tassonomiche
3. **Seed startup parziale**: il lifespan di `main.py` seedava esercizi+relazioni+media+metriche ma non la tassonomia
4. **Test in-memory non coprono**: i test pytest usano un engine singolo in-memory dove le tabelle tassonomiche vengono create vuote — nessun test verifica che contengano dati

### Differenza dall'INC-2026-03-28

L'incidente del 28 marzo era un bug di **session mismatch** (query sulla session sbagliata). Questo incidente e' un bug di **pipeline** (tabelle mai popolate). Effetto identico: Safety Engine cieco. Causa completamente diversa.

---

## Impatto

### Business
- **Primo partner con prodotto difettoso**: Alessio Crociani ha ricevuto un prodotto dove la feature di sicurezza — leva core differenziante — e' inoperativa
- **Credibilita' partner**: un bug sulla feature piu' critica il giorno stesso della prima consegna

### Tecnico
- **6 tabelle vuote**: muscoli, articolazioni, condizioni_mediche, esercizi_muscoli, esercizi_articolazioni, esercizi_condizioni
- **Safety Engine cieco**: `condition_count` corretto (rileva condizioni dall'anamnesi) ma `entries` vuoto (zero esercizi associati)
- **Training Science Engine degradato**: volume counting, balance ratios, muscle coverage dipendono da esercizi_muscoli — tutti senza dati

### Utente
- **Nessun warning visivo**: il builder non mostrava errori, semplicemente non mostrava note di sicurezza — il trainer poteva programmare esercizi controindicati senza saperlo

---

## Perimetro dei fix

### Fase 1 — Ripopolamento immediato (3 step)

```bash
# 1. Tassonomia base
python -c "from tools.admin_scripts.seed_taxonomy import seed_db; seed_db('data/catalog.db')"
# → muscoli: 53, articolazioni: 15, condizioni_mediche: 47

# 2. Junction muscoli + articolazioni
python -m tools.admin_scripts.populate_taxonomy --db data/catalog.db
# → esercizi_muscoli: 6996, esercizi_articolazioni: 1452

# 3. Junction condizioni
python -m tools.admin_scripts.populate_conditions --db data/catalog.db
# → esercizi_condizioni: 5154
```

### Fase 2 — Fix strutturale (2 file)

| # | File | Modifica |
|---|------|----------|
| 1 | `api/seed_taxonomy.py` (nuovo) | Wrapper che invoca i 3 populate script con guard idempotente (`count > 0` per ogni tabella) |
| 2 | `api/main.py` | Step 4d nel lifespan: `seed_taxonomy_all()` dopo seed metriche |

**Comportamento**:
- In sviluppo: se una qualsiasi delle 6 tabelle e' vuota, il seed ripopola automaticamente al startup
- In compiled mode: skip (catalog.db pre-costruito, `tools/` non nel bundle per ADR-007)
- Per il prodotto installato: la protezione e' consegnare un catalog.db completo nell'installer

---

## Verifica

| Check | Risultato |
|-------|-----------|
| `muscoli` | 53 (era 0) |
| `articolazioni` | 15 (era 0) |
| `condizioni_mediche` | 47 (era 0) |
| `esercizi_muscoli` | 6996 (era 0) |
| `esercizi_articolazioni` | 1452 (era 0) |
| `esercizi_condizioni` | 5154 (era 0) |
| Safety map cliente ID=31 (5 condizioni) | 374 esercizi flaggati (era 0) |
| Backend restart + health | OK |
| `pytest tests/ -v` | 361 passed |
| `ruff check api/` | All checks passed |

---

## Lezioni e Regole Derivate

### L1 — Ogni tabella di catalog.db DEVE avere un seed al startup o un check nel build

La pipeline di seed deve coprire TUTTE le tabelle di catalog.db, non solo quelle piu' visibili (esercizi). Se una tabella e' essenziale per il funzionamento di un motore scientifico, il suo popolamento non puo' dipendere dall'esecuzione manuale di uno script.

**Regola**: se aggiungi una tabella a catalog.db, aggiungi il seed nel lifespan O un check nel build pipeline. Zero eccezioni.

### L2 — Il build pipeline DEVE verificare l'integrita' completa di catalog.db

Cosi' come `build-release.sh` verifica alimenti e template di nutrition.db, deve verificare che catalog.db contenga dati in TUTTE le tabelle tassonomiche. Un count > 0 per tabella e' sufficiente.

**Regola**: aggiungere check nel preflight di `build-release.sh` per muscoli, articolazioni, condizioni_mediche, esercizi_muscoli, esercizi_articolazioni, esercizi_condizioni.

### L3 — Rebuild di catalog.db richiede riesecuzione completa della pipeline seed

catalog.db non e' un singolo file monolitico — e' il prodotto di 6 script indipendenti. Ricreare il file `.db` senza rieseguire tutti gli script produce un DB strutturalmente corretto ma funzionalmente vuoto.

**Regola**: documentare in `SUPPORT_RUNBOOK.md` e in `CLAUDE.md` (pitfalls) che ogni rebuild di catalog.db richiede i 3 step: `seed_taxonomy` → `populate_taxonomy` → `populate_conditions`, in questo ordine.

### L4 — Audit pre-consegna DEVE includere conteggio tabelle tassonomiche

L'audit del 2026-04-17 ha verificato esercizi attivi, media, template nutrizionali, ma non le 6 tabelle tassonomiche. Se il check fosse stato presente, il bug sarebbe stato rilevato 2 giorni prima della consegna.

**Regola**: aggiungere alla checklist di audit pre-consegna un conteggio per ogni tabella tassonomica con soglia minima attesa.

---

## Azioni preventive

| Azione | Priorita' | Stato |
|--------|-----------|-------|
| Ripopolamento catalog.db (3 script) | P0 | DONE |
| Seed tassonomia al startup (`api/seed_taxonomy.py`) | P0 | DONE |
| Integrazione nel lifespan (`api/main.py` step 4d) | P0 | DONE |
| Incidente documentato (`INC-2026-04-19`) | P0 | DONE |
| POSTMORTEMS.md aggiornato | P0 | DONE |
| CLAUDE.md pitfalls aggiornato | P0 | DONE |
| RELEASE_CHECKLIST.md: check tassonomia | P0 | DONE |
| Rebuild installer v1.0.8 con catalog.db completo | P0 | TODO |
| Consegna aggiornamento ad Alessio | P0 | TODO |
| Check tassonomia nel preflight di `build-release.sh` | P1 | TODO |

---

## Classificazione

- **Tipo**: Gap pipeline build/seed — tabelle mai popolate dopo rebuild catalog.db
- **Trigger**: Rebuild catalog.db durante audit esercizi v1.0.7 senza riesecuzione script tassonomia
- **Severita'**: P0 — Safety Engine cieco sul prodotto consegnato al primo partner
- **MTTR**: ~2 ore dall'identificazione al fix completo (ripopolamento + fix strutturale)
- **Relazione con INC-2026-03-28**: stesso effetto (Safety Engine cieco), causa diversa (pipeline vs session mismatch)
