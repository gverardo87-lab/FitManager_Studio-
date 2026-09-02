# SPEC — Vocabolario e classificazione degli stati contratto (SSoT su tutte le superfici)

**Versione:** 1.1
**Stato:** Vincolante sui criteri di accettazione — **silente sull'implementazione** (Claude Code è l'architetto nel codebase). ✅ **Giro 1 IMPLEMENTATO** (`91cbc39`): `is_insolvente` SSoT, lista/dettaglio `/contratti` derivano lo stato dal SSoT, modulo `lib/contract-status.tsx`, delega residuo. **⏳ Giro 2 PENDENTE:** `rinnovi-incassi` + `workspace_engine` off-SSoT + grep-guard.
**Owner:** Giacomo Verardo (AVGV Technologies)
**Destinatario:** Claude Code
**Collocazione:** `docs/specs/` (lavoro aperto; a chiusura → `docs/archive/specs/`)
**Data:** 2026-06-22
**Modello di dominio (SSoT):** `FINANCIAL_DOMAIN_MODEL.md` v1.3 (§2 assi, §3 stati di vita, §5 sotto-stato denaro, §10 regola d'oro) + `api/services/contract_state.py`
**Applica il principio di:** `TASSONOMIA_FINANZIARIA.md` §5 («lo stesso concetto usi la stessa etichetta in ogni superficie») ai label di **stato di vita** e **sotto-stato denaro**. *Non* chiude la tabella naming dell'asse cassa di §5 (incassi netti / rimborsi / venduto / …), che resta debito aperto di quel documento.
**Coordina con:** `IMPL_PLAN_FINANCIAL_REALIGN.md` §4.7 (anti-pattern inline-residuo) — vedi Giro 2. **NB:** la delega-residuo del §2.2 **anticipa il BLOCKER #1 di G7** (residuo→SSoT), non lo duplica (vedi §7).

> **Nota di versione 1.1 (2026-06-22, assorbita la review code-grounded di Claude Code — workflow 9 agenti su codice vivo).**
> La v1.0 è stata verificata claim-per-claim contro il codice reale: **la diagnosi regge interamente** (cascata
> `getPaymentBadge`, collasso a 2 stati, 3 ricalcoli di `is_scaduto`, SSoT che espone già tutto il necessario,
> §4.7 che omette i 3 siti del `workspace_engine`). La v1.1 **chiude 3 gap HIGH** che la stesura a fonte-codice-chiusa
> non poteva vedere — con **decisioni di Giacomo**: (G1) il segnale di riga scatta **anche su ATTIVO con rate scadute**
> (il caso "Rate in Ritardo" non perde visibilità — §2.5/§2.6); (G2) l'insolvenza si segnala con **icona +
> `aria-label` + opacità alzata**, mai col solo colore (regola `frontend/CLAUDE.md`) — **niente badge testuale**,
> §4.2 preservato; (G3) i nodi della catena rinnovi (`RenewalChainLink`) ricevono il **proprio `lifecycle`**
> (estensione di `RenewalChainItem`, §2.7). **Corregge imprecisioni** (8 rami non 7 in `getPaymentBadge`; le 3
> definizioni di "insolvente" sono su **2 file**; `financial.py:274` è un commento-doc, non un calcolo; AC-4/AC-5;
> drift righe ~+1) e **aggiunge AC** (esclusività `is_insolvente`/`in_scadenza`; non-regressione + KPI cumulativi
> pitfall #14; edge `prezzo_totale=null`; percepibilità senza colore). Riposiziona il grep-guard da "CI" (inesistente)
> a `check-all.sh` con allowlist, e **estende il censimento** dei siti inline-residuo (anche `dashboard.py` senza clamp).
> **Nuovo §7 (bridge esteso):** registra la convergenza con G7 e il puntatore "insolvente" da far atterrare nel FDM.

> **Perché esiste.** Il SSoT (`contract_state.py`) modella già **correttamente** lo stato del contratto
> su due assi ortogonali (vita × denaro, FDM §2/§3/§5). Ma **nessuna superficie frontend lo consuma per
> classificare**: la pagina contratti, la scheda dettaglio, `rinnovi-incassi` e il workspace engine
> **reimplementano** la classificazione ognuna a modo suo, con un vocabolario diverso. Risultato: lo
> stesso contratto ha **nomi diversi a un click di distanza**, e la stessa pagina si **autocontraddice**
> (il KPI in alto sa che un contratto è SOSPESO, la riga sotto lo chiama "Attivo"). Questa spec impone
> **una fonte sola** — di numeri **e** di nomi — esattamente come §4.7 ha imposto `contract_state.residuo()`
> come fonte unica del residuo. È "fare ordine": un asse vita, un asse denaro, flag derivati per
> l'attenzione, tutti dal SSoT, ciascuno con **definizione unica**.

---

## 0. Principio guida (macro prima del micro)

Tre regole, da cui discende tutto il resto:

1. **Un asse vita, un asse denaro — mai fusi.** Un contratto ha **uno** stato di vita (ATTIVO / SOSPESO
   / ESAURITO / CHIUSO) **e**, contemporaneamente, **uno** sotto-stato denaro (saldato / da pianificare /
   …). Sono **ortogonali** (FDM §2/§5): non vanno mai compressi in un'unica etichetta a cascata, perché
   comprimerli **distrugge informazione** (vedi §1, difetto C).
2. **Tutto derivato dal SSoT, mai ricalcolato per-vista.** Stato di vita, sotto-stato denaro, "scaduto",
   "in scadenza", "insolvente": ogni classificazione la produce `contract_state.py` **una volta**, il
   backend la attacca alla riga, il frontend la **legge**. Regola d'oro FDM §10, estesa dai numeri ai
   **nomi**.
3. **Insolvente è un FLAG DERIVATO, non un quinto stato.** "Insolvente" = scaduto **e** con rate scadute:
   è una **combinazione** dei due assi, non una categoria propria (specularmente a come CHIUSO è
   qualificato dal motivo ma non genera un quinto stato, FDM §3.1). Vive come **predicato del SSoT** e
   come **segnale di attenzione sulla riga**, mai come badge che compete con gli assi.

> **Invariante di non-regressione del modello.** Questa spec **non introduce nuovi stati di dominio**:
> `is_insolvente` e `in_scadenza` sono **derivazioni** di stati già definiti. Il FDM §3 resta a 4 stati
> di vita + ELIMINATO. Nessuna modifica al modello di dominio — solo al *consumo* del modello.

---

## 1. Diagnosi — i tre difetti da rimuovere (con evidenza sul codice)

### Difetto A — collasso a 2 stati (`attivo = !chiuso`), vietato dal FDM §4
Il frontend deriva lo stato di vita come `c.chiuso ? "chiusi" : "attivi"`, cancellando SOSPESO ed
ESAURITO che il backend **calcola e conta separatamente**.
- `contratti/page.tsx`: `const statoKey = c.chiuso ? "chiusi" : "attivi"` + `STATO_CHIPS` a 2 voci.
- `contratti/[id]/page.tsx`: `contract.chiuso ? "Chiuso" : "Attivo"` in **tre** punti (header badge,
  `RenewalChainLink`, riga "Stato" del tab Dettagli).
- **Conseguenza:** un SOSPESO mostra badge verde "Attivo" nella scheda, mentre `rinnovi-incassi` lo
  chiama "Sospeso da N giorni". Il KPI `kpi_attivi` (corretto, deriva da `contract_lifecycle`) e la
  tabella sotto si **contraddicono**.

### Difetto B — quattro ricalcoli paralleli di `is_scaduto`
`is_scaduto` esiste nel SSoT, e il frontend lo reimplementa con `differenceInDays(parseISO(...)) < 0` in:
`contratti/page.tsx` (`matchesSituazione`), `ContractsTable.tsx` (`getPaymentBadge` **e** `getScadenzaStyle`),
e — lato backend — `workspace_engine.py` (vedi Giro 2). Quattro derivazioni dello stesso asse tempo.

### Difetto C — i due assi fusi in una cascata che distrugge informazione
`ContractsTable.getPaymentBadge` è il vero motore di classificazione: una colonna intitolata "Rate" con
**8 rami a priorità** (7 `if` condizionali + 1 default) che mescola asse vita e asse denaro in un badge solo:
`Chiuso` (vita) → `Insolvente` (vita+denaro) → `Rate in Ritardo` (denaro) → `Scaduto` (vita) → `Saldato`
(denaro) → `In corso` (denaro) → `Piano mancante` (denaro) → `Nessuna rata` (default). Il primo match vince
→ **un SOSPESO saldato mostra "Scaduto" e l'informazione "saldato" sparisce**; un ESAURITO con rate a posto
mostra "Scaduto" e non sai se ti deve denaro. *(NB: il docstring dello stesso file dichiara "7 livelli" ma è
a sua volta stale — ne omette uno. Il conteggio reale verificato sul codice è 8.)*
- **Tre definizioni divergenti di "insolvente", distribuite su DUE file** (non in uno solo): chip FilterBar
  (`ha_rate_scadute && isExpired && !chiuso`, in `contratti/page.tsx::matchesSituazione`), badge tabella
  (`ha_rate_scadute && isExpired`, in `ContractsTable.tsx`), e "Rate in Ritardo"
  (`ha_rate_scadute` senza scaduto, in `ContractsTable.tsx` — terzo *trattamento* divergente dello stesso
  flag, non una terza etichetta testuale "Insolvente"). Quando lo stesso concetto ha tre definizioni, non
  è una primitiva: è una **vista da derivare una volta**.

---

## 2. GIRO 1 — Unificazione su `/contratti` + scheda dettaglio + backend

> Ordine vincolante: **backend-first**. Ogni passo è verde (test) prima del successivo. I campi backend
> sono **additivi e retro-compatibili**: `rinnovi-incassi` e `workspace_engine` continuano a funzionare
> identici durante questo giro (non si toccano — vedi Giro 2).

### 2.1 SSoT — un predicato nuovo in `contract_state.py`
Aggiungere `is_insolvente(state: ContractState) -> bool`, **gemello** di `is_rate_planificabile` e
`is_residuo_incassabile_diretto` già presenti. Definizione **unica e vincolante**:

> *insolvente* ⟺ `lifecycle ∈ {SOSPESO, ESAURITO}` **AND** `rate_scadute` (entrambi già prodotti da
> `evaluate_contract`).

Nessun'altra modifica al SSoT: `evaluate_contract` espone già `lifecycle`, `money`, `residuo`,
`crediti_residui`, `rate_scadute`, `in_scadenza`.

> **`rate_scadute` (SSoT) è la fonte UNICA di "denaro arretrato".** `is_insolvente` è il **sotto-caso
> scaduto** (`lifecycle ∈ {SOSPESO,ESAURITO}`) di un segnale più ampio: *avere rate scadute*. Lo stesso
> `rate_scadute` accende il **segnale di riga anche su un ATTIVO** (rate arretrate su contratto vigente — il
> vecchio "Rate in Ritardo", §2.5/§2.6, gap G1). Un SOSPESO/ESAURITO con rate scadute è **insolvente**; un
> ATTIVO con rate scadute è **in ritardo** ma non insolvente (non è scaduto): due nomi, **un solo predicato
> sorgente**.
>
> **⚠️ Riconciliazione di "rate scadute" (chiude una divergenza residua).** Esistono oggi DUE definizioni:
> il campo-riga `ha_rate_scadute` (`contracts.py`, *larga*: `Rate.data_scadenza < oggi OR Contract.data_scadenza
> < oggi`, Contract-Integrity #11) e il SSoT `has_rate_scadute` (*stretta*: la **rata** stessa scaduta). I
> guard di integrità #9/#10 le tengono **di fatto equivalenti** (una rata non può essere datata oltre la
> scadenza del contratto), ma sopravvivono come **due formule** — esattamente il debito che questa spec
> esiste per eliminare (Invariante §5.1). **Decisione:** un solo predicato — il SSoT `rate_scadute` di
> `evaluate_contract` — alimenta sia `is_insolvente` sia il flag-riga sia il filtro Situazione; `ha_rate_scadute`
> sul wire o viene **derivato dal SSoT** o documentato come suo alias equivalente. Niente seconda formula viva.

**AC-1.** Esiste `is_insolvente` come funzione pura nel SSoT. Test: un ESAURITO con rata scaduta → `True`;
un ATTIVO con rata scaduta → `False` (non scaduto ⇒ non insolvente, ma **flag-riga "in ritardo" acceso**, §2.5);
un SOSPESO senza rate scadute → `False`; un CHIUSO → `False`.
**AC-1b.** Il campo "rate scadute" esposto sulla riga e usato dal filtro Situazione deriva dal **SSoT
`rate_scadute`** (un'unica formula). Test: la popolazione del filtro "Rate scadute" coincide con quella
calcolata da `evaluate_contract().rate_scadute`, senza una seconda definizione inline.

### 2.2 Backend — `list_contracts` e `get_contract` attaccano gli assi derivati alla riga
Ogni item esposto porta **quattro campi derivati** dallo **stesso** `evaluate_contract` (i `crediti_usati`
sono già in `credits_used_map`, le `rates` in `rates_by_contract` → zero query nuove):

| Campo | Tipo wire | Sorgente SSoT |
|---|---|---|
| `lifecycle` | `"attivo"\|"sospeso"\|"esaurito"\|"chiuso"` | `contract_lifecycle().value` |
| `money_substate` | `"saldato"\|"da_pianificare"\|"parziale"\|"pianificato"` | `money_substate().value` |
| `is_insolvente` | `bool` | `is_insolvente(state)` |
| `in_scadenza` | `bool` | `state.in_scadenza` (ATTIVO entro `SOGLIA_IN_SCADENZA_GG`) |

`is_insolvente` e `in_scadenza` sono **mutuamente esclusivi per costruzione** (uno è scaduto, l'altro è
ATTIVO-non-scaduto): non possono accendersi insieme. *(Verificato sul codice: `in_scadenza` si accende solo
se `lifecycle == ATTIVO`, `contract_state.py`; `is_insolvente` richiede `SOSPESO/ESAURITO`. Asserito in AC-2b.)*

**Consolidamento gratuito (siamo già nel file):** `_to_response_with_rates` (sito reale **`contracts.py:128`**,
non :127 — drift di una riga) calcola `residuo` inline (`round(max(0, prezzo − versato), 2)`). **Delegare a
`contract_state.residuo()`** — il MANDATORY-fix del §4.7 (`importo_da_rateizzare` ≈`:131` e `disallineamento`
≈`:132` ereditano la correzione). `cstate` è **già importato** in `contracts.py` → la delega è un one-liner a
**zero cambio comportamento oggi** (le due formule sono byte-identiche; la divergenza emerge solo post-G7, §7).
*(Nota: l'altra citazione che gira nell'inventario, `financial.py:274`, NON è un secondo calcolo — è il
**commento-doc** del campo `residuo` nello schema Pydantic. L'unico inline del percorso-dettaglio è `:128`.)*

**AC-2.** I KPI headline (`kpi_attivi/kpi_sospesi/kpi_esauriti`) e i campi-riga `lifecycle` derivano dalla
**stessa** `contract_lifecycle`: non possono divergere. Test: per ogni contratto, lo stato contato nel
KPI coincide col `lifecycle` della sua riga.
**AC-2b.** `is_insolvente` e `in_scadenza` non sono **mai** entrambi `True`. Test parametrico su tutte le
combinazioni di stato: `NOT (is_insolvente AND in_scadenza)`. (Blinda l'asserzione "mutuamente esclusivi per
costruzione", che oggi regge ma poggia su due funzioni separate.)
**AC-3.** `get_contract` (dettaglio) espone gli stessi quattro campi sull'oggetto `Contract`.
**AC-4.** Dopo il fix-residuo, `residuo` nel dettaglio coincide con `contract_state.residuo()`. **Oggi
identico su TUTTI i contratti** (aperti e chiusi: `quota_stornata` non esiste ancora) → la delega è un
refactor a comportamento-zero. La divergenza diventa load-bearing **con G7**, e si manifesterà proprio sui
**chiusi/terminati** (dove `residuo()` esteso sottrarrà `quota_stornata` — §7). Test: refactor a output invariato.
**AC-4b (non-regressione).** La suite backend resta verde e i **KPI cumulativi** (fatturato/incassato, che
**includono i contratti chiusi** — pitfall #14, INC-2026-06-08) restano **invariati**. Test di guardia:
`test_contract_integrity.py::test_kpi_fatturato_includes_closed_contracts` dopo le modifiche a `contracts.py`.

### 2.3 Tipo — `types/api.ts`
Introdurre i due union type canonici e i quattro campi **su `Contract` base** (NON solo su `ContractListItem`):
così propagano per ereditarietà sia a `ContractListItem` sia a `ContractWithRates` — la scheda dettaglio usa
`ContractWithRates extends Contract`, e mettendoli solo su `ContractListItem` la scheda resterebbe senza
`lifecycle` (AC-13 fallirebbe). **Inoltre (gap G3, §2.7):** estendere anche `RenewalChainItem` con `lifecycle`
(oggi porta solo `chiuso`), o i nodi della catena rinnovi non hanno la sorgente-dati per il badge SSoT.

```
export type ContractLifecycle = "attivo" | "sospeso" | "esaurito" | "chiuso";
export type ContractMoneySubstate = "saldato" | "da_pianificare" | "parziale" | "pianificato";
// + lifecycle, money_substate, is_insolvente, in_scadenza   (su Contract base)
// + lifecycle su RenewalChainItem
```
`useContracts` li propaga senza modifiche (già tipizzato su `ContractListResponse`).

**AC-5.** I union type rispecchiano i **4 valori esposti sul wire** degli enum SSoT `Lifecycle`/`MoneySubstate`.
*Precisazione:* l'enum `Lifecycle` ha **5** membri — il 5° è `ELIMINATO`, deliberatamente **fuori dal union**
perché i soft-deleted (`deleted_at != None`) sono filtrati da `list_contracts` e non raggiungono mai il wire.
Non aggiungere `"eliminato"` al union credendo di sanare una non-corrispondenza: l'esclusione è by-design.

### 2.4 Modulo naming — `lib/contract-status.ts` (il pezzo RIUSABILE, fonte unica del vocabolario)
**Solo mappatura `valore → presentazione`. ZERO logica di stato.** È il modulo che le tre superfici
condivideranno: lo si costruisce ora, lo si collauda su `/contratti` (il caso peggiore), e il Giro 2
diventa find-and-replace contro un modulo già validato.

Contenuto: `LIFECYCLE_BADGE: Record<ContractLifecycle, {label, className}>` e
`MONEY_BADGE: Record<ContractMoneySubstate, {label, className}>`, più i componentini
`<ContractLifecycleBadge lifecycle={…}/>` e `<ContractMoneyBadge money={…}/>`. Etichette IT canoniche
(chiudono TASSONOMIA §5): `attivo→"Attivo"`, `sospeso→"Sospeso"`, `esaurito→"Esaurito"`, `chiuso→"Chiuso"`.

**AC-6.** Il modulo non importa `date-fns` né calcola alcuno stato: mappa solo i valori-enum ricevuti.
**AC-7.** Le etichette di stato di vita usate ovunque nel frontend provengono da `LIFECYCLE_BADGE` (nessuna
stringa di stato hardcoded fuori dal modulo).

### 2.5 `ContractsTable.tsx` — due colonne pulite + riga "denaro arretrato" evidenziata
- **`getPaymentBadge` (8 rami a cascata) → ELIMINATA.**
- **Nuova colonna "Stato"** (asse vita): `<ContractLifecycleBadge lifecycle={c.lifecycle}/>`.
- **Colonna "Pagamenti"** (asse denaro): `<ContractMoneyBadge money={c.money_substate}/>`.
- **Segnale "denaro arretrato" = riga evidenziata + icona + `aria-label`, NIENTE badge testuale** (decisioni
  G1+G2, §4.2). Il trigger del segnale di riga è **`rate_scadute`** (SSoT, §2.1) — copre **entrambi**:
  - **insolvente** (`is_insolvente`: SOSPESO/ESAURITO con rate scadute), e
  - **in ritardo su ATTIVO** (`lifecycle==ATTIVO && rate_scadute` — il vecchio "Rate in Ritardo" che, senza
    questo, sparirebbe dalla lista: gap G1). *Un ATTIVO con la rata di marzo arretrata NON deve apparire sano.*

  Resa (gap G2 — la regola `frontend/CLAUDE.md` vieta lo stato comunicato col **solo** colore): la `TableRow`
  riceve (a) uno sfondo rosso **percepibile** (es. `bg-red-100 dark:bg-red-900/30` — NON il `bg-red-50/60
  dark:bg-red-950/20` quasi invisibile in dark mode), **resistente all'hover** esistente; (b) un'**icona
  `AlertTriangle`** accanto al badge Pagamenti; (c) un **`aria-label`** sulla `TableRow`. Niente etichetta
  testuale che finga di stare accanto ai due assi: l'attenzione resta un *segnale di riga*, non un terzo badge.
- **`getScadenzaStyle`**: rimuovere il ricalcolo `differenceInDays`. La colonna Scadenza mostra la data in
  stile **neutro** (decisione §4.1); l'urgenza la comunicano il badge **Stato** (Sospeso/Esaurito = scaduto)
  e il flag **`in_scadenza`** per gli ATTIVO prossimi a scadere (marcatore discreto). **Nessun gradiente
  temporale ricalcolato nel frontend.**

**AC-8.** Un SOSPESO saldato mostra **insieme** badge "Sospeso" (Stato) e "Saldato" (Pagamenti) — nessuna
informazione persa (il bug della cascata è chiuso). Test/verifica visiva su dato reale.
**AC-9.** Una riga con rate scadute è evidenziata e mostra comunque il suo stato di vita esatto e il suo
sotto-stato denaro (non più "Insolvente"/"Scaduto" che mascherano tutto).
**AC-9b (gap G1).** Un **ATTIVO con `rate_scadute`** riceve il segnale di riga (evidenziazione + icona),
pur restando badge Stato "Attivo": il pagamento in ritardo è visibile **in lista**, non solo via filtro.
**AC-9c (gap G2).** L'attenzione "denaro arretrato" è percepibile **senza distinguere il colore** (icona +
`aria-label`) **e in dark mode** (opacità verificata su sfondo scuro + hover). Test: snapshot/verifica visiva
in light e dark.
**AC-10.** `getPaymentBadge` non esiste più; nessun ramo di classificazione a cascata residuo nel file.

### 2.6 `contratti/page.tsx` — filtro Stato 2→4, Situazione riancorato al SSoT
- **`STATO_CHIPS` da 2 a 4 voci**: `Attivi · Sospesi · Esauriti · Chiusi`. Il filtro legge `c.lifecycle`.
  Sparisce `statoKey = c.chiuso ? "chiusi" : "attivi"`.
- **`matchesSituazione` riancorato** ai campi backend (il blocco Situazione **resta**, ma diventa onesto —
  legge il predicato del modello invece di reimplementarlo): `insolventi → c.is_insolvente`,
  `rate_scadute → c.rate_scadute` (il campo **derivato dal SSoT**, AC-1b — non una seconda formula),
  `saldati → c.money_substate === "saldato"`. Sparisce il ricalcolo inline di `isExpired`/`isSaldato`.
- **⚠️ Edge `prezzo_totale = null/0` (gap minore).** `residuo()` su prezzo assente → 0 → `money_substate ==
  "saldato"`: un contratto **senza termini economici** mostrerebbe badge verde "Saldato" (= "pagato"),
  semanticamente errato. Oggi la cascata lo intercetta col ramo "Nessuna rata". **Requisito:** un contratto
  con `prezzo_totale` nullo **non** mostra "Saldato" (nessun badge denaro, oppure label dedicata) e il filtro
  "Saldati" **non** lo include. Verificare sui dati reali di Chiara prima del rollout.

**AC-11.** Selezionando solo "Sospesi", la tabella mostra esattamente i contratti con `lifecycle==="sospeso"`,
e il loro numero coincide con `kpi_sospesi`.
**AC-12.** Il chip "Insolventi" filtra su `c.is_insolvente` (SOSPESO/ESAURITO + rate scadute): è un
**sottoinsieme** delle righe evidenziate (che includono anche gli ATTIVO in ritardo, §2.5/AC-9b). La sua
popolazione coincide con quella delle righe evidenziate **che sono anche scadute**.
**AC-12b (edge).** Un contratto con `prezzo_totale = null` NON compare nel filtro "Saldati" e NON mostra il
badge "Saldato". Test dedicato.

### 2.7 `contratti/[id]/page.tsx` — i tre punti di collasso → badge SSoT
Tre siti derivano lo stato dal solo `chiuso`, cancellando SOSPESO/ESAURITO. Due sono il letterale
`chiuso?"Chiuso":"Attivo"` (header badge, riga "Stato" del tab Dettagli); il terzo, **`RenewalChainLink`**, è
un `item.chiuso && <Badge>Chiuso</Badge>` (mostra il badge solo se chiuso, **nessun ramo "Attivo"**). Tutti e
tre → `<ContractLifecycleBadge lifecycle={…}/>`.

> **⚠️ Header + riga Stato** usano `contract.lifecycle` (il contratto corrente, `ContractWithRates extends
> Contract` → ha il campo dopo §2.3). **`RenewalChainLink` NO:** rende **altri** contratti — genitore e figli
> della catena rinnovi — via `RenewalChainItem`, che oggi porta solo `chiuso` (gap G3). Render col badge SSoT
> richiede **`item.lifecycle`**, dato che oggi non esiste.

**Gap G3 — lavoro backend aggiuntivo (deciso: estendi lo scope).** Aggiungere `lifecycle` a `RenewalChainItem`
(schema `financial.py` + tipo TS, §2.3) e **calcolarlo** per genitore + figli quando `get_contract` costruisce
la catena: serve `crediti_usati` + `rate` di **quei** contratti (oggi non fetchati nella costruzione catena) →
batch-fetch come in `list_contracts`, poi `contract_lifecycle()` per ciascuno. **Non** è a costo zero come la
delega del contratto principale: è scope esplicito di questo giro, non un by-product.

**AC-13.** Un SOSPESO aperto nella scheda dettaglio mostra badge "Sospeso" (non "Attivo" verde) — header e riga Stato.
**AC-13b (gap G3).** Ogni nodo della catena rinnovi (`RenewalChainLink`) mostra il **proprio `lifecycle` reale**:
un genitore SOSPESO appare "Sospeso", non "Chiuso" né "Attivo". Test: catena con un nodo SOSPESO + uno CHIUSO →
badge distinti e corretti.

### 2.8 Cosa sparisce / cosa nasce (sintesi Giro 1)
**Sparisce:** `getPaymentBadge` (8 rami) · `statoKey` · il ricalcolo `isExpired` in 3 punti frontend
(`matchesSituazione`, `getPaymentBadge`, `getScadenzaStyle`) · le 3 definizioni divergenti di "insolvente"
(su 2 file) · il collasso lo-stato-dal-solo-`chiuso` in 4 punti (`statoKey` + header/`RenewalChainLink`/riga
Stato di `[id]`) · la **seconda formula** di "rate scadute" (riconciliata al SSoT, AC-1b).
**Nasce:** 1 predicato SSoT (`is_insolvente`) · 4 campi derivati nel backend (su `Contract` base) ·
`lifecycle` su `RenewalChainItem` (gap G3) · 1 modulo naming riusabile (`contract-status.ts`) · il segnale di
riga "denaro arretrato" con icona+`aria-label` (gap G1/G2). **Semplificazione netta E unificazione.**

---

## 3. GIRO 2 — Allineamento `rinnovi-incassi` + `workspace_engine` (find-and-replace contro il modulo)

> Eseguibile **dopo** che il Giro 1 è in produzione e stabile. Il valore concettuale (vocabolario
> canonico ancorato al SSoT) è già fatto; qui è applicazione meccanica + la chiusura del debito
> off-SSoT del workspace engine. **Inserito ora perché zero ambiguità su cosa viene dopo.**

### 3.1 `rinnovi-incassi/page.tsx` — usare il vocabolario canonico per la parola-stato
Le card hardcodano la parola di stato: `SuspendedCard` → `"Sospeso da N giorni"`. La **parola** "Sospeso"
deve venire da `LIFECYCLE_BADGE.sospeso.label`; il testo di aging ("da N giorni") resta. Stesso trattamento
per ogni etichetta di stato di vita nelle altre card (rinnovo/recupero).

**AC-G2-1.** Nessuna stringa di stato di vita hardcoded in `rinnovi-incassi`: tutte da `contract-status.ts`.

### 3.2 `workspace_engine.py` — secondo consumer OFF-SSoT (il debito da chiudere)
Il workspace engine è un **secondo motore di worklist che non consuma `contract_state`** e ricalcola
inline ciò che i Blocchi 1-2 avevano consolidato. Due conseguenze, una di correttezza e una di vocabolario:

**(a) Inventario inline-residuo — §4.7 è dimostrabilmente incompleto.** Il workspace engine contiene
**siti inline-residuo NON elencati** nell'inventario §4.7:
- `_build_payment_due_soon_cases` → `contract_residual_amount = max((prezzo_totale or 0) − totale_versato, 0)`
  (esposto in `finance_context.total_residual_amount`, visibile all'utente in `renewals_cash`).
- `_build_contract_renewal_cases` → **stessa** formula nel `total_residual_amount`.
- `_load_expiring_contract_rows` → derivazione crediti inline `residual = max(total − used, 0)` (duplica
  `contract_state.crediti_residui()`).

  **Safe oggi** (le query sorgenti filtrano `Contract.chiuso == False`, e su un aperto `quota_stornata == 0`
  per l'invariante §9.5.6), **ma**: l'enumerazione manuale del §4.7 aveva già **mancato questi siti**.

  **Censimento esteso (review code-grounded v1.1).** §4.7 *e* la v1.0 di questa spec sono entrambe incomplete —
  conferma vivente della tesi "l'elenco manuale manca sempre un sito". Siti inline-residuo NON censiti da
  nessuno dei due documenti:
  - **`dashboard.py:497`** → `round((prezzo or 0) − (versato or 0), 2)` **SENZA `max(0,…)`** → può andare
    **negativo**: bug latente da fixare (o delegare a `residuo()`, che clampa) cogliendo l'occasione.
  - **`rates.py:525`** (senza clamp/None-guard) e **`rates.py:734`**.
  - **G6** (prossimo blocco finanziario) introdurrà un **nuovo** inline nel suo endpoint `incassa-residuo`
    (guard ≤0.009 + cap overpayment) → va fatto delegare a `residuo()` **alla sorgente**, o nascerà già "sporco".

  → **Decisione recepita:** l'invariante `quota_stornata>0 ⟹ chiuso` **non può** reggere su un elenco
  manuale (già bucato due volte). Va reso **enforce-abile centralmente**: (1) delegare i siti a
  `contract_state.residuo()`/`crediti_residui()`, **e** (2) un **grep-guard come rete** che fallisce su nuovi
  `prezzo − versato` / `crediti_totali − usati` inline fuori dal SSoT. **Posizione reale del guard:** NON "in
  CI" — una CI non esiste (no `.github/workflows`; l'unico quality-gate è `tools/scripts/check-all.sh` =
  `ruff` + `next build`). Il guard vive **in `check-all.sh`**, con **allowlist del file SSoT**
  (`api/services/contract_state.py` definisce *legittimamente* `prezzo − versato`) ed **esclusione** di
  `tools/` e `tests/` (seed/demo contengono il pattern → falsi positivi). È **difesa-in-profondità accoppiata**
  alla migrazione, mai il meccanismo primario (aggirabile con una variabile intermedia: è un dosso, non un muro).
  **Landare il guard SOLO a censimento completo** (migrati/allowlistati tutti i siti sopra), mai a metà — o
  spacca il gate sui siti preesistenti.

**(b) SOSPESO assente da `renewals_cash` per OMISSIONE, non per scelta.** `_load_expiring_contract_rows`
richiede `data_scadenza >= today` (solo ATTIVO in scadenza) e i case pagamento sono rate-driven: un SOSPESO
senza rate è **invisibile** nel workspace, mentre la dashboard lo mostra in "contratti sospesi". Le due
superfici hanno scopi diversi (può essere corretto), ma oggi la risposta è "no" **per omissione**. →
**Risoluzione cosciente richiesta** quando il workstream SOSPESO/G7 matura: il workspace **deve o no** far
emergere i SOSPESO? Decisione da prendere, non da lasciare implicita.

**(c) Vocabolario.** I `case_kind`/label che rappresentano uno stato di vita devono portare il **valore-enum
`lifecycle`** sul wire e farsi rendere dal frontend via `contract-status.ts` — un solo vocabolario di
display (il modulo TS), l'enum come formato di trasporto. Niente parole di stato hardcoded server-side.

**AC-G2-2.** I tre siti inline di `workspace_engine.py` — **e** i siti del censimento esteso (`dashboard.py:497`,
`rates.py:525/734`) — delegano al SSoT (residuo/crediti), **e** il grep-guard è installato in `check-all.sh`
(non "CI") con allowlist `contract_state.py` + esclusione `tools/`,`tests/`. Il guard è landato solo a
censimento completo. `dashboard.py:497` è fixato per il clamp mancante (no residuo negativo).
**AC-G2-3.** Esiste una decisione esplicita e documentata (BUILD_LOG/spec) su "SOSPESO nel workspace": sì/no
con motivazione.
**AC-G2-4.** Nessuna stringa di stato di vita hardcoded nella resa dei case workspace: enum dal backend,
etichetta dal modulo.

---

## 4. Decisioni prese (registrate per non riaprirle)

- **4.1 Colonna Scadenza neutra, urgenza dal modello.** Niente color-coding graduale ricalcolato nel
  frontend (rosso/ambra/ambra-chiaro su soglie 0/7/30gg). Le soglie temporali vivono nel SSoT
  (`SOGLIA_IN_SCADENZA_GG`); l'urgenza la comunicano il badge **Stato** (scaduto = Sospeso/Esaurito) e il
  flag **`in_scadenza`** (ATTIVO entro soglia). Motivo: il gradiente è un quinto ricalcolo dell'asse tempo,
  e la soglia "≤7gg" non corrisponde ad alcuno stato del modello (terza nozione temristica inventata).
- **4.2 "Denaro arretrato" = riga evidenziata + icona + `aria-label`, niente badge testuale** (rivista v1.1,
  decisioni G1+G2). Il segnale di riga è guidato da `rate_scadute` (SSoT) e copre **sia** l'insolvente
  (SOSPESO/ESAURITO) **sia** l'ATTIVO in ritardo (gap G1: il caso "Rate in Ritardo" non sparisce dalla lista).
  Resa **mai col solo colore** (regola `frontend/CLAUDE.md`): sfondo percepibile anche in dark mode + icona
  `AlertTriangle` + `aria-label` (gap G2). Resta un *segnale di attenzione sulla riga*, non un terzo badge che
  compete coi due assi. "Insolvente" sopravvive come **predicato del SSoT** (`is_insolvente`, il filtro chip)
  e come sotto-caso scaduto dell'evidenziazione.
- **4.5 Edge `prezzo_totale = null` (v1.1).** Un contratto senza prezzo NON è "Saldato": niente badge denaro
  verde, niente inclusione nel filtro "Saldati" (§2.6/AC-12b).
- **4.6 "Rate scadute" ha UNA sola definizione (v1.1).** Il SSoT `rate_scadute` alimenta `is_insolvente`, il
  flag-riga e il filtro Situazione. La formula-riga "larga" preesistente (`ha_rate_scadute`) viene derivata
  dal SSoT o documentata come suo alias — niente seconda formula viva (§2.1/AC-1b).
- **4.3 Scope split (1 blocco per volta).** Giro 1 = `contract_state` + `contracts.py` + `types` +
  `contract-status.ts` + `ContractsTable` + `contratti/page.tsx` + `contratti/[id]/page.tsx`. Giro 2 =
  `rinnovi-incassi` + `workspace_engine` (+ grep-guard). I campi backend additivi rendono il Giro 1
  non-rompente per le superfici del Giro 2.
- **4.4 Naming insolvente cross-pagina (contratti vs rinnovi): non toccato in questo ciclo.** Si riancora
  solo al SSoT dove già usato; nessuna unificazione di label "insolvente" tra pagine in questo giro.

---

## 5. Invarianti (regola d'oro del vocabolario)

1. **Una classificazione, una fonte.** Stato di vita, sotto-stato denaro, scaduto, in-scadenza, insolvente:
   ognuno definito **una volta** in `contract_state.py`, esposto dal backend, **letto** dal frontend.
   Vietato ricalcolare qualunque di questi in JS o in un secondo motore Python.
2. **Due assi mai fusi nella UI.** Vita e denaro restano **due** badge/colonne distinti. Vietato comprimerli
   in un'unica etichetta a cascata (è il difetto C che questa spec rimuove).
3. **Un vocabolario, un modulo.** Ogni etichetta di stato di vita proviene da `contract-status.ts`
   (display) alimentato dall'enum `lifecycle` del backend (trasporto). Vietate stringhe di stato hardcoded
   fuori dal modulo, su qualsiasi superficie.
4. **I flag derivati non diventano stati.** `is_insolvente`, `in_scadenza` sono derivazioni di stati
   esistenti: non aggiungono stati al FDM §3, non ottengono un badge-asse proprio.

---

## 6. Bridge rule + ancoraggi documentali

Questa spec **non modifica il modello di dominio** (nessun nuovo stato): è una spec di *consumo del SSoT*
+ *vocabolario UI*. **Ma conia una definizione canonica nuova** ("insolvente", che nel codice aveva 3
definizioni divergenti) → va fatta **atterrare nella SSoT-vocabolario** come puntatore, non lasciata solo in
una spec di consumo (sennò un futuro lettore del FDM ne re-inventa una quarta — il failure mode che il
consolidamento esiste per evitare).

**Ancoraggi da scrivere quando la spec entra in `docs/` (step "integra in docs/"):**
1. **FDM §4 (vocabolario) / §5 (sotto-stati denaro):** una riga — *«insolvente = flag derivato cross-asse:
   `lifecycle ∈ {SOSPESO,ESAURITO} AND rate scadute`. NON uno stato (il FDM resta a 4+ELIMINATO), nessun
   badge-asse. Mutuamente esclusivo con `in_scadenza` per costruzione. Dettaglio: questa spec.»*
2. **`INDEX.md`** + puntatore in `api/CLAUDE.md` (sezione `contract_state.py`), come per le altre spec finanziarie.
3. **`BUILD_LOG.md`** a fine Giro 1: «vocabolario contratti unificato via SSoT su `/contratti` (giro 1/2);
   `rinnovi-incassi` + `workspace_engine` da allineare allo stesso modulo `contract-status.ts` (giro 2)».

**Learning capture (output non banale di Claude Code).** Oltre alla *forma* del grep-guard e alla decisione
SOSPESO-nel-workspace, catturare la **lezione livello-3 trasferibile** (`LEARNING_APP_ARCHITECTURE`): *un
invariante che alcuni siti calcolano inline non si garantisce **enumerandone** i siti — l'enumerazione manuale
è strutturalmente incompleta (qui ha mancato siti due volte: §4.7 e la v1.0 di questa spec) — ma o
**centralizzando** la derivazione (delega al SSoT) o con un **enforcement automatico** (grep-guard); meglio
entrambi.* È il principio che "si ritrova ovunque": merita interiorizzazione, non solo applicazione.

---

## 7. Convergenza con G7 — questa spec NON collide col filone finanziario, lo anticipa

Verificato sul codice vivo (review v1.1): l'unico punto di contatto reale con il blocco terminazione **G7** è
la **delega-residuo** del §2.2, ed è **convergenza, non collisione**:

- Le due formule (`contracts.py:128` ed `contract_state.residuo()`) sono **byte-identiche oggi** → delegare è
  un refactor a comportamento-zero; `cstate` è già importato → one-liner.
- È **letteralmente il BLOCKER #1 di G7** (`IMPL_PLAN_FINANCIAL_REALIGN.md §4.7`: "residuo→SSoT") **anticipato**.
  Farlo ora **de-riska** G7: il punto più guardato della UI (residuo nel dettaglio) viene corretto sotto un
  change piccolo e testato, non dentro il blocco schema-pesante della terminazione.
- È **forward-compatible**: passando l'oggetto `contract`, quando G7 estenderà `residuo()` con
  `getattr(contract,'quota_stornata',0)` (firma invariata, `IMPL_PLAN §4.3`) il call-site delegato **eredita
  automaticamente** la sottrazione, senza ulteriori modifiche.

**Sequenza raccomandata (verificata):** **Giro 1 (ora o subito dopo G6) → G6 → G7 → Giro 2.** Mai Giro 1 *in
parallelo* a G6 sugli stessi file (`contracts.py`, `contratti/page.tsx`: regioni diverse, conflitti banali ma
evitabili). Giro 2 **dopo/con G7** (la decisione "SOSPESO nel workspace", §3.2(b), è legata alla maturità di G7;
il grep-guard ha senso solo a censimento completo). **Vincolo non-negoziabile per G7:** mantenere
`residuo(contract) -> float` con `quota_stornata` di default 0 (gate di code-review, `IMPL_PLAN §9`).

**Sinergia (non regressione):** post-G7, su un CHIUSO con storno `residuo → 0` → `money_substate = "saldato"`
(niente debito-fantasma). I campi di Giro 1 non vengono invalidati da G7: li **completa**. Registrarlo in
`BUILD_LOG` così la verifica e2e di G7 non lo legga come regressione.
