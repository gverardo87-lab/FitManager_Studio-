"""add_workout_log_feedback_fields

Revision ID: f41a3dcede95
Revises: a7d48af4b62d
Create Date: 2026-03-29 07:42:15.931850

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'f41a3dcede95'
down_revision: Union[str, Sequence[str], None] = 'a7d48af4b62d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aggiunge 6 campi feedback sessione a allenamenti_eseguiti."""
    with op.batch_alter_table('allenamenti_eseguiti', schema=None) as batch_op:
        batch_op.add_column(sa.Column('durata_effettiva_min', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('energia_pre', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('energia_post', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('soddisfazione', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('difficolta_percepita', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('source', sqlmodel.sql.sqltypes.AutoString(), nullable=True))


def downgrade() -> None:
    """Rimuove i 6 campi feedback."""
    with op.batch_alter_table('allenamenti_eseguiti', schema=None) as batch_op:
        batch_op.drop_column('source')
        batch_op.drop_column('difficolta_percepita')
        batch_op.drop_column('soddisfazione')
        batch_op.drop_column('energia_post')
        batch_op.drop_column('energia_pre')
        batch_op.drop_column('durata_effettiva_min')
