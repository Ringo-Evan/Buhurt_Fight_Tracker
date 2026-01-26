"""
Unit tests for FightService.

Tests business logic layer for Fight operations with mocked repository.
Following TDD approach - these tests are written before implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import date, datetime, UTC

from app.services.fight_service import FightService
from app.repositories.fight_repository import FightRepository
from app.models.fight import Fight
from app.exceptions import FightNotFoundError, ValidationError


class TestFightServiceCreate:
    """Test suite for fight creation with validation."""

    @pytest.mark.asyncio
    async def test_create_fight_with_valid_data_succeeds(self):
        """
        Test that creating a fight with valid data succeeds.
        """
        # Arrange
        mock_repository = AsyncMock(spec=FightRepository)
        fight = Fight(
            id=uuid4(),
            date=date(2024, 6, 15),
            location="IMCF Worlds 2024",
            video_url="https://youtube.com/watch?v=abc",
            winner_side=1,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )
        mock_repository.create.return_value = fight

        service = FightService(mock_repository)
        fight_data = {
            "date": date(2024, 6, 15),
            "location": "IMCF Worlds 2024",
            "video_url": "https://youtube.com/watch?v=abc",
            "winner_side": 1
        }

        # Act
        result = await service.create(fight_data)

        # Assert
        assert result == fight
        mock_repository.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_fight_rejects_future_date(self):
        """
        Test that creating a fight with future date raises ValidationError.
        """
        # Arrange
        mock_repository = AsyncMock(spec=FightRepository)
        service = FightService(mock_repository)

        future_date = date(2099, 12, 31)
        fight_data = {
            "date": future_date,
            "location": "Future Tournament"
        }

        # Act & Assert
        with pytest.raises(ValidationError, match="Fight date cannot be in the future"):
            await service.create(fight_data)

        mock_repository.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_fight_rejects_empty_location(self):
        """
        Test that creating a fight with empty location raises ValidationError.
        """
        # Arrange
        mock_repository = AsyncMock(spec=FightRepository)
        service = FightService(mock_repository)

        fight_data = {
            "date": date(2024, 6, 15),
            "location": ""
        }

        # Act & Assert
        with pytest.raises(ValidationError, match="Location is required"):
            await service.create(fight_data)

    @pytest.mark.asyncio
    async def test_create_fight_rejects_whitespace_location(self):
        """
        Test that creating a fight with whitespace-only location raises ValidationError.
        """
        # Arrange
        mock_repository = AsyncMock(spec=FightRepository)
        service = FightService(mock_repository)

        fight_data = {
            "date": date(2024, 6, 15),
            "location": "   "
        }

        # Act & Assert
        with pytest.raises(ValidationError, match="Location is required"):
            await service.create(fight_data)

    @pytest.mark.asyncio
    async def test_create_fight_rejects_invalid_winner_side(self):
        """
        Test that creating a fight with invalid winner_side raises ValidationError.
        """
        # Arrange
        mock_repository = AsyncMock(spec=FightRepository)
        service = FightService(mock_repository)

        fight_data = {
            "date": date(2024, 6, 15),
            "location": "Test",
            "winner_side": 3  # Invalid - must be 1, 2, or None
        }

        # Act & Assert
        with pytest.raises(ValidationError, match="Winner side must be 1, 2, or null"):
            await service.create(fight_data)

    @pytest.mark.asyncio
    async def test_create_fight_accepts_none_winner_side(self):
        """
        Test that creating a fight with None winner_side (draw/unknown) succeeds.
        """
        # Arrange
        mock_repository = AsyncMock(spec=FightRepository)
        fight = Fight(
            id=uuid4(),
            date=date(2024, 6, 15),
            location="Test",
            winner_side=None,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )
        mock_repository.create.return_value = fight

        service = FightService(mock_repository)
        fight_data = {
            "date": date(2024, 6, 15),
            "location": "Test",
            "winner_side": None
        }

        # Act
        result = await service.create(fight_data)

        # Assert
        assert result.winner_side is None


class TestFightServiceRetrieve:
    """Test suite for fight retrieval operations."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_fight_when_exists(self):
        """
        Test that get_by_id returns fight when it exists.
        """
        # Arrange
        fight_id = uuid4()
        fight = Fight(
            id=fight_id,
            date=date(2024, 6, 15),
            location="Test",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_repository = AsyncMock(spec=FightRepository)
        mock_repository.get_by_id.return_value = fight

        service = FightService(mock_repository)

        # Act
        result = await service.get_by_id(fight_id)

        # Assert
        assert result == fight

    @pytest.mark.asyncio
    async def test_get_by_id_raises_not_found_when_not_exists(self):
        """
        Test that get_by_id raises FightNotFoundError when fight doesn't exist.
        """
        # Arrange
        mock_repository = AsyncMock(spec=FightRepository)
        mock_repository.get_by_id.return_value = None

        service = FightService(mock_repository)

        # Act & Assert
        with pytest.raises(FightNotFoundError):
            await service.get_by_id(uuid4())

    @pytest.mark.asyncio
    async def test_list_all_returns_all_fights(self):
        """
        Test that list_all returns all non-deleted fights.
        """
        # Arrange
        fights = [
            Fight(id=uuid4(), date=date(2024, 1, 1), location="Fight 1", is_deleted=False, created_at=datetime.now(UTC)),
            Fight(id=uuid4(), date=date(2024, 2, 1), location="Fight 2", is_deleted=False, created_at=datetime.now(UTC)),
        ]

        mock_repository = AsyncMock(spec=FightRepository)
        mock_repository.list_all.return_value = fights

        service = FightService(mock_repository)

        # Act
        result = await service.list_all()

        # Assert
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_by_date_range_returns_filtered_fights(self):
        """
        Test that list_by_date_range returns fights within the range.
        """
        # Arrange
        fights = [
            Fight(id=uuid4(), date=date(2024, 6, 15), location="Fight 1", is_deleted=False, created_at=datetime.now(UTC)),
        ]

        mock_repository = AsyncMock(spec=FightRepository)
        mock_repository.list_by_date_range.return_value = fights

        service = FightService(mock_repository)

        # Act
        result = await service.list_by_date_range(
            start_date=date(2024, 6, 1),
            end_date=date(2024, 6, 30)
        )

        # Assert
        assert len(result) == 1


class TestFightServiceUpdate:
    """Test suite for fight update operations."""

    @pytest.mark.asyncio
    async def test_update_fight_location_succeeds(self):
        """
        Test that updating fight location works correctly.
        """
        # Arrange
        fight_id = uuid4()
        fight = Fight(
            id=fight_id,
            date=date(2024, 6, 15),
            location="Updated Location",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_repository = AsyncMock(spec=FightRepository)
        mock_repository.get_by_id.return_value = fight
        mock_repository.update.return_value = fight

        service = FightService(mock_repository)

        # Act
        result = await service.update(fight_id, {"location": "Updated Location"})

        # Assert
        assert result.location == "Updated Location"

    @pytest.mark.asyncio
    async def test_update_fight_rejects_empty_location(self):
        """
        Test that updating fight with empty location raises ValidationError.
        """
        # Arrange
        fight_id = uuid4()
        fight = Fight(
            id=fight_id,
            date=date(2024, 6, 15),
            location="Original",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_repository = AsyncMock(spec=FightRepository)
        mock_repository.get_by_id.return_value = fight

        service = FightService(mock_repository)

        # Act & Assert
        with pytest.raises(ValidationError, match="Location cannot be empty"):
            await service.update(fight_id, {"location": ""})

    @pytest.mark.asyncio
    async def test_update_fight_handles_non_existent_fight(self):
        """
        Test that updating non-existent fight raises FightNotFoundError.
        """
        # Arrange
        mock_repository = AsyncMock(spec=FightRepository)
        mock_repository.get_by_id.return_value = None

        service = FightService(mock_repository)

        # Act & Assert
        with pytest.raises(FightNotFoundError):
            await service.update(uuid4(), {"location": "New"})


class TestFightServiceDelete:
    """Test suite for fight delete operations."""

    @pytest.mark.asyncio
    async def test_soft_delete_fight_succeeds(self):
        """
        Test that soft deleting a fight succeeds.
        """
        # Arrange
        fight_id = uuid4()
        mock_repository = AsyncMock(spec=FightRepository)

        service = FightService(mock_repository)

        # Act
        await service.delete(fight_id)

        # Assert
        mock_repository.soft_delete.assert_awaited_once_with(fight_id)

    @pytest.mark.asyncio
    async def test_soft_delete_non_existent_fight_raises_error(self):
        """
        Test that soft deleting non-existent fight raises FightNotFoundError.
        """
        # Arrange
        mock_repository = AsyncMock(spec=FightRepository)
        mock_repository.soft_delete.side_effect = ValueError("Fight not found")

        service = FightService(mock_repository)

        # Act & Assert
        with pytest.raises(FightNotFoundError):
            await service.delete(uuid4())


class TestFightServiceCreateWithParticipants:
    """Test suite for fight creation with participants (atomic transaction)."""

    @pytest.mark.asyncio
    async def test_create_fight_with_valid_participants_succeeds(self):
        """
        Test that creating a fight with valid participants creates both atomically.

        Following TDD: This test is written FIRST (RED phase).
        The service.create_with_participants method doesn't exist yet.
        """
        # Arrange
        from app.repositories.fight_participation_repository import FightParticipationRepository
        from app.repositories.fighter_repository import FighterRepository
        from app.models.fighter import Fighter
        from app.models.fight_participation import FightParticipation

        mock_fight_repo = AsyncMock(spec=FightRepository)
        mock_participation_repo = AsyncMock(spec=FightParticipationRepository)
        mock_fighter_repo = AsyncMock(spec=FighterRepository)

        fight_id = uuid4()
        fighter1_id = uuid4()
        fighter2_id = uuid4()

        # Mock fighter lookups
        fighter1 = Fighter(id=fighter1_id, name="John Smith", is_deleted=False, created_at=datetime.now(UTC))
        fighter2 = Fighter(id=fighter2_id, name="Jane Doe", is_deleted=False, created_at=datetime.now(UTC))
        mock_fighter_repo.get_by_id.side_effect = lambda fid: fighter1 if fid == fighter1_id else fighter2

        # Mock fight creation
        fight = Fight(
            id=fight_id,
            date=date(2025, 6, 15),
            location="Battle Arena Denver",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )
        mock_fight_repo.create.return_value = fight
        # Mock get_by_id to return the fight (used for refresh after creating participations)
        mock_fight_repo.get_by_id.return_value = fight

        # Mock participation creation
        participation1 = FightParticipation(
            id=uuid4(),
            fight_id=fight_id,
            fighter_id=fighter1_id,
            side=1,
            role="fighter",
            created_at=datetime.now(UTC)
        )
        participation2 = FightParticipation(
            id=uuid4(),
            fight_id=fight_id,
            fighter_id=fighter2_id,
            side=2,
            role="fighter",
            created_at=datetime.now(UTC)
        )
        mock_participation_repo.create.side_effect = [participation1, participation2]

        # Service with all dependencies
        service = FightService(
            fight_repository=mock_fight_repo,
            participation_repository=mock_participation_repo,
            fighter_repository=mock_fighter_repo
        )

        fight_data = {
            "date": date(2025, 6, 15),
            "location": "Battle Arena Denver"
        }
        participations_data = [
            {"fighter_id": fighter1_id, "side": 1, "role": "fighter"},
            {"fighter_id": fighter2_id, "side": 2, "role": "fighter"}
        ]

        # Act
        result = await service.create_with_participants(fight_data, participations_data)

        # Assert
        assert result.id == fight_id
        assert result.location == "Battle Arena Denver"
        mock_fight_repo.create.assert_awaited_once()
        assert mock_participation_repo.create.await_count == 2

    @pytest.mark.asyncio
    async def test_create_fight_rejects_participants_on_only_one_side(self):
        """
        Test that creating a fight with participants on only one side fails.

        Scenario: Cannot create fight with participants on only one side
        """
        # Arrange
        from app.repositories.fight_participation_repository import FightParticipationRepository
        from app.repositories.fighter_repository import FighterRepository

        mock_fight_repo = AsyncMock(spec=FightRepository)
        mock_participation_repo = AsyncMock(spec=FightParticipationRepository)
        mock_fighter_repo = AsyncMock(spec=FighterRepository)

        fighter1_id = uuid4()
        fighter2_id = uuid4()

        service = FightService(
            fight_repository=mock_fight_repo,
            participation_repository=mock_participation_repo,
            fighter_repository=mock_fighter_repo
        )

        fight_data = {
            "date": date(2024, 6, 15),
            "location": "Test Arena"
        }
        # Both fighters on side 1, no one on side 2
        participations_data = [
            {"fighter_id": fighter1_id, "side": 1, "role": "fighter"},
            {"fighter_id": fighter2_id, "side": 1, "role": "fighter"}
        ]

        # Act & Assert
        with pytest.raises(ValidationError, match="both sides"):
            await service.create_with_participants(fight_data, participations_data)

        # Verify fight was NOT created
        mock_fight_repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_fight_rejects_duplicate_fighter(self):
        """
        Test that creating a fight with the same fighter twice fails.

        Scenario: Cannot add same fighter twice to same fight
        """
        # Arrange
        from app.repositories.fight_participation_repository import FightParticipationRepository
        from app.repositories.fighter_repository import FighterRepository

        mock_fight_repo = AsyncMock(spec=FightRepository)
        mock_participation_repo = AsyncMock(spec=FightParticipationRepository)
        mock_fighter_repo = AsyncMock(spec=FighterRepository)

        fighter1_id = uuid4()
        fighter2_id = uuid4()

        service = FightService(
            fight_repository=mock_fight_repo,
            participation_repository=mock_participation_repo,
            fighter_repository=mock_fighter_repo
        )

        fight_data = {
            "date": date(2024, 6, 15),
            "location": "Test Arena"
        }
        # Same fighter on both sides
        participations_data = [
            {"fighter_id": fighter1_id, "side": 1, "role": "fighter"},
            {"fighter_id": fighter1_id, "side": 2, "role": "fighter"},
            {"fighter_id": fighter2_id, "side": 2, "role": "fighter"}
        ]

        # Act & Assert
        with pytest.raises(ValidationError, match="duplicate fighter"):
            await service.create_with_participants(fight_data, participations_data)

        mock_fight_repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_fight_rejects_multiple_captains_per_side(self):
        """
        Test that creating a fight with multiple captains on same side fails.

        Scenario: Cannot have multiple captains on same side
        """
        # Arrange
        from app.repositories.fight_participation_repository import FightParticipationRepository
        from app.repositories.fighter_repository import FighterRepository

        mock_fight_repo = AsyncMock(spec=FightRepository)
        mock_participation_repo = AsyncMock(spec=FightParticipationRepository)
        mock_fighter_repo = AsyncMock(spec=FighterRepository)

        fighter1_id = uuid4()
        fighter2_id = uuid4()
        fighter3_id = uuid4()
        fighter4_id = uuid4()

        service = FightService(
            fight_repository=mock_fight_repo,
            participation_repository=mock_participation_repo,
            fighter_repository=mock_fighter_repo
        )

        fight_data = {
            "date": date(2024, 6, 15),
            "location": "Test Arena"
        }
        # Two captains on side 1
        participations_data = [
            {"fighter_id": fighter1_id, "side": 1, "role": "captain"},
            {"fighter_id": fighter2_id, "side": 1, "role": "captain"},
            {"fighter_id": fighter3_id, "side": 2, "role": "fighter"},
            {"fighter_id": fighter4_id, "side": 2, "role": "fighter"}
        ]

        # Act & Assert
        with pytest.raises(ValidationError, match="multiple captains"):
            await service.create_with_participants(fight_data, participations_data)

        mock_fight_repo.create.assert_not_awaited()
