"""Create fights table with soft delete and notes

Revision ID: f1a2b3c4d5e6
Revises: a1b2c3d4e5f6
Create Date: 2026-01-12 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create fights table with soft delete support and notes field."""
    op.create_table(
        'fights',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('location', sa.String(length=200), nullable=False),
        sa.Column('video_url', sa.String(length=500), nullable=True),
        sa.Column('winner_side', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_deactivated', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # Create check constraint for winner_side
    op.create_check_constraint(
        'ck_fights_winner_side',
        'fights',
        'winner_side IS NULL OR winner_side IN (1, 2)'
    )

    # Create indexes for optimization
    op.create_index('ix_fights_date', 'fights', ['date'])
    op.create_index('ix_fights_is_deactivated', 'fights', ['is_deactivated'])


def downgrade() -> None:
    """Drop fights table."""
    op.drop_index('ix_fights_is_deactivated', table_name='fights')
    op.drop_index('ix_fights_date', table_name='fights')
    op.drop_constraint('ck_fights_winner_side', 'fights', type_='check')
    op.drop_table('fights')
