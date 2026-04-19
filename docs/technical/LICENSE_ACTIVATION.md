# Attivazione Licenza — Guida Operativa

Procedura completa per attivare FitManager su un nuovo PC cliente.

## Architettura anti-copia

La licenza e' un JWT RS256 con **hardware binding**: il token contiene un hash SHA-256
della macchina del trainer (CPU + Motherboard + BIOS). Se copiato su un altro PC, il
fingerprint non corrisponde e l'app mostra "Computer non autorizzato".

```
┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  license.key     │     │  check_license() │     │  machine_fp      │
│  JWT con claims: │────>│  verifica:       │<────│  SHA-256 di:     │
│  - client_id     │     │  1. firma RSA    │     │  - CPU ID        │
│  - tier          │     │  2. expiry       │     │  - Board serial  │
│  - machine_id    │     │  3. machine_id   │     │  - BIOS serial   │
│  - exp           │     │     == fp reale? │     │  (via PowerShell) │
└──────────────────┘     └─────────────────┘     └──────────────────┘
```

## Flusso trainer (lato cliente)

```
1. Installa FitManager_Setup.exe
2. Avvia → /login → /setup (primo avvio, nessun trainer esiste)
3. Compila: Nome, Cognome, Email, Password → registrazione
4. Dopo registrazione → licenza mancante → redirect a /licenza
5. La pagina /licenza mostra:
   - Nome e cognome del trainer
   - Email del trainer
   - Codice Macchina (fingerprint breve + completo nell'email)
6. Il trainer clicca "Richiedi licenza":
   → si apre email pre-compilata con tutti i dati
   → oppure clicca "Copia tutto" e manda via WhatsApp/altro
7. Riceve license.key dall'admin
8. Copia license.key in C:\Program Files\FitManager\data\
9. Riavvia FitManager → licenza valida → dashboard
```

## Flusso admin (lato sviluppatore)

### Prerequisiti

- Chiave privata RSA in `~/.fitmanager/private_key.pem`
- Chiave pubblica copiata in `data/license_public.pem` (inclusa nell'installer)
- Se non esistono, generarle:
  ```bash
  python -m tools.admin_scripts.generate_license generate-keys
  cp ~/.fitmanager/public_key.pem data/license_public.pem
  ```

### Generare licenza per un nuovo cliente

```bash
# 1. Ricevi email/messaggio dal trainer con:
#    - Nome: Mario Rossi
#    - Email: mario@esempio.com
#    - Codice Macchina: 695ad621e92e710f76015d36db06b169d355ee01f89b722c99c5d8adc94a4315

# 2. Genera la licenza:
python -m tools.admin_scripts.generate_license sign \
  --client "mario-rossi" \
  --tier pro \
  --months 12 \
  --machine-id 695ad621e92e710f76015d36db06b169d355ee01f89b722c99c5d8adc94a4315 \
  --output mario-rossi-license.key

# 3. Manda il file mario-rossi-license.key al trainer
```

### Parametri disponibili

| Parametro | Obbligatorio | Descrizione |
|-----------|-------------|-------------|
| `--client` | Si | Identificativo cliente (es. `mario-rossi`, `gym-roma`) |
| `--tier` | Si | Livello: `basic`, `pro`, `enterprise` |
| `--months` | No (default 12) | Durata in mesi |
| `--max-clients` | No (illimitato) | Limite numero clienti nel CRM |
| `--machine-id` | Si | Hash SHA-256 completo (64 caratteri) dalla pagina /licenza |
| `--output` | No (default `data/license.key`) | Path file output |

### Verificare una licenza

```bash
python -m tools.admin_scripts.generate_license verify data/license.key
# Mostra: status, scadenza, client_id, tier, machine_id match/mismatch
```

### Vedere il fingerprint della macchina corrente

```bash
python -m tools.admin_scripts.generate_license fingerprint
# Mostra: hash completo (64 char) + breve (16 char) + display (con spazi)
```

## Trasferimento licenza (cambio PC)

Se il trainer cambia PC (nuovo computer, formattazione, cambio hardware):

1. Il trainer avvia FitManager sul nuovo PC
2. Vede "Computer non autorizzato" con il nuovo Codice Macchina
3. Manda il nuovo codice all'admin
4. L'admin ri-genera la licenza con il nuovo `--machine-id`
5. Il trainer sostituisce `license.key` e riavvia

La vecchia licenza smette automaticamente di funzionare sul vecchio PC
(il `machine_id` nel JWT non corrisponde piu' se l'hardware e' cambiato).

## Rinnovo licenza (scadenza)

1. Il trainer vede "Licenza scaduta" nella pagina /licenza
2. I dati di attivazione sono gia' visibili (nome, email, codice macchina)
3. L'admin ri-genera con gli stessi parametri + nuovo `--months`
4. Il trainer sostituisce `license.key` e riavvia

## Componenti tecnici

| Componente | Path | Ruolo |
|-----------|------|-------|
| Fingerprint engine | `api/services/machine_fingerprint.py` | SHA-256 di CPU+Board+BIOS via PowerShell |
| License service | `api/services/license.py` | Validazione JWT + check machine_id |
| License middleware | `api/main.py` (middleware) | Blocca API se licenza non valida (403) |
| CLI admin | `tools/admin_scripts/generate_license.py` | Genera keypair, firma licenze, verifica |
| Pagina licenza | `frontend/src/app/licenza/page.tsx` | UI attivazione con dati trainer + machine ID |
| Health endpoint | `/health` | Espone `machine_id` e `machine_id_full` (exempt da licenza) |
| System status | `frontend/src/components/settings/SystemStatusSection.tsx` | Mostra codice macchina in Impostazioni |

## Endpoint exempt da licenza

Questi endpoint funzionano anche senza licenza valida (necessari per setup e attivazione):

```
/health                    → diagnostica + machine_id
/api/auth/login            → login
/api/auth/register         → registrazione primo trainer
/api/auth/setup-status     → check primo avvio
/api/auth/reset-password   → cambio password (richiede current_password)
/media/*                   → file statici
/api/public/*              → portale anamnesi pubblico
```

## Sicurezza

- **Chiave privata** (`~/.fitmanager/private_key.pem`): MAI distribuire, MAI committare
- **Chiave pubblica**: embedded nel codice Python compilato (non piu' da file in produzione)
- **Fingerprint**: hash SHA-256, non espone seriali hardware reali
- **Backward compat**: licenze senza `machine_id` continuano a funzionare (campo opzionale)
- **Proxy fix**: `/licenza` rimossa da `AUTH_ONLY_PAGES` — un trainer loggato senza licenza deve poterla vedere

### Hardening anti-tampering (ADR-005, 2026-03-24)

In build PyInstaller (frozen mode), sono attive 4 protezioni aggiuntive:

| Protezione | Effetto |
|-----------|--------|
| Chiave pubblica embedded nel codice | `license_public.pem` su disco viene ignorato — impedisce sostituzione chiave |
| Integrity hash SHA-256 | Se la chiave embedded viene alterata nel bytecode, l'hash non corrisponde → blocco |
| Enforcement sempre ON | `LICENSE_ENFORCEMENT_ENABLED` env var viene ignorata — impossibile disabilitare |
| Fingerprint fail-closed | Se PowerShell/WMI non disponibile → blocco (non bypass silenzioso) |

In dev mode (non-frozen) il comportamento resta invariato per comodita' sviluppo.

Per il modello di sicurezza completo e la roadmap: `docs/technical/SECURITY_MODEL.md`
