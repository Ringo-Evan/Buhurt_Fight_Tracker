"""
FastAPI router for Fighter endpoints.

Provides CRUD operations for fighters with proper error handling
and OpenAPI documentation.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.fighter_repository import FighterRepository
from app.repositories.team_repository import TeamRepository
from app.services.fighter_service import FighterService
from app.schemas.fighter import (
    FighterCreate,
    FighterUpdate,
    FighterFullResponse,
)
from app.exceptions import FighterNotFoundError, InvalidTeamError, ValidationError

router = APIRouter(prefix="/fighters", tags=["Fighters"])


def get_fighter_service(db: AsyncSession = Depends(get_db)) -> FighterService:
    """Dependency that provides a FighterService instance."""
    fighter_repository = FighterRepository(db)
    team_repository = TeamRepository(db)
    return FighterService(fighter_repository, team_repository)


@router.post(
    "",
    response_model=FighterFullResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new fighter",
    description="Create a new fighter associated with an existing team.",
)
async def create_fighter(
    fighter_data: FighterCreate,
    service: FighterService = Depends(get_fighter_service),
) -> FighterFullResponse:
    """
    Create a new fighter.

    - **name**: Fighter name (1-100 characters)
    - **team_id**: UUID of an existing, active team
    """
    try:
        fighter = await service.create(fighter_data.model_dump())
        return FighterFullResponse.model_validate(fighter)
    except InvalidTeamError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.get(
    "",
    response_model=list[FighterFullResponse],
    summary="List all fighters",
    description="Retrieve a list of all active fighters with team and country details.",
)
async def list_fighters(
    include_deleted: bool = Query(False, description="Include soft-deleted fighters (admin only)"),
    service: FighterService = Depends(get_fighter_service),
) -> list[FighterFullResponse]:
    """List all fighters, optionally including deleted ones."""
    fighters = await service.list_all(include_deleted=include_deleted)
    return [FighterFullResponse.model_validate(f) for f in fighters]


@router.get(
    "/by-team/{team_id}",
    response_model=list[FighterFullResponse],
    summary="List fighters by team",
    description="Retrieve all fighters for a specific team.",
)
async def list_fighters_by_team(
    team_id: UUID,
    include_deleted: bool = Query(False, description="Include soft-deleted fighters (admin only)"),
    service: FighterService = Depends(get_fighter_service),
) -> list[FighterFullResponse]:
    """List all fighters for a specific team."""
    fighters = await service.list_by_team(team_id, include_deleted=include_deleted)
    return [FighterFullResponse.model_validate(f) for f in fighters]


@router.get(
    "/by-country/{country_id}",
    response_model=list[FighterFullResponse],
    summary="List fighters by country",
    description="Retrieve all fighters for teams in a specific country.",
)
async def list_fighters_by_country(
    country_id: UUID,
    include_deleted: bool = Query(False, description="Include soft-deleted fighters (admin only)"),
    service: FighterService = Depends(get_fighter_service),
) -> list[FighterFullResponse]:
    """List all fighters for teams in a specific country."""
    fighters = await service.list_by_country(country_id, include_deleted=include_deleted)
    return [FighterFullResponse.model_validate(f) for f in fighters]


@router.get(
    "/{fighter_id}",
    response_model=FighterFullResponse,
    summary="Get a fighter by ID",
    description="Retrieve a single fighter by its UUID with full team and country details.",
)
async def get_fighter(
    fighter_id: UUID,
    include_deleted: bool = Query(False, description="Include soft-deleted fighters (admin only)"),
    service: FighterService = Depends(get_fighter_service),
) -> FighterFullResponse:
    """Get a fighter by its UUID."""
    try:
        fighter = await service.get_by_id(fighter_id, include_deleted=include_deleted)
        return FighterFullResponse.model_validate(fighter)
    except FighterNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fighter with ID {fighter_id} not found",
        )


@router.patch(
    "/{fighter_id}",
    response_model=FighterFullResponse,
    summary="Update a fighter",
    description="Update a fighter's name or team (transfer).",
)
async def update_fighter(
    fighter_id: UUID,
    fighter_data: FighterUpdate,
    service: FighterService = Depends(get_fighter_service),
) -> FighterFullResponse:
    """Update a fighter's attributes or transfer to a different team."""
    try:
        # Filter out None values
        update_data = {k: v for k, v in fighter_data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update",
            )
        fighter = await service.update(fighter_id, update_data)
        return FighterFullResponse.model_validate(fighter)
    except FighterNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fighter with ID {fighter_id} not found",
        )
    except InvalidTeamError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.delete(
    "/{fighter_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete a fighter",
    description="Soft delete a fighter (sets is_deleted flag).",
)
async def delete_fighter(
    fighter_id: UUID,
    service: FighterService = Depends(get_fighter_service),
) -> None:
    """Soft delete a fighter."""
    try:
        await service.delete(fighter_id)
    except FighterNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fighter with ID {fighter_id} not found",
        )
