# ADR-014 — Gestione finanziaria: tassonomia cassa/competenza + vista Contract-first

- Date: 2026-06-19
- Status: accepted
- Deciders: Giacomo Verardo (AVGV Technologies); analisi e rilievi tecnici di Claude Code
- Related upgrade ID: —
- Spec di dettaglio (vincolanti sui criteri di accettazione):
  - `docs/technical/TASSONOMIA_FINANZIARIA.md` (v1.1) — vocabolario condiviso, vincolante su concetti e formule
  - `docs/technical/SPEC_RINNOVO_E_CONTRATTI_DA_PIANIFICARE.md` (v1.2)
  - `docs/technical/SPEC_GESTIONE_FINANZIARIA_TEMPORALE.md` (v1.1)

> Questo ADR **cristallizza la decisione architetturale**; le tre spec restano la fonte di dettaglio
> sui criteri di accettazione. L'ADR non le duplica: registra il *perché* e i confini vincolanti.

## Context

La gestione finanziaria attuale espone solo uno **stato istantaneo** (`kpi_fatturato`,
`kpi_incassato`, aging report sulle rate, `monthly_revenue` scalare). Due lacune emergono dal primo
cliente reale *efficienza-driven*:

1. **Nessun asse temporale.** Il PT non può rispondere a "come sto andando rispetto a prima?": manca
   aggregazione per periodo, trend, composizione del fatturato.
2. **Denaro dovuto invisibile.** L'aging report è costruito su `select(Rate).join(Contract)` — itera
   sulle rate. Un contratto **senza piano rate** (caso reale "Chiara") non produce righe: è
   strutturalmente cieco all'intero sottosistema di solleciti, pur essendo contato in `kpi_fatturato`.

È la prima modifica alla logica finanziaria dal 2026-06-08 (INC-2026-06-08, fix KPI contratti chiusi).
Toccando il nodo centrale del sistema (il contratto, con 12 livelli di Contract Integrity), serve una
decisione tracciabile prima del codice.

Inoltre, entrambe le spec introducono nozioni di scomposizione del fatturato: senza un vocabolario
unico l'UI finanziaria nascerebbe incoerente (stessi concetti, nomi e formule diverse).

## Decision Drivers

- **Differenziatore competitivo**: la gestione economico-finanziaria è lo spazio scoperto dai leader
  anglosassoni (Trainerize, TrueCoach), nati attorno al training con la finanza come bolt-on.
- **Conformità forfettario per cassa**: le tasse del trainer si calcolano sull'incassato, non sul
  venduto. Il numero "fatturato" deve essere coerente col principio di cassa.
- **Tracciabilità e riconciliazione**: nessun numero finanziario deve sovrastimare o non riconciliare.
- **Zero migrazione dati**: i contratti esistenti devono comparire appena la vista sa cercarli.
- **Confine di rischio (posizionamento)**: visibilità sulla liquidità reale ≠ agevolazione di reddito
  non dichiarato. Decisione di prodotto e di rischio da fissare esplicitamente.

## Considered Options

### Option A — Estendere l'aging report per coprire anche i contratti senza rate

- Pro: un unico sottosistema di "orizzonte finanziario".
- Contro: l'aging è **Rate-first** per natura; forzarvi i contratti senza rate snatura la query e
  confonde due nozioni distinte (scadenze delle rate vs denaro da cadenzare). Rischio di regressione
  su un report già testato.

### Option B — Vista Contract-first separata + asse temporale, con vocabolario condiviso

- Pro: ogni nozione resta pura e riconciliabile; l'aging non si tocca; il vocabolario condiviso
  (tassonomia) impedisce l'incoerenza UI; ogni layer è un `GROUP BY` su campi già esistenti (nessun
  motore finanziario nuovo, nessuna migrazione).
- Contro: introduce nuovi endpoint/aggregati da mantenere e una terza spec (la tassonomia) come
  dipendenza vincolante.

### Option C — Solo asse temporale (rimandare i contratti da pianificare)

- Pro: scope minimo.
- Contro: lascia scoperto il buco più grave per il cliente reale (denaro dovuto mai sollecitato).

## Decision

**Option B.** Si adotta una **tassonomia finanziaria condivisa e vincolante** e una **vista
Contract-first separata dall'aging**, con questi punti fermi:

1. **Due nozioni mai fuse** — *cassa* (incassato, `CashMovement.data_effettiva`) **primaria/default**
   e *competenza* (venduto, `Contract.data_vendita`) **secondaria/affiancata**. Lo scarto tra le due
   è l'informazione di valore (credito vivo). Mai sommate in un unico totale.
2. **Incassato per periodo ristretto alle categorie contrattuali** (`ACCONTO_CONTRATTO` +
   `PAGAMENTO_RATA`), **escludendo storni e ENTRATA non-ricavo** (es. `STORNO_SPESA_FISSA`). Un
   generico `sum(ENTRATA)` sovrastima il fatturato per cassa. `kpi_incassato` resta
   `sum(Contract.totale_versato)`: la spina dorsale "incassi da contratti" riconcilia con la logica
   contratti, il "cash flow reale" (con "Altri incassi") **non** riconcilia — ed è corretto.
3. **"Da pianificare" calcolato sul residuo**:
   `(prezzo_totale − totale_versato) − somma(residui rate NON SALDATE)`, dove "non saldate" =
   `stato ∈ {PENDENTE, PARZIALE}` (stesso predicato dell'aging). Per i contratti a zero rate collassa
   sul residuo pieno e, per i parzialmente pianificati, coincide con `importo_disallineamento` già
   calcolato in `_to_response_with_rates`. **Non** "Booked − Billed" letterale (doppia-conta acconti
   e rate saldate).
4. **Vista Contract-first** dei contratti aperti, con residuo positivo e **zero rate**, integrata nel
   sistema di solleciti come categoria a sé. Il pattern di sicurezza di `create_contract` (trainer_id
   dal JWT, `_check_client_ownership`, 404 mai 403) resta invariato anche sul flusso di rinnovo.
5. **Confine di posizionamento (vincolante)**: il software espone **cash management neutro**
   (visibilità sulla liquidità: quanto entra, datato e categorizzato). NON nomina, struttura o
   agevola alcuna nozione di reddito "non dichiarato". Nessun campo, label o filtro deve mai codificare
   lo *stato fiscale*: il sistema distingue solo "con contratto / senza contratto" (`id_contratto`
   presente/assente). Questa linea separa uno strumento neutro da uno con finalità di evasione, e
   protegge la postura di compliance di AVGV. *Non è un parere fiscale: l'asse va validato con un
   tributarista.*

Perimetro escluso per scelta consapevole: stato "parzialmente pianificato" (segnale già pronto via
`piano_allineato`/`importo_disallineamento`); taglio per tipo pacchetto (testo libero, inaffidabile);
top-clienti (vista relazionale, non temporale); cifratura backup automatici (traccia G1/G5 separata).

## Consequences

- **Positive**: differenziatore competitivo difendibile; numeri riconciliabili e non gonfiati;
  l'aging non viene toccato (zero regressione); vocabolario unico → UI coerente; zero migrazione dati
  (caso Chiara risolto leggendo campi esistenti); decisioni di rischio cristallizzate.
- **Negative**: nuovi endpoint/aggregati da mantenere; dipendenza vincolante dalla tassonomia (ogni
  modifica concettuale va riflessa lì per prima); l'asse "Altri incassi" richiede disciplina sul
  confine di posizionamento.
- **Follow-up actions**:
  - Implementazione consigliata: prima `SPEC_RINNOVO` (lacuna operativa + nasce il vocabolario),
    poi `SPEC_GESTIONE_FINANZIARIA_TEMPORALE` (Layer 1 → 2 → 3).
  - Definire i bucket di cassa come **partizione complementare su `id_contratto`** (esaustiva per
    costruzione), poi escludere gli storni.
  - Fissare il naming UI italiano definitivo (regola 9 CLAUDE.md) coerente tra le due spec.
  - A implementazione avvenuta: aggiornare `api/CLAUDE.md` (nuovi endpoint dashboard/contracts) e
    `BUILD_LOG.md` (bridge rule), aggiungere test di riconciliazione.
  - Validare il confine di posizionamento §0 con un professionista tributarista.

## Rollback / Exit Strategy

Ogni layer è consegnabile e disattivabile da solo (sono letture aggregate read-only su dati già
scritti). Rollback = rimozione degli endpoint/aggregati nuovi e dei relativi componenti UI; nessun
dato viene scritto o migrato, quindi nessuna perdita né necessità di down-migration. L'aging report e
i KPI esistenti restano intatti per costruzione.

## Supersedes / Superseded By

- Supersedes: —
- Superseded by: —
