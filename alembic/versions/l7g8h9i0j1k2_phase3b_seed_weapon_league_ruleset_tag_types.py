"""Phase 3B: Seed weapon, league, ruleset TagTypes

Revision ID: l7g8h9i0j1k2
Revises: k6f7g8h9i0j1
Create Date: 2026-02-23 00:00:00.000000

Changes:
- Seeds weapon, league, ruleset TagTypes (Phase 3B - DD-014 through DD-021)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'l7g8h9i0j1k2'
down_revision: Union[str, None] = 'k6f7g8h9i0j1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed UUIDs for new TagTypes (referential consistency across environments)
WEAPON_TAG_TYPE_ID = '00000000-0000-0000-0000-000000000007'
LEAGUE_TAG_TYPE_ID = '00000000-0000-0000-0000-000000000008'
RULESET_TAG_TYPE_ID = '00000000-0000-0000-0000-000000000009'


def upgrade() -> None:
    # Seed weapon, league, ruleset TagTypes (Phase 3B)
    op.execute(
        sa.text("""
            INSERT INTO tag_types (id, name, is_privileged, is_parent, has_children, display_order, is_deactivated, created_at)
            VALUES
                (:weapon_id,  'weapon',  true,  false, false, 4, false, NOW()),
                (:league_id,  'league',  true,  false, false, 5, false, NOW()),
                (:ruleset_id, 'ruleset', true,  false, false, 6, false, NOW())
        """).bindparams(
            weapon_id=WEAPON_TAG_TYPE_ID,
            league_id=LEAGUE_TAG_TYPE_ID,
            ruleset_id=RULESET_TAG_TYPE_ID,
        )
    )


def downgrade() -> None:
    # Remove seeded TagTypes
    op.execute(
        sa.text("DELETE FROM tag_types WHERE id IN (:wpn, :lge, :rls)").bindparams(
            wpn=WEAPON_TAG_TYPE_ID,
            lge=LEAGUE_TAG_TYPE_ID,
            rls=RULESET_TAG_TYPE_ID,
        )
    )
