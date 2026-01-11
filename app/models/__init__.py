"""
SQLAlchemy ORM models for Buhurt Fight Tracker.

Import all models in dependency order to ensure proper relationship resolution.
This prevents circular import issues and allows SQLAlchemy to properly configure
all relationships when metadata is created.

Import Order (bottom-up dependency chain):
1. Country (no dependencies)
2. Team (depends on Country)
3. Fighter (depends on Team, which depends on Country)

All models share the same Base metadata instance (defined in country.py).
"""

# Import Base first (defined in country module)
from app.models.country import Base, Country

# Import dependent models in order
from app.models.team import Team
from app.models.fighter import Fighter

# Export all models for convenient importing
__all__ = [
    "Base",
    "Country",
    "Team",
    "Fighter",
]
