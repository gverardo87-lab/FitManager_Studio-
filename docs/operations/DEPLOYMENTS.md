# Deployment Registry

Registro ufficiale delle consegne FitManager AI Studio.
Ogni riga = un installer consegnato e installato su macchina del cliente.

---

## Deployments

| Data | Cliente | Email | Versione | Machine ID | Tier | Scadenza licenza | SHA-256 installer | Note |
|------|---------|-------|----------|------------|------|-------------------|-------------------|------|
| 2026-04-19 | Alessio Crociani | alessio@crocianicoaching.com | v1.0.7 | `4c06bb47ead1...9d0f37` | pro | 2027-04-14 | `7085add53826...09922` | Primo install — primo partner ufficiale |
| 2026-06-18 | Alessio Crociani | alessio@crocianicoaching.com | v1.0.13 | `4c06bb47ead1...9d0f37` | pro | 2027-06-13 | `948b5e426b69...57eb88` | **Upgrade da v1.0.7.** Prima istanza con **tunnel FRP attivo** (`instance_id=alessio-crociani` → `alessio-crociani.fitmanagerstudio.com`). Include fix fingerprint INC-2026-06-18 + tutte le release intermedie (1.0.8→1.0.13). Consegnato via WeTransfer (installer + nuova `license.key`, stesso machine_id). **Testato live in call: portale schede pubbliche via tunnel funzionante.** |

> **Stato relazione 2026-08-29:** exit Alessio ratificata in
> `docs/specs/SPEC_EXIT_ALESSIO.md`. Le righe sopra restano storico fedele delle consegne, ma non
> attestano un rapporto partner corrente né uso operativo del CRM. In E0 non sono stati revocati
> licenza, tunnel, DNS o accessi: lo stato tecnico resta da verificare e chiudere soltanto dopo
> comunicazione, review contrattuale ed eventuale export/no-data nei gate E1–E3.

---

> 🎯 **Milestone 2026-06-18 — Primo accesso reale al portale pubblico via tunnel FRP.** Con la consegna di v1.0.13 ad Alessio (primo partner), un cliente esterno ha aperto **dal vivo** un link scheda pubblico instradato attraverso il tunnel FRP self-hosted (VPS edge Hetzner, SNI passthrough, P2 data-blind), terminato sul PC del trainer. È la **prima validazione sul campo** dell'architettura tunnel (Fase 1) con un trainer reale e un link condiviso reale — non più solo test e2e interni. Da qui in poi l'architettura data-blind non è teoria: è in produzione. Residuo noto: cert self-signed (G3/Fase 2) → eventuali avvisi browser sui link pubblici fino a Let's Encrypt.

---

## Release artifacts (sealed, pre-consegna)

Build sigillati dalla pipeline ADR-004, in attesa di consegna. Quando consegnati, aggiungere la riga corrispondente nella tabella **Deployments** sopra (con machine ID + licenza).

| Data build | Versione | Commit | SHA-256 installer | Dimensione | Note |
|------------|----------|--------|-------------------|------------|------|
| 2026-06-14 | v1.0.11 | `8ff0cd8` | `1101f674ed0d8f41853017435163ca716226aec357ad376e5ad526ae93773ab6` | ~117 MB | Bugfix: cross-DB FK latente su `metriche` (i crm.db fresh da installer crashavano al 1° salvataggio misurazione). **Auto-heal dei DB deployati al primo boot** (FK rimossa, dati preservati, −80% size). + cleanup catalogo Thread A (29 keeper orfani, dedup, ADR-003 chiuso). Target upgrade: Alessio (da v1.0.7), Chiara. |
| 2026-06-16 | v1.0.12 | `cc0204e` | `df2d602e9e0959612fdd7c898c9e1e61522768170232dbe590e2fac36e51fb50` | ~117 MB | Bugfix installer: aggiornamento "a caldo" su v1.0.11 falliva con `ERROR_ACCESS_DENIED` (codice 5) su `backend\frpc.exe`, bloccato da un processo `frpc.exe` orfano. Fix B (causa radice): `frpc` agganciato a Windows Job Object kill-on-close (muore col backend). Fix A (sintomo): installer chiude i processi prima di sovrascrivere (`CloseApplications` + `taskkill` in `PrepareToInstall`). Vedi `docs/incidents/INC-2026-06-15-installer-frpc-lock.md`. Target upgrade: Alessio (da v1.0.7), Chiara (da v1.0.11). |
| 2026-06-18 | v1.0.13 | `fe085e7` | `948b5e426b6977627c3674cc91c1bb9b541ef21af5547aa03318bf772057eb88` | ~117 MB | Bugfix: fingerprint hardware **parziale** (query WMI vuota a intermittenza) produceva un hash ≠ `machine_id` firmato → falso `wrong_machine` → blocco licenza intermittente del CRM (INC-2026-06-18, evidenza: 45+ episodi nel log di Chiara). Fix: mai hash parziale (`unavailable` fail-closed), cache solo del completo 3/3 (auto-heal), retry; hash 3/3 invariato → licenze esistenti valide. Build via **MSVC** (MinGW incompatibile col gcc winlibs corrente). **CONSEGNATA ad Alessio 2026-06-18** (vedi Deployments). Target anche Chiara (da v1.0.10, stesso bug). |

---

## Procedura

1. **Build**: `bash tools/build/build-release.sh` (genera installer + SHA-256 in output)
2. **Firma licenza**: `python -m tools.admin_scripts.generate_license sign --client "nome-cognome" ...`
3. **Consegna**: installer + `license.key` al cliente
4. **Registra**: aggiungere riga in tabella sopra con tutti i campi compilati
5. **Commit**: `git add docs/operations/DEPLOYMENTS.md && git commit -m "deploy: vX.Y.Z consegnata a <cliente>"`

## Convenzioni

- **Machine ID**: SHA-256 64 char da `generate_license fingerprint` sulla macchina del cliente
- **SHA-256 installer**: hash del file `.exe` consegnato (output di `build-release.sh` fase seal)
- **Tier**: `founder` | `pro` | `inner_circle` | `partner`
- **Upgrade**: nuova riga con nota "Upgrade da vX.Y.Z"
