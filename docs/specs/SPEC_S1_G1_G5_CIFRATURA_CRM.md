# SPEC — S1 G1/G5: cifratura password-bound di crm.db e recovery

**Stato:** APERTA E RATIFICATA — S1.0 docs-first chiuso il 2026-09-04; prossimo gate S1.1
primitive envelope RED→GREEN; nessun codice G1/G5 implementato da questa SPEC
**Data:** 2026-09-04
**Branch:** `FitManager_Studio`
**Blocco:** S1 / G1 + G5, inseparabili
**Autorità:** `AGENTS.md` → `SPEC_PRE_POC.md` → ADR-013 + Addendum I →
`PRE_DELIVERY_SECURITY_GATE.md` → questa SPEC
**Decisioni founder:** owner unico per installazione compilata; G2 proof-first e separato da questo
blocco

> Questa SPEC prescrive un solo blocco: rendere il database CRM e il suo ciclo di
> backup/recovery sicuri a riposo. Non autorizza G2, G4, dati reali, release o distribuzione.

---

## 0. Impact map

- **Obiettivo:** soddisfare G1 e G5 con SQLCipher, envelope DEK–KEK password-bound, recovery
  obbligatoria e boot a due fasi, senza creare copie plaintext nei percorsi ordinari.
- **Layer previsti:** configurazione/path `data/`; database business e session dependency; auth e
  setup; lifespan; backup/restore; frontend setup/login/recovery; build Windows; test e runbook.
- **File probabili, non esaustivi:** `api/database.py`, `api/main.py`, `api/auth/*`,
  `api/routers/backup.py`, nuovi servizi security mirati, `frontend/src/types/api.ts`, superfici
  setup/login/settings, test G1/G5 e build Nuitka.
- **Invarianti:** cataloghi ADR-007 invariati; Bouncer/IDOR e licenza invariati; dati persistenti
  solo in `data/`; nessun path assoluto; portale pre-unlock fail-closed; CRM usabile senza AI;
  nessun fallback plaintext in compiled mode; dev/test seam preservato.
- **Esclusioni:** G2/G4, G6–G12, G-MAC.2–5, FT.1–FT.5, feature, refactor generalisti, dati reali,
  migrazione del database di Chiara e qualunque consegna.

**Tesi falsificabile:** in una build compilata, possedere `crm.db`, un backup o i soli metadati
envelope non permette di leggere dati senza password valida o recovery key; ogni transizione
critica fallisce lasciando una copia valida e recuperabile, e nessun endpoint dati opera prima di
un unlock autenticato completo.

---

## 1. Ground truth al gate S1.0

Verifica read-only del 2026-09-04:

1. `api/database.py` costruisce oggi l'engine business a import-time contro `DATABASE_URL` SQLite.
2. `api/main.py` esegue auto-backup, `create_db_and_tables`, schema sync e integrity check prima di
   qualsiasi login.
3. `api/routers/backup.py` importa l'engine business direttamente e usa `sqlite3` standard per
   backup, restore e safety copy.
4. `/auth/setup-status`, register e login dipendono tutti da `get_session()`; l'hash bcrypt
   dell'owner vive quindi nello stesso DB che G1 deve sigillare.
5. `/auth/register` consente tecnicamente più trainer, benché il prodotto sia una singola istanza
   locale per trainer.
6. SQLCipher non è ancora una dipendenza del runtime di produzione; il canary C0.1 usa
   `sqlcipher3==0.6.2` e ha già provato create/write/reopen, wrong-key e assenza plaintext in un
   artefatto Nuitka ARM64. ADR-013 registra inoltre lo spike Windows Nuitka.
7. La suite applicativa di partenza è verde: ultimo checkpoint documentato `929 passed`, Ruff
   PASS, origin allineato.

Conseguenza: G1 non è uno swap di driver. Richiede una boundary esplicita per stato, engine,
autenticazione, manutenzione, migrazione e backup.

---

## 2. Decisioni prescrittive

### D1 — Owner unico per installazione compilata

Una installazione licenziata contiene **un solo trainer owner**. Non esistono operatori secondari
nel perimetro POC.

- `/auth/register` è disponibile soltanto nello stato `UNINITIALIZED`.
- Dopo la creazione dell'owner, un nuovo register fallisce in modo generico e non crea righe.
- Un database legacy con più di un trainer entra in `MANUAL_REVIEW_REQUIRED`: nessuna scelta
  automatica dell'owner e nessuna migrazione. Un DB con zero trainer è inizializzabile come nuovo
  soltanto se tutte le tabelle business risultano vuote; altrimenti richiede review manuale.
- I test multi-tenant restano obbligatori come harness IDOR, ma costruiscono i trainer attraverso
  fixture/dependency override; non riaprono il register di produzione.
- Una futura installazione multi-operatore richiede nuova decisione e nuova SPEC; non è un'opzione
  dormiente di S1.

### D2 — Modalità compilata cifrata senza downgrade

- In compiled mode `crm.db` è sempre SQLCipher dopo setup/migrazione.
- Un file plaintext inatteso non viene aperto come fallback: entra nel flusso di migrazione o in
  errore recuperabile.
- Errori di driver, envelope o chiave non autorizzano SQLite standard.
- Dev mode può conservare il database plaintext previsto da ADR-013, ma il controller deve essere
  costruibile esplicitamente in modalità cifrata nei test d'integrazione: `is_compiled()` non può
  rendere il percorso produttivo non testabile.
- Cataloghi `catalog.db` e `nutrition.db` mantengono il modello ADR-007 read-only; non condividono
  DEK, envelope o recovery del CRM.

### D3 — DEK stabile e envelope versionato

- Una DEK casuale da 32 byte è la raw key SQLCipher dell'installazione.
- La DEK resta stabile durante cambio password e recovery ordinari: cambia il wrapping, non si
  esegue `PRAGMA rekey` dell'intero DB.
- La DEK non viene derivata direttamente dalla password, non viene scritta in chiaro e non viene
  inserita in log, eccezioni, URL o telemetria.
- Password e recovery key producono KEK indipendenti che avvolgono la stessa DEK con AES-256-GCM.
- Envelope e DB sono legati da un `database_id` casuale e da AAD autenticato; envelope di una
  installazione non può essere sostituito con quello di un'altra senza fallimento.
- Il medesimo `database_id` vive in metadati interni al DB cifrato e viene confrontato dopo
  l'apertura candidata: la presenza del valore nel solo JSON envelope non costituisce binding.

### D4 — L'unwrap non equivale ad autenticazione

L'hash bcrypt vive nel DB cifrato. L'ordine vincolante del login è:

```text
password + email
→ deriva password-KEK e tenta unwrap della DEK
→ apre un engine SQLCipher candidato
→ verifica cipher + leggibilità minima
→ carica l'unico owner
→ verifica email normalizzata + bcrypt + account attivo
→ esegue manutenzione post-unlock
→ pubblica engine e stato UNLOCKED
→ emette JWT
```

- Un unwrap valido con email errata, owner inattivo o bcrypt non valido non pubblica l'engine.
- Ogni candidato fallito viene chiuso e la DEK candidata non resta raggiungibile dallo stato
  globale.
- Gli errori pre-auth sono generici; non distinguono email, password, envelope o presenza owner.
- L'engine business è accessibile soltanto tramite controller/accessor; sono vietati nuovi import
  diretti di un singleton business.

### D5 — Recovery obbligatoria e verificata

- La recovery key è generata localmente con CSPRNG: 32 byte, rappresentazione Base32 canonica e
  raggruppata per leggibilità.
- Viene mostrata una sola volta e mai persistita in chiaro.
- Il setup non conclude e non emette JWT finché il trainer non reinserisce la recovery key e
  dimostra crittograficamente che sblocca il relativo slot. Un solo checkbox non basta.
- Se il processo termina prima della conferma, lo stato è `SETUP_RECOVERY_PENDING`: la password
  permette di rigenerare una nuova recovery key e invalida quella non confermata.
- Se password e recovery key vengono perse entrambe, i dati sono irrecuperabili per costruzione;
  il prodotto deve dirlo senza promettere recovery cloud.

### D6 — Password policy minima, byte-safe

Per setup, cambio password e recovery:

- minimo 12 caratteri;
- nessuna regola obbligatoria “maiuscola + numero + simbolo”;
- blocco backend di password comuni, ovvie, ripetitive o direttamente derivate da email/prodotto;
- indicatore frontend informativo, mai unica autorità;
- nessun troncamento bcrypt silenzioso: fino a quando il verifier resta bcrypt, il backend rifiuta
  esplicitamente input oltre 72 byte UTF-8;
- confronto e messaggi non rivelano quale criterio segreto o account sia fallito.

Un owner legacy con password sotto soglia può fare l'unlock necessario alla migrazione, ma deve
scegliere una password conforme prima di completare il nuovo setup G1.

### D7 — Portale e API fail-closed

- Prima di `UNLOCKED`, gli endpoint CRM, backup e portale non ricevono sessioni business.
- Il portale pubblico risponde con indisponibilità generica del trainer, senza distinguere setup,
  password, recovery, migrazione o errore.
- Health e setup-status restano minimali e non interrogano `crm.db` sigillato.
- Un JWT ancora presente dopo un riavvio non sblocca il database e non bypassa il login.
- La DEK resta in RAM per la vita del processo dopo un unlock riuscito, come deciso in ADR-013.
  Il logout revoca la sessione applicativa ma non introduce un manual re-lock in S1.

### D8 — Migrazione legacy atomica e bloccante

- La migrazione usa credenziali esistenti e accetta un DB plaintext con esattamente un owner valido.
  Un DB con zero owner e zero record business segue il first-setup dopo backup preventivo; zero
  owner con dati, più owner o owner ambiguo portano a `MANUAL_REVIEW_REQUIRED`.
- Prima dell'export si acquisisce il lock esclusivo, si rende consistente/chiude l'eventuale WAL e
  si impedisce a qualunque vecchio engine di riaprire il file.
- Prima della trasformazione esiste un backup preventivo byte-exact; qualunque copia plaintext è
  solo transitoria dentro uno stato di migrazione bloccato e deve essere rimossa prima di
  `UNLOCKED`.
- Il candidato cifrato viene prodotto con `sqlcipher_export`, non con copia ORM parziale.
- Schema, trigger, indici, conteggi per tabella, `integrity_check`, `cipher_integrity_check` e una
  lettura business minima devono passare prima dello swap.
- Lo swap è atomico e governato da journal; un crash in ogni fase porta a resume o rollback
  deterministico, mai all'apertura casuale del file trovato.
- L'originale non viene sovrascritto finché candidato, envelope e recovery non sono validi.
- Nessun DB reale viene migrato nel code gate. La migrazione Chiara richiederà backup, dry-run,
  autorizzazione separata e verifier.

### D9 — Backup G5 come bundle recuperabile

Ogni backup automatico, manuale o esportato è un bundle versionato che contiene soltanto:

- snapshot SQLCipher consistente del CRM;
- envelope necessario a quel backup;
- manifest non sensibile con versione formato, `database_id`, timestamp e checksum;
- nessuna password, DEK o recovery key in chiaro.

Regole:

- niente `sqlite3.backup()` standard sul CRM cifrato;
- niente raw file-copy mentre WAL/connessioni possono rendere lo snapshot incoerente;
- i backup locali gestiti mantengono la retention esistente solo dopo verifica del nuovo bundle;
- un backup esportato conserva gli slot validi al momento della creazione; questo limite viene
  comunicato al trainer;
- password/recovery rotation riallineano gli envelope dei backup locali gestiti, ma non possono
  modificare copie offline non più sotto controllo dell'app;
- restore same-instance e disaster restore su installazione vuota sono entrambi casi accettati;
- prima dello swap di restore viene creato un safety backup cifrato dello stato corrente;
- checksum, envelope, chiave, cipher integrity e identità owner vengono verificati prima dello
  swap; dopo lo swap engine e manutenzione vengono riaperti da zero.

### D10 — Cambio password e recovery sono transazioni recuperabili

DB SQLite ed envelope sono due risorse distinte. Aggiornare bcrypt e password-slot senza protocollo
lascia una finestra in cui nessuna password funziona.

- Ogni cambio credenziale usa un journal a due fasi che contiene solo slot wrapped e verifier
  one-way, mai password/DEK plaintext.
- Dopo crash, old password, new password o recovery determinano in modo non ambiguo quale fase
  completare o annullare.
- Cambio password: verifica password corrente, aggiorna bcrypt, sostituisce password-slot, non
  ricifra le pagine SQLCipher.
- Recovery: verifica recovery-slot, imposta nuova password, genera una nuova recovery key e
  invalida lo slot recovery corrente per l'installazione live.
- La rotazione non rende retroattivamente illeggibili backup offline creati con vecchi slot: è un
  limite esplicito del modello snapshot.

---

## 3. Contratto crittografico v1

### 3.1 Envelope logico

Il nome fisico viene risolto sempre da `DATA_DIR`; il formato logico minimo è:

```json
{
  "format_version": 1,
  "database_id": "uuid-casuale",
  "cipher_profile": "sqlcipher-4-defaults",
  "password_slot": {
    "kdf": {"name": "scrypt", "n": 131072, "r": 8, "p": 1, "salt": "base64"},
    "wrap": {"name": "AES-256-GCM", "nonce": "base64", "ciphertext": "base64"}
  },
  "recovery_slot": {
    "kdf": {"name": "HKDF-SHA256", "salt": "base64", "info": "fitmanager/crm-recovery/v1"},
    "wrap": {"name": "AES-256-GCM", "nonce": "base64", "ciphertext": "base64"}
  }
}
```

Questo esempio è uno schema, non un file contenente valori reali.

- salt: almeno 16 byte casuali e distinti;
- nonce GCM: 12 byte casuali, mai riusati con la stessa KEK;
- AAD: almeno `format_version`, `database_id`, `slot_type`, `cipher_profile`;
- input recovery: decodifica Base32 canonica prima di HKDF;
- raw DEK fornita a SQLCipher in forma binaria/hex validata, mai interpolando input utente;
- `cipher_plaintext_header_size` resta zero: nessun header SQLite deliberatamente in chiaro.

### 3.2 Parametri scrypt congelati

Baseline locale Windows del 2026-09-04, Python 3.12.10 + `cryptography 46.0.5`, tre derive:

| Parametri | Misure | Mediana |
|---|---:|---:|
| `N=2^17`, `r=8`, `p=1`, output 32 byte | 337,4 · 341,7 · 357,3 ms | 341,7 ms |

Il profilo è coerente con il minimo OWASP corrente di 128 MiB per scrypt ed è accettabile per un
unlock interattivo desktop. È il profilo v1; un cambiamento futuro richiede nuova versione slot e
migrazione lazy, mai reinterpretazione dei parametri salvati.

### 3.3 Persistenza atomica

- envelope, journal e manifest vengono validati con schema fail-closed;
- scrittura su file candidato nello stesso filesystem, flush/fsync dove disponibile, quindi
  replace atomico;
- permessi filesystem restrittivi best-effort come difesa in profondità, non come chiave;
- file temporanei hanno nomi deterministici governati dal journal, non glob distruttivi;
- il cleanup non usa path non risolti e non opera fuori da `DATA_DIR`.

---

## 4. State machine runtime

| Stato | Significato | Superfici consentite |
|---|---|---|
| `UNINITIALIZED` | nessun owner/envelope | health, setup-status, avvio register |
| `SETUP_RECOVERY_PENDING` | DB cifrato e owner creato, recovery non confermata | health, setup-status, resume setup autenticato |
| `MIGRATION_REQUIRED` | rilevato CRM legacy plaintext | health, setup-status, login/migration |
| `MIGRATING` | journal attivo, nessun servizio dati | health minimale, stato generico |
| `LOCKED` | envelope + DB cifrato presenti, nessuna DEK pubblicata | health, setup-status, login, recovery |
| `UNLOCKING` | engine candidato e controlli in corso | nessuna sessione business |
| `UNLOCKED` | owner verificato, manutenzione conclusa, engine pubblicato | superfici normali soggette ad auth/licenza |
| `RECOVERY_REQUIRED` | transizione interrotta o credenziali normali inutilizzabili | health, setup-status, recovery |
| `MANUAL_REVIEW_REQUIRED` | stato legacy ambiguo, incluso più di un trainer | health minimale; nessuna mutazione automatica |
| `ERROR` | corruzione/incompatibilità non recuperata | health minimale; nessun fallback |

Il controller serializza le transizioni. Due login concorrenti non possono creare due engine
pubblicati, duplicare manutenzione o corrompere journal/envelope.

### 4.1 Manutenzione post-unlock

Dopo identità valida e prima di emettere JWT/esporre il portale:

1. backup automatico SQLCipher-aware;
2. `create_db_and_tables` solo attraverso l'engine candidato;
3. schema sync;
4. integrity check SQLite + cipher integrity;
5. pubblicazione atomica dell'engine e stato `UNLOCKED`.

Un fallimento dispone l'engine candidato e porta a stato recuperabile. La manutenzione non gira due
volte nello stesso processo per effetto di richieste concorrenti.

---

## 5. Contratti API/UX minimi

La forma esatta degli schema sarà fissata nel code gate preservando il type sync, ma devono valere
queste proprietà:

- `setup-status` deriva solo dallo stato installazione e non apre il DB;
- register è un protocollo setup, non una normale creazione account;
- register, resume-setup e recovery restano superfici locali e non vengono aggiunti alla allowlist
  del tunnel pubblico;
- nessun JWT prima della conferma recovery;
- login con errore restituisce sempre la stessa classe di risposta e non rivela l'owner;
- recovery richiede la recovery key e una nuova password conforme;
- frontend gestisce loading/error/resume senza memorizzare segreti persistenti;
- refresh o restart durante setup/migrazione non crea un secondo owner;
- il testo spiega che portale e dati diventano disponibili dopo unlock e che AVGV non possiede una
  chiave master.

---

## 6. Gate di implementazione

Ogni gate sotto è una unità coesa, verificata, committata e pushata prima del successivo.

### S1.1 — Primitive envelope RED→GREEN

- modello e validazione envelope v1;
- generation DEK/recovery;
- scrypt/HKDF/AES-GCM;
- atomic write;
- test wrong password, wrong recovery, tamper, truncation, slot swap, versione ignota;
- nessun cambiamento al boot corrente in questo gate.

### S1.2 — Engine late-bound e boundary locked

- controller business DB e session accessor;
- rimozione degli import diretti del business engine;
- candidate-open + verifica owner prima della pubblicazione;
- fail-closed di CRM/backup/portale;
- test concorrenza e dependency override;
- catalog/nutrition engine invariati.

### S1.3 — Setup owner e recovery UX

- register solo `UNINITIALIZED`;
- DB cifrato iniziale + owner singolo;
- recovery display/re-entry/resume;
- password policy backend-authoritative;
- frontend type sync, loading/error state e secret hygiene.

### S1.4 — Migrazione legacy

- detector plaintext/ciphertext;
- preflight owner unico;
- backup preventivo e journal;
- `sqlcipher_export`, verifiche e atomic swap;
- fault injection su ogni boundary;
- solo fixture sintetiche.

### S1.5 — Backup, restore e credenziali

- bundle G5 automatico/manuale/export;
- backup → mutate → restore;
- disaster restore su installazione vuota;
- cambio password e recovery a due fasi;
- retention soltanto su bundle verificati;
- aggiornamento runbook trainer.

### S1.6 — Packaging Windows e chiusura G1/G5

- dipendenza SQLCipher di produzione exact-pinned e verificata nella supply chain;
- smoke sul percorso produttivo, non sul solo canary isolato;
- wrong-key/plaintext scan sull'artefatto;
- full suite, build Windows e fold-back SSoT;
- consuntivo e archiviazione di questa SPEC nello stesso gate di chiusura.

La numerazione S1 successiva per G2/G4 resta nella regia `SPEC_PRE_POC.md`; questa SPEC non la
autorizza in anticipo.

---

## 7. Matrice di accettazione G1/G5

| Caso | Evidenza richiesta |
|---|---|
| Possesso del solo `crm.db` | SQLite standard/wrong key non leggono schema o fixture note |
| Possesso del solo envelope | nessuna DEK/plaintext recuperabile |
| Password corretta + email errata | nessun JWT, engine non pubblicato, errore generico |
| Password errata | nessun DB/sessione/log sensibile; stato torna `LOCKED` |
| Recovery corretta | nuova password + nuova recovery; DB e owner preservati |
| Recovery non confermata | nessun JWT; restart riprende senza perdere DB |
| Secondo register compiled | fallisce senza nuova riga o informazione sensibile |
| Legacy con 0 owner e zero dati | first-setup cifrato dopo backup preventivo |
| Legacy con 0 owner ma dati, o >1 owner | stop manuale, nessuna migrazione automatica |
| Crash migrazione in ogni fase | resume/rollback deterministico; almeno una copia valida |
| Crash cambio password/recovery | old/new/recovery consentono completamento deterministico |
| Endpoint CRM pre-unlock | fail-closed, nessuna query business |
| Portale pre-unlock | indisponibilità generica, nessuna distinzione stato |
| JWT residuo dopo restart | non sblocca e non serve dati |
| Backup | bundle cifrato, consistente, manifest/checksum validi |
| Restore manomesso/wrong key | rifiutato prima dello swap; stato corrente intatto |
| Restore valido | backup → mutate → restore ripristina dati e integrità |
| Compiled artifact Windows | SQLCipher reale, wrong-key respinta, nessun fallback plaintext |
| Log/artifact scan | zero password, recovery key, DEK e fixture sensibili note |

---

## 8. Quality gate e verifier

Per ogni code gate:

1. canary/regressione RED quando pratico;
2. test mirati del microstep;
3. suite backend completa;
4. `ruff check api/`;
5. test frontend pertinenti e `next build` se il frontend cambia;
6. test di fault injection proporzionati al gate;
7. `git diff --check`, stato, lista file, staged diff/stat;
8. commit atomico, push immediato e delta remoto `0 0`.

Verifier finale adversariale:

- negative-path matrix completa;
- backup → mutate → restore;
- scansione plaintext su DB, backup, temp, journal e log;
- avvio/riavvio compiled locked→unlocked;
- prova che stdlib SQLite e una chiave errata non leggano gli artefatti;
- build/smoke Windows con la dependency nativa realmente inclusa.

Il conteggio dei test viene registrato dal runner effettivo; non si riusa il numero della baseline
come prova di un gate futuro.

---

## 9. Stop condition

Il blocco si ferma e resta non-GREEN se:

- SQLCipher non è bundle-abile nel percorso Windows reale;
- una transizione può lasciare come unica copia un DB illeggibile;
- compare plaintext persistente fuori dallo stato transitorio di migrazione bloccato;
- è necessario supportare più di un owner;
- recovery richiede una chiave master AVGV o un segreto cloud;
- backup/restore non sono consistenti con WAL e cipher integrity;
- il normale dev/test path è l'unico ad essere testato;
- per procedere serve modificare G2, G4, licenza, tunnel o una policy non ratificata.

Non sono fallback ammessi: cifratura di soli campi, chiave embedded, DPAPI-only, SQLite plaintext
compilato, skip dei test o migrazione diretta di dati reali.

---

## 10. Fold-back previsto a chiusura

- `ADR-013`: eventuali soli Addendum normativi, mai riscrittura storica;
- `SECURITY_MODEL.md`: comportamento realmente implementato, threat boundary e file chiave;
- `PRE_DELIVERY_SECURITY_GATE.md`: G1/G5 con evidenze effettive;
- `SPEC_PRE_POC.md`: stato S1 e prossimo gate reale;
- `docs/INDEX.md` e `docs/adr/README.md`;
- `docs/operations/SUPPORT_RUNBOOK.md` e/o upgrade runbook per recovery/migrazione;
- `docs/learning/BUILD_LOG.md` append-only;
- consuntivo di questa SPEC e spostamento in `docs/archive/specs/` quando G1/G5 sono chiusi.

---

## 11. Riferimenti tecnici

- ADR-013: `docs/adr/ADR-013-crm-db-encryption-at-rest.md`
- Security gate: `docs/technical/PRE_DELIVERY_SECURITY_GATE.md` §G1 + §G5
- Security SSoT: `docs/technical/SECURITY_MODEL.md`
- Regia: `docs/specs/SPEC_PRE_POC.md`
- SQLCipher API, `sqlcipher_export` e `cipher_integrity_check`:
  <https://www.zetetic.net/sqlcipher/sqlcipher-api/>
- OWASP Password Storage Cheat Sheet, profilo scrypt:
  <https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html>
- `cryptography` Scrypt KDF:
  <https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/>

---

## 12. Consuntivo S1.0 docs-first — 2026-09-04

- ratificato owner unico per installazione compilata; multi-tenant mantenuto solo come harness test;
- risolto il paradosso auth/DB con candidate engine + doppia verifica unwrap e bcrypt;
- congelati state machine, envelope v1, scrypt, recovery, migration journal e backup bundle;
- confermato G2 proof-first come blocco successivo separato, senza indebolimento implicito;
- nessun codice, schema, dipendenza, DB, artefatto o dato reale modificato in S1.0;
- prossimo gate autorizzabile: **S1.1 primitive envelope RED→GREEN**.
