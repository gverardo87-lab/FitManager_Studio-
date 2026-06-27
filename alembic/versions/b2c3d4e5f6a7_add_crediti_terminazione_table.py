"""add_crediti_terminazione_table

Revision ID: b2c3d4e5f6a7
Revises: c7e1a2b3d4f5
Create Date: 2026-06-27

G7.10 (ADR-018) — credito differito. Nuova tabella `crediti_terminazione`: il credito a favore del trainer
che SOPRAVVIVE alla chiusura del contratto (azione A_CREDITO della terminazione), tracciato FUORI da
`contract_state.residuo()` (mai una Rate viva su contratto chiuso). Receivable con lifecycle
APERTO/SALDATO/ANNULLATO; l'incasso parziale genera `CashMovement` ENTRATA `INCASSO_CONGUAGLIO_CONTRATTO`.

NB: essendo una TABELLA NUOVA, `create_db_and_tables()` (SQLModel.metadata.create_all, idempotente) la crea
al boot su TUTTI i DB business — inclusi i deployati/frozen (alembic_version congelato). Questa migrazione è
il record formale Alembic per crm.db.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'c7e1a2b3d4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'crediti_terminazione',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trainer_id', sa.Integer(), nullable=False),
        sa.Column('id_contratto', sa.Integer(), nullable=False),
        sa.Column('id_cliente', sa.Integer(), nullable=False),
        sa.Column('importo', sa.Float(), nullable=False),
        sa.Column('importo_incassato', sa.Float(), nullable=False, server_default='0'),
        sa.Column('stato', sa.String(), nullable=False, server_default='APERTO'),
        sa.Column('data_creazione', sa.Date(), nullable=False),
        sa.Column('data_chiusura', sa.Date(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainers.id']),
        sa.ForeignKeyConstraint(['id_contratto'], ['contratti.id']),
        sa.ForeignKeyConstraint(['id_cliente'], ['clienti.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_crediti_terminazione_trainer_id', 'crediti_terminazione', ['trainer_id'])
    op.create_index('ix_crediti_terminazione_id_contratto', 'crediti_terminazione', ['id_contratto'])


def downgrade() -> None:
    op.drop_index('ix_crediti_terminazione_id_contratto', table_name='crediti_terminazione')
    op.drop_index('ix_crediti_terminazione_trainer_id', table_name='crediti_terminazione')
    op.drop_table('crediti_terminazione')
