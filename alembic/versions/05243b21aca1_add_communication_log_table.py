"""add communication_log table

Revision ID: 05243b21aca1
Revises: d33f906da6cb
Create Date: 2026-03-27 12:00:47.128401

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05243b21aca1'
down_revision: Union[str, Sequence[str], None] = 'd33f906da6cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea tabella communication_log per tracciare comunicazioni WhatsApp/tel/email."""
    op.create_table('communication_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trainer_id', sa.Integer(), nullable=False),
        sa.Column('id_cliente', sa.Integer(), nullable=False),
        sa.Column('canale', sa.String(), nullable=False),
        sa.Column('template_usato', sa.String(), nullable=True),
        sa.Column('anteprima', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['id_cliente'], ['clienti.id']),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainers.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_communication_log_id_cliente', 'communication_log', ['id_cliente'])
    op.create_index('ix_communication_log_trainer_id', 'communication_log', ['trainer_id'])


def downgrade() -> None:
    """Rimuove tabella communication_log."""
    op.drop_index('ix_communication_log_trainer_id', table_name='communication_log')
    op.drop_index('ix_communication_log_id_cliente', table_name='communication_log')
    op.drop_table('communication_log')
