# Deployment Registry

Registro ufficiale delle consegne FitManager AI Studio.
Ogni riga = un installer consegnato e installato su macchina del cliente.

---

## Deployments

| Data | Cliente | Email | Versione | Machine ID | Tier | Scadenza licenza | SHA-256 installer | Note |
|------|---------|-------|----------|------------|------|-------------------|-------------------|------|
| 2026-04-19 | Alessio Crociani | alessio@crocianicoaching.com | v1.0.7 | `4c06bb47ead1...9d0f37` | pro | 2027-04-14 | `7085add53826...09922` | Primo install — primo partner ufficiale |

---

## Release artifacts (sealed, pre-consegna)

Build sigillati dalla pipeline ADR-004, in attesa di consegna. Quando consegnati, aggiungere la riga corrispondente nella tabella **Deployments** sopra (con machine ID + licenza).

| Data build | Versione | Commit | SHA-256 installer | Dimensione | Note |
|------------|----------|--------|-------------------|------------|------|
| 2026-06-14 | v1.0.11 | `8ff0cd8` | `1101f674ed0d8f41853017435163ca716226aec357ad376e5ad526ae93773ab6` | ~117 MB | Bugfix: cross-DB FK latente su `metriche` (i crm.db fresh da installer crashavano al 1° salvataggio misurazione). **Auto-heal dei DB deployati al primo boot** (FK rimossa, dati preservati, −80% size). + cleanup catalogo Thread A (29 keeper orfani, dedup, ADR-003 chiuso). Target upgrade: Alessio (da v1.0.7), Chiara. |

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
