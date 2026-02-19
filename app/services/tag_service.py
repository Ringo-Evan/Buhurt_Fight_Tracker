from typing import Any, Dict
from uuid import UUID

from app.models.tag import Tag
from app.models.tag_type import TagType
from app.repositories.tag_repository import TagRepository
from app.repositories.tag_type_repository import TagTypeRepository

from app.exceptions import ValidationError, TagNotFoundError


class TagService:
    """
    Business logic layer for Tag operations.

    Handles validation and business rules.
    Delegates data access to TagRepository.
    """

    def __init__(
        self,
        tag_repository: TagRepository,
        tag_type_repository: TagTypeRepository
    ):
        """
        Initialize service with repositories.

        Args:
            tag_repository: TagRepository instance for tag data access
            tag_type_repository: TagTypeRepository for validating tag types
        """
        self.tag_repository = tag_repository
        self.tag_type_repository = tag_type_repository

    def _validate_tag_data(self, data: Dict[str, Any]) -> None:
        """
        Validate tag data fields (format validation only).

        Args:
            data: Dictionary with tag fields

        Raises:
            ValidationError: If validation fails
        """
        # Validate name
        if 'name' in data:
            name = data.get('name', '').strip()
            if not name:
                raise ValidationError("Tag name is required")
            if len(name) > 50:
                raise ValidationError("Tag name must not exceed 50 characters")
            

    async def create(self, tag_data: Dict[str, Any]) -> Tag:
        """
        Create a new tag after validating data.

        Args:
            tag_data: Dictionary with tag fields

        Returns:
            Created Tag instance

        Raises:
            ValidationError: If validation fails
        """
        # Validate tag type exists
        tag_type = await self.tag_type_repository.get_by_id(
            tag_data['tag_type_id']
        )
        if not tag_type:
            raise ValidationError(
                f"Tag type with ID {tag_data['tag_type_id']} not found"
            )

        return await self.tag_repository.create(tag_data)

    async def get_by_id(self, tag_id: UUID) -> Tag | None:
        """
        Get a tag by its ID.

        Args:
            tag_id: UUID of the tag to retrieve

        Returns:
            Tag instance if found, None otherwise
        """
        return await self.tag_repository.get_by_id(tag_id)

    async def list_all(self) -> list[Tag]:
        """
        List all non-deleted tags.

        Returns:
            List of Tag instances
        """
        return await self.tag_repository.list_all()

    async def update(self, tag_id: UUID, update_data: Dict[str, Any]) -> Tag | None:
        """
        Update an existing tag.

        Args:
            tag_id: UUID of the tag to update
            update_data: Dictionary with fields to update

        Returns:
            Updated Tag instance or None if not found
        """
        return await self.tag_repository.update(tag_id, update_data)

    async def deactivate(self, tag_id: UUID) -> None:
        """
        Deactivate a tag.

        Args:
            tag_id: UUID of the tag to deactivate
        """
        await self.tag_repository.deactivate(tag_id)

    async def delete(self, tag_id: UUID) -> None:
        """
        Permanently delete a tag from the database.

        Args:
            tag_id: UUID of the tag to delete

        Raises:
            TagNotFoundError: If tag not found
        """
        try:
            await self.tag_repository.delete(tag_id)
        except ValueError as e:
            raise TagNotFoundError(str(e))