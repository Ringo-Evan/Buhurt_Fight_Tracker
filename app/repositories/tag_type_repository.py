"""
Repository for TagType entity data access.

Implements data access layer for tag type reference data.
"""

from typing import Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tag_type import TagType


class TagTypeRepository:
    """
    Data access layer for TagType entity.

    Handles all database operations for tag types.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, tag_type_data: Dict[str, Any]) -> TagType:
        """Create a new tag type."""
        try:
            tag_type = TagType(**tag_type_data)
            self.session.add(tag_type)
            await self.session.commit()
            await self.session.refresh(tag_type)
            return tag_type
        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_by_id(self, tag_type_id: UUID, include_deactivated: bool = False) -> TagType | None:
        """Get tag type by ID."""
        query = select(TagType).where(TagType.id == tag_type_id)
        if not include_deactivated:
            query = query.where(TagType.is_deactivated == False)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str, include_deactivated: bool = False) -> TagType | None:
        """Get tag type by name."""
        query = select(TagType).where(TagType.name == name)
        if not include_deactivated:
            query = query.where(TagType.is_deactivated == False)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_all(self, include_deactivated: bool = False) -> list[TagType]:
        """List all tag types ordered by display_order."""
        query = select(TagType).order_by(TagType.display_order)
        if not include_deactivated:
            query = query.where(TagType.is_deactivated == False)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, tag_type_id: UUID, update_data: Dict[str, Any]) -> TagType:
        """Update a tag type."""
        tag_type = await self.get_by_id(tag_type_id)
        if tag_type is None:
            raise ValueError("Tag type not found")

        # Update fields
        for key, value in update_data.items():
            if hasattr(tag_type, key):
                setattr(tag_type, key, value)

        await self.session.commit()
        await self.session.refresh(tag_type)
        return tag_type

    async def deactivate(self, tag_type_id: UUID) -> None:
        """Soft delete a tag type."""
        tag_type = await self.get_by_id(tag_type_id)
        if tag_type is None:
            raise ValueError("Tag type not found")
        tag_type.is_deactivated = True
        await self.session.commit()

    async def delete(self, tag_type_id: UUID) -> None:
        """Permanently delete a tag type."""
        tag_type = await self.get_by_id(tag_type_id, include_deactivated=True)
        if tag_type is None:
            raise ValueError("Tag type not found")
        await self.session.delete(tag_type)
        await self.session.commit()
