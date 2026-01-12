"""
Repository for Country entity data access.

Implements data access layer with soft delete support.
All queries filter out soft-deleted records by default.
"""

from typing import Dict, Any
from uuid import UUID
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.country import Country
from app.models.team import Team


class CountryRepository:
    """
    Data access layer for Country entity.

    Handles all database operations for countries with soft delete support.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, country_data: Dict[str, Any]) -> Country:
        """
        Create a new country.

        Args:
            country_data: Dictionary with country fields (name, code)

        Returns:
            Created Country instance

        Raises:
            IntegrityError: If code violates unique constraint
        """
        try:
            country = Country(**country_data)
            self.session.add(country)
            await self.session.commit()
            await self.session.refresh(country)
            return country
        except Exception as e:
            await self.session.rollback()
            raise e
        
    async def get_by_id(self, country_id: UUID, include_deleted: bool = False) -> Country | None:
        """
        Retrieve a country by ID.

        Args:
            country_id: UUID of the country
            include_deleted: If True, include soft-deleted countries

        Returns:
            Country instance or None if not found
        """
        query = select(Country).where(Country.id == country_id)

        if not include_deleted:
            query = query.where(Country.is_deleted == False)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str, include_deleted: bool = False) -> Country | None:
        """
        Retrieve a country by ISO code.

        Args:
            code: ISO 3166-1 alpha-3 country code
            include_deleted: If True, include soft-deleted countries

        Returns:
            Country instance or None if not found
        """
        query = select(Country).where(Country.code == code)

        if not include_deleted:
            query = query.where(Country.is_deleted == False)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_all(self, include_deleted: bool = False) -> list[Country]:
        """
        List all countries.

        Args:
            include_deleted: If True, include soft-deleted countries

        Returns:
            List of Country instances
        """
        query = select(Country)

        if not include_deleted:
            query = query.where(Country.is_deleted == False)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def soft_delete(self, country_id: UUID) -> None:
        """
        Soft delete a country by setting is_deleted flag.

        Args:
            country_id: UUID of the country to delete

        Raises:
            ValueError: If country not found
        """
        country = await self.get_by_id(country_id, include_deleted=False)
        if country is None:
            raise ValueError("Country not found")

        country.is_deleted = True
        await self.session.commit()

    async def update(self, country_id: UUID, update_data: Dict[str, Any]) -> Country:
        """
        Update a country's attributes.

        Args:
            country_id: UUID of the country to update
            update_data: Dictionary with fields to update

        Returns:
            Updated Country instance

        Raises:
            ValueError: If country not found
            IntegrityError: If update violates unique constraint
        """
        country = await self.get_by_id(country_id, include_deleted=False)
        if country is None:
            raise ValueError("Country not found")

        for key, value in update_data.items():
            setattr(country, key, value)

        await self.session.commit()
        await self.session.refresh(country)
        return country

    async def permanent_delete(self, country_id: UUID) -> None:
        """
        Permanently delete a country from database.

        Args:
            country_id: UUID of the country to delete

        Raises:
            ValueError: If country not found
        """
        country = await self.get_by_id(country_id, include_deleted=True)
        if country is None:
            raise ValueError("Country not found")

        await self.session.delete(country)  # delete() is synchronous
        await self.session.commit()

    async def count_relationships(self, country_id: UUID) -> int:
        """
        Count the number of relationships (teams) associated with a country.

        Args:
            country_id: UUID of the country

        Returns:
            Number of related teams

        Raises:
            ValueError: If country not found
            NotImplementedError: Team entity not yet implemented
        """
        # Validate country exists
        country = await self.get_by_id(country_id, include_deleted=True)
        if country is None:
            raise ValueError("Country not found")

        # Count all teams associated with this country (including soft-deleted)
        query = select(func.count(Team.id)).where(Team.country_id == country_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def replace(self, old_country_id: UUID, new_country_id: UUID) -> int:
        """
        Replace old country with new country in all relationships.

        Args:
            old_country_id: UUID of country to replace
            new_country_id: UUID of replacement country

        Returns:
            Number of relationships updated

        Raises:
            ValueError: If either country not found
            NotImplementedError: Team entity not yet implemented
        """
        old_country = await self.get_by_id(old_country_id, include_deleted=True)
        if old_country is None:
            raise ValueError("Old country not found")

        new_country = await self.get_by_id(new_country_id, include_deleted=False)
        if new_country is None:
            raise ValueError("New country not found")

        # Update all team.country_id references from old to new
        query = (
            update(Team)
            .where(Team.country_id == old_country_id)
            .values(country_id=new_country_id)
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
