# ADR-015 — Funnel Rinnovi & Retention: nessuna perdita silenziosa di contratti/clienti

- Date: 2026-06-20
- Status: accepted
- Deciders: Giacomo Verardo (AVGV Technologies); analisi e proposta di Claude Code
- Related upgrade ID: —
- Spec di dettaglio (vincolante sui criteri): `docs/technical/SPEC_RINNOVI_SCADUTI_E_RETENTION.md`
- Correlati: `ADR-014` (gestione finanziaria), `SPEC_RINNOVO_E_CONTRATTI_DA_PIANIFICARE.md`

## Context

I contratti **scaduti** (`data_scadenza < oggi`) spariscono silenziosamente: `/rinnovi-incassi` e
l'alert mostrano solo i contratti **in scadenza futura** (`dashboard.py:346-347`). Non esiste alcuno
**stato terminale** ("perso"/"non rinnova"). Un contratto che oltrepassa la scadenza senza rinnovo
cade fuori dalla finestra e non compare più → si perdono **opportunità di rinnovo** (denaro) e
**clienti** (churn) per *assenza*, non per decisione. È l'opposto del controllo che il prodotto promette.

## Decision Drivers

- **Nessuna perdita silenziosa** — invariante già adottato altrove (contratti-da-pianificare): denaro/
  opportunità dovuti mai invisibili.
- **Determinismo** — gli stati business-critical sono espliciti e auditabili.
- **Riuso** — sfruttare flusso di rinnovo (SPEC_RINNOVO), pagina `/rinnovi-incassi`, WhatsApp win-back.
- **Differenziazione** — superare lo standard CRM separando le due lenti e producendo dati di churn.

## Considered Options

### Option A — Auto-archiviare gli scaduti dopo un grace period
- Pro: zero stato nuovo.
- Contro: si perde il *perché* e la decisione umana; resta una sparizione (solo ritardata).

### Option B — Funnel con stato terminale esplicito "non rinnova" + due lenti (scelta)
- Pro: nessuna sparizione; esito = dato (churn analytics); contract-lens e client-lens separate e
  collegate; riuso massimo.
- Contro: introduce un piccolo stato dato ("perso" + motivo) e nuove viste da mantenere.

### Option C — Unificare contratto e cliente in un'unica vista "a rischio"
- Pro: una sola lista.
- Contro: confonde due nozioni distinte (un cliente può avere uno scaduto e un attivo); è l'errore
  tipico dei gestionali palestra.

## Decision

**Option B.** Si adotta un **funnel Rinnovi & Retention** con:

1. **Due lenti separate e collegate** — *contratto* (opportunità di rinnovo) e *cliente* (retention/
   churn). Non si fondono.
2. **Stati derivati** del contratto: `attivo · in scadenza · scaduto(da rinnovare) · rinnovato · perso`.
   `rinnovato` = esiste figlio `rinnovo_di`; `scaduto` = aperto, `data_scadenza<oggi`, non rinnovato,
   non perso, con opportunità residua.
3. **Stato terminale esplicito "non rinnova" + motivo** (decisione founder): il trainer chiude
   l'opportunità registrando un motivo strutturato. Il contratto **esce dalla worklist ma resta nello
   storico** (non distruttivo, reversibile). Il motivo diventa dato di churn.
4. **Invariante non-negoziabile — nessuna perdita silenziosa**: nessun contratto aperto, scaduto, con
   opportunità residua, non rinnovato e non marcato perso, può lasciare la worklist senza una
   **decisione umana esplicita** (rinnovo o "non rinnova").
5. **Esclusione dei già-rinnovati** anche dalla vista "in scadenza" (correzione del bug attuale).
6. **Perimetro**: iterazione corrente = **lente contratto** (scaduti da rinnovare + esito "non
   rinnova"); **lente cliente** (retention/lapsed/win-back) progettata nella spec ma **differita**.
   Confine con l'alert `inactive_clients` (attività-based) chiarito: complementare, non fuso.

> **Emendamento 2026-06-20 (rilievo founder) — rilevazione client-aware.** La rilevazione
> contract-level ("nessun figlio `rinnovo_di`") è **fallace**: un cliente può aprire un nuovo
> contratto NON collegato → falso positivo "da rinnovare" mentre il cliente è ancora attivo. Decisione
> corretta: un'opportunità di recupero esiste **solo se il cliente non ha alcun contratto attivo**
> (`chiuso=False AND data_scadenza>=oggi`). Questo sussume sia il rinnovo-figlio sia il
> nuovo-contratto-non-collegato. **Unità = cliente** (conteggio per clienti, 1 riga/cliente,
> rappresentato dal contratto scaduto più recente). Conseguenza: una fetta minima della lente cliente
> entra necessariamente già ora (non si può fare la lente contratto "pura" senza falsi positivi); la
> retention ricca (segmenti/scoring/win-back) resta differita. Vedi SPEC v1.1 §3-bis/§4.

> **Emendamento 2 — 2026-06-20 (esame dato reale) — stato SOSPESO.** `chiuso` true/false è
> insufficiente: un contratto **scaduto per data ma con sedute prepagate residue** veniva contato
> "attivo" e/o offerto come "da recuperare", quando il trainer **deve** ancora quelle sedute (clienti
> reali Paola/Merchiori/Scalmato). Decisione: **ciclo a 4 stati derivati** — ATTIVO / **SOSPESO**
> (scaduto + crediti residui > 0) / **ESAURITO** (scaduto + crediti 0) / CHIUSO. **Ingaggio cliente =
> ATTIVO o SOSPESO**: il sospeso è ingaggio (sedute da erogare) → esclude dalla win-back. Nuova worklist
> **"Contratti sospesi / sedute da recuperare"** (estendi o decadi, decisione esplicita — invariante
> anti-perdita esteso alle SEDUTE prepagate, non solo al denaro). Corretto anche il rappresentante
> (più recente in assoluto). L'auto-close non scatta mai per pacchetti a crediti residui → causa
> meccanica del falso "attivo". Impatto: rivedere endpoint `clients-to-recover` + UI (Step 2-5) per
> escludere i sospesi. Vedi SPEC v2.0 §3/§3-bis/§4-bis.

## Consequences

- **Positive**: stop alla perdita silenziosa di denaro e clienti; renewal pipeline allo stato dell'arte;
  dati di churn (motivi); riuso di rinnovo/comunicazioni; base pronta per la retention cliente.
- **Negative**: un piccolo stato dato nuovo ("perso" + motivo) da gestire (audit, reversibilità);
  due sezioni in più da mantenere; rischio di worklist lunga se il trainer non decide (mitigato da
  aging + azione "non rinnova").
- **Follow-up actions**:
  - SPEC → `IMPL_PLAN_RINNOVI_SCADUTI.md` ancorato al codice, poi implementazione.
  - Definire forma dello stato "perso" (campo nullable su `Contract` vs tabella outcome) e set motivi.
  - Iterazione successiva: lente cliente (retention) come da SPEC §6.
  - A implementazione: aggiornare `api/CLAUDE.md` + `BUILD_LOG.md`.

## Rollback / Exit Strategy

Le viste sono letture aggregate; rimuoverle non tocca i dati. L'unico stato persistente nuovo è
l'esito "non rinnova" (campo/tabella) — reversibile e non distruttivo; in caso di rollback resta un
dato inerte ignorato. Nessuna migrazione che alteri i contratti esistenti.

## Supersedes / Superseded By

- Supersedes: — (estende ADR-014 sul dominio rinnovo/retention)
- Superseded by: —
