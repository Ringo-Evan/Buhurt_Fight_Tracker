"""
Unit tests for FightRepository.

Tests the data access layer for Fight entity operations with mocked SQLAlchemy AsyncSession.
Following TDD approach - these tests are written before implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import date, datetime, UTC
from sqlalchemy.exc import IntegrityError

from app.repositories.fight_repository import FightRepository
from app.models.fight import Fight


class TestFightRepositoryCreate:
    """Test suite for fight creation operations."""

    @pytest.mark.asyncio
    async def test_create_fight_calls_session_methods_correctly(self):
        """
        Test that creating a fight calls add(), commit(), and refresh() in correct order.
        """
        # Arrange
        mock_session = AsyncMock()
        mock_session.add = MagicMock()  # add() is synchronous
        fight_data = {
            "date": date(2024, 6, 15),
            "location": "IMCF World Championship 2024, Warsaw",
            "video_url": "https://youtube.com/watch?v=abc123",
            "winner_side": 1
        }

        repository = FightRepository(mock_session)

        # Act
        result = await repository.create(fight_data)

        # Assert
        assert isinstance(result, Fight)
        assert result.date == date(2024, 6, 15)
        assert result.location == "IMCF World Championship 2024, Warsaw"
        assert result.winner_side == 1
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_fight_without_winner_succeeds(self):
        """
        Test that creating a fight without winner_side (draw/unknown) works.
        """
        # Arrange
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        fight_data = {
            "date": date(2024, 6, 15),
            "location": "Local Tournament",
            "video_url": None,
            "winner_side": None
        }

        repository = FightRepository(mock_session)

        # Act
        result = await repository.create(fight_data)

        # Assert
        assert result.winner_side is None
        assert result.video_url is None

    @pytest.mark.asyncio
    async def test_create_fight_handles_database_error(self):
        """
        Test that database errors during creation are propagated.
        """
        # Arrange
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit.side_effect = IntegrityError("DB error", None, None)
        mock_session.rollback = AsyncMock()

        fight_data = {
            "date": date(2024, 6, 15),
            "location": "Test Location"
        }

        repository = FightRepository(mock_session)

        # Act & Assert
        with pytest.raises(IntegrityError):
            await repository.create(fight_data)

        mock_session.rollback.assert_awaited_once()


class TestFightRepositoryGetById:
    """Test suite for fight retrieval by ID operations."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_fight_when_exists(self):
        """
        Test that get_by_id returns the fight when it exists.
        """
        # Arrange
        fight_id = uuid4()
        fight = Fight(
            id=fight_id,
            date=date(2024, 6, 15),
            location="Test Location",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fight

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightRepository(mock_session)

        # Act
        result = await repository.get_by_id(fight_id)

        # Assert
        assert result == fight
        assert result.id == fight_id

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_exists(self):
        """
        Test that get_by_id returns None when fight doesn't exist.
        """
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightRepository(mock_session)

        # Act
        result = await repository.get_by_id(uuid4())

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_filters_soft_deleted_fights(self):
        """
        Test that get_by_id filters out soft-deleted fights by default.
        """
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # Filtered out

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightRepository(mock_session)

        # Act
        result = await repository.get_by_id(uuid4())

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_as_admin_returns_soft_deleted_fight(self):
        """
        Test that get_by_id with include_deleted=True returns soft-deleted fights.
        """
        # Arrange
        fight_id = uuid4()
        fight = Fight(
            id=fight_id,
            date=date(2024, 6, 15),
            location="Deleted Fight",
            is_deleted=True,
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fight

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightRepository(mock_session)

        # Act
        result = await repository.get_by_id(fight_id, include_deleted=True)

        # Assert
        assert result == fight
        assert result.is_deleted is True


class TestFightRepositoryList:
    """Test suite for fight listing operations."""

    @pytest.mark.asyncio
    async def test_list_all_excludes_soft_deleted_fights(self):
        """
        Test that list_all excludes soft-deleted fights by default.
        """
        # Arrange
        fights = [
            Fight(id=uuid4(), date=date(2024, 1, 1), location="Fight 1", is_deleted=False, created_at=datetime.now(UTC)),
            Fight(id=uuid4(), date=date(2024, 2, 1), location="Fight 2", is_deleted=False, created_at=datetime.now(UTC)),
        ]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = fights

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightRepository(mock_session)

        # Act
        result = await repository.list_all()

        # Assert
        assert len(result) == 2
        assert all(not f.is_deleted for f in result)

    @pytest.mark.asyncio
    async def test_list_all_returns_empty_list_when_no_fights(self):
        """
        Test that list_all returns empty list when no fights exist.
        """
        # Arrange
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightRepository(mock_session)

        # Act
        result = await repository.list_all()

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_list_by_date_range_filters_correctly(self):
        """
        Test that list_by_date_range returns fights within the specified range.
        """
        # Arrange
        fights = [
            Fight(id=uuid4(), date=date(2024, 6, 15), location="Fight 1", is_deleted=False, created_at=datetime.now(UTC)),
        ]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = fights

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightRepository(mock_session)

        # Act
        result = await repository.list_by_date_range(
            start_date=date(2024, 6, 1),
            end_date=date(2024, 6, 30)
        )

        # Assert
        assert len(result) == 1


class TestFightRepositorySoftDelete:
    """Test suite for fight soft delete operations."""

    @pytest.mark.asyncio
    async def test_soft_delete_sets_is_deleted_flag_to_true(self):
        """
        Test that soft_delete sets the is_deleted flag to True.
        """
        # Arrange
        fight_id = uuid4()
        fight = Fight(
            id=fight_id,
            date=date(2024, 6, 15),
            location="Test Fight",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fight

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightRepository(mock_session)

        # Act
        await repository.soft_delete(fight_id)

        # Assert
        assert fight.is_deleted is True
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_soft_delete_raises_error_for_non_existent_fight(self):
        """
        Test that soft_delete raises ValueError for non-existent fight.
        """
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightRepository(mock_session)

        # Act & Assert
        with pytest.raises(ValueError, match="Fight not found"):
            await repository.soft_delete(uuid4())


class TestFightRepositoryUpdate:
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
            location="Old Location",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fight

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightRepository(mock_session)

        # Act
        result = await repository.update(fight_id, {"location": "New Location"})

        # Assert
        assert result.location == "New Location"
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_fight_winner_side_succeeds(self):
        """
        Test that updating winner_side works correctly.
        """
        # Arrange
        fight_id = uuid4()
        fight = Fight(
            id=fight_id,
            date=date(2024, 6, 15),
            location="Test",
            winner_side=None,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fight

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightRepository(mock_session)

        # Act
        result = await repository.update(fight_id, {"winner_side": 2})

        # Assert
        assert result.winner_side == 2

    @pytest.mark.asyncio
    async def test_update_fight_raises_error_for_non_existent_fight(self):
        """
        Test that update raises ValueError for non-existent fight.
        """
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightRepository(mock_session)

        # Act & Assert
        with pytest.raises(ValueError, match="Fight not found"):
            await repository.update(uuid4(), {"location": "New"})
