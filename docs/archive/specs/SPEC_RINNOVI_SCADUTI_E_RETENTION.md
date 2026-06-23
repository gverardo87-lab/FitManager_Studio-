# SPEC — Rinnovi dei contratti scaduti + Retention (funnel anti-perdita silenziosa)

**Versione:** 2.0
**Stato:** Vincolante sui criteri di accettazione — **non vincolante sull'implementazione**
**Owner:** Giacomo Verardo (AVGV Technologies)
**Destinatario:** Claude Code (architetto finale nel codebase)
**Collocazione:** `docs/technical/`
**Data:** 2026-06-20

> **Nota di versione 2.0 (2026-06-20):** dall'esame del dato reale (Paola/Merchiori/Scalmato) emerso
> il difetto grave: contratti **scaduti per data ma con sedute prepagate residue** venivano trattati
> come "attivi" o "da recuperare", quando il trainer **deve** ancora quelle sedute. Introdotto lo
> stato **SOSPESO** di prima classe (ciclo a 4 stati §3), l'**ingaggio** = ATTIVO o SOSPESO (§3-bis),
> la worklist dedicata **"Contratti sospesi / sedute da recuperare"** (§4-bis). "Clienti da recuperare"
> ora esclude gli ingaggiati (incl. sospesi). Corretto anche il rappresentante (più recente in
> assoluto, non più recente-aperto). Impatto: l'endpoint `clients-to-recover` e la UI Step 2-5 vanno
> rivisti (escludere sospesi). Vedi ADR-015 emendamento 2.

> **Nota di versione 1.2 (2026-06-20):** durante l'implementazione (Step 2) emerso che il filtro
> "opportunità residua" — ereditato dalla lente contratto — **ri-introduceva la perdita silenziosa di
> clienti**: un cliente che ha completato e pagato tutto (residuo 0, crediti esauriti) e non rinnova
> veniva escluso, pur essendo il miglior win-back. **Rimosso il filtro**: la worklist surface TUTTI i
> lapsed; residuo/crediti = info + priorità. Vedi §A.2.

> **Nota di versione 1.1 (2026-06-20):** rilievo founder — la rilevazione contract-level ("nessun
> figlio `rinnovo_di`") è **fallace**: un cliente può aprire un nuovo contratto NON collegato →
> falso positivo. Corretto a **client-aware**: si recupera un cliente solo se NON ha alcun contratto
> attivo (`chiuso=False AND data_scadenza>=oggi`); unità = **cliente** (conta clienti); rappresentato
> dal contratto scaduto più recente. Vedi §3-bis e §4 riscritti.
**Decisione architetturale:** `docs/adr/ADR-015-renewal-retention-funnel.md`
**Modello di dominio (SSoT):** `FINANCIAL_DOMAIN_MODEL.md` — stati di vita, vocabolario, worklist e
invarianti sono definiti LÌ. Questa spec contiene solo i criteri di accettazione e vi referenzia.
**Spec correlate:** `SPEC_RINNOVO_E_CONTRATTI_DA_PIANIFICARE.md` (flusso di rinnovo + contratti da pianificare)

> **Natura del documento.** Prescrittivo su *cosa deve essere vero*, silenzioso su *come*. I criteri
> di accettazione sono vincolanti; ogni scelta implementativa (forma campo/stato, query, naming UI
> italiano) spetta a Claude Code, che si adatta al codebase reale — **fonte di verità sopra ogni
> assunzione qui**.

---

## 0. Perché esiste questo documento

Oggi i contratti **scaduti** (`data_scadenza < oggi`) **spariscono silenziosamente**: la pagina
`/rinnovi-incassi` e l'alert mostrano solo i contratti **in scadenza futura** (`get_expiring_contracts`,
`dashboard.py:346-347`: `data_scadenza >= today AND <= today+30`). Un contratto che oltrepassa la
scadenza senza essere rinnovato cade fuori dalla finestra e **non compare più da nessuna parte**.
Non esiste alcuno **stato terminale** (`perso`/`non rinnova`): è perdita per *assenza*, non per
decisione. Conseguenza: si perdono **opportunità di rinnovo** (denaro) e **clienti** (churn), in
silenzio — l'opposto di ciò che il prodotto promette.

Il bersaglio: portare la logica al livello dei migliori CRM (renewal pipeline che non sparisce alla
scadenza; segmento *lapsed/win-back*) e **superarli** con due lenti separate e un invariante
deterministico di non-perdita.

---

## 1. Ground-truth (cosa esiste, file:riga)

| Capacità | Dove | Stato |
|---|---|---|
| Contratti in scadenza (futuro) | `dashboard.py:346-347` (endpoint), `:717-718` (alert) | ✅ ma **solo finestra futura** (`>= today AND <= +30`) |
| Stato terminale "perso/non rinnova" | — | ❌ **non esiste** |
| Esclusione contratti già rinnovati dalla finestra | `get_expiring_contracts` | ❌ non esclude (no check sul figlio `rinnovo_di`) |
| Catena rinnovo (figlio via `rinnovo_di`) | `Contract.rinnovo_di`, `get_contract` | ✅ esiste |
| `chiuso` vs scaduto | `Contract.chiuso` (saldato+crediti usati) ≠ `data_scadenza<oggi` | ✅ concetti distinti |
| Alert clienti inattivi | `dashboard.py` `inactive_clients` (>14gg senza eventi) | ✅ ma **basato su attività/eventi**, non sui contratti |
| Win-back / WhatsApp | sistema comunicazioni (15 template) | ✅ riusabile |

**Conseguenza:** serve (a) far emergere gli scaduti non rinnovati, (b) uno **stato terminale
esplicito** con motivo, (c) escludere i già-rinnovati. La lente cliente è progettata qui ma differita.

---

## 2. Le due lenti (fondamento concettuale)

Distinzione vincolante: *contratti O clienti, non necessariamente entrambi*.

- **Lente contratto — opportunità di rinnovo.** Per singolo contratto. Ciclo:
  `attivo → in scadenza → scaduto (non rinnovato) → rinnovato | perso`.
- **Lente cliente — retention/churn.** Rollup sui contratti del cliente:
  `attivo → a rischio → lapsed (nessun contratto attivo) → perso`.

Non coincidono: un cliente con un contratto scaduto **e** uno attivo è opportunità di rinnovo
*contratto* ma non churn *cliente*. Confonderle è l'errore tipico dei gestionali; qui restano
**separate e collegate**.

---

## 3. Ciclo di vita del contratto — 4 stati derivati (v2.0)

`chiuso` (bool) da solo è insufficiente: un contratto **scaduto per data** con `chiuso=False` viene
oggi contato come "attivo", e un pacchetto con **sedute prepagate non usate** non si chiude mai
(l'auto-close richiede SALDATO **E** crediti esauriti). Servono 4 stati **derivati**, deterministici:

| Stato | Definizione | Significato |
|---|---|---|
| **ATTIVO** | `chiuso=False` AND (`data_scadenza` NULL OR `>= today`) | copertura in corso |
| **SOSPESO** | `chiuso=False` AND `data_scadenza < today` AND `crediti_residui > 0` | scaduto per data ma **ha sedute prepagate da erogare** — gli DEVI sessioni |
| **ESAURITO** | `chiuso=False` AND `data_scadenza < today` AND `crediti_residui == 0` | pacchetto davvero concluso (sedute finite) |
| **CHIUSO** | `chiuso=True` | terminato (saldato + crediti usati, o chiuso a mano) |

> `crediti_residui = crediti_totali − crediti_usati` (eventi PT non cancellati). Esempi reali
> (2026-06-20): Paola 18/20 → SOSPESO (2 sedute); Merchiori 5/10 → SOSPESO (5); Scalmato 7/10 →
> SOSPESO (3); Dalila 4/4 → ESAURITO (+ residuo 20€).

**Esito terminale "perso"** (`esito_rinnovo_motivo` valorizzato): decisione esplicita "non rinnova",
ortogonale agli stati sopra; esce dalla worklist win-back, resta in storico.

### 3-bis. Ingaggio cliente e rilevazione client-aware (v2.0)

**Un cliente è "ingaggiato" se ha ≥1 contratto ATTIVO _o_ SOSPESO.** Il SOSPESO conta come ingaggio:
il cliente ha sedute prepagate da usare → **non è perso**, gli devi sessioni. Quindi:

- **"Cliente da recuperare" (win-back)** = cliente **NON ingaggiato** (nessun ATTIVO, nessun SOSPESO)
  con ≥1 contratto scaduto, rappresentante non marcato perso. Sussume rinnovo-figlio, nuovo-contratto-
  non-collegato **e** sospeso → niente falsi positivi (esclude Paola/Merchiori/Scalmato).
- **Rappresentante** del cliente = **contratto più recente in assoluto** (incl. CHIUSO), non il più
  recente *aperto*. (Bug v1.x: per Dalila mostrava c25 apr-aperto invece di c29 mag-chiuso = vero
  punto di interruzione.)
- **Unità = cliente** (1 riga, conta clienti).
- **SOSPESO ha la sua worklist** (§4-bis): non è win-back, è "sedute da recuperare".
- Il denaro residuo di uno scaduto vive nelle worklist denaro (aging/da-incassare), separato.

---

## 4. Criterio A — Vista "Clienti da recuperare" (anti-perdita silenziosa, client-aware)

### A.1 Cosa deve essere vero

Un cliente la cui copertura è **lapsed** (contratto scaduto, nessun contratto attivo) non deve mai
essere uno stato invisibile. Deve comparire in una vista esplicita e azionabile, accanto a "in
scadenza", finché non viene **recuperato** (nuovo contratto attivo) o **marcato perso**.

### A.2 Criteri di accettazione

- Esiste una vista/aggregato **"clienti da recuperare"** — **unità = cliente** (1 riga/cliente,
  conteggio per **clienti**). Un cliente vi compare se **tutte** valgono:
  - ha **almeno un contratto scaduto** (`chiuso=False`, `deleted_at=None`, `data_scadenza < today`);
  - **NON è ingaggiato**: nessun contratto **ATTIVO** *né* **SOSPESO** (§3). Cioè: nessun contratto
    aperto con `data_scadenza >= today` (attivo) E nessun contratto aperto scaduto con `crediti_residui > 0`
    (sospeso). Il sospeso conta come ingaggio (gli devi sedute) → il cliente non è perso (v2.0);
  - il suo **contratto rappresentante** (più recente in assoluto, §3-bis) **non è marcato "perso"** (§5).
- **NESSUN filtro "opportunità residua"** (v1.2). Ogni cliente non-ingaggiato è un win-back, anche chi
  ha completato e pagato tutto. `residuo`/`crediti_residui` = info + priorità, non filtro.
- Rappresentante = **contratto più recente in assoluto** (incl. CHIUSO); `giorni_ritardo` calcolato
  sul suo `data_scadenza` (se scaduto).
- **Aging**: ordinati per ritardo (0-30 / 31-90 / 90+), urgenza decrescente.
- **Invariante "nessuna perdita silenziosa" (vincolante):** nessun cliente non-ingaggiato con ≥1
  scaduto, non marcato perso, può uscire da questa vista senza una **decisione umana esplicita**.
- **Correzione collaterale**: i contratti già rinnovati (figlio attivo) esclusi anche da "in scadenza".
- La vista entra in `/rinnovi-incassi`, CTA "Rinnova" (riusa SPEC_RINNOVO) + "Non rinnova".
- **Nessuna migrazione dati**.

### A.3 Lasciato a Claude Code

Endpoint dedicato vs estensione; forma della query (clienti con scaduti `EXCEPT` clienti ingaggiati
= con attivi-o-sospesi); bucket di aging; innesto UI; naming italiano.

---

## 4-bis. Criterio A2 — Vista "Contratti sospesi" (sedute da recuperare) [v2.0]

### A2.1 Cosa deve essere vero

Un contratto **SOSPESO** (scaduto per data, con sedute prepagate residue) rappresenta **sessioni che
il trainer DEVE al cliente**. Non è win-back e non è denaro da incassare: sono **sedute pagate non
ancora erogate**, a rischio di andare perse silenziosamente. Devono comparire in una vista azionabile.

### A2.2 Criteri di accettazione

- Esiste una vista/aggregato **"contratti sospesi"**: contratti `chiuso=False`, `deleted_at=None`,
  `data_scadenza < today`, `crediti_residui > 0`. **Unità = contratto** (ogni contratto sospeso ha le
  sue sedute e la sua data).
- Mostra: cliente, pacchetto, `data_scadenza`, `giorni_ritardo`, **crediti residui** (sedute da erogare),
  eventuale residuo economico.
- **Azioni** (forma a Claude Code, concetto vincolante):
  - **Estendi/riattiva** — nuova `data_scadenza` (il contratto torna ATTIVO); riusa `update_contract`.
  - **Sedute decadute** — chiusura esplicita (le sedute si considerano perse per policy); decisione
    umana, non silenziosa. Reversibile/auditata.
- **Invariante**: un contratto SOSPESO non esce dalla vista senza decisione esplicita (estendi o decadi).
- I contratti sospesi **non** compaiono in "clienti da recuperare" (il cliente è ingaggiato, §3-bis).

### A2.3 Lasciato a Claude Code

Endpoint/innesto UI (sezione in `/rinnovi-incassi` o tab); forma azioni estendi/decadi; naming
("Contratti sospesi", "Sedute da recuperare", "Da riattivare").

---

## 5. Criterio B — Esito "Non rinnova" con motivo (stato terminale)

### B.1 Cosa deve essere vero

Il trainer deve poter chiudere esplicitamente l'opportunità di rinnovo di un contratto scaduto,
registrando un **motivo**. Il contratto esce dalla worklist ma **resta nello storico** (mai cancellato).

### B.2 Criteri di accettazione

- Esiste un'azione **"Non rinnova"** su un contratto scaduto che registra un **esito terminale +
  motivo** (es. prezzo, trasferito, infortunio, insoddisfatto, altro). La forma (campo nullable su
  `Contract` / tabella outcome) è a Claude Code; il concetto è vincolante.
- Dopo "Non rinnova", il contratto **esce** dalla vista "scaduti da rinnovare" ma resta consultabile.
- L'azione è **reversibile** (ri-aprire l'opportunità) o almeno non distruttiva (nessun hard delete).
- Sicurezza: ownership via `trainer_id` (pattern bouncer, 404 mai 403); audit trail su CREATE/UPDATE.
- Il motivo è **dato strutturato** (set di motivi + eventuale testo libero), così da abilitare in
  futuro analytics di churn.

### B.3 Lasciato a Claude Code

Forma dello stato (campo vs tabella), set dei motivi, reversibilità, UI dell'azione.

---

## 6. Criterio C — Retention cliente (PROGETTATO, differito a iterazione successiva)

> **Fuori da questa iterazione (decisione 2026-06-20)**, ma specificato ora perché la lente contratto
> deve incastrarsi senza riaperture.

- Stato cliente derivato (rollup sui contratti): **attivo** (≥1 contratto attivo) · **a rischio**
  (ultimo attivo in scadenza) · **lapsed** (nessun contratto attivo, ultimo scaduto entro finestra
  win-back) · **perso** (lapsed oltre finestra / tutti i contratti marcati persi).
- Vista/segmento **retention** con worklist di clienti lapsed → re-engagement (WhatsApp esistente).
- **Confine con `inactive_clients`**: quell'alert è *attività-based* (>14gg senza eventi); la retention
  qui è *contratto-based* (nessun contratto attivo). Sono segnali complementari, da non fondere.

---

## 7. Confini con l'esistente

- **"In scadenza"** (futuro) e **"Scaduti da rinnovare"** (passato) sono due sezioni distinte e
  complementari della stessa pagina — non unificare i numeri.
- **"Contratti da pianificare"** (SPEC_RINNOVO §B): contratti aperti senza rate — asse diverso
  (denaro non messo a scadenza), può sovrapporsi a uno scaduto ma è un'altra worklist.
- **Flusso di rinnovo** (SPEC_RINNOVO §A): la CTA "Rinnova" sugli scaduti riusa quel flusso invariato
  (eredità dati sequenziale, navigazione guidata al piano rate).

---

## 8. Checklist di accettazione (sintesi verificabile)

**Ciclo di vita (v2.0):**
- [ ] 4 stati derivati: ATTIVO / SOSPESO (scaduto+crediti>0) / ESAURITO (scaduto+crediti=0) / CHIUSO.
- [ ] Ingaggio cliente = ha ATTIVO **o** SOSPESO.

**Clienti da recuperare (A) — client-aware + v2.0:**
- [ ] Vista per **cliente** (conta clienti): ha scaduto + **NON ingaggiato** (zero ATTIVI e zero SOSPESI) + rappresentante non perso. Nessun filtro opportunità.
- [ ] Rappresentante = contratto **più recente in assoluto** (incl. chiuso); `giorni_ritardo` + aging.
- [ ] Sospesi/già-rinnovati/continuati esclusi; fix esclusione su "in scadenza".
- [ ] Invariante: nessun cliente non-ingaggiato esce senza decisione esplicita (recupero/perso).

**Contratti sospesi (A2) — v2.0:**
- [ ] Vista per **contratto**: aperto + scaduto + crediti residui > 0; mostra sedute residue + ritardo.
- [ ] Azioni estendi/riattiva (nuova data) e sedute-decadute (chiusura esplicita); non distruttive.
- [ ] Invariante: nessun sospeso esce senza decisione; non compare in "da recuperare".
- [ ] Zero migrazione.

**Esito "Non rinnova" (B):**
- [ ] Azione che registra esito terminale + motivo strutturato; contratto esce dalla worklist, resta in storico.
- [ ] Non distruttivo / reversibile; ownership 404-mai-403 + audit.

**Retention cliente (C):**
- [ ] NON in questa iterazione (documentato); stati cliente progettati; confine con `inactive_clients` chiarito.

---

## 9. Bridge rule

Output non banale di Claude Code (forma dello stato "perso", query scaduti, aging, innesto UI) →
learning capture in chat + riflesso in `BUILD_LOG.md`. Decisione architetturale in `ADR-015`.
