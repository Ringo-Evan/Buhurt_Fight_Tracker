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
    tag_type_id: UUID = Field(..., description="UUID of the tag type this tag belongs to")
    value: str = Field(..., min_length=1, max_length=100, description="The tag value")
    parent_tag_id: UUID | None = Field(None, description="UUID of the parent tag (for hierarchical tags)")
    fight_id: UUID | None = Field(None, description="UUID of the fight this tag is attached to")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "tag_type_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "value": "melee",
                "parent_tag_id": None,
                "fight_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901"
            }]
        }
    }


class TagUpdate(BaseModel):
    """
    Schema for updating a Tag (all fields optional for partial updates).

    Attributes:
        value: The tag value (1-100 characters)
        parent_tag_id: Optional parent tag for hierarchy
    """
    value: str | None = Field(None, min_length=1, max_length=100, description="Updated tag value")
    parent_tag_id: UUID | None = Field(None, description="Updated parent tag UUID")


class TagResponse(BaseModel):
    """
    Schema for Tag responses (includes system-generated fields).

    Attributes:
        id: UUID of the tag
        tag_type_id: UUID of the tag type
        value: The tag value
        parent_tag_id: Parent tag UUID if hierarchical
        fight_id: Fight UUID if attached to a fight
        is_deactivated: Soft delete flag
        created_at: Timestamp of record creation
    """
    id: UUID = Field(..., description="Tag UUID")
    tag_type_id: UUID = Field(..., description="UUID of the tag type")
    value: str = Field(..., description="The tag value")
    parent_tag_id: UUID | None = Field(None, description="Parent tag UUID (for hierarchical tags)")
    fight_id: UUID | None = Field(None, description="Fight UUID this tag is attached to")
    is_deactivated: bool = Field(..., description="Whether this record has been soft-deleted")
    created_at: datetime = Field(..., description="Timestamp of record creation")

    model_config = {
        "from_attributes": True
    }
