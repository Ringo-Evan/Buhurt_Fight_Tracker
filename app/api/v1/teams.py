"""
FastAPI router for Team endpoints.

Provides CRUD operations for teams with proper error handling
and OpenAPI documentation.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.team_repository import TeamRepository
from app.repositories.country_repository import CountryRepository
from app.services.team_service import TeamService
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamWithCountryResponse,
)
from app.exceptions import TeamNotFoundError, InvalidCountryError, ValidationError

router = APIRouter(prefix="/teams", tags=["Teams"])


def get_team_service(db: AsyncSession = Depends(get_db)) -> TeamService:
    """Dependency that provides a TeamService instance."""
    team_repository = TeamRepository(db)
    country_repository = CountryRepository(db)
    return TeamService(team_repository, country_repository)


@router.post(
    "",
    response_model=TeamWithCountryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new team",
    description="Create a new team associated with an existing country.",
    responses={
        422: {"description": "Invalid country_id or validation error"},
    },
)
async def create_team(
    team_data: TeamCreate,
    service: TeamService = Depends(get_team_service),
) -> TeamWithCountryResponse:
    """
    Create a new team.

    - **name**: Team name (1-100 characters)
    - **country_id**: UUID of an existing, active country
    """
    try:
        team = await service.create(team_data.model_dump())
        return TeamWithCountryResponse.model_validate(team)
    except InvalidCountryError as e:
        raise HTTPException(
            #TODO: is this 400 or 422?
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=list[TeamWithCountryResponse],
    summary="List all teams",
    description="Retrieve a list of all active teams with their countries.",
)
async def list_teams(
    include_deactivate: bool = Query(False, description="Include deactivated teams (admin only)"),
    service: TeamService = Depends(get_team_service),
) -> list[TeamWithCountryResponse]:
    """List all teams, optionally including deleted ones."""
    teams = await service.list_all(include_deactivated=include_deactivate)
    return [TeamWithCountryResponse.model_validate(t) for t in teams]


@router.get(
    "/by-country/{country_id}",
    response_model=list[TeamWithCountryResponse],
    summary="List teams by country",
    description="Retrieve all teams for a specific country.",
)
async def list_teams_by_country(
    country_id: UUID,
    include_deactivate: bool = Query(False, description="Include deactivated teams (admin only)"),
    service: TeamService = Depends(get_team_service),
) -> list[TeamWithCountryResponse]:
    """List all teams for a specific country."""
    teams = await service.list_by_country(country_id, include_deactivated=include_deactivate)
    return [TeamWithCountryResponse.model_validate(t) for t in teams]


@router.get(
    "/{team_id}",
    response_model=TeamWithCountryResponse,
    summary="Get a team by ID",
    description="Retrieve a single team by its UUID with country details.",
    responses={
        404: {"description": "Team not found"},
    },
)
async def get_team(
    team_id: UUID,
    include_deactivate: bool = Query(False, description="Include deactivated teams (admin only)"),
    service: TeamService = Depends(get_team_service),
) -> TeamWithCountryResponse:
    """Get a team by its UUID."""
    try:
        team = await service.get_by_id(team_id, include_deactivated=include_deactivate)
        return TeamWithCountryResponse.model_validate(team)
    except TeamNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with ID {team_id} not found",
        )


@router.patch(
    "/{team_id}",
    response_model=TeamWithCountryResponse,
    summary="Update a team",
    description="Update a team's name or country.",
    responses={
        400: {"description": "No valid fields provided for update"},
        404: {"description": "Team not found"},
        422: {"description": "Invalid country_id or validation error"},
    },
)
async def update_team(
    team_id: UUID,
    team_data: TeamUpdate,
    service: TeamService = Depends(get_team_service),
) -> TeamWithCountryResponse:
    """Update a team's attributes."""
    try:
        # Filter out None values
        update_data = {k: v for k, v in team_data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update",
            )
        team = await service.update(team_id, update_data)
        return TeamWithCountryResponse.model_validate(team)
    except TeamNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with ID {team_id} not found",
        )
    except InvalidCountryError as e:
        raise HTTPException(
            #TODO: is this 400 or 422?
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch(
    "/{team_id}/deactivate",
    response_model=TeamWithCountryResponse,
    summary="Deactivate a team",
    description="Deactivate a team (sets is_deactivated flag). Record is preserved.",
    responses={
        404: {"description": "Team not found"},
    },
)
async def deactivate_team(
    team_id: UUID,
    service: TeamService = Depends(get_team_service),
) -> TeamWithCountryResponse:
    """Deactivate a team (soft delete)."""
    try:
        await service.deactivate(team_id)
        team = await service.get_by_id(team_id, include_deactivated=True)
        return TeamWithCountryResponse.model_validate(team)
    except TeamNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with ID {team_id} not found",
        )


@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete a team",
    description="Permanently delete a team from the database.",
    responses={
        404: {"description": "Team not found"},
    },
)
async def delete_team(
    team_id: UUID,
    service: TeamService = Depends(get_team_service),
) -> None:
    """Permanently delete a team."""
    try:
        await service.delete(team_id)
    except TeamNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with ID {team_id} not found",
        )
