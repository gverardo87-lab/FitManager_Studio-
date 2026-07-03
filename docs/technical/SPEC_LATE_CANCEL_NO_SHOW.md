# SPEC G7.8-bis — Late Cancel e No Show

**Tipo:** specifica prescrittiva (bridge Chat→Code), blocco di completamento dell'agenda e dell'asse occupazione crediti.
**Stato:** ✅ **IMPLEMENTATA** (2026-07-03: Step 0 `4944a49` prep-SSoT + Step 1 `db322eb` stati-penale; suite 787; ADR-017 Addendum I accepted; correzioni bridge in §6)
**Origine:** emersa nell'allineamento roadmap del 2026-07-03; rappresenta il completamento dell'**ADR-017** (Opzione C "Modello Mindbody", inizialmente differita per motivi di scope pre-lancio).
**SSoT di dominio:** `FINANCIAL_DOMAIN_MODEL.md` (integrazione penali agenda e cassa) · `TASSONOMIA_FINANZIARIA.md`.
**Posizione nella sequenza (Blocco G7/G8):**
1.  `G7.8` (Rinvio libera il credito, ✅ completato): ha definito l'occupazione crediti come `Programmato + Completato`.
2.  `G7.9` (Terminazione bilaterale, ✅ completato): ha introdotto il conguaglio su base sedute `Completato`.
3.  **`G7.8-bis` (Late Cancel & No Show, PROPOSTO)**: estende retroattivamente la logica di `G7.8` (occupazione) e `G7.9` (conguaglio/penale) introducendo la distinzione tra sessione fisica e penale finanziaria.
4.  `G8.1` / `G8.2` / `G8.3` (Integrità, wallet e INV-RATE, ✅ completati): erediteranno automaticamente le nuove definizioni grazie al design basato su SSoT.

---

## 0. Tesi unica (falsificabile)

> **T1 — `Cancellato_Tardivo` e `No_Show` occupano il credito ma non la performance.**
> Un evento PT in stato `Cancellato_Tardivo` (Late Cancel) o `No_Show` (Mancata Presentazione) rappresenta una penale: consuma il credito dal contratto del cliente al pari di una lezione svolta, ma non costituisce performance atletica (viene ignorato dalla Training Intelligence). Inoltre, nel calcolo di settlement di terminazione, questi eventi sono assimilati alle lezioni erogate, in quanto il corrispettivo è trattenuto dal trainer a titolo di penale.

Falsificabile su tre fronti:
1.  **Consumo Crediti**: Creando un contratto con 10 crediti e associando 1 evento `Completato`, 1 `Programmato`, 1 `Cancellato_Tardivo` e 1 `No_Show`, il valore di `crediti_residui` deve scendere a **6** (oggi scenderebbe a 8 perché gli ultimi due verrebbero ignorati).
2.  **Training Science**: La Training Intelligence e l'analisi dei carichi muscolari non devono registrare alcun volume o stimolo da eventi `Cancellato_Tardivo` o `No_Show`.
3.  **Settlement di Recesso**: Una terminazione anticipata su un contratto con 10 lezioni vendute a €1000 (prezzo unitario €100), di cui 6 `Completato`, 1 `Cancellato_Tardivo`, 1 `No_Show` e 2 non erogate, deve calcolare il valore del servizio reso/dovuto come **€800** (6 completate + 2 penali), erogando al cliente un rimborso massimo di €200 (se interamente versato).

---

## 1. Modello ratificato (decisioni di dominio, vincolanti)

La tassonomia degli stati evento PT e il loro impatto sui tre assi del sistema viene così estesa:

| Stato Event PT | Consuma Credito (Contratto) | Valore Contabile (Cassa/Penale) | Erogato Scientifico (Intelligence) | Semantica |
| :--- | :--- | :--- | :--- | :--- |
| `Programmato` | **SÌ** (impegnato) | NO (reversibile) | NO | Sessione pianificata in agenda |
| `Completato` | **SÌ** (definitivo) | **SÌ** (servizio reso) | **SÌ** | Sessione eseguita con successo |
| `Rinviato` | **NO** (liberato) | NO | NO | Sessione rinviata prima del limite |
| `Cancellato` | **NO** (liberato) | NO | NO | Sessione annullata tempo utile |
| `Cancellato_Tardivo`| **SÌ** (definitivo) | **SÌ** (penale dovuta) | NO | Cancellata fuori tempo massimo |
| `No_Show` | **SÌ** (definitivo) | **SÌ** (penale dovuta) | NO | Il cliente non si è presentato |

### Decisioni founder vincolanti:
1.  **D-VALID-STATUS**: I nuovi stati letterali accettati in agenda sono `Cancellato_Tardivo` e `No_Show`. Il router di agenda ne valida l'inserimento e la modifica.
2.  **D-CREDIT-CONSUMPTION**: I due nuovi stati entrano stabilmente nella definizione di `OCCUPAZIONE_CREDITO`. L'auto-close del contratto si attiva al completamento/saturazione del monte-ore considerando anche le penali.
3.  **D-RECESSO-PENALE**: Ai fini fiscali e di recesso (ADR-016), le lezioni perse per colpa del cliente (`Cancellato_Tardivo` e `No_Show`) non sono rimborsabili. Il calcolo del settlement del contratto le include come quote dovute al trainer.
4.  **D-CALENDAR-OVERLAP**: Gli eventi in stato `Cancellato_Tardivo` e `No_Show` rappresentano slot orari passati in cui il trainer non ha potuto lavorare. Tuttavia, per flessibilità gestionale retroattiva, **liberano lo slot orario** in `_check_overlap` al pari di `Cancellato` e `Rinviato`, per consentire al trainer di riprogrammare o inserire appuntamenti correttivi nello stesso orario storico.

---

## 2. Predicati canonici post-fix

### 2.1 Occupazione Credito (Asse Crediti - Estensione G7.8)
Sostituisce il predicato a due stati `IN ('Programmato', 'Completato')` (introdotto in `G7.8`) in tutti i conteggi di crediti usati del contratto:
```python
OCCUPAZIONE_CREDITO ⟺ Event.categoria == 'PT'
                   AND Event.deleted_at IS NULL
                   AND Event.stato.in_(["Programmato", "Completato", "Cancellato_Tardivo", "No_Show"])
```

### 2.2 Servizio Contabilizzabile (Asse Denaro / Settlement - Estensione G7.9)
Sostituisce il conteggio basato unicamente su `Completato` (introdotto in `G7.9`) in tutti i moduli di calcolo del conguaglio finanziario e di recesso:
```python
SERVIZIO_RESO_FINANZIARIO ⟺ Event.categoria == 'PT'
                          AND Event.deleted_at IS NULL
                          AND Event.stato.in_(["Completato", "Cancellato_Tardivo", "No_Show"])
```

---

## 3. Inventario completo dei siti (CAMBIA / LASCIA)

### 3.1 Siti da modificare per l'occupazione crediti (CAMBIA in `OCCUPAZIONE_CREDITO`)
Ogni file che calcola il numero di crediti consumati o blocca nuove prenotazioni deve includere i due nuovi stati:

*   [contracts.py:L245](file:///c:/Users/gvera/Projects/FitManager_AI_Studio/api/routers/contracts.py#L245) (`_count_crediti_usati` batch query):
    ```diff
    - Event.stato.in_(["Programmato", "Completato"]),
    + Event.stato.in_(["Programmato", "Completato", "Cancellato_Tardivo", "No_Show"]),
    ```
*   [contracts.py:L318, L437, L620, L1049](file:///c:/Users/gvera/Projects/FitManager_AI_Studio/api/routers/contracts.py#L318) (sottomoduli di conteggio e validazione contratti): applicare la stessa inclusione a 4 stati.
*   [agenda.py:L200, L285, L439](file:///c:/Users/gvera/Projects/FitManager_AI_Studio/api/routers/agenda.py#L200) (guards di creazione/modifica eventi e overlap):
    ```python
    # agenda.py L200 e L285 (check overlap e sync chiuso)
    # check overlap tiene solo Programmato e Completato per bloccare l'orario reale,
    # mentre sync chiuso (L285) deve usare l'occupazione crediti a 4 stati.
    ```
*   [clients.py:L317](file:///c:/Users/gvera/Projects/FitManager_AI_Studio/api/routers/clients.py#L317) (`sedute_PT_usate` query nel dettaglio cliente).
*   [client_avatar.py:L431](file:///c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/client_avatar.py#L431) (calcolo dell'avatar e dei report).
*   [workspace_engine.py:L1248, L1391, L2148](file:///c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/workspace_engine.py#L1248) (tutti i conteggi di crediti del cockpit).
*   [transitions.py:L686](file:///c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/financial/transitions.py#L686) (validazione della terminazione).
*   [dashboard.py:L406, L567, L1107](file:///c:/Users/gvera/Projects/FitManager_AI_Studio/api/routers/dashboard.py#L406) (calcoli KPI contratti attivi e scadenze).

### 3.2 Siti da modificare per l'asse denaro (CAMBIA in `SERVIZIO_RESO_FINANZIARIO`)
Il modulo di settlement deve conteggiare le cancellazioni tardive e le mancate presentazioni come lezioni erogate/dovute ai fini del saldo finale:

*   `api/services/contract_settlement.py` (funzione `_count_sedute_erogate` o query equivalente):
    Deve includere `Completato`, `Cancellato_Tardivo` e `No_Show`.

### 3.3 Siti da non toccare (LASCIA)
*   **Training Intelligence / Volume Model** (`api/services/training_science/`):
    L'analisi del carico muscolare, MEV/MAV e il calcolo delle sedute eseguite devono continuare a filtrare rigidamente per `Event.stato == 'Completato'`, in quanto gli stati penali non corrispondono ad attività fisica reale.
*   `client_avatar.py:L635` (`Q16: Next scheduled PT session`):
    Deve cercare solo il primo evento futuro in stato `Programmato`.

---

## 4. Modifiche Infrastrutturali (Validazione ed Enum)

1.  **Validazione degli stati in agenda**:
    Aggiornare la costante dei valori accettati in [agenda.py:L41](file:///c:/Users/gvera/Projects/FitManager_AI_Studio/api/routers/agenda.py#L41):
    ```python
    VALID_STATUSES = {"Programmato", "Completato", "Cancellato", "Rinviato", "Cancellato_Tardivo", "No_Show"}
    ```
2.  **Tipo Frontend e Schemi**:
    Aggiornare lo schema Pydantic `EventResponse` e la corrispondente interfaccia TypeScript in `frontend/src/types/api.ts` per includere i due nuovi stati nella tipizzazione dell'agenda.

---

## 5. Oracolo di non-regressione e Test

### 5.1 Test Unitari Backend
Creare una suite di test specifica `tests/test_late_cancel_no_show.py` che verifichi:
1.  Il consumo di crediti su un contratto misto con eventi `Completato`, `Cancellato_Tardivo` e `No_Show`.
2.  L'invarianza delle metriche scientifiche del cliente (carico ed EMG) rispetto ai Late Cancel.
3.  La corretta generazione di un settlement con trattenuta delle penali a favore del trainer.

### 5.2 Test di Non-Regressione Cassa
Eseguire il comando di verifica generale prima e dopo la modifica per garantire l'assenza di anomalie o deviazioni sugli aggregati storici di cassa:
```bash
pytest tests/ -v
```
Tutti i test contabili esistenti devono passare senza alcuna violazione degli invarianti finanziari ratificati in `assert_contract_invariants`.

---

## 6. [Bridge Code 2026-07-03] Correzioni code-grounded + censimento denylist (Step 0 eseguito)

**Sequenza ratificata dal founder: Step 0 (prep, behavior-preserving) → Step 1 (stati nuovi).**

### 6.1 Correzioni all'inventario (verificate sul codice vivo, post-G9.3)

- **§3.2 indicava il modulo SBAGLIATO**: `contract_settlement.py` è PURO (riceve `sedute_erogate: int`,
  zero query — è il cuore di ADR-016, presidiato dal grep-guard). Il conteggio vive in
  `transitions.count_sedute_erogate` (post-G9.3a). Step 1 interviene LÌ: `count_sedute_erogate` resta
  SOLO-Completato (nome onesto), si AFFIANCA `count_sedute_penali` (Cancellato_Tardivo+No_Show);
  `settlement_for` passa la somma come contabilizzabile; l'audit snapshot SEPARA i due numeri
  (erogate vere vs penali — difesa documentale del trainer).
- **Siti occupazione reali: 15** (12 ORM + 3 raw-SQL workspace + 2 raw-SQL dashboard = 17 totali,
  il conteggio della spec era quasi giusto). Post-G9.3d l'auto-close è UN sito (`transitions.
  sync_contract_chiuso`), non due (l'inventario citava ancora `agenda.py` sync + `rates.py` inline).
- **Step 0 FATTO**: predicato estratto a SSoT `contract_state.STATI_OCCUPAZIONE_CREDITO`
  (frozenset, ADR-017), TUTTI i 17 siti consumano il simbolo (ORM `.in_(...)` + raw SQL via
  bindparam expanding). Test semantico `tests/test_occupazione_ssot.py` VIETA i literal fuori dal
  SSoT (enforcement, non enumerazione — gemello G9.4-style del grep-guard ADR-017). **Step 1 = 2
  stati aggiunti a 1 frozenset**, non 17 siti.

### 6.2 Censimento denylist `!= 'Cancellato'` (21 siti — l'inventario originale li TACEVA)

Stati nuovi in una denylist = inclusione AUTOMATICA e silenziosa. Classificazione per Step 1:

| Gruppo | Siti | Semantica | Decisione Step 1 |
|---|---|---|---|
| Recency/engagement ("ultimo contatto", inattivi) | workspace 1613/1635/1639/2304 · dashboard 936/955/959/1191 · clients 407/473/506/554/754 · client_avatar 582/612 | Un No_Show È un appuntamento recente (relazione viva) anche se non svolto | **INCLUDONO (nessun cambio)** — il cliente non è "sparito"; il churn guarda la relazione, non la performance |
| Calendario/timeline giorno | workspace 302/686 · session_prep 188/227 · dashboard 137 | Slot e timeline mostrano anche penali (storia reale della giornata) | **INCLUDONO (nessun cambio)** — display; l'overlap-check (allowlist Programmato+Completato) resta com'è per D-CALENDAR-OVERLAP |
| Credit breakdown (GROUP BY stato) | contracts 562 (guard ADR-017) | I nuovi stati COMPARIRANNO nel breakdown | **VERIFICARE il mapping** in Step 1: chiavi nuove nel dict → il consumer FE non deve perderle in silenzio (campo `sedute_penali` additivo; display pieno in G8.4) |

**Regola:** nessun sito denylist cambia in Step 1; chi vorrà ESCLUDERE le penali da una metrica dovrà
farlo come decisione esplicita per-sito, mai di default.

### 6.3 Decisioni residue per Step 1 (proposte bridge, da ratificare a implementazione)

- **FSM stati Event**: `Programmato → Cancellato_Tardivo/No_Show` = flusso primario (legale).
  `Completato → Cancellato_Tardivo/No_Show` = PERMESSO (correzione; entrambi occupano il credito,
  zero cassa pre-settlement — il guard "Bouncer 4" resta scope-ristretto a `→Rinviato` come da
  decisione G7.8#2). Transizioni fra stati non-performance libere.
- **⚠️ Punto tributarista (stesso trattamento di `pro_sedute` PROVISIONAL)**: la penale trattenuta nel
  conguaglio di recesso (D-RECESSO-PENALE) è esigibile SOLO se pattuita nel contratto col cliente
  (Codice del Consumo). Il software PROPONE col metodo standard, il microcopy resta
  proposta-non-obbligo (framing G7.3). Non blocca il build; blocca la valorizzazione del claim.
