"""
Integration tests for TagType endpoints with real PostgreSQL database.

Uses Testcontainers to spin up a real PostgreSQL instance for testing the
TagType API endpoints. These tests verify that the entire stack (API -> Service -> Repository -> Database)
works correctly together.

Requirements:
- Docker Desktop must be running
- testcontainers package installed
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestTagTypeIntegration:
    """Integration tests for TagType API endpoints with real database."""

    @pytest.mark.asyncio
    async def test_create_tag_type(self, db_session):
        """
        Test the creation of a tag type via the API with real database.

        Verifies:
        - POST /tag-types endpoint creates tag type in database
        - Response contains correct data and status code
        - Tag type persists and can be retrieved

        Arrange: Set up async client with testcontainers database
        Act: Call the POST /tag-types endpoint with valid data
        Assert: Verify tag type was created successfully in database
        """
        # Arrange: Override the database dependency to use testcontainers
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        tag_type_data = {'name': 'Integration Test Tag Type'}

        try:
            # Act: Make API request with AsyncClient (properly handles async)
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/tag-types", json=tag_type_data)

            # Assert: Verify response
            assert response.status_code == 201
            response_data = response.json()
            assert response_data['name'] == 'Integration Test Tag Type'
            assert 'id' in response_data

            # Verify the tag type was actually persisted in the database
            from app.repositories.tag_type_repository import TagTypeRepository
            repo = TagTypeRepository(db_session)
            tag_types = await repo.list_all()
            assert len(tag_types) == 1
            assert tag_types[0].name == 'Integration Test Tag Type'

        finally:
            # Cleanup: Remove the dependency override
            app.dependency_overrides.clear()

