# api/schemas/financial.py
"""
Pydantic schemas per il dominio finanziario (Contratti + Rate + Movimenti + Dashboard).

SICUREZZA - Mass Assignment Prevention:
- ContractCreate: NO trainer_id (injected da JWT nel router)
- RateCreate: NO trainer_id, NO id_cliente (derivano dal contratto)
- RatePayment: NO id_contratto, NO id_cliente (derivano dalla rata target)
- MovementManualCreate: NO id_contratto, NO id_rata, NO id_cliente (Ledger Integrity)

Deep Relational IDOR chain:
  Rate -> Contract.trainer_id (verifica diretta)
  Contract -> Client.trainer_id (verifica coerenza Relational IDOR)
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from api.schemas import clinical as clinical_schemas

# Backward compatibility: readiness schemas moved to `api.schemas.clinical`
# and are re-exported here to avoid breaking existing imports.
ClinicalReadinessClientItem = clinical_schemas.ClinicalReadinessClientItem
ClinicalReadinessSummary = clinical_schemas.ClinicalReadinessSummary
ClinicalReadinessResponse = clinical_schemas.ClinicalReadinessResponse
ClinicalReadinessWorklistResponse = clinical_schemas.ClinicalReadinessWorklistResponse


# ════════════════════════════════════════════════════════════
# COSTANTI VALIDE (allineate a core/constants.py)
# ════════════════════════════════════════════════════════════

VALID_PAYMENT_METHODS = {"CONTANTI", "POS", "BONIFICO", "ASSEGNO", "ALTRO"}
VALID_RATE_STATUSES = {"PENDENTE", "PARZIALE", "SALDATA"}
VALID_PAYMENT_STATUSES = {"PENDENTE", "PARZIALE", "SALDATO"}
# ADR-018: azioni del ramo CREDITO_TRAINER della terminazione. `A_CREDITO` = credito differito (G7.10):
# il dovuto diventa un receivable `crediti_terminazione` FUORI da residuo(), incassabile (anche parziale) dopo.
VALID_AZIONI_CREDITO_TRAINER = {"INCASSA_ORA", "RINUNCIA_ESPRESSA", "A_CREDITO"}


# ════════════════════════════════════════════════════════════
# CONTRACT SCHEMAS
# ════════════════════════════════════════════════════════════

# Invariante di dominio (FDM §9.5.7, PREREQ-prezzo di G6): «niente prezzo = niente contratto».
# Un contratto è l'atto che attiva le coperture (assicurative/fiscali) e abilita gli incassi;
# senza prezzo strettamente positivo non è ancora un contratto. Messaggio didattico in italiano
# (regola #9), riusato da create e update — il software insegna il principio, non vomita un 422 crudo.
PREZZO_OBBLIGATORIO_MSG = (
    "Definisci un prezzo per il contratto: senza un prezzo concordato non si attivano "
    "le coperture (assicurative e fiscali) e non è possibile registrare incassi."
)


class ContractCreate(BaseModel):
    """
    Schema per creazione contratto.

    BLINDATO: nessun trainer_id — iniettato dal JWT nel router.
    id_cliente: verificato via Relational IDOR (deve appartenere al trainer).
    """
    model_config = {"extra": "forbid"}

    id_cliente: int = Field(gt=0)
    tipo_pacchetto: str = Field(min_length=1, max_length=100)
    crediti_totali: int = Field(ge=1, le=1000)
    prezzo_totale: float = Field(le=1_000_000)  # > 0 imposto nel validator (messaggio didattico, FDM §9.5.7)
    data_inizio: date
    # data_scadenza nullable (FDM §2, audit Contract 2026-06-23): i pacchetti/carnet a crediti
    # senza termine sono un'offerta reale. None = "senza scadenza" → il contratto resta ATTIVO
    # finché non si esauriscono i crediti (auto-close via _sync_contract_chiuso). SSoT null-safe.
    data_scadenza: Optional[date] = None
    acconto: float = Field(default=0, ge=0, le=1_000_000)
    metodo_acconto: Optional[str] = None
    note: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_dates_and_acconto(self):
        """Validazione cross-field: prezzo > 0 (invariante) + date coerenti + acconto <= prezzo."""
        if self.prezzo_totale <= 0:
            raise ValueError(PREZZO_OBBLIGATORIO_MSG)
        # Coerenza date solo se una scadenza è stata fornita (None = carnet senza termine).
        if self.data_scadenza is not None and self.data_scadenza <= self.data_inizio:
            raise ValueError("data_scadenza deve essere dopo data_inizio")
        if self.acconto > self.prezzo_totale:
            raise ValueError("acconto non puo' essere maggiore del prezzo_totale")
        if self.acconto > 0 and not self.metodo_acconto:
            raise ValueError("metodo_acconto obbligatorio se acconto > 0")
        if self.metodo_acconto and self.metodo_acconto not in VALID_PAYMENT_METHODS:
            raise ValueError(f"metodo_acconto invalido. Validi: {sorted(VALID_PAYMENT_METHODS)}")
        return self


class ContractUpdate(BaseModel):
    """
    Schema per aggiornamento contratto (partial update).

    BLINDATO:
    - NO trainer_id (non trasferibile)
    - NO id_cliente (non trasferibile)
    - NO crediti_usati, totale_versato (calcolati automaticamente)
    - NO chiuso (G7.3 §8): la chiusura NON passa più da update. Le uniche vie a CHIUSO sono
      l'auto-close (completamento, via pay/eventi) e `POST /contracts/{id}/terminate` (terminazione
      anticipata, che qualifica sempre la chiusura con un `motivo_chiusura`). Toglierlo qui elimina
      la chiusura-manuale-senza-motivo (`chiuso=True ∧ motivo=NULL`) come stato producibile via API.
    """
    model_config = {"extra": "forbid"}

    tipo_pacchetto: Optional[str] = Field(None, min_length=1, max_length=100)
    crediti_totali: Optional[int] = Field(None, ge=1, le=1000)
    prezzo_totale: Optional[float] = Field(None, le=1_000_000)  # > 0 se presente (chiude il leak di update, FDM §9.5.7)
    data_inizio: Optional[date] = None
    data_scadenza: Optional[date] = None
    note: Optional[str] = Field(None, max_length=500)

    @field_validator("prezzo_totale")
    @classmethod
    def _prezzo_positivo(cls, v: Optional[float]) -> Optional[float]:
        # L'invariante prezzo>0 (FDM §9.5.7) vale anche in update: non si può azzerare il prezzo
        # di un contratto esistente (riaprirebbe il credito-fantasma chiuso a creazione).
        if v is not None and v <= 0:
            raise ValueError(PREZZO_OBBLIGATORIO_MSG)
        return v


class ContractResponse(BaseModel):
    """Response model per contratto con rate."""
    id: int
    id_cliente: int
    tipo_pacchetto: Optional[str] = None
    data_vendita: Optional[date] = None
    data_inizio: Optional[date] = None
    data_scadenza: Optional[date] = None
    crediti_totali: Optional[int] = None
    crediti_usati: int = 0
    prezzo_totale: Optional[float] = None
    acconto: float = 0
    totale_versato: float = 0
    stato_pagamento: str = "PENDENTE"
    note: Optional[str] = None
    chiuso: bool = False
    rinnovo_di: Optional[int] = None
    # Terminazione (SPEC_G7.0): colonne reali. netto_incassato è derivato (sotto), oggi == totale_versato.
    totale_rimborsato: float = 0
    quota_stornata: float = 0
    data_chiusura: Optional[date] = None
    motivo_chiusura: Optional[str] = None

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def netto_incassato(self) -> float:
        """Incassato NETTO dei rimborsi (Strada B, FDM §9.5). Delega al SSoT
        `contract_state.netto_incassato` (la response LEGGE, non ricalcola — G7.1).
        Load-bearing da G7.3 (primo rimborso); oggi == totale_versato."""
        from api.services import contract_state as cstate
        return cstate.netto_incassato(self)


class ContractTerminate(BaseModel):
    """
    Input per la terminazione anticipata (G7.3 + ADR-018). Atto UMANO esplicito su un contratto vivo.

    BLINDATO (mass-assignment): NESSUN campo calcolato in input — né `totale_versato`, né
    `totale_rimborsato`/`quota_stornata`. Il conguaglio (e quindi `credito_cliente`/`credito_trainer`,
    l'esito e il `motivo_chiusura`) è calcolato server-side (`compute_settlement`, base sedute), NON
    scelto dal trainer. I DUE importi in input sono **proposte editabili**, mai conguagli arbitrari:
    `importo_incassato` (saldo a favore del trainer, cap `[0, credito_trainer]`) e `importo_rimborso`
    (rimborso al cliente, cap `[0, credito_cliente]`); il cap superiore è verificato nel router → 422.

    Ramo CREDITO_CLIENTE (G8.1/ADR-020): `importo_rimborso` EDITABILE `[0, credito_cliente]` (default =
    pieno); `metodo_rimborso` obbligatorio SOLO se rimborso > 0; il non-rimborsato va a wallet cliente.
    Ramo CREDITO_TRAINER: `azione_credito_trainer` obbligatoria (422); poi
      - `INCASSA_ORA` → `metodo_pagamento` obbligatorio; `importo_incassato` opzionale (default = credito_trainer);
      - `RINUNCIA_ESPRESSA` → `note` non vuote obbligatorie.
    `data_chiusura`: quando la chiusura ha effetto (default oggi nel router).
    """
    model_config = {"extra": "forbid"}

    metodo_rimborso: Optional[str] = None                 # ramo CREDITO_CLIENTE (richiesto solo se rimborso > 0)
    importo_rimborso: Optional[float] = None              # CREDITO_CLIENTE (G8.1): rimborso editabile [0, credito_cliente]
    azione_credito_trainer: Optional[str] = None          # ramo CREDITO_TRAINER: INCASSA_ORA | RINUNCIA_ESPRESSA
    importo_incassato: Optional[float] = None             # INCASSA_ORA: proposta editabile [0, credito_trainer]
    metodo_pagamento: Optional[str] = None                # INCASSA_ORA: metodo dell'incasso di conguaglio
    note: Optional[str] = Field(None, max_length=500)
    data_chiusura: Optional[date] = None

    @field_validator("metodo_rimborso", "metodo_pagamento")
    @classmethod
    def _validate_metodo(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_PAYMENT_METHODS:
            raise ValueError(f"Metodo invalido. Validi: {sorted(VALID_PAYMENT_METHODS)}")
        return v

    @field_validator("azione_credito_trainer")
    @classmethod
    def _validate_azione(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_AZIONI_CREDITO_TRAINER:
            raise ValueError(f"Azione non valida. Valide: {sorted(VALID_AZIONI_CREDITO_TRAINER)}.")
        return v

    @field_validator("importo_incassato")
    @classmethod
    def _validate_importo_incassato(cls, v: Optional[float]) -> Optional[float]:
        # Cap superiore (<= credito_trainer) verificato nel router (richiede R−V server-side).
        if v is not None and v < 0:
            raise ValueError("L'importo da incassare non può essere negativo.")
        return v

    @field_validator("importo_rimborso")
    @classmethod
    def _validate_importo_rimborso(cls, v: Optional[float]) -> Optional[float]:
        # Cap superiore (<= credito_cliente) verificato nel router (richiede V−R server-side).
        if v is not None and v < 0:
            raise ValueError("L'importo da rimborsare non può essere negativo.")
        return v

    @field_validator("data_chiusura")
    @classmethod
    def _data_chiusura_non_futura(cls, v: Optional[date]) -> Optional[date]:
        # D4 (G7.5c): una terminazione registra denaro uscito ORA o in passato (il rimborso è
        # cassa in uscita), mai un impegno futuro. Una data nel futuro è un errore d'inserimento.
        if v is not None and v > date.today():
            raise ValueError(
                "La data di chiusura non può essere nel futuro: la terminazione (e l'eventuale "
                "rimborso) registra denaro uscito ora o in passato, non un impegno futuro."
            )
        return v


class ContractSettlementPreview(BaseModel):
    """
    Esito del conguaglio di terminazione, calcolato PRIMA della conferma (G7.3 dry-run, AC-7.3-4).

    Posizionamento (ADR-014, §0 della spec): il software **propone** un conguaglio calcolato col
    metodo standard pro-rata sedute; **non afferma** che sia l'obbligo legale del trainer. Il campo
    `messaggio` porta il framing di proposta (load-bearing quanto i numeri): mai "da rimborsare",
    sempre "calcolato/proposto, verifica con le condizioni del contratto".
    """
    esito: str                            # CREDITO_CLIENTE | CREDITO_TRAINER | PARI (balance-based, ADR-018)
    motivo_chiusura: str                  # derivato: TERMINAZIONE_RIMBORSO | TERMINAZIONE_SALDO_TRAINER | CONSUNZIONE
    valore_servizio_reso: float
    conguaglio: float                     # valore_reso − versato (firmato)
    importo_rimborso: float               # credito_cliente: > 0 solo se esito CREDITO_CLIENTE
    credito_trainer: float = 0.0          # > 0 solo se esito CREDITO_TRAINER (default proposto per INCASSA_ORA, editabile [0, credito_trainer])
    quota_da_stornare: float              # residuo_pre che verrà regolato (storno + eventuale incasso/abbuono)
    sedute_erogate: int                   # sedute Completate (servizio reso) — base del pro-rata
    sedute_totali: Optional[int] = None   # crediti_totali (None = senza monte-sedute)
    sedute_prenotate: int = 0             # D2 (G7.5c): PT prenotate-non-svolte — SOLO display (NON entra nel conguaglio)
    metodo_rimborso_richiesto: bool       # True se esito CREDITO_CLIENTE → il form deve chiedere il metodo rimborso
    azioni_permesse: List[str] = []       # ramo CREDITO_TRAINER: scelte offerte (INCASSA_ORA, RINUNCIA_ESPRESSA, A_CREDITO)
    policy_mode: str = "pro_sedute"       # metodo di valorizzazione (default dichiarato, §0)
    messaggio: str                        # framing di proposta (§0/§4)


class CreditoTerminazioneResponse(BaseModel):
    """Credito differito a favore del trainer (G7.10, ADR-018) — receivable FUORI da `residuo()`.
    `residuo` = `importo − importo_incassato` (quanto resta da incassare)."""
    model_config = {"from_attributes": True}

    id: int
    id_contratto: int
    id_cliente: int
    importo: float
    importo_incassato: float
    stato: str                            # APERTO | SALDATO | ANNULLATO
    data_creazione: date
    data_chiusura: Optional[date] = None

    @computed_field
    @property
    def residuo(self) -> float:
        """Quanto resta da incassare. SSoT unico (G9.0c): delega a `contract_state.residuo_credito`."""
        from api.services import contract_state as cstate
        return cstate.residuo_credito(self.importo, self.importo_incassato)


class CreditoClienteResponse(BaseModel):
    """Wallet del cliente (G8.1, ADR-020) — credito a favore del cliente FUORI dal `residuo()`.
    `residuo` = `importo − importo_erogato` (quanto resta da erogare in cassa)."""
    model_config = {"from_attributes": True}

    id: int
    trainer_id: int
    id_cliente: int
    importo: float
    importo_erogato: float
    stato: str                            # APERTO | SALDATO | ANNULLATO
    causale: str                          # RIMBORSO_DIFFERITO | OVERPAYMENT
    id_contratto_origine: int
    data_creazione: date
    data_chiusura: Optional[date] = None

    @computed_field
    @property
    def residuo(self) -> float:
        """Quanto resta da erogare in cassa. SSoT unico (G9.0c): delega a `contract_state.residuo_credito`."""
        from api.services import contract_state as cstate
        return cstate.residuo_credito(self.importo, self.importo_erogato)


class ReopenPreview(BaseModel):
    """Impatto pieno di una riapertura, calcolato PRIMA della conferma (G8.1/ADR-019, dry-run).

    Gemello di ContractSettlementPreview per il reopen NON-distruttivo: mostra cosa RESTA (la cassa di
    terminazione NON si cancella → diventa pagamento/rimborso sul contratto) e cosa si ANNULLA (storno,
    receivable, wallet), col residuo ricalcolato net-aware. Se esiste un rinnovo vivo a valle (S5) lo
    SEGNALA, perché il FE proponga la gestione — mai blocco cieco, mai azione silenziosa (D-PROPONE).
    ZERO scritture.
    """
    residuo_dopo: float                    # residuo() net-aware dopo la riapertura (quota azzerata)
    rimborso_che_resta: float              # USCITA RIMBORSO_CONTRATTO non cancellata (diventa rimborso sul contratto)
    incasso_che_resta: float               # ENTRATA INCASSO_CONGUAGLIO non cancellata (diventa pagamento)
    rate_da_ripristinare: int              # rate marcate chiusa_da_terminazione che tornano vive
    receivable_da_annullare: int           # crediti_terminazione (G7.10) che passano ad ANNULLATO
    wallet_da_annullare: int = 0           # crediti_cliente (ADR-020) che passano ad ANNULLATO (G8.1 Step 3)
    wallet_erogato_riassorbito: float = 0.0  # D1 forma-d: erogato wallet che RIENTRA nel residuo (mai silenzioso)
    ha_rinnovo_vivo: bool = False          # S5: esiste un contratto figlio (rinnovo_di) ancora aperto
    id_rinnovo_vivo: Optional[int] = None  # id del rinnovo vivo, se presente
    messaggio: str                         # riepilogo leggibile (la cassa resta, il residuo si ricalcola)


# ════════════════════════════════════════════════════════════
# RATE SCHEMAS
# ════════════════════════════════════════════════════════════

class RateCreate(BaseModel):
    """
    Schema per creazione singola rata manuale.

    BLINDATO:
    - NO trainer_id (derivato dal contratto)
    - NO id_cliente (derivato dal contratto)
    - id_contratto: verificato via Bouncer (contratto deve appartenere al trainer)
    """
    model_config = {"extra": "forbid"}

    id_contratto: int = Field(gt=0)
    data_scadenza: date
    importo_previsto: float = Field(gt=0, le=1_000_000)
    descrizione: Optional[str] = Field(None, max_length=200)


class RateUpdate(BaseModel):
    """
    Schema per aggiornamento rata (partial update, tutte le rate).

    data_scadenza e descrizione: sempre modificabili.
    importo_previsto su rate con pagamenti: consentito se >= importo_saldato.

    BLINDATO:
    - NO id_contratto (non trasferibile)
    - NO stato (ricalcolato automaticamente se importo_previsto cambia)
    - NO importo_saldato (gestito solo via pagamento)
    """
    model_config = {"extra": "forbid"}

    data_scadenza: Optional[date] = None
    importo_previsto: Optional[float] = Field(None, gt=0, le=1_000_000)
    descrizione: Optional[str] = Field(None, max_length=200)


class RatePayment(BaseModel):
    """
    Schema per pagamento rata — Unit of Work.

    Operazione atomica:
    1. Aggiorna rate_programmate.importo_saldato += importo
    2. Aggiorna rate_programmate.stato (PARZIALE | SALDATA)
    3. Aggiorna contratti.totale_versato += importo
    4. Crea movimento_cassa ENTRATA

    BLINDATO:
    - NO id_contratto, NO id_cliente (derivano dalla rata target)
    - importo: strettamente positivo
    """
    model_config = {"extra": "forbid"}

    importo: float = Field(gt=0, le=1_000_000)
    metodo: str = Field(default="CONTANTI")
    data_pagamento: date = Field(default_factory=date.today)
    note: Optional[str] = Field(None, max_length=500)

    @field_validator("metodo")
    @classmethod
    def validate_metodo(cls, v: str) -> str:
        if v not in VALID_PAYMENT_METHODS:
            raise ValueError(f"Metodo invalido. Validi: {sorted(VALID_PAYMENT_METHODS)}")
        return v


class RatePaymentReceipt(BaseModel):
    """Singolo pagamento registrato per una rata (da CashMovement)."""
    id: int
    importo: float
    metodo: Optional[str] = None
    data_pagamento: date
    note: Optional[str] = None


class RateResponse(BaseModel):
    """
    Response model per singola rata.

    Campi ricevuta (opzionali, ultimo pagamento — backward-compat):
    - data_pagamento: data effettiva dell'ultimo pagamento
    - metodo_pagamento: metodo usato nell'ultimo pagamento

    Storico completo:
    - pagamenti: lista cronologica di tutti i pagamenti sulla rata

    Campi computati (calcolati nel router, mai dal frontend):
    - importo_residuo: quanto manca per saldare questa rata
    - is_scaduta: true se non saldata e oltre la data_scadenza
    - giorni_ritardo: giorni di ritardo (0 se non scaduta)
    """
    id: int
    id_contratto: int
    data_scadenza: date
    importo_previsto: float
    descrizione: Optional[str] = None
    stato: str = "PENDENTE"
    importo_saldato: float = 0
    data_pagamento: Optional[date] = None
    metodo_pagamento: Optional[str] = None
    pagamenti: List[RatePaymentReceipt] = []

    # ── Computed (calcolati nel router) ──
    importo_residuo: float = 0
    is_scaduta: bool = False
    giorni_ritardo: int = 0

    model_config = {"from_attributes": True}


class ContractListResponse(ContractResponse):
    """
    Response arricchita per la lista contratti con KPI aggregati.

    Campi extra (calcolati nel router via batch fetch):
    - client_nome/cognome: nome del cliente (evita JOIN lato frontend)
    - rate_totali/rate_pagate: conteggi per progress badge
    - ha_rate_scadute: derivato dal SSoT `contract_state.rate_scadute` (AC-1b, fonte unica)

    Stato derivato dal SSoT (SPEC_VOCABOLARIO §2.2 — il frontend LEGGE, non ricalcola):
    - lifecycle/money_substate: i due assi (vita × denaro), valori-enum del SSoT.
    - is_insolvente/in_scadenza: flag derivati, mutuamente esclusivi per costruzione.
    """
    client_nome: str = ""
    client_cognome: str = ""
    rate_totali: int = 0
    rate_pagate: int = 0
    ha_rate_scadute: bool = False
    # ── Stato derivato dal SSoT contract_state (SPEC_VOCABOLARIO §2.2) ──
    lifecycle: str = "attivo"          # attivo|sospeso|esaurito|chiuso
    money_substate: str = "saldato"    # saldato|da_pianificare|parziale|pianificato
    is_insolvente: bool = False        # scaduto (SOSPESO/ESAURITO) + rate scadute
    in_scadenza: bool = False          # ATTIVO entro SOGLIA_IN_SCADENZA_GG
    residuo: float = 0                 # SSoT contract_state.residuo() — il frontend LEGGE, non ricalcola (G6)
    # ── Trasparenza erogato↔occupazione (R4: L1 + M4) — il frontend LEGGE, non ricalcola ──
    sedute_completate: int = 0            # erogato (servizio reso) da affiancare ai residui (L1)
    sedute_non_erogate_chiusura: int = 0  # M4: prenotate-non-erogate alla chiusura (solo chiuso COMPLETAMENTO)


class RenewalChainItem(BaseModel):
    """Minimal contract info for renewal chain display."""
    id: int
    tipo_pacchetto: Optional[str] = None
    data_inizio: Optional[str] = None
    data_scadenza: Optional[str] = None
    chiuso: bool = False
    lifecycle: str = "attivo"  # stato di vita reale del nodo catena (SPEC_VOCABOLARIO §2.7/G3)


class ContractMovementItem(BaseModel):
    """Movimento di cassa del contratto (G8.1.1/F1) — per lo storico cassa unificato sul dettaglio.
    Tutti i `CashMovement` con `id_contratto` (ENTRATA+USCITA): acconto, pagamenti rata, rimborso,
    conguaglio. L'erogazione wallet (`id_contratto=None`) NON è qui (cassa a livello cliente, sul profilo)."""
    model_config = {"from_attributes": True}

    id: int
    tipo: str                       # ENTRATA | USCITA
    categoria: str                  # ACCONTO_CONTRATTO | PAGAMENTO_RATA | RIMBORSO_CONTRATTO | INCASSO_CONGUAGLIO_CONTRATTO | ...
    importo: float
    data_effettiva: date
    metodo: Optional[str] = None
    id_rata: Optional[int] = None   # correla col piano rate (None = movimento a livello contratto)
    note: Optional[str] = None


class ContractHistoryEvent(BaseModel):
    """Evento CURATO dello storico stato/attività del contratto (G8.1.1/F6) — parsato da `audit_log`.
    Il grezzo completo resta in `/movements/audit-log`."""
    tipo: str                       # creato | terminato | riaperto | saldato | stato | modificato | eliminato | ripristinato
    titolo: str
    dettaglio: Optional[str] = None
    data: datetime


class ContractWithRatesResponse(ContractResponse):
    """
    Response model per contratto con lista rate embedded.

    KPI computati (calcolati in _to_response_with_rates, unica fonte di verita'):
    - Il frontend NON calcola nessun valore finanziario, li legge da qui.
    - Formula chiave: importo_da_rateizzare = prezzo - acconto - somma_saldate
    """
    rate: List[RateResponse] = []
    movimenti: List[ContractMovementItem] = []  # F1: storico cassa unificato (acconto+rate+rimborsi+conguagli)

    # ── Client info (per la pagina dettaglio) ──
    client_nome: str = ""
    client_cognome: str = ""

    # ── Renewal chain ──
    contratto_originale: Optional[RenewalChainItem] = None  # parent (rinnovo_di)
    rinnovi_successivi: List[RenewalChainItem] = []          # children

    # ── KPI Computed (calcolati nel router) ──
    residuo: float = 0                  # SSoT: contract_state.residuo() (no formula inline)
    percentuale_versata: int = 0        # round((totale_versato / prezzo_totale) * 100)
    importo_da_rateizzare: float = 0    # prezzo - acconto - somma(SALDATA)
    somma_rate_previste: float = 0      # sum(ALL importo_previsto)
    somma_rate_saldate: float = 0       # sum(SALDATA importo_previsto)
    somma_rate_pendenti: float = 0      # sum(non-SALDATA importo_previsto)
    piano_allineato: bool = True        # abs(importo_da_rateizzare - somma_rate_pendenti) < 0.01
    importo_disallineamento: float = 0  # importo_da_rateizzare - somma_rate_pendenti
    rate_totali: int = 0
    rate_pagate: int = 0
    rate_scadute: int = 0

    # ── Credit breakdown (computed on read da eventi PT) ──
    sedute_programmate: int = 0   # stato=Programmato
    sedute_completate: int = 0    # stato=Completato
    sedute_rinviate: int = 0      # stato=Rinviato
    crediti_residui: int = 0      # crediti_totali - programmate - completate
    sedute_non_erogate_chiusura: int = 0  # M4: prenotate-non-erogate alla chiusura (solo chiuso COMPLETAMENTO)

    # ── Stato derivato dal SSoT contract_state (SPEC_VOCABOLARIO §2.2, scheda dettaglio) ──
    lifecycle: str = "attivo"          # attivo|sospeso|esaurito|chiuso
    money_substate: str = "saldato"    # saldato|da_pianificare|parziale|pianificato
    is_insolvente: bool = False        # scaduto (SOSPESO/ESAURITO) + rate scadute
    in_scadenza: bool = False          # ATTIVO entro SOGLIA_IN_SCADENZA_GG


# ════════════════════════════════════════════════════════════
# PAYMENT PLAN GENERATION SCHEMA
# ════════════════════════════════════════════════════════════

class PaymentPlanCreate(BaseModel):
    """
    Schema per generazione piano rate automatico.

    Elimina rate PENDENTI esistenti e ne crea di nuove.
    Rate gia' SALDATE vengono mantenute.
    """
    model_config = {"extra": "forbid"}

    importo_da_rateizzare: float = Field(gt=0, le=1_000_000)
    numero_rate: int = Field(ge=1, le=60)
    data_prima_rata: date
    frequenza: str = Field(default="MENSILE")

    @field_validator("frequenza")
    @classmethod
    def validate_frequenza(cls, v: str) -> str:
        valid = {"MENSILE", "SETTIMANALE", "TRIMESTRALE"}
        if v not in valid:
            raise ValueError(f"Frequenza invalida. Valide: {sorted(valid)}")
        return v


# ════════════════════════════════════════════════════════════
# MOVEMENT SCHEMAS (Ledger)
# ════════════════════════════════════════════════════════════

VALID_MOVEMENT_TYPES = {"ENTRATA", "USCITA"}


class MovementManualCreate(BaseModel):
    """
    Schema per creazione movimento manuale (spese, incassi extra).

    BLINDATO (Ledger Integrity):
    - NO id_contratto (solo movimenti di sistema — pagamenti rata, acconti)
    - NO id_rata (solo movimenti di sistema)
    - NO id_cliente (solo movimenti di sistema)
    - NO trainer_id (injected da JWT nel router)

    L'utente puo' creare solo movimenti "liberi" (affitto, attrezzatura, ecc.).
    I movimenti legati a contratti/rate vengono creati SOLO dal sistema
    tramite pay_rate e create_contract.
    """
    model_config = {"extra": "forbid"}

    importo: float = Field(gt=0, le=1_000_000)
    tipo: str
    categoria: Optional[str] = Field(None, max_length=100)
    metodo: Optional[str] = None
    data_effettiva: date
    note: Optional[str] = Field(None, max_length=500)

    @field_validator("tipo")
    @classmethod
    def validate_tipo(cls, v: str) -> str:
        if v not in VALID_MOVEMENT_TYPES:
            raise ValueError(f"Tipo invalido. Validi: {sorted(VALID_MOVEMENT_TYPES)}")
        return v

    @field_validator("categoria", mode="before")
    @classmethod
    def sanitize_categoria(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v if v else None

    @field_validator("metodo")
    @classmethod
    def validate_metodo(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_PAYMENT_METHODS:
            raise ValueError(f"Metodo invalido. Validi: {sorted(VALID_PAYMENT_METHODS)}")
        return v


class MovementResponse(BaseModel):
    """Response model per movimento cassa."""
    id: int
    data_movimento: Optional[datetime] = None
    data_effettiva: date
    tipo: str
    categoria: Optional[str] = None
    importo: float
    metodo: Optional[str] = None
    id_cliente: Optional[int] = None
    id_contratto: Optional[int] = None
    id_rata: Optional[int] = None
    id_spesa_ricorrente: Optional[int] = None
    note: Optional[str] = None
    operatore: str = "API"

    model_config = {"from_attributes": True}


# ════════════════════════════════════════════════════════════
# DASHBOARD SCHEMA
# ════════════════════════════════════════════════════════════

class DashboardSummary(BaseModel):
    """
    KPI aggregati per la dashboard.

    Tutti calcolati con query SQL aggregate (func.count, func.sum)
    per latenza zero — nessun record caricato in Python.
    """
    active_clients: int = 0
    monthly_revenue: float = 0.0
    pending_rates: int = 0
    todays_appointments: int = 0
    ledger_alerts: int = 0
    saldo_attuale: float = 0.0
    exercise_count: int = 0


# ════════════════════════════════════════════════════════════
# DASHBOARD ALERTS (Warning proattivi)
# ════════════════════════════════════════════════════════════

class AlertItem(BaseModel):
    """Singolo warning con severity, messaggio e contesto navigabile."""
    severity: str           # "critical" | "warning" | "info"
    category: str           # "ghost_events" | "expiring_contracts" | "overdue_rates" | "inactive_clients" | "birthdays"
    title: str
    detail: str
    count: int = 1
    link: Optional[str] = None   # path frontend per navigazione diretta


class DashboardAlerts(BaseModel):
    """
    Warning proattivi per la dashboard — rispondono a:
    "Cosa richiede la mia attenzione ORA?"

    6 categorie di alert:
    1. ghost_events: eventi passati ancora 'Programmato' (no-show candidates)
    2. expiring_contracts: contratti in scadenza con crediti inutilizzati
    3. overdue_rates: rate scadute non saldate
    4. inactive_clients: clienti attivi senza eventi da >14 giorni
    5. stale_schede/stale_measurements: programmi/misurazioni da aggiornare
    6. birthdays: compleanni oggi o nei prossimi 7 giorni
    """
    total_alerts: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    items: List[AlertItem] = []


# Backward compatibility:
# readiness schemas moved to `api.schemas.clinical` but remain re-exported here.


# ════════════════════════════════════════════════════════════
# RICONCILIAZIONE CONTRATTI vs LEDGER
# ════════════════════════════════════════════════════════════

class ReconciliationItem(BaseModel):
    """Singolo contratto con divergenza tra le colonne denormalizzate e il libro mastro (versato e/o
    rimborsato). G9.0b: la riconciliazione è BIDIREZIONALE — non più solo `totale_versato == Σ ENTRATA`."""
    contract_id: int
    client_name: str
    totale_versato: float
    ledger_total: float           # Σ ENTRATA[id_contratto]
    delta: float                  # totale_versato − ledger_total (lato versato)
    # ── G9.0b: lato rimborso (ancora I5 raffinata, ADR-019 D1 forma-d). Default 0 → backward-compat. ──
    totale_rimborsato: float = 0
    ledger_rimborsi: float = 0    # Σ USCITA RIMBORSO[id_contratto] + Σ erogato wallet ANNULLATO[origine]
    delta_rimborsi: float = 0     # totale_rimborsato − ledger_rimborsi


class ReconciliationResponse(BaseModel):
    """Risultato audit riconciliazione: contratti allineati vs divergenti."""
    total_contracts: int
    aligned: int
    divergent: int
    items: List[ReconciliationItem] = []


# ════════════════════════════════════════════════════════════
# AGING REPORT (Orizzonte Finanziario)
# ════════════════════════════════════════════════════════════

class AgingItem(BaseModel):
    """Singola rata nell'aging report."""
    rate_id: int
    contract_id: int
    client_id: int
    client_nome: str
    client_cognome: str
    data_scadenza: date
    giorni: int               # positivo = scaduta da N gg, negativo = manca tra N gg
    importo_previsto: float
    importo_saldato: float
    importo_residuo: float
    stato: str                # PENDENTE | PARZIALE


class AgingBucket(BaseModel):
    """Fascia temporale con rate raggruppate."""
    label: str                # "0-30", "31-60", "61-90", "90+"
    min_days: int
    max_days: int             # 999 per "90+"
    totale: float             # somma importo_residuo nel bucket
    count: int                # numero rate
    items: List[AgingItem]


class AgingResponse(BaseModel):
    """Orizzonte finanziario completo: scaduto + in arrivo."""
    totale_scaduto: float
    totale_in_arrivo: float
    rate_scadute: int
    rate_in_arrivo: int
    clienti_con_scaduto: int
    overdue_buckets: List[AgingBucket]    # 4 bucket: 0-30, 31-60, 61-90, 90+
    upcoming_buckets: List[AgingBucket]   # 4 bucket: 0-7, 8-30, 31-60, 61-90


# ════════════════════════════════════════════════════════════
# ANDAMENTO FINANZIARIO TEMPORALE (Layer 1 — cassa per periodo)
# ════════════════════════════════════════════════════════════

class FinancialTrendPeriod(BaseModel):
    """
    Incassato di un singolo periodo (mese), per cassa.

    Tre nozioni mai fuse (TASSONOMIA_FINANZIARIA.md §1 Asse 1):
    - incassi_contratti: ENTRATA con id_contratto (acconti + rate) — spina dorsale riconciliabile
    - altri_incassi: ENTRATA fuori contratto (id_contratto IS NULL), AL NETTO degli storni
    - cash_flow_reale: incassi_contratti + altri_incassi − rimborsi_contratti (netto storni E rimborsi, G7.5b)
    """
    anno: int
    mese: int
    label: str                  # es. "giu 2026"
    incassi_contratti: float
    altri_incassi: float
    cash_flow_reale: float
    # G7.5b — USCITA RIMBORSO_CONTRATTO del periodo (contra-ricavo da terminazione). cash_flow_reale ne è
    # già al netto; mostrato come **contra-linea separata** (gli incassi_* restano LORDI — BLOCKER-4: le due
    # decomposizioni nuovi/rinnovi e acconti/rate non si toccano, "nessun numero che sparisce").
    rimborsi_contratti: float = 0.0
    # Layer 2 — competenza (Σ prezzo_totale dei contratti VENDUTI nel periodo, su data_vendita).
    # Asse diverso dalla cassa: mai sommato. Lo scarto venduto−incassato = credito vivo.
    venduto: float = 0.0
    # Layer 3 — composizione di incassi_contratti (due tagli indipendenti, ognuno somma a incassi_contratti).
    incassi_nuovi: float = 0.0      # da contratti nuovi (rinnovo_di IS NULL)
    incassi_rinnovi: float = 0.0    # da rinnovi (rinnovo_di valorizzato)
    incassi_acconti: float = 0.0    # categoria ACCONTO_CONTRATTO
    incassi_rate: float = 0.0       # categoria PAGAMENTO_RATA


class FinancialTrendResponse(BaseModel):
    """
    Serie temporale: incassato (cassa, su data_effettiva) + venduto (competenza,
    su data_vendita) su N mesi consecutivi. Due assi distinti, MAI sommati.

    Storni (STORNO_SPESA_FISSA) sempre esclusi dalla cassa. Il venduto è best-effort
    sui contratti legacy (data_vendita nullable/default — vedi spec §5.4).
    """
    mesi: int
    periodi: List[FinancialTrendPeriod]      # cronologico, dal più vecchio al più recente
    tot_incassi_contratti: float
    tot_altri_incassi: float
    tot_cash_flow_reale: float
    tot_venduto: float = 0.0
    tot_incassi_nuovi: float = 0.0
    tot_incassi_rinnovi: float = 0.0
    tot_incassi_acconti: float = 0.0
    tot_incassi_rate: float = 0.0
    tot_rimborsi_contratti: float = 0.0  # G7.5b — totale rimborsi da terminazione (contra-ricavo)


# ════════════════════════════════════════════════════════════
# ESITO RINNOVO ("non rinnova" / cliente perso) — SPEC_RINNOVI_SCADUTI §5
# ════════════════════════════════════════════════════════════

VALID_RENEWAL_OUTCOME_REASONS = {"prezzo", "trasferito", "infortunio", "insoddisfatto", "altro"}


class RenewalOutcomeCreate(BaseModel):
    """
    Esito "non rinnova" su un contratto scaduto (cliente perso) con motivo strutturato.
    Stato terminale reversibile: la DELETE dell'esito riapre l'opportunità di recupero.
    """
    model_config = {"extra": "forbid"}

    motivo: str
    note: Optional[str] = Field(None, max_length=500)

    @field_validator("motivo")
    @classmethod
    def validate_motivo(cls, v: str) -> str:
        if v not in VALID_RENEWAL_OUTCOME_REASONS:
            raise ValueError(f"Motivo invalido. Validi: {sorted(VALID_RENEWAL_OUTCOME_REASONS)}")
        return v
