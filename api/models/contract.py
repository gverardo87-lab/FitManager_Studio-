# api/models/contract.py
"""
Modello Contract — mappa la tabella 'contratti' esistente in SQLite.

IMPORTANTE: la tabella esiste gia' con 7 record (tutti chiuso=0).
La colonna trainer_id viene aggiunta dalla migrazione in api/main.py.

Multi-tenancy:
- trainer_id: FK diretta verso trainers (aggiunta via migration)
- id_cliente: FK verso clienti (il cliente DEVE appartenere allo stesso trainer)

Deep Relational IDOR chain:
  Rate -> Contract.trainer_id (verifica diretta)
  Contract -> Client.trainer_id (verifica coerenza su POST)
"""

from datetime import date, datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from api.models.rate import Rate
    from api.models.movement import CashMovement


class Contract(SQLModel, table=True):
    """
    ORM model per la tabella 'contratti' esistente.

    Mappa 1:1 le colonne SQLite. Il campo trainer_id e' la FK
    per la multi-tenancy: ogni contratto appartiene a un trainer.

    Relationships:
    - rates: lista Rate associate (1:N)
    - movements: lista CashMovement associate (1:N)
    """
    __tablename__ = "contratti"

    id: Optional[int] = Field(default=None, primary_key=True)
    trainer_id: Optional[int] = Field(default=None, foreign_key="trainers.id", index=True)
    id_cliente: int = Field(foreign_key="clienti.id")
    tipo_pacchetto: Optional[str] = None
    data_vendita: Optional[date] = Field(default_factory=date.today)
    data_inizio: Optional[date] = None
    data_scadenza: Optional[date] = None
    crediti_totali: Optional[int] = None
    crediti_usati: int = Field(default=0)
    prezzo_totale: Optional[float] = None
    acconto: float = Field(default=0)
    totale_versato: float = Field(default=0)
    stato_pagamento: str = Field(default="PENDENTE")
    note: Optional[str] = None
    chiuso: bool = Field(default=False)
    rinnovo_di: Optional[int] = Field(default=None, foreign_key="contratti.id", index=True)
    deleted_at: Optional[datetime] = None

    # Esito rinnovo (SPEC_RINNOVI_SCADUTI §5 / ADR-015): null = opportunità di recupero aperta;
    # valorizzato = "non rinnova" (cliente perso) con motivo. Reversibile (set a null = riapre).
    esito_rinnovo_motivo: Optional[str] = Field(default=None, index=True)
    esito_rinnovo_note: Optional[str] = None
    esito_rinnovo_il: Optional[date] = None

    # Terminazione anticipata (SPEC_G7.0 / IMPL_PLAN §4.1 — G7). Colonne PLAIN, mai FK (pitfall #15),
    # gemelle di esito_rinnovo_motivo. Strada B: il LORDO (prezzo_totale/totale_versato) è immutabile,
    # il netto si DERIVA (netto_incassato = totale_versato − totale_rimborsato). totale_rimborsato parte da 0
    # e cresce soltanto; quota_stornata NON è strettamente monotòna (vedi inline). NB G7.0: residuo() NON le
    # legge ancora (è G7.1).
    totale_rimborsato: float = Field(default=0)   # LORDO rimborsi (monotòno); netto = versato − questo
    # Write-off che azzera il residuo senza riscrivere il prezzo. NON monotòna: reopen la azzera
    # (ADR-019); l'incasso differito la riduce (Reperto #1 G9.0). G9.2b: PROIEZIONE di Σ rettifiche;
    # scrittura runtime via ledger.post_adjustment + backfill boot idempotente per il legacy pre-penna.
    quota_stornata: float = Field(default=0)
    data_chiusura: Optional[date] = None          # quando la chiusura ha effetto (qualsiasi via a CHIUSO)
    # esito economico, enum chiuso a 4: COMPLETAMENTO|CONSUNZIONE|TERMINAZIONE_RIMBORSO|TERMINAZIONE_DECADENZA.
    # NULL = legacy (chiusi pre-G7) = COMPLETAMENTO implicito in classificazione, mai riaperto auto.
    motivo_chiusura: Optional[str] = Field(default=None, index=True)

    # Relationships (lazy-loaded, non incluse in JSON di default)
    rates: List["Rate"] = Relationship(back_populates="contract")
    movements: List["CashMovement"] = Relationship(back_populates="contract")
