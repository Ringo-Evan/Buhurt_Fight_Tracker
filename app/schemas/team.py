"""
Pydantic schemas for Team entity.

Defines request and response schemas for Team API operations.
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.schemas.country import CountryResponse


class TeamCreate(BaseModel):
    """
    Schema for creating a new team.

    Attributes:
        name: Team name (1-100 characters)
        country_id: UUID of the associated country
    """
    name: str = Field(..., min_length=1, max_length=100)
    country_id: UUID


class TeamUpdate(BaseModel):
    """
    Schema for updating an existing team.

    Attributes:
        name: Optional team name (1-100 characters)
        country_id: Optional UUID of the associated country
    """
    name: str | None = Field(None, min_length=1, max_length=100)
    country_id: UUID | None = None


class TeamResponse(BaseModel):
    """
    Schema for team response (without nested country).

    Attributes:
        id: Team UUID
        name: Team name
        country_id: UUID of the associated country
        created_at: Timestamp of creation
    """
    id: UUID
    name: str
    country_id: UUID
    created_at: datetime

    model_config = {
        "from_attributes": True  # Enable ORM mode for SQLAlchemy compatibility
    }


class TeamWithCountryResponse(BaseModel):
    """
    Schema for team response with nested country details.

    Attributes:
        id: Team UUID
        name: Team name
        country: Nested country object
        created_at: Timestamp of creation
    """
    id: UUID
    name: str
    country: CountryResponse
    created_at: datetime

    model_config = {
        "from_attributes": True  # Enable ORM mode for SQLAlchemy compatibility
    }
