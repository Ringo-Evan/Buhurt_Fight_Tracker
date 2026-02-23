"""
Integration tests for Team API endpoints with real PostgreSQL database.

Uses Testcontainers to verify the full stack (API -> Service -> Repository -> Database).
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import get_db

pytestmark = pytest.mark.integration


class TestTeamDeleteIntegration:
    """Integration tests for Team hard delete and deactivate endpoints."""

    @pytest.mark.asyncio
    async def test_delete_team_permanently_removes_from_database(self, db_session):
        """
        Scenario: Permanently delete a team

        Given a country "Germany" exists
        And a team "German Knights" belongs to that country
        When I DELETE /teams/{id}
        Then the response status should be 204
        And the team should not exist in the database even with include_deactivated=True
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                # Arrange: create country and team
                country_response = await client.post(
                    "/api/v1/countries",
                    json={"name": "Germany", "code": "DEU"}
                )
                assert country_response.status_code == 201
                country_id = country_response.json()["id"]

                team_response = await client.post(
                    "/api/v1/teams",
                    json={"name": "German Knights", "country_id": country_id}
                )
                assert team_response.status_code == 201
                team_id = team_response.json()["id"]

                # Act: permanently delete
                delete_response = await client.delete(f"/api/v1/teams/{team_id}")

            # Assert: 204 and fully removed from database
            assert delete_response.status_code == 204

            from app.repositories.team_repository import TeamRepository
            repo = TeamRepository(db_session)
            result = await repo.get_by_id(team_id, include_deactivated=True)
            assert result is None

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_deactivate_team_sets_flag_but_keeps_record(self, db_session):
        """
        Scenario: Deactivate a team (soft delete)

        Given a country "France" and team "French Wolves" exist
        When I PATCH /teams/{id}/deactivate
        Then the response status should be 200
        And the team should not appear in the active list
        But the team should still exist in the database with is_deactivated=True
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                # Arrange
                country_response = await client.post(
                    "/api/v1/countries",
                    json={"name": "France", "code": "FRA"}
                )
                assert country_response.status_code == 201
                country_id = country_response.json()["id"]

                team_response = await client.post(
                    "/api/v1/teams",
                    json={"name": "French Wolves", "country_id": country_id}
                )
                assert team_response.status_code == 201
                team_id = team_response.json()["id"]

                # Act: deactivate
                deactivate_response = await client.patch(f"/api/v1/teams/{team_id}/deactivate")
                assert deactivate_response.status_code == 200

                # Assert: not in active list
                list_response = await client.get("/api/v1/teams")
                names = [t["name"] for t in list_response.json()]
                assert "French Wolves" not in names

            # But: still exists with flag set
            from app.repositories.team_repository import TeamRepository
            repo = TeamRepository(db_session)
            team = await repo.get_by_id(team_id, include_deactivated=True)
            assert team is not None
            assert team.is_deactivated is True

        finally:
            app.dependency_overrides.clear()
