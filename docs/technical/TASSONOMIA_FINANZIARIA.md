# TASSONOMIA FINANZIARIA — vocabolario condiviso

**Versione:** 1.1
**Stato:** Vincolante sui concetti e le formule — **non vincolante su naming UI e implementazione**
**Owner:** Giacomo Verardo (AVGV Technologies)
**Destinatario:** Claude Code (architetto finale nel codebase)
**Collocazione:** `docs/technical/`
**Data:** 2026-06-19
**Referenziato da:** `SPEC_RINNOVO_E_CONTRATTI_DA_PIANIFICARE.md`, `SPEC_GESTIONE_FINANZIARIA_TEMPORALE.md`

> **Nota di versione 1.1 (2026-06-19):** secondo giro di rilievi Claude Code. (1) "Rate non saldate"
> nella formula "Da pianificare" = `stato ∈ {PENDENTE, PARZIALE}`, non solo PENDENTE (§1 Asse 3).
> (2) "Incassi da contratti" / "Altri incassi" da definire come partizione complementare su
> `id_contratto`, esaustiva per costruzione (§2).

> **Perché esiste.** Entrambe le spec finanziarie introducono nozioni di scomposizione del fatturato
> e di stato di pianificazione. Senza un vocabolario unico, l'UI finanziaria nasce incoerente
> (stessi concetti con nomi diversi). Questo documento fissa **i concetti e le formule** una volta
> sola. Il **naming UI in italiano** resta giudizio di Claude Code e di Giacomo (regola 9 CLAUDE.md);
> qui si fissa il *significato*, non l'etichetta a schermo.

---

## 0. Principio di posizionamento (leggere prima di tutto)

Il differenziatore competitivo che queste spec perseguono è la **gestione economico-finanziaria** —
spazio scoperto dai leader anglosassoni (Trainerize, TrueCoach…), nati attorno al training con la
parte finanziaria come bolt-on (integrano un gateway di pagamento e finisce lì).

Il bisogno reale del libero professionista italiano è **sapere quanto è davvero entrato**
(liquidità reale, gestionale), distinto da **quanto ha documentato fiscalmente**. Questo bisogno è
**legittimo e universale**, e il software lo serve come fa ogni gestionale serio: offrendo
**visibilità sul cash flow**, tenuta **distinta** dalla posizione fiscale.

**Confine non negoziabile.** Il software espone **cash management neutro** (quanto entra, datato e
categorizzato). NON nomina, NON struttura, NON agevola alcuna nozione di reddito "non dichiarato".
La finalità progettuale documentata è *visibilità sulla liquidità*, non occultamento. Questa
distinzione non è cosmetica: separa uno strumento neutro (l'utente lo usa come crede, come un foglio
di calcolo) da uno strumento con finalità di evasione (che esporrebbe AVGV). Coerente con l'intero
impianto di compliance di AVGV (P2 data-blind, postura GDPR): non si introduce nulla che sposti
AVGV da "fornitore di gestionale neutro" ad altro.

> Nota: questa è una linea di prodotto e di rischio, non un parere legale/fiscale. Decisioni
> definitive su questo asse vanno validate con un professionista tributarista italiano.

---

## 1. I tre assi (cinque nozioni)

### Asse 1 — Liquidità reale (cassa, gestionale) — PRIMARIO

Il quadro di cosa è **davvero entrato**, datato per incasso reale (`CashMovement.data_effettiva`).

| Nozione | Definizione operativa | Origine dati |
|---|---|---|
| **Incassi da contratti** | ENTRATA legate a contratto | `CashMovement` con `categoria` ∈ {`ACCONTO_CONTRATTO`, `PAGAMENTO_RATA`} |
| **Altri incassi** | ENTRATA fuori contratto (sessioni singole, extra) | `CashMovement` ENTRATA con `id_contratto IS NULL`, **escluse le rettifiche** (vedi §2) |
| **Cash flow reale** | Tutto ciò che entra | Incassi da contratti + Altri incassi |

- **"Incassi da contratti"** è la spina dorsale: riconcilia con i contratti, è la base di tutte le
  viste temporali e di composizione.
- **"Altri incassi"** è mostrato come **riga/categoria separata**, mai fuso negli incassi da
  contratti (così la parte contrattuale resta riconciliabile).
- **"Cash flow reale"** è l'informazione gestionale che i competitor non danno.

### Asse 2 — Posizione commerciale (competenza) — SECONDARIO

Quanto **venduto** (firmato) in un periodo, indipendentemente dall'incasso.

| Nozione | Definizione operativa | Origine dati |
|---|---|---|
| **Venduto** | Valore dei contratti firmati nel periodo | `Contract.prezzo_totale` aggregato su `Contract.data_vendita` |

Misura l'andamento delle vendite. **Mai sommato alla cassa** (assi distinti). Lo *scarto*
venduto − incassato = denaro venduto ma non ancora entrato (credito vivo dell'attività).

### Asse 3 — Stato di pianificazione

Quanto, di ciò che è dovuto, **non è ancora stato messo a rata**.

| Nozione | Formula | Note |
|---|---|---|
| **Da pianificare** | `(prezzo_totale − totale_versato) − somma(residui rate NON SALDATE)` | Per contratti a **zero rate** collassa sul **residuo pieno** (`prezzo − versato`) |

> **Formula corretta (rilievo Claude Code 2026-06-19).** NON usare "Booked − Billed" letterale
> (`prezzo_totale − rate pendenti`): includerebbe acconti e rate **già saldate**, contando come "da
> pianificare" denaro già incassato. La formula sul **residuo** è coerente con il `residuo` già
> calcolato in `_to_response_with_rates` e con il criterio §B.3 della spec rinnovo.

> **"Rate non saldate" = `stato ∈ {PENDENTE, PARZIALE}` (rilievo Claude Code 2026-06-19, v1.1).**
> NON solo `stato == "PENDENTE"`. Una rata **PARZIALE** ha un residuo positivo (`importo_previsto −
> importo_saldato`) di denaro già messo a scadenza: va sottratto, altrimenti rientra erroneamente in
> "Da pianificare". È lo stesso predicato usato dall'aging report
> (`Rate.stato.in_(["PENDENTE", "PARZIALE"])`). Con questa lettura la formula riconcilia in tutti i
> casi e coincide con `importo_disallineamento` per i contratti parzialmente pianificati.

---

## 2. Esclusioni obbligatorie dalla cassa (rilievo Claude Code 2026-06-19)

Il libro mastro ENTRATA contiene movimenti che **NON sono fatturato** e vanno **esclusi** dagli
aggregati di incassato, altrimenti il "fatturato per cassa" sovrastima:

- **`STORNO_SPESA_FISSA`** (e ogni categoria di **rettifica/storno**): è una correzione di un'uscita,
  non un ricavo. Escludere.
- Eventuali altre categorie di sistema non-ricavo presenti nel mastro.

**Conseguenza per gli aggregati temporali:** l'incassato per periodo si costruisce sulle categorie
**contrattuali** (`ACCONTO_CONTRATTO` + `PAGAMENTO_RATA`) per la spina dorsale riconciliabile, più
"Altri incassi" come riga separata (ENTRATA fuori contratto, **al netto degli storni**). Mai un
generico `sum(ENTRATA)`.

> **Robustezza dei bucket (rilievo Claude Code 2026-06-19, v1.1).** "Incassi da contratti" e "Altri
> incassi" vanno definiti come **partizione complementare sullo stesso predicato** — presenza di
> `id_contratto` (valorizzato = contratti / `NULL` = altri), **poi** escludendo gli storni — non con
> predicati eterogenei (whitelist di categoria da un lato, `id_contratto IS NULL` dall'altro). Oggi i
> due criteri combaciano, ma una futura ENTRATA con `id_contratto` valorizzato e categoria fuori
> whitelist cadrebbe in **nessuno** dei due bucket e sparirebbe dal "cash flow reale". Definirli come
> partizione li rende **esaustivi per costruzione**. (Verificato: `STORNO_SPESA_FISSA` ha
> `id_contratto = NULL` — è legato a `id_spesa_ricorrente` — quindi l'esclusione storni sugli "Altri
> incassi" lo intercetta correttamente.)

---

## 3. Riconciliazione — cosa torna con cosa (rilievo Claude Code 2026-06-19)

Attenzione a non assumere riconciliazioni che il codice non garantisce:

- `kpi_incassato` = `sum(Contract.totale_versato)` sui contratti — **non** è una somma del libro
  mastro. Quindi la **somma "Incassi da contratti" per periodo** riconcilia con la logica dei
  contratti, ma il **cash flow reale totale** (che include "Altri incassi") **non** riconcilia con
  `kpi_incassato` — ed è corretto così: sono nozioni diverse.
- La vista primaria "fatturato dai contratti" è quella riconciliabile e pulita; "Altri incassi" è
  esplicitamente fuori da quella riconciliazione, per scelta.

---

## 4. Conformità — regime forfettario

Tutte le nozioni qui sono **gestionali**, non *revenue recognition* GAAP. AVGV opera in
**forfettario per cassa**. La nozione "Venduto" (competenza) è un **indicatore commerciale**, non
una posta contabile di bilancio (no *deferred revenue*). Il numero esposto come incassato deve
restare coerente con il **principio di cassa**.

---

## 5. Mappa naming (significato → etichetta UI, da decidere)

Claude Code e Giacomo fissano le etichette italiane. Il vincolo è che **lo stesso concetto usi la
stessa etichetta in entrambe le spec**. Esempi indicativi (NON prescrittivi):

| Concetto (questo doc) | Possibile etichetta UI (da decidere) |
|---|---|
| Incassi da contratti | "Incassato (contratti)" |
| Altri incassi | "Altri incassi" |
| Cash flow reale | "Liquidità reale" / "Entrate totali" |
| Venduto (competenza) | "Venduto" / "Contratti firmati" |
| Da pianificare | "Da pianificare" / "Da cadenzare" |

---

## 6. Bridge rule

Quando Claude Code implementa scelte non banali ancorate a questa tassonomia (forma degli aggregati,
gestione delle esclusioni, naming definitivo), la decisione va ricondotta a una *learning capture*
in chat e — se vincolante — riflessa in `BUILD_LOG.md`.
