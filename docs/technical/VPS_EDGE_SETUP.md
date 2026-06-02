# VPS_EDGE_SETUP.md

**Progetto:** FitManager AI Studio
**Versione:** 1.0
**Data:** 2026-06-02
**Autore:** AVGV Technologies (Giacomo Verardo)
**Stato:** Operativo — Fase 0 completata
**Prerequisito di:** `TUNNEL_MIGRATION_STRATEGY.md` Fase 1-3
**Documenti correlati:**
- `TUNNEL_MIGRATION_STRATEGY.md` v1.0 (piano di migrazione completo)
- `CRM_ACCESS_ARCHITECTURE.md` v2.0 (blueprint architetturale)
- `LEGAL_REGULATORY_REPORT.md` v1.3 (compliance GDPR)
- `TAILSCALE_FUNNEL_SETUP.md` (setup precedente, da archiviare a migrazione completata)

---

## 1. Panoramica

Questo documento descrive la configurazione completa dell'infrastruttura edge di AVGV Technologies per il sistema di tunnel FRP self-hosted. Questa infrastruttura sostituira' Tailscale Funnel come meccanismo di esposizione pubblica delle istanze FitManager dei trainer.

### Ruolo dell'infrastruttura edge

```
Cliente finale           VPS Edge (questo server)           PC Trainer
(smartphone)             (centralino AVGV)                  (palestra)
     |                         |                                |
     |  alessio.fitmanager     |                                |
     |    studio.com           |                                |
     |------------------------>|  SNI routing + TCP passthrough  |
     |                         |------------------------------->|
     |                         |                                |
     |                         |    risposta cifrata TLS        |
     |                         |<-------------------------------|
     |   risposta cifrata TLS  |                                |
     |<------------------------|                                |
```

**Proprieta' critica (P2 — data-blind):** il VPS edge instrada traffico TLS cifrato senza terminarlo. AVGV non puo' leggere il contenuto delle comunicazioni tra cliente finale e PC del trainer. Il certificato TLS risiede sul PC del trainer, non sul VPS.

---

## 2. Dominio

### 2.1 Registrazione

| Proprieta' | Valore |
|------------|--------|
| **Dominio** | `fitmanagerstudio.com` |
| **Registrar** | Cloudflare Registrar |
| **Data registrazione** | 2026-06-02T14:51:53Z |
| **Account** | G.verardo87@gmail.com |
| **WHOIS privacy** | Attiva (Cloudflare redacted) |
| **Rinnovo** | Annuale, $10.46/anno |
| **DNS provider** | Cloudflare DNS (incluso nel registrar) |

### 2.2 Scelta del dominio

`fitmanager.it` non era disponibile (ne' su Cloudflare ne' su Namecheap). `fitmanager.com` non era disponibile. `fitmanagerstudio.com` scelto per coerenza con il nome prodotto "FitManager AI Studio" e per posizionamento internazionale (.com > .it per software B2B).

### 2.3 Record DNS configurati

| Tipo | Nome | Valore | Proxy | TTL | Scopo |
|------|------|--------|-------|-----|-------|
| `A` | `*` | `128.140.91.39` | DNS only (grigio) | Auto | Wildcard: qualsiasi `*.fitmanagerstudio.com` punta al VPS edge |

**Proxy status = DNS only (nuvola grigia):** critico. Se fosse arancione (Proxied), Cloudflare intercetterebbe il traffico TLS, violando il principio P2 (data-blind). Con DNS only, Cloudflare fa solo da rubrica — risponde "l'IP e' 128.140.91.39" e basta.

**Wildcard vs record individuali:** un singolo record wildcard copre tutti i trainer presenti e futuri. Non serve creare un record DNS per ogni nuovo trainer. Il routing per-trainer e' gestito da FRP tramite il campo `customDomains` nella configurazione di ogni FRP client.

### 2.4 Verifica DNS

```bash
# Test eseguito il 2026-06-02
$ dig test.fitmanagerstudio.com +short
128.140.91.39

$ dig alessio-crociani.fitmanagerstudio.com +short
128.140.91.39

$ dig qualsiasi-slug.fitmanagerstudio.com +short
128.140.91.39
```

Tutti i subdomain risolvono allo stesso IP. Il differenziamento avviene a livello FRP (SNI routing).

---

## 3. VPS Edge

### 3.1 Specifiche server

| Proprieta' | Valore |
|------------|--------|
| **Provider** | Hetzner Cloud |
| **Account** | Giacomo Verardo (G.verardo87@gmail.com) |
| **Progetto** | Default |
| **Nome server** | `fitmanagerstudio-edge` |
| **Tipo** | CPX22 (Shared vCPU, Regular Performance) |
| **CPU** | 2 vCPU (AMD) |
| **RAM** | 4 GB |
| **Disco** | 80 GB SSD |
| **Location** | Falkenstein, Germania (eu-central) |
| **IP pubblico IPv4** | `128.140.91.39` |
| **IP pubblico IPv6** | `2a01:4f8:c013:2f66::1` |
| **Sistema operativo** | Ubuntu 26.04 LTS |
| **Kernel** | 7.0.0-22-generic (aggiornato 2026-06-02) |
| **Costo** | ~4.50 EUR/mese (IVA 22% inclusa) |
| **Data creazione** | 2026-06-02 |

### 3.2 Scelta del provider

Hetzner scelto per:
- **GDPR compliance**: azienda tedesca, datacenter in UE (Germania)
- **Costo**: il piu' economico tra i provider UE affidabili (~4.50 EUR/mese vs ~5-6 EUR DigitalOcean/Vultr)
- **Affidabilita'**: SLA 99.9%, rete 1Gbps
- **Semplicita'**: console Cloud intuitiva, API disponibile per automazione futura

### 3.3 Scelta Regular Performance vs Cost-Optimized

Scelto "Regular Performance" (hardware recente) anziche' "Cost-Optimized" (hardware legacy con "limited availability"). Per un server edge always-on che gestisce connessioni di tutti i trainer, l'affidabilita' hardware e' prioritaria rispetto al risparmio di ~1-2 EUR/mese.

---

## 4. Accesso SSH

### 4.1 Configurazione

| Proprieta' | Valore |
|------------|--------|
| **Tipo chiave** | Ed25519 |
| **File chiave privata** | `C:\Users\gvera\.ssh\id_ed25519` |
| **File chiave pubblica** | `C:\Users\gvera\.ssh\id_ed25519.pub` |
| **Label su Hetzner** | `giacomo-avgv-hetzner` |
| **Passphrase** | Si (richiesta ad ogni connessione) |
| **Utente** | `root` |

### 4.2 Comando di connessione

```bash
ssh -i ~/.ssh/id_ed25519 root@128.140.91.39
```

### 4.3 Fingerprint del server

Il fingerprint ED25519 del server e' stato accettato e salvato in `~/.ssh/known_hosts` alla prima connessione (2026-06-02). Se cambia, SSH rifiutera' la connessione (protezione da man-in-the-middle).

### 4.4 Note operative

- La connessione richiede la passphrase della chiave SSH ad ogni sessione
- Da PowerShell (Windows): usare `ssh -i ~/.ssh/id_ed25519 root@128.140.91.39`
- Da Git Bash: stesso comando
- Nano come editor di testo sul server (`nano <file>`, salva con Ctrl+O → Invio, esci con Ctrl+X)

---

## 5. Hardening del server

### 5.1 Aggiornamenti sistema

```bash
apt update && apt upgrade -y
```

Eseguito il 2026-06-02. Kernel aggiornato da 7.0.0-15 a 7.0.0-22. 14 pacchetti aggiornati (sicurezza LTS).

### 5.2 Firewall (ufw)

```bash
apt install -y ufw
ufw allow 22/tcp comment 'SSH'
ufw allow 443/tcp comment 'HTTPS tunnel'
ufw allow 7000/tcp comment 'FRP bind'
ufw --force enable
```

**Stato firewall attivo:**

| Porta | Protocollo | Scopo | Accessibile da |
|-------|-----------|-------|----------------|
| 22/tcp | SSH | Amministrazione server (solo AVGV) | Qualsiasi IP (protetto da chiave SSH) |
| 443/tcp | HTTPS | Traffico clienti finali verso i tunnel | Internet pubblica |
| 7000/tcp | TCP | Connessioni FRP client (PC trainer → VPS) | Internet pubblica |

Tutte le altre porte sono bloccate. Sia IPv4 che IPv6.

**Nota sicurezza futura:** considerare di restringere la porta 22 ai soli IP di AVGV (`ufw allow from <IP_AVGV> to any port 22`) quando l'IP dell'ufficio sara' stabile. Per ora accetta da qualsiasi IP, protetto dalla chiave SSH con passphrase.

### 5.3 Fail2ban

```bash
apt install -y fail2ban
```

Installato con configurazione default. Protegge SSH da tentativi di brute force: dopo 5 tentativi falliti in 10 minuti, l'IP viene bannato per 10 minuti. Servizio abilitato e attivo all'avvio.

### 5.4 Stato servizi di sicurezza

```bash
# Verifica
systemctl status ufw       # active
systemctl status fail2ban  # active (running)
```

---

## 6. FRP Server

### 6.1 Installazione

```bash
cd /opt
curl -sL https://github.com/fatedier/frp/releases/download/v0.61.1/frp_0.61.1_linux_amd64.tar.gz | tar xz
mv frp_0.61.1_linux_amd64 frp
```

| Proprieta' | Valore |
|------------|--------|
| **Versione** | 0.61.1 |
| **Percorso installazione** | `/opt/frp/` |
| **Binario server** | `/opt/frp/frps` |
| **Binario client** | `/opt/frp/frpc` (presente ma non usato sul VPS) |
| **Configurazione** | `/opt/frp/frps.toml` |
| **Log** | `/var/log/frps/frps.log` |
| **Fonte** | https://github.com/fatedier/frp/releases |

### 6.2 Configurazione (`/opt/frp/frps.toml`)

```toml
bindPort = 7000
vhostHTTPSPort = 443

[webServer]
addr = "127.0.0.1"
port = 7500
user = "admin"
password = "FitMgr-Edge-2026!"

[log]
to = "/var/log/frps/frps.log"
level = "info"
maxDays = 30
```

**Spiegazione parametri:**

| Parametro | Valore | Significato |
|-----------|--------|-------------|
| `bindPort` | 7000 | Porta su cui i FRP client (PC trainer) si collegano al server |
| `vhostHTTPSPort` | 443 | Porta su cui arriva il traffico HTTPS dei clienti finali. FRP fa SNI routing: legge l'hostname dalla richiesta TLS (senza decifrare) e la inoltra al tunnel del trainer corretto |
| `webServer.addr` | 127.0.0.1 | Dashboard admin accessibile solo localmente (non da Internet) |
| `webServer.port` | 7500 | Porta della dashboard admin |
| `webServer.user` | admin | Username dashboard |
| `webServer.password` | FitMgr-Edge-2026! | Password dashboard |
| `log.to` | /var/log/frps/frps.log | File di log |
| `log.level` | info | Livello di logging |
| `log.maxDays` | 30 | Retention log: 30 giorni poi cancellazione automatica |

**Dashboard admin:** accessibile solo dal server stesso (bind su 127.0.0.1). Per accedervi da remoto, usare SSH tunnel:

```bash
# Dal PC AVGV (Windows/PowerShell):
ssh -L 7500:127.0.0.1:7500 -i ~/.ssh/id_ed25519 root@128.140.91.39
# Poi aprire nel browser: http://localhost:7500
# Login: admin / FitMgr-Edge-2026!
```

### 6.3 Servizio systemd (`/etc/systemd/system/frps.service`)

```ini
[Unit]
Description=FRP Server for FitManagerStudio
After=network.target

[Service]
Type=simple
ExecStart=/opt/frp/frps -c /opt/frp/frps.toml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Comportamento:**
- Si avvia automaticamente al boot del server (`enabled`)
- Se il processo crolla, si riavvia dopo 5 secondi (`Restart=always`, `RestartSec=5`)
- Avviato dopo che la rete e' disponibile (`After=network.target`)

### 6.4 Comandi di gestione

```bash
# Stato
systemctl status frps

# Riavvio (dopo modifica configurazione)
systemctl restart frps

# Stop
systemctl stop frps

# Log in tempo reale
journalctl -u frps -f

# Log dal file
tail -f /var/log/frps/frps.log
```

### 6.5 Verifica post-installazione

```bash
# Eseguito il 2026-06-02
$ systemctl status frps
● frps.service - FRP Server for FitManagerStudio
     Loaded: loaded (/etc/systemd/system/frps.service; enabled; preset: enabled)
     Active: active (running) since Tue 2026-06-02 18:46:06 UTC
   Main PID: 7571 (frps)
```

---

## 7. Architettura di rete risultante

```
                    INTERNET
                       |
                       v
            ┌──────────────────┐
            │  Cloudflare DNS  │
            │  (solo rubrica)  │
            │                  │
            │  *.fitmanager    │
            │  studio.com     │
            │  → 128.140.91.39│
            └────────┬─────────┘
                     |
                     v
     ┌───────────────────────────────┐
     │  VPS: fitmanagerstudio-edge   │
     │  128.140.91.39                │
     │  Hetzner, Falkenstein (DE)    │
     │                               │
     │  ┌─────────┐  ┌────────────┐ │
     │  │ ufw     │  │ fail2ban   │ │
     │  │ 22,443, │  │ SSH guard  │ │
     │  │ 7000    │  │            │ │
     │  └─────────┘  └────────────┘ │
     │                               │
     │  ┌─────────────────────────┐ │
     │  │ frps (FRP Server)       │ │
     │  │ porta 7000: bind client │ │
     │  │ porta 443: HTTPS vhost  │ │
     │  │ SNI routing (no TLS     │ │
     │  │ termination)            │ │
     │  └────────────┬────────────┘ │
     └───────────────┼───────────────┘
                     │
          tunnel cifrato (porta 7000)
                     │
          ┌──────────┴──────────┐
          v                     v
   ┌─────────────┐      ┌─────────────┐
   │ PC Trainer A │      │ PC Trainer B │
   │ frpc client  │      │ frpc client  │
   │ TLS termina  │      │ TLS termina  │
   │ qui          │      │ qui          │
   └─────────────┘      └─────────────┘
```

---

## 8. Flusso di una richiesta (end-to-end)

1. Il cliente finale apre `https://alessio-crociani.fitmanagerstudio.com/public/workout/abc123`
2. Il browser chiede al DNS: "qual e' l'IP di alessio-crociani.fitmanagerstudio.com?"
3. Cloudflare DNS risponde: `128.140.91.39` (wildcard match)
4. Il browser si connette a `128.140.91.39:443` e inizia un handshake TLS
5. FRP server (frps) legge l'SNI hostname dalla richiesta TLS: `alessio-crociani.fitmanagerstudio.com`
6. FRP server cerca tra i client connessi quale ha `customDomains = ["alessio-crociani.fitmanagerstudio.com"]`
7. FRP server inoltra i byte TLS cifrati (senza decifrare) attraverso il tunnel al PC del trainer
8. Il PC del trainer (frpc) riceve i byte e li passa al server locale (Next.js su porta 3000)
9. Next.js risponde con la pagina dell'allenamento
10. La risposta torna indietro per lo stesso percorso, sempre cifrata

**In nessun punto del percorso AVGV puo' leggere il contenuto.** Il VPS vede solo:
- Che qualcuno ha chiesto `alessio-crociani.fitmanagerstudio.com` (SNI hostname, in chiaro nel TLS handshake)
- L'IP del cliente finale
- La quantita' di byte scambiati
- Nient'altro

---

## 9. Costi operativi

| Voce | Costo | Frequenza |
|------|-------|-----------|
| Dominio `fitmanagerstudio.com` | $10.46 (~9.50 EUR) | Annuale |
| VPS Hetzner CX22 | ~4.50 EUR | Mensile |
| **Totale annuo** | **~63.50 EUR** | — |

Costo sostenuto interamente da AVGV Technologies. I trainer non hanno costi infrastrutturali.

---

## 10. Ruolo operativo AVGV post-vendita

### 10.1 Il VPS e' infrastruttura permanente

Il VPS edge e' il centralino che smista le richieste dei clienti finali verso i PC dei trainer. Deve restare acceso 24/7 finche' esiste almeno un trainer con licenza attiva. Se il VPS viene spento, **tutti** i link pubblici di **tutti** i trainer smettono di funzionare contemporaneamente.

Questo significa che AVGV Technologies, dopo la vendita di ogni licenza, mantiene un ruolo operativo permanente: la gestione dell'infrastruttura edge.

### 10.2 Attivita' ricorrenti AVGV

| Attivita' | Frequenza | Sforzo | Note |
|-----------|-----------|--------|------|
| Pagamento VPS Hetzner (~4.50 EUR/mese) | Mensile | Zero (addebito automatico) | Impostare addebito su carta |
| Pagamento dominio (~$10.46/anno) | Annuale | Zero (auto-rinnovo Cloudflare) | Verificare una volta l'anno |
| Aggiornamento sistema (`apt upgrade`) | Mensile | 5 minuti | Collegamento SSH, un comando |
| Aggiornamento FRP (se versione critica) | Raro (1-2 volte/anno) | 10 minuti | Solo se bugfix/sicurezza |
| Monitoraggio uptime | Continuo | Zero (automatizzabile) | Uptime Kuma in Fase 0.7 |

### 10.3 Attivita' per-trainer (solo al momento della vendita)

| Attivita' | Quando | Sforzo | Comando |
|-----------|--------|--------|---------|
| Generare licenza con `instance_id` | Vendita | 1 minuto | `generate_license.py sign --instance-id <slug> ...` |
| Annotare nel registro trainer | Vendita | 1 minuto | Aggiornare `docs/operations/DEPLOYMENTS.md` |

**Non serve** creare record DNS, configurare FRP server, o toccare il VPS per ogni nuovo trainer. Il wildcard DNS + FRP gestiscono tutto automaticamente.

### 10.4 Scalabilita' dei costi

Il costo dell'infrastruttura edge e' **fisso**, non scala con il numero di trainer:

| Trainer attivi | Costo VPS | Costo per trainer |
|----------------|-----------|-------------------|
| 1 | 4.50 EUR/mese | 4.50 EUR/mese |
| 10 | 4.50 EUR/mese | 0.45 EUR/mese |
| 50 | 4.50 EUR/mese | 0.09 EUR/mese |
| 100+ | ~9 EUR/mese (upgrade CX32) | ~0.09 EUR/mese |

Il costo annuo (~63.50 EUR) e' coperto gia' dal primo abbonamento PRO (79 EUR/anno). Con 10 trainer PRO il costo edge e' trascurabile rispetto ai ricavi.

L'upgrade a un VPS piu' grande (CX32: 4 vCPU, 8GB RAM, ~7 EUR/mese) sara' necessario solo superati i ~100 trainer connessi simultaneamente, dato che FRP gestisce connessioni TCP leggere.

---

## 11. Manutenzione ordinaria (procedure)

### 11.1 Aggiornamenti sistema (mensile)

```bash
ssh -i ~/.ssh/id_ed25519 root@128.140.91.39
apt update && apt upgrade -y
```

Se il kernel viene aggiornato, riavviare il server:

```bash
reboot
```

FRP si riavviera' automaticamente (systemd). I tunnel dei trainer si riconnettono entro 60 secondi.

### 11.2 Aggiornamento FRP (quando necessario)

```bash
# 1. Verificare nuova versione su https://github.com/fatedier/frp/releases
# 2. Scaricare e sostituire
cd /opt
systemctl stop frps
curl -sL https://github.com/fatedier/frp/releases/download/v<NUOVA>/frp_<NUOVA>_linux_amd64.tar.gz | tar xz
cp frp_<NUOVA>_linux_amd64/frps /opt/frp/frps
cp frp_<NUOVA>_linux_amd64/frpc /opt/frp/frpc
rm -rf frp_<NUOVA>_linux_amd64
systemctl start frps
systemctl status frps
```

### 11.3 Rotazione log

I log FRP ruotano automaticamente (maxDays = 30). Verificare periodicamente lo spazio disco:

```bash
df -h /
du -sh /var/log/frps/
```

### 11.4 Monitoraggio

Verifica rapida che tutto funzioni:

```bash
systemctl status frps        # FRP attivo?
ufw status                   # Firewall attivo?
fail2ban-client status       # Fail2ban attivo?
df -h /                      # Spazio disco?
uptime                       # Da quanto e' acceso?
```

---

## 12. Disaster recovery

### 12.1 Server irrecuperabile

Se il VPS viene distrutto o compromesso:

1. Creare nuovo VPS Hetzner con stesse specifiche (CPX22, Falkenstein, Ubuntu)
2. Ripetere Step 2-5 di questo documento (hardening + FRP)
3. Aggiornare il record DNS wildcard su Cloudflare con il nuovo IP
4. I FRP client dei trainer si riconnetteranno automaticamente (se configurati con hostname `edge.fitmanagerstudio.com` anziche' IP diretto)

**Tempo stimato di ripristino:** 30-60 minuti.

### 12.2 Dominio

Il dominio `fitmanagerstudio.com` e' registrato su Cloudflare con auto-rinnovo. Se l'account Cloudflare viene perso, contattare il supporto Cloudflare con i dati di registrazione. Mantenere le credenziali dell'account in un password manager sicuro.

---

## 13. Credenziali e accessi (registro AVGV)

| Servizio | URL/Host | Username | Nota |
|----------|----------|----------|------|
| Cloudflare | dash.cloudflare.com | G.verardo87@gmail.com | Registrar + DNS |
| Hetzner Cloud | console.hetzner.cloud | G.verardo87@gmail.com | VPS |
| VPS SSH | 128.140.91.39:22 | root | Chiave Ed25519 con passphrase |
| FRP Dashboard | 127.0.0.1:7500 (via SSH tunnel) | admin | Password: FitMgr-Edge-2026! |

**IMPORTANTE:** queste credenziali devono essere conservate in un password manager sicuro (es. 1Password, Bitwarden). La password della dashboard FRP dovra' essere cambiata prima del go-live con i primi trainer.

---

## 14. Checklist di validazione Fase 0

| # | Criterio | Stato | Data |
|---|----------|-------|------|
| 0.1 | Dominio registrato e attivo | OK | 2026-06-02 |
| 0.2 | VPS creato e raggiungibile via SSH | OK | 2026-06-02 |
| 0.3 | Sistema aggiornato (kernel + pacchetti) | OK | 2026-06-02 |
| 0.4 | Firewall attivo (22, 443, 7000) | OK | 2026-06-02 |
| 0.5 | Fail2ban attivo | OK | 2026-06-02 |
| 0.6 | DNS wildcard configurato e verificato | OK | 2026-06-02 |
| 0.7 | FRP server installato (v0.61.1) | OK | 2026-06-02 |
| 0.8 | FRP server configurato e attivo (systemd) | OK | 2026-06-02 |
| 0.9 | FRP server auto-start al boot | OK | 2026-06-02 |
| 0.10 | Test e2e tunnel con FRP client | OK | 2026-06-02 |

### Test e2e Fase 0.10 (2026-06-02)

**Obiettivo:** verificare che il tunnel FRP trasporta traffico dal VPS edge al PC di sviluppo (Windows) e che il frontend risponde attraverso il tunnel.

**Prerequisiti del test:**
- Frontend dev attivo su `localhost:3001` (PC Windows AVGV)
- FRP server attivo sul VPS (`frps` su porta 7000)
- Porta 8080 aperta temporaneamente sul firewall VPS (`ufw allow 8080/tcp`)

**Setup FRP client di test:**

1. Scaricato `frpc.exe` v0.61.1 (Windows amd64, ~15MB) in `tools/bin/frpc.exe`
2. Creato file di configurazione test `data/tunnel/frpc-test.toml`:

```toml
serverAddr = "128.140.91.39"
serverPort = 7000

[[proxies]]
name = "test-tunnel"
type = "tcp"
localIP = "127.0.0.1"
localPort = 3001
remotePort = 8080
```

Questa configurazione dice al client FRP: "collegati al server FRP sul VPS (128.140.91.39:7000) e apri un proxy TCP che mappa la porta 8080 del VPS alla porta 3001 del mio PC locale (dove gira Next.js)".

3. Avviato il client FRP dal PC Windows:

```bash
tools/bin/frpc.exe -c data/tunnel/frpc-test.toml
```

Output:
```
2026-06-02 21:16:17 [I] login to server success, get run id [3dc73bde2c21cd86]
2026-06-02 21:16:17 [I] proxy added: [test-tunnel]
```

Il client si e' connesso al server e ha registrato il proxy `test-tunnel`.

**Esecuzione del test:**

Dal VPS, eseguito:

```bash
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080
```

Risposta: `307` (HTTP redirect al login di FitManager).

**Interpretazione:** la richiesta ha percorso il cammino completo:

```
curl sul VPS (127.0.0.1:8080)
  → frps riceve sulla porta 8080
    → frps inoltra via tunnel al frpc sul PC Windows
      → frpc passa a localhost:3001
        → Next.js risponde con 307 (redirect a /login)
          → la risposta torna indietro per lo stesso percorso
            → curl riceve HTTP 307
```

Il frontend del PC Windows e' stato raggiunto dal VPS attraverso il tunnel FRP. Il traffico ha attraversato Internet (VPS in Germania → PC in Italia) in modo trasparente.

**Cleanup post-test:**
- Fermato `frpc.exe` sul PC Windows
- Fermato frontend dev
- Rimossa porta 8080 dal firewall VPS (`ufw delete allow 8080/tcp`)
- Il file `data/tunnel/frpc-test.toml` e `tools/bin/frpc.exe` restano per test futuri

**Nota:** questo test usa un proxy TCP senza TLS (tipo `tcp`, porta HTTP 8080). Il test completo con TLS end-to-end (tipo `https`, porta 443, certificato Let's Encrypt) sara' eseguito nella Fase 2 quando il cert manager sara' implementato. Il test attuale valida la connettivita' di base del tunnel: FRP client si collega al server, il traffico viene inoltrato correttamente, e il frontend risponde.

---

## 15. Prossimi passi (Fase 1)

Completata l'infrastruttura edge, la Fase 1 prevede:

1. Aggiungere claim `instance_id` nella licenza JWT (`generate_license.py`)
2. Leggere `instance_id` dal servizio licenza backend (`api/services/license.py`)
3. Creare `tunnel_manager.py` per gestire il ciclo di vita FRP client
4. Bundlare `frpc.exe` nel build Nuitka
5. Auto-start tunnel al boot di FitManager
6. Test e2e: PC dev → tunnel → `test.fitmanagerstudio.com` raggiungibile

Dettagli in `TUNNEL_MIGRATION_STRATEGY.md` sezione 4, Fase 1.

---

## Changelog

| Versione | Data | Modifiche |
|----------|------|-----------|
| 1.0 | 2026-06-02 | Prima emissione. Fase 0 completata: dominio, VPS, hardening, FRP server, DNS wildcard. |
