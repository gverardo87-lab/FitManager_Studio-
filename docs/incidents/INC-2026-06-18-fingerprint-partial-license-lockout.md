# INC-2026-06-18 — Fingerprint hardware parziale → falso "wrong_machine" → blocco CRM ricorrente

- **Data**: bug latente da sempre (feature fingerprint); evidenza dal 2026-03-25; diagnosticato e corretto il 2026-06-18
- **Gravita'**: ALTA (P1) — accesso al CRM bloccato in modo ricorrente per un cliente pagante, con workaround (riavvio app) ma senza fix
- **Impatto**: Chiara Bassani (v1.0.10) si vede chiedere la `license.key` e bloccare l'accesso al CRM "ogni tanto". Workaround scoperto da lei: riavviare l'app. **Oltre 45 episodi in 3 mesi** documentati nei log.
- **Scope**: `api/services/machine_fingerprint.py` (calcolo fingerprint hardware per binding licenza). Presente in **tutte** le versioni (v1.0.7 / v1.0.10 / v1.0.12) — codice invariato.
- **Durata disservizio**: nessun down totale; blocchi intermittenti per-sessione, recuperabili con riavvio.
- **Rilevato da**: segnalazione utente (Chiara) → diagnosi su codice + log reale (Giacomo + Claude Code).

---

## Executive Summary

Il `machine_id` della licenza e' un SHA-256 di tre identificatori hardware letti via PowerShell/WMI (CPU `ProcessorId`, BaseBoard `SerialNumber`, BIOS `SerialNumber`). Su alcune macchine queste query WMI **falliscono a intermittenza** (ritornano stringa vuota) per cause transitorie: sistema sotto carico, antivirus, risveglio da sleep.

Il difetto: `_compute_fingerprint()` calcolava l'hash anche su un set **parziale**, includendo le stringhe vuote (`sha256("cpu||bios")`), e ritornava `"unavailable"` **solo** se *tutte e tre* fallivano. Un set parziale produce un hash **diverso** dal `machine_id` firmato nella licenza → `check_license()` ritorna `wrong_machine` → il middleware licenza risponde **403** → il frontend redirige a `/licenza` ("chiede la license.key") e blocca il CRM.

Aggravante: `get_machine_fingerprint()` **cachava** il valore (anche quello sbagliato) per tutta la vita del processo → la sessione restava bloccata finche' l'app non veniva riavviata e la computazione successiva otteneva tutti e 3 i valori. Da qui: intermittenza, e "logout/login (= riavvio app) risolve".

La correlazione "WiFi della palestra" lamentata dall'utente e' **coincidente, non causale**: connettersi a una rete nuova coincide spesso col risveglio da sleep, durante il quale WMI e' transitoriamente fiacco.

---

## Cronologia

| Quando | Evento |
|--------|--------|
| (sempre) | La logica "tollera il parziale" e' presente fin dalla feature fingerprint. Un test (`test_partial_failure_still_produces_fingerprint`) ne **certificava** il comportamento bacato come corretto. |
| 2026-03-25 | Prima evidenza nel log di Chiara: `WARNING ... Fingerprint parziale: 2/3 identificatori disponibili`. |
| 2026-03-25 → 2026-06-16 | **Oltre 45 episodi** "Fingerprint parziale" (44× 2/3, 2× 1/3) + 1× `Nessun identificatore hardware disponibile` (0/3) il 2026-06-01. |
| 2026-06-18 | Segnalazione utente → diagnosi su codice → conferma sul log reale → fix + test di regressione + incidente. |

---

## Root Cause Analysis

### Catena del difetto

`api/services/machine_fingerprint.py` (pre-fix):
```python
values = [_powershell_query(cls, prop) for cls, prop in _HW_QUERIES]   # 3 query WMI
non_empty = [v for v in values if v]
if not non_empty:
    return "unavailable"                 # ← SOLO se TUTTE e 3 falliscono
raw = f"{cpu_id}|{board_serial}|{bios_serial}"   # ← include i segmenti VUOTI
return hashlib.sha256(raw.encode()).hexdigest()  # ← hash DIVERSO da quello firmato
```

`_powershell_query` ritorna `""` su query vuota/fallita (returncode != 0 o stdout vuoto), **senza** sollevare eccezione → un fallimento "silenzioso" che non logga nemmeno `PowerShell query fallita` (quel log scatta solo su eccezione).

`api/services/license.py` `check_license()`:
```python
if current_fp != "unavailable" and claims.machine_id != current_fp:
    return LicenseCheckResult(status="wrong_machine", ...)   # → 403 → /licenza
```

Il fingerprint parziale ≠ `"unavailable"` **e** ≠ `machine_id` → `wrong_machine`.

### Caching del valore sbagliato
```python
def get_machine_fingerprint() -> str:
    global _cached_fingerprint
    if _cached_fingerprint is None:
        _cached_fingerprint = _compute_fingerprint()   # cacha QUALSIASI esito, incluso il parziale
    return _cached_fingerprint
```
Una computazione parziale al primo accesso dopo l'avvio → fingerprint sbagliato cachato per tutta la sessione → blocco fino al riavvio.

### Perche' sfuggito al test
Il test `test_partial_failure_still_produces_fingerprint` **asseriva l'invariante sbagliata**:
```python
assert fp != "unavailable"
assert len(fp) == 64   # "con 2/3 il fingerprint viene comunque generato" → BACATO
```
Un test che certifica il bug e' peggio di nessun test: da' falsa sicurezza. Sulla macchina di sviluppo WMI risponde sempre (3/3), quindi il difetto non si manifestava mai in dev — classico "works on my machine", con un test a coprirlo.

---

## Impatto

### Business
- Cliente pagante (Chiara) bloccato ripetutamente dall'accesso al proprio CRM per **3 mesi**. Erosione di fiducia diretta. Senza il workaround scoperto da lei (riavvio), avrebbe richiesto supporto a ogni episodio.
- **Gate per la consegna ad Alessio**: stesso codice in v1.0.12 → un secondo cliente sarebbe stato esposto allo stesso difetto.

### Tecnico
- Nessuna corruzione dati. Il blocco e' a livello di enforcement licenza (403), non di integrita'.
- Rischio collaterale **enrollment**: se il "Codice Macchina" mostrato in `/licenza` viene letto durante un singhiozzo, la licenza viene firmata su un fingerprint parziale → mismatch ogni volta che WMI funziona pienamente.

### Utente
- Sintomo: "mi chiede la licenza e non entro nel CRM", intermittente, risolto riavviando. Nessuna perdita di lavoro.

---

## Perimetro del fix (v1.0.13)

`api/services/machine_fingerprint.py` — 3 interventi:

1. **Mai hashare un set parziale.** Se *qualunque* identificatore manca → `"unavailable"` (fail-closed), mai un hash. L'hash 3/3 resta `sha256("cpu|board|bios")` → **identico alla forma storica** → le licenze gia' firmate (Chiara, Alessio) restano valide.
2. **Non cachare i fallimenti.** `get_machine_fingerprint()` cacha **solo** un fingerprint completo. Un `"unavailable"` non viene congelato → la richiesta successiva ritenta e si **auto-guarisce** in secondi, invece di bloccare l'intera sessione.
3. **Retry sui vuoti transitori.** `_powershell_query` ritenta fino a 3 volte sui vuoti "veloci" (con micro-backoff). Sul **timeout** NON ritenta (ha gia' atteso) per non far esplodere la latenza.

La proprieta' di sicurezza ADR-005 ("`unavailable` in frozen → blocco fail-closed") resta **intatta**: si eliminano i *falsi* blocchi da parziale, non i blocchi legittimi.

`tests/test_machine_fingerprint.py` — il test bacato e' stato **capovolto** (`test_partial_failure_returns_unavailable_not_a_hash`) + aggiunti: back-compat hash 3/3, auto-heal senza cache, recupero via retry, timeout→unavailable, cache del completo. **11 test, tutti verdi.**

---

## Verifica

| Check | Risultato |
|-------|-----------|
| Hash 3/3 invariato (back-compat licenze) | OK (`sha256("cpu\|board\|bios")` identico) |
| Parziale → `unavailable`, mai hash | OK (test) |
| Fallimento non cachato → auto-heal | OK (test) |
| Retry recupera il vuoto transitorio | OK (test) |
| `pytest tests/test_machine_fingerprint.py` | 11 passed |
| `ruff check` | clean |
| Suite completa | (vedi BUILD_LOG / commit) |

---

## Lezioni e Regole Derivate

### L1 — Un identificatore di sicurezza si calcola su un set COMPLETO e DETERMINISTICO, o non si calcola
Un fingerprint/hash usato per autorizzazione non deve mai degradare a "uso quello che ho": un set variabile produce hash variabili e mismatch. O tutti i componenti sono presenti (hash), o si fallisce in modo esplicito e **recuperabile** (`unavailable`). La degradazione parziale e' accettabile per un *display*, mai per un *binding*.

### L2 — Non cachare i fallimenti transitori di una risorsa esterna fiacca
Cachare un esito di errore congela il guasto per l'intera sessione. Le risorse esterne fiacche (WMI, rete, subprocess) vanno interrogate con retry e l'esito di errore NON va memoizzato: la prossima chiamata deve poter riprovare.

### L3 — Un test che asserisce il comportamento bacato e' un debito, non una copertura
`test_partial_failure_still_produces_fingerprint` "verde" dava falsa sicurezza. Quando si scrive un test su un failure mode, chiedersi: *sto asserendo cosa il sistema DEVE fare, o cosa per caso fa oggi?* Specie per la sicurezza, l'invariante va derivata dal requisito, non dall'implementazione corrente.

### L4 — Il dev environment e' il caso migliore, non quello rappresentativo
WMI risponde sempre 3/3 sulla macchina dello sviluppatore. I difetti delle risorse di sistema emergono solo in campo, sotto carico/sleep/antivirus. Per logica che dipende dall'ambiente OS, il test deve **simulare il degrado**, non solo il percorso felice.

---

## Azioni preventive

| Azione | Priorita' | Stato |
|--------|-----------|-------|
| Fix `machine_fingerprint.py` (3 parti) | P1 | DONE |
| Test di regressione (parziale/retry/auto-heal/timeout) | P1 | DONE |
| Capovolgere il test bacato | P1 | DONE |
| Incidente + POSTMORTEMS + pitfall CLAUDE.md | P1 | DONE |
| Release v1.0.13 + consegna a Chiara (sblocca) e Alessio (versione pulita) | P1 | TODO |
| Valutare query WMI singola (1 spawn invece di 3) per ridurre la flakiness alla radice | P3 | TODO (nota in fix) |
| Gestire l'edge "campo hardware permanentemente vuoto" (oggi → `unavailable` perpetuo) se mai osservato in campo | P3 | TODO |

---

## Classificazione

- **Tipo**: degradazione errata di un identificatore di sicurezza (set parziale hashato) + caching di un esito transitorio + test che certificava il bug.
- **Trigger**: singhiozzo transitorio di una query WMI/PowerShell durante la prima computazione del fingerprint dopo l'avvio.
- **Severita'**: P1 — blocco accesso CRM ricorrente per cliente pagante, recuperabile con riavvio.
- **Relazione con altri incidenti**: come INC-2026-04-19 e INC-2026-06-15, e' un bug che emerge **solo sulla macchina del cliente** (ambiente reale), invisibile in dev.
