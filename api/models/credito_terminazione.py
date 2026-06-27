# api/models/credito_terminazione.py
"""
Modello CreditoTerminazione — credito a favore del trainer che SOPRAVVIVE alla chiusura (G7.10, ADR-018).

Quando una terminazione ha esito CREDITO_TRAINER e il trainer sceglie `A_CREDITO` ("chiudo oggi, il
cliente paga dopo"), il dovuto NON resta nel contratto (romperebbe `residuo()==0` su CHIUSO): viene
**stornato** dal residuo del contratto (`quota_stornata`) e **ri-tracciato** qui come receivable parallelo,
FUORI da `contract_state.residuo()`. Mai una Rate viva su un contratto chiuso (no rata-fantasma).

Lifecycle del receivable: `APERTO` → `SALDATO` (incassato per intero) | `ANNULLATO` (il trainer rinuncia
al residuo non incassato). L'incasso (anche parziale) genera un `CashMovement` ENTRATA
`INCASSO_CONGUAGLIO_CONTRATTO` e fa crescere `totale_versato` (Strada B). `reopen` del contratto annulla
il receivable e (via la gamba C-bis) inverte gli incassi parziali già registrati.

Ownership: `id_contratto` → `Contract.trainer_id` (Deep Relational IDOR). `trainer_id` ridondante per le
query worklist cross-contratto (gemella di G6 "incassa residuo").
"""

from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class CreditoTerminazione(SQLModel, table=True):
    __tablename__ = "crediti_terminazione"

    id: Optional[int] = Field(default=None, primary_key=True)
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    id_contratto: int = Field(foreign_key="contratti.id", index=True)
    id_cliente: int = Field(foreign_key="clienti.id")
    importo: float                               # = credito_trainer (R − V) fissato al terminate
    importo_incassato: float = Field(default=0)  # accumulato dagli incassi parziali (≤ importo)
    stato: str = Field(default="APERTO")         # APERTO | SALDATO | ANNULLATO
    data_creazione: date
    data_chiusura: Optional[date] = None         # valorizzata quando SALDATO o ANNULLATO
    deleted_at: Optional[datetime] = None
