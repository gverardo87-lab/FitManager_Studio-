"""add indirizzo and codice_fiscale to clienti

Revision ID: d33f906da6cb
Revises: e032e783a2e8
Create Date: 2026-03-17 19:41:58.604901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd33f906da6cb'
down_revision: Union[str, Sequence[str], None] = 'e032e783a2e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clienti", sa.Column("indirizzo", sa.Text(), nullable=True))
    op.add_column("clienti", sa.Column("codice_fiscale", sa.String(16), nullable=True))


def downgrade() -> None:
    op.drop_column("clienti", "codice_fiscale")
    op.drop_column("clienti", "indirizzo")
