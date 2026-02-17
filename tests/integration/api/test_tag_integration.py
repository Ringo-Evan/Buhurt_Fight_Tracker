"""
Integration tests for Tag endpoints with real PostgreSQL database.

Uses Testcontainers to spin up a real PostgreSQL instance for testing the
Tag API endpoints. These tests verify that the entire stack (API -> Service -> Repository -> Database)
works correctly together.

Following the tag.feature scenarios as specification.

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


class TestTagIntegration:
    """Integration tests for Tag API endpoints with real database."""

    @pytest.mark.asyncio
    async def test_create_tag_with_valid_tag_type(self, db_session):
        """
        Scenario: Create a tag with valid tag type

        Given the following tag types exist:
            | name          | is_privileged | display_order |
            | fight_format  | true          | 1             |
        When I create a tag with the following details:
            | tag_type_name | value    |
            | fight_format  | singles  |
        Then the tag should exist with value "singles"
        And the tag should reference tag type "fight_format"

        Verifies:
        - POST /tags endpoint creates tag in database
        - Response contains correct data and status code
        - Tag persists with correct tag_type reference
        """
        # Arrange: Override the database dependency to use testcontainers
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        # Create prerequisite tag type (Background)
        from app.repositories.tag_type_repository import TagTypeRepository
        tag_type_repo = TagTypeRepository(db_session)
        fight_format = await tag_type_repo.create({
            'name': 'fight_format',
            'is_privileged': True,
            'is_parent': False,
            'has_children': False,
            'display_order': 1
        })
        await db_session.commit()

        # Tag data to create
        tag_data = {
            'tag_type_id': str(fight_format.id),
            'value': 'singles'
        }

        try:
            # Act: Make API request with AsyncClient
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/tags", json=tag_data)

            # Assert: Verify response
            assert response.status_code == 201
            response_data = response.json()
            assert response_data['value'] == 'singles'
            assert response_data['tag_type_id'] == str(fight_format.id)
            assert 'id' in response_data

            # Verify the tag was actually persisted in the database
            from app.repositories.tag_repository import TagRepository
            tag_repo = TagRepository(db_session)
            tag = await tag_repo.get_by_id(response_data['id'])
            assert tag is not None
            assert tag.value == 'singles'
            assert tag.tag_type_id == fight_format.id

        finally:
            # Cleanup: Remove the dependency override
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_retrieve_tag_by_id(self, db_session):
        """
        Scenario: Retrieve tag by ID

        Given a tag exists with tag_type "fight_format" and value "singles"
        When I retrieve the tag by ID
        Then I should receive the tag with value "singles"
        And it should reference tag type "fight_format"

        Verifies:
        - GET /tags/{id} returns specific tag
        - Response contains correct data
        - Tag type reference is included
        """
        # Arrange: Override the database dependency
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        # Create prerequisite tag type
        from app.repositories.tag_type_repository import TagTypeRepository
        tag_type_repo = TagTypeRepository(db_session)
        fight_format = await tag_type_repo.create({
            'name': 'fight_format',
            'is_privileged': True,
            'is_parent': False,
            'has_children': False,
            'display_order': 1
        })

        # Create the tag
        from app.repositories.tag_repository import TagRepository
        tag_repo = TagRepository(db_session)
        tag = await tag_repo.create({
            'tag_type_id': fight_format.id,
            'value': 'singles'
        })
        await db_session.commit()

        try:
            # Act: Retrieve by ID
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(f"/api/v1/tags/{tag.id}")

            # Assert
            assert response.status_code == 200
            response_data = response.json()

            assert response_data['id'] == str(tag.id)
            assert response_data['value'] == 'singles'
            assert response_data['tag_type_id'] == str(fight_format.id)

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_prevent_tag_creation_with_nonexistent_tag_type(self, db_session):
        """
        Scenario: Prevent tag creation with nonexistent tag type

        When I attempt to create a tag with tag_type "nonexistent" and value "test"
        Then I should receive an error indicating tag type does not exist

        Verifies:
        - POST /tags with invalid tag_type_id returns 400
        - Error message indicates tag type not found
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        from uuid import uuid4
        nonexistent_tag_type_id = uuid4()

        tag_data = {
            'tag_type_id': str(nonexistent_tag_type_id),
            'value': 'test'
        }

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/tags", json=tag_data)

            assert response.status_code == 400
            error_data = response.json()
            assert 'detail' in error_data
            assert 'not found' in error_data['detail'].lower()

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_all_tags(self, db_session):
        """
        Scenario: List all tags

        Given the following tags exist:
            | tag_type_name | value   |
            | fight_format  | singles |
            | fight_format  | melee   |
            | category      | duel    |
        When I retrieve the list of tags
        Then I should see 3 tags

        Verifies:
        - GET /tags returns all tags
        - Response contains correct count
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        # Create prerequisite tag types
        from app.repositories.tag_type_repository import TagTypeRepository
        from app.repositories.tag_repository import TagRepository

        tag_type_repo = TagTypeRepository(db_session)
        fight_format = await tag_type_repo.create({
            'name': 'fight_format',
            'is_privileged': True,
            'is_parent': False,
            'has_children': False,
            'display_order': 1
        })
        category = await tag_type_repo.create({
            'name': 'category',
            'is_privileged': True,
            'is_parent': True,
            'has_children': False,
            'display_order': 2
        })

        # Create tags
        tag_repo = TagRepository(db_session)
        await tag_repo.create({'tag_type_id': fight_format.id, 'value': 'singles'})
        await tag_repo.create({'tag_type_id': fight_format.id, 'value': 'melee'})
        await tag_repo.create({'tag_type_id': category.id, 'value': 'duel'})
        await db_session.commit()

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/api/v1/tags")

            assert response.status_code == 200
            tags = response.json()
            assert len(tags) == 3

            values = [t['value'] for t in tags]
            assert 'singles' in values
            assert 'melee' in values
            assert 'duel' in values

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_tag_value(self, db_session):
        """
        Scenario: Update a tag value

        Given a tag exists with tag_type "category" and value "duel"
        When I update the tag value to "profight"
        Then the tag should have value "profight"
        And the tag type should remain "category"

        Verifies:
        - PATCH /tags/{id} updates tag value
        - Tag type remains unchanged
        - Updated value persists
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        # Create prerequisite tag type
        from app.repositories.tag_type_repository import TagTypeRepository
        from app.repositories.tag_repository import TagRepository

        tag_type_repo = TagTypeRepository(db_session)
        category = await tag_type_repo.create({
            'name': 'category',
            'is_privileged': True,
            'is_parent': True,
            'has_children': False,
            'display_order': 2
        })

        # Create the tag
        tag_repo = TagRepository(db_session)
        tag = await tag_repo.create({
            'tag_type_id': category.id,
            'value': 'duel'
        })
        await db_session.commit()

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.patch(
                    f"/api/v1/tags/{tag.id}",
                    json={'value': 'profight'}
                )

            assert response.status_code == 200
            response_data = response.json()
            assert response_data['value'] == 'profight'
            assert response_data['tag_type_id'] == str(category.id)

            # Verify persistence
            updated_tag = await tag_repo.get_by_id(tag.id)
            assert updated_tag.value == 'profight'

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_soft_delete_tag(self, db_session):
        """
        Scenario: Soft delete a tag

        Given a tag exists with tag_type "weapon" and value "sword"
        When I delete the tag
        Then the tag should not appear in the list
        But the tag should still exist in the database with is_deleted true

        Verifies:
        - DELETE /tags/{id} soft deletes tag
        - Deleted tag doesn't appear in list
        - is_deleted flag set to true
        - Data still exists in database
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        # Create prerequisite tag type
        from app.repositories.tag_type_repository import TagTypeRepository
        from app.repositories.tag_repository import TagRepository

        tag_type_repo = TagTypeRepository(db_session)
        weapon = await tag_type_repo.create({
            'name': 'weapon',
            'is_privileged': True,
            'is_parent': False,
            'has_children': False,
            'display_order': 3
        })

        # Create the tag
        tag_repo = TagRepository(db_session)
        tag = await tag_repo.create({
            'tag_type_id': weapon.id,
            'value': 'sword'
        })
        await db_session.commit()

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                # Delete the tag
                delete_response = await client.delete(f"/api/v1/tags/{tag.id}")
                assert delete_response.status_code == 204

                # Verify not in list
                list_response = await client.get("/api/v1/tags")
                tags = list_response.json()
                values = [t['value'] for t in tags]
                assert 'sword' not in values

            # Verify still exists with is_deleted=True
            deleted_tag = await tag_repo.get_by_id(tag.id, include_deleted=True)
            assert deleted_tag is not None
            assert deleted_tag.value == 'sword'
            assert deleted_tag.is_deleted == True

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_validate_tag_value_required(self, db_session):
        """
        Scenario: Validate tag value is required

        When I attempt to create a tag with empty value
        Then I should receive an error indicating value is required

        Verifies:
        - Empty value rejected at schema validation level (422)
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        # Create prerequisite tag type
        from app.repositories.tag_type_repository import TagTypeRepository
        tag_type_repo = TagTypeRepository(db_session)
        fight_format = await tag_type_repo.create({
            'name': 'fight_format',
            'is_privileged': True,
            'is_parent': False,
            'has_children': False,
            'display_order': 1
        })
        await db_session.commit()

        tag_data = {
            'tag_type_id': str(fight_format.id),
            'value': ''  # Empty value
        }

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/tags", json=tag_data)

            assert response.status_code == 422  # Pydantic validation error

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_validate_tag_value_length(self, db_session):
        """
        Scenario: Validate tag value length

        When I attempt to create a tag with a value longer than 100 characters
        Then I should receive an error indicating value is too long

        Verifies:
        - Values exceeding 100 characters are rejected (422)
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        # Create prerequisite tag type
        from app.repositories.tag_type_repository import TagTypeRepository
        tag_type_repo = TagTypeRepository(db_session)
        fight_format = await tag_type_repo.create({
            'name': 'fight_format',
            'is_privileged': True,
            'is_parent': False,
            'has_children': False,
            'display_order': 1
        })
        await db_session.commit()

        # Value with 101 characters (exceeds limit)
        long_value = 'a' * 101

        tag_data = {
            'tag_type_id': str(fight_format.id),
            'value': long_value
        }

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/tags", json=tag_data)

            assert response.status_code == 422  # Pydantic validation error

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_tag_with_parent_tag(self, db_session):
        """
        Scenario: Create tag with parent tag (hierarchy)

        Given a tag exists with tag_type "category" and value "melee"
        When I create a tag with the following details:
            | tag_type_name | value | parent_tag_value |
            | weapon        | sword | melee            |
        Then the tag should exist with value "sword"
        And the tag should have parent tag with value "melee"

        Verifies:
        - POST /tags with parent_tag_id creates hierarchical tag
        - Parent tag reference is correct
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        # Create prerequisite tag types
        from app.repositories.tag_type_repository import TagTypeRepository
        from app.repositories.tag_repository import TagRepository

        tag_type_repo = TagTypeRepository(db_session)
        category = await tag_type_repo.create({
            'name': 'category',
            'is_privileged': True,
            'is_parent': True,
            'has_children': False,
            'display_order': 2
        })
        weapon = await tag_type_repo.create({
            'name': 'weapon',
            'is_privileged': True,
            'is_parent': False,
            'has_children': False,
            'display_order': 3
        })

        # Create parent tag
        tag_repo = TagRepository(db_session)
        parent_tag = await tag_repo.create({
            'tag_type_id': category.id,
            'value': 'melee'
        })
        await db_session.commit()

        # Create child tag with parent reference
        tag_data = {
            'tag_type_id': str(weapon.id),
            'value': 'sword',
            'parent_tag_id': str(parent_tag.id)
        }

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/tags", json=tag_data)

            assert response.status_code == 201
            response_data = response.json()
            assert response_data['value'] == 'sword'
            assert response_data['parent_tag_id'] == str(parent_tag.id)

            # Verify the tag was persisted with correct parent
            child_tag = await tag_repo.get_by_id(response_data['id'])
            assert child_tag is not None
            assert child_tag.value == 'sword'
            assert child_tag.parent_tag_id == parent_tag.id

        finally:
            app.dependency_overrides.clear()
