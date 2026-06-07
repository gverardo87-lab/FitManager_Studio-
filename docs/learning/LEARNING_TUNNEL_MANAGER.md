# LEARNING_TUNNEL_MANAGER.md

**Progetto:** FitManager
**Data:** 2026-06-05
**Stato:** Teoria (pre-implementazione)
**Contesto:** Preparazione Fase 1 tunnel migration — il tunnel_manager e' il componente nuovo piu' critico.
**Macro di riferimento:** `LEARNING_FASE1_BASI_TEORICHE.md` sez. 3, `TUNNEL_MIGRATION_STRATEGY.md` sez. 4.

---

## 0. Cos'e' il tunnel_manager (richiamo dal macro)

Un componente nuovo del backend (`tunnel_manager.py`) che gestisce il ciclo di vita del processo `frpc`: lo avvia all'accensione dell'app, lo tiene vivo, lo riavvia se cade, verifica che il tunnel sia realmente funzionante. E' il "babysitter" del processo tunnel.

Il pattern e' lo stesso di systemd sul VPS (babysitter di `frps`), ma qui dentro l'applicazione invece che a livello di sistema operativo.

---

## 1. Perche' i casi edge sono il cuore del problema

Il "caso felice" del tunnel_manager e' banale: avvia frpc, frpc si connette, tutto funziona. Ci vogliono poche righe di codice.

Il problema e' che il tunnel gira sul PC di un trainer non tecnico, su Windows, con rete domestica/studio. Il contesto e' intrinsecamente instabile: sleep, WiFi ballerino, antivirus, doppi click. Se il tunnel_manager gestisce solo il caso felice, il trainer va offline silenziosamente e non capisce perche'. La differenza tra "demo" e "produzione" sta interamente nella gestione dei casi edge.

---

## 2. Casi edge — mappa completa

### 2.1 Sleep/Hibernate (frequenza: alta)

**Livello 1 — Cosa succede:**
Il trainer chiude il laptop o il PC va in sleep automatico. Quando riapre, la rete torna su ma la connessione TCP tra `frpc` e `frps` e' morta — il server l'ha gia' chiusa per timeout.

**Livello 2 — Perche' e' un problema:**
`frpc` potrebbe non accorgersene subito. TCP ha un meccanismo di keepalive con timeout lunghi (anche minuti). Risultato: FitManager sembra attivo, ma il tunnel e' morto. Il portale del cliente da' timeout. Il trainer non capisce perche'.

**Livello 3 — Il meccanismo sotto:**
Una connessione TCP e' uno stato mantenuto da entrambe le parti (client e server). Se una parte sparisce senza avvisare (sleep = sparizione improvvisa), l'altra non lo sa finche' non prova a comunicare e fallisce, o finche' scade un timer di keepalive. E' come una telefonata: se uno stacca il telefono senza riagganciare, l'altro resta in linea in silenzio finche' non prova a parlare.

**Cosa deve fare il tunnel_manager:**
Rilevare il resume da sleep (Windows espone eventi di power state) e forzare un health check o un restart di `frpc` al wake-up. Non fidarsi che la connessione sia ancora viva dopo un sleep.

**Failure mode:** senza gestione -> tunnel silenziosamente morto dopo ogni sleep. Il trainer deve chiudere e riaprire FitManager manualmente.

---

### 2.2 Rete che cade e torna (frequenza: alta)

**Livello 1 — Cosa succede:**
WiFi instabile, router che si riavvia, passaggio WiFi->ethernet, hotspot mobile. La connessione TCP si spezza.

**Livello 2 — Due sottocasi con gravita' diversa:**
- **frpc se ne accorge** -> esce con errore -> il tunnel_manager lo vede (processo morto) e lo rilancia. Caso semplice.
- **frpc NON se ne accorge** -> il processo resta vivo ma la connessione e' morta. Caso insidioso: il controllo "il processo e' vivo?" dice SI, ma il tunnel non funziona.

**Livello 3 — Perche' il secondo caso esiste:**
Per lo stesso motivo del sleep: TCP non ha un meccanismo istantaneo per rilevare una connessione rotta dall'altra parte. Se la rete cade e torna, `frpc` potrebbe pensare di essere ancora connesso alla vecchia sessione TCP, che in realta' non esiste piu' lato server.

**Cosa deve fare il tunnel_manager:**
Non basta controllare "il processo e' vivo?". Serve un **health check attivo**: chiamare periodicamente un endpoint attraverso il tunnel e verificare che risponde. Se il processo e' vivo ma il tunnel non funziona -> kill + restart.

**Nota:** `frpc` ha un meccanismo interno di reconnect. Da verificare in pratica quanto e' affidabile e se copre questo caso o se serve supervisione aggiuntiva.

**Failure mode:** senza health check -> tunnel morto con processo vivo. La diagnostica dice "tutto ok" ma il portale non risponde.

---

### 2.3 frpc crasha (frequenza: bassa)

**Livello 1 — Cosa succede:**
Il processo `frpc` muore (crash, errore fatale, OOM). Il tunnel_manager lo rileva tramite l'exit code del processo figlio e lo rilancia.

**Livello 2 — L'attenzione necessaria: backoff esponenziale.**
Se `frpc` crasha subito dopo il lancio (configurazione sbagliata, porta occupata), rilanciarlo immediatamente in loop consuma CPU e riempie i log. Serve un pattern di attesa crescente.

**Livello 3 — Il pattern backoff:**
- Primo retry: 1 secondo
- Secondo: 2 secondi
- Terzo: 4 secondi
- ...fino a un cap (es. 60 secondi)
- Reset del backoff dopo un periodo di stabilita' (es. 5 minuti connesso = torna a 1s)

Il backoff impedisce il "retry storm" — lo stesso principio per cui i client HTTP ben scritti non riprovano tutti insieme dopo un errore del server. E' un concetto trasversale che si ritrova ovunque nei sistemi distribuiti.

**Failure mode:** senza backoff -> CPU al 100%, log giganteschi, il PC del trainer rallenta.

---

### 2.4 frps si riavvia (frequenza: rara)

**Livello 1 — Cosa succede:**
Aggiornamento di `frps` sul VPS, o manutenzione del provider (Hetzner). Tutti i tunnel dei trainer cadono simultaneamente.

**Livello 2 — Perche' mi importa:**
Non e' un caso edge del tunnel_manager in se' — il comportamento e' identico al caso 2.2 (rete cade e torna). Ma ha un'implicazione operativa: **ogni manutenzione VPS disconnette tutti i trainer**. Le manutenzioni vanno fatte in orari morti e il recovery deve essere automatico e rapido.

**Livello 3 — Interazione col backoff:**
Se 50 trainer tentano il reconnect simultaneamente dopo un restart di `frps`, serve che i retry siano **sfalsati** (jitter). Il backoff puro senza jitter farebbe riprovare tutti allo stesso istante -> thundering herd -> `frps` sotto carico. Si aggiunge un ritardo casuale al backoff: `delay = base_delay * 2^attempt + random(0, base_delay)`.

**Failure mode:** senza jitter -> tutti riconnettono insieme -> frps sovraccarico -> fallisce di nuovo -> loop.

---

### 2.5 Doppia istanza di FitManager (frequenza: media)

**Livello 1 — Cosa succede:**
Il trainer clicca due volte sull'icona. Due processi FitManager -> due tunnel_manager -> due `frpc` che tentano di aprire lo stesso tunnel.

**Livello 2 — Perche' e' un problema:**
Conflitto: il secondo `frpc` potrebbe fallire (tunnel gia' registrato su `frps`) o, peggio, entrambi alternano connessioni in modo instabile.

**Livello 3 — Il meccanismo di protezione: lockfile.**
Prima di avviare `frpc`, il tunnel_manager verifica se c'e' gia' un'istanza in esecuzione. Pattern standard: un **lockfile** (o PID file) — un file che dice "io sono gia' attivo, il mio PID e' X". Se il file esiste e il processo con quel PID e' vivo -> non lanciare. Se il file esiste ma il processo e' morto (crash precedente senza cleanup) -> sovrascrivere e procedere.

Nota: questo potrebbe gia' essere gestito a livello di FitManager (impedire doppia istanza dell'app intera). Da verificare nel codebase — se l'app gia' impedisce doppia istanza, il tunnel_manager eredita la protezione gratis.

**Failure mode:** senza protezione -> tunnel instabile, log confusi, difficile da diagnosticare.

---

### 2.6 Shutdown pulito (frequenza: ogni sessione)

**Livello 1 — Cosa succede:**
Il trainer chiude FitManager. Se il tunnel_manager non uccide `frpc`, resta un **processo orfano**: `frpc` gira in background senza genitore, occupa risorse, e al prossimo avvio c'e' conflitto.

**Livello 2 — Cosa deve fare:**
Registrare un handler di shutdown che fa kill del processo `frpc` figlio prima di uscire. Su Windows: `process.terminate()` + timeout breve + `process.kill()` se non risponde.

**Livello 3 — Il concetto sotto: processo orfano.**
Quando un processo genitore muore senza uccidere i figli, i figli diventano "orfani" — continuano a girare ma nessuno li controlla piu'. Su Unix vengono adottati da init/systemd. Su Windows restano attivi finche' non terminano da soli o vengono uccisi manualmente. E' un concetto di gestione processi che vale in ogni sistema operativo.

**Failure mode:** senza cleanup -> processi orfani accumulati, porte occupate, conflitti al riavvio.

---

### 2.7 Firewall / Antivirus (frequenza: al primo avvio — alta gravita')

**Livello 1 — Cosa succede:**
Windows Defender o un antivirus vede `frpc.exe` come eseguibile sconosciuto e lo blocca. Il processo non parte o parte ma non puo' aprire connessioni di rete.

**Livello 2 — Perche' e' particolarmente insidioso:**
L'errore si manifesta in modi confusi: timeout, "connessione rifiutata", permesso negato. Il trainer non pensa all'antivirus — pensa che il software sia rotto.

**Livello 3 — Strategia di mitigazione (non soluzione perfetta):**
- Lato installer: firma digitale dell'eseguibile, eccezione firewall Windows durante l'installazione (Inno Setup puo' farlo).
- Lato tunnel_manager: catturare stderr/stdout di `frpc`, riconoscere pattern di errore (permission denied, access denied) e mostrare un messaggio chiaro al trainer ("il tuo antivirus potrebbe bloccare la connessione").
- Lato documentazione: includere nel supporto una guida "come autorizzare FitManager nel firewall".

Non esiste una soluzione tecnica al 100% — l'antivirus e' sovrano sul PC del trainer. Si puo' solo minimizzare l'attrito.

**Failure mode:** senza gestione -> il trainer pensa che il software sia rotto, contatta il supporto, frustrazione.

---

## 3. Il principio trasversale: health check end-to-end

Il filo comune dei casi 2.1 e 2.2 (i piu' frequenti) e' che **lo stato del processo non riflette lo stato del tunnel**. Processo vivo != tunnel funzionante.

Il pattern risolutivo e' il **health check end-to-end**: il tunnel_manager, periodicamente, fa una richiesta HTTP attraverso il tunnel (es. chiama `https://slug.fitmanagerstudio.com/health`) e verifica che risponde. Se non risponde -> il tunnel e' morto indipendentemente dallo stato del processo -> kill + restart.

Questo e' lo stesso principio dei load balancer in produzione: non basta che il server sia acceso, deve rispondere correttamente a una richiesta di test. E' un fondamentale dei sistemi distribuiti.

---

## 4. Riepilogo: cosa deve fare il tunnel_manager (checklist di design)

- [x] Avvio `frpc` come processo figlio con stdout/stderr catturati (subprocess.Popen + drain thread)
- [ ] Lockfile/PID per impedire doppia istanza (rimandato: frps rifiuta tunnel duplicati per name)
- [x] Restart automatico con backoff esponenziale + jitter (BackoffTimer, testato con kill simulato)
- [ ] Health check periodico end-to-end (non solo "processo vivo?") — rimandato a dopo e2e funzionante
- [ ] Rilevamento sleep/wake Windows -> health check forzato al resume — rimandato a raffinamento
- [x] Shutdown handler: kill `frpc` alla chiusura dell'app (atexit + terminate/kill con timeout 5s)
- [x] Log strutturato di ogni evento (avvio, restart, errore, health check)
- [x] Messaggi diagnostici leggibili per errori firewall/antivirus (PermissionError catturato con messaggio)

---

## 5. Domande aperte (da chiudere in Fase 1)

- [x] `frpc` ha un reconnect interno? — Si', frpc rileva disconnessione e riprova. Ma il tunnel_manager aggiunge supervisione extra (process monitor + backoff) per i casi che frpc non copre (crash, sleep/wake).
- [ ] FitManager impedisce gia' la doppia istanza a livello app? — Da verificare. In ogni caso, frps rifiuta tunnel con lo stesso `name`, quindi doppia istanza frpc = errore pulito (non instabilita').
- [ ] Come si rilevano gli eventi di power state (sleep/wake) su Windows da Python? — Rimandato a raffinamento post-e2e.
- [ ] La firma digitale dell'installer copre anche `frpc.exe` bundlato, o serve firma separata? — Da verificare con Inno Setup.
- [x] Qual e' il timeout giusto per l'health check? — Monitor ogni 5s (MONITOR_INTERVAL). Health check e2e da definire dopo tunnel funzionante.
