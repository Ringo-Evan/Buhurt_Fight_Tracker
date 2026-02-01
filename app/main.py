"""
FastAPI application entry point.

Creates and configures the main FastAPI application with all routers
and middleware.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import api_v1_router

import uvicorn

# OpenAPI tag descriptions for Swagger UI grouping
tags_metadata = [
    {
        "name": "Health",
        "description": "Health check and status endpoints.",
    },
    {
        "name": "Countries",
        "description": "Manage countries. Countries are the top-level geographic entity that teams belong to.",
    },
    {
        "name": "Teams",
        "description": "Manage teams. Each team belongs to a country and contains fighters.",
    },
    {
        "name": "Fighters",
        "description": "Manage fighters. Each fighter belongs to a team and can participate in fights.",
    },
    {
        "name": "Fights",
        "description": "Manage fight records. Fights include date, location, format, and optional participant details.",
    },
    {
        "name": "Tag Types",
        "description": "Manage tag type categories. Tag types define the classification system for tags (e.g., fight_format, weapon_type).",
    },
    {
        "name": "Tags",
        "description": "Manage tags. Tags are values within a tag type that can be attached to fights for categorization.",
    },
]

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "API for indexing and cataloging Buhurt (medieval armored combat) fight videos.\n\n"
        "## Overview\n\n"
        "The Buhurt Fight Tracker provides a REST API to manage:\n"
        "- **Countries** and **Teams** (organizational hierarchy)\n"
        "- **Fighters** (individual combatants belonging to teams)\n"
        "- **Fights** (recorded bouts with participants, dates, and outcomes)\n"
        "- **Tags** (flexible categorization system for fights)\n\n"
        "## Key Concepts\n\n"
        "- All entities use **UUID** primary keys\n"
        "- Deletions are **soft deletes** (records are flagged, not removed)\n"
        "- Fights support two formats: **singles** (1v1) and **melee** (5v5+)\n"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=tags_metadata,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)