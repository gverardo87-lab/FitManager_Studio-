"""add_exercise_logs_and_share_token_id_scheda

Revision ID: a7d48af4b62d
Revises: 05243b21aca1
Create Date: 2026-03-29 06:14:21.075817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'a7d48af4b62d'
down_revision: Union[str, Sequence[str], None] = '05243b21aca1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Nuova tabella exercise_logs — dati effettivi per-esercizio (client portal)
    op.create_table('exercise_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_schedule_slot', sa.Integer(), nullable=False),
        sa.Column('id_esercizio_sessione', sa.Integer(), nullable=False),
        sa.Column('trainer_id', sa.Integer(), nullable=False),
        sa.Column('id_cliente', sa.Integer(), nullable=False),
        sa.Column('serie_effettive', sa.Integer(), nullable=True),
        sa.Column('ripetizioni_effettive', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('carico_effettivo_kg', sa.Float(), nullable=True),
        sa.Column('rpe', sa.Float(), nullable=True),
        sa.Column('note_cliente', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('source', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('updated_at', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['id_cliente'], ['clienti.id'], ),
        sa.ForeignKeyConstraint(['id_esercizio_sessione'], ['esercizi_sessione.id'], ),
        sa.ForeignKeyConstraint(['id_schedule_slot'], ['workout_schedule.id'], ),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('exercise_logs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_exercise_logs_id_cliente'), ['id_cliente'], unique=False)
        batch_op.create_index(batch_op.f('ix_exercise_logs_id_esercizio_sessione'), ['id_esercizio_sessione'], unique=False)
        batch_op.create_index(batch_op.f('ix_exercise_logs_id_schedule_slot'), ['id_schedule_slot'], unique=False)
        batch_op.create_index(batch_op.f('ix_exercise_logs_trainer_id'), ['trainer_id'], unique=False)

    # 2. Nuovo campo id_scheda su share_tokens (FK a schede_allenamento, scope=workout)
    with op.batch_alter_table('share_tokens', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id_scheda', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_share_tokens_id_scheda',
            'schede_allenamento', ['id_scheda'], ['id']
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('share_tokens', schema=None) as batch_op:
        batch_op.drop_constraint('fk_share_tokens_id_scheda', type_='foreignkey')
        batch_op.drop_column('id_scheda')

    with op.batch_alter_table('exercise_logs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_exercise_logs_trainer_id'))
        batch_op.drop_index(batch_op.f('ix_exercise_logs_id_schedule_slot'))
        batch_op.drop_index(batch_op.f('ix_exercise_logs_id_esercizio_sessione'))
        batch_op.drop_index(batch_op.f('ix_exercise_logs_id_cliente'))

    op.drop_table('exercise_logs')
