"""add_esito_rinnovo_to_contratti

Revision ID: b2f1a9c7d4e3
Revises: f41a3dcede95
Create Date: 2026-06-20 00:00:00.000000

Stato "non rinnova" sui contratti (SPEC_RINNOVI_SCADUTI §5 / ADR-015).
Tre campi nullable: motivo (presenza = perso), note libere, data della decisione.
NB: schema_sync aggiunge comunque queste colonne al boot sui DB deployati/frozen;
questa migrazione è il record formale Alembic per crm.db.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'b2f1a9c7d4e3'
down_revision: Union[str, Sequence[str], None] = 'f41a3dcede95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aggiunge esito_rinnovo_motivo/note/il a contratti."""
    with op.batch_alter_table('contratti', schema=None) as batch_op:
        batch_op.add_column(sa.Column('esito_rinnovo_motivo', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.add_column(sa.Column('esito_rinnovo_note', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.add_column(sa.Column('esito_rinnovo_il', sa.Date(), nullable=True))
        batch_op.create_index('ix_contratti_esito_rinnovo_motivo', ['esito_rinnovo_motivo'], unique=False)


def downgrade() -> None:
    """Rimuove i campi esito rinnovo."""
    with op.batch_alter_table('contratti', schema=None) as batch_op:
        batch_op.drop_index('ix_contratti_esito_rinnovo_motivo')
        batch_op.drop_column('esito_rinnovo_il')
        batch_op.drop_column('esito_rinnovo_note')
        batch_op.drop_column('esito_rinnovo_motivo')
