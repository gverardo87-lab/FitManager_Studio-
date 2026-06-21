# TASSONOMIA FINANZIARIA — vocabolario condiviso

**Versione:** 1.2
**Stato:** Vincolante sui concetti e le formule — **non vincolante su naming UI e implementazione**
**Owner:** Giacomo Verardo (AVGV Technologies)
**Destinatario:** Claude Code (architetto finale nel codebase)
**Collocazione:** `docs/technical/`
**Data:** 2026-06-21
**Referenziato da:** `SPEC_RINNOVO_E_CONTRATTI_DA_PIANIFICARE.md`, `SPEC_GESTIONE_FINANZIARIA_TEMPORALE.md`
**Modello di dominio (SSoT):** `FINANCIAL_DOMAIN_MODEL.md` (§8 referenzia questo doc per l'asse cassa/competenza; §3.1/§7-G7 introducono il rimborso da terminazione che questo doc classifica).

> **Nota di versione 1.2 (2026-06-21, rimborso da terminazione anticipata):** il modello (FDM v1.3 §3.1)
> introduce un movimento finora **assente**: il **rimborso** al cliente da terminazione anticipata —
> una **USCITA legata a contratto** (`id_contratto` valorizzato). Modifiche: (1) **§1 Asse 1** — gli
> "Incassi da contratti" diventano **al netto dei rimborsi**; la cassa contrattuale è ora
> **bidirezionale**. (2) **§2** — il predicato "movimento contrattuale" va reso **esplicito e
> bidirezionale** (entrata: `ACCONTO`/`RATA`; uscita: `RIMBORSO_CONTRATTO`); estende la previsione
> della v1.1 (che già aveva intuito il buco, ma solo sul lato ENTRATA). (3) **§7 NEW** — categoria
> `RIMBORSO_CONTRATTO`, sua natura di **contra-ricavo** (NON costo operativo), e le **9 query** da
> allineare perché un rimborso non cada negli aggregati di uscite-variabili. La **policy** del rimborso
> (pro-sedute, prezzo seduta, recesso IT) è **DECISIONE APERTA** (vedi FDM §3.1).

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

> **v1.2 — il rimborso non sposta il confine.** Un rimborso è un **evento di cassa reale** (denaro che
> esce davvero verso il cliente, datato): è cash management neutro come un incasso, nella direzione
> opposta. Non introduce nozioni fiscali; riduce il **netto incassato** del contratto nel periodo in
> cui avviene.

> Nota: questa è una linea di prodotto e di rischio, non un parere legale/fiscale. Decisioni
> definitive su questo asse vanno validate con un professionista tributarista italiano.

---

## 1. I tre assi (cinque nozioni)

### Asse 1 — Liquidità reale (cassa, gestionale) — PRIMARIO

Il quadro di cosa è **davvero entrato** (e, da v1.2, di cosa è **uscito verso il cliente**), datato per
movimento reale (`CashMovement.data_effettiva`).

| Nozione | Definizione operativa | Origine dati |
|---|---|---|
| **Incassi da contratti (lordi)** | ENTRATA legate a contratto | `CashMovement` ENTRATA con `categoria` ∈ {`ACCONTO_CONTRATTO`, `PAGAMENTO_RATA`} |
| **Rimborsi da contratti** *(v1.2)* | USCITA legate a contratto (restituzioni) | `CashMovement` USCITA con `categoria` = `RIMBORSO_CONTRATTO` (`id_contratto` valorizzato) |
| **Incassi netti da contratti** *(v1.2)* | Spina dorsale riconciliabile, al netto delle restituzioni | **Incassi da contratti (lordi) − Rimborsi da contratti** |
| **Altri incassi** | ENTRATA fuori contratto (sessioni singole, extra) | `CashMovement` ENTRATA con `id_contratto IS NULL`, **escluse le rettifiche** (vedi §2) |
| **Cash flow reale** | Tutto ciò che entra, meno ciò che torna al cliente | **Incassi netti da contratti + Altri incassi** |

- **"Incassi netti da contratti"** è la spina dorsale: riconcilia con i contratti, è la base di tutte le
  viste temporali e di composizione. **v1.2:** la formula è **bidirezionale** —
  `Σ(ACCONTO + RATA) − Σ(RIMBORSO_CONTRATTO)`.
- **"Rimborsi da contratti"** è mostrato come **componente esplicita** (non sepolto tra le uscite
  operative): è un **contra-ricavo** (riduce l'incassato dei contratti), **non** un costo di gestione
  (vedi §7).
- **"Altri incassi"** è mostrato come **riga/categoria separata**, mai fuso negli incassi da
  contratti (così la parte contrattuale resta riconciliabile).
- **"Cash flow reale"** è l'informazione gestionale che i competitor non danno.

> **Relazione con il netto del contratto (FDM §2).** A livello di **singolo contratto** il modello
> definisce `netto_incassato = totale_versato − totale_rimborsato`. La somma di
> `totale_rimborsato` sui contratti del periodo **è** la nozione "Rimborsi da contratti" di questo asse.
> Sono la stessa grandezza vista da due lati (per-contratto vs per-periodo).

### Asse 2 — Posizione commerciale (competenza) — SECONDARIO

Quanto **venduto** (firmato) in un periodo, indipendentemente dall'incasso.

| Nozione | Definizione operativa | Origine dati |
|---|---|---|
| **Venduto** | Valore dei contratti firmati nel periodo | `Contract.prezzo_totale` aggregato su `Contract.data_vendita` |

Misura l'andamento delle vendite. **Mai sommato alla cassa** (assi distinti). Lo *scarto*
venduto − incassato = denaro venduto ma non ancora entrato (credito vivo dell'attività).

> **v1.2 — la terminazione non altera il venduto storico.** La terminazione anticipata **non riscrive**
> `prezzo_totale` (FDM §3.1): il *venduto* del periodo di firma resta integro. L'effetto economico della
> terminazione vive **interamente** sull'Asse 1 (rimborso) e sullo storno del residuo (FDM §9.5), non
> sulla competenza. Questa è una delle ragioni per cui lo storno usa un **campo dedicato** e non la
> riscrittura del prezzo.

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

> **v1.2 — contratti terminati fuori dal "da pianificare".** Un contratto CHIUSO per terminazione è
> **regolato** (residuo ≡ 0, rate future soft-deleted, FDM §9.5): non compare in "Da pianificare" né in
> "Da incassare". Coerente con la restrizione G1 (solo ATTIVO è pianificabile).

---

## 2. Esclusioni obbligatorie dalla cassa + il predicato contrattuale (rilievo Claude Code)

Il libro mastro contiene movimenti che **NON sono fatturato** e vanno **esclusi** dagli aggregati di
incassato, altrimenti il "fatturato per cassa" sovrastima:

- **`STORNO_SPESA_FISSA`** (e ogni categoria di **rettifica/storno** di spesa): è una correzione di
  un'uscita, non un ricavo. Escludere dagli incassi.
- Eventuali altre categorie di sistema non-ricavo presenti nel mastro.

**Conseguenza per gli aggregati temporali:** l'incassato per periodo si costruisce sulle categorie
**contrattuali** per la spina dorsale riconciliabile, più "Altri incassi" come riga separata. Mai un
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

> **Il predicato contrattuale, reso esplicito e BIDIREZIONALE (v1.2).** La previsione della v1.1 si è
> avverata dal lato **uscita**: il rimborso da terminazione è una **USCITA con `id_contratto`
> valorizzato**, e oggi **non esiste un predicato** che dica "questo movimento è contrattuale" — le
> query partizionano implicitamente per `id_contratto IS NOT NULL`, ma **solo sulle ENTRATA**. Una
> USCITA contrattuale cadrebbe quindi **negli aggregati di uscite operative/variabili** (misclassificata
> come costo). → Va introdotto un **predicato esplicito** del *movimento contrattuale*, valido **nelle
> due direzioni**:
>
> | Direzione | Categorie | Ruolo nell'incassato |
> |---|---|---|
> | **Contrattuale IN (entrata)** | `ACCONTO_CONTRATTO`, `PAGAMENTO_RATA` | **+** incassi da contratti |
> | **Contrattuale OUT (uscita)** *(v1.2)* | `RIMBORSO_CONTRATTO` | **−** incassi da contratti (contra-ricavo) |
>
> Gli "Incassi netti da contratti" = `Σ(contrattuale IN) − Σ(contrattuale OUT)`. Definito così, il
> bucket è **esaustivo e corretto per costruzione**: nessun movimento contrattuale (in nessuna
> direzione) finisce per errore tra i costi operativi o sparisce dal cash flow. Questa è
> l'**applicazione bidirezionale** del principio v1.1 (non più solo ENTRATA).

---

## 3. Riconciliazione — cosa torna con cosa (rilievo Claude Code)

Attenzione a non assumere riconciliazioni che il codice non garantisce:

- `kpi_incassato` = `sum(Contract.totale_versato)` sui contratti — **non** è una somma del libro
  mastro. Quindi la **somma "Incassi da contratti" per periodo** riconcilia con la logica dei
  contratti, ma il **cash flow reale totale** (che include "Altri incassi") **non** riconcilia con
  `kpi_incassato` — ed è corretto così: sono nozioni diverse.
- La vista primaria "fatturato dai contratti" è quella riconciliabile e pulita; "Altri incassi" è
  esplicitamente fuori da quella riconciliazione, per scelta.

> **v1.2 — la riconciliazione deve "vedere" i rimborsi.** Oggi `get_reconciliation`
> (`dashboard.py:127-208`) somma **solo ENTRATA** ed è **cieca alle uscite**: un rimborso di 600 su un
> incasso di 1000 sarebbe **invisibile** (il CASE azzera l'USCITA → delta 0 → falso "aligned"). Con il
> rimborso, l'invariante di riferimento diventa:
>
> - `totale_versato == Σ ENTRATA(contratto)` **(lordo, resta vero — non si tocca)**
> - `totale_rimborsato == Σ USCITA RIMBORSO_CONTRATTO(contratto)` **(nuovo)**
> - `netto_incassato == totale_versato − totale_rimborsato`
>
> Ridurre `totale_versato` per "incorporare" il rimborso **romperebbe** il primo invariante e farebbe
> riapparire un dovuto inesistente (FDM §2/§9.5): **vietato**. Il netto vive su `totale_rimborsato`.

---

## 4. Conformità — regime forfettario

Tutte le nozioni qui sono **gestionali**, non *revenue recognition* GAAP. AVGV opera in
**forfettario per cassa**. La nozione "Venduto" (competenza) è un **indicatore commerciale**, non
una posta contabile di bilancio (no *deferred revenue*). Il numero esposto come incassato deve
restare coerente con il **principio di cassa**.

> **v1.2 — il rimborso nel principio di cassa.** Un rimborso è un'**uscita di cassa reale**: riduce
> l'incassato **del periodo in cui avviene** (data del rimborso effettivo), non del periodo dell'incasso
> originale (che resta storicamente vero). Il trattamento fiscale del rimborso (e dell'eventuale storno
> del residuo) è parte della **DECISIONE APERTA** da chiudere col tributarista insieme alla policy di
> rimborso (FDM §3.1).

---

## 5. Mappa naming (significato → etichetta UI, da decidere)

Claude Code e Giacomo fissano le etichette italiane. Il vincolo è che **lo stesso concetto usi la
stessa etichetta in entrambe le spec**. Esempi indicativi (NON prescrittivi):

| Concetto (questo doc) | Possibile etichetta UI (da decidere) |
|---|---|
| Incassi netti da contratti | "Incassato (contratti)" |
| Rimborsi da contratti *(v1.2)* | "Rimborsi" / "Restituzioni" |
| Altri incassi | "Altri incassi" |
| Cash flow reale | "Liquidità reale" / "Entrate totali" |
| Venduto (competenza) | "Venduto" / "Contratti firmati" |
| Da pianificare | "Da pianificare" / "Da cadenzare" |

---

## 6. Bridge rule

Quando Claude Code implementa scelte non banali ancorate a questa tassonomia (forma degli aggregati,
gestione delle esclusioni, naming definitivo), la decisione va ricondotta a una *learning capture*
in chat e — se vincolante — riflessa in `BUILD_LOG.md`.

---

## 7. `RIMBORSO_CONTRATTO` — la categoria di uscita contrattuale (v1.2, NEW)

Il rimborso da terminazione anticipata (FDM §3.1, gamba rimborso) è registrato come **movimento di cassa
in uscita legato al contratto**, con una **categoria dedicata**.

### 7.1 Natura

| Proprietà | Valore |
|---|---|
| Tipo movimento | **USCITA** |
| `id_contratto` | **valorizzato** (il contratto terminato) |
| Categoria | **`RIMBORSO_CONTRATTO`** (naming definitivo a Claude Code) |
| Natura economica | **contra-ricavo** (restituzione di un incasso) — **NON** costo operativo |
| Data | `data_effettiva` = giorno del **rimborso effettivo** |
| Immutabilità | movimento **datato e immutabile** (compensa, non cancella) — come `STORNO_SPESA_FISSA` |
| Effetto sul Contract | incrementa `totale_rimborsato` **nella stessa transazione atomica** (FDM §9.5) |

> **Distinta da tutto il resto.** Non è una spesa fissa (non è un costo di gestione), non è uno storno
> di spesa (`STORNO_SPESA_FISSA` ha `id_contratto = NULL` e compensa un'uscita), non è "Altri incassi"
> (è un'uscita, non un'entrata). È la **prima** USCITA del sistema legata a un contratto.

### 7.2 Dove DEVE essere conteggiata / esclusa — le 9 query da allineare

La ricognizione sul codice reale ha mappato l'impatto di una USCITA contrattuale sulle query di cassa.
Poiché il predicato "contrattuale" non esiste ancora (§2), un `RIMBORSO_CONTRATTO` cadrebbe per
**default** negli aggregati di uscite-variabili. Allineamenti richiesti:

| # | Query | file:riga | Trattamento corretto del rimborso |
|---|---|---|---|
| 1 | `_compute_saldo` / `_signed_importo` | `movements.py:66-118` | ✅ **già corretto** — l'USCITA sottrae dal saldo reale (così deve essere) |
| 2 | `_compute_variable_burn_rate` | `movements.py:290-310` | ⚠️ **escludere** — un rimborso **non** è burn variabile (contra-ricavo, non costo) |
| 3 | `get_movement_stats` (uscite variabili) | `movements.py:1148-1151` | ⚠️ **escludere** dalle uscite operative — non deve ridurre il `margine_netto` come fosse un costo |
| 4 | `get_forecast` (burn/uscite) | `movements.py:1486-1535` | ⚠️ **escludere** dal burn proiettato — non gonfiare la proiezione spese a 90gg |
| 5 | `get_financial_trend` L1/L2/L3 | `movements.py:1609-1654` | ⚠️ **includere come componente contrattuale** — oggi il trend vede **solo ENTRATA** (`:1612`): il rimborso sarebbe **invisibile**. Deve abbattere gli incassi netti da contratti del periodo |
| 6 | `get_reconciliation` | `dashboard.py:127-208` | ⚠️ **rendere visibile** — oggi cieca alle uscite (§3); deve riconciliare `totale_rimborsato` vs `Σ USCITA RIMBORSO_CONTRATTO` |
| 7 | `get_cash_audit_log` (`flow_hint`) | `movements.py:900-906` | ⚠️ **non forzare ENTRATA** — oggi forza il segno entrata per le entity "contract"; un rimborso è un flusso **in uscita** |
| 8 | `get_balance` (`totale_uscite`) | `movements.py:396-415` | ⚠️ **dipende dall'uso** — se `totale_uscite` è la cassa-out **grezza** del saldo, il rimborso **ci sta** (è denaro uscito); se è/alimenta le **«uscite operative»**, **escluderlo** (contra-ricavo, non opex). Claude Code applica in base a cosa `get_balance` alimenta davvero |
| 9 | `get_dashboard_summary` (`monthly_revenue`) | `dashboard.py:84-94` | ⚠️ **vista contrattuale (netto)** — KPI "revenue del mese" su `tipo==ENTRATA + id_contratto`: oggi NON sottrae i rimborsi → sovrastima il netto. Deve sottrarre i `RIMBORSO_CONTRATTO` del mese. *(`divergent_count` dello stesso summary resta corretto: confronta `totale_versato` lordo vs Σ ENTRATA, invariante che Strada B preserva.)* |

> **Principio unificante.** Le query si dividono in famiglie rispetto al rimborso:
> - **Cassa/saldo reale** (#1, e #8 quando è saldo grezzo): il rimborso **deve** sottrarre (è denaro
>   uscito davvero). ✅
> - **Aggregati operativi** (#2, #3, #4, e #8 quando è «uscite operative»): il rimborso **non deve**
>   comparire come **costo** (falserebbe burn e margine). ⚠️ escludere.
> - **Viste contrattuali** (#5, #6, #7, #9): il rimborso **deve** comparire come **componente contrattuale
>   in uscita** (abbatte l'incassato/revenue dei contratti, non i costi). ⚠️ includere col segno giusto.
>
> Tutte e tre le famiglie si servono dello **stesso predicato esplicito** del §2 (movimento contrattuale
> IN/OUT): è quel predicato a smistare correttamente il rimborso in ciascuna query.

### 7.3 Cosa resta aperto

- **Naming definitivo** della categoria (italiano, coerenza UI) → Claude Code.
- **Policy** che genera l'importo del rimborso (pro-sedute, prezzo seduta) → **DECISIONE APERTA**,
  tributarista/legale (FDM §3.1).
- **Trattamento fiscale** del rimborso e dello storno residuo nel forfettario → stessa decisione aperta.
- **Storno del residuo** (gamba write-off, FDM §3.1): è la "nota di credito" speculare al rimborso —
  riduce il dovuto **senza** movimento di cassa e **senza** riscrivere `prezzo_totale`. Il meccanismo è
  **confermato** (ricognizione→spec): un campo immutabile `quota_stornata`, **gemello** di
  `totale_rimborsato`, che `contract_state.residuo()` sottrae (`residuo = max(prezzo − versato −
  quota_stornata, 0)`, FDM §2). Resta **fuori dalla cassa** e quindi fuori da questa tassonomia (che
  classifica i movimenti): lo storno **non** è un `CashMovement` — non compare in nessuna delle 9 query.
  La sua coerenza è l'invariante FDM §9.5.6 (`quota_stornata > 0 ⟹ chiuso`).
