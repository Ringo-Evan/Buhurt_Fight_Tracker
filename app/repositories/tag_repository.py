"""
Repository for Tag entity data access.

Implements data access layer for hierarchical tags.
"""

from typing import Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.tag import Tag


class TagRepository:
    """
    Data access layer for Tag entity.

    Handles all database operations for tags including hierarchy.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, tag_data: Dict[str, Any]) -> Tag:
        """Create a new tag."""
        try:
            tag = Tag(**tag_data)
            self.session.add(tag)
            await self.session.commit()
            await self.session.refresh(tag)
            return tag
        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_by_id(self, tag_id: UUID, include_deactivated: bool = False) -> Tag | None:
        """Get tag by ID with eager-loaded tag_type."""
        query = select(Tag).options(
            joinedload(Tag.tag_type)
        ).where(Tag.id == tag_id)
        if not include_deactivated:
            query = query.where(Tag.is_deactivated == False)
        result = await self.session.execute(query)
        return result.unique().scalar_one_or_none()

    async def list_all(self, include_deactivated: bool = False) -> list[Tag]:
        """List all tags with eager-loaded tag_type."""
        query = select(Tag).options(
            joinedload(Tag.tag_type)
        )
        if not include_deactivated:
            query = query.where(Tag.is_deactivated == False)
        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    async def list_by_fight(self, fight_id: UUID, include_deactivated: bool = False) -> list[Tag]:
        """List all tags for a fight."""
        query = select(Tag).options(
            joinedload(Tag.tag_type)
        ).where(Tag.fight_id == fight_id)
        if not include_deactivated:
            query = query.where(Tag.is_deactivated == False)
        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    async def get_by_fight_and_type(
        self,
        fight_id: UUID,
        tag_type_id: UUID,
        include_deactivated: bool = False
    ) -> Tag | None:
        """Get the active tag of a specific type for a fight."""
        query = select(Tag).where(
            Tag.fight_id == fight_id,
            Tag.tag_type_id == tag_type_id
        )
        if not include_deactivated:
            query = query.where(Tag.is_deactivated == False)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_active_children(self, parent_tag_id: UUID) -> list[Tag]:
        """Return all active (non-deactivated) child tags of the given parent."""
        query = select(Tag).where(
            Tag.parent_tag_id == parent_tag_id,
            Tag.is_deactivated == False
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, tag_id: UUID, update_data: Dict[str, Any]) -> Tag | None:
        """Update an existing tag."""
        tag = await self.get_by_id(tag_id)
        if tag is None:
            return None

        for key, value in update_data.items():
            if hasattr(tag, key):
                setattr(tag, key, value)

        await self.session.commit()
        await self.session.refresh(tag)
        return tag

    async def deactivate(self, tag_id: UUID) -> None:
        """Soft delete a tag."""
        tag = await self.get_by_id(tag_id)
        if tag is None:
            raise ValueError("Tag not found")
        tag.is_deactivated = True
        await self.session.commit()

    async def delete(self, tag_id: UUID) -> None:
        """
        Permanently delete a tag from the database.

        Args:
            tag_id: UUID of the tag to delete

        Raises:
            ValueError: If tag not found
        """
        tag = await self.get_by_id(tag_id, include_deactivated=True)
        if tag is None:
            raise ValueError("Tag not found")

        await self.session.delete(tag)
        await self.session.commit()

    async def cascade_deactivate_children(self, parent_tag_id: UUID) -> int:
        """Soft delete all child tags of a parent tag."""
        query = select(Tag).where(
            Tag.parent_tag_id == parent_tag_id,
            Tag.is_deactivated == False
        )
        result = await self.session.execute(query)
        children = list(result.scalars().all())

        count = 0
        for child in children:
            child.is_deactivated = True
            count += 1
            # Recursively deactivate grandchildren
            count += await self.cascade_deactivate_children(child.id)

        await self.session.commit()
        return count
