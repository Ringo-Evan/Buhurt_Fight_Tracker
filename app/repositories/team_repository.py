"""
Repository for Team entity data access.

Implements data access layer with deactivate support and country relationship.
All queries filter out soft-deleted records by default and eager load country data.
"""

from typing import Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.team import Team


class TeamRepository:
    """
    Data access layer for Team entity.

    Handles all database operations for teams with deactivate support
    and country relationship management.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, team_data: Dict[str, Any]) -> Team:
        """
        Create a new team.

        Args:
            team_data: Dictionary with team fields (name, country_id)

        Returns:
            Created Team instance with eager-loaded country

        Raises:
            IntegrityError: If country_id violates FK constraint
        """
        try:
            team = Team(**team_data)
            self.session.add(team)
            await self.session.commit()
            await self.session.refresh(team)
            return team
        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_by_id(self, team_id: UUID, include_deactivated: bool = False) -> Team | None:
        """
        Retrieve a team by ID with eager-loaded country data.

        Args:
            team_id: UUID of the team
            include_deleted: If True, include deactivated teams

        Returns:
            Team instance with country relationship loaded, or None if not found

        Note:
            Country is eager loaded using joinedload to prevent N+1 queries.
            Even if team is soft-deleted, country relationship is accessible.
        """
        query = select(Team).options(joinedload(Team.country)).where(Team.id == team_id)

        if not include_deactivated:
            query = query.where(Team.is_deactivated == False)

        result = await self.session.execute(query)
        return result.unique().scalar_one_or_none()

    async def list_all(self, include_deactivated: bool = False) -> list[Team]:
        """
        List all teams with eager-loaded country data.

        Args:
            include_deleted: If True, include deactivated teams

        Returns:
            List of Team instances, each with country relationship loaded

        Note:
            Uses joinedload for efficient eager loading of country data.
            This prevents N+1 query problem when iterating through teams.
        """
        query = select(Team).options(joinedload(Team.country))

        if not include_deactivated:
            query = query.where(Team.is_deactivated == False)

        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    async def list_by_country(
        self,
        country_id: UUID,
        include_deactivated: bool = False
    ) -> list[Team]:
        """
        List all teams for a specific country.

        Args:
            country_id: UUID of the country to filter by
            include_deleted: If True, include deactivated teams

        Returns:
            List of Team instances for the specified country

        Note:
            Country is eager loaded even though we're filtering by country_id.
            This ensures consistent API - all team retrievals include country data.
        """
        query = select(Team).options(joinedload(Team.country)).where(
            Team.country_id == country_id
        )

        if not include_deactivated:
            query = query.where(Team.is_deactivated == False)

        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    async def update(self, team_id: UUID, update_data: Dict[str, Any]) -> Team:
        """
        Update a team's attributes.

        Args:
            team_id: UUID of the team to update
            update_data: Dictionary of fields to update (name, country_id, etc.)

        Returns:
            Updated Team instance with eager-loaded country

        Raises:
            ValueError: If team not found
            IntegrityError: If country_id violates FK constraint
        """
        team = await self.get_by_id(team_id, include_deactivated=True)
        if team is None:
            raise ValueError("Team not found")

        for key, value in update_data.items():
            setattr(team, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(team)
            return team
        except Exception as e:
            await self.session.rollback()
            raise e

    async def deactivate(self, team_id: UUID) -> None:
        """
        Deactivate a team by setting is_deactivated flag.

        Args:
            team_id: UUID of the team to deactivate

        Raises:
            ValueError: If team not found

        Note:
            Soft deleting a team preserves the country relationship.
            The team can still be retrieved with include_deactivated=True.
            Country reference remains valid for historical tracking.
        """
        team = await self.get_by_id(team_id, include_deactivated=True)
        if team is None:
            raise ValueError("Team not found")

        team.is_deactivated = True
        await self.session.commit()

    async def delete(self, team_id: UUID) -> None:
        """
        Permanently delete a team from database.

        Args:
            team_id: UUID of the team to delete

        Raises:
            ValueError: If team not found

        Warning:
            This is a hard delete - the team is removed from the database entirely.
            Use deactivate() for most cases to preserve historical data.
            Only use this for data cleanup or GDPR compliance.
        """
        team = await self.get_by_id(team_id, include_deactivated=True)
        if team is None:
            raise ValueError("Team not found")

        await self.session.delete(team)  # delete() is synchronous
        await self.session.commit()
