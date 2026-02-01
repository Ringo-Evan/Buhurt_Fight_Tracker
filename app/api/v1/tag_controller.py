"""
FastAPI router for tag endpoints.

Provides CRUD operations for tags with proper error handling
and OpenAPI documentation.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.repositories.tag_repository import TagRepository
from app.repositories.tag_type_repository import TagTypeRepository
from app.services.tag_service import TagService
from app.schemas.tag_schema import TagCreate, TagUpdate, TagResponse
from app.exceptions import ValidationError

router = APIRouter(prefix="/tags", tags=["Tags"])


def get_tag_service(db: AsyncSession = Depends(get_db)) -> TagService:
    """Dependency that provides a TagService instance."""
    tag_repository = TagRepository(db)
    tag_type_repository = TagTypeRepository(db)
    return TagService(tag_repository, tag_type_repository)


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tag",
    description="Create a new tag with validation for tag type existence",
    responses={
        400: {"description": "Validation error (e.g., invalid tag_type_id)"},
    },
)
async def create_tag(
    tag: TagCreate,
    service: TagService = Depends(get_tag_service)
):
    """Create a new tag."""
    try:
        return await service.create(tag.model_dump())
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=list[TagResponse],
    status_code=status.HTTP_200_OK,
    summary="List all tags",
    description="Retrieve all non-deleted tags"
)
async def list_tags(
    service: TagService = Depends(get_tag_service)
):
    """List all tags."""
    return await service.list_all()


@router.get(
    "/{tag_id}",
    response_model=TagResponse,
    status_code=status.HTTP_200_OK,
    summary="Get tag by ID",
    description="Retrieve a specific tag by its UUID",
    responses={
        404: {"description": "Tag not found"},
    },
)
async def get_tag(
    tag_id: UUID,
    service: TagService = Depends(get_tag_service)
):
    """Get a specific tag by ID."""
    tag = await service.get_by_id(tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    return tag


@router.patch(
    "/{tag_id}",
    response_model=TagResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a tag",
    description="Update an existing tag's value",
    responses={
        404: {"description": "Tag not found"},
    },
)
async def update_tag(
    tag_id: UUID,
    update_data: TagUpdate,
    service: TagService = Depends(get_tag_service)
):
    """Update an existing tag."""
    update_dict = update_data.model_dump(exclude_unset=True)
    tag = await service.update(tag_id, update_dict)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    return tag


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tag",
    description="Soft delete a tag (sets is_deleted flag)",
    responses={
        404: {"description": "Tag not found"},
    },
)
async def delete_tag(
    tag_id: UUID,
    service: TagService = Depends(get_tag_service)
):
    """Soft delete a tag."""
    try:
        await service.delete(tag_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
