"""
Repository for Fight entity data access.

Implements data access layer with deactivate support.
All queries filter out soft-deleted records by default.
"""

from typing import Dict, Any
from uuid import UUID
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.fight import Fight


class FightRepository:
    """
    Data access layer for Fight entity.

    Handles all database operations for fights with deactivate support.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, fight_data: Dict[str, Any]) -> Fight:
        """
        Create a new fight.

        Args:
            fight_data: Dictionary with fight fields

        Returns:
            Created Fight instance
        """
        try:
            fight = Fight(**fight_data)
            self.session.add(fight)  # add() is synchronous
            await self.session.commit()
            await self.session.refresh(fight)
            return fight
        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_by_id(self, fight_id: UUID, include_deactivated: bool = False) -> Fight | None:
        """
        Retrieve a fight by ID.

        Args:
            fight_id: UUID of the fight
            include_deactivate: If True, include deactivated fights

        Returns:
            Fight instance or None if not found
        """
        query = select(Fight).where(Fight.id == fight_id)

        if not include_deactivated:
            query = query.where(Fight.is_deactivated == False)

        result = await self.session.execute(query)
        return result.unique().scalar_one_or_none()
    
    async def list_all(self, include_deactivated: bool = False) -> list[Fight]:
        """
        List all fights.

        Args:
            include_deactivate: If True, include deactivated fights

        Returns:
            List of Fight instances
        """
        query = select(Fight).order_by(Fight.date.desc())

        if not include_deactivated:
            query = query.where(Fight.is_deactivated == False)

        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    async def list_by_date_range(
        self,
        start_date: date,
        end_date: date,
        include_deactivated: bool = False
    ) -> list[Fight]:
        """
        List fights within a date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            include_deactivate: If True, include deactivated fights

        Returns:
            List of Fight instances within the date range
        """
        query = select(Fight).where(
            Fight.date >= start_date,
            Fight.date <= end_date
        ).order_by(Fight.date.desc())

        if not include_deactivated:
            query = query.where(Fight.is_deactivated == False)

        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    async def deactivate(self, fight_id: UUID) -> None:
        """
        Deactivate a fight by setting is_deactivated flag.

        Args:
            fight_id: UUID of the fight to delete

        Raises:
            ValueError: If fight not found
        """
        fight = await self.get_by_id(fight_id, include_deactivated=False)
        if fight is None:
            raise ValueError("Fight not found")

        fight.is_deactivated = True
        await self.session.commit()

    async def update(self, fight_id: UUID, update_data: Dict[str, Any]) -> Fight:
        """
        Update a fight's attributes.

        Args:
            fight_id: UUID of the fight to update
            update_data: Dictionary with fields to update

        Returns:
            Updated Fight instance

        Raises:
            ValueError: If fight not found
        """
        fight = await self.get_by_id(fight_id, include_deactivated=False)
        if fight is None:
            raise ValueError("Fight not found")

        for key, value in update_data.items():
            setattr(fight, key, value)

        await self.session.commit()
        await self.session.refresh(fight)
        return fight

    async def refresh_session(self, fight: Fight) -> None:
        """
        Refresh the fight instance from the database.

        Args:
            fight: Fight instance to refresh
        """
        await self.session.refresh(fight)