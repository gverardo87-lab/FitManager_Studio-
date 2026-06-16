# INC-2026-06-15 — Aggiornamento installer bloccato da `frpc.exe` orfano (codice 5)

- **Data**: 2026-06-15 (rilevato), 2026-06-16 (fix rilasciato in v1.0.12)
- **Gravita'**: MEDIA (P2) — blocco aggiornamento, recuperabile con intervento manuale, zero perdita dati
- **Impatto**: l'aggiornamento di una macchina gia' installata (v1.0.10 → v1.0.11) fallisce con `ERROR_ACCESS_DENIED` durante la sovrascrittura di `backend\frpc.exe`. L'installer si interrompe; senza guida l'utente non riesce a completare l'upgrade.
- **Scope**: installer (`installer/fitmanager.iss`) + ciclo di vita del processo `frpc` (`api/services/tunnel_manager.py`)
- **Durata disservizio**: nessuna (l'installazione esistente continua a funzionare; solo l'upgrade e' bloccato)
- **Rilevato da**: Giacomo Verardo, installando v1.0.11 sopra v1.0.10 sul proprio PC

---

## Executive Summary

Installando v1.0.11 sopra una v1.0.10 gia' presente, l'installer Inno Setup si e' fermato con:

```
C:\Users\gvera\AppData\Local\Programs\FitManager\backend\frpc.exe
Si e' verificato un errore durante la sovrascrittura del file esistente:
Deleted file failed; codice 5. Accesso negato.
```

`Codice 5` = `ERROR_ACCESS_DENIED`. Windows mantiene un **lock esclusivo sull'immagine `.exe` di ogni processo vivo**: finche' un `frpc.exe` gira, il suo binario non puo' essere ne' cancellato ne' sovrascritto. Sulla macchina era rimasto in esecuzione un **`frpc.exe` orfano** lasciato da una sessione precedente di v1.0.10 — l'installer non poteva quindi rimpiazzarlo.

Due cause concorrenti: (1) `frpc` e' un processo **nipote detached** il cui cleanup dipendeva solo da `atexit` + shutdown ASGI, percorsi che **non scattano su terminazione brusca** (chiusura della finestra del launcher); (2) l'installer **non chiudeva i processi dell'app** prima di sovrascrivere i binari. La condizione era **latente dalla v1.0.10** (prima versione a includere `frpc.exe` nel bundle, Fase 1.6 del 2026-06-09) ed e' emersa al **primo aggiornamento** che doveva rimpiazzare quel binario.

---

## Cronologia

| Quando | Evento |
|--------|--------|
| 2026-06-09 | Fase 1.6 tunnel: `frpc.exe` bundlato nell'installer per la prima volta (~v1.0.10). Condizione latente introdotta. |
| (uso normale) | Trainer avvia v1.0.10 → il backend (lifespan step 6) avvia `frpc.exe` come processo nipote. |
| (uso normale) | Trainer chiude la finestra del launcher → `fitmanager.exe` termina, ma `frpc.exe` (nipote detached) **resta orfano** e continua a girare. |
| 2026-06-15 | Trainer lancia l'installer v1.0.11 sopra v1.0.10 → fallisce su `backend\frpc.exe` (codice 5). |
| 2026-06-16 | Root cause analysis, fix doppio (Job Object + installer), release v1.0.12. |

---

## Root Cause Analysis

### Albero dei processi

```
launcher.bat  (finestra cmd)
   └─ start /B fitmanager.exe          ← backend (figlio diretto del cmd)
         └─ subprocess.Popen frpc.exe  ← tunnel (NIPOTE, CREATE_NO_WINDOW)
```

`frpc` viene avviato da `TunnelManager._launch()` (`api/services/tunnel_manager.py`) con `subprocess.Popen(..., creationflags=CREATE_NO_WINDOW)` — un processo **nipote, senza finestra, non nel gruppo console del cmd**.

### Causa primaria — cleanup affidato a percorsi "gentili"

La terminazione di `frpc` dipendeva da due soli meccanismi:

1. `atexit.register(self._cleanup)` — gira **solo** se l'interprete Python chiude in modo pulito.
2. `_tunnel_manager.stop()` nel lifespan shutdown (`api/main.py`) — gira **solo** se uvicorn riceve uno shutdown ASGI ordinato.

Quando l'utente **chiude la finestra del launcher** (modo normale di "spegnere" l'app), il `cmd` muore e `fitmanager.exe` (figlio diretto) viene terminato, ma **nessuno dei due percorsi di cleanup scatta** su una `TerminateProcess`. `frpc.exe`, essendo un nipote detached in un proprio contesto, **sopravvive come orfano** e continua a girare a tempo indefinito.

### Causa che trasforma l'orfano in blocco — lock sull'immagine .exe

Un eseguibile in esecuzione su Windows ha il proprio file immagine **mappato in memoria e lockato**: non puo' essere cancellato/sovrascritto finche' il processo vive. L'`frpc.exe` orfano teneva quindi bloccato `backend\frpc.exe`.

### Causa che lo rende fatale all'upgrade — installer senza pre-chiusura

`installer/fitmanager.iss` non aveva ne' `CloseApplications` (Restart Manager) ne' alcun `taskkill`: provava a sovrascrivere `backend\frpc.exe` "a caldo" e falliva direttamente con codice 5.

### Perche' non rilevato prima

- **Prima volta che si rimpiazza `frpc.exe`**: il binario e' nel bundle solo dalla ~v1.0.10 (2026-06-09). v1.0.10 → v1.0.11 e' stato il **primo upgrade** a doverlo sovrascrivere. Le installazioni precedenti (Alessio v1.0.7) non avevano `frpc.exe`.
- **Le installazioni "pulite" non lo mostrano**: su fresh install non c'e' nulla da sovrascrivere. Il bug richiede *upgrade su macchina dove l'app e' girata almeno una volta e poi e' stata chiusa* — esattamente il flusso del trainer reale.
- **Nessun test copre l'installazione**: i quality gate (pytest, ruff, next build) non eseguono l'installer ne' simulano un upgrade a caldo.

---

## Impatto

### Business
- Upgrade bloccato per la macchina con tunnel attivo gia' usata. Per un trainer non tecnico, un dialog d'errore in inglese tecnico ("codice 5") e' uno stop totale → necessita supporto.
- Riguarda i target di aggiornamento reali: Chiara (da v1.0.11) e Alessio alla prima installazione che includa `frpc.exe`.

### Tecnico
- `backend\frpc.exe` non sovrascrivibile → installer interrotto. Se l'utente sceglie "Salta questo file", resta un `frpc.exe` vecchio incoerente col resto del bundle.
- Processo `frpc.exe` orfano persistente: consuma risorse e tiene una porta/handle anche quando l'app e' "chiusa".

### Utente
- Nessuna perdita dati: `crm.db` e `data/` non sono toccati. L'installazione esistente continua a funzionare. Il danno e' limitato all'**impossibilita' di aggiornare** senza intervento manuale.

---

## Perimetro dei fix (v1.0.12)

Difesa in profondita': si correggono **sia la causa radice** (niente piu' orfani) **sia il sintomo** (installer che chiude i processi), perche' le macchine gia' deployate (v1.0.10/v1.0.11) ospitano ancora il binario orfanabile — solo il Fix A le salva al **prossimo** upgrade.

### Fix B — causa radice: `frpc` muore col backend (Windows Job Object)

| File | Modifica |
|------|----------|
| `api/services/tunnel_manager.py` | `_create_kill_on_close_job()` crea un Job Object con `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`; `_assign_process_to_job()` aggancia `frpc` al job subito dopo lo spawn. |

Il SO uccide tutti i processi del job quando l'**ultimo handle al job si chiude** — cioe' quando il processo backend (che tiene l'handle) termina, **comunque** termini (anche `TerminateProcess`). E' l'unico meccanismo affidabile su Windows contro l'orfanaggio. Fallback su `atexit`/`stop()` se il job non e' disponibile (non-Windows / errore) — comportamento invariato rispetto a prima.

### Fix A — sintomo: l'installer chiude i processi prima di scrivere

| File | Modifica |
|------|----------|
| `installer/fitmanager.iss` | `[Setup]`: `CloseApplications=yes` + `RestartApplications=no` (Restart Manager rileva i lock per file — scoping preciso, nessun collaterale su `node.exe` estranei). `[Code]` `PrepareToInstall`: `taskkill /F /T` su `frpc.exe` e `fitmanager.exe` (nomi app-specifici) prima della copia dei `[Files]`. |

---

## Verifica

| Check | Risultato |
|-------|-----------|
| Creazione Job Object su Windows reale | OK (handle valido) |
| `ruff check api/` | All checks passed |
| `pytest tests/` (preflight release) | 364 passed |
| `next build` (preflight release) | pass |
| Pipeline ADR-004 v1.0.12 | 5/5 fasi, smoke test 5/5 invarianti |
| Artifact | `FitManager_Setup_1.0.12.exe`, SHA-256 `df2d602e…fb50` |

### Procedura di sblocco manuale (macchine gia' bloccate)

Per chi e' fermo sul dialog d'errore (prima di avere l'installer v1.0.12):

```powershell
taskkill /IM frpc.exe /F
taskkill /IM fitmanager.exe /F
```
Poi "Riprova" (NON "Salta questo file", che lascerebbe il binario vecchio). Dall'installer v1.0.12 in poi questo e' automatico.

---

## Lezioni e Regole Derivate

### L1 — Ogni processo figlio/nipote del backend DEVE morire col backend via meccanismo del SO

`atexit` e lo shutdown ASGI coprono solo la chiusura "gentile". Per un'app desktop, **la chiusura brusca e' la norma** (l'utente chiude la finestra). Qualsiasi processo a vita lunga lanciato dal backend (oggi `frpc`, domani altri) DEVE essere agganciato al ciclo di vita del parent con un meccanismo del sistema operativo (Job Object kill-on-close su Windows), mai con il solo cleanup applicativo.

### L2 — Un installer che aggiorna binari bundlati DEVE chiudere i processi che li usano

Un `.exe` in esecuzione locka il proprio file immagine. Se l'installer spedisce un eseguibile a vita lunga, l'upgrade DEVE chiudere quel processo prima di sovrascriverlo: `CloseApplications` (Restart Manager, scoping per lock) + `taskkill` esplicito per i nomi app-specifici.

### L3 — Bundlare un nuovo binario a vita lunga e' un rischio di upgrade latente

Aggiungere `frpc.exe` al bundle non ha rotto nulla fino al **primo upgrade** che doveva rimpiazzarlo. Ogni nuovo runtime/eseguibile aggiunto al bundle va valutato con la domanda: *"questo file puo' essere in uso durante un aggiornamento?"* Se si', serve la pre-chiusura nell'installer + kill-on-close nel codice.

### L4 — Difesa in profondita': correggere causa E sintomo

Le macchine gia' deployate hanno il binario orfanabile: il fix del codice (Fix B) le protegge solo *dalla prossima installazione in poi*. Il fix dell'installer (Fix A) e' cio' che le sblocca **adesso**. Quando un bug ha una coda di artefatti gia' distribuiti, serve sia la prevenzione (codice) sia la remediation (installer).

---

## Azioni preventive

| Azione | Priorita' | Stato |
|--------|-----------|-------|
| Job Object kill-on-close su `frpc` (`tunnel_manager.py`) | P1 | DONE (v1.0.12) |
| Installer chiude processi prima di scrivere (`fitmanager.iss`) | P1 | DONE (v1.0.12) |
| Release v1.0.12 + tag + DEPLOYMENTS | P1 | DONE |
| Incidente documentato (`INC-2026-06-15`) | P1 | DONE |
| POSTMORTEMS.md + BUILD_LOG.md + INDEX aggiornati | P1 | DONE |
| CLAUDE.md pitfall (spawned process lifecycle + installer lock) | P2 | DONE |
| Consegna v1.0.12 a Chiara (sblocca upgrade) | P1 | TODO |
| Estendere la regola Job Object a futuri processi spawnati dal backend | P2 | TODO (regola in L1) |

---

## Classificazione

- **Tipo**: lifecycle di processo (orfanaggio nipote detached) + gap installer (sovrascrittura a caldo di binario in uso)
- **Trigger**: chiusura brusca dell'app lascia `frpc.exe` orfano → primo upgrade che deve rimpiazzare quel binario fallisce con `ERROR_ACCESS_DENIED`
- **Severita'**: P2 — blocco upgrade recuperabile, zero perdita dati
- **MTTR**: ~1 giorno dall'osservazione (2026-06-15) al fix rilasciato (2026-06-16, v1.0.12)
- **Relazione con altri incidenti**: nessuna causa condivisa; come INC-2026-04-19 e' un bug di *distribuzione* (cosa arriva/gira sulla macchina del cliente), non di logica applicativa.
