# SPEC — Strategia e readiness pre-POC

**Stato:** 🟡 IN CORSO — D0, C0.0, FT.0 ed E0 chiusi; prossimo gate founder E1 testo exit;
prossimo gate tecnico C0.1 canary RED; F0 in HOLD finché FT.1–FT.4 non sono chiusi
**Data di ratifica founder:** 2026-07-31
**Branch:** `FitManager_Studio`
**Tipo:** regia operativa pre-POC; non duplica le specifiche tecniche sottostanti
**Orizzonte:** 31 luglio → seconda metà di settembre 2026
**Autorità:** `AGENTS.md` → `MANIFESTO.md` → `LAUNCH_SCOPE.md` → questa SPEC → SPEC/ADR/SSoT di dettaglio

> Questo è l'unico piano operativo vivo per il periodo pre-POC. Audit, roadmap e piani commerciali
> precedenti sono materiale storico: spiegano come si è arrivati qui, ma non determinano più priorità,
> scope o calendario. Le SSoT tecniche restano autorevoli sui propri criteri di accettazione.

## 1. North Star

Entro settembre FitManager deve poter avviare un utilizzo reale, sicuro e misurabile del core con
trainer qualificati, producendo evidenza su adozione, valore percepito e disponibilità a pagare.

La POC non serve a dimostrare quante feature esistono. Serve a ridurre tre incertezze, in ordine:

1. il trainer attiva e usa il workflow core;
2. l'uso produce valore operativo percepibile;
3. il valore è sufficiente a sostenere una decisione di acquisto.

Il percorso formativo, la categoria «PT Evoluto», la community e il contributo del partner sono
esperimenti separati o secondari: non devono rendere il risultato prodotto illeggibile.

## 2. Ground truth al freeze strategico

- branch `FitManager_Studio`, HEAD di partenza `459a75d5`, remoto allineato;
- versione sorgente `1.0.14`; la candidate `v1.0.15` non è ancora costruita né consegnata;
- R0.1–R0.4 chiusi e consuntivati;
- G3/TLS pubblico core+live verde, da ripetere sull'artefatto candidato;
- G1 è ancora assente dal codice di produzione; G2 è aperto; G4 è parziale;
- la consegna con dati reali resta vincolata a G1–G4 e l'onboarding del primo atleta anche a G9–G11;
- il blocco P è nuovo sviluppo, non remediation pre-POC;
- al 2026-08-29 non esiste evidenza di uso autonomo, hands-on o data-bearing del prodotto da parte di
  Alessio, né di clienti o pipeline qualificata prodotti in circa quattro mesi; nessuna interlocuzione
  sostanziale è nota da circa metà luglio. Il ruolo partner è ritirato e l'exit è governata da
  `SPEC_EXIT_ALESSIO.md`;
- Daniele è il primo target macOS noto: MacBook Air M1 2020, ARM64, 8 GB, macOS Tahoe 26.5.1,
  configurazione confermata il 2026-08-02; foto e identificatori hardware non sono conservati nel
  repository o nei log. Il potenziale rapporto Virgin è upside non validato;
- non esiste ancora `.agents/product-marketing-context.md`.

I fatti cambiano solo con evidenza. Le valutazioni founder su fiducia, opportunità e priorità sono
decisioni strategiche dichiarate, non metriche osservate.

## 3. Decisioni ratificate

### D1 — Una sola regia operativa

Questa SPEC sostituisce ogni roadmap o analisi pre-POC come fonte di scheduling. `docs/INDEX.md`,
`CLAUDE.md` e le SPEC vive devono puntare qui. Se divergono, questa SPEC prevale fino al fold-back.

### D2 — Scope applicativo della v1.0.15

La `v1.0.15` è la release di sicurezza e readiness pre-POC. Comprende:

- G1, G2 e completamento G4;
- G3 già verde, con ripetizione dei probe sulla candidate;
- G9–G11 prima del primo dato atleta reale;
- backup/restore e recovery coerenti con G1;
- minimi adattamenti runtime necessari a non congelare una soluzione Windows-only;
- fix release-critical dimostrati da test o rehearsal.
- remediation Financial Truth FT.1–FT.4, dimostrata dall'audit del grafico Cassa del 24 luglio.

Non comprende P, nuove macro-feature, cleanup generalisti, refactor monolitici o framework frontend
non richiesti da evidenza utente.

### D3 — Prima il codice applicativo, poi la distribuzione

La sequenza è vincolante:

```text
scope freeze v1.0.15
→ portability canary macOS
→ core/security
→ application code freeze
→ distribuzione Windows + G-MAC
→ release freeze, seal e tag
→ consegna
```

L'**application code freeze** chiude comportamento e feature della release. Il **release freeze**
arriva dopo che build, installer e verifiche di entrambe le piattaforme sono entrati nel commit da
sigillare. Il tag `v1.0.15` deve identificare la stessa baseline dei due artefatti.

### D4 — macOS ARM64 è un deliverable impegnato

macOS ARM64 non è subordinato a ulteriori conferme commerciali. Daniele è il primo target di
accettazione e consegna, non il centro della strategia né un gate allo sviluppo. Il percorso conserva
valore come capacità di distribuzione riutilizzabile; non è più legato alla credibilità o alla
relazione commerciale con Alessio. Una consegna a Daniele richiede contatto diretto e disponibilità
verificata, oltre ai normali gate tecnici e di sicurezza.

Prima dell'application freeze sono autorizzati il portability canary e i minimi adattamenti runtime
che esso dimostra necessari, incluso G-MAC.1. Devono provare che dipendenze e G1 siano realmente
implementabili su ARM64 senza avviare packaging cliente. G-MAC.2–5 — pipeline di distribuzione,
firma, notarizzazione, installazione e validazione — aprono dopo l'application freeze.

Il canary C0 usa tre checkpoint: C0.0 fissa il contratto; C0.1 costruisce su GitHub `macos-15` e
prova lo stesso artefatto su `macos-26`; C0.2 esegue un probe compilato e source-free sul target
esatto. Il runner non garantisce la patch `26.5.1`: un PASS solo CI resta condizionale. Sul Mac di
Daniele non arrivano sorgenti, toolchain, dati reali o chiavi private e il report non contiene
seriale, UUID o fingerprint. Soglie, matrice e DoD sono in `SPEC_G-MAC_CONSEGNA_MACOS.md` §3 C0.

C0 non è una sessione CRM licenziata. Senza licenza target-bound verifica soltanto `/health`
redatto, endpoint auth già esenti, superfici frontend corrispondenti e self-test tecnici compilati su
dati sintetici. Non modifica middleware/exempt/enforcement, non usa licenze fittizie e non attribuisce
PASS alle API CRM protette. Licenza reale e flusso applicativo end-to-end restano G-MAC.4.

L'intero percorso definito è pre-autorizzato. Non servono nuovi GO founder tra gate già descritti;
serve escalation solo se cambiano scope, policy di sicurezza, architettura, branch/remoto, support
boundary o costi esterni materiali.

Support boundary pre-POC: Apple Silicon ARM64, configurazioni macOS testate, pilot assistito. Intel,
self-service generalizzato e parità non verificata con ogni configurazione Mac restano fuori scope.

### D5 — Nessuna deroga sui dati reali

Nessun trainer riceve una build per uso data-bearing senza G1–G4. Nessun atleta reale viene onboardato
senza G1–G4 e G9–G11. Una technical preview usa soltanto dati sintetici e non costituisce consegna
operativa. Non può disabilitare o aggirare l'enforcement della licenza per ampliare uno smoke test.
Deadline e opportunità commerciali non possono trasformarsi in waiver impliciti.

### D6 — Il blocco P è in HOLD

P1–P6 non aprono prima dei dati della Wave 0 e di una nuova decisione founder. La SPEC resta viva per
preservare le decisioni già ratificate; non appartiene alla `v1.0.15`.

### D7 — Frontend evidence-driven

FE-2–FE-4 e cleanup estesi restano in HOLD. Un fix frontend entra pre-POC soltanto se un test, un
rehearsal o un utente pilota dimostra che blocca o falsifica demo, onboarding o workflow core.

Il grafico giornaliero Cassa del 24 luglio soddisfa il criterio: rappresenta come `0` Entrate e
`204,25 €` Uscite una giornata con `333,25 €` di inflow e `537,50 €` di rimborsi. Non è redesign:
è una remediation di verità finanziaria osservata su dati reali, con ledger e saldo corretti.

### D8 — Exit Alessio; percorso founder-led

Dal 2026-08-29 Alessio non è partner, abilitatore, recruiter, demo owner o dipendenza del percorso
pre-POC. L'uscita commerciale, contrattuale e operativa segue `SPEC_EXIT_ALESSIO.md`; nessuna vecchia
proposta di percentuale, revenue share o equity è autorizzata dalla permanenza nei documenti storici.

Demo, claim, recruiting e product truth sono founder-led fino alla ratifica della nuova strategia
commerciale. Il product marketing context agent-neutral viene auto-draftato dal repository e corretto
col founder. L'eventuale materiale raw ricevuto da terzi può essere classificato soltanto come
evidenza o ipotesi, senza attribuirgli autorità e nel rispetto degli obblighi di riservatezza. Nessun
claim esterno nuovo è autorizzato prima della revisione.

### D9 — POC a coorti

La Wave 0 coinvolge al massimo tre design partner. L'espansione a cinque e poi fino a dieci avviene
solo dopo un checkpoint che confermi: security gate intatto, nessun P0/P1 aperto, onboarding core
riuscito, carico di supporto sostenibile e misurazione utilizzabile. I risultati delle coorti non
vengono aggregati ignorando date o condizioni diverse.

### D10 — Financial Truth è release-critical, non un filone parallelo

L'audit read-only del 2026-08-05 sul 24 luglio ha escluso corruzione dell'asse DENARO ma ha provato
un P1 attivo, un P1 latente e quattro gap P2 correlati dopo lo sviluppo conguagli/rimborsi. La casa
tecnica è l'Addendum FT in `SPEC_G8.4_TRASPARENZA_FINANZIARIA_FE.md`; l'incident è
`INC-2026-08-05-grafico-cassa-netting-rimborsi.md`. Non nasce una roadmap concorrente né una nuova
ADR: le leggi esistenti su cassa bidirezionale, nessun netto nudo, auditabilità e determinismo sono
sufficienti.

- FT.0 è il gate docs-only che registra baseline, finding, canary e interlock;
- C0.1 resta il prossimo gate esecutivo: il finding non corrompe dati e non invalida il canary Mac;
- FT.1–FT.4 aprono in gate atomici dopo C0.2/A0 e dopo le fondazioni S1 G1/G2/G4, senza lavoro
  concorrente sugli stessi file, e devono chiudere prima di F0;
- FT.5 è una bonifica dati separata: richiede backup, dry-run, GO founder specifico e verifier; fino
  alla sua chiusura il database interessato non ottiene il Real-data GO;
- nessun code gate finanziario può essere dichiarato verde finché il runner pytest locale non è
  nuovamente eseguibile.

## 4. Classificazione stabile delle priorità

| Classe | Elementi | Regola |
|---|---|---|
| Fondamentali | G1–G4, G9–G11, Financial Truth FT.1–FT.4, candidate, backup/restore, onboarding, misurazione, macOS ARM64 consegnabile | Senza questi la POC non parte o non è interpretabile |
| Abilitatori | Recruitment founder-led, product truth, materiali approvati e rehearsal | Accelerano senza creare dipendenze esterne |
| Target di accettazione | Chiara/non-dev Windows, Daniele macOS | Verificano gli artefatti; non governano la roadmap |
| Exit | Alessio: E1–E4 in `SPEC_EXIT_ALESSIO.md` | Nessuna dipendenza; nessuna azione esterna o tecnica implicita |
| Upside | Contatto indiretto associato a Virgin, scala commerciale Mac, category creation | Non entra nel critical path senza rapporto diretto ed evidenza |
| HOLD | Nuova strategia commerciale, Wave 0 commerciale, P, FE non dimostrato, cleanup, refactor, nuove feature | Nuovo GO secondo la SPEC pertinente |

Una nuova informazione aggiorna questa matrice solo con evidenza o decisione founder esplicita. Non
riscrive automaticamente l'intera strategia.

## 5. Gate e scadenze

Le scadenze sono deadline di evidenza e decisione, mai autorizzazioni a saltare un gate. Dal
2026-08-29 le date non raggiunte del piano originario sono ritirate: l'ordine tecnico resta valido,
ma il calendario viene ripianificato dopo E1 e nella nuova strategia commerciale.

| Deadline | Gate | Evidenza di uscita |
|---|---|---|
| 2026-08-02 | **D0 — Autorità documentale** | questa SPEC viva; fonti concorrenti archiviate; INDEX/CLAUDE/LAUNCH_SCOPE e interlock allineati |
| Da ripianificare | **C0 — Scope + portability canary** | C0.0 contratto target e boundary licenza chiusi; C0.1 build `macos-15` + esecuzione medesimo artefatto `macos-26`; C0.2 probe source-free su M1/8 GB/Tahoe 26.5.1; SQLCipher/G1, Nuitka, frontend ARM64, auth exempt, memoria e display verificati senza packaging cliente né claim sul CRM protetto |
| Da ripianificare | **A0 — Product truth founder-led** | context agent-neutral e claims matrix approvata; nessun claim esterno non sostenuto; nessuna dipendenza da materiale o readiness Alessio |
| Da ripianificare | **S1 — Core/security** | G1/G2/G4 verdi; backup/restore coerenti; G9–G11 pronti per il real-data gate |
| Da ripianificare | **F0 — Application code freeze** | suite completa Windows + runtime Mac CI; FT.1–FT.4 chiusi; nessuna feature o finding release-critical aperto |
| 2026-08-29 | **E0 — Strategia exit Alessio** | ruolo e dipendenza ritirati; interlock documentale e `SPEC_EXIT_ALESSIO.md` ratificati; nessuna azione esterna o tecnica |
| Prossimo gate founder | **E1 — Testo comunicazione exit** | testo costruito e approvato col founder in `docs/`; nessun invio nel gate E1 |
| HOLD nuova strategia | **W0 — Protocollo Wave 0** | massimo tre candidati qualificati; ipotesi, metriche, calendario, support boundary e criteri stop scritti |
| Da ripianificare | **D1 — Distribution engineering** | installer Windows e artifact Mac ARM64 firmato/notarizzato; clean install, upgrade, licenza, process lifecycle e data preservation verificati |
| Da ripianificare | **R1 — Release freeze** | candidate e2e, restore, FRP/TLS, seal, manifest e tag `v1.0.15` dalla stessa baseline |
| HOLD nuova strategia | **M0 — Field delivery** | target e canale di consegna nuovamente confermati; dati reali solo dopo GO security |
| HOLD nuova strategia | **W1 — Wave 0 live** | massimo tre design partner attivati e misurazione avviata |
| HOLD nuova strategia | **W2 — Scale checkpoint** | decisione evidence-based su espansione 5→10 |

Se C0 scopre un'incompatibilità Mac, il finding diventa requisito della v1.0.15: non riapre la
decisione strategica G-MAC. Se un gate supera la deadline, slitta il milestone dipendente o si riduce
lo scope non fondamentale; sicurezza, test e tracciabilità non vengono ridotti.

## 6. Sequenza dei gate repository

Un solo gate repository è attivo alla volta, secondo `AGENTS.md`. Attività esterne possono avanzare
in calendario, ma non sono «zero ore founder» e non autorizzano lavoro concorrente sugli stessi file.

1. D0 docs-first e checkpoint remoto pulito;
2. C0.0 contratto target docs-first e checkpoint remoto pulito;
3. FT.0 Financial Truth docs-only e checkpoint remoto pulito;
4. E0 strategia exit Alessio docs-only e checkpoint remoto pulito;
5. E1 testo comunicazione exit, docs-only e senza invio esterno;
6. C0.1 canary RED;
7. G-MAC.1 remediation runtime dimostrata dal canary, in gate codice separato, e re-run C0.1 GREEN;
8. C0.2 probe source-free sul target esatto;
9. A0 product truth founder-led, docs-only e checkpoint remoto pulito;
10. S1 in gate tecnici atomici secondo ADR-013 e Security Gate; dopo G1/G2/G4 e prima di F0 si
   inseriscono FT.1–FT.4, ciascuno con checkpoint proprio;
11. F0 application freeze;
12. D1 distribuzione Windows e macOS in gate separati ma sulla stessa baseline applicativa;
13. R1 build/seal/tag;
14. M0 consegne e registrazione, dopo nuova conferma commerciale dei target;
15. W1 Wave 0, dopo la nuova strategia commerciale.

FT.5 non è un gate di codice e non viene assorbito in FT.1–FT.4: è una manutenzione controllata del
database interessato, dopo i relativi checkpoint e prima del suo Real-data GO, con autorizzazione
specifica alla mutazione.

E2–E4 dell'exit Alessio seguono le precondizioni e le autorizzazioni di `SPEC_EXIT_ALESSIO.md`.
Recruiting, enrollment Apple e appuntamenti restano founder-led o richiedono una nuova assegnazione
esplicita. Ogni modifica repository relativa viene chiusa in un gate proprio: il parallelismo
organizzativo non viola il checkpoint Git singolo.

## 7. Definition of Done dei milestone esterni

### Exit Alessio

- E1 testo approvato senza invio implicito;
- E2 verifica contrattuale e notifica concluse sul canale corretto;
- E3 dati, licenza, tunnel e accessi portati a stato finale verificato;
- E4 fonti vive e nuova strategia commerciale allineate;
- nessun milestone pre-POC dipende da Alessio durante l'intero percorso.

### macOS consegnabile

- build nativa ARM64 su `macos-15`, esecuzione del medesimo artefatto su `macos-26` e cross-check
  sul target M1/8 GB/Tahoe 26.5.1, senza sorgenti sul Mac cliente;
- budget memoria C0 rispettato e flusso core usabile alle risoluzioni target;
- Developer ID e notarizzazione valide sull'artefatto consegnato;
- clean install e avvio senza workaround di quarantena destinati al cliente;
- fingerprint/licenza, health, login, tunnel e portale verificati;
- upgrade preserva `data/` e `license.key`;
- backup/restore e G1 verificati;
- chiusura lascia zero processi orfani;
- runbook e deployment registry aggiornati.

Un artifact che parte soltanto sul runner CI non è consegnabile; una label `macos-26` non sostituisce
la verifica sulla patch esatta del primo target.

### Real-data GO

- G1–G4 soddisfatti;
- G9–G11 disponibili;
- candidate installata e verificata;
- backup/recovery provati;
- FT.1–FT.4 chiusi e nessun P1/P2 Financial Truth aperto sul codice candidato;
- FT.5 chiuso per ogni database data-bearing interessato da un'anomalia censita;
- nessuna eccezione implicita o promessa commerciale usata come waiver.

## 8. Anti-scope fino alla Wave 0

- niente P1–P6;
- niente refactor di monoliti frontend;
- niente bonifica dead-code generalista;
- niente nuova macro-feature;
- niente supporto macOS Intel;
- niente `.app`/distribuzione self-service se richiede cambiare il layout ratificato pre-pilota;
- niente nuova policy prodotto inventata per chiudere una deadline;
- niente nuovi audit generalisti pre-POC: solo verifier di gate o finding da evidenza reale.

## 9. Stop ed escalation

Il lavoro prosegue senza nuova conferma founder entro scope. Si ferma e richiede decisione solo se:

- un finding cambia una regola di dominio o una policy di sicurezza;
- la parità Windows richiede una regressione;
- il support boundary Mac deve allargarsi;
- emerge un costo esterno materiale non già autorizzato;
- la baseline v1.0.15 deve cambiare dopo l'application freeze;
- una richiesta commerciale introduce dati reali prima dei gate;
- branch, remoto o scope del gate cambiano.

Un semplice ritardo, test rosso o difficoltà implementativa non è da solo una nuova decisione
strategica: si diagnostica, si corregge o si riporta il milestone dipendente.

## 10. Fonti di dettaglio

- sicurezza e real-data gate: `docs/technical/PRE_DELIVERY_SECURITY_GATE.md` + ADR-013;
- release: `docs/operations/RELEASE_CHECKLIST.md` + ADR-004;
- macOS: `docs/specs/SPEC_G-MAC_CONSEGNA_MACOS.md` + ADR-026;
- frontend: `docs/specs/SPEC_FRONTEND_CORE_INTUITIVITA.md`;
- verità finanziaria: `docs/specs/SPEC_G8.4_TRASPARENZA_FINANZIARIA_FE.md` Addendum FT +
  `docs/incidents/INC-2026-08-05-grafico-cassa-netting-rimborsi.md`;
- blocco P in HOLD: `docs/specs/SPEC_P_PRESTAZIONI_SINGOLE_E_PORTAFOGLIO.md`;
- verità prodotto: `MANIFESTO.md` e, dopo il gate dedicato, `.agents/product-marketing-context.md`;
- exit relazione Alessio: `docs/specs/SPEC_EXIT_ALESSIO.md`;
- storia di sviluppo: `docs/learning/BUILD_LOG.md`.

## 11. Consuntivo D0 — 2026-07-31

- ratificate D1–D9 e le deadline D0→W2;
- allineati entry point, launch scope, release/security gate, INDEX, ADR-026 e interlock delle SPEC
  FE, P e G-MAC;
- archiviate con esito sei fotografie concorrenti: due audit pre-POC, tre piani business/partner e
  la roadmap post-launch;
- preservati Business Plan e Financial Model come baseline numerica pre-validazione, senza autorità
  sullo scheduling corrente;
- verificati Ruff, lifecycle documentale, copertura INDEX 10/10, riferimenti vivi, link operativi e
  le 24 asserzioni statiche del canary R0.4;
- nessun codice applicativo, schema, dato, release artifact o claim commerciale è stato modificato
  o prodotto in D0.

Il runner pytest locale non è stato disponibile perché `venv/Scripts/python.exe` punta a un
interprete Windows Store rimosso. Per questo gate docs-only le asserzioni del canary R0.4 sono state
replicate in PowerShell e controllate una per una; la riparazione della venv resta un prerequisito
operativo del prossimo gate C0, che richiede prove runtime reali.

## 12. Addendum E0 — Exit Alessio — 2026-08-29

- ritirato il ruolo Alessio come Industry Partner, abilitatore e dipendenza pre-POC;
- ritirato A1 Alessio readiness; A0 resta esclusivamente founder-led;
- messe in HOLD Wave 0, field delivery e scale checkpoint fino alla nuova strategia commerciale;
- separate capacità tecnica G-MAC e opportunità commerciale indiretta: nessun credito, relazione
  Virgin o target di consegna deriva dal solo contatto di secondo grado;
- aperta `SPEC_EXIT_ALESSIO.md` con E1 testo, E2 notifica, E3 offboarding tecnico ed E4 reset
  commerciale come gate distinti;
- nessuna comunicazione esterna, revoca, modifica infrastrutturale, nuova politica commerciale o
  modifica applicativa eseguita in E0.

## 13. Chiusura della SPEC

La SPEC chiude quando la Wave 0 è attiva, le evidenze iniziali sono raccolte e la decisione di scala è
registrata. A quel punto riceve consuntivo, fold-back nelle SSoT toccate e viene spostata in
`docs/archive/specs/` nello stesso gate docs di chiusura.
