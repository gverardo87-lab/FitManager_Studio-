# Audit Senior - Terminazione bilaterale e tutela trainer

> **Provenienza:** audit backend read-only eseguito su `FitManager_Studio` dopo riallineamento a `CLAUDE.md`, `api/CLAUDE.md`, `docs/learning/BUILD_LOG.md` e ai fix G7.7/G7.8 gia chiusi.  
> **Data:** 2026-06-27  
> **Modalita:** sola lettura (codice + docs vive). Nessuna mutazione runtime nel corso dell'audit.  
> **Trigger:** nuova analisi senior sul flusso contratti/recesso dopo le segnalazioni reali e dopo la chiusura dei bug/fix G7.7-G7.8; focus specifico sulla tutela del trainer quando il cliente ha fruito piu servizio di quanto ha pagato.

**Scope:** asse contratti/terminazione/backend, in particolare `contract_settlement.py`, `contracts.py`, `contract_state.py`, schemi API, audit log e percorso `reopen`.

**Domanda di audit:** il sistema gestisce davvero un recesso/conguaglio **bilaterale**, oppure oggi e' ancora sbilanciato sul solo caso in cui il trainer deve restituire denaro al cliente?

---

## 1. Executive summary

Il nucleo matematico del recesso e' corretto sul lato **servizio reso**: il calcolo economico continua a dipendere dall'asse **EROGATO** (`Event PT Completato`), non dall'occupazione-credito, e questo resta un presidio forte da non toccare.

Il problema residuo, pero', e' di **semantica di dominio e di azione**:

- quando `versato > servizio_reso`, il software tutela il cliente in modo esplicito (`RIMBORSO`);
- quando `servizio_reso > versato`, il software **non tutela il trainer in modo equivalente**;
- il ramo positivo del conguaglio viene collassato su `SALDO_A_PERDERE`, cioe' su una rinuncia implicita del trainer, non su una scelta esplicita.

In altre parole: la matematica del servizio reso e' bilaterale, ma l'azione di terminazione **non lo e' ancora**. Il sistema distingue bene il credito del cliente; non distingue ancora tra:

1. credito del trainer da incassare contestualmente;
2. credito del trainer a cui il trainer decide di rinunciare.

Questo e' il finding principale dell'audit. Non e' un dettaglio di UX: e' un difetto di dominio che puo' tradursi in perdita silenziosa di un credito a favore del trainer.

---

## 2. Baseline: cosa e' gia stato chiuso

Questo audit NON riapre finding che il progetto ha gia corretto nei blocchi immediatamente precedenti. Restano chiusi e non sono il problema di oggi:

- **H1 / `unpay_rate` su terminati** -> chiuso in G7.7-R1
- **M1 / `reopen` over-restore delle rate** -> chiuso in G7.7-M1
- **M2 / `update_rate` su contratto terminato + cap off-SSoT** -> chiuso in G7.7-M2
- **L1/M3/M4 / gap di trasparenza occupazione vs erogato** -> chiusi da G7.7-R4/R5
- **hardening audit su retrodatazione/estensione `data_scadenza`** -> chiuso il 2026-06-27

Il report 2026-06-26 resta quindi il baseline storico del filone. Questo audit ne prende il testimone solo sul gap che rimane aperto dopo quei fix: la **asimmetria del ramo positivo del conguaglio**.

---

## 3. Verdetto sintetico

| Asse | Verdetto | Nota |
|------|----------|------|
| **EROGATO come base del valore reso** | **REGGE** | presidio corretto, non da toccare |
| **Strada B (lordo immutabile + netto derivato)** | **REGGE** | modello contabile corretto anche per il nuovo blocco |
| **Terminazione come atto atomico** | **REGGE lato cliente** | manca la gamba speculare lato trainer |
| **Tutela del cliente overpaid** | **REGGE** | percorso esplicito: rimborso |
| **Tutela del trainer underpaid** | **NON REGGE** | percorso implicito di rinuncia, non scelta |
| **Distinzione fatto economico vs azione scelta** | **NON REGGE** | `SALDO_A_PERDERE` fonde i due livelli |
| **Reversibilita simmetrica via `reopen`** | **PARZIALE** | corretta per i rami attuali, da estendere se nasce l'incasso contestuale trainer |

---

## 4. Findings confermati

### HIGH

**H1 - Il ramo `conguaglio > 0` tutela il cliente ma non il trainer**

**Evidenza codice**
- `api/services/contract_settlement.py`
  - `conguaglio < 0` -> `RIMBORSO`
  - `conguaglio > 0` -> `SALDO_A_PERDERE`
- `api/routers/contracts.py`
  - mapping esito -> `TERMINAZIONE_DECADENZA`
  - nessun ramo di incasso contestuale quando il cliente deve ancora denaro per servizio gia reso

**Descrizione**
Il sistema riconosce matematicamente che, se `valore_servizio_reso > totale_versato`, il cliente ha ricevuto piu servizio di quanto abbia pagato. Pero questa situazione non genera una scelta esplicita a tutela del trainer. Viene trasformata direttamente in write-off del dovuto.

**Perche e' grave**
Il software non e' neutro: prende posizione al posto del trainer. Non gli chiede se voglia:

- incassare il saldo dovuto e chiudere;
- rinunciare volontariamente al saldo e chiudere.

La rinuncia del trainer e' oggi il default implicito, non una decisione auditabile.

**Impatto**
- perdita silenziosa di credito a favore del trainer;
- storico indistinto tra "servizio non erogato annullato" e "servizio erogato ma abbuonato";
- impossibilita di dimostrare a posteriori se il trainer abbia scelto davvero la rinuncia.

**Categoria:** **BUG_DI_DOMINIO**

**Remediation**
Spezzare il ramo positivo in due livelli:

1. **esito puro di bilancio**: `credito_cliente` / `credito_trainer` / `pari`
2. **azione scelta** lato router: `INCASSA_ORA` oppure `RINUNCIA_ESPRESSA`

---

### MEDIUM

**M1 - `SettlementEsito` oggi fonde fatto economico e decisione operativa**

**Evidenza codice**
- `api/services/contract_settlement.py`: `SettlementEsito.SALDO_A_PERDERE`

**Descrizione**
`SALDO_A_PERDERE` non e' solo un esito. E' gia un'azione interpretata: "il trainer rinuncia a incassare". Questo rende il modulo puro meno puro di quanto dovrebbe essere, perche gli fa prendere una decisione di prodotto che dovrebbe spettare al caller.

**Impatto**
- il settlement non e' piu un motore di fatti economici, ma di fatti + policy implicita;
- la preview e la terminate API non possono piu chiedere una scelta, perche ricevono gia una decisione chiusa;
- la documentazione FDM parla di conguaglio bidirezionale, ma il codice materializza solo un lato in forma action-ready.

**Categoria:** **DEBITO_SSOT**

**Remediation**
Evolvere `SettlementEsito` verso esiti **balance-based** (`CREDITO_CLIENTE`, `CREDITO_TRAINER`, `PARI`) e spostare l'azione nel router.

---

**M2 - `terminate` non supporta l'incasso contestuale del saldo dovuto al trainer**

**Evidenza codice**
- `api/routers/contracts.py`
  - esiste gamba `USCITA RIMBORSO_CONTRATTO`
  - non esiste gamba speculare `ENTRATA` diretta di conguaglio trainer

**Descrizione**
Oggi il trainer, se vuole chiudere un contratto dove il cliente ha fruito piu di quanto ha pagato, non ha un path nativo che gli permetta di:

1. incassare il delta dovuto nello stesso atto di terminazione;
2. chiudere il contratto con `residuo == 0`.

Questo crea un falso bivio:

- o lascia il contratto aperto e recupera il dovuto fuori dal flusso di terminazione;
- o termina e perde il saldo in modo implicito.

**Impatto**
- assenza di un canale atomico lato trainer gemello di G6/G7.3;
- maggiore rischio operativo di procedure manuali o workaround non auditabili;
- impossibilita di chiudere il contratto e regolare tutto "in un colpo solo".

**Categoria:** **GAP_FUNZIONALE**

**Remediation**
Introdurre una gamba `ENTRATA` diretta su contratto per il solo caso `credito_trainer > 0`, nello stesso commit della terminazione, con categoria cassa dedicata e `id_rata = NULL`.

---

**M3 - Il linguaggio API/preview e' ancora client-centric**

**Evidenza codice**
- payload `terminate` orientato a `metodo_rimborso`
- preview e mapping esito costruiti per il solo lato rimborso / decadenza

**Descrizione**
L'interfaccia del caso d'uso e' costruita come se il problema fosse solo: "quanto devo restituire al cliente?" oppure "chiudo senza rimborso". Manca un vocabolario esplicito del caso opposto: "quanto deve ancora il cliente per servizio gia erogato?".

**Impatto**
- il frontend non puo obbligare una scelta consapevole nel ramo `credito_trainer > 0`;
- il backend non ha un contratto API che renda esplicita quella biforcazione;
- il report finale di chiusura non distingue incasso da rinuncia.

**Categoria:** **GAP_DI_MODELLAZIONE**

**Remediation**
Estendere preview e payload `terminate` con:

- esito di bilancio puro;
- importo `credito_trainer`;
- elenco azioni permesse;
- scelta obbligatoria nel ramo positivo.

---

**M4 - `reopen` e' corretto per i rami attuali ma non ancora preparato alla nuova simmetria**

**Evidenza codice**
- `api/routers/contracts.py`
  - `reopen` annulla rimborso e storno
  - nessun annullamento di un eventuale incasso diretto da conguaglio trainer

**Descrizione**
Questo non e' un bug gia in produzione: e' un finding di design load-bearing. Se introduciamo la gamba `INCASSA_ORA` senza estendere `reopen`, la terminazione diventerebbe asimmetrica e non piu round-trip.

**Impatto**
- impossibilita di ripristinare esattamente lo stato pre-terminate;
- nuova possibile divergenza Contract/mastro;
- regressione sul principio G7.4 "reopen = inverso esplicito dello stato".

**Categoria:** **VINCOLO_DI_IMPLEMENTAZIONE**

**Remediation**
Qualsiasi nuovo incasso di conguaglio trainer deve nascere insieme al suo inverso canonico in `reopen`.

---

### LOW

**L1 - Divergenza doc-vs-code sul significato pratico di "conguaglio bidirezionale"**

**Evidenza doc/code**
- `docs/technical/FINANCIAL_DOMAIN_MODEL.md` descrive il `conguaglio > 0` come "da incassare (G6) oppure STORNO"
- il codice reale oggi implementa solo il ramo write-off implicito dentro `terminate`

**Descrizione**
Il modello documentale aveva gia visto il bivio giusto, ma il codice non lo ha ancora trasformato in percorso esplicito. Non e' una contraddizione totale, ma e' una promessa di modello ancora non mantenuta.

**Categoria:** **DOC_DRIFT**

**Remediation**
Allineare il FDM e la nuova spec al comportamento che verra realmente implementato, evitando frasi ambigue tipo "oppure STORNO" senza indicare chi sceglie, quando e con quale tracciabilita.

---

**L2 - `motivo_chiusura` e nomenclatura storica poco espressivi sul ramo trainer**

**Evidenza codice**
- mapping attuale a `TERMINAZIONE_DECADENZA` per il ramo positivo

**Descrizione**
L'etichetta storica del motivo di chiusura non aiuta a distinguere:

- terminazione con saldo trainer incassato;
- terminazione con saldo trainer rinunciato;
- pura consunzione money-neutral.

**Categoria:** **IGIENE_SEMANTICA**

**Remediation**
Rendere piu espressivo il mapping del ramo trainer o, almeno, spostare la distinzione nel payload audit strutturato.

---

## 5. Cosa regge e va preservato

L'audit conferma che non serve rifondare tutto. Le basi sane da preservare sono:

- `valore_servizio_reso` calcolato sull'asse **EROGATO**
- `Rinviato` escluso dal denaro (G7.8)
- Strada B: `totale_versato` lordo immutabile, `totale_rimborsato` separato, `netto_incassato()` derivato
- `terminate` come atto atomico, non via `_sync_contract_chiuso`
- `reopen` come percorso esplicito di inversione
- rate non saldate soft-delete selettivo
- `residuo()` come fonte unica del dovuto operativo

La correzione cercata e' quindi una estensione rigorosa del modello attuale, non un cambio di paradigma.

---

## 6. Piano di remediation raccomandato

| # | Azione | Severita/Rischio | Note |
|---|--------|------------------|------|
| **1** | Separare esito puro e azione scelta nel settlement | HIGH - dominio | chiude H1/M1 alla radice |
| **2** | Estendere `terminate` con scelta obbligatoria `INCASSA_ORA` / `RINUNCIA_ESPRESSA` | HIGH - flusso contrattuale | evita write-off implicito |
| **3** | Introdurre gamba `ENTRATA` diretta di conguaglio trainer | MEDIUM - cassa | gemello in entrata del rimborso G7.3 |
| **4** | Rendere `reopen` inverso esatto anche del nuovo incasso | MEDIUM - riconciliazione | evita nuova asimmetria |
| **5** | Allineare preview/payload/audit al nuovo ramo bilaterale | MEDIUM - trasparenza API | nessun default implicito lato FE |
| **6** | Aggiornare FDM/API docs/BUILD_LOG solo dopo implementazione reale | LOW - governance | evitare nuova divergenza doc-vs-code |

---

## 7. Test minimi raccomandati

1. `compute_settlement` con `servizio_reso > versato` -> ritorna un esito di **credito trainer**, non un write-off gia deciso.
2. `terminate` con `credito_trainer > 0` e nessuna scelta -> **422**.
3. `terminate` con `INCASSA_ORA`:
   - crea una sola `ENTRATA` diretta di conguaglio
   - incrementa `totale_versato`
   - chiude il contratto con `residuo == 0`
4. `terminate` con `RINUNCIA_ESPRESSA`:
   - non crea `ENTRATA`
   - scrive audit con importo rinunciato
   - chiude il contratto con `residuo == 0`
5. `reopen` dopo `INCASSA_ORA` ripristina esattamente stato e mastro pre-terminate.
6. Reportistica e predicati di cassa non confondono l'incasso da conguaglio trainer con rimborso o spesa.

---

## 8. Output di questo audit

L'audit porta a una conclusione netta:

> **Il modello del recesso e' corretto sul "quanto vale il servizio reso", ma incompleto sul "cosa fare quando il saldo e' a favore del trainer".**

La risposta tecnica corretta non e' alterare l'asse EROGATO, ne reintrodurre residui su contratti chiusi. La risposta corretta e':

- mantenere intatto il calcolo del valore reso;
- rendere esplicito il **credito trainer** come fatto economico;
- obbligare una scelta esplicita tra **incasso contestuale** e **rinuncia auditata**;
- mantenere `reopen` come inverso esatto.

Questo audit e' il fondamento del blocco di lavoro formalizzato in:

- [SPEC_TERMINAZIONE_BILATERALE_E_TUTELA_TRAINER.md](/C:/Users/gvera/Projects/FitManager_AI_Studio/docs/technical/SPEC_TERMINAZIONE_BILATERALE_E_TUTELA_TRAINER.md)

---

## 9. Stato di verifica

Verificato in audit documentale e code-reading contro:

- `docs/learning/BUILD_LOG.md` fino al follow-up backend del **2026-06-27**
- `api/CLAUDE.md`
- `docs/technical/FINANCIAL_DOMAIN_MODEL.md`
- `docs/technical/SPEC_G7.3_TERMINAZIONE_ENDPOINT.md`
- `docs/operations/AUDIT_CREDITI_RIMBORSO_2026-06-26.md`
- `api/services/contract_settlement.py`
- `api/routers/contracts.py`
- `api/schemas/financial.py`

**Limite dichiarato:** non sono stati eseguiti test runtime in questo step di sola documentazione; inoltre l'ambiente locale mantiene il problema gia emerso sul `venv` non eseguibile, quindi la validazione positiva del blocco avverra solo in fase implementativa con interpreter funzionante.
