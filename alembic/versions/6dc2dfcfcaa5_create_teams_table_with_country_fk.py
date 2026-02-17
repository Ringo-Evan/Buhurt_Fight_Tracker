"""Create teams table with country FK

Revision ID: 6dc2dfcfcaa5
Revises: ab555486f418
Create Date: 2026-01-10 18:42:12.259901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6dc2dfcfcaa5'
down_revision: Union[str, None] = 'ab555486f418'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create teams table with foreign key to countries."""
    op.create_table(
        'teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('country_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_deactivated', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # Create foreign key constraint to countries table
    op.create_foreign_key(
        'fk_teams_country_id',
        'teams', 'countries',
        ['country_id'], ['id'],
        onupdate='CASCADE',
        ondelete='RESTRICT'
    )

    # Create indexes for optimization
    op.create_index('ix_teams_country_id', 'teams', ['country_id'])
    op.create_index('ix_teams_is_deactivated', 'teams', ['is_deactivated'])


def downgrade() -> None:
    """Drop teams table."""
    op.drop_index('ix_teams_is_deactivated', table_name='teams')
    op.drop_index('ix_teams_country_id', table_name='teams')
    op.drop_constraint('fk_teams_country_id', 'teams', type_='foreignkey')
    op.drop_table('teams')
