"""
Service layer for Team business logic.

Implements business rules and validation for Team operations.
Validates country relationships and delegates data access to repository.
"""

from typing import Dict, Any
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from app.models.team import Team
from app.repositories.team_repository import TeamRepository
from app.repositories.country_repository import CountryRepository
from app.exceptions import (
    TeamNotFoundError,
    InvalidCountryError,
    ValidationError
)


class TeamService:
    """
    Business logic layer for Team operations.

    Handles validation, country relationship verification, and business rules.
    Delegates data access to TeamRepository and CountryRepository.
    """

    def __init__(self, team_repository: TeamRepository, country_repository: CountryRepository):
        """
        Initialize service with repositories.

        Args:
            team_repository: TeamRepository instance for team data access
            country_repository: CountryRepository instance for country validation

        Note:
            TeamService requires both repositories because it needs to validate
            that referenced countries exist and are active before creating/updating teams.
        """
        self.team_repository = team_repository
        self.country_repository = country_repository

    def _validate_team_data(self, data: Dict[str, Any]) -> None:
        """
        Validate team data fields (format validation only).

        Args:
            data: Dictionary with team fields

        Raises:
            ValidationError: If validation fails

        Note:
            This only validates field formats. Country existence and status
            are validated separately in _validate_country_reference().
        """
        # Validate name
        if 'name' in data:
            name = data.get('name', '').strip()
            if not name:
                raise ValidationError("Team name is required")
            if len(name) > 100:
                raise ValidationError("Team name must not exceed 100 characters")

    async def _validate_country_reference(self, country_id: UUID) -> None:
        """
        Validate that country exists and is active.

        Args:
            country_id: UUID of the country to validate

        Raises:
            InvalidCountryError: If country not found or soft-deleted

        Note:
            Teams can only reference active (not soft-deleted) countries.
            This ensures data integrity and prevents orphaned relationships.
        """
        country = await self.country_repository.get_by_id(country_id, include_deactivated=False)
        if country is None:
            # Check if country exists but is soft-deleted
            deleted_country = await self.country_repository.get_by_id(country_id, include_deactivated=True)
            if deleted_country and deleted_country.is_deactivated:
                raise InvalidCountryError("Country is not active")
            raise InvalidCountryError("Country not found")

    async def create(self, team_data: Dict[str, Any]) -> Team:
        """
        Create a new team with validation.

        Args:
            team_data: Dictionary with team fields (name, country_id)

        Returns:
            Created Team instance with eager-loaded country

        Raises:
            ValidationError: If validation fails
            InvalidCountryError: If country not found or inactive

        Workflow:
            1. Validate team data fields (format)
            2. Validate country exists and is active
            3. Create team via repository
            4. Return team with eager-loaded country
        """
        # Validate input
        self._validate_team_data(team_data)

        # Validate country reference
        country_id = team_data.get('country_id')
        if not country_id:
            raise ValidationError("country_id is required")

        await self._validate_country_reference(country_id)

        # Create team
        try:
            return await self.team_repository.create(team_data)
        except IntegrityError as e:
            # FK constraint violation (country_id doesn't exist at DB level)
            if "foreign key constraint" in str(e).lower():
                raise InvalidCountryError("Country not found")
            raise

    async def get_by_id(self, team_id: UUID, include_deleted: bool = False) -> Team:
        """
        Retrieve a team by ID.

        Args:
            team_id: UUID of the team
            include_deleted: If True, include soft-deleted teams

        Returns:
            Team instance with eager-loaded country

        Raises:
            TeamNotFoundError: If team not found
        """
        team = await self.team_repository.get_by_id(team_id, include_deleted=include_deleted)
        if team is None:
            raise TeamNotFoundError()
        return team

    async def list_all(self, include_deleted: bool = False) -> list[Team]:
        """
        List all teams.

        Args:
            include_deleted: If True, include soft-deleted teams

        Returns:
            List of Team instances, each with eager-loaded country
        """
        return await self.team_repository.list_all(include_deleted=include_deleted)

    async def list_by_country(
        self,
        country_id: UUID,
        include_deleted: bool = False
    ) -> list[Team]:
        """
        List all teams for a specific country.

        Args:
            country_id: UUID of the country to filter by
            include_deleted: If True, include soft-deleted teams

        Returns:
            List of Team instances for the specified country

        Note:
            Does not validate country exists - returns empty list if no teams found.
            Country validation only happens on team creation/update.
        """
        return await self.team_repository.list_by_country(country_id, include_deleted=include_deleted)

    async def update(self, team_id: UUID, update_data: Dict[str, Any]) -> Team:
        """
        Update a team's attributes.

        Args:
            team_id: UUID of the team to update
            update_data: Dictionary of fields to update (name, country_id, etc.)

        Returns:
            Updated Team instance with eager-loaded country

        Raises:
            TeamNotFoundError: If team not found
            ValidationError: If validation fails
            InvalidCountryError: If new country_id is invalid

        Note:
            If updating country_id, validates that new country exists and is active.
        """
        # Validate team exists
        team = await self.team_repository.get_by_id(team_id, include_deleted=True)
        if team is None:
            raise TeamNotFoundError()

        # Validate input
        self._validate_team_data(update_data)

        # If updating country, validate new country reference
        if 'country_id' in update_data:
            await self._validate_country_reference(update_data['country_id'])

        # Update team
        try:
            return await self.team_repository.update(team_id, update_data)
        except IntegrityError as e:
            if "foreign key constraint" in str(e).lower():
                raise InvalidCountryError("Country not found")
            raise

    async def delete(self, team_id: UUID) -> None:
        """
        Soft delete a team.

        Args:
            team_id: UUID of the team to soft delete

        Raises:
            TeamNotFoundError: If team not found

        Note:
            Soft deleting a team preserves country relationship for historical tracking.
        """
        try:
            await self.team_repository.soft_delete(team_id)
        except ValueError:
            raise TeamNotFoundError()

    async def permanent_delete(self, team_id: UUID) -> None:
        """
        Permanently delete a team from database.

        Args:
            team_id: UUID of the team to permanently delete

        Raises:
            TeamNotFoundError: If team not found

        Warning:
            This is a hard delete - the team is removed from the database entirely.
            Use delete() (soft delete) for most cases to preserve historical data.
            Only use this for data cleanup or GDPR compliance.
        """
        try:
            await self.team_repository.permanent_delete(team_id)
        except ValueError:
            raise TeamNotFoundError()
