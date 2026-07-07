# Audit — Architettura informativa FE (segnali operativi) + selettori clienti

**Data:** 2026-07-07 · **Trigger:** founder su cattura EventForm («(2 crediti)» accanto a «non ha
contratti attivi» = PANICO; «il frontend è rimasto con la vecchia logica») · **Tipo:** audit
READ-ONLY, 2 censimenti agente. Input per **ADR-025** (seduta singola + portafoglio cliente).
**Decisioni founder GIÀ ratificate (2026-07-07):** (1) seduta singola = importo LIBERO, CONSIGLIATO
dai contratti precedenti del cliente · (3) wallet: si segnala e si SUGGERISCE di scalarlo ·
(4) scelta esplicita alla creazione. **(2) dove vive l'insoluto = decisione POST questo audit.**
**Legge nuova (dalla cattura): segnale ⇒ azione** — un warning senza scelta non dà controllo, dà
ansia (raffina D-MAI-SILENZIO-IN-SCRITTURA, ADR-024).

## 1. Root cause del dropdown (risposta secca)

`crediti_residui` client-level è l'**UNICO** campo dell'enrichment che **NON filtra
`chiuso == False`** (`clients.py:304-332`, commento deliberato: «chiuso blocca nuove operazioni,
non invalida crediti» — pensato per il recupero/storico). Tutti gli altri (`contratti_attivi`,
`totale_versato`, `prezzo_totale_attivo`, `ha_rate_scadute`) filtrano i chiusi
(`clients.py:378-433`). EventForm etichetta il dropdown con quel campo («(N crediti)»,
`EventForm.tsx:270`) → sullo stesso schermo due interpreti in disaccordo (P1). L'unico selettore
col problema è EventForm; gli altri (rubrica, palette, form contratto) mostrano solo il nome.

**Incoerenze P1-P5:** P1 label da chiusi · P2 doppio warning su assi diversi (hard crediti / soft
contratti) · P3 «residui» fonde scalabile+non-scalabile → KPI inflazionabili · P4 scoperta tardiva
(il blocco arriva solo dopo la selezione) · P5 `ha_rate_scadute` esclude i chiusi ma la label non
lo dice. **Gap wire per l'etichetta onesta:** serve `crediti_residui_attivi` (residui dei SOLI
contratti attivi) — `contratti_attivi` basta già per «senza contratto attivo».

## 2. Mappa segnali (sintesi — dettaglio nel report agente, in coda)

**Cat. A — riduzioni inline FE dove il resto è SSoT:** I1 «importo da incassare» (rinnovi-incassi,
`sum()` FE) · I5 preflight status /oggi (`getPreFlightStatus` FE vs `HealthCheck` backend, mapping
non documentato) · I7 «da incassare vs da pianificare» (PlanStat, riduzione FE).
**Cat. B — stesso nome, semantica diversa:** I3 «crediti residui» (cliente=somma multi-contratto
incl. chiusi vs contratto=singolo) · I4 «rate scadute» (KPI clienti conta CLIENTI, KPI contratti
conta RATE) · I6 readiness score da 2 endpoint con cache diverse.
**Cat. C — dati backend senza casa in UI:** **B4 wallet cliente invisibile nel profilo** ·
**B5 receivable (crediti da incassare) invisibile nel profilo** · B1 `sedute_non_erogate_chiusura`
mai mostrato in lista/profilo (nell'hero c'è il banner) · B7 aging 60+ senza alert · B8 runway
negativo senza alert · B10 contracts-to-plan poco prominente · B3 occupazione vs erogazione senza
confronto side-by-side.
**⚠️ Falsi positivi dell'agente, verificati e SCARTATI:** «B2 history mai chiamato» (il tab Storico
esiste, G8.1.1/G8.4) · «B12 reopen-preview inutilizzato» (ReopenContractDialog lo usa) — restano
nel report grezzo, NON sono finding.

## 3. La risposta che l'audit dà alla decisione (2): dove vive l'insoluto

Il profilo cliente oggi NON ha una casa per la posizione economica complessiva: wallet € (B4),
crediti da incassare (B5), e i futuri insoluti da sedute singole sono tutti senza superficie.
La direzione coerente con «portafoglio cliente che include TUTTO» (founder):
- **Pannello «Portafoglio» nel profilo cliente** = crediti sedute SCALABILI (contratti attivi) ·
  wallet € · crediti da incassare (receivable) · insoluti sedute singole (post ADR-025) · storico.
- **Le worklist globali restano per l'AZIONE cross-cliente** (rinnovi-incassi), il profilo per il
  CONTESTO — un segnale, due viste, UN solo interprete backend.
- Il dropdown EventForm etichetta con la stessa semantica del portafoglio (scalabile vs non).
Da ratificare in ADR-025 insieme al modello seduta-singola.

## 4. Prossimi passi
1. **ADR-025 «Seduta singola e portafoglio cliente»** (proposed → decisioni founder: collocazione
   insoluto §3, conferma pannello Portafoglio).
2. Dentro G9.7 (non-money, subito): dropdown onesto (campo `crediti_residui_attivi` + label
   «senza contratto attivo»), fix P1-P4.
3. Cat. A (I1/I5/I7) → candidati G9.7.4 (guard di classe: riduzioni inline = stessa classe del
   money-math FE).
4. La matrice assi (`MATRICE_ASSI_SEMANTICI.md`) si aggiorna con l'asse «crediti-cliente
   (scalabile vs storico)» — oggi due interpreti.
