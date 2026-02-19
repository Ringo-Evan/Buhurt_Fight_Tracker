"""
Integration tests for Fight Tag Management endpoints.

Follows fight_tag_management.feature BDD scenarios.
Uses Testcontainers with a real PostgreSQL database.

Requirements:
- Docker Desktop must be running
- testcontainers package installed
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import get_db

pytestmark = pytest.mark.integration


class TestFightTagIntegration:
    """Integration tests for fight-scoped tag management."""

    async def _create_fight(self, db_session, client, supercategory="singles"):
        """Helper: create prerequisite data and a fight. Returns fight_id."""
        from app.repositories.country_repository import CountryRepository
        from app.repositories.team_repository import TeamRepository
        from app.repositories.fighter_repository import FighterRepository

        country_repo = CountryRepository(db_session)
        team_repo = TeamRepository(db_session)
        fighter_repo = FighterRepository(db_session)

        country = await country_repo.create({"code": "AUT", "name": "Austria"})
        team = await team_repo.create({"name": "Austrian Knights", "country_id": country.id})
        fighter1 = await fighter_repo.create({"name": "Hans Fischer", "team_id": team.id})
        fighter2 = await fighter_repo.create({"name": "Ernst Wagner", "team_id": team.id})
        await db_session.commit()

        fight_data = {
            "date": "2025-03-10",
            "location": "Vienna Stadium",
            "supercategory": supercategory,
            "participations": [
                {"fighter_id": str(fighter1.id), "side": 1, "role": "fighter"},
                {"fighter_id": str(fighter2.id), "side": 2, "role": "fighter"},
            ],
        }
        response = await client.post("/api/v1/fights", json=fight_data)
        assert response.status_code == 201, response.text
        return response.json()["id"]

    # -------------------------------------------------------------------------
    # Scenario 1: Creating a fight links supercategory tag to the fight
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_fight_response_includes_supercategory_tag(self, db_session):
        """
        Scenario: Creating a fight links supercategory tag to the fight

        Given a valid fight is created with supercategory "singles"
        When I retrieve the fight
        Then the fight has an active supercategory tag with value "singles"
        And the tag has the correct fight_id
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                fight_id = await self._create_fight(db_session, client, supercategory="singles")

                # Act: retrieve the fight
                response = await client.get(f"/api/v1/fights/{fight_id}")

            assert response.status_code == 200
            data = response.json()

            # Assert: tags array is present
            assert "tags" in data, "FightResponse must include a 'tags' field"
            tags = data["tags"]
            assert len(tags) >= 1, "Fight should have at least one tag (the supercategory)"

            # Assert: supercategory tag exists with correct value
            supercategory_tags = [t for t in tags if not t.get("is_deactivated", True)]
            assert len(supercategory_tags) >= 1, "At least one active tag expected"

            # Find the supercategory tag by value
            sc_tag = next((t for t in supercategory_tags if t.get("value") == "singles"), None)
            assert sc_tag is not None, "Supercategory tag with value 'singles' not found in tags"

            # Assert: tag is linked to this fight
            assert sc_tag["fight_id"] == fight_id, (
                f"Tag fight_id '{sc_tag['fight_id']}' should equal fight_id '{fight_id}'"
            )

        finally:
            app.dependency_overrides.clear()
