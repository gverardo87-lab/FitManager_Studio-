"""invariant_gate — sensore osservabile degli invarianti del dominio finanziario (G9.0, ADR-022).

Invoca `contract_state.assert_contract_invariants` in coda a una transizione che muove denaro e
**logga (warn)** le eventuali violazioni di I1/I4/I5/I6. È il PASSO 2 di G8.2-prep
(`_log_invariant_violations`, prima locale a `contracts.py`) **promosso a sensore ovunque**: oggi era
cablato a UNA sola transizione (reopen), ora gira su tutte (G9.0-a).

**NESSUN `try/except`.** Il sensore è TOTALE per costruzione, non *fail-safe-by-catch*:
`assert_contract_invariants` è pura + `getattr(..., default)` → non solleva su un Contract ben tipato;
le 3 query sono `SELECT` identici a quelli che gli endpoint già eseguono (se sollevano, è un DB rotto →
la transazione è comunque condannata, stesso destino del `commit()`). Se questo solleva è un BUG del
sensore che DEVE fallire rumorosamente (la suite lo cattura, AC-G90-1), MAI essere inghiottito: un
sensore nato per chiudere i fallimenti silenziosi non può diventarne uno (regola #6 Determinismo;
`api/CLAUDE.md` Convenzioni). Razionale completo: `SPEC_G9_FINANCIAL_COMMAND_LAYER.md` §A.1-bis.

**G9.4-a — da sensore a GATE (flag-driven):** le violazioni I1/I4 (chiuso⟹residuo-0, quota≥0)
diventano **409 + rollback** quando `INVARIANT_ENFORCEMENT=raise` — default in dev/CI/test (`not
is_compiled()`), `log` in compiled/prod finché la telemetria G9.0 non è provata pulita sul campo
(AC-G94-2/G94-4). I5/I6 e le ancore ledger restano **warn** (telemetria). Il raise avviene PRIMA del
`session.commit()` del caller → la transazione non viene mai scritta (rollback per costruzione).
"""

import logging
import os

from fastapi import HTTPException, status
from sqlmodel import Session, select

from api.config import is_compiled

from api.models.contract import Contract
from api.models.credito_cliente import CreditoCliente
from api.models.movement import CashMovement
from api.models.rate import Rate
from api.services import contract_state as cstate
from api.services.cash_categories import CATEGORIA_RIMBORSO_CONTRATTO
from api.services.financial.ledger import project_columns_from_ledger

logger = logging.getLogger(__name__)

# G9.4-a: invarianti promossi a gate duro (409+rollback). I5/I6 restano warn: la loro ancora forte
# vive nella /reconciliation e diventerà gate quando la telemetria di prod sarà provata pulita.
ENFORCE_HARD = frozenset({"I1", "I4"})


def _enforcement_mode() -> str:
    """'raise' | 'log'. Override esplicito via env INVARIANT_ENFORCEMENT; default: raise in dev/CI/test,
    log in compiled (prod) — strumenta-poi-imponi (ADR-022): il gate si accende dove la suite lo prova
    a ogni run, e resta osservazione dove i dati sono reali finché la telemetria non è verde."""
    return os.getenv("INVARIANT_ENFORCEMENT") or ("log" if is_compiled() else "raise")


def enforce_contract_invariants(session: Session, contract: Contract, *, motivo: str) -> None:
    """Osserva E IMPONE (G9.4-a) gli invarianti I1/I4/I5/I6 sul contratto in coda a una transizione.

    Fornisce a `assert_contract_invariants` la fotografia netta (`crediti_cliente` del contratto, I5),
    l'ancora ledger forte di I5 (Σ USCITA RIMBORSO_CONTRATTO diretto) e le rate attive (I6, INV-RATE).
    Ogni violazione è SEMPRE loggata (telemetria); con `_enforcement_mode() == "raise"` una violazione
    **I1/I4** solleva `HTTPException 409` PRIMA del commit del caller → la transizione fa rollback
    (zero scrittura, AC-G94-1). Va chiamata immediatamente prima di `session.commit()`.
    """
    crediti = session.exec(
        select(CreditoCliente).where(CreditoCliente.id_contratto_origine == contract.id)
    ).all()
    rimborso_diretto = round(sum(m.importo for m in session.exec(
        select(CashMovement).where(
            CashMovement.id_contratto == contract.id,
            CashMovement.tipo == "USCITA",
            CashMovement.categoria == CATEGORIA_RIMBORSO_CONTRATTO,
            CashMovement.deleted_at == None,  # noqa: E711 (SQLModel richiede == None)
        )
    ).all()), 2)
    rate_attive = session.exec(
        select(Rate).where(Rate.id_contratto == contract.id, Rate.deleted_at == None)  # noqa: E711
    ).all()
    violazioni = list(cstate.assert_contract_invariants(
        contract, crediti, rimborso_cassa_diretto=rimborso_diretto, rate_attive=rate_attive
    ))
    for v in violazioni:
        logger.warning(
            "Invariante %s violato dopo '%s' sul contratto %s: %s",
            v.code, motivo, contract.id, v.message,
        )

    # G9.2-a: ancora ledger-VERSATO (`totale_versato == Σ ENTRATA[id_contratto]`). `assert_contract_invariants`
    # copre già il lato RIMBORSO (I5); questo aggiunge il lato versato via `project_columns_from_ledger`, la
    # derivazione unica delle colonne dal mastro. Log-only (gate duro in G9.4); su DB post-penna è vero per
    # costruzione → una violazione segnala drift legacy o un write fuori-penna.
    proj = project_columns_from_ledger(session, contract.id)
    if abs((contract.totale_versato or 0) - proj["versato"]) > 0.01:
        logger.warning(
            "Ancora ledger-versato violata dopo '%s' sul contratto %s: totale_versato %.2f ≠ Σ ENTRATA %.2f",
            motivo, contract.id, contract.totale_versato or 0, proj["versato"],
        )

    # G9.2-b Stage 2: ancora ledger-STORNO (`quota_stornata == Σ importo[rettifiche_contratto]`, ADR-022
    # Addendum I D-ANCORA-STORNO). Terza ancora dopo versato/rimborso: sui path via terza penna è vera per
    # costruzione → una violazione segnala un write fuori-penna o drift legacy pre-backfill. Log-only
    # (gate duro in G9.4). NB: i test che scrivono `quota_stornata` a mano (test_lifecycle_audit) la
    # accendono — atteso, non sorpresa (SPEC_G9 §B.6).
    if abs((contract.quota_stornata or 0) - proj["stornato"]) > 0.01:
        logger.warning(
            "Ancora ledger-storno violata dopo '%s' sul contratto %s: quota_stornata %.2f ≠ Σ rettifiche %.2f",
            motivo, contract.id, contract.quota_stornata or 0, proj["stornato"],
        )

    # G9.4-a — il GATE: I1/I4 violati + modalità raise → 409 e la transazione muore prima del commit.
    hard = [v for v in violazioni if v.code in ENFORCE_HARD]
    if hard and _enforcement_mode() == "raise":
        codici = ", ".join(sorted({v.code for v in hard}))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Operazione annullata: violerebbe l'integrità finanziaria del contratto "
                f"({codici} dopo '{motivo}'). Nessuna modifica salvata."
            ),
        )


# Alias di compatibilità (G9.0 → G9.4): i call-site e gli spy dei test usano questo nome.
log_invariant_violations = enforce_contract_invariants
