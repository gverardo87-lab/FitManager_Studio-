# Audit — Eventi orfani su contratto chiuso + occupazione crediti invisibile a video

> **ARCHIVIATO 2026-09-02** — 13 finding foldati in ADR-024 e SPEC_G9.7 (tutti i gate chiusi
> 2026-07-16). Riferimento storico, mai contesto di lavoro.

**Data:** 2026-07-07 · **Trigger:** segnalazione founder su caso reale (contratto 39, Verardo Giacomo,
crm.db dev) · **Tipo:** audit READ-ONLY (forensics DB + 2 censimenti code-grounded). **ZERO fix applicati** —
questo documento è l'input della riflessione di metodo, non una spec.
**Metodo:** forensics sqlite `mode=ro` sul crm.db reale + 2 agenti Explore (asse scrittura eventi×contratto ·
asse lettura/display occupazione). Coordinate `file:riga` = snapshot 2026-07-07.

---

## 1. Forensics — cosa è successo davvero (contratto 39)

Timeline dal DB (audit_log + agenda.data_creazione):

| Quando (07/07) | Fatto | Stato contratto 39 |
|---|---|---|
| 16:46:40 · 16:46:53 | Trainer crea 2 eventi PT «Completato» (id 640, 641) dall'agenda | **CHIUSO** (terminato 03/07) |
| — | `_auto_assign_contract` filtra `chiuso==False` → nessun match → eventi salvati con **`id_contratto=NULL`**, **201 senza alcun segnale** | |
| 16:47:15 | Reopen: riconcilia rate (1 ripristinata) + cassa + wallet (1 annullato/riassorbito) — **gli eventi NON sono nel perimetro** | riaperto |
| 16:48:35 | Trainer crea PT (id 642) → contratto ora aperto → **si aggancia e occupa** (poi → No_Show) | aperto |

**Esito:** i 2 eventi 640/641 sono gli **unici PT orfani in stato di occupazione dell'intero DB**
(quindi fenomeno nuovo, non storico). Sono irrecuperabili dalla UI: il re-parenting è **vietato by
design** (`EventUpdate` extra-forbid esclude `id_contratto` — la protezione anti-bypass del fence
G7.8-ter chiude anche l'unica via di recupero). Limbo permanente.

**Il display che «non torna»:** occupazione reale del 39 = 5 Completato + 1 Cancellato_Tardivo +
1 No_Show = **7/12 → residui 5**. L'hero mostra «Programmate 0 · Completate 5 · Residui 5» su 12
totali → **2 crediti spariti a video** (le penali occupano ma nessuna superficie le mostra).
`sedute_penali` e `sedute_rinviate` sono **GIÀ sul wire** del dettaglio — il FE non li renderizza.

## 2. Censimento asse SCRITTURA eventi×contratto (B1-B8)

| # | Sev | Buco | Dove |
|---|---|---|---|
| B1 | ALTO | Cliente con soli contratti chiusi → auto-FIFO ritorna None → evento PT nasce orfano **fail-silent** (201, zero warning) | `agenda.py:488-491` |
| B2 | ALTO | `reopen` riconcilia rate/cassa/receivable/wallet ma **non enumera gli eventi**: gli orfani creati durante la chiusura non rientrano MAI | `transitions.py:502-670` |
| B3 | ALTO | `terminate` non censisce/marca gli orfani (nessun marker `chiusa_da_*` come per le rate) → indistinguibili al reopen | `transitions.py:156-406` |
| B4 | MEDIO | EventForm avvisa solo su `crediti_residui <= 0`; NON avvisa «questo cliente non ha contratti attivi» → il trainer non può sapere che nascerà un orfano | `EventForm.tsx:154-157` |
| B5 | MEDIO | Il backend non distingue nella response «agganciato» da «orfano» (201 identico) → il FE non PUÒ avvisare nemmeno volendo | `agenda.py:487-519` |
| B6 | MEDIO | Ghost-events include gli orfani passati ma non li etichetta come «senza contratto» (e i Completato orfani non compaiono in NESSUNA worklist) | `dashboard.py:245-298` |
| B7 | BASSO | (Auto-protezione, non bug) gli orfani NON inquinano il conguaglio di terminate — sono fuori da tutto, incluso ciò che dovrebbe contarli | — |
| B8 | BASSO | Il fence ADR-023 salta gli orfani (`id_contratto` NULL → check falsy) — coerente ma non dichiarato | `agenda.py:314-333` |

**Nota strutturale (il finding più interessante):** B1 + divieto di re-parenting = **deadlock da due
protezioni giuste**. Il filtro `chiuso==False` dell'auto-assign è corretto; il no-re-parenting
(G7.8-ter, chiude il bypass del fence) è corretto; la loro composizione produce un dato
irrecuperabile senza che nessuna delle due decisioni sia sbagliata da sola.

## 3. Censimento asse LETTURA/display occupazione (D1-D5)

| # | Superficie | Mostra | Manca | Dato già sul wire? |
|---|---|---|---|---|
| D1 | Hero dettaglio (riga crediti) | Totali · Programmate · Completate · Residui | **Penali · Rinviate** → i residui non sono spiegabili dalla vista | ✅ `sedute_penali`, `sedute_rinviate` |
| D2 | ContractRow (lista) | `usati/totali` + «N svolte» | la differenza usati−svolte (programmate? penali?) non è spiegata | ⚠️ lista non ha il breakdown |
| D3 | ContrattiTab (profilo cliente) | come D2 | come D2 | ⚠️ come D2 |
| D4 | DeleteContractDialog | `crediti_residui` **RICALCOLATO inline** (`totali − usati`) | violazione R-SSOT-FE sull'asse CREDITI (il guard FE-no-money-math copre solo il denaro) | ✅ `crediti_residui` |
| D5 | ExpiringContractsSheet / SuspendedCard (rinnovi) | usati/residui aggregati | breakdown per stato | ⚠️ response minimal |

**Classe:** identica al «netto nudo» dell'INC-2026-07-03 — un derivato mostrato senza i suoi
componenti. D-NESSUN-NETTO-NUDO (ADR-022 Add. II) è stato applicato SOLO alla cassa.

## 4. Cosa regge (per completezza)

Guard esplicito su `id_contratto` chiuso (400) · fence ADR-023 sugli eventi contabilizzati ·
occupazione da SSoT `STATI_OCCUPAZIONE_CREDITO` con test semantico anti-literal · il conguaglio
è cieco agli orfani (non si corrompe) · gli orfani sono 2 in tutto il DB (fenomeno contenuto).

## 5. Le classi ricorrenti (input per la riflessione di metodo)

1. **Fail-silent in scrittura su ramo non presidiato** (B1/B5) — 3ª occorrenza della classe
   (typo-422 payload · default silenzioso in lettura cassa · auto-assign fallito).
2. **Derivato nudo a video** (D1-D3, D5) — 2ª occorrenza (netto nudo cassa → residui nudi crediti).
3. **Transizione che non enumera le entità satellite** (B2/B3) — gemella dei «5 produttori
   mancati»: terminate/reopen enumerano rate+cassa+receivable+wallet ma non gli eventi.
4. **Violazione consumo-SSoT fuori dal perimetro del guard** (D4) — il gemello FE-no-money-math
   esiste per il denaro, non per i crediti.

Le leggi che curano queste classi ESISTONO già (metodo in 4 regole di LEARNING_PROGRAMMAZIONE:
chiudi l'insieme · interprete unico · totalità fail-loud · gemello di esaustività; ADR-022 Add. II;
TransitionExecutor; Hypothesis G9.5) ma sono state applicate **per-asse** (cassa/denaro), non
**per-classe**. Il censimento assi del 2026-07-04 aveva già nominato A9 (crediti/wallet senza
modulo SSoT) e A10 (occupazione); il charter `semantic-birth-auditor` (SPEC_G9.4-BIS §5) è il
flag LOW mai attivato. La macchina Hypothesis esplora solo il money-path: una rule
«crea evento su contratto chiuso/riaperto» avrebbe trovato B1/B2 da sola.

**Nessun fix in questo documento.** Prossimo passo = decisione di metodo col founder.
