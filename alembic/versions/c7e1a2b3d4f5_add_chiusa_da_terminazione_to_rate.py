"""add_chiusa_da_terminazione_to_rate_programmate

Revision ID: c7e1a2b3d4f5
Revises: d83abb993ea8
Create Date: 2026-06-26

M1 (G7.7 remediation audit). Marker per il `reopen` inverso esatto: `terminate` soft-elimina solo le
rate non-saldate e ora le MARCA (`chiusa_da_terminazione=1`); `reopen` ripristina SOLO le marcate, non
ogni rata con `deleted_at` (cancellazioni manuali / piano rigenerato verrebbero resuscitate — il bug M1).
Colonna PLAIN bool NOT NULL server_default '0' → le righe esistenti vengono backfillate a 0 (False).
NB: schema_sync aggiunge comunque questa colonna al boot sui DB deployati/frozen (column-sync generico,
DEFAULT 0 per il bool non-nullable); questa migrazione è il record formale Alembic per crm.db.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7e1a2b3d4f5'
down_revision: Union[str, Sequence[str], None] = 'd83abb993ea8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aggiunge chiusa_da_terminazione a rate_programmate (bool NOT NULL default 0)."""
    with op.batch_alter_table('rate_programmate', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('chiusa_da_terminazione', sa.Boolean(), nullable=False, server_default='0')
        )


def downgrade() -> None:
    """Rimuove il marker."""
    with op.batch_alter_table('rate_programmate', schema=None) as batch_op:
        batch_op.drop_column('chiusa_da_terminazione')
