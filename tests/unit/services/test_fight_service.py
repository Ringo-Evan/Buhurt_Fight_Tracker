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
            is_deactivated=False,
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
            is_deactivated=False,
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
            is_deactivated=False,
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
            Fight(id=uuid4(), date=date(2024, 1, 1), location="Fight 1", is_deactivated=False, created_at=datetime.now(UTC)),
            Fight(id=uuid4(), date=date(2024, 2, 1), location="Fight 2", is_deactivated=False, created_at=datetime.now(UTC)),
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
            Fight(id=uuid4(), date=date(2024, 6, 15), location="Fight 1", is_deactivated=False, created_at=datetime.now(UTC)),
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
            is_deactivated=False,
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
            is_deactivated=False,
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


class TestFightServiceDeactivate:
    """Test suite for fight deactivate operations."""

    @pytest.mark.asyncio
    async def test_deactivate_fight_succeeds(self):
        """
        Test that deactivating a fight succeeds.
        """
        # Arrange
        fight_id = uuid4()
        mock_repository = AsyncMock(spec=FightRepository)

        service = FightService(mock_repository)

        # Act
        await service.deactivate(fight_id)

        # Assert
        mock_repository.deactivate.assert_awaited_once_with(fight_id)

    @pytest.mark.asyncio
    async def test_deactivate_non_existent_fight_raises_error(self):
        """
        Test that soft deleting non-existent fight raises FightNotFoundError.
        """
        # Arrange
        mock_repository = AsyncMock(spec=FightRepository)
        mock_repository.deactivate.side_effect = ValueError("Fight not found")

        service = FightService(mock_repository)

        # Act & Assert
        with pytest.raises(FightNotFoundError):
            await service.deactivate(uuid4())


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
        fighter1 = Fighter(id=fighter1_id, name="John Smith", is_deactivated=False, created_at=datetime.now(UTC))
        fighter2 = Fighter(id=fighter2_id, name="Jane Doe", is_deactivated=False, created_at=datetime.now(UTC))
        mock_fighter_repo.get_by_id.side_effect = lambda fid: fighter1 if fid == fighter1_id else fighter2

        # Mock fight creation
        fight = Fight(
            id=fight_id,
            date=date(2025, 6, 15),
            location="Battle Arena Denver",
            is_deactivated=False,
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
        fight_format = "singles"
        participations_data = [
            {"fighter_id": fighter1_id, "side": 1, "role": "fighter"},
            {"fighter_id": fighter2_id, "side": 2, "role": "fighter"}
        ]

        # Act
        result = await service.create_with_participants(fight_data, fight_format, participations_data)

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
        fight_format = "singles"
        # Both fighters on side 1, no one on side 2
        participations_data = [
            {"fighter_id": fighter1_id, "side": 1, "role": "fighter"},
            {"fighter_id": fighter2_id, "side": 1, "role": "fighter"}
        ]

        # Act & Assert
        with pytest.raises(ValidationError, match="both sides"):
            await service.create_with_participants(fight_data, fight_format, participations_data)

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
        fight_format = "singles"
        # Same fighter on both sides
        participations_data = [
            {"fighter_id": fighter1_id, "side": 1, "role": "fighter"},
            {"fighter_id": fighter1_id, "side": 2, "role": "fighter"},
            {"fighter_id": fighter2_id, "side": 2, "role": "fighter"}
        ]

        # Act & Assert
        with pytest.raises(ValidationError, match="duplicate fighter"):
            await service.create_with_participants(fight_data, fight_format, participations_data)

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
        fight_format = "melee"
        # Two captains on side 1
        participations_data = [
            {"fighter_id": fighter1_id, "side": 1, "role": "captain"},
            {"fighter_id": fighter2_id, "side": 1, "role": "captain"},
            {"fighter_id": fighter3_id, "side": 2, "role": "fighter"},
            {"fighter_id": fighter4_id, "side": 2, "role": "fighter"}
        ]

        # Act & Assert
        with pytest.raises(ValidationError, match="multiple captains"):
            await service.create_with_participants(fight_data, fight_format, participations_data)

        mock_fight_repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_fight_requires_minimum_2_participants(self):
        """
        Test that creating a fight with only 1 participant fails.

        Scenario: Cannot create fight with only 1 participant
        """
        # Arrange
        from app.repositories.fight_participation_repository import FightParticipationRepository
        from app.repositories.fighter_repository import FighterRepository

        mock_fight_repo = AsyncMock(spec=FightRepository)
        mock_participation_repo = AsyncMock(spec=FightParticipationRepository)
        mock_fighter_repo = AsyncMock(spec=FighterRepository)

        fighter1_id = uuid4()

        service = FightService(
            fight_repository=mock_fight_repo,
            participation_repository=mock_participation_repo,
            fighter_repository=mock_fighter_repo
        )

        fight_data = {
            "date": date(2024, 6, 15),
            "location": "Test Arena"
        }
        fight_format = "singles"
        # Only 1 participant
        participations_data = [
            {"fighter_id": fighter1_id, "side": 1, "role": "fighter"}
        ]

        # Act & Assert
        with pytest.raises(ValidationError, match="at least 2 participants"):
            await service.create_with_participants(fight_data, fight_format, participations_data)

        mock_fight_repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_fight_rejects_nonexistent_fighter(self):
        """
        Test that creating a fight with nonexistent fighter fails.

        Scenario: Cannot create fight with nonexistent fighter
        """
        # Arrange
        from app.repositories.fight_participation_repository import FightParticipationRepository
        from app.repositories.fighter_repository import FighterRepository

        mock_fight_repo = AsyncMock(spec=FightRepository)
        mock_participation_repo = AsyncMock(spec=FightParticipationRepository)
        mock_fighter_repo = AsyncMock(spec=FighterRepository)

        fighter1_id = uuid4()
        nonexistent_fighter_id = uuid4()

        # Mock fighter lookups - fighter1 exists, but nonexistent_fighter does not
        from app.models.fighter import Fighter
        fighter1 = Fighter(id=fighter1_id, name="John Smith", is_deactivated=False, created_at=datetime.now(UTC))
        mock_fighter_repo.get_by_id.side_effect = lambda fid: fighter1 if fid == fighter1_id else None

        service = FightService(
            fight_repository=mock_fight_repo,
            participation_repository=mock_participation_repo,
            fighter_repository=mock_fighter_repo
        )

        fight_data = {
            "date": date(2024, 6, 15),
            "location": "Test Arena"
        }
        fight_format = "singles"
        participations_data = [
            {"fighter_id": fighter1_id, "side": 1, "role": "fighter"},
            {"fighter_id": nonexistent_fighter_id, "side": 2, "role": "fighter"}
        ]

        # Act & Assert
        with pytest.raises(ValidationError, match="not found"):
            await service.create_with_participants(fight_data, fight_format, participations_data)

        mock_fight_repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_fight_creates_supercategory_tag(self):
        """
        Test that creating a fight also creates the supercategory tag linked to the fight.

        Scenario: Fight must have exactly one supercategory tag (DD-007)
        """
        # Arrange
        from app.repositories.fight_participation_repository import FightParticipationRepository
        from app.repositories.fighter_repository import FighterRepository
        from app.repositories.tag_repository import TagRepository
        from app.repositories.tag_type_repository import TagTypeRepository
        from app.models.fighter import Fighter
        from app.models.tag_type import TagType

        mock_fight_repo = AsyncMock(spec=FightRepository)
        mock_participation_repo = AsyncMock(spec=FightParticipationRepository)
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_tag_repo = AsyncMock(spec=TagRepository)
        mock_tag_type_repo = AsyncMock(spec=TagTypeRepository)

        fight_id = uuid4()
        fighter1_id = uuid4()
        fighter2_id = uuid4()
        supercategory_tag_type_id = uuid4()

        # Mock fighter lookups
        fighter1 = Fighter(id=fighter1_id, name="John Smith", is_deactivated=False, created_at=datetime.now(UTC))
        fighter2 = Fighter(id=fighter2_id, name="Jane Doe", is_deactivated=False, created_at=datetime.now(UTC))
        mock_fighter_repo.get_by_id.side_effect = lambda fid: fighter1 if fid == fighter1_id else fighter2

        # Mock supercategory TagType lookup
        supercategory_tag_type = TagType(
            id=supercategory_tag_type_id,
            name="supercategory",
            is_privileged=True,
            is_deactivated=False,
            created_at=datetime.now(UTC)
        )
        mock_tag_type_repo.get_by_name.return_value = supercategory_tag_type

        # Mock fight creation
        fight = Fight(
            id=fight_id,
            date=date(2025, 6, 15),
            location="Battle Arena Denver",
            is_deactivated=False,
            created_at=datetime.now(UTC)
        )
        mock_fight_repo.create.return_value = fight

        # Service with all dependencies
        service = FightService(
            fight_repository=mock_fight_repo,
            participation_repository=mock_participation_repo,
            fighter_repository=mock_fighter_repo,
            tag_repository=mock_tag_repo,
            tag_type_repository=mock_tag_type_repo
        )

        fight_data = {
            "date": date(2025, 6, 15),
            "location": "Battle Arena Denver"
        }
        supercategory = "singles"
        participations_data = [
            {"fighter_id": fighter1_id, "side": 1, "role": "fighter"},
            {"fighter_id": fighter2_id, "side": 2, "role": "fighter"}
        ]

        # Act
        result = await service.create_with_participants(fight_data, supercategory, participations_data)

        # Assert
        assert result.id == fight_id
        mock_fight_repo.create.assert_awaited_once()
        mock_tag_repo.create.assert_awaited_once()
        # Verify tag created with correct data including fight_id (DD-008)
        tag_call_args = mock_tag_repo.create.call_args[0][0]
        assert tag_call_args["fight_id"] == fight_id
        assert tag_call_args["tag_type_id"] == supercategory_tag_type_id
        assert tag_call_args["value"] == "singles"

    @pytest.mark.asyncio
    async def test_singles_format_requires_exactly_one_fighter_per_side(self):
        """
        Test that singles format requires exactly 1 fighter per side.

        Scenario: Singles fights must have exactly 1 fighter per side (DD-003)
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

        # Mock fighter lookups
        from app.models.fighter import Fighter
        fighter1 = Fighter(id=fighter1_id, name="Fighter1", is_deactivated=False, created_at=datetime.now(UTC))
        fighter2 = Fighter(id=fighter2_id, name="Fighter2", is_deactivated=False, created_at=datetime.now(UTC))
        fighter3 = Fighter(id=fighter3_id, name="Fighter3", is_deactivated=False, created_at=datetime.now(UTC))

        def get_fighter_mock(fid):
            if fid == fighter1_id:
                return fighter1
            elif fid == fighter2_id:
                return fighter2
            elif fid == fighter3_id:
                return fighter3
            return None

        mock_fighter_repo.get_by_id.side_effect = get_fighter_mock

        service = FightService(
            fight_repository=mock_fight_repo,
            participation_repository=mock_participation_repo,
            fighter_repository=mock_fighter_repo
        )

        fight_data = {
            "date": date(2024, 6, 15),
            "location": "Test Arena"
        }
        fight_format = "singles"
        # 2 fighters on side 1, 1 on side 2 - invalid for singles
        participations_data = [
            {"fighter_id": fighter1_id, "side": 1, "role": "fighter"},
            {"fighter_id": fighter2_id, "side": 1, "role": "fighter"},
            {"fighter_id": fighter3_id, "side": 2, "role": "fighter"}
        ]

        # Act & Assert
        with pytest.raises(ValidationError, match="Singles.*exactly 1 fighter per side"):
            await service.create_with_participants(fight_data, fight_format, participations_data)

        mock_fight_repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_melee_format_requires_minimum_five_fighters_per_side(self):
        """
        Test that melee format requires at least 5 fighters per side.

        Scenario: Melee fights must have minimum 5 fighters per side (DD-004)
        """
        # Arrange
        from app.repositories.fight_participation_repository import FightParticipationRepository
        from app.repositories.fighter_repository import FighterRepository

        mock_fight_repo = AsyncMock(spec=FightRepository)
        mock_participation_repo = AsyncMock(spec=FightParticipationRepository)
        mock_fighter_repo = AsyncMock(spec=FighterRepository)

        # Create 8 fighters (4 per side - insufficient for melee)
        fighter_ids = [uuid4() for _ in range(8)]

        # Mock fighter lookups
        from app.models.fighter import Fighter
        fighters = {fid: Fighter(id=fid, name=f"Fighter{i}", is_deactivated=False, created_at=datetime.now(UTC))
                    for i, fid in enumerate(fighter_ids)}

        mock_fighter_repo.get_by_id.side_effect = lambda fid: fighters.get(fid)

        service = FightService(
            fight_repository=mock_fight_repo,
            participation_repository=mock_participation_repo,
            fighter_repository=mock_fighter_repo
        )

        fight_data = {
            "date": date(2024, 6, 15),
            "location": "Test Arena"
        }
        fight_format = "melee"
        # 4 fighters per side - insufficient for melee (needs 5+)
        participations_data = [
            {"fighter_id": fighter_ids[0], "side": 1, "role": "fighter"},
            {"fighter_id": fighter_ids[1], "side": 1, "role": "fighter"},
            {"fighter_id": fighter_ids[2], "side": 1, "role": "fighter"},
            {"fighter_id": fighter_ids[3], "side": 1, "role": "fighter"},
            {"fighter_id": fighter_ids[4], "side": 2, "role": "fighter"},
            {"fighter_id": fighter_ids[5], "side": 2, "role": "fighter"},
            {"fighter_id": fighter_ids[6], "side": 2, "role": "fighter"},
            {"fighter_id": fighter_ids[7], "side": 2, "role": "fighter"}
        ]

        # Act & Assert
        with pytest.raises(ValidationError, match="Melee.*at least 5 fighters per side"):
            await service.create_with_participants(fight_data, fight_format, participations_data)

        mock_fight_repo.create.assert_not_awaited()


class TestFightServicePermanentDelete:
    """Test suite for Fight permanent delete business logic."""

    @pytest.mark.asyncio
    async def test_delete_fight_delegates_to_repository(self):
        """
        Test that delete calls repository.delete() and succeeds.

        Arrange: Mock repository returning None (no error)
        Act: Call service.delete()
        Assert: Repository delete called with correct ID
        """
        # Arrange
        from app.repositories.fight_participation_repository import FightParticipationRepository
        from app.repositories.fighter_repository import FighterRepository
        mock_fight_repo = AsyncMock(spec=FightRepository)
        mock_participation_repo = AsyncMock(spec=FightParticipationRepository)
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_fight_repo.delete.return_value = None

        service = FightService(
            fight_repository=mock_fight_repo,
            participation_repository=mock_participation_repo,
            fighter_repository=mock_fighter_repo
        )
        fight_id = uuid4()

        # Act
        await service.delete(fight_id)

        # Assert
        mock_fight_repo.delete.assert_awaited_once_with(fight_id)

    @pytest.mark.asyncio
    async def test_delete_non_existent_fight_raises_error(self):
        """
        Test that deleting non-existent fight raises FightNotFoundError.

        Arrange: Mock repository raising ValueError
        Act: Call service.delete()
        Assert: FightNotFoundError raised
        """
        # Arrange
        from app.repositories.fight_participation_repository import FightParticipationRepository
        from app.repositories.fighter_repository import FighterRepository
        mock_fight_repo = AsyncMock(spec=FightRepository)
        mock_participation_repo = AsyncMock(spec=FightParticipationRepository)
        mock_fighter_repo = AsyncMock(spec=FighterRepository)
        mock_fight_repo.delete.side_effect = ValueError("Fight not found")

        service = FightService(
            fight_repository=mock_fight_repo,
            participation_repository=mock_participation_repo,
            fighter_repository=mock_fighter_repo
        )

        # Act & Assert
        with pytest.raises(FightNotFoundError):
            await service.delete(uuid4())
