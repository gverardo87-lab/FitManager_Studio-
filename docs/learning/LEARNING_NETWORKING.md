# LEARNING_NETWORKING.md

**Progetto:** FitManager
**Ambito:** Concetti di rete incontrati durante lo sviluppo — NAT, porte, tunnel, reverse proxy, DNS, TLS
**Metodo:** vedi `LEARNING_METHOD.md` — tre livelli di "perche'" + failure mode
**Convenzione:** i concetti vivono qui una volta sola. Il diario cronologico sta in `BUILD_LOG.md` e rimanda qui.
**Macro di riferimento:** `ARCHITECTURE_OVERVIEW.md` (la metafora del centralino), `TUNNEL_MIGRATION_STRATEGY.md`, `VPS_EDGE_SETUP.md`.

---

## Indice concetti

- [Porte di rete](#porte)
- [localhost / 127.0.0.1 vs IP pubblico](#localhost)
- [NAT: perche' un PC dietro un router non e' raggiungibile](#nat)
- [Tunnel: come si aggira il NAT](#tunnel)
- [FRP (Fast Reverse Proxy): cos'e' e i due pezzi frps/frpc](#frp)
- [I piani di accesso del VPS (porte = stanze diverse)](#piani-accesso)
- [Lettura del test e2e di Fase 0 (perche' un 307 e' una prova)](#test-e2e)

---

<a name="porte"></a>
## Porte di rete — 03/06/2026

**Livello 1 — Cosa fa:**
Un computer raggiungibile in rete ha UN indirizzo (IP), ma puo' offrire piu' servizi contemporaneamente. Le "porte" sono numeri che distinguono i servizi sullo stesso indirizzo. IP = indirizzo del palazzo; porta = numero della stanza/ufficio dentro il palazzo.

**Livello 2 — Perche' mi importa:**
Sul VPS girano piu' programmi insieme: SSH (amministrazione), FRP server (tunnel), dashboard FRP, HTTPS pubblico. Senza le porte non potrei distinguerli sullo stesso IP. Il firewall (ufw) lavora proprio sulle porte: decide quali stanze sono accessibili dalla strada.

**Livello 3 — Perche' funziona cosi' sotto:**
Una connessione di rete e' identificata dalla combinazione IP+porta su entrambi i lati. Quando un programma "ascolta" su una porta, dice al sistema operativo "consegna a me il traffico diretto a questa porta". Alcune porte hanno usi convenzionali (22=SSH, 443=HTTPS, 80=HTTP) ma sono convenzioni, non leggi fisiche: un servizio puo' girare su qualsiasi porta.

**Porte del VPS FitManager:**
| Porta | Servizio | Esposta a |
|-------|----------|-----------|
| 22 | SSH (amministrazione) | Internet (protetta da chiave) |
| 443 | HTTPS (clienti finali) | Internet |
| 7000 | FRP server (aggancio PC trainer) | Internet |
| 7500 | Dashboard FRP | solo localhost (non Internet) |

**Failure mode:**
Aprire nel firewall una porta che non serve = stanza accessibile dalla strada senza motivo = superficie d'attacco in piu'. Principio: aprire solo le porte necessarie, chiudere il resto (vedi cleanup porta 8080 dopo il test).

---

<a name="localhost"></a>
## localhost / 127.0.0.1 vs IP pubblico — 03/06/2026

**Livello 1 — Cosa fa:**
`127.0.0.1` (nome: `localhost`) e' un indirizzo speciale che significa "questo stesso computer". Un servizio in ascolto su 127.0.0.1 risponde SOLO a richieste che nascono dentro la macchina stessa, non da fuori. L'IP pubblico (es. `128.140.91.39`) e' invece l'indirizzo su cui la macchina e' raggiungibile da Internet.

**Livello 2 — Perche' mi importa:**
La dashboard FRP ascolta su `127.0.0.1:7500`: da Internet NON e' raggiungibile, neanche conoscendo l'IP pubblico del VPS. Per arrivarci devo prima entrare nel server (via SSH) e poi accedervi "da dentro". E' il motivo per cui la password della dashboard, pur finita in chiaro in un documento, aveva esposizione limitata: per usarla un attaccante dovrebbe gia' essere dentro.

**Livello 3 — Perche' funziona cosi' sotto:**
`127.0.0.1` e' l'interfaccia di "loopback": il traffico verso questo indirizzo non esce mai sulla scheda di rete, fa un giro interno alla macchina. Un programma sceglie a quale indirizzo legarsi (bind): se si lega a 127.0.0.1 e' privato alla macchina; se si lega a 0.0.0.0 (tutte le interfacce) e' raggiungibile da fuori (firewall permettendo). Il backend FitManager si lega a 127.0.0.1 in produzione apposta: non vuole essere raggiungibile direttamente, solo attraverso il tunnel.

**Failure mode:**
Confondere "il servizio ascolta su una porta" con "il servizio e' raggiungibile da Internet": dipende dall'indirizzo di bind E dal firewall. Un servizio su 0.0.0.0 con la porta aperta nel firewall = esposto. Su 127.0.0.1 = privato anche se la porta fosse aperta.

---

<a name="nat"></a>
## NAT: perche' un PC dietro un router non e' raggiungibile — 03/06/2026

**Contesto:** il cuore del problema che FitManager deve risolvere. Il PC del trainer e' in palestra, dietro un router. Il cliente finale e' su Internet. Perche' non puo' raggiungerlo direttamente?

**Livello 1 — Cosa fa:**
Un dispositivo dietro un router ha un indirizzo privato (es. `192.168.1.50`) valido solo dentro la rete locale. Verso Internet, il router espone un solo indirizzo pubblico e tiene nascosti i dispositivi interni. Risultato: i dispositivi interni POSSONO iniziare connessioni verso l'esterno, ma l'esterno NON puo' iniziarle verso di loro.

**Livello 2 — Perche' mi importa:**
E' la ragione per cui non posso semplicemente "dare al cliente l'indirizzo del PC del trainer". Quell'indirizzo non esiste su Internet. E' anche il motivo per cui esisteva Tailscale prima, e ora FRP: serve un meccanismo per aggirare questa asimmetria. Ed e' perche' non voglio chiedere al trainer di configurare il router (aprire porte, port forwarding): troppo complesso, viola il vincolo "zero configurazione".

**Livello 3 — Perche' funziona cosi' sotto:**
NAT = Network Address Translation. Gli indirizzi privati (192.168.x.x, 10.x.x.x) non sono instradabili su Internet: esistono apposta per le reti locali e si ripetono in milioni di case. Il router fa da traduttore: quando un dispositivo interno apre una connessione, il router sostituisce l'indirizzo privato col proprio pubblico e tiene una tabella per ricondurre le risposte al dispositivo giusto. Ma una connessione che ARRIVA da fuori non e' in quella tabella (non corrisponde a niente che e' stato iniziato dall'interno), quindi il router non sa a chi consegnarla e la scarta. Da qui l'asimmetria: uscita si', entrata no.

**Failure mode:**
Pensare di risolvere con "port forwarding sul router del trainer" -> richiede configurazione manuale per ogni trainer, IP pubblici che cambiano, e spesso le reti aziendali/palestre non lo permettono. Per questo la soluzione e' il tunnel (sotto), non l'apertura del router.

---

<a name="tunnel"></a>
## Tunnel: come si aggira il NAT — 03/06/2026

**Livello 1 — Cosa fa:**
Visto che l'interno puo' iniziare connessioni verso l'esterno ma non viceversa, si capovolge il problema: e' il PC del trainer che apre per primo una connessione verso un punto pubblico (il VPS) e la tiene aperta. Quella connessione persistente diventa un canale a doppio senso in cui far viaggiare il traffico dei clienti.

**Livello 2 — Perche' mi importa:**
E' il meccanismo centrale di tutta l'architettura FitManager. Il VPS e' il "punto pubblico sempre acceso" che esiste solo per fare da aggancio ai tunnel. Senza tunnel, niente accesso dei clienti finali alle istanze dei trainer.

**Livello 3 — Perche' funziona cosi' sotto:**
La connessione iniziata dall'interno E' nella tabella NAT del router (e' uscita, quindi le risposte rientrano). Finche' resta aperta, il VPS puo' rimandare indietro traffico lungo quella stessa connessione: tecnicamente sono "risposte" a una connessione che il PC del trainer ha iniziato, quindi il router le lascia passare. Il tunnel sfrutta esattamente la regola del NAT (uscita si', le risposte rientrano) per ottenere un canale bidirezionale.

**Failure mode:**
Se il PC del trainer e' spento, il tunnel non esiste e lo studio e' offline (per questo serve la pagina "studio offline" sul VPS). Se la connessione cade, il client deve riconnettersi (FRP lo fa in automatico).

---

<a name="frp"></a>
## FRP (Fast Reverse Proxy): cos'e' e i due pezzi — 03/06/2026

**Contesto:** il programma scelto per realizzare i tunnel (sostituisce Tailscale). Da capire a fondo: e' infrastruttura centrale.

**Livello 1 — Cosa fa:**
FRP e' un programma che fa da tramite per esporre su Internet un servizio che vive in un posto non raggiungibile direttamente (dietro NAT). E' software libero, gratuito, maturo, scritto in Go, distribuito come binario (singolo file eseguibile, niente ecosistema da installare).

**Livello 2 — Perche' lo voglio (vs alternative):**
Realizza il tunnel mantenendo il VPS "data-blind" (P2): in modalita' TCP passthrough il VPS instrada senza decifrare il TLS. Cloudflare Tunnel e' stato escluso perche' Cloudflare terminerebbe il TLS (vedrebbe il traffico, violando P2). FRP e' un binario piccolo bundlabile nel prodotto del trainer.

**Livello 3 — Perche' funziona cosi' sotto (il nome lo spiega):**
- **Proxy** = intermediario che inoltra traffico tra due parti (ne' origine ne' destinazione, il tramite).
- **Reverse** = sta davanti al SERVER (non al client): riceve le richieste dall'esterno e le gira al server giusto dietro di lui. Il VPS fa questo.
- **Fast** = solo il nome (scritto in Go).

**I due pezzi (la coppia che fa tutto):**
- `frps` (server): gira sul VPS, ascolta sulla porta 7000, aspetta i client. E' il centralino. Installato in `/opt/frp/` come servizio systemd (riparte da solo al boot).
- `frpc` (client): gira sul PC del trainer, INIZIA la connessione verso frps (dall'interno verso l'esterno, l'unica direzione consentita dal NAT) e tiene il tunnel aperto.

**Dinamica completa:**
1. `frpc` (PC trainer) si connette a `frps` (VPS:7000): "sono Alessio, tieni aperto il tunnel".
2. `frps` registra: traffico per Alessio -> dentro questo tunnel.
3. Cliente apre `alessio.fitmanagerstudio.com` -> DNS wildcard -> IP del VPS:443.
4. `frps` riceve, capisce che e' per Alessio, infila la richiesta nel tunnel.
5. PC di Alessio risponde, la risposta torna per lo stesso tunnel al cliente.

**Failure mode:**
Confondere frps e frpc (chi sta dove): il server e' sul VPS, il client sul PC del trainer. Il client inizia sempre la connessione, mai il contrario (vincolo NAT).

**Domande aperte:**
- [ ] Capire la differenza tra modalita' tcp (test fatto, senza TLS) e https/passthrough (Fase 2, con TLS e2e) a livello di cosa vede il VPS
- [ ] Cos'e' SNI routing (come frps decide a quale tunnel mandare senza decifrare)

---

<a name="piani-accesso"></a>
## I piani di accesso del VPS (porte = stanze diverse) — 03/06/2026

**Contesto:** confusione iniziale tra "passphrase SSH" e "password dashboard FRP", trattate come lucchetti sullo stesso cancello. Sono su porte/scopi diversi.

**Il punto chiave:** la mia sessione SSH (amministrazione) e il funzionamento del servizio per i trainer sono PIANI INDIPENDENTI.
- Entro/esco dalla porta 22 (admin) senza toccare le porte 7000/443 (trainer e clienti).
- Se mi scollego dall'SSH, NON succede niente ai trainer: il servizio gira da solo (FRP come servizio systemd). Prova: ho riavviato tutto il server e FRP e' tornato su da solo, senza che fossi connesso.

**Le due password, finalmente distinte:**
| Password | Apre | Dove agisce | Se esposta |
|----------|------|-------------|------------|
| Passphrase SSH | la chiave privata -> porta 22 | sul MIO PC (decifra la chiave, non viaggia al VPS) | chi ruba il mio PC entra nel server |
| Password dashboard FRP | porta 7500 (pannello FRP) | dentro il VPS, solo localhost | esposizione limitata (serve gia' essere dentro), ma va cambiata per principio |

**Sottigliezza sulla passphrase SSH:** non "sblocca il VPS". Sblocca la chiave privata SUL MIO PC. L'operazione avviene a Marsiglia prima che parta qualcosa verso la Germania. Il VPS non conosce la passphrase. (vedi LEARNING_LINUX_SYSADMIN §passphrase)

**Defense-in-depth:** un segreto esposto si considera bruciato e si cambia, anche se "tanto c'e' un altro strato che protegge". Le configurazioni cambiano (un domani la dashboard potrebbe essere esposta diversamente); non si lascia un segreto appeso a un'assunzione ("restera' sempre su localhost").

---

<a name="test-e2e"></a>
## Lettura del test e2e di Fase 0 (perche' un 307 e' una prova) — 03/06/2026

**Contesto:** il test del 02/06 ha restituito HTTP 307 e questo e' stato considerato un successo. Perche'?

**Cosa diceva il test:**
- Tunnel `tcp` aperto: porta 8080 del VPS mappata alla 3001 del PC dev (dove girava Next.js).
- Dal VPS: `curl http://127.0.0.1:8080` -> risposta `307`.

**Perche' 307 = successo:**
307 e' un codice HTTP di "redirect temporaneo". Significa che QUALCOSA di vivo ha risposto: il frontend Next.js ha detto "vai al login". Il punto del test non era il contenuto della risposta, ma il fatto che una richiesta partita sul VPS (Germania) sia arrivata fino al PC dev (Italia) attraverso il tunnel e sia tornata indietro. Il 307 e' la prova che il giro completo ha funzionato: se il tunnel non avesse trasportato nulla, `curl` non avrebbe ricevuto nessun codice (errore di connessione), non un 307.

**Cosa il test NON dimostra (importante):**
Era un tunnel `tcp` SENZA TLS: il traffico passava in chiaro, quindi in questo test il VPS AVREBBE potuto leggerlo. La proprieta' "data-blind" (P2) NON e' dimostrata da questo test. Dipende dal TLS e2e (Fase 2). Faro: il test che conta per P2/GDPR e' quello di Fase 2.

**Failure mode di interpretazione:**
Concludere "data-blind funziona" da questo test = errore. Ha provato solo la connettivita' del tunnel, non la cecita' del VPS sul contenuto.
