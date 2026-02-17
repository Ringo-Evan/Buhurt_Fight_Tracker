"""Seed fight_format TagType with singles and melee values

Revision ID: j5e6f7g8h9i0
Revises: i4d5e6f7g8h9
Create Date: 2026-01-26 10:10:00.000000

This migration seeds the fight_format TagType which is required for all fights.
- singles: exactly 1 fighter per side
- melee: minimum 5 fighters per side
"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'j5e6f7g8h9i0'
down_revision: Union[str, None] = 'i4d5e6f7g8h9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed UUIDs for referential consistency
FIGHT_FORMAT_TAG_TYPE_ID = '00000000-0000-0000-0000-000000000001'
SINGLES_TAG_ID = '00000000-0000-0000-0000-000000000002'
MELEE_TAG_ID = '00000000-0000-0000-0000-000000000003'


def upgrade() -> None:
    """Seed fight_format TagType and its allowed values."""
    # Insert fight_format TagType
    op.execute(
        sa.text("""
            INSERT INTO tag_types (id, name, is_privileged, is_parent, has_children, display_order, is_deactivated, created_at)
            VALUES (
                :id,
                'fight_format',
                true,
                false,
                false,
                0,
                false,
                NOW()
            )
        """).bindparams(id=FIGHT_FORMAT_TAG_TYPE_ID)
    )


def downgrade() -> None:
    """Remove fight_format TagType and its values."""
    # Remove the fight_format TagType
    op.execute(
        sa.text("DELETE FROM tag_types WHERE id = :id").bindparams(id=FIGHT_FORMAT_TAG_TYPE_ID)
    )
