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

### Da fare (Fase 1)

- [x] 1.1 Instance ID nella licenza (claim + CLI + lettura)
- [x] 1.2 Configurazione tunnel (TunnelConfig, risoluzione path, config layer)
- [ ] 1.3 Script provisioning AVGV-side (DNS via Cloudflare API)
- [ ] 1.4 Tunnel manager (babysitter frpc)
- [ ] 1.5 Config FRP client (genera frpc.toml)
- [ ] 1.6 Bundle FRP binary (frpc.exe in Nuitka)
- [ ] 1.7 Auto-start tunnel (entry_point.py)
- [ ] 1.8 Health endpoint tunnel (/tunnel/status)
- [ ] 1.9 Test e2e (tunnel connesso, URL raggiungibile, reconnect)

---
