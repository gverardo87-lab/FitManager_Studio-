# api/models/rettifica_contratto.py
"""
Modello RettificaContratto — ledger separato delle rettifiche non-cash (G9.2b, ADR-022 Addendum I).

`quota_stornata` (write-off che azzera il residuo senza riscrivere il prezzo) era l'ultima grandezza del
contratto SENZA posting: scritta a mano in 3 siti (terminate/reopen/incassa credito differito), era una
verità-parallela non derivabile. Lo storno è NON-CASH (nessun euro si muove) → NON entra nel mastro cassa
`movimenti_cassa` (riaprirebbe la superficie di esclusione scartata da ADR-019: categoria-storno da
filtrare in ogni aggregato). Ledger dedicato, append-only:

    quota_stornata == Σ importo[rettifiche_contratto]     (importo FIRMATO: + storno, − reversal)

La colonna diventa una PROIEZIONE verificabile del Σ, come `totale_versato` lo è di Σ ENTRATA (I5).
Scrittura SOLO via la terza penna `ledger.post_adjustment` (gemello non-cash di post_inflow/post_outflow).

Sotto-libro del CONTRATTO: niente `id_cliente` (DEC-3 — derivabile via JOIN, una colonna ridondante
sarebbe una verità-parallela dentro l'ADR che le vieta); `trainer_id` resta (frontiera tenant-isolation).
FK verso tabelle business crm.db (mai catalog/nutrition, pitfall #15).
"""

from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel, Field

# Causali ammesse (SSoT, fail-loud in post_adjustment — parità con CONTRACT_CASH_IN/OUT della penna cassa)
CAUSALE_STORNO_TERMINAZIONE = "STORNO_TERMINAZIONE"            # terminate: +Δ porta residuo() a 0 (gamba E)
CAUSALE_REVERSAL_REOPEN = "REVERSAL_REOPEN"                    # reopen: −quota (azzera lo storno, ADR-019)
CAUSALE_REVERSAL_INCASSO_DIFFERITO = "REVERSAL_INCASSO_DIFFERITO"  # incasso credito differito: −importo (Reperto #1)
CAUSALE_BACKFILL_LEGACY = "BACKFILL_LEGACY"                    # backfill boot: quota legacy pre-G9.2b → 1 riga

CAUSALI_RETTIFICA = frozenset({
    CAUSALE_STORNO_TERMINAZIONE,
    CAUSALE_REVERSAL_REOPEN,
    CAUSALE_REVERSAL_INCASSO_DIFFERITO,
    CAUSALE_BACKFILL_LEGACY,
})


class RettificaContratto(SQLModel, table=True):
    __tablename__ = "rettifiche_contratto"

    id: Optional[int] = Field(default=None, primary_key=True)
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    id_contratto: int = Field(foreign_key="contratti.id", index=True)
    importo: float                                     # FIRMATO: + storno, − reversal (append-only, mai UPDATE)
    causale: str                                       # ∈ CAUSALI_RETTIFICA (validata dalla penna)
    data_effettiva: date
    note: Optional[str] = None
    deleted_at: Optional[datetime] = None
