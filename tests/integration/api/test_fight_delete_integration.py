"""
Integration tests for Fight hard delete and deactivate endpoints.

Uses Testcontainers to verify the full stack (API -> Service -> Repository -> Database).
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import get_db

pytestmark = pytest.mark.integration


class TestFightDeleteIntegration:
    """Integration tests for Fight permanent delete and deactivate endpoints."""

    async def _create_fight(self, db_session, client):
        """Helper: create prerequisite data and a singles fight. Returns fight_id."""
        from app.repositories.country_repository import CountryRepository
        from app.repositories.team_repository import TeamRepository
        from app.repositories.fighter_repository import FighterRepository

        country_repo = CountryRepository(db_session)
        team_repo = TeamRepository(db_session)
        fighter_repo = FighterRepository(db_session)

        country = await country_repo.create({"code": "DEU", "name": "Germany"})
        team = await team_repo.create({"name": "German Knights", "country_id": country.id})
        fighter1 = await fighter_repo.create({"name": "Hans Mueller", "team_id": team.id})
        fighter2 = await fighter_repo.create({"name": "Klaus Weber", "team_id": team.id})
        await db_session.commit()

        fight_data = {
            "date": "2025-01-15",
            "location": "Berlin Arena",
            "supercategory": "singles",
            "participations": [
                {"fighter_id": str(fighter1.id), "side": 1, "role": "fighter"},
                {"fighter_id": str(fighter2.id), "side": 2, "role": "fighter"},
            ],
        }
        response = await client.post("/api/v1/fights", json=fight_data)
        assert response.status_code == 201
        return response.json()["id"]

    @pytest.mark.asyncio
    async def test_delete_fight_permanently_removes_from_database(self, db_session):
        """
        Scenario: Permanently delete a fight

        Given a fight exists
        When I DELETE /fights/{id}
        Then the response status should be 204
        And the fight should not exist in the database even with include_deactivated=True
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                fight_id = await self._create_fight(db_session, client)

                # Act: permanently delete
                delete_response = await client.delete(f"/api/v1/fights/{fight_id}")

            # Assert: 204 and fully removed
            assert delete_response.status_code == 204

            from app.repositories.fight_repository import FightRepository
            repo = FightRepository(db_session)
            result = await repo.get_by_id(fight_id, include_deactivated=True)
            assert result is None

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_deactivate_fight_sets_flag_but_keeps_record(self, db_session):
        """
        Scenario: Deactivate a fight (soft delete)

        Given a fight exists
        When I PATCH /fights/{id}/deactivate
        Then the response status should be 200
        And the fight should not appear in the active list
        But the fight should still exist in the database with is_deactivated=True
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                fight_id = await self._create_fight(db_session, client)

                # Act: deactivate
                deactivate_response = await client.patch(
                    f"/api/v1/fights/{fight_id}/deactivate"
                )
                assert deactivate_response.status_code == 200

                # Assert: not in active list
                list_response = await client.get("/api/v1/fights")
                ids = [f["id"] for f in list_response.json()]
                assert fight_id not in ids

            # But: still exists with flag set
            from app.repositories.fight_repository import FightRepository
            repo = FightRepository(db_session)
            fight = await repo.get_by_id(fight_id, include_deactivated=True)
            assert fight is not None
            assert fight.is_deactivated is True

        finally:
            app.dependency_overrides.clear()
