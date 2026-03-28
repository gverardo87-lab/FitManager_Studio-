# POSTMORTEMS.md - FitManager AI Studio

Questa non e' una fonte di regole nuove.
Raccoglie solo lezioni concrete da errori gia' emersi, per evitare che la memoria orale torni a guidare il progetto.

## 2026-03-28 - Safety Engine Blind Spot (P0 — demo investitore)

Problema:
- 3 bug indipendenti (cross-DB session mismatch + cache invalidation gap + UX visibility) hanno reso il profilo clinico completamente invisibile nel builder schede
- la generazione Scheda Smart crashava 500 per ogni cliente con condizioni mediche (mascherato da errore CORS)
- la BuilderSafetyCard era nascosta su desktop dietro un toggle opzionale (default OFF)
- la cache safety map non veniva invalidata dopo modifica anamnesi

Lezioni:
- `safety_engine.py` usava `session` (crm.db) per cercare `esercizi` che vivono in `catalog.db` — test in-memory con engine singolo non copre questo tipo di bug
- ogni mutation che modifica anamnesi DEVE invalidare `["exercise-safety-map", clientId]`
- informazioni cliniche MAI dietro toggle opzionale — la BuilderSafetyCard e' non negoziabile quando `condition_count > 0`
- crash 500 mascherati da CORS: guardare SEMPRE i log backend prima di diagnosticare come errore CORS
- report completo: `docs/incidents/INC-2026-03-28-safety-engine-blind-spot.md`

## 2026-03-11 - Governance sprawl

Problema:
- regole vive, roadmap, release notes e memoria storica erano finite negli stessi documenti

Lezione:
- un agente deve poter trovare in pochi minuti:
  - come lavorare
  - cosa non puo' violare
  - cosa conta per il lancio
- il resto va trattato come storico o riferimento locale, non come legge

## 2026-03-11 - `license.key` fuori da `data/`

Problema:
- su macchina installata l'app sembrava rotta, ma il runtime era sano
- la licenza era stata spostata fuori da `data/license.key`

Lezione:
- prima di classificare un caso come bug runtime, controllare la presenza fisica della licenza nella cartella dati attiva

## 2026-03-11 - Rewrite standalone contaminati da host di sviluppo

Problema:
- il bundle installer puntava ancora a un host dev baked nel frontend standalone

Lezione:
- i rewrite server-side devono restare loopback-safe
- il build deve fallire se congela destinazioni HTTP non ammesse

## 2026-03-11 - Ambiguita' su `trusted_devices`

Problema:
- alcune guide facevano sembrare `trusted_devices` equivalente a accesso senza login applicativo

Lezione:
- l'accesso di rete e l'autenticazione FitManager sono due passaggi distinti
- il Funnel pubblico serve solo per route pubbliche come l'anamnesi

## 2026-03-10 - Documenti storici scambiati per stato corrente

Problema:
- piani e snapshot vecchi sembravano ancora prescrittivi

Lezione:
- i numeri e i freeze temporanei devono vivere nel ledger upgrade o nei runbook dedicati
- i documenti autorevoli devono contenere solo cio' che resta vero oltre il microstep
