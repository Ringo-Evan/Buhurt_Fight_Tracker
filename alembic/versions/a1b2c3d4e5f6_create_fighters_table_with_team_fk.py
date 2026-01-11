"""Create fighters table with team FK

Revision ID: a1b2c3d4e5f6
Revises: 6dc2dfcfcaa5
Create Date: 2026-01-11 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '6dc2dfcfcaa5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create fighters table with foreign key to teams."""
    op.create_table(
        'fighters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Create foreign key constraint to teams table
    op.create_foreign_key(
        'fk_fighters_team_id',
        'fighters', 'teams',
        ['team_id'], ['id'],
        onupdate='CASCADE',
        ondelete='RESTRICT'
    )

    # Create indexes for optimization
    op.create_index('ix_fighters_team_id', 'fighters', ['team_id'])
    op.create_index('ix_fighters_is_deleted', 'fighters', ['is_deleted'])


def downgrade() -> None:
    """Drop fighters table."""
    op.drop_index('ix_fighters_is_deleted', table_name='fighters')
    op.drop_index('ix_fighters_team_id', table_name='fighters')
    op.drop_constraint('fk_fighters_team_id', 'fighters', type_='foreignkey')
    op.drop_table('fighters')
