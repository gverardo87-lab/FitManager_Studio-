# docs/learning/ — Diario di apprendimento

Formazione personale del founder-developer, in parallelo allo sviluppo di FitManager.

## Cosa contiene

- **Concetti tecnici studiati**: crittografia, networking, SSH, protocolli — appunti di studio, non spec di implementazione
- **Diario cronologico**: cosa ho fatto, cosa ho imparato, perché ho preso certe decisioni
- **Metodo di studio**: come organizzo l'apprendimento mentre sviluppo

## Cosa NON e'

- NON e' documentazione vincolante per il codice (quella sta in `docs/technical/`)
- NON e' materiale formativo per i trainer (quello sta in `docs/product/`)
- NON e' spec di feature (quelle stanno in `docs/upgrades/`)

## Regola per gli agenti

**Questo dominio va IGNORATO durante l'implementazione di codice.**
I file qui dentro sono materiale didattico personale. Non influenzano decisioni architetturali,
non contengono requisiti, non sono SSoT per nessun componente del sistema.

## File presenti

| File | Ambito |
|------|--------|
| `LEARNING_METHOD.md` | Metodo di studio: 4 principi, flusso cattura/elaborazione, ponte con Claude Code |
| `BUILD_LOG.md` | Diario cronologico: cosa ho fatto e quando, checklist per fase |
| `LEARNING_LINUX_SYSADMIN.md` | Concetti Linux/Unix: crittografia asimmetrica, chiavi SSH, passphrase |
| `LEARNING_NETWORKING.md` | DNS, reverse proxy, TLS, SNI, tunnel, NAT, FRP |
| `LEARNING_FASE1_BASI_TEORICHE.md` | Preparazione Fase 1: JWT, instance_id, tunnel_manager, bundling |
| `LEARNING_TUNNEL_MANAGER.md` | Casi edge processo figlio: sleep/wake, rete, backoff, health check e2e |

## Convenzioni

- Un file `LEARNING_*.md` per dominio tecnico (networking, security, deployment, app architecture)
- `BUILD_LOG.md` = diario cronologico, rimanda ai file LEARNING per i concetti
- Ogni concetto segue il template a 3 livelli definito in `LEARNING_METHOD.md` §4
