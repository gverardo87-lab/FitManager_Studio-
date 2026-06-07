# BUILD_LOG.md

**Progetto:** FitManager — migrazione tunnel + infrastruttura AVGV
**Scopo:** diario cronologico di cosa ho fatto, giorno per giorno. Risponde a "cosa ho fatto e quando". Per il "perche' / cosa ho imparato" rimanda ai file `LEARNING_*.md`.
**Metodo:** vedi `LEARNING_METHOD.md`
**Documenti di riferimento:** `TUNNEL_MIGRATION_STRATEGY.md`, `CRM_ACCESS_ARCHITECTURE.md`

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
- [ ] 1.6 Bundle FRP binary (frpc.exe in Nuitka)
- [ ] 1.7 Script provisioning AVGV-side (DNS via Cloudflare API)
- [ ] 1.8 Health endpoint tunnel (/tunnel/status)

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

---
