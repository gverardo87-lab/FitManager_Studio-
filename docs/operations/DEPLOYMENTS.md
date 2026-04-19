# Deployment Registry

Registro ufficiale delle consegne FitManager AI Studio.
Ogni riga = un installer consegnato e installato su macchina del cliente.

---

## Deployments

| Data | Cliente | Email | Versione | Machine ID | Tier | Scadenza licenza | SHA-256 installer | Note |
|------|---------|-------|----------|------------|------|-------------------|-------------------|------|
| 2026-04-19 | Alessio Crociani | — | v1.0.7 | *(da compilare)* | Partner | *(da compilare)* | *(da compilare)* | Primo install — primo partner ufficiale |

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
