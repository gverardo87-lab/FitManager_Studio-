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

**'Predisposta per 409'** (osservazione → enforcement): oggi LOGGA soltanto, byte-identica sull'output.
L'hardening per il disaccoppiamento (osservazione post-commit) e l'escalation a 409+rollback sono G9.3/G9.4.
"""

import logging

from sqlmodel import Session, select

from api.models.contract import Contract
from api.models.credito_cliente import CreditoCliente
from api.models.movement import CashMovement
from api.models.rate import Rate
from api.services import contract_state as cstate
from api.services.cash_categories import CATEGORIA_RIMBORSO_CONTRATTO

logger = logging.getLogger(__name__)


def log_invariant_violations(session: Session, contract: Contract, *, motivo: str) -> None:
    """Osserva (log-only) gli invarianti I1/I4/I5/I6 sul contratto in coda a una transizione `motivo`.

    Fornisce a `assert_contract_invariants` la fotografia netta (`crediti_cliente` del contratto, I5),
    l'ancora ledger forte di I5 (Σ USCITA RIMBORSO_CONTRATTO diretto) e le rate attive (I6, INV-RATE).
    Nessuna scrittura: solo SELECT + log. Va chiamata immediatamente prima di `session.commit()`.
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
    for v in cstate.assert_contract_invariants(
        contract, crediti, rimborso_cassa_diretto=rimborso_diretto, rate_attive=rate_attive
    ):
        logger.warning(
            "Invariante %s violato dopo '%s' sul contratto %s: %s",
            v.code, motivo, contract.id, v.message,
        )
