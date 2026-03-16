"""add workout_schedule table

Revision ID: e032e783a2e8
Revises: b7c8d9e0f1a2
Create Date: 2026-03-16 11:40:00.309296

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e032e783a2e8'
down_revision: Union[str, Sequence[str], None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea tabella workout_schedule per pianificazione calendario sessioni."""
    op.create_table(
        'workout_schedule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_scheda', sa.Integer(), nullable=False),
        sa.Column('id_sessione', sa.Integer(), nullable=False),
        sa.Column('id_cliente', sa.Integer(), nullable=False),
        sa.Column('trainer_id', sa.Integer(), nullable=False),
        sa.Column('data_pianificata', sa.Date(), nullable=False),
        sa.Column('stato', sa.String(), server_default='pianificato', nullable=False),
        sa.Column('id_log', sa.Integer(), nullable=True),
        sa.Column('note', sa.String(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['id_scheda'], ['schede_allenamento.id']),
        sa.ForeignKeyConstraint(['id_sessione'], ['sessioni_scheda.id']),
        sa.ForeignKeyConstraint(['id_cliente'], ['clienti.id']),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainers.id']),
        sa.ForeignKeyConstraint(['id_log'], ['allenamenti_eseguiti.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('workout_schedule', schema=None) as batch_op:
        batch_op.create_index('ix_workout_schedule_id_scheda', ['id_scheda'])
        batch_op.create_index('ix_workout_schedule_id_sessione', ['id_sessione'])
        batch_op.create_index('ix_workout_schedule_id_cliente', ['id_cliente'])
        batch_op.create_index('ix_workout_schedule_trainer_id', ['trainer_id'])
        batch_op.create_index('ix_workout_schedule_data', ['data_pianificata'])


def downgrade() -> None:
    """Rimuove tabella workout_schedule."""
    op.drop_table('workout_schedule')
