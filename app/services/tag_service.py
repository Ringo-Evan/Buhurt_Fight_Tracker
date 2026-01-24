from typing import Any, Dict

from app.models.tag import Tag
from app.models.tag_type import TagType
from app.repositories.tag_repository import TagRepository


from app.exceptions import (ValidationError)

class TagService:
    """
    Business logic layer for Tag operations.

    Handles validation and business rules.
    Delegates data access to TagRepository.
    """

    def __init__(self, tag_repository: TagRepository):
        """
        Initialize service with repository.

        Args:
            tag_repository: TagRepository instance for tag data access
        """
        self.tag_repository = tag_repository

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
            

    async def create_tag(self, tag_data: Dict[str, Any]) -> Tag:
        """
        Create a new tag after validating data.

        Args:
            tag_data: Dictionary with tag fields

        Returns:
            Created Tag instance

        Raises:
            ValidationError: If validation fails
        """
        self._validate_tag_data(tag_data)

        # Check what type of tag is being created and apply any specific business rules if needed
        return await self.tag_repository.create(tag_data)