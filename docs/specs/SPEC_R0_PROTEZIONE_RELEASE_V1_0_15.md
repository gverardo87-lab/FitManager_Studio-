# SPEC R0 — Protezione release v1.0.15

**Stato:** 🟠 APERTA — R0.1 contenimento verde; **R0.1.5 TLS valido APERTO**; R0.2 non aperto
**Data:** 2026-07-24
**Branch:** `FitManager_Studio`
**Tipo:** contenimento release cross-layer; nessuna nuova macro-feature e nessuna nuova regola finanziaria
**Audit fondante:** `docs/archive/AUDIT_OBSOLESCENZA_POST_MIGRAZIONI_2026-07-23.md`
**Autorità:** `AGENTS.md` → `MANIFESTO.md` → `LAUNCH_SCOPE.md` → layer `CLAUDE.md` → ADR/SSoT
**Sequenza ratificata:** FE-0 + FE-1.0/1.1 ✅ → **R0.1 → R0.1.5 → R0.2 → R0.3 → R0.4** → P1..P6 → candidate v1.0.15 → G-MAC

> Questa SPEC è la casa del solo lavoro release-critical emerso dall'audit. La bonifica massiva di
> codice morto, API dormienti e tool storici non entra in R0 e non interrompe il blocco P. A chiusura
> di R0: consuntivo, full suite proporzionata ai layer toccati, verifier finanziario sui money-read,
> fold-back degli evergreen realmente modificati, append al BUILD_LOG e archiviazione della SPEC nello
> stesso commit docs del gate finale.

## 1. Decisione e tesi falsificabile

Il founder approva un **gate ristretto di protezione release prima di P1**, non l'intera «Fascia A»
dell'audit originario.

Dopo R0 devono essere vere contemporaneamente quattro proprietà:

1. un'installazione provisionata FRP non avvia, propone o configura un secondo percorso Tailscale
   Funnel;
2. P1 può introdurre la propria migrazione Alembic senza alcuna procedura viva che ricrei
   `crm_dev.db`;
3. le superfici cliente toccate mostrano il denaro dal netto SSoT e non espongono importi nella
   Command Palette globale;
4. checklist e runbook di candidate verificano il percorso FRP reale, non quello Tailscale storico.

La tesi è falsificata se anche uno solo di questi scenari resta possibile: Funnel auto-avviato da un
`.env` preservato; wizard che propone Tailscale su istanza FRP; `migrate-all.sh` che crea
`crm_dev.db`; ContrattiTab che diverge da `/contratti`; Command Palette che mostra lordo/prezzo;
preflight che dichiara verde una verifica Tailscale senza provare FRP.

## 2. Impact map

- **Obiettivo:** eliminare i rischi capaci di compromettere la candidate v1.0.15 o la sua fiducia
  percepita prima di aggiungere il nuovo asse economico di P1.
- **Layer:** installer + tunnel backend/frontend; procedura Alembic/rehearsal; read-only finance FE;
  documentazione operativa.
- **Invarianti da preservare:**
  - FRP resta l'unico percorso target e il portale pubblico continua a funzionare;
  - l'assenza o il fermo temporaneo di FRP non apre automaticamente un percorso alternativo;
  - fallback locale sempre disponibile;
  - nessun cambio a ledger, rate, payload di pagamento, residuo, wallet o transizioni;
  - denaro letto dal wire SSoT, mai ricalcolato nel frontend;
  - privacy-first e finanze confinate ai contesti dedicati;
  - un solo `crm.db`, dati persistenti solo in `data/`;
  - ownership, Bouncer Pattern e audit trail invariati.
- **Non-obiettivi:** dismissione completa Fase 3 di Tailscale; apertura CRM via Strada B; rimozione
  massiva dei cluster morti; smontaggio Nutrition/Training; bonifica di tutti i tool storici;
  ottimizzazioni generali dashboard; modifica della semantica crediti già assegnata a P4/P5.

## 3. Rettifiche vincolanti dell'audit fondante

La verifica indipendente 2026-07-24 conferma i blocker ma corregge la stima del perimetro:

- `crm_dev` compare in **34 sorgenti tracciati**, non 63: il conteggio 63 includeva 29 `.pyc`
  ignorati in `__pycache__`;
- `workspace_engine.py` non è morto: `/workspace/today` e `collect_workspace_snapshot` sono vivi e
  consumati dalla pagina Oggi. Solo i rami list/detail senza UI sono candidati a un audit post-release;
- Nutrition è montato e privo di UI, ma gli endpoint richiedono autenticazione trainer e il tunnel
  FRP corrente non espone il CRM: decisione post-release, non blocker R0;
- la non-coesistenza Tailscale/FRP è un vincolo **a regime**. R0 chiude l'auto-Funnel e la confusione
  sulle istanze FRP; la dismissione completa resta una decisione Fase 3;
- le circa 6.900 LOC frontend non importate sono debito reale ma non entrano normalmente nel bundle
  Next: cleanup separato dopo v1.0.15.

## 4. Sequenza dei gate

| Ordine | Gate | Scopo | Dipendenza |
|---:|---|---|---|
| 1 | **R0.1 — Percorso pubblico unico** | Contenere transizione FRP/Tailscale | FE-1 chiuso LIVE |
| 2 | **R0.1.5 — TLS pubblico valido** | Chiudere il finding live senza cedere P2 | R0.1 verde + decisione founder |
| 3 | **R0.2 — Binario unico di migrazione** | Rendere sicura l'apertura P1/Alembic | R0.1.5 chiuso |
| 4 | **R0.3 — Verità finanziaria e privacy** | Chiudere lordo/netto e denaro globale | G8.4 SSoT |
| 5 | **R0.4 — Verità operativa release** | Allineare checklist/runbook/contesto | R0.1–R0.3 reali |
| 6 | **P1** | Apre il blocco P | R0 chiuso e consuntivato |

Ogni gate è un'unità coesa e verificabile. Nessun cleanup post-release viene infilato tra questi gate.

## 5. R0.1 — Percorso pubblico unico

### Contratto di transizione ratificato

- **Istanza FRP provisionata:** FRP è l'autorità dell'URL pubblico. La UI non propone installazione,
  login o Funnel Tailscale; una configurazione manuale non può sostituire in-process o su `.env`
  l'URL gestito da FRP.
- **Istanza non provisionata FRP:** comportamento locale attuale preservato. Il destino del fallback
  Tailscale viene deciso nella Fase 3, non in R0.
- **Ogni istanza:** `launcher.bat` non esegue mai `tailscale funnel`, anche se un upgrade conserva
  `PUBLIC_PORTAL_ENABLED=true` in `data/.env`.

### File/layer probabili

- `installer/launcher.bat`, `installer/fitmanager.iss` solo per verifica del packaging;
- `api/services/connectivity_config.py`, `api/services/connectivity_runtime.py`,
  `api/routers/system.py`, eventuale read-model tunnel condiviso;
- `frontend/src/components/dashboard/ConnectivityOnboardingCard.tsx`, componenti `settings/`
  Connettività, hook e `types/api.ts` se il contratto wire cambia;
- copy attivo in condivisione scheda/anamnesi.

### Criteri di accettazione

- **AC-R01-1:** grep/static guard: zero comando `tailscale funnel` nel launcher installato.
- **AC-R01-2:** fixture `.env` legacy con `PUBLIC_PORTAL_ENABLED=true` non abilita un secondo tunnel.
- **AC-R01-3:** istanza FRP provisionata non restituisce né rende `install_tailscale`,
  `connect_tailscale`, `enable_funnel` come prossima azione.
- **AC-R01-4:** su istanza FRP, POST di configurazione legacy non può cambiare il base URL autoritativo;
  il rifiuto o il no-op è esplicito e testato, mai silenzioso.
- **AC-R01-5:** portale pubblico FRP, route separation e fallback localhost restano funzionanti.
- **AC-R01-6:** test backend connectivity + Vitest mirati + `next build`; prova packaging che il launcher
  stageato è quello corretto.

### Consuntivo R0.1 — 2026-07-24

**Esito del contenimento:** implementato e verificato. Il founder ha scelto la remediation immediata
R0.1.5; R0.2 non è ancora aperto.

- `instance_id` della licenza valida è ora il segnale autorevole della provision FRP, indipendente
  dalla disponibilità temporanea di `frpc`; il runtime imposta sempre origine gestita e fallback
  localhost senza persistere un secondo flag.
- `launcher.bat` non legge più `PUBLIC_PORTAL_ENABLED` e contiene zero comando Funnel; il packaging
  Inno Setup continua a stageare esattamente quel launcher.
- il read-model espone `public_access_provider=managed_frp`; su tale ramo non esegue probe Funnel,
  non restituisce azioni Tailscale e usa esclusivamente l'origine `*.fitmanagerstudio.com`.
- ogni POST legacy di configurazione su istanza FRP riceve `409` esplicito prima di qualsiasi
  scrittura a `.env` o modifica dell'environment del processo.
- la UI FRP non monta il wizard legacy: mostra origine non modificabile, fallback locale, verifica
  end-to-end e validazione portale. Il percorso legacy non-FRP resta invariato, come ratificato.

**Evidenze:**

- backend connectivity **28/28**; full backend **880/880** (31 warning baseline);
- frontend mirato R0.1 **5/5**; suite frontend definitiva **157/157**; lint mirato e ruff mirato verdi;
- Next production build verde, **20 pagine**;
- static/package guard: zero `tailscale funnel`, zero `PUBLIC_PORTAL_ENABLED` nel launcher e sorgente
  `installer/launcher.bat` confermata da `fitmanager.iss`;
- live FRP applicativo: `/health` **200**, `/clienti` **404**, ma solo disabilitando la verifica della
  trust chain del certificato.

**Finding live non occultabile:** il client HTTPS strict rifiuta il certificato self-signed
(`Impossibile stabilire una relazione di trust`). Il routing e la route separation funzionano, ma
l'end-to-end pubblico non è dichiarabile production-ready finché la Fase 2 TLS descritta nel root
`CLAUDE.md` non viene completata oppure il founder non ratifica una collocazione diversa. Decisione
presa dal founder: remediation immediata **R0.1.5**, da chiudere prima di R0.2.

**Nota ambiente test:** i warning di rollover `fitmanager.log` dipendono dal server live
`uvicorn --reload` già in esecuzione che condivide il log con pytest. Il processo `frpc` osservato
non è orfano: è figlio di quel runtime live e non è stato terminato.

## 6. R0.1.5 — TLS pubblico valido, P2-preserving

### Decisione ratificata

L'emissione e il rinnovo del certificato pubblico avvengono sul PC del trainer tramite ACME
**HTTP-01 instradato da FRP**. `frps` ascolta anche sulla porta 80, ma inoltra al trainer soltanto
`/.well-known/acme-challenge/`; `frpc` serve quella location da un webroot dedicato sotto
`data/tunnel/`, senza collegarla a Next.js o all'API. Ogni altra route HTTP riceve 404 all'edge.

Il client ACME è un binario standalone maturo, versionato e verificato nel build. Account ACME,
chiave del certificato e certificato vivono esclusivamente in `data/tunnel/` sul PC trainer. Nessuna
credenziale Cloudflare/DNS entra in licenza, installer o runtime: i token Cloudflare con `DNS Write`
sono limitabili alla zona, non al singolo record, quindi distribuirli allargherebbe ingiustificatamente
il blast radius.

La porta 80 trasporta esclusivamente challenge ACME pubbliche e prive di dati applicativi. Il traffico
atleta/trainer resta su 443 con terminazione TLS sul PC trainer: P2 data-blind rimane invariato.
L'edge non custodisce certificati o chiavi private dei trainer.

### Impact map

- **Obiettivo:** browser mainstream in trust strict sul dominio FRP, senza avvisi self-signed.
- **Layer:** configurazione FRP client/server; nuovo certificate manager backend; boot/scheduler;
  packaging del client ACME; documentazione tunnel e release.
- **Invarianti:** route CRM sempre 404 dal tunnel; Next.js mai raggiungibile su HTTP; chiave privata
  sempre locale; fallback localhost e CRM core disponibili anche se ACME fallisce; ultimo certificato
  valido mai sovrascritto da un risultato incompleto; zero modifiche a schema, dati business, ledger,
  ownership o audit finanziario.
- **Non-obiettivi:** wildcard certificate centralizzato; terminazione TLS sul VPS; DNS-01 con token sul
  trainer; pagina studio-offline, token hash, inactivity timeout o apertura CRM Strada B.

### Microstep ordinati

1. **Edge challenge path:** backup verificato di `frps.toml`, aggiunta `vhostHTTPPort=80`, apertura
   UFW 80/tcp, restart e probe; rollback esplicito se health/frps non restano verdi.
2. **Trasporto challenge locale:** secondo proxy FRP `type=http`, `locations` ristretto alla challenge
   e plugin `static_file` su webroot dedicato; verifica sintassi con lo stesso `frpc` v0.61.1 del bundle.
3. **Certificate manager:** emissione opportunistica al boot, controllo ogni 12 ore e rinnovo entro
   30 giorni dalla scadenza; errori ACME non bloccano il CRM locale e usano backoff senza retry storm.
4. **Install atomica:** il risultato viene promosso su `cert.pem`/`key.pem` solo dopo verifica SAN,
   validità temporale e corrispondenza cert↔key; quindi restart controllato di `frpc`.
5. **Packaging e live gate:** client ACME versionato/hash-verificato nel build; prova esterna strict e
   route separation ripetuta prima di chiudere R0.1.5.

### Criteri di accettazione

- **AC-R015-1:** nessuna credenziale DNS/API è richiesta o persistita sul trainer; guard statico su
  licenza, config, installer e `data/tunnel/` di fixture.
- **AC-R015-2:** config FRP verificata contiene proxy HTTPS applicativo e proxy HTTP limitato a
  `/.well-known/acme-challenge/`; una route HTTP diversa non raggiunge frontend/API.
- **AC-R015-3:** assenza client ACME, timeout, CA indisponibile o challenge fallita preservano il CRM
  locale e l'ultimo cert/key valido, con errore diagnostico e senza loop aggressivo.
- **AC-R015-4:** installazione cert/key è atomica e rifiuta SAN errato, certificato scaduto/non ancora
  valido o chiave non corrispondente.
- **AC-R015-5:** boot e scheduler sono idempotenti; nessun rinnovo se il certificato ha più di 30
  giorni residui; dopo una promozione riuscita `frpc` rilegge i file senza lasciare processi orfani.
- **AC-R015-6:** build/installer falliscono se il binario ACME pinato manca o non supera la verifica
  prevista; nessun path assoluto hardcoded.
- **AC-R015-7:** test backend mirati, ruff, full backend e gate packaging pertinenti verdi.
- **AC-R015-8:** live strict su `gvera-dev.fitmanagerstudio.com`: chain browser-trusted e SAN corretto,
  `/health` 200, `/clienti` 404; nessun `-k`, `--insecure` o trust bypass nell'evidenza finale.

### Evidenza progettuale pre-codice

- probe esterno iniziale su porta 80: timeout, coerente con `vhostHTTPPort`/UFW non ancora attivi;
- `frpc` v0.61.1 accetta sintatticamente `type=http` + `locations` + plugin `static_file`;
- la documentazione ufficiale Let's Encrypt richiede HTTP-01 su porta 80 e raccomanda HTTP-01 come
  default; FRP rende raggiungibile dietro NAT il solo webroot di challenge;
- ADR-011 Addendum I sostituisce esclusivamente il meccanismo challenge DNS-01, non FRP, SNI
  passthrough, terminazione locale o identità da licenza.

### Consuntivo parziale R0.1.5 — trasporto challenge locale (2026-07-24)

- `TunnelConfig` espone un `acme_webroot_path` dedicato e crea soltanto
  `data/tunnel/acme-webroot/.well-known/acme-challenge/` come radice del contenuto HTTP pubblico.
- `generate_frpc_toml()` genera due proxy distinti: HTTPS applicativo `https2http` verso Next.js e
  HTTP ACME con `locations=["/.well-known/acme-challenge/"]` + plugin `static_file`. Il blocco ACME
  non contiene `localAddr` né `127.0.0.1:3000`.
- Test mirati **3/3**: separazione dei due blocchi, creazione webroot e sintassi reale accettata da
  `frpc` **0.61.1**. Ruff mirato e `git diff --check` verdi.
- Il lato edge non è falsamente consuntivato: SSH non interattivo con la chiave documentata ha
  restituito `Permission denied`; `ssh-agent` locale è disabilitato. Restano quindi pendenti backup,
  `vhostHTTPPort=80`, UFW, restart/probe e prova 404 fuori challenge.
- Nessun file `data/tunnel/`, processo live, schema, dato business, ledger o frontend è stato mutato
  da questo microstep.

### Consuntivo parziale R0.1.5 — certificate manager core (2026-07-24)

- Integrato lego **v5.2.1 windows/amd64** come client ACME locale: release GitHub immutabile, ZIP
  SHA-256 `3e87c133bcb0a6fd4236d11e0583967ecd2f04f454d2ff48286f1ab1183d699e`, binario
  SHA-256 `e2d5f33c26032197db5953f8cfd93aa960f08cf2014c887b79ba950cb5b525e5`.
- `CertificateManager` è avviato dopo `frpc`, mai blocca il CRM locale, controlla ogni 12 ore e usa
  retry a 15 minuti sui fallimenti. Prima di eseguire il binario verifica hash e versione; il comando
  usa solo `--http --http.webroot`, mai DNS o email/PII.
- Prima di creare un ordine CA esegue un **preflight falsificabile**: token casuale scritto nel
  webroot, GET su HTTP pubblico, status 200 e body byte-identico, cleanup sempre. Se fallisce, lego non
  viene eseguito e nessun ordine viene consumato.
- La candidate viene accettata solo con SAN esatto, finestra temporale valida, cert↔key match, chain
  bundled e firma leaf verificata. La promozione usa staging + fsync + backup pair + marker di recovery;
  un failure sulla seconda replace ripristina entrambi i file. `frpc` viene riavviato una sola volta
  solo dopo installazione riuscita. Lo shutdown del backend termina esplicitamente l'eventuale
  processo ACME ancora attivo.
- Il bootstrap ora rifiuta coppie esistenti con SAN errato, key mismatch o finestra non valida.
- Test tunnel+certificate manager **16/16**; regressione condivisa connectivity/health/tunnel/cert
  **43/43**; full suite finale **896/896 PASS** (31 warning baseline, exit 0). Includono hash mismatch
  fail-closed, assenza ordine prima del preflight, stop processo attivo, race monitor↔restart e
  stop↔launch, CA failure che preserva la coppia, SAN/key/chain, rollback iniettato e TOML verificato
  con `frpc` 0.61.1. Ruff mirato e diff check verdi. Un primo run pre-hardening aveva mostrato il
  warning ambientale Windows `WinError 32` sulla rotazione log con server dev concorrente; il run
  finale non lo ha riprodotto. Zero processi `lego` o pytest residui a fine gate.
- **Finding live da reload dev:** prima dell'aggiunta del preflight il server `uvicorn --reload` ha
  creato l'account ACME locale no-email e tentato due ordini production falliti a 15 minuti di
  distanza. Nessun certificato è stato emesso/installato; la coppia attiva resta valida ma self-signed
  (`public_chain=False`, scadenza 2027-06-07), zero processo lego e zero token residuo nel webroot.
  Dopo il fix il probe reale termina in timeout e l'ordine non parte.
- **Blocker live esterno:** dal runner corrente le porte edge 22/80/443/7000 risultano tutte non
  raggiungibili. Non è attribuibile al proxy HTTP (anche SSH e bind FRP sono down), ma impedisce edge
  setup e prova HTTPS. R0.1.5 resta aperto.
- Alla data del checkpoint core restavano packaging, configurazione edge e prova strict; il packaging
  è consuntivato nel blocco successivo.

### Consuntivo parziale R0.1.5 — packaging ACME fail-closed (2026-07-24)

- `build-installer.sh` invoca dopo il build backend uno staging dedicato che fallisce se `lego.exe`
  manca, ha hash diverso da quello pinato, non dichiara esattamente `5.2.1 windows/amd64`, oppure se
  la licenza MIT tracked manca/non coincide. Solo dopo i controlli copia binario e licenza sotto
  `dist/fitmanager/`, già incluso ricorsivamente da Inno Setup.
- `fetch-lego.ps1` è un'operazione developer esplicita, separata dalla build: URL release v5.2.1
  immutabile, SHA-256 ZIP/exe/licenza, target/versione e copia finale riverificati; scratch confinato
  nel temp root e cleanup deterministico. Test end-to-end reale completato con SHA exe
  `e2d5f33c26032197db5953f8cfd93aa960f08cf2014c887b79ba950cb5b525e5`.
- Il binario resta ignorato da Git; sono tracked solo script, pin e licenza. `.gitattributes` forza LF
  sui file soggetti a hash/esecuzione shell, evitando drift CRLF sui checkout Windows.
- Gate packaging + release guard **9/9 PASS**; `bash -n` sui due script shell, parse PowerShell, fetch
  end-to-end e diff check verdi. Coperti dinamicamente missing, tampering e staging del client reale.
- AC-R015-6 è coperto a livello pipeline. Non è stato prodotto un nuovo installer release candidate in
  questo microstep; l'ispezione dell'artifact finale resta nella checklist release.
- **Restano aperti per chiudere R0.1.5:** configurazione edge HTTP/80 e prova live browser-trusted con
  HTTPS 200 sulle sole route ammesse e 404 sui path privati/HTTP non challenge.

### Consuntivo parziale R0.1.5 — edge apply/probe pronti, non eseguiti (2026-07-25)

- Ground truth esterna ripetuta: DNS `gvera-dev.fitmanagerstudio.com → 128.140.91.39`; TCP 22 e 7000
  raggiungibili; HTTPS permissivo (`-k`) 200; HTTP/80 timeout; HTTPS strict fallisce con
  `SEC_E_UNTRUSTED_ROOT`. Il tunnel applicativo è quindi vivo, mentre challenge e trust restano aperti.
- SSH BatchMode con la chiave locale documentata arriva al server ma riceve `Permission denied
  (publickey,password)`: la passphrase non è disponibile al processo. **Zero mutazioni live** eseguite;
  edge e TLS non sono consuntivati come verdi.
- `apply-frps-http01.sh` rende idempotente il solo top-level `vhostHTTPPort=80`, preserva tabelle e
  segreti, verifica la candidate prima del write, usa backup univoco in directory `0700`, non abilita
  UFW globalmente e rollbacka config/regola 80 su failure di restart/verify/listener.
- `probe-r015-tls.ps1` non disabilita mai il trust e non segue redirect: richiede HTTP non-challenge
  404, handshake chain+hostname valido, HTTPS privata 404 e, con link letto da file ignorato, route
  `/public/` 200 senza stampare URL/token.
- Test edge operations **5/5 PASS**; gate combinato edge+packaging+release guard **14/14 PASS**; Bash e
  PowerShell syntax PASS. L'apply reale richiede una sessione SSH interattiva sbloccata; la verifica
  Claude resta differita e non è un PASS implicito.

## 7. R0.2 — Binario unico di migrazione

### Scope

- ritirare o riscrivere `tools/scripts/migrate-all.sh` affinché esista un solo target `crm.db`;
- correggere la regola dual-DB in `api/CLAUDE.md`;
- rimuovere dal distribution rehearsal il requisito positivo `crm_dev.db`;
- aggiungere un guard che fallisca se una procedura release/migrazione viva tenta di creare
  `data/crm_dev.db`.

I restanti sorgenti storici che nominano `crm_dev` non vengono ripuntati alla cieca su `crm.db`: alcuni
sono script distruttivi di seed/curation e richiedono triage dedicato post-release.

### Criteri di accettazione

- **AC-R02-1:** la procedura prescritta esegue Alembic una sola volta sul DB configurato.
- **AC-R02-2:** nessun rehearsal sano richiede l'esistenza di `crm_dev.db`.
- **AC-R02-3:** prova in directory temporanea: l'esecuzione della procedura non crea un secondo DB.
- **AC-R02-4:** `api/CLAUDE.md`, root `CLAUDE.md` e ADR-014 non si contraddicono sul modello single-DB.
- **AC-R02-5:** gate Alembic/schema pertinenti verdi prima di aprire P1.

## 8. R0.3 — Verità finanziaria e privacy

### Scope

- `ContrattiTab` consuma `netto_incassato` dal wire; se serve disclosure lordo/rimborsi, riusa il
  pattern canonico senza sottrazioni frontend;
- il gemello anti-vacuità di G8.4 include esplicitamente ContrattiTab;
- la Command Palette globale non mostra `totale_versato` né `prezzo_totale_attivo` nel preview cliente;
- `ExpiringContractsSheet` non calcola `(prezzo / crediti) × residui` nel frontend: il valore
  approssimativo viene rimosso finché non esiste un read-model backend canonico;
- il tour Clienti descrive le colonne e gli stati realmente esistenti dopo FE-0.

### Criteri di accettazione

- **AC-R03-1:** su contratto con rimborso, netto in hero/lista/profilo è identico.
- **AC-R03-2:** guard G8.4 fallisce se ContrattiTab torna a leggere il lordo come posizione.
- **AC-R03-3:** test privacy Command Palette: nessun importo monetario nel preview cliente.
- **AC-R03-4:** zero formula monetaria del «valore sedute residue» in `ExpiringContractsSheet`.
- **AC-R03-5:** nessuna mutation, endpoint, invalidazione o payload money-path modificato.
- **AC-R03-6:** Vitest mirati + suite FE + lint/build; `financial-invariant-verifier` = MONEY AXIS
  PRESERVED.

## 9. R0.4 — Verità operativa release

Aggiornare solo i documenti e le prove che possono guidare male la candidate:

- `docs/operations/RELEASE_CHECKLIST.md`: FRP, `tunnel-status`, dominio
  `*.fitmanagerstudio.com`, route separation e conteggi catalogo correnti;
- `docs/operations/SUPPORT_RUNBOOK.md`: diagnosi FRP prima di ogni riferimento legacy;
- `LAUNCH_SCOPE.md`: accesso remoto coerente con FRP/Strada B;
- `docs/technical/TUNNEL_ARCHITECTURE.md`: esempio `https2http` e path reali;
- `api/CLAUDE.md` / `frontend/CLAUDE.md`: solo drift direttamente toccato da R0;
- `tools/admin_scripts/e2e_distribution_rehearsal.py`: checklist manuale FRP.

I conteggi cosmetici, la tabella WhatsApp e altra documentazione non release-critical restano fuori R0.

### Criteri di accettazione

- **AC-R04-1:** zero istruzioni attive di release/supporto che chiedono Funnel Tailscale.
- **AC-R04-2:** checklist FRP falsificabile: stato tunnel, URL pubblico, portale, 404 CRM dal tunnel.
- **AC-R04-3:** review coerenza cross-doc e link/path integrity.
- **AC-R04-4:** `docs/INDEX.md` rispecchia esattamente il fronte `docs/specs/`.

## 10. Findings già assorbiti o differiti

### Assorbiti da lavoro vivo

- `crediti_residui_attivi`, dropdown e filtri onesti → SPEC_P P4/P5;
- raw count e residuo workspace → SPEC_VOCABOLARIO Giro 2, dopo verifica dei soli siti vivi;
- `signed_contractual_amount` → HOLD fino al birth-audit P1; nessuna rimozione in R0.

### Differiti dopo v1.0.15

- cluster frontend morti e relativi test;
- soli rami workspace list/detail realmente orfani;
- alert/wire costosi non consumati e dipendenze orfane;
- triage dei 34 sorgenti tracciati con `crm_dev`;
- decisione founder su mount Nutrition/Training e dismissione completa Tailscale Fase 3.

Questi punti non sono autorizzazione a modificare codice: dopo la candidate ricevono una SPEC dedicata
solo se il founder apre il blocco.

## 11. Definition of Done R0

1. AC-R01, AC-R015, AC-R02, AC-R03 e AC-R04 verificati con evidenza reale;
2. full suite raccolta verde per backend/frontend e quality gate AGENTS.md;
3. financial-invariant-verifier PASS su R0.3;
4. test upgrade/installazione con `.env` legacy e test live FRP da rete esterna;
5. commit atomici per gate, con branch rilasciabile dopo ciascuno;
6. consuntivo con commit, suite, rischi residui e decisioni;
7. fold-back negli evergreen realmente toccati;
8. append a `docs/learning/BUILD_LOG.md`, aggiornamento `docs/INDEX.md` e spostamento di questa SPEC
   in `docs/archive/specs/` nello stesso commit docs di chiusura;
9. soltanto dopo questi punti si apre P1.
