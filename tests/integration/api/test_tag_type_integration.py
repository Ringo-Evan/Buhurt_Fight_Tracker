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

        tag_type_data = {
            'name': 'fight_format',
            'is_privileged': True,
            'is_parent': False,
            'has_children': False,
            'display_order': 1
        }

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
            assert response_data['name'] == 'fight_format'
            assert response_data['is_privileged'] == True
            assert response_data['display_order'] == 1
            assert 'id' in response_data

            # Verify the tag type was actually persisted in the database
            from app.repositories.tag_type_repository import TagTypeRepository
            repo = TagTypeRepository(db_session)
            tag_types = await repo.list_all()
            assert len(tag_types) == 1
            assert tag_types[0].name == 'fight_format'

        finally:
            # Cleanup: Remove the dependency override
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_duplicate_tag_type_returns_400(self, db_session):
        """
        Test that creating a duplicate tag type name returns 400 error.

        Verifies:
        - Duplicate tag type names are rejected
        - Appropriate error message returned

        Arrange: Create an existing tag type
        Act: Attempt to create tag type with same name
        Assert: Receive 400 Bad Request with error message
        """
        # Arrange: Override the database dependency
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        tag_type_data = {
            'name': 'category',
            'is_privileged': True,
            'display_order': 1
        }

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                # Create first tag type
                response1 = await client.post("/api/v1/tag-types", json=tag_type_data)
                assert response1.status_code == 201

                # Act: Attempt to create duplicate
                response2 = await client.post("/api/v1/tag-types", json=tag_type_data)

                # Assert: Should receive 400 error
                assert response2.status_code == 400
                error_data = response2.json()
                assert 'detail' in error_data
                assert 'unique' in error_data['detail'].lower() or 'exists' in error_data['detail'].lower()

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_tag_type_with_empty_name_returns_422(self, db_session):
        """
        Test that creating a tag type with empty name returns 422 validation error.

        Verifies:
        - Empty names are rejected at schema validation level

        Arrange: Set up database session
        Act: Attempt to create tag type with empty name
        Assert: Receive 422 Unprocessable Entity
        """
        # Arrange
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        tag_type_data = {
            'name': '',  # Empty name
            'is_privileged': True
        }

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                # Act
                response = await client.post("/api/v1/tag-types", json=tag_type_data)

                # Assert
                assert response.status_code == 422  # Pydantic validation error

        finally:
            app.dependency_overrides.clear()

