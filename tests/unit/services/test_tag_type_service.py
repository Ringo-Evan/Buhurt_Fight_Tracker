import pytest
from unittest.mock import AsyncMock, MagicMock


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
        mock_tag_type_repository.create.return_value = tag_type
        
        tag_type_data = {'name': 'Test Tag Type'}

        #act
        created_tag_type = await tag_type_service.create(tag_type_data)

        #assert
        mock_tag_type_repository.create.assert_called_once()
        #Is this something we want to check at the service level?
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

    @pytest.mark.skip(reason="Not implemented yet")
    def test_delete_tag_type(self):
        pass