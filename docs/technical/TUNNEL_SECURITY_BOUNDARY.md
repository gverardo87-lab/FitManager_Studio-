# Tunnel Security Boundary — Acceptance Criteria (Strada B)

**Stato:** binding (`docs/technical/`)
**Contesto:** Apertura del CRM all'accesso del trainer da qualunque rete, via tunnel FRP.
**Versione:** 1.0
**Premessa critica:** fino all'introduzione di questo documento il tunnel serviva *esclusivamente* gli atleti (`/api/public/*`). Strada B espone il CRM su Internet. Il modello di minaccia passa da **"rete locale fidata"** a **"esposto su Internet"**. Ogni assunzione basata sulla fiducia della rete locale è da considerarsi non più valida.

Questo documento specifica *cosa deve essere vero*, non *come implementarlo*. L'implementazione è libera di adattarsi al codebase reale.

---

## 0. Principio fondante

> **L'autorizzazione trainer-vs-atleta è una proprietà del JWT firmato, verificata lato FastAPI. Non è una proprietà del path, dell'header `Host`, della rete di origine, né di alcun meccanismo a livello Next.js.**

Tutto ciò che precede FastAPI (Next.js middleware, Tunnel Guard, routing SNI sul VPS) è **difesa in profondità**: utile, ma non è il confine. Il confine è crittografico e vive nel layer applicativo Python, perché è l'unico punto che un client non può aggirare senza possedere la chiave privata di firma.

---

## 1. Ruolo nel JWT (AC-1) — BLOCCANTE

**Cosa deve essere vero:**

- Il JWT emesso da `create_access_token` per un trainer DEVE contenere un claim di ruolo esplicito (es. `role: "trainer"`).
- I token emessi per gli atleti dal portale pubblico DEVONO contenere un claim di ruolo distinto (es. `role: "athlete"`) e DEVONO avere scope ristretto al solo atleta cui si riferiscono.
- I due tipi di token NON devono essere intercambiabili: un token atleta non deve mai soddisfare un controllo che richiede ruolo trainer, e viceversa per gli endpoint che eventualmente devono restare athlete-only.
- Il ruolo DEVE essere dentro il payload firmato (quindi protetto da manomissione), MAI derivato da header, path o hostname.

**Criterio di accettazione:**
Decodificando un token trainer e un token atleta, i rispettivi `role` sono distinti e presenti. Un token a cui venga alterato il campo `role` in chiaro fallisce la verifica di firma.

**Nota su token già emessi:** i trainer registrati prima di AC-1 hanno token senza `role`. La verifica (AC-2) deve trattare l'assenza di `role` come **non autorizzato** (fail-closed), non come "trainer per default". Questo forza un re-login pulito e impedisce che vecchi token diventino un bypass.

---

## 2. Verifica del ruolo lato FastAPI (AC-2) — BLOCCANTE, è IL confine

**Cosa deve essere vero:**

- Esiste una dependency FastAPI (es. `require_trainer`) che:
  1. estrae il JWT dalla richiesta,
  2. ne verifica la firma con la chiave attesa,
  3. verifica che `role == "trainer"`,
  4. rifiuta con `401`/`403` in ogni altro caso (firma invalida, token assente, ruolo assente, ruolo diverso).
- Questa dependency è applicata a **TUTTI** gli endpoint che leggono o scrivono dati del CRM: `clients`, `contracts`, `rates`, `movements`, `recurring_expenses`, `dashboard`, `agenda`, `todos`, `measurements`, `goals`, `workout*`, `nutrition`, `communications`, `backup`, `workspace`, e qualunque altro router non esplicitamente pubblico.
- Gli endpoint del portale atleti (`/api/public/*`) restano governati dalla loro logica di token tokenizzato, e NON devono mai accettare di esporre dati CRM al di fuori dello scope dell'atleta.

**Criterio di accettazione (test obbligatori prima del POC):**
- Richiesta a un endpoint CRM **senza** token → 401/403.
- Richiesta a un endpoint CRM con token **atleta** → 403. *(questo è il test che dimostra la separazione dei ruoli)*
- Richiesta a un endpoint CRM con token **trainer valido** → 200.
- Richiesta a un endpoint CRM con token trainer **a cui è stato manomesso il payload** → 401 (firma fallita).
- Tutti e quattro i test devono passare colpendo l'app **attraverso il dominio pubblico del tunnel**, non solo da localhost.

> Se AC-2 è soddisfatto, il CRM è sicuro su Internet **indipendentemente** da cosa fa il middleware Next.js. Questo è il punto: il confine non deve dipendere da nient'altro.

---

## 3. Tunnel Guard come difesa in profondità (AC-3)

**Cosa deve essere vero:**

- `TUNNEL_ALLOWED_PREFIXES` in `middleware.ts` viene esteso per consentire l'accesso del trainer al CRM via tunnel (login, dashboard, API CRM). Questo è necessario per Strada B.
- Il Tunnel Guard **non è più il meccanismo di sicurezza** che impedisce l'accesso al CRM da Internet: quel ruolo passa interamente ad AC-2. Il guard resta solo come strato di riduzione della superficie (es. bloccare path puramente interni/diagnostici che non servono né a trainer né ad atleti via tunnel).
- **`isTunnelRequest` NON deve basare alcuna decisione di sicurezza sull'header `Host`.** L'header `Host` arriva da `frpc` dopo terminazione TLS ed è influenzabile dal client → spoofabile. Una guardia che classifica come "LAN fidata" sulla base dell'`Host` può essere aggirata inviando `Host: localhost` dal dominio pubblico.

**Conseguenza pratica:** con AC-2 in vigore, la distinzione LAN-vs-tunnel **smette di avere rilevanza di sicurezza**. Un trainer su LAN e un trainer via tunnel presentano lo stesso JWT con `role=trainer` e ottengono lo stesso accesso — che è esattamente il comportamento voluto in Strada B. Il redirect a `/login` (Layer 2) resta una comodità UX, non una protezione.

**Criterio di accettazione:**
Inviare al dominio pubblico una richiesta con header `Host: localhost` (o `127.0.0.1`) verso un endpoint CRM, **senza** token trainer valido → deve comunque ricevere 401/403. Se riceve 200 o il contenuto del CRM, AC-2 non è correttamente in vigore e il sistema è vulnerabile.

---

## 4. P2 — Data-blind (proprietà GDPR) — BLOCCANTE per la tesi GDPR

**Problema rilevato:** la configurazione attuale del tunnel usa `type = "https"` + plugin `https2http`. In questa modalità il vhost HTTPS è gestito da `frps` sul VPS, che **termina o ispeziona il TLS**. Il VPS quindi *non è cieco* rispetto al traffico trainer/atleti. La proprietà P2 (data-blind), su cui poggia la semplificazione GDPR, **è falsa come configurato.** Il test TCP della Fase 0 (HTTP 307) non dimostra P2 — dimostra solo connettività.

**Cosa deve essere vero perché P2 sia reale:**

- Il TLS DEVE iniziare sul client finale (browser del tablet/atleta) e terminare **solo** sul `frpc` del PC del trainer.
- Il VPS DEVE instradare leggendo **esclusivamente** il campo SNI dell'handshake TLS (metadata di routing, in chiaro per design del protocollo) e inoltrare il flusso applicativo cifrato come byte opachi.
- Il VPS NON deve possedere alcuna chiave privata né certificato di alcun trainer.
- Architetturalmente: `type = "tcp"` (transito byte grezzi) con un router/proxy SNI davanti a `frps`, NON `type = "https"`.

**Criterio di accettazione (test del data-blind, da eseguire in Fase 1 con cert self-signed):**
Mentre un client è connesso a `{instance_id}.fitmanagerstudio.com`, catturare sul VPS il traffico in ingresso a `frps` (es. `tcpdump` sulla porta del tunnel). Deve risultare:
- SNI visibile in chiaro nell'handshake (atteso, è routing).
- Payload applicativo **opaco/cifrato** dopo l'handshake.
- Nessun certificato di trainer presente o richiesto sul VPS per servire la connessione.

Se si osserva HTTP leggibile, o se `frps` deve presentare un certificato, **P2 è falso** e va corretto **prima** del POC, non dopo.

> Questo test usa il principio già stabilito: "il sistema è la source of truth". Lo si dimostra sul campo, non sulla carta.

---

## 5. Conseguenze operative del passaggio locale → Internet

Una volta che il CRM è raggiungibile da Internet, alcune protezioni finora implicite (offerte dalla LAN) vanno rese esplicite:

- **Rate limiting su login via tunnel.** `auth_limiter` esiste già su `/auth/*`. Verificare che operi correttamente quando l'IP di origine arriva dal tunnel (l'IP visto da FastAPI potrebbe essere `127.0.0.1` di frpc, non l'IP reale del client → il rate limiter potrebbe contare tutti i tentativi come un'unica fonte, o al contrario non distinguere attaccanti). Decidere come ricavare l'IP reale del client (header propagati dal tunnel) **senza fidarsi ciecamente di header spoofabili.**
- **Brute force su `/auth/login` è ora esposto a Internet.** Il login constant-time c'è già (buono, anti-enumeration). Valutare lockout progressivo o captcha dopo N tentativi falliti, dato che la superficie non è più la sola LAN.
- **CORS.** Il regex CORS attuale ammette `localhost`/`192.168`/`100.x`. NON deve essere allargato a `*` per "far funzionare il tunnel": le richieste cross-origin dal dominio pubblico vanno gestite consapevolmente. Se l'app è servita *dallo stesso* dominio del tunnel (stesso origin), il CORS non è il meccanismo rilevante e non va toccato; la protezione resta AC-2.
- **Disponibilità dell'istanza.** Vincolo di prodotto già noto: l'accesso da tablet richiede il PC del trainer acceso. Da comunicare ai trainer del POC.

---

## 6. Procedure di supporto (POC, 10 trainer)

- **Trainer cambia PC:** rigenerare `license.key` col nuovo `machine_id` (hardware fingerprint). L'`instance_id` **resta invariato** → l'URL del tablet non cambia.
- **Trainer cambia macchina ma vuole stesso URL:** garantito da quanto sopra (instance_id disaccoppiato da machine_id).
- **Onboarding nuovo trainer:** interamente nel control plane (genera licenza → instance_id → config frpc). **Zero interventi su Cloudflare** (il wildcard `*.fitmanagerstudio.com` copre tutti gli instance_id). Nessuna registrazione DNS manuale per-trainer.

---

## 7. Riepilogo gravità (ordine di intervento)

1. **AC-1 + AC-2 (ruolo nel JWT + verifica lato FastAPI).** Senza questi, esporre il CRM su Internet significa esporlo a chiunque sappia spoofare un header. **Bloccante assoluto per Strada B.**
2. **AC-3 (Host-spoofing).** Eliminare la dipendenza di sicurezza dall'header `Host`. Mitigato automaticamente se AC-2 è solido, ma il guard va comunque corretto per non dare falsa sicurezza.
3. **P2 / data-blind (sez. 4).** Bloccante per la *tesi GDPR*, non per il funzionamento. Va dimostrato in Fase 1 col self-signed, prima che ci siano atleti reali sopra.
4. **Operative (sez. 5).** Rate limiting / brute force / IP reale: necessari prima del POC perché la superficie è ora pubblica.

---

## Note di confine (cosa questo documento NON copre)

- Non specifica la struttura esatta dei claim oltre `role` — la lascia all'implementazione, purché firmati.
- Non specifica il meccanismo di routing SNI sul VPS — lascia a Fase 2 / `cert_manager.py` la scelta, vincolata al criterio della sez. 4.
- Non sostituisce la verifica con un consulente legale sulla tesi GDPR; fornisce la condizione *tecnica* (P2 reale) necessaria perché quella tesi sia difendibile.
