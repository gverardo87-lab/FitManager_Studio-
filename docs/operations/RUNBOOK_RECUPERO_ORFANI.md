# RUNBOOK — Recupero orfani reali (esecuzione trainer-driven)

**Origine:** `SPEC_G9.7` gate G9.7.2 (spec consuntivata e archiviata 2026-09-02; questo runbook è
l'unica voce che la teneva aperta). **Regola ferrea:** SOLO via endpoint auditati, MAI a mano nel DB.
**Stato:** 🟡 PENDENTE — in attesa di esecuzione founder/trainer.

## Worklist (fotografia 2026-07-09, verificare live prima di agire)

**5 orfani** — `640/641/643` (Giacomo Verardo; il 643 è nato DOPO l'audit; il suo contratto 39 è
CHIUSO → oggi «nessun contratto aperto») + `647/649` (eventi `test` del founder su Sara Di Grumo e
Dalila Floris).

## Procedura

1. **647/649 (test):** eliminarli dall'agenda (erano prove del founder) — o assegnarli se erano
   sedute vere.
2. **640/641/643 (Giacomo):** scelta esplicita founder per ciascuno (ADR-025):
   *(a)* riapri il contratto 39 (`reopen-preview` li NOMINA) → assegna dal dettaglio evento o dalla
   worklist → gestisci il contratto (ri-termina/completa); oppure
   *(b)* attendi P2 (blocco P, in HOLD) e promuovili a **prestazioni singole**.
3. **Verifica di chiusura:** alert `orphan_events` a zero (o al solo residuo scelto), crediti del
   contratto coerenti a video.

A esecuzione completata: annotare l'esito in `BUILD_LOG.md` e archiviare questo runbook con header
di esito.
