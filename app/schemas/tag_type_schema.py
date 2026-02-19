"""
Pydantic schemas for TagType API operations.
Defines request and response schemas for TagType entity.

"""

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class TagTypeBase(BaseModel):
    """
    Base schema for TagType shared fields.

    Attributes:
        name: Name of the tag type (1-100 characters)
        is_privileged: If True, changes require voting
        is_parent: If True, can have child tags
        has_children: If True, has child tags
        display_order: Order for display purposes
    """
    name: str = Field(..., description="Name of the tag type")
    is_privileged: bool = Field(..., description="If true, changes to tags of this type require voting")
    is_parent: bool = Field(..., description="If true, this tag type can have child tags")
    has_children: bool = Field(..., description="If true, this tag type currently has child tags")
    display_order: int = Field(..., description="Sort order for display purposes")

    model_config = {
        "from_attributes": True
    }


class TagTypeCreate(BaseModel):
    """
    Schema for creating a new TagType.

    Attributes:
        name: Name of the tag type (1-50 characters)
        is_privileged: If True, changes require voting (default: True)
        is_parent: If True, can have child tags (default: False)
        has_children: If True, has child tags (default: False)
        display_order: Order for display purposes (default: 0)
    """
    name: str = Field(..., min_length=1, max_length=50, description="Name of the tag type (must be unique)")
    is_privileged: bool = Field(True, description="If true, changes to tags of this type require voting")
    is_parent: bool = Field(False, description="If true, this tag type can have child tags")
    has_children: bool = Field(False, description="If true, this tag type currently has child tags")
    display_order: int = Field(0, description="Sort order for display purposes")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "fight_format",
                "is_privileged": True,
                "is_parent": False,
                "has_children": False,
                "display_order": 1
            }]
        }
    }


class TagTypeUpdate(BaseModel):
    """
    Schema for updating a TagType (all fields optional for partial updates).

    Attributes:
        name: Name of the tag type (1-50 characters)
        is_privileged: If True, changes require voting
        is_parent: If True, can have child tags
        has_children: If True, has child tags
        display_order: Order for display purposes
    """
    name: str | None = Field(None, min_length=1, max_length=50, description="Updated tag type name")
    is_privileged: bool | None = Field(None, description="Updated privileged flag")
    is_parent: bool | None = Field(None, description="Updated parent flag")
    has_children: bool | None = Field(None, description="Updated has_children flag")
    display_order: int | None = Field(None, description="Updated display order")


class TagTypeResponse(TagTypeBase):
    """
    Schema for TagType responses (includes system-generated fields).

    Attributes:
        id: UUID of the tag type
        name: Name of the tag type
        is_privileged: If True, changes require voting
        is_parent: If True, can have child tags
        has_children: If True, has child tags
        display_order: Order for display purposes
        is_deactivated: Soft delete flag
        created_at: Timestamp of record creation
    """
    id: UUID = Field(..., description="Tag type UUID")
    is_deactivated: bool = Field(..., description="Whether this record has been soft-deleted")
    created_at: datetime = Field(..., description="Timestamp of record creation")
