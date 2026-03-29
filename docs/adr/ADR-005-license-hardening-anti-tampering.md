# ADR-005 — License Hardening Anti-Tampering

- Date: 2026-03-24
- Status: accepted
- Deciders: gvera
- Related: ADR-004 (release pipeline), docs/technical/SECURITY_MODEL.md

## Context

Il sistema licenza (JWT RS256 + hardware binding) era funzionalmente corretto ma aveva
4 vettori di attacco che un utente tecnico poteva sfruttare per bypassare la protezione:

1. **File replacement**: sostituire `data/license_public.pem` con una propria chiave pubblica,
   firmare JWT con la propria chiave privata → l'app accetta la licenza forgiata.
2. **Env var bypass**: impostare `LICENSE_ENFORCEMENT_ENABLED=false` → enforcement disabilitato.
3. **Fingerprint bypass**: bloccare PowerShell/WMI → fingerprint = `"unavailable"` → hardware
   check saltato per backward compatibility.
4. **Bytecode patching**: decompilare PyInstaller, modificare la chiave embedded nel bytecode.

Il contesto specifico: necessita' di installare il software su PC di un potenziale industry partner
per valutazione, senza copyright formale registrato e con conoscenza limitata della persona.

## Decision Drivers

- Protezione IP prima di installare su macchina di terzi
- Costo zero infrastrutturale (no license server, no cloud)
- Nessun impatto su esperienza sviluppo (dev mode invariato)
- Test suite esistente (22 test) non deve rompersi
- Soluzione proporzionata: barriera anti-copia opportunistica, non anti-nation-state

## Considered Options

### Option A — License server cloud

- Pro: protezione forte, revoca remota, analytics
- Contro: introduce dipendenza cloud (viola principio privacy-first), costo infrastruttura,
  complessita' operativa, richiede connettivita' del trainer

### Option B — Obfuscation pesante (Cython, Nuitka)

- Pro: codice nativo, difficile da reverse-engineer
- Contro: complessita' build enorme, debug impossibile, tempi di compilazione lunghi,
  fragilita' su aggiornamenti Python/dipendenze

### Option C — Hardening in-process (SCELTA)

- Pro: zero dipendenze esterne, zero impatto build, chirurgico (3 file),
  dev mode invariato, test retrocompatibili, proporzionato al rischio
- Contro: un reverse engineer esperto puo' ancora patchare bytecode (ma deve
  trovare e modificare sia la chiave che l'hash, in codice compilato)

## Decision

**Option C**: hardening in-process su 3 file, attivo solo in frozen mode (PyInstaller).

### Modifiche implementate

**`api/services/license.py`** (3 interventi):
1. Chiave pubblica RSA embedded come costante `EMBEDDED_PUBLIC_KEY_PEM`
2. Hash SHA-256 della chiave (`EMBEDDED_PUBLIC_KEY_HASH`) verificato a runtime
3. In frozen mode: `_load_public_key()` usa SOLO la chiave embedded (ignora file/env)
4. In frozen mode: fingerprint `"unavailable"` → `wrong_machine` (fail-closed)

**`api/services/system_runtime.py`** (1 intervento):
5. In frozen mode: `is_license_enforcement_enabled()` ritorna sempre `True` (ignora env var)

### Matrice protezione risultante

| Vettore | Prima | Dopo |
|---------|-------|------|
| Sostituire `license_public.pem` | Bypass totale | Chiave da file ignorata in frozen |
| `LICENSE_ENFORCEMENT_ENABLED=false` | Bypass totale | Env var ignorata in frozen |
| PowerShell bloccato → fingerprint unavailable | Hardware check saltato | Blocco con messaggio supporto |
| Bytecode patching chiave embedded | N/A (chiave era da file) | Deve patchare anche hash SHA-256 |

### Invariante dev mode

Nessun comportamento cambia in dev mode (non-frozen):
- File/env resolution attiva
- Enforcement toggle via env var
- Fingerprint graceful degradation

## Consequences

- Positive: i 4 vettori piu' accessibili sono chiusi; nessun impatto UX, build, dev workflow
- Negative: un attaccante determinato con competenze di reverse engineering Python puo'
  ancora bypassare (ma il costo e' molto piu' alto del valore della copia)
- Follow-up: aggiornare `LICENSE_ACTIVATION.md`, creare `docs/technical/SECURITY_MODEL.md`,
  aggiornare indice ADR

## Rollback / Exit Strategy

Revert dei 3 file modificati. I test di hardening (`test_license_hardening.py`) vanno
rimossi o adattati. Zero impatto su dati o licenze gia' emesse.

## Supersedes / Superseded By

- Supersedes: nessuno (estende il sistema licenza esistente)
- Superseded by: eventuale migrazione a license server o obfuscation nativa
