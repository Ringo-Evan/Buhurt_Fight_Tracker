"""
Pydantic schemas for Fighter entity.

Defines request and response schemas for Fighter API operations.
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.schemas.team import TeamResponse, TeamWithCountryResponse


class FighterCreate(BaseModel):
    """
    Schema for creating a new fighter.

    Attributes:
        name: Fighter name (1-100 characters)
        team_id: UUID of the associated team
    """
    name: str = Field(..., min_length=1, max_length=100)
    team_id: UUID


class FighterUpdate(BaseModel):
    """
    Schema for updating an existing fighter.

    Attributes:
        name: Optional fighter name (1-100 characters)
        team_id: Optional UUID of the associated team (for transfers)
    """
    name: str | None = Field(None, min_length=1, max_length=100)
    team_id: UUID | None = None


class FighterResponse(BaseModel):
    """
    Schema for fighter response (without nested team).

    Attributes:
        id: Fighter UUID
        name: Fighter name
        team_id: UUID of the associated team
        created_at: Timestamp of creation
    """
    id: UUID
    name: str
    team_id: UUID
    created_at: datetime

    model_config = {
        "from_attributes": True  # Enable ORM mode for SQLAlchemy compatibility
    }


class FighterWithTeamResponse(BaseModel):
    """
    Schema for fighter response with nested team (but not country).

    Attributes:
        id: Fighter UUID
        name: Fighter name
        team: Nested team object (without country)
        created_at: Timestamp of creation
    """
    id: UUID
    name: str
    team: TeamResponse
    created_at: datetime

    model_config = {
        "from_attributes": True  # Enable ORM mode for SQLAlchemy compatibility
    }


class FighterFullResponse(BaseModel):
    """
    Schema for fighter response with full hierarchy (team with country).

    Attributes:
        id: Fighter UUID
        name: Fighter name
        team: Nested team object with country
        created_at: Timestamp of creation
    """
    id: UUID
    name: str
    team: TeamWithCountryResponse
    created_at: datetime

    model_config = {
        "from_attributes": True  # Enable ORM mode for SQLAlchemy compatibility
    }
