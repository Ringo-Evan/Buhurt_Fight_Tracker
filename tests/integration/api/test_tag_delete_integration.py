"""
Integration tests for Tag hard delete endpoint with real PostgreSQL database.

Extends the existing tag integration tests to cover permanent delete behavior.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import get_db

pytestmark = pytest.mark.integration


class TestTagDeleteIntegration:
    """Integration tests for Tag permanent delete endpoint."""

    @pytest.mark.asyncio
    async def test_delete_tag_permanently_removes_from_database(self, db_session):
        """
        Scenario: Permanently delete a tag

        Given a tag type "fight_format" and tag "singles" exist
        When I DELETE /tags/{id}
        Then the response status should be 204
        And the tag should not exist in the database even with include_deactivated=True
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                # Arrange: create tag type and tag
                tt_response = await client.post(
                    "/api/v1/tag-types",
                    json={
                        "name": "fight_format",
                        "is_privileged": True,
                        "display_order": 1
                    }
                )
                assert tt_response.status_code == 201
                tag_type_id = tt_response.json()["id"]

                tag_response = await client.post(
                    "/api/v1/tags",
                    json={"value": "singles", "tag_type_id": tag_type_id}
                )
                assert tag_response.status_code == 201
                tag_id = tag_response.json()["id"]

                # Act: permanently delete
                delete_response = await client.delete(f"/api/v1/tags/{tag_id}")

            # Assert: 204 and fully removed
            assert delete_response.status_code == 204

            from app.repositories.tag_repository import TagRepository
            repo = TagRepository(db_session)
            result = await repo.get_by_id(tag_id, include_deactivated=True)
            assert result is None

        finally:
            app.dependency_overrides.clear()
