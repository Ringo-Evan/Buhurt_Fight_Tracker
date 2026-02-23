"""
API v1 routers.

Exports all v1 API routers for inclusion in the main application.
"""

from fastapi import APIRouter

from app.api.v1.countries import router as countries_router
from app.api.v1.teams import router as teams_router
from app.api.v1.fighters import router as fighters_router
from app.api.v1.fights import router as fights_router
from app.api.v1.tag_type_controller import router as tag_types_router

# Create combined v1 router
api_v1_router = APIRouter()

# Include all entity routers
api_v1_router.include_router(countries_router)
api_v1_router.include_router(teams_router)
api_v1_router.include_router(fighters_router)
api_v1_router.include_router(fights_router)
api_v1_router.include_router(tag_types_router)

__all__ = ["api_v1_router"]
