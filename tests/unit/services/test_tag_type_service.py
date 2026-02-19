import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

from app.repositories.tag_type_repository import TagTypeRepository
from app.services.tag_type_service import TagTypeService
from app.models.tag_type import TagType

class TestTagTypeService:

    @pytest.mark.asyncio
    async def test_create_tag_type(self):
        """
        Test the creation of a tag type.

        Arrange: Set up the necessary mock objects and the service instance.
        Act: Call the create_tag_type method with valid data.
        Assert: Verify that the tag type was created successfully.
        """

        #arrange
        mock_tag_type_repository = AsyncMock(spec=TagTypeRepository)
        tag_type_service = TagTypeService(tag_type_repository=mock_tag_type_repository)
        tag_type = TagType(id='123e4567-e89b-12d3-a456-426614174000', name='Test Tag Type')

        # Mock get_by_name to return None (no duplicate)
        mock_tag_type_repository.get_by_name.return_value = None
        mock_tag_type_repository.create.return_value = tag_type

        tag_type_data = {'name': 'Test Tag Type'}

        #act
        created_tag_type = await tag_type_service.create(tag_type_data)

        #assert
        mock_tag_type_repository.get_by_name.assert_called_once_with('Test Tag Type')
        mock_tag_type_repository.create.assert_called_once()
        assert created_tag_type.name == 'Test Tag Type'

    @pytest.mark.asyncio
    async def test_get_tag_type(self):
        """
        Test retrieving a tag type by ID.

        Arrange: Set up the necessary mock objects and the service instance.
        Act: Call the get_tag_type method with a valid ID.
        Assert: Verify that the correct tag type is returned.
        """

        #arrange 
        mock_tag_type_repository = AsyncMock(spec=TagTypeRepository)
        tag_type_service = TagTypeService(tag_type_repository=mock_tag_type_repository)
        tag_type = TagType(id='123e4567-e89b-12d3-a456-426614174000', name='Test Tag Type')
        mock_tag_type_repository.get_by_id.return_value = tag_type
        
        tag_type_id = '123e4567-e89b-12d3-a456-426614174000'

        #act
        retrieved_tag_type = await tag_type_service.get_by_id(tag_type_id)

        #assert
        mock_tag_type_repository.get_by_id.assert_called_once_with(tag_type_id)
        assert retrieved_tag_type.id == tag_type_id
        assert retrieved_tag_type.name == 'Test Tag Type'


    @pytest.mark.asyncio
    async def test_update_tag_type(self):
        """
        Test updating a tag type.
        Arrange: Set up the necessary mock objects and the service instance.
        Act: Call the update_tag_type method with valid data.
        Assert: Verify that the tag type was updated successfully.
        """
        #arrange 
        mock_tag_type_repository = AsyncMock(spec=TagTypeRepository)
        tag_type_service = TagTypeService(tag_type_repository=mock_tag_type_repository)
        tag_type = TagType(id='123e4567-e89b-12d3-a456-426614174000', name='Original Tag Type')
        mock_tag_type_repository.update.return_value = tag_type
        
        tag_type_id = '123e4567-e89b-12d3-a456-426614174000'
        tag_type_data = {'name': 'Updated Tag Type'}

        #act
        updated_tag_type = await tag_type_service.tag_type_repository.update(tag_type_id, tag_type_data)

        #assert
        mock_tag_type_repository.update.assert_called_once_with(tag_type_id, tag_type_data)
        assert updated_tag_type.name == 'Updated Tag Type'

    @pytest.mark.asyncio
    async def test_create_tag_type_with_duplicate_name_raises_error(self):
        """
        Test that creating a tag type with duplicate name raises ValidationError.

        Arrange: Mock repository to return existing tag type with same name
        Act: Call create with duplicate name
        Assert: ValidationError raised with appropriate message
        """
        # Arrange
        mock_tag_type_repository = AsyncMock(spec=TagTypeRepository)
        tag_type_service = TagTypeService(tag_type_repository=mock_tag_type_repository)

        # Mock repository to return existing tag type (indicates duplicate)
        existing_tag_type = TagType(
            id='123e4567-e89b-12d3-a456-426614174000',
            name='category'
        )
        mock_tag_type_repository.get_by_name.return_value = existing_tag_type

        tag_type_data = {'name': 'category'}

        # Act & Assert
        from app.exceptions import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            await tag_type_service.create(tag_type_data)

        assert 'unique' in str(exc_info.value).lower() or 'exists' in str(exc_info.value).lower()
        mock_tag_type_repository.get_by_name.assert_called_once_with('category')
        mock_tag_type_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_tag_type_with_empty_name_raises_error(self):
        """
        Test that creating a tag type with empty name raises ValidationError.

        Arrange: Mock repository
        Act: Call create with empty name
        Assert: ValidationError raised
        """
        # Arrange
        mock_tag_type_repository = AsyncMock(spec=TagTypeRepository)
        tag_type_service = TagTypeService(tag_type_repository=mock_tag_type_repository)

        tag_type_data = {'name': '   '}  # Whitespace only

        # Act & Assert
        from app.exceptions import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            await tag_type_service.create(tag_type_data)

        assert 'required' in str(exc_info.value).lower()
        mock_tag_type_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_tag_type_with_name_too_long_raises_error(self):
        """
        Test that creating a tag type with name exceeding max length raises ValidationError.

        Arrange: Mock repository
        Act: Call create with name > 50 characters
        Assert: ValidationError raised
        """
        # Arrange
        mock_tag_type_repository = AsyncMock(spec=TagTypeRepository)
        tag_type_service = TagTypeService(tag_type_repository=mock_tag_type_repository)

        # Name with 51 characters (exceeds 50 char limit from model)
        long_name = 'a' * 51
        tag_type_data = {'name': long_name}

        # Act & Assert
        from app.exceptions import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            await tag_type_service.create(tag_type_data)

        assert 'exceed' in str(exc_info.value).lower() or 'long' in str(exc_info.value).lower()
        mock_tag_type_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_all_tag_types(self):
        """
        Test retrieving all tag types.

        Arrange: Mock repository to return list of tag types
        Act: Call service.list_all()
        Assert: Returns all tag types from repository
        """
        # Arrange
        mock_tag_type_repository = AsyncMock(spec=TagTypeRepository)
        tag_type_service = TagTypeService(tag_type_repository=mock_tag_type_repository)

        tag_types = [
            TagType(id=uuid4(), name='fight_format', display_order=1),
            TagType(id=uuid4(), name='category', display_order=2),
            TagType(id=uuid4(), name='weapon', display_order=3)
        ]
        mock_tag_type_repository.list_all.return_value = tag_types

        # Act
        result = await tag_type_service.list_all()

        # Assert
        assert len(result) == 3
        assert result[0].name == 'fight_format'
        assert result[1].name == 'category'
        assert result[2].name == 'weapon'
        mock_tag_type_repository.list_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_tag_type(self):
        """
        Test updating a tag type.

        Arrange: Mock repository to return existing and updated tag type
        Act: Call service.update()
        Assert: Tag type updated successfully
        """
        # Arrange
        mock_tag_type_repository = AsyncMock(spec=TagTypeRepository)
        tag_type_service = TagTypeService(tag_type_repository=mock_tag_type_repository)

        tag_type_id = '123e4567-e89b-12d3-a456-426614174000'
        existing_tag_type = TagType(
            id=tag_type_id,
            name='weapon',
            display_order=3
        )
        updated_tag_type = TagType(
            id=tag_type_id,
            name='weapon',
            display_order=10
        )

        mock_tag_type_repository.get_by_id.return_value = existing_tag_type
        mock_tag_type_repository.update.return_value = updated_tag_type

        update_data = {'display_order': 10}

        # Act
        result = await tag_type_service.update(tag_type_id, update_data)

        # Assert
        assert result.display_order == 10
        mock_tag_type_repository.get_by_id.assert_called_once_with(tag_type_id)
        mock_tag_type_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_nonexistent_tag_type_raises_error(self):
        """
        Test that updating a nonexistent tag type raises error.

        Arrange: Mock repository to return None (not found)
        Act: Call service.update()
        Assert: Raises appropriate error
        """
        # Arrange
        mock_tag_type_repository = AsyncMock(spec=TagTypeRepository)
        tag_type_service = TagTypeService(tag_type_repository=mock_tag_type_repository)

        tag_type_id = UUID('123e4567-e89b-12d3-a456-426614174000')
        mock_tag_type_repository.get_by_id.return_value = None

        update_data = {'display_order': 10}

        # Act & Assert
        from app.exceptions import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            await tag_type_service.update(tag_type_id, update_data)

        assert 'not found' in str(exc_info.value).lower()
        mock_tag_type_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_deactivate_tag_type(self):
        """
        Test deactivating a tag type.

        Arrange: Mock repository
        Act: Call service.deactivate()
        Assert: Repository deactivate called
        """
        # Arrange
        mock_tag_type_repository = AsyncMock(spec=TagTypeRepository)
        tag_type_service = TagTypeService(tag_type_repository=mock_tag_type_repository)

        tag_type_id = UUID('123e4567-e89b-12d3-a456-426614174000')
        existing_tag_type = TagType(id=tag_type_id, name='league')
        mock_tag_type_repository.get_by_id.return_value = existing_tag_type

        # Act
        await tag_type_service.deactivate(tag_type_id)

        # Assert
        mock_tag_type_repository.get_by_id.assert_called_once_with(tag_type_id)
        mock_tag_type_repository.deactivate.assert_called_once_with(tag_type_id)