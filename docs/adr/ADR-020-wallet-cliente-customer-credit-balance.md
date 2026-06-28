# ADR-020 — Wallet del cliente (customer credit balance): il credito a favore del cliente esce dal contratto

- Date: 2026-06-28
- Status: accepted
- Deciders: Giacomo Verardo (AVGV Technologies); analisi senior e bridge code-grounded di Claude Code
- Related upgrade ID: programma post-G7 "integrita' contabile + completamento bilaterale" (blocco wallet)
- Audit fondante: `docs/operations/AUDIT_REOPEN_SCENARIOS_2026-06-28.md` (§6/§7 instradamento + overpayment) · `AUDIT_TERMINAZIONE_BILATERALE_2026-06-27.md`
- Estende: **ADR-018** (completa il lato cliente della simmetria bilaterale) · si appoggia a **ADR-019** (reopen instrada il credito al wallet)
- Correlati: `ADR-016` (asse EROGATO); modello vivo `FINANCIAL_DOMAIN_MODEL.md`; entita' gemella lato trainer = `crediti_terminazione` (G7.10)

## Context

`ADR-018` ha reso flessibile il lato **trainer-credito** della terminazione (`INCASSA_ORA` editabile /
`RINUNCIA` / `A_CREDITO` differito). Il lato speculare — **cliente-credito** (rimborso) — e' rimasto **rigido**:
`terminate` ramo `CREDITO_CLIENTE` forza un **rimborso pieno, in contanti, subito** (`importo =
settlement.credito_cliente` fisso, `metodo_rimborso` obbligatorio). Il trainer non puo' rimborsare **parziale**
o **niente**.

Decisione founder: il trainer deve poter scegliere quanto rimborsare (anche parziale o zero); **il non
rimborsato genera un credito al cliente, da tracciare**. L'audit (`AUDIT_REOPEN_SCENARIOS`, §7) mostra inoltre
che il clamp `max(...,0)` di `residuo()` **butta via i sovra-pagamenti in silenzio**: un credito del cliente si
puo' perdere. Serve una **casa per il credito del cliente** — e per costruzione (ADR-019) **il credito esce dal
contratto**: il contratto tiene il debito (`residuo`), non un saldo negativo.

Questa casa e' un **wallet del cliente** (customer credit balance), la primitiva dei billing maturi
(Stripe *customer balance*, Chargebee *refundable credits*, QuickBooks/Xero *credit memo*).

## Decision Drivers

- **Completare la simmetria bilaterale** (ADR-018): anche il lato cliente flessibile.
- **Nessuna perdita silenziosa del credito cliente** (rimborso-differito + overpayment).
- **Primitiva provata** (customer credit balance) invece di un'invenzione locale.
- **Disciplina di scope** (D-STAGING di ADR-019): lean v1, niente stato distribuito prima della domanda reale.

## Considered Options

### Option A — `crediti_terminazione` bidirezionale (flag `beneficiario` TRAINER|CLIENTE)
- Pro: una tabella.
- Contro: biforca **ogni** endpoint sulla direzione cassa (incasso ENTRATA vs rimborso USCITA) e appiccica la
  logica "applica a contratto futuro" su un *receivable* a cui non appartiene. Il "unico modello" diventa il
  piu' sporco.

### Option B — Entita' separata: wallet del cliente (scelta)
- Il credito del cliente vive in un **ledger di credito per-cliente** (saldo derivato), distinto dal receivable
  del trainer. In contabilita' sono **due libri diversi** (crediti/attivo vs anticipi-wallet/passivo).
- Pro: pulizia (il wallet cresce i suoi comportamenti — applica-a-contratto — senza inquinare il receivable);
  e' un concetto di dominio riconoscibile (saldo cliente).
- Contro: piu' superficie (tabella + worklist + endpoint); il rischio over-engineering si controlla con lo
  staging (lean v1).

### Option C — Nessuna entita' (rimborso pieno o blocco)
- Contro: lascia lo spunto del founder irrisolto; rigido; perde i sovra-pagamenti.

## Decision

**Option B, lean.** Decisioni founder vincolanti (2026-06-28):

1. **D-RIMBORSO-EDITABILE** — `terminate` ramo `CREDITO_CLIENTE`: importo rimborso **editabile** `[0,
   credito_cliente]` (default = `credito_cliente`). Il **non rimborsato** (`credito_cliente − rimborsato`)
   diventa un **credito a wallet** del cliente. Niente "rinuncia" sul lato cliente (vedi §asimmetria).
2. **D-WALLET-ENTITA** — nuovo **ledger wallet del cliente** (per-cliente; voci con segno, **saldo derivato**;
   ogni voce tracciabile alla sua causale: `RIMBORSO_DIFFERITO` / `OVERPAYMENT` / `APPLICATO_CONTRATTO` /
   `RIMBORSATO_CASSA`). Tabella nuova business (`create_db_and_tables` la crea al boot su tutti i DB; migrazione
   = record formale, come `crediti_terminazione`). **Distinto** da `crediti_terminazione` (receivable trainer).
3. **D-WALLET-SORGENTI** — alimentato da: (a) **rimborso-differito** al terminate; (b) **overpayment** (il clamp
   di `residuo` non scarta piu' in silenzio: l'eccedenza va al wallet, ADR-019 D-INSTRADA).
4. **D-WALLET-USI** — il credito e': **rimborsabile** in cassa (USCITA `RIMBORSO_CONTRATTO`) + **applicabile** a
   un contratto futuro (acconto/sconto). Worklist "Rimborsi/Crediti da erogare" (gemella di `crediti-da-incassare`).
5. **D-STAGING-WALLET** — **v1 LEAN**: credito **tracciato + rimborsabile + applicato A MANO** dal trainer.
   L'**auto-applicazione cross-contratto** (stato distribuito, scenario S4 dell'audit) e' fetta **successiva**,
   su domanda reale. La regola e': prima il credito *non si perde e si vede*, poi lo si automatizza.
6. **D-WALLET-REOPEN** — `reopen` instrada il credito al wallet (ADR-019); se un credito wallet e' gia' **speso**
   a valle (S4), `reopen` **propone** la gestione (ADR-019 D-PROPONE), non agisce in automatico.

### Asimmetria deliberata (corretta) trainer vs cliente

Il lato trainer ha **3** azioni (incassa / a-credito / **rinuncia**); il lato cliente ne ha **2** (rimborsa /
metti-a-wallet). Non e' un'incompletezza: **si puo' rinunciare a cio' che ti e' dovuto, non a cio' che devi**.
Il trainer non puo' "rinunciare" unilateralmente al denaro che deve al cliente (sarebbe trattenere denaro
altrui); il cliente potra' *rinunciare al proprio credito* solo come azione esplicita e separata (futuro).

**Invarianti che NON cambiano**: asse EROGATO (ADR-016), Strada B, `residuo == 0 ⟺ saldato`, terminate come
atto atomico. Il wallet vive **fuori** dal `residuo()` del contratto (come il receivable trainer).

## Consequences

- **Positive**: simmetria bilaterale completata; nessun credito cliente perso (rimborso-differito + overpayment
  catturati); chiave di volta che rende `reopen` pulito (ADR-019 ha dove instradare il credito); base per la
  fidelizzazione (credito spendibile su contratti futuri).
- **Negative / costo**: nuova tabella + worklist + endpoint (rimborsa / applica) + FE; `terminate` lato cliente
  diventa editabile (tocca lo schema `ContractTerminate` + il ramo `CREDITO_CLIENTE`); l'auto-applicazione
  cross-contratto, **se** attivata, introduce consistenza di stato distribuito (tenuta in panchina dallo staging).
- **Follow-up**: spec di dettaglio; a implementazione aggiornare FDM, `api/CLAUDE.md`, `BUILD_LOG.md`.

## Rollback / Exit Strategy

La tabella wallet e' additiva (`create_db_and_tables`/`schema_sync`); rollback = drop tabella + ripristino del
rimborso pieno-obbligato lato terminate. Il rimborso editabile e' un superset retro-compatibile (default =
importo pieno = comportamento attuale). Nessun dato business in altre tabelle alterato.

## Supersedes / Superseded By

- **Estende ADR-018**: completa il lato cliente (rimborso editabile + wallet) della simmetria bilaterale; il
  lato trainer (`crediti_terminazione`) resta invariato.
- Si appoggia a **ADR-019** (reopen instrada il credito al wallet; ledger non-distruttivo).
- Superseded by: —
