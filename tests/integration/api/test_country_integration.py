"""
Integration tests for Country API endpoints with real PostgreSQL database.

Uses Testcontainers to verify the full stack (API -> Service -> Repository -> Database).
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import get_db

pytestmark = pytest.mark.integration


class TestCountryDeleteIntegration:
    """Integration tests for Country hard delete and deactivate endpoints."""

    @pytest.mark.asyncio
    async def test_delete_country_permanently_removes_from_database(self, db_session):
        """
        Scenario: Permanently delete a country with no relationships

        Given a country "Germany" with code "DEU" exists
        When I DELETE /countries/{id}
        Then the response status should be 204
        And the country should not exist in the database even with include_deactivated=True
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                # Arrange: create country
                create_response = await client.post(
                    "/api/v1/countries",
                    json={"name": "Germany", "code": "DEU"}
                )
                assert create_response.status_code == 201
                country_id = create_response.json()["id"]

                # Act: permanently delete
                delete_response = await client.delete(f"/api/v1/countries/{country_id}")

            # Assert: 204 and fully removed from database
            assert delete_response.status_code == 204

            from app.repositories.country_repository import CountryRepository
            repo = CountryRepository(db_session)
            result = await repo.get_by_id(country_id, include_deactivated=True)
            assert result is None

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_deactivate_country_sets_flag_but_keeps_record(self, db_session):
        """
        Scenario: Deactivate a country (soft delete)

        Given a country "France" with code "FRA" exists
        When I PATCH /countries/{id}/deactivate
        Then the response status should be 200
        And the country should not appear in the active list
        But the country should still exist in the database with is_deactivated=True
        """
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                # Arrange: create country
                create_response = await client.post(
                    "/api/v1/countries",
                    json={"name": "France", "code": "FRA"}
                )
                assert create_response.status_code == 201
                country_id = create_response.json()["id"]

                # Act: deactivate
                deactivate_response = await client.patch(
                    f"/api/v1/countries/{country_id}/deactivate"
                )
                assert deactivate_response.status_code == 200

                # Assert: not in active list
                list_response = await client.get("/api/v1/countries")
                names = [c["code"] for c in list_response.json()]
                assert "FRA" not in names

            # But: still exists with flag set
            from app.repositories.country_repository import CountryRepository
            repo = CountryRepository(db_session)
            country = await repo.get_by_id(country_id, include_deactivated=True)
            assert country is not None
            assert country.is_deactivated is True

        finally:
            app.dependency_overrides.clear()
