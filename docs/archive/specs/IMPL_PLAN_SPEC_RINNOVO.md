# PIANO DI IMPLEMENTAZIONE — SPEC_RINNOVO_E_CONTRATTI_DA_PIANIFICARE

**Versione:** 1.0
**Data:** 2026-06-19
**Owner:** Giacomo Verardo (AVGV Technologies)
**Esecutore:** Claude Code
**Spec di riferimento:** `SPEC_RINNOVO_E_CONTRATTI_DA_PIANIFICARE.md` (v1.2), `TASSONOMIA_FINANZIARIA.md` (v1.1)
**Decisione architetturale:** `docs/adr/ADR-014-gestione-finanziaria-cassa-competenza.md`

> **Natura del documento.** Piano operativo ancorato al codice reale (esplorazione 2026-06-19).
> È materiale di lavoro: viene **superato dal codice + test** una volta implementato. I riferimenti
> `file:riga` sono fotografie al 2026-06-19 — verificare sempre contro il codice corrente.

---

## 0. Scoperta che riduce il perimetro (Criterio B già parziale)

Esiste **già** la categoria alert `orphan_contracts` (`api/routers/dashboard.py:596-618`, introdotta nel
commit `bc28e3c` "contratti orfani — alert, badge ambra, onboarding 3 stati"):

```sql
SELECT COUNT(*) FROM contratti c
WHERE c.trainer_id=:tid AND c.deleted_at IS NULL AND c.chiuso=0
  AND COALESCE(c.prezzo_totale,0) > 0
  AND NOT EXISTS (SELECT 1 FROM rate_programmate r WHERE r.id_contratto=c.id AND r.deleted_at IS NULL)
```

→ Il Criterio B **non si costruisce da zero: si raffina e si rende azionabile**. Differenze vs spec §B.3:
1. Filtro `prezzo_totale > 0` invece di **residuo positivo** (`prezzo > versato`).
2. È solo un contatore con link generico `/contratti` — manca endpoint di risoluzione inline + Sheet
   azionabile (come `overdue-rates` → `OverdueRatesSheet`).
3. Manca il **cruscotto** venduto / a-rate / da-pianificare.

**Decisione (2026-06-19):** raffinare `orphan_contracts`, nessuna categoria duplicata.

---

## 1. Decisioni di prodotto bloccate (2026-06-19)

| # | Decisione | Valore |
|---|---|---|
| 1 | Categoria alert | **Raffina `orphan_contracts`** (residuo + sheet), niente categoria nuova |
| 2 | Cruscotto B.4 | **Pagina lista `/contratti`** (4° blocco KPI accanto a Attivi/Fatturato/Incassato/Rate scadute) |
| 3 | Post-rinnovo | **`/contratti/{nuovo_id}?tab=payments`** con form generazione piano aperto |

---

## 2. Criterio A — Flusso di rinnovo guidato

**Stato reale verificato:**
- Backend `renew_contract` (`api/routers/contracts.py:735`) **già conforme alla sicurezza** (trainer_id
  da JWT, `_check_client_ownership`, 404). Nessuna modifica di sicurezza richiesta.
- Frontend: rinnovo parte da `/rinnovi-incassi` (`frontend/src/app/(dashboard)/rinnovi-incassi/page.tsx:164,278`)
  → `ContractSheet` / `ContractForm`. Dopo conferma (`frontend/src/hooks/useContracts.ts:123`) lo sheet
  si chiude e il trainer **resta sulla pagina**: il passaggio al piano rate è **assente** (§A.3 confermato).
- Pre-fill attuale (`ContractForm.tsx:85-90` `RenewalDefaults`): `id_cliente, tipo_pacchetto,
  crediti_totali, prezzo_totale`. **Manca `data_scadenza` derivata dalla durata del padre** (§A.2).

**Interventi:**
| ID | Dove | Cosa |
|----|------|------|
| A1 | `ContractForm.tsx` `RenewalDefaults` + default values | Aggiungere `data_scadenza` derivata = oggi + (padre.`data_scadenza` − padre.`data_inizio`), **modificabile** |
| A2 | `useContracts.ts` `useRenewContract.onSuccess` + `ContractSheet` | Dopo rinnovo navigare a `/contratti/{nuovo_id}?tab=payments` (il nuovo id arriva dalla response del POST renew) |
| A3 | `PaymentPlanTab.tsx:76-96` | Verificare che con zero rate apra direttamente `GeneratePlanForm` (già il comportamento attuale) |

Criterio A = quasi tutto frontend + un ritocco di pre-fill. Backend invariato.

---

## 3. Criterio B — Contratti da pianificare (raffina l'esistente)

| ID | Dove | Cosa |
|----|------|------|
| B1 | `dashboard.py:596-618` query `orphan_count` | `prezzo_totale > 0` → `prezzo_totale > totale_versato` (residuo positivo, §B.3) |
| B2 | `dashboard.py` nuovo `GET /dashboard/contracts-to-plan` | Contract-first, modello `get_overdue_rates` (`dashboard.py:261`): batch fetch client, ritorna **residuo** + nome/cognome/telefono per azione |
| B3 | Frontend `ContractsToPlanSheet` + hook `useContractsToPlan` | Clone di `OverdueRatesSheet` / `useOverdueRates`; CTA "Definisci piano" → `/contratti/{id}?tab=payments` |
| B4 | `AlertHub.tsx` + `dashboard/page.tsx` | Agganciare la categoria allo Sheet (mappa `alertActions` già estensibile); icona + severity style |
| B5 | `contracts.py:216-251` KPI + `ContractListResponse`/`kpi_data` | 3 KPI cruscotto: `kpi_venduto` (Σ `prezzo` aperti), `kpi_a_rate` (Σ residui rate **non-saldate** aperti), `kpi_da_pianificare` (Σ `(prezzo−versato) − residui non-saldate` aperti) |
| B6 | `contratti/page.tsx:56-100` `CONTRATTI_KPI` | Mostrare il cruscotto (naming UI italiano da decidere) |

**Formula vincolante (tassonomia §1 Asse 3):** rate **non-saldate** = `stato ∈ {PENDENTE, PARZIALE}`
(stesso predicato di aging `Rate.stato.in_(["PENDENTE","PARZIALE"])`). Per contratti a zero rate
"da pianificare" = residuo pieno; per parziali coincide con `importo_disallineamento` di
`_to_response_with_rates` (`contracts.py:49`).

**Esclusioni cassa:** N/A in questa spec (riguarda la temporale), ma il cruscotto resta coerente con
il principio di cassa del forfettario (numeri gestionali, non GAAP).

---

## 4. Test (standard non negoziabile su logica finanziaria)

Nuovo `tests/test_contracts_to_plan.py` (+ estensione `tests/test_contract_integrity.py`):
- Contratto aperto, residuo>0, zero rate → **compare**.
- Contratto saldato in acconto senza rate (residuo=0) → **non** compare (verifica B1).
- Contratto con ≥1 rata non eliminata → non compare. Chiuso/eliminato → non compare.
- Multi-tenant: contratto di altro trainer invisibile (isolamento, 404 sul resolver).
- Riconciliazione cruscotto: `da_pianificare` per zero-rate = residuo pieno; per parziale =
  `importo_disallineamento`; somma componenti coerente.

---

## 5. Sequenza di esecuzione

Ogni step lascia il branch rilasciabile; commit intermedi; `bash tools/scripts/check-all.sh` + `pytest`
prima di ogni commit.

1. **Step 1 — Criterio A** (frontend pre-fill + navigazione guidata). Backend invariato.
2. **Step 2 — Backend B1+B5** (query residuo + 3 KPI cruscotto).
3. **Step 3 — Backend B2** (endpoint `contracts-to-plan`).
4. **Step 4 — Frontend B3+B4+B6** (sheet + aggancio AlertHub + cruscotto lista).
5. **Step 5 — Test** (`test_contracts_to_plan.py` + estensioni) + verifica riconciliazione.

---

## 6. Punti da verificare in corso d'opera

- **Path endpoint piano rate**: i due agenti di esplorazione riportano `POST /generate-plan/{id}`
  (backend) vs `POST /contracts/{id}/payment-plan` (frontend hook). Verificare il route reale al
  momento di A2/B3.
- **Response del POST renew**: oggi ritorna `ContractResponse` (`contracts.py:814` `_to_response`) →
  contiene `id` del figlio, sufficiente per la navigazione A2.

---

## 7. Bridge rule

Output non banale (scelte su endpoint, forma cruscotto, navigazione) → learning capture in chat +,
se vincolante, riflesso in `BUILD_LOG.md`. A implementazione conclusa: aggiornare `api/CLAUDE.md`
(nuovo endpoint dashboard + KPI) e marcare questo piano come "superato dal codice".
