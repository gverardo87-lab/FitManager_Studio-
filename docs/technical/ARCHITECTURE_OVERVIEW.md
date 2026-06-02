# ARCHITECTURE_OVERVIEW.md

**Progetto:** FitManager
**Versione:** 1.0
**Data:** 2026-06-02
**Scopo:** La mappa d'insieme — *cosa* stiamo costruendo e *perche'*, spiegato in modo discorsivo. E' la bussola macro: prima di lavorare su un singolo pezzo, si torna qui per ricordare dove quel pezzo sta nel disegno complessivo (vedi `LEARNING_METHOD.md` Principio 4).
**Rapporto con gli altri documenti:** `CRM_ACCESS_ARCHITECTURE.md` e `TUNNEL_MIGRATION_STRATEGY.md` sono i documenti *tecnici e prescrittivi* (requisiti, tabelle, criteri). Questo documento e' la *spiegazione narrata* degli stessi contenuti, pensata per capire, non per eseguire.

---

## 1. Il problema di partenza, in parole semplici

FitManager non e' un sito web normale dove tutti i dati stanno su un server centrale. E' un programma che **ogni trainer installa sul proprio computer** (un PC o un mini-PC nella sua palestra). Quel computer fa due cose insieme:

1. E' il **gestionale (CRM)** che il trainer usa per gestire i suoi clienti — lo apre dal proprio tablet o telefono mentre e' in palestra.
2. E' anche un **piccolo server** che deve mostrare delle pagine (schede di allenamento, questionari di anamnesi) ai **clienti finali** del trainer, che le aprono da casa loro cliccando un link.

I dati dei clienti (anche dati sanitari, delicatissimi dal punto di vista legale) stanno **solo** su quel computer, mai sui server di AVGV. Questa e' una scelta deliberata: rende tutta la parte legale/GDPR molto piu' semplice, perche' AVGV non tocca mai quei dati.

Da qui nasce un problema tecnico preciso: **come fa il cliente finale, che e' a casa sua su Internet, a raggiungere un programma che gira sul computer del trainer dentro una palestra?**

Il computer del trainer e' dietro il router della palestra. Non ha un indirizzo pubblico su Internet, non e' un sito raggiungibile. E' come una casa senza indirizzo civico: c'e', ma nessuno da fuori sa come arrivarci. E noi NON vogliamo chiedere al trainer di configurare il router, aprire porte, gestire indirizzi IP — sarebbe troppo complicato e il vincolo del progetto e' "zero configurazione per il trainer".

---

## 2. La soluzione: il tunnel e il "centralino"

La soluzione e' un **tunnel**. Invece di aspettare che qualcuno da fuori riesca a entrare nel computer del trainer (difficile, dietro il router), e' **il computer del trainer che apre da solo una connessione verso l'esterno**, verso un punto fisso che controlliamo noi. Quel punto fisso e' il **VPS** (vedi sezione 3). Una volta che questa connessione e' aperta, il traffico dei clienti finali puo' viaggiarci dentro nei due sensi.

Metafora del centralino telefonico:

- Il **VPS** e' un centralino con un numero pubblico noto, sempre acceso, raggiungibile da chiunque.
- Il **computer del trainer** chiama il centralino e dice "sono lo studio di Alessio, tieni aperta la linea con me".
- Quando un **cliente finale** vuole raggiungere lo studio di Alessio, chiama il centralino (il VPS), che gira la chiamata sulla linea gia' aperta verso il computer di Alessio.

Il cliente non sa (e non gli serve sapere) dov'e' fisicamente il computer di Alessio. Parla col centralino, che fa da ponte.

Punto cruciale di tutto il progetto — il **centralino non ascolta le telefonate**. Il traffico che passa nel tunnel e' cifrato in modo tale che il VPS lo instrada senza poterlo leggere ("data-blind", principio P2 dei documenti tecnici). Questo e' sia una scelta di sicurezza sia una scelta legale: se AVGV non puo' leggere i dati sanitari dei clienti, allora dal punto di vista del GDPR non li "tratta", e tutta una serie di obblighi pesanti decadono.

---

## 3. Cos'e' un VPS (il pezzo che stiamo costruendo ora)

**VPS = Virtual Private Server. E' un computer in affitto, sempre acceso, in un data center.**

Spacchettiamo la sigla:

- **Server**: un computer il cui mestiere e' stare acceso e rispondere a richieste che arrivano dalla rete (a differenza del tuo portatile, che usi e spegni). Ha un indirizzo IP pubblico: un "indirizzo civico" su Internet a cui chiunque puo' bussare.
- **Private**: e' tuo (in affitto), isolato dagli altri. Hai i pieni poteri di amministratore, ci installi quello che vuoi.
- **Virtual**: non e' una macchina fisica intera dedicata a te. Nel data center c'e' un server fisico potente che viene diviso in tante macchine virtuali indipendenti; tu ne affitti una. E' il motivo per cui costa ~4.50 euro/mese invece di centinaia: condividi il ferro fisico con altri, ma in compartimenti separati e isolati.

**Perche' ci serve nel nostro disegno:** il VPS e' il "centralino" della sezione 2. Deve esistere un punto sempre acceso, con indirizzo pubblico fisso, verso cui i computer dei trainer aprono il tunnel e a cui i clienti finali si collegano. Il computer del trainer non puo' fare questo ruolo (e' spento di notte, sta dietro il router, cambia indirizzo). Il VPS si'.

**Cosa ci gira sopra, alla fine** (i pezzi che installeremo nei prossimi step):
- un programma server di tunnel (FRP) che accetta le connessioni in arrivo dai computer dei trainer;
- un sistema che, guardando *quale* studio sta cercando il cliente (es. `alessio.fitmanagerstudio.com`), instrada verso il tunnel giusto;
- senza mai decifrare il contenuto (data-blind).

**Dove sta il VPS che stiamo creando:** Hetzner, provider tedesco (UE, quindi comodo per il GDPR), modello CX22 (2 processori virtuali, 4GB RAM, 40GB disco), in un data center in Germania (Falkenstein o Nuremberg).

**Perche' va messo in sicurezza (hardening) prima di tutto:** appena un VPS si accende, avendo un indirizzo pubblico, inizia a ricevere tentativi di intrusione automatici da bot di tutto il mondo, in pochi minuti. Non e' sfortuna, e' il rumore di fondo costante di Internet. Per questo la primissima cosa che facciamo, prima ancora di installarci sopra qualunque cosa, e' chiudere le porte d'ingresso piu' ovvie: accesso solo con chiave crittografica (non password), firewall, blocco automatico di chi insiste. Questo e' il lavoro di "hardening" — task 0.2 della strategia — ed e' il punto da cui siamo partiti con le chiavi SSH.

---

## 4. I tre attori, per non perderli di vista

| Attore | Chi e' | Dove gira | Cosa vede |
|--------|--------|-----------|-----------|
| **AVGV (io/Giacomo)** | operatore della piattaforma | il VPS + il PC di sviluppo | gestisce il centralino; NON vede i dati clinici |
| **Trainer** | cliente che paga (B2B) | il proprio PC/mini-PC in palestra | usa il CRM in locale; i dati dei suoi clienti stanno qui |
| **Cliente finale** | cliente del trainer (B2C) | un browser qualsiasi, da casa | apre solo un link, compila schede; zero registrazione |

Regola d'oro dell'architettura: il **CRM del trainer non e' MAI raggiungibile da Internet** — solo dalla rete locale della palestra. Dal tunnel pubblico passano **solo** le pagine destinate ai clienti finali (`/public/*`). Sono due "piani" separati, e questa separazione e' applicata in piu' punti (rete e codice) cosi' che un cliente finale non possa mai sbirciare nel gestionale del trainer.

---

## 5. La sequenza macro (dove siamo nel viaggio)

```
[Fase 0] Costruire il VPS centralino e metterlo in sicurezza   <-- SIAMO QUI
            |
            v
[Fase 1] Far si' che il programma del trainer apra il tunnel da solo all'avvio
            |
            v
[Fase 2] Cifratura end-to-end (il centralino non legge) + separazione dei due piani
            |
            v
[Fase 3] Onboarding automatico + spegnere il vecchio sistema (Tailscale)
```

Ogni fase poggia sulla precedente. Adesso, in Fase 0, stiamo costruendo le fondamenta: il centralino sicuro. Tutto il "micro" su cui lavoriamo (chiavi SSH, firewall, ecc.) serve a questo macro: **avere un punto pubblico, sempre acceso, sicuro, pronto a fare da ponte.**

---

## 6. Dominio

Dominio unico: **`fitmanagerstudio.com`** (registrato su Cloudflare, 01/06/2026). Usato sia come sito vetrina sia per i sottodomini dei trainer (es. `alessio.fitmanagerstudio.com`). Wildcard DNS `*.fitmanagerstudio.com` punta al VPS edge.

---

## 7. Changelog

| Versione | Data | Modifiche |
|----------|------|-----------|
| 1.0 | 2026-06-02 | Prima emissione. Mappa narrata: problema, tunnel/centralino, cos'e' un VPS, tre attori, sequenza fasi. Nata per colmare la lacuna "macro prima del micro". |
