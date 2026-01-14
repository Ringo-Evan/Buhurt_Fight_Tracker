from typing import Any, Dict

from app.models.tag_type import TagType
from app.repositories.tag_type_repository import TagTypeRepository

from app.exceptions import (ValidationError)

class TagTypeService:
    """
    Business logic layer for TagType operations.

    Handles validation and business rules.
    Delegates data access to TagTypeRepository.
    """

    def __init__(self, tag_type_repository: TagTypeRepository):
        """
        Initialize service with repository.

        Args:
            tag_type_repository: TagTypeRepository instance for tag type data access
        """
        self.tag_type_repository = tag_type_repository

    ###CRUD Operations###

    async def create(self, tag_type_data: Dict[str, Any]) -> TagType:
        """
        Create a new tag type after validating data.

        Args:
            tag_type_data: Dictionary with tag type fields

        Returns:
            Created TagType instance

        Raises:
            ValidationError: If validation fails
        """
        await self._validate_tag_type_data(tag_type_data)
        try:
            #do we want to return this?
            return await self.tag_type_repository.create(tag_type_data)
        except Exception as e:
            # Handle specific exceptions if needed
            raise e

    ###Helper Methods###

    async def _validate_tag_type_data(self, data: Dict[str, Any]) -> None:
        """
        Validate tag type data fields (format validation only).

        Args:
            data: Dictionary with tag type fields

        Raises:
            ValidationError: If validation fails
        """
        pass
        # Validate name
        if 'name' in data:
            name = data.get('name', '').strip()
            if not name:
                raise ValidationError("Tag type name is required")
            if len(name) > 200:
                raise ValidationError("Tag type name must not exceed 200 characters")
        #HOW MANY OF THESE DO WE WANT TO ENFORCE AT THE SERVICE LEVEL?
        #TODO Check for uniqueness
        #TODO Check if privledged tag type creation
        #TODO Verify hierarchy level if provided
        #TODO Verify parent tag type if provided
        #TODO do we need to check for children?
        #TODO check for circular references?
        #TODO 