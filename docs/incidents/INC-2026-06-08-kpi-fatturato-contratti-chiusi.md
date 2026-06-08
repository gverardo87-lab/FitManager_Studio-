# INC-2026-06-08 — KPI Fatturato/Incassato escludevano contratti chiusi

- **Data**: 2026-06-08
- **Gravita'**: CRITICA (P1)
- **Impatto**: Fatturato e Incassato nella pagina Contratti calavano ad ogni chiusura di contratto saldato — percezione di business in declino costante
- **Scope**: KPI pagina Contratti (backend `api/routers/contracts.py`)
- **Durata disservizio stimata**: dal primo contratto chiuso da Chiara (circa febbraio/marzo 2026) a fix (2026-06-08) = ~4 mesi
- **Rilevato da**: Chiara Bassani (utente produzione) tramite confronto di 2 backup

---

## Executive Summary

I KPI "Fatturato" e "Incassato" nella pagina Contratti sommavano SOLO i contratti con `chiuso=False`, escludendo tutti i contratti completati e chiusi. Ogni volta che un contratto veniva saldato e chiuso (flusso naturale del business), il suo `prezzo_totale` e `totale_versato` scomparivano dai KPI, dando l'impressione che il fatturato stesse diminuendo nel tempo.

Chiara ha segnalato il problema dopo mesi di utilizzo, notando un calo progressivo e crescente dei numeri nonostante un'attivita' in crescita. Il confronto tra due backup (02-giu e 08-giu) ha confermato: incassi reali +EUR1.000, KPI fatturato -EUR1.940, KPI incassato -EUR940.

---

## Cronologia

| Ora | Evento |
|-----|--------|
| ~2026-02 | Chiara inizia a usare il software in produzione con clienti reali |
| ~2026-03 | Primi contratti vengono chiusi (saldati + crediti esauriti = auto-close) |
| 2026-06-08 | Chiara segnala: "il programma fa calare il fatturato nel tempo sempre di piu'" |
| 2026-06-08 | Analisi dei 2 backup conferma il bug |
| 2026-06-08 | Fix applicato, 361 test pass, commit `943a8c1` |

---

## Root Cause Analysis

### Il bug — Filtro `if not c.chiuso` su KPI cumulativi

**File**: `api/routers/contracts.py:225-226`

```python
# PRIMA (BUG): sommava solo contratti aperti
kpi_fatturato = round(sum(c.prezzo_totale or 0 for c in all_contracts if not c.chiuso), 2)
kpi_incassato = round(sum(c.totale_versato for c in all_contracts if not c.chiuso), 2)

# DOPO (FIX): somma tutti i contratti non eliminati
kpi_fatturato = round(sum(c.prezzo_totale or 0 for c in all_contracts), 2)
kpi_incassato = round(sum(c.totale_versato for c in all_contracts), 2)
```

La variabile `all_contracts` era gia' filtrata per `deleted_at == None` (riga 219). Il filtro `if not c.chiuso` era ridondante per escludere i soft-deleted e dannoso per i chiusi legittimi.

### Perche' il bug era insidioso

1. **Progressione lenta**: il calo era proporzionale al numero di contratti chiusi. Nei primi mesi (pochi chiusi) era impercettibile. Dopo 4+ mesi di attivita' il delta diventa evidente.
2. **Conferma percettiva**: "meno clienti attivi = meno fatturato" sembra plausibile — il bug confermava un bias anziche' contraddirlo.
3. **Nessun test di regressione**: i test backend verificavano la struttura della risposta e il bouncer, non la correttezza semantica dei KPI aggregati.
4. **KPI "Attivi" corretto**: il conteggio contratti attivi (filtrato per `not c.chiuso`) era semanticamente giusto, mascherando il fatto che lo stesso filtro fosse sbagliato per fatturato/incassato.

---

## Impatto numerico (dati reali Chiara)

| Metrica | 02-giu (BUG) | 08-giu (BUG) | Delta BUG | 08-giu (FIX) |
|---------|-------------|-------------|-----------|-------------|
| kpi_fatturato | EUR16.567 | EUR14.627 | **-EUR1.940** | **EUR24.467** |
| kpi_incassato | EUR10.576 | EUR9.636 | **-EUR940** | **EUR19.476** |
| Incasso reale (ledger) | EUR18.881 | EUR19.881 | **+EUR1.000** | EUR19.881 |

Tra i due backup Chiara aveva:
- Chiuso contratto ID=9 (Sara Di Grumo, EUR950, SALDATO)
- Chiuso contratto ID=13 (Tiziana Sabbia, EUR990, SALDATO)
- Incassato EUR1.000 in nuovi pagamenti

Il KPI le diceva che stava perdendo soldi. La realta' era l'opposto.

---

## Perimetro del bug

| Componente | Affetto? | Note |
|------------|----------|------|
| Pagina Contratti — KPI "Fatturato" | SI | Escludeva contratti chiusi |
| Pagina Contratti — KPI "Incassato" | SI | Escludeva contratti chiusi |
| Dashboard — `monthly_revenue` | NO | Calcolato da CashMovement (corretto) |
| Dashboard — `saldo_attuale` | NO | Calcolato da CashMovement (corretto) |
| Cassa — `/movements/stats` | NO | Calcolato da CashMovement (corretto) |
| Cassa — Forecast | NO | Calcolato da Rate + CashMovement (corretto) |
| Riconciliazione | NO | Include tutti i contratti non eliminati |

Il bug era isolato alle 2 righe dei KPI nel router contratti.

---

## Fix applicato

Commit: `943a8c1`
File: `api/routers/contracts.py:225-226`
Diff: rimosso `if not c.chiuso` da entrambe le sommatorie.

Nessun impatto su altri KPI (kpi_attivi, kpi_chiusi, kpi_rate_scadute correttamente filtrati).

---

## Lezioni

### L1 — KPI cumulativi vs KPI di stato: semantica diversa, filtri diversi

"Quanti contratti sono attivi?" richiede `if not c.chiuso` (stato corrente).
"Quanto ho fatturato?" richiede TUTTI i contratti (metrica cumulativa storica).
Mischiare i due filtri in uno e' un errore logico silenzioso.

**Regola**: ogni KPI aggregato deve dichiarare esplicitamente se e' una metrica di STATO (filtra per attivi) o CUMULATIVA (include tutto). Commento inline obbligatorio.

### L2 — I bug finanziari sono invisibili nei test unitari

Nessun test verificava che il KPI fatturato includesse i contratti chiusi. I test coprivano struttura della risposta e permessi, non la correttezza del calcolo business.

**Azione**: aggiungere test di regressione specifici per la semantica dei KPI finanziari (contratto aperto + chiuso = entrambi nel fatturato).

### L3 — L'utente finale vede pattern che lo sviluppatore non vede

Chiara ha visto il calo progressivo dopo mesi di uso quotidiano. Lo sviluppatore, testando con dati di pochi giorni, non avrebbe mai notato l'effetto cumulativo.

**Azione**: per ogni KPI finanziario, testare con dataset che simulano 6+ mesi di attivita' con contratti chiusi.

### L4 — Backup come strumento di debug

Chiara ha inviato 2 backup a distanza di 6 giorni, permettendo un confronto deterministico riga per riga. Senza i backup il bug sarebbe stato molto piu' difficile da riprodurre.

---

## Azioni preventive

| # | Azione | Stato |
|---|--------|-------|
| 1 | Rimosso filtro `if not c.chiuso` da kpi_fatturato/kpi_incassato | COMPLETATO |
| 2 | Test regressione: KPI con contratti chiusi inclusi nel fatturato | TODO |
| 3 | Audit completo logica finanziaria (rate, saldo, forecast, dashboard) | TODO |
| 4 | Commento inline su ogni KPI: "stato" vs "cumulativo" | TODO |
| 5 | Rilascio installer aggiornato per Chiara | TODO |
