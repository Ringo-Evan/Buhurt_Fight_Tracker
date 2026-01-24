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
