"""
Service layer for Fighter business logic.

Implements business rules and validation for Fighter operations.
Validates team references and delegates data access to repositories.
"""

from typing import Dict, Any
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from app.models.fighter import Fighter
from app.repositories.fighter_repository import FighterRepository
from app.repositories.team_repository import TeamRepository
from app.exceptions import (
    FighterNotFoundError,
    InvalidTeamError,
    ValidationError
)


class FighterService:
    """
    Business logic layer for Fighter operations.

    Handles validation, business rules, and delegates data access to repositories.
    Requires both FighterRepository and TeamRepository for team validation.
    """

    def __init__(self, fighter_repository: FighterRepository, team_repository: TeamRepository):
        """
        Initialize service with repositories.

        Args:
            fighter_repository: FighterRepository instance for fighter data access
            team_repository: TeamRepository instance for team validation
        """
        self.repository = fighter_repository
        self.team_repository = team_repository

    def _validate_fighter_data(self, data: Dict[str, Any]) -> None:
        """
        Validate fighter data fields.

        Args:
            data: Dictionary with fighter fields

        Raises:
            ValidationError: If validation fails
        """
        # Validate name
        if 'name' in data:
            name = data.get('name', '').strip()
            if not name:
                raise ValidationError("name is required")

    async def _validate_team_reference(self, team_id: UUID) -> None:
        """
        Validate that team exists and is active.

        Args:
            team_id: UUID of the team

        Raises:
            InvalidTeamError: If team doesn't exist or is deactivated
        """
        team = await self.team_repository.get_by_id(team_id, include_deactivated=False)
        if team is None:
            # Check if team exists but is deactivated
            deleted_team = await self.team_repository.get_by_id(team_id, include_deactivated=True)
            if deleted_team and deleted_team.is_deactivated:
                raise InvalidTeamError("Team is not active")
            raise InvalidTeamError("Team not found")

    async def create(self, fighter_data: Dict[str, Any]) -> Fighter:
        """
        Create a new fighter with validation.

        Args:
            fighter_data: Dictionary with fighter fields (name, team_id)

        Returns:
            Created Fighter instance

        Raises:
            ValidationError: If validation fails
            InvalidTeamError: If team doesn't exist or is inactive
        """
        # Validate input
        self._validate_fighter_data(fighter_data)

        # Validate team reference
        team_id = fighter_data.get('team_id')
        await self._validate_team_reference(team_id)

        # Create fighter
        try:
            return await self.repository.create(fighter_data)
        except IntegrityError:
            raise InvalidTeamError("Team not found")

    async def get_by_id(self, fighter_id: UUID, include_deleted: bool = False) -> Fighter:
        """
        Retrieve a fighter by ID.

        Args:
            fighter_id: UUID of the fighter
            include_deleted: If True, include deactivated fighters

        Returns:
            Fighter instance

        Raises:
            FighterNotFoundError: If fighter not found
        """
        fighter = await self.repository.get_by_id(fighter_id, include_deactivated=include_deactivated)
        if fighter is None:
            raise FighterNotFoundError()

        return fighter

    async def list_all(self, include_deleted: bool = False) -> list[Fighter]:
        """
        List all fighters.

        Args:
            include_deleted: If True, include deactivated fighters

        Returns:
            List of Fighter instances
        """
        return await self.repository.list_all(include_deactivated=include_deactivated)

    async def list_by_team(self, team_id: UUID, include_deleted: bool = False) -> list[Fighter]:
        """
        List fighters filtered by team.

        Args:
            team_id: UUID of the team
            include_deleted: If True, include deactivated fighters

        Returns:
            List of Fighter instances for the specified team
        """
        return await self.repository.list_by_team(team_id, include_deactivated=include_deactivated)

    async def list_by_country(self, country_id: UUID, include_deleted: bool = False) -> list[Fighter]:
        """
        List fighters filtered by country (via team relationship).

        Args:
            country_id: UUID of the country
            include_deleted: If True, include deactivated fighters

        Returns:
            List of Fighter instances from teams in the specified country
        """
        return await self.repository.list_by_country(country_id, include_deactivated=include_deactivated)

    async def delete(self, fighter_id: UUID) -> None:
        """
        Deactivate a fighter.

        Args:
            fighter_id: UUID of the fighter to delete

        Raises:
            FighterNotFoundError: If fighter not found
        """
        try:
            await self.repository.deactivate(fighter_id)
        except ValueError as e:
            raise FighterNotFoundError(str(e))

    async def update(self, fighter_id: UUID, update_data: Dict[str, Any]) -> Fighter:
        """
        Update a fighter with validation.

        Args:
            fighter_id: UUID of the fighter to update
            update_data: Dictionary with fields to update

        Returns:
            Updated Fighter instance

        Raises:
            ValidationError: If validation fails
            FighterNotFoundError: If fighter not found
            InvalidTeamError: If team update references invalid team
        """
        # Validate update data
        self._validate_fighter_data(update_data)

        # Validate team reference if updating team
        if 'team_id' in update_data:
            await self._validate_team_reference(update_data['team_id'])

        # Update fighter
        try:
            return await self.repository.update(fighter_id, update_data)
        except ValueError as e:
            raise FighterNotFoundError(str(e))
        except IntegrityError:
            raise InvalidTeamError("Team not found")
