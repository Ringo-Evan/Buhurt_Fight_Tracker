"""
Unit tests for FighterRepository.

Tests the data access layer for Fighter entity operations with mocked SQLAlchemy AsyncSession.
Following TDD approach - these tests are written before implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, UTC
from sqlalchemy.exc import IntegrityError

# These imports will fail until implementation exists - that's expected in TDD
from app.repositories.fighter_repository import FighterRepository
from app.models.fighter import Fighter
from app.models.team import Team
from app.models.country import Country


class TestFighterRepositoryCreate:
    """Test suite for fighter creation operations."""

    @pytest.mark.asyncio
    async def test_create_fighter_calls_session_methods_correctly(self):
        """
        Test that creating a fighter calls add(), commit(), and refresh() in correct order.

        Arrange: Mock AsyncSession and create test fighter data
        Act: Call repository.create() with fighter data
        Assert: Verify session methods called with correct arguments
        """
        # Arrange
        mock_session = AsyncMock()
        fighter_data = {
            "name": "John Smith",
            "team_id": uuid4()
        }

        repository = FighterRepository(mock_session)

        # Act
        result = await repository.create(fighter_data)

        # Assert
        assert isinstance(result, Fighter)
        assert result.name == "John Smith"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_fighter_handles_invalid_team_id_constraint_violation(self):
        """
        Test that creating a fighter with non-existent team_id raises IntegrityError.

        Arrange: Mock session to raise IntegrityError on commit
        Act: Call repository.create()
        Assert: IntegrityError is raised (FK constraint violation)
        """
        # Arrange
        mock_session = AsyncMock()
        mock_session.commit.side_effect = IntegrityError("FK violation", None, None)
        mock_session.rollback = AsyncMock()

        fighter_data = {
            "name": "John Smith",
            "team_id": uuid4()  # Non-existent team
        }

        repository = FighterRepository(mock_session)

        # Act & Assert
        with pytest.raises(IntegrityError):
            await repository.create(fighter_data)

        mock_session.rollback.assert_awaited_once()


class TestFighterRepositoryGetById:
    """Test suite for fighter retrieval by ID operations."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_fighter_with_eager_loaded_team_when_exists(self):
        """
        Test that get_by_id returns fighter with eager-loaded team and country.

        Arrange: Mock session returning fighter with team and country
        Act: Call repository.get_by_id()
        Assert: Returns fighter with nested relationships
        """
        # Arrange
        mock_session = AsyncMock()
        fighter_id = uuid4()
        team_id = uuid4()
        country_id = uuid4()

        country = Country(
            id=country_id,
            name="United States",
            code="USA",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        team = Team(
            id=team_id,
            name="Team USA",
            country_id=country_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )
        team.country = country

        fighter = Fighter(
            id=fighter_id,
            name="John Smith",
            team_id=team_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )
        fighter.team = team

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = fighter
        mock_session.execute.return_value = mock_result

        repository = FighterRepository(mock_session)

        # Act
        result = await repository.get_by_id(fighter_id)

        # Assert
        assert result is not None
        assert result.id == fighter_id
        assert result.name == "John Smith"
        assert result.team.name == "Team USA"
        assert result.team.country.code == "USA"
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_exists(self):
        """
        Test that get_by_id returns None when fighter doesn't exist.

        Arrange: Mock session returning None
        Act: Call repository.get_by_id()
        Assert: Returns None
        """
        # Arrange
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = FighterRepository(mock_session)

        # Act
        result = await repository.get_by_id(uuid4())

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_filters_soft_deleted_fighters(self):
        """
        Test that get_by_id excludes soft-deleted fighters by default.

        Arrange: Mock session with soft-deleted fighter
        Act: Call repository.get_by_id(include_deleted=False)
        Assert: Returns None (soft-deleted fighter excluded)
        """
        # Arrange
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None  # Filtered out
        mock_session.execute.return_value = mock_result

        repository = FighterRepository(mock_session)

        # Act
        result = await repository.get_by_id(uuid4(), include_deleted=False)

        # Assert
        assert result is None
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_id_as_admin_returns_soft_deleted_fighter(self):
        """
        Test that get_by_id returns soft-deleted fighter when include_deleted=True.

        Arrange: Mock session returning soft-deleted fighter
        Act: Call repository.get_by_id(include_deleted=True)
        Assert: Returns soft-deleted fighter
        """
        # Arrange
        mock_session = AsyncMock()
        fighter = Fighter(
            id=uuid4(),
            name="John Smith",
            team_id=uuid4(),
            is_deleted=True,
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = fighter
        mock_session.execute.return_value = mock_result

        repository = FighterRepository(mock_session)

        # Act
        result = await repository.get_by_id(fighter.id, include_deleted=True)

        # Assert
        assert result is not None
        assert result.is_deleted is True


class TestFighterRepositoryList:
    """Test suite for fighter list operations."""

    @pytest.mark.asyncio
    async def test_list_all_excludes_soft_deleted_fighters(self):
        """
        Test that list_all excludes soft-deleted fighters by default.

        Arrange: Mock session with active and soft-deleted fighters
        Act: Call repository.list_all()
        Assert: Returns only active fighters
        """
        # Arrange
        mock_session = AsyncMock()
        active_fighter = Fighter(
            id=uuid4(),
            name="John Smith",
            team_id=uuid4(),
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = [active_fighter]
        mock_session.execute.return_value = mock_result

        repository = FighterRepository(mock_session)

        # Act
        result = await repository.list_all()

        # Assert
        assert len(result) == 1
        assert all(not fighter.is_deleted for fighter in result)

    @pytest.mark.asyncio
    async def test_list_by_team_filters_correctly(self):
        """
        Test that list_by_team returns only fighters for specified team.

        Arrange: Mock session with fighters from different teams
        Act: Call repository.list_by_team()
        Assert: Returns only fighters from specified team
        """
        # Arrange
        mock_session = AsyncMock()
        team_id = uuid4()
        fighter1 = Fighter(
            id=uuid4(),
            name="John Smith",
            team_id=team_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )
        fighter2 = Fighter(
            id=uuid4(),
            name="Jane Doe",
            team_id=team_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = [fighter1, fighter2]
        mock_session.execute.return_value = mock_result

        repository = FighterRepository(mock_session)

        # Act
        result = await repository.list_by_team(team_id)

        # Assert
        assert len(result) == 2
        assert all(fighter.team_id == team_id for fighter in result)

    @pytest.mark.asyncio
    async def test_list_by_country_filters_correctly(self):
        """
        Test that list_by_country returns fighters from teams in specified country.

        Arrange: Mock session with fighters from teams in specified country
        Act: Call repository.list_by_country()
        Assert: Returns fighters from country's teams
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()

        fighter1 = Fighter(
            id=uuid4(),
            name="John Smith",
            team_id=uuid4(),
            is_deleted=False,
            created_at=datetime.now(UTC)
        )
        fighter2 = Fighter(
            id=uuid4(),
            name="Jane Doe",
            team_id=uuid4(),
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = [fighter1, fighter2]
        mock_session.execute.return_value = mock_result

        repository = FighterRepository(mock_session)

        # Act
        result = await repository.list_by_country(country_id)

        # Assert
        assert len(result) == 2
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_by_team_excludes_soft_deleted(self):
        """
        Test that list_by_team excludes soft-deleted fighters.

        Arrange: Mock session with active and soft-deleted fighters
        Act: Call repository.list_by_team(include_deleted=False)
        Assert: Returns only active fighters
        """
        # Arrange
        mock_session = AsyncMock()
        team_id = uuid4()
        active_fighter = Fighter(
            id=uuid4(),
            name="John Smith",
            team_id=team_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = [active_fighter]
        mock_session.execute.return_value = mock_result

        repository = FighterRepository(mock_session)

        # Act
        result = await repository.list_by_team(team_id, include_deleted=False)

        # Assert
        assert len(result) == 1
        assert all(not fighter.is_deleted for fighter in result)


class TestFighterRepositorySoftDelete:
    """Test suite for soft deletion operations."""

    @pytest.mark.asyncio
    async def test_soft_delete_sets_is_deleted_flag_to_true(self):
        """
        Test that soft delete updates is_deleted flag to True.

        Arrange: Mock session with active fighter
        Act: Call repository.soft_delete()
        Assert: Fighter is_deleted set to True, commit called
        """
        # Arrange
        mock_session = AsyncMock()
        fighter = Fighter(
            id=uuid4(),
            name="John Smith",
            team_id=uuid4(),
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = fighter
        mock_session.execute.return_value = mock_result

        repository = FighterRepository(mock_session)

        # Act
        await repository.soft_delete(fighter.id)

        # Assert
        assert fighter.is_deleted is True
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_soft_delete_raises_error_for_non_existent_fighter(self):
        """
        Test that soft deleting non-existent fighter raises ValueError.

        Arrange: Mock session returning None
        Act: Call repository.soft_delete()
        Assert: ValueError raised
        """
        # Arrange
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = FighterRepository(mock_session)

        # Act & Assert
        with pytest.raises(ValueError, match="Fighter not found"):
            await repository.soft_delete(uuid4())


class TestFighterRepositoryUpdate:
    """Test suite for fighter update operations."""

    @pytest.mark.asyncio
    async def test_update_fighter_name_succeeds(self):
        """
        Test that updating fighter name succeeds.

        Arrange: Mock session with existing fighter
        Act: Call repository.update() with new name
        Assert: Fighter name updated, commit and refresh called
        """
        # Arrange
        mock_session = AsyncMock()
        fighter_id = uuid4()
        fighter = Fighter(
            id=fighter_id,
            name="John Smith",
            team_id=uuid4(),
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = fighter
        mock_session.execute.return_value = mock_result

        repository = FighterRepository(mock_session)

        # Act
        result = await repository.update(fighter_id, {"name": "Jonathan Smith"})

        # Assert
        assert result.name == "Jonathan Smith"
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_fighter_team_succeeds(self):
        """
        Test that updating fighter's team succeeds.

        Arrange: Mock session with existing fighter
        Act: Call repository.update() with new team_id
        Assert: Fighter team_id updated
        """
        # Arrange
        mock_session = AsyncMock()
        fighter_id = uuid4()
        old_team_id = uuid4()
        new_team_id = uuid4()

        fighter = Fighter(
            id=fighter_id,
            name="John Smith",
            team_id=old_team_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = fighter
        mock_session.execute.return_value = mock_result

        repository = FighterRepository(mock_session)

        # Act
        result = await repository.update(fighter_id, {"team_id": new_team_id})

        # Assert
        assert result.team_id == new_team_id
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_fighter_raises_error_for_non_existent_fighter(self):
        """
        Test that updating non-existent fighter raises ValueError.

        Arrange: Mock session returning None
        Act: Call repository.update()
        Assert: ValueError raised
        """
        # Arrange
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = FighterRepository(mock_session)

        # Act & Assert
        with pytest.raises(ValueError, match="Fighter not found"):
            await repository.update(uuid4(), {"name": "New Name"})

    @pytest.mark.asyncio
    async def test_update_fighter_with_non_existent_team_raises_integrity_error(self):
        """
        Test that updating fighter with non-existent team raises IntegrityError.

        Arrange: Mock session to raise IntegrityError on commit
        Act: Call repository.update()
        Assert: IntegrityError raised
        """
        # Arrange
        mock_session = AsyncMock()
        fighter_id = uuid4()
        fighter = Fighter(
            id=fighter_id,
            name="John Smith",
            team_id=uuid4(),
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = fighter
        mock_session.execute.return_value = mock_result
        mock_session.commit.side_effect = IntegrityError("FK violation", None, None)
        mock_session.rollback = AsyncMock()

        repository = FighterRepository(mock_session)

        # Act & Assert
        with pytest.raises(IntegrityError):
            await repository.update(fighter_id, {"team_id": uuid4()})
