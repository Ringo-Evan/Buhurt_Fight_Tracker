"""
Unit tests for TagService.

Tests business logic layer for Tag operations.
Following STRICT TDD - ONE test at a time, RED → GREEN → REFACTOR.
"""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.repositories.tag_repository import TagRepository
from app.repositories.tag_type_repository import TagTypeRepository
from app.services.tag_service import TagService
from app.models.tag import Tag
from app.models.tag_type import TagType
from app.exceptions import ValidationError


class TestTagServiceCreate:
    """Test suite for tag creation with strict TDD."""

    @pytest.mark.asyncio
    async def test_create_tag_validates_tag_type_exists(self):
        """
        Test that creating a tag validates tag_type_id exists.

        This is TEST #1 following strict TDD.

        Arrange: Mock repository where tag type does NOT exist
        Act: Call service.create() with invalid tag_type_id
        Assert: ValidationError raised with appropriate message
        """
        # Arrange
        mock_tag_repo = AsyncMock(spec=TagRepository)
        mock_tag_type_repo = AsyncMock(spec=TagTypeRepository)

        # Tag type does NOT exist
        mock_tag_type_repo.get_by_id.return_value = None

        service = TagService(
            tag_repository=mock_tag_repo,
            tag_type_repository=mock_tag_type_repo
        )

        tag_type_id = uuid4()
        tag_data = {
            'tag_type_id': tag_type_id,
            'value': 'singles'
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await service.create(tag_data)

        assert 'tag type' in str(exc_info.value).lower()
        assert 'not found' in str(exc_info.value).lower()
        mock_tag_type_repo.get_by_id.assert_called_once_with(tag_type_id)
        mock_tag_repo.create.assert_not_called()
