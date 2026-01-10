"""
Unit tests for TeamService.

Tests the business logic layer for Team entity operations with mocked repositories.
Follows TDD approach with comprehensive coverage of all service methods.
Tests both TeamRepository and CountryRepository interactions.
"""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, UTC

from app.services.team_service import TeamService
from app.repositories.team_repository import TeamRepository
from app.repositories.country_repository import CountryRepository
from app.models.team import Team
from app.models.country import Country
from app.exceptions import (
    TeamNotFoundError,
    InvalidCountryError,
    ValidationError
)


class TestTeamServiceCreate:
    """Test suite for team creation business logic."""

    @pytest.mark.asyncio
    async def test_create_team_with_valid_data_succeeds(self):
        """
        Test that creating a team with valid data and active country succeeds (happy path).

        Arrange: Mock repositories with active country and no existing team
        Act: Call service.create() with valid data
        Assert: Repository create called and team returned
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        country_id = uuid4()
        team_data = {
            "name": "Team USA",
            "country_id": country_id
        }

        active_country = Country(
            id=country_id,
            name="United States",
            code="USA",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        expected_team = Team(
            id=uuid4(),
            name="Team USA",
            country_id=country_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_country_repository.get_by_id.return_value = active_country
        mock_team_repository.create.return_value = expected_team

        # Act
        result = await service.create(team_data)

        # Assert
        assert result == expected_team
        assert result.name == "Team USA"
        assert result.country_id == country_id
        mock_country_repository.get_by_id.assert_awaited_once_with(country_id, include_deleted=False)
        mock_team_repository.create.assert_awaited_once_with(team_data)

    @pytest.mark.asyncio
    async def test_create_team_rejects_empty_name(self):
        """
        Test that creating a team with empty name is rejected.

        Arrange: Mock repositories and prepare data with empty name
        Act: Attempt to create team with empty name
        Assert: ValidationError raised
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        country_id = uuid4()
        team_data = {
            "name": "",
            "country_id": country_id
        }

        # Act & Assert
        with pytest.raises(ValidationError, match="Team name is required"):
            await service.create(team_data)

        mock_country_repository.get_by_id.assert_not_awaited()
        mock_team_repository.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_team_rejects_whitespace_only_name(self):
        """
        Test that creating a team with whitespace-only name is rejected.

        Arrange: Mock repositories and prepare data with whitespace name
        Act: Attempt to create team with whitespace name
        Assert: ValidationError raised
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        country_id = uuid4()
        team_data = {
            "name": "   ",
            "country_id": country_id
        }

        # Act & Assert
        with pytest.raises(ValidationError, match="Team name is required"):
            await service.create(team_data)

        mock_country_repository.get_by_id.assert_not_awaited()
        mock_team_repository.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_team_rejects_name_exceeding_max_length(self):
        """
        Test that creating a team with name exceeding 100 characters is rejected.

        Arrange: Mock repositories and prepare data with long name
        Act: Attempt to create team with name > 100 chars
        Assert: ValidationError raised
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        country_id = uuid4()
        team_data = {
            "name": "A" * 101,  # 101 characters
            "country_id": country_id
        }

        # Act & Assert
        with pytest.raises(ValidationError, match="Team name must not exceed 100 characters"):
            await service.create(team_data)

        mock_country_repository.get_by_id.assert_not_awaited()
        mock_team_repository.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_team_rejects_missing_country_id(self):
        """
        Test that creating a team without country_id is rejected.

        Arrange: Mock repositories and prepare data without country_id
        Act: Attempt to create team without country_id
        Assert: ValidationError raised
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        team_data = {
            "name": "Team USA"
        }

        # Act & Assert
        with pytest.raises(ValidationError, match="country_id is required"):
            await service.create(team_data)

        mock_country_repository.get_by_id.assert_not_awaited()
        mock_team_repository.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_team_rejects_non_existent_country(self):
        """
        Test that creating a team with non-existent country is rejected.

        Arrange: Mock country repository returning None for both queries
        Act: Attempt to create team with non-existent country
        Assert: InvalidCountryError raised
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        country_id = uuid4()
        team_data = {
            "name": "Team USA",
            "country_id": country_id
        }

        # Country doesn't exist at all
        mock_country_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(InvalidCountryError, match="Country not found"):
            await service.create(team_data)

        # Should check without deleted first, then with deleted
        assert mock_country_repository.get_by_id.await_count == 2
        mock_country_repository.get_by_id.assert_any_await(country_id, include_deleted=False)
        mock_country_repository.get_by_id.assert_any_await(country_id, include_deleted=True)
        mock_team_repository.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_team_rejects_soft_deleted_country(self):
        """
        Test that creating a team with soft-deleted country is rejected.

        Arrange: Mock country repository returning None (active) but deleted country exists
        Act: Attempt to create team with soft-deleted country
        Assert: InvalidCountryError raised with "not active" message
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        country_id = uuid4()
        team_data = {
            "name": "Team USA",
            "country_id": country_id
        }

        deleted_country = Country(
            id=country_id,
            name="United States",
            code="USA",
            is_deleted=True,
            created_at=datetime.now(UTC)
        )

        # First call (include_deleted=False) returns None
        # Second call (include_deleted=True) returns soft-deleted country
        mock_country_repository.get_by_id.side_effect = [None, deleted_country]

        # Act & Assert
        with pytest.raises(InvalidCountryError, match="Country is not active"):
            await service.create(team_data)

        assert mock_country_repository.get_by_id.await_count == 2
        mock_country_repository.get_by_id.assert_any_await(country_id, include_deleted=False)
        mock_country_repository.get_by_id.assert_any_await(country_id, include_deleted=True)
        mock_team_repository.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_team_handles_foreign_key_constraint_violation(self):
        """
        Test that FK constraint violation is converted to InvalidCountryError.

        Arrange: Mock repository raising IntegrityError on create
        Act: Attempt to create team
        Assert: InvalidCountryError raised
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        country_id = uuid4()
        team_data = {
            "name": "Team USA",
            "country_id": country_id
        }

        active_country = Country(
            id=country_id,
            name="United States",
            code="USA",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_country_repository.get_by_id.return_value = active_country

        # Repository raises IntegrityError (FK constraint)
        from sqlalchemy.exc import IntegrityError
        mock_team_repository.create.side_effect = IntegrityError(
            statement="INSERT INTO teams...",
            params={},
            orig=Exception("foreign key constraint fails")
        )

        # Act & Assert
        with pytest.raises(InvalidCountryError, match="Country not found"):
            await service.create(team_data)

        mock_team_repository.create.assert_awaited_once_with(team_data)


class TestTeamServiceRetrieve:
    """Test suite for team retrieval business logic."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_team_when_exists(self):
        """
        Test successful retrieval of team by ID.

        Arrange: Mock repository returning team
        Act: Call service.get_by_id()
        Assert: Returns team object
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        team_id = uuid4()
        country_id = uuid4()
        expected_team = Team(
            id=team_id,
            name="Team USA",
            country_id=country_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_team_repository.get_by_id.return_value = expected_team

        # Act
        result = await service.get_by_id(team_id)

        # Assert
        assert result == expected_team
        assert result.id == team_id
        mock_team_repository.get_by_id.assert_awaited_once_with(team_id, include_deleted=False)

    @pytest.mark.asyncio
    async def test_get_by_id_raises_not_found_error_when_not_exists(self):
        """
        Test that get_by_id raises TeamNotFoundError for non-existent team.

        Arrange: Mock repository returning None
        Act: Call service.get_by_id()
        Assert: TeamNotFoundError raised
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        team_id = uuid4()
        mock_team_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(TeamNotFoundError, match="Team not found"):
            await service.get_by_id(team_id)

        mock_team_repository.get_by_id.assert_awaited_once_with(team_id, include_deleted=False)

    @pytest.mark.asyncio
    async def test_get_by_id_as_admin_returns_deleted_team(self):
        """
        Test that admin can retrieve soft-deleted teams.

        Arrange: Mock repository with include_deleted flag
        Act: Call service.get_by_id(include_deleted=True)
        Assert: Returns deleted team
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        team_id = uuid4()
        country_id = uuid4()
        deleted_team = Team(
            id=team_id,
            name="Team USA",
            country_id=country_id,
            is_deleted=True,
            created_at=datetime.now(UTC)
        )

        mock_team_repository.get_by_id.return_value = deleted_team

        # Act
        result = await service.get_by_id(team_id, include_deleted=True)

        # Assert
        assert result == deleted_team
        assert result.is_deleted is True
        mock_team_repository.get_by_id.assert_awaited_once_with(team_id, include_deleted=True)

    @pytest.mark.asyncio
    async def test_list_all_returns_all_teams(self):
        """
        Test successful retrieval of all teams.

        Arrange: Mock repository returning list of teams
        Act: Call service.list_all()
        Assert: Returns list of teams
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        country_id = uuid4()
        expected_teams = [
            Team(
                id=uuid4(),
                name="Team USA",
                country_id=country_id,
                is_deleted=False,
                created_at=datetime.now(UTC)
            ),
            Team(
                id=uuid4(),
                name="Team Canada",
                country_id=country_id,
                is_deleted=False,
                created_at=datetime.now(UTC)
            )
        ]

        mock_team_repository.list_all.return_value = expected_teams

        # Act
        result = await service.list_all()

        # Assert
        assert result == expected_teams
        assert len(result) == 2
        mock_team_repository.list_all.assert_awaited_once_with(include_deleted=False)

    @pytest.mark.asyncio
    async def test_list_all_as_admin_includes_deleted_teams(self):
        """
        Test that admin can list all teams including deleted ones.

        Arrange: Mock repository returning active and deleted teams
        Act: Call service.list_all(include_deleted=True)
        Assert: Returns all teams including deleted
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        country_id = uuid4()
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
                name="Team Canada",
                country_id=country_id,
                is_deleted=True,
                created_at=datetime.now(UTC)
            )
        ]

        mock_team_repository.list_all.return_value = all_teams

        # Act
        result = await service.list_all(include_deleted=True)

        # Assert
        assert len(result) == 2
        assert any(t.is_deleted for t in result)
        mock_team_repository.list_all.assert_awaited_once_with(include_deleted=True)

    @pytest.mark.asyncio
    async def test_list_by_country_returns_teams_for_country(self):
        """
        Test successful retrieval of teams filtered by country.

        Arrange: Mock repository returning teams for specific country
        Act: Call service.list_by_country()
        Assert: Returns teams for specified country
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        country_id = uuid4()
        expected_teams = [
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
                is_deleted=False,
                created_at=datetime.now(UTC)
            )
        ]

        mock_team_repository.list_by_country.return_value = expected_teams

        # Act
        result = await service.list_by_country(country_id)

        # Assert
        assert result == expected_teams
        assert len(result) == 2
        assert all(t.country_id == country_id for t in result)
        mock_team_repository.list_by_country.assert_awaited_once_with(country_id, include_deleted=False)

    @pytest.mark.asyncio
    async def test_list_by_country_returns_empty_list_when_no_teams(self):
        """
        Test that list_by_country returns empty list when no teams exist.

        Arrange: Mock repository returning empty list
        Act: Call service.list_by_country()
        Assert: Returns empty list
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        country_id = uuid4()
        mock_team_repository.list_by_country.return_value = []

        # Act
        result = await service.list_by_country(country_id)

        # Assert
        assert result == []
        mock_team_repository.list_by_country.assert_awaited_once_with(country_id, include_deleted=False)


class TestTeamServiceUpdate:
    """Test suite for team update business logic."""

    @pytest.mark.asyncio
    async def test_update_team_name_succeeds(self):
        """
        Test that updating a team's name with valid data succeeds.

        Arrange: Mock repositories with existing team
        Act: Call service.update() with new name
        Assert: Repository update called and updated team returned
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        team_id = uuid4()
        country_id = uuid4()
        update_data = {"name": "Team USA Elite"}

        existing_team = Team(
            id=team_id,
            name="Team USA",
            country_id=country_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        updated_team = Team(
            id=team_id,
            name="Team USA Elite",
            country_id=country_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_team_repository.get_by_id.return_value = existing_team
        mock_team_repository.update.return_value = updated_team

        # Act
        result = await service.update(team_id, update_data)

        # Assert
        assert result == updated_team
        assert result.name == "Team USA Elite"
        mock_team_repository.get_by_id.assert_awaited_once_with(team_id, include_deleted=True)
        mock_team_repository.update.assert_awaited_once_with(team_id, update_data)

    @pytest.mark.asyncio
    async def test_update_team_country_to_valid_country_succeeds(self):
        """
        Test that updating team's country to a valid active country succeeds.

        Arrange: Mock repositories with existing team and valid new country
        Act: Call service.update() with new country_id
        Assert: Country validation performed and update succeeds
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        team_id = uuid4()
        old_country_id = uuid4()
        new_country_id = uuid4()
        update_data = {"country_id": new_country_id}

        existing_team = Team(
            id=team_id,
            name="Team USA",
            country_id=old_country_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        new_country = Country(
            id=new_country_id,
            name="Canada",
            code="CAN",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        updated_team = Team(
            id=team_id,
            name="Team USA",
            country_id=new_country_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_team_repository.get_by_id.return_value = existing_team
        mock_country_repository.get_by_id.return_value = new_country
        mock_team_repository.update.return_value = updated_team

        # Act
        result = await service.update(team_id, update_data)

        # Assert
        assert result == updated_team
        assert result.country_id == new_country_id
        mock_team_repository.get_by_id.assert_awaited_once_with(team_id, include_deleted=True)
        mock_country_repository.get_by_id.assert_awaited_once_with(new_country_id, include_deleted=False)
        mock_team_repository.update.assert_awaited_once_with(team_id, update_data)

    @pytest.mark.asyncio
    async def test_update_team_rejects_empty_name(self):
        """
        Test that updating team to empty name is rejected.

        Arrange: Mock repositories
        Act: Attempt to update with empty name
        Assert: ValidationError raised before repository call
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        team_id = uuid4()
        country_id = uuid4()
        update_data = {"name": ""}

        existing_team = Team(
            id=team_id,
            name="Team USA",
            country_id=country_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_team_repository.get_by_id.return_value = existing_team

        # Act & Assert
        with pytest.raises(ValidationError, match="Team name is required"):
            await service.update(team_id, update_data)

        mock_team_repository.get_by_id.assert_awaited_once_with(team_id, include_deleted=True)
        mock_team_repository.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_team_rejects_name_exceeding_max_length(self):
        """
        Test that updating team to name exceeding 100 characters is rejected.

        Arrange: Mock repositories
        Act: Attempt to update with name > 100 chars
        Assert: ValidationError raised
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        team_id = uuid4()
        country_id = uuid4()
        update_data = {"name": "A" * 101}

        existing_team = Team(
            id=team_id,
            name="Team USA",
            country_id=country_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_team_repository.get_by_id.return_value = existing_team

        # Act & Assert
        with pytest.raises(ValidationError, match="Team name must not exceed 100 characters"):
            await service.update(team_id, update_data)

        mock_team_repository.get_by_id.assert_awaited_once_with(team_id, include_deleted=True)
        mock_team_repository.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_team_rejects_non_existent_country(self):
        """
        Test that updating team to non-existent country is rejected.

        Arrange: Mock country repository returning None
        Act: Attempt to update with non-existent country_id
        Assert: InvalidCountryError raised
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        team_id = uuid4()
        old_country_id = uuid4()
        new_country_id = uuid4()
        update_data = {"country_id": new_country_id}

        existing_team = Team(
            id=team_id,
            name="Team USA",
            country_id=old_country_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_team_repository.get_by_id.return_value = existing_team
        # Country doesn't exist
        mock_country_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(InvalidCountryError, match="Country not found"):
            await service.update(team_id, update_data)

        mock_team_repository.get_by_id.assert_awaited_once_with(team_id, include_deleted=True)
        assert mock_country_repository.get_by_id.await_count == 2
        mock_team_repository.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_team_rejects_soft_deleted_country(self):
        """
        Test that updating team to soft-deleted country is rejected.

        Arrange: Mock country repository returning None (active) but deleted exists
        Act: Attempt to update with soft-deleted country_id
        Assert: InvalidCountryError raised with "not active" message
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        team_id = uuid4()
        old_country_id = uuid4()
        new_country_id = uuid4()
        update_data = {"country_id": new_country_id}

        existing_team = Team(
            id=team_id,
            name="Team USA",
            country_id=old_country_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        deleted_country = Country(
            id=new_country_id,
            name="Canada",
            code="CAN",
            is_deleted=True,
            created_at=datetime.now(UTC)
        )

        mock_team_repository.get_by_id.return_value = existing_team
        # First call returns None, second returns deleted country
        mock_country_repository.get_by_id.side_effect = [None, deleted_country]

        # Act & Assert
        with pytest.raises(InvalidCountryError, match="Country is not active"):
            await service.update(team_id, update_data)

        mock_team_repository.get_by_id.assert_awaited_once_with(team_id, include_deleted=True)
        assert mock_country_repository.get_by_id.await_count == 2
        mock_team_repository.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_team_handles_non_existent_team(self):
        """
        Test that update raises error for non-existent team.

        Arrange: Mock repository returning None
        Act: Attempt to update non-existent team
        Assert: TeamNotFoundError raised
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        team_id = uuid4()
        update_data = {"name": "New Name"}

        mock_team_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(TeamNotFoundError, match="Team not found"):
            await service.update(team_id, update_data)

        mock_team_repository.get_by_id.assert_awaited_once_with(team_id, include_deleted=True)
        mock_team_repository.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_team_handles_foreign_key_constraint_violation(self):
        """
        Test that FK constraint violation on update is converted to InvalidCountryError.

        Arrange: Mock repository raising IntegrityError on update
        Act: Attempt to update team
        Assert: InvalidCountryError raised
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        team_id = uuid4()
        old_country_id = uuid4()
        new_country_id = uuid4()
        update_data = {"country_id": new_country_id}

        existing_team = Team(
            id=team_id,
            name="Team USA",
            country_id=old_country_id,
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        new_country = Country(
            id=new_country_id,
            name="Canada",
            code="CAN",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_team_repository.get_by_id.return_value = existing_team
        mock_country_repository.get_by_id.return_value = new_country

        # Repository raises IntegrityError (FK constraint)
        from sqlalchemy.exc import IntegrityError
        mock_team_repository.update.side_effect = IntegrityError(
            statement="UPDATE teams...",
            params={},
            orig=Exception("foreign key constraint fails")
        )

        # Act & Assert
        with pytest.raises(InvalidCountryError, match="Country not found"):
            await service.update(team_id, update_data)

        mock_team_repository.update.assert_awaited_once_with(team_id, update_data)


class TestTeamServiceDelete:
    """Test suite for team deletion business logic."""

    @pytest.mark.asyncio
    async def test_delete_team_delegates_to_repository(self):
        """
        Test that delete operation delegates to repository soft_delete.

        Arrange: Mock repository
        Act: Call service.delete()
        Assert: Repository soft_delete called with correct ID
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        team_id = uuid4()
        mock_team_repository.soft_delete.return_value = None

        # Act
        await service.delete(team_id)

        # Assert
        mock_team_repository.soft_delete.assert_awaited_once_with(team_id)

    @pytest.mark.asyncio
    async def test_delete_team_handles_non_existent_team(self):
        """
        Test that delete raises error for non-existent team.

        Arrange: Mock repository raising ValueError
        Act: Call service.delete() with non-existent ID
        Assert: TeamNotFoundError raised
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        team_id = uuid4()
        mock_team_repository.soft_delete.side_effect = ValueError("Team not found")

        # Act & Assert
        with pytest.raises(TeamNotFoundError, match="Team not found"):
            await service.delete(team_id)

        mock_team_repository.soft_delete.assert_awaited_once_with(team_id)


class TestTeamServicePermanentDelete:
    """Test suite for permanent deletion business logic."""

    @pytest.mark.asyncio
    async def test_permanent_delete_succeeds(self):
        """
        Test that permanent delete succeeds.

        Arrange: Mock repository
        Act: Call service.permanent_delete()
        Assert: Repository permanent_delete called
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        team_id = uuid4()
        mock_team_repository.permanent_delete.return_value = None

        # Act
        await service.permanent_delete(team_id)

        # Assert
        mock_team_repository.permanent_delete.assert_awaited_once_with(team_id)

    @pytest.mark.asyncio
    async def test_permanent_delete_handles_non_existent_team(self):
        """
        Test that permanent delete raises error for non-existent team.

        Arrange: Mock repository raising ValueError
        Act: Attempt to permanently delete non-existent team
        Assert: TeamNotFoundError raised
        """
        # Arrange
        mock_team_repository = AsyncMock(spec=TeamRepository)
        mock_country_repository = AsyncMock(spec=CountryRepository)
        service = TeamService(mock_team_repository, mock_country_repository)

        team_id = uuid4()
        mock_team_repository.permanent_delete.side_effect = ValueError("Team not found")

        # Act & Assert
        with pytest.raises(TeamNotFoundError, match="Team not found"):
            await service.permanent_delete(team_id)

        mock_team_repository.permanent_delete.assert_awaited_once_with(team_id)
