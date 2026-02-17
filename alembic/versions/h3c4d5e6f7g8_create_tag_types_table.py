"""Create tag_types table

Revision ID: h3c4d5e6f7g8
Revises: g2b3c4d5e6f7
Create Date: 2026-01-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'h3c4d5e6f7g8'
down_revision: Union[str, None] = 'g2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tag_types reference table."""
    op.create_table(
        'tag_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('is_privileged', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_parent', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('has_children', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_deactivated', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # Create unique constraint for name
    op.create_unique_constraint(
        'uq_tag_types_name',
        'tag_types',
        ['name']
    )

    # Create index for soft delete filtering
    op.create_index('ix_tag_types_is_deactivated', 'tag_types', ['is_deactivated'])


def downgrade() -> None:
    """Drop tag_types table."""
    op.drop_index('ix_tag_types_is_deactivated', table_name='tag_types')
    op.drop_constraint('uq_tag_types_name', 'tag_types', type_='unique')
    op.drop_table('tag_types')
