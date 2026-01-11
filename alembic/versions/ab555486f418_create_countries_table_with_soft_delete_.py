"""Create countries table with soft delete support

Revision ID: ab555486f418
Revises: 
Create Date: 2026-01-10 17:47:14.642605

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision: str = 'ab555486f418'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create countries table with soft delete support."""
    op.create_table(
        'countries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=3), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # Create unique constraint and index on code
    op.create_unique_constraint('uq_countries_code', 'countries', ['code'])
    op.create_index('ix_countries_code', 'countries', ['code'])


def downgrade() -> None:
    """Drop countries table."""
    op.drop_index('ix_countries_code', table_name='countries')
    op.drop_constraint('uq_countries_code', 'countries', type_='unique')
    op.drop_table('countries')
