"""
Pydantic schemas for Fight entity.

Defines request and response schemas for Fight API operations.
"""

import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Date
from app.schemas.tag_schema import TagResponse


class ParticipationCreate(BaseModel):
    """
    Schema for creating a fight participation.

    Attributes:
        fighter_id: UUID of the fighter
        side: Side assignment (1 or 2)
        role: Role in the fight (fighter, captain, alternate, coach)
    """
    fighter_id: UUID = Field(..., description="UUID of the participating fighter")
    side: int = Field(..., ge=1, le=2, description="Side assignment (1 or 2)")
    role: str = Field(default="fighter", description="Role in the fight: fighter, captain, alternate, or coach")

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate that role is valid."""
        valid_roles = {"fighter", "captain", "alternate", "coach"}
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [{"fighter_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "side": 1, "role": "fighter"}]
        }
    }


class ParticipationResponse(BaseModel):
    """
    Schema for participation response.

    Attributes:
        id: Participation UUID
        fight_id: Fight UUID
        fighter_id: Fighter UUID
        side: Side assignment (1 or 2)
        role: Role in the fight
        created_at: Timestamp of creation
    """
    id: UUID = Field(..., description="Participation UUID")
    fight_id: UUID = Field(..., description="UUID of the fight")
    fighter_id: UUID = Field(..., description="UUID of the fighter")
    side: int = Field(..., description="Side assignment (1 or 2)")
    role: str = Field(..., description="Role in the fight")
    created_at: datetime.datetime = Field(..., description="Timestamp of record creation")

    model_config = {
        "from_attributes": True
    }


class FightCreate(BaseModel):
    """
    Schema for creating a new fight.

    Attributes:
        date: Date of the fight (not in future)
        location: Location/event name (1-200 characters)
        fight_format: Format of the fight (singles or melee)
        video_url: Optional URL to fight video
        winner_side: Optional winner (1 or 2, None for draw/unknown)
        notes: Optional notes about the fight
        participations: Optional list of participations
    """
    date: datetime.date = Field(..., description="Date of the fight (cannot be in the future)")
    location: str = Field(..., min_length=1, max_length=200, description="Event name or location")
    supercategory: str = Field(..., pattern="^(singles|melee)$", description="Supercategory: 'singles' or 'melee'")
    video_url: str | None = Field(None, max_length=500, description="URL to fight video recording")
    winner_side: int | None = Field(None, description="Winning side (1, 2, or null for draw/unknown)")
    notes: str | None = Field(None, description="Additional notes about the fight")
    participations: Optional[list[ParticipationCreate]] = Field(None, description="List of fighter participations")

    @field_validator('winner_side')
    @classmethod
    def validate_winner_side(cls, v: int | None) -> int | None:
        """Validate that winner_side is 1, 2, or None."""
        if v is not None and v not in (1, 2):
            raise ValueError('Winner side must be 1, 2, or null')
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "date": "2025-06-15",
                "location": "Battle of the Nations 2025",
                "supercategory": "melee",
                "video_url": "https://example.com/fight-video",
                "winner_side": 1,
                "notes": "Semi-final round"
            }]
        }
    }


class TagAddRequest(BaseModel):
    """
    Schema for adding a tag to a fight via POST /fights/{id}/tags.

    Attributes:
        tag_type_name: Name of the tag type (supercategory, category, gender, custom)
        value: Tag value (validated per type)
        parent_tag_id: Optional parent tag UUID (for hierarchy)
    """
    tag_type_name: str = Field(
        ..., min_length=1, max_length=50, description="Tag type name"
    )
    value: str = Field(
        ..., min_length=1, max_length=200, description="Tag value"
    )
    parent_tag_id: Optional[UUID] = Field(
        None, description="Optional parent tag UUID"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"tag_type_name": "category", "value": "duel"}]
        }
    }


class TagUpdateRequest(BaseModel):
    """
    Schema for updating a tag's value via PATCH /fights/{id}/tags/{tag_id}.

    Attributes:
        value: New tag value
    """
    value: str = Field(..., min_length=1, max_length=200, description="New tag value")

    model_config = {
        "json_schema_extra": {
            "examples": [{"value": "profight"}]
        }
    }


class FightUpdate(BaseModel):
    """
    Schema for updating an existing fight.

    Attributes:
        date: Optional new date
        location: Optional new location
        video_url: Optional new video URL
        winner_side: Optional new winner
        notes: Optional new notes
    """
    date: datetime.date | None = Field(None, description="Updated fight date (cannot be in the future)")
    location: str | None = Field(None, min_length=1, max_length=200, description="Updated event name or location")
    video_url: str | None = Field(None, max_length=500, description="Updated video URL")
    winner_side: int | None = Field(None, description="Updated winning side (1, 2, or null)")
    notes: str | None = Field(None, description="Updated notes")

    @field_validator('winner_side')
    @classmethod
    def validate_winner_side(cls, v: int | None) -> int | None:
        """Validate that winner_side is 1, 2, or None."""
        if v is not None and v not in (1, 2):
            raise ValueError('Winner side must be 1, 2, or null')
        return v


class FightResponse(BaseModel):
    """
    Schema for fight response.

    Attributes:
        id: Fight UUID
        date: Date of the fight
        location: Location/event name
        video_url: URL to fight video (if any)
        winner_side: Which side won (1, 2, or None)
        notes: Optional notes about the fight
        is_deactivated: Soft delete flag
        created_at: Timestamp of creation
        participations: List of participations (if loaded)
    """
    id: UUID = Field(..., description="Fight UUID")
    date: datetime.date = Field(..., description="Date of the fight")
    location: str = Field(..., description="Event name or location")
    video_url: str | None = Field(None, description="URL to fight video recording")
    winner_side: int | None = Field(None, description="Winning side (1, 2, or null for draw/unknown)")
    notes: str | None = Field(None, description="Additional notes about the fight")
    is_deactivated: bool = Field(..., description="Whether this record has been soft-deleted")
    created_at: datetime.datetime = Field(..., description="Timestamp of record creation")
    participations: Optional[list[ParticipationResponse]] = Field(None, description="List of fighter participations")
    tags: list[TagResponse] = Field(default_factory=list, description="Tags associated with this fight")

    model_config = {
        "from_attributes": True
    }
