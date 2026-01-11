"""
Repository for Fighter entity data access.

Implements data access layer with soft delete support and 3-level eager loading.
All queries filter out soft-deleted records by default.
Eager loads Fighter → Team → Country to prevent N+1 queries.
"""

from typing import Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.fighter import Fighter
from app.models.team import Team


class FighterRepository:
    """
    Data access layer for Fighter entity.

    Handles all database operations for fighters with soft delete support
    and eager loading of team and country relationships.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, fighter_data: Dict[str, Any]) -> Fighter:
        """
        Create a new fighter.

        Args:
            fighter_data: Dictionary with fighter fields (name, team_id)

        Returns:
            Created Fighter instance

        Raises:
            IntegrityError: If team_id violates foreign key constraint
        """
        try:
            fighter = Fighter(**fighter_data)
            self.session.add(fighter)
            await self.session.commit()
            await self.session.refresh(fighter)
            return fighter
        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_by_id(self, fighter_id: UUID, include_deleted: bool = False) -> Fighter | None:
        """
        Retrieve a fighter by ID with eager-loaded team and country.

        Args:
            fighter_id: UUID of the fighter
            include_deleted: If True, include soft-deleted fighters

        Returns:
            Fighter instance or None if not found
        """
        query = (
            select(Fighter)
            .options(joinedload(Fighter.team).joinedload(Team.country))
            .where(Fighter.id == fighter_id)
        )

        if not include_deleted:
            query = query.where(Fighter.is_deleted == False)

        result = await self.session.execute(query)
        return result.unique().scalar_one_or_none()

    async def list_all(self, include_deleted: bool = False) -> list[Fighter]:
        """
        List all fighters with eager-loaded relationships.

        Args:
            include_deleted: If True, include soft-deleted fighters

        Returns:
            List of Fighter instances
        """
        query = (
            select(Fighter)
            .options(joinedload(Fighter.team).joinedload(Team.country))
        )

        if not include_deleted:
            query = query.where(Fighter.is_deleted == False)

        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    async def list_by_team(self, team_id: UUID, include_deleted: bool = False) -> list[Fighter]:
        """
        List fighters filtered by team with eager-loaded relationships.

        Args:
            team_id: UUID of the team
            include_deleted: If True, include soft-deleted fighters

        Returns:
            List of Fighter instances for the specified team
        """
        query = (
            select(Fighter)
            .options(joinedload(Fighter.team).joinedload(Team.country))
            .where(Fighter.team_id == team_id)
        )

        if not include_deleted:
            query = query.where(Fighter.is_deleted == False)

        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    async def list_by_country(self, country_id: UUID, include_deleted: bool = False) -> list[Fighter]:
        """
        List fighters filtered by country (via team relationship).

        Args:
            country_id: UUID of the country
            include_deleted: If True, include soft-deleted fighters

        Returns:
            List of Fighter instances from teams in the specified country
        """
        query = (
            select(Fighter)
            .options(joinedload(Fighter.team).joinedload(Team.country))
            .join(Team, Fighter.team_id == Team.id)
            .where(Team.country_id == country_id)
        )

        if not include_deleted:
            query = query.where(Fighter.is_deleted == False)

        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    async def soft_delete(self, fighter_id: UUID) -> None:
        """
        Soft delete a fighter by setting is_deleted flag.

        Args:
            fighter_id: UUID of the fighter to delete

        Raises:
            ValueError: If fighter not found
        """
        fighter = await self.get_by_id(fighter_id, include_deleted=False)
        if fighter is None:
            raise ValueError("Fighter not found")

        fighter.is_deleted = True
        await self.session.commit()

    async def update(self, fighter_id: UUID, update_data: Dict[str, Any]) -> Fighter:
        """
        Update a fighter's attributes.

        Args:
            fighter_id: UUID of the fighter to update
            update_data: Dictionary with fields to update

        Returns:
            Updated Fighter instance

        Raises:
            ValueError: If fighter not found
            IntegrityError: If update violates foreign key constraint
        """
        fighter = await self.get_by_id(fighter_id, include_deleted=False)
        if fighter is None:
            raise ValueError("Fighter not found")

        for key, value in update_data.items():
            setattr(fighter, key, value)

        await self.session.commit()
        await self.session.refresh(fighter)
        return fighter
