# INC-2026-07-03 — Falso allarme: entrate negative in Cassa (−140,42 €) percepite come bug del rimborso

- **Data**: 2026-07-03 (sera)
- **Gravita'**: NESSUNA sull'asse denaro (verificato al centesimo) — **P2 di trasparenza/metodo**
- **Classe**: **FALSO ALLARME** — primo incident di questa classe registrato deliberatamente
- **Impatto**: sessione di investigazione d'emergenza ("MASSIMA ALLERTA — GRAVISSIMO"); fiducia nel numero incrinata nel momento in cui il progettista stesso non sapeva spiegarlo dalla UI
- **Scope**: card KPI "Entrate" pagina Cassa (`GET /movements/stats`, `api/routers/movements.py`) + filtro "Solo entrate" del Libro Mastro
- **Rilevato da**: Giacomo Verardo (founder) — registrato a suo nome su sua richiesta esplicita
- **Trigger**: terminazioni di test eseguite lo stesso pomeriggio (G7.9/G8.1 sul DB di sviluppo)

---

## Executive Summary

La card "Entrate" della Cassa mostrava **−140,42 €** per luglio 2026 (percepito come "~142 in negativo"). Il Libro Mastro filtrato "Solo entrate" non mostrava alcun movimento negativo. Il founder ha dichiarato massima allerta ipotizzando un bug nelle nuove logiche di rimborso (G7/G8).

L'investigazione ha verificato l'asse denaro fino ai contratti sorgente: **zero bug di calcolo**. Il numero e' il comportamento contra-ricavo di G7.5 applicato correttamente: luglio aveva 375,00 € di incassi lordi e 515,42 € di rimborsi da terminazione (contratti 19 e 39 + erogazione wallet 0,75 €), quindi entrate nette = 375,00 − 515,42 = −140,42 €. Il filtro lista non mostra nulla di negativo perche' i rimborsi sono fisicamente movimenti USCITA: il KPI li sottrae, la lista li classifica tra le uscite.

**Il falso allarme E' l'incident.** Se chi ha progettato il contra-ricavo non riesce a spiegare il proprio numero guardando la propria UI, un trainer in produzione andra' nel panico (precedente reale: INC-2026-06-08, Chiara e il "fatturato che cala"). La root cause non e' nel calcolo ma nella struttura: KPI netto senza componenti esposti + read-model della cassa decentralizzato in ~6 interpreti inline.

---

## Cronologia

| Quando | Evento |
|--------|--------|
| 2026-07-03 16:45–17:48 | Terminazioni di test sul DB dev: contratto 19 (rimborso 376,67 €), contratto 39 (terminazione SALDO_TRAINER → reopen → ri-terminazione con rimborso 138,00 € + wallet 0,75 € erogato) |
| 2026-07-03 sera | Founder apre Cassa/luglio: "Entrate" = −140,42 €; filtro "Solo entrate" mostra solo +375 → allarme bug rimborsi, "GRAVISSIMO" |
| 2026-07-03 sera | Investigazione: query dirette su crm.db, ricalcolo manuale dei settlement, audit trail contratti 19/39 → verdetto: matematica esatta, design G7.5 rispettato |
| 2026-07-04 | Analisi di metodo (founder + Claude Code): la classe di problema e' strutturale, non puntuale. Registrazione di questo INC + cattura learning |

---

## Root Cause Analysis — dell'ALLARME, non di un bug

Il calcolo era corretto. L'allarme ha **quattro concause strutturali**:

### RC1 — KPI netto senza componenti esposti
`MovementStatsResponse` non espone `entrate_lorde` ne' `rimborsi_contratti`: la card "Entrate" puo' solo mostrare il netto. Un numero negativo senza scomposizione non e' spiegabile *dalla UI stessa* — serve un'indagine sul DB per capirlo. Un netto nudo e' un numero che chiede un atto di fede.

### RC2 — Asimmetria semantica KPI ↔ lista, senza ponte
Il KPI parla la lingua del **conto economico** (entrate nette dei contra-ricavi, G7.5); la lista Mastro parla la lingua della **cassa** (movimenti lordi per tipo). Entrambe legittime, ma la UI non dichiara da nessuna parte che sono due lingue diverse. Il filtro "Solo entrate" che non trova il negativo e' la trappola percettiva esatta.

### RC3 — Read-model della cassa decentralizzato (~6 interpreti inline)
`get_movement_stats`, `_compute_variable_burn_rate`, forecast, financial-trend, `monthly_revenue` (dashboard), split view (FE): ognuno decide *inline*, per proprio conto, come trattare ogni categoria (`STORNO_SPESA_FISSA` = rettifica, `RIMBORSO_CONTRATTO` = contra-ricavo, ...). G7.5 fu letteralmente la rincorsa di queste superfici. Ogni nuova categoria richiede N decisioni manuali che nessuna struttura elenca.

### RC4 — Default silenzioso in lettura (fail-silent)
Nelle query aggregate una categoria non riconosciuta finisce nei ricavi o nei costi variabili **per esclusione**. La penna di scrittura (G9.1, `ledger.py`) su categoria ignota fa `ValueError` (fail-loud); la lettura assegna semantica implicita alle categorie future senza dirlo a nessuno. Scrittura fail-loud, lettura fail-silent: il gemello cattivo.

---

## Verifica eseguita (l'asse denaro regge)

| Verifica | Esito |
|----------|-------|
| Movimenti luglio su crm.db reale (inclusi soft-deleted) | 1 ENTRATA (375,00) + 3 USCITA RIMBORSO_CONTRATTO (376,67 + 138,00 + 0,75) → netto −140,42 ✓ |
| Settlement contratto 19 (Jessica): 1450/30 sedute × 16 contabilizzate = 773,33 reso; 1150 versato → credito 376,67 | Rimborso 376,67 esatto ✓ |
| Settlement contratto 39 (Giacomo): 480/12 × 6 = 240 reso; 378,75 versato → credito 138,75; rimborso editato 138,00 + 0,75 a wallet (erogato, SALDATO) | Esatto, ADR-020 rispettato ✓ |
| Ciclo terminate → reopen → ri-terminate su 39 | Conforme ADR-019: cassa preservata, ricalcolo net-aware, nessun doppio rimborso ✓ |
| `residuo()` sui contratti chiusi | = 0 su entrambi (net-aware) ✓ |
| Doppi conteggi (wallet contato due volte, movimenti orfani) | Nessuno ✓ |

---

## Lezioni

### L1 — Un falso allarme e' un incident reale, e si registra
Il costo e' concreto: una sessione d'investigazione d'emergenza, fiducia nel sistema incrinata. E la sua root cause e' sempre un **debito di trasparenza**: il sistema aveva ragione ma non sapeva dimostrarlo. Regola: *numero giusto ma inspiegabile in-place = difetto di prodotto*, con dignita' di INC. N falsi allarmi non gestiti = il trainer smette di guardare i KPI.

### L2 — Nessun KPI netto nudo
Ogni KPI che e' un NETTO (lordo − contra) deve esporre i componenti nel contratto API e mostrarli in UI (pattern "Lorde X · Rimborsi −Y"). Vale gia' per lo storno spese fisse (trattato come rettifica); il contra-ricavo deve avere lo stesso trattamento di trasparenza.

### L3 — Anticipare non e' disciplina, e' struttura (il metodo in 4 regole)
La rincorsa delle logiche (G7.5, ADR-017 "5 produttori", ADR-022 "7 siti di scrittura") ha sempre la stessa anatomia: *una semantica nasce in un punto, va interpretata in N punti, nessuna struttura enumera gli N punti*. Il metodo che il progetto ha gia' convergentemente scoperto:
1. **Chiudi l'insieme** — ogni asse di variabilita' e' un set chiuso enumerato in UN modulo;
2. **Un solo interprete per asse** — i consumer chiamano la funzione del SSoT, mai re-inline;
3. **Totalita' per costruzione** — valore ignoto = errore rumoroso, mai default implicito;
4. **Il gemello che vigila** — un test di esaustivita' fallisce quando nasce un membro senza trattamento dichiarato (pattern `test_occupazione_ssot.py`).
Quando valgono tutte e quattro, la rincorsa la fa la CI, non il founder in produzione.

### L4 — Il read-model della cassa e' il gemello mancante della penna
`contract_state.py` centralizza la lettura del contratto; la penna (G9.1) centralizza la scrittura della cassa; **la lettura della cassa non ha SSoT**. Il pezzo mancante e' una classificazione canonica (`classify(movement) → RICAVO | CONTRA_RICAVO | COSTO_FISSO | RETTIFICA_COSTO_FISSO | COSTO_VARIABILE`) in `cash_categories.py`, totale e fail-loud, consumata da tutte le superfici. ADR-019 aveva gia' previsto questo rischio quando scarto' lo storno-in-cassa ("andrebbe escluso in tutti gli aggregati — di nuovo la superficie G7.5").

---

## Azioni preventive

| # | Azione | Stato |
|---|--------|-------|
| 1 | Registrare questo INC + voce POSTMORTEMS + cattura learning (LEARNING_PROGRAMMAZIONE §Concetti dal campo) | COMPLETATO (2026-07-04) |
| 2 | Addendum ADR-022: il read-model della cassa e' il gemello di lettura della penna (governance prima del codice) | TODO |
| 3 | SPEC_G9: gate read-model cassa — enum classi di lettura, mappa categoria→classe, migrazione delle ~6 superfici, test di esaustivita' come AC | TODO |
| 4 | `/movements/stats` espone i bucket (`entrate_lorde`, `rimborsi_contratti`) + sub-label UI sulla card Entrate | TODO (dentro il gate, non come cerotto) |
| 5 | Valutare agente auditor "nascita di una semantica" (rilevazione interpreti impliciti nel diff, gemello semantico di docs-code-drift-auditor / financial-invariant-verifier) | IN DISCUSSIONE |
