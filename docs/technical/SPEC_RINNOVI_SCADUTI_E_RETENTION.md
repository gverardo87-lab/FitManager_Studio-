# SPEC — Rinnovi dei contratti scaduti + Retention (funnel anti-perdita silenziosa)

**Versione:** 1.0
**Stato:** Vincolante sui criteri di accettazione — **non vincolante sull'implementazione**
**Owner:** Giacomo Verardo (AVGV Technologies)
**Destinatario:** Claude Code (architetto finale nel codebase)
**Collocazione:** `docs/technical/`
**Data:** 2026-06-20
**Decisione architetturale:** `docs/adr/ADR-015-renewal-retention-funnel.md`
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

## 3. Stati del funnel (derivati dai campi esistenti)

Contratto (derivato, deterministico):
- **attivo** — `chiuso=False`, `data_scadenza > today + soglia in-scadenza`.
- **in scadenza** — `chiuso=False`, `today <= data_scadenza <= today + N` (N attuale = 30). [esiste]
- **scaduto (da rinnovare)** — `chiuso=False`, `data_scadenza < today`, **nessun figlio rinnovo**,
  **non marcato perso**, con valore residuo *o* crediti inutilizzati. [IL BUCO]
- **rinnovato** — esiste un contratto-figlio con `rinnovo_di = id`. Terminale positivo (derivato).
- **perso** — il trainer ha registrato l'esito "non rinnova" (con motivo). Terminale negativo. [NUOVO]

---

## 4. Criterio A — Vista "Scaduti da rinnovare" (anti-perdita silenziosa)

### A.1 Cosa deve essere vero

Un contratto scaduto e non rinnovato non deve mai essere uno stato invisibile. Deve comparire in una
vista esplicita e azionabile, accanto a "in scadenza", finché non viene **rinnovato** o **marcato perso**.

### A.2 Criteri di accettazione

- Esiste una vista/aggregato **"contratti scaduti da rinnovare"** che seleziona i contratti con:
  - aperti (`chiuso == False`), non eliminati (`deleted_at == None`), del trainer;
  - `data_scadenza < today`;
  - **nessun contratto-figlio** (nessun `Contract` con `rinnovo_di = id`, non eliminato) → non già rinnovato;
  - **non marcati "perso"** (vedi §5);
  - con **opportunità residua**: crediti inutilizzati **oppure** residuo economico > 0 (denaro o sedute da non perdere).
- I contratti **già rinnovati** sono esclusi **anche** dalla vista "in scadenza" (correzione del bug
  secondario: oggi un rinnovato può ancora comparire).
- **Aging**: gli scaduti sono ordinati/raggruppati per ritardo (es. 0-30 / 31-90 / 90+ giorni dalla
  scadenza), urgenza decrescente.
- **Invariante "nessuna perdita silenziosa" (vincolante):** nessun contratto aperto, scaduto, con
  opportunità residua, non rinnovato e non marcato perso, può uscire da questa vista. Ne esce solo per
  decisione esplicita (rinnovo o "non rinnova").
- La vista entra nel flusso di `/rinnovi-incassi` come sezione dedicata (oltre a "In scadenza"), con
  CTA "Rinnova" (riusa il flusso di SPEC_RINNOVO) e "Non rinnova".
- **Nessuna migrazione dati**: i contratti scaduti esistenti compaiono appena la vista sa cercarli.

### A.3 Lasciato a Claude Code

Endpoint dedicato vs estensione; forma della query; bucket di aging; innesto UI; naming italiano
("Scaduti da rinnovare", "Da recuperare"…).

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

**Scaduti da rinnovare (A):**
- [ ] Vista contratti `chiuso=False` + `data_scadenza<today` + non rinnovati + non persi + opportunità residua.
- [ ] Già-rinnovati esclusi anche da "in scadenza".
- [ ] Aging per ritardo; integrazione in `/rinnovi-incassi` + solleciti.
- [ ] Invariante: nessuna uscita senza decisione esplicita (rinnovo/perso).
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
