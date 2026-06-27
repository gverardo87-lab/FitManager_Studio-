# SPEC_G7.7-R5 — Trasparenza e Azioni Frontend

**Tipo:** specifica prescrittiva (frontend-only, bridge Chat→Code).
**Data:** 2026-06-27.
**Stato:** ✅ **IMPLEMENTATA** (2026-06-27) e archiviata come design-record.
**Origine:** audit frontend di dettaglio sul flusso contratti dopo G7 e R4+R5; tre finding confermati sul codice vivo il 2026-06-27.
**SSoT di dominio:** `FINANCIAL_DOMAIN_MODEL.md` · `TASSONOMIA_FINANZIARIA.md` · `SPEC_VOCABOLARIO_E_CLASSIFICAZIONE_CONTRATTI.md` · `SPEC_G7.3_TERMINAZIONE_ENDPOINT.md` · `SPEC_RINVIO_LIBERA_CREDITO.md` (solo come contesto del filone).
**Verifica finale:** `next build` verde + verifica visiva founder su ambiente dev 8000/3000.
**Vincolo metodologico:** la ground truth e' il codice reale; se diverge da questa spec, vince il codice e la spec va corretta prima di implementare.

> Questa spec NON apre un nuovo filone di dominio. E' una remediation locale del consumo frontend di campi e azioni gia' esistenti. Nessun backend, nessuna nuova semantica finanziaria, nessun nuovo calcolo lato client.

---

## 0. Tesi unica (falsificabile)

> **T1 — la trasparenza deve restare locale e visibile su ogni superficie principale del contratto.**
>
> Se la UI comunica una remediation o una distinzione operativa sul contratto, allora:
> 1. la superficie che la comunica deve offrire anche il punto d'ingresso locale all'azione corrispondente, oppure una microcopy che non prometta un'azione assente;
> 2. i segnali di trasparenza introdotti da R5 (`crediti`, `svolte`, `prenotate non svolte`) devono restare visibili anche sotto `lg`, senza costringere il trainer ad aprire il dettaglio e senza peggiorare il layout desktop;
> 3. la modifica generica di `data_scadenza` non deve cambiare implicitamente il comportamento lifecycle di un contratto aperto senza che il trainer capisca cosa significa `oggi` vs `passato`.

La tesi e' falsificata se si verifica anche solo uno di questi casi:
- il dettaglio contratto mostra il banner M4 ma da quella pagina non esiste un path locale coerente per `Riapri` o `Termina`;
- sotto `lg` la lista contratti perde i segnali `svolte` / `prenotate non svolte` introdotti da R5;
- il form di modifica accetta `data_scadenza` odierna o passata senza chiarire che `oggi` non sospende subito mentre una data passata rende il contratto immediatamente scaduto;
- la remediation introduce nuovi calcoli client-side al posto di leggere i campi SSoT gia' esposti dal backend.

---

## 1. Problema osservato (code-grounded)

### 1.1 — Scheda dettaglio: microcopy vera ma non azionabile localmente

Il dettaglio contratto mostra nel hero il banner M4 (`sedute prenotate non erogate alla chiusura`) e la microcopy indica il percorso `Riapri -> Termina`.

Problema: sulla pagina dettaglio le azioni disponibili sono oggi solo `Modifica` ed `Elimina`. Le azioni lifecycle esistono altrove nel prodotto (lista contratti / worklist), ma non sulla superficie che espone il banner.

Conseguenza UX:
- la scheda dettaglio e' la superficie naturale di drill-down per capire il caso anomalo;
- il trainer vede la spiegazione ma non il comando corrispondente;
- il banner si comporta come dead-end locale.

### 1.2 — Lista contratti: la trasparenza R5 sparisce sui breakpoint stretti

La lista contratti mostra `crediti`, `svolte` e `prenotate non svolte` solo nella colonna `Crediti`, che e' nascosta sotto `lg`.

Conseguenza UX:
- su tablet/mobile il trainer perde proprio il pezzo di trasparenza introdotto per risolvere la segnalazione di Chiara;
- la lista principale torna a essere opaca proprio dove il layout si restringe;
- il problema non e' di dominio ma di consumo responsive del dato gia' corretto.

### 1.3 — Modifica contratto: la sospensione manuale via `data_scadenza` e' implicita e semanticamente opaca

Oggi il form di modifica contratto consente di impostare `data_scadenza` a una data passata purche' resti dopo `data_inizio`.
Il backend accetta l'update e lo stato di vita si ri-deriva dal SSoT in base alla regola temporale gia' attiva:

- `data_scadenza == oggi` -> il contratto resta **vigente** fino a fine giornata (`is_scaduto = scadenza < today`)
- `data_scadenza < oggi` -> il contratto diventa immediatamente **scaduto** e quindi compare come `SOSPESO` o `ESAURITO` a seconda dei crediti residui

Lacuna reale:
- la UI non spiega la differenza fra `oggi` e `passato`;
- la retrodatazione della scadenza agisce come leva lifecycle implicita dentro un form generico di modifica;
- il trainer puo' credere di "sospendere ora" impostando oggi, ma il modello non funziona cosi';
- il trainer puo' rendere un contratto immediatamente scaduto con una semplice modifica data senza guardrail esplicito.

Nota di confine: sul backend l'update oggi registra solo il diff campo-per-campo, non una transizione lifecycle dedicata. E' una lacuna tecnica vera, ma NON entra in questa spec: qui si presidia la superficie frontend senza cambiare il modello o l'audit server-side. Il follow-up backend e' stato isolato come task separato.

---

## 2. Decisioni vincolanti di superficie

### 2.1 — La scheda dettaglio diventa azionabile nel proprio header

Le azioni lifecycle del contratto devono essere disponibili anche nella scheda dettaglio.

Decisione:
- il punto d'ingresso sta nell'header pagina del dettaglio contratto, non dentro il hero;
- il hero resta superficie informativa, non diventa action bar;
- l'header ospita le stesse azioni gia' esistenti nel flusso (`Termina`, `Riapri`, `Incassa residuo`) secondo le stesse guardie di disponibilita'.

Razionale:
- coerente con l'header gia' esistente (`Modifica`, `Elimina`);
- evita di trasformare il hero in un contenitore misto KPI + CTA;
- mantiene la remediation locale alla superficie che espone il problema.

### 2.2 — Sotto `lg` si usa un summary compatto, non una nuova colonna

Per la lista contratti sotto `lg` la soluzione canonica e' un `summary` nella cella `Cliente`, non una nuova colonna responsive.

Decisione:
- desktop `lg+`: la colonna `Crediti` resta la sede primaria della trasparenza R5;
- mobile/tablet `< lg`: la cella `Cliente` ospita un summary secondario compatto con i segnali R5;
- non si aggiunge una nuova colonna dedicata per i breakpoint stretti.

Razionale:
- una colonna extra su viewport stretti peggiora densita', overflow e scansione;
- il summary preserva l'informazione senza rompere la struttura tabellare esistente;
- il desktop non va toccato se non per evitare duplicazioni.

### 2.3 — Stesse guardie, stessi dialog, zero semantica nuova

Le azioni del dettaglio devono riusare i dialog e le mutation gia' esistenti:
- `TerminateContractDialog`
- `ReopenContractDialog`
- `IncassaResiduoDialog`

Le guardie di visibilita' devono essere semanticamente identiche a quelle gia' in uso nella lista contratti.

Vincolo non negoziabile:
- nessuna reimplementazione di logica di dominio o di calcolo importi;
- nessun branching nuovo sul backend;
- nessuna nuova semantica dei badge o dei lifecycle.

### 2.4 — La retrodatazione della scadenza diventa un gesto esplicito, non silenzioso

Decisione:
- il form di modifica NON blocca in assoluto la retrodatazione della scadenza;
- `data_scadenza == oggi` mostra una nota esplicita: il contratto resta vigente fino a fine giornata, quindi non entra subito in `SOSPESO` / `ESAURITO`;
- `data_scadenza < oggi` su un contratto oggi aperto/vigente richiede una conferma esplicita prima del salvataggio;
- la conferma non predice client-side il lifecycle finale con nuova logica: dichiara che il contratto diverra' immediatamente **scaduto** e che lo stato reale verra' derivato dal sistema in base ai crediti residui.

Razionale:
- si preserva il modello esistente (`scade oggi` = ancora vigente);
- si evita che una data passata agisca come sospensione implicita senza consenso chiaro;
- non si introduce un nuovo concetto di dominio (`sospendi`) dove oggi esiste solo uno stato derivato da tempo + crediti.

---

## 3. Inventario dei siti

### 3.1 — Siti da CAMBIARE

| File | Ruolo | Cosa deve cambiare |
|------|------|--------------------|
| `frontend/src/app/(dashboard)/contratti/[id]/page.tsx` | shell dettaglio contratto | aggiunge entry-point locali `Termina` / `Riapri` / `Incassa residuo` nell'header e monta i dialog corrispondenti |
| `frontend/src/components/contracts/ContractFinancialHero.tsx` | hero informativo dettaglio | mantiene il banner M4 ma con copy coerente al fatto che l'azione e' disponibile nella stessa pagina |
| `frontend/src/components/contracts/ContractsTable.tsx` | lista contratti | preserva i segnali R5 sotto `lg` tramite summary nella cella `Cliente`, lasciando invariata la colonna `Crediti` su `lg+` |
| `frontend/src/components/contracts/ContractForm.tsx` | form modifica contratto | aggiunge guardrail semantico su `data_scadenza == oggi` vs `data_scadenza < oggi` |
| `frontend/src/components/contracts/ContractSheet.tsx` | wrapper salvataggio form | ospita, se necessario, la conferma esplicita prima di salvare una retrodatazione che rende il contratto immediatamente scaduto |

### 3.2 — Siti che possono essere TOCCATI solo per convergenza tecnica

| File | Ruolo | Vincolo |
|------|------|---------|
| `frontend/src/components/contracts/TerminateContractDialog.tsx` | dialog terminate | nessun cambio di semantica; al massimo adattamenti minimi di copy o wiring se il dettaglio richiede props gia' disponibili |
| `frontend/src/components/contracts/ReopenContractDialog.tsx` | dialog reopen | nessun cambio di semantica |
| `frontend/src/components/contracts/IncassaResiduoDialog.tsx` | dialog G6 | nessun cambio di semantica |

### 3.3 — Siti da LASCIARE invariati

| File | Perche' resta |
|------|---------------|
| `frontend/src/components/clients/profile/ContrattiTab.tsx` | il profilo e' gia' allineato a R5 sul piano informativo; non e' il punto dove oggi si perde la trasparenza |
| `frontend/src/lib/contract-status.tsx` | vocabolario SSoT di badge; fuori scope |
| `frontend/src/hooks/useContracts.ts` | mutation e invalidation gia' corrette; da riusare, non da ridefinire |

---

## 4. Regole di implementazione

### 4.1 — Dettaglio contratto

Il dettaglio contratto deve esporre queste azioni in header:
- `Termina` quando il contratto NON e' chiuso;
- `Riapri` quando il contratto e' chiuso;
- `Incassa residuo` solo quando il contratto e' aperto e il residuo e' incassabile secondo la stessa logica gia' usata nella lista.

Vincoli:
- `Termina` e `Riapri` sono mutuamente esclusivi;
- `Incassa residuo` puo' convivere con `Termina` solo nei casi gia' previsti dal flusso G6/G7;
- nessun nuovo dialog: si riusano quelli esistenti;
- l'ordine visivo deve restare compatibile con le azioni gia' presenti (`Modifica`, `Elimina`).

### 4.2 — Microcopy del hero

Il banner M4 del hero non deve piu' comportarsi come istruzione che rimanda a un'azione assente.

Vincolo:
- la copy deve rendere chiaro che il trainer puo' eseguire l'azione dalla scheda stessa;
- il banner NON introduce un bottone interno se l'header fornisce gia' il punto d'ingresso;
- il banner resta un segnale di riconciliazione, non una seconda toolbar.

### 4.3 — Summary responsive nella lista

Sotto `lg`, la lista contratti deve rendere visibili nella cella `Cliente` i tre segnali chiave:
- `crediti_usati / crediti_totali`
- `N svolte`
- `N prenotate non svolte` solo se `sedute_non_erogate_chiusura > 0`

Vincoli:
- il blocco summary esiste solo sotto `lg`;
- su `lg+` non devono comparire duplicati dei contenuti gia' presenti nella colonna `Crediti`;
- il summary usa solo i campi backend gia' esposti (`crediti_usati`, `crediti_totali`, `sedute_completate`, `sedute_non_erogate_chiusura`), zero derivazioni nuove.

### 4.4 — Guardrail sul form di modifica (`data_scadenza`)

Il form di modifica contratto deve distinguere esplicitamente tre casi:

1. `data_scadenza` futura
   - nessun guardrail speciale oltre alle validazioni gia' esistenti.

2. `data_scadenza == oggi`
   - mostra una nota informativa non distruttiva;
   - la copy deve dichiarare che il contratto resta vigente fino a fine giornata;
   - la UI NON deve suggerire che `oggi` equivalga a sospensione immediata.

3. `data_scadenza < oggi`
   - su un contratto oggi **aperto/vigente** mostra un warning forte;
   - il submit richiede una conferma esplicita solo se l'edit attraversa davvero il confine `vigente -> scaduto`;
   - la conferma deve dire che il contratto risultera' immediatamente **scaduto**;
   - la conferma non deve ricalcolare o promettere client-side se il badge finale sara' `SOSPESO` o `ESAURITO`: quel risultato resta derivato dal SSoT backend.

Vincoli:
- il guardrail vale sul path di **edit** del contratto, non sulla creazione;
- non si introduce un nuovo endpoint `suspend`;
- non si cambia la regola di dominio `is_scaduto = data_scadenza < today`.

---

## 5. Acceptance criteria

### AC-1 — Azione locale sul dettaglio

Aprendo un contratto dalla lista o dal profilo, la scheda dettaglio offre un path locale coerente per il lifecycle:
- contratto aperto -> bottone `Termina` visibile;
- contratto chiuso -> bottone `Riapri` visibile;
- contratto con residuo incassabile -> bottone `Incassa residuo` visibile.

Falsificabile: il trainer vede il banner o i dati lifecycle ma deve tornare alla lista per agire.

### AC-2 — Banner M4 non piu' dead-end

Se `sedute_non_erogate_chiusura > 0`, il banner M4 del dettaglio non promette piu' un percorso assente dalla pagina.

Falsificabile: la copy dice `Riapri -> Termina`, ma sulla pagina non esiste il relativo entry-point.

### AC-3 — Trasparenza preservata sotto `lg`

Sotto `lg`, ogni riga della lista contratti continua a mostrare almeno:
- occupazione crediti,
- numero di sedute svolte,
- indicatore amber delle prenotate non svolte se presente.

Falsificabile: riducendo il viewport sotto `lg`, i segnali R5 spariscono completamente.

### AC-4 — Desktop invariato

Su `lg+` la colonna `Crediti` resta la sede primaria della trasparenza. Il nuovo summary responsive non compare e non genera duplicazioni.

Falsificabile: su desktop si vedono gli stessi dati sia nella colonna `Cliente` sia nella colonna `Crediti`.

### AC-5 — Zero nuova logica di dominio

L'intervento resta frontend-only e non introduce calcoli nuovi su lifecycle, soldi o crediti.

Falsificabile: compare un nuovo helper che ricalcola `svolte`, `non svolte`, `residuo` o la disponibilita' delle azioni partendo da formule nuove invece di leggere i campi gia' esposti.

### AC-6 — Wiring riusato, invalidation invariata

Le azioni del dettaglio riusano i dialog e le hook/mutation esistenti. Nessuna nuova mutation e nessuna nuova invalidation key.

Falsificabile: nasce una seconda implementazione di `terminate`, `reopen` o `incassa residuo` per il dettaglio.

### AC-7 — Semantica chiara su `oggi`

Nel form di modifica, impostando `data_scadenza == oggi`, il trainer vede esplicitamente che il contratto non entra subito in stato scaduto.

Falsificabile: la UI lascia intendere che `oggi` sospenda immediatamente il contratto.

### AC-8 — Retrodatazione non silenziosa

Nel form di modifica, impostando `data_scadenza < oggi` su un contratto oggi aperto/vigente, il trainer deve confermare esplicitamente il salvataggio.

Falsificabile: una retrodatazione che rende il contratto immediatamente scaduto passa con un normale submit senza warning o conferma.

### AC-8b — Nessun falso positivo sui gia' scaduti

Se il contratto e' gia' scaduto e l'edit cambia `data_scadenza` da una data passata a un'altra data passata, la UI non deve aprire la stessa conferma di crossing `vigente -> scaduto`.

Falsificabile: un contratto gia' `SOSPESO` o `ESAURITO` richiede la conferma "diventera' immediatamente scaduto" anche quando resta gia' scaduto.

### AC-9 — Gate minimo eseguibile

`next build` deve restare verde.

---

## 6. Piano di verifica

### 6.1 — Verifica eseguibile

- `cd frontend && npx next build`

### 6.2 — Verifica manuale mirata

1. Contratto chiuso con `sedute_non_erogate_chiusura > 0`
   - apri la scheda dettaglio;
   - verifica banner M4;
   - verifica presenza di `Riapri` nella stessa pagina.

2. Contratto aperto terminabile
   - apri la scheda dettaglio;
   - verifica presenza di `Termina`;
   - apri il dialog e verifica che sia il dialog canonico G7.3.

3. Contratto sospeso/esaurito con residuo incassabile
   - apri la scheda dettaglio;
   - verifica presenza di `Incassa residuo`;
   - apri il dialog e verifica che sia il dialog canonico G6.

4. Lista contratti sotto `lg`
   - riduci il viewport;
   - verifica che `crediti`, `svolte` e l'eventuale segnale amber restino visibili in riga.

5. Lista contratti su `lg+`
   - verifica che non ci siano duplicazioni tra `Cliente` e colonna `Crediti`.

6. Modifica contratto con `data_scadenza == oggi`
   - apri il form di modifica di un contratto aperto/vigente;
   - imposta la scadenza a oggi;
   - verifica che la UI dichiari esplicitamente che il contratto resta vigente fino a fine giornata.

7. Modifica contratto con `data_scadenza < oggi`
   - apri il form di modifica di un contratto aperto/vigente;
   - imposta la scadenza a ieri;
   - verifica warning + conferma esplicita prima del salvataggio.

8. Modifica contratto gia' scaduto con `data_scadenza < oggi`
   - apri il form di modifica di un contratto gia' `SOSPESO` o `ESAURITO`;
   - cambia la scadenza da una data passata a un'altra data passata;
   - verifica che NON compaia la stessa conferma di crossing `vigente -> scaduto`.

---

## 7. Confini espliciti

### 7.1 — Cosa NON toccare

- nessun endpoint backend;
- nessuna semantica di `motivo_chiusura`, `lifecycle`, `money_substate` o `residuo`;
- nessuna modifica alla regola SSoT `scade oggi = ancora vigente`, `scadenza passata = scaduto`;
- nessun cambio al vocabolario badge SSoT;
- nessuna modifica a `ContrattiTab` del profilo se non emerge un difetto reale durante l'implementazione;
- nessun nuovo documento ADR: non c'e' una decisione architetturale o di dominio, solo una remediation di superficie.
- nessun hardening backend dell'audit lifecycle in `update_contract` dentro questa spec: il follow-up dedicato e' stato isolato come task separato.

### 7.2 — Rischio principale

Il rischio non e' tecnico di dominio ma di deriva UX:
- duplicare contenuti su desktop;
- introdurre nel dettaglio un secondo pattern di azioni incoerente con la lista;
- ricopiare la guardia `residuo incassabile` in due posti e farle divergere nel tempo;
- trasformare la retrodatazione della scadenza in una pseudo-azione di sospensione senza semantica chiara.

Mitigazione:
- un solo pattern action-level per il dettaglio;
- summary solo sotto `lg`;
- guardie semanticamente allineate alla lista esistente;
- conferma esplicita per la retrodatazione e nota chiara sul significato di `oggi`.

---

## 8. Condizione di archiviazione

Questa spec esce da `docs/technical/` quando sono veri tutti e tre i punti:
- il dettaglio contratto espone le azioni lifecycle locali richieste da AC-1;
- la lista contratti preserva i segnali R5 anche sotto `lg` (AC-3/AC-4);
- il form di modifica presidia `data_scadenza == oggi` vs `data_scadenza < oggi` secondo AC-7/AC-8;
- `next build` e la verifica manuale mirata sono stati eseguiti e registrati nel `BUILD_LOG.md`.

Una volta chiusa, la spec va archiviata in `docs/archive/specs/` come design-record del follow-up G7.7-R5.