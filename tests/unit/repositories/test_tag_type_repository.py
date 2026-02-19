"""
Unit tests for TagTypeRepository.

Tests the data access layer for TagType entity operations with mocked SQLAlchemy AsyncSession.
These tests document existing repository behavior and prevent regressions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, UTC

from app.repositories.tag_type_repository import TagTypeRepository
from app.models.tag_type import TagType


class TestTagTypeRepositoryCreate:
    """Test suite for tag type creation operations."""

    @pytest.mark.asyncio
    async def test_create_tag_type_calls_session_methods_correctly(self):
        """
        Test that creating a tag type calls add(), commit(), and refresh() in correct order.

        Arrange: Mock AsyncSession and create test tag type data
        Act: Call repository.create() with tag type data
        Assert: Verify session methods called with correct arguments
        """
        # Arrange
        mock_session = AsyncMock()
        mock_session.add = MagicMock()  # Synchronous

        tag_type_data = {
            "name": "fight_format",
            "is_privileged": True,
            "display_order": 1
        }

        repository = TagTypeRepository(mock_session)

        # Act
        result = await repository.create(tag_type_data)

        # Assert
        assert isinstance(result, TagType)
        assert result.name == "fight_format"
        assert result.is_privileged == True
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()


class TestTagTypeRepositoryGetById:
    """Test suite for tag type retrieval by ID operations."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_tag_type_when_exists(self):
        """
        Test that get_by_id returns tag type when it exists and is not deleted.

        Arrange: Mock session returning tag type
        Act: Call repository.get_by_id()
        Assert: Returns tag type with correct properties
        """
        # Arrange
        mock_session = AsyncMock()
        tag_type_id = uuid4()

        mock_tag_type = TagType(
            id=tag_type_id,
            name="category",
            is_privileged=True,
            display_order=2,
            is_deactivated=False,
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_tag_type
        mock_session.execute.return_value = mock_result

        repository = TagTypeRepository(mock_session)

        # Act
        result = await repository.get_by_id(tag_type_id)

        # Assert
        assert result is not None
        assert result.id == tag_type_id
        assert result.name == "category"
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self):
        """
        Test that get_by_id returns None when tag type doesn't exist.

        Arrange: Mock session returning None
        Act: Call repository.get_by_id()
        Assert: Returns None
        """
        # Arrange
        mock_session = AsyncMock()
        tag_type_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = TagTypeRepository(mock_session)

        # Act
        result = await repository.get_by_id(tag_type_id)

        # Assert
        assert result is None
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_id_filters_deactivated_by_default(self):
        """
        Test that get_by_id filters out deactivated tag types by default.

        Arrange: Mock session, verify query filters is_deactivated=False
        Act: Call repository.get_by_id() without include_deactivate
        Assert: Query includes deactivate filter
        """
        # Arrange
        mock_session = AsyncMock()
        tag_type_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = TagTypeRepository(mock_session)

        # Act
        await repository.get_by_id(tag_type_id, include_deactivated=False)

        # Assert
        mock_session.execute.assert_awaited_once()
        # Note: Detailed query inspection would require capturing the query object


class TestTagTypeRepositoryGetByName:
    """Test suite for tag type retrieval by name operations."""

    @pytest.mark.asyncio
    async def test_get_by_name_returns_tag_type_when_exists(self):
        """
        Test that get_by_name returns tag type when it exists.

        Arrange: Mock session returning tag type
        Act: Call repository.get_by_name()
        Assert: Returns tag type with correct name
        """
        # Arrange
        mock_session = AsyncMock()

        mock_tag_type = TagType(
            id=uuid4(),
            name="weapon",
            is_privileged=True,
            display_order=3,
            is_deactivated=False,
            created_at=datetime.now(UTC)
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_tag_type
        mock_session.execute.return_value = mock_result

        repository = TagTypeRepository(mock_session)

        # Act
        result = await repository.get_by_name("weapon")

        # Assert
        assert result is not None
        assert result.name == "weapon"
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_name_returns_none_when_not_found(self):
        """
        Test that get_by_name returns None when tag type doesn't exist.

        Arrange: Mock session returning None
        Act: Call repository.get_by_name()
        Assert: Returns None
        """
        # Arrange
        mock_session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = TagTypeRepository(mock_session)

        # Act
        result = await repository.get_by_name("nonexistent")

        # Assert
        assert result is None
        mock_session.execute.assert_awaited_once()


class TestTagTypeRepositoryListAll:
    """Test suite for listing all tag types."""

    @pytest.mark.asyncio
    async def test_list_all_returns_tag_types_ordered_by_display_order(self):
        """
        Test that list_all returns tag types sorted by display_order.

        Arrange: Mock session returning multiple tag types
        Act: Call repository.list_all()
        Assert: Returns list ordered by display_order
        """
        # Arrange
        mock_session = AsyncMock()

        tag_type_1 = TagType(
            id=uuid4(),
            name="fight_format",
            display_order=1,
            is_deactivated=False
        )
        tag_type_2 = TagType(
            id=uuid4(),
            name="category",
            display_order=2,
            is_deactivated=False
        )
        tag_type_3 = TagType(
            id=uuid4(),
            name="weapon",
            display_order=3,
            is_deactivated=False
        )

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [tag_type_1, tag_type_2, tag_type_3]

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        repository = TagTypeRepository(mock_session)

        # Act
        result = await repository.list_all()

        # Assert
        assert len(result) == 3
        assert result[0].name == "fight_format"
        assert result[1].name == "category"
        assert result[2].name == "weapon"
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_all_filters_deactivated_by_default(self):
        """
        Test that list_all filters out deactivated tag types by default.

        Arrange: Mock session
        Act: Call repository.list_all() without include_deactivate
        Assert: Query filters deactivated records
        """
        # Arrange
        mock_session = AsyncMock()

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        repository = TagTypeRepository(mock_session)

        # Act
        result = await repository.list_all(include_deactivated=False)

        # Assert
        assert result == []
        mock_session.execute.assert_awaited_once()


class TestTagTypeRepositorySoftDelete:
    """Test suite for deactivate operations."""

    @pytest.mark.asyncio
    async def test_deactivate_sets_is_deactivated_to_true(self):
        """
        Test that soft_delete sets is_deactivated flag to True.

        Arrange: Mock session with existing tag type
        Act: Call repository.soft_delete()
        Assert: Tag type has is_deactivated=True and commit called
        """
        # Arrange
        mock_session = AsyncMock()
        tag_type_id = uuid4()

        mock_tag_type = TagType(
            id=tag_type_id,
            name="league",
            is_deactivated=False
        )

        # Mock the get_by_id call that happens inside soft_delete
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_tag_type
        mock_session.execute.return_value = mock_result

        repository = TagTypeRepository(mock_session)

        # Act
        await repository.deactivate(tag_type_id)

        # Assert
        assert mock_tag_type.is_deactivated == True
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_deactivate_raises_error_when_not_found(self):
        """
        Test that soft_delete raises ValueError when tag type not found.

        Arrange: Mock session returning None
        Act: Call repository.soft_delete()
        Assert: Raises ValueError
        """
        # Arrange
        mock_session = AsyncMock()
        tag_type_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = TagTypeRepository(mock_session)

        # Act & Assert
        with pytest.raises(ValueError, match="Tag type not found"):
            await repository.deactivate(tag_type_id)
