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

    @pytest.mark.asyncio
    async def test_retrieve_all_tag_types_ordered_by_display_order(self, db_session):
        """
        Scenario 2: Retrieve all tag types ordered by display_order

        Given the following tag types exist (from Background):
            - fight_format (display_order=1)
            - category (display_order=2)
            - weapon (display_order=3)
        When I retrieve the list of tag types
        Then I should see tag types in this order

        Verifies:
        - GET /tag-types returns all tag types
        - Results are ordered by display_order
        - All fields are populated correctly
        """
        # Arrange: Override database dependency
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        # Create background tag types
        from app.repositories.tag_type_repository import TagTypeRepository
        repo = TagTypeRepository(db_session)

        await repo.create({'name': 'fight_format', 'is_privileged': True, 'is_parent': False, 'has_children': False, 'display_order': 1})
        await repo.create({'name': 'category', 'is_privileged': True, 'is_parent': True, 'has_children': False, 'display_order': 2})
        await repo.create({'name': 'weapon', 'is_privileged': True, 'is_parent': False, 'has_children': False, 'display_order': 3})
        await db_session.commit()

        try:
            # Act: Retrieve list of tag types
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/api/v1/tag-types")

            # Assert: Verify response
            assert response.status_code == 200
            tag_types = response.json()

            assert len(tag_types) == 3

            # Verify order by display_order
            assert tag_types[0]['name'] == 'fight_format'
            assert tag_types[0]['is_privileged'] == True
            assert tag_types[0]['display_order'] == 1

            assert tag_types[1]['name'] == 'category'
            assert tag_types[1]['is_privileged'] == True
            assert tag_types[1]['display_order'] == 2

            assert tag_types[2]['name'] == 'weapon'
            assert tag_types[2]['is_privileged'] == True
            assert tag_types[2]['display_order'] == 3

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_retrieve_tag_type_by_id(self, db_session):
        """
        Scenario 3: Retrieve a specific tag type by ID

        Given the tag type "category" exists
        When I retrieve the tag type "category" by ID
        Then I should receive the tag type with name "category"
        And it should have is_privileged equal to true

        Verifies:
        - GET /tag-types/{id} returns specific tag type
        - All fields are populated correctly
        """
        # Arrange
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        # Create the tag type
        from app.repositories.tag_type_repository import TagTypeRepository
        repo = TagTypeRepository(db_session)
        category = await repo.create({
            'name': 'category',
            'is_privileged': True,
            'is_parent': True,
            'has_children': False,
            'display_order': 2
        })
        await db_session.commit()

        try:
            # Act: Retrieve by ID
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(f"/api/v1/tag-types/{category.id}")

            # Assert
            assert response.status_code == 200
            tag_type = response.json()

            assert tag_type['name'] == 'category'
            assert tag_type['is_privileged'] == True
            assert tag_type['id'] == str(category.id)

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_tag_type(self, db_session):
        """
        Scenario 4: Update an existing tag type

        Given the tag type "weapon" exists
        When I update the tag type "weapon" with display_order=10
        Then the tag type "weapon" should have display_order equal to 10

        Verifies:
        - PATCH /tag-types/{id} updates tag type
        - Only specified fields are updated
        - Updated values persist
        """
        # Arrange
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        # Create the tag type
        from app.repositories.tag_type_repository import TagTypeRepository
        repo = TagTypeRepository(db_session)
        weapon = await repo.create({
            'name': 'weapon',
            'is_privileged': True,
            'is_parent': False,
            'has_children': False,
            'display_order': 3
        })
        await db_session.commit()

        try:
            # Act: Update display_order
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.patch(
                    f"/api/v1/tag-types/{weapon.id}",
                    json={'display_order': 10}
                )

            # Assert
            assert response.status_code == 200
            updated_tag_type = response.json()

            assert updated_tag_type['name'] == 'weapon'
            assert updated_tag_type['display_order'] == 10
            assert updated_tag_type['is_privileged'] == True  # Unchanged

            # Verify persistence
            refreshed = await repo.get_by_id(weapon.id)
            assert refreshed.display_order == 10

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_deactivate_tag_type(self, db_session):
        """
        Scenario 5: Deactivate a tag type

        Given the tag type "weapon" exists
        When I deactivate the tag type "weapon"
        Then the tag type "weapon" should not appear in the list
        But the tag type "weapon" should still exist in the database with is_deactivated true

        Verifies:
        - PATCH /tag-types/{id}/deactivate deactivates tag type
        - Deactivated tag types don't appear in list
        - is_deactivated flag set to true
        - Data still exists in database
        """
        # Arrange
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        # Create the tag type
        from app.repositories.tag_type_repository import TagTypeRepository
        repo = TagTypeRepository(db_session)
        weapon = await repo.create({
            'name': 'weapon',
            'is_privileged': True,
            'is_parent': False,
            'has_children': False,
            'display_order': 3
        })
        await db_session.commit()

        try:
            # Act: Deactivate
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                deactivate_response = await client.patch(f"/api/v1/tag-types/{weapon.id}/deactivate")
                assert deactivate_response.status_code == 200

                # Then: Verify not in list
                list_response = await client.get("/api/v1/tag-types")
                tag_types = list_response.json()
                names = [tt['name'] for tt in tag_types]
                assert 'weapon' not in names

            # But: Still exists in database with is_deactivated=True
            deactivated_tag_type = await repo.get_by_id(weapon.id, include_deactivated=True)
            assert deactivated_tag_type is not None
            assert deactivated_tag_type.name == 'weapon'
            assert deactivated_tag_type.is_deactivated == True

        finally:
            app.dependency_overrides.clear()



    @pytest.mark.asyncio
    async def test_create_tag_type_with_name_too_long_returns_422(self, db_session):
        """
        Scenario 8: Validate tag type name length

        When I attempt to create a tag type with a name longer than 50 characters
        Then I should receive an error indicating name is too long

        Verifies:
        - Names exceeding 50 characters are rejected
        - Pydantic validation error returned (422)
        """
        # Arrange
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        # Name with 51 characters (exceeds limit)
        long_name = 'a' * 51

        tag_type_data = {
            'name': long_name,
            'is_privileged': True
        }

        try:
            # Act
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/tag-types", json=tag_type_data)

            # Assert
            assert response.status_code == 422  # Pydantic validation error
            error_data = response.json()
            assert 'detail' in error_data

        finally:
            app.dependency_overrides.clear()
