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
| [ADR-002](ADR-2026-03-09-operational-workspace-case-engine.md) | 2026-03-09 | Accettata | Workspace "Oggi" ranking + dominance matrix |
| [ADR-003](ADR-003-separazione-architetturale-3-database.md) | 2026-03-19 | Accettata | Separazione 3 DB: crm.db sacro, catalog.db + nutrition.db read-only |
| [ADR-004](ADR-004-release-pipeline-sicuro.md) | 2026-03-21 | Accettata | Release pipeline 5 fasi con safety gates |
| [ADR-005](ADR-005-license-hardening-anti-tampering.md) | 2026-03-24 | Accettata | License hardening: embedded key, env bypass block, fingerprint fail-closed |

## Flusso

1. Copia `ADR_TEMPLATE.md`.
2. Compila opzioni, decisione e conseguenze.
3. Linka l'ADR nell'upgrade log relativo.
