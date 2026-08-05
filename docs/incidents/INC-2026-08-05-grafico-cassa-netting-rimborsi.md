# INC-2026-08-05 — Grafico Cassa: netting giornaliero nasconde inflow e rimborso

- **Data rilevazione:** 2026-08-05
- **Giorno osservato:** 2026-07-24
- **Gravità:** **P1 rappresentazione finanziaria**; nessuna corruzione dell'asse DENARO rilevata
- **Stato:** OPEN — remediation governata da FT.1–FT.5
- **Scope:** pagina Cassa, grafico giornaliero, trend, audit timeline e invalidazioni correlate
- **Rilevato da:** founder durante verifica post sviluppo conguagli/rimborsi
- **Dati:** audit read-only del `data/crm.db` attivo; nessun dato personale riportato nel documento

---

## Executive summary

Il 24 luglio la cassa ha registrato **333,25 € di inflow** e **537,50 € di rimborsi/outflow**. Il
delta reale del saldo è quindi **−204,25 €**. Il grafico giornaliero mostra invece **Entrate 0,00 €**
e **Uscite 204,25 €**: conserva il delta, ma cancella entrambi i fatti lordi e attribuisce l'intero
netto a una sola direzione.

Il ledger, i saldi e le ancore contratto/wallet riconciliano. Il bug è nel read-model di
presentazione: dopo aver classificato il rimborso come contra-ricavo, `/movements/stats` lo sottrae
dalle entrate del giorno e, se il bucket diventa negativo, ribalta l'eccedenza nelle uscite. Questa
normalizzazione è adatta a evitare barre negative, ma semanticamente falsa un grafico che promette
“Entrate e uscite per giorno + saldo progressivo”.

È una ricorrenza della famiglia dell'incident 2026-07-03: il KPI mensile era stato reso spiegabile,
ma la copertura non aveva incluso la verità lorda di ogni slice giornaliera né le superfici adiacenti.

## Evidenza numerica

| Controllo | Esito |
|---|---:|
| Inflow reali 24/07 | 333,25 € |
| Rimborsi/outflow reali 24/07 | 537,50 € |
| Delta saldo 24/07 | −204,25 € |
| API/grafico 24/07 | Entrate 0,00 € · Uscite 204,25 € |
| Luglio inflow lordi | 848,25 € |
| Luglio rimborsi | 537,50 € |
| Luglio netto | 310,75 € |
| Saldo inizio → fine luglio | 8.932,36 € → 9.243,11 € |

Identità verificata: `8.932,36 + 310,75 = 9.243,11`. Il numero finale è corretto; la scomposizione
giornaliera mostrata non lo è.

## Root cause analysis

### RC1 — Due lingue fuse nello stesso read-model

Il KPI mensile usa correttamente la lingua economica del contra-ricavo: rimborsi sottratti agli
incassi. Il grafico giornaliero, il suo titolo e la linea saldo parlano invece la lingua della cassa
fisica. La stessa trasformazione è stata riusata senza dichiarare il cambio di semantica.

### RC2 — Normalizzazione distruttiva dei componenti

`get_movement_stats` costruisce bucket giornalieri per classe, poi ribalta un bucket negativo
nell'altra serie per evitare barre sotto zero. L'operazione preserva soltanto `entrate − uscite`,
non preserva `entrate` e `uscite` come fatti indipendenti.

### RC3 — Canary incompleto dopo l'incident precedente

La remediation del 2026-07-03 ha coperto bucket e disclosure del KPI mensile. Mancava il canary
stesso-giorno “inflow + rimborso” con l'invariante doppio: conservazione dei componenti lordi e
riconciliazione della variazione saldo.

### RC4 — Simmetria trasversale non presidiata

L'audit ha trovato quattro gap adiacenti della stessa famiglia: empty state basato sul segno del
netto, conguagli classificati come rate, query invalidations divergenti e `flow_hint` audit
hardcoded per entity type. Non corrompono il ledger, ma possono falsificare o rendere stale la
lettura finanziaria.

## Audit di integrità

| Verifica | Esito |
|---|---|
| Relazioni attive contratto ↔ ledger ↔ wallet | riconciliate |
| Tenant mismatch / IDOR relazionali nei dati | nessuno |
| Movimenti orfani o invalidi | nessuno |
| Duplicati esatti | nessuno |
| Saldo iniziale + movimenti = saldo finale | PASS |
| Anomalia legacy | rata #98 / contratto #29: piano 120,00 €, pagato 110,00 €, rata PARZIALE; contratto 110,00 €, SALDATO/chiuso |

L'anomalia legacy non cambia la cassa e non viene corretta da questo incident gate. La bonifica è
FT.5, per-record e con autorizzazione distinta.

## Contenimento

- nessuna mutazione del database durante l'audit;
- fino a FT.1 il ledger e il saldo sono le fonti affidabili per la composizione giornaliera; le due
  barre del grafico non devono essere usate come evidenza dei flussi lordi;
- nessun hotfix sul dato: il branch di sviluppo resta `FitManager_Studio` e la remediation segue i
  gate pre-POC;
- FT.1–FT.4 bloccano l'application freeze; FT.5 blocca il Real-data GO del DB interessato.

## Azioni preventive e chiusura

| Azione | Gate | Stato |
|---|---|---|
| contratto giornaliero cash-direction + canary inflow/rimborso stesso giorno | FT.1 | OPEN |
| empty state strutturale + bucket conguagli esplicito ed esaustivo | FT.2 | OPEN |
| semantica audit flow basata sul fatto, non sull'entità | FT.3 | OPEN |
| matrice/helper unico di invalidazione dei read-model finanziari | FT.4 | OPEN |
| bonifica auditata della rata legacy #98 | FT.5 | OPEN — richiede GO specifico |

L'incident chiude quando FT.1–FT.4 sono verificati e pubblicati, il grafico del 24 luglio è
validato visivamente, il verifier contabile non rileva regressioni e FT.5 è chiuso o formalmente
separato dal codice con il Real-data GO del database ancora bloccato.
