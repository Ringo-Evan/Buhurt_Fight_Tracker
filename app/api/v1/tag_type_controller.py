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
from app.schemas.tag_type_schema import TagTypeCreate, TagTypeResponse
from app.exceptions import TagTypeNotFoundError, ValidationError

router = APIRouter(prefix="/tag-types", tags=["Tag Types"])


def get_tag_type_service(db: AsyncSession = Depends(get_db)) -> TagTypeService:
    """Dependency that provides a TagTypeService instance."""
    tag_type_repository = TagTypeRepository(db)
    return TagTypeService(tag_type_repository)

@router.post(
    "",
    response_model=TagTypeResponse,
    status_code=status.HTTP_201_CREATED
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
    
