# ADR Framework

ADR = Architecture Decision Record.

Usa un ADR quando una scelta:
- impatta piu moduli o team decisions future,
- introduce tradeoff non banali,
- deve restare tracciabile nel tempo.

## Convenzione file

Formato consigliato: `ADR-YYYY-MM-DD-short-title.md`

Esempio:
- `ADR-2026-03-03-workout-replacement-ranking.md`

## Stato ADR

- proposed
- accepted
- superseded
- deprecated

## Indice ADR

| ADR | Data | Stato | Decisione |
|-----|------|-------|-----------|
| [ADR-001](ADR-001-single-source-of-truth-scientifica.md) | 2026-03-07 | Accettata | Backend = SSoT per dati scientifici |
| ADR-002 | 2026-03-09 | Rimossa (obsoleta) | Workspace operativo — ADR rimosso come obsoleto (commit `0748ddf`); la decisione vive negli UPG spec archiviati (`docs/archive/specs/UPG-2026-03-09-*`) |
| [ADR-003](ADR-003-separazione-architetturale-3-database.md) | 2026-03-19 | Accettata | Separazione 3 DB: crm.db sacro, catalog.db + nutrition.db read-only |
| [ADR-004](ADR-004-release-pipeline-sicuro.md) | 2026-03-21 | Accettata | Release pipeline 5 fasi con safety gates |
| [ADR-005](ADR-005-license-hardening-anti-tampering.md) | 2026-03-24 | Accettata | License hardening: embedded key, env bypass block, fingerprint fail-closed |
| [ADR-006](ADR-006-fitmanager-box-multi-platform.md) | 2026-03-27 | Accettata | FitManager Box multi-platform (Raspberry Pi 5 always-on) |
| [ADR-007](ADR-007-anti-reverse-engineering.md) | 2026-04-09 | Accettata | Anti-reverse engineering: 4-step layered hardening (bundle sanitization, DB encryption, Nuitka) |
| [ADR-008](ADR-008-builder-fullscreen-science-panel.md) | 2026-03-26 | Accettata | Builder fullscreen con Science Panel live |
| [ADR-009](ADR-009-client-workout-portal.md) | 2026-03-29 | Accettata | Client Workout Portal: token multi-uso, ExerciseLog, 5 endpoint pubblici |
| [ADR-010](ADR-010-fitscan-computer-vision-biomechanics.md) | 2026-03-25 | Accettata | FitScan: Computer Vision per analisi corporea e biomeccanica |
| [ADR-011](ADR-011-tunnel-frp-self-hosted.md) | 2026-06-09 | Accettata | Migrazione a Tunnel FRP self-hosted (SNI passthrough, instance_id, route separation, P2 data-blind) |
| ADR-012 | — | Riservato (pending gate) | Routing media per classificazione del dato — hosting centrale clip (v2.2). In attesa del gate autotest (`docs/learning/LEARNING_METHOD.md` §9 / `LEARNING_MEDIA_CLOUD_ARCHITECTURE.md` §9). Razionale in `docs/technical/EXERCISE_LIBRARY_STRATEGY.md` §4ter (hosting centrale media) |
| [ADR-013](ADR-013-crm-db-encryption-at-rest.md) | 2026-06-16 | **Accettata** (2026-06-17) | Cifratura a riposo di crm.db password-bound (SQLCipher + envelope DEK-KEK + boot a due fasi). Gate G1 di `docs/technical/PRE_DELIVERY_SECURITY_GATE.md`. Spike validato; decisioni founder: recovery key obbligatoria, portale fail-closed, policy password minima. Implementazione dopo design di dettaglio |
| [ADR-014](ADR-014-gestione-finanziaria-cassa-competenza.md) | 2026-06-19 | Accettata | Gestione finanziaria: tassonomia cassa/competenza vincolante + vista Contract-first "contratti da pianificare" + confine di posizionamento (cash management neutro). Referenzia le 3 spec in `docs/technical/`. Implementazione: prima rinnovo, poi asse temporale |
| [ADR-015](ADR-015-renewal-retention-funnel.md) | 2026-06-20 | Accettata (+2 emend.) | Funnel Rinnovi & Retention: nessuna perdita silenziosa di contratti/clienti/**sedute**. Emend.1 client-aware (cliente non ingaggiato); Emend.2 stato **SOSPESO** (scaduto+crediti residui = sedute da erogare, worklist dedicata). Ciclo 4 stati. Spec v2.0 |
| [ADR-016](ADR-016-asse-erogato-canonico-recesso.md) | 2026-06-26 | Accettata (§1 emendato da ADR-017) | Asse **EROGATO** canonico per la valorizzazione del recesso (sedute `Completato`; OCCUPAZIONE mai un importo €) + **forfeiture** delle prenotate + **riconciliazione** display↔rimborso obbligatoria (no recompute off-SSoT). Ratifica le invarianti G7.0→G7.6. Corollari: `unpay` su terminato → 409 (reject, riapri prima); marker `reopen`; grep-guard euro-da-crediti. Audit `AUDIT_CREDITI_RIMBORSO_2026-06-26.md`, blocco G7.7 |
| [ADR-017](ADR-017-rinvio-libera-credito.md) | 2026-06-26 | Accettata | **Il rinvio libera il credito**: `Rinviato` fuori dall'asse OCCUPAZIONE-credito (= `Programmato + Completato`). **Emenda ADR-016 §1.** Asse EROGATO/denaro invariante per costruzione (oracolo settlement byte-identico). Decisioni founder D-AUTO-CLOSE / D-MODELLO / D-GUARD + overlap CAMBIA. Trigger: 2ª segnalazione Chiara ("rinviate scalate come svolte"). Spec `SPEC_RINVIO_LIBERA_CREDITO.md`, blocco G7.8 |
| [ADR-018](ADR-018-terminazione-bilaterale-credito-trainer.md) | 2026-06-27 | Accettata | **Terminazione bilaterale**: il ramo `servizio_reso > versato` esige una **scelta esplicita** (incasso contestuale *editabile* `[0,R−V]` / rinuncia auditata) invece del write-off implicito (`SALDO_A_PERDERE`→`DECADENZA`). Esito puro balance-based (`CREDITO_CLIENTE/TRAINER/PARI`); nuova categoria `INCASSO_CONGUAGLIO_CONTRATTO`; **credito differito** come entità `crediti_terminazione` **fuori da `residuo()`** (residuo 0 su CHIUSO preservato). **Estende ADR-016** (norma il ramo positivo lasciato implicito). Decisioni founder D-ESITO-PURO/SCELTA/IMPORTO/CATEGORIA/CREDITO-DIFFERITO/REOPEN/MOTIVO. Spec `SPEC_TERMINAZIONE_BILATERALE_E_TUTELA_TRAINER.md` + audit `AUDIT_TERMINAZIONE_BILATERALE_2026-06-27.md`. Blocchi **G7.9** (core) **+ G7.10** (credito differito) |

## Flusso

1. Copia `ADR_TEMPLATE.md`.
2. Compila opzioni, decisione e conseguenze.
3. Linka l'ADR nell'upgrade log relativo.
