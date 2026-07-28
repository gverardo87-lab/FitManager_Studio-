# LAUNCH_SCOPE.md - FitManager AI Studio

Questo documento definisce cosa conta davvero per arrivare al lancio.
Non e' un changelog e non e' un backlog totale.

## Obiettivo

Portare FitManager a un lancio credibile come software locale Windows per chinesiologi, personal trainer e professionisti fitness a P.IVA,
con installazione ripetibile, supporto gestibile e flussi core affidabili.

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

## Criteri di passaggio al launch

Prima del lancio allargato servono evidenze su:

- installazione o upgrade su macchina Windows non-dev
- percorso negativo licenza (`/licenza`) verificato
- backup e restore riusciti con dati reali
- validazione LAN e origine FRP gestita `https://<instance_id>.fitmanagerstudio.com` da rete esterna
- TLS strict browser-trusted, portale pubblico operativo e CRM → 404 sul dominio pubblico
- artefatto di rilascio ripetibile, versionato e tracciabile
- issue note e fallback di supporto chiari

## Fuori scope fino a dopo il launch

- cloud sync o trasformazione in SaaS
- app mobile native
- chat/messaging in-app
- modulo nutrizione avanzato (meal prep, shopping list, tracking aderenza)
- multi-operatore/team workflow
- nuove macro-feature AI non necessarie al CRM core
- redesign trasversali che non spostano affidabilita' o supportabilita'

> **Post-launch**: la roadmap 90 giorni (ADR-006 + `docs/product/POST_LAUNCH_ROADMAP_90D.md`) definisce
> la strategia PWA sul percorso FRP e il modello hardware FitManager Box. L'eventuale accesso CRM
> remoto segue esclusivamente la Strada B di `TUNNEL_SECURITY_BOUNDARY.md`, dopo i relativi gate di
> sicurezza; non fa parte del lancio Windows corrente.

## Regole anti-scope-creep

- Nessuna nuova macro-feature entra se rallenta installazione, supporto, licenza, backup o connettivita'.
- La UI puo' migliorare, ma non a costo di regressioni nei flussi core del trainer.
- La documentazione di launch deve restare corta: decisioni vive qui, dettagli storici nel ledger upgrade.

## Riferimenti operativi

Per la procedura concreta usare:

- `docs/operations/SUPPORT_RUNBOOK.md`
- `docs/operations/UPGRADE_PROCEDURE.md`
- `docs/technical/TUNNEL_ARCHITECTURE.md` (operations VPS edge; ex `TAILSCALE_FUNNEL_SETUP.md`, ora archiviato)
- `docs/operations/RELEASE_CHECKLIST.md`

Per la storia dettagliata dei microstep:

- `docs/learning/BUILD_LOG.md` (log unico append-only)
