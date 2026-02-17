"""Create tags table

Revision ID: i4d5e6f7g8h9
Revises: h3c4d5e6f7g8
Create Date: 2026-01-26 10:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'i4d5e6f7g8h9'
down_revision: Union[str, None] = 'h3c4d5e6f7g8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tags table with hierarchical support."""
    op.create_table(
        'tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('fight_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tag_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('value', sa.String(length=200), nullable=False),
        sa.Column('parent_tag_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # Create foreign key to fights table (nullable, with CASCADE/RESTRICT)
    op.create_foreign_key(
        'fk_tags_fight_id',
        'tags', 'fights',
        ['fight_id'], ['id'],
        onupdate='CASCADE',
        ondelete='RESTRICT'
    )

    # Create foreign key to tag_types table
    op.create_foreign_key(
        'fk_tags_tag_type_id',
        'tags', 'tag_types',
        ['tag_type_id'], ['id'],
        onupdate='CASCADE',
        ondelete='RESTRICT'
    )

    # Create self-referential foreign key for hierarchy
    op.create_foreign_key(
        'fk_tags_parent_tag_id',
        'tags', 'tags',
        ['parent_tag_id'], ['id'],
        onupdate='CASCADE',
        ondelete='SET NULL'
    )

    # Create indexes for optimization
    op.create_index('ix_tags_fight_id', 'tags', ['fight_id'])
    op.create_index('ix_tags_tag_type_id', 'tags', ['tag_type_id'])
    op.create_index('ix_tags_is_deleted', 'tags', ['is_deleted'])


def downgrade() -> None:
    """Drop tags table."""
    op.drop_index('ix_tags_is_deleted', table_name='tags')
    op.drop_index('ix_tags_tag_type_id', table_name='tags')
    op.drop_index('ix_tags_fight_id', table_name='tags')
    op.drop_constraint('fk_tags_parent_tag_id', 'tags', type_='foreignkey')
    op.drop_constraint('fk_tags_tag_type_id', 'tags', type_='foreignkey')
    op.drop_constraint('fk_tags_fight_id', 'tags', type_='foreignkey')
    op.drop_table('tags')
