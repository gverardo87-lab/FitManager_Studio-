# api/models/credito_cliente.py
"""
Modello CreditoCliente — wallet del cliente (customer credit balance, G8.1, ADR-020).

Specchio lato CLIENTE del receivable trainer `crediti_terminazione`: quando una terminazione ha esito
CREDITO_CLIENTE e il trainer rimborsa SOLO una parte (X < credito_cliente), il non-rimborsato NON si
perde — diventa un credito a favore del cliente, tracciato qui FUORI dal `residuo()` del contratto.
Anche un eventuale overpayment instradato da `reopen` (ADR-019 D-INSTRADA) finirà qui (causale
`OVERPAYMENT`, predisposta — in G8.1 i guard di pagamento non producono ancora overpayment).

Lifecycle: `APERTO` → `SALDATO` (erogato per intero) | `ANNULLATO` (reopen della terminazione d'origine).
L'erogazione (anche parziale, G8.1 Step 4) genera un `CashMovement` USCITA `RIMBORSO_CONTRATTO` e fa
crescere `importo_erogato`. **Distinto** da `crediti_terminazione` (receivable trainer): in contabilità
sono due libri diversi — il wallet è un anticipo/passività verso il cliente, il receivable un credito.

Ownership: `trainer_id` diretto (worklist cross-cliente, gemella di G6/G7.10) + `id_cliente` →
Client.trainer_id. FK verso tabelle business crm.db (mai catalog/nutrition, pitfall #15).
"""

from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class CreditoCliente(SQLModel, table=True):
    __tablename__ = "crediti_cliente"

    id: Optional[int] = Field(default=None, primary_key=True)
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    id_cliente: int = Field(foreign_key="clienti.id", index=True)
    importo: float                                     # credito a favore del cliente (non-rimborsato / overpayment)
    importo_erogato: float = Field(default=0)          # accumulato dalle erogazioni in cassa (≤ importo)
    stato: str = Field(default="APERTO")               # APERTO | SALDATO | ANNULLATO
    causale: str = Field(default="RIMBORSO_DIFFERITO")  # RIMBORSO_DIFFERITO | OVERPAYMENT
    id_contratto_origine: int = Field(foreign_key="contratti.id", index=True)  # da quale terminazione nasce
    data_creazione: date
    data_chiusura: Optional[date] = None               # valorizzata quando SALDATO o ANNULLATO
    deleted_at: Optional[datetime] = None
