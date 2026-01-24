"""
Unit tests for FightParticipationRepository.

Tests the data access layer for FightParticipation junction table.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, UTC

from app.repositories.fight_participation_repository import FightParticipationRepository
from app.models.fight_participation import FightParticipation, ParticipationRole


class TestFightParticipationRepositoryCreate:
    """Test suite for participation creation operations."""

    @pytest.mark.asyncio
    async def test_create_participation_calls_session_methods_correctly(self):
        """Test that creating a participation works correctly."""
        # Arrange
        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        participation_data = {
            "fight_id": uuid4(),
            "fighter_id": uuid4(),
            "side": 1,
            "role": ParticipationRole.FIGHTER.value
        }

        repository = FightParticipationRepository(mock_session)

        # Act
        result = await repository.create(participation_data)

        # Assert
        assert isinstance(result, FightParticipation)
        assert result.side == 1
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_participation_with_captain_role(self):
        """Test creating a participation with captain role."""
        # Arrange
        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        participation_data = {
            "fight_id": uuid4(),
            "fighter_id": uuid4(),
            "side": 2,
            "role": ParticipationRole.CAPTAIN.value
        }

        repository = FightParticipationRepository(mock_session)

        # Act
        result = await repository.create(participation_data)

        # Assert
        assert result.role == ParticipationRole.CAPTAIN.value
        assert result.side == 2


class TestFightParticipationRepositoryGetById:
    """Test suite for participation retrieval by ID."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_participation_when_exists(self):
        """Test that get_by_id returns participation when exists."""
        # Arrange
        participation_id = uuid4()
        participation = FightParticipation(
            id=participation_id,
            fight_id=uuid4(),
            fighter_id=uuid4(),
            side=1,
            role=ParticipationRole.FIGHTER.value,
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = participation

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightParticipationRepository(mock_session)

        # Act
        result = await repository.get_by_id(participation_id)

        # Assert
        assert result == participation

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_exists(self):
        """Test that get_by_id returns None when not exists."""
        # Arrange
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightParticipationRepository(mock_session)

        # Act
        result = await repository.get_by_id(uuid4())

        # Assert
        assert result is None


class TestFightParticipationRepositoryListByFight:
    """Test suite for listing participations by fight."""

    @pytest.mark.asyncio
    async def test_list_by_fight_returns_all_participations(self):
        """Test that list_by_fight returns all participations for a fight."""
        # Arrange
        fight_id = uuid4()
        participations = [
            FightParticipation(id=uuid4(), fight_id=fight_id, fighter_id=uuid4(), side=1, role="fighter", created_at=datetime.now(UTC)),
            FightParticipation(id=uuid4(), fight_id=fight_id, fighter_id=uuid4(), side=2, role="fighter", created_at=datetime.now(UTC)),
        ]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = participations

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value = mock_scalars

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightParticipationRepository(mock_session)

        # Act
        result = await repository.list_by_fight(fight_id)

        # Assert
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_by_fight_returns_empty_when_none(self):
        """Test that list_by_fight returns empty list when no participations."""
        # Arrange
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value = mock_scalars

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightParticipationRepository(mock_session)

        # Act
        result = await repository.list_by_fight(uuid4())

        # Assert
        assert result == []


class TestFightParticipationRepositoryListByFighter:
    """Test suite for listing participations by fighter."""

    @pytest.mark.asyncio
    async def test_list_by_fighter_returns_all_fights_for_fighter(self):
        """Test that list_by_fighter returns all participations for a fighter."""
        # Arrange
        fighter_id = uuid4()
        participations = [
            FightParticipation(id=uuid4(), fight_id=uuid4(), fighter_id=fighter_id, side=1, role="fighter", created_at=datetime.now(UTC)),
        ]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = participations

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value = mock_scalars

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightParticipationRepository(mock_session)

        # Act
        result = await repository.list_by_fighter(fighter_id)

        # Assert
        assert len(result) == 1


class TestFightParticipationRepositorySoftDelete:
    """Test suite for participation soft delete."""

    @pytest.mark.asyncio
    async def test_soft_delete_sets_is_deleted_flag(self):
        """Test that soft_delete sets is_deleted to True."""
        # Arrange
        participation_id = uuid4()
        participation = FightParticipation(
            id=participation_id,
            fight_id=uuid4(),
            fighter_id=uuid4(),
            side=1,
            role="fighter",
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = participation

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightParticipationRepository(mock_session)

        # Act
        result = await repository.delete(participation_id)

        # Assert
        assert result is True
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_returns_false_for_non_existent(self):
        """Test that delete returns False for non-existent participation."""
        # Arrange
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        repository = FightParticipationRepository(mock_session)

        # Act
        result = await repository.delete(uuid4())

        # Assert
        assert result is False
