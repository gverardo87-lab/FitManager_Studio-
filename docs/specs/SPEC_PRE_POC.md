# SPEC — Strategia e readiness pre-POC

**Stato:** 🟡 IN CORSO — D0, C0.0, G-MAC.1, C0.1 GREEN, FT.0, E0, D11, A0 e S1.0 chiusi;
prossimo gate founder E1 testo exit; prossimo gate tecnico S1.1 envelope; C0.2/G-MAC.2–5 in HOLD su trigger Mac; F0
in HOLD finché FT.1–FT.4 non sono chiusi
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
- il product marketing context è depositato e ratificato: `docs/business/PRODUCT_MARKETING_CONTEXT.md`
  (A0, 2026-09-03; `.agents/product-marketing-context.md` è solo un puntatore per le skill).

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

### D3 — Prima il codice applicativo, poi la distribuzione Windows

La sequenza è vincolante:

```text
scope freeze v1.0.15
→ portability canary macOS
→ core/security
→ application code freeze
→ distribuzione Windows
→ release freeze, seal e tag v1.0.15
→ consegna e prima POC Windows
→ C0.2 + distribuzione G-MAC solo su trigger commerciale diretto
```

L'**application code freeze** chiude comportamento e feature della release. Il **release freeze**
arriva dopo che build, installer e verifiche Windows sono entrati nel commit da sigillare. Il tag
`v1.0.15` identifica un solo commit e un solo artefatto Windows riproducibile. Una futura release Mac
usa una propria versione/tag e conserva gli stessi contratti applicativi congelati, senza
ricostruire `v1.0.15` da un commit differente.

### D4 — La portabilità macOS ARM64 è impegnata; la distribuzione è pull-based

Il portability hedge macOS ARM64 non è subordinato a ulteriori conferme commerciali: C0.1 e i minimi
adattamenti G-MAC.1 restano pre-S1 per impedire che G1 venga progettato Windows-only. La pipeline di
distribuzione, il packaging e la consegna macOS sono invece subordinati a evidenza commerciale
diretta. Daniele è un target tecnico noto, non un design partner verificato né un gate allo sviluppo.

Prima dell'application freeze sono autorizzati il portability canary e i minimi adattamenti runtime
che esso dimostra necessari, incluso G-MAC.1. Devono provare che dipendenze e G1 siano realmente
implementabili su ARM64 senza avviare packaging cliente. C0.1 GREEN è sufficiente ad aprire S1.
C0.2 e G-MAC.2–5 — target exact, pipeline di distribuzione, firma, notarizzazione, installazione e
validazione — restano in HOLD fino al trigger D11 e si aprono soltanto dopo la release Windows.

Il canary C0 usa tre checkpoint: C0.0 fissa il contratto; C0.1 costruisce su GitHub `macos-15` e
prova lo stesso artefatto su `macos-26`; C0.2 esegue un probe compilato e source-free sul target
esatto. Il runner non garantisce la patch `26.5.1`: un PASS solo CI resta condizionale. Sul Mac di
Daniele non arrivano sorgenti, toolchain, dati reali o chiavi private e il report non contiene
seriale, UUID o fingerprint. Soglie, matrice e DoD sono in `SPEC_G-MAC_CONSEGNA_MACOS.md` §3 C0.

C0 non è una sessione CRM licenziata. Senza licenza target-bound verifica soltanto `/health`
redatto, endpoint auth già esenti, superfici frontend corrispondenti e self-test tecnici compilati su
dati sintetici. Non modifica middleware/exempt/enforcement, non usa licenze fittizie e non attribuisce
PASS alle API CRM protette. Licenza reale e flusso applicativo end-to-end restano G-MAC.4.

Il percorso C0.1 → G-MAC.1 → C0.1 GREEN è pre-autorizzato. C0.2 e G-MAC.2–5 richiedono invece il
trigger e il nuovo GO previsti da D11; serve comunque escalation se cambiano scope, policy di
sicurezza, architettura, branch/remoto, support boundary o costi esterni materiali.

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
- C0.1 GREEN è chiuso; S1 è il prossimo gate tecnico e mantiene la precedenza sulle remediation FT;
- FT.1–FT.4 aprono in gate atomici dopo le fondazioni S1 G1/G2/G4, senza lavoro
  concorrente sugli stessi file, e devono chiudere prima di F0;
- FT.5 è una bonifica dati separata: richiede backup, dry-run, GO founder specifico e verifier; fino
  alla sua chiusura il database interessato non ottiene il Real-data GO;
- nessun code gate finanziario può essere dichiarato verde finché il runner pytest locale non è
  nuovamente eseguibile.

### D11 — POC Windows-first e distribuzione Mac su evidenza — 2026-09-01

Il founder ratifica la separazione tra capacità architetturale e canale di distribuzione:

- **C0.1 GREEN è fondamentale e pre-S1:** costruzione `macos-15`, esecuzione del medesimo artefatto
  su `macos-26`, supply chain finale ARM64, SQLCipher/Nuitka/frontend/auth e zero bypass;
- **C0.2 non blocca S1/F0/R1-WIN:** resta obbligatorio prima di aprire G-MAC.2 e non viene chiamato
  PASS finché il canary source-free non gira sul target esatto;
- **G-MAC.2–5 sono pull-based:** si aprono dopo la release Windows soltanto con un design partner Mac
  diretto e qualificato, protocollo pilota accettato, installazione assistita calendarizzata e
  capacità di supporto confermata;
- **Wave 0 Windows-first:** quando la nuova strategia commerciale autorizza W0/W1, la prima coorte
  usa Windows per mantenere omogenei onboarding, supporto e misurazione; un partecipante Mac entra
  soltanto attraverso il trigger precedente;
- **versioning univoco:** `v1.0.15` è la candidate Windows security/readiness. Una futura release Mac
  riceve un nuovo numero/tag secondo ADR-004, anche se riusa gli stessi contratti applicativi
  congelati. Nessun artefatto diverso viene pubblicato sotto `v1.0.15`.

Il trigger Mac è una decisione founder esplicita e verificabile, non deriva da un contatto indiretto,
da un prospect non qualificato o dal solo interesse tecnico. L'enrollment Apple può avanzare come
opzione amministrativa, ma non autorizza codice G-MAC.2–5 né spese senza il normale GO.

### D12 — S1 owner unico e G2 proof-first — 2026-09-04

Il founder apre S1 con due decisioni vincolanti:

- la POC compilata ha un solo trainer owner per installazione; il multi-tenant resta un harness di
  sicurezza nei test, non una funzionalità produttiva;
- G2 parte da una prova della catena client→FRP→Next→FastAPI e non si fida di header inoltrati senza
  una trust boundary dimostrata. Se il vero IP non è trasportabile in modo non spoofabile, il vecchio
  criterio non viene dichiarato GREEN: si presenta un Addendum con compensazioni prima del codice.

G1 e G5 sono un unico blocco perché una copia di backup plaintext annullerebbe la cifratura del CRM.
La casa esecutiva è `SPEC_S1_G1_G5_CIFRATURA_CRM.md`; S1.0 ratifica soltanto il contratto e non
modifica codice, schema, dipendenze o dati.

## 4. Classificazione stabile delle priorità

| Classe | Elementi | Regola |
|---|---|---|
| Fondamentali | C0.1 GREEN/G-MAC.1, G1–G4, G9–G11, Financial Truth FT.1–FT.4, candidate Windows, backup/restore, onboarding, misurazione | Senza questi la POC Windows non parte o non è interpretabile |
| Abilitatori | Recruitment founder-led, product truth, materiali approvati e rehearsal | Accelerano senza creare dipendenze esterne |
| Target di accettazione | Chiara/non-dev Windows, Daniele macOS | Verificano gli artefatti; non governano la roadmap |
| Exit | Alessio: E1–E4 in `SPEC_EXIT_ALESSIO.md` | Nessuna dipendenza; nessuna azione esterna o tecnica implicita |
| Upside | Contatto indiretto associato a Virgin, scala commerciale Mac, category creation | Non entra nel critical path senza rapporto diretto ed evidenza |
| HOLD | C0.2/G-MAC.2–5, nuova strategia commerciale, Wave 0 commerciale, P, FE non dimostrato, cleanup, refactor, nuove feature | Nuovo GO secondo la SPEC pertinente |

Una nuova informazione aggiorna questa matrice solo con evidenza o decisione founder esplicita. Non
riscrive automaticamente l'intera strategia.

## 5. Gate e scadenze

Le scadenze sono deadline di evidenza e decisione, mai autorizzazioni a saltare un gate. Dal
2026-08-29 le date non raggiunte del piano originario sono ritirate: l'ordine tecnico resta valido,
ma il calendario viene ripianificato dopo E1 e nella nuova strategia commerciale.

| Deadline | Gate | Evidenza di uscita |
|---|---|---|
| 2026-08-02 | **D0 — Autorità documentale** | questa SPEC viva; fonti concorrenti archiviate; INDEX/CLAUDE/LAUNCH_SCOPE e interlock allineati |
| 2026-09-03 ✅ | **C0.1 RED — Portability hedge CI** | run `33763567587`: build `macos-15` + smoke stesso artefatto `macos-26` verdi; RED falsificabile su `frpc.exe`, `lego.exe` e policy input wheel universal2 |
| 2026-09-03 ✅ | **G-MAC.1 + C0.1 GREEN** | commit `b7b74c2`, run `33772591605`: filename tunnel/ACME platform-conditional con parità Windows; policy wheel final-artifact-authoritative; build e smoke stesso artefatto entrambi success |
| HOLD trigger Mac | **C0.2 — Target exact source-free** | medesimo canary sul target M1/8 GB/Tahoe 26.5.1; obbligatorio prima di G-MAC.2, non blocca S1/F0/R1-WIN |
| 2026-09-03 ✅ | **A0 — Product truth founder-led** | CHIUSO: context + claims matrix ratificati riga per riga (`docs/business/PRODUCT_MARKETING_CONTEXT.md`); leggi competitor estratte (`LEGGI_COMPETITOR.md`); nessun claim esterno non sostenuto; zero dipendenze Alessio |
| 2026-09-04 ✅ | **S1.0 — G1/G5 docs-first** | owner unico, auth/DB boundary, envelope, recovery, migrazione e backup prescritti; ADR-013 Add. I; zero codice |
| Prossimo gate tecnico | **S1.1 — Primitive envelope** | RED→GREEN su envelope v1, scrypt/HKDF/AES-GCM e atomic write; nessun cambio boot |
| Dopo i gate S1 atomici | **S1 — Core/security** | G1/G2/G4 verdi; backup/restore coerenti; G9–G11 pronti per il real-data gate |
| Da ripianificare | **F0 — Application code freeze** | suite completa Windows + runtime Mac CI; FT.1–FT.4 chiusi; nessuna feature o finding release-critical aperto |
| 2026-08-29 | **E0 — Strategia exit Alessio** | ruolo e dipendenza ritirati; interlock documentale e `SPEC_EXIT_ALESSIO.md` ratificati; nessuna azione esterna o tecnica |
| Prossimo gate founder | **E1 — Testo comunicazione exit** | testo costruito e approvato col founder in `docs/`; nessun invio nel gate E1 |
| HOLD nuova strategia | **W0 — Protocollo Wave 0** | massimo tre candidati qualificati; ipotesi, metriche, calendario, support boundary e criteri stop scritti |
| Da ripianificare | **D1-WIN — Distribution engineering Windows** | installer Windows; clean install, upgrade, licenza, process lifecycle e data preservation verificati |
| Da ripianificare | **R1-WIN — Release freeze v1.0.15** | candidate Windows e2e, restore, FRP/TLS, seal, manifest e tag univoco `v1.0.15` |
| HOLD trigger Mac | **G-MAC.2–5 — Distribuzione Mac** | dopo R1-WIN e C0.2: nuova release/versione, artifact ARM64 firmato/notarizzato, rehearsal, licenza, upgrade e lifecycle verificati |
| HOLD nuova strategia | **M0 — Field delivery** | target e canale di consegna nuovamente confermati; dati reali solo dopo GO security |
| HOLD nuova strategia | **W1 — Wave 0 live** | massimo tre design partner attivati e misurazione avviata |
| HOLD nuova strategia | **W2 — Scale checkpoint** | decisione evidence-based su espansione 5→10 |

Se C0.1 scopre un'incompatibilità nel portability hedge, il finding viene classificato e chiuso nel
perimetro minimo necessario prima di S1 oppure escalato se cambia architettura/scope. C0.2 e i finding
di distribuzione Mac spostano il solo milestone Mac e non la release Windows. Sicurezza, test e
tracciabilità non vengono ridotti.

## 6. Sequenza dei gate repository

Un solo gate repository è attivo alla volta, secondo `AGENTS.md`. Attività esterne possono avanzare
in calendario, ma non sono «zero ore founder» e non autorizzano lavoro concorrente sugli stessi file.

1. D0 docs-first e checkpoint remoto pulito;
2. C0.0 contratto target docs-first e checkpoint remoto pulito;
3. FT.0 Financial Truth docs-only e checkpoint remoto pulito;
4. E0 strategia exit Alessio docs-only e checkpoint remoto pulito;
5. E1 testo comunicazione exit, docs-only e senza invio esterno;
6. C0.1 canary RED — CHIUSO 2026-09-03, run `33763567587`, commit `5ca635e`;
7. G-MAC.1 remediation runtime/policy wheel + re-run C0.1 GREEN — CHIUSO 2026-09-03, commit
   `b7b74c2`, run `33772591605`;
8. A0 product truth founder-led, docs-only e checkpoint remoto pulito;
9. S1.0 G1/G5 docs-first — CHIUSO 2026-09-04; S1.1–S1.6 implementano G1/G5 in gate atomici
   secondo ADR-013 Add. I e `SPEC_S1_G1_G5_CIFRATURA_CRM.md`; seguono G2 proof-first e G4 in
   SPEC/gate separati; dopo G1/G2/G4 e prima di F0 si inseriscono FT.1–FT.4, ciascuno con
   checkpoint proprio;
10. F0 application freeze;
11. D1-WIN distribuzione Windows;
12. R1-WIN build/seal/tag `v1.0.15`;
13. M0-WIN consegna e registrazione Windows, dopo nuova strategia commerciale e GO security;
14. W1 prima Wave 0 Windows;
15. soltanto su trigger D11: C0.2 → G-MAC.2–5 in gate separati → nuova release/tag Mac.

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
- frontend: `docs/specs/hold/SPEC_FRONTEND_CORE_INTUITIVITA.md`;
- verità finanziaria: `docs/specs/SPEC_G8.4_TRASPARENZA_FINANZIARIA_FE.md` Addendum FT +
  `docs/incidents/INC-2026-08-05-grafico-cassa-netting-rimborsi.md`;
- blocco P in HOLD: `docs/specs/hold/SPEC_P_PRESTAZIONI_SINGOLE_E_PORTAFOGLIO.md`;
- verità prodotto: `MANIFESTO.md` + `docs/business/PRODUCT_MARKETING_CONTEXT.md` (A0, claims matrix);
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

## 13. Addendum D11 — Windows-first, Mac pull-based — 2026-09-01

- separati il portability hedge pre-S1 e la distribuzione commerciale Mac;
- mantenuti C0.1/G-MAC.1 come unico interlock Mac prima di S1 e spostati C0.2/G-MAC.2–5 dopo
  R1-WIN, in HOLD su trigger diretto;
- resa `v1.0.15` una release Windows univoca; vietato ricostruire lo stesso numero da una baseline
  diversa per la futura distribuzione Mac;
- definita la prima POC Windows-first, senza autorizzare W0/W1 prima della nuova strategia
  commerciale e dei normali gate security;
- definito il trigger Mac come design partner diretto e qualificato, protocollo accettato,
  installazione calendarizzata e capacità di supporto confermata;
- preservati integralmente boundary licenza C0, privacy del probe, G1–G4/G9–G11, parità Windows e
  requisiti Developer ID/notarizzazione per qualunque futura consegna Mac;
- nessuna comunicazione esterna, spesa Apple, modifica codice, artifact o consegna eseguita in D11.

## 14. Addendum A0 — Product truth founder-led — 2026-09-03

- anticipato A0 per decisione founder esplicita (docs-only, nessun conflitto coi gate tecnici;
  E1 lasciato intatto come prossimo gate founder dell'exit);
- ratificate riga per riga le tre righe gialle della claims matrix: uso reale quotidiano ATTESTATO
  dal founder (wording onesto, consegna v1.0.14 resta gate aperto); pricing DIFFERITO (il kit
  design partner non espone prezzi, coerente con l'HOLD della strategia commerciale); «email
  automatiche» declassata a NON DICHIARABILE su evidenza di codice (zero SMTP in `api/`);
- aggiunto guardrail competitor: claim assoluti «nessun competitor italiano» vietati finché la
  lacuna N-1 (vendor italiani mai censiti) non è chiusa da ricerca dedicata;
- depositi: `docs/business/PRODUCT_MARKETING_CONTEXT.md` (SSoT claims, tracciata) +
  `docs/business/LEGGI_COMPETITOR.md` (W1-W11, L1-L6, lacune N estratte dagli archivi);
- nessun materiale esterno prodotto o inviato; nessun claim nuovo pubblicato; nessuna modifica
  applicativa.

## 15. Consuntivo S1.0 — G1/G5 docs-first — 2026-09-04

- ratificato un solo trainer owner per installazione compilata, senza ridurre i test IDOR;
- risolto il boundary auth/DB: unwrap della DEK, engine candidato, verifica email+bcrypt+account,
  manutenzione e solo infine pubblicazione/JWT;
- congelati envelope v1, state machine, recovery confermata, migrazione journaled, backup bundle e
  matrice di accettazione nella SPEC G1/G5;
- ratificato G2 proof-first: nessun header client diventa fidato per assunzione e nessun falso GREEN
  se il criterio real-IP richiede un Addendum;
- nessun codice, schema, dipendenza, dato, artefatto o infrastruttura modificato in S1.0.

## 16. Chiusura della SPEC

La SPEC chiude quando la Wave 0 è attiva, le evidenze iniziali sono raccolte e la decisione di scala è
registrata. A quel punto riceve consuntivo, fold-back nelle SSoT toccate e viene spostata in
`docs/archive/specs/` nello stesso gate docs di chiusura.
