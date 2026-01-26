"""
Service layer for Fight entity business logic.

Implements validation and business rules for fight operations.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import date

from app.repositories.fight_repository import FightRepository
from app.repositories.fight_participation_repository import FightParticipationRepository
from app.repositories.fighter_repository import FighterRepository
from app.models.fight import Fight
from app.exceptions import FightNotFoundError, ValidationError


class FightService:
    """
    Business logic layer for Fight entity.

    Handles validation and business rules for fight operations.
    """

    def __init__(
        self,
        fight_repository: FightRepository,
        participation_repository: Optional[FightParticipationRepository] = None,
        fighter_repository: Optional[FighterRepository] = None
    ):
        """
        Initialize service with repositories.

        Args:
            fight_repository: Repository for fight data access
            participation_repository: Optional repository for participation data access
            fighter_repository: Optional repository for fighter data access
        """
        self.fight_repository = fight_repository
        self.participation_repository = participation_repository
        self.fighter_repository = fighter_repository

    def _validate_fight_data(self, fight_data: Dict[str, Any], is_update: bool = False) -> None:
        """
        Validate fight data.

        Args:
            fight_data: Dictionary with fight fields
            is_update: If True, validation is for update operation

        Raises:
            ValidationError: If validation fails
        """
        # Validate date (not in future)
        if "date" in fight_data and fight_data["date"]:
            if fight_data["date"] > date.today():
                raise ValidationError("Fight date cannot be in the future")

        # Validate location
        if "location" in fight_data:
            location = fight_data.get("location", "")
            if is_update and (location is None or (isinstance(location, str) and location.strip() == "")):
                raise ValidationError("Location cannot be empty")
            elif not is_update and (not location or not location.strip()):
                raise ValidationError("Location is required")

        # Validate winner_side (must be 1, 2, or None)
        if "winner_side" in fight_data:
            winner_side = fight_data.get("winner_side")
            if winner_side is not None and winner_side not in (1, 2):
                raise ValidationError("Winner side must be 1, 2, or null")

    async def create(self, fight_data: Dict[str, Any]) -> Fight:
        """
        Create a new fight.

        Args:
            fight_data: Dictionary with fight fields

        Returns:
            Created Fight instance

        Raises:
            ValidationError: If validation fails
        """
        self._validate_fight_data(fight_data, is_update=False)
        return await self.fight_repository.create(fight_data)

    def _validate_participations(self, participations_data: List[Dict[str, Any]]) -> None:
        """
        Validate participation data before creating fight.

        Args:
            participations_data: List of participation dictionaries

        Raises:
            ValidationError: If validation fails
        """
        if not participations_data:
            return

        # Check both sides have participants
        sides = {p["side"] for p in participations_data}
        if sides != {1, 2}:
            raise ValidationError("Fight must have participants on both sides")

        # Check for duplicate fighters
        fighter_ids = [p["fighter_id"] for p in participations_data]
        if len(fighter_ids) != len(set(fighter_ids)):
            raise ValidationError("Cannot have duplicate fighter in the same fight")

        # Check max 1 captain per side
        for side in [1, 2]:
            captains = [p for p in participations_data if p["side"] == side and p.get("role") == "captain"]
            if len(captains) > 1:
                raise ValidationError(f"Cannot have multiple captains on side {side}")

    async def create_with_participants(
        self,
        fight_data: Dict[str, Any],
        participations_data: List[Dict[str, Any]]
    ) -> Fight:
        """
        Create a fight with participants atomically.

        Args:
            fight_data: Dictionary with fight fields
            participations_data: List of participation dictionaries

        Returns:
            Created Fight instance with participations

        Raises:
            ValidationError: If validation fails
        """
        self._validate_fight_data(fight_data, is_update=False)
        self._validate_participations(participations_data)

        # Create the fight first
        fight = await self.fight_repository.create(fight_data)

        # Create each participation
        for participation_data in participations_data:
            await self.participation_repository.create({
                "fight_id": fight.id,
                "fighter_id": participation_data["fighter_id"],
                "side": participation_data["side"],
                "role": participation_data.get("role", "fighter")
            })
        
        test = await self.participation_repository.list_by_fight(fight.id)
        partipant_one = await self.participation_repository.list_by_fighter(participations_data[0]["fighter_id"])
        fighter = await self.fighter_repository.get_by_id(participations_data[0]["fighter_id"])



        # Refresh the fight to load the newly created participations
        await self.fight_repository.refresh_session(fight)
        return fight

    async def get_by_id(self, fight_id: UUID, include_deleted: bool = False) -> Fight:
        """
        Get a fight by ID.

        Args:
            fight_id: UUID of the fight
            include_deleted: If True, include soft-deleted fights

        Returns:
            Fight instance

        Raises:
            FightNotFoundError: If fight not found
        """
        fight = await self.fight_repository.get_by_id(fight_id, include_deleted=include_deleted)
        if fight is None:
            raise FightNotFoundError(f"Fight with ID {fight_id} not found")
        return fight

    async def list_all(self, include_deleted: bool = False) -> list[Fight]:
        """
        List all fights.

        Args:
            include_deleted: If True, include soft-deleted fights

        Returns:
            List of Fight instances
        """
        return await self.fight_repository.list_all(include_deleted=include_deleted)

    async def list_by_date_range(
        self,
        start_date: date,
        end_date: date,
        include_deleted: bool = False
    ) -> list[Fight]:
        """
        List fights within a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range
            include_deleted: If True, include soft-deleted fights

        Returns:
            List of Fight instances
        """
        return await self.fight_repository.list_by_date_range(
            start_date, end_date, include_deleted=include_deleted
        )

    async def update(self, fight_id: UUID, update_data: Dict[str, Any]) -> Fight:
        """
        Update a fight.

        Args:
            fight_id: UUID of the fight to update
            update_data: Dictionary with fields to update

        Returns:
            Updated Fight instance

        Raises:
            FightNotFoundError: If fight not found
            ValidationError: If validation fails
        """
        # Check fight exists
        fight = await self.fight_repository.get_by_id(fight_id)
        if fight is None:
            raise FightNotFoundError(f"Fight with ID {fight_id} not found")

        self._validate_fight_data(update_data, is_update=True)
        return await self.fight_repository.update(fight_id, update_data)

    async def delete(self, fight_id: UUID) -> None:
        """
        Soft delete a fight.

        Args:
            fight_id: UUID of the fight to delete

        Raises:
            FightNotFoundError: If fight not found
        """
        try:
            await self.fight_repository.soft_delete(fight_id)
        except ValueError:
            raise FightNotFoundError(f"Fight with ID {fight_id} not found")
