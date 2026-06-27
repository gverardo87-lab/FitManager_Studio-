# api/routers/_audit.py
"""
Utility condivisa per l'audit trail.

log_audit() registra un'azione nella tabella audit_log.
NON fa session.commit() — il chiamante committa atomicamente.
"""

import json
from sqlmodel import Session
from api.models.audit_log import AuditLog


def log_audit(
    session: Session,
    entity_type: str,
    entity_id: int,
    action: str,
    trainer_id: int,
    changes: dict | None = None,
) -> None:
    """
    Registra un'azione nel log di audit.

    Args:
        entity_type: 'client', 'contract', 'rate', 'event', 'movement', 'recurring_expense'
        entity_id: ID del record modificato
        action: 'CREATE', 'UPDATE', 'DELETE', 'RESTORE'
        trainer_id: chi ha eseguito l'azione
        changes: dict con diff campo-per-campo (solo UPDATE)
                 es. {"prezzo_totale": {"old": 100, "new": 150}}
    """
    entry = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        changes=json.dumps(changes, default=str) if changes else None,
        trainer_id=trainer_id,
    )
    session.add(entry)


def log_contract_lifecycle_transition(
    session: Session,
    contract,
    *,
    old_chiuso: bool,
    motivo: str | None = None,
    importo_rimborsato: float | None = None,
    residuo_annullato: float | None = None,
    data_chiusura=None,
) -> None:
    """
    Audita la transizione del flag `chiuso` di un contratto (chiusura o riapertura).

    Colma il buco rilevato in ricognizione: oggi `pay_rate` e `agenda._sync_contract_chiuso`
    accendono/spengono `chiuso` senza loggarlo. La terminazione (G7) è l'evento più importante
    da tracciare legalmente: non può ereditare un audit bucato.

    - **Idempotente**: NON emette nulla se `chiuso` non è cambiato.
    - **Non committa** (come `log_audit`): il chiamante committa atomicamente.
    - `trainer_id` derivato da `contract.trainer_id` → nessun cambio di firma nei caller.
    - Firma estesa (motivo/rimborso/storno/data) **pronta per G6/G7**: finché le colonne dedicate
      (`motivo_chiusura`, `data_chiusura`) non atterrano col blocco terminazione, questi campi
      viaggiano nel JSON `changes`.
    """
    if old_chiuso == contract.chiuso:
        return
    changes: dict = {"chiuso": {"old": old_chiuso, "new": contract.chiuso}}
    if motivo is not None:
        changes["motivo"] = motivo
    if importo_rimborsato is not None:
        changes["importo_rimborsato"] = importo_rimborsato
    if residuo_annullato is not None:
        changes["residuo_annullato"] = residuo_annullato
    if data_chiusura is not None:
        changes["data_chiusura"] = data_chiusura
    log_audit(session, "contract", contract.id, "UPDATE", contract.trainer_id, changes)


def log_contract_open_lifecycle_transition(
    session: Session,
    contract,
    *,
    old_lifecycle: str,
    new_lifecycle: str,
    trigger: str = "data_scadenza_update",
    motivo: str,
) -> None:
    """
    Audita una transizione del lifecycle *aperto* del contratto (ATTIVO/SOSPESO/ESAURITO)
    causata da un update della scadenza.

    Fratello di `log_contract_lifecycle_transition()`: NON riguarda il flag `chiuso` né i flussi
    G6/G7, ma il crossing del confine temporale del SSoT (`is_vigente` <-> `is_scaduto`) dentro
    `update_contract`.

    - Idempotente: no-op se il lifecycle non cambia.
    - Non committa: il chiamante resta responsabile della transazione atomica.
    - `motivo` è audit-tecnico (`scadenza_retrodatata` / `scadenza_estesa`), NON `motivo_chiusura`.
    """
    if old_lifecycle == new_lifecycle:
        return

    changes: dict = {
        "lifecycle": {"old": old_lifecycle, "new": new_lifecycle},
        "trigger": trigger,
        "motivo": motivo,
    }
    log_audit(session, "contract", contract.id, "UPDATE", contract.trainer_id, changes)
