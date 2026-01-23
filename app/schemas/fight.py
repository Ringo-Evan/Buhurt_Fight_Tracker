"""
Pydantic schemas for Fight entity.

Defines request and response schemas for Fight API operations.
"""

from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class FightCreate(BaseModel):
    """
    Schema for creating a new fight.

    Attributes:
        date: Date of the fight (not in future)
        location: Location/event name (1-200 characters)
        video_url: Optional URL to fight video
        winner_side: Optional winner (1 or 2, None for draw/unknown)
        notes: Optional notes about the fight
    """
    date: date
    location: str = Field(..., min_length=1, max_length=200)
    video_url: str | None = Field(None, max_length=500)
    winner_side: int | None = None
    notes: str | None = None

    @field_validator('winner_side')
    @classmethod
    def validate_winner_side(cls, v: int | None) -> int | None:
        """Validate that winner_side is 1, 2, or None."""
        if v is not None and v not in (1, 2):
            raise ValueError('Winner side must be 1, 2, or null')
        return v


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
    date: date # TODO None|None was causing issues. What is happening here?
    location: str | None = Field(None, min_length=1, max_length=200)
    video_url: str | None = Field(None, max_length=500)
    winner_side: int | None = None
    notes: str | None = None

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
        is_deleted: Soft delete flag
        created_at: Timestamp of creation
    """
    id: UUID
    date: date
    location: str
    video_url: str | None
    winner_side: int | None
    notes: str | None
    is_deleted: bool
    created_at: datetime

    model_config = {
        "from_attributes": True  # Enable ORM mode for SQLAlchemy compatibility
    }
