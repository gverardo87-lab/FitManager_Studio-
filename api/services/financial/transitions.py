"""transitions — TransitionExecutor del dominio contrattuale-economico (G9.3, ADR-022).

Command-handler tipati per le transizioni di stato del contratto: qui vivono i CORPI delle transizioni
(terminate, reopen, auto-close sync) che i router delegano. Il router resta bouncer + parse + delega +
serialize; la decisione pura resta nei collaboratori (`compute_settlement`, `contract_state`); la
scrittura di cassa/rettifiche resta nelle penne (`ledger.post_inflow/post_outflow/post_adjustment`).

Pattern dell'executor (SPEC_G9 §G9.3):
    carica stato → decisione pura → postings via penna → audit + lifecycle transition
    → sensore invarianti (PRE-commit, log-only oggi; gate 409+rollback in G9.4) → commit atomico

Nota di layering (D-C7, Appendice C): `log_audit`/`log_contract_lifecycle_transition` vivono in
`api/routers/_audit.py` — importarli qui NON crea cicli (`api/routers/__init__.py` è vuoto). Debito
esplicito: lo spostamento di `_audit.py` in services/ è un rename meccanico rinviato.

Rilocazione fedele (G9.3a/b): i corpi sono quasi-verbatim dagli endpoint di `contracts.py` — HTTP
identico, `HTTPException` incluse (D-C3: la conversione a eccezioni di dominio è materia di G9.4).
"""

from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, func, select

from api.models.client import Client
from api.models.contract import Contract
from api.models.credito_cliente import CreditoCliente
from api.models.credito_terminazione import CreditoTerminazione
from api.models.event import Event
from api.models.rate import Rate
from api.models.rettifica_contratto import CAUSALE_STORNO_TERMINAZIONE
from api.models.trainer import Trainer
from api.routers._audit import log_audit, log_contract_lifecycle_transition
from api.schemas.financial import ContractTerminate
from api.services import contract_state as cstate
from api.services.cash_categories import (
    CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO,
    CATEGORIA_RIMBORSO_CONTRATTO,
)
from api.services.contract_settlement import MotivoChiusura, SettlementEsito, compute_settlement
from api.services.financial.invariant_gate import log_invariant_violations
from api.services.financial.ledger import post_adjustment, post_inflow, post_outflow


# ════════════════════════════════════════════════════════════
# Helpers settlement (condivisi da execute_terminate e settlement_preview)
# ════════════════════════════════════════════════════════════

def count_sedute_erogate(session: Session, contract_id: int) -> int:
    """Sedute PT **erogate** (servizio reso) = Event PT Completati, non eliminati. Base del conguaglio
    pro-sedute (IMPL_PLAN §4.2). NB: ≠ `crediti_usati` dell'auto-close (che conta i NON-Cancellati,
    incl. i Programmati): il conguaglio valuta ciò che è stato reso, non ciò che è solo prenotato."""
    return session.exec(
        select(func.count(Event.id)).where(
            Event.id_contratto == contract_id,
            Event.categoria == "PT",
            Event.stato == "Completato",
            Event.deleted_at == None,  # noqa: E711 (SQLModel richiede == None)
        )
    ).one()


def count_sedute_prenotate(session: Session, contract_id: int) -> int:
    """Sedute PT **prenotate ma non svolte** = Event PT Programmati, non eliminati. Proiezione di Event
    (gemello di `count_sedute_erogate`, stato diverso), query SEPARATA: NON tocca il path del conguaglio
    (codice verde). **SOLO display** nella preview (D2, G7.5c): NON entra in `compute_settlement` — il
    conguaglio resta su base sedute Completate. Serve all'avviso UI 'le prenotate non riducono il rimborso'."""
    return session.exec(
        select(func.count(Event.id)).where(
            Event.id_contratto == contract_id,
            Event.categoria == "PT",
            Event.stato == "Programmato",
            Event.deleted_at == None,  # noqa: E711
        )
    ).one()


def motivo_from_esito(esito: SettlementEsito) -> str:
    """Mappa esito→motivo_chiusura (AC-7.3-9 + ADR-018). terminate NON assegna MAI COMPLETAMENTO
    (riservato all'auto-close; lo riaprirebbe la reopen-allowlist G7.2). TERMINAZIONE_DECADENZA è
    legacy: non più emesso qui (il ramo trainer è ora TERMINAZIONE_SALDO_TRAINER)."""
    if esito == SettlementEsito.CREDITO_CLIENTE:
        return MotivoChiusura.TERMINAZIONE_RIMBORSO.value
    if esito == SettlementEsito.CREDITO_TRAINER:
        return MotivoChiusura.TERMINAZIONE_SALDO_TRAINER.value
    return MotivoChiusura.CONSUNZIONE.value  # PARI (conguaglio ~ 0)


def settlement_for(session: Session, contract: Contract):
    """Conguaglio di terminazione (puro, zero scritture). Fonte-unica-importo (§2): il
    `residuo_corrente = contract_state.residuo()` PRE-storno passa in UNA variabile a compute_settlement."""
    residuo_corrente = cstate.residuo(contract)
    sedute_erogate = count_sedute_erogate(session, contract.id)
    return compute_settlement(
        sedute_erogate=sedute_erogate,
        prezzo_totale=contract.prezzo_totale,
        crediti_totali=contract.crediti_totali,
        totale_versato=contract.totale_versato,
        totale_rimborsato=contract.totale_rimborsato,  # G8.1: net-aware (ri-terminazione post-reopen)
        residuo_corrente=residuo_corrente,
    )


# ════════════════════════════════════════════════════════════
# Executor: TERMINATE (G9.3a — rilocazione fedele da contracts.py)
# ════════════════════════════════════════════════════════════

def execute_terminate(
    session: Session,
    *,
    contract: Contract,
    data: ContractTerminate,
    trainer: Trainer,
) -> Contract:
    """
    Terminazione anticipata di un contratto vivo (G7.3 + ADR-018, Strada B). Atto UMANO esplicito,
    terza via a CHIUSO. Transazione UNICA atomica. Il caller ha già fatto il bouncer (D-C2).

    Flusso (un solo commit):
    B) guard chiuso 400
    C) Conguaglio puro balance-based (fonte-unica-importo §2: `residuo()` PRE-storno in UNA variabile)
    D) Gamba d'azione (un solo CashMovement), derivata dall'esito:
       • CREDITO_CLIENTE → USCITA RIMBORSO_CONTRATTO (`metodo_rimborso` → 422) + `totale_rimborsato +=`
       • CREDITO_TRAINER → scelta esplicita (422 se assente): INCASSA_ORA (ENTRATA INCASSO_CONGUAGLIO,
         importo editabile [0, credito_trainer], `metodo_pagamento` → 422, `totale_versato +=`) oppure
         RINUNCIA_ESPRESSA (no cassa, nota obbligatoria → 422). A_CREDITO è G7.10 (422 a schema).
       • PARI → nessun movimento
    E) Gamba STORNO (SEMPRE): `quota_stornata += residuo_pre − incasso_ora + rimborso_out` → `residuo()` → 0
       (net-aware G8.1/ADR-019: il rimborso che ESCE riduce il netto → entra nello storno, simmetrico
       all'incasso che lo cresce; pre-G8.1 il rimborso non toccava il residuo e bastava `− incasso_ora`)
    F) Soft-delete SOLO rate NON-saldate (B-3): mai SALDATA né i loro CashMovement
    G) Stato terminale DIRETTO (B-2-attiva): chiuso/motivo/data — **MAI** via `sync_contract_chiuso`
       (su un SOSPESO terminato il sync vedrebbe should_be_chiuso=False e riaprirebbe nello stesso commit)
    H) Audit (snapshot `sedute_erogate`, no-silent-loss) + transizione `chiuso` + sensore + commit
    """
    # B) Guard: già chiuso → non terminabile
    if contract.chiuso:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Il contratto è già chiuso")

    # C) Conguaglio puro balance-based (fonte-unica-importo: residuo PRE-storno). ADR-018.
    settlement = settlement_for(session, contract)
    motivo = motivo_from_esito(settlement.esito)
    data_chiusura = data.data_chiusura or date.today()
    old_quota = contract.quota_stornata or 0
    old_rimborsato = contract.totale_rimborsato or 0
    old_versato = contract.totale_versato or 0
    old_chiuso = contract.chiuso

    client = session.get(Client, contract.id_cliente)
    client_label = f"{client.nome} {client.cognome}" if client else f"Cliente #{contract.id_cliente}"

    # D) Gamba d'azione, derivata dall'esito (ADR-018): un solo CashMovement per terminazione.
    movement = None
    incasso_ora = 0.0                 # X incassato dal trainer (ramo CREDITO_TRAINER + INCASSA_ORA)
    rimborso_out = 0.0                # X rimborsato al cliente (ramo CREDITO_CLIENTE) — entra nello storno (G8.1)
    saldo_trainer_rinunciato = 0.0    # parte del credito_trainer abbuonata (credito_trainer − X)
    credito_differito = None          # receivable creato dal ramo A_CREDITO (G7.10)
    wallet_cliente = None             # crediti_cliente creato dal ramo CREDITO_CLIENTE (G8.1, non-rimborsato)

    if settlement.esito == SettlementEsito.CREDITO_CLIENTE:
        # G8.1/ADR-020: rimborso EDITABILE [0, credito_cliente] (default = pieno → retro-compatibile). Il
        # non-rimborsato NON si perde: diventa un credito a wallet del cliente (RIMBORSO_DIFFERITO), FUORI
        # dal residuo(). Niente "rinuncia" lato cliente: non si abbuona denaro dovuto al cliente (asimmetria).
        rimborso_out = (
            settlement.credito_cliente if data.importo_rimborso is None
            else round(data.importo_rimborso, 2)
        )
        if rimborso_out > settlement.credito_cliente + 0.009:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"L'importo da rimborsare (€{rimborso_out:.2f}) non può superare il credito del "
                    f"cliente (€{settlement.credito_cliente:.2f})."
                ),
            )
        rimborso_out = max(rimborso_out, 0.0)
        if rimborso_out > 0.009:
            if not data.metodo_rimborso:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Metodo di rimborso obbligatorio per una terminazione con rimborso",
                )
            movement = post_outflow(  # penna unica (G9.1): USCITA + totale_rimborsato += in UN atto
                session, contract=contract, importo=rimborso_out, categoria=CATEGORIA_RIMBORSO_CONTRATTO,
                metodo=data.metodo_rimborso, data_effettiva=data_chiusura, trainer_id=trainer.id,
                id_cliente=contract.id_cliente,
                note=data.note or f"Rimborso terminazione - {client_label}",
            )  # totale_rimborsato += rimborso_out (== old_rimborsato + rimborso_out; fonte-unica-importo)
        # Il non-rimborsato → wallet del cliente (ADR-020), fuori dal residuo (storno = residuo_pre + rimborso_out).
        wallet_credit = round(settlement.credito_cliente - rimborso_out, 2)
        if wallet_credit > 0.009:
            wallet_cliente = CreditoCliente(
                trainer_id=trainer.id,
                id_cliente=contract.id_cliente,
                importo=wallet_credit,
                importo_erogato=0.0,
                stato="APERTO",
                causale="RIMBORSO_DIFFERITO",
                id_contratto_origine=contract.id,
                data_creazione=data_chiusura,
            )
            session.add(wallet_cliente)

    elif settlement.esito == SettlementEsito.CREDITO_TRAINER:
        # Il cliente deve ancora per servizio già reso → scelta esplicita obbligatoria (ADR-018).
        if data.azione_credito_trainer is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Il cliente ha ricevuto più servizio di quanto versato (saldo a tuo favore "
                    f"€{settlement.credito_trainer:.2f}): scegli se incassarlo ora o rinunciarvi."
                ),
            )
        if data.azione_credito_trainer == "INCASSA_ORA":
            if not data.metodo_pagamento:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Metodo di pagamento obbligatorio per incassare il saldo a tuo favore",
                )
            # Importo proposto = credito_trainer; EDITABILE solo verso il basso (cap [0, credito_trainer]).
            incasso_ora = (
                settlement.credito_trainer if data.importo_incassato is None
                else round(data.importo_incassato, 2)
            )
            if incasso_ora > settlement.credito_trainer + 0.009:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"L'importo da incassare (€{incasso_ora:.2f}) non può superare il saldo a tuo "
                        f"favore (€{settlement.credito_trainer:.2f}): non si fattura servizio non erogato."
                    ),
                )
            incasso_ora = max(incasso_ora, 0.0)
            saldo_trainer_rinunciato = round(settlement.credito_trainer - incasso_ora, 2)
            if incasso_ora > 0.009:
                movement = post_inflow(  # penna unica (G9.1): ENTRATA + totale_versato += in UN atto
                    session, contract=contract, importo=incasso_ora,
                    categoria=CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO, metodo=data.metodo_pagamento,
                    data_effettiva=data_chiusura, trainer_id=trainer.id, id_cliente=contract.id_cliente,
                    id_rata=None, note=data.note or f"Incasso conguaglio terminazione - {client_label}",
                )  # totale_versato += incasso_ora (== old_versato + incasso_ora; Strada B)
        elif data.azione_credito_trainer == "RINUNCIA_ESPRESSA":
            if not (data.note and data.note.strip()):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Nota obbligatoria per rinunciare al saldo a tuo favore (presidio auditabile)",
                )
            saldo_trainer_rinunciato = settlement.credito_trainer
        elif data.azione_credito_trainer == "A_CREDITO":
            # G7.10: "chiudo oggi, il cliente paga dopo". Il credito_trainer NON resta nel contratto
            # (romperebbe residuo()==0): viene STORNATO (gamba E, incasso_ora=0 → quota_stornata piena) e
            # RI-TRACCIATO come receivable FUORI da residuo(). Nessuna cassa ora; mai una Rate su chiuso.
            credito_differito = CreditoTerminazione(
                trainer_id=trainer.id,
                id_contratto=contract.id,
                id_cliente=contract.id_cliente,
                importo=settlement.credito_trainer,
                importo_incassato=0.0,
                stato="APERTO",
                data_creazione=data_chiusura,
            )
            session.add(credito_differito)

    # E) Gamba STORNO (sempre): porta residuo() a 0 sotto il net-aware (G8.1/ADR-019). quota = P − netto =
    #    residuo_pre − incasso_ora + rimborso_out. Il rimborso che ESCE (USCITA) riduce il netto incassato →
    #    va aggiunto allo storno, simmetrico all'incasso che lo cresce. (Pre-G8.1 il rimborso non entrava nel
    #    residuo → bastava residuo_pre − incasso_ora; net-aware lo richiede esplicito per tenere residuo()==0.)
    #    G9.2b: via terza penna — riga +Δ nel ledger rettifiche + delta-colonna in UN atto (quota == Σ).
    post_adjustment(
        session, contract=contract,
        importo_firmato=round(settlement.residuo_pre - incasso_ora + rimborso_out, 2),
        causale=CAUSALE_STORNO_TERMINAZIONE, data_effettiva=data_chiusura, trainer_id=trainer.id,
    )

    # F) Soft-delete SOLO le rate NON-saldate (B-3). Le SALDATE e i loro CashMovement ENTRATA
    #    SOPRAVVIVONO: cancellarle romperebbe l'àncora `totale_versato == Σ ENTRATA` (Σ ENTRATA
    #    scenderebbe, il lordo no). NON riusare il cascade di delete_contract (tocca anche le SALDATE).
    now = datetime.now(timezone.utc)
    rate_non_saldate = session.exec(
        select(Rate).where(
            Rate.id_contratto == contract.id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.deleted_at == None,  # noqa: E711
        )
    ).all()
    for r in rate_non_saldate:
        r.deleted_at = now
        r.chiusa_da_terminazione = True  # M1: marca per il reopen inverso esatto (solo queste si ripristinano)
        session.add(r)
        log_audit(session, "rate", r.id, "DELETE", trainer.id)

    # G) Stato terminale DIRETTO (B-2-attiva). MAI `sync_contract_chiuso`: su un SOSPESO terminato
    #    (saldato, crediti residui) ricalcolerebbe should_be_chiuso=False → reset `chiuso=False`.
    contract.chiuso = True
    contract.motivo_chiusura = motivo
    contract.data_chiusura = data_chiusura
    session.add(contract)

    # H) Audit atomico. flush per popolare l'id del movimento. Snapshot `sedute_erogate` (no-silent-loss:
    #    crediti_usati è event-derived e può driftare; è l'unico record del servizio forfettato).
    #    Payload ADR-018 (§6.2): ricostruibile se il trainer ha incassato, abbuonato o rinunciato.
    is_cliente = settlement.esito == SettlementEsito.CREDITO_CLIENTE
    if movement is not None or credito_differito is not None or wallet_cliente is not None:
        session.flush()  # popola gli id (movimento, receivable e/o wallet) per l'audit
    if movement is not None:
        log_audit(session, "movement", movement.id, "CREATE", trainer.id)
    if credito_differito is not None:
        log_audit(session, "credito_terminazione", credito_differito.id, "CREATE", trainer.id)
    if wallet_cliente is not None:
        log_audit(session, "credito_cliente", wallet_cliente.id, "CREATE", trainer.id)
    log_audit(session, "contract", contract.id, "UPDATE", trainer.id, {
        "motivo_chiusura": {"old": None, "new": motivo},
        "data_chiusura": {"old": None, "new": data_chiusura},
        "quota_stornata": {"old": old_quota, "new": contract.quota_stornata},
        "totale_rimborsato": {"old": old_rimborsato, "new": contract.totale_rimborsato},
        "totale_versato": {"old": old_versato, "new": contract.totale_versato or 0},
        "sedute_erogate_snapshot": settlement.sedute_erogate,
        "valore_servizio_reso": settlement.valore_servizio_reso,
        "esito_balance": settlement.esito.value,
        "credito_cliente": settlement.credito_cliente,
        "credito_trainer": settlement.credito_trainer,
        "quota_non_erogata": settlement.quota_non_erogata,
        "azione_credito_trainer": data.azione_credito_trainer,
        "importo_incassato": round(incasso_ora, 2),
        "saldo_trainer_rinunciato": round(saldo_trainer_rinunciato, 2),
        "importo_differito": round(settlement.credito_trainer, 2) if credito_differito is not None else 0.0,
        "importo_rimborsato": round(rimborso_out, 2),
        "wallet_cliente_credito": round(settlement.credito_cliente - rimborso_out, 2) if is_cliente else 0.0,
        "movimento_cassa_id": movement.id if movement is not None else None,
        "credito_terminazione_id": credito_differito.id if credito_differito is not None else None,
        "credito_cliente_id": wallet_cliente.id if wallet_cliente is not None else None,
    })
    # Transizione `chiuso`: terminate la logga DA SÉ (non chiama il sync, che altrimenti la loggherebbe).
    # Slice A (audit AUDIT_INTEGRITA_RESIDUI_2026-06-29, P1): la companion porta la CASSA EFFETTIVAMENTE
    # USCITA (`rimborso_out`), non il credito teorico (`settlement.credito_cliente`). Con rimborso parziale
    # (resto a wallet) i due divergevano → due "importo_rimborsato" diversi per la stessa chiusura nell'audit
    # grezzo. Ora == alla entry ricca (riga sopra). Byte-identico col rimborso pieno (rimborso_out==credito).
    log_contract_lifecycle_transition(
        session,
        contract,
        old_chiuso=old_chiuso,
        motivo="terminazione",
        importo_rimborsato=round(rimborso_out, 2) if is_cliente else None,
        residuo_annullato=round(settlement.residuo_pre - incasso_ora, 2),
        data_chiusura=data_chiusura,
    )
    # Post-condizione dell'executor (AC-G93-4): sensore invarianti PRE-commit (D-C4 — il gate G9.4 deve
    # poter fare rollback). Log-only oggi. Atteso pulito (chiuso ⟹ residuo 0; ancore versato/storno).
    log_invariant_violations(session, contract, motivo="terminazione")
    session.commit()
    session.refresh(contract)
    return contract
