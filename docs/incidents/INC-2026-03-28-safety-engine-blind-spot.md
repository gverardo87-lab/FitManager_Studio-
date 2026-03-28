# INC-2026-03-28 — Safety Engine Blind Spot

- **Data**: 2026-03-28
- **Gravita'**: CRITICA (P0)
- **Impatto**: Demo investitore fallita — profilo clinico completamente invisibile
- **Scope**: Safety Engine + Cache Invalidation + Builder UX Visibility
- **Durata disservizio stimata**: dall'introduzione del builder full-screen (2026-03-25) a fix (2026-03-28) = 3 giorni
- **Rilevato da**: Giacomo Vera durante demo live con potenziale investitore

---

## Executive Summary

Tre bug indipendenti hanno agito in combinazione per rendere il profilo clinico — leva core del prodotto e principale elemento differenziante — completamente invisibile nel workflow principale. Un cliente con 5 condizioni mediche rilevate (ernia cervicale C4-C5, dolori ginocchia, spalle) risultava privo di qualsiasi indicazione clinica nel builder schede, annullando il valore della Safety Engine di fronte a un investitore.

---

## Cronologia

| Ora | Evento |
|-----|--------|
| 2026-03-25 | Commit `d8b029f`: SciencePanel gated behind `showAdvanced` toggle (default: OFF) |
| 2026-03-25 | Commit `d8b029f`: BuilderSafetyCard limitata a `lg:hidden` (solo mobile) |
| 2026-03-28 mattina | Alessio Crociani compila anamnesi da cellulare (portale pubblico) — senza patologie |
| 2026-03-28 mattina | Giacomo modifica anamnesi aggiungendo Ginocchia, Spalle, Ernia cervicale C4-C5 |
| 2026-03-28 mattina | Tentativo generazione Scheda Smart per Alessio — crash 500 mascherato da errore CORS |
| 2026-03-28 mattina | Builder non mostra profilo clinico — investitore presente |
| 2026-03-28 sera | Root cause analysis e fix applicati |

---

## Root Cause Analysis

### Bug 1 — Cross-DB Session Mismatch (CRITICO)

**File**: `api/services/safety_engine.py:236`
**Commit introduttivo**: separazione 3 DB (2026-03-19, ADR-003)

```python
# PRIMA (BUG): cercava esercizi nella session di crm.db
active_ids = session.exec(
    select(Exercise.id).where(Exercise.in_subset == True, Exercise.deleted_at == None)
).all()

# DOPO (FIX): esercizi vivono in catalog.db
active_ids = catalog_session.exec(
    select(Exercise.id).where(Exercise.in_subset == True, Exercise.deleted_at == None)
).all()
```

**Meccanismo**: la tabella `esercizi` vive in `catalog.db` dal 2026-03-19 (ADR-003). `build_safety_map()` riceve sia `session` (crm.db) sia `catalog_session` (catalog.db), ma la query per gli ID esercizi attivi usava `session` (crm.db) dove la tabella non esiste. Il crash 500 avveniva prima che il middleware CORS potesse aggiungere header → il browser mostrava `ERR_FAILED` / `No Access-Control-Allow-Origin` invece del vero errore.

**Perche' non rilevato prima**: i test in-memory usano un singolo engine dove tutte le tabelle coesistono. Il bug si manifesta SOLO con database fisicamente separati (ambiente reale o dev con 3 file .db).

**Effetto**: generazione Scheda Smart impossibile per QUALSIASI cliente con condizioni mediche. Endpoint `POST /training-science/plan-package` → 500 per ogni client con anamnesi che attiva condizioni.

---

### Bug 2 — Cache Invalidation Gap (ALTO)

**File**: `frontend/src/hooks/useClients.ts:126-130`

```typescript
// PRIMA (BUG): useUpdateAnamnesi non invalidava la safety map
onSuccess: (client) => {
  queryClient.invalidateQueries({ queryKey: ["clients"] });
  queryClient.invalidateQueries({ queryKey: ["client", client.id] });
  queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  // MANCAVA: ["exercise-safety-map", client.id]
};
```

**Meccanismo**: la query `exercise-safety-map` ha `staleTime: 5min`. Se l'anamnesi viene compilata (dal portale o dal trainer) senza condizioni, la cache salva `condition_count: 0`. Quando l'anamnesi viene modificata (es. aggiungendo infortuni), la cache non viene invalidata → il builder continua a usare il valore stale.

**Scenario esatto della demo**:
1. Alessio compila anamnesi dal cellulare → nessun infortunio → safety map cachata con `condition_count: 0`
2. Giacomo modifica anamnesi aggiungendo dolori e infortuni → cache NON invalidata
3. Apertura builder → React Query serve cache stale → profilo clinico invisibile

**Fix**: aggiunta invalidazione `["exercise-safety-map", client.id]` in `useUpdateAnamnesi()` e `useUpdateClient()`.

---

### Bug 3 — BuilderSafetyCard Hidden on Desktop (MEDIO)

**File**: `frontend/src/app/(dashboard)/schede/[id]/page.tsx:175`

```jsx
// PRIMA (BUG): invisibile su desktop, visibile solo mobile
<div className="lg:hidden mb-3">

// FIX INTERMEDIO (ancora problematico): nascosta quando SciencePanel attivo
<div className={showAdvanced ? "lg:hidden mb-3" : "mb-3"}>

// FIX FINALE: sempre visibile — il profilo clinico e' troppo critico per nasconderlo
<div className="mb-3">
```

**Meccanismo**: commit `d8b029f` (builder full-screen, ADR-008) ha spostato le informazioni safety nel SciencePanel (sidebar destra da 320px) e nascosto la BuilderSafetyCard su desktop (`lg:hidden`). Ma il SciencePanel e' gated behind un toggle Flask (`showAdvanced`, default OFF, persistito in localStorage). Risultato: su desktop con toggle OFF → zero profilo clinico.

Il fix intermedio nascondeva la card solo quando `showAdvanced = true` (aspettandosi che il SciencePanel la sostituisse). Ma nella pratica, la sezione Safety nel SciencePanel e' posizionata sotto Score Ring e sub-scores — non immediatamente visibile. Il fix finale rende la card sempre visibile indipendentemente dallo stato del toggle.

---

## Impatto

### Business
- **Demo investitore compromessa**: la feature piu' differenziante del prodotto (safety-awareness clinica) era completamente invisibile
- **Percezione prodotto**: un CRM fitness che non mostra le condizioni mediche del cliente nella scheda allenamento perde la sua ragion d'essere

### Tecnico
- **Endpoint plan-package inutilizzabile**: crash 500 per ogni cliente con condizioni mediche rilevate dall'anamnesi
- **Safety map stale dopo modifica anamnesi**: il trainer non aveva modo di forzare il refresh se non con hard reload del browser
- **Informazioni vitali nascoste**: il builder in modalita' full-screen default non mostrava nessuna informazione clinica su desktop

### Utente
- **Zero feedback**: il crash 500 era mascherato da errore CORS — nessun messaggio d'errore comprensibile
- **Falsa sicurezza**: il builder mostrava la scheda come se il cliente fosse sano, creando un rischio potenziale

---

## Perimetro dei fix

| # | File | Modifica | Riga |
|---|------|----------|------|
| 1 | `api/services/safety_engine.py` | `session` → `catalog_session` per query esercizi attivi | 236 |
| 2 | `frontend/src/hooks/useClients.ts` | `useUpdateAnamnesi` invalida `["exercise-safety-map", client.id]` | 129 |
| 3 | `frontend/src/hooks/useClients.ts` | `useUpdateClient` invalida `["exercise-safety-map", client.id]` | 104 |
| 4 | `frontend/src/app/(dashboard)/schede/[id]/page.tsx` | BuilderSafetyCard sempre visibile (`"mb-3"` senza condizioni responsive) | 175 |

---

## Verifica

| Check | Risultato |
|-------|-----------|
| `build_safety_map()` per Alessio (5 condizioni) | OK — 5 condition IDs, 686 exercise rules |
| `build_plan_package()` per Alessio | OK — genera piano con safety context |
| `pytest tests/ -v` | 337 passed |
| `ruff check api/` | All checks passed |
| `next build` | Build succeeded, 0 errors |

---

## Lezioni e Regole Derivate

### L1 — Test cross-DB obbligatori per dual-session

I test in-memory con engine singolo **non coprono** bug di session mismatch. Ogni servizio che riceve sia `session` sia `catalog_session` deve avere almeno un test con engine separati. In assenza di test integration cross-DB, ogni nuovo endpoint dual-session va verificato manualmente con `python -c` sui database fisici prima del merge.

**Regola**: dopo ogni modifica a funzioni dual-session (`safety_engine.py`, `profile_resolver.py`, `session_prep.py`), verificare che ogni `select()` usi la session corretta:
- `session` → tabelle crm.db (clienti, contratti, rate, eventi, schede, misurazioni)
- `catalog_session` → tabelle catalog.db (esercizi, muscoli, articolazioni, condizioni, relazioni, media)

### L2 — Invalidazione safety map e' un obbligo architetturale

La safety map dipende dall'anamnesi. Qualsiasi mutation che modifica anamnesi (direttamente o indirettamente) DEVE invalidare `["exercise-safety-map", clientId]`. Questo include:
- `useUpdateAnamnesi` (modifica diretta)
- `useUpdateClient` (potrebbe contenere anamnesi)
- Futuro: submission da portale pubblico (se polling o websocket)

**Regola**: in `frontend/CLAUDE.md`, aggiungere `exercise-safety-map` alla lista di query che vanno invalidate su modifica anamnesi.

### L3 — Informazioni cliniche MAI dietro toggle opzionale

Il profilo clinico e' informazione vitale per la sicurezza del cliente. Non deve MAI essere nascosto dietro un toggle, un tab, o una condizione di viewport. La BuilderSafetyCard deve essere **sempre visibile** quando `condition_count > 0`, indipendentemente da:
- Stato del toggle Flask (`showAdvanced`)
- Viewport (mobile/desktop)
- Tab attivo (Sessioni/Analisi)

**Regola**: la visibilita' della BuilderSafetyCard e' non negoziabile. Solo `safetyMap.condition_count > 0` controlla la visibilita'. Zero ulteriori condizioni.

### L4 — Crash 500 mascherati da CORS

Quando un endpoint FastAPI crasha prima che il middleware CORS aggiunga gli header, il browser mostra un errore CORS generico (`No Access-Control-Allow-Origin`). Questo nasconde completamente il vero errore (500, traceback, messaggio).

**Regola**: in fase di debug, se appare un errore CORS su un endpoint che normalmente funziona → guardare PRIMA i log del backend (stderr/uvicorn) per cercare un crash 500. L'errore CORS e' quasi sempre un sintomo, non la causa.

---

## Azioni preventive

| Azione | Priorita' | Stato |
|--------|-----------|-------|
| Fix applicati (4 modifiche) | P0 | DONE |
| POSTMORTEMS.md aggiornato | P0 | DONE |
| CLAUDE.md pitfalls aggiornati | P0 | DONE |
| frontend/CLAUDE.md pitfalls aggiornati | P0 | DONE |
| api/CLAUDE.md safety engine documentation | P0 | DONE |
| Test integration cross-DB per safety_engine | P1 | BACKLOG |
| Error boundary frontend per crash 500 mascherati | P2 | BACKLOG |

---

## Classificazione

- **Tipo**: Regressione multi-layer (backend + frontend cache + frontend UX)
- **Trigger**: Combinazione di ADR-003 (separazione 3 DB) + ADR-008 (builder full-screen) + gap invalidazione cache
- **Severita'**: P0 — impatto diretto su demo commerciale + sicurezza informativa cliente
- **MTTR**: ~3 ore dall'inizio analisi al fix completo
