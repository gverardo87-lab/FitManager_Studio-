"""add_termination_fields_to_contratti

Revision ID: d83abb993ea8
Revises: b2f1a9c7d4e3
Create Date: 2026-06-24 00:37:09.356899

Terminazione anticipata (SPEC_G7.0 / IMPL_PLAN_FINANCIAL_REALIGN §4.1 — G7). 4 colonne PLAIN
su contratti (mai FK, pitfall #15). Strada B: il LORDO è immutabile, il netto si deriva.
NB: schema_sync aggiunge comunque queste colonne (+ indice ix_contratti_motivo_chiusura,
CREATE INDEX IF NOT EXISTS → idempotente con questa) al boot sui DB deployati/frozen; questa
migrazione è il record formale Alembic per crm.db.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'd83abb993ea8'
down_revision: Union[str, Sequence[str], None] = 'b2f1a9c7d4e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aggiunge totale_rimborsato/quota_stornata/data_chiusura/motivo_chiusura a contratti."""
    with op.batch_alter_table('contratti', schema=None) as batch_op:
        # Float NOT NULL con server_default '0' → le righe esistenti vengono backfillate a 0
        # (gemello della logica _resolve_default di schema_sync: DEFAULT 0 per i float non-nullable).
        batch_op.add_column(sa.Column('totale_rimborsato', sa.Float(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('quota_stornata', sa.Float(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('data_chiusura', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('motivo_chiusura', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.create_index('ix_contratti_motivo_chiusura', ['motivo_chiusura'], unique=False)


def downgrade() -> None:
    """Rimuove i 4 campi di terminazione."""
    with op.batch_alter_table('contratti', schema=None) as batch_op:
        batch_op.drop_index('ix_contratti_motivo_chiusura')
        batch_op.drop_column('motivo_chiusura')
        batch_op.drop_column('data_chiusura')
        batch_op.drop_column('quota_stornata')
        batch_op.drop_column('totale_rimborsato')
