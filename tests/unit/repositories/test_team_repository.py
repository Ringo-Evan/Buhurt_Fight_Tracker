"""
Unit tests for TeamRepository.

Tests the data access layer for Team entity operations with mocked SQLAlchemy AsyncSession.
Following TDD approach - these tests follow the same patterns as CountryRepository tests.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, UTC
from sqlalchemy.exc import IntegrityError

from app.repositories.team_repository import TeamRepository
from app.models.team import Team
from app.models.country import Country


class TestTeamRepositoryCreate:
    """Test suite for team creation operations."""

    @pytest.mark.asyncio
    async def test_create_team_calls_session_methods_correctly(self):
        """
        Test that creating a team calls add(), commit(), and refresh() in correct order.

        Arrange: Mock AsyncSession and create test team data
        Act: Call repository.create() with team data
        Assert: Verify session methods called with correct arguments
        """
        # Arrange
        mock_session = AsyncMock()
        mock_session.add = MagicMock()  # session.add() is not async
        repository = TeamRepository(mock_session)

        country_id = uuid4()
        team_data = {
            "name": "Team USA",
            "country_id": country_id
        }

        # Act
        result = await repository.create(team_data)

        # Assert
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()

        # Verify the created team has expected attributes
        assert result.name == "Team USA"
        assert result.country_id == country_id
        assert result.is_deleted is False
        assert result.id is not None
        assert result.created_at is not None

    @pytest.mark.asyncio
    async def test_create_team_handles_invalid_country_id_constraint_violation(self):
        """
        Test that creating a team with non-existent country_id raises IntegrityError.

        Arrange: Mock AsyncSession to raise IntegrityError on commit (FK violation)
        Act: Attempt to create team with invalid country_id
        Assert: IntegrityError is propagated
        """
        # Arrange
        mock_session = AsyncMock()
        mock_session.add = MagicMock()  # session.add() is not async
        mock_session.commit.side_effect = IntegrityError(
            statement="INSERT INTO teams...",
            params={},
            orig=Exception("foreign key constraint fails")
        )
        repository = TeamRepository(mock_session)

        invalid_country_id = uuid4()
        team_data = {
            "name": "Team Nowhere",
            "country_id": invalid_country_id
        }

        # Act & Assert
        with pytest.raises(IntegrityError):
            await repository.create(team_data)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
        mock_session.rollback.assert_awaited_once()


class TestTeamRepositoryGetById:
    """Test suite for retrieving teams by ID."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_team_with_eager_loaded_country_when_exists(self):
        """
        Test successful team lookup by ID with eager-loaded country relationship.

        Arrange: Mock session with execute returning a team with country
        Act: Call repository.get_by_id()
        Assert: Returns the team object with country relationship loaded
        """
        # Arrange
        mock_session = AsyncMock()
        team_id = uuid4()
        country_id = uuid4()

        # Create mock country
        mock_country = Country(
            id=country_id,
            name="United States",
            code="USA",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        # Create mock team with country relationship
        expected_team = Team(
            id=team_id,
            name="Team USA",
            country_id=country_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )
        expected_team.country = mock_country

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = expected_team
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        # Act
        result = await repository.get_by_id(team_id)

        # Assert
        assert result == expected_team
        assert result.id == team_id
        assert result.name == "Team USA"
        assert result.country is not None
        assert result.country.code == "USA"
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_exists(self):
        """
        Test that get_by_id returns None for non-existent team.

        Arrange: Mock session returning None
        Act: Call repository.get_by_id() with non-existent ID
        Assert: Returns None
        """
        # Arrange
        mock_session = AsyncMock()
        team_id = uuid4()

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        # Act
        result = await repository.get_by_id(team_id)

        # Assert
        assert result is None
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_id_filters_soft_deleted_teams(self):
        """
        Test that get_by_id excludes soft-deleted teams.

        Arrange: Mock session that would return a soft-deleted team
        Act: Call repository.get_by_id()
        Assert: Returns None (soft-deleted filtered out)
        """
        # Arrange
        mock_session = AsyncMock()
        team_id = uuid4()

        # The query should filter is_deleted=False, so it returns None
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        # Act
        result = await repository.get_by_id(team_id)

        # Assert
        assert result is None
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_id_as_admin_returns_soft_deleted_team(self):
        """
        Test that get_by_id with include_deleted=True returns soft-deleted teams.

        Arrange: Mock session returning a soft-deleted team
        Act: Call repository.get_by_id(include_deleted=True)
        Assert: Returns the soft-deleted team
        """
        # Arrange
        mock_session = AsyncMock()
        team_id = uuid4()
        country_id = uuid4()

        mock_country = Country(
            id=country_id,
            name="United States",
            code="USA",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        deleted_team = Team(
            id=team_id,
            name="Team USA",
            country_id=country_id,
            is_deleted=True,
            created_at=datetime.now(UTC)
        )
        deleted_team.country = mock_country

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = deleted_team
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        # Act
        result = await repository.get_by_id(team_id, include_deleted=True)

        # Assert
        assert result == deleted_team
        assert result.is_deleted is True
        assert result.country is not None
        mock_session.execute.assert_awaited_once()


class TestTeamRepositoryList:
    """Test suite for listing teams."""

    @pytest.mark.asyncio
    async def test_list_all_excludes_soft_deleted_teams(self):
        """
        Test that list_all excludes soft-deleted entries.

        Arrange: Mock session returning only active teams
        Act: Call repository.list_all()
        Assert: Returns list without deleted teams
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()

        mock_country = Country(
            id=country_id,
            name="United States",
            code="USA",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        active_teams = [
            Team(
                id=uuid4(),
                name="Team USA",
                country_id=country_id,
                is_deleted=False,
                created_at=datetime.now(UTC)
            ),
            Team(
                id=uuid4(),
                name="Team Poland",
                country_id=country_id,
                is_deleted=False,
                created_at=datetime.now(UTC)
            )
        ]
        # Attach country relationship to teams
        for team in active_teams:
            team.country = mock_country

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = active_teams
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        # Act
        result = await repository.list_all()

        # Assert
        assert len(result) == 2
        assert all(not team.is_deleted for team in result)
        assert all(team.country is not None for team in result)
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_all_returns_empty_list_when_no_active_teams(self):
        """
        Test that list_all returns empty list when no active teams exist.

        Arrange: Mock session returning empty list
        Act: Call repository.list_all()
        Assert: Returns empty list
        """
        # Arrange
        mock_session = AsyncMock()

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        # Act
        result = await repository.list_all()

        # Assert
        assert result == []
        assert len(result) == 0
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_all_as_admin_includes_soft_deleted_teams(self):
        """
        Test that list_all with include_deleted=True includes soft-deleted teams.

        Arrange: Mock session returning both active and deleted teams
        Act: Call repository.list_all(include_deleted=True)
        Assert: Returns list with both active and deleted teams
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()

        mock_country = Country(
            id=country_id,
            name="United States",
            code="USA",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        all_teams = [
            Team(
                id=uuid4(),
                name="Team USA",
                country_id=country_id,
                is_deleted=False,
                created_at=datetime.now(UTC)
            ),
            Team(
                id=uuid4(),
                name="Team Poland",
                country_id=country_id,
                is_deleted=True,  # Soft-deleted
                created_at=datetime.now(UTC)
            ),
            Team(
                id=uuid4(),
                name="Team Germany",
                country_id=country_id,
                is_deleted=False,
                created_at=datetime.now(UTC)
            )
        ]
        for team in all_teams:
            team.country = mock_country

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = all_teams
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        # Act
        result = await repository.list_all(include_deleted=True)

        # Assert
        assert len(result) == 3
        assert any(team.is_deleted for team in result)
        assert all(team.country is not None for team in result)
        mock_session.execute.assert_awaited_once()


class TestTeamRepositoryListByCountry:
    """Test suite for listing teams by country."""

    @pytest.mark.asyncio
    async def test_list_by_country_returns_teams_for_specified_country(self):
        """
        Test that list_by_country returns only teams for the specified country.

        Arrange: Mock session returning teams filtered by country_id
        Act: Call repository.list_by_country()
        Assert: Returns teams for the specified country only
        """
        # Arrange
        mock_session = AsyncMock()
        usa_country_id = uuid4()
        poland_country_id = uuid4()

        mock_usa_country = Country(
            id=usa_country_id,
            name="United States",
            code="USA",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        usa_teams = [
            Team(
                id=uuid4(),
                name="Team USA 1",
                country_id=usa_country_id,
                is_deleted=False,
                created_at=datetime.now(UTC)
            ),
            Team(
                id=uuid4(),
                name="Team USA 2",
                country_id=usa_country_id,
                is_deleted=False,
                created_at=datetime.now(UTC)
            )
        ]
        for team in usa_teams:
            team.country = mock_usa_country

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = usa_teams
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        # Act
        result = await repository.list_by_country(usa_country_id)

        # Assert
        assert len(result) == 2
        assert all(team.country_id == usa_country_id for team in result)
        assert all(not team.is_deleted for team in result)
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_by_country_excludes_soft_deleted_teams(self):
        """
        Test that list_by_country excludes soft-deleted teams.

        Arrange: Mock session returning only active teams for country
        Act: Call repository.list_by_country()
        Assert: Returns list without deleted teams
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()

        mock_country = Country(
            id=country_id,
            name="United States",
            code="USA",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        active_teams = [
            Team(
                id=uuid4(),
                name="Team USA",
                country_id=country_id,
                is_deleted=False,
                created_at=datetime.now(UTC)
            )
        ]
        for team in active_teams:
            team.country = mock_country

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = active_teams
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        # Act
        result = await repository.list_by_country(country_id)

        # Assert
        assert len(result) == 1
        assert all(not team.is_deleted for team in result)
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_by_country_returns_empty_list_when_no_teams_exist(self):
        """
        Test that list_by_country returns empty list when no teams exist for country.

        Arrange: Mock session returning empty list
        Act: Call repository.list_by_country()
        Assert: Returns empty list
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        # Act
        result = await repository.list_by_country(country_id)

        # Assert
        assert result == []
        assert len(result) == 0
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_by_country_as_admin_includes_soft_deleted_teams(self):
        """
        Test that list_by_country with include_deleted=True includes soft-deleted teams.

        Arrange: Mock session returning both active and deleted teams
        Act: Call repository.list_by_country(include_deleted=True)
        Assert: Returns list with both active and deleted teams
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()

        mock_country = Country(
            id=country_id,
            name="United States",
            code="USA",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        all_teams = [
            Team(
                id=uuid4(),
                name="Team USA 1",
                country_id=country_id,
                is_deleted=False,
                created_at=datetime.now(UTC)
            ),
            Team(
                id=uuid4(),
                name="Team USA 2",
                country_id=country_id,
                is_deleted=True,  # Soft-deleted
                created_at=datetime.now(UTC)
            )
        ]
        for team in all_teams:
            team.country = mock_country

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = all_teams
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        # Act
        result = await repository.list_by_country(country_id, include_deleted=True)

        # Assert
        assert len(result) == 2
        assert any(team.is_deleted for team in result)
        mock_session.execute.assert_awaited_once()


class TestTeamRepositorySoftDelete:
    """Test suite for soft deletion operations."""

    @pytest.mark.asyncio
    async def test_soft_delete_sets_is_deleted_flag_to_true(self):
        """
        Test that soft delete updates is_deleted flag to True.

        Arrange: Mock session and existing team
        Act: Call repository.soft_delete()
        Assert: is_deleted flag set to True and changes committed
        """
        # Arrange
        mock_session = AsyncMock()
        team_id = uuid4()
        country_id = uuid4()

        mock_country = Country(
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
        team.country = mock_country

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = team
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        # Act
        await repository.soft_delete(team_id)

        # Assert
        assert team.is_deleted is True
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_soft_delete_raises_error_for_non_existent_team(self):
        """
        Test that soft delete raises error for non-existent team.

        Arrange: Mock session returning None for team lookup
        Act: Attempt to soft delete non-existent team
        Assert: Raises appropriate exception
        """
        # Arrange
        mock_session = AsyncMock()
        team_id = uuid4()

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        # Act & Assert
        with pytest.raises(ValueError, match="Team not found"):
            await repository.soft_delete(team_id)

        mock_session.commit.assert_not_awaited()


class TestTeamRepositoryUpdate:
    """Test suite for team update operations."""

    @pytest.mark.asyncio
    async def test_update_team_name_succeeds(self):
        """
        Test that updating a team's name succeeds.

        Arrange: Mock session with existing team
        Act: Call repository.update() with new name
        Assert: Name updated and changes committed
        """
        # Arrange
        mock_session = AsyncMock()
        team_id = uuid4()
        country_id = uuid4()

        mock_country = Country(
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
        team.country = mock_country

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = team
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        update_data = {"name": "Team United States"}

        # Act
        result = await repository.update(team_id, update_data)

        # Assert
        assert result.name == "Team United States"
        assert result.country_id == country_id
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_team_country_id_succeeds(self):
        """
        Test that updating a team's country_id succeeds.

        Arrange: Mock session with existing team
        Act: Call repository.update() with new country_id
        Assert: country_id updated and changes committed
        """
        # Arrange
        mock_session = AsyncMock()
        team_id = uuid4()
        old_country_id = uuid4()
        new_country_id = uuid4()

        mock_old_country = Country(
            id=old_country_id,
            name="United States",
            code="USA",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        team = Team(
            id=team_id,
            name="Team International",
            country_id=old_country_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )
        team.country = mock_old_country

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = team
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        update_data = {"country_id": new_country_id}

        # Act
        result = await repository.update(team_id, update_data)

        # Assert
        assert result.name == "Team International"
        assert result.country_id == new_country_id
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_team_with_invalid_country_id_raises_integrity_error(self):
        """
        Test that updating to invalid country_id raises IntegrityError.

        Arrange: Mock session raising IntegrityError on commit (FK violation)
        Act: Attempt to update team with invalid country_id
        Assert: IntegrityError is propagated
        """
        # Arrange
        mock_session = AsyncMock()
        team_id = uuid4()
        country_id = uuid4()
        invalid_country_id = uuid4()

        mock_country = Country(
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
        team.country = mock_country

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = team
        mock_session.execute.return_value = mock_result
        mock_session.commit.side_effect = IntegrityError(
            statement="UPDATE teams...",
            params={},
            orig=Exception("foreign key constraint fails")
        )

        repository = TeamRepository(mock_session)

        update_data = {"country_id": invalid_country_id}

        # Act & Assert
        with pytest.raises(IntegrityError):
            await repository.update(team_id, update_data)

        mock_session.commit.assert_awaited_once()
        mock_session.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_team_raises_error_for_non_existent_team(self):
        """
        Test that update raises error for non-existent team.

        Arrange: Mock session returning None for team lookup
        Act: Attempt to update non-existent team
        Assert: Raises ValueError
        """
        # Arrange
        mock_session = AsyncMock()
        team_id = uuid4()

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        update_data = {"name": "New Name"}

        # Act & Assert
        with pytest.raises(ValueError, match="Team not found"):
            await repository.update(team_id, update_data)

        mock_session.commit.assert_not_awaited()


class TestTeamRepositoryPermanentDelete:
    """Test suite for permanent deletion operations."""

    @pytest.mark.asyncio
    async def test_permanent_delete_removes_team_from_database(self):
        """
        Test that permanent delete removes team from database.

        Arrange: Mock session with soft-deleted team
        Act: Call repository.permanent_delete()
        Assert: session.delete() called and changes committed
        """
        # Arrange
        mock_session = AsyncMock()
        team_id = uuid4()
        country_id = uuid4()

        mock_country = Country(
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
            is_deleted=True,
            created_at=datetime.now(UTC)
        )
        team.country = mock_country

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = team
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        # Act
        await repository.permanent_delete(team_id)

        # Assert
        mock_session.delete.assert_called_once_with(team)
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_permanent_delete_raises_error_for_non_existent_team(self):
        """
        Test that permanent delete raises error for non-existent team.

        Arrange: Mock session returning None
        Act: Attempt to permanently delete non-existent team
        Assert: Raises ValueError
        """
        # Arrange
        mock_session = AsyncMock()
        team_id = uuid4()

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = TeamRepository(mock_session)

        # Act & Assert
        with pytest.raises(ValueError, match="Team not found"):
            await repository.permanent_delete(team_id)

        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_awaited()
