# LEARNING_LINUX_SYSADMIN.md

**Progetto:** FitManager
**Ambito:** Concetti di amministrazione di sistema Linux/Unix incontrati durante lo sviluppo
**Metodo:** vedi `LEARNING_METHOD.md` — tre livelli di "perche'" + failure mode
**Convenzione:** i concetti vivono qui una volta sola, organizzati per tema. Il diario cronologico ("cosa ho fatto quando") sta in `BUILD_LOG.md` e rimanda qui.

---

## Indice concetti

- [Crittografia asimmetrica (chiave pubblica/privata)](#crittografia-asimmetrica)
- [Coppia di chiavi SSH: i due file](#coppia-di-chiavi-ssh)
- [La passphrase della chiave privata](#passphrase-chiave-privata)
- [Il kernel e perche' serve il reboot dopo l'aggiornamento](#kernel-reboot)
- [L'estensione di un file e' solo un'etichetta](#estensione-etichetta)
- [Quando AI/documento e sistema divergono, vince il sistema](#fonte-di-verita)

---

<a name="crittografia-asimmetrica"></a>
## Crittografia asimmetrica (chiave pubblica/privata) — 02/06/2026

**Contesto:** dovevo generare una SSH key per accedere al VPS Hetzner senza password. Per capire *perche'* le chiavi battono le password ho dovuto capire la crittografia asimmetrica, che e' il fondamentale sotto SSH, TLS, i JWT di licenza e Let's Encrypt. Vale il livello 3 pieno: lo ritrovo ovunque.

**Livello 1 — Cosa fa:**
Genero una coppia di chiavi matematicamente legate: una privata (resta segreta sul mio PC) e una pubblica (posso distribuirla liberamente). Quello che una "chiude", l'altra lo verifica. Conoscere la pubblica NON permette di ricavare la privata.

**Livello 2 — Perche' la voglio (vs password):**
Con una password il segreto e' *condiviso*: lo conosco io e lo conosce il server, e per autenticarmi devo trasmettere qualcosa che ne dipende. Due debolezze: (a) un segreto condiviso puo' trapelare da due posti — se il server e' compromesso, la password se ne va; (b) un VPS appena acceso con SSH a password viene martellato in minuti da botnet che scansionano IP e provano root + password comuni h24. Con le chiavi il segreto (la privata) non e' condiviso e non viene MAI trasmesso: elimino la categoria stessa del brute-force.

**Livello 3 — Perche' funziona cosi' sotto:**
La sicurezza nasce da un'asimmetria computazionale: un calcolo e' facile in un senso e impossibile nell'altro. In RSA si basa sulla fattorizzazione di numeri primi enormi; in Ed25519 su curve ellittiche. Al login il server mi pone una "sfida" che solo chi possiede la chiave privata corrispondente alla pubblica registrata puo' risolvere. Io la risolvo sul mio PC con la privata: la privata non attraversa mai la rete. Un attaccante che osserva tutto il traffico non vede nulla di riutilizzabile. E' la stessa famiglia di meccanismi di: TLS (il tunnel data-blind, P2 del blueprint), la firma del JWT di licenza (AVGV firma con privata, il software verifica con pubblica — D3 strategia tunnel), Let's Encrypt.

**Failure mode:**
Se confondo il modello e tratto la chiave privata come "una password piu' lunga" da poter condividere/incollare -> la sicurezza crolla. La privata e' l'UNICO segreto e il suo valore sta tutto nel non lasciare mai il mio PC.

**Domande aperte:**
- [ ] Capire meglio il dettaglio del challenge-response SSH (cosa viene firmato esattamente)
- [ ] Collegare a TLS quando configuro il cert Let's Encrypt (Fase 2 tunnel)

---

<a name="coppia-di-chiavi-ssh"></a>
## Coppia di chiavi SSH: i due file — 02/06/2026

**Contesto:** generazione chiave su Windows/PowerShell prima di creare il VPS Hetzner, per iniettare la pubblica alla creazione del server.

**Livello 1 — Cosa fa:**
`ssh-keygen -t ed25519 -C "etichetta"` produce due file nella cartella `.ssh` della home:
- `id_ed25519` (senza estensione) = **chiave privata**, resta sul PC, non si incolla MAI da nessuna parte.
- `id_ed25519.pub` = **chiave pubblica**, e' quella che incollo su Hetzner. `.pub` = public = quella che esce nel mondo.

**Livello 2 — Perche' la voglio:**
Generando la chiave *prima* di creare il VPS, Hetzner mi permette di iniettare la pubblica alla creazione: il server nasce gia' accessibile a chiave e puo' nascere senza password abilitata. Salto del tutto la finestra di vulnerabilita' in cui sarebbe esposto al brute-force. Prevenzione, non rimedio.

**Livello 3 — Perche' funziona cosi' sotto:**
Gli argomenti del comando:
- `-t ed25519` = tipo di algoritmo. Ed25519 (curve ellittiche) = scelta moderna: chiavi molto piu' corte di RSA a parita' di robustezza, piu' veloci. `-t rsa -b 4096` non e' sbagliato, e' datato.
- `-C "..."` = comment, etichetta appiccicata in fondo alla pubblica. Nessun effetto sulla sicurezza, serve solo a me per distinguere le chiavi.
La cartella `.ssh` nella home e' la convenzione che il client SSH si aspetta di default. Su Windows = `C:\Users\<nome>\.ssh\`, su Linux = `~/.ssh/`. Stessa logica, percorso diverso.

**Comando reale:**
```powershell
ssh-keygen -t ed25519 -C "giacomo-avgv-hetzner"
```

**Failure mode:**
Se apro `id_ed25519` (la privata) e ne incollo il contenuto fuori dal PC (sito, chat, screenshot) -> chiave compromessa: la butto e ne rigenero una. L'UNICO file che si incolla e' quello che finisce in `.pub`. Regola: se un servizio mi chiede di incollare la chiave *privata*, il servizio e' sbagliato.

**Domande aperte:**
- [ ] Visualizzare la pubblica in PowerShell (comando diverso da `cat` di Linux) — prossimo step
- [ ] Capire come SSH sceglie quale chiave usare quando ne ho piu' di una (config file ~/.ssh/config)

---

<a name="passphrase-chiave-privata"></a>
## La passphrase della chiave privata — 02/06/2026

**Contesto:** `ssh-keygen` chiede "Enter passphrase" durante la generazione. Decisione di sicurezza, non fastidio da saltare.

**Livello 1 — Cosa fa:**
Cifra il file della chiave privata con una password. Senza passphrase il file e' usabile da solo; con passphrase serve anche qualcosa che so per usarlo.

**Livello 2 — Perche' la voglio:**
La privata e' un file sul PC. Senza passphrase, chiunque metta le mani sul file (laptop rubato, malware, backup finito male) *e'* me dal punto di vista del server. Con passphrase, il file da solo non basta: e' il secondo fattore applicato alla chiave. Scenario concreto: laptop che viaggia tra Marsiglia e Italia = "dispositivo che puo' essere perso/rubato". La passphrase e' la differenza tra incidente e catastrofe.

**Livello 3 — Perche' funziona cosi' sotto:**
Il prezzo della passphrase e' digitarla all'uso. Ma `ssh-agent` e' un processo che la tiene in memoria dopo la prima volta nella sessione, quindi non la ridigito a ogni connessione: il costo e' una volta per sessione, non sempre. Decisione presa: passphrase SI (questo VPS porta il traffico dei clienti).

**Failure mode:**
Se salto la passphrase "per comodita'" e poi perdo il controllo del PC -> accesso pieno al VPS senza ulteriori barriere. Se invece dimentico la passphrase -> non recupero la chiave, ne genero una nuova e aggiorno la pubblica sul server (non e' una catastrofe perche' la pubblica e' sostituibile).

**Domande aperte:**
- [ ] Configurare ssh-agent su Windows perche' non chieda la passphrase a ogni connessione (incontrato dal vivo 03/06: la passphrase viene chiesta a ogni `ssh`, a volte due volte)

---

<a name="kernel-reboot"></a>
## Il kernel e perche' serve il reboot dopo l'aggiornamento — 03/06/2026

**Contesto:** dopo `apt upgrade` sul VPS, il documento diceva kernel `7.0.0-22` ma `uname -r` rispondeva `7.0.0-15`. In `/boot` c'erano DUE kernel (`-15` e `-22`). Capito perche' e risolto con reboot. Fondamentale Unix incontrato dal vivo: livello 3 pieno.

**Livello 1 — Cosa fa:**
Il kernel e' il programma centrale del sistema operativo: parla con l'hardware, gestisce memoria e processi, controlla accesso a file e rete. Quando lo aggiorno con `apt`, il file nuovo viene messo sul disco (`/boot`) ma NON sostituisce quello attualmente in esecuzione. Serve un reboot perche' il nuovo entri in funzione.

**Livello 2 — Perche' mi importa:**
Gli aggiornamenti di kernel sono spesso patch di sicurezza nel cuore del sistema. Un kernel di sicurezza installato ma non attivo NON protegge: la patch e' sul disco ma il sistema gira ancora sul codice vecchio e vulnerabile (serratura nuova lasciata nella scatola). Quindi "kernel aggiornato" e' vero solo dopo il reboot. La Fase 0 non era chiusa al 100% finche' non ho riavviato.

**Livello 3 — Perche' funziona cosi' sotto:**
Il kernel viene caricato in memoria (RAM) UNA volta sola, all'avvio, e ci resta finche' il sistema e' acceso. Tutti gli altri programmi girano *sopra* quel kernel in memoria. Non si puo' scambiare il kernel attivo mentre regge il sistema in tempo reale ("non sostituisci il pavimento mentre ci cammini sopra"). Per questo `apt` puo' solo depositare il nuovo kernel in `/boot`: i due file convivono apposta (`-15` in esecuzione, `-22` in attesa). Al boot successivo il bootloader carica in RAM il piu' recente (`-22`) e da li' `uname -r` lo conferma. Differenza con un programma normale (es. `nano`): quello al prossimo lancio parte gia' aggiornato, perche' non e' caricato permanentemente in memoria come il kernel.

**Comandi reali:**
```bash
uname -r                  # kernel attualmente in esecuzione (in RAM)
ls -t /boot/vmlinuz-*     # kernel presenti sul disco, piu' recente per primo
reboot                    # riavvia: il bootloader carichera' il kernel piu' recente
# dopo riconnessione:
uname -r                  # ora conferma il kernel nuovo
```

**Failure mode:**
Se installo un kernel di sicurezza e non riavvio mai -> resto vulnerabile pur "credendo" di essere aggiornato. Sintomo diagnostico: `uname -r` (in esecuzione) diverso dal piu' recente in `/boot` (installato) = reboot pendente. Su un server con utenti reali il reboot va pianificato (cade la connessione ~30-60s); su questo VPS era a basso rischio perche' nessun trainer in produzione e FRP riparte da solo via systemd.

**Domande aperte:**
- [ ] Capire `unattended-upgrades` e se/come gestisce i reboot automatici per le patch di sicurezza

---

<a name="estensione-etichetta"></a>
## L'estensione di un file e' solo un'etichetta — 02/06/2026

**Contesto:** Esplora risorse di Windows mostrava `id_ed25519.pub` come "Microsoft Publisher Document". Non lo e'.

**Livello 1 — Cosa fa:**
Windows associa l'estensione `.pub` al programma Publisher e mostra quell'icona/tipo. Ma il file e' un semplice file di testo contenente la chiave pubblica. L'estensione non determina il contenuto.

**Livello 2 — Perche' mi importa:**
Mi ha quasi confuso facendomi pensare che la chiave fosse un documento Publisher. Sapere che l'estensione e' solo un'etichetta evita errori (es. aprire la chiave col doppio clic -> Windows lancia Publisher e fa pasticci). La pubblica va letta come testo, da terminale.

**Livello 3 — Perche' funziona cosi' sotto:**
Su Windows l'associazione e' guidata dall'estensione (mappa estensione -> programma). Il contenuto reale e' un'altra cosa: i byte del file non cambiano per via dell'estensione. Su Linux le estensioni contano molto meno: cosa sia un file si deduce dal contenuto, non dal suffisso (un'altra differenza nel modo in cui Unix e Windows ragionano).

**Failure mode:**
Doppio clic su file con estensione "ingannevole" -> il programma sbagliato prova ad aprirlo. Per file tecnici (chiavi, config) leggere sempre da terminale con `Get-Content` (PowerShell) o `cat` (Linux), non col doppio clic.

---

<a name="fonte-di-verita"></a>
## Quando AI/documento e sistema divergono, vince il sistema — 03/06/2026

**Contesto:** Claude (chat) ha dubitato che "Ubuntu 26.04 / kernel 7.0.0" fossero reali (sembravano troppo recenti). `lsb_release -a` ha confermato: 26.04 "Resolute" e' reale. Aveva ragione il sistema, torto l'AI.

**Livello 1 — Cosa fa (come principio operativo):**
Di fronte a un fatto verificabile (versione, stato di un servizio, contenuto di un file), non scegliere tra due opinioni (documento vs AI): interroga la fonte autorevole, cioe' il sistema stesso.

**Livello 2 — Perche' mi importa:**
- Claude (chat) ha una data di taglio delle conoscenze: non e' aggiornato sul presente (Ubuntu 26.04 e' uscita dopo il suo orizzonte). E' utile per ragionare, NON e' fonte di verita' sul presente.
- Un documento descrive il sistema in un certo momento e puo' divergere (refusi, stato cambiato dopo la stesura — vedi il kernel -22 scritto ma non ancora attivo).
- Il sistema, interrogato, dice la verita' su se stesso adesso.

**Livello 3 — Perche' funziona cosi' (gerarchia delle fonti):**
Gerarchia di affidabilita' per un fatto sul presente: sistema reale > documento recente > memoria/AI. Comandi di verita': `lsb_release -a` (distro), `uname -r` (kernel in esecuzione), `systemctl status <servizio>` (stato reale di un servizio), `ufw status verbose` (firewall reale). Corollario del metodo (Principio: il sistema vince sul documento): quando divergono, si aggiorna il documento al sistema, mai il contrario.

**Failure mode:**
Fidarsi del documento o dell'AI su un fatto verificabile -> portarsi dietro un'imprecisione (es. credere il kernel aggiornato quando non lo e'). L'antidoto e' gratis: un comando di verifica.

**Domande aperte:**
- [ ] Tenere a mente: questo vale anche per il codice che Claude Code genera — gira davvero? lo verifico, non lo assumo.
