# LEARNING_METHOD.md

**Progetto:** FitManager
**Versione:** 1.0
**Data:** 2026-06-02
**Stato:** Attivo
**Ambito:** Metodo di apprendimento continuo integrato nello sviluppo
**Obiettivo:** Diventare un programmatore esperto e consapevole padroneggiando il proprio software, non accumulando codice funzionante ma non compreso.

---

## 0. Perche' questo documento esiste

Imparare "strada facendo" sotto pressione di consegna ha una trappola precisa: si ottiene che la cosa *funzioni*, si prova sollievo, si va avanti. Il comando gira -> spunta -> task successivo. Mesi dopo qualcosa si rompe, si riapre quel pezzo, e si scopre di non aver mai capito *perche'* funzionava -- si era solo copiato qualcosa che girava.

Questo e' il "non padroneggiare il proprio software". Questo metodo costruisce un attrito deliberato contro quella trappola, senza rallentare tanto da far abbandonare la didattica quando la scadenza preme.

La distinzione tra un programmatore "qualunque" e uno "consapevole" non sta nel risultato apparente (entrambi fanno girare il server) ma nella capacita' di rispondere a: *perche' questo e non altro? cosa sto effettivamente facendo? come mi accorgo se ho sbagliato?*

---

## 1. I tre principi

### Principio 1 — "Lo spiego o non l'ho capito"

Per ogni concetto, prima di considerarlo chiuso, devo saperlo riformulare **con parole mie, a fonte chiusa**. Non riscrivere copiando un po' diverso: chiudere la pagina e spiegarlo da zero. Se mi blocco, ho trovato il buco di comprensione.

E' il filtro piu' potente che esista per la profondita' reale, ed e' gratis.

### Principio 2 — Tre livelli di "perche'"

Per ogni cosa, fermarsi a tre domande in cascata:

1. **Cosa fa?** — il fatto osservabile (es. "il comando disabilita il login di root via SSH")
2. **Perche' lo voglio?** — la motivazione (es. "root e' un bersaglio noto, ogni bot lo attacca per primo")
3. **Perche' funziona cosi' a livello sottostante?** — il meccanismo (es. "cos'e' root nel modello di permessi Unix, cos'e' un demone SSH, cosa legge quando decide se accettarmi")

Il **livello 3** e' quello che quasi tutti saltano ed e' quello che separa "so configurare un server" da "capisco i sistemi". E' anche quello che rende la conoscenza **trasferibile**: i fondamentali sotto un concetto sono gli stessi sotto mille altri.

### Principio 3 — Il failure mode e' parte della comprensione

Per ogni concetto: **cosa succede se sbaglio, e come me ne accorgo.** Capire un sistema *e'* capire come si rompe. Chi conosce solo il percorso felice non capisce il sistema: conosce una ricetta.

### Principio 4 — Il macro prima del micro

**Senza conoscere il macro e' inutile sapere il micro.** Prima di studiare un componente (un comando, un file di config, un tool), devo sapere: cos'e' il sistema piu' grande di cui fa parte, e che ruolo ci gioca dentro. Un dettaglio appreso senza la mappa d'insieme e' un fatto isolato che non si ancora a niente e si dimentica; lo stesso dettaglio appreso *dentro* la sua funzione nel sistema diventa comprensione che resta.

Operativamente, ogni nuovo blocco di lavoro parte da una **vista d'insieme** (cosa stiamo costruendo, quali pezzi, come si parlano, perche' in quest'ordine) prima di scendere nel singolo pezzo. Se mi accorgo di star imparando un micro-dettaglio senza avere chiaro il macro che lo contiene, mi fermo e risalgo. Questo principio nasce da un errore reale (02/06/2026: generata una chiave SSH per un VPS prima di aver spiegato cos'e' un VPS e cosa stiamo costruendo) — l'errore e' diventato regola.

Esiste un documento dedicato alla mappa d'insieme: `ARCHITECTURE_OVERVIEW.md` — la "strategia spiegata", da consultare e tenere aggiornata come bussola macro.

---

## 2. Calibrazione della profondita'

Profondita' massima su *tutto* e' insostenibile e porta ad abbandonare. Si calibra cosi':

- **Livello 3 pieno** solo sui **fondamentali trasversali** — quelli che si ritrovano ovunque: modello permessi Unix, come funziona TLS, cos'e' un processo, DNS, modello client-server, crittografia asimmetrica.
- **Livello 1-2** per i **dettagli specifici di un tool** — la sintassi esatta di un blocco Caddy, le opzioni di un file `frpc.toml`. Quelli si ri-cercano comunque e non vale la pena interiorizzarli.

Sapere *dove* mettere lo sforzo e' esso stesso una competenza.

---

## 3. Il flusso operativo

Separazione netta tra **cattura** (veloce, durante il lavoro) ed **elaborazione** (lenta, a mente fredda). E' questo che impedisce alla didattica di sabotare la consegna.

1. **Cattura grezza, sul momento.** Quando incontro qualcosa di nuovo durante lo sviluppo o la configurazione: una riga, il comando, "capire meglio". Non interrompere il flusso. Cinque secondi.
2. **Elaborazione, a fine sessione.** Riprendo le catture grezze e le espando col template (S4). *Questo* e' il momento di studio vero, quando trasformo "ha funzionato" in "ho capito".
3. **Ripasso, una volta a settimana.** Rileggo un file vecchio e provo a spiegare un concetto ad alta voce. Quello che non riesco piu' a spiegare torna in cima alle domande aperte.

---

## 4. Il template del singolo concetto

```markdown
## [Nome concetto] — gg/mm/aaaa
**Contesto:** cosa stavo facendo quando l'ho incontrato

**Livello 1 — Cosa fa:** (parole mie, fonte chiusa)
**Livello 2 — Perche' lo voglio:**
**Livello 3 — Perche' funziona cosi' sotto:** <- il livello che non salto sui fondamentali

**Comando/config reale:**
\`\`\`
snippet dal mio setup
\`\`\`

**Failure mode:** se sbaglio X -> succede Y -> me ne accorgo da Z
**Domande aperte:** [ ] da chiudere
```

---

## 5. Il ponte con Claude Code

Lo sviluppo segue una separazione di ruoli deliberata:

- **Claude (chat)** — didattica, brainstorming, decisioni a contesto ampio. Il registro del *capire e decidere*.
- **Claude Code (VS Code)** — implementazione con visibilita' sul codebase reale. Il registro del *fare*.

**Rischio specifico da sorvegliare:** delegare a Claude Code anche la *comprensione*, non solo la scrittura. Claude Code e' cosi' efficace nel far funzionare le cose che e' facile accettare codice che gira senza attraversare il "perche'". Il software cresce, la comprensione no -> debito di comprensione silenzioso.

**Regola del ponte:** quando Claude Code produce qualcosa di non banale, quel pezzo diventa una **cattura** per il file di learning. Non va capito nel momento (rallenterebbe), ma annotato grezzo e digerito a mente fredda.

**Micro-disciplina:** prima di accettare codice che non capisco del tutto, mi chiedo "saprei spiegare cosa fa questa riga a qualcuno?". Se no -> cattura.

---

## 6. Struttura dei file di learning

Cartella `/learning/` parallela a `/legal/`, file per dominio tecnico (non per giornata):

| File | Ambito |
|------|--------|
| `LEARNING_NETWORKING.md` | DNS, reverse proxy, TLS, SNI, tunnel, NAT |
| `LEARNING_LINUX_SYSADMIN.md` | utenti, permessi, systemd, SSH, processi |
| `LEARNING_SECURITY.md` | firewall, fail2ban, gestione segreti, token, threat model |
| `LEARNING_DEPLOYMENT.md` | build, CI/CD, logging, monitoring |
| `LEARNING_APP_ARCHITECTURE.md` | FastAPI, Next.js, middleware, auth nel codebase |

---

## 7. Avvertenza onesta

Claude (chat e Code) e' utile per accelerare la comprensione, ma il salto a programmatore esperto lo fa la pratica diretta e il confronto con altri umani: community, code review, qualcuno piu' avanti che guarda il proprio codice. L'apprendimento non va costruito solo sul dialogo con un'AI: l'AI puo' confermare un errore quanto correggerlo, e non sostituisce il riscontro di un sistema reale in produzione ne' l'occhio di un mentore umano.

---

## 8. Regola di cattura automatica (Claude Code)

**Problema:** se la cattura di concetti nuovi dipende dal founder che si ricorda di chiederla, fallira'. Serve un trigger automatico lato agente.

**Regola per Claude Code (attiva in ogni conversazione):**

Quando durante una sessione di lavoro emergono **concetti tecnici nuovi o approfondimenti non banali** (casi edge, pattern architetturali, failure mode, meccanismi sotto la superficie), Claude Code:

1. **Identifica** il materiale didattico nella conversazione — tutto cio' che soddisfa almeno uno dei 3 livelli del template (sez. 4).
2. **Propone** l'aggiornamento al file `LEARNING_*.md` appropriato (per dominio, non per sessione). Se il dominio non ha ancora un file, ne propone la creazione.
3. **Scrive** il contenuto seguendo il template a 3 livelli, includendo failure mode e domande aperte.
4. **Aggiorna** il README se necessario (nuovo file aggiunto).

**Quando NON scatta:**
- Dettagli di implementazione pura (sintassi, API call, config) che non contengono concetti trasferibili.
- Informazioni gia' presenti nei file learning esistenti.
- Sessioni di puro bugfix dove non emerge niente di nuovo.

**Il trigger e' intrinseco alla conversazione, non alla richiesta.** Se il founder e Claude Code discutono di health check end-to-end e poi passano a implementarlo, il concetto va catturato anche se nessuno ha detto "scrivi nel learning". La cattura e' parte del workflow, non un'azione separata.

---

## 9. Changelog

| Versione | Data | Modifiche |
|----------|------|-----------|
| 1.0 | 2026-06-02 | Prima emissione. Metodo a tre principi, flusso cattura/elaborazione, ponte con Claude Code. |
| 1.1 | 2026-06-05 | Aggiunta sez. 8: regola di cattura automatica Claude Code. Il trigger e' intrinseco alla conversazione, non alla richiesta. |
