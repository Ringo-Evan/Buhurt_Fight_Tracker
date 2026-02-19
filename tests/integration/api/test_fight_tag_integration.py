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

    @pytest.mark.asyncio
    async def test_add_melee_category_to_singles_fight_returns_422(self, db_session):
        """
        Scenario: Cannot add a melee category to a singles fight
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
                response = await client.post(
                    f"/api/v1/fights/{fight_id}/tags",
                    json={"tag_type_name": "category", "value": "5s"}
                )

            assert response.status_code == 422, response.text

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_add_two_category_tags_returns_422(self, db_session):
        """
        Scenario: Cannot add two active category tags to the same fight
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
                # Add first category tag
                r1 = await client.post(
                    f"/api/v1/fights/{fight_id}/tags",
                    json={"tag_type_name": "category", "value": "duel"}
                )
                assert r1.status_code == 201, r1.text

                # Attempt to add a second
                r2 = await client.post(
                    f"/api/v1/fights/{fight_id}/tags",
                    json={"tag_type_name": "category", "value": "profight"}
                )

            assert r2.status_code == 422, r2.text

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_add_valid_gender_tag(self, db_session):
        """
        Scenario: Add a gender tag to a fight
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
                response = await client.post(
                    f"/api/v1/fights/{fight_id}/tags",
                    json={"tag_type_name": "gender", "value": "male"}
                )

            assert response.status_code == 201, response.text
            data = response.json()
            assert data["value"] == "male"
            assert data["fight_id"] == fight_id

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_add_invalid_gender_value_returns_422(self, db_session):
        """
        Scenario: Cannot add an invalid gender value
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
                response = await client.post(
                    f"/api/v1/fights/{fight_id}/tags",
                    json={"tag_type_name": "gender", "value": "unknown"}
                )

            assert response.status_code == 422, response.text

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_add_custom_tag(self, db_session):
        """
        Scenario: Add a custom tag to a fight
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
                response = await client.post(
                    f"/api/v1/fights/{fight_id}/tags",
                    json={"tag_type_name": "custom", "value": "great technique"}
                )

            assert response.status_code == 201, response.text
            data = response.json()
            assert data["value"] == "great technique"

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_fight_can_have_multiple_custom_tags(self, db_session):
        """
        Scenario: Fight can have multiple custom tags
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
                r1 = await client.post(
                    f"/api/v1/fights/{fight_id}/tags",
                    json={"tag_type_name": "custom", "value": "exciting"}
                )
                assert r1.status_code == 201, r1.text

                r2 = await client.post(
                    f"/api/v1/fights/{fight_id}/tags",
                    json={"tag_type_name": "custom", "value": "controversial"}
                )
                assert r2.status_code == 201, r2.text

                # Both custom tags exist
                get_response = await client.get(f"/api/v1/fights/{fight_id}")

            assert get_response.status_code == 200
            tags = get_response.json()["tags"]
            values = [t["value"] for t in tags if not t["is_deactivated"]]
            assert "exciting" in values
            assert "controversial" in values

        finally:
            app.dependency_overrides.clear()

    # -------------------------------------------------------------------------
    # Scenario 7: Deactivate a tag (cascade to children)
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_deactivate_supercategory_cascades_to_category(self, db_session):
        """
        Scenario: Deactivating supercategory tag cascades deactivation to category tag
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

                # Add a category tag (child of supercategory)
                cat_response = await client.post(
                    f"/api/v1/fights/{fight_id}/tags",
                    json={"tag_type_name": "category", "value": "duel"}
                )
                assert cat_response.status_code == 201, cat_response.text

                # Find the supercategory tag id
                fight_data = (await client.get(f"/api/v1/fights/{fight_id}")).json()
                sc_tag = next(
                    t for t in fight_data["tags"]
                    if t["value"] == "singles" and not t["is_deactivated"]
                )
                sc_tag_id = sc_tag["id"]

                # Deactivate the supercategory tag
                deactivate_response = await client.patch(
                    f"/api/v1/fights/{fight_id}/tags/{sc_tag_id}/deactivate"
                )

            assert deactivate_response.status_code == 200, deactivate_response.text

            # Verify category tag is also deactivated
            from app.repositories.tag_repository import TagRepository
            tag_repo = TagRepository(db_session)
            cat_tag_id = cat_response.json()["id"]
            cat_tag = await tag_repo.get_by_id(cat_tag_id, include_deactivated=True)
            assert cat_tag is not None
            assert cat_tag.is_deactivated is True

        finally:
            app.dependency_overrides.clear()

    # -------------------------------------------------------------------------
    # Scenario 8: Cross-fight access guard
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_cannot_deactivate_tag_via_different_fight(self, db_session):
        """
        Scenario: Cannot manage a tag via a different fight's endpoint
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                # Create fight A with a gender tag
                fight_a_id = await self._create_fight(db_session, client, supercategory="singles")
                tag_response = await client.post(
                    f"/api/v1/fights/{fight_a_id}/tags",
                    json={"tag_type_name": "gender", "value": "male"}
                )
                tag_id = tag_response.json()["id"]

                # Create fight B (different fight)
                from app.repositories.country_repository import CountryRepository
                from app.repositories.team_repository import TeamRepository
                from app.repositories.fighter_repository import FighterRepository
                country_repo = CountryRepository(db_session)
                team_repo = TeamRepository(db_session)
                fighter_repo = FighterRepository(db_session)
                country = await country_repo.create({"code": "POL", "name": "Poland"})
                team = await team_repo.create({"name": "Polish Crew", "country_id": country.id})
                f1 = await fighter_repo.create({"name": "Piotr K", "team_id": team.id})
                f2 = await fighter_repo.create({"name": "Marek W", "team_id": team.id})
                await db_session.commit()

                fight_b_data = {
                    "date": "2025-04-20",
                    "location": "Warsaw Arena",
                    "supercategory": "singles",
                    "participations": [
                        {"fighter_id": str(f1.id), "side": 1, "role": "fighter"},
                        {"fighter_id": str(f2.id), "side": 2, "role": "fighter"},
                    ]
                }
                fight_b_resp = await client.post("/api/v1/fights", json=fight_b_data)
                fight_b_id = fight_b_resp.json()["id"]

                # Try to deactivate fight A's tag via fight B's endpoint
                response = await client.patch(
                    f"/api/v1/fights/{fight_b_id}/tags/{tag_id}/deactivate"
                )

            assert response.status_code == 404, response.text

        finally:
            app.dependency_overrides.clear()
    # -------------------------------------------------------------------------
    # Scenario 2: Add valid category tag to a singles fight
    # Scenario 3: Category-supercategory validation
    # Scenario 4: One-per-type rule
    # Scenario 5: Gender tag
    # Scenario 6: Custom tag (multiple allowed)
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_add_valid_category_tag_to_singles_fight(self, db_session):
        """
        Scenario: Add a valid category tag to a singles fight

        Given a singles fight exists
        When I add a category tag "duel" to the fight
        Then the fight has an active category tag with value "duel"
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

                # Act: add a category tag
                response = await client.post(
                    f"/api/v1/fights/{fight_id}/tags",
                    json={"tag_type_name": "category", "value": "duel"}
                )

            assert response.status_code == 201, response.text
            data = response.json()
            assert data["value"] == "duel"
            assert data["fight_id"] == fight_id
            assert data["is_deactivated"] is False

        finally:
            app.dependency_overrides.clear()

    # -------------------------------------------------------------------------
    # Delete tag (DD-012: reject if children exist)
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_hard_delete_tag_with_no_children(self, db_session):
        """
        Scenario: Hard delete a tag that has no children

        Given a singles fight with an active gender tag "male"
        When I hard delete the gender tag
        Then the gender tag no longer exists
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
                tag_resp = await client.post(
                    f"/api/v1/fights/{fight_id}/tags",
                    json={"tag_type_name": "gender", "value": "male"}
                )
                assert tag_resp.status_code == 201, tag_resp.text
                tag_id = tag_resp.json()["id"]

                # Hard delete
                delete_resp = await client.delete(f"/api/v1/fights/{fight_id}/tags/{tag_id}")

            assert delete_resp.status_code == 204, delete_resp.text

            # Verify gone from DB
            from app.repositories.tag_repository import TagRepository
            tag_repo = TagRepository(db_session)
            result = await tag_repo.get_by_id(tag_id, include_deactivated=True)
            assert result is None

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_hard_delete_tag_with_active_children_returns_422(self, db_session):
        """
        Scenario: Cannot delete a tag that has active children

        Given a singles fight with an active category tag "duel"
        When I hard delete the supercategory tag
        Then I receive a 422 validation error
        And the supercategory tag still exists
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

                # Add a category tag (child of supercategory)
                cat_resp = await client.post(
                    f"/api/v1/fights/{fight_id}/tags",
                    json={"tag_type_name": "category", "value": "duel"}
                )
                assert cat_resp.status_code == 201, cat_resp.text

                # Find supercategory tag
                fight_data = (await client.get(f"/api/v1/fights/{fight_id}")).json()
                sc_tag = next(t for t in fight_data["tags"] if t["value"] == "singles")
                sc_tag_id = sc_tag["id"]

                # Attempt to hard-delete supercategory (which has a child)
                delete_resp = await client.delete(
                    f"/api/v1/fights/{fight_id}/tags/{sc_tag_id}"
                )

            assert delete_resp.status_code == 422, delete_resp.text

            # Supercategory tag still exists
            from app.repositories.tag_repository import TagRepository
            tag_repo = TagRepository(db_session)
            still_there = await tag_repo.get_by_id(sc_tag_id, include_deactivated=True)
            assert still_there is not None

        finally:
            app.dependency_overrides.clear()

    # -------------------------------------------------------------------------
    # Supercategory immutability (DD-011)
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_cannot_update_supercategory_tag(self, db_session):
        """
        Scenario: Cannot update supercategory tag after fight creation

        Given a singles fight exists
        When I update the supercategory tag to "melee"
        Then I receive a 422 validation error
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

                fight_data = (await client.get(f"/api/v1/fights/{fight_id}")).json()
                sc_tag = next(t for t in fight_data["tags"] if t["value"] == "singles")
                sc_tag_id = sc_tag["id"]

                response = await client.patch(
                    f"/api/v1/fights/{fight_id}/tags/{sc_tag_id}",
                    json={"value": "melee"}
                )

            assert response.status_code == 422, response.text

        finally:
            app.dependency_overrides.clear()
