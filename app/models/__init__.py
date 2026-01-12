"""
SQLAlchemy ORM models for Buhurt Fight Tracker.

Import all models in dependency order to ensure proper relationship resolution.
This prevents circular import issues and allows SQLAlchemy to properly configure
all relationships when metadata is created.

Import Order (bottom-up dependency chain):
1. Country (no dependencies)
2. Team (depends on Country)
3. Fighter (depends on Team)
4. Fight (no dependencies on above, but referenced by participations/tags)
5. FightParticipation (depends on Fight, Fighter)
6. TagType (no dependencies)
7. Tag (depends on Fight, TagType)

All models share the same Base metadata instance (defined in country.py).
"""

# Import Base first (defined in country module)
from app.models.country import Base, Country

# Import dependent models in order
from app.models.team import Team
from app.models.fighter import Fighter
from app.models.fight import Fight
from app.models.fight_participation import FightParticipation, ParticipationRole
from app.models.tag_type import TagType
from app.models.tag import Tag
from app.models.tag_change_request import TagChangeRequest, RequestStatus
from app.models.vote import Vote

# Export all models for convenient importing
__all__ = [
    "Base",
    "Country",
    "Team",
    "Fighter",
    "Fight",
    "FightParticipation",
    "ParticipationRole",
    "TagType",
    "Tag",
    "TagChangeRequest",
    "RequestStatus",
    "Vote",
]
