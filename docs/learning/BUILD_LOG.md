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

### 2026-06-23 — SPEC_REVISIONE_PRE_G7 Sezione A: convergenza del residuo al SSoT (refactoring output-invariante)

**Cosa.** Tutti i siti che ricalcolavano il residuo del contratto inline (`prezzo − versato`) ora **delegano**
a `contract_state.residuo()` — unica definizione. Prerequisito di G7 (che ridefinirà `residuo = prezzo − versato
− quota_stornata`): senza questa convergenza, ogni copia inline diventerebbe una bugia silenziosa. Refactoring
**output-invariante** (oracolo: la suite di prima, byte-identica).

**Backend delegato (9 siti, incl. i 5 trovati dal bridge oltre la lista A.4):**
- `contracts.py:296` (`kpi_residuo`) → `Σ cstate.residuo(c)`; `:324` (`resto`) → `cstate.residuo(c) − rate`.
- `workspace_engine.py:1135/1324` (finance_context renewals_cash) → `cstate.residuo(contract)` (+`prezzo_totale or 0`
  su `total_due_amount`); aggiunto import `contract_state`.
- `dashboard.py:497` (`contracts-to-plan.importo_residuo`) → `cstate.residuo(contract)` (guadagna il clamp).
- `rates.py:525` (**cap anti-overpayment di `pay_rate`** — guard di integrità: il più importante) → `cstate.residuo`;
  `:734` (`generate_payment_plan`) → `cstate.residuo` + **rimossa la formula hard-coded dal messaggio 422**;
  aggiunto import `contract_state`.
- `dashboard.py:446` (where-clause ORM `prezzo > versato`) **lasciato** come pre-filtro grezzo (SQL, non delegabile;
  il SSoT ri-corregge a valle via `is_rate_planificabile`; regex-safe perché senza `-`).
- `financial.py:310` — corretto il **commento** `# prezzo_totale − totale_versato` (era un falso positivo del guard-rail).

**Frontend.** `DeleteContractDialog.tsx:58` (`importoNonRiscosso`, unico ricalcolo residuo del FE) → legge
`contract.residuo` dal SSoT backend; prop ristretto a `Contract & { residuo: number }` (i caller passano
`ContractListItem`/`ContractWithRates`, entrambi lo espongono) → guadagna il clamp `max(0,…)`.

**Reti (AC).** `tests/test_residuo_convergence.py`: **AC-A1** guard-rail in suite (source-scan `api/**/*.py`,
allowlist `contract_state.py`, regex sulla coppia `prezzo_totale…−…totale_versato`) **+ meta-test** che prova che
non è un no-op; **AC-A2** coerenza cross-surface (lista = dettaglio = workspace `finance_context`, fixture pilotata
su contratto in scadenza → `total_residual_amount` È il residuo-contratto). **AC-A3** (invariante `kpi_residuo =
a_rate + da_pianificare + da_incassare_scaduto`) già presidiato da `test_contracts_to_plan.py:218`.

**Limiti noti del guard-rail (documentati).** AC-A1 è sintattico: cieco a predicati ORM (`dashboard.py:446`),
raw-SQL, forme multilinea e **frontend TS**. AC-A2 è il backstop semantico. L'hook di CI dedicato e una guardia
TS sono direzione futura (§A.5), fuori da questo giro.

**Verifica.** Suite **552 passed / 1 xfailed** (549 + 3 nuovi): ogni test pre-esistente **invariato** → byte-identità
confermata. I 3 siti senza clamp (`dashboard.py:497`, `rates.py:525`, `DeleteContractDialog.tsx:58`) cambiano output
SOLO su contratto sovra-pagato (negativo→0): correzione di bug latente attesa, non regressione. `check-all` verde.

**Lezione.** Per un valore *derivato* (residuo) l'enforcement non è la disciplina ma una **proprietà presidiata**:
il guard-rail (sintattico, prima linea) + il test cross-surface (semantico, cattura anche l'ignoto). Il bridge aveva
già provato che l'enumerazione manuale manca i siti (A.4 ne aveva mancati 5/9). Ora un nuovo `prezzo − versato`
inline fa diventare rossa la suite.

**⏭️ Prossimo:** **Sezione B** (builder SOSPESO nel workspace `renewals_cash`, `lifecycle==SOSPESO`, dedup via
exclusion-set, commit a sé) → **G7**. A e B mai nello stesso commit (§1.1).

---

### 2026-06-23 — SPEC_REVISIONE_PRE_G7 Sezione B: copertura SOSPESO nel workspace (cambiamento funzionale)

**Cosa.** Il cockpit operativo (`/api/workspace/cases?workspace=renewals_cash`) non vedeva i contratti
**SOSPESO** (aperti, scaduti, con sedute prepagate ancora da erogare): cadevano nel buco fra la maglia
*renewal* (`data_scadenza >= today`) e la maglia *overdue* (rate scadute) — mentre lista
(`kpi_da_incassare_scaduto`) e `/dashboard/suspended-contracts` li mostravano già. Cambiamento **funzionale**
(non output-invariante → verificato con test che descrivono i case attesi, non con l'output di prima).

**Backend** (`workspace_engine.py`). Nuovo `case_kind` `suspended_contract` (schema `workspace.py`). Loader
`_load_suspended_contract_rows`: pre-filtro SQL grossolano (aperti + scaduti + con crediti) → classificazione
fine **dal SSoT** `contract_state.contract_lifecycle == SOSPESO` (esclude gli ESAURITO, regola d'oro §10),
aging **invertito** (più vecchio = più urgente: l'obbligazione non decade). Builder
`_build_suspended_contract_cases` → `OperationalCase` in `renewals_cash`. Helper `_suspended_bucket`/`_severity`.
Cablato nell'assembly **dopo** overdue, con l'**exclusion-set `overdue_contract_ids`** (un SOSPESO che ha
ANCHE rate scadute è già `payment_overdue` → niente doppione; la dedup fra builder passa dagli exclusion-set,
**non** da `merge_key` — nessun consumer lo legge).

**Decisioni di dominio (AC-B3, documentate).** Aggancio su **`lifecycle==SOSPESO`, NON su `residuo>0`**: un
SOSPESO *saldato* con sedute residue (residuo 0) è il caso-tipo del doppio-debito e deve comparire. Bucket
**`now`** (obbligazione già scaduta, azionabile subito; non una deadline futura). Severity per aging, **mai
`critical`** (riservato all'arretrato di cassa). **Doppio-debito esplicito**: sedute (asse crediti, nel
testo/segnale) ≠ denaro (asse denaro, `total_residual_amount = cstate.residuo` — già SSoT da Sez. A).

**Frontend.** `case_kind` `suspended_contract` aggiunto all'union `CaseKind` e ai due `Record<CaseKind,…>`
esaustivi (`DEFAULT_CASE_KIND_TONES` + `WORKSPACE_CASE_KIND_META`, label "Sospeso") + `getFinanceAmountLabel`
("Residuo") + `getCaseImpactLine`. (Senza questi il `next build` rompe sui Record esaustivi.)

**Test.** `tests/test_workspace_suspended.py` (7): il SOSPESO compare; ESAURITO/ATTIVO no; bucket `now` +
`total_residual_amount == residuo del dettaglio`; severity alta su molto-scaduto; **dedup** (SOSPESO con rata
scaduta → `payment_overdue`, NON `suspended_contract`); **allineamento AC-B2** con `/dashboard/suspended-contracts`.

**Verifica.** Suite **559 passed / 1 xfailed** (552 + 7); `check-all` verde. Zero regressioni (anche
`test_workspace_today`, già flaky, verde). Commit **separato da Sezione A** (§1.1).

**⏭️ Prossimo:** **G7** terminazione (4 colonne plain + conguaglio policy-gated + endpoint atomico 2 gambe,
4 BLOCKER §4.7; il BLOCKER residuo→SSoT è già soddisfatto da Sez. A). Poi G1 cifratura; Giro 2 vocabolario.

---

### 2026-06-24 — Bridge SPEC_G7.0 + implementazione G7.0 (schema terminazione, zero comportamento)

**Bridge (Chat→Code).** Il founder ha prodotto in Claude Chat `SPEC_G7.0_SCHEMA_TERMINAZIONE` — primo blocco di
uno **scorporo di G7 in 7 sotto-blocchi** (G7.0→G7.6) più sano del piano monolitico §4: isola lo schema dalla
logica (`residuo()` resta intoccato, è G7.1) e **front-carica** la marcatura `motivo_chiusura=COMPLETAMENTO` in
G7.0 perché la reopen-allowlist di G7.2 ci si aggancia. Verifica contro codice vivo: **spec accurata, zero
correzioni, 3 chiarimenti** — (1) `incassa_residuo` (G6) già coperto (chiude via `_sync_contract_chiuso`); (2) il
*clear* del motivo in riapertura è deferito a G7.2 (innocuo in G7.0); (3) `netto_incassato` come `@computed_field`
è empiricamente SAFE col round-trip `model_dump()`+`**` perché i response usano `extra='ignore'`.

**Implementato (G7.0 — commit a sé, rilasciabile, nessuna terminazione avviene).**
- **4 colonne PLAIN** su `contratti` (mai FK, pitfall #15): `totale_rimborsato`/`quota_stornata` (float, monotòni,
  default 0), `data_chiusura` (date?), `motivo_chiusura` (str?, indicizzato). Enum a 4
  (COMPLETAMENTO|CONSUNZIONE|TERMINAZIONE_RIMBORSO|TERMINAZIONE_DECADENZA), NULL=legacy.
- **Migrazione doppio binario**: Alembic `d83abb993ea8` (down_revision=`b2f1a9c7d4e3`, batch add_column ×4 +
  `ix_contratti_motivo_chiusura`, float con `server_default='0'`); schema_sync aggiunge colonne+indice al boot sui
  deployati (path esistente, zero codice nuovo). **Migrazione verificata su CLONE di un backup reale**
  (`auto_20260620_082707.sqlite`, 39 contratti): colonne+indice, **zero FK sulle nuove**, righe preservate,
  idempotente. Backup-first (copia temporanea, originale intatto).
- **Marcatura COMPLETAMENTO (chirurgica)**: `pay_rate` auto-close inline + ramo chiusura di `_sync_contract_chiuso`
  scrivono `motivo_chiusura="COMPLETAMENTO"` quando chiudono. Solo `setattr` aggiunto, nessuna riorganizzazione,
  audit-diff intatto → byte-invariante.
- **Response/TS**: `ContractResponse` += 4 campi + `netto_incassato` `@computed_field` (= max(versato−rimborsato,0),
  oggi == versato); `types/api.ts` base `Contract` += 5 campi (qui ACCURATO sul base, ≠ residuo: sono colonne reali
  + computed_field su ContractResponse base, ritornate anche da POST/PUT).
- **`residuo()` NON toccato** (è G7.1). Nessun endpoint. Le 9 query inerti.

**AC verdi.** AC-7.0-1 (clone backup reale) · AC-7.0-2 (`test_schema_sync` colonne+indice+idempotente, zero-FK) ·
AC-7.0-3 (`test_termination_schema` completamento via pay_rate + agenda) · AC-7.0-5 (enum+NULL) · AC-7.0-6 (response
5 campi + `next build` verde). **AC-7.0-4 byte-invarianza**: suite verde; `test_manual_close_not_reopened_by_agenda_edit`
**resta xfail-strict** (G7.0 marca, ma NON installa l'allowlist — è G7.2). +7 test.

**Lezione.** Lo scorporo di un blocco rischioso (G7) in sotto-blocchi rilasciabili isola la *tesi falsificabile* di
ciascuno: G7.0 = "lo schema regge senza cambiare comportamento" (oracolo: suite byte-identica + migrazione su clone
reale), separata da G7.1 = "il residuo converge col write-off". Il front-load della marcatura COMPLETAMENTO dove
serve (non dove "appartiene logicamente") è ciò che rende G7.2 un fix pulito invece di un intreccio.

**⏭️ Prossimo:** **G7.1** (`contract_settlement.py` conguaglio puro policy-pluggable + `residuo()` esteso con
`quota_stornata` getattr-default + `netto_incassato()` in `contract_state`) → **G7.2** (reopen-allowlist:
`_sync_contract_chiuso` riapre solo se `motivo==COMPLETAMENTO` → `test_manual_close_*` xfail→xpass) → G7.3+ → G1.

---

### 2026-06-24 — G7.1: conguaglio puro + convergenza SSoT residuo/netto (output-invariante)

**Cosa.** Seconda tappa dello scorporo G7: la *logica* della terminazione, senza endpoint né scritture
(il calcolo del conguaglio + l'estensione del SSoT). Output-invariante: oggi `quota_stornata` e
`totale_rimborsato` sono 0 ovunque → nessun valore osservabile cambia (come Sez. A).

**`contract_state.py` (SSoT esteso).**
- `residuo()` ora sottrae `getattr(contract, "quota_stornata", 0)` (Strada B: il LORDO prezzo/versato resta
  immutabile, lo storno abbassa il dovuto). `getattr` default 0 **non-negoziabile** (i 53 test usano
  SimpleNamespace senza il campo; byte-identico finché G7.3 non scrive il primo storno).
- nuovo `netto_incassato(contract) = max(versato − getattr(rimborsato,0), 0)` — DERIVATO, mai ridurre il LORDO.

**`contract_settlement.py` (nuovo, puro — specchio di `contract_state`).** `SettlementPolicy` PLUGGABLE
(`mode='pro_sedute'` default, **PROVISIONAL**); `valore_servizio_reso` su **BASE SEDUTE** (`prezzo·sedute/crediti`,
cappato, tutto-reso se senza monte-sedute); `compute_settlement` → `Settlement` con conguaglio firmato →
esito **RIMBORSO** (versato>reso, importo=abs) / **SALDO_A_PERDERE** (versato≤reso, write-off del residuo) /
**NULLO**; `quota_da_stornare` = `residuo_corrente` (passato dal caller in UNA variabile, fonte-unica-importo
§4.6). Enum `MotivoChiusura` a 4 (SPEC_G7.0 §2) centralizzato qui. Zero DB, zero scritture: G7.3 tradurrà.

**SSoT consistency.** `ContractResponse.netto_incassato` (computed_field di G7.0) ora **delega** a
`contract_state.netto_incassato(self)` (la response LEGGE, non ricalcola) — import locale, una sola formula.

**Confine.** Nessun endpoint, nessuna scrittura di `quota_stornata`/`totale_rimborsato` (è G7.3). La
reopen-allowlist è G7.2 (`test_manual_close_*` resta xfail).

**Verifica.** +15 test (`test_contract_settlement.py` 12 + 3 in `test_contract_state.py`). I 53 test
contract_state restano verdi (getattr-default = byte-identico). **AC-A1 guard-rail verde** (la riga `residuo()`
estesa resta l'unica fonte allowlisted; nessun nuovo ricalcolo off-SSoT). Suite verde, check-all verde.

**⏭️ Prossimo:** **G7.2** reopen-allowlist (`_sync_contract_chiuso` auto-riapre SOLO se
`motivo_chiusura==COMPLETAMENTO`; NULL/TERMINAZIONE_* non si riaprono) → `test_manual_close_not_reopened_by_agenda_edit`
xfail→xpass (poi rimuovere il marker) → **G7.3** endpoint terminate (servono i 3 input di Giacomo per la
*valorizzazione*) → G7.4/5/6 → **G1**.

---

### 2026-06-24 — Bridge SPEC_G7.1_COPERTURA_SETTLEMENT: presidio confini esito (test-only, modulo invariato)

**Bridge (Chat→Code).** Spec di *copertura* su `contract_settlement.py`: aggiungere test che esercitano i
confini di esito (dead-zone ±0.009) e la gamba rimborso, senza toccare il modulo (output-invariante; il
modulo vince — i test descrivono ciò che già fa). La spec chiedeva esplicitamente di verificare gli input
sul modulo reale prima di scriverli (cautela su `round()`).

**Verifica empirica → 2 delta importanti (segnalati, modulo NON modificato):**
- **Δ1 — la dead-zone ±0.009 è IRRAGGIUNGIBILE.** `compute_settlement` fa `conguaglio = round(reso − versato, 2)`,
  quindi il conguaglio è **sempre un multiplo di €0.01**: nessun multiplo di 0.01 vive negli intervalli aperti
  (−0.009, 0) o (0, 0.009). L'input suggerito (`versato=400.005`) dà `conguaglio = −0.0 → NULLO` via il ramo
  `==0`, non via la tolleranza; scan ±0.001 → zero hit di dead-zone. Quindi gli **AC-1/2 non sono costruibili
  come scritti**: il ramo NULLO è raggiungibile solo da `conguaglio == 0.00` (già coperto). La tolleranza ±0.009
  è *inerte* — il pre-rounding rimuove già il rumore di virgola che proteggerebbe.
- **Δ2 — il `round()` sull'abs è INERTE.** `abs(conguaglio)` è già a 2 decimali → `round(abs, 2)` è un no-op;
  toglierlo non cambia output → **AC-4 non "cade solo se round() è in funzione"**.

**Scritto (contro il comportamento REALE, ottenendo comunque l'intento — uccidere il mutante soglia 0.009→0.9).**
+4 test in `tests/test_contract_settlement.py` (10→14): confine reale **−0.01 → RIMBORSO €0.01** e **+0.01 →
SALDO_A_PERDERE** (i casi −200/+100 esistenti NON uccidono il mutante soglia; ∓0.01 sì), **quota_da_stornare
clampa residuo negativo → 0.0** (AC-3, esercita il `max(…,0.0)` mai battuto), **rimborso frazionario 266.67**
(copertura del percorso non-intero; docstring onesto: non muore se si toglie l'abs-round, vedi Δ2). Commento in
testa che lega gli input alla semantica di `round(,2)` (cautela tecnica della spec) per chi tocca `arrotondamento`.
I 10 test esistenti **invariati**; `contract_settlement.py`/`contract_state.py` **non toccati** (zero diff).

**Lezione.** Un gate con tolleranza (`±0.009`) a valle di un arrotondamento alla stessa scala (`round(,2)`) è
**logicamente morto**: la quantizzazione collassa la dead-zone prima del confronto. I test di confine vanno
pinnati sul *valore quantizzato* reale (∓0.01), non sull'epsilon nominale; e una mutazione su un `round()`
ridondante è non-rilevabile per costruzione. Verificare sempre gli input-di-confine sul modulo, mai derivarli
dal codice "a occhio" (il bridge ha intercettato 2 AC non costruibili su 5).

---

### 2026-06-24 — G7.2: reopen-allowlist (functional change) — il bug latente diventa presidio

**Bridge (Chat→Code) + ricognizione call-site (primo passo richiesto).** Spec G7.2: l'auto-riapertura
credit-driven di `_sync_contract_chiuso` riapre qualsiasi chiusura tornata a crediti non-esauriti, a
prescindere dal motivo → latente sulle chiusure manuali (motivo=NULL), e bomba per G7.3 (ogni terminazione
riaperta dall'agenda → zombie `chiuso=False ∧ quota_stornata>0`, viola FDM §9.5.6). Verifica sul codice vivo
(mandata da Giacomo) prima di scrivere la guardia:
- **`COMPLETAMENTO` scritto da 2 call-site** distinti: `pay_rate` inline (`rates.py:570`) + ramo chiusura di
  `_sync_contract_chiuso` (`agenda.py:331`); `incassa_residuo` (G6) passa da `_sync` → eredita. Prereq (1) OK.
- **Riapertura in DUE rami distinti** (non "copie"): `_sync_contract_chiuso` (credit-driven, agenda) **e**
  `unpay_rate` (`rates.py:668`, payment-driven). → per la direttiva chat ("se due rami → allowlist su entrambi")
  la guardia va su **entrambi**.

**Implementato (allowlist POSITIVA su entrambi i rami).** `if reopening and motivo_chiusura != "COMPLETAMENTO":
non riaprire`. Allowlist, **mai** denylist: il NULL è il contro-esempio che una denylist (`motivo ∈
TERMINAZIONE_*`) mancherebbe (NULL non è in TERMINAZIONE_* → si riaprirebbe → bug intatto). **AC-7.2-5
(clear-on-reopen, deferito da G7.0):** scelta **opzione (a)** — la riapertura legittima azzera
`motivo_chiusura=None` ("aperto senza motivo"), pinnato in test. Solo `reopen`/`unterminate` espliciti (G7.4)
riapriranno una terminazione.

**Test.** `test_manual_close_not_reopened_by_agenda_edit`: rimosso `@pytest.mark.xfail(strict=True)` → **xpass**,
ora presidio permanente (AC-7.2-2; suite passa a **0 xfailed**). +3 test: `test_completamento_si_riapre_ancora`
(AC-7.2-3, ramo positivo + clear-motivo), `test_terminazione_non_si_riapre_da_agenda` (AC-7.2-4 forward-guard,
motivo TERMINAZIONE_* + quota scritti via ORM dato che terminate è G7.3), `test_terminazione_non_si_riapre_da_unpay`
(gemello sul 2° ramo). `test_unpay_reopens_closed_contract`/`test_unpay_autoreopen_logs_transition` (COMPLETAMENTO)
restano verdi. **Igiene orologio:** verificato che il conteggio crediti di `_sync` NON ha filtro data → la classe
flaky di mezzanotte (22-23/06) non si applica a questo meccanismo; date comunque ancorate (no `now()+δ`).

**Lezione.** Quando una "guardia" deve distinguere il deliberato dall'automatico, formularla come **allowlist
del caso buono** (`== COMPLETAMENTO`), non come denylist dei cattivi: l'insieme dei "cattivi" è aperto (il NULL
legacy, futuri motivi) e una denylist lo manca silenziosamente. E un auto-comportamento (qui la riapertura) va
cercato in **tutti** i suoi trigger (credit-driven + payment-driven), non solo in quello citato dalla spec — la
ricognizione call-site sul codice è ciò che ha rivelato il 2° ramo che il bridge non vedeva.

**⏭️ Prossimo:** **G7.3** endpoint terminate/preview (2 gambe atomiche, primo storno reale → accende le 9 query,
4 BLOCKER §4.7). **BLOCCATO sui 3 input di Giacomo** per la valorizzazione (SettlementPolicy.mode, oggi
`pro_sedute` PROVISIONAL): policy tributarista, conferma enum motivo_chiusura, R/T contratti muti id 4/9/13.
G7.2 è l'ultimo blocco chiudibile senza quella decisione esterna.

---

### 2026-06-24 — Audit consolidamento PRE-G7.3 (workflow 12 agenti, READ-ONLY, code-grounded + verifica adversariale)

**Cosa.** Prima di aprire G7.3 (bloccato sugli input esterni), audit del raggio d'esplosione del primo storno +
inventario dei test-scorciatoia + caccia discrepanze doc-vs-codice. Metodo: sweep per classe → scettico che rilegge
ogni sito + sweep di completezza per i siti mancati → discrepanze → sintesi. Sostituisce i numeri-a-memoria con un
inventario verificato. Ratificato da Bridge-Claude. **Esiti durevoli (coordinate omesse di proposito — si ritrovano
dal codice, vedi lezione):**

- **Convergenza residuo Sez. A = COMPLETA.** Ogni calcolo di "denaro ancora dovuto" delega a `contract_state.residuo()`
  (backend + letture FE); l'unica where-clause ORM `prezzo>versato` rimasta è safe (filtro `chiuso` + ricalcolo SSoT a valle).
- **Invariante `totale_versato == Σ ENTRATA` REGGE sotto G7.3** → l'intervento sull'àncora è ADDITIVO (nuova leg
  `totale_rimborsato == Σ USCITA RIMBORSO`). L'unico modo di romperla = soft-deletare una rata SALDATA + il suo
  CashMovement ENTRATA. **BLOCKER-3 riformulato col meccanismo esatto:** NON riusare verbatim il cascade di
  `delete_contract` (tocca le SALDATE); terminate non soft-elimina il contratto → riusarlo darebbe Σ ENTRATA < versato
  **permanente**. Terminate soft-elimina SOLO rate non-saldate, mai SALDATA né i loro movimenti.
- **Test PUT chiuso=True = 16 (non ~15).** Uno è un **PRESIDIO TRAVESTITO da scorciatoia**: l'unico test del ramo NULL
  della reopen-allowlist G7.2. Migrarlo meccanicamente a un motivo lo lascerebbe verde e MORTO → **decisione di modello**
  (FDM §9.5.6): ricondurre a simulazione ORM o ritirare con nota; mai migrare meccanicamente. Conseguenza tirata
  dall'audit: se ogni chiusura post-G7.3 passa da terminate (setta sempre un motivo), `chiuso=True ∧ motivo=NULL` diventa
  non costruibile via API → ramo NULL difensivo-irraggiungibile. Correzione a una premessa del pacchetto G7.2:
  `test_manual_close_*` NON è "forward-guard non-toccare" — è questo presidio (ne esiste uno solo).
- **`kpi_incassato` = unico vero sovrastimante aggregato** sotto G7.3 (somma `totale_versato` incl. chiusi → card
  "Incassato" mente di Σ rimborsato). Fuori da entrambe le liste "9 query". Rimpiazzo `netto_incassato()` GIÀ pronto e
  inutilizzato (pattern-firma del filone: enforcement esiste, consumer no). → **edit obbligatorio G7.3, HIGH** (si rompe
  nell'istante del primo storno, non in G7.5).
- **BLOCKER §4.7 parzialmente STALE.** B-1 (residuo→SSoT) incassato in Sez. A; la *guardia allowlist* di B-2 incassata
  in G7.2 — ma la *regola endpoint* ("terminate setta `chiuso`/`motivo`/`data` direttamente, MAI via
  `_sync_contract_chiuso`, che resetterebbe `chiuso=False` su un SOSPESO") resta viva e va nel codice G7.3. Vivi:
  **B-3** (cascade non-verbatim, G7.3) + **B-4** (financial-trend doppia decomposizione, G7.5 per il confine sotto). Il
  pacchetto G7.3 NON deve "far rispettare" B-1 (posizione già tenuta).
- **Confine G7.3 vs G7.5 confermato.** G7.3 = endpoint 2 gambe + accendere `compute_settlement` (fonte-unica-importo:
  `residuo()` PRE-storno, un solo importo per il movement E per il `+=`) + scrivere `quota_stornata`/`totale_rimborsato` +
  USCITA RIMBORSO + soft-delete selettivo + `kpi_incassato`→netto + decisione presidio-NULL. G7.5 = allineamento delle
  viste-cassa che riflettono RIMBORSO_CONTRATTO (burn, movement-stats, le 2 forecast, financial-trend, monthly_revenue,
  **coppia flow_hint+flow_filter — mai uno solo**, `_build_cash_protection` a valle del burn). **Eccezione segnalata a
  Bridge:** la catena variable-burn → `_build_cash_protection` è l'UNICA query G7.5 con profilo-ALLARME (falso CRITICO
  sulla protezione cassa) e non cosmetico/conservativo → valutare il pull-forward dell'esclusione-burn in G7.3 (no-op
  fino al primo rimborso, usa il predicato P0; esercitabile end-to-end nello stesso test) oppure garantire che G7.5
  atterri nella stessa finestra di G7.3 prima che i rimborsi reali inizino. Tutte le altre viste G7.5 driftano in
  direzione cosmetica/conservativa (margine sottostimato) o ottimistica-display (revenue/trend sovrastimati): nessun
  allarme, nessuna blocca l'atto di terminare.
- **Rinumerazione "8 cambiano + 8 invarianti" = DA RATIFICARE in G7.5, non fatto.** Tocca governance (`api/CLAUDE.md`
  dice 8, gli altri 9). TASSONOMIA §7.2 risulta più fedele di IMPL_PLAN §5 (#5 `get_forecast` entrate-certe è eccedenza:
  aggrega RATE non CashMovement → refund strutturalmente invisibile). In G7.5: un solo numero verificato + liste vecchie
  marcate superseded.
- **6 decisioni esterne bloccano G7.3** (nessuna fatto-di-codice): 3 note (SettlementPolicy tributarista; semantica enum
  `motivo_chiusura` per chiusura money-neutral; R/T contratti muti) + 3 emerse dall'audit (target money-neutral per la
  migrazione delle ~14 scorciatoie; destino del ramo NULL; terminate deve accettare scadenza futura).

**Lezione (governance).** I numeri-a-memoria di questo dominio sbagliano sistematicamente: i siti residuo (erano di più
e già delegati), ~15 test (sono 16), BLOCKER §4.7 (uno già morto), e file:riga "pervasivamente driftati di pochi-decine
di righe per commit". → la memory e questo log catturano **esiti e decisioni, non coordinate**; i file:riga si ritrovano
dal codice ogni volta. Mettere nuovi numeri-di-riga in memory creerebbe solo altro drift.

**⏭️ Prossimo invariato:** G7.3 resta BLOCCATO sui 6 input esterni. Quando arriva la SettlementPolicy, Bridge riscrive
il pacchetto G7.3 da questa mappa verificata (scope ristretto, BLOCKER riformulati, `kpi_incassato` dentro, presidio-NULL
come decisione di modello).

**☑️ Checklist chiusura G7.3** `[Bridge ratify 2026-06-24]`**:** lo snapshot `AUDIT_PRE_G7.3_RAGGIO_STORNO.md` è un
**riferimento a tempo** (coordinate-bound a `d7bbcdc`, file:riga che driftano) — mappa operativa **finché G7.3 non è
implementato**. **A G7.3 chiuso → archiviare `docs/technical/AUDIT_PRE_G7.3_RAGGIO_STORNO.md` in `docs/archive/`** con
banner "snapshot pre-G7.3, coordinate driftate, esiti assorbiti in BUILD_LOG + FDM" (stesso trattamento degli IMPL_PLAN
implementati nel riordino 2026-06-23). La riga nomina il file, non le sue righe (lezione del drift).

**Micro-correzioni allo snapshot** `[Bridge ratify 2026-06-24]`**:** (1) `test_kpi_fatturato` confermato **invariante
sotto qualsiasi storno** (legge `prezzo_totale`, non versato/rimborsato) → migrabile a qualsiasi motivo, esce dalla lista
money-neutral (restano ~13 scorciatoie + presidio-NULL); (2) `_build_cash_protection` confermato con **ingresso-burn
unico** → risanata in G7.3 a monte con la burn-exclusion, in G7.5 solo verifica (nessun fix proprio). Entrambi verificati
sul codice vivo.

---

### 2026-06-24 — G7.3: endpoint terminazione anticipata + conguaglio cablato (SPEC_G7.3, due commit)

Bridge ha sbloccato G7.3 (`pro_sedute` = default DICHIARATO + microcopy "proposta ≠ obbligo legale"; #3/#5 cablati;
#2 con default CONSUNZIONE). Ricognizione call-site sul vivo prima di scrivere (regola della spec). Implementato in
**due commit** (scelta founder): **G7.3a `9acd2c5`** (core) + **G7.3b `3f1404b`** (ritiro PUT chiuso + migrazione test
+ frontend). Suite **598 passed / 0 xfailed**, check-all verde (ruff + next build).

**G7.3a — core.** `POST /contracts/{id}/terminate` + `GET /{id}/settlement-preview` (Strada B). Conguaglio puro G7.1
cablato. **Due gambe che CONVIVONO** (non either/or): storno SEMPRE (`quota_stornata += residuo_corrente` → `residuo()`→0)
+ rimborso SE overpaid (`CashMovement` USCITA `RIMBORSO_CONTRATTO` + `totale_rimborsato +=`). Fonte-unica-importo:
`residuo()` PRE-storno in UNA variabile, stesso importo per movimento e campo. B-2-attiva: stato terminale settato DIRETTO,
mai via `_sync_contract_chiuso`. B-3: soft-delete SOLO rate non-saldate (mai SALDATA né i loro CashMovement → àncora regge).
`kpi_incassato`→`netto_incassato()` (§6); esclusione-burn `RIMBORSO_CONTRATTO` (§7). +12 test (AC-7.3-1..9 + guardie).

**G7.3b — ritiro PUT chiuso + migrazione + frontend.** `chiuso` rimosso da `ContractUpdate` → chiusura solo via auto-close
o terminate (sempre con motivo). 16 test PUT chiuso=True migrati: 13 → terminate (canale canonico), 3 → ORM. Frontend:
`TerminateContractDialog` (preview + microcopy-proposta + metodo condizionale), i 2 bottoni Blocco-3 → un "Termina",
"Termina" anche nel dropdown `ContractsTable` per ogni non-chiuso (recesso anticipato di un ATTIVO = caso principale §5).

**Decisioni/divergenze dalla spec (code-grounded, da portare a Bridge per G7.4):**
- **`motivo_chiusura` DERIVATO dall'esito** (RIMBORSO→TERMINAZIONE_RIMBORSO, write-off→TERMINAZIONE_DECADENZA,
  conguaglio~0→CONSUNZIONE), NON passato dal trainer. Sciolto il conflitto §1 ("scelto dal trainer") vs §9/AC-7.3-9
  ("mappatura esito→motivo"): vince l'AC. Confermato dal founder (scelta esplicita). terminate non assegna MAI COMPLETAMENTO.
- **Le "due gambe" CONVIVONO**, non sono mutuamente esclusive come legge la prosa di §1: il modulo G7.1 ha
  `quota_da_stornare = residuo` SEMPRE + `importo_rimborso` solo se overpaid. Es. prezzo 1000/versato 500/2 sedute su 10 →
  rimborso 300 **e** storno 500 → netto=200=reso, residuo=0. È il comportamento (già testato) del modulo, non un cambio.
- **`sedute_erogate` = Event `Completato`** (servizio reso, IMPL_PLAN §4.2), NON `!= "Cancellato"` (che è `crediti_usati`
  dell'auto-close). Corretta la mia nota di ricognizione che le aveva confuse: il conguaglio valuta ciò che è reso, non
  ciò che è solo prenotato.
- **Raffinamento a §8 (migrazione test):** oltre al presidio-NULL, **2 mini-presidi** (`aging_report`, `forecast_phantom`)
  vanno a **ORM, non a terminate**: testano il *filtro-chiuso* (esclusione di un contratto chiuso che MANTIENE una rata
  viva), e il soft-delete di terminate rimuoverebbe la rata → l'esclusione passerebbe per la cancellazione, non per il
  filtro → presidio mascherato. Stessa lezione del presidio-NULL applicata al filtro-chiuso. Gli altri 13 → terminate
  (canale canonico) perché l'esclusione lì è lifecycle-based (chiuso→escluso), che terminate realizza esattamente.
- **Entry-point UI oltre i 2 bottoni Blocco-3:** aggiunto "Termina" al dropdown `ContractsTable` (ogni non-chiuso) — senza,
  il caso d'uso principale (recesso anticipato di un ATTIVO, §5) non avrebbe avuto un punto d'accesso (la SuspendedCard
  copre solo i SOSPESO).

**Lezione (livello-3).** La stessa euristica del presidio-NULL — "una migrazione meccanica può lasciare un test verde ma
morto" — si applica a OGNI test che verifica un *filtro su uno stato* mantenendo viva la condizione che il filtro deve
escludere: se il nuovo canale (qui terminate) *altera* quella condizione (soft-delete della rata), il test verde non
prova più ciò che presidiava. Discriminante operativo: il test ha bisogno che il dato (rata) **sopravviva** alla chiusura?
→ ORM. Gli basta lo stato chiuso? → canale canonico. Ho trovato 2 casi oltre al presidio noto cercando questo pattern.

**⏭️ Prossimo:** **G7.4** (reopen / unterminate espliciti) · **G7.5** (allineamento delle ~7 query-cassa residue al
predicato bidirezionale: movement-stats, 2 forecast, financial-trend, monthly_revenue, **coppia flow_hint+flow_filter**,
+ ratifica rinumerazione "8+8" con liste vecchie superseded) · **G7.6** (runbook 3 muti id 4/9/13) → **G1 cifratura**.
Lo snapshot `AUDIT_PRE_G7.3_RAGGIO_STORNO.md` resta vivo per G7.4/5/6 (archiviazione alla chiusura di G7, vedi checklist sopra).

---

### 2026-06-24 — G7.4: riapertura esplicita (inverso di terminate / auto-close)

Nessuna SPEC_G7.4 di Bridge (G7.4 = "Medio" risk, zero blocker esterni) → guidato da IMPL_PLAN §4.4 + i
pattern di G7.3, con ricognizione sul vivo e checkpoint sulle 2 decisioni reali (rhythm di G7.3). Decisioni
(founder via AskUserQuestion): **(1) un solo `/reopen` smart** (non lo split reopen/unterminate di §4.4) +
**(2) ripristino delle rate soft-eliminate**. Suite **604 passed / 0 xfailed**, check-all verde.

**`POST /contracts/{id}/reopen`** — un endpoint **state-driven**: inverte CIÒ CHE LO STATO mostra, qualunque
sia il `motivo_chiusura`. (a) se `totale_rimborsato>0` soft-elimina via ORM i `CashMovement` USCITA
`RIMBORSO_CONTRATTO` attivi (`delete_movement` blocca `id_contratto` → ORM, come `unpay_rate`) + `totale_rimborsato -=`;
(b) `quota_stornata=0` → `residuo()` ripristinato; (c) ripristina (`deleted_at=None`) le rate non-saldate
soft-eliminate (le SALDATE non erano state toccate, B-3); (d) `chiuso=False`+motivo/data cleared. UN commit,
audit + transizione `chiuso` (motivo `riapertura_esplicita`).

**Perché un endpoint solo, state-driven (vs lo split §4.4):** la chiusura CONSUNZIONE/DECADENZA ha storno ma
NON rimborso → uno split "light reopen / full unterminate" cadrebbe in mezzo; lo **stato** del contratto (non il
label `motivo`) dice cosa invertire. È anche il path che il runbook G7.6 usa sui 3 muti (motivo NULL, nessuno
storno → solo `chiuso=False`).

**È il path ESPLICITO della reopen-allowlist G7.2:** la G7.2 blocca solo l'**auto**-riapertura (credit/payment-driven)
delle chiusure non-COMPLETAMENTO; `reopen` è il path che la allowlist demanda esplicitamente — il trainer dichiara
di voler annullare la chiusura, quindi nessuna allowlist da rispettare.

**Modello (Strada B):** come `unpay_rate` decrementa `totale_versato` (il "cresce-solo" vale sul forward; l'inverso
esplicito è l'eccezione sanzionata), `reopen` decrementa `totale_rimborsato`/`quota_stornata`. `stato_pagamento` NON
si tocca (terminate non l'aveva cambiato → resta coerente col pre-terminazione). Invarianti dopo reopen: `totale_versato
== Σ ENTRATA` (intatta, non si toccano le ENTRATA) · `totale_rimborsato == Σ USCITA RIMBORSO attivi` (→0, il movimento
è soft-eliminato).

**Rate (decisione 2):** ripristino delle non-saldate soft-eliminate del contratto. Edge accettato: una rata eliminata
singolarmente PRIMA del terminate verrebbe ri-ripristinata (over-restore di 1, basso impatto; il contratto chiuso non
ammette altre delete-rata, quindi in pratica le soft-eliminate sono quelle del terminate).

**Test (`test_contract_reopen.py`, +6):** reopen di un auto-close COMPLETAMENTO (zero cassa) · **round-trip
RIMBORSO** (refund annullato + storno + rate ripristinate, stato attivo == pre-terminate, riconciliazione ledger) ·
DECADENZA storno-only · guardia non-chiuso 400 · bouncer 404 · **reopen→re-terminate** (un solo rimborso attivo, non
accumulato → nessuno stato-zombie). **Frontend:** `useReopenContract` + `ReopenContractDialog` (conferma con riepilogo
di cosa viene invertito: rimborso annullato/residuo ripristinato/rate ripristinate) + "Riapri" nel dropdown
`ContractsTable` per i chiusi (mutuamente esclusivo con "Termina").

**⏭️ Prossimo:** **G7.5** (allineamento ~7 query-cassa + coppia flow_hint/filter + ratifica "8+8" + D4/D2 da
IMPL_PLAN §5-bis/5-ter) · **G7.6** (runbook 3 muti) → **G1 cifratura**.

---

### 2026-06-24 — Igiene doc finanziari: rimozione stale-done dopo G7.0→G7.4 (audit 18 agenti)

Prima di aprire G7.5, audit multi-agente code-grounded (18 agenti, find→verifica adversariale per doc-unit →
cross-doc → sintesi) sui doc finanziari vivi: **zero falsi positivi**, ogni stale-done confermato aperto sul codice.
**~13 stale-done [high]** che descrivevano come "da fare" lavoro G7.0-G7.4 già in produzione. Corretti **9 file**
(commit `fca56a5`): `api/CLAUDE.md` (callout "In arrivo G7"→IMPLEMENTATA; SPEC_VOCABOLARIO "da implementare"→Giro 1
fatto; Integrity Engine #4 reopen-allowlist; router map + endpoint), `docs/INDEX.md` (righe IMPL_PLAN/AUDIT/closing →
G7.4 fatto, prossimo G7.5), `IMPL_PLAN` (RESUME POINT re-baseline a `1df3414`; §4 banner IMPLEMENTATO; **reopen NON via
`PUT chiuso=False` → `POST /reopen`** [claim attivamente fuorviante, dava 422, replicato in 3+ doc]; BLOCKER §4.7 residuo
chiuso; §7 OPZIONE R; diagramma §1), `FDM` (§3.1 colonne esistono; §6 bottoni cablati; §7 predicato cassa esiste; enum
motivo DECISO; §11 schema fatto; ref `SPEC_TERMINAZIONE`→`SPEC_G7.0/G7.3`), `SPEC_REVISIONE_PRE_G7`/`SPEC_VOCABOLARIO`/
`SPEC_G7.0 §8` (marker stato/superato), `AUDIT_PRE_G7.3` (banner: G7.3/G7.4 fatti, perimetro→SPEC_G7.3, vivo come
mappa-query G7.5/6), `TASSONOMIA §7.2` (avanzamento tracciato altrove). **Deferito di proposito:** "8 vs 9 query"→ratifica
G7.5; archiviazione spec→a chiusura G7; legittimamente-aperto invariato; log/ADR/snapshot-corpi non toccati (point-in-time).

**Lezione (governance).** Dopo un blocco grosso (G7.0-G7.4), lo stale-done si concentra negli **header/banner/framing
temporale** dei piani e degli hub d'ingresso (`api/CLAUDE.md`, `INDEX`), non nel corpo dei SSoT. Un audit code-grounded
prima del blocco successivo evita che il prossimo implementatore (o Bridge) parta da istruzioni superate — es. "reopen via
PUT chiuso=False" sarebbe stato seguito e avrebbe dato 422.

---

### 2026-06-25 — G7.5a: allineamento query-cassa al rimborso (contra-ricavo) + ratifica inventario

Primo storno reale (terminate, G7.3) ora esiste → le query-cassa che aggregano i movimenti possono produrre numeri
sbagliati con un `RIMBORSO_CONTRATTO`. Nessuna SPEC_G7.5 di Bridge (zero blocker esterni) → guidato da IMPL_PLAN §5 +
AUDIT_PRE_G7.3 Classe C (mappa viva). **Decisioni founder (AskUserQuestion):** scope = **solo le query che mentono**
(non le additive/display); struttura = **3 sub-commit**. Commit `4c918af`, suite **607 passed**.

**Modello:** `RIMBORSO_CONTRATTO` = USCITA **contra-ricavo** (specchio esatto di `STORNO_SPESA_FISSA`, contra-uscita).
Allineate le 3 query backend: **get_movement_stats** (single-treatment IMPL_PLAN §5: sottratto dalle entrate **E**
escluso dalle uscite variabili — mai entrambi, il margine resta identico ma la classificazione è corretta; chart
day-bucket come riduzione entrate + normalizzazione simmetrica per entrate negative); **get_forecast** ×2 (escluso da
`past_var_totals` burn-variabile e `past_total_uscite` burn-KPI, null-safe coalesce); **monthly_revenue** (sottrae i
RIMBORSO del mese → revenue netto). Tutte **byte-invarianti** finché non esiste un rimborso (suite pre-esistente verde).

**Ratifica inventario (governance, chiude il "8 vs 9"):** `TASSONOMIA §7.2` code-grounded — il "9" non era un inventario
verificato. Reale: **4 query cambiano** (movement-stats, forecast, monthly_revenue, financial-trend); le altre sono
**invarianti** (saldo, burn-già-fatto, reconciliation-àncora) o **display/audit a basso valore** (#7 flow-timeline:
per un `movement` legge il `tipo` reale, già corretto; #8 balance-uscite: cash-out grezzo corretto). Lasciate per scope con
motivo in tabella. +3 test (`test_g75_cash_alignment.py`).

---

### 2026-06-25 — G7.5b: financial-trend contra-line `rimborsi_contratti` (BLOCKER-4)

`get_financial_trend` vedeva **solo ENTRATA** → un rimborso era invisibile (sovrastima del netto contrattuale). Commit
`68c470e`, suite **608 passed**, check-all verde. Soluzione = **query SEPARATA e additiva** `buckets_rimborsi` (USCITA
`RIMBORSO_CONTRATTO` per mese): `cash_flow_reale` diventa **netto** (`incassi_contratti + altri_incassi − rimborsi`), ma
`incassi_contratti` e le **due decomposizioni** (nuovi/rinnovi, acconti/rate) restano **LORDE** (BLOCKER-4: "nessun numero
che sparisce" — il rimborso vive come **contra-linea separata**, non nettato dentro decomposizioni ambigue). Schema
`FinancialTrendPeriod`/`Response` += `rimborsi_contratti`/`tot_rimborsi_contratti`; `types/api.ts`; `AndamentoTab`
contra-linea rossa tratteggiata **condizionale** (solo se `tot_rimborsi>0` → niente linea piatta a zero) + caption.
Byte-invariante senza rimborsi (additivo, default 0). +1 test (incassi LORDI invariati, cash_flow netto, decomposizioni
lorde, totali).

**⏸️ STOP (richiesto da Giacomo):** analisi congiunta col Bridge del lavoro G7.5a/b prima di G7.5c (D4 guardia
`data_chiusura` non-futura + D2 campo derivato `sedute_prenotate`).

---

### 2026-06-25 — G7.5c: guardia `data_chiusura` non-futura (D4) + `sedute_prenotate` in preview (D2)

Chiude lo STOP precedente. Commit `27bef81`, suite **611 passed**, check-all verde. Due raffinamenti da IMPL_PLAN
§5-bis/5-ter, entrambi **additivi** (nessun importo cambia, byte-invarianti sul percorso conguaglio).

**D4 (§5-bis):** `field_validator` su `ContractTerminate.data_chiusura` (`financial.py`) — una data nel **futuro** →
**422 al boundary, zero scritture**. Razionale: una terminazione (e l'eventuale rimborso) registra cassa uscita
**ORA o in passato**, mai un impegno futuro; una data futura è errore d'inserimento, non uno stato valido. Test:
422 + controprova `oggi`→200, atomicità (`chiuso` resta False).

**D2 (§5-ter):** `settlement-preview` espone `sedute_prenotate` (Event PT `Programmato`, non eliminati) via
`_count_sedute_prenotate` — **query SEPARATA dal path del conguaglio** (decisione di Giacomo via Bridge: strada
additiva sicura, NON tocca `_settlement_for`/`_count_sedute_erogate`). `compute_settlement` invariato: il conguaglio
resta su base sedute **Completate**. Solo display: microcopy FE "le prenotate non riducono il rimborso" condizionale a
`>0`. Test: `valore_servizio_reso` invariato a 200 con 2 erogate + 3 prenotate, 0 se nessun Programmato.

**⏭️ Prossimo:** **G7.6** (runbook 3 muti id 4/9/13) → **G1 cifratura**.

---

### 2026-06-25 — Decisione APERTA: Fatturato lordo (venduto) vs ricavo netto (KPI fiscale)

Emersa da un **test manuale di terminazione** (DB dev): contratto 10 crediti / €550 / acconto €100 / rate non
pianificate, terminato con 0 sedute → rimborso €100 + storno €450 → **il KPI "Fatturato" resta 550**. Verificato a
terra che è **corretto per disegno**: `kpi_fatturato = Σ prezzo_totale` includendo i chiusi (`contracts.py:248`) è il
**venduto/contrattualizzato**, metrica cumulativa storica (pitfall #14, INC-2026-06-08). La realtà economica della
terminazione **è già riflessa negli altri due assi**: `kpi_incassato`→`netto_incassato()` (100→0, rimborso) e
`kpi_residuo` (450→0, storno). Chiarito anche che **i €450 NON sono un movimento di cassa** (terminate scrive solo
l'USCITA €100 `RIMBORSO_CONTRATTO`, `contracts.py:1252`): sono write-off di credito mai incassato (`quota_stornata`),
mostrato come "Residuo azzerato" nel dialog (`TerminateContractDialog.tsx:129`), **non** nel libro cassa.

**Punto aperto (tributarista + founder):** se per il contratto è stata emessa una **fattura**, fiscalmente una
terminazione anticipata → **nota di credito** e il fatturato fiscale scenderebbe; ma il KPI di FitManager è
**commerciale**, non un registro fatture. Decisione tracciata in **IMPL_PLAN §11** (write-up + guardia anti-regressione:
un eventuale "ricavo netto" è un KPI **additivo**, MAI una mutazione di `kpi_fatturato`) e in **§10 punto 5** (lista
domande al tributarista). **Non blocca nulla** in corso (differito post-G1).

---

### 2026-06-25 — G7.6: runbook remediation contratti muti (chiude la catena G7) + correzione data-driven

Ultimo anello di G7. **Deliverable = solo documento** (`docs/operations/RUNBOOK_REMEDIATION_CONTRATTI_MUTI.md`): gli
endpoint che usa (reopen G7.4, terminate G7.3) erano già in produzione e testati. Nessun codice nuovo.

**Scoperta che ha riscritto il piano (verifica sul DB dev, READ-ONLY).** Il piano §7 descriveva "3 muti id 4/9/13"
col profilo `crediti_usati=0` + scadenza futura + saldati (relazione viva → reopen). Sul crm.db dev attuale i muti
(`chiuso=1 AND motivo_chiusura IS NULL AND deleted_at IS NULL`) sono **19**, con profilo **opposto e eterogeneo**:
**16** hanno `crediti_usati == crediti_totali` + scadenza passata + saldati = **completamenti impliciti** (chiusi a
ragione, manca solo l'etichetta `motivo`; la reopen-allowlist G7.2 li tratta già bene → **LEAVE**, zero azione), più
inconsistenze sparse (contratto #29 rata non-saldata su chiuso; #4/#9/#13/#26/#28 sedute `Programmato` su chiuso).
→ I muti **NON sono una popolazione uniforme** e **gli ID dipendono dal DB**. Il runbook è quindi un **albero
decisionale per PROFILO** (LEAVE / R-reopen / T-terminate-via-reopen→terminate), **data-driven** (query diagnostica,
mai per-ID), **per-contratto, mai bulk, reversibile, backup-first, solo via endpoint, decisione col trainer**.

**Note tecniche del runbook:** T su un muto = 2 passi (reopen → terminate, `data_chiusura` retroattiva ma mai futura
per D4); se `terminate` propone un RIMBORSO ma nessun rimborso reale è mai avvenuto → segnale che il caso è R, non T.
Snapshot PRE/POST via `/api/dashboard/reconciliation` + `/api/movements/stats` + dump contratto + `audit_log`.

**Esecuzione NON fatta in autonomia:** la bonifica vera gira sui DB reali (Chiara/Alessio) insieme al trainer, che
decide R/T per contratto. Sul DB dev i muti sono in larga parte completamenti legittimi → nessun bulk-cleanup.

Doc allineati: IMPL_PLAN §7 (banner consegnato + correzione data-driven) + RESUME POINT/§1/§10/file-list, INDEX
(operations + riga RESUME), api/CLAUDE.md (callout G7.5/G7.6 fatti). **Con G7.6 la catena G7 è chiusa →
⏭️ G1 (cifratura crm.db).**

---

### 2026-06-26 — Audit crediti/rimborso → G7.7 remediation + 2ª segnalazione Chiara → ADR-017 (il rinvio libera il credito)

Step **docs-only / governance** (zero codice). Apre due filoni innescati dal trainer reale (Chiara) prima di G1.

**Trigger 1 — audit senior crediti/contratti/rimborso** (`docs/operations/AUDIT_CREDITI_RIMBORSO_2026-06-26.md`,
multi-agente L0-L5, 34 finding confermati su 54, grounding su `crm.db` reale 35 contratti). Esito: la logica di
rimborso è **strutturalmente sana** (asse EROGATO canonico); la 1ª segnalazione di Chiara ("residui 4 ma rimborso su 2
sedute") = **gap di trasparenza, non di matematica** (le prenotate non riducono il rimborso, by-design). **Un solo
money-bug (H1): `unpay_rate` privo di guardia su contratto terminato** (`rates.py:656` decrementa `totale_versato`
incondizionato; l'allowlist `:670-674` tiene `chiuso` ma non blocca il decremento) → `totale_rimborsato > totale_versato`,
il clamp di `netto_incassato()` **maschera** l'over-rimborso. Resto = debito-SSoT (M1 `reopen` over-restore, M2
`update_rate` senza guard `chiuso`, M3 `ContrattiTab` off-SSoT) + trasparenza (M4/L1) + igiene (L2/L3).

**Piano G7.7 (R0-R6) + decisioni founder (AskUserQuestion):** remediation **completa**; `unpay` su terminato →
**reject 409** (riapri prima, non reroute); `reopen` esatto via **marker `rate.chiusa_da_terminazione`**; M4 =
**indicatore leggero** (nessun nuovo sotto-stato enum). **ADR-016** scritto: asse EROGATO canonico + forfeiture
prenotate + riconciliazione I6 obbligatoria + grep-guard "euro-da-crediti".

**Trigger 2 — 2ª segnalazione Chiara, più profonda** (spec `SPEC_RINVIO_LIBERA_CREDITO` prodotta dal founder in
Claude Chat): *"i crediti delle sedute RINVIATE vengono scalati come se fossero state svolte"*. **L'audit l'aveva
mancata** — ha preso l'occupazione esistente (`!= Cancellato`, incl. `Rinviato`) come corretta-per-disegno, scrutinando
solo l'asse denaro. Tesi T1: `Rinviato` = slot **liberato**, non occupa il credito (occupazione = `Programmato +
Completato`); **nessun euro cambia**.

**Bridge code-grounded (ground truth = codice), HEAD `324be75`:**
- **Bug confermato:** `contracts.py:149` somma `programmate + completate + rinviate`; lo schema servito
  (`financial.py:404`) documenta `# crediti_totali - programmate - completate` (senza rinviate) → `crediti_residui`
  **sottostimato**. Il codice contraddice il proprio contratto.
- **Asse denaro invariante per costruzione:** `compute_settlement` legge solo `sedute_erogate` (`== Completato`) e
  `residuo()` (prezzo/versato); **mai** `!= Cancellato` → oracolo settlement byte-identico (spec §5/§6 verificati).
- **Inventario §3 INCOMPLETO** — la spec era esaustiva *solo sui file in contesto* (`clients/agenda/contracts/dashboard`,
  classificati **correttamente al 100%**). **5 produttori di `crediti_usati` mancati**, integrati in §3.1: 🔴
  `rates.py:565` (auto-close di `pay_rate`, **gemello payment-driven** di `_sync_contract_chiuso` — lo documenta il
  commento `agenda.py:307`; senza, un saldato all-rinviate si auto-chiude COMPLETAMENTO al pagamento ultima rata →
  **D-AUTO-CLOSE violata**), `workspace_engine.py:1247/1389/2145` (worklist cockpit), `client_avatar.py:430`. Più
  `_check_overlap` (`agenda.py:198`), §3-bis **risolto = CAMBIA** (D-GUARD). **Stessa firma della scoperta dei due rami
  di G7.2** (riapertura credit-driven + payment-driven): anche l'auto-chiusura ha due rami, la spec ne vedeva uno.

**Governance prodotta (questo commit):** `ADR-016` **emendato** in 3 punti (Context, Decisione §1, Superseded-by → la
definizione di occupazione è "precisata da ADR-017"; asse EROGATO e barriera strutturale invariati); **`ADR-017`
accepted** (emenda ADR-016 §1; decisioni founder D-AUTO-CLOSE / D-MODELLO / D-GUARD + overlap CAMBIA); spec installata
in `docs/technical/SPEC_RINVIO_LIBERA_CREDITO.md` col fold-back `[Bridge Code 2026-06-26]` (5 siti mancati, §3.3
verificata + allowlist, §3-bis risolto, oracolo). `INDEX` + `adr/README` allineati (15 ADR attivi). **FDM NON toccato**
(la definizione occupazione si aggiorna a implementazione di G7.8, spec §10) — l'edit prematuro al FDM era stato
correttamente rifiutato dal founder.

**Lezione (governance/bridge).** Un audit multi-agente code-grounded verifica la **coerenza interna** del codice ma
può prendere per buona una **semantica di dominio sbagliata** (qui: `Rinviato` in occupazione). La correttezza esterna
la dà il dominio (il trainer reale). Il bridge code-grounded è il punto in cui le due si incontrano: ha confermato la
matematica del denaro **e** scoperto che l'inventario manuale della spec mancava i 5 produttori fuori-contesto — il
fallimento ricorrente *enumerazione ≠ enforcement*, già visto in §4.7 e in G7.2.

**⏭️ Sequenza (decisione founder):** **H1 (G7.7-R1, money-bug) → G7.8 (T1 rinvio) → resto G7.7** (M1 marker / M2 /
trasparenza R4-R5 / igiene R6) → **G1 cifratura**. Differiti post-G1 invariati (G7.x-override, Fatturato-lordo-vs-netto,
Giro 2 vocabolario). Zero codice prodotto in questo step.

---

### 2026-06-26 — G7.7-R1 / H1: guardia `unpay_rate` su contratto terminato (unico money-bug dell'audit)

Primo **codice** del blocco G7.7. Chiude l'unico difetto che muove denaro in modo errato (audit §HIGH).
`unpay_rate` non aveva guardia su un contratto terminato: le rate SALDATE sopravvivono al `terminate`
(soft-elimina solo le non-saldate, B-3) → il bouncer ne trova una e, senza guardia, `unpay` decrementava
`totale_versato` (`rates.py:656`) facendolo scendere sotto `totale_rimborsato`; il clamp di
`netto_incassato()=max(versato−rimborsato,0)` **mascherava** un over-rimborso reale (mastro
ΣRIMBORSO > ΣENTRATA, cassa già uscita).

**Fix (`rates.py`, guard B-bis prima di ogni mutazione):** revoca rifiutata **409** se il contratto è
`chiuso` E `quota_stornata>0 OR totale_rimborsato>0 OR motivo_chiusura.startswith("TERMINAZIONE_")`.
Predicato = la *condizione di corruzione* (lo stato di conguaglio), **non** il flag `chiuso`: un blanket
`if chiuso` regredirebbe l'auto-reopen legittimo da COMPLETAMENTO (quota/rimborso a 0). Policy founder =
**reject, non reroute** (un solo inverso esplicito): path canonico `POST /reopen` (riallinea
atomicamente rimborso+storno), poi la revoca.

**Test:** migrato `test_terminazione_non_si_riapre_da_unpay` (era 200 + allowlist → ora **409**, presidio
più forte: sul ramo unpay l'allowlist diventa difesa-in-profondità) + nuovo E2E
`test_unpay_dopo_terminate_rifiutato_409` (terminate REALE, rimborso 800 → unpay SALDATA = 409 → tetto
`rimborsato≤versato` retto → **reopen → unpay torna 200**). Il guard NON tocca l'auto-reopen da
COMPLETAMENTO (`test_unpay_reopens_closed_contract` resta 200) né il ramo agenda (`_sync`: ricalcola
crediti, non decrementa versato → nessun money-bug). Suite **612 passed** (+1), ruff verde sui file
toccati. Gotcha: il PostToolUse ruff `--fix` ha strippato `from api.models.rate import Rate` aggiunto
prima del suo uso → ri-aggiunto dopo l'uso ([[feedback_formatter_strips_imports]]).

**⏭️ Prossimo:** G7.8 (T1 rinvio libera credito) → resto G7.7 (M1 marker / M2 / trasparenza / igiene) → G1.

---

### 2026-06-26 — G7.8 / ADR-017: il rinvio libera il credito (T1)

Seconda segnalazione di Chiara ("rinviate scalate come svolte") chiusa. **`Rinviato` non occupa il
credito**: occupazione-credito = `Programmato + Completato`. Cambio funzionale isolato, **asse denaro
invariante per costruzione** (`compute_settlement` non legge mai `!= Cancellato` → oracolo settlement
byte-identico, AC-1).

**Core:** `contracts.py:149` → `crediti_usati_computed = programmate + completate` (rimossa `+ rinviate`;
`rinviate` resta solo display via `sedute_rinviate`). **17 predicati credito** `!= "Cancellato"` →
`.in_(["Programmato", "Completato"])` (e `IN ('Programmato', 'Completato')` per le 5 raw SQL): §3.1 (11
siti verificati) + **i 5 produttori trovati dal bridge** (`rates.py:565` auto-close `pay_rate` →
**D-AUTO-CLOSE sul ramo pagamento**; `workspace_engine.py:1247/1389/2145` worklist cockpit;
`client_avatar.py:430`) + overlap `agenda.py:198` (§3-bis, D-GUARD). **`contracts.py:490` (breakdown
GROUP BY) LASCIATO** di proposito (tiene il conteggio `Rinviato` per il display `sedute_rinviate`, §3.2).
I ~21 `!= Cancellato` rimasti = siti LEAVE (recency/calendario/dossier), verificati uno a uno via grep.

**Test (`test_rinvio_libera_credito.py`, +8):** AC-2 conteggio escluso (dettaglio + lista contratti +
lista clienti = sito di Chiara), AC-3 D-AUTO-CLOSE su **entrambi** i rami (pay_rate non chiude su
rinviate; agenda `_sync` riapre al rinvio), AC-4 D-GUARD (riprenotabile dopo rinvio), AC-5 overlap (slot
liberato, no 409), AC-1 oracolo (conguaglio invariante con rinviate presenti). Suite **620 passed** (+8),
ruff verde sui 7 file.

**Doc (spec §10):** FDM §3 definizione occupazione-credito aggiornata (`Programmato + Completato`,
`Rinviato` libera); `api/CLAUDE.md` (callout G7.7/G7.8 + monito anti-regressione sul Credit guard #8: mai
riusare `!= 'Cancellato'` sui siti credito); spec già installata col fold-back bridge (governance `72eaa9b`).

**Lezione / firma del bridge.** La spec v1 era esaustiva solo sui file in contesto; il bridge ha trovato
5 produttori `crediti_usati` fuori-contesto — capofila `rates.py:565`, **gemello payment-driven**
dell'auto-close di `agenda._sync` (la spec vedeva solo il ramo credit-driven). Senza, D-AUTO-CLOSE si
sarebbe rotta sul pagamento dell'ultima rata. *Enumerazione manuale ≠ enforcement* — stesso pattern dei
due rami di G7.2.

**Deferito a R6 (igiene):** grep-guard anti-ritorno `!= 'Cancellato'` sui siti credito (allowlist
calendario) + centralizzazione del predicato in costante condivisa (spec §12, refactoring puro separato).
**Accertamento §7** (contratti già auto-chiusi COMPLETAMENTO *per rinviate* → SOSPESO post-fix): read-only,
decisione umana caso per caso sui DB reali, coordinato col runbook G7.6 — NON in autonomia (popolazione
distinta dai muti M4).

**⏭️ Prossimo:** resto G7.7 — M1 (`reopen` inverso esatto via marker `rate.chiusa_da_terminazione`) · M2
(`update_rate` guard `chiuso` + cap su asse residuo) · M3/M4/L1 (trasparenza display↔erogato) · igiene +
grep-guard → **G1 cifratura**.

---

### 2026-06-26 — G7.8 follow-up (review founder/bridge): AC-3 4° quadrante + accertamento §7 + decisione aperta Completato→Rinviato

Post-chiusura G7.8, review del founder (bridge method): 3 buchi di rete + 1 accertamento dati. G7.8 è
verde e corretto in produzione — questi sono copertura test + una decisione di dominio non presa.

**#1 (test, FATTO).** Aggiunto `test_ac3_autoclose_agenda_sync_non_chiude_su_rinvio` — il 4° quadrante
della matrice AC-3 (pay_rate-non-chiude ✓ · _sync-riapre ✓ · **_sync-non-chiude-all'arrivo** ← era solo
sfiorato dal test di riapertura). Isola la transizione full-of-rinviate→resta-aperto sul ramo edit-evento
+ asserisce `motivo_chiusura is None` (clear-on-reopen, AC-7.2-5). File a **9 test**. Commit test-only.

**#4 (accertamento §7, READ-ONLY, FATTO).** Query §7 sul `data/crm.db` reale → **0 contratti a rischio**
di riapertura-a-sorpresa col deploy G7.8. `motivo_chiusura='COMPLETAMENTO'` totali = **0** (la marcatura
esiste solo da G7.0; nessun auto-close da allora); i **19 muti** sono tutti `motivo NULL` e **non si
auto-riaprono** (reopen-allowlist G7.2 scatta SOLO su COMPLETAMENTO). Nessun contratto "torna vivo senza
aver fatto nulla". *Caveat:* è il crm.db locale; se la macchina di Chiara ha auto-close post-G7.0,
ri-girare la query lì prima del deploy. Popolazione distinta dai muti M4.

**#2 (DECISIONE DI DOMINIO APERTA — Completato→Rinviato).** Grounded sul codice: `update_event`
(`agenda.py:584-597`) applica `stato` **senza guardia di transizione** + chiama `_sync` se PT-con-contratto.
Una Completata→Rinviata libera **sia il credito** (`crediti_usati` scende, post-G7.8 la Rinviata non
conta) **sia il valore** (`_count_sedute_erogate == "Completato"`, `contracts.py:1114` → `valore_servizio_reso`
cala). È l'**unica** transizione G7.8 dove l'asse denaro NON è invariante. Due opzioni (decide il
dominio/Chiara, NON implementato): **(a)** permettere (comportamento attuale) + test documentativo che il
valore cala; **(b)** bloccare in `update_event` con 422 ("non puoi rinviare una seduta già svolta — semmai
cancellala o riportala a Programmato"). **Raccomandazione = (b)**: preserva la tesi G7.8 come invariante
*pulita* (l'unica transizione money-moving viene vietata), è domain-coerente (il "rinvio" pospone una
seduta **non** ancora svolta), deterministico (rule #6); l'`update_event` è documentato "scheduling only",
denaro che ci passa è una sorpresa. Scope del guard: SOLO Completato→Rinviato (Completato→Programmato e
→Cancellato restano correzioni legittime di un "done" sbagliato). Commit a sé una volta presa la decisione.

**#3 (requisito R6, ANNOTATO nel task).** Il grep-guard di R6 è **bidirezionale**: (a) vietato
reintrodurre `!= 'Cancellato'` sui siti credito §3.1; (b) vietato "armonizzare" il `!= 'Cancellato'` dei
siti DISPLAY (breakdown `contracts.py:490` + ogni sito che conta Rinviato per mostrarlo) sostituendolo con
`IN (...)` — manderebbe `sedute_rinviate` a zero in silenzio. Allowlist esplicita dei display con il
**perché** annotato (non solo *che* sono esenti, altrimenti il prossimo li "pulisce"). `test_ac2_dettaglio…`
copre il solo `:490`; il guard presidia la direzione inversa in generale.

**⏭️ Prossimo:** decisione #2 dal founder → poi resto G7.7 (M1/M2/trasparenza/igiene) → G1. Lato §7 il
deploy di G7.8 è sbloccato (0 a rischio sul DB verificato).

---

### 2026-06-26 — G7.8 #2 DECISA (founder, deferito a Chiara): blocca Completato→Rinviato (422)

Decisione sul punto #2 aperto: **opzione (b) bloccare**. Una seduta già `Completato` non si rinvia. Guard
in `update_event` (`agenda.py`, "Bouncer 4"): se `update_data.stato == "Rinviato"` **e** `event.stato ==
"Completato"` → **422** "Non puoi rinviare una seduta già svolta: riportala a Programmato o annullala."
Scope **SOLO** Completato→Rinviato: le altre uscite da Completato (→Programmato per riprogrammare,
→Cancellato per non-avvenuta) **restano permesse** — correzioni legittime di un "done" errato, dove il
valore DEVE seguire la realtà. Così la tesi di G7.8 ("il rinvio non muove denaro") torna un invariante
*pulito*: l'unica transizione money-moving è vietata a monte, l'`update_event` ("scheduling only") non
muove più denaro di nascosto. +1 test (`test_completato_non_si_rinvia_422`: 422 + stato invariato +
controprova Programmato/Cancellato = 200). Suite **622 passed**, ruff verde. Commit a sé.

**⏭️ Prossimo:** resto G7.7 — M1 (reopen marker `chiusa_da_terminazione`) · M2 (update_rate guard+cap) ·
M3/M4/L1 (trasparenza) · R6 igiene (incl. grep-guard bidirezionale) → **G1 cifratura**.

---

### 2026-06-26 — G7.7-M1: `reopen` inverso esatto via marker `rate.chiusa_da_terminazione`

Audit M1 (DEBITO_SSOT). `reopen` (G7.4) ripristinava OGNI rata non-saldata con `deleted_at != None` →
resuscitava anche rate cancellate manualmente o da un piano rigenerato PRIMA del terminate (sul crm.db
reale il contratto 20 ha 30 rate pre-eliminate). Rate-fantasma in forecast "entrate certe" / worklist /
`is_insolvente`. **Fix con marker:** `terminate` MARCA (`chiusa_da_terminazione=True`) solo le rate che
soft-elimina; `reopen` ripristina **SOLO** le marcate e azzera il marker (inverso esatto). Le cancellate
per altre ragioni (marker False) non si toccano.

**Schema (M1 = unico schema-touch di G7.7):** colonna `chiusa_da_terminazione bool NOT NULL default False`
su `rate_programmate` (PLAIN, no FK). Migrazione Alembic `c7e1a2b3d4f5` (down=`d83abb993ea8`, pattern
identico a G7.0). `Rate` model + `terminate` (mark) + `reopen` (filtro `== True` + clear del marker).

**Verifica backup-first (come G7.0) su `auto_20260620_082707.sqlite` reale (111 rate, 39 contratti):**
`sync_schema` aggiunge `chiusa_da_terminazione (INTEGER DEFAULT 0)`, **111 rate preservate, tutte
backfillate a 0, FK_check CLEAN, integrity ok, idempotente** (re-run = no-op).

**Learning (meccanismo schema, livello-3).** `alembic upgrade head` su un backup/crm.db reale **fallisce**
(e3q8: tenta di ricreare tabelle già esistenti): l'`alembic_version` di TUTTI i DB — backup **e** crm.db
dev — è **frozen a `27b8b9852489`** mentre lo schema è corrente. L'evoluzione schema su questo progetto
passa **sempre da `schema_sync`** (column-sync generico al boot) + `create_db_and_tables` (DB fresh),
**mai da `alembic upgrade` sui DB esistenti**. Alembic è il **record formale** (paper-trail), non il path
di deploy → la verifica backup-first va fatta con `sync_schema`, non con `alembic upgrade`. **Tech-debt
collaterale segnalato (non di M1):** le migrazioni si accumulano ma non sono mai replayed e
`alembic_version` è fuorviante; andrebbe o ri-sincronizzato (stamp) o dismesso a favore di schema_sync.

**Test:** `test_reopen_non_resuscita_rate_pre_eliminate` (rata cancellata a mano + rata del terminate →
reopen ripristina solo la seconda; marker consumato). Suite **623 passed**, ruff verde.

**⏭️ Prossimo:** M2 (`update_rate` guard `chiuso` + cap su asse residuo) → trasparenza (M3/M4/L1) → R6 → G1.

---

### 2026-06-26 — G7.7-M2: guard `chiuso` su `update_rate` + cap su asse residuo

Audit M2 (DEBITO_SSOT). Due fix in `rates.py`:
- **Guard `chiuso` su `update_rate`** (era assente, a differenza di `create_rate:307`): una rata SALDATA
  superstite di un contratto terminato poteva tornare PARZIALE alzando `importo_previsto` →
  residuo-fantasma a livello rata. Ora `if contract.chiuso → 400` ("Impossibile modificare rate di un
  contratto chiuso"). Path canonico: riapri prima (`POST /reopen`).
- **`_cap_rateizzabile` sottrae `quota_stornata`**: il cap rateizzabile usa ora lo STESSO asse di
  `contract_state.residuo()` (lo storno non è rateizzabile). Inerte sui non-terminati (`quota_stornata==0`):
  entrambi i caller (`create_rate`/`update_rate`) bloccano `chiuso`, quindi il cap con `quota_stornata>0` è
  di fatto irraggiungibile via endpoint → difesa-in-profondità + SSoT unica del residuo (allineato per
  costruzione, non per disciplina).

**Test:** `test_m2_update_rate_su_terminato_400` (SALDATA superstite → PUT 400, rata invariata; dopo reopen
la modifica torna possibile = guard chiuso-specifico, non blanket). Suite **624 passed**, ruff verde.

**⏭️ Prossimo:** trasparenza — R4 backend (`sedute_completate` su `ContractListResponse` + M4 indicatore
COMPLETAMENTO-prenotato) · R5 frontend (display↔erogato + M3 `ContrattiTab` badge SSoT) → R6 igiene
(L2/L3 + grep-guard bidirezionale) → **G1 cifratura**.

---

### 2026-06-26 — G7.7-R6: igiene (L2 vocabolario + L3 test gap + grep-guard ADR-016/017)

Scelta founder: R6 prima della trasparenza UI, per chiudere la **spina dorsale backend** di G7.7 prima
della UI. Tre filoni, low-risk:

**L2 — vocabolario CONSUNZIONE.** Il commento dell'enum `MotivoChiusura.CONSUNZIONE`
(`contract_settlement.py:25`) era "(riservato) residuo post-scadenza", ma il codice (`_motivo_from_esito`
+ `financial.py:207`) lo usa per le terminazioni a conguaglio ~0 (esito NULLO). Aggiornato il commento al
doppio uso reale (no nuovo enum value, no behavior change; `TERMINAZIONE_PARI` resta opzione futura se si
vuole separare i due significati).

**L3 — gap di copertura (3 test, +10 casi).** (a) **property del tetto** `importo_rimborso <=
totale_versato` su griglia 8 casi (incl. overpayment, crediti=0): un refactor della formula del conguaglio
che violasse I3 passerebbe muto. (b) **prenotate-non-riducono sul WRITE-path** (`POST /terminate`, non
solo la preview GET già coperta): 2 Completato + 3 Programmato → rimborso su 2 + USCITA su 2. (c) **seam
auto-close → reopen → preview**: COMPLETAMENTO su prenotate (erogato=0) → reopen → settlement-preview =
rimborso pieno. (Il 4° gap dell'audit — unpay-post-terminate — era già chiuso in H1.)

**grep-guard (`tools/scripts/check-all.sh`, ADR-016/ADR-017).** Due guardie robuste (verificate: passano
sul codice corretto, falliscono sulle violazioni simulate): (1) **euro-da-crediti** —
`contract_settlement.py` non deve riferire l'occupazione (`crediti_residui|crediti_usati|sedute_rinviate|
sedute_prenotate`) → la barriera strutturale di ADR-016 resa enforceable. (2) **bidirezionale
display-exempt** (review G7.8 #3) — il `credit_breakdown` (GROUP BY stato, `contracts.py`) DEVE restare
`!= "Cancellato"` per contare i Rinviato e alimentare `sedute_rinviate`: NON armonizzarlo a `IN(...)`
(manderebbe sedute_rinviate a zero in silenzio). Marker `[G7.8 DISPLAY-EXEMPT]` esplicito al sito. La
direzione opposta (Rinviato fuori dall'occupazione-credito) è già presidiata dai test AC-2/AC-3. **NB:** il
guard vive in `check-all.sh` (gate documentato, obbligatorio pre-commit), non nel git pre-commit hook
(ruff+next build) — integrarlo anche lì è follow-up opzionale.

Suite **634 passed**, ruff verde. **Con R6 la spina dorsale backend di G7.7 è chiusa (H1 · M1 · M2 · R6).**

**⏭️ Prossimo:** trasparenza UI — R4 backend (`sedute_completate` su `ContractListResponse` + M4 indicatore
COMPLETAMENTO-prenotato) · R5 frontend (display↔erogato + M3 `ContrattiTab` badge SSoT, verifica
Playwright) → **G1 cifratura**.

---

### 2026-06-26 — G7.7-R4: trasparenza backend (L1 erogato in lista + M4 indicatore COMPLETAMENTO-prenotato)

Prima metà della trasparenza (la parte che risponde alla 1ª segnalazione di Chiara: "residui 4 ma rimborso
su 2"). R4 = backend + contratto-tipi; R5 = la UI che li mostra.

**L1 — erogato in lista.** `ContractListResponse` ora espone `sedute_completate` (erogato puro), via una
batch-query dedicata (`COUNT Completato` per contratto, anti-N+1). Il dettaglio già lo aveva (G7.8). Così
lista/scheda/profilo potranno affiancare "erogate" ai "residui" senza ricalcolo client-side.

**M4 — indicatore COMPLETAMENTO-prenotato.** Nuovo derivato SSoT
`contract_state.sedute_non_erogate_alla_chiusura(contract, sedute_completate)`: per un contratto chiuso
`COMPLETAMENTO` con erogato < monte-sedute, il numero di sedute prenotate-ma-non-erogate alla chiusura
(segnala un rimborso recuperabile via Riapri→Termina — l'auto-close conta l'OCCUPAZIONE, quindi un
COMPLETAMENTO può chiudersi su sole PRENOTATE). 0 negli altri casi. Esposto su lista + dettaglio; tipi TS
allineati (`ContractListItem`/`ContractWithRates`).

**Test:** `test_r4_lista_e_dettaglio_espongono_erogato` + `test_r4_m4_indicatore_completamento_prenotato`
(+2). Suite verde, ruff verde, next build verde.

**⏭️ Prossimo:** R5 frontend — affiancare "erogate" a "residui" (lista/scheda/profilo) + indicatore M4 +
M3 (`ContrattiTab` → badge SSoT `ContractLifecycleBadge`/`ContractMoneyBadge`), con verifica Playwright.

---

### 2026-06-26 — G7.7-R5: trasparenza frontend (L1 erogato + M3 badge SSoT + M4 indicatore)

Seconda metà della trasparenza — la UI che mostra il dato esposto da R4. Chiude la radice della 1ª
segnalazione di Chiara: lista/scheda/profilo affiancano ora l'erogato all'occupazione.

**M3 — `ContrattiTab` ai badge SSoT.** Eliminata la cascata off-SSoT (`chiuso? : ha_rate_scadute? :
Attivo`) che collassava Sospeso/Esaurito in "Attivo" verde (divergeva da `/contratti`). Ora la colonna
Stato rende `ContractLifecycleBadge` (vita) + `ContractMoneyBadge` (denaro) da `lib/contract-status` +
segnale "Rate scadute" (icona `AlertTriangle`, solo `!chiuso`). Un SOSPESO ora mostra "Sospeso" anche nel
profilo. (Rimosso l'import `Badge` non più usato.)

**L1 — erogato accanto all'occupazione.** Lista (`ContractsTable`) + profilo (`ContrattiTab`): sotto
`crediti_usati/totali` ora compare "N svolte" (`sedute_completate`, erogato). Dettaglio
(`ContractFinancialHero`): già mostrava Completate; aggiunta la microcopy di riconciliazione "il rimborso
da recesso si calcola sulle sole Completate; le prenotate non riducono il rimborso" (solo se non tutto
erogato).

**M4 — indicatore COMPLETAMENTO-prenotato.** Dove `sedute_non_erogate_chiusura > 0`: lista/profilo
mostrano "N prenotate non svolte" (amber); il dettaglio un banner amber "N sedute prenotate non erogate
alla chiusura — per rimborsare: Riapri → Termina".

**Verifica:** `next build` verde (TS pulito su tutte e 3 le superfici); dato corretto = R4 (test backend).
**⚠️ Playwright live NON eseguito:** l'ambiente dev del founder è già in esecuzione (lock `.next/dev/lock`
→ il mio `next dev` non parte; il backend in background ha fallito sul path relativo). Le edit sono
display-only e hot-reloadano nell'istanza dev del founder (eyeball diretto possibile, previo backend su
R4). **Verifica Playwright a schermo (light+dark) DA RIFARE quando l'ambiente è libero** — unico residuo
di G7.7.

**🏁 Con R5 la trasparenza è completa → la remediation dell'audit (H1·M1·M2·R6·R4·R5) + G7.8 è CHIUSA.
⏭️ Prossimo: G1 cifratura crm.db** (con, in coda, la verifica Playwright di R5).

---

### 2026-06-27 — G7.7-R5 follow-up frontend: scheda azionabile + summary mobile + guardrail scadenza

Chiusura del follow-up frontend emerso dall'audit di dettaglio del 2026-06-27. Obiettivo: rendere il
dettaglio contratto davvero azionabile dove il banner M4 spiegava il caso, preservare la trasparenza R5
sotto `lg`, e togliere l'ambiguità UX sulla retrodatazione della scadenza senza toccare il modello.

**Implementato.**
- **Scheda dettaglio azionabile:** `/contratti/[id]` ora espone `Termina` / `Riapri` / `Incassa residuo`
  nell'header, riusando i dialog canonici G7.3/G7.4/G6. Nessun nuovo endpoint, nessuna logica di dominio
  duplicata. La guardia dell'incasso diretto è stata estratta in helper condiviso (`contract-action-guards.ts`)
  per non driftare tra lista e dettaglio.
- **Banner M4 allineato al percorso reale:** `ContractFinancialHero` non dice più solo `Riapri -> Termina`
  in astratto; chiarisce che l'azione è disponibile dalla scheda stessa.
- **Lista contratti sotto `lg`:** aggiunto summary compatto nella cella Cliente con `crediti_usati/totali`,
  `N svolte` e `N prenotate non svolte` (solo se presenti). La colonna `Crediti` resta sede primaria su `lg+` —
  nessun doppione desktop.
- **Guardrail scadenza in modifica:** il form distingue esplicitamente `oggi` vs `passato`. `data_scadenza == oggi`
  mostra che il contratto resta vigente fino a fine giornata; `data_scadenza < oggi` su un contratto oggi ATTIVO
  richiede conferma esplicita prima del salvataggio. Nessun ricalcolo client-side di `SOSPESO/ESAURITO`: il testo
  dichiara solo che il contratto diventa immediatamente scaduto, e il lifecycle finale resta derivato dal SSoT.

**Verifica.**
- `next build` verde dopo il wiring finale (unico fix locale: `ReopenContractDialog` allargato da `ContractListItem`
  a `Contract` per il riuso dal dettaglio).
- **Verifica visiva reale eseguita dal founder** sull'ambiente dev **8000/3000**: la spec frontend può essere
  considerata chiusa.

**Metodo / stato docs.**
- `SPEC_G7.7_R5_TRASPARENZA_E_AZIONI_FRONTEND.md` chiusa e **archiviata** in `docs/archive/specs/` come design-record.
- Il **gap backend** emerso nello stesso audit (retrodatazione `data_scadenza` che cambia il lifecycle senza audit
  semantico dedicato) è stato **isolato come task separato** e NON entra in questo commit/task frontend.

**⏭️ Prossimo:** commit atomico del task frontend chiuso; poi riaprire il filone backend sulla tracciabilità del
`lifecycle` indotto da `update_contract` (spec separata, fuori da questa chiusura).

---

### 2026-06-27 — Hardening audit backend su retrodatazione/estensione scadenza (`update_contract`)

Chiusura del follow-up backend nato dallo stesso audit G7.7-R5: il path `PUT /contracts/{id}` poteva già
cambiare il lifecycle reale di un contratto aperto tramite `data_scadenza`, ma lasciava solo il diff generico
del campo, non una traccia semantica della transizione.

**Problema isolato.** Il modello era già corretto (`scaduto` = `data_scadenza < today`, `oggi` ancora vigente;
distinzione `SOSPESO` vs `ESAURITO` via crediti residui, non per comando manuale), quindi il debt NON era di
dominio né di endpoint mancante. Era un debt di **audit/observability** dentro `update_contract`.

**Implementato.**
- Nuovo helper audit fratello di `log_contract_lifecycle_transition()` in `_audit.py`: registra le sole
  transizioni del **lifecycle aperto** (`attivo/sospeso/esaurito`) indotte da `data_scadenza`, con:
  `lifecycle.old`, `lifecycle.new`, `trigger=data_scadenza_update`, `motivo=scadenza_retrodatata|scadenza_estesa`.
  Scelta intenzionale: NON overloadare l'helper G6/G7 di `chiuso`, che resta semanticamente dedicato alle
  transizioni del flag terminale.
- `update_contract` ora calcola il crossing col **SSoT** (`contract_state`) e con il conteggio canonico
  dell'occupazione-credito (`Programmato + Completato`). Nessuna logica inline `if data<oggi => sospeso`:
  il trigger è `data_scadenza`, la decisione del lifecycle resta al SSoT.
- Il log dedicato scatta **solo** se l'edit attraversa davvero il confine `vigente <-> scaduto`.
  Nessun falso positivo per `future -> future`, `past -> past` o contratti chiusi. Nessun nuovo endpoint,
  nessun cambiamento al modello, nessuna regressione sulla semantica di **ESTENDI = PUT** del Blocco 3.

**Verifica.**
- Nuovo file mirato `tests/test_contract_expiry_lifecycle_audit.py`: **6/6 verdi**.
  Copertura: `ATTIVO->SOSPESO`, `ATTIVO->ESAURITO`, `SOSPESO->ATTIVO`, `ESAURITO->ATTIVO`, più i 2 no-op
  (`ATTIVO->ATTIVO`, `SOSPESO->SOSPESO`) che dimostrano l'assenza di audit spurio.
- Regressione sul path già esistente di **ESTENDI**: `tests/test_suspended_contracts.py` **11/11 verdi**
  (prova che il riuso di `update_contract` per i sospesi non è stato rotto).
- `ruff check api/` verde.

**Lezione trasferibile.** Un update CRUD può essere corretto sul dato ma insufficiente sul significato. Se un
campo è anche una leva di derivazione di stato, il diff `old/new` del campo non basta più: serve una seconda
traccia che dica *che cosa è cambiato nel modello*. Qui l'errore sarebbe stato inventare un endpoint `suspend`
per colmare un debt che era solo di audit. Il metodo giusto è: preservare il comando esistente, rendere
esplicita la semantica derivata e testare i crossing veri + i no-op.

**Metodo / stato docs.**
- `SPEC_RETRODATAZIONE_SCADENZA_E_AUDIT_LIFECYCLE.md` chiusa e **archiviata** in `docs/archive/specs/` come design-record.
- Il dominio vivo non cambia: il follow-up è stato un hardening del path esistente, non una nuova policy di prodotto.

**⏭️ Prossimo:** se vuoi mantenere il metodo “un task = un commit”, il prossimo passo è il commit atomico del task backend audit.

---

### 2026-06-27 — G7.9 / ADR-018: terminazione BILATERALE (tutela del trainer)

3° audit senior (prodotto con Codex: `AUDIT_TERMINAZIONE_BILATERALE_2026-06-27.md` + spec omonima),
verificato code-grounded e ratificato in **ADR-018**. Dopo G7.7/G7.8 il recesso era corretto sulla
*matematica* (asse EROGATO) ma **asimmetrico sull'azione**: `compute_settlement` collassava `conguaglio≥0`
su `SALDO_A_PERDERE` → `terminate` lo mappava su `TERMINAZIONE_DECADENZA` = **write-off implicito** del
credito del trainer, senza scelta né traccia.

**Prova economica.** P=1000 (10 sedute @100), cliente ne fa 7 (R=700), versato V=500 → oggi
`quota_stornata=500` fonde **300** non-erogato (storno legittimo) + **200** = `R−V` servizio reso e non
pagato → **credito reale del trainer abbuonato in silenzio**. BUG_DI_DOMINIO, non UX.

**Governance (docs-only, commit `06f2771`).** ADR-018 (accepted, **estende ADR-016**, non emenda) + corpo
della spec **riscritto unificato** (zero doppia-verità: niente sezione "Emendamenti" sopra un corpo vecchio)
+ INDEX + adr/README (16 ADR). **6 decisioni founder** (2 round AskUserQuestion): (D-IMPORTO) importo
incassabile **editabile**, cap `[0, R−V]` solo verso il basso (mitiga `pro_sedute` PROVISIONAL senza
attendere il tributarista); (D-CREDITO-DIFFERITO) "chiudo oggi, incasso dopo" **rientra in scope** come
**G7.10** (entità dedicata `crediti_terminazione` FUORI da `residuo()`); (D-CATEGORIA) nuova
`INCASSO_CONGUAGLIO_CONTRATTO`; (D-ESITO-PURO) balance-based; (D-MOTIVO) `TERMINAZIONE_SALDO_TRAINER`;
(D-REOPEN) reopen inverte anche la nuova ENTRATA. **Split G7.9 (core, zero tabella) → G7.10 (differito).**

**Implementazione G7.9 (commit `fdf70b6`).**
- `contract_settlement.py` → esito `CREDITO_CLIENTE/CREDITO_TRAINER/PARI`; grandezze pure
  `credito_cliente/credito_trainer/quota_non_erogata/residuo_pre`; `SALDO_A_PERDERE` esce dal modulo puro.
- `terminate` → ramo `CREDITO_TRAINER` con **scelta obbligatoria** (422 senza): `INCASSA_ORA` (ENTRATA
  `INCASSO_CONGUAGLIO_CONTRATTO`, `X` editabile `[0, R−V]`, `totale_versato += X`,
  `quota_stornata += residuo_pre − X`) oppure `RINUNCIA_ESPRESSA` (nota obbl., audit
  `saldo_trainer_rinunciato`). Formula storno uniforme su tutti i rami; `residuo()==0` per costruzione.
- `reopen` → gamba **C-bis**: soft-delete della nuova ENTRATA + `totale_versato −=` (1ª volta che reopen
  tocca il lordo — eccezione sanzionata, gemella di `unpay_rate`; coordinata col guard H1).
- FE: `TerminateContractDialog` a **3 vie** (segmented control + importo editabile/nota), zero calcolo client.
- grep-guard ADR-018 in `check-all.sh` (la categoria deve restare in `CONTRACT_CASH_IN`).

**Verifica.** Backend **651 verdi** (full suite: solo 3 fallimenti da migrazione — cash-categories set,
2 reopen su DECADENZA/esito — corretti; +9 AC nuovi: incassa pieno/parziale/over-cap/no-metodo, rinuncia,
reopen round-trip, coerenza ricavi). `ruff` + `next build` + grep-guard verdi.

**Lezioni trasferibili.**
1. **La stessa policy cambia profilo di rischio col verso del denaro.** `pro_sedute` (PROVISIONAL) finché
   decideva un *abbuono* era a sfavore del trainer (rischio basso); appena decide un importo *fatturato a un
   cliente reale* il rischio è "bolletta indifendibile". Mitigazione scelta: **proposta editabile**, non gate.
2. **Cross-check per convalidare una formula nuova.** `INCASSA_ORA` è economicamente identico a "incasso il
   residuo pieno via G6, poi rimborso il non-erogato" (netto = R in entrambi) → conferma la §4.2 sulla
   macchina esistente; modello mentale: *incassi ciò che hai reso, storni il resto*.
3. **De-risking per ispezione dei consumer.** Gli aggregati cassa classificano l'inflow per
   `tipo=='ENTRATA'` + presenza `id_contratto` (financial-trend) o per esclusione esplicita di
   `RIMBORSO_CONTRATTO` (movement-stats/forecast) — **mai** per allowlist di categoria. Quindi la nuova
   ENTRATA è **auto-inclusa** come ricavo ovunque: il cablaggio "in tutti i predicati G7.5" si è ridotto a
   `CONTRACT_CASH_IN` + 1 test. Verificare *come* i consumer filtrano prima di stimare il blast radius.
4. **Riconferma `[[feedback_formatter_strips_imports]]`**: il PostToolUse ruff --fix ha stripato la nuova
   `CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO` perché aggiunta prima del suo uso → re-aggiunta dopo l'uso.

**⏭️ Prossimo:** G7.10 (credito differito: entità `crediti_terminazione`, worklist, endpoint incasso,
reopen esteso) → **G1 cifratura crm.db**. In coda: verifica Playwright live del dialog a 3 vie.

---

### 2026-06-28 — G7.10 / ADR-018: credito differito post-chiusura (entità `crediti_terminazione`)

Secondo e ultimo blocco di ADR-018: l'azione **A_CREDITO** della terminazione ("chiudo oggi, il cliente
paga dopo"). Il saldo a favore del trainer SOPRAVVIVE alla chiusura **senza** rompere `residuo()==0`.

**Architettura (la chiave).** Il credito differito **non** vive nel contratto: a `terminate` A_CREDITO il
dovuto viene **stornato** dal residuo del contratto (`quota_stornata` piena, come la rinuncia) e
**ri-tracciato** come receivable parallelo `crediti_terminazione`, **FUORI** da `contract_state.residuo()`.
Il contratto chiude con `residuo()==0`; il credito è tracciato altrove. Mai una Rate viva su contratto
chiuso (no rata-fantasma). Quando il cliente paga, l'incasso (anche parziale) genera una ENTRATA
`INCASSO_CONGUAGLIO_CONTRATTO` e fa crescere `totale_versato` (Strada B) → `residuo()` resta 0 (clamp,
`quota_stornata` ha già assorbito il differito), `netto_incassato` cresce.

**Implementazione (commit `16b70df`).**
- **Entità** `api/models/credito_terminazione.py` (`importo`, `importo_incassato`, `stato`
  APERTO/SALDATO/ANNULLATO, FK contratto/cliente/trainer) + **migrazione `b2c3d4e5f6a7`**. NB: essendo una
  TABELLA NUOVA, `create_db_and_tables()` (metadata.create_all, idempotente, al boot — `main.py:237`) la
  crea su **tutti** i DB business inclusi i deployati/frozen → la migrazione Alembic è solo record formale
  (diverso da G7.0/M1 che aggiungevano COLONNE e richiedevano `schema_sync`).
- `terminate` ramo `A_CREDITO`: crea il receivable (importo = credito_trainer), `incasso_ora=0` → la
  formula storno uniforme `quota_stornata += residuo_pre − incasso_ora` assorbe il differito; zero cassa.
- Endpoint `POST …/crediti-terminazione/{cid}/incassa` (parziale OK → SALDATO; **niente `_sync`**, il
  contratto resta chiuso) **+ `/annulla`** (rinuncia residuo → ANNULLATO, zero cassa) **+ list per
  contratto** + worklist `GET /dashboard/crediti-da-incassare` (aging-driven, gemella G6).
- `reopen` esteso (gamba **C-ter**): i receivable → ANNULLATO. Gli incassi parziali erano **già** invertiti
  da C-bis (stessa categoria `INCASSO_CONGUAGLIO_CONTRATTO`) → C-ter chiude solo il record. Inverso esatto.
- FE: dialog terminate a **3 vie** (+"Metti a credito e chiudi") + `CreditiDaIncassareCard` (worklist
  auto-nascosta) + `IncassaCreditoDialog` su `/rinnovi-incassi` + hook `useCreditiDaIncassare`/
  `useIncassaCredito`/`useAnnullaCredito` + tipi.

**Decisione di scope (v1).** A_CREDITO differisce l'**intero** `credito_trainer` (nessun edit dell'importo
al terminate, a differenza di INCASSA_ORA): il caso "incasso parte ora + parte dopo" si ottiene con
A_CREDITO + incasso parziale del receivable; il "forgive parziale" con A_CREDITO + `annulla` del residuo.
Un solo importo editabile per ramo → niente combinazioni di azioni in una sola terminazione (§12 dello spec).

**Verifica.** **658 test verdi** (+8 AC G7.10: receivable creato, incasso parziale→saldo, over-cap 422,
annulla, bouncer 404, reopen round-trip con incasso parziale invertito, worklist). `ruff` + `next build` +
grep-guard ADR-018 verdi.

**Lezione trasferibile.** *Un credito che sopravvive alla chiusura non si forza dentro l'invariante che lo
vieta — gli si dà un'entità a sé.* L'istinto sbagliato era tenere una Rate viva o gonfiare `residuo()` sul
chiuso; entrambi rompono `residuo()==0`. La via giusta: stornare dal contratto (che torna a 0) e
ri-tracciare il dovuto in un receivable parallelo, con la sua riconciliazione (l'incasso cresce
`totale_versato`, `quota_stornata` lo compensa → `residuo()` resta 0). L'invariante non si piega: si
aggiunge un piano ortogonale.

**⏭️ Prossimo:** **G1 cifratura crm.db**. In coda: verifica Playwright live (dialog 3-vie G7.9 + worklist
crediti G7.10). Differiti post-G1 invariati.

---

### 2026-06-28 — Governance: ADR-019 (mastro non-distruttivo + reopen ricalcola) + ADR-020 (wallet cliente)

Programma nuovo aperto da **due osservazioni del founder** sul reopen, dopo G7.9/G7.10. **G1 messo in
stand-by temporaneo** per dare priorita' a questo. **Governance docs-only** (zero codice, "governance first").

**Trigger 1 — reopen non protetto.** `reopen` soft-cancella scritture di cassa (rimborso + incasso conguaglio)
senza alert, **scavalcando la protezione del mastro** (`delete_movement` vieta — 400 — di eliminare un
movimento con `id_contratto`). Un terminate con `INCASSA_ORA` (€300 incassati) riaperto mostra **zero warning**:
€300 di reddito reale spariscono dal mastro.

**Trigger 2 — rimborso rigido + simmetria a meta'.** ADR-018 ha reso flessibile il lato trainer (incassa/
rinuncia/a-credito); il lato cliente e' rimasto a "rimborso pieno obbligato". Il founder: rimborso editabile
(anche parziale/zero) + il non-rimborsato = **credito al cliente** da tracciare.

**Audit specifico `AUDIT_REOPEN_SCENARIOS_2026-06-28.md`** (code-grounded): `reopen` e' **sovraccaricato** — un
verbo per 3 operazioni (undo / storno-correttivo / riattivazione). Grounding fiscale: **niente layer
documentale** (no fattura/nota-credito) → il `CashMovement` *e'* il dato fiscale → soft-cancellarlo in un
periodo dichiarato lo altera retroattivamente. Matrice **S1–S7**.

**Il principio (osservazione del founder, generalizzata e validata):** la posizione su un contratto e' sempre
**debito** (vive nel contratto, `residuo`) o **credito** (esce in un ledger: wallet cliente / receivable
trainer); **la cassa mossa non si tocca mai**; terminate e reopen **ricalcolano e instradano**. Questo
**dissolve** la matrice (S1/S2/S3/S6/S7 → trattamento unico; restano S4/S5 = software-propone) e **converge coi
best CRM aziendali** (Stripe/Chargebee/QuickBooks: customer credit balance + ledger immutabile +
reactivation-recompute). Due scoperte derivate: (A) `residuo` net-aware `P−netto−storno` (oggi usa il lordo →
sbaglia su un riaperto con rimborso); (B) il clamp `max(...,0)` **butta via gli overpayment in silenzio** → il
wallet e' il sink generale.

**Decisioni → 2 ADR:**
- **ADR-019** (mastro non-distruttivo + reopen ricalcola): D-CASSA-IMMUTABILE (reopen non cancella la cassa) ·
  D-RICALCOLA · D-RESIDUO-NETTO · D-INSTRADA (debito→contratto/credito→wallet) · D-PROPONE (S4/S5) · D-STAGING.
  **Emenda G7.4** "reopen = inverso esatto" → "true-to-ledger".
- **ADR-020** (wallet cliente = customer credit balance): rimborso editabile `[0,credito_cliente]` + non-
  rimborsato/overpayment → wallet; rimborsabile + applicabile a contratti futuri; **asimmetria corretta** vs
  trainer (si rinuncia a cio' che ti e' dovuto, non a cio' che devi); **v1 LEAN** (tracciato + applicato a mano;
  auto-applicazione cross-contratto = stato distribuito, differita su domanda).

**Distinzione senior architect vs developer (esplicitata col founder):** il *principio* (collassare la matrice
in un invariante, convergente con l'industria) e' la mossa da architect; renderla da *developer* e' **non
costruirlo tutto adesso** — adottare il principio come stella polare e **stadiare il build** (fetta economica
prima: reopen-recompute + propose + wallet manuale; cross-contratto dopo, su domanda). Il vero costo non e'
reopen ma il **wallet auto-spendibile cross-contratto** (consistenza di stato distribuito) → tenuto in panchina.

**Doc:** audit in `docs/operations/`, ADR-019/020 in `docs/adr/`, INDEX + adr/README (18 ADR). **Spec di
dettaglio SCRITTA:** `docs/technical/SPEC_INTEGRITA_CONTABILE_E_WALLET.md` (blocco **G8**, 2 fette — **G8.1**
reopen-recompute + residuo net-aware + wallet lean + rimborso editabile + UX-propone [6 step, 16 AC]; **G8.2**
wallet auto-spendibile cross-contratto, su domanda). **Prossimo:** implementazione **G8.1** (Step 1 = `residuo`
net-aware nel SSoT → Step 2 reopen-recompute → …). **G1 resta in stand-by.**

---

### 2026-06-28 — G8.1 / ADR-019+020: integrità contabile + wallet cliente — IMPLEMENTATA

Implementato il blocco **G8.1** (6 step, 6 commit `f84d345`→`a51d180`, branch FitManager_Studio). Il modello "ricalcola-e-instrada" è ora end-to-end: ogni euro tracciabile, nessun credito perso, la cassa mossa non si tocca.

**Step 1 — `residuo` net-aware** (`f84d345`): `contract_state.residuo()` da `P − versato − storno` a `P − netto_incassato − storno` (`netto = versato − rimborsato`), delegando a `netto_incassato()` già esistente. Backward-compat (byte-identico dove `rimborsato=0`). **Coupling necessario:** la gamba storno di `terminate` assorbe il rimborso (`quota = residuo_pre − incasso_ora + rimborso_out = P − netto`) per tenere `residuo()==0` sul chiuso. AC-1 (griglia byte-identica) + AC-2 (rimborso che resta).

**Step 2 — `reopen` non-distruttivo** (`8101281`): gambe delete C/C-bis RIMOSSE (la cassa di terminazione resta, fatti datati); reopen = R2 storno→0 · R3 receivable→ANNULLATO · R5 rate · R6 stato · R7 residuo net-aware auto. `GET /reopen-preview` (dry-run, R8 rinnovo-vivo S5) + schema `ReopenPreview`. **Coupling:** `compute_settlement` net-aware (`reso` vs `netto`) → ri-terminare un riaperto con rimborso-che-resta dà **PARI/CONSUNZIONE, niente doppio rimborso** (`test_reopen_then_reterminate` ora dimostra l'opposto di prima). 4 reopen-roundtrip migrati → "ricalcola" + AC-3/7/8.

**Step 3 — wallet + rimborso editabile** (`cb933b3`): entità `crediti_cliente` (ADR-020, gemello-cliente di `crediti_terminazione`, FUORI da `residuo()`; migrazione `c8d9e0f1a2b3` = record formale, `create_db_and_tables` la crea al boot; crm.db **27→28**). `terminate` ramo CREDITO_CLIENTE: `importo_rimborso` editabile `[0, credito_cliente]` (default pieno, metodo solo se >0); il non-rimborsato → wallet (`RIMBORSO_DIFFERITO`). `reopen` R4 annulla il wallet. AC-9/10/11/12 + AC-6.

**Step 4 — worklist + eroga** (`3fcc4f3`): `GET /dashboard/rimborsi-da-erogare` + `POST /clients/{id}/crediti/{cid}/eroga` (USCITA `RIMBORSO_CONTRATTO`, **`id_contratto=None`** → non tocca l'àncora `totale_rimborsato == Σ USCITA[id_contratto]`; il wallet traccia da sé via `importo_erogato`) + `GET /clients/{id}/crediti` + schema `CreditoClienteResponse`. AC-13/14.

**Step 5 — frontend** (`a51d180`): `ReopenContractDialog` da lista statica (che MENTIVA "rimborso annullato") a impatto pieno dal `reopen-preview`; `TerminateContractDialog` ramo cliente con rimborso editabile + microcopy wallet; `RimborsiDaErogareCard` + `EroghaRimborsoDialog` su `/rinnovi-incassi`; badge wallet su profilo (`ContrattiTab`). Hook (`useReopenPreview`/`useRimborsiDaErogare`/`useEroghaRimborso`/`useClientWalletCredits`) + tipi. next build verde.

**Step 6 — gate + doc:** grep-guard ADR-019 in `check-all.sh` (reopen non soft-cancella CashMovement, via estrazione awk del corpo di `reopen_contract`); doc allineati (FDM residuo net-aware §2, api/CLAUDE.md callout, root CLAUDE.md 28 tab, spec IMPLEMENTATA, questo log).

**Learning catturato** (`320f16a`): *cassa immutabile + residuo net-aware* in `LEARNING_APP_ARCHITECTURE.md` (3 failure mode silenziosi: doppio rimborso, reddito che sparisce, overpayment perso).

**Verifica:** suite backend **678 verde**, ruff verde, next build verde, **Playwright live OK** (read-only su crm.db reale: terminate editabile Agate €478,50 → riduce → microcopy wallet; reopen Agate-39 "rimborso €100 resta + residuo ricalcola a €550", il fix del dialog-che-mentiva; `/rinnovi-incassi` render pulito + auto-hide). **Prossimo:** G8.2 (wallet auto-spendibile cross-contratto) su domanda; **G1 cifratura** ripreso.

---

### 2026-06-28 — G8.1.1 / ADR-019 Addendum: reopen reconciliation + transparency (CRM-grade) — IMPLEMENTATA

Il founder ha testato il flusso G8.1 e ha trovato due cose che **confondono l'utente** anche se il calcolo è corretto: (1) dopo reopen-con-cassa il dettaglio contratto NON mostrava lo storico dei movimenti (rimborsi/conguagli invisibili → il residuo "non torna" a vista); (2) le rate ripristinate restavano agli importi pre-terminate, superiori al residuo ricalcolato. Audit senior → **G8.1.1 = hardening** (recepire fino in fondo il modello net-aware/non-distruttivo nel *contorno*: presentazione + piano rate + guard di cap/stato), non un blocco nuovo. Governance docs-only prima (ADR-019 Addendum + SPEC §14/§14.6), poi codice.

**F3/F4 — net-aware ovunque** (cap + sotto-stato denaro): `_cap_rateizzabile` (`rates.py`) usa `cstate.netto_incassato()` invece del LORDO `totale_versato`; nuovo `cstate.is_saldato(contract)` (SSoT: `prezzo>0 ∧ residuo()≤0.01`) sostituisce il confronto LORDO `versato≥prezzo` in `pay_rate`/`unpay_rate`/`incassa_residuo`. Senza, `pay_rate` (già net) e `_cap`/auto-close (lordo) si contraddicono e un riaperto-con-rimborso poteva marcare SALDATO con `residuo()>0`. Test: `test_contract_state.py::test_is_saldato_net_aware`.

**F2 — reopen riallinea il piano rate** (decisione founder = **riallineo automatico**): nuovo `_reconcile_rate_plan(session, contract, trainer_id)` cablato in `reopen` dopo il ripristino rate. Taglio cronologico dell'eccedenza sul residuo ricalcolato: rata interamente eccedente con saldato 0 → eliminata; rata a cavallo → previsto ridotto a coprire l'esatto residuo (PARZIALE, **mai sotto `importo_saldato`**); sotto-copertura → il resto resta "da pianificare" (mai rata-fantasma). L'inverso-esatto M1/G7.7 ("ripristina rate identiche") **non vale più** sotto il non-distruttivo. +4 test `test_contract_reopen.py` (riallinea eccedenza · sotto-copertura · round-trip esatto senza cassa · parziale mai sotto saldato).

**F1/F5 — storico cassa unificato** (D-CASSA-VISIBILE): `get_contract` espone `movimenti` = TUTTI i `CashMovement` con `id_contratto` (acconto, pagamenti rata, **rimborsi** USCITA, **conguagli** ENTRATA), ordine cronologico; schema `ContractMovementItem` (`financial.py`). Σ-con-segno (ENTRATA + / USCITA −) == `netto_incassato`; l'erogazione wallet (`id_contratto=None`) NON compare (cassa a livello cliente). FE: tab **"Storico"** del dettaglio → `ContractHistoryTab` card "Movimenti di cassa" con **saldo netto progressivo** + *Netto incassato*. Test: `test_contract_reopen.py::test_f1_movimenti_esposti_dopo_reopen_con_cassa` + `test_wallet_cliente.py::test_f1_eroga_wallet_non_in_movimenti_contratto` (confine wallet).

**F6 — storico stato/attività** (CRM-grade): nuovo `GET /contracts/{id}/history` (bouncer, read-only) = timeline curata da `audit_log` (`entity_type='contract'`) via `_curate_contract_event`. Eventi: Creato · Terminato [esito + rimborso + motivo] · Riaperto [residuo ricalcolato + rate riallineate + rimborso preservato] · Saldato · Stato/Modifica. **Dedup delle companion**: terminate/reopen scrivono SIA l'entry ricca (`motivo_chiusura`) SIA la transizione lifecycle bare (`chiuso`+motivo tecnico) → si tiene la ricca, si scarta la companion (`motivo` 'terminazione'/'riapertura_esplicita'). La pura cassa (pagamenti intermedi) NON inquina la timeline di stato (vive in F1/F5). FE: card "Stato & attività" (timeline, recente in cima). Schema `ContractHistoryEvent`. Nuovo `test_contract_history.py` (6 test: creazione · terminazione ricca senza companion · ordine terminate→reopen · completamento→saldato · pagamento intermedio non inquina · bouncer 404).

**Verifica:** suite backend **691 verde** (+13 vs G8.1), ruff verde, **grep-guard ADR-019 verde** (reopen non soft-cancella CashMovement), next build verde. Governance allineata: ADR-019 Addendum (stato IMPLEMENTATA), SPEC §14/§14.6 (status), api/CLAUDE.md callout, FDM. **Prossimo:** Playwright live sul tab Storico (env dev del founder); poi G8.2 su domanda / **G1 cifratura** ripreso.

**🐞 Bug F6 trovato dal Playwright gate + corretto (`a52e7f4`):** la curation #2 pretendeva `"chiuso" in changes` → le riaperture in formato STORICO G8.1 (changes senza `chiuso`, il toggle stava solo nella companion poi deduplicata) sparivano dalla timeline (2 "terminato" senza "riaperto"). Fix: discriminante = `motivo_chiusura.new is None`. +2 test unit, suite 693, Playwright LIVE OK (contratto 33). Committato+pushato `2602cbd`+`a52e7f4`.

---

### 2026-06-28 — G8.1.1 follow-up (test di flusso founder, Garavelli): reopen-con-rimborso sotto-copre il piano rate

Secondo test di flusso del founder su un reopen-con-rimborso (contratto Garavelli 33). Sintomo: «alla riapertura considera giustamente il rimborso (367−37=netto 330), il mancante è 1100−330=**770** giusto, **ma rateizza per 733** — mancano i 37». Audit on-demand richiesto.

**Causa radice.** Un rimborso rende `netto_incassato (330) < Σ importo_saldato (367)` — la cassa netta trattenuta scende sotto i pagamenti-rata **lordi** (Strada B tiene `totale_versato` lordo; il rimborso è una USCITA separata). `residuo()` è net-aware (770) ma due calcoli del piano rate erano ancora gross-bound. Già corretti/net-aware (per contrasto): `importo_da_rateizzare = residuo()` e `generate_payment_plan` (valida contro `residuo()` → **rigenerare funziona**). Il sistema era **internamente incoerente**: dichiarava "da rateizzare 770, mancano 37" (lo flaggava pure: `piano_allineato=False`) ma non copriva il gap né lasciava aggiungerlo a mano.

**Difetto 1 — `_cap_rateizzabile` (rates.py): il clamp `max(0, netto − saldato)` ingoiava il −37** → `cap=prezzo(1100)`, `spazio=0`: impossibile aggiungere i 37. **Fix A (richiesto, consistenza SSoT):** tolto il clamp → `acconto` negativo è corretto e load-bearing, `cap = prezzo + rimborso − storno = 1137`, `spazio = 37`. Chirurgico: inerte con `rimborsato==0` (netto≥saldato).

**Difetto 2 — `_reconcile_rate_plan` (contracts.py): la sotto-copertura era no-op deliberato** (`Σ residui 733 ≤ residuo 770 → return`, lasciava "da pianificare"). **Fix B (scelta founder AskUserQuestion = auto-copertura):** la sotto-copertura ora copre **solo il RIMBORSO che resta** (`min(ammanco, totale_rimborsato)`) — l'unico € che il reopen ha aggiunto al residuo e che il piano non copre — assorbendolo nell'**ultima rata pendente ESISTENTE** (mirror del taglio). Niente cassa toccata; `cresciute` entra in `rate_riallineate` nell'audit del reopen. **⚠️ Iterazione (1ª stesura troppo larga, intercettata dalla suite):** la prima versione copriva TUTTO l'ammanco e **fabbricava una rata** quando non c'erano pendenti → ha rotto `test_m2_update_rate_su_terminato_400` (CONSUNZIONE/storno-puro: nessuna pendente, residuo "da pianificare" → la rata fabbricata da 500 consumava lo spazio-piano e bloccava `update_rate` post-reopen). Il limite `min(ammanco, totale_rimborsato)` + "cresci solo pendenti esistenti, mai fabbricare" risolve: re-incassa esattamente il rimborso, lascia intatto il "da pianificare" originale del trainer.

Dopo i due fix, Garavelli riaperto: residuo 770, **piano pendente 770** (366,5 + 403,5), `piano_allineato=True`. +4 test (Garavelli end-to-end · cap unit Fix A · sotto-copertura coperta-dal-rimborso · CONSUNZIONE-senza-rimborso non-fabbrica). Governance: ADR-019 Addendum (F2-bis/F3-bis), SPEC §14.7, questo log. **Learning livello-3:** *net-aware non è un singolo punto ma un asse* — ogni calcolo che esprime "quanto è dovuto/rateizzabile" deve derivare dallo stesso SSoT (`residuo()`); un clamp difensivo (`max(0,…)`) su un termine intermedio maschera in silenzio l'asimmetria lordo/netto del rimborso, e un "no-op su sotto-copertura" la nasconde alla vista. Sintomo classico: un KPI (residuo) e il suo consumatore (piano rate) divergono di **esattamente** l'importo del rimborso. **Corollario (dalla regressione test_m2):** "auto-copertura" non è "chiudi ogni gap" — va circoscritta alla causa (il rimborso ri-incassabile), o invade il legittimo "da pianificare" e fabbrica stato che rompe invarianti a valle.

---

### 2026-06-28 — Audit-2 (3° test di flusso founder, Garavelli): A deploy-lag, B versato-netto, C accorcia-scadenza

3° giro di test del founder → 3 punti, audit on-demand.

**① I «37 non rateizzati» — GIÀ RISOLTO da `be7fbb4`, vista stale (zero codice).** Il DB prova che F2-bis ha girato: `audit_log` su rate 102 con `reopen_cover` (28/06 18:31) → rata 102 = 403,50 (366,5+37), pendenti = 770 = residuo, allineato. Gli screenshot erano di PRIMA di quel reopen (uvicorn senza auto-reload: il server del founder serviva codice pre-fix al momento dello scatto). Il «37 scaduto non rateizzabile» in lista era il disallineamento, ora 0. → basta ricaricare. **Learning operativo:** un fix su processo backend long-running non è "live" finché il server non riparte; uno screenshot post-fix-commit può ancora mostrare lo stato pre-fix.

**② `versato` LORDO fuorviante in lista + scheda [issue B, decisione founder = netto-primario].** Fuori dallo Storico, lista (`ContractsTable`) e scheda (`ContractFinancialHero` + tabella `PaymentPlanTab`) mostravano `totale_versato` LORDO (367) ignorando il rimborso (netto reale 330) — a vista «1100 − 367 ≠ 770». Fix FE-only (il netto = `totale_versato − totale_rimborsato`, già esposti dal backend; `ContractListItem extends Contract` → tipo TS già ok): hero + lista mostrano il NETTO come cifra primaria, barra su netto, nota «lordo 367 · −37 rimborso» + label «Incassato netto» (vs «Versato») quando c'è rimborso; la tabella di riconciliazione aggiunge la riga «Rimborsato +37» → `1100 − 367 + 37 = 770` torna a vista.

**③ Accorcia-scadenza bloccata da rate oltre la data [issue C, decisione founder = sposta-rate].** `update_contract` dava 422 "Modifica prima le rate" anticipando `data_scadenza` con rate oltre il nuovo termine. Ora **auto-cap**: le rate NON-SALDATE oltre la nuova data sono riportate ALLA scadenza (Chargebee-style, come `generate_payment_plan`), il dovuto resta intero, audit `scadenza_anticipata`; le SALDATE non si toccano (niente riscrittura di storico cassa). +1 test `test_update_contract_accorcia_scadenza_sposta_rate`. Pitfall/guard #10 (api/CLAUDE.md) riscritto da "blocco 422" a "auto-cap".

Gate: ruff + grep-guard + suite + next build verdi. Governance: api/CLAUDE.md (#10), questo log.

---

### 2026-06-28 — Audit posizione finanziaria → G8.2-prep / D1 forma-d: la fotografia netta per-contratto (chiude Bug-1)

Audit architetturale READ-ONLY (trigger founder) → `docs/technical/AUDIT_POSIZIONE_FINANZIARIA_E_INVARIANTI_2026-06-28.md`. **Tesi confermata sul write-model decentralizzato ma corretta:** il read-model È già centralizzato (`contract_state.py`, regola d'oro rispettata). Radice = nessun punto unico applica gli invarianti dopo le transizioni + nessuna posizione-CLIENTE di prima classe + clamp `max(0,…)` che silenziano. **Money-bug latente Bug-1:** `reopen` annullava il wallet **incondizionatamente** senza riassorbire la cassa già **erogata** (USCITA `id_contratto=None`, fuori da `totale_rimborsato`) → quegli euro sparivano dalla posizione del contratto riaperto (cassa nel mastro intatta, attribuzione persa). Scenario `eroga-parziale → reopen` non testato.

**Decisione founder D1 — CHIUSA, forma (d) "fotografia netta":** il reopen NON riavvolge; scatta la posizione netta cliente↔contratto e quella è il punto di partenza. Rimborso/conguaglio/wallet erogato = termini della stessa somma (modello billing-leader: ledger immutabile, posizione ricalcolata). Perimetro = **PER-CONTRATTO** (posizione-cliente intera = G8.2, in panchina).

**Implementazione G8.2-prep (5 passi, branch FitManager_Studio).**
- **P1 — read-model:** `contract_state.posizione_netta_contratto(contract, crediti_cliente)` (pura, `netto = versato − rimborsato − Σ erogato wallet VIVI`). Esclude i wallet ANNULLATO (già riassorbiti) → la fotografia è **invariante attraverso il reopen**. È il gradino che abilita G8.2 senza riscrittura.
- **P2 — checker:** `contract_state.assert_contract_invariants(...)` (pura): I1 (`residuo()==0` su chiuso), I4 (`netto_raw≥0` senza clamp-mask), **I5** («nessun euro della fotografia sparisce», ancora ledger `totale_rimborsato == Σ USCITA RIMBORSO[id_contratto] + Σ erogato wallet RIASSORBITO`). In `reopen` via `_log_invariant_violations` **log-only** (predisposta-per-409).
- **P3 — harness:** `tests/test_financial_invariants_harness.py` (invariante × transizione × stato di partenza). Costruito per essere **rosso oggi** su `eroga_wallet_then_reopen` (Bug-1) e verde su tutto il resto → rosso→verde col P4. È la rete strutturale che chiude la CLASSE.
- **P4 — fix (conseguenza):** `reopen` gamba **R2-bis** folda l'erogato dei wallet annullati in `totale_rimborsato` → rientra nel `residuo()` net-aware **per costruzione**. Cassa NON toccata (ri-attribuzione gestionale, ADR-019). `reopen-preview` espone `wallet_erogato_riassorbito` + messaggio «il cliente ha già riavuto €X, che torna dovuto» (mai silenzioso). Es. acconto 800/reso 200/wallet 600/eroga 250 → reopen → `totale_rimborsato=250`, **`residuo()=450`** (era 200 = bug). FE: type-sync + `<li>` nel `ReopenContractDialog`.
- **P5 — patch strutturali:** `delete_client`/`delete_contract` RESTRICT su posizione aperta (wallet/receivable APERTO, **Bug-4**); estratto `contract_state.recompute_stato_pagamento()` = unica derivazione SALDATO/PARZIALE/PENDENTE (**Bug-3**, 4 copie inline pay/unpay/incassa/reopen, byte-identico).

**Learning architetturale.** (1) *Read-model centralizzato ≠ write-model centralizzato:* `contract_state` poteva solo **segnalare** una violazione (residuo>0 su chiuso), mai **impedirla** — il checker osservabile (P2) + l'harness (P3) chiudono questo gap senza un rewrite del cuore finanziario. (2) *Il fold preserva la fotografia attraverso la transizione:* `posizione_netta_contratto` pre-reopen == post-reopen perché Werog migra da «erogato wallet vivo» a «totale_rimborsato» (wallet→ANNULLATO escluso) → il netto non cambia, l'attribuzione sì. (3) *Re-attribuzione ≠ tocco-cassa:* il `CashMovement` wallet resta `id_contratto=None` e datato; solo `totale_rimborsato` (colonna di posizione) assorbe — il mandato dell'audit lo sancisce lecito (ricalcolo della posizione, non riscrittura di documenti fiscali).

**D2 — APERTA, in panchina:** wallet auto-spendibile cross-contratto (un credito di A applicabile a B) = stato distribuito; opzioni a/b/c (mai / manuale / automatico) → decisione founder a domanda reale. Vedi `SPEC_INTEGRITA §15`.

**Gate.** Suite backend **711 verde** (era 696; +harness +behavioral +2 delete-guard), `ruff api/` + 4 grep-guard (ADR-016/017/018/019) + `tsc --noEmit` (FE) verdi. ⚠️ **`next build` pieno NON eseguito** (dev server del founder tiene `.next`/db/log lock — WinError 32; tsc usato come proxy). Governance allineata: ADR-019 **Addendum II**, SPEC_INTEGRITA **§15**, api/CLAUDE.md (blocco G8), INDEX, FDM §residuo-net-aware. **Prossimo:** `check-all.sh` completo + Playwright a env libero; poi **G1 cifratura**.

---

### 2026-06-29 — Audit difetti residui di integrità → Slice A/B/C (audit-trail · force-delete · storico reopen)

3° passaggio adversariale (Codex) sul filone finanziario, poi **verificato riga-per-riga** sul codice vivo →
`docs/operations/AUDIT_INTEGRITA_RESIDUI_2026-06-29.md`. **NON tocca l'aritmetica** (asse DENARO/EROGATO regge,
98 test mirati verdi al baseline): tre difetti di **trasparenza/integrità amministrativa**, tutti **conseguenze
di decisioni già accettate** (ADR-018/019) → **nessun nuovo ADR** (ADR-019 **Addendum III** + `SPEC_INTEGRITA §16`).
**Metodo:** governance docs-only PRIMA (`a8c0ce1`), poi un commit backend-only per slice (A→B→C), poi questo log.

**Slice A — audit della terminazione parziale a una sola verità** (`b895edb`, P1). La companion lifecycle di
`terminate` passava `settlement.credito_cliente` (credito teorico) mentre la entry ricca passava `rimborso_out`
(cassa uscita): con rimborso **parziale** (resto a wallet) due `importo_rimborsato` diversi per la stessa chiusura
nell'audit grezzo. Regressione introdotta dal rimborso editabile (G8.1): pre-G8.1 `rimborso_out==credito_cliente`.
Fix 1-spot (`contracts.py:1784`): la companion porta `rimborso_out`. Invariant-neutral (nessun invariante legge
il JSON di audit). +2 test (AC-A1 parziale 200/100-a-wallet → entrambe le entry 200; AC-A2 pieno byte-identico).

**Slice B — il guard posizione-aperta vale SEMPRE** (`7e0699e`, P2). `DELETE force=true` aggirava il RESTRICT su
wallet/receivable APERTO (viveva solo nel ramo `not force`) → posizione viva orfanata su contratto soft-deleted,
reopen poi impossibile (bouncer 404). Completamento di Bug-4 (G8.2-prep): `delete_client` aveva già il guard
sempre-attivo, `delete_contract?force` era l'outlier. Fix: RESTRICT-3 dedentato fuori da `if not force:` → sempre
409. Policy: `force` abbuona rate/crediti-seduta (write-off noto), MAI una posizione con controparte. +3 test
(AC-B1 wallet+force→409 · AC-B2 receivable+force→409 · AC-B3 no-regressione: rate+crediti senza posizione→force 204).

**Slice C — lo storico del reopen spiega la cassa preservata** (`fea9ff3`, P3). `_curate_contract_event` caso #2
cercava `rimborso_preservato` (campo che `reopen` non emette mai) → la riga non si stampava, pur essendo
l'informazione più importante del reopen non-distruttivo (ADR-019 D-CASSA-VISIBILE); l'intento era documentato
(questo log, F6 G8.1.1) ma mai cablato. Fix del **consumatore**: deriva da `totale_rimborsato.new` +
`wallet_erogato_riassorbito` (già emessi dal reopen). Wording completo: "rimborso €X preservato (di cui €Y da
wallet riassorbito)". +3 test (AC-C1 E2E reopen-con-rimborso · AC-C2 unit wallet riassorbito · AC-C3 unit storno-puro).

**Verifica.** Suite backend **718 passed** (+8), ruff verde, 4 grep-guard finanziari (ADR-016/017/018/019) verdi.
`next build` pieno NON eseguito (FE invariato, zero file frontend toccati; dev server del founder tiene `.next`).
**Rischio residuo dichiarato (fuori scope):** l'harness `assert_contract_invariants` resta cablato solo su `reopen`
(log-only) — già differito da G8.2-prep; allargarne il rollout a terminate/incassa/pay/unpay/eroga è il blocco di
hardening *dopo* A/B/C.

**Learning livello-3 (UI corretta ≠ substrato corretto).** Un sistema può apparire **giusto in UI mentre il
substrato forense è contraddittorio**: in P1 la curation dello storico deduplica la companion e legge
`totale_rimborsato`, mascherando i due `importo_rimborsato` divergenti che una query diretta su `audit_log`
vedrebbe. Corollario da P3: un **campo documentato che nessun produttore emette è codice morto silenzioso** nel
consumatore — l'intento ("rimborso preservato", scritto nel log F6) non si auto-realizza, va cablato e
**falsificato con un test E2E che attraversa producer→consumer**, non solo unit. Regola operativa: per ogni evento
finanziario verificare la coerenza del **dato grezzo** (audit/ledger), non solo della sua proiezione UI.

---

### 2026-06-29 — G8.3 / ADR-021: INV-RATE — il piano rate è una partizione del residuo

Test di flusso del **trainer reale** (Chiara Pais, contratto 35): contratto **SALDATO** (`residuo()=0`) ma la UI
mostra `RATE PAGATE 0/1` e **"1 scaduta"**. Il founder ha chiesto di **fermarsi** e capire l'errore architetturale
e di metodo che perseveriamo, non l'ennesima toppa. Diagnosi sul DB reale (read-only) → audit
`AUDIT_PIANO_RATE_VS_RESIDUO_2026-06-29.md` + **ADR-021**.

**Ground truth.** Contratto 35: versato 400 = **280 via rata** (`mov 223`, `id_rata=106`) + **120 via conguaglio**
(`mov 221`, `INCASSO_CONGUAGLIO_CONTRATTO`, **`id_rata=None`**). Rata 106: `previsto 400 / saldato 280` → PARZIALE,
residuo-rata **120** = esattamente il conguaglio. La pistola fumante: `_to_response_with_rates` calcola `residuo`
dal SSoT (0) **e** `rate_scadute` dal ledger rata (1) **e** `piano_allineato=False` / `disallineamento=−120` — il
sistema **misura la propria contraddizione** e la spedisce alla UI.

**Errore architetturale.** Due ledger dell'obbligazione, SSoT solo sul residuo. Il piano rate è un secondo ledger
che la UI legge; riconciliato **solo su reopen** (`_reconcile_rate_plan`). Ogni canale non-rata che abbassa il
residuo (`incassa-residuo`, conguaglio) lo lascia stale. **Errore di metodo:** test su operazioni isolate (non
sequenze composte); l'harness non copriva l'invariante cross-ledger; patchiamo i transition point invece di
imporre un invariante; e ignoriamo `piano_allineato=False` che già misura l'incoerenza.

**Legge (founder = "legge mancante corretta") — INV-RATE:** contratto non chiuso → `Σ(previsto−saldato) ≤ residuo()`.
Eccedenza = denaro-fantasma (vietata); sotto-copertura = "da pianificare" (legittima, F2-bis invariata).

**Stance C (founder), tre leve, backend-only, zero schema-change, asse DENARO invariato:**
- **B — D-RICONCILIA-OVUNQUE** (`20e11d0`): `_reconcile_rate_plan` (il cui ramo ECCEDENZA già taglia al residuo,
  mai sotto il saldato) chiamata anche dopo `incassa-residuo`; il reopen la chiamava già. La rata stale → SALDATA
  *per conseguenza*, mai a mano.
- **I6 — INV-RATE nell'harness**: `assert_contract_invariants(rate_attive=…)` guadagna I6; `_log_invariant_violations`
  (reopen) e l'harness `_invariants` lo passano; nuovo scenario `incassa_residuo_con_rata` + unit `test_i6…`
  (rosso sul fantasma → verde dopo la riconciliazione). Chiude la **classe**.
- **A — proiezione difesa**: `_to_response_with_rates` clampa `is_scaduta`/`rate_scadute` col `residuo()` (un saldato
  non ha rate scadute) → copre a vista i dati **già stale** (contratto 35) finché B non li sana.

**Verifica.** Suite **723** verde su data singola (720 nel primo run completo a cavallo della mezzanotte 29→30 +
i **3 date-flake** — `suspended-contracts`/`clients-to-recover`, `TODAY` congelato all'import vs `date.today()` a
runtime — confermati verdi isolati su 06-30), ruff verde, 4 grep-guard finanziari verdi. Governance docs-only PRIMA
(`a44c01d`: ADR-021 + SPEC §17 + audit), poi codice (`20e11d0`), poi questo log.

**Learning livello-3 (un SSoT non è SSoT finché ogni suo consumatore deriva da lui).** Avere eletto `residuo()` a
SSoT del dovuto non basta: finché un **secondo ledger** (il piano rate) esprime la stessa grandezza ed è
riconciliato solo su *un* path, ogni nuovo canale che muove il SSoT per un'altra strada lo desincronizza. Il
sintomo è un sistema che **misura la propria incoerenza** (`piano_allineato=False`) e la mostra invece di
risolverla. Il rimedio non è la riconciliazione al transition-point (capability) ma l'**invariante imposto +
esercitato dall'harness su sequenze composte** (correttezza): chiude la classe, non l'istanza. Metodo: i bug di
questa famiglia emergono **solo** dalle sequenze reali composte (terminate→incassa→reopen→paga), non dalle
operazioni isolate — il test reale del trainer ha trovato ciò che 700+ unit-test non vedevano.

---

## 2026-06-30 (sessione lunga) — G9 financial command layer: G9.0 → G9.2a + Reperto #1 + governance G9.2b

Avvio del programma **G9** (ADR-022): rendere il libro mastro `CashMovement` **load-bearing** dando al SSoT di
lettura `contract_state.py` il suo gemello di **scrittura**. Trigger: dopo G8.3 il founder ha chiesto «cosa
farebbe un senior CRM leader che non stiamo facendo». Diagnosi (review multi-agente): write-model decentralizzato
→ doppia-verità ledger↔colonne sincronizzata a mano in ~8 siti. **10 commit pushati** su `FitManager_Studio`.

**G9.0 — sensore invarianti ovunque (gate chiuso).**
- `f419169` G9.0a: estratto `_log_invariant_violations` → `api/services/financial/invariant_gate.py` (sensore
  **TOTALE-per-costruzione, zero try/except**), cablato log-only sulle 6 transizioni denaro mancanti.
- `2e1799e` G9.0b: `/reconciliation` BIDIREZIONALE (lato rimborso, ancora I5 raffinata).
- `5b54ccd` G9.0c: SSoT unico `contract_state.residuo_credito` (de-dup 2 DTO) + nota KPI gross-SQL re-scoped.
- `e683058` **Reperto #1** (emerso dal sensore il primo giorno): `incassa_credito_terminazione` accendeva I1
  (residuo_raw<0) — `quota_stornata` assorbiva l'intero residuo_pre al terminate A_CREDITO ma non si riduceva
  all'incasso del receivable. Fix: l'incasso REVERTE lo storno provvisorio (`quota_stornata −= importo`);
  corretto anche `reopen-preview` (sovrastimava `residuo_dopo`). Esame: `quota_stornata` NON sommata in alcun KPI.
- `ce69d72` chore: untrack `.claude/settings.local.json` (config locale già in `.gitignore`).

**G9.1 — penna unica (gate chiuso).** `api/services/financial/ledger.py` `post_inflow`/`post_outflow`: crea il
`CashMovement` E il delta-colonna nello STESSO atto → I5 (`totale_versato == Σ ENTRATA`) vero per costruzione.
Adozione strangler-fig: `8674493` G9.1a (pay_rate + incassa_residuo) · `897a21a` G9.1b (terminate×2 +
incassa_credito + eroga, net −30 righe) · `d21abac` G9.1c (acconto create_contract/renew + collasso 4ª copia
inline `stato_pagamento`). **Tutte le scritture di cassa su contratto passano ora per la penna, zero eccezioni.**

**G9.2a** (`97b4463`): `project_columns_from_ledger` (inverso per-contratto di reconciliation) + ancora
ledger-versato nel sensore. Scoperta: wallet/receivable sono GIÀ postings → resta solo `quota_stornata` (storno).

**G9.2b governance** (`a8ea4dd`): bivio architetturale — storno nel mastro cassa riapre la superficie esclusione
scartata da ADR-019. **Decisione founder = Opzione A (ledger SEPARATO `rettifiche_contratto`)** → ADR-022 Addendum I.

**Metodo/learning (dettaglio in ADR-022 / SPEC_G9 / `LEARNING_PROGRAMMAZIONE §0.8`):**
- *Strumenta-poi-imponi*: il sensore log-only ha trovato un bug reale (Reperto #1 + reopen-preview) che nessun
  test copriva — il suo scopo, il primo giorno.
- *Correctness by construction, non `try/except`*: il founder ha intercettato un `except Exception` largo nel
  sensore (auto-contraddittorio). → convenzione binding in `api/CLAUDE.md`.
- *Estrazione fedele*: ogni migrazione verificata dalla **full-suite** (732→755 passed, 0 xfailed),
  behavior-preserving, spesso net-negativa di righe (la penna toglie boilerplate).

**Verifica.** Suite full **755 passed / 0 xfailed**, `check-all.sh` verde a ogni commit. **⏭️ Prossimo: G9.2b
CODICE Stage 1** (modello `RettificaContratto` + `post_adjustment` + schema_sync + backfill idempotente + wiring
3 write-site; `residuo()` byte-identico; **backup-first per il backfill** sui dati reali). Poi G9.3 TransitionExecutor,
G9.4 enforcement, G9.5 Hypothesis, G9.6 Money.

---

### 2026-06-30 (sessione 2) — G9.2b decisioni di dettaglio (DEC-1/2/3) + design implementation-ready (docs-only)

Ripresa verso **G9.2b CODICE Stage 1**. Letta la SSoT **sul codice vivo** (non dalla memoria): ADR-022 Add.I,
SPEC_G9 §G9.2, `ledger.py`, `credito_terminazione.py`, `database.py`, `schema_sync.py`, i 3 write-site di
`quota_stornata`. Prima di scrivere codice, **3 decisioni di dettaglio risolte da senior** e messe a record
(SPEC_G9 **Appendice B**, implementation-ready):

- **DEC-1 — il clamp `max(·,0)` di `incassa` si ritira; I4 (+I1 sui chiusi) fa da rete log-only.** È un'asserzione
  travestita da correzione, **incompatibile** con l'ancora `quota_stornata == Σ rettifiche` (lo scopo di Opzione A) e
  **irraggiungibile** (`old_quota ≥ credito_trainer ≥ Σ incassi`; test `700/600/200` mai clampati). **Seconda occhiata
  sul caveat** («un log che nessuno legge»): DEC-1 *migliora* l'osservabilità vs il clamp (zero-segnale); `residuo()`
  ha il suo `max(·,0)` a valle; doppia rete I1+I4 sui chiusi; il log-only è temporaneo (Stage 2 → `/reconciliation`,
  G9.4 → 409). Presidi costo-zero: **test del path no-clamp** + **commento inline** anti-ripristino.
- **DEC-2 — la penna arrotonda la colonna a 2dp.** Gli assert dei test fanno già `round(quota_stornata, 2)` → la
  byte-identità a 2dp è sufficiente, **FP non è un rischio**.
- **DEC-3 — `id_cliente` NON entra** in `rettifiche_contratto` (la memory-index lo citava per analogia — **corretto**):
  sotto-libro del contratto, derivabile via `JOIN`, evita una verità-parallela; `trainer_id` resta (tenant-isolation).

**Dato reale (sola lettura, `crm.db` dev): 38 contratti, 1 solo con `quota_stornata>0`** (TERMINAZIONE_RIMBORSO,
250.0) → il backfill produrrà **1 riga** `BACKFILL_LEGACY`, verificabile a occhio sul clone al checkpoint.

**Piano commit Stage 1 (baseline 755/0xfailed):** `G9.2b.1` modello+registrazione+migrazione · `G9.2b.2` penna
`post_adjustment` · `G9.2b.3` backfill idempotente **[🔶 checkpoint founder, backup-first]** · `G9.2b.4` wiring 3
write-site. **Docs-only oggi (zero codice):** SPEC_G9 Appendice B + ADR-022 Add.I decisioni di dettaglio.
**⏭️ Ripresa domani: `feat: G9.2b.1`.**

---
## 2026-07-02 — G9.2b Stage 1: ledger rettifiche_contratto + terza penna post_adjustment (chiude G9.2)

Implementato il design dell'**Appendice B** di SPEC_G9 (bake-nel-SPEC del 2026-06-30, DEC-1/2/3). Da oggi
`quota_stornata` è una **proiezione verificabile** di `Σ importo[rettifiche_contratto]` — l'ultima grandezza
del contratto senza posting ha la sua derivazione ledger. **4 commit atomici pushabili**, branch verde a ognuno:

- `1795425` **G9.2b.1** — modello `RettificaContratto` (`rettifiche_contratto`, append-only, importo FIRMATO
  + storno/− reversal, 4 causali `CAUSALE_*`) + registrazione (`models/__init__` + import esplicito in
  `database.py`, specchio di share_token) + record migrazione `d9e0f1a2b3c4` (Alembic FROZEN → la crea
  `create_db_and_tables` al boot). crm.db 28→29 tabelle.
- `45f6178` **G9.2b.2** — terza penna `ledger.post_adjustment` (gemello non-cash di post_inflow/out):
  rettifica + delta-colonna in UN atto, causale fuori-enum → ValueError, DEC-2 round 2dp, DEC-1 **nessun
  clamp**. NON tocca `movimenti_cassa` (lo storno nel mastro cassa riaprirebbe la superficie ADR-019).
- `f0b8672` **G9.2b.3** — backfill idempotente al boot (`schema_sync._backfill_quota_stornata_rettifiche`,
  gemello di `_fix_cross_db_fk`): quota legacy >0 senza rettifiche → 1 riga `BACKFILL_LEGACY`.
  **🔶 Checkpoint superato sul clone del crm.db dev** (backup API read-only): 38 contratti → 1 riga attesa
  (+250, contratto 32, TERMINAZIONE_RIMBORSO), re-run no-op, ancora verde su tutti.
- `d0c01f8` **G9.2b.4** — wiring 3 write-site: terminate→`+Δ STORNO_TERMINAZIONE`, reopen→`−quota
  REVERSAL_REOPEN` (niente righe-zero), incassa differito→`−importo REVERSAL_INCASSO_DIFFERITO` col clamp
  `max(·,0)` RITIRATO (DEC-1). `residuo()` byte-identico. Zero scritture manuali fuori dalla penna.

**Learning (2 scoperte dal codice, non dal design):**
1. **Ordine del backfill in `sync_schema`**: lo SPEC lo collocava dopo `_drop_stale_catalog_tables`, ma il
   test legacy-DB esistente ha rivelato che su un DB pre-G7.0 la colonna `quota_stornata` nasce dalla
   column-sync (ALTER) → il backfill DEVE seguirla o crasha il boot con "no such column". Il test suite
   come rete anche sul codice di migrazione, non solo sul dominio.
2. **Il crm.db dev reale aveva già la tabella** (0 righe) al momento del checkpoint: il backend dev in
   auto-reload aveva bootato `create_db_and_tables` appena creato il modello. Innocuo per costruzione
   (backfill idempotente al prossimo boot) — ma conferma che ogni modello nuovo tocca i DB reali PRIMA
   del commit se un dev server gira: il design additivo-idempotente non è un lusso.

**Verifica.** Suite **769 passed / 0 xfailed** (baseline 755 + 14: 5 penna, 4 backfill, 5 wiring incl.
sequenze composte AC-G92-4 terminate→incassa→reopen e terminate→reopen→ri-terminate), `check-all.sh` verde
a ogni commit. **⏭️ Prossimo: G9.2b Stage 2** (estendere `project_columns_from_ledger` con `quota_stornata
= Σ rettifiche` + terza ancora log-only nel sensore; NB `test_lifecycle_audit.py:212/238` scrive quota a
mano → log atteso, non sorpresa). Poi G9.3 TransitionExecutor.

---
## 2026-07-02 (sessione 2) — G9.2b Stage 2: terza ancora nel sensore (CHIUDE G9.2) + verifier nel processo

**Stage 2 (`8a6902c`):** `project_columns_from_ledger` ritorna anche `stornato = Σ importo[rettifiche_contratto]`
(terza proiezione dopo versato/rimborsato) e il sensore `invariant_gate` osserva l'**ancora ledger-storno**
`quota_stornata == Σ rettifiche` (log-only, gate duro in G9.4) accanto a quella del versato (G9.2a). Sui path
via terza penna è vera per costruzione → una violazione segnala un write fuori-penna o drift legacy. Il caveat
previsto in SPEC §B.6 (`test_lifecycle_audit` scrive quota a mano → log atteso) confermato innocuo. +2 test.
Suite full **771 passed / 0 xfailed**. **🏁 G9.2 (a+b Stage 1+2) CHIUSO — le 3 colonne cassa/storno del
contratto sono ora proiezioni verificabili e osservate dei 2 ledger.**

**Processo consolidato (novità di metodo):** prima del push di Stage 1 è stato lanciato l'agente
**`financial-invariant-verifier`** (read-only, adversariale) sul diff `b012bb8..0fa1b15` → verdetto **PASS**:
V1 firewall `contract_state.py`/`contract_settlement.py` fuori dal diff · V2 harness I1/I4/I5/I6 integro ·
V3 zero coverage-gap (ogni simbolo money-mutating ha un oracolo collectable che lo esercita) · V4 i 4
grep-guard ADR-016/017/018/019 vivi e non aggirati · V5 ancora-sensore classificata PIANIFICATO-E-TRACCIATO
(ora chiusa da Stage 2). 194 test money-band ri-eseguiti indipendentemente. **Il loop di consegna del filone
finanziario è ora: implementazione → full suite → verifier adversariale → push.**

---
## 2026-07-02 (sessione 3) — G9.3 TransitionExecutor + FSM + auto-close unificato (CHIUDE G9.3)

Il gate più strutturale di G9: il write-model delle transizioni contrattuali ha ora UNA casa. Metodo
consolidato: design-record PRIMA del codice (**Appendice C** di SPEC_G9, `757091b` — decisioni D-C1..D-C7
code-grounded), poi strangler-fig una transizione alla volta. **4 commit, branch verde a ognuno:**

- `757091b` **design** — Appendice C implementation-ready. Decisioni chiave: comando = schema Pydantic
  esistente (no DTO parallelo) · bouncer nel router, guard di dominio nell'executor · HTTPException resta
  (conversione = G9.4) · sensore PRE-commit (il gate G9.4 deve poter fare ROLLBACK — l'idea post-commit di
  A.1-ter valeva per l'osservazione pura) · `_audit` importabile da un service senza cicli (routers/__init__
  vuoto, debito di layering annotato) · direzioni per-caller sull'auto-close (corner 1-cent-unpay).
- `44d0494` **G9.3a** — `api/services/financial/transitions.py`: `execute_terminate` (~247 righe rilocate
  quasi-verbatim) + i 4 helper settlement (pubblici: li consuma anche `settlement_preview`, che resta nel
  router). Router terminate → 19 righe.
- `43fa250` **G9.3b** — `execute_reopen` (~190 righe) + `reconcile_rate_plan` pubblico (lo consumano
  execute_reopen E incassa_residuo: la dipendenza si inverte, router→service). Router reopen → 18 righe.
- `6a2aaf9` **G9.3c/d** — **FSM esplicita** di `(chiuso, motivo_chiusura)` nel docstring del modulo
  (tabella stati×transizioni, design-record eseguibile) + `AUTO_REOPEN_ALLOWLIST`/`puo_auto_riaprire`
  (la reopen-allowlist G7.2 vive in UN posto) + **`sync_contract_chiuso` UNIFICATO**: le 3 copie
  (agenda._sync bidirezionale · pay_rate E-auto inline solo-close · unpay_rate inline solo-reopen)
  convergono su UN percorso logico con **direzioni per-caller** (D-C6: la condizione è una sola, la
  direzione permessa è policy del trigger — un sync bidirezionale su unpay potrebbe CHIUDERE in un corner
  patologico, comportamento nuovo vietato dal contratto behavior-preserving). Audit per-path preservato
  (completamento / riapertura_pagamento / riapertura_crediti). +6 test AC-G93-3/FSM/direzioni.

**AC verificati:** AC-G93-1 router 19/18 righe (≤~40) · AC-G93-2 suite verde al primo passaggio a ogni
commit (unico ritocco test: lo spy del sensore segue il corpo nel nuovo modulo — target monkeypatch,
non comportamento) · AC-G93-3 payment-driven e credit-driven → stesso stato terminale (test) · AC-G93-4
sensore = post-condizione di ogni executor (spy test).

**Verifica.** Suite full **777 passed / 0 xfailed** (771 + 6), check-all verde a ogni commit.
**⏭️ Prossimo: G9.4** (invarianti → 409+rollback dietro flag `INVARIANT_ENFORCEMENT` + ritiro dei 4
grep-guard → test semantici). Poi G9.5 Hypothesis, G9.6 Money (differito).

---
### 2026-07-02 (sessione 3, addendum) — verifier G9.3: guard ADR-019 vacuo trovato e chiuso

Il **verifier adversariale** sul diff G9.3 ha classificato la rilocazione **byte-identica** (V1 diff
meccanico corpo-per-corpo, 176/0 fascia money) MA ha trovato l'unico difetto reale: il **grep-guard
ADR-019 era diventato VACUO** — estraeva il corpo di reopen da `contracts.py`, dove dopo G9.3b vive solo
il delegatore → passava perché il codice sorvegliato era sparito dal file greppato (falso PASS, la classe
di errore peggiore per un guard). **Fix `e748151`**: ripuntato su `execute_reopen` in `transitions.py` +
**check anti-vacuità** (il corpo estratto DEVE contenere il marker `Cassa IMMUTABILE`, altrimenti FAIL
esplicito). **Fix gemello sul residuo LOW**: ADR-016 era l'unico altro positive-fail senza anti-vacuità →
stesso presidio (`def compute_settlement` richiesto nel file). Follow-up verifier: **PASS — MONEY AXIS
PRESERVED**. **Lezione (classe generale):** un guard *positive-fail* (fallisce se un pattern APPARE) va
sempre accoppiato a un check di **presenza** del codice sorvegliato — ogni rilocazione futura che svuota
il file greppato deve rompere il guard, non zittirlo. È la conferma empirica del razionale G9.4 (grep-guard
testuali → test semantici sul simbolo).

---
## 2026-07-03 — G7.8-bis Late Cancel & No Show (Step 0 prep-SSoT + Step 1 stati-penale)

Dalle 2 spec del founder (ROADMAP_FINANCIAL_UPGRADES + SPEC_LATE_CANCEL_NO_SHOW, prodotte con AI
esterna): analisi bridge code-grounded → 2 correzioni sostanziali all'inventario (§3.2 puntava a
`contract_settlement.py` che è PURO — il conteggio vive in `transitions.py`; l'inventario taceva i
21 siti denylist `!= 'Cancellato'` la cui semantica cambia in silenzio con stati nuovi) → **sequenza
ratificata Step 0 → Step 1** invece dell'esecuzione diretta della spec.

- **`4944a49` Step 0 (G7.8bis-prep, behavior-preserving):** predicato occupazione estratto a SSoT
  `contract_state.STATI_OCCUPAZIONE_CREDITO`; TUTTI i 17 siti (12 ORM + 5 raw-SQL via bindparam
  expanding) consumano il simbolo. `tests/test_occupazione_ssot.py` = **test semantico che vieta i
  literal** (enforcement, non enumerazione — il gemello G9.4-style del grep-guard ADR-017). Censimento
  denylist in SPEC §6.2 (decisione: NON cambiano — un No_Show è un appuntamento reale della relazione).
  Governance: **ADR-017 Addendum I** (D-STATI-PENALE / D-SSOT-PREDICATO / D-CONTEGGI-SEPARATI /
  D-DENYLIST-INTATTE / D-PENALE-PROVISIONAL). Suite 780.
- **`db322eb` Step 1 (G7.8-bis):** i 2 stati-penale entrano nel SSoT (+2 stati in 1 frozenset = il
  dividendo dello Step 0) su 3 assi: occupano il credito · contabilizzano nel conguaglio
  (`count_sedute_penali`, audit con conteggi SEPARATI vere/penali/contabilizzate) · non sono
  performance. **Nuovo asse dichiarato `STATI_OCCUPAZIONE_SLOT`**: le penali liberano lo slot
  calendario (D-CALENDAR-OVERLAP) — l'overlap-check DIVERGE dall'asse credito (prima coincidevano;
  senza il censimento Step 0, i No_Show avrebbero bloccato slot in silenzio). Suite **787**.

**2 scoperte dal codice:** (1) `_check_overlap` consumava lo stesso predicato dell'occupazione — la
divergenza degli assi andava DICHIARATA con una seconda costante, non ereditata; (2) il dettaglio
contratto ri-implementava l'occupazione **sommando chiavi del breakdown a mano**
(`programmate + completate`) — un sito semantico invisibile al literal-grep, ora derivato dal SSoT.
Lezione: l'enforcement testuale (grep/literal-test) copre i re-inline sintattici, NON le
re-implementazioni semantiche — quelle le trova solo la lettura del consumer.

**⏭️ Residui:** display pieno penali nel FE (badge/timeline) → G8.4 · esigibilità della penale nel
recesso = punto tributarista (D-PENALE-PROVISIONAL, come pro_sedute) · FDM/TASSONOMIA da aggiornare
con l'asse a 6 stati (prossima sessione docs).

---
## 2026-07-03 (sessione 2) — Riordino strutturale docs/ + IL metodo (ciclo di vita dei documenti)

**Trigger founder:** «stiamo accumulando spec in un'unica cartella che saturerà; a volte generiamo ADR,
altre spec che non archiviamo mai; UPGRADE_LOG mai più aggiornato; gli agenti lavorano con contesto
sbagliato. Un senior si fermerebbe, stabilirebbe IL metodo, farebbe un audit e ordine.» Audit con
`docs-code-drift-auditor` (read-only): 8 HIGH (INDEX che descrive G9 "da implementare" a G9.3 chiuso,
SPEC_RINVIO senza riga Stato e col predicato 2-stati superato, CLAUDE.md con 28 tabelle/361 test/conteggi
file stale, api/CLAUDE.md col predicato occupazione vecchio) + 15 link BLOCCANTI mappati + conferma che
`docs/upgrades/` è morto da marzo.

**IL metodo (AGENTS.md §7, ratificato): la POSIZIONE è lo STATO.**
`docs/adr/` = la legge (immortale, Addendum) · `docs/technical/` = SSoT evergreen (zero spec) ·
**`docs/specs/` = NUOVA, solo spec aperte** (`ls docs/specs/` = work-queue) · `docs/archive/` = storia,
mai contesto · BUILD_LOG = log unico (UPGRADE_LOG dismesso formalmente). Definition of Done del gate
estesa: … → verifier → **fold-back docs (Stato+INDEX+BUILD_LOG+archiviazione) → push**.

**Eseguito:** 3 spec vive → `docs/specs/` (G9, G8.4, VOCABOLARIO) · 8 spec implementate + IMPL_PLAN →
`archive/specs/` · 2 AUDIT + ROADMAP (con header di esito: §1.2/§1.3 già shippate) → `archive/` ·
chirurgia Stato su SPEC_RINVIO ("IMPLEMENTATA, SUPERATA da G7.8-bis 4-stati") · 15 link ripuntati
(incl. `api/services/financial/__init__.py` e il docstring dell'harness) · INDEX riscritto (sezione
`specs/` con work-queue + backlog esplicito: G8.2, G9.4-9.6, wallet append-only, forecast ponderato,
punto tributarista, FDM 6-stati) · CLAUDE.md corretto (29 tabelle, ~790 test, contratto di contesto) ·
api/CLAUDE.md predicato occupazione → simbolo SSoT · adr/README + Addendum ADR-017.

**Guard ciclo-di-vita in `check-all.sh`** (le regole vivono nei check, non nella disciplina): FAIL se
SPEC_*/IMPL_PLAN_* in technical/ o spec IMPLEMENTATA in specs/. **Il liveness-test del guard ha trovato
un bug nel guard stesso**: `ls glob1 glob2` torna nonzero se UN glob non matcha → check cieco; fix con
`compgen -G`. Lezione (terza della serie guard): OGNI guard nuovo va provato sul caso FAIL, non solo sul
caso PASS — un guard mai visto fallire non è ancora un guard.

---
## 2026-07-04 — G7.8-ter Temporal fence (ADR-023): la storia contabilizzata di una liquidazione è immutabile

**Trigger founder (2026-07-03):** «il fattore tempo sulle modifiche ai crediti — riaperture/rinvii/
cancellazioni su contratti terminati riapre l'aspetto finanziario; se non protetto genera mismatch
irreversibili». Prima della spec: **ricerca competitor su fonti ufficiali** (3 agenti — Mindbody,
WellnessLiving, Zen Planner/Daxko, Glofox, Vagaro + QuickBooks/Xero/Stripe/Trainerize/PushPress;
citazioni durevoli in `docs/archive/RICERCA_COMPETITOR_TEMPORAL_FENCE_2026-07-03.md`) → **5 leggi
convergenti** (presenze libere/denaro no · mai ricalcolo incrociato automatico · la liquidazione
CONGELA · correzione forward-only · la grazia sta PRIMA del denaro) + il pattern del varco maturo:
esplicito, role-gated, auditato (QBO Exceptions-report). Perimetro code-grounded: il denaro era già
tutto fenced (H1/M2/B-ter); il buco era SOLO `update_event.stato`/`delete_event`.

**Opzione C ratificata → `bca28e0` governance** (ADR-023 accepted + SPEC in docs/specs/ + INDEX) →
**`292949f` implementazione**: terzo asse SSoT `STATI_SERVIZIO_CONTABILIZZATO` (= Completato+penali,
la base di compute_settlement) + helper unico `_assert_storia_liquidata_intatta` + Bouncer 5 su
update_event + guard su delete_event (409 con microcopy che indirizza a `POST /reopen`). Raffinamento
chiave emerso dal codice: il terminate NON tocca gli eventi futuri → la **pulizia dei `Programmato`
orfani resta libera** (D-TF-PULIZIA) — il fence protegge la BASE, non l'agenda. Legacy NULL dentro,
COMPLETAMENTO fuori (auto-reopen simmetrico invariato). +10 test AC-TF 1:1 con la SPEC (incl. varco:
reopen → correggi → ri-termina ricalcola sul corretto). Suite full **797 passed / 0 xfailed**.

**Il quadro temporale del dominio è ora completo:** cassa append-only (ADR-019) · denaro fenced
(G7.7) · storia contabilizzata fenced (ADR-023) · varco unico esplicito e auditato (`reopen`).

---
## 2026-07-05 — G9.4 (enforcement + test semantici) + G9.4-bis (read-model cassa): il gemello di lettura

Sequenza affidata dalla governance del founder (`994c63d`: ADR-022 Addendum II + SPEC_G9.4-BIS +
censimento assi semantici). **9 commit, branch verde a ognuno:**

**G9.4-bis.0** (`85deb12`) quick-win: F3 storno→costante (6 siti, 2 in SCRITTURA — la penna delle
spese ora esiste) · F4 asse A9 stati credito/wallet → `STATO_CREDITO_*` (~23 siti, 1 raw-SQL
parametrizzato) · F8 `signed_importo_case` unico in ledger.py.

**G9.4** (`c3c5702`+`fd297e5`): il sensore G9.0 diventa GATE — I1/I4 → **409+rollback** dietro flag
`INVARIANT_ENFORCEMENT` (raise in dev/CI/test, log in prod: la suite che passa in modalità raise È
la telemetria-CI-pulita di AC-G94-4, provata a ogni run) · i 4 grep-guard ADR-016/017/018/019
RITIRATI da check-all, sostituiti da `test_semantic_guards.py` (ADR-019 end-to-end immune alla
rilocazione — fine dell'era grep, 3 lezioni-guard consolidate).

**G9.4-bis.1-4**: `ClasseContabile` (6 classi) + `classify_cash_movement` fail-loud, convalidata sul
crm.db reale (218/218, zero celle violate) (`99e5dd9`) · migrazione superfici I1/I2/I4/I5/I6 al piano
dei conti (`3b788fa`) · trasparenza D-NESSUN-NETTO-NUDO: bucket in /stats, sub-label card Entrate,
/balance dichiara la cassa-pura — **AC-RM-6: il −140,42 dell'INC è ora spiegabile dalla response da
sola** (`09d701e`) · gemelli esaustività-alla-nascita + no-re-inline (`cd4046f`+`6e650a1`).

**2 SCOPERTE dalla migrazione:** (1) **il censimento aveva ragione sulle micro-varianti**: trend e
stats già DIVERGEVANO sulla cella "ENTRATA manuale etichettata STORNO senza id_spesa" (trend escludeva
per stringa, stats contava per struttura) — unificata per D-CLASSIFY ("la classe la dà la struttura")
+ chiuso il buco in scrittura (write-guard 422 sulle categorie riservate nel movimento manuale);
(2) **la git-bash di questo ambiente interpreta gli escape negli heredoc anche quotati** — causa-radice
di tutti i fallimenti heredoc della settimana e di un test scritto corrotto (scoperto POST-commit:
il pre-commit non esegue pytest) → regola a memoria: contenuti con escape SOLO via Write tool.

**Coda: full-suite + verifier (2 commit).** Il full-suite ha catturato l'UNICO test con assunzione
pre-ADR-019 residua: `test_unpay_dopo_terminate_rifiutato_409` asseriva "dopo reopen la revoca torna
possibile" (vero con l'inverso-esatto che cancellava il rimborso; falso col reopen non-distruttivo:
la cassa preservata fa da FLOOR — unpay di 500 con rimborsato 800 = I4 netto −300, che il sensore
loggava già SU QUEL TEST). Aggiornato a 409+rollback (`aafba2d`) → suite **829/829**. Verifier sul
blocco `b54ab67..HEAD`: **MONEY AXIS PRESERVED** — 0 regressioni, 4 cambi osservabili tutti sanzionati
ADR-022 e coperti (gate 409 · write-guard 422 · trend per-classe · floor unpay post-reopen), oracoli
puri intoccati. Finding F5 (MEDIUM) chiuso subito: il ritiro dei grep spostava l'enforcement sulla
disciplina (check-all non esegue pytest, CI assente) → fascia `test_semantic_guards.py` (~6s) nel
gate obbligatorio (`b5ce30e`). Flag operativi per il founder: **OD-1** convalidare `classify` read-only
sul crm.db di Alessio PRIMA del suo upgrade (fail-loud su stats/trend = blast radius endpoint intero);
**OD-2** il gate è volutamente `log` in compiled — accensione `INVARIANT_ENFORCEMENT=raise` a
telemetria di campo pulita (strumenta-poi-imponi, decisione founder).

---

## 2026-07-05 — G9.5: la macchina a stati Hypothesis (il gemello generativo dell'harness)

`tests/test_financial_state_machine.py`: dove l'harness enumera 12 path manuali, la macchina esplora
**sequenze** (30 esempi × ≤12 mosse): 10 rule tentano transizioni via API (rifiuto 4xx del dominio =
no-op esplorato, 5xx = bug), `@invariant` verifica I1-I6 dopo OGNI mossa riusando `_invariants`
dell'harness. Canary espliciti (AC-G95-4): Bug-1 eroga→reopen + floor-unpay post-reopen, come replay
delle stesse rule. Test negativo AC-G95-1: drift I4 iniettato a mano fa scattare l'oracolo (non è vacuo).
Dipendenza `hypothesis` solo-test (pyproject; mai importata da `api/` → fuori dal bundle per costruzione).

**2 LEZIONI dalla liveness (misurata con sonda usa-e-getta, non presunta):** (1) **`derandomize=True`
NON è "seed pinnato"** — replaya UNA generazione fissa minimale che non selezionava MAI pay/unpay;
il determinismo CI corretto è `@seed(SM_SEED)` sulla classe (supporto ufficiale stateful) +
`database=None` (2 run → esiti byte-identici, provato con diff). (2) **senza cap sui create il bundle
si diluisce**: 27% delle mosse creava contratti nuovi e reopen/eroga_wallet non venivano MAI esercitati
(0/43); `precondition(len(tracked) < 3)` ha portato ogni famiglia di rule ad almeno un'accettazione.
La morale è la stessa dei grep-guard G9.3: un presidio che "gira verde" senza prova di vitalità può
essere vuoto — la sonda è il gemello di liveness della macchina stessa.

**Calibrazione di processo (founder, 2026-07-05):** per un diff **test-only o docs-only** la full
suite è sproporzionata (non c'è codice che possa regredire) → fascia mirata + `--collect-only`
sull'intera suite. La full resta obbligatoria per ogni diff che tocca `api/` sui money-path.
Eccezione una-tantum qui: G9.5 installa un plugin pytest nuovo (hypothesis) attivo sull'intera
suite = cambiamento ambientale, validato con una full singola alla nascita della dipendenza.
**Stessa logica per il verifier:** niente verifier su diff che solo AGGIUNGONO test/docs (V2 "oracoli
intoccati" è vero per costruzione dal diff); resta obbligatorio se il diff MODIFICA/elimina oracoli
money esistenti — un test-only può danneggiare l'asse denaro accecandolo (caso `aafba2d`).

---

## 2026-07-06 — G8.4 ripresa: ri-grounding della spec + ratifica D-1/D-2 (governance docs-only)

Ripresa del filone finanziario su G8.4 (trasparenza FE). Il founder ha fermato le decisioni D-1/D-2 con la
domanda giusta: la spec è del 2026-06-30, scritta DURANTE G7-G9 — prima di decidere, riverificare il backend
e guardare i competitor. La verifica gli ha dato ragione su entrambi i fronti.

**Ri-grounding sul codice vivo (2 agenti read-only):** F1 confermata ma perimetro corretto — i ricalcoli veri
sono Hero:42-45, ContractsTable:181-183, HistoryTab:81-90; `PaymentPlanTab` NON viola F1 (l'audit originale
lo accusava a torto: legge già i campi SSoT); gli import inline in `[id]/page.tsx` non esistono più;
`ContractsTable` (370 LOC) entra in F5. Il backend è pronto: manca SOLO `saldo_progressivo` (additivo);
`sedute_penali` è già sul preview (G7.8-bis) ma non sincronizzato in `types/api.ts`. F1.d cambia forma:
test semantico in `test_semantic_guards.py`, non grep (allineato al ritiro G9.4-b).

**Ricerca competitor (11 vendor, fonti ufficiali, citazioni):**
`docs/archive/RICERCA_COMPETITOR_TRASPARENZA_FINANZIARIA_2026-07-06.md` — 6 leggi convergenti L1-L6.
Le due che decidono: **L1** il ledger si chiama "Balance"/"Running Balance" (QBO/Xero/WellnessLiving/Square/
Stripe), mai "netto" → D-2 confermata; **L2** il netto non è mai nudo (Stripe raggruppa per refunds BY
DEFAULT; Xero/QBO credit note = riga visibile) → **D-1 EMENDATA**: il breakdown «lordo − rimborsi» esce dai
collassabili e diventa sub-label always-visible (pattern G9.4-bis.3 già shippato in cassa).

**Ratifiche founder (2026-07-06):** D-2 = colonna «Saldo» per riga + footer «Saldo movimenti del contratto»
→ **ADR-019 Addendum IV** (D-LEDGER-SALDO: i due netti, netto-POSIZIONE vs saldo-LEDGER). D-1 = lista §F2
con emendamento L2. Spec aggiornata (§0-bis ri-grounding, F1.c/F1.d/F2/F3.e-f/F5, AC-G84-7/8): entrano
formalmente display `sedute_penali` (F3.e) e nota-abbuono obbligatoria FE (F3.f) — i residui già assegnati
a G8.4 da INDEX. Allineati INDEX (anche drift G9.5 chiuso) e adr/README.

**Lezione di metodo:** una spec scritta durante un ciclo lungo di implementazione va ri-groundata PRIMA di
eseguirla — qui il ri-grounding ha tolto un file dal perimetro F1 (falsa accusa), aggiunto un file a F5
(vero scoperto), cambiato la forma del guard (grep→test semantico) e ribaltato una decisione UX (L2).
Il costo è un giro di agenti read-only; l'alternativa era implementare contro coordinate morte.

**⏭️ Prossimo: fetta-RIGORE** (F1 consumo `netto_incassato` + `saldo_progressivo` server-side + guard
semantico FE-no-money-math + F5 split <300). Poi fetta-UX-presentazionale (F2+F6), fetta-comportamentale
(F3.a-f). G8.5 (goodwill): governance da aprire prima della chiusura G8.4.

---

## 2026-07-06 (stessa giornata) — G8.4 fetta-RIGORE (F1+F5) COMPLETATA

**F1 (`5086045`).** Backend: `ContractMovementItem.saldo_progressivo` calcolato in `get_contract`
(ENTRATA +, USCITA −, round 2dp per riga, ordine `data_effettiva,id`) — ADR-019 Add. IV. FE: hero e
riga-lista consumano `contract.netto_incassato` (ricalcoli inline eliminati); lo Storico legge il saldo
dal wire, footer «Saldo movimenti del contratto» + «Saldo» per riga (D-2). 3 test dedicati incl. la
divergenza legittima netto-POSIZIONE vs saldo-LEDGER post-reopen con wallet riassorbito (AC-G84-2:
800 vs 550, delta = esattamente l'erogato riassorbito). **Suite full 836.**

**F1.d — il guard è nato e ha subito lavorato due volte.** Il gemello semantico FE-no-money-math
(`test_semantic_guards.py`) alla prima esecuzione ha pescato **3 siti `.reduce(…importo)` fuori dal
censimento della spec** → esaminati uno a uno: tutti legittimi con dottrina propria (2 aggregati-di-vista
row-derived [rinnovi-incassi KPI worklist, LedgerColumn footer] + 1 Σ-selezione input-local
[RecurringExpensesTab]) → allowlist esplicita motivata, mai in silenzio. Poi il gemello anti-vacuità
ha FALLITO quando F5.b ha rilocato il consumo di `netto_incassato` da ContractsTable a ContractRow —
esattamente il failure-mode per cui esiste (lezione G9.3): ripuntato, vitalità provata sul campo.

**F5 (3 commit, tutti behavior-preserving, build verde a ognuno).** `4f2d07c` F5.a: `[id]/page.tsx`
511→280 (RenewalChainSection/ContractSessioniTab/ContractDettagliTab estratti) + **EventsTable
condivisa** profilo↔contratto che chiude anche un drift task #14 (il dettaglio contratto renderizzava
`e.stato` grezzo → underscore a video sui penali). `ab38c90` F5.b: TerminateContractDialog 357→192
(figli controllati `terminate/*`: SettlementBreakdown/ClientRefundBranch/TrainerCreditBranch — stato e
gating SOLO nel container) + ContractsTable 370→166 (riga → ContractRow). `1978572` F5.c (delegato ad
agente con vincoli, verificato): PaymentPlanTab 897→198 in `payment-plan/*` (6 moduli; `usePayRate`
resta per-card: hoistarlo condividerebbe `isPending` tra card = cambio comportamento).

**Scoperte del giro:** (1) **F3.f era GIÀ in codice** — il gating richiede la nota su RINUNCIA_ESPRESSA
(AC-G84-8 già vero); (2) il ri-grounding mattutino sbagliava sugli import inline di `[id]/page.tsx`
(esistevano ancora, l'audit originale aveva ragione — corretta la nota §0-bis: anche il ri-grounding
va verificato sul file).

**Gate F5 (AC-G84-6): verifica Playwright LIVE su crm.db reale** (dev 3001/8001, SOLO azioni read-only,
zero submit): lista contratti (netto SSoT + sub-label «lordo X · −Y» sui contratti con rimborso, badge
2 assi, segnale rate scadute) · dettaglio 39 (hero netto 240,75 con sub-label; breakdown; rate card con
storico) · **tab Storico: «Saldo» per riga dal backend (75→176,25→277,50→378,75→240,75 col rimborso
−138) + footer «Saldo movimenti del contratto»** · dialog Termina su ATTIVO (preview backend, prefill
rimborso ramo-cliente, chiuso con Annulla). Server spenti a fine verifica.

**⏭️ Prossimo: fetta-UX-presentazionale (F2+F6)** — disclosure con lista D-1 emendata + token-map F6
(neutralizzare violet/blue/indigo decorativi) — poi **fetta-comportamentale (F3.a/c/d/e)** e apertura
governance **G8.5** (goodwill) prima della chiusura G8.4.

---

## 2026-07-07 — G8.4 fetta-UX-presentazionale (F2+F6) COMPLETATA (`0b80bc8`)

**F2 (D-DISCLOSURE, lista D-1 ratificata):** hero con toggle «Mostra dettaglio» — dietro il toggle
SOLO gli informativi (Acconto · Da Rateizzare quando il piano è coperto · riga Crediti Sedute);
sempre visibili i segnali (Residuo + conteggio scadute · banner amber prenotate-non-erogate ·
Da Rateizzare quando il piano NON copre · sub-label «lordo X · −Y» sul netto, D-1 emendata).
Scelta di layout: griglia UNICA che fluisce (collassata = Valore·Netto·Rate·Residuo, 4 card;
espansa = identica al layout storico 2×3 + riga crediti) — niente row vuote né salti di card.
Storico: righe ledger collassabili alla **coda dei 6 più recenti** (il running balance della prima
riga visibile include già la storia nascosta — pattern QBO "balance valido solo cronologico");
footer prova-a-vista SEMPRE.

**F6 (D-COLORE):** neutralizzati a zinc i 5 tint decorativi (Valore violet · Acconto/Rate
Pagate/Programmate blue · Crediti Totali indigo); restano SOLO i colori-valenza
(emerald/amber/red + emerald su Completate = erogato).

**AC-G84-5 = 3 render-test vitest** (`__tests__/contracts/financial-hero-disclosure.test.tsx`,
primo render-test testing-library del repo): segnali presenti senza interazione · dettaglio
nascosto/rivelato dal toggle · Da Rateizzare always-visible a piano scoperto. Vitest **85/85**,
next build verde, guard semantici 6/6, verifica visiva LIVE su crm.db reale (contratto 39, dark).
Nota operativa: il dev server ucciso brusco lascia il lock `frontend/.next/dev/lock` → rimuoverlo
prima del restart.

**⏭️ Prossimo: fetta-comportamentale (F3.a/c/d/e)** — raccomandazione solo-visiva ramo trainer +
advisory `azione_consigliata` (opzionale) + radiogroup a11y + display `sedute_penali` (sync
types/api.ts) — poi apertura governance **G8.5** prima della chiusura G8.4.

---

## 2026-07-07 (stessa giornata) — G8.4 fetta-comportamentale (F3) COMPLETATA (`58c01ea`)

**F3.c (backend, additivo):** `ContractSettlementPreview.azione_consigliata` — advisory sul ramo
CREDITO_TRAINER (= `INCASSA_ORA`, l'opzione che tutela il trainer; MAI la rinuncia; il gate 422
D-SCELTA resta intatto). Il FE legge il suggerimento dal wire invece di hardcodarlo (SSoT anche
per la raccomandazione). +2 test backend, **suite full 839**.

**F3.a/F3.d (FE):** badge «Consigliato» + ring emerald sul bottone suggerito, SOLO visivo — zero
pre-selezione (`azione=''`, `canSubmit=false` finché non si clicca). Gruppo scelta accessibile:
`role=group` + `aria-pressed` = stato REALE; il selezionato ha il marcatore non-cromatico (Check).
**Decisione di dettaglio:** il check segna la SELEZIONE, non il suggerimento — la spec F3.a citava
"icona check sul bottone suggerito", ma un check su un bottone non scelto sembrerebbe una scelta
già fatta (anti-pattern a11y); il suggerito si distingue con badge+ring, il selezionato con
variant filled+check. Annotato nell'header del componente.

**F3.e:** `sedute_penali` sincronizzato in `types/api.ts` (era il gap type-sync del ri-grounding)
e mostrato nel breakdown come riga SEPARATA amber «Sedute penali (contabilizzate)» — mai sommate
alle erogate a video (coerente con l'audit conteggi separati di G7.8-bis).

**Test AC-G84-4/7/8:** 6 vitest nuovi (`terminate-dialog-choice.test.tsx`) col dialog INTERO a
hook mockati (`vi.mock` di useContracts): nessun `aria-pressed` all'apertura + submit disabled ·
badge sul suggerito e mai sulla rinuncia · la scelta reale abilita · rinuncia senza nota resta
bloccata (F3.f) · penali visibili/assenti. Vitest **91/91**, build verde.

**🏁 G8.4: TUTTE LE FETTE CHIUSE (F1+F5 · F2+F6 · F3).** Per la DoD §8 resta SOLO il punto (5):
**apertura governance G8.5** (ADR goodwill proposed + spec, decisioni founder i-iv da chiudere:
destinazione cassa/wallet · base importo · categoria dedicata vs riuso · inversione al reopen).
Il workaround amber «Riapri e poi Termina» resta per design finché G8.5 non shippa.

---

## 2026-07-07 (sera) — Audit eventi orfani + ADR-024 «Semantica per-classe» + apertura G9.7

**Trigger founder (caso reale, contratto 39):** 2 sedute Completato create dall'agenda a contratto
CHIUSO → nate con `id_contratto=NULL` in totale silenzio (auto-assign filtra i chiusi, 201 muto);
il reopen riconcilia rate/cassa/receivable/wallet ma NON gli eventi → orfane in limbo PERMANENTE
(il re-parenting è vietato dal fence G7.8-ter: **deadlock da due protezioni giuste**, il finding
strutturale della giornata). E a video l'occupazione non torna: 5+2 penali = 7/12 → residui 5, ma
l'hero mostra solo «0 · 5 · 5» — 2 crediti spariti (i campi `sedute_penali`/`sedute_rinviate`
erano GIÀ sul wire, mai renderizzati).

**Audit READ-ONLY depositato** (`operations/AUDIT_CREDITI_EVENTI_ORFANI_2026-07-07.md`, `04b7e7f`):
forensics sqlite mode=ro sul crm.db reale + 2 censimenti agente → **13 finding** (B1-B8 scrittura,
D1-D5 display), founder ne aveva stimati «minimo 10». Le 2 orfane (eventi 640/641) sono le UNICHE
del DB: fenomeno nuovo, contenuto. Tra i finding anche D4: `DeleteContractDialog` RICALCOLA
`crediti_residui` inline — la violazione R-SSOT-FE sull'asse che il guard non copre.

**Riflessione di metodo (ratificata dal founder):** nessun finding è una classe nuova — fail-silent
in scrittura (3ª occorrenza), derivato nudo (2ª), transizione che non enumera i satelliti, SSoT
violato fuori perimetro guard. Le leggi esistono ma applicate PER-ASSE (cassa), non PER-CLASSE.
«Chi non anticipa insegue» → **ADR-024 accepted** (D-LEGGI-PER-CLASSE / D-MAI-SILENZIO-IN-SCRITTURA /
D-DERIVATO-MAI-NUDO / D-PERIMETRO-TRANSIZIONI / D-RECUPERO-ESPLICITO / D-BIRTH-AUDITOR /
D-GENERATIVO-PER-ASSE) + **SPEC_G9.7** (gate 0-5: matrice assi×regole → mai-silenzio write-path →
recupero esplicito orfani [incl. 640/641 via endpoint, MAI a mano nel DB] → occupazione mai nuda →
guard di classe + perimetro transizioni → birth-auditor + Hypothesis estesa con I-EVENTI).
I 13 finding = gli AC del blocco, non 13 rincorse.

**⏭️ Prossimo: G9.7.0 (matrice) → G9.7.1-2 (i bug del founder) → G9.7.3 → G9.7.4-5.**
G8.5 (goodwill) resta in coda dopo G9.7.

---

## 2026-07-07 (notte) → 2026-07-08 — G9.7.0-1 · filone ADR-025 (fondamenta → ratifica → apertura blocco P)

**G9.7.0 FATTO** (`dbac53f`, docs-only): nasce `docs/technical/MATRICE_ASSI_SEMANTICI.md` — 7 assi
di stato × 4 regole del metodo + derivati-a-video + composizione protezioni (SSoT evergreen,
ADR-024 D-LEGGI-PER-CLASSE). **G9.7.1 codice FATTO** (`6cdbfb9`): mai-silenzio sul write-path
eventi — B4 pre-warning in `EventForm` su `contratti_attivi === 0` («la seduta nascerà SENZA
contratto») + B5 toast dedicato sul 201 con `id_contratto == null`. In coda al gate: vitest
AC-G97-1 + verifica LIVE.

**Seconda cattura founder (2026-07-07 sera):** «(2 crediti)» nel dropdown da contratto CHIUSO
accanto al warning «nessun contratto attivo» = PANICO — il pre-warning B4 passava proprio perché
`crediti_residui` client-level è l'unico campo enrichment che NON filtra `chiuso`
(`clients.py:304-332`, deliberato ma non dichiarato al consumo). **Audit FE depositato**
(`211c481`, `operations/AUDIT_FE_SEGNALI_E_SELETTORI_2026-07-07.md`): P1-P5 dropdown, I1-I7
incoerenze segnali, B4/B5 wallet+receivable invisibili nel profilo; gap wire =
`crediti_residui_attivi`. Legge nuova ratificata: **segnale ⇒ azione** (un warning senza scelta
non dà controllo: dà ansia).

**Fondamenta ADR-025 depositate** (`9ee325f`, workflow ultracode 14 agenti / ~1.5M token):
`archive/RICERCA_COMPETITOR_WALLET_SEDUTE_SINGOLE_2026-07-07.md` (11 vendor, leggi W1-W11 — chiave
W9: NESSUN vendor ha il prezzo suggerito dallo storico = unicità FitManager) +
`product/CATALOGO_SCENARI_PT.md` (96 scenari a 6 lenti + critic; copertura 15% piena / 51%
parziale / 34% assente; 14/26 scenari SETTIMANALI scoperti; 23 domande Q1-Q23).

**ADR-025 ACCEPTED** (`332ebd2`, 2026-07-08): decisioni percorse UNA A UNA col founder —
D-CLASSE-PRESTAZIONE · D-INSOLUTO-DERIVATO · D-WALLET-SEPARATO-COMPENSA · D-PARZIALE-AMMESSO ·
D-UNPAY-FLOOR · D-PAGATORE-LEGGERO · D-REGISTRO-OPERATIVO · D-PREZZO-LIBERO-CONSIGLIATO ·
D-PORTAFOGLIO · D-SCELTA-ALLA-CREAZIONE · D-SEGNALE-AZIONE (legge trasversale). Q6-Q23
dispatchate (in-spec vs differite con casa dichiarata).

**Apertura blocco «P»** (questo commit): `docs/specs/SPEC_P_PRESTAZIONI_SINGOLE_E_PORTAFOGLIO.md`
— gate P0..P6 dentro la macchina G9 + checklist di nascita ADR-024. P0 fondazione docs+ratifica
(riga matrice, P-D1..P-D6) → P1 schema+7ª `ClasseContabile`+penna+invarianti IP1-IP4 → P2
write-path (nascita atomica, incasso parziale, unpay-floor, suggeritore Q6) → P3 compensazione
wallet a due gambe + condono → P4 read-model Portafoglio + `crediti_residui_attivi` → P5 FE
(scelta a 3 vie al posto del warning-ansia, pannello Portafoglio, dropdown onesto) → P6 presidio
+ runbook 640/641 (interlock G9.7.2). Igiene INDEX: rimossa la riga stale di `SPEC_G9.4-BIS`
(archiviata alla chiusura G9, era ancora listata tra le aperte).

**⏭️ Prossimo: ratifica P-D1..P-D6 (gate P0) col founder → P1. In parallelo resta la coda G9.7**
(vitest AC-G97-1 + LIVE per chiudere G9.7.1; G9.7.2 si allinea ad ADR-025: assegna-contratto O
promuovi-a-singola, scelta esplicita).

---

## 2026-07-08 — Blocco P: P-D1..P-D6 ratificate una a una (gate P0, prima metà)

Metodo ADR-025 (contesto → raccomandazione → conseguenze → alternativa scartata, una decisione
per volta):

- **P-D1 ✅** stati contabilizzanti singola = **{Completato}**: penali su singola = zero fatto
  economico fino alla call tributarista (Q8 gated — addebito senza accordo sottoscritto = terreno
  art. 33), con segnale UI dichiarato (D-MAI-SILENZIO). Prepagata + no-show: incasso resta,
  azione suggerita (rimborsa/riprogramma), MAI automatica.
- **P-D2 ✅** compensazione wallet→singola = **due gambe di cassa pareggiate** in una transazione
  (gamba OUT = erogazione wallet già esistente, gamba IN = incasso prestazione via penna, metodo
  `COMPENSAZIONE_WALLET`): àncore Σ vere per costruzione, saldo invariato, reopen gratis (R2-bis),
  atto visibile nel mastro. Scartato il registro interno senza cassa (àncore rotte, atto invisibile).
- **P-D3 ✅** **condono sempre ammesso** (atto nuovo datato oggi: `importo_condonato`, motivo
  obbligatorio, audit; cassa ed evento intoccabili) — il fence resta sugli eventi. Ogni insoluto ha
  per sempre 3 uscite: incassa/compensa/condona. **Definitivo** nel blocco P (niente annullo-condono).
- **P-D4 ✅** (approfondita insieme su richiesta founder) l'escape hatch **«senza fatto economico»
  RESTA**: ultima posizione, label onesta, nag worklist B6. Caso forte = «seduta prima del
  contratto» (senza via 3, l'aggancio G9.7.2 si romperebbe: servirebbe smontare una prestazione
  finta). Il pericolo non era mai l'esistenza della via — era il silenzio, già ucciso da ADR-024.
  Scartati sia il motivo-obbligatorio (attrito-teatro) sia l'ontologia chiusa (semantica finta).
- **P-D5 ✅** naming `prestazioni_singole` / `prestazioni.py` / `id_prestazione` /
  `RICAVO_PRESTAZIONE_SINGOLA`: «prestazione» separa l'asse economico da «seduta» (=scheduling,
  già occupato da `sedute_*`), è il termine del registro operativo, forward-compatible su servizi
  non-allenamento.
- **P-D6 ✅ RIVISTA IN RATIFICA — Q9 differita INTERA a G8.2+G8.5.** Preparando la ratifica è
  emerso il difetto della bozza «metà veicolo»: la sola gamba `CONVERSIONE_PRESTAZIONE` si
  biforcava in (A) insoluto-su-erogata (il derivato P-D1 punirebbe lo spostamento dell'incasso da
  una prestazione EROGATA) o (B) wallet nato senza cassa = anticipo non governato di G8.5 — e in
  entrambi il valore parcheggiato non aveva destinazione (gamba wallet→contratto = G8.2 in
  panchina). Il blocco P non costruisce nessuna conversione; direzione wallet resta ratificata;
  interim = sconto ESPLICITO sul prezzo contratto. Spec emendata (via `CONVERSIONE_PRESTAZIONE`
  rimossa da P3, Q9 → fuori scope con casa). *La ratifica ha fatto il suo mestiere: difetto trovato
  prima del codice.*

**⏭️ Resta di P0: riga matrice + birth-review (4 regole × composizione protezioni). Poi P1.**

---

## 2026-07-08/09 — G9.7.1: verifica LIVE meticolosa (Playwright) → 3 gravissimi, 1 fixato

**Mandato founder:** «da ultima verifica c'erano ancora errori gravissimi su 9.7.1 — esegui test
meticoloso live playwright». Setup: cliente di test TestG97 col caso founder ESATTO ricostruito via
API (contratto 2 crediti, versato 0 → terminate → CHIUSO con 2 crediti residui) + cliente di test
senza contratti. Dati propri ([[feedback_test_data]]), cleanup completo a fine sessione (zero residui).

**GRAVISSIMO #1 — TUTTI i toast dell'app erano muti (root cause del «201 muto», AC-G97-1 FAIL).**
Live: PT orfano creato → calendario aggiornato, sheet chiuso, **regione notifiche VUOTA** — né il
B5 warning né il success generico; nemmeno il toast d'errore 409 appariva. Diagnosi con esperimento
DOM (`[data-sonner-toaster]` = 0 subito dopo `toast.error()`): **doppia istanza del modulo sonner**
— il `dynamic(() => import("@/components/ui/sonner"), {ssr:false})` in `providers.tsx` caricava il
Toaster in un chunk con la SUA copia di sonner; `toast()` dagli hook scriveva sull'istanza del grafo
principale, il Toaster ascoltava l'altra. **Fix: import statico** (il wrapper è già "use client",
ssr:false non serviva). Verificato live su ENTRAMBI i rami: B5 warning a video («Seduta creata SENZA
contratto…») + error 409 catturato da MutationObserver in-page (i toast da 4s si perdono coi
round-trip lenti — observer race-free). Vitest 91/91 + next build verdi. NB: muti in dev da data
imprecisata — nessuna verifica LIVE aveva mai ASSERITO un toast.

**GRAVISSIMO #2 — le orfane decrementano i crediti client-level (trappola composta, NON fixato:
decisione design).** `_calc_credits_batch` (clients.py:316-327) conta come «usate» TUTTE le PT in
stati di occupazione **senza filtrare `id_contratto IS NOT NULL`**: la seduta orfana — che per
promessa del B4 «non scala crediti» (vero a livello contratto) — fa scendere il numero nel dropdown.
Live: 2 orfane su TestG97 → «(2 crediti)» diventa «(0 crediti)» → scatta l'hard-block «Crediti
esauriti» → **il cliente resta intrappolato: nessuna nuova PT creabile da UI** (il backend la
permetterebbe). Verificato simmetrico: delete orfana → crediti risalgono. Il numero mente due volte
(include i chiusi E sottrae le orfane). Casa del fix: P4 (`crediti_residui_attivi` + semantica
enrichment onesta) — decidere se serve interim.

**GRAVISSIMO #3 — l'hard-block «Crediti esauriti» contraddice l'escape hatch (NON fixato: è la
scelta a 3 vie di P5).** `EventForm` disabilita il submit con `crediti_residui <= 0` e afferma una
regola che il backend NON impone («il cliente deve avere un contratto attivo»). Composizione: il
cliente SENZA contratti (0 crediti) prende il blocco duro → il soft-warning B4 è irraggiungibile
per lui; il B4 scatta SOLO nel caso «chiusi con crediti residui». Due politiche contraddittorie
sullo stesso asse. La soluzione vera è D-SCELTA-ALLA-CREAZIONE (P5); decidere interim vs attesa.

**Verdetto AC-G97-1:** B4 pre-warning ✅ (caso founder) · B5 toast ✅ SOLO dopo il fix toaster ·
coda gate G9.7.1 ancora aperta: vitest AC-G97-1 + decisioni founder su #2/#3. Minore: warning
console `DialogContent` senza `aria-describedby` (a11y, non bloccante).

---

## 2026-07-09 — G9.7.1-bis: decisioni #2/#3 + fix + gate G9.7.1 CHIUSO

**Decisioni founder (una alla volta, metodo ADR-025):** #2 orfane-decrementano-crediti → **fix
interim chirurgico** (non anticipa P4, che resta intero per i contratti chiusi nel numero) ·
#3 hard-block «Crediti esauriti» → **declassato a warning soft** (un solo asse, submit sempre
permesso; il blocco affermava una regola che il backend non impone e rendeva impossibile da UI il
flusso «seduta prima del contratto» appena ratificato in P-D4; P5 lo sostituirà con la scelta a
3 vie).

**Implementazione:**
- `clients.py` `_calc_credits_batch`: filtro `Event.id_contratto != None` sulla query «usate» —
  le orfane non consumano crediti acquistati (interpreti client-level e contract-level riallineati).
  Gemello: `test_g971bis_orfana_non_decrementa_crediti_cliente` (in `test_rinvio_libera_credito.py`,
  la casa dei conteggi-occupazione).
- `EventForm.tsx`: hard-block rimosso; due warning soft calibrati (`contratti_attivi === 0` → B4;
  attivi > 0 ∧ crediti ≤ 0 → «crediti esauriti sui contratti attivi») + submit `disabled={isPending}`
  soltanto.
- `useAgenda.ts`: predicato B5 estratto puro ed esportato (`isPtOrfanoCreato`) — l'invariante
  «mai 201 muto» ha un nome testabile che sopravvive a P5.
- Vitest nuovo `event-form-warnings.test.tsx` (7 test): B4 raggiungibile su TUTTE e tre le classi
  di cliente (caso founder · nuovo senza contratti · attivo esaurito) + submit mai bloccato +
  truth-table del predicato. **AC-G97-1 presidiato.**

**Verifiche:** pytest full **840 passed** (839+1) · vitest **98 passed** (91+7) · next build verde ·
LIVE read-only: cliente reale 0-crediti → warning soft + submit ABILITATO (prima: blocco duro).

**🏁 GATE G9.7.1 CHIUSO** (B4+B5 vivi e presidiati, vitest+LIVE fatti). Restano G9.7.2-5.

---

## 2026-07-09 — G9.7.2 CHIUSO: recupero esplicito degli orfani (B2/B3/B6 + D-RECUPERO-ESPLICITO)

**Sequenza decisa col founder («cosa è più corretto come logica di sviluppo?»):** chiudere G9.7
per intero PRIMA di aprire P1 — direzione delle dipendenze (G9.7.2 costruisce la superficie
orfani su cui P2 aggiungerà la seconda azione; G9.7.4-5 = guard e birth-auditor che devono
esistere PRIMA della nascita più grande), WIP-limit (la coda parallela è dove i gravissimi si
sono annidati), e il dato reale esce dal limbo subito.

**Backend:** `POST /events/{id}/assegna-contratto` (`agenda.py`) — UNICA via di re-parenting
(EventUpdate resta chiuso, fence ADR-023 intatto): bouncer 404 → solo PT → solo orfani →
contratto stesso-cliente (404, mai rivelare) + aperto (400) + **credit-guard condizionato
all'occupazione** (un Rinviato è assegnabile anche a contratto pieno, ADR-017) → audit UPDATE →
auto-close via `_sync_contract_chiuso` → UN commit. Guard CP-2 forward-dichiarato per P1.
**Reopen PROPONE (B2/B3):** `_orfani_periodo_chiusura` (`data_creazione ≥ data_chiusura`) in
`reopen-preview` (campo + messaggio) e nella response di `POST /reopen`
(`ContractReopenResponse`, snapshot PRE-reopen perché la riapertura azzera `data_chiusura`) —
propone, MAI riaggancia (D-PROPONE). **Worklist B6:** `GET /dashboard/orphan-events`
(`_orphan_pt_candidates`, SOLO stati di occupazione: un orfano Rinviato non è un caso) + alert
`orphan_events` (stesso helper → count==items); ogni riga porta i contratti APERTI del cliente
con crediti residui = l'azione inline (D-SEGNALE-AZIONE).

**Frontend:** badge hover «Senza contratto — non scala crediti» (EventHoverCard) ·
`AssegnaContrattoBanner` nel dettaglio evento (select contratti aperti + Assegna; riusa
`useClientContracts`) · `OrphanEventsSheet` (pattern GhostEventsSheet, Assegna inline per riga)
+ alert wiring (categoria nuova nella union AlertItem, icona Unlink, action+sheet in page.tsx) ·
`useAssegnaContratto` (invalidazioni = create/update evento + toast dedicato).

**Gemello formatter-pitfall rivissuto:** il PostToolUse ha strippato gli import aggiunti in un
Edit separato dall'uso → ri-aggiunti a usi esistenti ([[feedback_formatter_strips_imports]]).

**Test: +10** (`test_assegna_contratto_orfano.py`): guard chain completa · Rinviato esente ·
composizione auto-close (ultimo credito su SALDATO → chiuso) · 2b preview+response nominano e
NON riagganciano · worklist+alert coerenti. **LIVE E2E:** orfano creato da UI → alert → sheet →
assegna → occupa → alert decrementa. **La worklist ha subito rivelato dato reale:** 6 orfani,
non 2 — oltre a 640/641 c'erano **643** (terza seduta di Giacomo nata dopo l'audit) e 647/649
(eventi `test` del founder). Runbook di recupero depositato in coda alla spec (esecuzione
trainer-driven: 647/649 da eliminare; 640/641/643 = scelta founder reopen-39+assegna O attesa
P2 promuovi-a-singola).

**⏭️ Prossimo: G9.7.3 (derivato-occupazione mai nudo: hero crediti + sub-label — i campi sono
già sul wire) → G9.7.4-5 → poi P1.**

---

## 2026-07-09 (sera) — G9.7.3 fetta D1-D4 (`e533f9d`) + prova prod-ports + 3 lezioni ambiente

**G9.7.3 fetta 1 (D1-D4) PUSHATA e verificata LIVE sul caso reale:**
- **D1 (hero dettaglio):** riga crediti a **6 card** (Totali · Programmate · Completate ·
  **Penali** «Occupano il credito» amber · **Rinviate** «Non occupano» · Residui) dietro la
  disclosure F2, **+ banner-SEGNALE always-visible** quando `penali > 0` con l'equazione
  dell'occupazione: `totali = programmate + svolte + penali + residui` (± rinviate informativo).
  Conciliazione dei due vincoli ratificati: la RIGA resta collassabile (lista F2), il SEGNALE
  no (D-DERIVATO-MAI-NUDO).
- **D2/D3 (liste):** sub-label «N svolte · M penali» (amber) su ContractRow (tabella contratti,
  entrambe le viste responsive) + ContrattiTab del profilo cliente.
- **D4:** `DeleteContractDialog` legge `crediti_residui` dal wire — chiusa la violazione
  R-SSOT-FE dell'audit (ricalcolo inline `totali − usati`).
- **Wire additivo:** `ContractListResponse.sedute_penali` + `crediti_residui`; le DUE query di
  conteggio del batch lista fuse in **UNA** `group by (id_contratto, stato)` con derivazione
  dal SSoT `STATI_OCCUPAZIONE_CREDITO` (un solo interprete, mai due query divergibili).
  Type-sync FE: `sedute_penali` sul dettaglio era STALE (il backend lo esponeva da G7.8-bis,
  il tipo FE no — la conferma dell'audit «già sul wire, mai renderizzati»).
- **Gemelli:** `test_g973_lista_espone_penali_e_residui` (lista == dettaglio, stessi numeri) +
  vitest `hero-occupazione-spiegata` sul caso founder 12·5·2 (banner con equazione; zero
  penali → zero banner; rinviate informativo). Fascia 19 pytest + **101 vitest** + build verdi.
- **LIVE contratto 39 REALE:** banner «**2 crediti occupati da penali**: 12 totali = 0
  programmate + 7 svolte + 2 penali + 3 residui» + card a 6. I 2 crediti "spariti" del caso
  founder ora si spiegano dalla vista. (NB: il 39 nel frattempo è stato lavorato dal founder
  nella sua prova — 7 completate, valore €480, rimborso €138,75.)

**Prova founder su porte prod (3000/8000) ANDATA BENE.** Durante la prova, 3 inciampi ambiente
— stessa lezione in 3 facce: **due processi dalla stessa working dir condividono le risorse**:
1. *Log rotation* (`data/logs/fitmanager.log`): doppio backend → `PermissionError WinError 32`
   a ogni rollover (Windows non rinomina file aperti da altri) → spam infinito su stderr, app
   comunque sana. + doppio frpc stesso instance_id (il VPS rifiuta il duplicato, babysitter ok).
2. *Lock `next dev`* (`.next/dev/lock`): il lock è per-CARTELLA, non per-porta — una sola
   istanza dev per working dir.
3. *Build vs dev* (`.next`): il `next build` del pre-commit ha ucciso il `next dev` in corsa
   (riscrive la build dir sotto i piedi del server) — morte silenziosa, zero errori nel log.
Candidati hardening (non fatti): log per-porta in source mode · guard di singola istanza.

**⏭️ RIPRESA DOMANI: G9.7.3 fetta D5** (breakdown penali minimo su sheet/rinnovi: campo sul
wire di `SuspendedContractItem`+`ExpiringContractItem` + sub-label sulle card) **+ suite FULL
+ fold-back docs per chiudere il gate → G9.7.4 (guard classe crediti + perimetro transizioni)
→ G9.7.5 (birth-auditor + Hypothesis I-EVENTI) → POI P1 blocco P.** Runbook orfani
(640/641/643 Giacomo + 647/649 test) sempre pendente, trainer-driven, in coda a SPEC_G9.7.

---

## 2026-07-08 — Blocco P: P0 CHIUSO (riga matrice + birth-review)

**Riga in matrice** (`MATRICE_ASSI_SEMANTICI.md`): asse «prestazione singola & insoluto» — celle
R1-R4/DV ✗ coi puntatori ai gate P1..P6 che le chiudono; annotato che la prestazione **non ha
colonna `stato`** (derivato-only per decisione, S1). È la **prima riga nata col protocollo
completo** ADR-024: matrice + review PRIMA del codice — finora ogni cella ✅ era costata un
incidente.

**Birth-review** (charter S1-S5 di SPEC_G9.4-BIS §5 + lente CP, applicata inline — l'agente
`.claude/agents/` nasce in G9.7.5): S1-S5 conformi by-design. La lente **composizione protezioni**
ha trovato **4 finding reali**, foldati nei gate prima che diventassero codice:
- **CP-1** `delete_client` RESTRICT non copriva le prestazioni con posizione aperta (cliente
  cancellabile con insoluto vivo) → esteso in P2, gemello nell'harness.
- **CP-2** `assegna-contratto` (G9.7.2) × promozione-a-singola (P2): senza guard incrociato, un
  orfano poteva avere ENTRAMBI i fatti economici → vie mutuamente esclusive, guard nei due
  endpoint (annotato in entrambe le spec).
- **CP-3** blocco prestazione in `EventCreate` × auto-assign: la scelta esplicita SOPPRIME
  l'auto-assign; singola su cliente CON contratto attivo = legittima (seduta fuori pacchetto).
- **CP-4** delete evento con prestazione senza denaro → cascade soft-delete dichiarato
  (D-PERIMETRO-TRANSIZIONI); con denaro → RESTRICT (già in spec).
E **2 composizioni verificate OK** (nessun cambio): CP-5 reopen×compensazione (R2-bis riassorbe,
zero double-count) · CP-6 Rinviato-prepagata (uscite esistenti: riprogramma o unpay).

La review di nascita ha pagato SUBITO: CP-1/CP-2 erano esattamente la classe «deadlock da
protezioni giuste» (B1×no-re-parenting) che ADR-024 è nato per anticipare.

**⏭️ Prossimo: P1 (schema `prestazioni_singole` + FK/pagatore su CashMovement + 7ª
`ClasseContabile` + penna + IP1-IP4 + gemelli + Alembic). In parallelo coda G9.7.1 (vitest
AC-G97-1 + LIVE).**

---

## 2026-07-11 — G9.7.3 fetta D5 + GATE CHIUSO (occupazione spiegabile su OGNI superficie)

**Fetta D5 — breakdown penali su worklist dashboard e sheet (l'ultima superficie col conteggio nudo):**
- **Backend (`dashboard.py`):** nuovo helper `_occupazione_breakdown_map` = UNICO interprete batch
  dell'asse occupazione per le worklist — UNA query `group by (id_contratto, stato)` con derivazione
  dal SSoT (`STATI_OCCUPAZIONE_CREDITO` per usati, `Completato` per svolte, `STATI_PENALE` per
  penali — la costante SSoT, non la sottrazione usata in `contracts.py`). `_crediti_usati_map`
  DELEGA (un solo interprete, `_lapsed_client_candidates` invariato); la **raw-SQL COUNT
  dell'expiring RITIRATA** (era il sito migrato di G7.8-bis Step 0 — ora anche fuso).
  `_suspended_contracts_candidates` ritorna il breakdown; `suspended-contracts` +
  `expiring-contracts` espongono `sedute_completate` + `sedute_penali` (additivo).
- **FE:** type-sync `ExpiringContractItem`+`SuspendedContractItem`; sub-label pattern D2
  «N svolte · M penali» (penali amber solo se >0 — segnale, non rumore) su RenewalCard +
  SuspendedCard (`rinnovi-incassi/page.tsx`) e sotto la progress bar di `ExpiringContractsSheet`.
- **Gemelli:** 2 pytest (`test_g973_d5_*` in `test_late_cancel_no_show.py`: worklist == dettaglio
  sul mix Completato/penali/Rinviato — un solo interprete) + 2 vitest
  (`expiring-sheet-breakdown.test.tsx`, hook mockati + QueryClientProvider per il WhatsAppButton).

**Verifica:** suite full **853 pytest** (+2) · **103 vitest** (era 101, +2) · ruff ·
`check-all.sh` verde · **LIVE read-only** su dev 3001/8001 (backend riavviato per servire D5 —
lezione Audit-2 ①: uvicorn senza reload serviva codice stale): il caso founder A VIDEO — card
rinnovo contratto 39 «12 PT · 3/12 crediti · **7 svolte · 2 penali** · 480 €», sospesi
«5 da recuperare · 5 svolte», card senza penali = solo «N svolte». Zero submit.

**Fold-back (gate chiuso, metodo §7):** SPEC_G9.7 → G9.7.3 ✅ CHIUSO (restano G9.7.4-5) ·
MATRICE_ASSI_SEMANTICI: cella **DV occupazione-credito → ✅** + R2/DV crediti-residui → ✅
(D4 già fatto in D1-D4, cella era stale) · questo log.

**⏭️ RIPRESA: G9.7.4** (guard classe crediti FE anti-re-inline con allowlist + test perimetro
transizioni `PERIMETRO_TRANSIZIONE` su execute_terminate/reopen) **→ G9.7.5** (agente
`semantic-birth-auditor` da charter SPEC_G9.4-BIS §5 + Hypothesis I-EVENTI) **→ POI P1 blocco P.**
Runbook orfani 640/641/643 + 647/649 sempre pendente (trainer-driven, in coda a SPEC_G9.7).

---
## 2026-07-14 — G9.7.4 GATE CHIUSO (guard di classe crediti + perimetro transizioni dichiarato)

**Cinque gemelli nuovi in `test_semantic_guards.py`** (la casa dei guard semantici, ADR-022
D-INVARIANTI-IMPOSTI) — il no-recalc si estende dall'asse denaro all'asse crediti, e le
transizioni dichiarano il destino di OGNI entità satellite:

- **`test_g974_fe_no_credit_math`** — vietati nel FE: `totali−usati` (residui ricalcolati),
  `totali−residui` (usati ricalcolati), conteggi di stati evento client-side spacciati per
  occupazione. Allowlist motivata SOLO per gli **aggregati-di-vista** (dashboard-helpers KPI del
  giorno, RangeStatsBar agenda — stessa dottrina Σ-di-vista del money-guard G8.4).
  **Provato ROSSO sul codice pre-fix** (stash → red → pop): ha beccato esattamente i 2 siti reali,
  poi fixati — progress bar `RenewalCard` (`totali−residui` → `crediti_usati` dal wire) e dropdown
  `AssegnaContrattoBanner` (`totali−usati` → `crediti_residui` dal wire, il campo D4 c'era già).
- **`test_g974_fe_consuma_occupazione_dal_wire`** — anti-vacuità (lezione guard G9.3):
  hero/ContractRow/DeleteContractDialog/banner/rinnovi DEVONO leggere i campi wire; autorità
  `ContractListResponse.model_fields` (mai il type FE).
- **`test_g974_stati_credito_no_reinline`** — chiude il **flag LOW G9.4-bis** della matrice:
  classificazioni wallet/receivable solo via `STATO_CREDITO_*`; `SALDATO` fuori dalla rete
  (collide con l'asse `stato_pagamento` — assi diversi, reti diverse); verificato prima sul
  codice: zero literal classificanti, i restanti sono SSoT/default-modello/stringhe audit.
- **`PERIMETRO_TRANSIZIONE`** (`transitions.py`) — **7 satellite dichiarate con dottrina**
  terminate/reopen: rate (M1/reconcile) · movimenti_cassa (IMMUTABILE R1) · rettifiche
  (storno/reversal) · crediti_terminazione (→ANNULLATO) · crediti_cliente (→ANNULLATO+fold
  R2-bis) · agenda (SOLO lettura; reopen NOMINA) · contratti self (`rinnovo_di` mai mutato, R8).
  Gemello `test_g974_perimetro_transizioni_esaustivo` = **set-equality bidirezionale** col
  metadata ORM: satellite nuova non dichiarata O voce fantasma = rosso. La scoperta ha DUE reti:
  FK dichiarata + colonna per nome (`id_contratto`/`id_contratto_origine`) — la seconda copre il
  pattern cross-DB senza FK (pitfall #15).
- **`test_g974_perimetro_becca_satellite_nuova`** (AC-G97-4) — la funzione di scoperta è PURA e
  provata con una tabella FINTA `prestazioni_finte(id_contratto)` in MetaData separato (zero
  inquinamento del registry): scoperta senza FK ✓, non nel perimetro ✓ → il gemello andrebbe
  rosso. **La futura `prestazioni_singole` (P1) non può nascere senza dichiarare il suo destino
  nelle transizioni** — CP-4 della birth-review P0 diventa by-construction.

**Verifica:** suite full **858 pytest** (+5, 12:11 min) · **103 vitest** · ruff · check-all
verde. Zero submit/LIVE necessari (fix FE display-equivalenti, gate presidiato dai gemelli;
server dev spenti → il `next build` del gate non ha ucciso nulla, lezione 2026-07-09 ③).
**Asse DENARO invariato** (in `transitions.py` è entrata una COSTANTE dichiarativa, zero logica).

**Fold-back:** SPEC_G9.7 → G9.7.4 ✅ CHIUSO (resta G9.7.5) · MATRICE: 4 celle → ✅ (CP
stati-evento con canary G9.7.5 annotato · CP lifecycle-contratto · R4 stati-crediti/wallet ·
R4 crediti-residui-FE) · questo log.

**⏭️ RIPRESA: G9.7.5** (agente `.claude/agents/semantic-birth-auditor.md` da charter
SPEC_G9.4-BIS §5 + lente CP; Hypothesis rule asse occupazione in `test_financial_state_machine.py`
+ invariante **I-EVENTI**; canary «crea-su-chiuso poi riapri») **→ POI P1 blocco P.**
Runbook orfani 640/641/643 + 647/649 sempre pendente (trainer-driven, in coda a SPEC_G9.7).

---
## 2026-07-16 — G9.7.5 GATE CHIUSO (birth-auditor + Hypothesis I-EVENTI + canary composizione) → G9.7 tutti i gate chiusi

**Tre consegne** (diff solo-test + agente: asse DENARO invariato per costruzione):

- **Agente `semantic-birth-auditor`** (`.claude/agents/`, terzo della famiglia read-only dopo
  docs-drift e invariant-verifier): charter S1-S5 da SPEC_G9.4-BIS §5 (censimento assi ·
  interpreti impliciti · totalità sul diff · netto nudo · rito di nascita) + la lente **CP
  «composizione protezioni»** di SPEC_G9.7 — per ogni guard nuovo/toccato enumera gli stati che
  può PRODURRE o INTRAPPOLARE e pretende l'uscita esplicita (il deadlock B1×no-re-parenting è il
  caso canonico: due protezioni giuste, zero uscite). Tassonomia findings: ASSE-APERTO /
  INTERPRETE-IMPLICITO / TOTALITÀ-VIOLATA / NETTO-NUDO / NASCITA-SENZA-RITO / CP-DEADLOCK.
  Read-only meccanico, findings→STRUTTURA, metrica = findings in calo. Prima corsa reale: P1.

- **Macchina Hypothesis estesa all'asse OCCUPAZIONE** (`test_financial_state_machine.py`):
  5 rule — `crea_pt_auto` (auto-FIFO: la nascita B1 quando i contratti sono chiusi/pieni),
  `crea_pt_su_contratto` (bouncer chiuso/credit-guard esplorati), `nasce_orfano` (builder
  diretto), `cambia_stato_seduta` (PUT api, penali G7.8-bis comprese, fence ADR-023 esplorato),
  `assegna_orfano` (G9.7.2) — + invariante **I-EVENTI** dopo OGNI mossa: PT in occupazione ⇒
  contratto VALIDO (esiste, non eliminato, stesso cliente) OPPURE segnalato dalla worklist
  `/dashboard/orphan-events` — mai occupazione fantasma, mai orfano invisibile.

- **AC-G97-5 liveness + canary.** Sonda `RULE_FIRINGS` (Counter modulo) azzerata e ASSERITA nel
  test principale: nessuna delle 15 rule a zero sotto `SM_SEED` (distribuzione misurata 2026-07-16:
  create 37 · reopen 51 · cambia_stato 58 · nasce_orfano 68 · assegna 16 · pay 3 · unpay 4 …).
  `test_i_eventi_non_vacuo` prova l'oracolo su ENTRAMBI i rami (monkeypatch worklist→INVISIBILE;
  id_contratto inesistente→FANTASMA). `test_canary_crea_su_chiuso_poi_riapri` = replay esplicito
  B1→segnale→B2 propone (reopen NOMINA, non riaggancia)→assegna esplicita→occupa (crediti 2→3)
  →segnale spento. Suite **860** pytest (+2) · fascia adiacente 38 · check-all verde.

**2 scoperte dalla sonda (non dal design):**
1. **Orologio per-istanza = liveness morta dall'esempio 2**: la macchina gira N esempi nello
   stesso DB; il vecchio `self._hour` ripartiva da 0 a ogni istanza → le create via API (che, a
   differenza degli insert diretti, PASSANO da `_check_overlap`) sarebbero morte di 409 overlap
   sugli slot degli esempi precedenti. Fix: `_CLOCK` monotono a livello MODULO. Classe generale:
   quando un builder passa dal boundary API, l'isolamento per-istanza non basta più — le risorse
   contese (slot temporali) vanno allocate a livello di RUN.
2. **La nascita spontanea dell'orfano è quasi-irraggiungibile nel generativo**: `_orfano_nato`=0
   sotto il seed — i contratti aperti residui degli esempi precedenti ADOTTANO sempre l'evento
   (FIFO cross-esempio). Senza il builder `nasce_orfano` l'esplorazione non avrebbe MAI esercitato
   assegna-con-successo né il ramo orfano di I-EVENTI: la liveness va MISURATA per-outcome, non
   solo per-invocazione (una rule che spara 45 volte può non raggiungere mai il ramo interessante).

**Fold-back:** SPEC_G9.7 → G9.7.5 ✅ + header 🟢 tutti-i-gate-chiusi (spec aperta SOLO per il
§Runbook trainer-driven) + Stato DoD 6/7 · MATRICE: riga «aggancio eventi×contratto» R3/R4/DV/CP
→ ✅ con evidenze, R1/R2 = rischio residuo ACCETTATO con puntatore P5; canary stati-evento FATTO;
regola manutenzione ora punta all'agente attivo · questo log.

**⏭️ RIPRESA: P1 (blocco P, SPEC_P)** — schema `prestazioni_singole` + 7ª `ClasseContabile.
RICAVO_PRESTAZIONE_SINGOLA` + penna `post_prestazione_inflow` + IP1-IP4; il perimetro-transizioni
(AC-G97-4) e la riga-matrice P la aspettano al varco; birth-run dell'auditor sulla nascita.
**Runbook orfani 640/641/643 + 647/649 sempre pendente (trainer-driven, §Runbook SPEC_G9.7).**

---
## 2026-07-16 (sera) — Pre-release candidata v1.0.14: triade auditor sul batch + piano R1 (checkpoint, docs-only)

**Decisione founder ratificata:** rilasciare al confine di blocco (G9.7 chiuso) PRIMA di P1 —
batch 206 commit già grande, valore non consegnato (Chiara su v1.0.10), OD-2 affamato di
telemetria. Runbook a 6 step; **step 1 eseguito** = triade auditor read-only in parallelo sul
delta `9ab426e..b888a0a`, con il `semantic-birth-auditor` alla PRIMA corsa (proposta founder:
collaudo pre-P1). Evidenza consolidata in `operations/AUDIT_PRE_RELEASE_2026-07-16.md` (SSoT).

**Verdetti:** money **PRESERVED** (394 oracle verdi, V1-V5 puliti, 1 LOW: `posizione_netta_contratto`
oracolo morto) · drift 8 finding TUTTI docs-layer (2 HIGH: INDEX dà G9.7 «da implementare» e ferma
gli ADR a 022; 1 falso positivo confutato in triage — il «29 tabelle» di CLAUDE.md è GIUSTO,
l'aritmetica dell'agente no) · semantic **AT RISK** 0 HIGH / 4 MEDIUM — il finding che conta:
**M1 `CONSUNZIONE` buca il guard H1 di `unpay_rate`** (predicato-famiglia non totale: niente
storno, niente rimborso, prefisso TERMINAZIONE_ non matcha → revoca su CHIUSO passa; in dev/CI il
gate maschera con 409 generico, **in prod log-only committa**). Più M2/M4 = re-inline
(`sedute_penali` literal nel dettaglio; `crediti_residui` inline senza clamp nella worklist
orfani) **nel codice scritto da me in G9.7.2/3** — l'enforcement ha beccato il suo autore.

**Fetta R1 definita (ratificanda, pre-bump):** R1.1 predicato SSoT `is_chiusura_da_terminazione`
in transitions.py consumato da guard unpay E predicato I1 + gemello provato ROSSO · R1.2 Σ su
STATI_PENALE · R1.3 worklist orfani delega SSoT+clamp · R1.4 costante CAUSALE_BACKFILL_LEGACY ·
R1.5 F1 pin-vs-delete [decisione founder] — poi R1-docs (INDEX 2 HIGH, conteggi 860/103/372,
annotazioni L1/L3/L4/L6-sem). Nessun nuovo ADR (tutto dentro dottrina ratificata). Deferral:
M3-sem → **nota depositata in SPEC_P §P1** (il gemello 7-classi copre ANCHE stats/trend, non solo
classify) · INC-2026-03-29 senza postmortem = policy founder in coda · L2/L7-sem → core/P5.

**Metodo:** governance docs-only PRIMA (questo commit: audit + INDEX + SPEC_P + log), codice DOPO
il GO. **⏭️ ATTESA GO founder su R1 → poi step 2 runbook (OD-1 sui backup di Alessio E Chiara,
salto doppio v1.0.10→v1.0.14) → bump → pipeline ADR-004 → consegna → main align (modello B).**

---
## 2026-07-17 — Nuovo fronte macOS (pilota Daniele, MacBook Air M1): audit + G-MAC.0 fingerprint FATTO

**Trigger founder:** Daniele (PT pilota, primo cliente reale) ha un MacBook Air M1 2020 (ARM64,
8GB, macOS Tahoe 26.5 — foto specifiche). Bozza strategia da chat esterna (fingerprint
cross-platform) usata come riferimento NON vincolante; grounding sul codice reale.

- **Audit accoppiamenti Windows** (workflow 6 agenti: tunnel, build/installer, sweep OS, deps + 2
  ricerche web con fonti): sintesi nelle «verità fondanti» di `specs/SPEC_G-MAC_CONSEGNA_MACOS.md`
  §1. Chiave: runtime `api/` quasi tutto portabile (1 solo BLOCKER: `tunnel_config.py:35` hardcoda
  `frpc.exe` → tunnel muto su mac); la montagna è la distribuzione (launcher.bat, Inno, node.exe,
  Nuitka `--msvc`); Nuitka NON cross-compila (build su GH Actions `macos-15` ARM64); bundle Next
  standalone platform-specific (sharp win32 dentro); Gatekeeper Tahoe = rischio consegna n.1
  (right-click bypass RIMOSSO; canale scp/zip-USB non applica quarantena; MAI AirDrop/browser);
  layout FLAT → `config.py` invariato; frpc darwin_arm64 v0.61.1 ufficiale ESISTE.
- **G-MAC.0 (fingerprint cross-platform) IMPLEMENTATO:** `_fingerprint_windows()` estratta (puro
  spostamento) + `_fingerprint_macos()` (SINGOLA invocazione `ioreg -rd1 -c IOPlatformExpertDevice`,
  hash `sha256("IOPlatformUUID|IOPlatformSerialNumber")` ordine fissato, disciplina tutto-o-niente
  INC-2026-06-18: retry sui vuoti, no-retry sui timeout, mai hash parziale, mai cache di
  unavailable) + dispatch `platform.system()`. **T1 PASS: oracolo hash pre/post refactor identico
  (`695ad621…4315`)** → licenze Windows esistenti intatte. Suite **867** (+7: hash+ordine, singola
  invocazione §4.1, tutto-o-niente, retry, timeout, self-heal, dispatch); fixture forza il ramo
  Windows → suite valida anche su host darwin. Il gate CHIUDE solo con T2 su hardware macOS reale.
- **Depositati:** `specs/SPEC_G-MAC_CONSEGNA_MACOS.md` (gate G-MAC.0..5, decisioni D-MAC-1..5,
  timeline 14gg) · `adr/ADR-026-distribuzione-macos.md` (**proposed**, D1-D6) ·
  `specs/SPEC_FINGERPRINT_CROSSPLATFORM.md` (spec di dettaglio dalla bozza founder, §4 blindata 25/06).

---
## 2026-07-19 — Sequenza rami ratificata dal founder: v1.0.14 → blocco P → blocco G-MAC (docs-only)

**Decisione founder:** il fronte macOS parte DOPO il completamento del filone
contratti/finanziario; PRIMA di tutto la release v1.0.14 da consegnare a Chiara (v1.0.10, bug
fingerprint) e Alessio (v1.0.13). La coda di lavoro (posizione=stato, leggibile da `docs/specs/`):

1. **Release v1.0.14** — runbook `operations/AUDIT_PRE_RELEASE_2026-07-16.md` §7: GO su R1
   (aperta la decisione R1.5 pin-vs-delete `posizione_netta_contratto`) → R1-code + R1-docs →
   OD-1 (convalida `classify` read-only sui backup di Alessio E Chiara) → bump → pipeline
   ADR-004 → consegna + verifica campo → `main` align (modello B). Runbook orfani
   640/641/643+647/649 resta trainer-driven, non release-blocking.
2. **Blocco P** (`SPEC_P`, coda #2) — P1..P6, chiude il filone finanziario. La nota M3-sem
   (gemelli 7-classi ANCHE su stats/trend) lo aspetta in §P1.
3. **Blocco G-MAC** (`SPEC_G-MAC`, coda #3) — G-MAC.0 già FATTO e sigillato; ratifica ADR-026
   D1-D6 all'apertura. **Unica azione anticipabile: enrollment Apple Developer** (coda in tempo
   di calendario, non di sviluppo — azione founder fuori-codice).

Stato-line aggiornate su SPEC_P (#2), SPEC_G-MAC (⏸️ #3, timeline relativa all'apertura),
SPEC_FINGERPRINT (codice sigillato), ADR-026 (ratifica calendarizzata). Il codice G-MAC.0
(verde, Windows-invariante provato) viene committato ORA per lasciare il working tree pulito
al preflight della release (ADR-004 esige git clean): sigillare ≠ aprire il fronte.

---
## 2026-07-19 — Collaborazione Claude Code + Codex: gate A0 depositato (docs-only)

**Trigger founder:** iniziare lo sviluppo congiunto in piccoli step, preservando integralmente il
funzionamento già costruito con Claude Code e mantenendo massimo ordine nelle settimane pre-lancio.

Depositata `specs/SPEC_COLLABORAZIONE_CLAUDE_CODEX.md`: architettura agent-neutral con `AGENTS.md`
come nucleo operativo unico, `CLAUDE.md` preservato come entry point/adapter Claude, nessun
`CODEX.md`, eventuale `.codex/` solo per necessità runtime dimostrata. Scelta una migrazione
**strangler**: A0 contratto → A1 runbook condiviso + Contract Smoke → solo dopo, e in gate separati,
riduzione duplicazioni, hook portabili, auditor condivisi e learning agent-neutral.

**Evidenza baseline:** branch `FitManager_Studio` @ `b7423b2`, tree pulito pre-A0; `AGENTS.md`
9.588 byte, `CLAUDE.md` 34.452 byte, tre auditor read-only in `.claude/agents/`, `.codex/` assente.
A0 modifica solo SPEC + INDEX + append BUILD_LOG: **zero codice, zero config, zero cambi operativi a
Claude Code**, nessuna alterazione della coda v1.0.14 → P → G-MAC.

**⏭️ ATTESA RATIFICA founder ACX-D1..D6.** Poi A1, ancora docs-only: runbook comune, link
non distruttivi dai bootstrap e smoke read-only su sessioni nuove Claude/Codex.

---
## 2026-07-19 — ACX-D1..D6 ratificate: gate A0 CHIUSO (docs-only)

**Decisione founder:** ratificate integralmente ACX-D1..D6 della
`specs/SPEC_COLLABORAZIONE_CLAUDE_CODEX.md`. Diventano vincolanti: `AGENTS.md` è il nucleo unico,
nessun `CODEX.md`, migrazione strangler senza riduzione immediata di `CLAUDE.md`, A1 prima del nuovo
codice congiunto, auditor condivisi solo dopo prova di parità, `.codex/` solo per bisogno dimostrato,
learning promosso a regola esclusivamente dopo review umana.

**Esito:** A0 CHIUSO; SPEC e INDEX allineati. Nessuna modifica a codice, configurazioni,
`AGENTS.md`, `CLAUDE.md` o `.claude/`; sequenza v1.0.14 → P → G-MAC invariata.

**⏭️ PROSSIMO MICROSTEP AUTORIZZABILE: A1 docs-only** — runbook condiviso, link non distruttivi
nei bootstrap e Contract Smoke Claude/Codex. Nessun codice applicativo.

---
## 2026-07-19 — A1 CHIUSO: runbook agent-neutral + Contract Smoke Claude/Codex PASS

**GO founder:** eseguito gate A1 della `specs/SPEC_COLLABORAZIONE_CLAUDE_CODEX.md`. Creato
`operations/AI_ASSISTED_DEVELOPMENT_WORKFLOW.md`; aggiunti link additivi in root `AGENTS.md` e
`CLAUDE.md` senza rimuovere contenuto. Nessuna modifica a file di layer, `.claude/`, `.codex/`,
codice applicativo o configurazioni runtime.

**Contract Smoke reale:** Claude Code `2.1.170` in plan mode con soli Read/Glob/Grep → **PASS**;
Codex CLI `0.144.5` con sandbox read-only ed esecuzione ephemeral → **PASS**. Parità provata su tutti
i cinque assi: ordine fonti · branch `FitManager_Studio`/no feature branch non coordinate · A1 meta
distinto dalla coda v1.0.14 → P → G-MAC · gate docs/process · lifecycle ADR/SPEC/technical/
AUDIT-ROADMAP/BUILD_LOG/archive. Nessuna fonte storica usata come autorità.

**Hardening del test:** il primo prompt non bounded ha causato una ricerca Codex workspace-wide
patologica; sostituito con allowlist delle cinque fonti vive e divieto esplicito di search globale.
Il rerun bounded di ENTRAMBI gli agenti è quello valido e ripetibile depositato nel runbook.

**Finding non bloccanti, non corretti fuori scope:** numerazione `§7` duplicata in `AGENTS.md`;
Codex CLI non carica `.agents/skills/find-skills/SKILL.md` perché una riga vuota precede il
frontmatter YAML. Nessuno dei due finding altera il Contract Smoke o il comportamento Claude Code.

**Esito:** A0+A1 CHIUSI; condizione per nuovo codice congiunto soddisfatta. Commit/push non eseguiti.
**⏭️ Coda autorevole:** v1.0.14 (R1) → blocco P → blocco G-MAC. A2-A6 non autorizzati e separati
dalla release.

---
## 2026-07-19 — GO COMMIT A0+A1: sigillo docs atomico

**Decisione founder:** autorizzato il commit unitario dei gate A0+A1, senza push. Allowlist chiusa a
sei file: root `AGENTS.md` + root `CLAUDE.md` + SPEC collaborazione + runbook agent-neutral + INDEX
+ append BUILD_LOG. Nessun codice, file di layer, `.claude/` o `.codex/` incluso.

**Gate pre-commit:** Contract Smoke bounded Claude/Codex entrambi PASS · cross-doc/lifecycle/link
review PASS · scope allowlist PASS · `git diff --check` PASS · `ruff check api/` PASS. Il pre-commit
hook resta autorevole e viene eseguito dal commit.

**Commit:** `docs: ratifica workflow condiviso Claude Code e Codex`. **Push:** non autorizzato e non
eseguito. La coda successiva resta v1.0.14 (R1) → P → G-MAC; A2-A6 chiusi.

---
## 2026-07-19 — R1 pre-release chiusa: drift semantici corretti, asse denaro preservato

**Trigger:** triade auditor del pre-release v1.0.14 (`operations/AUDIT_PRE_RELEASE_2026-07-16.md`)
e GO founder in microstep R1.1→R1.5. Decisione aperta F1 risolta: **PIN** della fotografia netta
per contratto, senza promuoverla a caller runtime.

**R1-code:** commit `41d62e8` (`fix: chiudi i drift semantici R1 pre-release`), 14 file,
+208/−23. Chiuso il buco prod-only `CONSUNZIONE` nell'unpay con classificatore totale condiviso;
penali contratto e worklist orfani riallineate ai rispettivi SSoT; causale backfill legacy
parametrizzata dalla costante; `posizione_netta_contratto` protetta da unit-oracle puro.

**Gate:** full suite **873 passed / 0 fail**; Ruff backend verde; `check-all.sh` exit 0 con 11 guard
semantici ADR-016/017/018/019, guard lifecycle docs e Next production build; verifier finanziario
V1–V5: **MONEY AXIS PRESERVED**, zero money-regression, coverage-gap o invariante non presidiata.
I 31 warning sono debito preesistente (Hypothesis `norecursedirs`, deprecazione HTTP 422).

**Fold-back R1-docs:** INDEX G9.7/ADR→025; conteggi volatili sostituiti con soft-SSoT ai runner;
breadcrumb SPEC vocabolario; enum `MotivoChiusura` a 5; puntatore DISPLAY-EXEMPT al record vero
ADR-017 Add. I D-DENYLIST-INTATTE e al gemello semantico vivo; matrice wallet con casa P4/P5;
audit pre-release consuntivato. Nessun nuovo ADR: R1 rende totali regole già ratificate.

**⏭️ Prossimo gate:** OD-1 read-only (`classify` sui backup reali Alessio + Chiara), poi bump
v1.0.14 → pipeline ADR-004 → consegna/verifica campo → allineamento `main`.

---

## 2026-07-19 — OD-1 chiuso sulla popolazione reale: Chiara PASS, Alessio N/A

**Decisione founder:** il gate operativo segue i database reali da aggiornare, non una lista
nominale. Chiara è l'unica utilizzatrice nota con dati storici. Ad Alessio è stata consegnata
un'installazione per promozione/collaudo, ma non è usata in esercizio e non ha un database
data-bearing noto: **N/A**, non PASS e non release-blocking. Se emergesse in seguito un suo database
reale, lo stesso audit sarebbe obbligatorio prima dell'upgrade.

**Evidenza Chiara:** `backup_20260608_175757.sqlite` aperto `ro + immutable + query_only`;
`quick_check=ok`, `integrity_check=ok`, `foreign_key_check=0`. Il classificatore corrente ha
accettato **205/205 movimenti** senza eccezioni (**201 attivi + 4 soft-deleted**); nessuna colonna
richiesta mancante. `sqlite_total_changes=0`; hash pre/post identico
`4D761A045A2D41850A0243A2980052000998174C0CE3CEF0B52B42060BBAEA7A`, con dimensione e timestamp
invariati. Nessun dato personale esposto nell'output.

**Verdetto:** OD-1 **CHIUSO**. Nessun ADR: perimetro/evidenza operativa, non regola di dominio. Il
restore del backup Chiara sulla release candidate resta separato e aperto nella release checklist.
**⏭️ Prossimo gate:** bump `v1.0.14` → pipeline ADR-004 → consegna/verifica campo → allineamento
`main`.

---

## 2026-07-20 — Verifica R1 indipendente (verde) + prova video: la variante segnali-crediti che elude entrambi i warning

**Verifica R1/R1.5 (lavoro Codex, richiesta founder pre-bump):** ri-verifica indipendente del
commit `41d62e8` senza fidarsi del consuntivo — full suite **873 passed / 0 fail** riprodotta,
`check-all.sh` exit 0, workflow 7 agenti (5 verificatori adversariali per fetta +
financial-invariant-verifier + semantic-birth-auditor): **0 FAIL**, verifier **PASS** (0
money-regression, i 3 cambi comportamentali tutti SANCTIONED), chiusure M1/M2/M4/L5/L1-sem
confermate sul codice. L'ipotesi adversariale su R1.3 (drop del filtro PT nella delega a
`_crediti_usati_map`) è SMENTITA: filtri identici uno-a-uno alla query rimossa. Note LOW emerse
(igiene futura, non bloccano): fixture PIN R1.5 senza wallet SALDATO; literal `"COMPLETAMENTO"`
pre-esistenti in `contract_state.py:105`/`transitions.py:65,777`; gemello unpay-post-reopen per
CONSUNZIONE non pinnato.

**Prova video founder → variante NUOVA del caso audit FE 2026-07-07:** cliente test con attivo
esaurito (8 Completato + 2 penali = 10/10) + chiuso con 2 residui → dropdown EventForm
«(2 crediti)» (dal CHIUSO), **nessun warning pre-submit** (B4 vede 1 attivo; «esauriti» legge il
cumulativo = 2), auto-assign rifiuta correttamente (B1), PT nasce orfano, toast B5 in
contraddizione col dropdown e con promessa vuota (nessun aperto con residui > 0). Root cause
INVARIATO (`crediti_residui` client-level non filtra i chiusi — deliberato, `clients.py`); il
difetto puntuale è il predicato dei warning che mescola due perimetri. NON è una regressione R1
(`41d62e8` tocca la worklist orfani in `dashboard.py`, non l'enrichment). Deposito: audit FE §5
(evidenza + quarta fixture mancante) + SPEC_P P4/P5 (il campo `crediti_residui_attivi` rende
coerente anche il predicato; quarta fixture nei vitest P5). Non release-blocking per v1.0.14.

**⏭️ Prossimo gate:** bump `v1.0.14` → pipeline ADR-004 (stessa sessione).

---

## 2026-07-20 — Release v1.0.14 TAGLIATA: pipeline ADR-004 verde 5/5, artifact sigillato

Bump `1.0.14` (`api/__init__.py` + `frontend/package.json`), commit `a5ada32` («release: v1.0.14»).
Pipeline `build-release.sh` completa: **PREFLIGHT** (pytest **873 passed**, ruff, next build, git
clean) → **BUILD** Nuitka+standalone+Inno → **VERIFY** smoke 5/5 invarianti su exe reale
(version_match, db, catalog, enforcement ON, distribution_mode) → **SEAL** → **TAG `v1.0.14`**.
Safety gates: crm_leak / iss_reference / nutrition_integrity PASS. Contenuti: 522 esercizi,
880 alimenti, 12 template.

**Artifact:** `dist/FitManager_Setup_1.0.14.exe` (118 MB) · SHA-256
`55d821d7b112101c914bd0b5485a219cd90afe6af1943108e3ad558ca53d5d35` · manifest `dist/manifest.json`.

**⏭️ Gate residui (runbook):** restore backup reale Chiara sulla RC (item aperto checklist) →
test installer su macchina diversa → **consegna Chiara** (ferma su v1.0.10 col bug fingerprint;
verifica post-install: zero `Fingerprint parziale → /licenza` nei log) → verifica sul campo →
allineamento `main` (modello B). L'audit pre-release passa in `docs/archive/` a chiusura release.

---
# 2026-07-21 — Audit frontend core foldato in SPEC operativa

- Audit senior read-only su Clienti, Contratti, Agenda, Rinnovi & Incassi e Cassa consolidato in
  `docs/archive/AUDIT_FRONTEND_CORE_INTUITIVITA_2026-07-21.md`.
- Lavoro aperto depositato in `docs/specs/SPEC_FRONTEND_CORE_INTUITIVITA.md` con cinque gate:
  FE-0 integrità/privacy; FE-1 accessibilità; FE-2 modello mentale; FE-3 scalabilità/performance;
  FE-4 distintività LIVE.
- Decisione di metodo: nessuna nuova directory `docs/senior/`; audit già archiviato e SPEC nella casa
  canonica determinata dallo stato. Nessun codice runtime modificato.
- Scheduling: FE-0 è raccomandato prima di P1 per chiudere rischi percettivi/privacy, ma l'inserimento
  nella sequenza founder `v1.0.14 → P → G-MAC` richiede GO esplicito prima del codice.
- Verifica prevista dalla SPEC: error≠empty/not-found, privacy overview, keyboard/money-path, dataset
  >200, verifier finanziario sui read-model money-adjacent e test LIVE autenticato.

---

## 2026-07-21 — Validazione founder installazione v1.0.14 e restore da v1.0.10

- Il founder ha installato sul proprio PC l'artefatto release `v1.0.14` e ha caricato con successo
  un backup proveniente dalla versione `v1.0.10`.
- Esito comunicato: software installato e restore operativo; nessuna anomalia bloccante riportata.
- L'evidenza chiude il controllo sul campo atteso dopo il taglio della `v1.0.14` e autorizza
  l'allineamento fast-forward di `main` a `FitManager_Studio`.
- Il backup resta locale e fuori da Git: nessun dato cliente, clinico o finanziario viene depositato
  nel repository.
- Sequenza prodotto concordata: `v1.0.15` = blocco P + FE-0 integrità/privacy + criticità FE-1;
  ottimizzazioni/redesign estesi fuori scope; G-MAC apre dopo validazione e consegna della `v1.0.15`.

---

## 2026-07-21 — FE-0.1: privacy Clienti e verità Rinnovi & Incassi

- Lista Clienti resa privacy-safe: rimossi prezzo, versato e crediti dall'overview; il caso con rate
  scadute espone soltanto «Azione amministrativa» e porta alla worklist dedicata.
- Rinnovi & Incassi ora possiede e verifica tutte le 6 fonti operative, incluse «Crediti da
  incassare» e «Rimborsi da erogare»: una fonte fallita blocca KPI/«Tutto in regola», indica cosa
  manca e offre retry.
- Le due card finanziarie ricevono dati già verificati dalla pagina; nessun money-math, write-path o
  invalidazione è cambiato.
- Verifiche: 4 canary nuovi verdi; suite frontend **107/107**; lint mirato pulito; `next build` verde
  (TypeScript + 20 pagine). FE-0 prosegue con error/not-found e stati parziali sulle restanti superfici.

---

## 2026-07-21 — FE-0.2a: profilo Cliente error≠empty/not-found

- Il profilo usa «Cliente non trovato» solo per ID invalido/HTTP 404; rete, 5xx e risposta senza dato
  hanno errore esplicito e retry.
- Fallimenti di contratti, sessioni o readiness rendono il profilo «parziale» e sospendono checklist,
  path consigliato e completion dot dipendenti: nessun falso «manca» costruito da dati non verificati.
- Tab Contratti, Sessioni e Movimenti distinguono loading/error/empty/ready; il wallet cliente non si
  auto-nasconde più in errore.
- Verifiche: 4 canary nuovi; suite frontend **111/111**; lint mirato pulito; `next build` verde.
  Prossimo microstep: dettaglio Contratto e blocchi finanziari Cassa.

---

## 2026-07-21 — FE-0.2b: dettaglio Contratto error≠empty/not-found

- Il dettaglio usa «Contratto non trovato» solo per ID invalido/HTTP 404; rete, 5xx e risposta senza
  dato hanno errore verificabile e retry.
- Sessioni non converte più un guasto in «nessuna sessione»; lo Storico mantiene il ledger principale
  e dichiara separatamente l'eventuale indisponibilità della timeline.
- Stato errore promosso a primitive UI condivisa per mantenere la stessa grammatica su Cliente e
  Contratto.
- Verifiche: 2 canary nuovi + regressione profilo; suite frontend **113/113**; lint pulito; build
  Next.js verde. Nessun write-path o calcolo monetario toccato. Prossimo microstep: Cassa.

---

## 2026-07-21 — FE-0.3: Cassa fail-closed senza falsi zeri

- Il riepilogo Cassa tratta saldo e statistiche come fonti esplicite: hero/contesto compositi
  nominano la sorgente fallita con retry, mentre KPI/grafico restano visibili se le statistiche sono
  valide. Il mastro verificato resta operativo come blocco indipendente.
- Andamento non costruisce più KPI a zero da una risposta assente. Entrate e Uscite falliscono per
  colonna, mentre un errore anagrafica sospende solo il filtro cliente.
- Spese fisse non presentano più configurazioni o pending vuoti in caso di errore e bloccano il form
  finché i dati non sono verificati. Scadenze e Previsioni adottano lo stesso retry esplicito.
- Il verifier avversariale ha fermato il primo pass: un errore del solo saldo nascondeva anche le
  statistiche mensili valide. Correzione applicata separando le dipendenze e aggiungendo il canary
  speculare `saldo KO + statistiche valide` prima della pubblicazione.
- Verifiche: 5 canary nuovi; suite frontend **118/118**; lint dei 7 file toccati pulito; build Next.js
  verde (20 pagine). Il lint globale segnala 17 errori preesistenti fuori scope e nessuno nei file
  FE-0.3; warning Vitest fixture `edge-cases` e deprecazione middleware Next invariati.
- `financial-invariant-verifier` finale: **PASS**, nessun blocker; indipendenza saldo/statistiche e
  Entrate/Uscite preservata. `check-all.sh` non avviabile su host senza Bash: Ruff, guard documentale
  e build riprodotti verdi separatamente; guard pytest semantico non avviabile per launcher Python
  della venv non più esistente (nessun file backend o semantica ADR toccati dal diff).
- Asse DENARO: nessuna formula, mutation, invalidazione o transizione modificata; solo query state e
  render fail-closed. Prossimo microstep: FE-0.4 dipendenze Cliente nei form Contratto/Evento.

---

## 2026-07-22 — FE-0.4: dipendenze Cliente esplicite e chiusura FE-0

- ContractForm ed EventForm non trasformano più caricamento, rete/500 o risposta assente in un menu
  Cliente vuoto: placeholder contestuale, stato esplicito, retry e empty reale sono distinti.
- La creazione Contratto e il submit PT restano sospesi finché la relazione obbligatoria non è
  verificata. Rinnovo/modifica Contratto e categorie Evento che non richiedono Cliente conservano i
  propri flussi; payload, warning B4/B5 e write-path finanziari non cambiano.
- I due form usano `useWatch` al posto di `watch`, eliminando i warning React Compiler nei file
  toccati senza introdurre stato derivato o render aggiuntivi.
- Il verifier avversariale ha fermato il primo pass: un PT in modifica con Cliente persistito restava
  bloccato se il lookup falliva. Il gate ora sospende solo i PT che devono ancora scegliere il
  Cliente; aggiunto il canary speculare prima della pubblicazione.
- Verifiche: 7 canary nuovi + 7 regressioni B4/B5; suite frontend **125/125**; lint mirato pulito;
  build Next.js verde (20 pagine). Warning preesistente della fixture `edge-cases` e deprecazione
  middleware Next invariati.
- Verifier finale **PASS**, nessun blocker. Gap LOW rinviati al gate accessibilità FE-1:
  associazione programmatica label/Select e annuncio live dello stato errore condiviso.
- FE-0 Integrità completato (AC-FE0-1..7). Prossimo gate: criticità FE-1 coordinate con SPEC_P.

---

## 2026-07-22 — FE-1.0 docs-first: Contextual Deep-Link Contract v1 autorizzato

- Test LIVE founder FE-0: «Azione amministrativa» preserva la privacy e apre Rinnovi & Incassi, ma
  perde cliente e intenzione portando all'inizio della pagina.
- Decisione: URL semantico con `focus`, `client_id` e `rate_id` opzionale; solo ID/enum, zero PII o
  importi. La destinazione possiede risoluzione, focus accessibile, reduced motion e fallback stale.
- Money-path invariato: nessuna apertura automatica, precompilazione o mutation; il comando finale
  resta esplicito e auditabile.
- Scheduling: FE-1.0 entra ora, dopo FE-0 e prima di P1, come singola vertical slice
  `Clienti → Rinnovi & Incassi → rata scaduta`. Astrazione comune soltanto dopo 2–3 casi reali.
- Casa: aggiornate la SPEC frontend aperta e la relativa riga in `docs/INDEX.md`; nessun ADR e nessun
  nuovo evergreen perché non cambia una regola di dominio né descrive ancora codice implementato.

---

## 2026-07-22 — FE-1.0 implementato, gate in validazione LIVE

- Docs-first `724b74a`; runtime `f678292`. Clienti genera un deep-link con intent e ID, Rinnovi &
  Incassi risolve la rata del cliente, porta la card nel viewport, assegna focus e mostra un marker
  accessibile. URL senza PII/importi; nessuna apertura o mutation finanziaria automatica.
- Parser fail-closed anche su parametri duplicati; `rate_id` è valido solo dentro il `client_id`.
  Target multiplo dichiarato come «prima di N»; target stale produce un fallback esplicito.
- Il verifier avversariale ha bloccato il primo pass per StrictMode e live region non persistente.
  Entrambi corretti e fissati con canary dedicati prima del commit.
- Verifiche: **148/148 Vitest**, lint mirato pulito, build Next/TypeScript verde (20 pagine),
  pre-commit Ruff+build verde. `financial-invariant-verifier`: **MONEY AXIS PRESERVED**, zero finding.
- Limite host invariato: Bash assente e venv backend con launcher Python non disponibile;
  `check-all.sh` non eseguito, sostituito per questo diff FE-only dai controlli differenziali del
  verifier. Warning baseline invariati: fixture `edge-cases` e convenzione middleware deprecata.
- Stato: implementazione automatizzata completa, **LIVE founder ancora richiesto** su target singolo,
  multiplo/stale e viewport mobile. FE-1.0 non è dichiarato chiuso fino a tale evidenza.

---

## 2026-07-22 — FE-1.0: bug al secondo utilizzo isolato e corretto

- Evidenza LIVE founder: il deep-link contestuale funzionava al primo utilizzo ma non al secondo
  attraversamento `Clienti → Rinnovi & Incassi` sullo stesso cliente; gate immediatamente riaperto.
- Root cause: l'hook leggeva la query solo al mount e ascoltava `popstate`, evento non emesso dalla
  navigazione client Next App Router. Con pagina/cache riutilizzata, intent e target rimanevano
  identici e l'effetto di focus non ripartiva.
- Canary red→green aggiunto prima del fix: simula destinazione, uscita su `/clienti` e ritorno allo
  stesso URL; sul codice precedente il secondo `scrollIntoView` mancava, sul fix passa.
- Commit runtime `d382a4b`: `usePathname`/`useSearchParams` rendono route e query reattive e la route
  completa governa il lifecycle di scroll, focus e marker. Nessun dialog, payload o mutation
  finanziaria toccati.
- Verifiche: pacchetto mirato **28/28**, suite frontend **149/149**, lint mirato e `diff --check`
  puliti, `next build` verde con `/rinnovi-incassi` statico e pre-commit reale Ruff+build verde.
  Warning baseline della fixture `edge-cases` e deprecazione middleware invariati.
- Verifier avversariale finale **PASS**, zero finding/blocker e **MONEY AXIS PRESERVED**. Due gap di
  test LOW non bloccanti (repeat+StrictMode nello stesso canary e sequenza live-region esplicita)
  restano dichiarati. Browser integrato non disponibile: nessuna falsa sostituzione del test reale.
- Stato: fix automatizzato completo; FE-1.0 resta **in validazione LIVE** finché il founder non
  conferma due utilizzi consecutivi e i casi mobile/multiplo/stale previsti dalla SPEC.

---

## 2026-07-23 — FE-1.0: root cause cache/scroll restore chiusa

- Seconda evidenza LIVE founder: `d382a4b` non bastava. Dal secondo click l'URL contestuale era
  corretto ma lo scroll restava ignorato; il refresh dello stesso URL lo eseguiva immediatamente.
- Audit: il layout dashboard salva `scroll:${pathname}` e ritenta il restore a
  0/50/100/250/500/1000/2000 ms. Con cache calda sovrascriveva il singolo scroll dell'hook; al
  refresh il pathname iniziale non cambia e il restore viene saltato. Il primo canary era falso
  positivo perché non smontava davvero la card durante `/clienti`.
- Docs-first `fccb06e`; runtime `8f5ca45`. La CTA contestuale disabilita lo scroll Next e cancella
  la chiave destinazione tramite il contratto esistente `clearPageState`; il layout non avvia più i
  restore concorrenti. La card tardiva è stato reattivo e focus/scroll partono nel RAF solo se il
  nodo è connesso.
- Correzioni avversariali nello stesso gate: timeout marker avviato dopo il RAF, evitando highlight
  permanente su tab sospesa; live region vuota durante loading/error anche con overdue cached e
  popolata soltanto dopo retry verificato.
- Canary rosso→verde: target tardivo, proprietà `scroll={false}`, consumo exact della chiave
  `scroll:/rinnovi-incassi`, RAF sospeso e cached-overdue+errore altra fonte. Pacchetto mirato
  **30/30**; suite frontend **151/151**; lint e `diff --check` puliti; build Next/TypeScript verde
  (20 pagine) e pre-commit reale Ruff+build verde. Warning baseline invariati.
- Verifier finale **PASS**, zero blocker/finding; **MONEY AXIS PRESERVED** — nessuna mutation,
  formula, payload, importo, endpoint o invalidazione finanziaria modificati.
- Stato: implementazione completa e push-ready; FE-1.0 resta aperto esclusivamente per il retest
  LIVE founder sul secondo/terzo click e per i casi mobile/multiplo/stale già previsti.

## 2026-07-24 — Audit obsolescenza post-migrazioni depositato

- Trigger founder: dopo tunnel FRP (Hetzner) e filone finanziario G7-G9, sezioni obsolete
  confondono l'utente e generano rumore. Audit read-only, nessuna modifica applicata.
- Metodo: workflow 7 agenti (6 sweep per dominio — tunnel, finanza BE, finanza FE, docs,
  dead-code FE, dead-code BE/tools — + 1 critico adversariale che ha ri-verificato nel codice
  tutti gli ALTA e i MEDIA user-facing). 54 finding grezzi → **41 CONFERMATI, 1 ridimensionato,
  0 falsi positivi** + 5 aree aggiunte dal critico (workspace_engine BE morto, 63 file tools/
  su crm_dev contro gli 8 censiti, alert `overdue_rates` calcolato e sempre scartato dalla UI,
  numeri pre-ADR-003 in RELEASE_CHECKLIST, `tests/legacy` documentata ma inesistente).
- Report: `docs/operations/AUDIT_OBSOLESCENZA_POST_MIGRAZIONI_2026-07-23.md` (evidenze
  file:riga complete, piano a fasce A/B/C).
- Highlights: **TN-2** `launcher.bat:76-101` shipped in v1.0.14 riattiva `tailscale funnel` se
  `PUBLIC_PORTAL_ENABLED=true` (doppio percorso vietato dal security boundary → gate consegna
  Chiara); **MB-2** `migrate-all.sh` («REGOLA BLINDATA») oggi ricrea il crm_dev.db dismesso;
  ~6.800 LOC morte FE (ProgressiTab ~3.070, workspace ~1.170 + gemello BE ~3.000,
  smart-programming client ~1.070, export Excel 900, OverdueRatesSheet 264); **FF-1**
  ContrattiTab mostra il versato LORDO (AC-G84-1 dichiarato chiuso, superficie mancata dal
  gemello → riaprire SPEC_G8.4 F1.a); sottosistema Connettività interamente Tailscale-based
  ancora attivo e visibile (Fase 3 pianificata ma senza spec aperta).
- Integrazione decisa: fascia A (quick win) nella finestra corrente tra chiusura FE-1.0 e
  apertura P1; TN-2 gated sulla consegna Chiara; fascia B = sessione decisionale founder
  (Connettività/Fase 3.7, router nutrition esposto, bonifica crm_dev); fascia C resta nelle
  case già aperte (SPEC_P P4/P5, SPEC_G8.4 F1.a, `signed_contractual_amount` HOLD fino a P1).

---

## 2026-07-24 — FE-1.0 chiuso LIVE e incasso rata reso guidato

- Il founder ha ripetuto oggi il test LIVE del deep-link dopo `8f5ca45` e ne ha confermato il
  corretto funzionamento: FE-1.0 è chiuso.
- Nuovo finding LIVE: nella worklist Rinnovi & Incassi «Incassa» eseguiva al primo click il pagamento
  dell'intero residuo con data odierna implicita, diversamente dal pagamento rata standard.
- La card ora riusa `PayRateForm`: il primo click apre importo, metodo e data; soltanto il submit
  finale chiama `usePayRate`. La data proposta è oggi, coerente con l'ingresso effettivo di cassa, e
  resta modificabile per registrazioni tardive; metodi, pagamenti parziali, endpoint e invalidazioni
  restano quelli canonici.
- Canary aggiunto: zero mutation al primo click e payload finale esplicito sulla fixture. Verifiche:
  pacchetto mirato **11/11**, suite frontend **152/152**, lint mirato pulito, build Next/TypeScript
  verde (20 pagine), `git diff --check` pulito. Warning baseline `edge-cases` e deprecazione
  middleware invariati.
- Verifier differenziale: **PASS — SANCTIONED-CHANGE** sul default temporale autorizzato dal founder;
  importi, writer, formule, endpoint e invalidazioni restano invariati e il nuovo canary copre la
  data proposta. Commit e push non eseguiti.
- **⏭️ Coda:** Fascia A audit obsolescenza post-migrazioni → P1 blocco P.

---

## 2026-07-24 — Rettifica audit e apertura docs-first R0 protezione release

- **Decisione founder:** prima di aprire P1 viene introdotto il gate stretto **R0 — Protezione release v1.0.15**. La sequenza operativa diventa `FE0/FE1 chiusi → R0.1–R0.4 → P1–P6 → candidate v1.0.15 → G-MAC`.
- **Rettifica append-only:** questa voce supera la coda “Fascia A audit obsolescenza post-migrazioni → P1” riportata nelle precedenti registrazioni del 2026-07-24. Le righe storiche non vengono riscritte, in conformità al contratto del `BUILD_LOG`.
- **Spec aperta:** creata `docs/specs/SPEC_R0_PROTEZIONE_RELEASE_V1_0_15.md`, con impact map, invarianti, non-obiettivi, acceptance criteria e Definition of Done per R0.1–R0.4.
- **Audit verificato e foldato:** `AUDIT_OBSOLESCENZA_POST_MIGRAZIONI_2026-07-23.md` è stato riclassificato da fotografia operativa a documento concluso e spostato in `docs/archive/`. La vecchia posizione `docs/operations/` citata nelle righe precedenti resta quindi solo un riferimento storico.
- **Correzioni emerse dal confronto col codice:**
  - il conteggio verificabile sul branch `crm_dev` è **34 file sorgente tracciati**, non 63; i 29 elementi ulteriori erano bytecode ignorato;
  - il workspace engine è già raggiunto dal flusso live `/workspace/today`; restano candidati di pulizia soltanto list/detail non esposti;
  - il modulo nutrition è autenticato e non costituisce l'attuale superficie pubblica FRP; la sua rimozione resta una decisione separata;
  - la rimozione completa Tailscale rimane nel perimetro Phase 3, mentre R0 protegge il percorso pubblico effettivo della release;
  - il cleanup frontend esteso (circa 6.900 LOC candidate) è differito dopo v1.0.15 per non allargare il rischio pre-release.
- **Coordinamento documentale:** aggiornate le SPEC FE, P e G-MAC con il nuovo ordine dei gate; riconciliato `docs/INDEX.md`, includendo anche le SPEC Fingerprint e G-MAC precedentemente mancanti.
- **Scope della modifica:** solo documentazione e governance; nessun file runtime, schema o dato persistente modificato. Il file locale non tracciato `live-01-dashboard.png` è rimasto intatto.
- **Verifica documentale:** tutte le 10 SPEC aperte presenti in `docs/specs/` risultano indicizzate; nessuna SPEC marcata `✅ IMPLEMENTATA` resta nella cartella aperta; l'audit non è più presente in `docs/operations/` ed è presente in `docs/archive/`.
- **⏭️ Prossimo microstep:** avviare R0.1 solo dopo approvazione di questo gate documentale, partendo dal contenimento del singolo percorso pubblico/FRP.

---

## 2026-07-24 — R0.1 contenimento FRP verde, HOLD su trust TLS live

- **Impact map eseguita:** percorso pubblico unico sulle istanze FRP provisionate; nessuna modifica a
  ledger, rate, schema, ownership, audit trail o comportamento delle installazioni non-FRP.
- **Autorità FRP:** l'`instance_id` della licenza valida determina l'origine
  `https://<instance_id>.fitmanagerstudio.com` anche quando `frpc` è temporaneamente indisponibile.
  Il fallback localhost resta attivo e il vecchio `.env` non può diventare autorità.
- **Fail-closed configurazione:** `public_access_provider=managed_frp` separa il wire dal percorso
  legacy; lo status non esegue né propone Funnel/Tailscale e ogni POST legacy riceve `409` prima di
  mutare file o process env.
- **Launcher/installazione:** rimosso integralmente l'auto-Funnel. Guard statico verde: zero comando
  `tailscale funnel`, zero lettura `PUBLIC_PORTAL_ENABLED`; `fitmanager.iss` stagea il launcher
  corretto.
- **UI:** sulle istanze FRP `ConnectivityStatusSection` non monta il wizard legacy e mostra soltanto
  origine gestita, fallback locale, verifica end-to-end e validazione portale. Il ramo legacy non-FRP
  resta invariato. Applicate le regole React/Next della skill Vercel senza nuove astrazioni laterali.
- **Test:** backend connectivity **28/28**; full backend **880/880** in 17:41 con 31 warning baseline;
  frontend full **153/153**, più canary route aggiunto **4/4** e canary UI/route finale **5/5**;
  ruff e lint mirati verdi; Next production build verde su 20 pagine; `git diff --check` pulito.
- **Live routing:** sul dominio FRP attivo, diagnostica applicativa con trust disabilitata:
  `/health` **200**, `/clienti` **404**. La route separation è quindi effettiva e il CRM non è esposto.
- **HOLD non occultabile:** il probe HTTPS strict fallisce perché il certificato presentato è
  self-signed (`relazione di trust` non stabilita). È coerente con la Fase 1/Fase 2 già documentata,
  ma impedisce di dichiarare l'origine pubblica production-ready senza una decisione: remediation
  immediata R0.1.5 oppure blocker falsificabile in R0.4. **R0.2 non aperto.**
- **Nota ambiente:** i warning di rollover `fitmanager.log` nella full suite derivano dal server live
  `uvicorn --reload` concorrente. Il processo `frpc` osservato è suo figlio, non un orfano, ed è stato
  lasciato intatto. `live-01-dashboard.png` non è stato toccato.
- **Commit/push:** non eseguiti, in attesa della decisione founder sul finding TLS e sul confine del
  prossimo commit atomico.
- **Gate frontend definitivo successivo al consuntivo:** **157/157**; include il canary route
  aggiunto dopo la prima esecuzione full. Lint mirato ancora verde.
- **Decisione founder successiva:** richiesti commit e push del gate R0.1 prima di decidere la
  collocazione del finding TLS. Il file locale `live-01-dashboard.png` resta fuori dal perimetro.

---

## 2026-07-24 — Protocollo Senior A1.1 depositato, HOLD sullo smoke Claude

- **Checkpoint R0.1 rettificato append-only:** il gate riportato sopra come non pubblicato è stato
  successivamente committato e pushato in `824799d` (`fix: rende FRP il percorso pubblico gestito`);
  delta remoto verificato `0 0`. Soltanto dopo quel checkpoint è iniziato il gate docs/process A1.1.
- **Root cause del calo di metodo:** `AGENTS.md` chiedeva il push dopo ogni step completato, mentre il
  runbook dichiarava commit/push non impliciti. Mancavano definizioni falsificabili di gate vs
  microstep, condizione tracked-clean tra gate e classificazione dei finding.
- **Decisione founder ACX-D7:** il microstep si verifica subito; il gate è l'unità di commit/push; il
  GO iniziale ne autorizza il checkpoint normale; nessun gate successivo prima di push, delta remoto
  `0 0` e zero modifiche tracked attribuibili al gate precedente. HOLD e finding fuori scope non
  trattengono né contaminano un gate corrente già verde.
- **Allineamento:** aggiornati nucleo `AGENTS.md`, runbook agent-neutral, adapter root `CLAUDE.md`,
  `CONTRIBUTING.md`, SPEC/INDEX e riferimento del guard lifecycle. Risolta anche la numerazione
  duplicata: lifecycle documentale ora univocamente in §11.
- **Contract Smoke Codex:** primo run read-only **FAIL** su un drift reale della coda prodotto
  (`v1.0.14 → P → G-MAC` rimasto nell'intestazione); fonti vive riallineate a
  `R0 → P → candidate v1.0.15 → G-MAC`; secondo run **PASS** sui sei campi, incluso
  `DELIVERY_CHECKPOINT`.
- **Contract Smoke Claude:** client `2.1.170` raggiungibile, ma tentativi default e Haiku bloccati dal
  provider per session limit fino alle 22:00. Nessun output semantico e nessun PASS dichiarato.
- **Guard deterministici:** sezioni AGENTS 1–11; zero contraddizioni vive; 10/10 SPEC indicizzate;
  zero leak SPEC/IMPL_PLAN in `docs/technical/`; zero spec implementate rimaste vive; link locali dei
  documenti toccati validi; Ruff e `git diff --check` verdi. Nessun test applicativo richiesto per il
  gate docs/process.
- **Stato:** A1.1 resta IN VERIFICA; commit/push del gate e apertura TLS R0.1.5 restano bloccati dal
  solo smoke Claude mancante. `live-01-dashboard.png` è intatto, fuori scope e mai staged.
- **Rettifica immediata prima del checkpoint:** il controllo finale non trova più
  `live-01-dashboard.png` né nel root né altrove nel workspace. Nessun comando del gate lo ha scritto,
  spostato o cancellato, ma la variazione non è attribuibile con certezza; stage/commit restano quindi
  sospesi anche per questa seconda stop condition. La frase precedente non va usata come stato finale.
- **Attribuzione founder successiva:** il founder conferma di avere rimosso personalmente
  `live-01-dashboard.png`. La stop condition sul working tree è chiusa; resta soltanto il Contract
  Smoke Claude eseguibile dopo il reset quota delle 22:00.
- **Waiver founder ACX-D8:** il founder decide di non attendere le 22:00 e autorizza il checkpoint
  A1.1 e la successiva apertura di R0.1.5. Lo smoke Claude resta un follow-up obbligatorio appena
  possibile e prima di A2+; non viene chiamato PASS e la waiver one-shot non modifica il Protocollo
  Senior né crea una fallback policy generale.
- **Chiusura operativa A1.1:** gate pronto per commit/push docs atomico; il gate TLS resta separato e
  può iniziare soltanto dopo verifica del delta remoto `0 0` e working tree tracked pulito.

---

## 2026-07-24 — R0.1.5 TLS: decisione HTTP-01 ristretto via FRP

- **Decisione founder:** non attendere lo smoke Claude delle 22:00; R0.1.5 procede ora. Il controllo
  Claude resta differito e non è registrato come PASS.
- **Finding confermato:** il piano storico DNS-01 assumeva un token Cloudflare limitabile al singolo
  record `_acme-challenge`; la documentazione ufficiale espone invece `DNS Write` come permesso di
  zona. Distribuire quel token sui PC trainer allargherebbe il blast radius all'intera zona DNS.
- **ADR-011 Addendum I:** il solo meccanismo challenge passa a HTTP-01 attraverso FRP. `frps` ascolta
  su 80 e instrada per host/path esclusivamente `/.well-known/acme-challenge/` a un webroot statico
  dedicato sul PC; ogni altro path HTTP è 404 e non ha Next.js/API come upstream.
- **P2 preservato:** certificato, account ACME e chiave privata restano in `data/tunnel/` sul PC del
  trainer. Il traffico applicativo continua su 443, con SNI passthrough e terminazione locale; la
  porta 80 trasporta soltanto challenge pubbliche.
- **Alternative respinte:** token DNS zone-wide sui trainer; wildcard/private key sul VPS; broker
  centrale che riceva la licenza completa con PII; TLS-ALPN-01 più complesso sul terminatore corrente.
- **Contratto R0.1.5:** client ACME standalone pinato nel build; emissione al boot, check ogni 12h,
  rinnovo entro 30 giorni; promozione cert/key atomica dopo SAN/tempo/key-match; ultimo certificato
  valido preservato su ogni failure; restart frpc controllato.
- **Evidenze pre-codice:** il probe esterno porta 80 è andato in timeout (edge non ancora configurato);
  `frpc` v0.61.1 ha accettato la sintassi del proxy HTTP con `locations` e plugin `static_file`.
- **Scope:** aggiornati SPEC R0, ADR-011 + indice ADR, SSoT tunnel/security, adapter root e indice docs.
  Nessun runtime, schema, dato business, denaro o file sotto `data/tunnel/` modificato dal gate.
- **Prossimo microstep:** verificare e applicare la configurazione edge con backup/rollback; poi
  implementare il trasporto challenge e il certificate manager in gate separati e verificati.

---

## 2026-07-24 — R0.1.5 microstep client: trasporto ACME separato dal CRM

- **Edge diagnosticato, non mutato:** SSH `BatchMode` verso il target documentato ha restituito
  `Permission denied (publickey,password)`; `ssh-agent` Windows risulta fermo/disabilitato e non
  esiste un alias SSH locale. Nessun segreto è stato richiesto o esposto. Il microstep edge resta
  pendente e non è dichiarato verde.
- **Config immutabile estesa:** `TunnelConfig` porta il path del webroot ACME dedicato; al boot viene
  creata soltanto la directory `.well-known/acme-challenge` sotto `data/tunnel/acme-webroot`.
- **Due upstream separati per costruzione:** il proxy HTTPS continua a terminare TLS e inoltrare a
  Next.js:3000; il nuovo proxy HTTP ha `locations` limitato alla challenge e plugin `static_file`,
  senza `localAddr` e senza riferimento a Next.js/API.
- **Test:** `tests/test_tunnel_config.py` **3/3 PASS**. Il terzo test invoca il binario reale ignorato
  dal repo e verifica sia versione **0.61.1** sia `frpc verify ... syntax is ok`. Ruff mirato e
  `git diff --check` PASS.
- **Nota runner:** `venv/Scripts/python.exe` punta a un base interpreter WindowsApps non più
  avviabile; i test sono stati eseguiti con l'interprete 3.12.10 funzionante e i `site-packages` della
  venv FitManager. È un problema ambiente separato, non un test rosso e non viene occultato.
- **Invarianti:** zero accesso HTTP a CRM/frontend, zero token DNS, zero modifica a processi live,
  `data/tunnel/`, schema, dati business, ledger o frontend.
- **Prossimo microstep:** checkpoint commit/push del trasporto client; poi certificate manager e
  packaging locale. La chiusura live resta subordinata alla configurazione edge e al probe strict.

---

## 2026-07-24 — R0.1.5 certificate manager core + stop order prematuri

- **Supply chain:** selezionato lego v5.2.1 (release GitHub immutabile). Metadata API, checksum file e
  ZIP concordano su SHA-256 `3e87…699e`; `lego.exe` dichiara `5.2.1 windows/amd64` e ha SHA-256
  `e2d5…25e5`. Il binario locale è in `tools/bin/`, ignorato da Git; il packaging resta un gate
  successivo.
- **Core:** nuovo `cert_manager.py`, scheduler dopo `frpc`, 12h/15min, nessun blocco al CRM locale.
  Il client è rifiutato prima dell'esecuzione su hash/version mismatch; argv senza shell e senza DNS.
- **Validazione/promozione:** SAN, tempo, cert↔key, chain bundled e firma leaf; staging+fsync, backup
  della coppia, marker di recovery e rollback entrambe le gambe. Solo una installazione verificata
  richiede restart controllato di frpc. Anche il bootstrap valida SAN/key/time.
- **Stop condition catturata dal live reload:** con lego appena disponibile, il processo dev in
  `uvicorn --reload` ha creato l'account ACME locale no-email e tentato due ordini production falliti
  (20:39 e 20:54), prima che l'edge 80 fosse pronto. Nessun cert emesso/installato e nessun processo
  orfano, ma il comportamento consumava ordini ogni 15 minuti.
- **Remediation nello stesso microstep:** preflight proprietario prima della CA — token casuale nel
  webroot, GET HTTP pubblico, 200+body esatto, cleanup. Sul live il preflight va in timeout e lego non
  parte; zero token residui e zero processo lego. Lo shutdown ora termina esplicitamente anche un
  processo ACME già in corso. La coppia attiva è coerente ma self-signed, `public_chain=False`,
  scadenza 2027-06-07.
- **Test:** tunnel+cert manager **16/16 PASS**; regressione condivisa connectivity/health/tunnel/cert
  **43/43 PASS**; full suite finale **896/896 PASS** (31 warning baseline, exit 0), Ruff mirato e diff
  check PASS. Coperti anche ordine proibito senza preflight, stop del processo ACME, race monitor↔restart,
  stop↔launch e rollback iniettato sulla seconda replace. Un primo run pre-hardening da 894 test aveva
  mostrato `WinError 32` sulla rotazione log per il server dev concorrente; il run finale non lo ha
  riprodotto. A fine gate restano solo server dev e relativo `frpc`, zero `lego`/pytest orfani.
- **Edge:** al controllo successivo 22/80/443/7000 risultano tutte non raggiungibili dal runner; poiché
  anche SSH e FRP bind sono down, il fatto non è attribuito al nuovo proxy. Live TLS resta blocker
  dichiarato, non falsamente verde.
- **Prossimo microstep:** checkpoint core; poi packaging riproducibile con hash gate. Edge e strict
  trust 200/404 restano necessari per chiudere R0.1.5.

---

## 2026-07-24 — R0.1.5 packaging ACME riproducibile e fail-closed

- **Build:** `build-installer.sh` richiama uno staging dedicato dopo il backend build. `lego.exe` viene
  copiato nel bundle solo se coincidono SHA-256 pinato, output esatto `5.2.1 windows/amd64` e licenza
  MIT tracked; anche la copia staged è ri-hashata. Inno Setup include già ricorsivamente il bundle.
- **Acquisizione:** nuovo `fetch-lego.ps1`, fuori dalla build e senza fallback `latest`: release URL
  v5.2.1, hash ZIP `3e87…699e`, hash exe `e2d5…25e5`, hash licenza `bf12…ddf6`, target/versione e
  destinazione finale tutti verificati. Esecuzione end-to-end reale PASS; scratch confinato nel temp
  root e rimosso. La build resta network-free.
- **Repository/licenze:** `tools/bin/lego.exe` resta ignorato. Sono tracked solo script, pin e testo MIT;
  `.gitattributes` forza LF per impedire che CRLF alteri l'hash della licenza o gli script su Windows.
- **Test:** packaging + connectivity release guard **9/9 PASS** (un warning Hypothesis baseline),
  inclusi missing, binario corrotto e stage reale; `bash -n` per gli script shell e parse PowerShell
  PASS. Nessun codice runtime, dato persistente o frontend modificato in questo microstep.
- **Gap dichiarato:** nessun nuovo installer RC prodotto qui; la checklist richiede ispezione finale di
  `backend/lego.exe` e `backend/THIRD_PARTY_LICENSES/lego-MIT.txt`. R0.1.5 resta aperto su edge e live
  strict 200/404; verifica Claude ancora differita, mai registrata come PASS.

---

## 2026-07-25 — R0.1.5 edge change preparato, blocker ridotto alla sessione SSH

- **Ground truth live:** DNS wildcard corretto; TCP 22/7000 raggiungibili; HTTPS con trust disabilitato
  risponde 200. HTTP/80 va in timeout e il client strict rifiuta la root self-signed
  (`SEC_E_UNTRUSTED_ROOT`): tunnel vivo, finding TLS ancora reale.
- **Accesso:** SSH BatchMode raggiunge il VPS ma la chiave locale protetta non è sbloccata
  (`Permission denied (publickey,password)`). Nessuna password/passphrase richiesta in chat e zero
  write remoti. Non è stato dichiarato alcun apply.
- **Artefatto apply:** `tools/operations/apply-frps-http01.sh` con renderer idempotente, candidate
  verificata da `frps`, backup univoco/privato, UFW 80 mirato, restart+listener check e rollback di
  entrambe le gambe. UFW inattivo è fail-closed: lo script non lo abilita per evitare lockout SSH.
- **Artefatto closeout:** `probe-r015-tls.ps1` usa trust di sistema e redirect off; controlla HTTP 404,
  TLS chain/hostname, HTTPS privata 404 e public 200 da URL letto via file ignorato, senza stamparlo.
- **Test:** edge operations **5/5 PASS**; gate combinato edge+packaging+release guard **14/14 PASS**;
  `bash -n`, parse PowerShell, Ruff e diff check PASS. Coperti inserimento top-level senza toccare il
  secret dashboard, byte-idempotenza, porta non canonica fail-closed e guard statici
  backup/rollback/trust.
- **Prossimo passo minimo:** sessione SSH interattiva sbloccata → apply unico → attesa emissione locale
  → probe strict completo. Claude verificherà appena disponibile; fino ad allora resta differito.

---

## 2026-07-26 — R0-D1 separa TLS core verde dal closeout LIVE

- **Decisione founder:** la passphrase SSH non è disponibile nella sessione corrente; nessuna
  modifica a FRPS, UFW o VPS viene eseguita. Il closeout TLS è posticipato senza attribuirgli PASS e
  senza cambiare ADR-011 Addendum I, HTTP-01, terminazione locale o P2 data-blind.
- **Evidenza read-only:** il founder osserva che il browser corrente apre il portale senza blocco. La
  coppia attiva in `data/tunnel/` è però ancora il self-signed del 2026-06-07 (`Issuer: FitManager
  Studio (self-signed)`, scadenza 2027-06-07), non una chain Let's Encrypt. L'osservazione resta
  evidenza UX locale, non public-trust PASS.
- **Probe:** DNS risolve correttamente, ma dal runner del gate 80/443 non sono risultate raggiungibili;
  nessun esito TLS è quindi dichiarato. Windows PowerShell non precarica `System.Net.Http` in questa
  baseline: il comando operativo ora esplicita il preload e il gate LIVE dovrà aggiungere un canary
  reale o rendere autonomo lo script prima del closeout.
- **Split ratificato:** **R0.1.5-core ✅** copre cert manager, trasporto client, installazione atomica,
  scheduler, packaging e tooling edge già verificati; **R0.1.5-live HOLD** conserva apply VPS, lato
  edge della route challenge e AC-R015-8 strict. R0.2 e poi R0.3 possono procedere perché indipendenti
  dalla trust chain; il LIVE resta interlock obbligatorio prima di R0.4 e quindi blocca ancora R0,
  P1 e candidate v1.0.15.
- **Fold-back:** riallineati SPEC R0, INDEX, SSoT tunnel/security e adapter root; release checklist già
  corretta e lasciata invariata. Nessuna ADR necessaria perché architettura e requisiti non cambiano.
- **Verifiche docs/process:** Ruff `api/` PASS; **10/10** SPEC aperte indicizzate; zero
  `SPEC_*`/`IMPL_PLAN_*` in `docs/technical/`; zero spec implementate rimaste vive; zero link locali
  rotti nei documenti toccati; zero vecchie formule di stato attive; `git diff --check` PASS.
  Nessuna suite applicativa richiesta: il gate modifica solo governance e stato documentale.
- **Prossimo gate:** checkpoint atomico R0-D1; poi R0.2 con GO e impact map separati. Nessuna
  remediation deep-link o apertura del blocco P è inclusa.

---

## 2026-07-26 — R0.2 chiude il binario unico di migrazione

- **Impact map eseguita:** sole procedure vive di migrazione/rehearsal e fonti operative backend;
  zero schema reale, revision Alembic, dati business, ledger, frontend, TLS o cleanup massivo dei 34
  sorgenti storici che nominano `crm_dev`.
- **RED:** il canary intercettato con Alembic stub fail-closed ha prodotto **3/3 failure causali**:
  `migrate-all.sh` ignorava il target configurato e forzava PROD+DEV, non rifiutava il legacy e il
  rehearsal richiedeva positivamente `crm_dev.db`.
- **Fix:** `migrate-all.sh` usa `DATABASE_URL` o il solo fallback `sqlite:///data/crm.db`, rifiuta
  `crm_dev.db` prima del subprocess e invoca esattamente una volta `alembic upgrade head`, senza
  stampare l'URL. Il rehearsal verifica `crm.db` come DB business e non contempla più il DB legacy.
  Root e `api/CLAUDE.md` convergono sullo script protetto e sul modello single-DB.
- **GREEN mirato:** canary finale **4/4**; canary + `schema_sync` + terminazione schema **22/22**;
  Ruff completo sui path Python, sintassi Bash e diff check verdi.
- **Full suite:** **910/910 PASS** in 20:11, 31 warning baseline. Il launcher della venv resta rotto
  perché punta a un interprete WindowsApps dismesso; la suite è stata eseguita con Python 3.12
  funzionante e i `site-packages` della stessa venv, senza installare o cambiare dipendenze.
- **Negative probe non occultato:** la replay Alembic su un file SQLite totalmente vuoto fallisce a
  `b4e89834fbef`, perché `2e74a22514ea` è uno stamp iniziale no-op. Il bootstrap autorevole crea lo
  schema corrente e lo stampa a head; R0.2 non riscrive la history e non scambia questo path grezzo
  per un PASS. Lo script è la procedura di migrazione di un DB business già bootstrapato/configurato.
- **Acceptance:** AC-R02-1..5 coperte. Nessuna procedura viva del gate ricrea un secondo DB; i guard
  build che nominano `crm_dev.db` per impedirne il leak restano correttamente invariati.
- **Coda:** R0.3 è il prossimo gate, solo dopo checkpoint R0.2 pushato e remoto `0 0` con GO separato;
  R0.1.5-live resta HOLD obbligatorio prima di R0.4/P.

---

## 2026-07-28 — R0.3 riallinea verità finanziaria e privacy frontend

- **Impact map eseguita:** sole superfici frontend read-only e relativi guard/documenti; zero API,
  hook, type wire, mutation, invalidazione, schema, dati, TLS/FRPS o apertura R0.4/P.
- **RED causale:** 4 failure Vitest hanno provato lordo al posto del netto in `ContrattiTab`, due
  importi nel preview cliente globale, stima `valore ~600` nello sheet e tour Clienti obsoleto. I
  due gemelli G8.4 sono falliti separatamente su formula residua e superficie profilo non coperta.
- **Fix:** `ContrattiTab` usa `netto_incassato` e, solo con rimborso, espone i campi wire
  `totale_versato`/`totale_rimborsato` come disclosure; Command Palette senza importi cliente;
  `ExpiringContractsSheet` senza stima prezzo/crediti; tour aderente a Nome, Contatti, Attenzioni,
  Ultimo Evento, Stato e Azioni. Nessun nuovo effect, stato, fetch o astrazione React.
- **GREEN:** pacchetto mirato **6/6**, suite frontend **161/161**, guard semantici **11/11**,
  ESLint sui path, Ruff sul guard, `git diff --check` e build Next/TypeScript (20 pagine) verdi.
  Restano soltanto i warning baseline della fixture Vitest `edge-cases` e della convenzione Next
  `middleware` deprecata.
- **Verifier avversariale:** **MONEY AXIS PRESERVED**. La posizione è un consumo del netto wire;
  zero sottrazioni, formule, mutation, endpoint, payload, hook, query invalidation, type o file
  backend/data/schema modificati. Il guard anti-vacuità include ora il profilo cliente.
- **Fold-back:** SPEC, INDEX, BUILD_LOG e `frontend/CLAUDE.md` allineati; nessun ADR necessario,
  perché R0.3 applica le regole esistenti G8.4/FE-0 senza introdurre policy di dominio.
- **Coda bloccata:** R0.1.5-live resta HOLD per assenza della passphrase. R0.4 può aprirsi soltanto
  dopo apply edge, chain pubblica e probe strict verificati; R0.3 non ha toccato il VPS.
