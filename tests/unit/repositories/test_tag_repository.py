"""
Unit tests for TagRepository.

Tests the data access layer for Tag entity operations with mocked SQLAlchemy AsyncSession.
Following STRICT TDD approach - writing ONE test at a time.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.repositories.tag_repository import TagRepository
from app.models.tag import Tag


class TestTagRepositoryCreate:
    """Test suite for tag creation operations."""

    @pytest.mark.asyncio
    async def test_create_tag_calls_session_methods_correctly(self):
        """
        Test that creating a tag calls add(), commit(), and refresh().

        Arrange: Mock AsyncSession and create test tag data
        Act: Call repository.create() with tag data
        Assert: Verify session methods called with correct arguments
        """
        # Arrange
        mock_session = AsyncMock()
        mock_session.add = MagicMock()  # Synchronous

        tag_type_id = uuid4()
        tag_data = {
            "tag_type_id": tag_type_id,
            "value": "singles"
        }

        repository = TagRepository(mock_session)

        # Act
        result = await repository.create(tag_data)

        # Assert
        assert isinstance(result, Tag)
        assert result.value == "singles"
        assert result.tag_type_id == tag_type_id
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()


class TestTagRepositoryListAll:
    """Test suite for listing all tags."""

    @pytest.mark.asyncio
    async def test_list_all_returns_all_non_deleted_tags(self):
        """
        Test that list_all returns all non-deleted tags.

        Arrange: Mock session to return list of tags
        Act: Call repository.list_all()
        Assert: All non-deleted tags returned
        """
        # Arrange
        mock_session = AsyncMock()
        tag_type_id = uuid4()

        tag1 = Tag(id=uuid4(), tag_type_id=tag_type_id, value='singles', is_deactivated=False)
        tag2 = Tag(id=uuid4(), tag_type_id=tag_type_id, value='melee', is_deactivated=False)

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = [tag1, tag2]
        mock_session.execute.return_value = mock_result

        repository = TagRepository(mock_session)

        # Act
        result = await repository.list_all()

        # Assert
        assert len(result) == 2
        assert result[0].value == 'singles'
        assert result[1].value == 'melee'
        mock_session.execute.assert_awaited_once()


class TestTagRepositoryUpdate:
    """Test suite for updating tags."""

    @pytest.mark.asyncio
    async def test_update_tag_modifies_value(self):
        """
        Test that update modifies tag value.

        Arrange: Mock session with existing tag
        Act: Call repository.update()
        Assert: Tag value updated
        """
        # Arrange
        mock_session = AsyncMock()
        tag_id = uuid4()
        tag_type_id = uuid4()

        existing_tag = Tag(id=tag_id, tag_type_id=tag_type_id, value='duel', is_deactivated=False)

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = existing_tag
        mock_session.execute.return_value = mock_result

        repository = TagRepository(mock_session)

        # Act
        result = await repository.update(tag_id, {'value': 'profight'})

        # Assert
        assert result.value == 'profight'
        mock_session.commit.assert_awaited_once()
