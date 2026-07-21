# AUDIT — Frontend core CRM: intuitività, fiducia e velocità operativa

**Stato:** ✅ CONCLUSO E FOLDATO — fotografia del codice al 2026-07-21
**Data audit:** 2026-07-20/21
**Esito operativo:** finding trasformati in `docs/specs/SPEC_FRONTEND_CORE_INTUITIVITA.md`
**Perimetro:** Clienti · Contratti · Agenda · Rinnovi & Incassi · Cassa · shell di navigazione
**Natura:** audit read-only; nessuna modifica runtime

> Questo documento è una fotografia storica. Non è contesto di lavoro e non prescrive l'implementazione.
> La posizione in `docs/archive/` dichiara che l'audit è concluso; il lavoro vivo è nella SPEC collegata.

## 1. Obiettivo e tesi

Obiettivo: verificare se il CRM core nasconde la propria complessità e permette al professionista di
capire sempre dove si trova, cosa richiede attenzione e quale azione sicura compiere dopo.

Tesi verificata: l'ossatura dei journey è valida, ma la qualità percepita è limitata soprattutto da
**integrità percettiva**, privacy e frammentazione del modello mentale — non da carenza di feature.

## 2. Metodo ed evidenza

Audit parallelo su tre lenti, consolidato da un lead review:

1. journey cliente → contratto → agenda → incasso → cassa;
2. accessibilità e Web Interface Guidelines aggiornate;
3. React/Next.js performance e data-fetching secondo le best practice Vercel.

Fonti autorevoli: `AGENTS.md`, `MANIFESTO.md`, `LAUNCH_SCOPE.md`, `frontend/CLAUDE.md`, ADR e SSoT
finanziarie vive. L'app rispondeva su `127.0.0.1:3000` con redirect al login, ma il browser integrato
non esponeva una sessione controllabile: responsive, focus runtime e journey autenticati restano da
verificare nel gate LIVE della SPEC.

## 3. Esito senior

### 3.1 Punti solidi da preservare

- creazione cliente con continuità verso il profilo;
- deep-link contestuali e ritorno alla superficie di origine;
- tab significativi sincronizzati nell'URL;
- Agenda con range server-side e dati precedenti durante il cambio intervallo;
- Rinnovi & Incassi già orientata alle eccezioni;
- dialog finanziari separati per transizione e conferme distruttive;
- invalidazioni inverse attente alla consistenza finanziaria;
- profilo cliente già vicino a un journey hub.

### 3.2 Finding bloccanti di fiducia

| ID | Severità | Finding | Evidenza primaria |
|---|---|---|---|
| A-01 | P0/P1 | La lista Clienti espone importi/prezzo/crediti fuori dal contesto finance dedicato | `frontend/src/components/clients/ClientsTable.tsx:131-132,203,226-231` |
| A-02 | P1 | Rinnovi & Incassi può convertire query fallite in array vuoti e mostrare «Tutto in regola» | `frontend/src/app/(dashboard)/rinnovi-incassi/page.tsx:576-590,695-704` |
| A-03 | P1 | Profilo cliente confonde errore/rete con «non trovato» | `frontend/src/app/(dashboard)/clienti/[id]/page.tsx:56-60,128-129` |
| A-04 | P1 | Tab Contratti/Sessioni/Movimenti trasformano errore in empty state | `ContrattiTab.tsx:40-50`, `SessioniTab.tsx:17-29`, `MovimentiTab.tsx:17-28` |
| A-05 | P1 | Cassa può nascondere errori di saldo/statistiche senza spiegazione | `frontend/src/app/(dashboard)/cassa/page.tsx:230-233,380-416` |
| A-06 | P1 | Il path cliente rende non interattive azioni lecite e simula un hard gate inesistente | `frontend/src/components/clients/profile/PanoramicaTab.tsx:56-96,242-249,282` |

### 3.3 Accessibilità operativa

| ID | Severità | Finding | Evidenza primaria |
|---|---|---|---|
| A-07 | Critico | Promemoria Agenda aperto con `div onClick`, non raggiungibile/azionabile da tastiera | `frontend/src/components/agenda/TodoHoverCard.tsx:145` |
| A-08 | Critico | Toggle Sidebar annidato nel Link, `tabIndex=-1`, semantica interattiva invalida | `frontend/src/components/layout/Sidebar.tsx:209,226-239` |
| A-09 | Alto | Popup promemoria senza dialog semantics, focus trap/restoration ed Escape affidabile | `TodoHoverCard.tsx:149-205` |
| A-10 | Alto | Label non associate nei form di incasso, rimborso, credito e piano rate | `IncassaResiduoDialog.tsx:132-169`, `EroghaRimborsoDialog.tsx:130-167`, `IncassaCreditoDialog.tsx:130-167`, `payment-plan/AddRateForm.tsx:54-79`, `GeneratePlanForm.tsx:70-112` |
| A-11 | Alto | Manca skip link al contenuto principale | `frontend/src/app/(dashboard)/layout.tsx:214-244` |

Finding sistemici medi: filtri senza `aria-pressed`; ricerca senza nome accessibile; loading non
annunciati; stato affidato al colore; `transition-all`; motion-reduce incompleto; più `h1` per il logo
della Sidebar; placeholder con `...` invece di `…`.

### 3.4 Architettura informativa

- L'incasso e il controllo finanziario sono distribuiti tra dettaglio Contratto, Rinnovi & Incassi e
  Cassa senza ownership lessicale sufficientemente netta.
- `Oggi` e `Dashboard` competono come home operativa.
- La ricerca Clienti non include il telefono, chiave frequente nel lavoro reale.
- Accenti blue/violet/rose/emerald sulle aree core divergono dalla grammatica teal + colori semantici
  ratificata nel `MANIFESTO.md`.

Modello mentale proposto alla SPEC, senza cambiare il dominio:

| Superficie | Domanda primaria |
|---|---|
| Cliente | Qual è la situazione e il prossimo passo? |
| Contratto | Qual è l'accordo e come sta evolvendo? |
| Rinnovi & Incassi | Quale azione amministrativa devo compiere adesso? |
| Cassa | Cosa è entrato/uscito e come controllo il registro? |
| Agenda | Cosa è previsto, quando e con quale relazione? |

### 3.5 Performance e affidabilità percepita

| ID | Severità | Finding | Evidenza primaria |
|---|---|---|---|
| A-12 | Alto | Clienti e Contratti limitati a 200 record e filtrati client-side: risultati/KPI incompleti oltre soglia | `frontend/src/hooks/useClients.ts:27-34`, `useContracts.ts:31-38` |
| A-13 | Alto | Cassa, profilo Cliente e dettaglio Contratto importano eager tab/dialog/grafici non visibili | `cassa/page.tsx:38-76`, `clienti/[id]/page.tsx:22-35`, `contratti/[id]/page.tsx:34-48` |
| A-14 | Medio-alto | Mutation finanziarie invalidano molte famiglie e possono produrre refetch storm/flicker | `useRates.ts:54-61`, `useContracts.ts:101-109`, `useAgenda.ts:129-133` |
| A-15 | Medio | Profilo cliente carica dataset completi per ricavare pochi booleani | `clienti/[id]/page.tsx:56-60,102-126` |
| A-16 | Medio | Agenda carica tutti i Todo e calcola scaduti/oggi client-side | `useTodos.ts:20-29`, `agenda/page.tsx:97-120` |

## 4. Decisione di fold-back

L'audit non autorizza un redesign trasversale. I finding sono divisi nella SPEC viva in gate ordinati:

1. integrità percettiva e privacy;
2. accessibilità dei flussi core e money-path;
3. modello mentale e ownership delle superfici;
4. scalabilità/performance;
5. distintività verificata con test LIVE.

Le regole di dominio finanziario restano quelle di ADR-014..025 e dei relativi SSoT. Qualunque
intervento che richieda nuova semantica, nuova transizione o nuovo calcolo monetario esce dalla SPEC e
richiede governance dedicata.

