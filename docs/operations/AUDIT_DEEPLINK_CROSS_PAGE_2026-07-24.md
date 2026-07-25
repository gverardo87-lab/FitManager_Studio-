# Audit — Deep-link & navigazione contestuale cross-page

**Stato:** 🔍 AUDIT READ-ONLY — nessuna modifica al codice. Report per decisione di remediation.
**Data:** 2026-07-24 (completato 2026-07-25)
**Branch:** `FitManager_Studio`
**Trigger:** il founder ha trovato LIVE «molti» link cross-page che non funzionano — non attivano il tab/sezione giusta e non scrollano all'oggetto — pur esistendo già il codice canonico costruito su `rinnovi-incassi` (pattern FE-1.0, `useOverdueRateContextFocus`).
**Metodo:** 2 workflow multi-agente (20 agenti totali, ~3.7M token), fan-out per area + ricerca CRM leader + **verifica adversariale** di ogni finding non-OK con obbligo di evidenza `file:riga`.
**Autorità:** `AGENTS.md` → `frontend/CLAUDE.md` → `SPEC_FRONTEND_CORE_INTUITIVITA.md` (FE-1.0 è il gate chiuso di riferimento).
**Non è una SPEC:** questo documento fotografa lo stato e propone la remediation a fasce; l'apertura del lavoro resta al founder.

---

## 1. Executive summary

Il founder ha ragione: il problema è reale, diffuso e **sistemico**, non un insieme di sviste. Su **77 link/flussi cross-page censiti** in 6 aree, **44 rispettano il contratto** (OK) e **33 hanno un difetto verificato** (5 root-cause ALTA, ~14 MEDIA, ~14 BASSA/polish). Nessun falso positivo è sopravvissuto alla verifica adversariale; **2 sub-claim degli auditor sono stati confutati** e **1 severità gonfiata è stata corretta** (dettaglio §7).

La causa non è «tanti link scritti male». Sono **10 pattern radice** che si ripetono. I due più gravi:

1. **`syncUrlParams` distrugge i parametri contestuali.** Ogni pagina-lista (`/contratti`, `/allenamenti`, …) al primo render riscrive l'URL a partire dai **soli filtri**, cancellando qualsiasi param estraneo (`?cliente=`, `?from=`, `?planId=`). Il param muore prima di essere letto. Un solo consumer fa l'opposto ed è il modello corretto: **`/cassa`** promuove il deep-link a stato React al mount, così sopravvive alla riscrittura.

2. **Il contratto FE-1.0 completo esiste per UN solo intento e UN solo emitter.** `focus=overdue-rate` da `ClientsTable` è l'unico link del sistema con scroll-dopo-dati + highlight + marker + aria-live + stato-mancante + re-trigger. **Ogni altro intento contestuale** — le altre 5 sezioni di Rinnovi & Incassi, la rata dentro il piano pagamenti, il contratto/sessione specifici nei tab del profilo, l'evento in agenda — atterra generico in cima alla pagina e obbliga l'utente a ri-cercare l'oggetto a mano.

**Tesi falsificabile della remediation:** dopo il blocco, ogni link con intento contestuale o (a) porta all'oggetto esatto con evidenziazione, o (b) atterra su uno stato onesto «non più presente», o (c) è dichiaratamente generico. Nessun param emesso e ignorato; nessun atterraggio muto in cima; nessuna back-navigation che mente.

---

## 2. Metodo e affidabilità

- **Fan-out per area** (A1 profilo cliente · A2 contratti · A3 comunicazioni+monitoraggio · A4 rinnovi-incassi consumer · A5 dashboard/oggi/agenda/cassa/schede · A6 infrastruttura url-state/scroll). Ogni agente ha letto emitter **e** consumer per intero, seguendo la catena `pagina → figli → hook → url-state → sessionStorage`, incluso il backend che produce href (`client_avatar_highlights.py`, `clinical_readiness.py`, `dashboard.py`, `session_prep.py`, `workspace_engine.py`).
- **Verifica adversariale**: ogni finding non-OK è passato a un secondo agente col mandato di **confutarlo**. Sopravvivenza solo con evidenza `file:riga` su entrambi i lati. In un audit precedente su questo repo 2 finding erano falsi positivi da agente: qui la verifica li ha intercettati (§7).
- **Ricerca leader** (Salesforce, HubSpot, Pipedrive, Attio, Linear, Asana, monday, Notion, GitHub/GitLab) → 9 leggi DL; **ricerca tecnica** (Next.js App Router + React Query) → 9 leggi TL. Servono come metro esterno, non come opinione (§4).
- **Working tree corrente** (modifiche non committate incluse): i file sono stati letti come sono su disco.
- **Checklist del contratto pieno** (metro di classificazione), estratta da FE-1.0:

| # | Requisito |
|---|-----------|
| C1 | emitter usa builder tipato/centralizzato (no stringa a mano) |
| C2 | consumer valida il param (valori multipli/invalidi) |
| C3 | consumer attiva tab/sezione corretta |
| C4 | scroll al target **dopo** che i dati async sono pronti (`scroll-mt`, block center, reduced-motion) |
| C5 | highlight visibile + marker + annuncio `aria-live` |
| C6 | stato esplicito «target non più presente» (mai atterraggio muto in cima) |
| C7 | ri-navigazione ripetuta ri-scatta l'effetto (Next non rimonta) |
| C8 | nessuna race con la scroll-restoration del layout |
| C9 | back-navigation coerente (`?from=` risolto, filtri della lista preservati) |

Classificazione: **OK** (contratto pieno o link generico legittimo) · **PARTIAL** (naviga/attiva tab ma manca scroll/highlight/stato) · **BROKEN** (param emesso e ignorato, o rotta/target inesistente) · **GAP** (intento reale ma link generico/assente).

---

## 3. I 10 pattern radice (il cuore del report)

I finding delle 6 aree collassano su 10 cause. Molti «link diversi» sono **lo stesso bug** visto da emitter diversi: sono raggruppati qui e mappati ai finding originali in §5.

### RC-1 — `syncUrlParams` strippa i parametri estranei (SISTEMICO) · ALTA
Le pagine-lista ricostruiscono l'URL dai soli filtri in un `useEffect` di sync che gira al mount → `history.replaceState` cancella ogni param non-filtro. Letale dove il param è letto **reattivamente** dopo il mount.
- `/contratti?cliente=X` (da CommandPalette «Contratti di {nome}» e da highlight avatar critico «N rate scadute») → param letto solo nel ramo `new=1`, poi cancellato. L'utente atterra sulla lista **intera**. → **A2-01, A6-04, A5-02, A3-extra**
- `/allenamenti?from=…` (da profilo e monitoraggio, «Vedi aderenza») → `getUrlParams()` riletto a ogni render + sync che riscrive senza `from` → il banner «Torna a…» **non appare mai** su cold load. → **A6-02, A3-07**
- `/allenamenti?planId=Y` («Aderenza programma» della singola scheda) → param mai consumato + strippato. → **A6-03, A5-04**

**Modello corretto già in casa:** `/cassa` (**A6-12**) promuove il deep-link (`focus_movement`) a stato React al mount con precedenza URL-su-storage → sopravvive alla sync. È il pattern da replicare, non da inventare.

### RC-2 — Il contratto FE-1.0 esiste per UN solo intento · ALTA/MEDIA
`focus=overdue-rate` (builder tipato `renewals-focus.ts` + `useOverdueRateContextFocus`) è l'unico link con scroll+highlight+marker+aria-live+stato-mancante+re-trigger. Tutti gli altri intenti contestuali atterrano generici:
- Le altre **5 sezioni** di Rinnovi & Incassi (Da rinnovare, Sospesi, Crediti da incassare, Rimborsi da erogare, Da recuperare): alert dashboard `clients_to_recover`/`suspended_contracts` arrivano nudi. → **A4-05, A4-06, A5-06**
- **Wallet/rimborso** per-cliente: il badge del profilo promette importo+cliente e atterra in cima. → **A4-07** (corretto GAP→PARTIAL MEDIA in verifica)
- **Rata specifica** dentro `PaymentPlanTab`: da qualsiasi contesto rata non esiste modo di atterrare sulla riga giusta (modifica/revoca vivono solo lì). → **A2-10**
- **Riga contratto/sessione** nei tab del profilo (`?tab=contratti` da highlight «Crediti esauriti» = QUEL contratto): tab attivato, riga da trovare a mano. → **A1-09, A1-15**
- **Evento in agenda**: nessuna capability `?date=/?event=` nel consumer; dalle sessioni del profilo non c'è ponte all'evento. → **A5-09, A5-11**

### RC-3 — L'infra di back-navigation esiste ma metà emitter non la usa (C9) · MEDIA
`resolveBackNavigation`, `appendFromParam`, `SIMPLE_BACK_ROUTES` (con `rinnovi-incassi` già registrato) sono pronti, ma i link partono nudi:
- Bottone «Dettaglio» + 4 link nome-cliente delle card Rinnovi & Incassi → back «Torna ai contratti/clienti» invece della worklist. → **A2-06, A4-11, A1-10, A2-extra, A1-extra**
- Step onboarding «genera le rate» (contratto orfano) → back a `/contratti`. → **A2-09**
- «Nuova Scheda» dal monitoraggio → catena di ritorno persa (`/clienti`→`/schede`). → **A3-08**
- `TemplateSelector` post-creazione non propaga `from` se assente. → **A1-04**
- Misurazioni dal profilo → ritorno deviato su Monitoraggio. → **A1-08**
- Catena rinnovi (contratto A→B) → back alla lista. → **A2-12**
- Link assoluti in-page nel profilo (checklist, chip avatar) azzerano `from`/`returnTo` d'arrivo. → **A1-16**
- Banner «Torna alla scheda» in dettaglio esercizio perde `parentFrom` (la freccia header no). → **A5-13**

`appendFromParam` (l'helper centralizzato) è usato da **un solo** emitter (`OggiCommandCenter`); tutti gli altri concatenano a mano, e uno ne re-implementa la logica inline. → **A6-09**

### RC-4 — Param emessi e mai consumati (BROKEN puro) · ALTA→BASSA
- `/agenda?from=clienti-{id}` da highlight «Nessuna seduta PT» → l'agenda **non consuma alcun `from`**; l'intento «prenota per QUESTO cliente» è perso, mentre il deep-link giusto `?newEvent=1&clientId=` esiste ed è già usato altrove. → **A3-13, A5-03** · **ALTA**
- `/impostazioni?from=dashboard` → Impostazioni non ha back-nav; `from` morto (l'anchor `#connettivita` invece funziona). → **A6-10, A5-14** · BASSA
- `?new=1` su `/misurazioni` da 3 emitter portale → mai letto, ma il default della pagina è già «nuova misurazione» → rumore innocuo. → **A3-12, A1-07, A6-11** · BASSA
- CommandPalette «Video Guide» → `/guida#{video.id}` ma **nessun elemento ha quell'id** → atterra in cima. → **A6-extra** · MEDIA

### RC-5 — La Dashboard non ha alcun percorso verso le rate scadute · ALTA
La rottura di coerenza più vistosa (probabile residuo di refactor, non design):
- Il backend emette l'alert `overdue_rates` (critical) con link **`/cassa`**, ma il FE lo **sopprime** ovunque (`AlertHub` lo esclude dalla griglia, `page.tsx` dai conteggi TodoCard). `OverdueRatesSheet` è **dead code** (zero import). → **A4-08, A5-08**
- CommandPalette KPI «Rate pendenti: N» → naviga a **`/`** = la dashboard dove le rate non sono visibili → **dead-end** su un intento monetario esplicito. → **A5-01, A4-extra**
- `/rinnovi-incassi` **non è nella CommandPalette** e il warning «Rate scadute» del ClientPreview è privo di CTA, pur avendo `client.id`. → **A4-10**
- `frontend/CLAUDE.md` documenta ancora `OverdueRatesSheet` come sheet attivo → **doc stale**.

Il target canonico esiste già (sezione «Incassi in ritardo» + `buildOverdueRateFocusHref`): serve ricablare, non costruire.

### RC-6 — Alert → destinazione che non può mantenere la promessa (GAP) · ALTA→BASSA
- `stale_schede` → `/schede`: la lista mostra solo `created_at`, **non** la staleness (calcolata su `updated_at`); e il conteggio è di **clienti**, non di schede («1 scheda» per un cliente con 3 stale). Promessa irrecuperabile a destinazione. → **A5-05, A5-extra** · **ALTA**
- `expiring_contracts` → sheet → dettaglio contratto **privo dell'azione Rinnova** (esiste solo su Rinnovi & Incassi) → vicolo cieco. → **A4-09** · MEDIA
- `stale_measurements` → `/monitoraggio` generico (nessun filtro «misurazioni scadute»). → **A5-07** · MEDIA
- `OrphanEventsSheet`: «creane uno dal profilo» in **prosa senza link**, proprio nel componente nato per la legge D-SEGNALE-AZIONE, con `id_cliente` a portata. → **A5-10** · MEDIA
- Terminazione a credito e `AgingReport` citano/mostrano worklist senza linkarle. → **A4-13, A4-14** · BASSA

### RC-7 — Consumer deep-link «mount-only» (C7) · MEDIA
`?new=1`/`?newEvent=1`/`startScheda=1` sono catturati solo nell'initializer `useState`. Una navigazione same-route che cambia solo i search-param **non rimonta** la pagina → click morto e URL sporco. La CommandPalette (Ctrl+K ovunque) rende lo scenario reale.
- «Nuovo Cliente» da `/clienti`, ri-click startScheda in-page, `?new=1` su liste. → **A1-01, A1-03, A6-06**

Il canone FE-1.0 risolve questo con `routeKey` reattivo; i deep-link «apri sheet» usano ancora il pattern mount-only.

### RC-8 — Stati not-found / validazione mancanti (C2/C6) · MEDIA
- `/monitoraggio/{id}` su cliente inesistente → **skeleton infinito** (`isError` ignorato); il gemello `/clienti/{id}` ha già `NotFoundState`. → **A3-05** · MEDIA
- `/misurazioni?edit={id}` stale → header «Modifica» con **form vuoto** e il bottone «Aggiorna» **CREA un record nuovo** (ramo `else` di `handleSubmit`). ⚠️ integrità dati. → **A1-06** · MEDIA
- `?tab=` sconosciuto → area sotto i tab **completamente vuota**, nessun messaggio. → **A1-02** · BASSA
- Filtri lista da URL senza allowlist (`?stato=Foo`) → lista vuota + empty state **fuorviante** («Aggiungi il primo cliente» con decine di clienti filtrati via). → **A1-17, A1-extra** · BASSA
- `/comunicazioni?cliente=` inesistente → select vuota + empty generico, no «cliente non trovato». → **A3-02** · BASSA

### RC-9 — Race scroll-restore non generalizzata (C8) · MEDIA
Il fix `8f5ca45` («coordina deep-link con scroll restore») è **solo emitter-side e solo per `ClientsTable`→`/rinnovi-incassi`** (`scroll={false}` + `clearPageState`). Il layout resta ignaro dei param contestuali: ritenta il restore a `[0,50,100,250,500,1000,2000]ms` su qualsiasi rotta con scroll salvato.
- `/comunicazioni?tab=&cliente=` e `/impostazioni#connettivita` ereditano la race identica. → **A6-01**
- I retry non sono cancellati dallo scroll dell'utente (solo dal cambio pathname). → **A6-extra**

### RC-10 — CommandPalette non rispetta il contratto di navigazione · MEDIA
`navigate()` = `router.push` senza `clearPageState`. La Sidebar pulisce lo stato (navigazione «fresca» → default), la palette no → stessa navigazione, due esiti: destinazione con **chip filtri stale** (possono nascondere record) e scroll ripristinato. → **A6-05**. Aggrava RC-1 (i deep-link contestuali della palette collidono anche con lo stato salvato).

---

## 4. Cosa fanno i leader (metro esterno)

Sintesi delle 9 leggi DL (Salesforce/HubSpot/Pipedrive/Attio/Linear/Asana/monday/Notion + GitHub/GitLab) e 9 leggi TL (Next.js App Router + React Query). Le fonti puntuali sono nel journal del workflow.

| ID | Legge | Riscontro in FitManager |
|----|-------|--------------------------|
| **DL-1** | Ogni record ha URL canonico semantico; **generarlo da helper centrale** (Salesforce NavigationMixin), mai stato in-memory | `renewals-focus.ts` è l'unico builder tipato; il resto è stringhe a mano + 4 file Python che assemblano href → RC-3/RC-1 |
| **DL-2** | Il sotto-elemento (rata, sezione) si indirizza con anchor/param sulla pagina del padre, **mai** route dedicate (Notion block link, Linear comment URL, GitHub `#L`) | Conferma la strada giusta: estendere `?focus=` su Rinnovi & Incassi e `PaymentPlanTab`, non creare viste nuove → RC-2 |
| **DL-3** | Arrivo = scroll-into-view **+ highlight transitorio** (coppia inseparabile; GitLab highlight blu, GitHub line highlight) | FE-1.0 lo fa; nessun altro link → RC-2 |
| **DL-4** | Target eliminato/risolto = **empty state onesto con causa+azione** (Salesforce «record deleted + Recycle Bin»); anti-pattern Asana «Private link» che genera panico | Coerente con D-SEGNALE-AZIONE già ratificata; oggi mancano gli stati «non più presente» → RC-6/RC-8 |
| **DL-5** | Click su notifica/alert → oggetto **esatto** nel suo contesto; lifecycle notifica separato dal record (Linear inbox, monday «Update section», Asana two-pane) | Gli alert dashboard atterrano generici → RC-5/RC-6 |
| **DL-6** | Code di lavoro processate in sequenza guidata (HubSpot «Complete and Move to Next», Linear J/K) | Idea per le worklist rate/orfani (fuori scope minimo) |
| **DL-7/DL-8** | Filtri **nell'URL** = stato condivisibile; il back restaura filtri+scroll con precedenza **deep-link target > scroll salvato > top** | È esattamente la race di RC-1/RC-9; i filtri oggi vivono in sessionStorage, non nell'URL condivisibile |
| **DL-9 / TL-5** | Navigazione client-side annunciata (title unico → route announcer Next) + **focus sul target** (`tabIndex=-1`, `focus({preventScroll:true})`) | FE-1.0 ha aria-live+focus; da propagare al modulo generalizzato |
| **TL-1** | `useSearchParams` isolato in sottoalbero client + Suspense (fallisce solo in build prod) | Da rispettare quando si sposta la lettura param dai `useState` initializer (RC-7) |
| **TL-2** | Scroll data-driven (deps `[targetId, isSuccess]` o callback-ref), **mai** timer come meccanismo primario | Il layout usa 7 `setTimeout` di restore: è la fonte della race → RC-9 |
| **TL-3** | **UN solo arbitro** dello scroll con precedenza esplicita; `history.scrollRestoration='manual'`; `{scroll:false}` ovunque si possieda lo scroll | Manca il punto unico di coordinamento nel layout → RC-9 |
| **TL-4** | Query param batte hash in App Router (hash invisibile a hook/server, pipeline scroll buggata) | Conferma `?focus=` vs `#anchor`; l'unico `#` in uso (`/guida#video`) è infatti morto → RC-4 |
| **TL-6** | Repeat navigation: param intent **one-shot** consumato e rimosso (`router.replace`), risolve anche back/F5 | La cura per RC-7; FE-1.0 usa `routeKey`, gli altri il pattern mount-only |
| **TL-7** | URL = verità per stato condivisibile che alimenta la query key; sessionStorage solo per effimero; **mai duplicare** | RC-1 nasce dal duplicare filtri in sessionStorage e riscrivere l'URL da lì |
| **TL-8** | `scroll-margin-top` sui target dimensionato sull'header sticky (raccomandazione ufficiale Next) | FE-1.0 usa `scroll-mt-24`; da standardizzare nel modulo |

**Verdetto del metro:** il pattern già emerso nel repo (intent via query param + scroll programmatico + coordinamento con lo scroll-restore) è esattamente ciò che i leader e la doc Next raccomandano. Il difetto non è la strada — è che **è stata percorsa una volta sola**.

---

## 5. Inventario completo per area

Legenda severità dopo verifica adversariale. «→» indica una correzione del verificatore rispetto all'auditor.

### A1 — Profilo cliente (19 censiti · 8 OK)
| ID | Target | Class. | Sev. | Sintesi | RC |
|----|--------|--------|------|---------|----|
| A1-01 | `/clienti?new=1` | PARTIAL | MEDIA | sheet apre solo al mount; Ctrl+K da `/clienti` = no-op | RC-7 |
| A1-02 | `/clienti/[id]?tab=` | PARTIAL | BASSA | tab sconosciuto → area vuota, no fallback | RC-8 |
| A1-03 | `?tab=schede&startScheda=1` | PARTIAL | MEDIA | ref one-shot: ri-click in-page morto + URL sporco | RC-7 |
| A1-04 | `/schede/[id]` post-creazione | PARTIAL | MEDIA | `TemplateSelector` non propaga `from` se assente | RC-3 |
| A1-05 | `/anamnesi?startWizard=1` | OK | — | auto-open + back coerenti | — |
| A1-06 | `/misurazioni?edit=` | PARTIAL | MEDIA | ⚠️ edit stale → form vuoto, «Aggiorna» **crea** nuovo record | RC-8 |
| A1-07 | `/misurazioni?new=1` | OK | — | param ignorato ma innocuo | RC-4 |
| A1-08 | `/misurazioni` senza `from` | PARTIAL | BASSA | ritorno deviato su Monitoraggio dal profilo | RC-3 |
| A1-09 | `?tab=contratti/sessioni` | PARTIAL | MEDIA | highlight su oggetto specifico → tab generico, no row-focus | RC-2 |
| A1-10 | `/clienti/[id]` da rinnovi | PARTIAL | BASSA | nome cliente senza `from=rinnovi-incassi` | RC-3 |
| A1-11..14 | `/clienti/[id]` vari | OK | — | link generici + `from`/`returnTo` corretti | — |
| A1-15 | ritorno `?tab=contratti` | GAP | BASSA | tab riattivato, riga da trovare a mano | RC-2 |
| A1-16 | link assoluti in-page | PARTIAL | BASSA | azzerano `from`/`returnTo` d'arrivo | RC-3 |
| A1-17 | `/clienti?stato=` | PARTIAL | BASSA | valori arbitrari → lista vuota non spiegata | RC-8 |
| A1-18/19 | monitoraggio→profilo / palette anamnesi | OK | — | flusso meglio cablato | — |

### A2 — Contratti (12 censiti · 6 OK, **area verificata al 100%**)
| ID | Target | Class. | Sev. | Sintesi | RC |
|----|--------|--------|------|---------|----|
| A2-01 | `/contratti?cliente=` | **BROKEN** | **ALTA** | «Contratti di {nome}» → param ignorato **e** strippato → lista intera | RC-1 |
| A2-02/03 | `?new=1[&cliente=]` | OK | — | creazione contratto onorata | — |
| A2-04/05 | `/contratti/[id]?from=dashboard` | OK | — | back + tab payments default corretti | — |
| A2-06 | «Dettaglio» da rinnovi | PARTIAL | MEDIA | senza `from` → back «Torna ai contratti» | RC-3 |
| A2-07/08 | post-rinnovo / profilo→dettaglio | OK | — | catene end-to-end corrette | — |
| A2-09 | onboarding orfano | PARTIAL | MEDIA | step «genera rate» senza `from` | RC-3 |
| A2-10 | rata in `PaymentPlanTab` | GAP | MEDIA | nessun focus rata da contesti rata | RC-2 |
| A2-11 | link generici | OK | — | round-trip con filtri preservati | — |
| A2-12 | catena rinnovi | PARTIAL | BASSA | back alla lista invece del nodo precedente | RC-3 |

### A3 — Comunicazioni + Monitoraggio (14 censiti · 6 OK)
| ID | Target | Class. | Sev. | Sintesi | RC |
|----|--------|--------|------|---------|----|
| A3-01 | `/comunicazioni?tab=registro&cliente=` | OK | — | tab+filtro corretti | — |
| A3-02 | cliente invalido | PARTIAL | BASSA | select vuota, no «non trovato» | RC-8 |
| A3-03 | `/comunicazioni` no back | GAP | BASSA | nessuna affordance di ritorno | RC-3 |
| A3-04 | lista `/monitoraggio` | GAP | MEDIA | filtri/pagina non persistiti (chiave `monitoraggio` morta) | RC-9/RC-1 |
| A3-05 | `/monitoraggio/[id]` | PARTIAL | MEDIA | cliente inesistente → skeleton infinito | RC-8 |
| A3-06 | worklist→azione→ritorno | OK | — | catena anamnesi/misurazioni/schede completa | — |
| A3-07 | `/allenamenti?from=` | BROKEN | ALTA→**MEDIA** | `from` distrutto dal sync → banner mai visibile | RC-1 |
| A3-08 | «Nuova Scheda» | GAP | MEDIA | catena di ritorno al portale persa | RC-3 |
| A3-09..11 | builder/portale/profilo | OK | — | back coerenti | — |
| A3-12 | `?new=1` misurazioni | PARTIAL | BASSA | param morto innocuo | RC-4 |
| A3-13 | `/agenda?from=clienti-` | **BROKEN** | **ALTA** | agenda non consuma `from`; intento perso (esiste `newEvent+clientId`) | RC-4 |
| A3-14 | highlight avatar provenienza | PARTIAL | BASSA | back al profilo invece del portale | RC-3 |
| A3-extra | `/contratti?cliente=` da avatar | **ALTA** | | conferma RC-1 da altro emitter | RC-1 |

### A4 — Rinnovi & Incassi come consumer (14 censiti · 4 OK)
| ID | Target | Class. | Sev. | Sintesi | RC |
|----|--------|--------|------|---------|----|
| A4-01 | `focus=overdue-rate` (ClientsTable) | OK | — | **riferimento FE-1.0, contratto pieno** | — |
| A4-02/03/04 | sidebar / post-rinnovo / consumer | OK | — | robusti | — |
| A4-05 | alert «da recuperare» | PARTIAL | MEDIA | sezione 5ª senza anchor | RC-2 |
| A4-06 | alert «sospesi» | PARTIAL | MEDIA | sezione 2ª senza anchor | RC-2 |
| A4-07 | wallet badge profilo | GAP→**PARTIAL** | ALTA→**MEDIA** | promette importo+cliente, atterra in cima | RC-2 |
| A4-08 | overdue_rates soppresso | BROKEN | MEDIA | alert filtrato + link `/cassa` stale + dead code | RC-5 |
| A4-09 | expiring → dettaglio | GAP | MEDIA | dettaglio senza azione Rinnova = vicolo cieco | RC-6 |
| A4-10 | palette senza rinnovi | GAP | MEDIA | pagina irraggiungibile da Ctrl+K | RC-5 |
| A4-11 | link in uscita | PARTIAL | MEDIA | nudi, back perde la worklist | RC-3 |
| A4-12 | workspace payment_overdue | GAP | BASSA | → `/cassa`, UI dormiente (debito latente) | RC-5 |
| A4-13/14 | terminate credit / aging | GAP | BASSA | worklist citata ma non linkata | RC-6 |

### A5 — Dashboard/Oggi/Agenda/Cassa/Schede (22 censiti · 8 OK)
| ID | Target | Class. | Sev. | Sintesi | RC |
|----|--------|--------|------|---------|----|
| A5-01 | palette «Rate pendenti»→`/` | GAP | **ALTA** | dead-end su intento monetario esplicito | RC-5 |
| A5-02 | `/contratti?cliente=` | **BROKEN** | **ALTA** | param ignorato (2 emitter forti) | RC-1 |
| A5-03 | `/agenda?from=` | **BROKEN** | **ALTA** | `from` morto, no pre-fill cliente | RC-4 |
| A5-04 | `/allenamenti?planId=` | BROKEN | ALTA→**MEDIA** | planId ignorato (esiste `/allenamenti/{id}`) | RC-1 |
| A5-05 | `stale_schede`→`/schede` | GAP | **ALTA** | staleness non mostrata; conta clienti non schede | RC-6 |
| A5-06 | alert aggregati→rinnovi | PARTIAL | MEDIA | nessuna sezione attivata | RC-2 |
| A5-07 | `stale_measurements`→monitoraggio | PARTIAL | MEDIA | nessun filtro preattivato | RC-6 |
| A5-08 | overdue_rates soppresso | BROKEN | BASSA | = A4-08 (dead code + doc stale) | RC-5 |
| A5-09 | sessioni→agenda | GAP | MEDIA | nessun ponte evento-specifico (manca capability) | RC-2 |
| A5-10 | OrphanEventsSheet no CTA | GAP | MEDIA | «creane uno» senza link (viola D-SEGNALE-AZIONE) | RC-6 |
| A5-11 | Oggi→agenda | GAP | BASSA | evento in focus non focalizzato | RC-2 |
| A5-12 | OggiHero promemoria | PARTIAL | BASSA | todo scaduti fuori settimana visibile | RC-2 |
| A5-13 | esercizi banner→scheda | PARTIAL | BASSA | banner perde `parentFrom` (la freccia no) | RC-3 |
| A5-14 | connettività `#anchor` | PARTIAL | BASSA | anchor ok, `from` morto | RC-4 |
| A5-15..22 | TodoCard/AlertHub inline/cassa/… | OK | — | risoluzione inline + cassa modello | — |

### A6 — Infrastruttura url-state/scroll (16 censiti · 8 OK)
| ID | Oggetto | Class. | Sev. | Sintesi | RC |
|----|---------|--------|------|---------|----|
| A6-01 | scroll-restore vs deep-link | PARTIAL | MEDIA | coordinamento solo per ClientsTable→rinnovi | RC-9 |
| A6-02 | `/allenamenti` `from` | **BROKEN** | **ALTA** | back-nav sabotata dal proprio sync | RC-1 |
| A6-03 | `/allenamenti` `planId` | BROKEN | MEDIA | param mai consumato | RC-1 |
| A6-04 | `/contratti?cliente=` palette | **BROKEN** | **ALTA** | = A2-01 | RC-1 |
| A6-05 | CommandPalette no clearPageState | PARTIAL | MEDIA | filtri stale a destinazione | RC-10 |
| A6-06 | deep-link mount-only | PARTIAL | MEDIA | morti same-route | RC-7 |
| A6-07 | FILTER_PAGE_KEYS | OK | — | coerente (1 entry morta `monitoraggio`) | — |
| A6-08 | censimento `from=` | OK | — | tutti i valori emessi risolti | — |
| A6-09 | appendFromParam quasi inutilizzato | OK | BASSA | ~20 emitter a mano, 1 re-implementa l'helper | RC-3 |
| A6-10 | `/impostazioni?from=` | BROKEN | BASSA | `from` morto | RC-4 |
| A6-11 | `?new=1` misurazioni | OK | BASSA | innocuo | RC-4 |
| A6-12 | **`/cassa` sync** | OK | — | **modello: deep-link promosso a stato, sopravvive** | RC-1 |
| A6-13 | `/comunicazioni` tab/cliente | OK | — | reattivo (solo race A6-01) | — |
| A6-14 | precedenza storage>URL | GAP | BASSA | 4 pagine storage-first vs 2 URL-first: trappola latente | RC-1 |
| A6-15 | FE-1.0 reference | OK | — | contratto pieno C1-C9 | — |
| A6-16 | consumer dettaglio cliente | OK | — | reattivo, preservante, idempotente | — |
| A6-extra | `/guida#video` anchor morto | | MEDIA | intento emesso mai consumato | RC-4 |

---

## 6. Osservazioni collaterali (non link, ma emerse in audit)

- **Dead code**: `components/clients/ProgressiTab.tsx` (mai importato — coerente con l'audit obsolescenza 2026-07-23); `OverdueRatesSheet.tsx` (zero import); `WorkspaceAgendaPanel.tsx` + UI workspace (`WorkspaceCaseCard`/`WorkspaceDetailPanel`/`useWorkspaceCases`) definiti e mai montati.
- **Hydration violation**: `clienti/page.tsx` e `contratti/page.tsx` leggono `window.location.search` in un `useState` initializer → viola la regola CRITICAL Hydration Safety di `frontend/CLAUDE.md`.
- **Backend come «builder» di URL non tipato**: `client_avatar_highlights.py`, `clinical_readiness.py`, `dashboard.py`, `session_prep.py`, `workspace_engine.py` assemblano href del profilo/tab a mano. Una rinomina di tab o flag FE va sincronizzata a mano in ~5 file Python — candidato a contratto condiviso se si estende FE-1.0.
- **Doc stale**: `frontend/CLAUDE.md` elenca `OverdueRatesSheet` come sheet attivo dell'Alert Panel (tabella «Inline Resolution») e `ProgressiTab` come tab attivo.
- **Etichetta errata**: alert `stale_schede` conta `DISTINCT clienti` ma il testo dice «N schede da aggiornare».

---

## 7. Falsi positivi e correzioni (integrità dell'audit)

La verifica adversariale ha **confermato tutti i finding sostanziali** ma corretto:
- **A4-07** wallet badge: **GAP→PARTIAL, ALTA→MEDIA**. Il link esiste e atterra sulla pagina giusta (worklist non-vuota per costruzione); l'esito utente è identico ad A4-05/06 (MEDIA), non un vicolo cieco.
- **A5-04** planId: **ALTA→MEDIA**. L'atterraggio non è muto — `idCliente` filtra comunque la lista sul cliente giusto; danno pari ad A5-06.
- **A3-07** `/allenamenti from`: **ALTA→MEDIA** per il ramo A3, mantenuto ALTA per A6-02 (stesso bug, framing «back-nav sabotata» vs «intento primario consegnato»). Nel report è trattato come cluster ALTA per blast-radius, con la sfumatura annotata.
- **Sub-claim confutate** (l'audit era **peggiore** del dichiarato, non migliore): A3-14 affermava che `/contratti?cliente=` funzionasse → **falso**, è morto (→ conferma RC-1); A1-10 dava per coperto il round-trip `returnTo` da Rinnovi & Incassi verso il dettaglio contratto → **falso** sul working tree corrente (link nudi).

Nessun finding è stato ritirato come inventato.

---

## 8. Raccomandazione architetturale

Il repo ha già la soluzione giusta costruita bene, in un posto solo. La remediation professionale **non è** toccare 33 link a mano: è **generalizzare FE-1.0 a un modulo unico** e poi cablarci gli emitter, chiudendo le cause radice in ordine di leva.

1. **`lib/context-focus.ts` — builder tipati + parser rigoroso** (generalizzazione di `renewals-focus.ts`): un intent tipato per `{page, section, entityId}` con validazione multi-valore. Sostituisce le stringhe a mano e i 5 file Python che assemblano href (DL-1). Chiude RC-3/RC-4 alla fonte.
2. **`useContextFocus` — hook consumer riusabile** (generalizzazione di `useOverdueRateContextFocus`): scroll-dopo-dati + highlight + marker + `aria-live` + stato «non più presente» + `routeKey` re-trigger. Applicabile a sezioni (Rinnovi & Incassi), righe (tab profilo, PaymentPlanTab) ed eventi (agenda). Chiude RC-2 e RC-7 (TL-2/TL-6/DL-3).
3. **Fix `syncUrlParams` (RC-1, massima leva):** preservare i param non-filtro, **oppure** promuovere ovunque il deep-link a stato al mount come fa `/cassa` (A6-12). Un solo fix ripara `/contratti?cliente=`, `/allenamenti?from=`, `/allenamenti?planId=` e mette in sicurezza ogni futuro deep-link su pagina-lista.
4. **Un solo arbitro dello scroll nel layout (RC-9):** l'hook di restore salta il restore se l'URL porta un intent di focus (precedenza `deep-link target > scroll salvato > top`), invece del coordinamento emitter-side caso-per-caso (TL-3/DL-8).
5. **Ricablare il percorso rate scadute (RC-5):** decidere il destino dell'alert `overdue_rates` (ripristino su `buildOverdueRateFocusHref` **oppure** rimozione emissione+dead-code), aggiungere `/rinnovi-incassi` alla CommandPalette, correggere il KPI «Rate pendenti».
6. **Stati onesti (RC-6/RC-8):** `NotFoundState` su `/monitoraggio/[id]`; fix del ramo `else` di `handleSubmit` misurazioni (⚠️ integrità dati); allowlist su `?tab=` e sui filtri lista; empty-state «filtri attivi» distinto da «nessun record»; CTA sul ramo senza contratti di `OrphanEventsSheet`.
7. **CommandPalette allinea il contratto Sidebar (RC-10):** `clearPageState` prima di navigare verso pagine con filtri salvati.

---

## 9. Remediation proposta a fasce

Non è una SPEC — è la sequenza suggerita, da ratificare. **Coordinamento obbligatorio con blocco P** (`SPEC_P`): `/contratti`, `PaymentPlanTab`, profilo cliente e Rinnovi & Incassi sono file condivisi; nessuna fascia FE tocca in parallelo gli stessi money-path di P.

**Fascia A — cause radice ad alta leva (chiude ~15 finding con pochi fix):**
- Fix `syncUrlParams` (RC-1) → ripara i 3 BROKEN ALTA `/contratti?cliente=`, `/allenamenti?from=`, `/allenamenti?planId=` in un colpo.
- `agenda?from=` → sostituire con `?newEvent=1&clientId=` esistente (RC-4, A3-13/A5-03).
- Percorso rate scadute dalla dashboard (RC-5): decisione alert + palette + KPI.
- `stale_schede`/`stale_measurements` → destinazione che mostra la staleness, o filtro preattivato (RC-6).
- ⚠️ Fix `handleSubmit` misurazioni edit-stale (RC-8, A1-06) — integrità dati, priorità a sé.

**Fascia B — generalizzazione FE-1.0 (chiude RC-2/RC-3/RC-7):**
- `lib/context-focus.ts` + `useContextFocus`.
- `?focus=` di sezione su Rinnovi & Incassi (5 sezioni + wallet).
- Focus rata su `PaymentPlanTab` + link dalle worklist rata.
- `from`/`returnTo` sui link nudi (usare `appendFromParam` ovunque).
- Consumer reattivi al posto di mount-only (`routeKey`).
- `NotFoundState` su `/monitoraggio/[id]`.

**Fascia C — coerenza e polish (chiude RC-9/RC-10 + BASSA):**
- Arbitro unico dello scroll nel layout.
- `clearPageState` nella CommandPalette.
- Allowlist `?tab=`/filtri + empty-state onesti.
- Capability `?date=/?event=` in agenda + ponte dalle sessioni.
- Pulizia dead code + allineamento `frontend/CLAUDE.md` + fix etichetta `stale_schede`.

**Verifica per ogni fascia:** vitest mirati sui contratti (sull'esempio di `renewals-focus.test.ts` + `rinnovi-incassi-context-focus.test.tsx`), `next build`, `check-all.sh`, e test LIVE autenticato desktop dei percorsi riparati (il founder ha trovato i bug LIVE: la verifica deve chiudere lì).

---

## Appendice — provenienza

- Workflow 1 (`wf_481d032a-87f`): ricerca tecnica TL + inventario A2/A3/A4/A6 + verifica A2. 12 agenti, ~1.8M token.
- Workflow 2 (`wf_41d3a74a-3b3`): ricerca CRM DL + inventario A1/A5 + verifica A3/A4/A6. 8 agenti, ~1.9M token.
- Journal completi negli output dei task `wq118iieg` / `weogpgtpl`. Ogni finding riporta evidenza `file:riga` verificata su entrambi i lati (emitter+consumer).
