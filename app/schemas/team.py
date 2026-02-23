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
    name: str = Field(..., min_length=1, max_length=100, description="Team name")
    country_id: UUID = Field(..., description="UUID of the country this team represents")

    model_config = {
        "json_schema_extra": {
            "examples": [{"name": "Knights of Valor", "country_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}]
        }
    }


class TeamUpdate(BaseModel):
    """
    Schema for updating an existing team.

    Attributes:
        name: Optional team name (1-100 characters)
        country_id: Optional UUID of the associated country
    """
    name: str | None = Field(None, min_length=1, max_length=100, description="Updated team name")
    country_id: UUID | None = Field(None, description="UUID of the new country (for transfers)")


class TeamResponse(BaseModel):
    """
    Schema for team response (without nested country).

    Attributes:
        id: Team UUID
        name: Team name
        country_id: UUID of the associated country
        created_at: Timestamp of creation
    """
    id: UUID = Field(..., description="Team UUID")
    name: str = Field(..., description="Team name")
    country_id: UUID = Field(..., description="UUID of the associated country")
    created_at: datetime = Field(..., description="Timestamp of record creation")

    model_config = {
        "from_attributes": True
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
    id: UUID = Field(..., description="Team UUID")
    name: str = Field(..., description="Team name")
    country: CountryResponse = Field(..., description="Country this team belongs to")
    created_at: datetime = Field(..., description="Timestamp of record creation")

    model_config = {
        "from_attributes": True
    }
