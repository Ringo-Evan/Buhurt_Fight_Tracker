"""
FastAPI router for Country endpoints.

Provides CRUD operations for countries with proper error handling
and OpenAPI documentation.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.country_repository import CountryRepository
from app.services.country_service import CountryService
from app.schemas.country import CountryCreate, CountryUpdate, CountryResponse
from app.exceptions import CountryNotFoundError, DuplicateCountryCodeError, ValidationError

router = APIRouter(prefix="/countries", tags=["Countries"])


def get_country_service(db: AsyncSession = Depends(get_db)) -> CountryService:
    """Dependency that provides a CountryService instance."""
    repository = CountryRepository(db)
    return CountryService(repository)


@router.post(
    "",
    response_model=CountryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new country",
    description="Create a new country with a unique ISO 3166-1 alpha-3 code.",
    responses={
        409: {"description": "Country with this code already exists"},
        422: {"description": "Validation error (e.g., invalid code format)"},
    },
)
async def create_country(
    country_data: CountryCreate,
    service: CountryService = Depends(get_country_service),
) -> CountryResponse:
    """
    Create a new country.

    - **name**: Country name (1-100 characters)
    - **code**: ISO 3166-1 alpha-3 country code (3 uppercase letters)
    """
    try:
        country = await service.create(country_data.model_dump())
        return CountryResponse.model_validate(country)
    except DuplicateCountryCodeError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=list[CountryResponse],
    summary="List all countries",
    description="Retrieve a list of all active countries.",
)
async def list_countries(
    include_deactivate: bool = Query(False, description="Include soft-deleted countries (admin only)"),
    service: CountryService = Depends(get_country_service),
) -> list[CountryResponse]:
    """List all countries, optionally including deleted ones."""
    countries = await service.list_all(include_deactivated=include_deactivate)
    return [CountryResponse.model_validate(c) for c in countries]


@router.get(
    "/{country_id}",
    response_model=CountryResponse,
    summary="Get a country by ID",
    description="Retrieve a single country by its UUID.",
    responses={
        404: {"description": "Country not found"},
    },
)
async def get_country(
    country_id: UUID,
    include_deactivate: bool = Query(False, description="Include soft-deleted countries (admin only)"),
    service: CountryService = Depends(get_country_service),
) -> CountryResponse:
    """Get a country by its UUID."""
    try:
        country = await service.get_by_id(country_id, include_deactivated=include_deactivate)
        return CountryResponse.model_validate(country)
    except CountryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with ID {country_id} not found",
        )


@router.get(
    "/code/{code}",
    response_model=CountryResponse,
    summary="Get a country by ISO code",
    description="Retrieve a single country by its ISO 3166-1 alpha-3 code.",
    responses={
        404: {"description": "Country with this code not found"},
    },
)
async def get_country_by_code(
    code: str,
    include_deactivate: bool = Query(False, description="Include soft-deleted countries (admin only)"),
    service: CountryService = Depends(get_country_service),
) -> CountryResponse:
    """Get a country by its ISO code."""
    try:
        country = await service.get_by_code(code.upper())
        return CountryResponse.model_validate(country)
    except CountryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with code {code} not found",
        )


@router.patch(
    "/{country_id}",
    response_model=CountryResponse,
    summary="Update a country",
    description="Update a country's name or code.",
    responses={
        400: {"description": "No valid fields provided for update"},
        404: {"description": "Country not found"},
        409: {"description": "Country with this code already exists"},
        422: {"description": "Validation error"},
    },
)
async def update_country(
    country_id: UUID,
    country_data: CountryUpdate,
    service: CountryService = Depends(get_country_service),
) -> CountryResponse:
    """Update a country's attributes."""
    try:
        # Filter out None values
        update_data = {k: v for k, v in country_data.model_dump(exclude={"include_deactivate"}).items() if v is not None}
        is_deactivated = country_data.include_deactivate
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update",
            )
        country = await service.update(country_id, update_data, include_deactivated=is_deactivated)
        return CountryResponse.model_validate(country)
    except CountryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with ID {country_id} not found",
        )
    except DuplicateCountryCodeError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch(
    "/{country_id}/deactivate",
    response_model=CountryResponse,
    summary="Deactivate a country",
    description="Deactivate a country (sets is_deactivated flag). Record is preserved.",
    responses={
        404: {"description": "Country not found"},
    },
)
async def deactivate_country(
    country_id: UUID,
    service: CountryService = Depends(get_country_service),
) -> CountryResponse:
    """Deactivate a country (soft delete)."""
    try:
        await service.deactivate(country_id)
        country = await service.get_by_id(country_id, include_deactivated=True)
        return CountryResponse.model_validate(country)
    except CountryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with ID {country_id} not found",
        )


@router.delete(
    "/{country_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete a country",
    description="Permanently delete a country from the database. Fails if the country has relationships.",
    responses={
        400: {"description": "Country has existing relationships"},
        404: {"description": "Country not found"},
    },
)
async def delete_country(
    country_id: UUID,
    service: CountryService = Depends(get_country_service),
) -> None:
    """Permanently delete a country."""
    try:
        await service.permanent_delete(country_id)
    except CountryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with ID {country_id} not found",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
