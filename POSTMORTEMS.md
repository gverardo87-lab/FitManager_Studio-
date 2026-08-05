# POSTMORTEMS.md - FitManager AI Studio

Questa non e' una fonte di regole nuove.
Raccoglie solo lezioni concrete da errori gia' emersi, per evitare che la memoria orale torni a guidare il progetto.

## 2026-08-05 - Grafico Cassa giornaliero: delta corretto, flussi lordi falsificati (P1)

Problema:
- il 24 luglio aveva 333,25 € di inflow e 537,50 € di rimborsi, delta saldo −204,25 €; il grafico
  mostrava Entrate 0 e Uscite 204,25 perché `/movements/stats` nettava i contra-ricavi e ribaltava il
  bucket negativo nell'altra serie
- ledger, saldo e ancore contratto/wallet erano corretti: il difetto era di rappresentazione, ma
  rendeva falso il significato esplicito “Entrate e uscite per giorno”
- la remediation dell'incident 2026-07-03 aveva coperto il KPI mensile lordo/rimborsi, non ogni
  timeslice né le superfici adiacenti; l'audit ha trovato anche empty state basato sul segno,
  conguagli nel bucket rate, invalidazioni cache divergenti e hint audit hardcoded

Lezioni:
- conservare il delta non equivale a conservare i fatti: un grafico di cassa bidirezionale deve
  mantenere inflow e outflow lordi separati e riconciliare entrambi con la variazione saldo
- ogni fix di trasparenza finanziaria richiede un canary sulla minima slice temporale esposta, non
  soltanto sul totale mensile
- esistenza del dato e segno del netto sono assi diversi: zero o negativo non significa empty
- tassonomie e invalidazioni condividono la stessa legge strutturale: insieme chiuso, interprete
  unico, totalità fail-loud e test gemello di esaustività/simmetria
- report completo: `docs/incidents/INC-2026-08-05-grafico-cassa-netting-rimborsi.md`

## 2026-07-03 - Falso allarme: entrate negative in Cassa percepite come bug del rimborso (P2 - trasparenza)

Problema:
- card "Entrate" Cassa/luglio = −140,42 € (375 incassi lordi − 515,42 rimborsi da terminazioni di test); filtro "Solo entrate" del Mastro non mostrava nulla di negativo (i rimborsi sono USCITA) → founder in massima allerta ipotizzando bug nelle logiche G7/G8
- investigazione fino ai contratti sorgente: ZERO bug, settlement esatti al centesimo, ciclo terminate→reopen→ri-terminate conforme ADR-019. Il numero era il contra-ricavo G7.5 applicato correttamente
- root cause dell'ALLARME (non del calcolo): KPI netto senza componenti esposti (`/stats` non espone lordo/rimborsi) + KPI in lingua "conto economico" vs lista in lingua "cassa" senza ponte + read-model cassa decentralizzato in ~6 interpreti inline + default silenzioso in lettura (categoria ignota classificata per esclusione, mentre la penna G9.1 e' fail-loud)

Lezioni:
- un falso allarme e' un incident reale: la sua root cause e' sempre debito di trasparenza. Numero giusto ma inspiegabile in-place = difetto di prodotto. Se il progettista va in allarme, il trainer andra' nel panico (cfr. INC-2026-06-08)
- nessun KPI netto nudo: ogni netto espone i componenti in API e in UI ("Lorde X · Rimborsi −Y")
- anticipare non e' disciplina, e' struttura: chiudi l'insieme / un solo interprete per asse / totalita' fail-loud / gemello di esaustivita' che vigila in CI. La rincorsa delle logiche (G7.5, ADR-017, ADR-022) ha sempre la stessa anatomia: semantica nata in un punto, interpretata in N punti che nessuna struttura enumera
- il read-model della cassa e' il gemello mancante della penna (G9.1): serve `classify(movement) → classe` totale e fail-loud in `cash_categories.py`, consumato da tutte le superfici
- report completo: `docs/incidents/INC-2026-07-03-falso-allarme-entrate-negative-cassa.md`

## 2026-06-18 - Fingerprint hardware parziale → blocco CRM ricorrente (P1)

Problema:
- Chiara (v1.0.10) si vede chiedere la `license.key` e bloccare il CRM "ogni tanto"; workaround scoperto da lei: riavviare l'app. Oltre 45 episodi in 3 mesi nei log (`Fingerprint parziale: 2/3 identificatori`)
- `machine_id` della licenza = SHA-256 di 3 valori hardware letti via PowerShell/WMI. Su alcune macchine le query falliscono a intermittenza (sistema sotto carico, antivirus, risveglio da sleep) ritornando stringa vuota
- `_compute_fingerprint` hashava anche un set PARZIALE (`sha256("cpu||bios")`) → hash diverso dal `machine_id` firmato → `wrong_machine` → 403 → redirect a `/licenza`. Ritornava `"unavailable"` SOLO se tutte e 3 fallivano
- `get_machine_fingerprint` CACHAVA il valore (anche sbagliato) per tutta la vita del processo → sessione bloccata fino al riavvio (= "logout/login risolve")
- correlazione "WiFi palestra" = coincidente, non causale (cambio rete ≈ risveglio da sleep, WMI fiacco)

Lezioni:
- un identificatore di sicurezza si calcola su un set COMPLETO e DETERMINISTICO, o si fallisce in modo esplicito e recuperabile (`unavailable`) — MAI degradare a "uso quello che ho": set variabile → hash variabili → mismatch. Degradazione parziale ok per un display, mai per un binding
- NON cachare i fallimenti transitori di una risorsa esterna fiacca (WMI, rete, subprocess): congela il guasto per l'intera sessione. Retry + non memoizzare l'errore
- un test che asserisce il comportamento bacato e' debito, non copertura: `test_partial_failure_still_produces_fingerprint` era VERDE e certificava il bug. Per la sicurezza l'invariante va derivata dal requisito, non dall'implementazione corrente
- il dev environment e' il caso MIGLIORE (WMI sempre 3/3), non quello rappresentativo: per logica dipendente dall'OS, il test deve simulare il degrado
- fix in v1.0.13 (3 parti: mai hash parziale, cache solo del completo, retry); hash 3/3 invariato → licenze esistenti restano valide; report: `docs/incidents/INC-2026-06-18-fingerprint-partial-license-lockout.md`

## 2026-06-15 - Upgrade installer bloccato da frpc.exe orfano (P2)

Problema:
- installando v1.0.11 sopra v1.0.10, l'installer Inno Setup fallisce con `ERROR_ACCESS_DENIED` (codice 5) sovrascrivendo `backend\frpc.exe`
- causa: un `frpc.exe` orfano di una sessione precedente teneva il lock sul proprio binario (un .exe in esecuzione locka il proprio file immagine)
- `frpc` e' un processo NIPOTE detached (launcher.bat → fitmanager.exe → frpc.exe via Popen `CREATE_NO_WINDOW`); il suo cleanup dipendeva solo da `atexit` + shutdown ASGI, che NON scattano su chiusura brusca (finestra del launcher chiusa) → orfano persistente
- l'installer non chiudeva i processi prima di sovrascrivere i binari
- condizione latente dalla ~v1.0.10 (prima versione a bundlare frpc.exe, 2026-06-09); emersa al PRIMO upgrade che doveva rimpiazzare quel binario

Lezioni:
- ogni processo figlio/nipote a vita lunga lanciato dal backend DEVE morire col backend via meccanismo del SO (Windows Job Object `KILL_ON_JOB_CLOSE`), MAI col solo `atexit`/shutdown ASGI — per un'app desktop la chiusura brusca e' la norma
- un installer che aggiorna binari bundlati DEVE chiudere i processi che li usano prima di scrivere (`CloseApplications` + `taskkill` per nomi app-specifici)
- bundlare un nuovo binario a vita lunga e' un rischio di upgrade latente: chiedersi sempre "puo' essere in uso durante un aggiornamento?"
- difesa in profondita': correggere causa (codice, niente orfani) E sintomo (installer chiude), perche' le macchine gia' deployate hanno il binario orfanabile — solo il fix installer le sblocca al prossimo upgrade
- fix in v1.0.12; report completo: `docs/incidents/INC-2026-06-15-installer-frpc-lock.md`

## 2026-04-19 - catalog.db tassonomia vuota dopo consegna v1.0.7 (P0)

Problema:
- 6 tabelle tassonomiche di catalog.db consegnate vuote al primo partner (Alessio Crociani, v1.0.7)
- Safety Engine rilevava condizioni cliniche dall'anamnesi ma trovava zero esercizi associati — note di sicurezza completamente vuote
- causa: rebuild di catalog.db durante audit esercizi senza riesecuzione dei 3 script manuali di tassonomia (`seed_taxonomy`, `populate_taxonomy`, `populate_conditions`)
- i 3 script non erano ne' nel seed al startup ne' nel build pipeline ne' nella release checklist

Lezioni:
- ogni tabella di catalog.db DEVE avere un seed al startup o un check nel build pipeline — se il popolamento dipende da esecuzione manuale, prima o poi verra' dimenticato
- rebuild di catalog.db = riesecuzione COMPLETA della pipeline seed (3 step in ordine: tassonomia base → junction muscoli/articolazioni → junction condizioni)
- il build pipeline DEVE verificare l'integrita' completa di catalog.db (count > 0 per OGNI tabella tassonomica), non solo esercizi
- audit pre-consegna DEVE includere conteggio tabelle tassonomiche con soglia minima attesa
- report completo: `docs/incidents/INC-2026-04-19-catalog-taxonomy-empty.md`

## 2026-03-28b - FK Cascade mancante su replace_sessions (P1)

Problema:
- `_delete_sessions_cascade` in `workouts.py` eliminava logs → esercizi → blocchi → sessioni, ma NON eliminava `WorkoutScheduleSlot` (FK su `id_sessione`)
- il PUT `/workouts/{id}/sessions` (full-replace) crashava 500 su qualsiasi scheda con schedule generato
- errore mascherato da CORS al frontend (crash prima del middleware CORS → no header `Access-Control-Allow-Origin`)
- bug presente sin dall'introduzione degli schedule slots, ma emerso solo quando un utente ha generato e poi ri-salvato la scheda

Lezioni:
- ogni nuova tabella con FK su `sessioni_scheda.id` DEVE essere aggiunta a `_delete_sessions_cascade` — non basta aggiungere il modello e il router
- crash 500 mascherato da CORS: SEMPRE guardare stderr/log uvicorn prima di diagnosticare come errore CORS (stessa lezione di INC-2026-03-28)
- il dominio workout aveva ZERO test (337 test totali, nessuno sul CRUD schede) — ora 12 test specifici in `test_workouts_crud.py`
- test chiave: `test_replace_sessions_with_schedule_no_500` riproduce esattamente il bug

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
