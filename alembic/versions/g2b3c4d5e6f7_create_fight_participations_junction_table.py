"""Create fight_participations junction table

Revision ID: g2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-01-12 16:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'g2b3c4d5e6f7'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create fight_participations junction table linking fighters to fights."""
    op.create_table(
        'fight_participations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('fight_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fighter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('side', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='fighter'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # Create foreign key constraint to fights table (CASCADE on delete)
    op.create_foreign_key(
        'fk_fight_participations_fight_id',
        'fight_participations', 'fights',
        ['fight_id'], ['id'],
        onupdate='CASCADE',
        ondelete='CASCADE'
    )

    # Create foreign key constraint to fighters table (RESTRICT on delete)
    op.create_foreign_key(
        'fk_fight_participations_fighter_id',
        'fight_participations', 'fighters',
        ['fighter_id'], ['id'],
        onupdate='CASCADE',
        ondelete='RESTRICT'
    )

    # Create unique constraint to prevent duplicate fighter in same fight
    op.create_unique_constraint(
        'uq_fight_fighter',
        'fight_participations',
        ['fight_id', 'fighter_id']
    )

    # Create check constraints
    op.create_check_constraint(
        'ck_fight_participations_side',
        'fight_participations',
        'side IN (1, 2)'
    )

    op.create_check_constraint(
        'ck_fight_participations_role',
        'fight_participations',
        "role IN ('fighter', 'captain', 'alternate', 'coach')"
    )

    # Create indexes for optimization
    op.create_index('ix_fight_participations_fight_id', 'fight_participations', ['fight_id'])
    op.create_index('ix_fight_participations_fighter_id', 'fight_participations', ['fighter_id'])


def downgrade() -> None:
    """Drop fight_participations table."""
    op.drop_index('ix_fight_participations_fighter_id', table_name='fight_participations')
    op.drop_index('ix_fight_participations_fight_id', table_name='fight_participations')
    op.drop_constraint('ck_fight_participations_role', 'fight_participations', type_='check')
    op.drop_constraint('ck_fight_participations_side', 'fight_participations', type_='check')
    op.drop_constraint('uq_fight_fighter', 'fight_participations', type_='unique')
    op.drop_constraint('fk_fight_participations_fighter_id', 'fight_participations', type_='foreignkey')
    op.drop_constraint('fk_fight_participations_fight_id', 'fight_participations', type_='foreignkey')
    op.drop_table('fight_participations')
