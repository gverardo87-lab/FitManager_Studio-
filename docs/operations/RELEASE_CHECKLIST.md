# FitManager AI Studio — Release Checklist Windows v1.0.15

> Checklist viva della prossima candidate. `[x]` indica evidenza valida sul sorgente corrente;
> `[ ]` indica una prova da ripetere sul nuovo artefatto. Un PASS di una release precedente non viene
> trasferito automaticamente alla candidate.

> **Scope aggiornato 2026-09-01:** `v1.0.15` è la release Windows security/readiness pre-POC. Il
> blocco P è in HOLD. C0.1 GREEN protegge la portabilità di G1 prima di S1; C0.2 e G-MAC.2–5 non
> bloccano questa candidate e aprono soltanto dopo la release Windows e il trigger commerciale D11,
> con una propria versione/tag. Regia: `../specs/SPEC_PRE_POC.md`.

## 1. Baseline e autorità

- [x] Branch di sviluppo: `FitManager_Studio`.
- [x] Versione sorgente pre-bump: `1.0.14` in `api/__init__.py` e `frontend/package.json`.
- [ ] Target candidate: bump sincronizzato a `1.0.15` secondo `AGENTS.md`.
- [ ] Working tree pulito e `origin/FitManager_Studio...FitManager_Studio = 0 0` prima della pipeline.
- [x] Fonti operative: questa checklist, [SUPPORT_RUNBOOK.md](SUPPORT_RUNBOOK.md),
  [UPGRADE_PROCEDURE.md](UPGRADE_PROCEDURE.md) e
  [TUNNEL_ARCHITECTURE.md](../technical/TUNNEL_ARCHITECTURE.md).

## 2. Quality gate sul sorgente

- [x] Backend full suite post-R0.2: **910/910 PASS**; nessun codice backend applicativo modificato dopo.
- [x] Frontend post-R0.3: **161/161 PASS**, guard semantici **11/11** e build Next/TypeScript verde.
- [x] R0.1.5-live: edge operations **7/7 PASS**, Ruff e parse Bash/PowerShell verdi.
- [x] R0.4: canary **5/5**, gate combinato **25/25**, Ruff e review link/path verdi.
- [ ] Preflight candidate `tools/build/build-release.sh`: full pytest, Ruff, Next build e version sync.
- [ ] Nessun warning nuovo classificato come release-critical.
- [ ] G1/G2/G4 soddisfatti sulla baseline applicativa; G9–G11 pronti prima del real-data GO.
- [x] C0.0 contratto target chiuso: MacBook Air M1 2020, ARM64, 8 GB, Tahoe 26.5.1; nessun
  seriale/foto/UUID conservato nel repository o nei log.
- [ ] C0.1 RED→GREEN: build canary su `macos-15`, esecuzione dello stesso artefatto su `macos-26`;
  SQLCipher/G1, Nuitka standalone, frontend darwin-arm64 e dipendenze/hash verificati.
- **Tracker non bloccante v1.0.15:** C0.2 source-free sul target esatto resta in HOLD trigger Mac ed
  è obbligatorio prima di G-MAC.2; non viene attribuito come PASS della candidate Windows.

## 3. Build e packaging candidate

- [x] Backend build autorevole: Nuitka nativo x86-64 tramite `tools/build/build-backend-nuitka.sh`.
- [x] Frontend build autorevole: Next standalone tramite `tools/build/build-frontend.sh`.
- [x] Inno Setup produce `FitManager_Setup_<versione>.exe` e riceve la versione dalla pipeline.
- [x] Launcher versionato con `LICENSE_ENFORCEMENT_ENABLED=true` e senza avvio del trasporto legacy.
- [x] Build fail-closed su leak `crm.db`, riferimenti ISS, cataloghi cifrati e nutrition integrity.
- [x] `lego.exe` v5.2.1 entra nel bundle solo dopo verifica hash/versione/target e licenza MIT.
- [ ] Costruire `dist/FitManager_Setup_1.0.15.exe` con la pipeline ADR-004.
- [ ] Ispezionare l'installer finale: `backend/lego.exe` e
  `backend/THIRD_PARTY_LICENSES/lego-MIT.txt` presenti.
- [ ] Verificare `dist/manifest.json`, SHA-256, commit, branch, safety gate e tag `v1.0.15`.

## 4. Licenza e runtime

- [x] `license.key` cliente esclusa da repository, installer assets e bundle generico.
- [x] Il bundle contiene soltanto `license_public.pem` per la verifica.
- [x] Enforcement ON di default nel runtime compiled, anche senza launcher.
- [x] `/health` espone stato licenza, modo applicativo e modo distribuzione.
- [x] Contratto C0 fail-closed: nessuna modifica a middleware/exempt/enforcement e nessuna licenza
  fittizia per ampliare lo smoke; il CRM target-bound si verifica in G-MAC.4.
- [ ] Installazione candidata: `data/license.key` presente nel path runtime effettivo.
- [ ] Prova negativa candidata: licenza assente → `/licenza` e CRM bloccato.
- [ ] Prova positiva candidata: licenza valida → health e login operativi.

## 5. Dati e cataloghi

- [x] Audit read-only 2026-07-28: `crm.db`, `catalog.db` e `nutrition.db` con
  `PRAGMA integrity_check = ok`; zero contaminazione catalog/nutrition nel DB business.
- [x] Catalogo sorgente: **522** righe esercizio, **495** non eliminate, **466** attive
  (`in_subset=1 AND deleted_at IS NULL`); il gate media richiede esattamente 466 attive.
- [x] Tassonomia sorgente: **53** muscoli, **15** articolazioni, **47** condizioni mediche;
  **6996** `esercizi_muscoli`, **1452** `esercizi_articolazioni`, **5154** `esercizi_condizioni`.
- [x] Relazioni/media sorgente: **868** `esercizi_relazioni`, **738** record `esercizi_media`,
  **750** file immagine. Nessun numero storico 400/500 viene usato come acceptance corrente.
- [x] Nutrition sorgente: **880** alimenti attivi e **12** plan template; restano vincolanti le soglie
  fail-closed della pipeline.
- [x] Seed sorgente richiesti: esercizi, progressioni, junction tassonomiche e media.
- [ ] Candidate: `crm.db` generico vuoto e first-run-safe; nessun dato trainer nel bundle.
- [ ] Candidate: snapshot catalog/nutrition cifrati prodotti dalla pipeline e conteggi nel manifest.
- [ ] Restore del backup trainer selezionato verificato sull'installazione candidata.

## 6. Rete, FRP e portale pubblico

- [x] Backend compiled in ascolto su `127.0.0.1:8000`; Next è l'unico proxy applicativo esposto.
- [x] Frontend standalone su `0.0.0.0:3000` per LAN e origine locale del tunnel.
- [x] Istanza provisionata: `public_access_provider = managed_frp` derivato dalla licenza.
- [x] Diagnostica autenticata: `GET /api/system/tunnel-status` restituisce stato, `instance_id`,
  `public_url` e PID; stato atteso durante il test: `connected`.
- [x] Origine pubblica: `https://<instance_id>.fitmanagerstudio.com`; nessuna configurazione DNS
  o URL pubblico manuale per singolo trainer.
- [x] TLS termina sul PC trainer; il VPS esegue SNI passthrough e resta data-blind.
- [x] R0.1.5-live su `gvera-dev`: `R0.1.5_STRICT_PROBE=PASS`, chain/SAN Let’s Encrypt validi,
  HTTP non-challenge 404, `/health` → 200, route `/public/` → 200.
- [x] Route separation live: `/clienti` → 404 e `/api/clients` → 404 dal dominio pubblico.
- [ ] Ripetere health, portale reale, CRM 404 e TLS strict dall'installer candidato su rete esterna.
- [ ] Test LAN da tablet/smartphone sullo stesso Wi-Fi.
- [ ] Test link anamnesi reale da smartphone, inclusa validazione token e salvataggio.

## 7. Backup, restore e flussi manuali

- [x] API backup: create, verify, download e restore WAL-safe con safety backup.
- [x] Export JSON v2 e auto-backup startup disponibili; retention applicativa presidiata.
- [ ] Upgrade in-place da un'installazione supportata, preservando `data/` e `license.key`.
- [ ] Restore candidato: clienti, contratti/rate, schede, agenda, cassa e media verificati.
- [ ] Cliente → contratto → rata → pagamento → cassa.
- [ ] Scheda → esercizi → salvataggio → export.
- [ ] Evento PT → completamento → crediti coerenti.

## 8. Go/no-go candidate

Non consegnare la v1.0.15 finché resta aperto uno di questi punti:

- [ ] pipeline ADR-004 completa e artefatto sigillato;
- [ ] installazione/upgrade reale e licenza negativa/positiva;
- [ ] restore reale e flussi core manuali;
- [ ] test FRP esterno sulla candidate con TLS strict, portale 200 e CRM 404;
- [ ] `CHANGELOG.md` con sezione v1.0.15 e note Upgrade;
- [ ] registrazione dell'artefatto/consegna in `docs/operations/DEPLOYMENTS.md` quando effettuata.

## 9. Rollback

1. Fermare FitManager e conservare log/snapshot diagnostico.
2. Ripristinare il backup `pre_update_*.sqlite` soltanto tramite la procedura di restore.
3. Reinstallare l'ultimo installer sigillato noto e riposizionare `data/license.key` se necessario.
4. Verificare login, health, DB/catalog, backup e percorso pubblico prima di dichiarare recovery.

Storico release e prove precedenti: `CHANGELOG.md`, `docs/operations/DEPLOYMENTS.md` e
`docs/learning/BUILD_LOG.md`.

## 10. Tracker distribuzione macOS — fuori dal go/no-go v1.0.15

Dopo R1-WIN e trigger D11, una release Mac dedicata deve riprendere almeno questi gate:

- C0.2 source-free sul target esatto, senza dati reali o identificatori nei report;
- companion `frpc` e `lego` Darwin ARM64 con versione/SHA-256/licenza verificati;
- artifact costruito su `macos-15`, provato invariato su `macos-26` e sul target esatto;
- Developer ID/notarizzazione, fingerprint/licenza, upgrade `data/`-safe e zero processi orfani;
- nuova versione/tag ADR-004: mai ricostruire `v1.0.15` da un commit differente.
