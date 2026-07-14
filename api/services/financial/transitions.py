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
from api.models.rettifica_contratto import (
    CAUSALE_REVERSAL_REOPEN,
    CAUSALE_STORNO_TERMINAZIONE,
)
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
# FSM di chiusura (G9.3c) — tabella stati×transizioni di (chiuso, motivo_chiusura)
# ════════════════════════════════════════════════════════════
#
# | Da \ Via                        | auto-close (pag./crediti) | terminate                 | auto-reopen (revoca/crediti) | reopen esplicito |
# |---------------------------------|---------------------------|---------------------------|------------------------------|------------------|
# | APERTO (False, None)            | → CHIUSO COMPLETAMENTO    | → CHIUSO TERMINAZIONE_*/  | —                            | — (400)          |
# |                                 |                           |   CONSUNZIONE             |                              |                  |
# | CHIUSO COMPLETAMENTO            | no-op                     | — (400)                   | → APERTO (False, None)       | → APERTO         |
# | CHIUSO TERMINAZIONE_*/CONSUNZ.  | no-op                     | — (400)                   | VIETATO (allowlist G7.2)     | → APERTO         |
# | CHIUSO NULL (legacy/manuale)    | no-op                     | — (400)                   | VIETATO (allowlist)          | → APERTO         |
#
# Ogni transizione vive in QUESTO modulo: terminate/reopen negli executor sopra, auto-close/auto-reopen
# in `sync_contract_chiuso` sotto. L'allowlist è POSITIVA (== COMPLETAMENTO), MAI denylist: il motivo
# NULL (chiusura manuale/legacy, deliberata) è il contro-esempio che una denylist mancherebbe →
# eviterebbe lo stato-zombie `chiuso=False ∧ quota_stornata>0` (G7.2, FDM §9.5.6).

AUTO_REOPEN_ALLOWLIST = frozenset({"COMPLETAMENTO"})

# ════════════════════════════════════════════════════════════
# D-PERIMETRO-TRANSIZIONI (G9.7.4, ADR-024) — perimetro DICHIARATO delle entità satellite
# ════════════════════════════════════════════════════════════
#
# Ogni tabella che referenzia `contratti` (FK dichiarata o colonna cross-ref) è una entità satellite
# delle transizioni: terminate/reopen devono DICHIARARE cosa ne fanno — anche quando la risposta è
# "niente" (l'omissione silenziosa è la classe d'errore dei «5 produttori mancati»). Il gemello di
# esaustività (`test_semantic_guards.py::test_g974_perimetro_transizioni_esaustivo`) scopre le
# satellite dal metadata ORM e fallisce se qui manca una voce (o se una voce è fantasma): una tabella
# nuova con FK verso il contratto NON può nascere senza decidere il suo destino nelle transizioni
# (es. CP-4 birth-review P0: la futura `prestazioni_singole` dovrà entrare qui, non in silenzio).
PERIMETRO_TRANSIZIONE: dict[str, str] = {
    "rate_programmate": (
        "terminate F: soft-delete SOLO non-saldate (marker M1, mai le SALDATE — B-3); "
        "reopen R5/R5-bis: ripristino inverso-esatto + reconcile_rate_plan (ADR-021)"
    ),
    "movimenti_cassa": (
        "terminate D: gamba d'azione via penne (post_inflow/post_outflow); "
        "reopen R1: IMMUTABILE — la cassa mossa non si tocca mai (ADR-019, fatti datati)"
    ),
    "rettifiche_contratto": (
        "terminate E: storno via terza penna (post_adjustment); "
        "reopen R2: reversal −quota — ledger append-only, quota == Σ righe"
    ),
    "crediti_terminazione": (
        "terminate D/A_CREDITO: nasce il receivable (G7.10, fuori da residuo()); "
        "reopen R3: → ANNULLATO (gli incassi parziali restano, R1)"
    ),
    "crediti_cliente": (
        "terminate D/CREDITO_CLIENTE: nasce il wallet del non-rimborsato (ADR-020); "
        "reopen R4+R2-bis: → ANNULLATO + fold dell'erogato in totale_rimborsato (D1 forma-d)"
    ),
    "agenda": (
        "SOLO lettura in entrambe: count_sedute_* per il conguaglio (terminate C), occupazione per "
        "sync_contract_chiuso — mai mutati; i PT orfani del periodo li NOMINA reopen (G9.7.2, D-PROPONE)"
    ),
    "contratti": (
        "self-ref (rinnovo_di): la catena rinnovi non è MAI mutata dalle transizioni; "
        "il rinnovo vivo lo segnala reopen-preview (R8), mai un re-parenting implicito"
    ),
}


def puo_auto_riaprire(contract: Contract) -> bool:
    """Reopen-allowlist G7.2 (FDM §9.5.6): l'auto-riapertura (credit/payment-driven) scatta SOLO per le
    chiusure da COMPLETAMENTO. TERMINAZIONE_*/CONSUNZIONE/NULL si riaprono SOLO via `execute_reopen`."""
    return contract.motivo_chiusura in AUTO_REOPEN_ALLOWLIST


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


def count_sedute_penali(session: Session, contract_id: int) -> int:
    """Sedute PT **perse per colpa del cliente** (G7.8-bis, ADR-017 Add. I): Cancellato_Tardivo +
    No_Show. CONTABILIZZANO nel conguaglio di recesso (penale dovuta al trainer, D-RECESSO-PENALE)
    ma NON sono servizio reso in senso atletico — l'audit le registra SEPARATE dalle erogate vere
    (D-CONTEGGI-SEPARATI). ⚠️ PROVISIONAL come pro_sedute: esigibile solo se pattuita nel contratto
    col cliente (punto tributarista, D-PENALE-PROVISIONAL)."""
    return session.exec(
        select(func.count(Event.id)).where(
            Event.id_contratto == contract_id,
            Event.categoria == "PT",
            Event.stato.in_(cstate.STATI_PENALE),
            Event.deleted_at == None,  # noqa: E711
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
    # G7.8-bis (D-RECESSO-PENALE): la base del conguaglio è il CONTABILIZZABILE = erogate vere
    # (Completato) + penali (Cancellato_Tardivo/No_Show, quota dovuta al trainer). Il modulo puro
    # resta cieco all'occupazione (ADR-016): riceve UN intero, qui si decide cosa ci entra.
    sedute_contabilizzabili = count_sedute_erogate(session, contract.id) + count_sedute_penali(session, contract.id)
    return compute_settlement(
        sedute_erogate=sedute_contabilizzabili,
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
                stato=cstate.STATO_CREDITO_APERTO,
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
                stato=cstate.STATO_CREDITO_APERTO,
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
    # D-CONTEGGI-SEPARATI (G7.8-bis): l'audit registra erogate VERE e penali come numeri distinti
    # (difesa documentale del trainer); settlement.sedute_erogate = la loro somma (contabilizzato).
    sedute_erogate_vere = count_sedute_erogate(session, contract.id)
    sedute_penali = count_sedute_penali(session, contract.id)
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
        "sedute_erogate_snapshot": sedute_erogate_vere,
        "sedute_penali_snapshot": sedute_penali,
        "sedute_contabilizzate_snapshot": settlement.sedute_erogate,  # base del conguaglio (vere+penali)
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


# ════════════════════════════════════════════════════════════
# Riconciliazione piano rate (condivisa da execute_reopen e incassa_residuo, ADR-021)
# ════════════════════════════════════════════════════════════

def reconcile_rate_plan(session: Session, contract: Contract, trainer_id: int) -> dict:
    """G8.1.1/F2 (ADR-019 Addendum, D-RECONCILIA-RATE): dopo `reopen`, riallinea il piano rate non-saldate
    al `residuo()` net-aware ricalcolato. L'inverso-esatto (M1) ripristina le rate al loro importo
    PRE-terminate: se la cassa è rimasta (rimborso/conguaglio), il residuo ricalcolato ≠ pre-terminate →
    le rate non combaciano.

    - **Eccedenza** (Σ residui-rata > residuo): taglio CRONOLOGICO — si copre il residuo riempiendo dalle
      rate più vecchie; la rata a cavallo è ridotta a coprire l'esatto residuo rimanente; le successive
      sono azzerate (soft-delete se `importo_saldato==0`, altrimenti `importo_previsto=importo_saldato` →
      SALDATA: **mai sotto il saldato**, la cassa non si orfaneggia).
    - **Sotto-copertura** (Σ < residuo): nessuna mutazione — il resto resta "da pianificare".
    - **Pari** (Σ == residuo, es. reopen senza-cassa): no-op (round-trip esatto preservato).

    Non tocca cassa né `residuo()` (modifica solo `importo_previsto`/`stato`/`deleted_at` delle rate; il
    `saldato` resta, quindi anche `totale_versato`/`netto`). Ritorna un riassunto per l'audit.
    """
    residuo = round(cstate.residuo(contract), 2)
    rate = list(session.exec(
        select(Rate).where(
            Rate.id_contratto == contract.id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.deleted_at == None,  # noqa: E711
        ).order_by(Rate.data_scadenza, Rate.id)
    ).all())
    somma_residui = round(sum(max((r.importo_previsto or 0) - (r.importo_saldato or 0), 0.0) for r in rate), 2)
    if abs(somma_residui - residuo) <= 0.01:
        # Pari (es. reopen senza-cassa): round-trip esatto preservato.
        return {"residuo": residuo, "somma_rate_pre": somma_residui, "tagliate": 0, "rimosse": 0, "cresciute": 0}

    if somma_residui < residuo - 0.01:
        # SOTTO-COPERTURA. Auto-copertura (scelta founder) LIMITATA al RIMBORSO che resta (re-incassabile):
        # è il SOLO € che il reopen ha aggiunto al residuo e che il piano ripristinato non copre. L'eventuale
        # ammanco oltre il rimborso è "da pianificare" ORIGINALE del trainer → NON lo fabbrichiamo (mai una
        # rata-fantasma su residuo mai pianificato: romperebbe la CONSUNZIONE/storno-puro senza pendenti, dove
        # il residuo torna "da pianificare" com'era). Cresce SOLO una rata pendente ESISTENTE (mirror del
        # taglio cronologico); senza pendenti o senza rimborso → no-op (Fix A lascia aggiungere a mano).
        # Non tocca cassa (solo importo_previsto).
        ammanco = min(round(residuo - somma_residui, 2), round(contract.totale_rimborsato or 0, 2))
        if ammanco > 0.01 and rate:
            last = rate[-1]
            last.importo_previsto = round((last.importo_previsto or 0) + ammanco, 2)
            session.add(last)
            log_audit(session, "rate", last.id, "UPDATE", trainer_id,
                      {"importo_previsto": {"new": last.importo_previsto}, "riallineo": "reopen_cover"})
            return {"residuo": residuo, "somma_rate_pre": somma_residui, "tagliate": 0, "rimosse": 0, "cresciute": 1}
        return {"residuo": residuo, "somma_rate_pre": somma_residui, "tagliate": 0, "rimosse": 0, "cresciute": 0}

    # ECCEDENZA (Σ residui-rata > residuo): taglio cronologico.
    now = datetime.now(timezone.utc)
    coperto = 0.0
    tagliate = 0
    rimosse = 0
    for r in rate:
        saldato = round(r.importo_saldato or 0, 2)
        residuo_rata = round(max((r.importo_previsto or 0) - saldato, 0.0), 2)
        spazio = round(residuo - coperto, 2)  # residuo ancora da coprire col piano
        if spazio <= 0.01:
            # Residuo già coperto → questa rata (e le successive) sono eccedenti.
            if saldato <= 0.01:
                r.deleted_at = now
                session.add(r)
                log_audit(session, "rate", r.id, "DELETE", trainer_id)
                rimosse += 1
            else:
                r.importo_previsto = saldato          # mai sotto il saldato
                r.stato = "SALDATA"
                session.add(r)
                log_audit(session, "rate", r.id, "UPDATE", trainer_id,
                          {"importo_previsto": {"new": saldato}, "riallineo": "reopen"})
                tagliate += 1
        elif residuo_rata > spazio + 0.01:
            # Rata a cavallo: riduci il previsto a coprire l'esatto residuo rimanente.
            nuovo_previsto = round(saldato + spazio, 2)
            r.importo_previsto = nuovo_previsto
            r.stato = "PARZIALE" if saldato > 0.01 else "PENDENTE"
            session.add(r)
            log_audit(session, "rate", r.id, "UPDATE", trainer_id,
                      {"importo_previsto": {"new": nuovo_previsto}, "riallineo": "reopen"})
            tagliate += 1
            coperto = residuo
        else:
            coperto = round(coperto + residuo_rata, 2)
    return {"residuo": residuo, "somma_rate_pre": somma_residui, "tagliate": tagliate, "rimosse": rimosse, "cresciute": 0}


# ════════════════════════════════════════════════════════════
# Executor: REOPEN (G9.3b — rilocazione fedele da contracts.py)
# ════════════════════════════════════════════════════════════

def execute_reopen(session: Session, *, contract: Contract, trainer: Trainer) -> Contract:
    """
    Riapre un contratto chiuso (G7.4 → G8.1/ADR-019: **ricalcola-e-instrada, NON-distruttivo**).
    Il caller ha già fatto il bouncer (D-C2).

    State-driven: porta il contratto allo stato CORRETTO rispetto alla cassa reale, qualunque sia il
    `motivo_chiusura`. È il path esplicito che la reopen-allowlist G7.2 demanda (vs l'auto-riapertura
    credit/payment-driven, bloccata per le chiusure non-COMPLETAMENTO). Copre i muti del runbook G7.6.

    **PRINCIPIO ADR-019 — la cassa mossa non si tocca mai.** Reopen LASCIA FERME le scritture di cassa
    (fatti datati, fiscalmente intoccabili) e RICALCOLA: la cassa di terminazione che resta diventa
    pagamento/rimborso sul contratto riaperto, e `residuo()` net-aware (G8.1) la riflette.

    Operazione atomica (UN solo commit):
    B) guard `chiuso==True` else 400
    R1) Cassa IMMUTABILE: i `CashMovement` di terminazione NON si toccano; `totale_versato` invariato
        (`totale_rimborsato` cresce SOLO per il fold R2-bis — mai per una cancellazione di cassa).
    R2) Storno inverso: riga −quota nel ledger rettifiche (terza penna, G9.2b) → colonna a 0.
    R2-bis) FOLD fotografia netta (D1 forma-d): l'erogato dei wallet annullati (R4) RIENTRA in
        `totale_rimborsato` → il residuo() net-aware lo include PER COSTRUZIONE (chiude Bug-1).
    R3) Receivable trainer (G7.10): `crediti_terminazione` del contratto → `ANNULLATO` (non-cash).
    R4) Wallet cliente (ADR-020): i `crediti_cliente` di questa terminazione → `ANNULLATO`.
    R5) Ripristino rate: SOLO le marcate `chiusa_da_terminazione` (M1). Le SALDATE intatte (B-3).
    R5-bis) Riallineo piano rate al residuo net-aware (`reconcile_rate_plan`, G8.1.1/F2 + ADR-021).
    R6) `chiuso=False` + `motivo_chiusura=None` + `data_chiusura=None`.
    R7) Residuo: ricalcolato dal SSoT net-aware (`P − netto − 0`).
    G) Audit + transizione `chiuso` (riapertura_esplicita) + sensore (post-condizione) + commit.
    """
    # B) Guard: solo un contratto chiuso si riapre
    if not contract.chiuso:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Il contratto non è chiuso")

    old_chiuso = contract.chiuso
    old_motivo = contract.motivo_chiusura
    old_rimborsato = contract.totale_rimborsato or 0
    old_versato = contract.totale_versato or 0
    old_quota = contract.quota_stornata or 0

    # R1) Cassa IMMUTABILE (ADR-019 D-CASSA-IMMUTABILE): NON si soft-cancellano i CashMovement di
    #   terminazione (USCITA RIMBORSO_CONTRATTO, ENTRATA INCASSO_CONGUAGLIO_CONTRATTO) e NON si
    #   decrementano `totale_versato`/`totale_rimborsato`. Restano fatti datati, fiscalmente intoccabili:
    #   il rimborso uscito e il conguaglio incassato diventano rimborso/pagamento sul contratto riaperto,
    #   e il residuo() net-aware (G8.1) li riflette da sé (R7). Le ancore Σ ENTRATA/USCITA reggono.
    #   (Pre-G8.1 qui c'erano le gambe C/C-bis che CANCELLAVANO la cassa — rimosse, ADR-019.)

    # R3) Receivable trainer (G7.10): il differito non-cash si chiude → ANNULLATO. Gli incassi parziali
    #   già registrati (ENTRATA INCASSO_CONGUAGLIO) RESTANO (R1) e contano come pagamento sul contratto.
    crediti_annullati = 0
    open_credits = session.exec(
        select(CreditoTerminazione).where(
            CreditoTerminazione.id_contratto == contract.id,
            CreditoTerminazione.stato != cstate.STATO_CREDITO_ANNULLATO,
            CreditoTerminazione.deleted_at == None,  # noqa: E711
        )
    ).all()
    for cr in open_credits:
        cr.stato = cstate.STATO_CREDITO_ANNULLATO
        cr.data_chiusura = date.today()
        session.add(cr)
        log_audit(session, "credito_terminazione", cr.id, "UPDATE", trainer.id, {
            "stato": {"old": "APERTO/SALDATO", "new": "ANNULLATO"},
        })
        crediti_annullati += 1

    # R4) Wallet cliente (ADR-020 / D1 forma-d, FOTOGRAFIA NETTA): i crediti_cliente di QUESTA terminazione
    #   → ANNULLATO. La fotografia (PASSO 1) tratta rimborso, conguaglio e wallet erogato come TERMINI DELLA
    #   STESSA SOMMA, non casi speciali per-provenienza: la parte GIÀ EROGATA in cassa (USCITA
    #   id_contratto=None, che RESTA — R1) viene RIASSORBITA nel contratto riaperto (fold in R2-bis) → il
    #   cliente risulta aver riavuto quel denaro, che torna dovuto sul contratto. La parte non-erogata
    #   (residuo del wallet) si annulla senza muovere denaro. Chiude Bug-1 (audit): il wallet erogato NON
    #   sparisce più dalla posizione. La cassa NON si tocca (ADR-019): è ri-attribuzione gestionale.
    wallet_annullati = 0
    wallet_erogato_riassorbito = 0.0
    open_wallets = session.exec(
        select(CreditoCliente).where(
            CreditoCliente.id_contratto_origine == contract.id,
            CreditoCliente.stato != cstate.STATO_CREDITO_ANNULLATO,
            CreditoCliente.deleted_at == None,  # noqa: E711
        )
    ).all()
    for w in open_wallets:
        wallet_erogato_riassorbito += (w.importo_erogato or 0)  # cassa già uscita → rientra nella posizione
        w.stato = cstate.STATO_CREDITO_ANNULLATO
        w.data_chiusura = date.today()
        session.add(w)
        log_audit(session, "credito_cliente", w.id, "UPDATE", trainer.id, {
            "stato": {"old": "APERTO/SALDATO", "new": "ANNULLATO"},
        })
        wallet_annullati += 1
    wallet_erogato_riassorbito = round(wallet_erogato_riassorbito, 2)

    # R2) Storno inverso: azzera la quota → il residuo() net-aware si ricalcola da sé (R7).
    #     G9.2b: via terza penna — riga −quota nel ledger rettifiche + colonna a 0 in UN atto (quota == Σ).
    #     Nessuna riga-zero nel ledger append-only (se non c'è storno da revertire).
    if old_quota:
        post_adjustment(
            session, contract=contract, importo_firmato=-old_quota,
            causale=CAUSALE_REVERSAL_REOPEN, data_effettiva=date.today(), trainer_id=trainer.id,
        )
    else:
        contract.quota_stornata = 0  # normalizza l'eventuale None legacy (nessuno storno da revertire)

    # R2-bis) FOLD della fotografia netta (D1 forma-d, chiude Bug-1): la cassa-wallet già erogata
    #   (id_contratto=None) viene RIASSORBITA in `totale_rimborsato` → il residuo() net-aware (P − netto)
    #   la include PER COSTRUZIONE sul contratto riaperto, senza ramo speciale. NON è una nuova USCITA (la
    #   cassa resta intatta, ADR-019). Σ-ledger di I5: il rimborso diretto resta == Σ USCITA RIMBORSO
    #   [id_contratto], il delta di `totale_rimborsato` è coperto dall'erogato dei wallet ora ANNULLATO.
    #   Deve precedere `reconcile_rate_plan` (il piano si riallinea al residuo già comprensivo del fold).
    contract.totale_rimborsato = round(old_rimborsato + wallet_erogato_riassorbito, 2)

    # E) Ripristino SOLO le rate marcate da terminate (M1, inverso esatto; le SALDATE non erano toccate, B-3)
    rate_ripristinate = 0
    deleted_rates = session.exec(
        select(Rate).where(
            Rate.id_contratto == contract.id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.deleted_at != None,  # noqa: E711
            Rate.chiusa_da_terminazione == True,  # noqa: E712 — M1: SOLO le rate eliminate da QUESTO terminate
        )
    ).all()
    for r in deleted_rates:
        r.deleted_at = None
        r.chiusa_da_terminazione = False  # M1: marker consumato (inverso esatto del terminate)
        session.add(r)
        log_audit(session, "rate", r.id, "RESTORE", trainer.id)
        rate_ripristinate += 1

    # R5-bis) G8.1.1/F2: riallinea il piano rate al residuo() net-aware ricalcolato (la cassa che resta ha
    #   cambiato il residuo → le rate ripristinate AS-IS potrebbero non combaciare). Auto-realign (founder).
    reconcile = reconcile_rate_plan(session, contract, trainer.id)

    # Ricalcola stato_pagamento net-aware (F4): il reopen ha cambiato il residuo. SSoT unico (de-dup).
    contract.stato_pagamento = cstate.recompute_stato_pagamento(contract)

    # F) Riapertura: stato terminale azzerato
    contract.chiuso = False
    contract.motivo_chiusura = None
    contract.data_chiusura = None
    session.add(contract)

    # G) Audit atomico + transizione `chiuso` (la logga log_contract_lifecycle_transition, no doppio).
    #   ADR-019: la cassa resta (rimborso/versato INVARIATI) → si registrano i fatti datati preservati
    #   accanto a ciò che si annulla (storno, receivable, rate ripristinate).
    log_audit(session, "contract", contract.id, "UPDATE", trainer.id, {
        "motivo_chiusura": {"old": old_motivo, "new": None},
        "chiuso": {"old": True, "new": False},
        "quota_stornata": {"old": old_quota, "new": 0},
        "rate_ripristinate": rate_ripristinate,
        "rate_riallineate": reconcile["tagliate"] + reconcile["rimosse"] + reconcile["cresciute"],  # F2: piano riconciliato al residuo (taglio/crescita)
        "residuo_dopo": reconcile["residuo"],
        "crediti_differiti_annullati": crediti_annullati,
        "wallet_cliente_annullati": wallet_annullati,
        # D1 forma-d: l'erogato dei wallet annullati rientra nella posizione (fold net-aware, R2-bis).
        "wallet_erogato_riassorbito": wallet_erogato_riassorbito,
        "totale_rimborsato": {"old": round(old_rimborsato, 2), "new": contract.totale_rimborsato},
        "totale_versato_preservato": round(old_versato, 2),       # ADR-019: cassa (versato) NON toccata
    })
    log_contract_lifecycle_transition(
        session,
        contract,
        old_chiuso=old_chiuso,
        motivo="riapertura_esplicita",
    )
    # Post-condizione dell'executor (AC-G93-4): sensore invarianti PRE-commit (D-C4). La posizione
    # ricalcolata deve rispettare gli invarianti (predisposta per 409 in G9.4).
    log_invariant_violations(session, contract, motivo="reopen")
    session.commit()
    session.refresh(contract)
    return contract


# ════════════════════════════════════════════════════════════
# Auto-close/auto-reopen UNIFICATO (G9.3d) — un solo percorso logico, direzioni per-caller
# ════════════════════════════════════════════════════════════

def sync_contract_chiuso(
    session: Session,
    contract_id: int,
    *,
    reopen_motivo: str = "riapertura_crediti",
    directions: frozenset = frozenset({"close", "reopen"}),
) -> None:
    """
    Ricalcola se il contratto deve essere chiuso o riaperto (auto-close/auto-reopen, FSM righe 1-2).

    UN solo percorso logico (AC-G93-3): condizione `should_be_chiuso = SALDATO + crediti esauriti` +
    reopen-allowlist G7.2 (`puo_auto_riaprire`). Prima viveva in 3 copie: `agenda._sync_contract_chiuso`
    (bidirezionale), `pay_rate` E-auto inline (solo close), `unpay_rate` auto-reopen inline (solo reopen).

    `directions` (D-C6): la CONDIZIONE è una sola, la direzione permessa è policy del trigger —
    payment-close passa `{"close"}`, payment-reopen `{"reopen"}` (byte-parity coi vecchi inline: un sync
    bidirezionale su `unpay` potrebbe CHIUDERE in un corner patologico, comportamento nuovo vietato).
    `reopen_motivo`: la chiusura logga sempre `"completamento"`; la riapertura logga il motivo del
    trigger (`"riapertura_crediti"` credit-driven, `"riapertura_pagamento"` payment-driven).

    NB (documentato, non-reachable-by-construction): il guard `not crediti_totali → return` vale anche
    per la direzione reopen — un chiuso COMPLETAMENTO con `crediti_totali` NULL non esiste (tutti i
    writer di COMPLETAMENTO esigono `crediti_totali` truthy); il vecchio inline di `unpay` lo avrebbe
    riaperto, questo no. Stato solo costruibile a mano via ORM.
    """
    contract = session.get(Contract, contract_id)
    if not contract or not contract.crediti_totali:
        return

    crediti_usati = session.exec(
        select(func.count(Event.id)).where(
            Event.id_contratto == contract.id,
            Event.categoria == "PT",
            # G7.8: Rinviato libera il credito (ADR-017) → no auto-close sulle rinviate (D-AUTO-CLOSE)
            Event.stato.in_(cstate.STATI_OCCUPAZIONE_CREDITO),
            Event.deleted_at == None,  # noqa: E711
        )
    ).one()

    should_be_chiuso = (
        crediti_usati >= contract.crediti_totali
        and contract.stato_pagamento == "SALDATO"
    )

    # FSM riga 3-4 — reopen-allowlist G7.2 (predicato `puo_auto_riaprire`): l'auto-riapertura scatta SOLO
    # per le chiusure da COMPLETAMENTO; NULL/TERMINAZIONE_* si riaprono solo via `execute_reopen`.
    if contract.chiuso and not should_be_chiuso and not puo_auto_riaprire(contract):
        return

    if contract.chiuso != should_be_chiuso:
        # D-C6: direzione permessa dal trigger (la condizione resta unica)
        if should_be_chiuso and "close" not in directions:
            return
        if not should_be_chiuso and "reopen" not in directions:
            return
        old_chiuso = contract.chiuso
        contract.chiuso = should_be_chiuso
        if should_be_chiuso:
            contract.motivo_chiusura = "COMPLETAMENTO"  # G7.0: qualifica la via a CHIUSO
        else:
            contract.motivo_chiusura = None  # G7.2 (AC-7.2-5): riapertura legittima → "aperto senza motivo"
        session.add(contract)
        # Audita la transizione: completamento (chiude) vs riapertura (motivo del trigger)
        log_contract_lifecycle_transition(
            session,
            contract,
            old_chiuso=old_chiuso,
            motivo="completamento" if should_be_chiuso else reopen_motivo,
        )
