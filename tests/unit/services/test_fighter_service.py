"""
Unit tests for FighterService.

Tests business logic layer for Fighter operations with mocked repositories.
Following TDD approach - these tests are written before implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, UTC
from sqlalchemy.exc import IntegrityError

# These imports will fail until implementation exists - that's expected in TDD
from app.services.fighter_service import FighterService
from app.repositories.fighter_repository import FighterRepository
from app.repositories.team_repository import TeamRepository
from app.models.fighter import Fighter
from app.models.team import Team
from app.models.country import Country
from app.exceptions import (
    FighterNotFoundError,
    InvalidTeamError,
    ValidationError
)


class TestFighterServiceCreate:
    """Test suite for fighter creation with validation."""

    @pytest.mark.asyncio
    async def test_create_fighter_with_valid_team_succeeds(self):
        """
        Test creating fighter with valid team succeeds.

        Arrange: Mock repositories with active team
        Act: Call service.create()
        Assert: Fighter created successfully
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        team_id = uuid4()
        team = Team(
            id=team_id,
            name="Team USA",
            country_id=uuid4(),
            is_deactivated=False,
            created_at=datetime.now(UTC)
        )

        fighter = Fighter(
            id=uuid4(),
            name="John Smith",
            team_id=team_id,
            is_deactivated=False,
            created_at=datetime.now(UTC)
        )

        mock_team_repo.get_by_id.return_value = team
        mock_fighter_repo.create.return_value = fighter

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act
        result = await service.create({"name": "John Smith", "team_id": team_id})

        # Assert
        assert result.name == "John Smith"
        assert result.team_id == team_id
        mock_team_repo.get_by_id.assert_awaited_once_with(team_id, include_deactivated=False)
        mock_fighter_repo.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_fighter_with_non_existent_team_raises_error(self):
        """
        Test creating fighter with non-existent team raises InvalidTeamError.

        Arrange: Mock team repository returning None (team doesn't exist at all)
        Act: Call service.create()
        Assert: InvalidTeamError raised with "Team not found"
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        team_id = uuid4()
        # Service checks twice: first with include_deactivated=False, then with include_deactivated=True
        mock_team_repo.get_by_id.side_effect = [None, None]  # Team doesn't exist at all

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act & Assert
        with pytest.raises(InvalidTeamError, match="Team not found"):
            await service.create({"name": "John Smith", "team_id": team_id})

        assert mock_team_repo.get_by_id.await_count == 2  # Checked twice
        mock_fighter_repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_fighter_with_soft_deleted_team_raises_error(self):
        """
        Test creating fighter with deactivated team raises InvalidTeamError.

        Arrange: Mock team repository returning None (filtered) but exists when include_deactivated=True
        Act: Call service.create()
        Assert: InvalidTeamError raised with "Team is not active"
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        team_id = uuid4()
        deleted_team = Team(
            id=team_id,
            name="Defunct Team",
            country_id=uuid4(),
            is_deactivated=True,
            created_at=datetime.now(UTC)
        )

        # First call (include_deactivated=False) returns None, second call (include_deactivated=True) returns deleted team
        mock_team_repo.get_by_id.side_effect = [None, deleted_team]

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act & Assert
        with pytest.raises(InvalidTeamError, match="Team is not active"):
            await service.create({"name": "John Smith", "team_id": team_id})

        assert mock_team_repo.get_by_id.await_count == 2
        mock_fighter_repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_fighter_with_empty_name_raises_error(self):
        """
        Test creating fighter with empty name raises ValidationError.

        Arrange: Service with mocked repositories
        Act: Call service.create() with empty name
        Assert: ValidationError raised
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act & Assert
        with pytest.raises(ValidationError, match="name is required"):
            await service.create({"name": "", "team_id": uuid4()})

        mock_team_repo.get_by_id.assert_not_awaited()
        mock_fighter_repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_fighter_with_whitespace_name_raises_error(self):
        """
        Test creating fighter with whitespace-only name raises ValidationError.

        Arrange: Service with mocked repositories
        Act: Call service.create() with whitespace name
        Assert: ValidationError raised
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act & Assert
        with pytest.raises(ValidationError, match="name is required"):
            await service.create({"name": "   ", "team_id": uuid4()})


class TestFighterServiceRetrieve:
    """Test suite for fighter retrieval operations."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_fighter_when_exists(self):
        """
        Test that get_by_id returns fighter when it exists.

        Arrange: Mock repository returning fighter
        Act: Call service.get_by_id()
        Assert: Returns fighter
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        fighter_id = uuid4()
        fighter = Fighter(
            id=fighter_id,
            name="John Smith",
            team_id=uuid4(),
            is_deactivated=False,
            created_at=datetime.now(UTC)
        )

        mock_fighter_repo.get_by_id.return_value = fighter

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act
        result = await service.get_by_id(fighter_id)

        # Assert
        assert result.id == fighter_id
        mock_fighter_repo.get_by_id.assert_awaited_once_with(fighter_id, include_deactivated=False)

    @pytest.mark.asyncio
    async def test_get_by_id_raises_not_found_when_fighter_not_exists(self):
        """
        Test that get_by_id raises FighterNotFoundError when fighter doesn't exist.

        Arrange: Mock repository returning None
        Act: Call service.get_by_id()
        Assert: FighterNotFoundError raised
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        mock_fighter_repo.get_by_id.return_value = None

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act & Assert
        with pytest.raises(FighterNotFoundError):
            await service.get_by_id(uuid4())

    @pytest.mark.asyncio
    async def test_list_all_returns_all_active_fighters(self):
        """
        Test that list_all returns all active fighters.

        Arrange: Mock repository returning list of fighters
        Act: Call service.list_all()
        Assert: Returns list of fighters
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        fighters = [
            Fighter(id=uuid4(), name="John Smith", team_id=uuid4(), is_deactivated=False, created_at=datetime.now(UTC)),
            Fighter(id=uuid4(), name="Jane Doe", team_id=uuid4(), is_deactivated=False, created_at=datetime.now(UTC))
        ]

        mock_fighter_repo.list_all.return_value = fighters

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act
        result = await service.list_all()

        # Assert
        assert len(result) == 2
        mock_fighter_repo.list_all.assert_awaited_once_with(include_deactivated=False)

    @pytest.mark.asyncio
    async def test_list_by_team_returns_team_fighters(self):
        """
        Test that list_by_team returns fighters for specified team.

        Arrange: Mock repository returning fighters for team
        Act: Call service.list_by_team()
        Assert: Returns team's fighters
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        team_id = uuid4()
        fighters = [
            Fighter(id=uuid4(), name="John Smith", team_id=team_id, is_deactivated=False, created_at=datetime.now(UTC)),
            Fighter(id=uuid4(), name="Jane Doe", team_id=team_id, is_deactivated=False, created_at=datetime.now(UTC))
        ]

        mock_fighter_repo.list_by_team.return_value = fighters

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act
        result = await service.list_by_team(team_id)

        # Assert
        assert len(result) == 2
        assert all(f.team_id == team_id for f in result)
        mock_fighter_repo.list_by_team.assert_awaited_once_with(team_id, include_deactivated=False)

    @pytest.mark.asyncio
    async def test_list_by_country_returns_country_fighters(self):
        """
        Test that list_by_country returns fighters from country's teams.

        Arrange: Mock repository returning fighters for country
        Act: Call service.list_by_country()
        Assert: Returns country's fighters
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        country_id = uuid4()
        fighters = [
            Fighter(id=uuid4(), name="John Smith", team_id=uuid4(), is_deactivated=False, created_at=datetime.now(UTC)),
            Fighter(id=uuid4(), name="Jane Doe", team_id=uuid4(), is_deactivated=False, created_at=datetime.now(UTC))
        ]

        mock_fighter_repo.list_by_country.return_value = fighters

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act
        result = await service.list_by_country(country_id)

        # Assert
        assert len(result) == 2
        mock_fighter_repo.list_by_country.assert_awaited_once_with(country_id, include_deactivated=False)


class TestFighterServiceUpdate:
    """Test suite for fighter update operations."""

    @pytest.mark.asyncio
    async def test_update_fighter_name_succeeds(self):
        """
        Test that updating fighter name succeeds.

        Arrange: Mock repository with existing fighter
        Act: Call service.update() with new name
        Assert: Fighter name updated
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        fighter_id = uuid4()
        updated_fighter = Fighter(
            id=fighter_id,
            name="Jonathan Smith",
            team_id=uuid4(),
            is_deactivated=False,
            created_at=datetime.now(UTC)
        )

        mock_fighter_repo.update.return_value = updated_fighter

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act
        result = await service.update(fighter_id, {"name": "Jonathan Smith"})

        # Assert
        assert result.name == "Jonathan Smith"
        mock_fighter_repo.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_fighter_team_validates_new_team_exists(self):
        """
        Test that updating fighter team validates new team exists.

        Arrange: Mock repositories with valid new team
        Act: Call service.update() with new team_id
        Assert: Team validated, fighter updated
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        fighter_id = uuid4()
        new_team_id = uuid4()

        new_team = Team(
            id=new_team_id,
            name="New Team",
            country_id=uuid4(),
            is_deactivated=False,
            created_at=datetime.now(UTC)
        )

        updated_fighter = Fighter(
            id=fighter_id,
            name="John Smith",
            team_id=new_team_id,
            is_deactivated=False,
            created_at=datetime.now(UTC)
        )

        mock_team_repo.get_by_id.return_value = new_team
        mock_fighter_repo.update.return_value = updated_fighter

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act
        result = await service.update(fighter_id, {"team_id": new_team_id})

        # Assert
        assert result.team_id == new_team_id
        mock_team_repo.get_by_id.assert_awaited_once_with(new_team_id, include_deactivated=False)
        mock_fighter_repo.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_fighter_team_to_non_existent_team_raises_error(self):
        """
        Test that updating to non-existent team raises InvalidTeamError.

        Arrange: Mock team repository returning None
        Act: Call service.update() with non-existent team
        Assert: InvalidTeamError raised
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        new_team_id = uuid4()
        mock_team_repo.get_by_id.return_value = None

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act & Assert
        with pytest.raises(InvalidTeamError, match="Team not found"):
            await service.update(uuid4(), {"team_id": new_team_id})

        mock_fighter_repo.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_fighter_team_to_soft_deleted_team_raises_error(self):
        """
        Test that updating to deactivated team raises InvalidTeamError.

        Arrange: Mock team repository with deactivated team
        Act: Call service.update()
        Assert: InvalidTeamError raised
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        new_team_id = uuid4()
        deleted_team = Team(
            id=new_team_id,
            name="Defunct Team",
            country_id=uuid4(),
            is_deactivated=True,
            created_at=datetime.now(UTC)
        )

        mock_team_repo.get_by_id.side_effect = [None, deleted_team]

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act & Assert
        with pytest.raises(InvalidTeamError, match="Team is not active"):
            await service.update(uuid4(), {"team_id": new_team_id})

        mock_fighter_repo.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_fighter_with_empty_name_raises_error(self):
        """
        Test that updating with empty name raises ValidationError.

        Arrange: Service with mocked repositories
        Act: Call service.update() with empty name
        Assert: ValidationError raised
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act & Assert
        with pytest.raises(ValidationError, match="name is required"):
            await service.update(uuid4(), {"name": ""})

        mock_fighter_repo.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_non_existent_fighter_raises_error(self):
        """
        Test that updating non-existent fighter raises FighterNotFoundError.

        Arrange: Mock repository raising ValueError
        Act: Call service.update()
        Assert: FighterNotFoundError raised
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        mock_fighter_repo.update.side_effect = ValueError("Fighter not found")

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act & Assert
        with pytest.raises(FighterNotFoundError):
            await service.update(uuid4(), {"name": "New Name"})


class TestFighterServiceDelete:
    """Test suite for fighter deletion operations."""

    @pytest.mark.asyncio
    async def test_soft_delete_fighter_succeeds(self):
        """
        Test that soft deleting fighter succeeds.

        Arrange: Mock repository with existing fighter
        Act: Call service.delete()
        Assert: Fighter deactivated
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        fighter_id = uuid4()
        mock_fighter_repo.soft_delete.return_value = None

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act
        await service.delete(fighter_id)

        # Assert
        mock_fighter_repo.soft_delete.assert_awaited_once_with(fighter_id)

    @pytest.mark.asyncio
    async def test_soft_delete_non_existent_fighter_raises_error(self):
        """
        Test that soft deleting non-existent fighter raises FighterNotFoundError.

        Arrange: Mock repository raising ValueError
        Act: Call service.delete()
        Assert: FighterNotFoundError raised
        """
        # Arrange
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_team_repo = AsyncMock(spec=TeamRepository)

        mock_fighter_repo.soft_delete.side_effect = ValueError("Fighter not found")

        service = FighterService(mock_fighter_repo, mock_team_repo)

        # Act & Assert
        with pytest.raises(FighterNotFoundError):
            await service.delete(uuid4())
