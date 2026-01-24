import pytest
from app.services.tag_service import TagService
from app.exceptions import ValidationError
from app.models.tag import Tag
from app.repositories.tag_repository import TagRepository

class TestTagService:
    def test_create_tag_success(self):
        # Arrange
        mock_tag_repository = pytest.mock.MagicMock(spec=TagRepository)
        tag_service = TagService(tag_repository=mock_tag_repository)
        tag_data = {'name': 'Test Tag'}

        # Act
        created_tag = pytest.asyncio.run(tag_service.create_tag(tag_data))

        # Assert
        mock_tag_repository.create_tag.assert_called_once()
        assert isinstance(created_tag, Tag)
        assert created_tag.name == 'Test Tag'

    def test_create_tag_validation_error_empty_name(self):
        # Arrange
        mock_tag_repository = pytest.mock.MagicMock(spec=TagRepository)
        tag_service = TagService(tag_repository=mock_tag_repository)
        tag_data = {'name': ''}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            pytest.asyncio.run(tag_service.create_tag(tag_data))
        assert str(exc_info.value) == "Tag name is required"

    def test_create_tag_validation_error_name_too_long(self):
        # Arrange
        mock_tag_repository = pytest.mock.MagicMock(spec=TagRepository)
        tag_service = TagService(tag_repository=mock_tag_repository)
        tag_data = {'name': 'A' * 51}  # 51 characters

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            pytest.asyncio.run(tag_service.create_tag(tag_data))
        assert str(exc_info.value) == "Tag name must not exceed 50 characters"