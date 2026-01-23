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
    name: str
    is_privileged: bool
    is_parent: bool
    has_children: bool
    display_order: int

    model_config = {
        "from_attributes": True  # Enable ORM mode for SQLAlchemy compatibility
    }


class TagTypeCreate(BaseModel):
    """
    Schema for creating a new TagType.

    Attributes:
        name: Name of the tag type (1-100 characters)
        is_privileged: If True, changes require voting (default: True)
        is_parent: If True, can have child tags (default: False)
        has_children: If True, has child tags (default: False)
        display_order: Order for display purposes (default: 0)
    """
    name: str = Field(..., min_length=1, max_length=100)
    is_privileged: bool = True
    is_parent: bool = False
    has_children: bool = False
    display_order: int = 0


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
        is_deleted: Soft delete flag
        created_at: Timestamp of record creation
    """
    id: UUID
    is_deleted: bool
    created_at: datetime
    