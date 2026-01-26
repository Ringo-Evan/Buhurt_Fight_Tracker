from typing import Any, Dict

from uuid import UUID

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
        await self._check_duplicate_name(str(tag_type_data.get('name')))
        return await self.tag_type_repository.create(tag_type_data)

    async def get_by_id(self, tag_type_id: UUID) -> TagType:
        """
        Retrieve a tag type by its ID.

        Args:
            tag_type_id: ID of the tag type to retrieve

        Returns:
            TagType instance

        Raises:
            ValidationError: If tag type not found
        """
        tag_type = await self.tag_type_repository.get_by_id(tag_type_id)
        if not tag_type:
            raise ValidationError(f"Tag type with ID {tag_type_id} not found")
        return tag_type

    async def list_all(self) -> list[TagType]:
        """
        Retrieve all tag types.

        Returns:
            List of TagType instances ordered by display_order
        """
        return await self.tag_type_repository.list_all()

    async def update(self, tag_type_id: UUID, update_data: Dict[str, Any]) -> TagType:
        """
        Update an existing tag type.

        Args:
            tag_type_id: ID of the tag type to update
            update_data: Dictionary with fields to update

        Returns:
            Updated TagType instance

        Raises:
            ValidationError: If tag type not found or validation fails
        """
        # Verify tag type exists
        #TODO Should this check be in the repository?
        existing_tag_type = await self.tag_type_repository.get_by_id(tag_type_id)
        if not existing_tag_type:
            raise ValidationError(f"Tag type with ID {tag_type_id} not found")

        # Validate update data if name is being changed
        if 'name' in update_data:
            await self._validate_tag_type_data(update_data)
            # Check for duplicate name only if name is changing
            if update_data['name'] != existing_tag_type.name:
                await self._check_duplicate_name(update_data['name'])

        return await self.tag_type_repository.update(tag_type_id, update_data)

    async def delete(self, tag_type_id: UUID) -> None:
        """
        Soft delete a tag type.

        Args:
            tag_type_id: ID of the tag type to delete

        Raises:
            ValidationError: If tag type not found
        """
        # Verify tag type exists
        existing_tag_type = await self.tag_type_repository.get_by_id(tag_type_id)
        if not existing_tag_type:
            raise ValidationError(f"Tag type with ID {tag_type_id} not found")

        await self.tag_type_repository.soft_delete(tag_type_id)

    ###Helper Methods###

    async def _validate_tag_type_data(self, data: Dict[str, Any]) -> None:
        """
        Validate tag type data fields (format validation only).

        Args:
            data: Dictionary with tag type fields

        Raises:
            ValidationError: If validation fails
        """
        # Validate name
        if 'name' in data:
            name = data.get('name', '').strip()
            if not name:
                raise ValidationError("Tag type name is required")
            if len(name) > 50:
                raise ValidationError("Tag type name must not exceed 50 characters")

    async def _check_duplicate_name(self, name: str) -> None:
        """
        Check if tag type name already exists.

        Args:
            name: Tag type name to check

        Raises:
            ValidationError: If name already exists
        """
        existing = await self.tag_type_repository.get_by_name(name)
        if existing:
            raise ValidationError(f"Tag type with name '{name}' already exists. Name must be unique")