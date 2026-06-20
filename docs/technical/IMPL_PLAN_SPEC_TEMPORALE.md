# PIANO DI IMPLEMENTAZIONE — SPEC_GESTIONE_FINANZIARIA_TEMPORALE

**Versione:** 1.0
**Data:** 2026-06-20
**Owner:** Giacomo Verardo (AVGV Technologies)
**Esecutore:** Claude Code
**Spec di riferimento:** `SPEC_GESTIONE_FINANZIARIA_TEMPORALE.md` (v1.1), `TASSONOMIA_FINANZIARIA.md` (v1.1)
**Decisione architetturale:** `docs/adr/ADR-014-gestione-finanziaria-cassa-competenza.md`

> Piano operativo ancorato al codice reale (esplorazione 2026-06-20). Materiale di lavoro:
> superato dal codice + test a implementazione conclusa. I `file:riga` sono fotografie al 2026-06-20.

---

## 0. Decisioni di prodotto bloccate (2026-06-20)

| # | Decisione | Valore |
|---|---|---|
| 1 | Collocazione | **Nuova tab "Andamento" in `/cassa`** (ha già filtri mese/anno + grafici recharts) |
| 2 | "Altri incassi" + cash flow reale (§4.4) | **Inclusi subito in L1** (con confine di posizionamento §0 rispettato — vedi §5) |
| 3 | `monthly_revenue` dashboard | **Corretto** in questo workstream (allineato alla tassonomia) |
| — | Sequenza | L1 → L2 → L3, ogni layer rilasciabile da solo (spec §3) |
| — | Granularità/finestra default | Mensile, ultimi 12 periodi (toggle trimestre/anno se a basso costo) |

---

## 1. Ground-truth (cosa esiste, file:riga)

- **CashMovement** (`api/models/movement.py:25-59`): `data_effettiva: date` (base cassa), `data_movimento: datetime` (tecnico, NON usare per cassa), `tipo` (ENTRATA/USCITA), `categoria` (nullable), `importo`, `id_contratto` (NULL = fuori contratto), `id_spesa_ricorrente` (valorizzato sugli storni), `deleted_at`. Relationship `contract` (riga 58) per i join L3.
- **Costanti categoria**: `ACCONTO_CONTRATTO` (`contracts.py:35`), `PAGAMENTO_RATA` (`rates.py:44`), `STORNO_SPESA_FISSA` (letterale, `recurring_expenses.py:578,592`). **Acconti/rate hanno sempre `id_contratto`; gli storni hanno `id_contratto IS NULL` + `id_spesa_ricorrente`** → il filtro "Altri incassi" (id_contratto NULL netto storni) li esclude.
- **`Contract.data_vendita`** (`contract.py:43`): `date`, nullable, default `date.today` → competenza **best-effort sui legacy** (§5.4). Nessuna aggregazione temporale esistente.
- **Aggregazioni esistenti NON riusabili come endpoint** ma utili come pattern:
  - `/movements/stats` (`movements.py:1101`): mono-mese, grouping per-giorno, somma ENTRATA senza separare contratti/altri. Riusa: logica esclusione storni (`:1129-1153`).
  - `/movements/forecast` (`movements.py:1403`): proiezione futura; **riusa il grouping `(anno,mese)` via defaultdict + helper `_next_months`/`_prev_months` (`:1379-1400`)**.
- **`monthly_revenue`** (`dashboard.py:72-88`): `sum(ENTRATA)` generico mese corrente, **non esclude storni, non ristretto a categorie contrattuali** → sovrastima (da correggere). Consumato da `useTrainerMaturity.ts:77`.
- **`kpi_incassato` = `sum(Contract.totale_versato)`** (`contracts.py:226`), NON somma del mastro → riconciliazione: "incassi da contratti" riconcilia con la logica contratti, il cash flow reale (con Altri incassi) NO, ed è corretto (tassonomia §3).
- **Frontend riuso**: `/cassa` (`cassa/page.tsx`) 5 tab + filtri mese/anno globali; `ui/chart.tsx` (ChartContainer/ChartConfig/tooltip); `GradientKpiCard` (`movements/GradientKpiCard.tsx`); `useForecast` (`useMovements.ts:367`) come template hook; `MeasurementChart` (2 serie temporali) + `ForecastTab/ProjectionChart` (gradient/tooltip) per L2; **stacked bar già fatto** in `WeeklyPulse.tsx:186` per L3; color-map pattern in `AgingReport.tsx:26`.

---

## 2. Layer 1 — Aggregazione per periodo (cassa) + Altri incassi

**Backend (ex-novo):** endpoint `GET /movements/financial-trend?mesi=12[&granularita=mese|trimestre|anno]` (nome/forma a Claude Code, spec §4.3). Per ogni periodo (grouping `(anno,mese)` via defaultdict, pattern `forecast`):
- **Incassi da contratti** = ENTRATA, `deleted_at IS None`, trainer, **`id_contratto IS NOT NULL`** (≡ categorie `ACCONTO_CONTRATTO`+`PAGAMENTO_RATA` oggi). Spina dorsale riconciliabile.
- **Altri incassi** = ENTRATA, `id_contratto IS NULL`, **escluso `STORNO_SPESA_FISSA`** (e ogni rettifica). Partizione complementare su `id_contratto` (tassonomia §2 robustezza) → esaustiva.
- **Cash flow reale** = incassi contratti + altri = tutte le ENTRATA al netto storni.
- *(coerente)* opzionale: USCITE per periodo → saldo netto periodico.

**Criteri**: somma "incassi da contratti" riconcilia con la logica contratti; cash flow reale NON riconcilia con `kpi_incassato` (atteso). Mai un `sum(ENTRATA)` generico.

**Frontend**: tab "Andamento" (4 edit meccanici in `cassa/page.tsx`: `CassaTabKey` :99, `CASSA_TAB_SET` :100, `TabsTrigger`, `TabsContent`). KPI periodo via `GradientKpiCard` config-driven. Hook `useFinancialTrend` (clone di `useForecast`, invalidato dalle mutation cash). Tipo `FinancialTrendResponse` (modello `ForecastResponse`).

## 3. Layer 2 — Trend (2 serie) + competenza affiancata

- **Serie incassato (cassa)** per N periodi (estende L1) **+ serie venduto (competenza)** = Σ `Contract.prezzo_totale` GROUP BY periodo su `data_vendita` (query nuova). Due serie **distinte, mai sommate**; scarto leggibile.
- **Grafico**: 2 linee/aree stessa scala €. Nessun template 1:1 → assemblare da `MeasurementChart` (2 serie) + `ProjectionChart` (gradient/tooltip multi-serie). ChartContainer + ChartConfig 2-serie + custom tooltip già pronti.
- Serie competenza dichiarata **best-effort sui legacy** (§5.4).

## 4. Layer 3 — Composizione del periodo

- **Nuovi vs Rinnovi**: join `CashMovement.id_contratto → Contract.rinnovo_di` (NULL = nuovo). Relationship `movement.contract` (`movement.py:58`) facilita.
- **Acconti vs Rate**: `CashMovement.categoria` (ACCONTO_CONTRATTO vs PAGAMENTO_RATA).
- Le componenti **riconciliano col totale "incassi da contratti" del periodo** (L1).
- **Grafico**: stacked bar — template diretto `WeeklyPulse.tsx:186` (`stackId`, gradient, legenda); palette da `AgingReport` color-map.

## 5. Confine di posizionamento (vincolante — "Altri incassi" incluso subito)

Per la decisione #2, "Altri incassi"/cash flow reale entrano in L1 da subito. Invariante non negoziabile (ADR-014 §Decision.5 / tassonomia §0):
- Il software espone **cash management neutro** (quanto entra, datato, con/senza contratto). **Nessun campo, label, filtro o tooltip codifica lo stato fiscale** (dichiarato/non dichiarato). "Altri incassi" = entrate **fuori contratto** (sessioni singole, extra), nient'altro.
- Non è un parere fiscale: l'asse va validato con un tributarista. Si costruisce la vista neutra; la validazione del posizionamento resta una traccia di rischio aperta.

## 6. Fix collaterale — `monthly_revenue` (decisione #3)

`dashboard.py:72-88`: ristringere a categorie contrattuali (`id_contratto IS NOT NULL` o whitelist) + escludere storni, coerente con L1. **Verificare impatto su `useTrainerMaturity.ts:77`** (il numero cambierà: oggi sovrastima). Aggiornare/aggiungere test del summary.

## 7. Test

Nuovo `tests/test_financial_trend.py`:
- Aggregazione per periodo corretta (movimenti su mesi diversi → bucket giusti).
- Storni (`STORNO_SPESA_FISSA`) **esclusi** da incassi contratti, altri incassi e cash flow reale.
- Split incassi-contratti (id_contratto valorizzato) vs altri-incassi (id_contratto NULL).
- Cash flow reale = contratti + altri (riconciliazione).
- Serie competenza su `data_vendita`.
- L3: nuovi+rinnovi = totale contratti del periodo; acconti+rate = totale contratti del periodo.
- Multi-tenant (isolamento).
- `monthly_revenue`: test che verifica esclusione storni + restrizione categorie.

## 8. Sequenza di esecuzione

Ogni step rilasciabile; `check-all.sh` + `pytest` prima di ogni commit; commit per layer.
1. **L1** — endpoint financial-trend (incassi contratti + altri + cash flow reale) + tab "Andamento" con KPI.
2. **Fix `monthly_revenue`** (piccolo, coerente con L1; verifica trainer maturity).
3. **L2** — serie venduto (competenza) + grafico 2 serie.
4. **L3** — composizione nuovi/rinnovi + acconti/rate (stacked).
5. **Test** — `test_financial_trend.py` + aggiornamento test summary (folded per layer dove sensato).

## 9. Punti da verificare in corso d'opera

- Granularità trimestre/anno: se il grouping `(anno,mese)` si estende a `(anno, trimestre)`/`(anno)` a basso costo, includere il toggle; altrimenti L1 mensile e toggle in iterazione.
- `data_movimento` vs `data_effettiva`: usare SEMPRE `data_effettiva` per la cassa (la spec è esplicita).
- Verifica e2e (skill `/verify`) sul `crm.db` reale a fine L2/L3 (come per RINNOVO), zero scritture.

## 10. Bridge rule

Output non banale (forma endpoint/serie, grafico 2-serie, composizione, fix monthly_revenue) → learning capture in chat + riflesso in `BUILD_LOG.md`. A fine workstream: aggiornare `api/CLAUDE.md` (nuovo endpoint) e marcare questo piano "superato dal codice".
