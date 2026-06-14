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
