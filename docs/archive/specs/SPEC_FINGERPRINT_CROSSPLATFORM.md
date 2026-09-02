# SPEC — Machine Fingerprint cross-platform (Windows preservato + ramo macOS)

> **CONSUNTIVATA E ARCHIVIATA 2026-09-02 (G-DOC.2)** — codice fatto e sigillato 2026-07-17 (T1
> PASS, hash Windows invariato, suite 867). I residui di verifica NON muoiono qui: T2 sul target
> esatto e il cross-check binding SONO i gate C0.2 e G-MAC.4 di `SPEC_G-MAC_CONSEGNA_MACOS.md`
> (viva, pull-based per D11). Nessun lavoro resta orfano con l'archiviazione.

**Stato:** 🟡 CODICE FATTO E SIGILLATO (2026-07-17) — T1 PASS (hash Windows mascherato e
invariato pre/post refactor, suite 867 verde). C0.2, ora HOLD trigger Mac e non bloccante per S1,
verifica stabilità T2 con probe source-free sul target M1/8 GB/Tahoe 26.5.1; il gate chiude
definitivamente con cross-check binding in G-MAC.4.
Sequenza: `SPEC_PRE_POC.md`; contratto C0: `SPEC_G-MAC_CONSEGNA_MACOS.md` §3.
**Blocco:** G-MAC.0 — Fingerprint feasibility gate
**Tipo:** Refactor isolato (Windows) + estensione additiva (macOS)
**File toccato:** `api/services/machine_fingerprint.py` — **UNICO**
**Ground-truth:** il codice reale vince sulla spec se divergono. Questa spec descrive *cosa deve risultare vero*, non *come* scriverlo riga per riga.

---

## 0. Perché questo blocco esiste (macro prima del micro)

Daniele (PT pilota) ha un Mac. Oggi la generazione del `machine_id` per il binding licenza si appoggia a PowerShell + WMI, che **non esistono su macOS**. Conseguenza: su Mac `get_machine_fingerprint()` ritorna sempre `UNAVAILABLE`, e in frozen mode `check_license()` tratta `UNAVAILABLE` come fail-closed → **la licenza non si attiva, il CRM è inaccessibile**.

Questo è un **cancello di fattibilità a monte di tutto il packaging macOS**: non ha senso costruire la pipeline Nuitka-macOS se la licenza non può attivarsi. Questo blocco va chiuso per primo.

Il blast radius è minimo per design: l'intera catena licenza dipende dal fingerprint attraverso **una sola funzione pubblica** (`get_machine_fingerprint()`), che è già platform-agnostica. L'unica logica Windows-specifica vive in `_compute_fingerprint()` e nei due helper PowerShell sotto di essa. Il dispatch va innestato **solo lì**.

---

## 1. Tesi falsificabili (due, distinte)

**T1 (refactor Windows — output-invariante):**
Dopo l'estrazione della logica Windows in una funzione dedicata, su una macchina Windows con i 3 identificatori presenti, `get_machine_fingerprint()` restituisce **lo stesso identico hash SHA-256 di 64 caratteri** che restituiva prima del refactor. L'oracolo esiste: l'output storico. Falsificabile confrontando l'hash prima/dopo sulla stessa macchina.

**T2 (estensione macOS — additiva):**
Su una macchina macOS con le primitive hardware leggibili, `get_machine_fingerprint()` restituisce un hash SHA-256 di 64 caratteri **deterministico tra riavvii**. Su fallimento di lettura delle primitive, restituisce `UNAVAILABLE` (mai un hash parziale). Non esiste oracolo pregresso macOS: è comportamento nuovo su piattaforma prima non supportata.

> **Separabilità:** T1 e T2 toccano lo stesso file ma sono logicamente indipendenti. Se si preferisce la separazione fisica, sono ammessi **due commit**: prima T1 (estrazione Windows a output costante, falsificabile contro l'output storico), poi T2 (aggiunta ramo macOS). La regola "mai refactor + funzionale nello stesso commit" **non è violata** anche in un commit unico, perché T2 è additivo su una piattaforma dove oggi non esiste output da preservare come oracolo. Decisione di granularità lasciata all'implementatore.

---

## 2. Invariante critico ereditato (NON negoziabile, cross-platform)

L'invariante **INC-2026-06-18** ("tutto-o-niente") è già documentato nel file e **vale identico su macOS**:

> Il fingerprint si calcola SOLO se **tutte** le primitive hardware previste sono presenti. Un set parziale (una primitiva ritorna vuoto per un singhiozzo transitorio) **non deve MAI essere hashato**: un segmento vuoto cambia l'hash → falso `wrong_machine` → blocco accesso CRM. In caso di incompletezza si ritorna `UNAVAILABLE` (fail-closed) **senza cacharlo**, così il tentativo successivo ritenta e si auto-guarisce.

Il ramo macOS **eredita questo vincolo**: raccoglie le sue primitive con la stessa disciplina. Se anche una sola manca dopo i retry → `UNAVAILABLE`, mai un hash parziale.

---

## 3. Cosa deve risultare vero (acceptance criteria)

### AC1 — Dispatch per piattaforma
`_compute_fingerprint()` deve dispatchare sulla piattaforma corrente usando il meccanismo **già presente nel file** (`platform.system()` — non introdurre `sys.platform`, esiste già `import platform` e già un branch `platform.system() == "Windows"` nei creationflags). Su `"Windows"` → percorso Windows. Su `"Darwin"` → percorso macOS. Su altre piattaforme → `UNAVAILABLE` (comportamento safe-default invariato rispetto a oggi).

### AC2 — Percorso Windows preservato bit-per-bit
La logica WMI/PowerShell esistente (le 3 query `_HW_QUERIES`, i retry `_powershell_query`, il timeout, il backoff, la concatenazione `"cpu|board|bios"`, l'hash SHA-256) deve restare **funzionalmente identica**. L'estrazione in una funzione dedicata (suggerito: `_fingerprint_windows() -> str`) è puro spostamento di codice. Stesso hash, stessi retry, stesso comportamento sui vuoti e timeout.

### AC3 — Percorso macOS nuovo
Una funzione dedicata (suggerito: `_fingerprint_macos() -> str`) raccoglie le primitive hardware macOS (`IOPlatformUUID` + `IOPlatformSerialNumber`, vedi §4) **da una singola invocazione `ioreg`** (clausola §4.1, non negoziabile), applica la **stessa disciplina tutto-o-niente**, e su set completo restituisce `sha256(raw)` dove `raw` è `IOPlatformUUID|IOPlatformSerialNumber`. Su set incompleto o errore → `UNAVAILABLE`. Se i due valori non sono ottenibili da un'unica invocazione, ripiegare su solo `IOPlatformUUID` (vedi fallback in §4.1) — **mai** aggiungere un secondo comando di sistema.

### AC4 — Contratto pubblico invariato
`get_machine_fingerprint()`, `get_machine_fingerprint_short()`, `get_machine_fingerprint_display()`, il valore sentinella `UNAVAILABLE`, e la **logica di cache asimmetrica** (cacha solo il completo, mai `UNAVAILABLE`) restano **invariati**. Nessuna firma cambia. Nessun chiamante a valle (`license.py`, `generate_license.py`) viene toccato.

### AC5 — Resilienza ai singhiozzi su macOS
Come per Windows, le letture macOS devono tollerare fallimenti transitori con retry sui vuoti "veloci" e nessun retry sui timeout (la primitiva ha già atteso). Riusare la costante/pattern di retry esistente dove sensato, senza duplicare logica se evitabile.

---

## 4. Decisione di dominio: quali primitive macOS (BLINDATA)

> ✅ **Decisione confermata.** Scelta di dominio chiusa il 25/06. Determina la stabilità del binding (sopravvivenza a update macOS / riparazioni hardware). Contesto: la macchina target è il Mac **personale** di Daniele → riparazioni rare, nessun turnover hardware, profilo di rischio identico a quello già accettato su Windows.

**Decisione:** due identificatori hardware, letti **entrambi dalla stessa singola invocazione `ioreg`**:

1. **IOPlatformUUID** — UUID hardware stabile legato alla logic board. Equivalente macOS più vicino al concetto attuale. Stabile attraverso update di sistema, reinstalli, cambio disco/RAM.
2. **IOPlatformSerialNumber** (hardware serial) — seriale della macchina, praticamente immutabile per la vita della macchina.

Comando di riferimento (l'implementatore sceglie la forma esatta del parsing):
```
ioreg -rd1 -c IOPlatformExpertDevice
```
da cui estrarre **entrambi** i campi `IOPlatformUUID` e `IOPlatformSerialNumber`.

**Ordine di concatenazione fissato:** `IOPlatformUUID|IOPlatformSerialNumber` (così l'hash è deterministico e riproducibile; documentarlo nel docstring come fatto per Windows).

### 4.1 — Clausola NON NEGOZIABILE: stessa invocazione

I due identificatori **DEVONO** essere estratti da **una sola** chiamata a `ioreg`, non da due comandi distinti (es. `ioreg` per uno + `system_profiler` per l'altro). Questa è la clausola che fa funzionare la scelta a due identificatori, ed ecco il ragionamento esplicito:

- L'invariante tutto-o-niente (INC-2026-06-18) significa che **ogni primitiva è un punto di fallimento**: se manca, si va in `UNAVAILABLE`. Con la disciplina AND, più chiamate di sistema indipendenti = più fragilità sul piano *disponibilità*, NON più robustezza sul piano *unicità*.
- Leggendo entrambi i campi dallo **stesso** output `ioreg`, "entrambi presenti" e "ioreg ha risposto" diventano **lo stesso evento**: un solo punto di fallimento, non due. Si ottiene così la ridondanza di *identità* (due campi indipendenti convergono sulla stessa macchina; se Apple cambiasse la derivazione di uno, l'altro resta ancora) pagando **un solo** punto di fallimento sul piano disponibilità.
- **Fallback obbligato:** se in implementazione emerge che i due valori NON sono ottenibili da una singola invocazione, NON aggiungere un secondo comando. Ripiegare invece su **solo `IOPlatformUUID`** (singolo identificatore, sufficiente da solo per l'unicità). A quel punto il secondo identificatore costerebbe più in disponibilità di quanto rende in unicità, e il minimalista è preferibile.

**Perché due e non tre** (a differenza di Windows): su macOS non esiste un terzo identificatore stabile e distinto che aggiunga valore reale al binding. Con la disciplina AND, una terza primitiva aumenterebbe solo la probabilità di `UNAVAILABLE` senza rafforzare l'identità. Anche una sola primitiva basterebbe per l'unicità; due è ridondanza di cortesia, gratuita solo perché letta da un'unica invocazione.

**Rischio residuo accettato:** sostituzione della logic board in assistenza → cambia IOPlatformUUID → falso `wrong_machine`. È un evento eccezionale (Mac personale), gestito con una **ri-emissione licenza una tantum** (rieseguire `fingerprint` sulla macchina riparata + rifirmare). Stesso identico rischio già accettato su Windows col Motherboard SerialNumber: nessuna classe di fragilità nuova introdotta.

---

## 5. Conseguenza dichiarata (nessuna regressione)

- Le licenze Windows **già firmate restano valide su Windows**: l'hash dei 3 valori WMI è preservato bit-per-bit (AC2).
- Un Mac produce un hash da primitive diverse — **corretto e inevitabile**. Non esiste "la stessa
  licenza su Windows e Mac": ogni macchina ha sempre avuto il suo `machine_id`. Il fingerprint del
  target viene acquisito dall'artefatto installato e trasferito soltanto nel canale amministrativo
  di attivazione; sul Mac cliente non si esegue il tool Python da sorgente.
- Nessuna licenza esistente si invalida. Il ramo macOS è puramente additivo.

### Privacy degli identificatori hardware

- `IOPlatformUUID`, seriale e output completo di `ioreg` non lasciano la macchina, non sono loggati
  e non entrano in repository, report, screenshot o artifact CI.
- Il probe C0.2 emette solo esiti booleani di disponibilità/stabilità; non emette il fingerprint.
- Il fingerprint derivato completo è comunque un identificatore univoco: è ammesso solo nel flusso
  amministrativo di firma licenza, non nei log tecnici o nella documentazione. Nei consuntivi si usa
  soltanto una forma mascherata o, preferibilmente, `MATCH/MISMATCH`.

---

## 6. Sezione "does NOT touch" (blinda lo scope)

Questo blocco **NON deve**:

- ❌ Toccare `api/services/license.py` — la catena di firma/verifica RS256, l'embedded public key, l'integrity hash, il fail-closed in frozen mode restano **identici**. Il fingerprint resta una stringa opaca per tutto ciò che sta a valle.
- ❌ Toccare `tools/admin_scripts/generate_license.py` — i comandi `sign`/`verify`/`fingerprint` continuano a ricevere/mostrare un hash a 64 char senza sapere da quali primitive viene.
- ❌ Cambiare il formato dell'output (sempre SHA-256 hex 64 char, o `UNAVAILABLE`).
- ❌ Cambiare le firme delle tre funzioni pubbliche o degli helper di display.
- ❌ Cambiare la logica di cache asimmetrica.
- ❌ Introdurre `sys.platform` (usare `platform.system()` già presente).
- ❌ Toccare il percorso Windows in modo che ne cambi l'output (solo spostamento di codice ammesso).
- ❌ Aggiungere dipendenze esterne: `ioreg` è un binario di sistema macOS invocato via `subprocess`, nessun package Python nuovo.
- ❌ Introdurre encryption-at-rest, packaging, CI, o altri temi macOS: questo blocco è **solo** il fingerprint.

---

## 7. Verifica (come falsificare)

**Windows (T1 — oracolo esiste):**
1. Su una macchina Windows, prima del refactor, annotare l'output di `python -m tools.admin_scripts.generate_license fingerprint` (valore "completo").
2. Dopo il refactor, rieseguire lo stesso comando sulla stessa macchina.
3. **PASS** se gli hash coincidono carattere per carattere. **FAIL** altrimenti.

**macOS (T2 — comportamento nuovo):**
1. In C0.1, eseguire i test automatici Darwin e un probe compilato sul runner `macos-26` usando
   l'artefatto costruito su `macos-15`.
2. Dopo R1-WIN e trigger D11, in C0.2 eseguire lo stesso probe source-free sul target
   M1/8 GB/Tahoe 26.5.1 prima di aprire G-MAC.2.
3. **PASS** se il probe riporta `AVAILABLE=true` e `STABLE=true` tra letture previste dal contratto,
   senza stampare primitive o hash. La stabilità attraverso riavvio viene chiusa in G-MAC.4.
4. Verifica tutto-o-niente automatica: simulare una primitiva vuota → `UNAVAILABLE`, mai hash
   parziale.

**Cross-check binding (end-to-end, su Mac):**
1. L'artefatto installato espone il fingerprint nel canale locale di attivazione; il valore viene
   trasferito al solo amministratore licenze, fuori da log/report.
2. Firmare la licenza per quel valore nel sistema amministrativo.
3. `verify` sulla stessa macchina deve riportare `MATCH`; il consuntivo registra solo l'esito.

> ⚠️ **Vincolo operativo:** il runner macOS prova il ramo Darwin, ma non certifica la patch esatta
> del target. T2 richiede C0.2 sul Mac reale nel percorso Mac pull-based; il binding end-to-end
> chiude in G-MAC.4. Nessun sorgente
> o toolchain viene copiato sul Mac cliente.

---

## 8. Nota docstring

Aggiornare il docstring del modulo per riflettere il dual-platform: oggi recita "via PowerShell Get-CimInstance (Windows)". Deve documentare entrambi i rami (Windows via WMI, macOS via `ioreg`), preservando il riferimento a INC-2026-06-18 e documentando l'ordine di concatenazione macOS come già fatto per Windows.
