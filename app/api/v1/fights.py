"""
FastAPI router for Fight endpoints.

Provides CRUD operations for fights with proper error handling
and OpenAPI documentation.
"""

from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.fight_repository import FightRepository
from app.repositories.fight_participation_repository import FightParticipationRepository
from app.repositories.fighter_repository import FighterRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.tag_type_repository import TagTypeRepository
from app.services.fight_service import FightService
from app.schemas.fight import FightCreate, FightUpdate, FightResponse, TagAddRequest, TagUpdateRequest
from app.schemas.tag_schema import TagResponse
from app.exceptions import FightNotFoundError, ValidationError

router = APIRouter(prefix="/fights", tags=["Fights"])


def get_fight_service(db: AsyncSession = Depends(get_db)) -> FightService:
    """Dependency that provides a FightService instance with all repositories."""
    fight_repository = FightRepository(db)
    participation_repository = FightParticipationRepository(db)
    fighter_repository = FighterRepository(db)
    tag_repository = TagRepository(db)
    tag_type_repository = TagTypeRepository(db)
    return FightService(
        fight_repository=fight_repository,
        participation_repository=participation_repository,
        fighter_repository=fighter_repository,
        tag_repository=tag_repository,
        tag_type_repository=tag_type_repository
    )


@router.post(
    "",
    response_model=FightResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new fight",
    description="Record a new fight with date, location, and optional participants.",
    responses={
        422: {"description": "Validation error (e.g., future date, invalid format, invalid fighter)"},
    },
)
async def create_fight(
    fight_data: FightCreate,
    service: FightService = Depends(get_fight_service),
) -> FightResponse:
    """
    Create a new fight record.

    - **date**: Date of the fight (cannot be in the future)
    - **location**: Event name/location (1-200 characters)
    - **video_url**: Optional URL to fight video
    - **winner_side**: Which side won (1, 2, or null for draw/unknown)
    - **participations**: Optional list of fighter participations
    """
    try:
        # Extract participations from request
        participations = fight_data.participations
        fight_dict = fight_data.model_dump(exclude={"participations", "fight_format"})
        fight_format = fight_data.fight_format

        if participations:
            # Create fight with participations atomically
            participations_data = [p.model_dump() for p in participations]
            fight = await service.create_with_participants(fight_data=fight_dict, fight_format=str(fight_format), participations_data=participations_data)
        else:
            # Create fight without participations
            fight = await service.create(fight_dict)

        return FightResponse.model_validate(fight)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=list[FightResponse],
    summary="List all fights",
    description="Retrieve a list of all fights, optionally filtered by date range.",
)
async def list_fights(
    start_date: date | None = Query(None, description="Filter fights from this date"),
    end_date: date | None = Query(None, description="Filter fights until this date"),
    include_deactivate: bool = Query(False, description="Include deactivated fights (admin only)"),
    service: FightService = Depends(get_fight_service),
) -> list[FightResponse]:
    """List all fights, optionally filtered by date range."""
    if start_date and end_date:
        fights = await service.list_by_date_range(start_date, end_date, include_deactivate)
    else:
        fights = await service.list_all(include_deactivated=include_deactivate)
    return [FightResponse.model_validate(f) for f in fights]


@router.get(
    "/{fight_id}",
    response_model=FightResponse,
    summary="Get a fight by ID",
    description="Retrieve a single fight by its UUID.",
    responses={
        404: {"description": "Fight not found"},
    },
)
async def get_fight(
    fight_id: UUID,
    include_deactivate: bool = Query(False, description="Include deactivated fights (admin only)"),
    service: FightService = Depends(get_fight_service),
) -> FightResponse:
    """Get a fight by its UUID."""
    try:
        fight = await service.get_by_id(fight_id, include_deactivated=include_deactivate)
        return FightResponse.model_validate(fight)
    except FightNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fight with ID {fight_id} not found",
        )


@router.patch(
    "/{fight_id}",
    response_model=FightResponse,
    summary="Update a fight",
    description="Update a fight's details.",
    responses={
        400: {"description": "No valid fields provided for update"},
        404: {"description": "Fight not found"},
        422: {"description": "Validation error"},
    },
)
async def update_fight(
    fight_id: UUID,
    fight_data: FightUpdate,
    service: FightService = Depends(get_fight_service),
) -> FightResponse:
    """Update a fight's attributes."""
    try:
        # Filter out None values
        update_data = {k: v for k, v in fight_data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update",
            )
        fight = await service.update(fight_id, update_data)
        return FightResponse.model_validate(fight)
    except FightNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fight with ID {fight_id} not found",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch(
    "/{fight_id}/deactivate",
    response_model=FightResponse,
    summary="Deactivate a fight",
    description="Deactivate a fight (sets is_deactivated flag). Record is preserved.",
    responses={
        404: {"description": "Fight not found"},
    },
)
async def deactivate_fight(
    fight_id: UUID,
    service: FightService = Depends(get_fight_service),
) -> FightResponse:
    """Deactivate a fight (soft delete)."""
    try:
        await service.deactivate(fight_id)
        fight = await service.get_by_id(fight_id, include_deactivated=True)
        return FightResponse.model_validate(fight)
    except FightNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fight with ID {fight_id} not found",
        )


@router.post(
    "/{fight_id}/tags",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a tag to a fight",
    description="Add a tag (category, gender, or custom) to a fight.",
    responses={
        400: {"description": "Validation error (invalid value, wrong type for fight_format, etc.)"},
        404: {"description": "Fight not found"},
    },
)
async def add_tag_to_fight(
    fight_id: UUID,
    tag_data: TagAddRequest,
    service: FightService = Depends(get_fight_service),
) -> TagResponse:
    """Add a tag to a fight."""
    try:
        tag = await service.add_tag(
            fight_id=fight_id,
            tag_type_name=tag_data.tag_type_name,
            value=tag_data.value,
            parent_tag_id=tag_data.parent_tag_id,
        )
        return TagResponse.model_validate(tag)
    except FightNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fight with ID {fight_id} not found",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.patch(
    "/{fight_id}/tags/{tag_id}",
    response_model=TagResponse,
    summary="Update a tag on a fight",
    description="Update a tag's value. Supercategory tags are immutable (DD-011).",
    responses={
        404: {"description": "Fight or tag not found"},
        422: {"description": "Supercategory is immutable, or invalid value"},
    },
)
async def update_fight_tag(
    fight_id: UUID,
    tag_id: UUID,
    tag_data: TagUpdateRequest,
    service: FightService = Depends(get_fight_service),
) -> TagResponse:
    """Update the value of a tag on a fight."""
    try:
        tag = await service.update_tag(fight_id=fight_id, tag_id=tag_id, new_value=tag_data.value)
        return TagResponse.model_validate(tag)
    except FightNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fight with ID {fight_id} not found",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.patch(
    "/{fight_id}/tags/{tag_id}/deactivate",
    response_model=TagResponse,
    summary="Deactivate a tag on a fight",
    description="Deactivate a tag. Cascades to child tags.",
    responses={
        404: {"description": "Fight or tag not found"},
        422: {"description": "Tag does not belong to this fight"},
    },
)
async def deactivate_fight_tag(
    fight_id: UUID,
    tag_id: UUID,
    service: FightService = Depends(get_fight_service),
) -> TagResponse:
    """Deactivate a tag on a fight (with cascade to children)."""
    try:
        tag = await service.deactivate_tag(fight_id=fight_id, tag_id=tag_id)
        return TagResponse.model_validate(tag)
    except FightNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fight with ID {fight_id} not found",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/{fight_id}/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hard delete a tag from a fight",
    description="Permanently delete a tag. Rejects with 422 if active children exist (DD-012).",
    responses={
        404: {"description": "Fight or tag not found"},
        422: {"description": "Tag has active children — deactivate or delete them first"},
    },
)
async def delete_fight_tag(
    fight_id: UUID,
    tag_id: UUID,
    service: FightService = Depends(get_fight_service),
) -> None:
    """Hard delete a tag from a fight."""
    try:
        await service.delete_tag(fight_id=fight_id, tag_id=tag_id)
    except FightNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fight with ID {fight_id} not found",
        )
    except ValidationError as e:
        # Could be "not found on fight" or "has children"
        detail = str(e)
        if "not found" in detail.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


@router.delete(
    "/{fight_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete a fight",
    description="Permanently delete a fight from the database.",
    responses={
        404: {"description": "Fight not found"},
    },
)
async def delete_fight(
    fight_id: UUID,
    service: FightService = Depends(get_fight_service),
) -> None:
    """Permanently delete a fight."""
    try:
        await service.delete(fight_id)
    except FightNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fight with ID {fight_id} not found",
        )
