"""Phase 3 tag setup: fight_id NOT NULL, rename supercategory, seed tag types

Revision ID: k6f7g8h9i0j1
Revises: j5e6f7g8h9i0
Create Date: 2026-02-19 00:00:00.000000

Changes:
- tags.fight_id becomes NOT NULL (was nullable during Phase 2 development)
- Renames fight_format TagType to supercategory (DD-007)
- Seeds category, gender, custom TagTypes (DD-010)
"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision: str = 'k6f7g8h9i0j1'
down_revision: Union[str, None] = 'j5e6f7g8h9i0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed UUIDs for new TagTypes (referential consistency across environments)
CATEGORY_TAG_TYPE_ID = '00000000-0000-0000-0000-000000000004'
GENDER_TAG_TYPE_ID = '00000000-0000-0000-0000-000000000005'
CUSTOM_TAG_TYPE_ID = '00000000-0000-0000-0000-000000000006'


def upgrade() -> None:
    # 1. Make tags.fight_id NOT NULL
    op.alter_column('tags', 'fight_id', nullable=False)

    # 2. Rename fight_format -> supercategory (DD-007)
    op.execute(
        sa.text("UPDATE tag_types SET name = 'supercategory' WHERE name = 'fight_format'")
    )

    # 3. Seed category, gender, custom TagTypes (DD-010)
    op.execute(
        sa.text("""
            INSERT INTO tag_types (id, name, is_privileged, is_parent, has_children, display_order, is_deactivated, created_at)
            VALUES
                (:category_id, 'category',    true,  false, false, 1, false, NOW()),
                (:gender_id,   'gender',       false, false, false, 2, false, NOW()),
                (:custom_id,   'custom',       false, false, false, 3, false, NOW())
        """).bindparams(
            category_id=CATEGORY_TAG_TYPE_ID,
            gender_id=GENDER_TAG_TYPE_ID,
            custom_id=CUSTOM_TAG_TYPE_ID,
        )
    )


def downgrade() -> None:
    # Remove seeded TagTypes
    op.execute(
        sa.text("DELETE FROM tag_types WHERE id IN (:cat, :gen, :cus)").bindparams(
            cat=CATEGORY_TAG_TYPE_ID,
            gen=GENDER_TAG_TYPE_ID,
            cus=CUSTOM_TAG_TYPE_ID,
        )
    )

    # Rename supercategory back to fight_format
    op.execute(
        sa.text("UPDATE tag_types SET name = 'fight_format' WHERE name = 'supercategory'")
    )

    # Make tags.fight_id nullable again
    op.alter_column('tags', 'fight_id', nullable=True)
