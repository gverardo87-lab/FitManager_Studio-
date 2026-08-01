# LAUNCH_SCOPE.md - FitManager AI Studio

Questo documento definisce cosa conta davvero per arrivare al lancio.
Non e' un changelog e non e' un backlog totale. Fino alla Wave 0, ordine, deadline e interlock
operativi vivono esclusivamente in `docs/specs/SPEC_PRE_POC.md`.

## Obiettivo

Portare FitManager a un lancio credibile come software locale per chinesiologi, personal trainer e
professionisti fitness a P.IVA, con Windows come baseline primaria e macOS Apple Silicon ARM64 come
deliverable pilot assistito, installazione ripetibile, supporto gestibile e flussi core affidabili.

## In scope ora

- installazione locale con licenza, setup wizard e runtime health leggibile
- core CRM operativo:
  - clienti
  - contratti e pagamenti
  - agenda
  - cassa
  - schede/workout
  - training intelligence (analisi scientifica post-esecuzione + workout diff piano vs eseguito)
  - misurazioni/anamnesi
- backup, restore e diagnostica locale
- connettivita' guidata per:
  - `local_only`
  - `trusted_devices`
  - `public_portal`
- portale pubblico per anamnesi cliente
- runbook di supporto e procedura di upgrade realmente eseguibili
- `v1.0.15` security/readiness: G1, G2, completamento G4 e processo G9-G11 prima dei dati reali
- portability canary macOS prima dell'application freeze, senza packaging cliente
- artifact macOS ARM64 firmato/notarizzato dopo l'application freeze, dalla stessa baseline Windows

## Criteri di passaggio al launch

Prima del lancio allargato servono evidenze su:

- installazione o upgrade su macchina Windows non-dev
- installazione/upgrade su Mac ARM64 pulito per il pilot assistito
- percorso negativo licenza (`/licenza`) verificato
- backup e restore riusciti con dati reali
- validazione LAN e origine FRP gestita `https://<instance_id>.fitmanagerstudio.com` da rete esterna
- TLS strict browser-trusted, portale pubblico operativo e CRM → 404 sul dominio pubblico
- artefatto di rilascio ripetibile, versionato e tracciabile
- issue note e fallback di supporto chiari
- G1-G4 verdi prima di qualsiasi consegna data-bearing; G9-G11 prima del primo atleta reale

## Fuori scope fino a dopo il launch

- cloud sync o trasformazione in SaaS
- app mobile native
- chat/messaging in-app
- modulo nutrizione avanzato (meal prep, shopping list, tracking aderenza)
- multi-operatore/team workflow
- nuove macro-feature AI non necessarie al CRM core
- redesign trasversali che non spostano affidabilita' o supportabilita'
- blocco P fino alle evidenze Wave 0 e nuovo GO founder
- supporto macOS Intel o self-service generalizzato; il support boundary pre-POC e' ARM64 pilot assistito

> **Post-launch:** la roadmap di marzo 2026 e' stata archiviata come fotografia superseded. PWA,
> FitManager Box e accesso CRM remoto verranno ripianificati dopo la Wave 0. L'eventuale accesso CRM
> remoto segue esclusivamente la Strada B di `TUNNEL_SECURITY_BOUNDARY.md`, dopo i relativi gate.

## Regole anti-scope-creep

- Nessuna nuova macro-feature entra se rallenta installazione, supporto, licenza, backup o connettivita'.
- La UI puo' migliorare, ma non a costo di regressioni nei flussi core del trainer.
- La documentazione di launch deve restare corta: regia in `SPEC_PRE_POC`, criteri nelle SSoT,
  fotografie in `docs/archive/` e storia nel solo `BUILD_LOG.md`.

## Riferimenti operativi

Per la procedura concreta usare:

- `docs/specs/SPEC_PRE_POC.md`
- `docs/operations/SUPPORT_RUNBOOK.md`
- `docs/operations/UPGRADE_PROCEDURE.md`
- `docs/technical/TUNNEL_ARCHITECTURE.md` (operations VPS edge; ex `TAILSCALE_FUNNEL_SETUP.md`, ora archiviato)
- `docs/operations/RELEASE_CHECKLIST.md`

Per la storia dettagliata dei microstep:

- `docs/learning/BUILD_LOG.md` (log unico append-only)
