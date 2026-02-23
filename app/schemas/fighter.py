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
    name: str = Field(..., min_length=1, max_length=100, description="Fighter name")
    team_id: UUID = Field(..., description="UUID of the team this fighter belongs to")

    model_config = {
        "json_schema_extra": {
            "examples": [{"name": "Ivan Petrov", "team_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}]
        }
    }


class FighterUpdate(BaseModel):
    """
    Schema for updating an existing fighter.

    Attributes:
        name: Optional fighter name (1-100 characters)
        team_id: Optional UUID of the associated team (for transfers)
    """
    name: str | None = Field(None, min_length=1, max_length=100, description="Updated fighter name")
    team_id: UUID | None = Field(None, description="UUID of the new team (for transfers)")


class FighterResponse(BaseModel):
    """
    Schema for fighter response (without nested team).

    Attributes:
        id: Fighter UUID
        name: Fighter name
        team_id: UUID of the associated team
        created_at: Timestamp of creation
    """
    id: UUID = Field(..., description="Fighter UUID")
    name: str = Field(..., description="Fighter name")
    team_id: UUID = Field(..., description="UUID of the associated team")
    created_at: datetime = Field(..., description="Timestamp of record creation")

    model_config = {
        "from_attributes": True
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
    id: UUID = Field(..., description="Fighter UUID")
    name: str = Field(..., description="Fighter name")
    team: TeamResponse = Field(..., description="Team this fighter belongs to")
    created_at: datetime = Field(..., description="Timestamp of record creation")

    model_config = {
        "from_attributes": True
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
    id: UUID = Field(..., description="Fighter UUID")
    name: str = Field(..., description="Fighter name")
    team: TeamWithCountryResponse = Field(..., description="Team with nested country details")
    created_at: datetime = Field(..., description="Timestamp of record creation")

    model_config = {
        "from_attributes": True
    }
