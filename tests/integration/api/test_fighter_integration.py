"""
Integration tests for Fighter API endpoints with real PostgreSQL database.

Uses Testcontainers to verify the full stack (API -> Service -> Repository -> Database).
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import get_db

pytestmark = pytest.mark.integration


class TestFighterDeleteIntegration:
    """Integration tests for Fighter hard delete and deactivate endpoints."""

    @pytest.mark.asyncio
    async def test_delete_fighter_permanently_removes_from_database(self, db_session):
        """
        Scenario: Permanently delete a fighter

        Given a country "Germany", a team "German Knights", and fighter "Hans Mueller" exist
        When I DELETE /fighters/{id}
        Then the response status should be 204
        And the fighter should not exist in the database even with include_deactivated=True
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                # Arrange: create country, team, fighter
                country_resp = await client.post(
                    "/api/v1/countries",
                    json={"name": "Germany", "code": "DEU"}
                )
                assert country_resp.status_code == 201
                country_id = country_resp.json()["id"]

                team_resp = await client.post(
                    "/api/v1/teams",
                    json={"name": "German Knights", "country_id": country_id}
                )
                assert team_resp.status_code == 201
                team_id = team_resp.json()["id"]

                fighter_resp = await client.post(
                    "/api/v1/fighters",
                    json={"name": "Hans Mueller", "team_id": team_id}
                )
                assert fighter_resp.status_code == 201
                fighter_id = fighter_resp.json()["id"]

                # Act: permanently delete
                delete_response = await client.delete(f"/api/v1/fighters/{fighter_id}")

            # Assert: 204 and fully removed
            assert delete_response.status_code == 204

            from app.repositories.fighter_repository import FighterRepository
            repo = FighterRepository(db_session)
            result = await repo.get_by_id(fighter_id, include_deactivated=True)
            assert result is None

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_deactivate_fighter_sets_flag_but_keeps_record(self, db_session):
        """
        Scenario: Deactivate a fighter (soft delete)

        Given a fighter "Klaus Weber" exists
        When I PATCH /fighters/{id}/deactivate
        Then the response status should be 200
        And the fighter should not appear in the active list
        But the fighter should still exist in the database with is_deactivated=True
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
                country_resp = await client.post(
                    "/api/v1/countries",
                    json={"name": "Germany", "code": "DEU"}
                )
                country_id = country_resp.json()["id"]

                team_resp = await client.post(
                    "/api/v1/teams",
                    json={"name": "German Knights", "country_id": country_id}
                )
                team_id = team_resp.json()["id"]

                fighter_resp = await client.post(
                    "/api/v1/fighters",
                    json={"name": "Klaus Weber", "team_id": team_id}
                )
                assert fighter_resp.status_code == 201
                fighter_id = fighter_resp.json()["id"]

                # Act: deactivate
                deactivate_response = await client.patch(
                    f"/api/v1/fighters/{fighter_id}/deactivate"
                )
                assert deactivate_response.status_code == 200

                # Assert: not in active list
                list_response = await client.get("/api/v1/fighters")
                names = [f["name"] for f in list_response.json()]
                assert "Klaus Weber" not in names

            # But: still exists with flag set
            from app.repositories.fighter_repository import FighterRepository
            repo = FighterRepository(db_session)
            fighter = await repo.get_by_id(fighter_id, include_deactivated=True)
            assert fighter is not None
            assert fighter.is_deactivated is True

        finally:
            app.dependency_overrides.clear()
