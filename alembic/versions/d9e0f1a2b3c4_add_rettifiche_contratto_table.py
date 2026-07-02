"""add_rettifiche_contratto_table

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
Create Date: 2026-07-02

G9.2b (ADR-022 Addendum I, Opzione A) — ledger separato delle rettifiche non-cash. `quota_stornata` era
l'ultima grandezza senza posting (scritta a mano in 3 siti: terminate/reopen/incassa credito differito).
Lo storno è NON-CASH → NON entra in `movimenti_cassa` (riaprirebbe la superficie di esclusione scartata
da ADR-019). Nuova tabella append-only `rettifiche_contratto` (importo FIRMATO: + storno, − reversal):
`quota_stornata == Σ importo[rettifiche_contratto]` — la colonna diventa una proiezione verificabile,
come `totale_versato` lo è di Σ ENTRATA (I5). Scrittura solo via `ledger.post_adjustment` (terza penna).

NB: essendo una TABELLA NUOVA, `create_db_and_tables()` (SQLModel.metadata.create_all, idempotente) la
crea al boot su TUTTI i DB business — inclusi i deployati/frozen (alembic_version congelato). Questa
migrazione è il record formale Alembic per crm.db.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9e0f1a2b3c4'
down_revision: Union[str, Sequence[str], None] = 'c8d9e0f1a2b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'rettifiche_contratto',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trainer_id', sa.Integer(), nullable=False),
        sa.Column('id_contratto', sa.Integer(), nullable=False),
        sa.Column('importo', sa.Float(), nullable=False),
        sa.Column('causale', sa.String(), nullable=False),
        sa.Column('data_effettiva', sa.Date(), nullable=False),
        sa.Column('note', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainers.id']),
        sa.ForeignKeyConstraint(['id_contratto'], ['contratti.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_rettifiche_contratto_trainer_id', 'rettifiche_contratto', ['trainer_id'])
    op.create_index('ix_rettifiche_contratto_id_contratto', 'rettifiche_contratto', ['id_contratto'])


def downgrade() -> None:
    op.drop_index('ix_rettifiche_contratto_id_contratto', table_name='rettifiche_contratto')
    op.drop_index('ix_rettifiche_contratto_trainer_id', table_name='rettifiche_contratto')
    op.drop_table('rettifiche_contratto')
