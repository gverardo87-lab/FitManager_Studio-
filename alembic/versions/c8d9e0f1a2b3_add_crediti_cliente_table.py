"""add_crediti_cliente_table

Revision ID: c8d9e0f1a2b3
Revises: b2c3d4e5f6a7
Create Date: 2026-06-28

G8.1 (ADR-020) — wallet del cliente. Nuova tabella `crediti_cliente`: il credito a favore del cliente che
SOPRAVVIVE alla terminazione (rimborso editabile parziale → il non-rimborsato va a wallet; in futuro anche
gli overpayment instradati da reopen, ADR-019). Tracciato FUORI da `contract_state.residuo()`, gemello lato
cliente di `crediti_terminazione`. Lifecycle APERTO/SALDATO/ANNULLATO; l'erogazione genera `CashMovement`
USCITA `RIMBORSO_CONTRATTO`.

NB: essendo una TABELLA NUOVA, `create_db_and_tables()` (SQLModel.metadata.create_all, idempotente) la crea
al boot su TUTTI i DB business — inclusi i deployati/frozen (alembic_version congelato). Questa migrazione è
il record formale Alembic per crm.db.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8d9e0f1a2b3'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'crediti_cliente',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trainer_id', sa.Integer(), nullable=False),
        sa.Column('id_cliente', sa.Integer(), nullable=False),
        sa.Column('importo', sa.Float(), nullable=False),
        sa.Column('importo_erogato', sa.Float(), nullable=False, server_default='0'),
        sa.Column('stato', sa.String(), nullable=False, server_default='APERTO'),
        sa.Column('causale', sa.String(), nullable=False, server_default='RIMBORSO_DIFFERITO'),
        sa.Column('id_contratto_origine', sa.Integer(), nullable=False),
        sa.Column('data_creazione', sa.Date(), nullable=False),
        sa.Column('data_chiusura', sa.Date(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainers.id']),
        sa.ForeignKeyConstraint(['id_cliente'], ['clienti.id']),
        sa.ForeignKeyConstraint(['id_contratto_origine'], ['contratti.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_crediti_cliente_trainer_id', 'crediti_cliente', ['trainer_id'])
    op.create_index('ix_crediti_cliente_id_cliente', 'crediti_cliente', ['id_cliente'])
    op.create_index('ix_crediti_cliente_id_contratto_origine', 'crediti_cliente', ['id_contratto_origine'])


def downgrade() -> None:
    op.drop_index('ix_crediti_cliente_id_contratto_origine', table_name='crediti_cliente')
    op.drop_index('ix_crediti_cliente_id_cliente', table_name='crediti_cliente')
    op.drop_index('ix_crediti_cliente_trainer_id', table_name='crediti_cliente')
    op.drop_table('crediti_cliente')
