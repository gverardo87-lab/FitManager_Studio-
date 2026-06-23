# BUILD_LOG.md

**Progetto:** FitManager — diario cronologico di sviluppo
**Scopo:** diario cronologico di cosa ho fatto, giorno per giorno. Risponde a "cosa ho fatto e quando". Per il "perche' / cosa ho imparato" rimanda ai file `LEARNING_*.md`; per il "perche' delle decisioni" agli ADR (`docs/adr/`) e ai changelog dei doc di strategia.
**Metodo:** vedi `LEARNING_METHOD.md`
**Nota di scope:** nato come diario della migrazione tunnel (Fase 0-1), ampliato il 2026-06-13 a diario generale di sviluppo per non frammentare la traccia cronologica su piu' file.
**Documenti di riferimento:** `ARCHITECTURE.md` (root, overview di sistema), `TUNNEL_ARCHITECTURE.md` + `TUNNEL_SECURITY_BOUNDARY.md` (sottosistema tunnel; consolidano i doc storici tunnel dal 2026-06-14), `EXERCISE_LIBRARY_STRATEGY.md`, `docs/adr/`

---

## Fase 0 — Infrastruttura AVGV (VPS edge)

### 2026-06-01 — Dominio
- Registrato `fitmanagerstudio.com` su Cloudflare. Attivo.
- WHOIS protetto da privacy Cloudflare.
- Nota: il dominio operativo per i tunnel nella strategia e' `fitmanager.it` (vedi TUNNEL_MIGRATION_STRATEGY D3 / wildcard `*.fitmanager.it`). Da chiarire con Claude Code quale dominio si usa per i subdomain dei trainer vs il sito vetrina. **Aperto.**

### 2026-06-02 — SSH key (preparazione pre-VPS)
- Deciso ambiente di connessione: **Windows / PowerShell** (OpenSSH gia' integrato, nessuna installazione). WSL valutato e rimandato (digressione rispetto all'hardening; da affrontare con calma piu' avanti).
- Generata coppia di chiavi Ed25519 sul PC *prima* di creare il VPS, per iniettare la pubblica alla creazione su Hetzner -> server nasce key-only senza finestra di brute-force.
- Decisione: passphrase **SI** sulla chiave privata (laptop in mobilita' MR/IT).
  - Concetto: crittografia asimmetrica -> `LEARNING_LINUX_SYSADMIN.md` §Crittografia asimmetrica
  - Concetto: i due file della coppia -> `LEARNING_LINUX_SYSADMIN.md` §Coppia di chiavi SSH
  - Concetto: passphrase -> `LEARNING_LINUX_SYSADMIN.md` §La passphrase della chiave privata

**Prossimo step:** visualizzare la chiave pubblica in PowerShell e creare il VPS Hetzner (CX22, Ubuntu 24.04, Falkenstein/Nuremberg) iniettando la pubblica.

### 2026-06-02 — Organizzazione documentale nel repo
- Creati in questa sessione (con Claude in chat): `ARCHITECTURE_OVERVIEW.md` (mappa macro narrata), `LEARNING_METHOD.md` (metodo, ora con Principio 4 "macro prima del micro"), `LEARNING_LINUX_SYSADMIN.md` (concetti), `BUILD_LOG.md` (questo file).
- **Decisione struttura:** seguire le convenzioni GIA' esistenti nel repo invece di imporre uno schema nuovo. Claude Code aveva gia' organizzato: `docs/technical/` (tunnel_strategy, crm_access + altra doc tecnica), `docs/business/` (legal_regulatory_report).
  - *Perche':* due strutture parallele sono peggio di una imperfetta. Quando si entra in un sistema con convenzioni proprie, prima si capiscono e si rispettano, poi semmai si migliorano. Coerenza interna > "struttura ideale". (Abbandonata la struttura `/docs/architecture` + `/docs/legal` proposta inizialmente da Claude in chat.)
- **Collocazione decisa:**
  - `ARCHITECTURE_OVERVIEW.md` -> `docs/technical/` (accanto a tunnel_strategy e crm_access; e' la versione narrata degli stessi contenuti; va letto per primo tra i tre).
  - File di learning (`LEARNING_METHOD`, `LEARNING_LINUX_SYSADMIN`, `BUILD_LOG`) -> nuova cartella `docs/learning/` (aggiunge una categoria allo schema esistente, non un secondo schema; separa il didattico dal vincolante).
- **Da verificare con Claude Code:** chiedere l'albero reale di `docs/` prima di collocare, per decidere sul territorio e non sulla mappa descritta a Claude in chat.
- **Principio di separazione:** `docs/technical/` e `docs/business/` = vincolanti per l'implementazione (Claude Code li rispetta). `docs/learning/` = materiale didattico personale, Claude Code lo ignora nell'implementazione. Da esplicitare in un eventuale `CLAUDE.md`.
- **Cautela:** mai segreti (chiavi, password, token) dentro i file del repo, BUILD_LOG incluso.

---

## Da fare (Fase 0, dal piano TUNNEL_MIGRATION_STRATEGY)

- [x] 0.1 Provisioning VPS Hetzner (CPX22, non CX22: 2 vCPU AMD, 4GB, 80GB) — 02/06
- [x] 0.2 Hardening VPS (SSH key-only+passphrase, fail2ban, ufw 22/443/7000, apt upgrade) — 02/06
- [x] 0.3 DNS setup wildcard `*.fitmanagerstudio.com` (DNS-only, non proxied) — 02/06
- [x] 0.4 FRP server (frps v0.61.1 in /opt/frp, systemd, auto-start) — 02/06
- [x] 0.8 Test manuale e2e tunnel (HTTP 307, tunnel tcp porta 8080, poi cleanup) — 02/06
- [x] Reboot per attivare kernel 7.0.0-22 (era installato ma non attivo) — 03/06

### 2026-06-03 — Chiusura Fase 0 + revisione critica del VPS_EDGE_SETUP.md

Documento `VPS_EDGE_SETUP.md` prodotto con Claude Code, riletto in chat con occhio critico. Esito: lavoro solido, Fase 0 ben fatta (ordine firewall corretto = nessun autoblocco, accesso a chiave+passphrase). Tre rilievi:

1. **[SICUREZZA - RISOLTO 03/06] Password in chiaro nel documento.** Sezione 13: password dashboard FRP era scritta in chiaro. Esposizione limitata (dashboard solo su 127.0.0.1:7500, non raggiungibile da Internet) ma principio non negoziabile (defense-in-depth): un segreto esposto si considera bruciato e si ruota, a prescindere dagli altri strati.
   - **Azioni completate 03/06:**
     - Backup del file: `cp /opt/frp/frps.toml /opt/frp/frps.toml.bak` prima di modificare (riflesso corretto: mai editare config di produzione senza backup).
     - Generata password nuova robusta, custodita SOLO nel password manager (NON nel repo, NON nel BUILD_LOG).
     - Modificata la riga `password` in `/opt/frp/frps.toml` (valore tra virgolette, formato TOML).
     - `systemctl restart frps` -> rilettura config. Verificato `systemctl status frps` = `active (running)`, PID nuovo, comando `frps -c /opt/frp/frps.toml` (conferma rilettura del file).
     - Vecchia password rimossa dal `VPS_EDGE_SETUP.md` (sezione 13) da Claude Code, sostituita con rimando a password manager.
   - Concetto: rotazione applicata col principio "il servizio rilegge la config al restart" (vedi LEARNING_LINUX_SYSADMIN §systemd) e defense-in-depth (vedi LEARNING_NETWORKING §piani di accesso).
   - Nota git: se il documento con la vecchia password era gia' stato committato, il valore resta nella storia git anche dopo la rimozione dal file. La rotazione della password rende innocuo qualunque residuo. Da verificare lo stato git del documento con Claude Code.

2. **[FALSO ALLARME - CHIUSO] Versione OS.** Claude (chat) aveva dubitato di "Ubuntu 26.04 / kernel 7.0.0" (sembravano oltre il suo orizzonte di conoscenza). `lsb_release -a` ha confermato: 26.04 "Resolute" e' reale. Aveva ragione il sistema. -> Concetto: `LEARNING_LINUX_SYSADMIN.md` §Quando AI/documento e sistema divergono, vince il sistema.

3. **[FARO - FASE 2] "Data-blind" (P2) non ancora dimostrato.** Il test e2e 0.8 usava tunnel `tcp` SENZA TLS: ha provato solo la connettivita' (i pacchetti passano), NON che il VPS non possa leggere. P2 (VPS instrada senza decifrare) dipende dal TLS e2e con cert sul PC trainer + SNI passthrough, in arrivo in Fase 2. P2 e' il pilastro della semplificazione GDPR (AVGV "non tratta" i dati): il test che conta davvero e' quello di Fase 2, da non dare per scontato.

**Discrepanza kernel risolta:** documento diceva `-22` attivo, sistema diceva `-15`. Causa: kernel `-22` installato in /boot ma non attivo (manca reboot). Risolto con `reboot` -> `uname -r` ora conferma `7.0.0-22-generic`. -> Concetto: `LEARNING_LINUX_SYSADMIN.md` §Il kernel e perche' serve il reboot.

**Da allineare nel VPS_EDGE_SETUP.md:** correggere riferimenti (kernel ora -22 davvero attivo dopo reboot; rimuovere password sezione 13). Far fare a Claude Code l'allineamento del documento al sistema reale.

**Concetti appresi dal vivo oggi (vedi LEARNING_LINUX_SYSADMIN.md):**
- Kernel e reboot
- Estensione file = etichetta (il `.pub` mostrato come "Publisher")
- Sistema = fonte di verita' su AI e documento

**Aperto:** ssh-agent su Windows (passphrase chiesta a ogni connessione, a volte due volte).

---

## Fase 1 — Tunnel client nel prodotto

Dettagli in `TUNNEL_MIGRATION_STRATEGY.md` sez. 4 Fase 1.

### 2026-06-07 — Step 1: instance_id nella licenza (IDENTITA')

**Obiettivo:** aggiungere il claim `instance_id` al JWT licenza e renderlo leggibile dal backend.

**File modificati:**
- `api/services/license.py` — aggiunto campo `instance_id: str | None = None` in `LicenseClaims` + property `instance_id` su `LicenseCheckResult` (scorciatoia per tunnel_manager)
- `tools/admin_scripts/generate_license.py` — aggiunto argomento `--instance-id` al comando `sign` + stampa instance_id in `sign` e `verify` (con tunnel URL derivato)

**Verifiche eseguite:**
- Generazione licenza con `--instance-id gvera-dev` -> claim presente nel JWT
- Verifica: `verify` legge e stampa instance_id + URL tunnel derivato
- Backward compatibility: licenza SENZA instance_id -> `valid`, campo `None`, zero rotture
- Property shortcut: `check_license().instance_id` restituisce slug se valida, `None` se no
- Suite completa: 361 test passati, zero regressioni

**Concetto consolidato (non nuovo — gia' in LEARNING_FASE1 sez. 1-2):**
Aggiungere un claim JWT = mettere un campo in piu' nel dizionario payload prima di firmare. Il campo `Optional` in Pydantic (`str | None = None`) garantisce backward compatibility: le licenze vecchie non hanno quel campo -> Pydantic lo mette a `None` -> tutto il codice esistente continua a funzionare. Stesso pattern gia' usato per `machine_id`. E' il pattern standard per evolvere un contratto dati senza rompere i consumatori esistenti.

**Prossimo step:** Step 2 — configurazione tunnel (layer tra identita' e esecuzione).

### 2026-06-07 — Step 2: configurazione tunnel (CONFIG LAYER)

**Obiettivo:** creare il layer di configurazione che il tunnel_manager consumera'. Separare "sapere chi sono" (licenza, path) da "gestire il processo" (avvio, restart, health check).

**File creato:**
- `api/services/tunnel_config.py` — modulo dedicato con:
  - Costanti server FRP: `FRP_SERVER_ADDR`, `FRP_SERVER_PORT`, `TUNNEL_DOMAIN`
  - `TunnelConfig` dataclass (frozen/immutabile): instance_id, server, path, domain
  - `_resolve_frpc_path()`: trova frpc.exe in `tools/bin/` (dev) o accanto all'exe (compiled)
  - `get_tunnel_config()`: legge licenza -> estrae instance_id -> risolve frpc -> assembla config

**Verifiche eseguite:**
- Licenza senza instance_id -> `get_tunnel_config()` restituisce `None` (tunnel disabilitato)
- Licenza con instance_id + frpc assente -> `None` con warning nel log
- Licenza con instance_id + frpc presente -> `TunnelConfig` assemblato, `public_url` corretto
- frpc.exe gia' presente in `tools/bin/` (~15MB, scaricato in Fase 0)
- Suite completa: 361 test passati, zero regressioni

**Concetto nuovo — separazione di responsabilita' (separation of concerns):**
Il config layer e' un "contratto" tra il sistema di identita' (licenza JWT) e il sistema di esecuzione (tunnel_manager). Il tunnel_manager ricevera' un `TunnelConfig` gia' pronto e non dovra' importare `license.py` ne' calcolare path. Ogni modulo fa UNA cosa. E' lo stesso principio per cui nel codebase i router (HTTP) non fanno query al database direttamente ma chiamano service/helper: ogni layer ha la sua responsabilita'. Il dataclass `frozen=True` significa che l'oggetto e' immutabile dopo la creazione — nessuno puo' modificarlo accidentalmente.

**Prossimo step:** Step 3 — tunnel_manager.py (babysitter frpc).

### 2026-06-07 — Step 3: tunnel_manager.py (BABYSITTER)

**Obiettivo:** creare il componente che gestisce il ciclo di vita di frpc: avvio, monitoraggio, restart su crash, shutdown pulito.

**File creato:**
- `api/services/tunnel_manager.py` (~250 LOC) con:
  - `TunnelState` enum: stopped/starting/connected/reconnecting/error
  - `BackoffTimer`: backoff esponenziale (1s→2s→4s→...60s) + jitter + reset dopo 5min stabilita'
  - `generate_frpc_toml()`: genera config FRP client da TunnelConfig (Fase 1: proxy HTTP)
  - `TunnelManager` classe principale:
    - `start()`: genera frpc.toml + avvia frpc + avvia monitor daemon thread
    - `stop()`: ferma frpc con terminate (gentile) + kill (forza dopo 5s)
    - `get_status()`: dict per health endpoint (state, instance_id, public_url, pid)
    - `_monitor_loop()`: daemon thread, controlla ogni 5s se frpc e' vivo, restart con backoff
    - `_drain_output()`: thread che legge stdout frpc (previene deadlock buffer pieno)
    - `_cleanup()`: handler atexit, uccide frpc alla chiusura app (evita orfani)

**Verifiche eseguite:**
- Generazione frpc.toml: TOML corretto con instance_id, server, customDomains
- Backoff timer: delay crescenti (1.4s, 2.6s, 4.2s, 8.8s, 16.9s, 32.1s), cap a 60s
- Ciclo di vita completo: start -> frpc si connette al VPS (login success) -> stop pulito (PID terminato)
- Restart automatico: frpc ucciso forzatamente -> monitor rileva exit code 1 -> backoff 2s -> nuovo PID
- VPS conferma: `vhostHTTPPort` non ancora configurato (atteso, da aggiungere per e2e)
- Suite completa: 361 test passati, zero regressioni

**Concetti nuovi (cattura per learning):**
1. **subprocess.Popen**: Python lancia un programma esterno come processo figlio. Il genitore mantiene il controllo (pid, poll(), terminate(), kill()). Stesso pattern di systemd con frps sul VPS.
2. **Daemon thread**: `threading.Thread(daemon=True)` — thread che muore quando il programma principale esce. Il monitor gira cosi': se FitManager crasha, il thread monitor muore con lui (e frpc viene ucciso dall'atexit handler).
3. **Backoff esponenziale + jitter**: attesa crescente tra retry (1s, 2s, 4s, ...) per evitare retry storm. Il jitter (ritardo casuale) evita thundering herd: se frps si riavvia, 50 frpc non riprovano tutti allo stesso istante.
4. **Output draining**: subprocess.PIPE ha un buffer finito. Se nessuno lo legge e si riempie, il processo figlio si blocca in attesa di scrivere (deadlock). Il thread `_drain_output` lo svuota continuamente.
5. **CREATE_NO_WINDOW**: flag Windows che impedisce a frpc di aprire una finestra console visibile al trainer.

**Prossimo step:** Step 4 — auto-start tunnel al boot dell'app.

### 2026-06-07 — Step 4: auto-start tunnel al boot (INTEGRAZIONE)

**Obiettivo:** il tunnel parte automaticamente quando l'app si avvia, se la licenza ha instance_id e frpc e' presente.

**File modificato:**
- `api/main.py` — step 6 nel lifespan (asynccontextmanager):
  - Startup: `get_tunnel_config()` -> se config presente -> `TunnelManager(config).start()`
  - Shutdown: `tunnel_manager.stop()` (ferma frpc prima di chiudere)
  - `_tunnel_manager` variabile globale per accesso da health endpoint / router
  - Try/except: tunnel fallito = warning nel log, non blocca l'app

**Verifiche eseguite:**
- Licenza dev senza instance_id -> log `TUNNEL = disabilitato`, backend funziona normalmente
- Licenza con instance_id -> log `TUNNEL = gvera-dev.fitmanagerstudio.com (frpc PID 27308)`, tunnel auto-start
- Suite completa: 361 test passati, zero regressioni

**Concetto consolidato — lifespan come lifecycle manager:**
Il `@asynccontextmanager lifespan(app)` e' il pattern FastAPI per gestire startup/shutdown. Tutto prima di `yield` = startup, tutto dopo `yield` = shutdown. Il tunnel si inserisce come step 6 dello startup. Il try/except garantisce che un fallimento del tunnel non blocchi l'app (best-effort, come l'auto-backup). La variabile `_tunnel_manager` globale e' necessaria perche' il lifespan e' un context manager asincrono: le variabili locali spariscono dopo il `yield`, ma la globale sopravvive per l'health endpoint.

**Prossimo step:** Step 5 — bundle frpc.exe nel build Nuitka.

### 2026-06-07 — Step 4b: correzione proxy type HTTP → HTTPS + cert self-signed

**Problema identificato (revisione critica con Claude chat):**
Il proxy `type = "http"` usato nel Step 3 non valida l'architettura reale:
- HTTP usa header `Host` per routing, HTTPS usa SNI — meccanismi diversi
- Con HTTP il VPS vede il traffico in chiaro — P2 (data-blind) non dimostrato
- Testare con HTTP rischia di scoprire problemi SNI solo in Fase 2

**Decisione: strada B — cert self-signed temporaneo.**
Valida SNI routing + P2 data-blind con cert finto. In Fase 2 si sostituisce solo il file `.pem`.
Il cert copre sia il subdomain specifico (`gvera-dev.fitmanagerstudio.com`) sia il wildcard (`*.fitmanagerstudio.com`) via SAN.

**File modificati:**
- `api/services/tunnel_config.py`:
  - Aggiunti `cert_path` e `key_path` a `TunnelConfig`
  - `_ensure_self_signed_cert()`: genera cert RSA 2048 + SHA-256, valido 365gg, idempotente (rigenera solo se scaduto)
  - `get_tunnel_config()` chiama `_ensure_self_signed_cert()` prima di assemblare il config
- `api/services/tunnel_manager.py`:
  - `generate_frpc_toml()`: da `type = "http"` / `localPort` a `type = "https"` / plugin `https2http` con cert path
  - Path in TOML con forward slash (`as_posix()`) per compatibilita' cross-platform

**Verifiche eseguite:**
- Cert generato: CN corretto, SAN con 2 DNS names, valido fino 2027-06-07
- Idempotenza: seconda chiamata = skip (cert gia' presente)
- frpc.toml: tipo `https`, plugin `https2http`, path cert con forward slash
- Ciclo completo: licenza con instance_id → cert auto-generato → frpc avviato → stop pulito
- Suite completa: 361 test passati, zero regressioni

**Concetto nuovo — SNI (Server Name Indication):**
Quando un browser apre una connessione HTTPS, PRIMA di cifrare manda in chiaro il nome del dominio che vuole raggiungere (SNI). Il VPS legge SOLO questo nome per decidere a quale tunnel inoltrare, senza mai aprire il pacchetto TLS. E' il meccanismo che permette a piu' siti HTTPS di condividere la stessa porta 443 sullo stesso IP. Per FitManager: tutti i trainer condividono la porta 443 del VPS, il routing avviene per nome (SNI), e il VPS non puo' leggere il contenuto (P2 data-blind). Questo funziona identico con cert self-signed e Let's Encrypt — il VPS non vede la differenza.

**Azione DNS rimanente:** creare record A esplicito `edge.fitmanagerstudio.com` → IP VPS su Cloudflare (DNS-only). Il wildcard lo coprirebbe ma un record esplicito e' intenzionale e modificabile indipendentemente.

### Da fare (Fase 1)

- [x] 1.1 Instance ID nella licenza (claim + CLI + lettura)
- [x] 1.2 Configurazione tunnel (TunnelConfig, risoluzione path, config layer)
- [x] 1.3 Tunnel manager (babysitter frpc + generazione frpc.toml)
- [x] 1.4 Auto-start tunnel al boot (lifespan step 6, startup/shutdown)
- [x] 1.4b Correzione: proxy HTTPS + cert self-signed (validazione SNI + P2 data-blind)
- [x] 1.5 Test e2e tunnel HTTPS (SNI routing + P2 data-blind dimostrato)
- [x] 1.5b Route separation middleware (CRM invisibile da tunnel)
- [x] 1.5c Auto PUBLIC_BASE_URL da instance_id (link pubblici usano URL tunnel)
- [x] 1.6 Bundle FRP binary + licenza reale + rimozione dual-env
- [~] 1.7 ~~Script provisioning AVGV-side~~ — NON NECESSARIO (wildcard DNS copre tutti i trainer, zero provisioning per-istanza)
- [x] 1.8 Health endpoint tunnel (GET /api/system/tunnel-status)
- [x] 1.9 Test produzione su 2 installazioni reali (v1.0.10)

### 2026-06-07 — Step 5: test e2e tunnel HTTPS

**Azioni VPS/DNS completate:**
- Record A `edge.fitmanagerstudio.com → 128.140.91.39` creato su Cloudflare (DNS-only, propagato)
- Verificato: frps ha `vhostHTTPSPort = 443`, porta 443 aperta nel firewall

**Test e2e:**
- Licenza con `--instance-id gvera-dev` generata
- Cert self-signed auto-generato (CN: gvera-dev.fitmanagerstudio.com, SAN wildcard)
- Backend avviato su porta 8000 → tunnel auto-start (frpc PID connesso a frps)
- HTTP test server su porta 3000 (simula frontend)
- Dal VPS: `curl -k https://gvera-dev.fitmanagerstudio.com` → `<h1>FitManager Tunnel Test OK</h1>`
- **Percorso verificato:** VPS (curl) → frps:443 (SNI routing) → frpc sul PC dev (TLS termination) → localhost:3000 → risposta

**P2 data-blind dimostrato:** il VPS ha instradato il traffico HTTPS usando solo il campo SNI (nome dominio in chiaro nell'handshake TLS). Il contenuto della richiesta e della risposta e' cifrato end-to-end — il VPS non puo' leggerlo. Questo e' il pilastro della semplificazione GDPR: AVGV "non tratta" i dati clinici perche' il VPS e' cieco sul contenuto.

**Concetto validato — architettura SNI passthrough:**
Il flusso e' identico a quello che avra' la produzione con Let's Encrypt. L'unica differenza e' che il browser mostrera' un warning (cert self-signed) invece del lucchetto verde. Il routing, la cifratura, e la cecita' del VPS sono gia' quelli definitivi.

### 2026-06-07 — Step 5b: route separation middleware (SICUREZZA)

**Problema identificato durante test e2e:**
Accedendo a `https://gvera-dev.fitmanagerstudio.com` dal browser, il tunnel mostrava la pagina di login del CRM. Il CRM intero era esposto su Internet — login, dashboard, clienti. Un attaccante poteva tentare brute-force su `/api/auth/login` (rate limiter aiuta ma non basta).

**Decisione: implementare subito, non rimandare a Fase 2.**
Gap G5 della strategia era pianificato per Fase 2, ma esporre il login su Internet e' un rischio reale che un programmatore esperto non rimanda.

**File creato:**
- `frontend/src/middleware.ts` — sostituisce `proxy.ts` (rinominato per convenzione Next.js):
  - **Layer 1 — Tunnel Guard**: rileva richieste dal tunnel via hostname (non localhost/LAN) → se path non e' `/public/*`, `/api/public/*`, `/health`, `/media` → **404**
  - **Layer 2 — Auth Guard**: invariato rispetto al vecchio proxy.ts (cookie check, redirect)
  - Il CRM e' completamente invisibile dal tunnel: `/login`, `/dashboard`, `/clienti` → 404

**File rimosso:**
- `frontend/src/proxy.ts` — sostituito da `middleware.ts`

**Verifiche eseguite:**
- Next.js build: passa, middleware riconosciuto (`Proxy (Middleware)`)
- Test frontend: 81 passed, 1 failed (pre-esistente, non legato alla modifica)
- Test backend: 361 passed (nessuna modifica backend)

**Concetto — defense in depth:**
Due layer indipendenti: anche se uno fallisce, l'altro protegge. Il tunnel guard blocca PRIMA dell'auth guard. Un attaccante dal tunnel non vede nemmeno il form di login — riceve 404 come se la pagina non esistesse. E' meglio di un 403 (che rivelerebbe l'esistenza della risorsa).

### 2026-06-09 — Step 6: bundle frpc.exe + licenza reale + rimozione dual-env

**Obiettivo:** completare Fase 1.6 (frpc nell'installer) e risolvere la confusione dev/prod.

**Analisi dual-env:**
Revisione critica ha rivelato che la separazione dual-env (dev 8001/3001 + crm_dev.db, prod 8000/3000 + crm.db) non era mai stata usata nella pratica. `crm.db` era il database di lavoro attivo (ultima modifica 8 giugno), `crm_dev.db` fermo dal 31 maggio. Il codice in `api/config.py` auto-rilevava la porta per scegliere il DB, ma tutto lo sviluppo avveniva sulle porte "prod". Complessita' senza valore.

**Decisione: ambiente unico (8000/3000, crm.db).**
La vera separazione dev/prod e' tra il PC di sviluppo e il PC del trainer (installazione). Non serve un DB separato sullo stesso PC.

**Licenza reale generata:**
- Intestata a: Giacomo Verardo (`giacomo-verardo`)
- Machine binding: SHA-256 di questo PC (MATCH verificato)
- Instance ID: `gvera-dev` → `gvera-dev.fitmanagerstudio.com`
- Tier: pro, scadenza 2027-06-04
- La licenza vive in `data/license.key`, sopravvive agli upgrade dell'installer (directory `data/` ha flag `uninsneveruninstall` in Inno Setup)

**Bundle frpc.exe — intervento nel build pipeline:**
- `build-installer.sh`: aggiunto safety gate (blocca build se `tools/bin/frpc.exe` mancante) + staging in `dist/fitmanager/`
- `fitmanager.iss`: nessuna modifica — il wildcard `Source: "..\dist\fitmanager\*"` raccoglie frpc.exe automaticamente
- `tunnel_config.py`: path resolution gia' implementata (`Path(sys.executable).parent / "frpc.exe"` in compiled mode)
- Catena verificata: `tools/bin/` → staging → installer → `{app}\backend\frpc.exe` → tunnel_config lo trova

**Pulizia dual-env (10 file, -87/+37 righe):**
- `api/config.py`: `_resolve_database_url()` semplificata — sempre `crm.db`, niente auto-detect porta
- `alembic/env.py`: rimosso riferimento a `crm_dev.db` nel docstring
- `CLAUDE.md`, `README.md`, `CONTRIBUTING.md`, `frontend/CLAUDE.md`: aggiornati comandi e topologia
- `frontend/next.config.ts`: rimosso `NEXT_DIST_DIR`, aggiornati commenti porte
- `frontend/tsconfig.json`: rimossi path `.next-dev`
- `frontend/src/lib/api-client.ts`: aggiornati commenti (Tailscale → FRP, porte aggiornate)
- `tools/DUAL_ENV.md` → archiviato in `docs/archive/`

**Verifiche eseguite:**
- 362 test passed (pytest), ruff OK, Next.js build OK
- Pre-commit hook superato (ruff + next build)

**Concetto — licenza indipendente dalla versione:**
La licenza e' un artefatto separato dal software. Si attiva una volta e sopravvive agli aggiornamenti. L'installer non la tocca (non e' nei `[Files]` di Inno Setup). L'unico momento in cui si rigenera e': scadenza, cambio macchina, o cambio tier. Questo e' il pattern standard per software con licenza perpetua: il file `.key` e' un JWT firmato con chiave privata AVGV, verificato dalla chiave pubblica embedded nel bundle.

### 2026-06-09 — Step 7: health endpoint + allineamento strategia

- Health endpoint `GET /api/system/tunnel-status` aggiunto a `system.py` (autenticato, solo LAN)
- Schema `TunnelStatusResponse`: state, instance_id, public_url, pid
- Se tunnel non configurato: `{ state: "disabled" }`
- `TUNNEL_MIGRATION_STRATEGY.md` aggiornata: Fase 1 tutta completata, G12 provisioning eliminato (wildcard DNS), D3/D4 corretti con architettura reale
- Step 1.7 (provisioning DNS) marcato NON NECESSARIO — il wildcard `*.fitmanagerstudio.com` copre tutti i trainer, zero interventi su Cloudflare per ogni nuovo cliente

### 2026-06-09 — Step 8: release v1.0.10 + test produzione su 2 PC

**Release v1.0.10:**
- Pipeline ADR-004 completa: preflight (362 test) → build → verify (5/5 smoke) → seal → tag
- Installer: `FitManager_Setup_1.0.10.exe` (117 MB, SHA-256: `77c5444d...`)
- frpc.exe bundlato in `{app}\backend\` — primo installer con tunnel FRP integrato

**Licenze emesse:**
- Giacomo Verardo: `giacomo-verardo`, machine-bound, instance_id `gvera-dev`, pro, scade 2027-06-04
- Chiara Bassani: `chiara-bassani`, machine-bound, instance_id `chiara-bassani`, pro, scade 2027-06-04

**Test produzione — 2 installazioni reali:**
- PC Giacomo: installazione v1.0.10 → attivazione licenza → tunnel auto-start → `gvera-dev.fitmanagerstudio.com` raggiungibile. **PASS.**
- PC Chiara: installazione v1.0.10 → attivazione licenza → tunnel auto-start → `chiara-bassani.fitmanagerstudio.com` raggiungibile. **PASS.**

**Flusso zero-touch validato in produzione:**
Installa → attiva licenza → tunnel parte automaticamente → URL pubblico raggiungibile. Il trainer non deve configurare nulla (DNS, certificati, porte). Il wildcard DNS e il cert self-signed gestiscono tutto.

**Fase 1 CHIUSA.** Tutti gli step completati, testati in produzione su 2 installazioni reali.

---

## Libreria esercizi & strategia media

Filone di lavoro avviato dopo la chiusura della Fase 1 tunnel. L'energia di prodotto si sposta sull'interfaccia cliente e sulla libreria di animazioni esercizi. Decisioni in `EXERCISE_LIBRARY_STRATEGY.md` (changelog v2.0 → v2.1 → v2.2).

### 2026-06-10 — Verifica strategia libreria esercizi dall'interno (v2.1)

- `EXERCISE_LIBRARY_STRATEGY.md` portata a v2.1: verifica dall'interno del codebase (query dirette su catalog.db, seed JSON, router, installer) + decisioni founder.
- **Numeri canonici fissati:** 500 esercizi totali, 466 attivi (`in_subset`), 894 relazioni, 750 media, 107 esercizi senza foto. Copertura del bundle calcolata sui 466 attivi.
- **`in_subset` ≠ fondamentali:** `in_subset` e' il flag "database attivo", non marca i ~50-80 fondamentali. Serve un marcatore dedicato.
- **Decisione founder:** Alessio fuori dall'equazione tecnica del contenuto (eventuale validatore, non produttore); decade la scadenza agosto. Contenuto ricco gia' popolato al 100% su 466/466 → il lavoro e' tuning interno.
- **Distribuzione (§4bis):** clip MP4 nell'installer, payload POC 1,2-2,3 GB, `nocompression` sui video. (Poi superseded dalla v2.2.)
- Commit: `a1ffc69`.

### 2026-06-12 — Strategia media cloud (chat) → learning doc + delta v2.2

- Discussione in chat sull'architettura "hosting centrale dei media, doppio flusso": il video esce dal tunnel e viaggia diretto a `media.fitmanagerstudio.com`; pagina e dati personali restano nel tunnel.
- Principio guida: **il routing segue la classificazione del dato** (personale → tunnel/P2; generico → media host diretto).
- Creati: `docs/learning/LEARNING_MEDIA_CLOUD_ARCHITECTURE.md` (fondamento didattico, 3 livelli di perche', failure mode, autotest §9) e `docs/technical/DELTA_v2.2_EXERCISE_LIBRARY_STRATEGY.md` (istruzioni di integrazione v2.1 → v2.2).
- **Gate:** la v2.2 non si consolida (commit nella strategia + mail al fornitore) finche' l'autotest §9 non passa. ADR-012 riservato in attesa del gate.

### 2026-06-13 — Azioni tecniche §5.6 + allineamento documentazione

**Codice (azioni §5.6 della strategia v2.1, da sessione precedente → committate oggi, `5caddd9`):**
- §5.6.1: campo `is_fondamentale` su `Exercise` (model + schema + `types/api.ts`).
- §5.6.2: normalizzazione `is_compiled()` (`config.py`, `database.py`).
- §5.6.3: rename `seed_exercise_relations.json` → `seed_taxonomy_junctions.json` (il file conteneva junction tassonomiche, non relazioni — nome fuorviante). Verificato: nessun codice runtime/build lo legge (le junction sono calcolate da `populate_taxonomy.py`); aggiornato l'unico riferimento (e2e rehearsal).
- §5.6.4: pruning `seed_exercise_media.json` (rimossi 1038 media orfani pre-rebuild, −8818 righe); file fisici spostati in quarantena `data/_media_orphans_pre_rebuild/` (mai cancellati senza backup).
- `.gitignore`: aggiunta la quarantena (era fuori da `data/media/`, gia' ignorato → 1639 file comparivano erroneamente come da committare).
- Quality gate verde: ruff + next build (anche via pre-commit hook).

**Documentazione (allineamento):**
- **ADR-011** creato (accepted): Migrazione Tunnel FRP self-hosted — la decisione architetturale piu' grande dell'ultimo mese non aveva ADR (solo strategia + BUILD_LOG).
- **ADR-002**: link rotto nell'indice corretto (era stato rimosso come obsoleto in `0748ddf`, indice mai aggiornato).
- **ADR-012** riservato nell'indice (pending gate autotest).
- **BUILD_LOG** ampliato da diario-tunnel a diario generale di sviluppo (questa sezione).

### 2026-06-14 — Audit metodico integrità 3 DB (read-only)

Audit completo prima del tuning di contenuto del catalogo. Record: `docs/operations/DB_INTEGRITY_AUDIT_2026-06-14.md`.
- **catalog.db: pristino** — zero FK orfane, copertura junction 100% (466/466), contenuto 100% popolato, JSON valido, demand vector esplicito.
- **Scoperta centrale:** `crm.db` contiene ancora le 10 tabelle catalog **stale** (pre-rebuild, 1111 esercizi) → violazione ADR-003 a livello fisico. I "numeri canonici" v2.1 (4168 condizioni, 1234 articolazioni) erano misurati su quelle tabelle stale, non su catalog.db (reali: 5154, 1452).
- **32 esercizi orfani** (Belt Squat, Landmine Press, …) referenziati da 58 righe di schede reali (`esercizi_sessione`), sopravvissuti solo nella tabella stale.
- Lista discrepanze prioritizzata P1-P3 + sequenza remediation (cleanup, non rebuild). **Nessuna mutazione eseguita.**
- Conferma strategica: il bundle di Alessio è uno **specchio**, non una base di rebuild — catalog.db non ha nulla da ricostruire.
- **Passo 1 remediation ESEGUITO (P2):** corretti i numeri canonici (condizioni 4168→5154, articolazioni 1234→1452) in `EXERCISE_LIBRARY_STRATEGY.md` (§1.4/§3/§4.1 + changelog v2.1.1), `CLAUDE.md`, `api/CLAUDE.md` e memory; chiarito che i numeri stale venivano dall'export seed `seed_taxonomy_junctions.json` e dalla copia stale in crm.db. §5.6.3/§5.6.4 marcate eseguite (rinomina + pruning media a 750). Restano P1 (32 orfani, DROP tabelle stale) e P3.
- **Analisi 32 orfani (read-only):** zero duplicati di nome, ID liberi → re-insert preservando l'ID. Tiering 3 ricchi / 7 medi / 22 gusci. **Founder conferma: le 5 schede impattate sono dati di test** → 58 referenze non preziose, decisione = merito di catalogo. Dettaglio in audit §8.
- **Sessione sospesa (sera 2026-06-14):** creato punto di ripresa `docs/operations/SESSION_HANDOFF_2026-06-14.md` (board thread aperti A/B/C/D) + memoria `project_session_resume.md`. Prossima azione alla ripresa: re-insert keeper orfani (backup prima).

### 2026-06-14 — Thread A: re-insert Ondata 1 (10 keeper orfani)

Ripresa del Thread A. Backup `crm.db` + `catalog.db` → `*.bak-threadA-20260614` (guardrail #11) **prima** di tutto.

**Indagine sulla meccanica (prima di mutare):**
- Il seed esercizi è idempotente *per tabella-non-vuota* (`if count>0: skip`), NON upsert → aggiungere al JSON + riavviare non re-inserisce nulla. Serve insert chirurgico o rebuild.
- **Scoperta chiave:** le junction tassonomiche NON sono hand-authored — `populate_taxonomy.py` le **genera** da `muscoli_primari/secondari` (muscoli) e `pattern_movimento` (articolazioni); `populate_conditions.py` per le condizioni. Gira solo per `in_subset=1`.
- Conseguenza: i 7 "medi" avevano junction=0 solo perché inattivi, non per dato mancante. Verificato: tutti e 10 i keeper hanno `muscoli_primari/secondari/pattern` popolati → junction rigenerabili.
- Verifica di sicurezza: tassonomia (53 muscoli / 15 articolazioni / 47 condizioni) **identica per ID e nome** tra stale crm.db e catalog.db (0 mismatch); junction dei 3 ricchi → 0 target disallineati.

**Esecuzione (insert chirurgico, non rebuild completo):**
- Inseriti 10 esercizi in catalog.db preservando l'ID, `in_subset=0`, `is_builtin=1`, `deleted_at=NULL`. Mapping stale→catalog: scartato `trainer_id`, aggiunto `is_fondamentale=0`.
- Aggiornato `seed_exercises.json` (500→510) per la riproducibilità — `catalog.db` è gitignored, il **seed è la fonte committata**; un rebuild pulito ricrea i 10 (in_subset=0, junction generate solo se attivati).
- Ricalcolato `data/catalog.sha256`.
- **Verifiche pre-commit (tutte verdi):** 500→510 esercizi, 466 attivi invariati, `integrity_check` OK, **orfani 32→22**.

**Decisione di scope (founder):** tutti e 10, `in_subset=0` — il re-insert è puro fix d'integrità; l'attivazione nella libreria (in_subset=1 + is_fondamentale) resta curation separata.

**Restano (Ondata 2):** 22 gusci (414, 428, 498, 509, 518, 522, 599, 603, 644, 656, 700, 738, 756, 791, 877, 905, 962, 984, 987, 1056, 1062, 1064) — curation founder. Poi P1 DROP tabelle stale crm.db, P3.

### 2026-06-14 — Thread A: Ondata 2 (curation 22 gusci)

**Triage (read-only) prima di decidere:** estratti tutti e 22 dallo stale crm.db. Contenuto 1/9 — l'unico campo pieno è `esecuzione` (per tutti e 22). Leggere quel testo è stato il segnale di curation decisivo.

**Scoperta:** i 22 non sono esercizi falsi — sono **movimenti reali con nomi auto-tradotti malamente**. Il catalogo pre-rebuild fu seedato da un DB inglese tradotto a macchina → nomi mangled. Evidenza dagli `esecuzione`:
- 877 "Buccinate da Seduto" (buccinatore = muscolo della guancia) → il testo descrive un **Box Squat**.
- 644 "Carico Kettlebell" (attrez=bodyweight) → testo = **caricamento barili/pietre** (strongman).
- 905 "Trazioni Laterali" → testo = **rematore a presa larga** ("parallelepipedo" = traduzione di "bar").
- 962 "Affondi Frontali" → categorizzato `stretching` ma il testo è **affondi saltati pliometrici**.

**Decisioni founder:**
- **19 re-inseriti** (in_subset=0, meccanica identica a Ondata 1): 18 reali con nome OK + 962 con fix `categoria stretching→compound`, `pattern stretch→squat`.
- **3 scartati** (877, 644, 905): troppo corrotti/di nicchia. NON re-inseriti → le loro refs restano dangling nelle schede TEST (cross-DB senza FK constraint → innocuo).

**Esecuzione + verifiche (pre-commit, verdi):** 510→529 esercizi, 466 attivi invariati, integrity OK, **orfani 22→3** (= i 3 scarti deliberati). `seed_exercises.json` 510→529, `catalog.sha256` ricalcolato. Backup `catalog.db.bak-threadA-ondata2`.

**Thread A — orfani chiusi:** tutti i keeper re-inseriti (29 totali tra Ondata 1+2), 3 scarti consapevoli. Sblocca P1 (DROP tabelle stale crm.db) + P3.

### 2026-06-14 — Thread A: P1 (DROP tabelle catalog stale da crm.db) — 9/10

Backup `crm.db.bak-threadA-p1` (regola #11) **prima**. crm.db non era stato modificato da Ondate 1/2 (solo letto).

**Verifica di sicurezza prima del DROP (decisiva):** `PRAGMA foreign_key_list` su tutte le 28 tabelle business → cercato chi referenzia le 10 catalog. **Landmine trovato:** `metriche` è referenziata da FK locale reale da `obiettivi_cliente.id_metrica` e `valori_misurazione.id_metrica` (146 righe). Le altre 9 catalog: zero FK business in entrata (`esercizi_sessione.id_esercizio` è cross-DB application-level, nessun constraint).

**Eseguito (9 tabelle pure):** drop di esercizi, esercizi_media, esercizi_muscoli/articolazioni/condizioni, esercizi_relazioni, muscoli, articolazioni, condizioni_mediche. `foreign_keys=OFF` durante i drop (FK intra-catalog), poi transazione con verifica pre-commit (`foreign_key_check` pulito, conteggi business invariati, metriche preservata) → COMMIT → VACUUM.

**Risultato:** crm.db 38→29 tabelle, integrity OK, **dimensione 4.56 MB → 0.91 MB (−80%)** — conferma quantitativa del gonfiore da detrito previsto dall'audit.

**`metriche` rimandata (P1-bis):** non droppabile senza rompere l'enforcement FK. È in `CATALOG_TABLE_NAMES` (l'app la legge da catalog.db) MA i modelli `goal.py`/`measurement.py` dichiarano ancora `foreign_key="metriche.id"` (FK locale) → incoerenza con la separazione ADR-003. Task dedicato: migrare i modelli al pattern cross-DB (come `componenti_pasto.alimento_id`) + Alembic migration (ricrea le 2 tabelle senza la FK) + DROP + test. NB: crm.db è gitignored — il DROP è cleanup del DB dev (un crm.db *fresh* esclude già le catalog via `create_db_and_tables`); nessun artefatto di codice da committare, solo doc.

### 2026-06-14 — Thread A: P1-bis `metriche` + correzione bug latente cross-DB FK

Analisi richiesta dal founder **prima** del codice: spiegare la logica di `metriche` + il bug latente, e capire lo stato nelle 2 licenze reali con installer.

**Diagnosi (riproduzione del bug, non teoria):**
- `metriche` è un catalogo scientifico (22 metriche standard) → vive in catalog.db, letta via `get_catalog_session`. L'app NON la legge mai da crm.db (verificato: tutti i `select(Metric)` usano `catalog_session`).
- Ma i modelli `goal.py`/`measurement.py` dichiaravano `id_metrica = Field(foreign_key="metriche.id")` → FK **locale** nel DDL di crm.db.
- L'installer **non spedisce crm.db** (solo `catalog.db.enc`/`nutrition.db.enc`): il crm.db sacro nasce fresh via `create_db_and_tables()`, che **esclude** metriche. Il boot NON lancia `alembic upgrade`.
- → su crm.db fresh + `foreign_keys=ON`, il primo INSERT di una misurazione/obiettivo crasha **`no such table: main.metriche`**. **Riprodotto** ricostruendo un crm.db fresh dai modelli.

**Stato nelle 2 licenze reali (dal backup crm.db di Chiara, 8 giu, analizzato read-only):**
- crm.db di Chiara è **monolite** (`alembic_version`, niente `_schema_version`) → contiene metriche (22) + tutte le 10 catalog stale → i suoi **145 valori funzionano**, bug NON attivo. Alessio (installer più vecchio) idem per inferenza.
- **A rischio: le nuove installazioni** dell'installer attuale (crm.db fresh).

**Fix (precedente identico: `_fix_cross_db_fk` per `esercizi_sessione→esercizi`):**
1. Modelli: `id_metrica` → `int` cross-DB, niente `foreign_key` (pattern `componenti_pasto.alimento_id`). Fix per le installazioni future.
2. `schema_sync._fix_cross_db_fk` generalizzato (`_CROSS_DB_FK_FIXES` + helper introspettivo `_recreate_table_dropping_fk`): ricrea `valori_misurazione`/`obiettivi_cliente` senza la FK a metriche **preservando righe e indici**, idempotente, no Alembic (gira in frozen). **Auto-ripara i DB deployati al boot.**
3. **Bonus** `_drop_stale_catalog_tables`: droppa dai crm.db deployati anche le catalog stale **popolate** (1111 esercizi ecc.) + VACUUM. Guard: skip su DB in-memory (test single-engine).
4. Niente migrazione Alembic separata — il precedente `esercizi_sessione` usa solo schema_sync (SSoT cross-DB FK, funziona in frozen).

**Validazione:** su **copia del backup reale di Chiara** → 145 valori + 1 obiettivo preservati, FK→metriche rimosse (altre FK tenute), 10 catalog stale droppate (37→28 tabelle), `foreign_key_check` pulito, idempotente, VACUUM 4.55→0.90 MB. Suite **362 passed** + 2 nuovi test schema_sync (7 totali), ruff clean. Dev crm.db guarito → **ADR-003 chiuso al 100%**.

**Da fare a valle:** ship nella prossima versione (auto-heal Alessio/Chiara al primo boot). Pitfall #15 in CLAUDE.md.

### 2026-06-14 — Thread A: P3 (housekeeping) + chiusura

**P3a — `crm_dev.db` archiviato.** Verificato che il runtime non apre il file: `api/main.py`/`system_runtime.py` controllano solo la stringa `"crm_dev" in DATABASE_URL` per il label DEV/PROD. Rinominato `data/crm_dev.db → .archived-20260614` (dati preservati, gitignored).

**P3b — 7 nomi duplicati in catalog.db.** Analisi: ogni nome = 1 attivo canonico (junction complete) + 1 inattivo degradato (`in_subset=0`, zero junction — stesso pattern degli orfani). 5 erano lo stesso esercizio, 2 varianti (Adduttori, Distensioni Pettorali). Decisione founder: **eliminare tutti e 7 gli inattivi + remap**. Eseguito: DELETE 351/468/990/552/1094/389/349 da catalog.db (con media/junction/relazioni), remap dei 3 ref schede dev al gemello attivo (351→350, 990→621, 552→169). catalog 529→522, **0 nomi duplicati**, attivi 466 invariati, integrity OK su catalog+crm, seed 522/738, sha256 ricalcolato. Backup `*.bak-threadA-p3`.

**🏁 Thread A chiuso.** Sintesi del filone catalog.db (giornata 2026-06-14):
- Audit read-only → catalog.db pristino, debito = detrito migrazione in crm.db.
- Ondate 1+2: 29 keeper orfani re-inseriti, 3 scartati (orfani 32→3).
- P1+P1-bis: 10 tabelle catalog stale rimosse da crm.db (ADR-003 chiuso 100%) + **bug latente cross-DB FK corretto** (metriche, fix shippabile auto-heal).
- P3: crm_dev.db archiviato, 7 duplicati risolti.
- Restano solo: azione di release (ship fix metriche) + eventuale correzione memory nutrition (210 vs 512 ricette, fuori scope).

---

## Governance documentazione

### 2026-06-14 — ARCHITECTURE.md (root) + consolidamento doc tunnel 7→2

Filone parallelo ai thread del catalogo: riassetto della documentazione architetturale. Obiettivo — una bussola macro di sistema e un riferimento unico per il sottosistema tunnel, eliminando la frammentazione (7 doc tunnel sovrapposti, 2.567 righe).

**`ARCHITECTURE.md` (root) — nuovo Tier-1.**
- Overview dell'intero sistema: local-first, 3 attori, topologia runtime, la decisione portante dei 3 DB, ciclo di vita di una richiesta, strati, preoccupazioni trasversali, distribuzione.
- Principio: tieni il file piccolo e stabile; i **numeri volatili** (versione, conteggi) NON vivono qui — hanno una sola casa (`api/__init__.py`, `DB_INTEGRITY_AUDIT_*`). Evita l'ennesimo posto da aggiornare e contraddire. (Macro prima del micro — `LEARNING_METHOD.md` Principio 4.)

**Consolidamento tunnel 7 → 2 (+1 archiviato).**
- `TUNNEL_ARCHITECTURE.md` (nuovo, v3.0) fonde 4 doc: `ARCHITECTURE_OVERVIEW` + `CRM_ACCESS_ARCHITECTURE` + `TUNNEL_MIGRATION_STRATEGY` + `VPS_EDGE_SETUP`. Struttura a 3 parti: Concetto → Architettura (P1-P10) → Build & Operations (migrazione, setup VPS, costi, DR).
- `TUNNEL_SECURITY_BOUNDARY.md` (v3.0) assorbe `STRADA_B_IMPLEMENTATION_PLAN` (→ §8-11).
- `TAILSCALE_FUNNEL_SETUP.md` → `git mv` in `docs/archive/` con banner legacy (superato da FRP).
- 5 file fusi rimossi con `git rm` (storia preservata). Backup extra in `/tmp/tunnel_backup_20260614/`.

**Decisioni di consolidamento:**
- **Deleghe anti-duplicazione:** i 3 attori vivono solo in `ARCHITECTURE.md`; il threat model solo in `SECURITY_MODEL.md`; gli acceptance criteria solo in `TUNNEL_SECURITY_BOUNDARY.md`. I doc tunnel ci puntano invece di ricopiare. (Founder ha confermato le 3 deleghe.)
- **Armonizzata** la tensione tra BOUNDARY (chiedeva IP forwarding) e STRADA_B (sceglieva lockout): il rate limiter è presentato come *orientamento proposto, da valutare al momento dell'implementazione*, non come decisione chiusa.

**Allineamento degli stati alla realtà del codice (non ai doc).**
- Verifica diretta sul ramo `FitManager_Studio`: Fase 0 ✅, Fase 1 ✅ (incl. frpc bundle + health endpoint reale `GET /system/tunnel-status`), Fase 2/3 ⬜.
- **Strada B: APPROVATA ma NON IMPLEMENTATA** — confermato dal codice (nessun claim `role` in `create_access_token`, nessun `LoginLockout`, middleware ancora whitelist `/public`). Aggiunta tabella §0bis in `TUNNEL_SECURITY_BOUNDARY` per evitare che il doc sembri descrivere qualcosa di già fatto.
- *Principio:* un documento che mente sullo stato è peggio di un documento assente. Il codice del ramo attuale fa fede.

**Puntatori riallineati (solo doc attivi):** `ARCHITECTURE.md`, `docs/INDEX.md` (7 righe → 2), `CLAUDE.md`, `ADR-011`, `LEGAL_REGULATORY_REPORT.md` (7 riferimenti + fix cross-ref §P2), `SUPPORT_RUNBOOK.md`, `UPGRADE_PROCEDURE.md`, `LAUNCH_SCOPE.md`. **Non toccati** i diari `learning/`, le spec congelate `archive/specs/` e le righe di changelog (riscriverli falsificherebbe la storia).

**Lavoro docs-only:** nessun codice toccato, nessun quality gate richiesto.

---

## Distribuzione

### 2026-06-16 — v1.0.12: fix upgrade installer bloccato da `frpc.exe` orfano (codice 5)

Installando v1.0.11 sopra v1.0.10, l'installer si fermava con `ERROR_ACCESS_DENIED` (codice 5) sovrascrivendo `backend\frpc.exe`. Causa: un `frpc.exe` **orfano** di una sessione precedente teneva il lock sul proprio binario (un .exe in esecuzione locka il proprio file immagine su Windows).

**Catena causale (due livelli).**
- `frpc` e' un processo **nipote detached**: `launcher.bat` (cmd) → `fitmanager.exe` (`start /B`) → `frpc.exe` (`subprocess.Popen`, `CREATE_NO_WINDOW`). Il suo cleanup dipendeva solo da `atexit` + shutdown ASGI (`_tunnel_manager.stop()`), percorsi che **non scattano** su chiusura brusca. Chiudendo la finestra del launcher, `fitmanager.exe` muore ma `frpc.exe` (nipote, altro contesto) **sopravvive orfano**.
- L'installer (`fitmanager.iss`) **non chiudeva i processi** prima di sovrascrivere → tentava la sostituzione a caldo → codice 5.

**Perche' ora.** `frpc.exe` e' nel bundle solo dalla ~v1.0.10 (Fase 1.6, 2026-06-09). v1.0.10 → v1.0.11 e' stato il **primo upgrade** a doverlo rimpiazzare: condizione latente diventata attiva. Fresh install non lo mostra (niente da sovrascrivere).

**Fix doppio (difesa in profondita').**
- **Fix B — causa radice** (`api/services/tunnel_manager.py`): `frpc` agganciato a un **Windows Job Object** con `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` (`_create_kill_on_close_job` + `_assign_process_to_job` via `ctypes`). Il SO uccide `frpc` quando l'ultimo handle al job si chiude — cioe' quando il backend termina, comunque termini. Fallback su `atexit`/`stop()` se il job non e' disponibile (non-Windows / errore).
- **Fix A — sintomo** (`installer/fitmanager.iss`): `CloseApplications=yes` + `RestartApplications=no` (Restart Manager, scoping per lock di file) + `[Code]` `PrepareToInstall` con `taskkill /F /T` su `frpc.exe` e `fitmanager.exe` (nomi app-specifici, nessun collaterale su `node.exe` estranei).
- *Perche' entrambi:* le macchine gia' deployate ospitano ancora il binario orfanabile; solo il Fix A le sblocca al **prossimo** upgrade. Il Fix B impedisce che si ricreino orfani da li' in avanti.

**Validazione.** Job Object creato OK su Windows reale; pipeline ADR-004 verde (pytest 364, ruff clean, next build, smoke 5/5); artifact `FitManager_Setup_1.0.12.exe` (SHA-256 `df2d602e…fb50`), tag `v1.0.12` pushato.

**Concetto catturato:** `LEARNING_BUILD_DISTRIBUZIONE.md` (orfanaggio nipote detached + lock immagine .exe + Job Object). Incident: `INC-2026-06-15-installer-frpc-lock.md`. Pitfall #16 in `CLAUDE.md`.

---

## Sicurezza pre-consegna — Gate G1 (cifratura crm.db)

Filone aperto dopo la v1.0.12. **Trigger:** Alessio ha portato il **primo cliente reale assoluto** — un PT storico di Virgin Active. Primo deployment con **atleti e dati reali** (categoria art. 9 GDPR), in anticipo sul POC di settembre, e in quanto tale **fissa lo standard di consegna per tutti**. Il modello di rischio cambia: da "bug recuperabile con patch" a "data breach con notifica al Garante in 72h". L'energia di prodotto si sposta dal bundle esercizi (⏸️ congelato) al **gate di sicurezza pre-consegna**. Decisione founder: solidità prima del tempo → G1 **full, niente postura interim**.

### 2026-06-16 — Gate nel repo + ADR-013 + spike SQLCipher

**Gate.** `docs/technical/PRE_DELIVERY_SECURITY_GATE.md` (elaborato in chat dal founder) portato nel repo e annotato **contro il codice reale** (bridge rule v1.1): per ogni voce una riga "Stato nel codice". 12 voci in 3 tier — Tier 1 bloccanti (G1 cifratura crm.db, G2 rate limiter real-IP, G3 TLS valido, G4 lifecycle ShareToken), Tier 2 (G5 backup cifrato, G6 auth hardening, G7 audit superficie pubblica, G8 logging), Tier 3 legale (G9-G12). **Correzioni ground-truth:** G4 era già ~60% fatto (modello `ShareToken` ha già expires_at/used_at/revoca), G7 ha già lo strato edge (tunnel guard nel middleware Next) — il codice vince sul doc.

**Verifiche nel codice (decisive per G1).** L'engine business nasce in chiaro (`database.py:101`): **crm.db è plaintext**. Il modello cifratura cataloghi (`db_crypto.py`) **non è riusabile** — chiave embedded nel binario (viola "possesso del file insufficiente") e read-only. Il **lifespan tocca crm.db prima di qualsiasi login** (auto-backup, `create_db_and_tables`, `schema_sync`, integrity) → una chiave password-bound impone un **boot a due fasi**. L'auto-backup produce oggi una **copia in chiaro** → tensione G1↔G5 da risolvere insieme.

**ADR-013 (cifratura crm.db a riposo).** Decisione `A + E + F`: **SQLCipher** (cifratura trasparente full-DB, read-write) + **envelope DEK-KEK** (una DEK random wrappata dalla password → cambio password = ri-wrap istantaneo, e abilita una **recovery key**) + **boot a due fasi** (engine late-bound, crm.db sigillato fino al login, maintenance post-unlock). Scartate: cifratura per-campo (rompe le query) e OS/DPAPI (non password-bound, viola G1).

**Spike SQLCipher — VALIDATO end-to-end** (`tools/spikes/sqlcipher/`, 3 cancelli):
1. **Wheel Windows**: `sqlcipher3-0.6.2-cp312-win_amd64` esiste (amalgamation + crypto statica nel wheel; gli altri driver no).
2. **Funzionale**: cifra realmente (ciphertext at-rest, cipher_version 4.12.0), chiave giusta/sbagliata, **integra con SQLAlchemy** via `module=` + `PRAGMA key` su connect (il pattern dell'app).
3. **Nuitka standalone**: l'exe prodotto gira e decifra, Nuitka bundla `_sqlite3.pyd` + `libcrypto-3.dll` (5.2 MB) + `sqlite3.dll` (+~7 MB sull'installer, trascurabile).

**Finding toolchain collaterale (indipendente da SQLCipher).** Lo spike è passato con **MSVC**; il path `--mingw64` della build reale è **rotto su questa macchina** (Nuitka 4.1.2 + gcc 15.2.0 → `windows.h not found` — Nuitka non passa il sysroot al gcc nuovo; `windows.h` *esiste* nel MinGW). Inoltre la **venv di progetto non ha Nuitka installato** → ambiente di build non catturato/riproducibile. Concetto catturato in `LEARNING_BUILD_DISTRIBUZIONE.md` (compilatore C, header di sistema, build riproducibili). → traccia **(b)** dedicata, prerequisito alla *release* con SQLCipher, non al design.

### 2026-06-17 — ADR-013 accettato (decisioni founder)

Chiusi i tre bivi di prodotto/rischio che il codice non poteva decidere:
1. **Recovery key OBBLIGATORIA** al setup. Data-blind ⇒ **niente reset password lato server** (non esiste un nostro cloud): senza recovery, "password dimenticata" = perdita totale irreversibile di dati di atleti reali. Schermata inequivocabile al setup.
2. **Portale atleti fail-closed** pre-unlock: gli endpoint pubblici servono i dati solo dopo che il trainer ha fatto login nella sessione (DEK in RAM per la vita del processo). "App aperta" non basta più: serve "trainer loggato".
3. **Policy password minima** non fastidiosa (soglia lunghezza + blocco password comuni + indicatore di forza). La cifratura vale quanto la password: cifrare con una password debole è un falso senso di sicurezza.
4. **Perimetro**: crm.db + backup cifrati; log fuori (→ G8 separato); cataloghi restano col modello ADR-007.
5. **Migrazione** crm.db deployati (Chiara): cifra in-place al 1° login post-upgrade, **backup-first**.

ADR-013 `proposed → accepted`. **Accettato = decisione presa, NON codice partito.**

### ⏭️ RIPRESA — prossima sessione: DESIGN DI DETTAGLIO G1

Punto di ripartenza lineare. L'implementazione di produzione parte **solo dopo** il design di dettaglio (follow-up 2-4 di ADR-013), che è il prossimo blocco:
- **Formato chiave su disco**: blob `wrapped_DEK` + salt + recovery-KEK — struttura, dove vivono (file accanto al DB, non segreti), flusso setup (genera DEK + recovery key + schermata obbligatoria) vs login (deriva KEK → unwrap DEK).
- **Refactor `database.py`**: engine business da singleton-all'import a **late-bound** (creato post-unlock); `get_session` post-unlock.
- **Boot a due fasi**: spostare auto-backup / `create_db_and_tables` / `schema_sync` / integrity dal lifespan-startup alla **Fase B** (post-login). Pre-unlock il backend serve solo login/setup/health.
- KDF (Argon2id/scrypt/PBKDF2), `PRAGMA rekey` per cambio password, `VACUUM INTO` cifrato per backup (G5), comportamento WAL su DB cifrato.

Parallele, non in conflitto col design: **(b)** decisione toolchain build (MSVC vs MinGW pinnato + congelamento Nuitka); **(c)** G2 rate limiter real-IP (doc dedicato). La call con Alessio (lato tecnico gestita dal founder) definirà "il di più" del rapporto col PT Virgin.

**Lavoro docs-only finora:** nessun codice di produzione toccato (solo script di spike standalone). Implementazione G1 al via dopo il design di dettaglio.

---

## Manutenzione — bugfix in produzione

### 2026-06-18 — INC fingerprint parziale: blocco licenza ricorrente di Chiara

Emerso durante la preparazione della consegna ad Alessio: Chiara (v1.0.10) lamentava che "ogni tanto" l'app le chiedeva la `license.key` bloccando il CRM, risolvendo con un riavvio, forse legato al WiFi della palestra.

**Diagnosi sul codice, poi confermata sul log reale.** Il `machine_id` della licenza è `sha256` di 3 valori hardware via PowerShell/WMI. `_compute_fingerprint` hashava anche un set **parziale** (una query vuota → `sha256("cpu||bios")`) → hash diverso dal `machine_id` firmato → `wrong_machine` → 403 → `/licenza`. Aggravante: `get_machine_fingerprint` **cachava** il valore sbagliato per tutta la sessione → blocco fino al riavvio. La "correlazione WiFi" era coincidente (cambio rete ≈ risveglio da sleep → WMI fiacco). **Prova nel log di Chiara:** oltre 45 righe `WARNING ... Fingerprint parziale: 2/3 identificatori disponibili` in 3 mesi (2026-03-25 → 06-16). Il log del founder (macchina sana): zero — controllo negativo.

**Il test certificava il bug.** `test_partial_failure_still_produces_fingerprint` asseriva `fp != "unavailable"` e `len==64` con 2/3 → falsa sicurezza. In dev WMI risponde sempre 3/3 → invisibile.

**Fix (3 parti, `machine_fingerprint.py`):** (a) set parziale → `"unavailable"`, mai hash; (b) cache solo del completo 3/3, il fallimento non si congela → auto-heal alla richiesta dopo; (c) retry sui vuoti transitori (no-retry sul timeout). Hash 3/3 **invariato** → licenze esistenti (Chiara, Alessio) restano valide. Sicurezza ADR-005 (fail-closed) preservata.

**Verifica:** `test_machine_fingerprint.py` 11/11 (test bacato capovolto + casi parziale/retry/auto-heal/timeout); suite completa **369 passed**; ruff clean. Presente in tutte le versioni → **gate per la consegna ad Alessio**: base per **v1.0.13** che sblocca Chiara e dà ad Alessio una versione pulita. Incidente: `docs/incidents/INC-2026-06-18-fingerprint-partial-license-lockout.md`. Pitfall #17 in `CLAUDE.md`. Post-mortem in `POSTMORTEMS.md`.

### 2026-06-18 — Release v1.0.13 (build MSVC) + 🎯 milestone: tunnel FRP in produzione con un cliente reale

**Build.** v1.0.13 prodotta con la pipeline ADR-004, ma per la **prima volta con MSVC** (`--msvc=latest`) invece di MinGW64: il gcc winlibs 15.2.0 in cache è incompatibile con Nuitka 4.1.2 (`windows.h not found`), MSVC (VS 2022, cl 14.3) compila l'app intera al primo colpo. Risolve di fatto il finding toolchain (b). Pipeline 5/5: preflight (369 test), build, verify (smoke 5/5), seal (`FitManager_Setup_1.0.13.exe`, SHA `948b5e42…eb88`), tag `v1.0.13`.

**Licenza.** Nuova `license.key` per Alessio: claim estratti dalla v1.0.7 (machine_id `4c06bb47…0f37` **invariato**, tier pro, client_id), aggiunto `instance_id=alessio-crociani` (attiva il tunnel → `alessio-crociani.fitmanagerstudio.com`), 12 mesi (scad. 2027-06-13). Firma valida (verify → `wrong_machine` qui = atteso, è la macchina di Alessio).

**🎯 Milestone — la data-blindness esce dalla teoria.** Consegna v1.0.13 ad Alessio (primo partner) via WeTransfer, **testata dal vivo in call**: un cliente esterno ha aperto un **link scheda pubblico reale** instradato attraverso il tunnel FRP self-hosted (VPS edge Hetzner, SNI passthrough, P2 data-blind), terminato sul PC del trainer. È la **prima validazione sul campo** dell'architettura tunnel (Fase 1) con un trainer e un link condiviso reali — non più solo test e2e interni. Registrato in `docs/operations/DEPLOYMENTS.md` (con callout milestone). Residuo noto: cert self-signed (G3/Fase 2) → eventuali avvisi browser fino a Let's Encrypt.

**Modello rami (B):** v1.0.13 = release **verificata sul campo** (test live su macchina reale di Alessio) → trigger di allineamento `main`. `main` portato a includere v1.0.13 + record di deployment.

---

## Filone — Gestione finanziaria avanzata (parallelo a G1)

Nuovo filone aperto dopo la v1.0.13. **Trigger:** dal primo cliente reale (efficienza-driven) emergono due lacune della gestione finanziaria — denaro dovuto che il software non sollecita mai (contratti senza piano rate, caso "Chiara") e assenza dell'asse temporale (fotografia, non film). Prima modifica alla logica finanziaria dal 2026-06-08 (INC-2026-06-08). Differenziatore competitivo: la gestione economico-finanziaria è lo spazio scoperto dai leader anglosassoni.

### 2026-06-19 — Spec + tassonomia + ADR-014 + allineamento governance (docs-only)

**Ponte ritorno (chat → Code → chat).** Tre spec elaborate in chat, analizzate da Claude Code contro il codice reale, rilievi rimandati in chat e reincorporati in **due giri**:
- Giro 1: (1) incassato per periodo ≠ `sum(ENTRATA)` — gli storni (`STORNO_SPESA_FISSA`, ENTRATA non-ricavo) vanno esclusi; `kpi_incassato` è `sum(totale_versato)`, non somma del mastro. (2) "Da pianificare" sul **residuo**, non "Booked − Billed" letterale (doppia-contava acconti e rate saldate). (3) `data_vendita` legacy/nullable → serie competenza best-effort.
- Giro 2: (1) "rate non saldate" nella formula = `stato ∈ {PENDENTE, PARZIALE}`, non solo PENDENTE (allineato all'aging; il residuo delle PARZIALI è già a scadenza). (2) bucket cassa come **partizione complementare** su `id_contratto` (esaustiva per costruzione).

**Verifiche decisive nel codice:** la formula "da pianificare" sul residuo **coincide con `importo_disallineamento`** già calcolato in `_to_response_with_rates` (`contracts.py:49`); `STORNO_SPESA_FISSA` ha `id_contratto = NULL` → l'esclusione "altri incassi al netto storni" lo intercetta.

**Governance allineata PRIMA del codice** (metodo: documentazione e governance alla realtà prima di nuovo sviluppo). Disallineamenti trovati e corretti: `docs/INDEX.md` non citava le 3 spec né `PRE_DELIVERY_SECURITY_GATE.md` e fermava gli ADR a 011; `api/CLAUDE.md` diceva "7 livelli" di Contract Integrity mentre la lista ne enumera 12. Creato **ADR-014** (gestione finanziaria: tassonomia cassa/competenza + vista Contract-first + confine di posizionamento "cash management neutro"), che referenzia le 3 spec senza duplicarle. **Commit `96b5ccc`** (docs-only, pre-commit ruff clean).

**Confine di posizionamento (ADR-014 §Decision punto 5):** il software espone visibilità sulla liquidità reale ("Altri incassi" = ENTRATA fuori contratto), NON nomina né struttura alcuna nozione fiscale. Nessun campo/label codifica lo stato dichiarato/non dichiarato: solo "con/senza contratto". Da validare con tributarista.

### 2026-06-19 — Piano d'implementazione SPEC_RINNOVO (prima del codice)

**Metodo macro-prima-del-micro.** Prima di toccare codice, prodotto un piano ancorato al codice reale (esplorazione 2 agenti su backend + frontend): `docs/technical/IMPL_PLAN_SPEC_RINNOVO.md`.

**Scoperta che riduce il perimetro:** la categoria alert `orphan_contracts` esiste già (`dashboard.py:596-618`, commit `bc28e3c`) e copre quasi il Criterio B. Decisione: **raffinarla** (filtro a residuo positivo + endpoint di risoluzione inline + Sheet azionabile + cruscotto), non creare una categoria duplicata. Criterio A: backend `renew_contract` già conforme alla sicurezza; manca solo il pre-fill `data_scadenza` derivata e la **navigazione guidata post-rinnovo** al piano rate (oggi il trainer resta su `/rinnovi-incassi`).

**Decisioni di prodotto bloccate:** (1) raffina `orphan_contracts`; (2) cruscotto venduto/a-rate/da-pianificare nella **pagina lista `/contratti`**; (3) post-rinnovo → `/contratti/{nuovo_id}?tab=payments`.

**Sequenza:** Step 1 Criterio A (frontend) → Step 2 backend B1+B5 → Step 3 endpoint B2 → Step 4 frontend B3+B4+B6 → Step 5 test (`test_contracts_to_plan.py`). Implementazione al via dallo Step 1.

### 2026-06-20 — SPEC_RINNOVO implementata (Step 1-4), verificata e2e + fix definitivo dual-env

**Implementazione completa** (commit `83c93b1`, `54f0c8a`, `a1a7dae`, `9b701ef`, `af47c23`):
- **Criterio A** — rinnovo guidato: pre-fill date **sequenziali** (figlio inizia `max(scadenza padre+1, oggi)`, durata = padre), tipo/prezzo ereditati; dopo conferma naviga al tab Piano Pagamenti del nuovo contratto. Backend `renew_contract` invariato (già sicuro); unico tocco BE: `data_inizio` padre esposto da `expiring-contracts`.
- **Criterio B** — vista Contract-first: raffinato l'alert esistente `orphan_contracts` (residuo>0, non prezzo>0), nuovo endpoint `GET /dashboard/contracts-to-plan` + `ContractsToPlanSheet` azionabile, agganciato ad AlertHub.
- **Cruscotto B.4** — 3 KPI in `list_contracts` (venduto/a_rate/da_pianificare, formula su residuo, rate non-saldate = PENDENTE+PARZIALE); striscia "Pianificazione" in `/contratti`.
- Test: `test_contracts_to_plan.py` (11 casi: selezione, riconciliazione, multi-tenant). Suite 380 passed.

**Verifica end-to-end live** (skill `/verify`, Playwright su `crm.db` reale): alert "1 contratto senza piano" → sheet (Chiara Agate, residuo 450€) → CTA `/contratti/39` su tab piano con form generazione; rinnovo Nicole Scalmato → **Data Inizio "01 luglio 2026" = scadenza padre +1** (non oggi), durata preservata; cruscotto Venduto 15.177 / A rate 4971 / **Da pianificare 470** (= 450 zero-rate + 20 di parziali sotto-coperti, differenza attesa e corretta). Zero scritture sul DB reale (rinnovo aperto e abbandonato senza submit).

**Fix definitivo dual-env** (commit `408a682`) — emerso durante la verifica: la rimozione del dual-env (2026-06-09) era **incompleta**. `package.json` (dev=3001), `restart-backend.sh` (dev=`crm_dev.db`) e ~50 script erano residui. Risolto alla radice (decisione founder, Option B): **un solo `crm.db`**; offset porte **dev 3001/8001 vs prod 3000/8000** mantenuto e documentato (fa coesistere sviluppo e app installata); dev/prod ora da **`is_compiled()`** (non dal nome DB, sempre falso ora) — corregge auto-backup-in-dev e `app_mode` sempre "production". Credenziali dev `Fitness2026!` (legate a `crm_dev.db`) rimosse da CLAUDE.md: ora un solo set (`chiarabassani`). Concetto catturato: `LEARNING_APP_ARCHITECTURE.md` (rinnovo sequenziale, convenzioni CRM). Decisione architetturale: `ADR-014`.

**Cruscotto "Da incassare" chiarito** (commit `739f69d`, SPEC v1.4) — il founder ha rilevato (re-verify) che i 3 KPI affiancati Venduto/A rate/Da pianificare confondevano: **non sommano** (Venduto=prezzo, A rate+Da pianificare=residuo) e Venduto collide con Fatturato. Ristrutturato in due blocchi per scope: Storico (Fatturato/Incassato "incl. chiusi") + "Da incassare · aperti" con ancora **Residuo = A scadenza + Da pianificare**. Backend `kpi_venduto`→`kpi_residuo`. Concetto: `LEARNING_APP_ARCHITECTURE.md` ("affianca solo ciò che somma; una vista = uno scope"). Verifica visiva founder OK.

### 2026-06-20 — Strategia SPEC_GESTIONE_FINANZIARIA_TEMPORALE (piano prima del codice)

Ripreso il filone (RINNOVO chiuso). Piano ancorato al codice (esplorazione 2 agenti BE+FE): `docs/technical/IMPL_PLAN_SPEC_TEMPORALE.md`.

**Mappa riuso:** nessun endpoint fa già il grouping storico multi-periodo (`/stats` mono-mese per-giorno; `/forecast` proiezione futura) → L1 ex-novo, riusando pattern grouping `(anno,mese)` + helper `_next_months` e logica esclusione storni. Frontend riuso alto: tab in `/cassa` (~4 righe), `ui/chart.tsx` + `GradientKpiCard` + clone `useForecast`; L3 stacked bar già fatto (`WeeklyPulse`); L2 a 2 serie da assemblare (`MeasurementChart` + `ProjectionChart`). `data_vendita` nullable → competenza best-effort.

**Decisioni founder bloccate:** (1) vista in **nuova tab "Andamento" /cassa**; (2) **"Altri incassi" + cash flow reale subito in L1** (confine di posizionamento §0 vincolante: nessun campo/label codifica stato fiscale, validare con tributarista); (3) **correggere `monthly_revenue`** (oggi `sum(ENTRATA)` generico → sovrastima; allineare a categorie contrattuali, verificare trainer maturity).

**Sequenza:** L1 (periodo+altri incassi+tab) → fix monthly_revenue → L2 (trend 2 serie+competenza) → L3 (composizione stacked) → test (`test_financial_trend.py`). Implementazione al via dal prossimo step.

---

### 2026-06-20 — SPEC_TEMPORALE implementata (L1+L2+L3) + nuovo filone: rinnovi scaduti / retention

**SPEC_GESTIONE_FINANZIARIA_TEMPORALE completa** (commit `9b36358` L1, `a053e85` fix monthly_revenue, `042b30c` L2, `60b1852` L3, `5da399e` fix grafico). Tab "Andamento" in /cassa: L1 incassato per periodo + altri incassi + cash flow reale (storni esclusi); fix `monthly_revenue` (incassi da contratti, no storni/altri); L2 venduto/competenza + grafico Incassato-vs-Venduto (ComposedChart); L3 composizione nuovi/rinnovi · acconti/rate (stacked + toggle). 389 test. Verificato a schermo dal founder.

**Gotcha catturato:** recharts non vede le `<Bar>` dentro un React Fragment `<>…</>` (assi sì, serie/legenda no) → serie condizionali via `.map()` su array. `LEARNING_APP_ARCHITECTURE.md`.

**Nuovo filone — rinnovi scaduti / retention (gap rilevato dal founder).** I contratti scaduti (`data_scadenza<oggi`) **sparivano silenziosamente**: `/rinnovi-incassi` e l'alert mostrano solo la finestra futura (`get_expiring_contracts` `>= today AND <= +30`), e non esiste stato terminale "perso". → perdita silenziosa di opportunità di rinnovo (denaro) e clienti (churn).

**Decisioni founder:** (1) stato terminale esplicito **"non rinnova" + motivo** (no auto-archivio silenzioso); (2) perimetro = **lente contratto** prima (scaduti da rinnovare), lente cliente (retention/lapsed) progettata e differita; (3) **SPEC + ADR poi piano** (metodo confermato).

**Prodotti:** `docs/technical/SPEC_RINNOVI_SCADUTI_E_RETENTION.md` (v1.0) + `ADR-015` (accepted). Architettura: funnel a stati derivati (`attivo·in scadenza·scaduto·rinnovato·perso`), due lenti separate/collegate, **invariante anti-perdita silenziosa** (nessun contratto aperto+scaduto+opportunità residua esce dalla worklist senza decisione esplicita), esclusione già-rinnovati anche da "in scadenza". Riuso: flusso rinnovo (SPEC_RINNOVO §A) + WhatsApp win-back. Prossimo step: IMPL_PLAN ancorato al codice.

---

### 2026-06-20 — RINNOVI_SCADUTI: scoperto difetto grave (sospensione) all'esame del dato reale

Implementati Step 1-5 (modello esito_rinnovo, endpoint client-aware clients-to-recover, azione non-rinnova, UI sezione + alert; commit 393a929/681d491/3296308/558b537). All'esame del founder sul DB reale (clienti Floris/Buscaglia/Merchiori/Scalmato) emerso un **errore logico silenzioso**: contratti **scaduti per data ma con sedute prepagate residue** (Paola 18/20, Merchiori 5/10, Scalmato 7/10) venivano contati "attivi" (kpi_attivi=chiuso==False) e/o offerti come "da recuperare" — quando il trainer **deve** ancora quelle sedute. Causa meccanica: l'auto-close richiede SALDATO+crediti-esauriti, quindi un pacchetto pagato con sedute residue non si chiude mai e resta `chiuso=0` per sempre.

**Diagnosi sul dato reale** (non su assunzioni): simulato `_lapsed_client_candidates` sul crm.db → restituisce tutti e 4 come candidati ⇒ il difetto è di **modello**, non l'asimmetria di visibilità riportata (quella è runtime/refetch — la logica li ritorna tutti). Trovati anche: rappresentante scelto tra i soli contratti aperti (ignora i chiusi più recenti → punto di interruzione sbagliato, caso Dalila).

**Decisione (founder):** introdurre lo stato **SOSPESO** di prima classe. Ciclo a 4 stati derivati (ATTIVO/SOSPESO/ESAURITO/CHIUSO); **ingaggio = ATTIVO o SOSPESO**; worklist dedicata "Contratti sospesi / sedute da recuperare" (estendi o decadi, decisione esplicita — invariante anti-perdita esteso alle SEDUTE prepagate). "Clienti da recuperare" esclude gli ingaggiati. SPEC → v2.0 (§3 ciclo, §3-bis ingaggio, §4-bis sospesi), ADR-015 emendamento 2. Prossimo: IMPL_PLAN della revisione, poi fix endpoint/UI (Step 2-5 vanno corretti per escludere i sospesi). Concetto: la finanza è il 90% del CRM, gli errori logici silenziosi vanno presi prima della consegna.

---

### 2026-06-20 — Consolidamento: FINANCIAL_DOMAIN_MODEL.md (SSoT del dominio finanziario)

Rilievo founder: stavamo definendo gli stati del contratto **per-feature** (kpi_attivi qui, "scaduto" lì, "sospeso" ora) con significati divergenti → logiche accavallate + frammentazione documentale (modello sparso su TASSONOMIA + 3 spec + 2 ADR). Stop alla frammentazione: rianalisi olistica vs CRM finanziari migliori e definizione delle **basi univoche**.

**Prodotto:** `docs/technical/FINANCIAL_DOMAIN_MODEL.md` (v1.0, SSoT vincolante): entità; 3 assi indipendenti (tempo/crediti/denaro); **stato di vita derivato in 4 stati** (ATTIVO/SOSPESO/ESAURITO/CHIUSO) via `contract_state()`; vocabolario univoco (**aperto ≠ attivo**, mai più "attivo=chiuso==False"); sotto-stato denaro; rollup cliente (ingaggiato/lapsed); **mappa worklist senza sovrapposizioni**; invarianti anti-perdita (denaro, sedute, clienti). Lacune G1-G5 risolte a livello di modello: G1 "da pianificare" solo su ATTIVO (residuo su scaduto = "da incassare", non pianificabile per guardia rate); G2 1 stato primario + flag denaro (niente worklist sovrapposte); G3 renewal-rate via continuità cliente non solo rinnovo_di; G4 kpi_attivi = stato ATTIVO; G5 terminazioni con motivo (non_rinnova/sedute_decadute/saldo_a_perdere).

**Consolidamento:** TASSONOMIA + le 3 spec finanziarie ora **referenziano** il modello (puntatore SSoT in testa); IMPL_PLAN effimeri → archive a fine implementazione; ADR-014/015 = decisioni. Lato codice: un solo modulo `contract_state()` (SSoT derivazione) da cui derivano KPI/worklist/alert.

**Prossimo:** riprendere l'implementazione contro il modello unico — `contract_state()`, poi correggere le parti già fatte (Step 2-5 RINNOVI_SCADUTI) che divergono (escludere sospesi, kpi_attivi, ecc.).

---

### 2026-06-20 — FINANCIAL_DOMAIN_MODEL v1.1 (rilievi bridge chat incorporati)

La chat parallela ha esaminato il modello v1.0 e prodotto 3 rilievi reali, tutti sull'**asse-tempo** (lo stesso che `chiuso` ignorava — coerenza: il tempo resta l'asse sottovalutato). Incorporati in v1.1 dopo ragionamento Code↔chat:

- **R1 (invariante transizioni indotte dal tempo, §9.4):** `contract_state()` è corretto ma *inerte* — il difetto SOSPESO fu una transizione MUTA, non un dato sparito. Invariante: nessuno stato non-terminale è "homeless"; ATTIVO→SOSPESO/ESAURITO (time-induced, silenziose) devono far rumore = la membership in una worklist È il segnale (modello **pull**: ogni stato ha casa). Push (notifica ad app chiusa) differito ad always-on (Box/tunnel).
- **R2 (rollup cliente natura mista, §4.1):** ingaggiato/lapsed **derivati**; perso **a memoria**; aggiunto **lapsed-freddo** (derivato da `communication_log` + tempo, nessun campo nuovo) e **decadimento asimmetrico**: lapsed si raffredda ed esce dalla worklist calda (opportunità); SOSPESO non decade mai, urgenza ↑ (obbligazione, gli devi sedute).
- **R3 (costanti temporali unificate, §4.2):** `SOGLIA_CHURN_GG=90` **unica** = raffreddamento lapsed = finestra retention (G3) = confine churn. `SOGLIA_IN_SCADENZA_GG=30`. Niente numeri magici sdoppiati.
- **Debito emerso (G1):** `orphan_contracts`/`contracts-to-plan` già implementati violano G1 (filtrano chiuso=False senza vigenza → azione impossibile su SOSPESO/ESAURITO). Da correggere (restringere ad ATTIVO) — primo fix che il modello fa emergere.

Decisioni founder: pull-coverage; freddo derivato da communication_log; una costante unica. Modello dichiarabile fermo → prossimo: `contract_state()` SSoT + fix progressivo (G1 + Step 2-5 RINNOVI_SCADUTI).

---

### 2026-06-20 — IMPL_PLAN_FINANCIAL_REALIGN (piano unico, post-modello)

Modello v1.2 fermo (3 rilievi + 2 robustezze chat incorporati/verificati; G6 scoperto verificando l'auto-close sul codice reale). Scritto **un solo** piano di riallineamento (anti-frammentazione, supera IMPL_PLAN_RINNOVI_SCADUTI): `IMPL_PLAN_FINANCIAL_REALIGN.md`. Blocchi: 0) `contract_state()` SSoT (modulo puro, 4 stati+sotto-stato denaro+engagement, test di confine) → 1) G1 da-pianificare solo ATTIVO → 2) riallineo worklist/KPI a contract_state (clients-to-recover esclude SOSPESI, rappresentante più-recente-assoluto, kpi_attivi=ATTIVO) → 3) worklist Contratti sospesi + estendi/decadi → 4) G6 incassa-residuo diretto → 5) win-back/freddo (communication_log) → 6) differiti (G3 analytics). Invariante di copertura §9.4 verificato dopo ogni blocco. Tutti i doc del dominio finanziario pushati. Prossimo: Blocco 0 (contract_state).

---

### 2026-06-21 — Blocchi 0-2 implementati + FDM v1.3/TASSONOMIA v1.2 + strategia G7 (Preludio installato)

**Codice (branch FitManager_Studio, pushato):** implementati i primi 3 blocchi del riallineamento.
- **Blocco 0** — `api/services/contract_state.py` SSoT puro (Lifecycle 4 stati + `is_rate_planificabile`/`is_residuo_incassabile_diretto`/`residuo`/`crediti_residui`/`money_substate`/`client_engagement`/`evaluate_contract`, costanti) + 53 test di confine (mutua esclusività 16 combinazioni, "scade oggi"→ATTIVO, scaduto+crediti→SOSPESO). Commit 4c28a08/a81da66/4d0808c.
- **Blocco 1 (G1)** — `_contracts_to_plan_candidates` (helper unico endpoint+alert via `is_rate_planificabile`); `kpi_da_incassare_scaduto` nel cruscotto (invariante `residuo = a_rate + da_pianificare + da_incassare_scaduto` preservato). Commit 9cba4ab.
- **Blocco 2 (G4 + fix SOSPESO)** — `kpi_attivi`=ATTIVO + `kpi_sospesi/esauriti`; `_lapsed_client_candidates` riscritto su `cstate.is_engaged` (un SOSPESO non è più win-back — fix difetto reale Paola/Merchiori) + rappresentante più-recente-in-assoluto (§6, caso Dalila); `_crediti_usati_map` estratto. Commit 6f42741. 462 test verdi.

**Ricognizione terminazione anticipata** (workflow 11 agenti read-only): report code-grounded → bridge → **FDM v1.3 + TASSONOMIA v1.2**. Terzo modo di morte del contratto (terminazione anticipata su contratto vivo, conguaglio bidirezionale su base sedute). Decisione **Strada B** (lordo immutabile `totale_versato`; `totale_rimborsato`/`quota_stornata` campi nuovi cresce-solo; `netto_incassato` derivato). Categoria `RIMBORSO_CONTRATTO` (contra-ricavo, non costo) + predicato cassa bidirezionale + 8 query da allineare. `non_rinnova` ortogonale a `motivo_chiusura`. Invariante §9.5.6 `quota_stornata > 0 ⟹ chiuso`.

**Strategia d'implementazione** (workflow 11 agenti: 6 progettisti + 4 verifiche adversariali + sintesi). Sequenza: Prereq P (cash_categories.py + fix Forecast P1 + audit transizione P2 + netto read-side P3) → Blocco 3 (sospesi + Estendi, zero schema) → Blocco 4 G6 (incassa residuo diretto) → Blocco terminazione G7 (4 colonne plain + endpoint atomico 2 gambe + `contract_settlement.py` policy-pluggable) → remediation runbook. **4 BLOCKER catturati dalla verifica adversariale:** (1) `residuo` inline `contracts.py:127`/`financial.py:274` = debito-fantasma nel dettaglio → delegare a `contract_state.residuo()` esteso con `quota_stornata`; (2) G7 NON deve chiamare `_sync_contract_chiuso` (riaprirebbe il SOSPESO terminato); (3) soft-delete rate solo non-saldate (mai SALDATA → romperebbe `totale_versato==ΣENTRATA`); (4) financial-trend doppia decomposizione. Alembic head = `b2f1a9c7d4e3`.

**Preludio installato (zero codice):** FDM v1.3 + TASSONOMIA v1.2 in `docs/technical/` (sostituite v1.2/v1.1); strategia → `IMPL_PLAN_FINANCIAL_REALIGN.md` v1.3; INDEX allineato; puntatore `contract_state.py` SSoT in `api/CLAUDE.md`. **Unica decisione aperta pre-migrazione G7:** enum di `motivo_chiusura` (esito economico vs ragione) — non blocca Blocco 3/4. **Prossimo:** Prereq P + Blocco 3 (entrambi costruibili subito, zero schema, zero policy).

---

### 2026-06-21 — Prereq P + Blocco 3 implementati (post-Preludio)

Ripreso lo sviluppo contro l'IMPL_PLAN v1.3 installato. Due blocchi, entrambi pushati.

**Prereq P** (commit 32437da) — fondazione per G6/G7, solo pezzi con effetto reale e testabile:
- **P0** `api/services/cash_categories.py`: SSoT delle categorie cassa + predicato "movimento contrattuale" bidirezionale (IN `ACCONTO_CONTRATTO`/`PAGAMENTO_RATA`, OUT `RIMBORSO_CONTRATTO`). Consolidate 3 literal sparsi (contracts.py, rates.py, movements.py) in un'unica fonte.
- **P1** fix Forecast "entrata-fantasma": `get_forecast` filtra ora `Contract.chiuso == False` sulle entrate certe (rate PENDENTI su contratti chiusi non più proiettate). Learning capturato (join-to-parent deve filtrare lo stato terminale del padre).
- **P2** `log_contract_lifecycle_transition()` in `_audit.py` (idempotente, no-commit, trainer_id dal contract): audita la transizione `chiuso` finora muta. Cablato in pay_rate (completamento), unpay_rate (riapertura_pagamento), agenda._sync_contract_chiuso (completamento/riapertura_crediti).
- **Raffinamento scope:** esclusioni-query inerti (#2/#3/#4/#8) + P3 netto-per-vista spostati in G7 (codice testabile col rimborso reale, non difese inerti). Learning capturato.
- +12 test (cash_categories 6, forecast_phantom 2, lifecycle_audit 4).

**Blocco 3** (commit 22d864e) — worklist "Contratti sospesi" + Estendi:
- Backend: `_suspended_contracts_candidates` (deriva SOSPESO da contract_state, helper unico endpoint+alert, aging invertito) + `GET /dashboard/suspended-contracts` + alert `suspended_contracts`. Dual-debt esplicito (sedute ≠ denaro). ESTENDI = PUT /contracts/{id} (riuso puro).
- Frontend: SuspendedContractItem, useSuspendedContracts, KPI "Sospesi" + sezione /rinnovi-incassi + SuspendedCard/ExtendDialog (DatePicker minDate=oggi, default +30g) + icona AlertHub. 2 bottoni chiusura disegnati DISABILITATI → G7 (design-scope ≠ build-scope).
- +11 test. Completa l'invariante §9.4 (lo SOSPESO non è più "homeless"). Suite **485 passed**, next build verde.

**Doc allineati (metodo):** api/CLAUDE.md (contract_state + cash_categories nei services, nota "già in codice" vs "in arrivo G7", tabella endpoint dashboard con le 3 worklist + pattern helper-unico), INDEX/IMPL_PLAN §6/§2 con stato implementato, 2 learning capture in LEARNING_APP_ARCHITECTURE.

**Prossimo:** Blocco 4 — G6 incassa residuo diretto (zero schema, zero policy; riusa cash_categories + auto-close; gemello-in-entrata del rimborso G7).

---

### 2026-06-21 — Review bridge sul codice mergiato (ALLINEAMENTO_REVIEW_CODICE_v1.3) — verificata e assorbita

La chat-bridge ha rivisto il codice realmente mergiato (post Blocco 3 + Prereq P) e prodotto
`ALLINEAMENTO_REVIEW_CODICE_v1.3.md` (artefatto-ponte su Desktop, non installato nel repo: i suoi
esiti durevoli sono assorbiti nei doc canonici qui sotto). Ogni rilievo verificato sul codice vivo.

**NOW (fix immediati, in questo batch):**
- **2.1 type drift** — `AlertItem.category` (types/api.ts) non includeva `suspended_contracts` /
  `clients_to_recover` che il backend emette → union completata (runtime già reggeva via fallback, ma la
  union "mentiva"). next build verde.
- **2.3 giorni_ritardo negativo** — `get_clients_to_recover`: il rappresentante è il contratto più recente
  IN ASSOLUTO e può essere CHIUSO con scadenza FUTURA (caso 3 muti) → `max(0, …)`. Niente più "Scaduto da
  −N giorni" sul dato reale di Chiara. +test.

**LOAD-BEARING verificato + tracciato (fix vero in G7):**
- **§1 reopen-semantics di `_sync_contract_chiuso`** — il ramo di auto-riapertura riapre QUALSIASI chiusura
  non-da-completamento (crediti non esauriti). **Già latente oggi** sulle chiusure manuali; **sistematico
  con G7** (ogni terminazione la innescherebbe → stato zombie `chiuso=False ∧ quota_stornata>0`, viola
  §9.5.6). Tracciato da `test_lifecycle_audit.test_manual_close_not_reopened_by_agenda_edit` (**xfail
  strict** → xpass quando G7 aggiunge la guard, allora si toglie il marker). Correzione all'analisi
  bridge precedente che lo dava come solo-post-G7.

**Delta modello assorbiti (verificati → canonici):**
- **FDM §9.5.6** esteso con la *semantica di riapertura* (auto-riapertura solo per completamento; le
  chiusure deliberate si riaprono solo via reopen/unterminate espliciti).
- **TASSONOMIA §7.2 / FDM §7-G7 / IMPL_PLAN §5**: aggiunta la **9ª query** da allineare in G7 —
  `get_dashboard_summary.monthly_revenue` (vista contrattuale netto: sottrarre i `RIMBORSO_CONTRATTO`).
  `divergent_count` dello stesso summary resta corretto (lordo vs Σ ENTRATA, invariante Strada B).
- **IMPL_PLAN §4.7**: aggiunto il guard sul ramo reopen come fix vincolante di G7.

**Tail (quando si toccano i file):** 2.4 `expiring-contracts` logica data inline → derivare da
`contract_state` (già notato in Blocco 2, nessuna regressione).

**Confermato fedele dal bridge (non toccato):** worklist sospesi (helper unico, aging invertito,
unità=contratto), dual-debt, design-vs-build dei 2 bottoni disabilitati, retention≠chiusura, Prereq P
(P0/P1/P2), query contra-ricavo correttamente NON ancora editate (inerti fino a G7).

Suite verde (1 xfailed atteso), next build verde. Prossimo: Blocco 4 — G6 incassa residuo diretto.

---

### 2026-06-22 — Addendum bridge §6 (guard allowlist) assorbito + fix tz minore

**Addendum §6 del bridge** (artefatto su Desktop): leggendo `test_manual_close_not_reopened_by_agenda_edit`
(xfail strict) contro la prosa della guard è emerso che la formulazione **denylist** ("non riaprire se
motivo∈TERMINAZIONE_* o quota_stornata>0") **non copre** il caso del test (chiusura manuale → `motivo=NULL`,
nessuno storno) → lo strict-xfail non sarebbe mai diventato xpass. Riformulata **al positivo (ALLOWLIST)**:
l'auto-riapertura credit-driven di `_sync_contract_chiuso` scatta **solo se `motivo_chiusura==COMPLETAMENTO`**;
NULL (manuale/legacy) e TERMINAZIONE_* non si riaprono. Due prerequisiti: (1) il completamento DEVE scrivere
`motivo_chiusura=COMPLETAMENTO` (altrimenti la allowlist congela anche le riaperture legittime); (2) doppio
significato del NULL dichiarato (guard=non-riaprire; runbook=completamento implicito). Alternativa di scope
(Giacomo): togliere `chiuso` da `update_contract`. Assorbito in **FDM §9.5.6** + **IMPL_PLAN §4.7**; commento
del test allineato. Tutto **G7** (la colonna `motivo_chiusura` esiste solo lì).

**Fix tz minore** (bug PRE-ESISTENTE esposto dalla suite a cavallo di mezzanotte): `completed_today_count`
(workspace_engine) confrontava `completed_at.date()` (UTC, da `toggle_todo` → SQLite naive) con
`reference_date` (locale) → nella finestra 00:00–02:00 CEST sottocontava. Estratto `_completed_in_local_day`
(riporta `completed_at` al fuso locale prima di `.date()`). **Verificato nella finestra esatta del bug**
(local 00:33 / UTC 22:33): prima 1 failed, dopo 24 passed; **suite completa 487 passed / 0 failed / 1 xfailed,
girata ancora di notte** (i 3 fallimenti precedenti erano tutti questa classe). +unit test del contratto
helper (deterministico, machine-independent). Learning capturato (tempo UTC salvato vs locale confrontato).

---

### 2026-06-22 — SPEC_VOCABOLARIO unificazione stati contratto: v1.0 (chat) → review code-grounded → v1.1 → integrata in docs/

**Cosa.** Prodotta in chat la `SPEC_VOCABOLARIO_E_CLASSIFICAZIONE_CONTRATTI.md` (spec di *consumo del SSoT*
+ *vocabolario UI*): il `contract_state` modella già correttamente lo stato su due assi ortogonali, ma
nessuna superficie frontend lo consuma — `/contratti`, scheda dettaglio, `rinnovi-incassi`, `workspace_engine`
reimplementano la classificazione ognuna a modo suo (cascata `getPaymentBadge`, `is_scaduto` ricalcolato 3×,
3 definizioni divergenti di "insolvente"). Stesso contratto, nomi diversi a un click di distanza.

**Bridge — review code-grounded (Claude Code, workflow 9 agenti su codice vivo).** 6 cluster di verifica
adversariale + 3 dimensioni strategiche. **La diagnosi della v1.0 regge interamente** (claim verificati
carattere per carattere): la cascata a 8 rami (non 7), il collasso `chiuso?"Chiuso":"Attivo"`, i 3 ricalcoli
frontend, il SSoT che espone già `money_substate`/`MoneySubstate`/`evaluate_contract` (6 campi)/`ha_rate_scadute`
sulla riga/batch-fetch pronti, e §4.7 che **omette** i 3 siti inline-residuo del `workspace_engine`. Scoperta
strategica: la delega-residuo del §2.2 **NON collide con G7 — lo anticipa** (è il BLOCKER #1 "residuo→SSoT",
byte-identico oggi, forward-compatible con `getattr(quota_stornata,0)`).

**v1.1 — 3 gap HIGH chiusi con decisioni Giacomo** (i gap che la stesura a fonte-codice-chiusa non poteva
vedere): **G1** il segnale di riga "denaro arretrato" scatta **anche su ATTIVO con rate scadute** (il caso
"Rate in Ritardo" non sparisce dalla lista); **G2** insolvenza segnalata con **icona `AlertTriangle` +
`aria-label` + opacità alzata**, mai col solo colore (regola `frontend/CLAUDE.md`), niente badge testuale;
**G3** i nodi della catena rinnovi ricevono il **proprio `lifecycle`** (estensione `RenewalChainItem`).
Più: imprecisioni corrette (8 rami; 3 def su 2 file; `financial.py:274` è doc non calcolo; AC-4/AC-5; drift
righe), AC aggiunti (esclusività `is_insolvente`/`in_scadenza`; non-regressione + KPI cumulativi pitfall #14;
edge `prezzo_totale=null`; percepibilità senza colore; riconciliazione "rate scadute" a una sola formula
SSoT), grep-guard riposizionato da "CI" (inesistente) a `check-all.sh` con allowlist, censimento esteso dei
siti inline-residuo (`dashboard.py:497` **senza clamp = bug latente di residuo negativo**, `rates.py:525/734`).

**Integrazione in docs/ (questo step, ZERO codice).** Spec installata in `docs/technical/`; **puntatore
"insolvente"** (flag derivato cross-asse, non uno stato) in `FINANCIAL_DOMAIN_MODEL.md` §4 (vocabolario) +
§5 (sotto-stato denaro, fonte unica di "rate scadute") — mirrorato anche sul working copy Desktop per non
perderlo al prossimo install; riga in `INDEX.md`; pointer in `api/CLAUDE.md` (sezione `contract_state.py`).
**Nessun bump di versione del FDM** (la spec non modifica il modello: `is_insolvente`/`in_scadenza` sono
derivazioni, il modello resta a 4 stati + ELIMINATO).

**Sequenza decisa (verificata):** Giro 1 (`/contratti` + dettaglio + backend) → **G6** (incassa residuo) →
**G7** (terminazione) → Giro 2 (`rinnovi-incassi` + `workspace_engine` + grep-guard). Mai Giro 1 in parallelo
a G6 sugli stessi file. **Prossimo step: implementazione Giro 1.**

**Learning da catturare (livello 3, `LEARNING_APP_ARCHITECTURE`):** un invariante che alcuni siti calcolano
inline non si garantisce **enumerandone** i siti — l'enumerazione manuale è strutturalmente incompleta (qui
ha mancato siti **due volte**: §4.7 e la v1.0 della spec) — ma o **centralizzando** la derivazione (delega al
SSoT) o con **enforcement automatico** (grep-guard); meglio entrambi.

---

### 2026-06-22 — SPEC_VOCABOLARIO Giro 1 IMPLEMENTATO (backend-first, suite + build verdi)

**Cosa.** Implementato il **Giro 1** della spec: il vocabolario contratti è ora unificato via SSoT su
`/contratti` (lista), scheda dettaglio e backend. Le superfici **leggono** la classificazione da
`contract_state.py`, non la ricalcolano. Sequenza backend-first, ogni passo verde prima del successivo.

**Backend.** (1) `is_insolvente(state)` nel SSoT — flag derivato (`lifecycle ∈ {SOSPESO,ESAURITO} AND
rate_scadute`), gemello di `is_rate_planificabile` (+36 test: 4 casi AC-1 + esclusività mutua esaustiva
32 combo AC-2b). (2) `list_contracts`/`get_contract` attaccano alla riga/oggetto i 4 campi derivati
(`lifecycle`/`money_substate`/`is_insolvente`/`in_scadenza`) da `evaluate_contract` — **zero query nuove**
(rate+crediti già batch-fetchati). (3) **Delega-residuo** di `_to_response_with_rates` a
`contract_state.residuo()` — **anticipa il BLOCKER #1 di G7** (residuo→SSoT), byte-identico oggi. (4)
`ha_rate_scadute` di riga **riconciliato** al SSoT `rate_scadute` (AC-1b, una sola formula; equivalente al
vecchio inline grazie ai guard rate-date #9/#10). (5) `RenewalChainItem` esteso con `lifecycle` reale di
genitore/figli (G3, batch-fetch crediti catena). Schema: 4 campi su `ContractListResponse` +
`ContractWithRatesResponse` (con default → create/update/renew restano plain, il FE rifetcha).

**Frontend.** Tipi (`ContractLifecycle`/`ContractMoneySubstate` union + 4 campi su `Contract` base +
`lifecycle` su `RenewalChainItem`). Nuovo modulo **`lib/contract-status.tsx`** = fonte unica del vocabolario
di display (LIFECYCLE_BADGE/MONEY_BADGE + componenti, zero logica/date). `ContractsTable`: eliminata la
cascata `getPaymentBadge` (8 rami) e `getScadenzaStyle`; due colonne **Stato**+**Pagamenti**; **segnale di
riga "denaro arretrato"** (`ha_rate_scadute`) con sfondo rosso dark-safe + icona `AlertTriangle`
(`role="img"`+`aria-label`) resistente all'hover — copre insolventi E ATTIVO in ritardo (G1+G2), mai col solo
colore; Scadenza neutra. `contratti/page.tsx`: `STATO_CHIPS` 2→4 su `c.lifecycle` (+ sanitizzazione filtri
salvati con chiavi vecchie), `matchesSituazione` riancorato (`is_insolvente`/`ha_rate_scadute`/`money_substate`),
edge `prezzo_totale=null` ≠ "Saldato" (AC-12b). `[id]/page.tsx`: i 3 punti di collasso →
`<ContractLifecycleBadge>`, `RenewalChainLink` usa `item.lifecycle` (G3).

**Verifica.** Suite backend **523 passed / 1 xfailed** (+ test integrazione AC-2/2b/3: i campi derivati sono
esposti e coerenti coi KPI su lista+dettaglio). `check-all.sh` (ruff + next build) **verde**, zero errori TS,
26 route compilate. Governance: `api/CLAUDE.md` + `frontend/CLAUDE.md` (sezione "Badge Contratti" riscritta +
pitfall superato) allineati.

**Debito tracciato (Giro 2, dopo G7):** `rinnovi-incassi` (stringhe stato hardcoded) + `workspace_engine`
(secondo motore off-SSoT, 3 siti inline-residuo + censimento esteso `dashboard.py:497`/`rates.py`) da allineare
allo stesso `contract-status.tsx` + grep-guard in `check-all.sh`. Chiunque riapra quei file: usare il modulo.
**Non ancora committato** (checkpoint di review founder); **verifica visiva su dato reale** (AC-8/9c/13:
dark mode + riga rossa + badge catena) ancora da fare.

> *Aggiornamento:* Giro 1 poi **committato `91cbc39`** e **verificato a schermo** (light+dark su crm.db reale);
> bug intercettato dalla verifica e corretto (CHIUSO non mostra più il segnale "denaro arretrato").

---

### 2026-06-22 — PREREQ-prezzo (di G6): invariante `prezzo_totale > 0` + audit invarianti Contract (tighten-first)

**Contesto (decisione founder).** Avvertita la sensazione di "allargare il cerchio" sul finanziario, scelta la
strada **tighten-first** (NON un rewrite): stringere *enforce-ando* gli invarianti del FDM, non patchando edge
a valle. Primo mattone: l'invariante `prezzo > 0` (PREREQ-prezzo, artefatto-ponte Desktop analizzato col bridge).

**Audit invarianti dell'entità Contract (code-grounded).** Scoperta chiave: il **boundary di creazione è già
più stretto del modello ORM** — `ContractCreate` richiede `tipo_pacchetto` non-vuoto, `crediti_totali ≥ 1`,
`data_inizio`, `data_scadenza`, mentre il modello li ha tutti `Optional`. Le "regole ferme" del contratto
esistono già quasi tutte: vivono come constraint al *boundary*, non nel *tipo*. L'unico buco a creazione era
`prezzo` (`ge=0` → accetta 0); e `ContractUpdate` lo lasciava passare (leak). **Decisioni aperte emerse (per
Giacomo):** (1) `data_scadenza` nullable — create la richiede ma FDM/SSoT trattano NULL come "pacchetto senza
termine" → contraddizione cross-layer; (2) `chiuso` settabile via update raw — origine dei 3 muti id 4/9/13,
scope G7; (3) type-honesty `Optional → non-Optional` via migrazione — rimandato.

**PREREQ-prezzo implementato.** (A) Bonifica **backup-first** (regola #11): backup `crm.db.bak-prereq-prezzo-*`,
soft-delete del contratto-test id 43 (prezzo 0, **zero** rate/movimenti/eventi, repro di oggi su cliente reale
Jessica Abarca → eliminato solo il contratto bogus, il suo contratto reale id 19 resta), verifica **zero**
contratti non-eliminati a prezzo NULL/0. (B) `prezzo > 0` su **create E update** (`api/schemas/financial.py`),
**messaggio italiano didattico** condiviso (`PREZZO_OBBLIGATORIO_MSG`), non il 422 Pydantic crudo. (C) SSoT non
toccato; le due guardie di consumo del Giro 1 (`prezzo != null`) **annotate** come difesa-in-profondità (no
terzo sito per una config resa irraggiungibile). **+3 test** (create/update/renew con prezzo 0 → 422). Suite
integrità **22 passed**.

**Assorbito nei canonici.** FDM **§9.5.7** (prezzo>0; `residuo=0 ⟺ saldato` senza asterischi; **simmetria
credito-/debito-fantasma**: campo dedicato quando lo stato *deve* esistere [§9.5.6 `quota_stornata`] vs
invariante a monte quando *non deve* [§9.5.7 `prezzo>0`]) + pointer §5; `api/CLAUDE.md` Contract Integrity;
**senza bump FDM** (consolidamento). ⚠️ **Il working copy FDM su Desktop è drifted dal repo** (manca l'addendum
§6 della review bridge) → il **canonico è il repo `docs/technical/`**; niente mirror su copie divergenti
(housekeeping: archiviare gli `IMPL_PLAN_*` implementati, tenere **un solo** FDM).

**Learning (livello 3, `LEARNING_APP_ARCHITECTURE`):** un valore "magico" (`NULL`/`0`) che il modello legge come
valore legittimo dell'asse è una **collisione semantica** (stesso numero, due significati). Si disambigua alla
radice: *vincolo di integrità* (non deve esistere → validazione a monte) vs *stato di processo* (legittimamente
incompleto → sotto-stato + worklist); il dominio decide quale.

**Prossimo:** decisioni audit aperte (data_scadenza / chiuso-via-update / type-honesty) + riordino doc → poi G6.

---

### 2026-06-23 — Fix flaky test_workspace_today (3 test): orologio congelato (fragilità al confine di mezzanotte)

**Scoperto** eseguendo la suite completa dopo il PREREQ: 3 test in `test_workspace_today.py` rossi
(`assert 2 == 1` su `items[0].root_entity.id`). **Provato ortogonale al PREREQ** (stash di `financial.py`
a HEAD → gli stessi 3 falliscono), e **pre-esistente** (verdi nel run del Giro 1, di giorno; rossi ora, a
mezzanotte passata).

**Causa-radice (test-bug, non code-bug).** I 3 test HTTP creano un evento a `datetime.now() + 30min`. Negli
ultimi 30 min del giorno quell'evento cade **domani** → fuori da `_as_local_day_bounds(oggi)` in
`_build_session_cases` → la sessione imminente **non** viene caricata → l'onboarding del cliente con sessione
non viene **assorbito** → restano due casi onboarding a pari severità/bucket/due → il `_sort_case` cade sul
**tiebreak alfabetico del titolo** (`case.title.lower()`) → "Cash" < "Onboarding" → il cliente sbagliato
finisce in posizione 0. Il **codice è corretto** (un evento di domani non è "oggi"); è il test che assumeva
fragilmente "now+30min = oggi". (Gli autori lo sapevano — commento esistente: «the HTTP endpoint uses
datetime.now() which differs from test time».)

**Fix (deterministico, non assert più lasco).** Fixture **autouse** module-scoped che congela
`workspace_engine._now_local()` a **oggi-09:00 locale** + default di `_create_event` ancorato a **oggi-09:30**
(futuro rispetto a 09:00, sempre dentro i bounds del giorno). I test diretti-engine (che passano un
`reference_dt` esplicito) non usano `_now_local` → non toccati. **25/25 nel file verdi**, deterministici e
indipendenti dall'ora di esecuzione.

**Learning (livello 3, già nel docstring del test):** un test che costruisce dati "relativi a oggi" con
`now() + offset` è **flaky al confine del giorno locale**. La cura non è un assert più permissivo (maschera
l'intento) ma **congelare l'orologio** a un riferimento fisso e ancorare i dati a quello — stessa famiglia dei
fix tz (d77c3fe `completed_today_count`): *salvato in un fuso, confrontato in un altro / costruito a un istante,
valutato a un altro*.

---

### 2026-06-23 — CHECKPOINT RESUME: 3 decisioni audit Contract risolte + stato sessione (tighten-first)

**Stato branch:** `FitManager_Studio` interamente verde — **528 passed / 1 xfailed / 0 failed**. Tre commit
in questa sessione: `d934948` (PREREQ-prezzo + audit), `631a3fd` (fix flaky workspace), + questo doc-align.

**Le 3 decisioni aperte dell'audit — RISOLTE (analisi workflow 3 agenti code-grounded → scelte di Giacomo):**

1. **`data_scadenza` nullable → SÌ, permetti NULL a creazione.** I pacchetti/carnet **senza scadenza**
   (contratto perpetuo a crediti) sono un'offerta reale. Il SSoT li gestisce già (null-safe end-to-end);
   l'unico punto che li vieta è il boundary `ContractCreate` + form. **Decisione: aprire il boundary**
   (`data_scadenza` opzionale in `ContractCreate` + form con "Senza scadenza" + label "Senza scadenza" in
   `ContractsTable`/dettaglio). Zero migrazione DB (colonna già nullable). **Impl pendente** (tighten-first,
   bounded). Registrata in FDM §2.

2. **`chiuso` via `ContractUpdate` → rimozione RIMANDATA a G7.** Nessuna UI live chiude via PUT (bottoni
   manuali già `disabled`); ~15 test usano `PUT chiuso=True` come scorciatoia. Toglierlo ora = ponte
   temporaneo che G7 butterebbe via. In **G7** nascono `terminate`/`close` con motivo+conguaglio → si toglie
   `chiuso` da update e i 15 test migrano **una volta sola** al canale definitivo + si sistema l'auto-reopen
   cieco (`test_lifecycle_audit` xfail bridge §6). Il leak grave (credito-fantasma) è già chiuso dal PREREQ.

3. **type-honesty (NOT NULL / ORM non-Optional) → RIMANDATO, resta boundary-only.** L'integrità è già
   incassata al boundary (entrambi i write-path passano da `ContractCreate`). `NOT NULL` su SQLite = rebuild
   della tabella **più referenziata** del dominio al boot sui DB di clienti reali, gated su zero-NULL che è
   **empiricamente falso** per `crediti_totali` (4 NULL nei backup di marzo). Rischio sproporzionato a una
   pulizia cosmetica mentre la priorità è G1 (cifratura). Allineato a ciò che FDM §9.5.7 già prescrive
   (ORM Optional + guardie annotate). Se mai in futuro: solo TIPO Response/TS, MAI NOT NULL DB, `crediti_totali`
   per ultimo e solo dopo backfill + audit zero-NULL per-cliente.

**⏭️ RIPRESA DA QUI (domani), in ordine:**
- **(a)** Implementare **data_scadenza-null** (decisione 1) — bounded: schema `ContractCreate` opzionale +
  validator condizionale + `ContractForm` (checkbox "Senza scadenza") + label "Senza scadenza" in lista/dettaglio
  + test. Chiude la contraddizione cross-layer.
- **(b)** **Riordino doc** (resto di option-2): archiviare gli `IMPL_PLAN_*` implementati in `docs/archive/`;
  **riconciliare il drift del FDM su Desktop** (la copia `…/svil/learning_method/FINANCIAL_DOMAIN_MODEL.md` è
  indietro rispetto al repo — il **canonico è il repo `docs/technical/`**; allineare o dismettere la copia Desktop).
- **(c)** Poi **G6** (incassa residuo diretto), poi **G7** (terminazione + i rimandi sopra), poi **G1** (cifratura).

**Audit invarianti Contract = "regole ferme" completato:** ~85% delle regole erano già enforced al boundary;
buco prezzo chiuso (PREREQ), 1 contraddizione decisa (data_scadenza), 2 rimandi consapevoli (chiuso/type) con
home in G7/§9.5.7. Niente rewrite: tighten-first ha consolidato senza buttare via il modello sano.

---

### 2026-06-23 — data_scadenza nullable: carnet senza scadenza (decisione 1 audit Contract, bounded)

**Cosa.** Implementata la **decisione 1** dell'audit Contract: `data_scadenza` opzionale a creazione →
i pacchetti/carnet a crediti senza termine sono ora un'offerta di prima classe (FDM §2). Modifica
**bounded** al boundary + frontend; **zero migrazione DB** (colonna già nullable), **zero tocco al SSoT**
(`contract_state.py` era già null-safe end-to-end: `is_scaduto=False`/`is_vigente=True` su scadenza assente
→ lifecycle ATTIVO finché i crediti non si esauriscono, poi auto-close).

**Backend** (`api/schemas/financial.py`): `ContractCreate.data_scadenza: Optional[date] = None`; il
`model_validator` salta il check `data_scadenza <= data_inizio` quando è None (gli altri invarianti —
prezzo>0, acconto≤prezzo — restano). I guard rate (#9 boundary, #10 shortening, update `contracts.py:648`)
erano **già** null-safe (`contract.data_scadenza and …` / `new_inizio and new_scadenza and …`).

**Frontend.** `ContractForm.tsx`: `data_scadenza` zod opzionale + nuovo campo `senza_scadenza` (checkbox
"Senza scadenza (pacchetto a crediti)") che governa due refine condizionali (richiedi scadenza **o**
checkbox; ordine date solo se presente); il submit manda `null` quando la checkbox è attiva; pre-selezione
in edit (contratto già senza scadenza) e in rinnovo (padre carnet). `ContractsTable` + dettaglio `[id]`:
fallback `—` → label esplicita **"Senza scadenza"**. `types/api.ts`: `ContractCreate.data_scadenza` →
`string | null`.

**Test.** Nuovo `tests/test_contract_no_expiry.py` (5): create senza/`null` scadenza → 201; lifecycle
**ATTIVO** in lista anche con `data_inizio` nel passato; rate boundary senza cap; SSoT puro null-safe
(`is_scaduto/is_vigente/is_in_scadenza/contract_lifecycle`). **Suite 533 passed / 1 xfailed**, ruff clean,
next build clean.

**Verifica a schermo.** Form "Nuovo Contratto" su crm.db reale: la checkbox "Senza scadenza" renderizza
nella posizione corretta sotto Data Scadenza. Submit live NON eseguita di proposito — creerebbe un
contratto-test sul crm.db reale di Chiara; il path POST→persistenza→lifecycle è coperto dai 5 test
d'integrazione sul router reale.

**⏭️ Prossimo:** (b) riordino doc (archiviare `IMPL_PLAN_*` implementati; riconciliare drift FDM Desktop,
canonico = repo) → poi **G6** (incassa residuo) → **G7** (terminazione) → **G1** (cifratura).

---

### 2026-06-23 — Riordino docs/: audit code-grounded + consolidamento (eleganza, 1 sottosistema = 1 riferimento)

**Perché.** Il filone finanziario aveva generato 9 doc che descrivevano lo stesso dominio (2 SSoT + 3 spec
+ 3 impl-plan + 2 ADR) con sovrapposizioni e drift; il cluster sicurezza aveva 4 reference per la stessa
storia. Confusione in arrivo. Principio del founder: eleganza e semplicità.

**Metodo.** Workflow multi-agente **code-grounded read-only** (14 agenti: 13 audit + 1 sintesi, ~1,5M token):
ogni doc classificato live-binding / live-active-plan / superseded / historical-snapshot contro il **codice
reale** (api/services/contract_state.py, cash_categories.py, schemas, routers), sovrapposizioni mappate,
piano di consolidamento sintetizzato. 3 scelte di gusto rimesse al founder (archiviare spec implementate;
foldare la tassonomia L0-L4; toccare il doc esercizi congelato) → tutte verso preservazione+eleganza.

**Fatto (zero codice toccato, solo docs).**
- **Archiviati 11 doc.** Finanziari implementati → `docs/archive/specs/`: SPEC_RINNOVO, SPEC_TEMPORALE,
  SPEC_RINNOVI_SCADUTI + i 3 IMPL_PLAN. Sicurezza storici → `docs/archive/`: SECURITY_AUDIT_BASELINE,
  SECURITY_AUDIT_POST_HARDENING, ANTI_REVERSE_ENGINEERING_STRATEGY (svuota `docs/security/`),
  PRE_DELIVERY_AUDIT_2026_04_17. Operations → `docs/archive/`: SESSION_HANDOFF_2026-06-14.
- **DELTA_v2.2 integrato + eliminato.** Le OP-1..OP-7 (incl. nuova §4ter hosting centrale media) foldate in
  `EXERCISE_LIBRARY_STRATEGY.md`, poi `git rm` del delta (si autodefiniva "da eliminare dopo l'integrazione").
- **Contenuto di valore preservato prima dell'archivio:** la tassonomia attaccanti L0-L4 (la più ricca) è
  stata foldata nel threat model di `SECURITY_MODEL.md` (unico reference sicurezza vivo).
- **7 drift doc-vs-codice corretti** nei doc che restano: banner REALIGN (HEAD `d77c3fe`→`3be936f`, +PREREQ-
  prezzo/Giro1/data_scadenza-null, suite 487→533); SECURITY_MODEL (Tailscale→FRP, crm.db da Fase-3-eventuale
  a gate Tier-1 G1); EXERCISE_LIBRARY (500→522 esercizi, is_fondamentale wired-but-empty, muscle_map_url 29,
  bug config.py risolto); PRE_DELIVERY_SECURITY_GATE + ADR-README (ADR-013 proposed→accepted); ADR-014/015
  (versioni stale + line-cite fragili resi robusti); CLAUDE.md (10→13 ADR).
- **INDEX.md** riscritto (sezioni security rimossa, technical sfoltita, +EXERCISE_LIBRARY, +INC-2026-06-18,
  learning 4→11, nota archivio). **Puntatori incrociati** aggiornati (ADR-007/014/015, REALIGN, RELEASE_CHECKLIST).
- **Verifica anti-orfani** repo-wide (ripgrep): zero riferimenti morti nei doc vivi. I log append-only
  (questo BUILD_LOG, UPGRADE_LOG) conservano le voci datate originali — registrano la storia, non si riscrivono;
  i file citati esistono comunque in `docs/archive/`.

**Esito.** Cluster finanziario 9→6 doc, sicurezza 4→1+gate. `docs/technical/` ~12 file in meno. Ogni
sottosistema torna ad avere un riferimento solo: restano doc o vincolanti o attivi, nessuno "finito ma a
scaffale". Lezione: l'audit della doc va fatto **contro il codice**, non a memoria — diversi doc dichiaravano
implementato ciò che era già in `contract_state.py`/`cash_categories.py` e viceversa.

---

### 2026-06-23 — G6 (Blocco 4): incassa residuo diretto — `POST /contracts/{id}/incassa-residuo`

**Cosa.** Prima cassa ENTRATA legata al contratto **senza passare da una rata**: l'azione per i contratti
SCADUTI aperti (SOSPESO/ESAURITO) il cui residuo non è più rateizzabile (bucket "da incassare scaduto" di
G1). Gemello in entrata del rimborso da terminazione (G7). **Zero schema, zero policy** — solo riuso.

**Backend** (`api/routers/contracts.py`). Flusso atomico (UN solo `commit`): bouncer 404 → guard chiuso 400
→ residuo via SSoT `contract_state.residuo()` (≤0.009 → 400) → cap overpayment 422 → `totale_versato +=` +
ricalcolo `stato_pagamento` → `CashMovement` ENTRATA (`PAGAMENTO_RATA` da `cash_categories`, `id_contratto`
set, `id_rata=None`, nota "Incasso residuo diretto") → **auto-close canonico** via `_sync_contract_chiuso`
(importato da `agenda.py`, nessun ciclo: agenda non importa contracts) → `log_audit` UPDATE. Riusa lo schema
`RatePayment` as-is (mass-assignment: niente `id_contratto/id_cliente/trainer_id` nel body).

**Decisione chiave (audit doppio-log).** `_sync_contract_chiuso` logga **da sé** la transizione `chiuso`
(P2, idempotente, motivo "completamento"). Quindi G6 **non** ri-logga `chiuso` nel diff UPDATE: rispecchia
esattamente `pay_rate` (solo `totale_versato`+`stato_pagamento`) → `_chiuso_transitions` conta **una** entry,
non due. La nota del piano "(H) ...E chiuso" era pre-P2.

**Frontend.** `useIncassaResiduo` (invalidazione **identica** a `usePayRate`); `IncassaResiduoDialog`
riusabile (UX clonata da PayRateForm: quick "Tutto (€residuo)" cap-limitato, `toISOLocal`); due superfici —
**SuspendedCard** (`/rinnovi-incassi`, SOSPESO) e **dropdown riga** di `ContractsTable` (copre anche ESAURITO,
gated su `lifecycle ∈ {sospeso,esaurito}` + residuo>0; ATTIVO resta sul piano rate).

**Test.** `tests/test_incassa_residuo.py` (16): incasso parziale/pieno, shape ENTRATA (+categoria
`PAGAMENTO_RATA` load-bearing), riconciliazione **ledger reale** (Σ ENTRATA == `totale_versato`), boundary
auto-close ESAURITO + no-close con crediti residui + **SOSPESO reale** (scaduto, `lifecycle=="sospeso"`),
overpayment 422, già-saldato/chiuso 400, IDOR/unknown 404, atomicità, audit transizione singola. Suite verde.

**Review adversariale** (workflow 13 agenti, 4 lenti → verifica scettica per finding): 9 rilievi → **4 reali**
(5 falsi positivi correttamente scartati). Tutti corretti: (1) **SSoT residuo** sorvegliato — `residuoIncassabile`
del frontend ricalcolava il residuo inline (viola §8.1/§8.9) → ora il backend lo espone su `ContractListResponse`
(`residuo`, da `state.residuo` già calcolato, costo zero) e il frontend lo **legge**, allineato a SuspendedCard
e forward-safe per G7; (2) dialog condiviso azzerava `residuo/clientLabel` durante il fade-out (~200ms → glitch
"Supera il residuo €0") → `open` disaccoppiato dal target; (3) test "riconciliazione" non interrogava il mastro
→ ora chiude il loop contratto↔ledger; (4) shape-test senza assert `categoria` → aggiunto.

**Lezione.** Ogni nuovo punto di lettura del residuo deve **delegare** al SSoT, anche lato frontend: la review
ha intercettato un ricalcolo inline che "funzionava" (byte-identico) ma avrebbe driftato con G7 (`quota_stornata`).
L'enforcement vero è il SSoT esposto sul wire, non la disciplina manuale (cfr. SPEC_VOCABOLARIO Giro 2).

**⏭️ Prossimo:** **G7** (terminazione: 4 colonne plain + conguaglio policy-gated + endpoint atomico 2 gambe,
rispettando i 4 BLOCKER §4.7) → **G1** (cifratura crm.db). Giro 2 vocabolario dopo G7.

---

### 2026-06-23 — Bridge Chat→Code: verifica e installazione SPEC_REVISIONE_PRE_G7 (zero codice)

**Cosa.** Il founder ha prodotto in Claude Chat `SPEC_REVISIONE_PRE_G7` (Desktop working copy) — una spec di revisione
pre-G7 in due sezioni: **A** convergenza del residuo a `contract_state.residuo()` (refactoring output-invariante,
prerequisito di G7), **B** copertura SOSPESO nel workspace `renewals_cash` (cambiamento funzionale, indipendente).
Metodo bridge: io la verifico **contro il codice vivo** (ground-truth vince), piego i delta, installo la canonica
in `docs/technical/`.

**Verifica (workflow 15 agenti: 5 angoli di sweep + verifica adversariale per ogni sito candidato, ~1,3M token).**
Esito: **spec solida e tesi confermata** — e A.4 confermata incompleta, come la spec stessa dichiarava, per un
margine più ampio. La lista A.4 (4 siti) ha **mancato 5 siti reali** di ricalcolo residuo inline:
- `rates.py:525` — cap anti-overpayment di `pay_rate` (B-ter), **senza clamp**. **PRIORITÀ ALTA**: è un guard del
  Contract Integrity Engine → sotto G7 (`residuo = prezzo − versato − quota_stornata`) over-permetterebbe pagamenti.
- `rates.py:734` — validazione `generate_payment_plan` (clamp ok, ma formula hard-coded anche nel messaggio 422).
- `dashboard.py:497` — `contracts-to-plan.importo_residuo`, senza clamp (era il grounding mio).
- `dashboard.py:446` — where-clause ORM `coalesce(prezzo,0) > coalesce(versato,0)` = predicato `residuo>0`: la
  **parafrasi SQL** che un guard-rail sintattico (AC-A1) NON vede → allowlist, non bug (Step 3 SSoT ri-corregge).
- `DeleteContractDialog.tsx:58` — `importoNonRiscosso`, **unico** ricalcolo residuo del frontend (caveat: prop è
  `Contract` base che non ha `residuo` → allargare a `ContractListItem`).

**Insight (rafforza la spec).** `rates.py:525/734` non sono convergenza cosmetica: sono **guard di integrità**.
Section A non protegge solo i numeri, protegge le difese sui pagamenti dal cambio semantico di G7. Questo eleva A
da "terreno pulito" a prerequisito di sicurezza del Contract Integrity Engine.

**AC verificati.** AC-A1: pytest source-scan su `api/**/*.py` + allowlist `contract_state.py`/`dashboard.py:446`,
regex sulla coppia `prezzo_totale…−…totale_versato` (esclude il residuo di rata); limiti reali documentati
(cieco a SQL/ORM/TS). AC-A2: i 3 seam wire esistono (list `.residuo`, detail `.residuo`, workspace
`finance_context.total_residual_amount`) **ma** `total_residual_amount` è **sovraccarico per `case_kind`** (residuo-
contratto per due kind, somma-rate-scadute per `payment_overdue`) → la fixture va pilotata. AC-A3: l'invariante
`kpi_residuo = a_rate + da_pianificare + da_incassare_scaduto` è **già** asserito (`test_contracts_to_plan.py:218`).

**Section B confermata per trace.** `renewals_cash` ha 3 maglie (overdue rata-scaduta · due_soon [oggi,+7] ·
renewal [oggi,+30]); un SOSPESO (aperto, scaduto, crediti residui, senza rate scadute) cade nel vuoto e non genera
`OperationalCase`. L'integrity-guard #9 (date-rata ≤ `data_scadenza`) garantisce che non possa nemmeno colpire
due_soon. Due correzioni: AC-B1 deve agganciarsi a **`lifecycle==SOSPESO`** (non `residuo>0`: un SOSPESO saldato
con sedute residue va mostrato); AC-B3 dedup via **exclusion-set** (`overdue_contract_ids`), non `merge_key` (nessun
consumer lo legge).

**Fold-back installato.** Spec corretta in `docs/technical/SPEC_REVISIONE_PRE_G7.md` (delta marcati `[Bridge Code
2026-06-23]`: §0bis inventario, A.3 limiti AC, A.4 +5 siti, B.1/B.3 correzioni). INDEX aggiornato (riga + "dominio
finanziario vivo"). Desktop working copy lasciata al founder; **canonica = repo**. ZERO codice.

**⏭️ Prossimo:** implementare **Sezione A** (convergenza + guard-rail, commit a sé, verifica byte-identica) →
**Sezione B** (builder SOSPESO workspace, commit a sé) → **G7**. A e B mai nello stesso commit (§1.1).

---
