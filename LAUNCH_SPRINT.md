# LAUNCH SPRINT — Piano Operativo Finale

Data: 2026-03-18
Branch: fit_launch_01
Obiettivo: **prodotto vendibile entro fine settimana**

---

## Stato Attuale vs Obiettivi

| Area | Stato attuale | Obiettivo | Gap |
|------|--------------|-----------|-----|
| Esercizi (catalog) | 439 attivi / 1111 totali | 500 attivi | +61 da archivio |
| Alimenti (nutrition) | 226 attivi | 500 attivi | +274 nuovi |
| Piani LARN | Donna under 30 attiva | 3 fasce eta' × 2-3 livelli attivita' | +7 profili |
| Pagina rinnovi-incassi | 340 LOC, funzionale ma grafica base | CRM-grade come cassa | Redesign UI |
| Pagina impostazioni | 517 LOC, layout piatto | Organizzata per sezioni | Redesign UI |
| Spotlight helper | 19 passi, 9 pagine coperte | Copertura completa | +pagine mancanti |
| Nome trainer in UI | Hardcoded "Chiara Bassani" | Dinamico da account registrato | Fix 2 punti |
| Schema sync (upgrade safe) | DONE (commit e9208b8) | — | ✅ Completato |
| License + fingerprint | DONE (commit d6ab1aa) | — | ✅ Completato |

---

## FASE 1 — Dati (cataloghi)

### 1A. Esercizi: 439 → 500 (+61)

Sorgente: 672 esercizi archiviati (`in_subset = 0`). Attivare i migliori.

Strategia:
- Identificare categorie sotto-rappresentate (bodyweight 42, avviamento 24, mobilita 30)
- Usare `activate_batch.py` con Ollama `gemma2:9b` per enrich
- Target: +20 bodyweight, +15 mobilita, +15 avviamento, +11 isolation/compound

### 1B. Alimenti: 226 → 500 (+274)

Sorgente: CREA 2019 (tabella completa ~800+ alimenti) + USDA FoodData Central.

Strategia:
- Seed script per importare ingredienti CREA mancanti (frutta, verdura, cereali, proteine)
- Aggiungere pietanze composte italiane comuni (pasta al pomodoro, insalata mista, ecc.)
- Bilanciare per categoria: target ~30-40 per categoria principale

Categorie da rinforzare:
- Verdure: 28 → 45 (+17)
- Frutta fresca: 17 → 35 (+18)
- Carne e pollame: 15 → 30 (+15)
- Prodotti ittici: 17 → 30 (+13)
- Cereali: 7 → 20 (+13)
- Legumi: 12 → 20 (+8)
- Pane e prodotti: 9 → 20 (+11)
- Latte e formaggi: 19 → 25 (+6)
- Uova: 4 → 8 (+4)
- Pietanze composte varie: +169 rimanenti

### 1C. Piani LARN: +7 profili donna (3 fasce eta' × livelli attivita')

Profilo gia' implementato:
- ✅ Donna under 30 attiva

Profili da aggiungere (8 combinazioni, 7 nuove):

| Fascia eta' | Sedentaria (PAL 1.4) | Attiva (PAL 1.6) | Sportiva (PAL 1.75+) |
|-------------|---------------------|-------------------|---------------------|
| Under 30 (18-29) | Da fare | ✅ Esistente | Da fare |
| 30-50 (30-59) | Da fare | Da fare | Da fare |
| Over 50 (50-74) | Da fare | Da fare | — |

Note:
- Over 50 sportiva esclusa (target troppo specifico per il lancio)
- Under 30 sportiva inclusa (target palestre/crossfit)

Implementazione:
- Le tabelle LARN per tutte le fasce eta' F esistono gia' in `larn_tables.py`
- Manca il calcolo automatico BMR + PAL → target_kcal
- Aggiungere enum `ActivityLevel` (sedentaria/attiva/sportiva)
- `ClientProfile.activity_level` → moltiplicatore PAL
- `auto_target_kcal(profile) → int` che calcola BMR Mifflin-St Jeor × PAL
- PAL riferimento LARN 2014: sedentaria 1.40, attiva 1.60, sportiva 1.75

---

## FASE 2 — UI Polish

### 2A. Pagina Rinnovi & Incassi → CRM-grade

Attuale: 2 sezioni flat (rinnovi + incassi), card base.
Target: visual premium come pagina Cassa (gradient cards, KPI, timeline).

Modifiche:
- KPI bar top: contratti in scadenza, rate scadute, importo da incassare
- Card rinnovi con progress bar crediti + scadenza visiva
- Card incassi con severity coloring (red overdue, amber warning)
- Timeline cronologica delle azioni
- Empty state celebrativo quando tutto è ok

### 2B. Pagina Impostazioni → organizzata

Attuale: 517 LOC, sezioni piatte una dopo l'altra.
Target: tab o accordion per raggruppamento logico.

Struttura proposta:
- **Tab Account**: nome, email, password (futuro)
- **Tab Sistema**: SystemStatus + Connectivity + SupportSnapshot
- **Tab Dati**: Backup/Restore + Export + Saldo iniziale

### 2C. Nome Trainer → dinamico (non hardcoded)

Attuale: "Chiara Bassani" hardcoded in Dashboard e Oggi.
Bug: se un altro trainer si registra, vede comunque "Chiara Bassani".

Target: saluto personalizzato dinamico dal cookie `fitmanager_trainer`:
- Dashboard hero: "Buongiorno, {nome}" (basato su ora del giorno)
- Oggi cockpit: "Buongiorno, {nome}"
- Sidebar: già dinamico ✅

Implementazione: sostituire stringhe hardcoded con `getStoredTrainer().nome`.
Pattern: `useState(null) + useEffect(() => setTrainer(getStoredTrainer()))` (hydration safe).

---

## FASE 3 — Guide & Polish

### 3A. Spotlight Tour completamento

Pagine senza tour:
- `/` (dashboard) — già ha step nel tour principale, manca `data-guide`
- `/oggi` — cockpit operativo, serve tour
- `/monitoraggio` — hub tracking, serve tour
- `/rinnovi-incassi` — dopo redesign, serve tour
- `/nutrizione` — se presente

Target: da 19 a ~25-28 passi, coprendo tutte le pagine navigabili.

---

## Ordine di Esecuzione

| Step | Task | Dipendenze | Stima |
|------|------|------------|-------|
| 1 | Esercizi 439→500 | Ollama running | Batch attivazione |
| 2 | Nome trainer in Dashboard + Oggi | Nessuna | Rapido |
| 3 | Alimenti 226→500 | Script seed CREA | Seed + verifica |
| 4 | Piani LARN 8 profili donna | Alimenti completati | Codice + test |
| 5 | Redesign rinnovi-incassi | Nessuna | UI |
| 6 | Redesign impostazioni | Nessuna | UI |
| 7 | Spotlight tour completamento | Pagine finite | Dati tour |
| 8 | Rebuild installer finale | Tutto completato | Build + test E2E |

---

## Vincoli

- **Schema sync garantito**: ogni modifica DB passa da schema_sync al startup
- **catalog.db e nutrition.db sono read-only**: shippati con l'installer, mai modificati dall'utente
- **Backup Chiara safe**: restore da v1.10.1 → schema_sync aggiunge colonne → zero crash
- **check-all.sh obbligatorio**: ruff + next build prima di ogni commit
- **Ollama necessario**: per enrich esercizi (gemma2:9b)
