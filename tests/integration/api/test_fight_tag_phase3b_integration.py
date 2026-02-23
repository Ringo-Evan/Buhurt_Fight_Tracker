"""
Integration tests for Phase 3B Tag Expansion (weapon, league, ruleset).

Follows fight_tag_phase3b.feature BDD scenarios.
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


class TestWeaponTagIntegration:
    """Integration tests for weapon tag management (Phase 3B)."""

    async def _create_fight_with_category(self, db_session, client, supercategory="singles", category="duel"):
        """Helper: create a fight with supercategory and category. Returns (fight_id, category_tag_id)."""
        from app.repositories.country_repository import CountryRepository
        from app.repositories.team_repository import TeamRepository
        from app.repositories.fighter_repository import FighterRepository

        country_repo = CountryRepository(db_session)
        team_repo = TeamRepository(db_session)
        fighter_repo = FighterRepository(db_session)

        country = await country_repo.create({"code": "GER", "name": "Germany"})
        team = await team_repo.create({"name": "German Knights", "country_id": country.id})

        if supercategory == "singles":
            # Singles: need exactly 1 fighter per side
            fighter1 = await fighter_repo.create({"name": "Hans Mueller", "team_id": team.id})
            fighter2 = await fighter_repo.create({"name": "Karl Schmidt", "team_id": team.id})
            participations = [
                {"fighter_id": str(fighter1.id), "side": 1, "role": "fighter"},
                {"fighter_id": str(fighter2.id), "side": 2, "role": "fighter"},
            ]
        else:
            # Melee: need at least 5 per side
            fighters = []
            for i in range(10):
                f = await fighter_repo.create({"name": f"Fighter {i+1}", "team_id": team.id})
                fighters.append(f)
            participations = [
                {"fighter_id": str(fighters[i].id), "side": 1 if i < 5 else 2, "role": "fighter"}
                for i in range(10)
            ]

        await db_session.commit()

        fight_data = {
            "date": "2025-04-15",
            "location": "Berlin Arena",
            "supercategory": supercategory,
            "participations": participations,
        }
        response = await client.post("/api/v1/fights", json=fight_data)
        assert response.status_code == 201, response.text
        fight_id = response.json()["id"]

        # Add category tag
        category_data = {
            "tag_type_name": "category",
            "value": category,
        }
        response = await client.post(f"/api/v1/fights/{fight_id}/tags", json=category_data)
        assert response.status_code == 201, response.text
        category_tag_id = response.json()["id"]

        return fight_id, category_tag_id

    # -------------------------------------------------------------------------
    # Scenario: Add weapon tag to a duel fight (happy path)
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_add_weapon_tag_to_duel_fight(self, db_session):
        """
        Scenario: Add weapon tag to a duel fight

        Given a singles fight with category "duel"
        When I add a weapon tag "Longsword"
        Then the fight has an active weapon tag with value "Longsword"
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                # Arrange: create fight with category="duel"
                fight_id, _ = await self._create_fight_with_category(
                    db_session, client, supercategory="singles", category="duel"
                )

                # Act: add weapon tag
                weapon_data = {
                    "tag_type_name": "weapon",
                    "value": "Longsword",
                }
                response = await client.post(f"/api/v1/fights/{fight_id}/tags", json=weapon_data)

                # Assert: weapon tag created
                assert response.status_code == 201
                weapon_tag = response.json()
                assert weapon_tag["tag_type_name"] == "weapon"
                assert weapon_tag["value"] == "Longsword"
                assert weapon_tag["fight_id"] == fight_id

                # Verify: get fight shows weapon tag
                response = await client.get(f"/api/v1/fights/{fight_id}")
                assert response.status_code == 200
                fight = response.json()
                weapon_tags = [t for t in fight["tags"] if t["tag_type_name"] == "weapon"]
                assert len(weapon_tags) == 1
                assert weapon_tags[0]["value"] == "Longsword"

        finally:
            app.dependency_overrides.clear()
