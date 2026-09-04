# ADR-013 — Cifratura a riposo di crm.db (password-bound) + boot a due fasi

- Date: 2026-06-16 (creazione) · **accettato 2026-06-17**
- Status: **accepted + Addendum I (2026-09-04)** — decisioni founder integrate (§Decision);
  spike prerequisito sciolto; owner unico e boundary auth/DB ratificati
- Deciders: Giacomo Verardo (founder), Claude Code (architetto nel codebase)
- Related: `docs/technical/PRE_DELIVERY_SECURITY_GATE.md` §G1 + §G5 · ADR-003 (separazione 3 DB) · ADR-007 (anti-RE, cifratura cataloghi)

> **Perché questo ADR esiste ora:** il gate di pre-consegna (G1) richiede che `crm.db` — che contiene
> dati ex art. 9 GDPR degli atleti — sia cifrato a riposo, con chiave **legata all'autenticazione del
> trainer** ("il solo possesso del file è insufficiente"). Decisione founder 2026-06-16: si fa **full,
> niente postura interim**. Questo non è "cifrare un file": tocca boot, auth, backup e ciclo di vita
> dell'engine. Va deciso come ADR prima di scrivere codice.

---

## Context

### Stato attuale (verificato nel codice, 2026-06-16)

- L'engine business nasce **in chiaro** da `create_engine(DATABASE_URL)` a livello di modulo (`api/database.py:101`), importato all'avvio. `crm.db` è un file SQLite plaintext sul disco del trainer.
- I cataloghi `catalog.db`/`nutrition.db` **sono** cifrati (AES-256-GCM, `api/services/db_crypto.py`), ma con un modello **non riutilizzabile** per crm.db:
  - chiave derivata da un **seed embedded nel binario** (`_EMBEDDED_KEY_SEED`) → file + binario viaggiano insieme, quindi **non soddisfa** il criterio "possesso del file insufficiente";
  - **read-only**: `decrypt_db_to_bytes()` → `sqlite3.deserialize()` → engine in-memory. crm.db è **read-write** e deve persistere.
- Il **lifespan tocca crm.db prima di qualsiasi login** (`api/main.py`, step 1–2–2b–5):
  1. `_auto_backup_on_startup(DATABASE_URL)` → **copia in chiaro** via `sqlite3.backup()`
  2. `create_db_and_tables()` → apre crm.db, crea tabelle
  3. `sync_schema(engine)` → l'auto-heal `_fix_cross_db_fk` **riscrive** crm.db
  4. `_integrity_check_on_startup(DATABASE_URL, …)` → PRAGMA su crm.db
- L'auth (`api/auth/service.py`): password verificata con **bcrypt** (hash one-way, non usabile come chiave), JWT HS256 con `JWT_SECRET` (non derivato dalla password), expiry 8h.

### Il problema in una frase

Cifrare crm.db con una chiave **password-bound** significa che **niente che tocchi crm.db può girare prima del login** — ma oggi mezza sequenza di boot lo fa. Serve un **boot a due fasi** e un engine **late-bound**, non un semplice swap di libreria.

### Minaccia che chiudiamo (e quella che non chiudiamo)

| Scenario | Coperto? |
|----------|----------|
| Laptop spento rubato → disco letto | ✅ DB illeggibile senza password |
| File `crm.db` copiato (USB, backup, cloud sync accidentale) | ✅ ciphertext inutile senza password |
| Disco estratto e montato su altra macchina | ✅ |
| Malware su sessione **già sbloccata** (chiave in RAM) | ❌ fuori scope (richiede hardening endpoint, non DB-at-rest) |
| Keylogger che cattura la password | ❌ fuori scope |
| Password del trainer debole/indovinabile | ⚠️ mitigata da KDF costosa + policy password, non eliminata |

Va scritto onestamente nel `BUILD_LOG.md` (criterio G1): da cosa difende e da cosa no.

---

## Decision Drivers

- **D1 — Criterio G1 vincolante:** chiave legata all'auth del trainer; possesso del solo file insufficiente. *Esclude* qualsiasi chiave embedded o puramente OS-bound.
- **D2 — Full, non interim** (decisione founder 2026-06-16): qualità prima del tempo.
- **D3 — Read-write + persistenza:** crm.db cambia in continuazione; il pattern in-memory dei cataloghi non si applica.
- **D4 — Bundle Nuitka/PyInstaller:** ogni dipendenza nativa nuova (es. SQLCipher) deve sopravvivere alla compilazione. Rischio di build da validare presto.
- **D5 — Zero frizione per il trainer:** una password al login è accettabile; doppie password o passphrase separate per il DB no.
- **D6 — Recuperabilità (tensione con D1):** se la chiave = solo password, "password dimenticata" = **perdita totale dei dati**. Serve un percorso di recovery che non riapra il buco.
- **D7 — Continuità del portale atleti:** gli endpoint pubblici leggono crm.db (`ShareToken`, schede). Se il DB è sigillato fino al login del trainer, l'accesso atleti **dipende** dall'aver sbloccato.
- **D8 — Backup cifrato (G5):** ogni copia di backup deve restare cifrata, o vanifica G1.

---

## Considered Options

### Asse 1 — Meccanismo di cifratura

#### Option A — SQLCipher (cifratura trasparente full-DB, page-level) ✅ raccomandato
SQLite con estensione SQLCipher: l'intero file è cifrato a pagine (AES-256), trasparente a SQLModel/SQLAlchemy una volta fornita la chiave via `PRAGMA key`.
- **Pro:** trasparente alle query (nessun cambio ai modelli/router); cifra **tutto** (dati, indici, schema, WAL); battle-tested; il backup è semplicemente il file ciphertext (`VACUUM INTO` con chiave); re-key nativo (`PRAGMA rekey`) per il cambio password.
- **Contro:** dipendenza nativa (`pysqlcipher3` / `sqlcipher3-binary` o un build di sqlite con SQLCipher) → **da validare nel bundle Nuitka presto** (rischio D4); il driver va agganciato all'URL SQLAlchemy.

#### Option B — Cifratura a livello di campo applicativo
Cifrare solo le colonne sensibili (anamnesi_json, note cliniche, misurazioni…) nel layer applicativo.
- **Pro:** zero dipendenze native; granulare.
- **Contro:** **rompe query/filtri/sort** sulle colonne cifrate (es. ricerca cliente per nome/email); superficie enorme (ogni modello, ogni router); lascia in chiaro **struttura e metadati** (nomi tabelle, relazioni, conteggi, date); error-prone (un campo dimenticato = leak silenzioso). Cattivo rapporto rischio/copertura per dati ex art. 9.

#### Option C — Cifratura a livello OS (Windows DPAPI / EFS / BitLocker)
Affidarsi al sistema operativo.
- **Pro:** zero cambi applicativi.
- **Contro:** **viola D1** — non è password-bound al trainer ma all'utente/macchina Windows; BitLocker spesso disattivo su PC consumer; la chiave DPAPI è recuperabile dal profilo loggato → non protegge nello scenario "disco estratto da macchina con utente Windows unico senza password forte". Scartata come soluzione primaria (resta utile come **difesa in profondità aggiuntiva**, non sostitutiva).

### Asse 2 — Derivazione e gestione della chiave

#### Option D — Chiave = KDF(password) diretta
- **Pro:** semplice.
- **Contro:** cambio password ⇒ **re-key dell'intero DB**; "password dimenticata" ⇒ **perdita totale**; impossibile aggiungere un percorso di recovery.

#### Option E — Envelope / DEK-KEK ✅ raccomandato
Una **Data Encryption Key (DEK)** random genera la cifratura del DB; la DEK è **wrappata** da una Key-Encryption-Key `KEK = KDF(password, salt)`. Sul disco vive solo `wrapped_DEK` (+ salt), mai la DEK in chiaro.
- **Pro:** cambio password = **ri-wrap della sola DEK** (operazione istantanea, nessun re-key del DB); supporta **più KEK** → si può aggiungere una **recovery key** (codice di ripristino mostrato una volta al setup, conservato offline dal trainer) che wrappa la stessa DEK → risolve D6 senza riaprire il buco; separazione netta tra "segreto che protegge" e "segreto che cifra".
- **Contro:** un filo più di codice (gestione blob `wrapped_DEK`, salt, recovery key) — ma è il pattern corretto e standard.

> **KDF:** Argon2id (preferito, memory-hard) o scrypt; PBKDF2-HMAC-SHA256 ad alto numero di iterazioni come fallback se Argon2 complica il bundle. La verifica password bcrypt **resta separata** (autenticazione); la KEK è una derivazione **aggiuntiva** dalla stessa password in chiaro, disponibile solo al momento del login.

### Asse 3 — Sequenza di boot

#### Option F — Boot a due fasi + engine late-bound ✅ raccomandato
- **Fase A (pre-auth):** il backend parte con crm.db **sigillato**. Servono solo `/login`, `/setup`, `/health`, static. L'`engine` business **non** è più un singleton creato all'import: è creato/aperto **dopo lo sblocco**. I cataloghi (chiave embedded) possono caricarsi (non sono dati atleti).
- **Sblocco:** login riuscito → deriva KEK dalla password → unwrap DEK → apre l'engine SQLCipher con la DEK → la DEK resta **in RAM per la vita del processo**.
- **Fase B (post-unlock, una volta per processo):** girano i passi oggi al boot — auto-backup (**cifrato**), `create_db_and_tables`, `schema_sync`, integrity check — ora contro il DB sbloccato.
- **Contro:** refactor non banale di `database.py` (engine + `get_session` da singleton a late-bound) e spostamento di parte del lifespan post-login. È il costo previsto da D2/D3.

---

## Decision

**Decisione (accettata 2026-06-17): A + E + F.**

> SQLCipher per la cifratura trasparente full-DB; envelope DEK-KEK con recovery key per la gestione chiave; boot a due fasi con engine late-bound. DPAPI/OS come difesa in profondità *opzionale*, mai come sostituto del password-binding.

Razionale: è l'unica combinazione che soddisfa **tutti** i driver insieme — D1 (password-bound vero), D3 (read-write trasparente), D5 (una sola password), D6 (recovery senza buco), D8 (backup = ciphertext nativo). B e C falliscono D1 o D3; D fallisce D6.

### Decisioni founder vincolanti (2026-06-17)

1. **Recovery key OBBLIGATORIA.** Al setup il trainer riceve un codice di emergenza (KEK aggiuntiva che wrappa la stessa DEK) e DEVE confermare di averlo salvato prima di procedere. Motivazione: l'architettura data-blind **esclude per costruzione** qualsiasi reset password lato server (non esiste un nostro cloud). Senza recovery, "password dimenticata" = perdita totale e irreversibile dei dati di atleti reali → relazione chiusa + esposizione legale. La frizione di una schermata al setup è il prezzo più basso contro quel disastro. La schermata deve essere inequivocabile: "questa è la tua chiave di emergenza, salvala/stampala — senza, i dati sono irrecuperabili, nemmeno noi possiamo recuperarli".
2. **Modello di disponibilità portale — confermato.** Gli endpoint pubblici servono i dati degli atleti **solo dopo** che il trainer ha fatto login (sblocco DB) nella sessione corrente; la DEK resta in RAM per la vita del processo. Pre-unlock il portale risponde **fail-closed** ("trainer non disponibile"). È coerente: il trainer deve essere "aperto per lavorare" perché i suoi atleti accedano ai loro dati. Da rendere esplicito in UX + runbook.
3. **Policy password minima.** Soglia di robustezza *minima e non fastidiosa* al setup/cambio password: lunghezza minima (target ~10-12 caratteri) + blocco delle password ovvie/comuni + indicatore di forza che **guida** invece di sbarrare. NON le regole controproducenti "1 maiuscola 1 simbolo". Motivazione: la cifratura vale quanto la password — cifrare con `chiara123` è un falso senso di sicurezza. Complemento necessario di G1, calibrato per non violare il principio no-frizione oltre il minimo indispensabile.
4. **Perimetro confermato.** Si cifrano **crm.db + i suoi backup** (G5 dentro questo design: ogni copia è ciphertext). I **log NON** contengono dati sensibili → fuori perimetro qui, trattati come problema separato in **G8** (disciplina di logging). I cataloghi `catalog.db`/`nutrition.db` restano col modello ADR-007 (chiave embedded, read-only) — non sono dati atleti.
5. **Migrazione dei crm.db già deployati** (Chiara): al primo boot post-upgrade, login con password esistente → deriva chiave → **cifra in-place** il plaintext, con **backup preventivo obbligatorio** prima della trasformazione (regola non negoziabile: mai operazione distruttiva su DB senza `.bak`). Genera contestualmente la recovery key (con la schermata obbligatoria del punto 1).

**Prerequisito bloccante prima di scrivere codice di produzione:** un **spike di validazione bundle** — verificare che SQLCipher (driver scelto) si compili e giri in **Nuitka standalone** (non solo in venv dev). Se SQLCipher non è bundle-abile in modo affidabile, si rivaluta (fallback possibile: SQLite "encryption extension" alternativa, o ripiego su Option B limitata ai campi ex art. 9 come second-best documentato). Questo spike va fatto **per primo**, perché può invalidare l'intero asse 1.

> **✅ Spike eseguito 2026-06-16 — PREREQUISITO SCIOLTO** (report: `tools/spikes/sqlcipher/SPIKE_REPORT.md`). Driver `sqlcipher3` 0.6.2 (wheel nativo `cp312-win_amd64`): cifra realmente (cipher_version 4.12.0), integra con SQLAlchemy via `module=` + `PRAGMA key` su connect, e **sopravvive a Nuitka standalone** — l'exe prodotto gira e decifra, con `_sqlite3.pyd` + `libcrypto-3.dll` (5.2 MB) + `sqlite3.dll` bundlati (+~7 MB sull'installer, trascurabile). Asse A **validato end-to-end**. **Caveat toolchain (indipendente da SQLCipher):** la build Nuitka è passata con **MSVC**; il path `--mingw64` della build reale è attualmente rotto su questa macchina (Nuitka 4.1.2 + gcc 15.2.0 → `windows.h not found`) e la venv di progetto non ha Nuitka installato. Decisione toolchain (MSVC vs fix MinGW vs pin versioni) da prendere prima della release con SQLCipher — non blocca questa decisione. Vedi §4 del report.

---

## Consequences

- **Positive:**
  - crm.db illeggibile senza la password del trainer → chiude il vettore di breach a più alto impatto (laptop/disco rubato).
  - Backup naturalmente cifrati (G5 risolto dentro lo stesso design): l'auto-backup diventa una copia del ciphertext.
  - Cambio password istantaneo (ri-wrap DEK), recovery key per "password dimenticata".
  - Argomento GDPR/commerciale rafforzato: "i dati non lasciano il PC **e** sono cifrati con la tua password".
- **Negative / costi:**
  - Refactor di `database.py` (engine late-bound) e del lifespan (maintenance post-login). Tocca `get_session`, backup, schema_sync.
  - Dipendenza nativa nel bundle (rischio build da validare per primo).
  - **Accoppiamento portale atleti ↔ unlock (D7) — DECISO (fail-closed):** gli endpoint pubblici servono i dati solo dopo che il trainer ha sbloccato il DB nella sessione corrente. Pre-unlock → "trainer non disponibile". "App aperta" non basta più: serve "trainer loggato". Da rendere esplicito in UX + runbook.
  - **Recovery key OBBLIGATORIA (DECISO):** risolve il rischio "password dimenticata = perdita totale" senza riaprire il buco data-blind. Costo: una schermata di frizione al setup + il trainer deve custodire il codice offline. Se perde *sia* password *sia* recovery key → dati persi comunque (limite intrinseco e accettato del data-blind, da comunicare con chiarezza).
- **Follow-up actions:**
  1. ✅ **Spike bundle SQLCipher in Nuitka** (bloccante) — fatto 2026-06-16, asse A validato.
  2. Design di dettaglio: formato blob `wrapped_DEK` + salt + recovery-KEK + dove vivono (file accanto al DB, non segreti); flusso setup (genera DEK + recovery key + **schermata obbligatoria**) vs login (unwrap).
  3. Refactor `database.py` → engine late-bound + `get_session` post-unlock.
  4. Spostare auto-backup/`create_db_and_tables`/`schema_sync`/integrity in Fase B.
  5. Cifrare il percorso di backup/restore/export (G5).
  6. ✅ Comportamento portale pubblico pre-unlock — **deciso: fail-closed** (§Decision punto 2). Resta da implementare + UX/runbook.
  7. Policy password al setup/cambio (§Decision punto 3): soglia minima + blocco password comuni + indicatore di forza.
  8. Voce `BUILD_LOG.md`: meccanismo, dove vive la chiave, minacce coperte/non coperte.
  9. Reset password (`current_password` già richiesto) → diventa ri-wrap della DEK.
  10. Decisione toolchain di build (MSVC vs MinGW pinnato) + congelamento Nuitka — **(b)**, prerequisito alla release con SQLCipher (non al design).

---

## Rollback / Exit Strategy

- ADR `accepted`: la *decisione* è presa, ma l'implementazione di produzione parte solo dopo il **design di dettaglio** (follow-up 2-4). Fino a lì, rollback = nessuno (nessun codice prodotto).
- In implementazione, sviluppo su branch dedicato; il dev mode resta su crm.db plaintext (nessun impatto sul flusso di sviluppo). La migrazione dei DB già deployati (Chiara) avviene una-tantum allo sblocco: plaintext → cifrato, con backup preventivo (regola non negoziabile: mai operazione distruttiva su DB senza `.bak`).
- Se lo spike bundle fallisce: si ripiega su Option B documentata come second-best, oppure si rivaluta il meccanismo, **senza** abbandonare il password-binding (D1 resta vincolante).

## Supersedes / Superseded By

- Supersedes: nessuno.
- Superseded by: —
- Si appoggia a: ADR-007 (cifratura cataloghi read-only — modello *diverso*, chiave embedded, da NON confondere con questo).

---

## Addendum I — 2026-09-04: owner unico e unlock autenticato

### Trigger

Il grounding S1.0 ha mostrato due ambiguità che il design originario non poteva lasciare al codice:

1. il prodotto e la licenza descrivono una istanza locale per trainer, ma il register corrente
   permette tecnicamente più account;
2. l'hash bcrypt dell'owner vive dentro `crm.db`, quindi non è possibile verificare l'identità
   completa prima di aprire il database cifrato.

Il founder ha ratificato il 2026-09-04 l'owner unico per la POC e il trattamento proof-first
separato di G2. Questo Addendum norma il solo confine G1; G2 resta fuori scope.

### Decisione

#### D-A1 — Un owner per installazione compilata

- Una installazione licenziata e compilata contiene un solo trainer owner.
- Il register è un protocollo di primo setup ed è chiuso dopo la creazione dell'owner.
- Un database legacy con più trainer non viene migrato automaticamente: richiede decisione e
  intervento separati.
- La creazione di più trainer nei test resta ammessa esclusivamente come harness per dimostrare
  ownership e Deep IDOR; non costituisce una funzionalità multi-operatore.

Una futura installazione multi-operatore richiede un nuovo atto decisionale: slot per-owner,
revoca/rotazione e recovery multi-account non entrano implicitamente in ADR-013.

#### D-A2 — Apertura candidata prima della verifica bcrypt, pubblicazione dopo

L'uso corretto della password per unwrap della DEK è necessario ma non sufficiente per autenticare
il trainer. Il flusso vincolante è:

```text
password → unwrap DEK → engine SQLCipher candidato
→ verifica email + bcrypt + account attivo
→ manutenzione post-unlock
→ pubblicazione engine → JWT
```

- L'engine candidato è confinato alla singola transizione e viene disposto su ogni fallimento.
- La DEK non entra nello stato globale prima della verifica completa dell'unico owner.
- Errori di email, password, envelope, cipher o owner sono indistinguibili fuori dal boundary auth.
- Un JWT residuo non è materiale di unlock e non può aprire il database dopo un riavvio.

Questa sequenza chiarisce, senza indebolirla, la decisione originaria «password-bound»: il possesso
del file o il solo superamento del wrapping non crea una sessione applicativa valida.

#### D-A3 — Nessun downgrade compiled; test seam esplicito

- In compiled mode il CRM è SQLCipher oppure resta bloccato/in recovery: SQLite plaintext non è un
  fallback operativo.
- Il dev mode plaintext previsto dalla decisione originaria resta disponibile.
- I test devono però poter istanziare esplicitamente il percorso cifrato di produzione senza
  dipendere dal flag compiled, così che G1 non sia verificato soltanto da canary isolati.

### Specifica esecutiva

Formato envelope, state machine, recovery, migrazione, backup e acceptance matrix sono prescritti
da `docs/specs/SPEC_S1_G1_G5_CIFRATURA_CRM.md`. La SPEC può scegliere dettagli implementativi entro
questa legge; non può riaprire owner multipli, pubblicare l'engine prima della verifica completa o
introdurre un fallback plaintext compilato.
