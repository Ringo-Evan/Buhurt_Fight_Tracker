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
from app.services.fight_service import FightService
from app.schemas.fight import FightCreate, FightUpdate, FightResponse
from app.exceptions import FightNotFoundError, ValidationError

router = APIRouter(prefix="/fights", tags=["Fights"])


def get_fight_service(db: AsyncSession = Depends(get_db)) -> FightService:
    """Dependency that provides a FightService instance."""
    repository = FightRepository(db)
    return FightService(repository)


@router.post(
    "",
    response_model=FightResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new fight",
    description="Record a new fight with date, location, and optional video URL.",
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
    """
    try:
        fight = await service.create(fight_data.model_dump())
        return FightResponse.model_validate(fight)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
    include_deleted: bool = Query(False, description="Include soft-deleted fights (admin only)"),
    service: FightService = Depends(get_fight_service),
) -> list[FightResponse]:
    """List all fights, optionally filtered by date range."""
    if start_date and end_date:
        fights = await service.list_by_date_range(start_date, end_date, include_deleted)
    else:
        fights = await service.list_all(include_deleted=include_deleted)
    return [FightResponse.model_validate(f) for f in fights]


@router.get(
    "/{fight_id}",
    response_model=FightResponse,
    summary="Get a fight by ID",
    description="Retrieve a single fight by its UUID.",
)
async def get_fight(
    fight_id: UUID,
    include_deleted: bool = Query(False, description="Include soft-deleted fights (admin only)"),
    service: FightService = Depends(get_fight_service),
) -> FightResponse:
    """Get a fight by its UUID."""
    try:
        fight = await service.get_by_id(fight_id, include_deleted=include_deleted)
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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.delete(
    "/{fight_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete a fight",
    description="Soft delete a fight (sets is_deleted flag).",
)
async def delete_fight(
    fight_id: UUID,
    service: FightService = Depends(get_fight_service),
) -> None:
    """Soft delete a fight."""
    try:
        await service.delete(fight_id)
    except FightNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fight with ID {fight_id} not found",
        )
