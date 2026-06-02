# CRM_ACCESS_ARCHITECTURE.md

**Progetto:** FitManager
**Versione:** 2.0
**Stato:** Draft per revisione implementativa
**Ambito:** Architettura di accesso e esposizione pubblica per software desktop distribuito
**Documento correlato:** `LEGAL_REGULATORY_REPORT.md` v1.3 (sezioni GDPR, autenticazione, dati sanitari)
**Sostituisce:** v1.0 (basata su assunzione errata di modello SaaS multi-tenant centralizzato)

---

## Nota preliminare per l'implementazione

Questo documento definisce **requisiti, principi di sicurezza e criteri di accettazione**. Le scelte implementative concrete (stack, librerie, pattern, struttura del codice) sono lasciate al giudizio dell'agente di sviluppo con visione reale del codebase. Le opzioni tecniche proposte in S5 sono **alternative valide a confronto**, non prescrizioni. L'obiettivo e' garantire che, qualunque sia il percorso scelto, i **criteri di accettazione (S7)** siano rispettati.

---

## 1. Contesto e modello di distribuzione

FitManager **non e' un SaaS centralizzato**. E' un'applicazione desktop distribuita come binario PyInstaller. Ogni trainer cliente installa il software sul proprio hardware (PC desktop, mini-PC, Raspberry Pi 5 o equivalente situato fisicamente nel proprio studio/palestra), che funge contemporaneamente da:

- Client di gestione del CRM (interfaccia trainer in locale, tipicamente su `localhost`)
- Server applicativo che ospita le pagine accessibili dal cliente finale tramite link

Il **database e' SQLite locale** all'istanza di ciascun trainer. Nessun dato sensibile risiede su infrastruttura di AVGV Technologies. Ogni installazione e' autonoma e isolata da tutte le altre.

### 1.1 Attori

| Attore | Ruolo | Dispositivo | Connettivita' richiesta |
|--------|-------|-------------|------------------------|
| **AVGV Technologies** (operatore piattaforma) | Sviluppo software, gestione infrastruttura di tunnel pubblico, rilascio aggiornamenti | VPS edge per tunnel + workstation sviluppo | -- |
| **Trainer** (cliente B2B) | Utilizza il CRM in locale per gestire i propri clienti finali | PC/Pi5 nel proprio studio + tablet/smartphone per accesso al CRM in LAN | Connessione Internet uscente (no port forwarding richiesto) |
| **Cliente finale del trainer** (utente B2C) | Compila anamnesi e feedback su schede di allenamento tramite link ricevuto dal trainer | Qualsiasi dispositivo con browser | Connessione Internet |

### 1.2 Conseguenze del modello distribuito sulla compliance GDPR

Il modello distribuito e' strutturalmente favorevole alla compliance:

- **AVGV Technologies e' fornitore di software**, non Data Processor dei dati clinici trattati. I dati sanitari (anamnesi, Art. 9 GDPR) non transitano sui server AVGV e non vi risiedono mai.
- **Ogni trainer e' autonomo Titolare del trattamento** dei dati dei propri clienti finali.
- **Non e' necessario DPA tra trainer e AVGV** per i dati clinici (il software non li accede). Resta consigliabile un EULA chiaro che espliciti questa separazione.
- **Il tunnel pubblico (vedi S5.1) deve essere "data-blind"**: il traffico cifrato end-to-end attraversa l'infrastruttura AVGV senza che AVGV possa leggerne il contenuto. Questa proprieta' va preservata come requisito di compliance, non solo di sicurezza.

Riferimento incrociato con `LEGAL_REGULATORY_REPORT.md` v1.3: la sezione "Ruoli GDPR" riflette che AVGV e' Titolare solo per dati propri (account, fatturazione, licenze, log infrastruttura di tunneling), mai dei dati clinici.

---

## 2. Vincoli di progetto

Ogni soluzione proposta o implementata deve rispettare i seguenti vincoli, definiti dal committente:

1. **Software locale, non SaaS centralizzato**: l'istanza FitManager gira sul hardware del trainer. Nessuna replica centrale dei dati clienti.
2. **Zero configurazione di rete lato trainer**: il trainer non configura DNS, port forwarding, IP statico, firewall, certificati. Tutto cio' che riguarda l'esposizione pubblica deve essere automatizzato dall'installer o dal software stesso.
3. **Zero installazioni e zero credenziali lato cliente finale**: il cliente finale apre il link ricevuto dal trainer e accede senza registrazione.
4. **Database SQLite locale per trainer**: nessun database centralizzato lato AVGV.
5. **Aggiornamenti via nuovo installer**: il trainer scarica e installa un nuovo PyInstaller quando rilasciato. Non esiste canale di auto-update remoto attivo permanentemente (eccetto eventualmente notifica di nuova versione disponibile).
6. **Disponibilita' legata al PC del trainer**: quando il PC e' spento il sistema e' offline; quando e' acceso e' raggiungibile. Comportamento atteso e accettato.
7. **Infrastruttura AVGV minima**: l'unico elemento server-side gestito da AVGV e' il tunnel edge che instrada il traffico cliente finale verso il PC del trainer. Nessun database, nessuna logica applicativa, nessun dato clinico.
8. **Costi sostenibili per la POC**: dominio AVGV (~10 euro/anno) + VPS edge tunnel (~4-6 euro/mese). Il trainer non sostiene costi infrastrutturali.

---

## 3. Threat model

### 3.1 Scenari di rischio

| ID | Scenario | Attore | Impatto | Probabilita' |
|----|----------|--------|---------|-------------|
| T1 | Cliente finale tronca URL del link e tenta accesso a CRM trainer | Cliente finale | Alto (data breach Art. 9) | Media |
| T2 | Cliente finale di trainer A tenta di accedere a link di cliente di trainer B (token o subdomain manipolato) | Cliente finale | Alto | Bassa |
| T3 | Link condiviso pubblicamente (screenshot, social, gruppo WhatsApp) | Cliente finale negligente | Medio | Media |
| T4 | Sessione CRM resta aperta su tablet condiviso in palestra | Terzi fisici in palestra | Alto | Media |
| T5 | Credenziali trainer compromesse | Attore esterno | Alto | Media |
| T6 | Intercettazione traffico su WiFi non protetta | Attore esterno | Medio (HTTPS mitiga) | Bassa |
| T7 | AVGV (o un dipendente) puo' leggere dati clinici in transito sul tunnel edge | AVGV stessa | Alto (compliance) | **Deve essere strutturalmente impossibile** |
| T8 | Tunnel edge AVGV compromesso da attore esterno | Attore esterno | Medio (se TLS e2e: solo metadata; se non e2e: catastrofico) | Bassa |
| T9 | Brute force su endpoint pubblico del tunnel | Attore esterno | Medio | Media |
| T10 | Trainer disinstalla software o cambia PC senza revocare link attivi | Trainer | Basso (link smettera' di funzionare) | Media |
| T11 | Token cliente finale resta valido oltre la durata necessaria | -- | Medio (compliance retention) | Alta se non gestito |
| T12 | Edge VPS AVGV down -> tutti i link clienti finali offline contemporaneamente | Guasto infrastruttura | Medio | Bassa |
| T13 | PC del trainer compromesso (malware, ransomware) | Attore esterno | Alto, ma fuori scope diretto del software | Bassa |

### 3.2 Principi di difesa

- **Defense in depth**: nessun singolo meccanismo e' l'unica barriera.
- **Least privilege**: ogni sessione accede solo alle risorse strettamente necessarie.
- **Separation of concerns**: l'area trainer (CRM completo in locale) e' logicamente e di rete separata dall'endpoint pubblico per cliente finale.
- **Zero trust sul path**: nessuna autorizzazione deve dipendere dalla conoscenza o complessita' di un URL.
- **End-to-end encryption obbligatoria sul tunnel**: AVGV non deve poter decifrare il traffico applicativo. Il tunnel veicola byte cifrati.
- **Data minimization**: i token non codificano dati personali; il contesto e' risolto server-side localmente sul PC del trainer.

---

## 4. Principi architetturali

I seguenti principi sono **vincolanti**; le scelte implementative sono libere purche' li rispettino.

### P1. Doppio piano di accesso: locale per trainer, pubblico-tunnellato per cliente finale

L'architettura espone due piani di accesso completamente separati:

- **Piano trainer (locale, LAN-only)**: il CRM gira su `localhost:<porta>` sul PC del trainer e/o e' raggiungibile dalla LAN dello studio. Accesso tipico da tablet/smartphone del trainer connessi al WiFi della palestra. **Non e' esposto al tunnel pubblico**. Mai.
- **Piano cliente finale (pubblico via tunnel)**: solo gli endpoint strettamente necessari (anamnesi, feedback schede) sono esposti via tunnel reverse e raggiungibili da Internet pubblica.

L'isolamento tra i due piani e' applicato a livello di binding di rete (interfacce diverse, porte diverse) **e** a livello applicativo (router separati, middleware che rifiuta accessi a route CRM da connessioni arrivate via tunnel pubblico, e viceversa).

### P2. Tunnel reverse data-blind operato da AVGV

L'esposizione pubblica avviene tramite tunnel reverse iniziato dal PC del trainer verso un edge gestito da AVGV. Il tunnel:

- E' inizializzato e mantenuto dal client integrato nell'installer; il trainer non lo configura
- Trasporta TLS end-to-end: il certificato di terminazione TLS risiede sul PC del trainer, non sull'edge AVGV
- L'edge AVGV vede solo: SNI/hostname (per routing), IP sorgente cliente, byte cifrati. Non puo' decifrare il body delle request ne' le response
- L'edge AVGV non logga il contenuto applicativo (solo metadata di routing/audit di sicurezza)

Questa proprieta' e' critica per la postura GDPR di AVGV (vedi S1.2).

### P3. Autenticazione trainer per accesso al CRM

Anche se il CRM e' raggiungibile solo in LAN, l'accesso richiede autenticazione locale. Lo studio e' uno spazio fisicamente non sempre presidiato e il WiFi puo' essere accessibile a terzi.

Meccanismi accettabili (singoli o combinati):

- Password locale + 2FA TOTP opzionale
- Passkey/WebAuthn locale
- PIN + biometrica del device del trainer
- Magic link interno (se SMTP configurato dal trainer) -- sconsigliato come unico metodo

Non accettabili come unico meccanismo: nessuna autenticazione, autenticazione bypassabile via flag, credenziali hardcoded, "trust della LAN" come unico criterio.

### P4. Accesso cliente finale via token firmato/opaco

Ogni link inviato al cliente finale e' un token che:

- Identifica univocamente la coppia (cliente finale, tipo di form/risorsa, istanza)
- Ha entropia >= 128 bit
- Ha scadenza configurabile dal trainer (default ragionevole, es. 30 giorni per anamnesi, durata della scheda per feedback allenamento)
- E' revocabile istantaneamente dal CRM del trainer
- Non codifica dati personali in chiaro
- E' associato server-side (cioe' sul PC del trainer) all'identita' e alla risorsa

Il formato (UUID random in tabella SQLite, JWT firmato con chiave locale del trainer, HMAC) e' scelta implementativa.

### P5. Authorization server-side su ogni route

Ogni endpoint deve verificare server-side:

- Identita' della richiesta (sessione trainer locale o token cliente finale valido)
- Diritto a quella specifica risorsa
- Origine della richiesta coerente con il piano di accesso (trainer da LAN/localhost, cliente finale da tunnel)

Nessuna authz su obscurity dell'URL, hidden fields, controlli solo client-side.

### P6. Isolamento per istanza, non per riga

Poiche' ogni trainer ha una propria istanza FitManager con proprio SQLite isolato, il principio classico di multi-tenancy con row-level filtering non si applica: **l'isolamento e' fisico**. Conseguenze:

- Non serve `tenant_id` nei record; ogni database e' gia' del trainer
- Il routing del tunnel edge instrada le richieste verso l'istanza giusta per subdomain o token; non c'e' rischio di "cross-tenant leakage" applicativo perche' le istanze non comunicano tra loro
- Il routing edge deve comunque essere robusto: una richiesta destinata al subdomain del trainer A non deve mai essere instradata all'istanza del trainer B (vedi criterio di accettazione 7.5)

**Nota implementativa (decisione codebase):** il codebase FitManager mantiene `trainer_id` come defense-in-depth anche se l'isolamento e' fisico per istanza. Questo non viola P6 -- e' una protezione aggiuntiva.

### P7. Sessioni limitate

- Durata massima sessione trainer: 4-12 ore (raccomandato 8h per uso lavorativo)
- Logout per inattivita': 20-60 minuti (suggerito 30 min per device condivisi in palestra)
- Re-autenticazione per operazioni sensibili: cambio password, export dati, eliminazione cliente, revoca token attivi in massa
- Token cliente finale ha vita propria, indipendente dalla sessione trainer

### P8. HTTPS ovunque, end-to-end

- Trasporto trainer<->CRM in LAN: HTTPS con certificato locale autogestito (mkcert o equivalente bundlato nell'installer), oppure HTTP solo su `localhost` (loopback interface)
- Trasporto cliente finale<->PC del trainer attraverso tunnel: TLS end-to-end, certificato pubblico (Let's Encrypt) emesso e rinnovato automaticamente sul PC del trainer per il suo subdomain `<slug>.fitmanagerstudio.com`
- Nessun "TLS termination sul VPS edge" -- questo violerebbe P2

### P9. Identita' di istanza e onboarding zero-touch

Ogni istanza FitManager ha un identificatore univoco (`instance_id` o `slug`) generato:

- Al primo avvio del software (auto-registrazione presso un servizio AVGV di issuance), oppure
- Pre-incluso nella licenza/installer personalizzato consegnato al trainer

L'`instance_id` determina:

- Il subdomain pubblico assegnato: `<instance_id>.fitmanagerstudio.com`
- L'identita' del tunnel client verso l'edge AVGV
- Il certificato Let's Encrypt da richiedere

Il trainer non sceglie ne' configura nulla di tutto questo: l'installer e il software gestiscono autonomamente.

### P10. Logging e audit

- Sul PC del trainer: ogni autenticazione, generazione/uso/revoca token, accesso a anamnesi e' loggato localmente (file rotato, retention configurabile dal trainer)
- Sull'edge AVGV: solo metadata di routing (timestamp, instance_id destinatario, IP sorgente, codice risposta), MAI contenuto applicativo
- Retention edge AVGV: limitata e documentata (raccomandato 30 giorni per security audit, poi anonimizzazione/cancellazione)

---

## 5. Opzioni tecniche di riferimento

Le opzioni seguenti sono **alternative a confronto**. La scelta spetta all'agente di sviluppo sulla base di stack reale, esperienza operativa e priorita' di progetto.

### 5.1 Tunnel reverse per esposizione pubblica

Questo e' il componente chiave dell'architettura. Confronto delle opzioni realistiche:

| Opzione | Modello | Vantaggi | Svantaggi | Frizione trainer | Costo AVGV |
|---------|---------|----------|-----------|------------------|------------|
| **FRP / rathole self-hosted su VPS AVGV** | Server tunnel self-hosted (`frps`/`rathole-server`) + client bundlato nell'installer | Pieno controllo, brand AVGV, scalabile, costo fisso, no sub-processor terzi (GDPR favorevole) | AVGV gestisce VPS, monitoring, scaling | Zero (installer fa tutto) | ~4-6 euro/mese VPS |
| **Cloudflare Tunnel** | `cloudflared` bundlato nell'installer, CF come edge | Edge globale, DDoS protection, HTTPS automatico, illimitato, free | Dipendenza Cloudflare (sub-processor da dichiarare in EULA), API CF per onboarding | Zero | Free |
| **Tailscale Funnel (attuale)** | Tailscale client + Funnel | Setup rapido | URL `*.ts.net` non brandizzato, limiti free tier, sub-processor Tailscale, modello non pensato per SaaS pubblico a scale | Bassa ma richiede account Tailscale | Free fino a limiti |
| **ngrok** | Tunnel SaaS | Setup molto rapido | Costo cresce con utenti, brand ngrok visibile o domain custom a pagamento | Zero (se token incluso in installer) | A pagamento per dominio custom |
| **WireGuard self-hosted + reverse proxy AVGV** | VPN site-to-site tra PC trainer e VPS AVGV | Massimo controllo low-level | Piu' complesso da automatizzare, gestione chiavi | Zero (installer fa tutto) | ~4-6 euro/mese VPS |

**Raccomandazione di principio**: per la POC e la prospettiva GDPR-favorevole, **FRP self-hosted su VPS AVGV** e' l'opzione piu' solida. **Cloudflare Tunnel viola P2** (CF termina TLS e vede il traffico, e' sub-processor). **Tailscale Funnel attuale e' da dismettere** per i motivi documentati.

### 5.2 Edge VPS AVGV -- architettura del nodo tunnel

Componenti minimi sul VPS edge (esempio per FRP, indicativo):

- **Server tunnel** (`frps` o `rathole-server`) in ascolto su porta dedicata
- **Reverse proxy** (Caddy raccomandato per gestione automatica wildcard cert se serve TLS in mezzo, oppure TCP passthrough puro se TLS end-to-end e' preservato)
- **DNS wildcard** `*.fitmanagerstudio.com` -> IP del VPS
- **Firewall** che espone solo porte necessarie (443 pubblica, porta tunnel server)
- **Monitoring** uptime e banda (es. Uptime Kuma, Netdata)
- **Backup configurazione** automatico

Per preservare TLS end-to-end (P2 + P8): il VPS edge fa **routing per SNI senza terminare TLS**. Il certificato Let's Encrypt e' emesso e gestito **sul PC del trainer**, non sul VPS.

### 5.3 Generazione e gestione certificati Let's Encrypt sul PC del trainer

Sfida: il PC del trainer e' dietro NAT, non risponde su porta 80 da Internet direttamente. ACME HTTP-01 challenge non funziona out-of-the-box.

Opzioni:

| Opzione | Pro | Contro |
|---------|-----|--------|
| **DNS-01 challenge** con API del provider DNS di `fitmanagerstudio.com` | Funziona sempre, no requisiti di esposizione porta 80 | Richiede credenziali API DNS sul PC trainer (gestire con cura, scope minimo) |
| **HTTP-01 attraverso il tunnel** | Riutilizza l'infrastruttura tunnel | Richiede coordinazione tunnel attivo durante challenge |
| **Wildcard cert centralizzato gestito da AVGV** | Trainer non gestisce nulla | **VIOLA P2** (TLS terminerebbe altrove): NON ACCETTABILE |

**Raccomandazione**: DNS-01 con API token scoped solo per record `_acme-challenge.<instance_id>.fitmanagerstudio.com`, distribuito dall'installer o richiesto al primo avvio tramite servizio AVGV di issuance.

### 5.4 Autenticazione trainer (accesso al CRM locale)

| Opzione | Pro | Contro |
|---------|-----|--------|
| Password locale (hash Argon2id) + 2FA TOTP opzionale | Standard, librerie ovunque, no dipendenze | Gestione reset richiede flusso locale |
| Passkey/WebAuthn locale (FIDO2) | UX eccellente, no password, sicurezza alta | Supporto su tutti i browser/device da verificare per pubblico trainer |
| OS-level auth integration (es. macOS Keychain, Windows Hello) | Massima integrazione | Frammentazione cross-OS, complessita' di gestione |

**Raccomandazione**: password + 2FA TOTP opzionale come baseline. Passkey come opzione aggiuntiva in Phase 2.

### 5.5 Token cliente finale

| Opzione | Pro | Contro |
|---------|-----|--------|
| UUID/random opaco in tabella SQLite (con hash del token) | Revoca banale, audit semplice | Una query DB per validazione (irrilevante a queste scale) |
| JWT firmato con chiave locale del trainer | Stateless | Revoca richiede blacklist o rotazione chiave (sovraingegneria per il caso) |

**Raccomandazione**: UUID opaco con hash in tabella `access_tokens` locale al SQLite del trainer.

### 5.6 Onboarding automatico nuovo trainer

Flusso suggerito (indicativo, implementazione libera):

1. Trainer acquista licenza -> AVGV genera `instance_id` univoco + token di onboarding
2. AVGV emette record DNS `<instance_id>.fitmanagerstudio.com` puntante al VPS edge (automatizzato via API)
3. AVGV consegna al trainer installer personalizzato (o installer generico + codice di attivazione)
4. Al primo avvio: l'installer/software si registra presso AVGV con il token, riceve la configurazione tunnel, richiede certificato Let's Encrypt via DNS-01, apre tunnel
5. Trainer crea account locale (email + password) per accedere al CRM
6. Sistema pronto. Trainer puo' iniziare a creare clienti e generare link.

---

## 6. Architettura logica di riferimento

```
        +--------------------------------------------------+
        |                  INTERNET PUBBLICA                |
        +---------+------------------------------+---------+
                  |                              |
                  | HTTPS (TLS end-to-end)       |
                  |                              |
                  v                              v
        +-----------------+              +-----------------+
        |  Cliente finale |              |  Cliente finale |
        |  di trainer A   |              |  di trainer B   |
        |  link tokenizzato              |  link tokenizzato
        +--------+--------+             +--------+--------+
                 |                                |
                 | richieste a                    |
                 | trainerA.fitmanagerstudio.com         | trainerB.fitmanagerstudio.com
                 |                                |
                 +------------+-------------------+
                              |
                              v
              +-------------------------------+
              |     VPS EDGE (AVGV)            |
              |  - DNS wildcard *.fitmanagerstudio.com|
              |  - Server tunnel (frps)        |
              |  - Routing SNI -> instance_id  |
              |  - NO TLS termination          |
              |  - NO logging contenuto        |
              |  - Solo metadata routing/audit  |
              +-------+---------------+--------+
                      |               |
            tunnel cifrato      tunnel cifrato
                      |               |
                      v               v
        +-------------------+  +-------------------+
        |   PC Trainer A    |  |   PC Trainer B    |
        |  (palestra A)     |  |  (palestra B)     |
        |                   |  |                   |
        |  +-------------+  |  |  +-------------+  |
        |  | FitManager  |  |  |  | FitManager  |  |
        |  | (Nuitka)    |  |  |  | (Nuitka)    |  |
        |  |             |  |  |  |             |  |
        |  | - Web server|  |  |  | - Web server|  |
        |  | - FRP client|  |  |  | - FRP client|  |
        |  | - TLS term  |  |  |  | - TLS term  |  |
        |  | - SQLite    |  |  |  | - SQLite    |  |
        |  | - Cert L.E. |  |  |  | - Cert L.E. |  |
        |  +-------------+  |  |  +-------------+  |
        |                   |  |                   |
        |  Route /admin/*   |  |  Route /admin/*   |
        |  -> solo da LAN   |  |  -> solo da LAN   |
        |                   |  |                   |
        |  Route /l/:token  |  |  Route /l/:token  |
        |  -> da tunnel     |  |  -> da tunnel     |
        +--------+----------+  +--------+----------+
                 |                       |
                 | LAN palestra          | LAN palestra
                 |                       |
                 v                       v
        +------------------+    +------------------+
        | Trainer A su     |    | Trainer B su     |
        | tablet/smartphone|    | tablet/smartphone|
        | accede CRM in LAN|    | accede CRM in LAN|
        +------------------+    +------------------+
```

**Invarianti critici:**

1. La route `/admin/*` accetta richieste **solo** se l'interfaccia di rete sorgente e' la LAN del trainer (localhost o IP della rete locale). Le richieste arrivate via tunnel verso `/admin/*` sono **rifiutate con 404**.
2. La route `/l/:token` accetta richieste **solo** dal tunnel pubblico (o opzionalmente anche da LAN per testing). Le richieste senza token valido sono rifiutate.
3. Il certificato TLS del subdomain `<instance_id>.fitmanagerstudio.com` e' generato, conservato e usato **esclusivamente sul PC del trainer**. AVGV non possiede ne' custodisce chiavi private dei trainer.
4. Il VPS edge AVGV instrada per SNI hostname senza ispezione ne' decifratura del traffico applicativo.

---

## 7. Criteri di accettazione

L'implementazione e' considerata conforme se e solo se soddisfa tutti i criteri seguenti, verificabili con test.

### 7.1 Isolamento piani di accesso

- [ ] Una richiesta a `/admin/*` arrivata via tunnel pubblico riceve 404 (non 401, non 403: il path non esiste dal piano pubblico).
- [ ] Una richiesta a `/l/:token` arrivata da LAN funziona normalmente (per facilitare test) ma non espone alcun dato di admin.
- [ ] Troncando un link cliente finale fino al solo subdomain (`https://<instance_id>.fitmanagerstudio.com/`), non si raggiunge alcuna pagina di login trainer ne' alcuna pagina admin.

### 7.2 Autenticazione trainer

- [ ] Il trainer accede al CRM da browser su tablet/smartphone in LAN senza installare nulla sul device client.
- [ ] L'accesso al CRM richiede credenziali; le password sono hashate con Argon2id (raccomandato) o bcrypt.
- [ ] Esiste un meccanismo di 2FA disponibile (anche se opzionale in POC).
- [ ] Login failures rate-limited per account e per IP della LAN.
- [ ] Cookie di sessione `httpOnly`, `Secure`, `SameSite=Lax`.

### 7.3 Sessione trainer

- [ ] La sessione scade per inattivita' (<= 60 min raccomandato).
- [ ] Esiste logout esplicito che invalida la sessione server-side.
- [ ] Operazioni sensibili richiedono re-autenticazione.

### 7.4 Token cliente finale

- [ ] Entropia >= 128 bit.
- [ ] Hash del token persistito (non il token in chiaro).
- [ ] Scadenza configurabile, default ragionevoli.
- [ ] Revocabile dal CRM trainer.
- [ ] Un token apre solo la sua specifica risorsa.
- [ ] Manipolazione del token produce errore generico.
- [ ] Rate limiting sugli endpoint di validazione.

### 7.5 Routing tunnel e isolamento istanze

- [ ] Una richiesta a `<trainerA>.fitmanagerstudio.com` raggiunge esclusivamente il PC del trainer A.
- [ ] Manipolare l'Host header non permette di raggiungere l'istanza di altri trainer.
- [ ] Il VPS edge non termina TLS: il certificato sul PC del trainer e' quello servito al cliente finale.
- [ ] Test di interruzione del tunnel su un'istanza: solo quella istanza diventa irraggiungibile, le altre continuano a funzionare.

### 7.6 TLS end-to-end

- [ ] HTTPS valido (Let's Encrypt) su tutti i subdomain attivi.
- [ ] Chiave privata del certificato risiede esclusivamente sul PC del trainer.
- [ ] Rinnovo certificato automatico (cron / scheduler interno al software).
- [ ] Test: dump del traffico al VPS edge non rivela contenuto applicativo decifrabile da AVGV.

### 7.7 Onboarding zero-touch

- [ ] Il trainer installa il PyInstaller e al primo avvio e' online senza aver configurato DNS, firewall, port forwarding o certificati.
- [ ] Tempo dall'avvio al primo link cliente generabile: <= 5 minuti (target POC).

### 7.8 Audit e logging

- [ ] Log locali sul PC trainer di tutte le auth e accessi a dati sensibili.
- [ ] Log VPS edge limitati a metadata di routing, mai contenuto.
- [ ] Retention documentata e implementata sia locale sia edge.

### 7.9 Resilienza

- [ ] Riavvio del PC trainer: tunnel si riconnette automaticamente entro <= 60s.
- [ ] Riavvio del VPS edge: tutti i tunnel si riconnettono entro <= 120s.
- [ ] Spegnimento PC trainer: link clienti restituiscono pagina informativa ("studio offline, riprovare piu' tardi") invece di errore generico.

### 7.10 Compliance GDPR

- [ ] Documentazione che AVGV non ha accesso ai dati clinici (confermato da P2 + 7.6).
- [ ] Privacy policy del trainer accessibile dalla pagina del link cliente finale.
- [ ] Diritto di revoca accessi garantito (revoca token).
- [ ] Retention policy documentata sia per audit log locali sia edge.

---

## 8. Roadmap migrazione da Tailscale Funnel

**Fase A -- Setup infrastruttura AVGV (interno, prima della POC)**
- Acquisto dominio `fitmanagerstudio.com` (se non gia' fatto)
- Provisioning VPS edge (Hetzner CX22 o equivalente)
- Deploy server tunnel (FRP) + reverse proxy SNI-routing
- Configurazione wildcard DNS `*.fitmanagerstudio.com`
- Sistema di issuance `instance_id` e provisioning DNS automatico
- Monitoring infrastruttura

**Fase B -- Integrazione nel build Nuitka**
- Bundling FRP client
- Implementazione modulo di onboarding (registrazione, ottenimento configurazione, richiesta certificato Let's Encrypt via DNS-01)
- Implementazione separazione route admin (LAN-only) vs route pubbliche (tunnel)
- Implementazione middleware authn/authz per entrambi i piani
- Test end-to-end su istanza pilota

**Fase C -- POC con primi 10 trainer**
- Onboarding manuale assistito dei primi trainer
- Monitoraggio uptime e raccolta feedback
- Iterazione su edge case (NAT particolari, ISP problematici, rete palestra)

**Fase D -- Dismissione Tailscale Funnel**
- Cessazione utilizzo Funnel per nuovi trainer
- Migrazione eventuali utilizzi residui
- Tailscale puo' rimanere come strumento interno di AVGV per accesso amministrativo ai propri sistemi (non piu' per esposizione pubblica trainer)

---

## 9. Rischi residui e aree aperte

| Rischio | Mitigazione | Status |
|---------|-------------|--------|
| Connessione Internet palestra instabile | Documentare requisito minimo; eventualmente cache offline lato client per form anamnesi | Da valutare |
| Trainer chiude il PC durante compilazione anamnesi cliente | Pagina informativa "offline"; eventuale notifica al trainer via canale alternativo | Da implementare |
| VPS edge AVGV e' SPOF per tutti i trainer | Phase 2: edge ridondato in due region, failover DNS | Phase 2 |
| Trainer disinstalla software senza prima esportare dati | EULA chiaro su backup; funzione export dati nel CRM | Da implementare |
| Compromissione PC trainer (malware, ransomware) | Fuori scope diretto; documentare best practice (backup, antivirus, OS aggiornato) in onboarding | Documentare |
| Conflitto IP/porte sulla LAN del trainer | Auto-detection porta libera all'avvio, fallback con UI di configurazione manuale | Da implementare |
| Certificato Let's Encrypt non rinnovato (PC spento per giorni a fine validita') | Notifica trainer + retry automatico al riavvio + grace period documentato | Da implementare |
| Conformita' Art. 9 GDPR su trasferimento dati attraverso edge AVGV | P2 (data-blind) + audit log + documentazione tecnica nel report compliance | Documentato |

---

## 10. Implicazioni per `LEGAL_REGULATORY_REPORT.md` v1.3

Il modello distribuito chiarito in questo documento ha implicazioni sul report compliance gia' riflesse nella v1.3 del LEGAL_REGULATORY_REPORT:

1. **Ruoli GDPR**: AVGV Technologies e' **fornitore di software**, non Data Processor dei dati clinici.
2. **DPA con trainer**: non necessario per dati clinici. EULA deve esplicitare che i dati clinici non transitano su AVGV.
3. **Sub-processor**: AVGV ha sub-processor solo per la propria infrastruttura di tunnel (es. provider VPS), non per dati clinici.
4. **DPIA**: il software gira sul cliente; eventuale DPIA e' responsabilita' del trainer come Titolare. AVGV fornisce documentazione tecnica di supporto.
5. **Data residency**: i dati clinici risiedono nel paese del trainer (presumibilmente Italia per POC). Nessun trasferimento extra-UE da parte di AVGV.

---

## 11. Riferimenti

- `LEGAL_REGULATORY_REPORT.md` v1.3
- `BUSINESS_PLAN.md`
- GDPR Reg. UE 2016/679 -- Art. 5, 9, 28, 32
- OWASP ASVS 4.0
- OWASP Session Management Cheat Sheet
- NIST SP 800-63B -- Digital Identity Guidelines
- WebAuthn / FIDO2 (W3C)
- ACME Protocol -- RFC 8555 (DNS-01 challenge)
- Documentazione FRP (https://github.com/fatedier/frp)

---

## 12. Changelog

| Versione | Data | Modifiche |
|----------|------|-----------|
| 1.0 | 2026-04-23 | Prima emissione (basata su assunzione errata di SaaS centralizzato) |
| 2.0 | 2026-04-23 | Riscrittura completa con modello corretto: PyInstaller distribuito, SQLite per-trainer, tunnel reverse data-blind. Aggiunte sezioni: S1.2 implicazioni GDPR del modello distribuito, S5.3 gestione certificati, S10 implicazioni per report compliance |
| 2.0.1 | 2026-06-01 | Inserito nel progetto FitManager. Aggiunta nota P6 su trainer_id defense-in-depth. Aggiornato S5.1 con raccomandazione FRP e esclusione CF per violazione P2. Allineamento a Nuitka build. |
