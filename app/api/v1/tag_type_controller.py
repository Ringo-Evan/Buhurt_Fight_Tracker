"""
FastAPI router for tag_type endpoints.

Provides CRUD operations for tag_types with proper error handling
and OpenAPI documentation.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.repositories.tag_type_repository import TagTypeRepository
from app.services.tag_type_service import TagTypeService
from app.schemas.tag_type_schema import TagTypeCreate, TagTypeUpdate, TagTypeResponse
from app.exceptions import TagTypeNotFoundError, ValidationError

router = APIRouter(prefix="/tag-types", tags=["Tag Types"])


def get_tag_type_service(db: AsyncSession = Depends(get_db)) -> TagTypeService:
    """Dependency that provides a TagTypeService instance."""
    tag_type_repository = TagTypeRepository(db)
    return TagTypeService(tag_type_repository)

@router.post(
    "",
    response_model=TagTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tag type",
    description="Create a new tag type with validation for duplicate names and field constraints",
    responses={
        400: {"description": "Validation error (e.g., duplicate name)"},
    },
)
async def create_tag_type(
    tag_type: TagTypeCreate,
    service: TagTypeService = Depends(get_tag_type_service)
):
    """Create a new tag type."""
    try:
        return await service.create(tag_type.model_dump())
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=list[TagTypeResponse],
    status_code=status.HTTP_200_OK,
    summary="List all tag types",
    description="Retrieve all tag types ordered by display_order"
)
async def list_tag_types(
    service: TagTypeService = Depends(get_tag_type_service)
):
    """List all tag types."""
    return await service.list_all()


@router.get(
    "/{tag_type_id}",
    response_model=TagTypeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get tag type by ID",
    description="Retrieve a specific tag type by its UUID",
    responses={
        404: {"description": "Tag type not found"},
    },
)
async def get_tag_type(
    tag_type_id: UUID,
    service: TagTypeService = Depends(get_tag_type_service)
):
    """Get a specific tag type by ID."""
    try:
        return await service.get_by_id(tag_type_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{tag_type_id}",
    response_model=TagTypeResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a tag type",
    description="Update an existing tag type with validation",
    responses={
        400: {"description": "Validation error (e.g., duplicate name)"},
    },
)
async def update_tag_type(
    tag_type_id: UUID,
    update_data: TagTypeUpdate,
    service: TagTypeService = Depends(get_tag_type_service)
):
    """Update an existing tag type."""
    try:
        # Only include fields that were explicitly set
        update_dict = update_data.model_dump(exclude_unset=True)
        return await service.update(tag_type_id, update_dict)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{tag_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tag type",
    description="Soft delete a tag type (sets is_deleted flag)",
    responses={
        404: {"description": "Tag type not found"},
    },
)
async def delete_tag_type(
    tag_type_id: UUID,
    service: TagTypeService = Depends(get_tag_type_service)
):
    """Soft delete a tag type."""
    try:
        await service.delete(tag_type_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
