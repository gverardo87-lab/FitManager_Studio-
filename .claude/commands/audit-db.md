Esegui un audit completo dell'integrita' dei 3 database del progetto.

## Cosa verificare

### 1. Separazione architetturale (ADR-003)
- crm.db: DEVE avere SOLO tabelle business (33). Se contiene esercizi/muscoli/articolazioni/condizioni = ERRORE CRITICO
- catalog.db: DEVE avere esattamente 10 tabelle (esercizi + tassonomia). Zero trainer_id.
- nutrition.db: DEVE avere 8 tabelle (alimenti + template). Zero trainer_id.

### 2. Conteggi
- catalog.db: esercizi attivi (in_subset=1), relazioni, media, muscoli, articolazioni, condizioni
- nutrition.db: alimenti attivi, categorie, porzioni
- crm.db: tabelle business (contratti, clienti, etc.)

### 3. Integrita' cross-DB
- esercizi_sessione.id_esercizio in crm.db → verificare che TUTTI gli ID referenziati esistano in catalog.db
- componenti_pasto.alimento_id in crm.db → verificare che TUTTI gli ID referenziati esistano in nutrition.db
- Zero FK constraint cross-DB (application-level integrity)

### 4. Alembic safety
- alembic/env.py: verificare che include_name() escluda CATALOG_TABLE_NAMES + NUTRITION_TABLE_NAMES
- Nessuna tabella catalog/nutrition deve essere creata da Alembic in crm.db

### 5. JSON fields integrity
- catalog.db esercizi: muscoli_primari, muscoli_secondari, coaching_cues, errori_comuni, controindicazioni
- Verificare che siano JSON validi (no double-encoding)
- Sample 10 esercizi random e parsare ogni campo JSON

## Output
Riporta risultati in formato tabella con OK/FAIL per ogni check.
Se trovi problemi, descrivi l'impatto e proponi il fix.
