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
