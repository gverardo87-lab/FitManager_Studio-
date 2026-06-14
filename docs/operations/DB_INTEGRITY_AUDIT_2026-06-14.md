# DB Integrity Audit — 2026-06-14

**Tipo:** record operativo d'audit (read-only). Fotografia della solidità dei 3 database prima del tuning di contenuto del catalogo.
**Scope:** `catalog.db` (focus), `crm.db` (separazione + integrità cross-DB), `nutrition.db` (sanity), `crm_dev.db` (artefatto legacy).
**Metodo:** query dirette SQLite sui file reali in `data/`, in dev mode (DB in chiaro). Strumento: skill `audit-db` + script di introspezione. **Nessuna mutazione** eseguita.
**Eseguito da:** Claude Code (verifica dall'interno). Versione prodotto: 1.0.10.
**Esito sintetico:** `catalog.db` impeccabile; il debito reale è **detrito di migrazione** in `crm.db` + drift di documentazione. Cleanup mirato, **non rebuild**.

---

## 1. Executive summary

La verifica conferma l'istinto founder ("catalog.db non creato in maniera metodica") **ma ne sposta il bersaglio**: il disordine non è nella qualità del catalogo corrente — è nei **detriti lasciati dalla migrazione 1111→500 esercizi**:

- `catalog.db` (fonte autorevole) è **pristino**: zero FK orfane, copertura junction 100%, contenuto 100% popolato, JSON valido, demand vector esplicito.
- `crm.db` contiene ancora una **copia stale e popolata del vecchio catalogo pre-rebuild** (10 tabelle catalog, 1111 esercizi) — violazione ADR-003 a livello di tabelle fisiche.
- **32 esercizi** droppati nel rebuild sono ancora referenziati da **58 righe di schede reali** (`esercizi_sessione`), sopravvissuti solo nella tabella stale di crm.db.
- I **numeri canonici** della strategia v2.1 (4168 condizioni, 1234 articolazioni) sono i numeri della **tabella stale di crm.db**, non di catalog.db (reali: 5154, 1452). La "verifica dall'interno" v2.1 ha misurato alcune junction sul DB sbagliato.

**Conseguenza strategica:** non c'è nulla da ricostruire. Il bundle di Alessio resta uno **specchio** di copertura/naming, non una base di rebuild. Il percorso metodico è **cleanup + curation mirata**.

---

## 2. `catalog.db` — stato di salute: ECCELLENTE

| Check | Esito |
|-------|-------|
| FK orfane: media / muscoli / articolazioni / condizioni / relazioni (entrambi i lati) | **0 ovunque** ✅ |
| FK junction → tassonomia base (muscoli, articolazioni, condizioni) | **0 orfani** ✅ |
| Copertura attivi (466): con ≥1 muscolo / articolazione / condizione | **466 / 466 / 466 (100%)** ✅ |
| Contenuto ricco attivi (setup, esecuzione, respirazione, anatomia, biomeccanica, note_sicurezza, tempo, cue, errori) | **466/466 su tutti i 9 campi (100%)** ✅ |
| Demand vector 10D: valori espliciti (non NULL) | **466/466** ✅ |
| Integrità JSON (muscoli_primari/secondari, coaching_cues, errori_comuni, controindicazioni — scan completo 500) | **0 invalidi, 0 double-encoded, 0 vuoti** ✅ |
| Distribuzione ruoli muscolari | primary 2635 / secondary 2978 / stabilizer 1383 |
| Distribuzione severità condizioni | avoid 590 / caution 2325 / modify 2239 |
| Media: tipo | 750 tutti `image` (0 video — atteso pre-bundle) |

**Numeri canonici VERI (fonte: `catalog.db`, 2026-06-14):**

| Entità | Valore |
|--------|--------|
| esercizi totali / attivi (`in_subset=1`) | 500 / 466 |
| `is_fondamentale=1` | **0** (campo cablato ma vuoto — atteso, prerequisito da decidere) |
| esercizi_relazioni | 894 |
| esercizi_media (attivi coperti / scoperti) | 750 (359 / **107**) |
| muscoli / esercizi_muscoli | 53 / 6996 |
| articolazioni / esercizi_articolazioni | 15 / **1452** |
| condizioni_mediche / esercizi_condizioni | 47 / **5154** |
| metriche | 22 |

---

## 3. La scoperta centrale — detrito di migrazione in `crm.db`

`crm.db` ha **38 tabelle**: 28 business + **10 tabelle catalog stale** (pre-rebuild, popolate). Le tabelle nutrition catalog sono correttamente **assenti** (fantasmi rimossi, come da memory).

**Confronto tabelle catalog: crm.db (stale) vs catalog.db (autorevole):**

| Tabella | crm.db (stale) | catalog.db (vero) |
|---------|---------------:|------------------:|
| esercizi | **1111** | 500 |
| esercizi_media | **1788** | 750 |
| esercizi_muscoli | 6040 | 6996 |
| esercizi_articolazioni | **1231** | 1452 |
| esercizi_condizioni | **4168** | 5154 |
| esercizi_relazioni | 480 | 894 |

I 500 ID di catalog.db sono tutti presenti in crm.db; crm.db ne ha **611 in più** (gli esercizi droppati nel rebuild). Gli esercizi stale di crm.db hanno contenuto (setup, cue popolati): è una copia ricca ma obsoleta.

**Perché è dormiente ma pericoloso:** l'app legge il catalogo da `catalog.db` (`get_catalog_session`), quindi le tabelle stale non sono servite. Ma: (a) hanno già ingannato la documentazione (§4), (b) gonfiano il DB sacro di backup, (c) sono l'unico appiglio residuo dei 32 orfani (§3.1).

### 3.1 — 32 esercizi orfani referenziati da dati business reali

`esercizi_sessione` (schede reali) ha **971 riferimenti** a esercizi; **32 ID distinti** (in **58 righe**) puntano a esercizi **assenti da catalog.db** ma presenti nella tabella stale di crm.db. Sono esercizi droppati nel rebuild 1111→500. Lista (con nomi dalla tabella stale):

```
15 Affondo Laterale · 16 Belt Squat · 46 Landmine Press · 73 Rematore T-Bar ·
81 Seal Row · 140 Rack Carry · 142 Clean Kettlebell · 235 Bear Hug Carry ·
252 Floor Press Bilanciere · 299 Front Squat con Due Kettlebell · 414 Board Press ·
428 Bradford Press · 498 Panca Declinata French Press · 509 Dip al petto ·
518 Drag Curl · 522 Girata con Manubrio · 599 Buongiorno alla Sbarra ·
603 Curl al Cavo · 644 Carico Kettlebell · 656 Muscle Up a Trazioni ·
700 Affondo Pass Through · 738 Allungamento Collo ·
756 Split Jerk con Kettlebell a Un Braccio · 791 Allungamento del Perone ·
877 Buccinate da Seduto · 905 Trazioni Laterali · 962 Affondi Frontali ·
984 Allungamento Quadricipiti Inclinato · 987 Allungamento Gambe Posteriori e Polpacci in Piedi ·
1056 Allungamento In Alto · 1062 Dip alla Panca Pesato · 1064 Jump Squat con Peso
```

Molti sono esercizi **veri e prescritti** (Belt Squat, Landmine Press, Seal Row, Split Jerk): probabile **re-inserimento** in catalog.db, non delete delle referenze.

---

## 4. Lista discrepanze prioritizzata

| Pri | Discrepanza | Impatto | Fix proposto | Tocca DB sacro? |
|-----|-------------|---------|--------------|-----------------|
| **P1** | Violazione ADR-003: 10 tabelle catalog stale in crm.db | Dormiente ma latente (inganna doc, gonfia backup, appiglio dei 32 orfani) | DROP delle tabelle catalog stale da crm.db — **solo dopo** aver gestito i 32 orfani | Sì (crm.db) → backup obbligatorio |
| **P1** | 32 esercizi orfani / 58 righe `esercizi_sessione` | Dato business riferisce esercizi assenti dalla fonte autorevole | Decisione di contenuto: re-inserire i 32 in catalog.db (sono reali) o rimappare le 58 righe | Sì (catalog.db + crm.db) → backup |
| **P2** | Numeri canonici sbagliati in doc/memory (4168/1234 vs 5154/1452) | Rumore interno; misurazione su DB sbagliato | Correggere `EXERCISE_LIBRARY_STRATEGY.md` §1.4/§4.1 + memory + CLAUDE.md | No (solo doc) — **sicuro** |
| **P3** | `crm_dev.db` legacy (dual-env rimosso) | Innocuo, non referenziato | Archiviare/rimuovere con backup | Sì (ha dati) → backup |
| **P3** | 7 nomi esercizio duplicati in catalog.db | Possibili veri duplicati o varianti | Review manuale | Sì (catalog.db) |
| nota | nutrition.db: memory dice 210 ricette → reali 512 | Fuori scope (nutrizione) | Correggere memory quando si tocca nutrizione | No |

**Duplicati catalog.db (P3):** Adduttori, Curl Bicipiti Inclinato, Distensioni Pettorali, Ellittica, Jumping Jacks, Rollout con Bilanciere, Ruota Addominale (×2 ciascuno).

---

## 5. `nutrition.db` e `crm_dev.db`

- **`nutrition.db`** (sano): 8 tabelle, **880 alimenti**, 15 categorie, 1610 porzioni, **512 ricette_pietanze** (memory dice 210 — drift), 12 plan_templates, 280 template_plan_meals, 784 template_plan_components. Zero leak catalog. Nessun problema strutturale.
- **`crm_dev.db`** (legacy): 28 tabelle, 1 trainer, 32 clienti, 38 contratti, **zero leak catalog**. Residuo del dual-env rimosso il 2026-06-09. Non referenziato dall'ambiente unico attuale (crm.db). Da archiviare con backup.

---

## 6. Sequenza di remediation raccomandata

Ordine per sicurezza crescente di rischio (mai distruttivo senza backup — vedi regola non negoziabile #11):

1. **P2 — Correzione numeri canonici** (doc + memory + CLAUDE.md). Solo-doc, zero rischio. *Candidato immediato.*
2. **P1 — Decisione 32 orfani**: re-inserire in catalog.db (raccomandato: sono esercizi veri) o rimappare le 58 righe. Decisione di contenuto del founder. Backup catalog.db + crm.db prima.
3. **P1 — DROP tabelle catalog stale da crm.db** (chiude ADR-003). **Solo dopo** il punto 2. Backup crm.db obbligatorio + autorizzazione esplicita.
4. **P3 — Archiviare `crm_dev.db`** + review 7 duplicati catalog.db.

**Nessuna di queste azioni è stata eseguita.** Questo documento è il record read-only che le precede.

---

## 8. Approfondimento — analisi dei 32 orfani (2026-06-14, read-only)

Analisi per decidere keep/remap/drop (vedi §6 passo 2). **Confermato dal founder: le 5 schede impattate sono dati di TEST (gvera-dev), non schede reali** → le 58 referenze non sono preziose; la decisione è puro **merito di catalogo**.

**Fatti chiave:**
- **Zero duplicati di nome** in catalog.db (fuzzy match cutoff 0.86 → 0 match per tutti e 32): sono genuinamente *assenti*, non doppioni rinominati. Remap "facile" non disponibile.
- **Raggio minuscolo:** 58 righe in **5 schede** (test).
- **Gli ID orfani sono liberi in catalog.db** → fix pulito = **re-inserire preservando l'ID** (le referenze si risolvono da sole, zero remap).

**Tiering per qualità contenuto (copia stale crm.db):**

| Tier | N | Esercizi | Stato stale | Sforzo |
|------|---|----------|-------------|--------|
| Ricchi | 3 | Bear Hug Carry, Floor Press Bilanciere, Front Squat con Due KB | 6/7 campi + junction | Basso |
| Medi | 7 | Affondo Laterale, Belt Squat, Landmine Press, Rematore T-Bar, Seal Row, Rack Carry, Clean Kettlebell | 5/7, 0 junction | Medio |
| Gusci | 22 | Board/Bradford Press, Drag Curl, Curl al Cavo, Dip al petto, Muscle Up, Split Jerk, Jump Squat, 5 allungamenti, … | 1/7, 0 junction | Alto (authoring) |

**Nomi sospetti da rivedere (possibile detrito auto-generato):** Buccinate da Seduto, Carico Kettlebell, Girata con Manubrio, Trazioni Laterali, Affondi Frontali (categorizzato `stretching` ma è un affondo).

**Decisione raccomandata:** re-inserire i keeper preservando l'ID, in due ondate — (1) i 3 ricchi + 7 medi (basso sforzo, esercizi veri), (2) i 22 gusci con curation founder (distinguere veri da scartare/rinominare). Il re-insert allo standard 100% è curation proprietaria (AC-3); il bundle Alessio + dominio founder informano l'authoring. Meccanica: re-insert nel seed + rebuild catalog.db (pitfall #13: `seed_taxonomy → populate_taxonomy → populate_conditions`), **backup prima**.

---

## 7. Riferimenti

- `docs/adr/ADR-003-separazione-architetturale-3-database.md` — la separazione violata a livello di tabelle fisiche
- `docs/technical/EXERCISE_LIBRARY_STRATEGY.md` — numeri canonici da correggere (§1.4, §4.1)
- `CLAUDE.md` — regola non negoziabile #11 (cataloghi sacri, mai distruttivo senza backup), pitfall #13 (rebuild catalog = pipeline completa)
- `docs/learning/BUILD_LOG.md` — voce cronologica dell'audit
