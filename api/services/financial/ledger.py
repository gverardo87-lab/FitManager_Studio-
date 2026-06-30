"""ledger — penna unica di posting del libro mastro (G9.1, ADR-022).

UNICO punto di scrittura della cassa contrattuale: `post_inflow`/`post_outflow` creano il `CashMovement`
**e**, nello stesso atto, applicano il delta sulla colonna denormalizzata del contratto. Così l'àncora I5
(`totale_versato == Σ ENTRATA[id_contratto]`, e il gemello rimborso) diventa vera **per costruzione** invece
che verificata a posteriori dalla `/reconciliation` — chiude la doppia-verità ledger↔colonne alla radice.

**Confine (G9.1):** la penna fa SOLO movimento + delta-colonna. NON ricalcola `stato_pagamento`, NON fa
auto-close, NON riconcilia il piano rate: quella è transition-logic del caller (resta dove sta). La penna è
il punto-unico-di-scrittura, non il command-handler (quello è G9.3). Categoria fuori asse → `ValueError`
(fail-loud: una categoria sbagliata è un bug del caller, non un caso da inghiottire — `api/CLAUDE.md`).
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from sqlmodel import Session, select

from api.models.contract import Contract
from api.models.credito_cliente import CreditoCliente
from api.models.movement import CashMovement
from api.services.cash_categories import (
    CATEGORIA_RIMBORSO_CONTRATTO,
    CONTRACT_CASH_IN,
    CONTRACT_CASH_OUT,
)


def post_inflow(
    session: Session,
    *,
    contract: Contract,
    importo: float,
    categoria: str,
    metodo: Optional[str],
    data_effettiva: date,
    trainer_id: int,
    id_cliente: Optional[int],
    note: Optional[str],
    id_rata: Optional[int] = None,
) -> CashMovement:
    """Registra un'ENTRATA contrattuale: crea il `CashMovement` E incrementa `totale_versato` nello STESSO
    atto → I5 (`totale_versato == Σ ENTRATA[id_contratto]`) vero per costruzione. Ritorna il movimento (non
    ancora flush-ato: l'`id` lo popola il commit/flush del caller). NON ricalcola `stato_pagamento` né fa
    auto-close — quella è del caller."""
    if categoria not in CONTRACT_CASH_IN:
        raise ValueError(
            f"post_inflow: categoria {categoria!r} non è un inflow contrattuale (CONTRACT_CASH_IN={sorted(CONTRACT_CASH_IN)})"
        )
    movement = CashMovement(
        trainer_id=trainer_id,
        data_effettiva=data_effettiva,
        tipo="ENTRATA",
        categoria=categoria,
        importo=importo,
        metodo=metodo,
        id_cliente=id_cliente,
        id_contratto=contract.id,
        id_rata=id_rata,
        note=note,
    )
    session.add(movement)
    contract.totale_versato = (contract.totale_versato or 0) + importo
    session.add(contract)
    return movement


def post_outflow(
    session: Session,
    *,
    contract: Optional[Contract],
    importo: float,
    categoria: str,
    metodo: Optional[str],
    data_effettiva: date,
    trainer_id: int,
    id_cliente: Optional[int],
    note: Optional[str],
) -> CashMovement:
    """Registra un'USCITA contrattuale (rimborso). Se `contract` è dato: crea il `CashMovement` E incrementa
    `totale_rimborsato` → l'àncora del rimborso (I5) regge per costruzione. Con `contract=None` (erogazione
    wallet, cassa a livello CLIENTE, ADR-020): crea SOLO il movimento con `id_contratto=None` e NON tocca
    alcuna colonna — l'erogato è tracciato dal wallet stesso (`importo_erogato`). NON ricalcola nulla."""
    if categoria not in CONTRACT_CASH_OUT:
        raise ValueError(
            f"post_outflow: categoria {categoria!r} non è un outflow contrattuale (CONTRACT_CASH_OUT={sorted(CONTRACT_CASH_OUT)})"
        )
    movement = CashMovement(
        trainer_id=trainer_id,
        data_effettiva=data_effettiva,
        tipo="USCITA",
        categoria=categoria,
        importo=importo,
        metodo=metodo,
        id_cliente=id_cliente,
        id_contratto=contract.id if contract is not None else None,
        id_rata=None,
        note=note,
    )
    session.add(movement)
    if contract is not None:
        contract.totale_rimborsato = (contract.totale_rimborsato or 0) + importo
        session.add(contract)
    return movement


def project_columns_from_ledger(session: Session, contract_id: int) -> dict:
    """Deriva le colonne (versato, rimborsato) di un contratto dal SOLO libro mastro — inverso per-contratto
    della `/reconciliation` (G9.2-a, ADR-022 D-LEDGER-LOAD-BEARING). È la derivazione UNICA che rende le
    colonne denormalizzate PROIEZIONI verificabili del ledger:

        versato    = Σ ENTRATA[id_contratto]
        rimborsato = Σ USCITA RIMBORSO[id_contratto] + Σ erogato wallet ANNULLATO[origine]  (I5 raffinata, D1 forma-d)

    PURA-lettura (solo SELECT). Usata come asserzione (oggi log-only nel sensore; gate duro in G9.4) e come
    fonte unica che `/reconciliation` e l'enforcement chiameranno."""
    versato = round(sum(m.importo for m in session.exec(
        select(CashMovement).where(
            CashMovement.id_contratto == contract_id,
            CashMovement.tipo == "ENTRATA",
            CashMovement.deleted_at == None,  # noqa: E711 (SQLModel richiede == None)
        )
    ).all()), 2)
    rimborsi_diretti = sum(m.importo for m in session.exec(
        select(CashMovement).where(
            CashMovement.id_contratto == contract_id,
            CashMovement.tipo == "USCITA",
            CashMovement.categoria == CATEGORIA_RIMBORSO_CONTRATTO,
            CashMovement.deleted_at == None,  # noqa: E711
        )
    ).all())
    wallet_riassorbito = sum(
        (c.importo_erogato or 0) for c in session.exec(
            select(CreditoCliente).where(
                CreditoCliente.id_contratto_origine == contract_id,
                CreditoCliente.stato == "ANNULLATO",
                CreditoCliente.deleted_at == None,  # noqa: E711
            )
        ).all()
    )
    return {"versato": versato, "rimborsato": round(rimborsi_diretti + wallet_riassorbito, 2)}
