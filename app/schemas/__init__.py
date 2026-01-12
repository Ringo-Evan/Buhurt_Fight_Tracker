"""
Pydantic schemas for API request/response validation.

This module exports all schema classes for use in API endpoints.
"""

from app.schemas.country import CountryCreate, CountryUpdate, CountryResponse
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamWithCountryResponse,
)
from app.schemas.fighter import (
    FighterCreate,
    FighterUpdate,
    FighterResponse,
    FighterWithTeamResponse,
    FighterFullResponse,
)
from app.schemas.fight import FightCreate, FightUpdate, FightResponse

__all__ = [
    # Country schemas
    "CountryCreate",
    "CountryUpdate",
    "CountryResponse",
    # Team schemas
    "TeamCreate",
    "TeamUpdate",
    "TeamResponse",
    "TeamWithCountryResponse",
    # Fighter schemas
    "FighterCreate",
    "FighterUpdate",
    "FighterResponse",
    "FighterWithTeamResponse",
    "FighterFullResponse",
    # Fight schemas
    "FightCreate",
    "FightUpdate",
    "FightResponse",
]
