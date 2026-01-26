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

    @pytest.mark.asyncio
    async def test_create_tag_with_valid_tag_type_succeeds(self):
        """
        Test that creating a tag with valid tag_type_id succeeds.

        This is TEST #2 following strict TDD.

        Arrange: Mock repository where tag type EXISTS
        Act: Call service.create()
        Assert: Tag created successfully
        """
        # Arrange
        mock_tag_repo = AsyncMock(spec=TagRepository)
        mock_tag_type_repo = AsyncMock(spec=TagTypeRepository)

        # Tag type EXISTS
        tag_type_id = uuid4()
        tag_type = TagType(id=tag_type_id, name='fight_format')
        mock_tag_type_repo.get_by_id.return_value = tag_type

        created_tag = Tag(
            id=uuid4(),
            tag_type_id=tag_type_id,
            value='singles'
        )
        mock_tag_repo.create.return_value = created_tag

        service = TagService(
            tag_repository=mock_tag_repo,
            tag_type_repository=mock_tag_type_repo
        )

        tag_data = {
            'tag_type_id': tag_type_id,
            'value': 'singles'
        }

        # Act
        result = await service.create(tag_data)

        # Assert
        assert result.value == 'singles'
        assert result.tag_type_id == tag_type_id
        mock_tag_type_repo.get_by_id.assert_called_once_with(tag_type_id)
        mock_tag_repo.create.assert_called_once()


class TestTagServiceGetById:
    """Test suite for tag retrieval by ID with strict TDD."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_tag_when_exists(self):
        """
        Test that get_by_id returns tag when it exists.

        Arrange: Mock repository to return a tag
        Act: Call service.get_by_id()
        Assert: Tag returned successfully
        """
        # Arrange
        mock_tag_repo = AsyncMock(spec=TagRepository)
        mock_tag_type_repo = AsyncMock(spec=TagTypeRepository)

        tag_id = uuid4()
        tag_type_id = uuid4()
        expected_tag = Tag(
            id=tag_id,
            tag_type_id=tag_type_id,
            value='singles'
        )
        mock_tag_repo.get_by_id.return_value = expected_tag

        service = TagService(
            tag_repository=mock_tag_repo,
            tag_type_repository=mock_tag_type_repo
        )

        # Act
        result = await service.get_by_id(tag_id)

        # Assert
        assert result is not None
        assert result.id == tag_id
        assert result.value == 'singles'
        mock_tag_repo.get_by_id.assert_called_once_with(tag_id)


class TestTagServiceListAll:
    """Test suite for listing all tags."""

    @pytest.mark.asyncio
    async def test_list_all_returns_all_tags(self):
        """
        Test that list_all returns all non-deleted tags.

        Arrange: Mock repository to return list of tags
        Act: Call service.list_all()
        Assert: All tags returned
        """
        # Arrange
        mock_tag_repo = AsyncMock(spec=TagRepository)
        mock_tag_type_repo = AsyncMock(spec=TagTypeRepository)

        tag_type_id = uuid4()
        tags = [
            Tag(id=uuid4(), tag_type_id=tag_type_id, value='singles'),
            Tag(id=uuid4(), tag_type_id=tag_type_id, value='melee'),
        ]
        mock_tag_repo.list_all.return_value = tags

        service = TagService(
            tag_repository=mock_tag_repo,
            tag_type_repository=mock_tag_type_repo
        )

        # Act
        result = await service.list_all()

        # Assert
        assert len(result) == 2
        assert result[0].value == 'singles'
        assert result[1].value == 'melee'
        mock_tag_repo.list_all.assert_called_once()


class TestTagServiceUpdate:
    """Test suite for updating tags."""

    @pytest.mark.asyncio
    async def test_update_tag_value_succeeds(self):
        """
        Test that updating tag value succeeds.

        Arrange: Mock repository with existing tag
        Act: Call service.update()
        Assert: Tag updated successfully
        """
        # Arrange
        mock_tag_repo = AsyncMock(spec=TagRepository)
        mock_tag_type_repo = AsyncMock(spec=TagTypeRepository)

        tag_id = uuid4()
        tag_type_id = uuid4()
        updated_tag = Tag(id=tag_id, tag_type_id=tag_type_id, value='profight')
        mock_tag_repo.update.return_value = updated_tag

        service = TagService(
            tag_repository=mock_tag_repo,
            tag_type_repository=mock_tag_type_repo
        )

        # Act
        result = await service.update(tag_id, {'value': 'profight'})

        # Assert
        assert result.value == 'profight'
        mock_tag_repo.update.assert_called_once_with(tag_id, {'value': 'profight'})


class TestTagServiceDelete:
    """Test suite for deleting tags."""

    @pytest.mark.asyncio
    async def test_delete_tag_calls_repository(self):
        """
        Test that delete calls repository soft_delete.

        Arrange: Mock repository
        Act: Call service.delete()
        Assert: Repository soft_delete called
        """
        # Arrange
        mock_tag_repo = AsyncMock(spec=TagRepository)
        mock_tag_type_repo = AsyncMock(spec=TagTypeRepository)

        tag_id = uuid4()

        service = TagService(
            tag_repository=mock_tag_repo,
            tag_type_repository=mock_tag_type_repo
        )

        # Act
        await service.delete(tag_id)

        # Assert
        mock_tag_repo.soft_delete.assert_called_once_with(tag_id)
