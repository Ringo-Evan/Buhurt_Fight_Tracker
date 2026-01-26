"""
Pydantic schemas for Tag API operations.
Defines request and response schemas for Tag entity.
"""

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    """
    Schema for creating a new Tag.

    Attributes:
        tag_type_id: UUID of the tag type this tag belongs to
        value: The tag value (1-100 characters)
        parent_tag_id: Optional parent tag for hierarchy
        fight_id: Optional fight this tag is attached to
    """
    tag_type_id: UUID
    value: str = Field(..., min_length=1, max_length=100)
    parent_tag_id: UUID | None = None
    fight_id: UUID | None = None


class TagUpdate(BaseModel):
    """
    Schema for updating a Tag (all fields optional for partial updates).

    Attributes:
        value: The tag value (1-100 characters)
        parent_tag_id: Optional parent tag for hierarchy
    """
    value: str | None = Field(None, min_length=1, max_length=100)
    parent_tag_id: UUID | None = None


class TagResponse(BaseModel):
    """
    Schema for Tag responses (includes system-generated fields).

    Attributes:
        id: UUID of the tag
        tag_type_id: UUID of the tag type
        value: The tag value
        parent_tag_id: Parent tag UUID if hierarchical
        fight_id: Fight UUID if attached to a fight
        is_deleted: Soft delete flag
        created_at: Timestamp of record creation
    """
    id: UUID
    tag_type_id: UUID
    value: str
    parent_tag_id: UUID | None
    fight_id: UUID | None
    is_deleted: bool
    created_at: datetime

    model_config = {
        "from_attributes": True  # Enable ORM mode for SQLAlchemy compatibility
    }
