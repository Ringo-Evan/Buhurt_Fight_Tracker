"""
Integration tests for Fight endpoints with real PostgreSQL database.

Uses Testcontainers to spin up a real PostgreSQL instance for testing the
Fight API endpoints. These tests verify that the entire stack (API -> Service -> Repository -> Database)
works correctly together.

Following the fight_management.feature scenarios as specification.

Requirements:
- Docker Desktop must be running
- testcontainers package installed
"""

import pytest
from datetime import date
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestFightIntegration:
    """Integration tests for Fight API endpoints with real database."""

    @pytest.mark.asyncio
    async def test_create_singles_fight_with_two_participants(self, db_session):
        """
        Scenario: Create a singles duel fight with two participants

        Given an active country exists with code "USA" and name "United States"
        And a team "Team USA" exists for country "USA"
        And a fighter "John Smith" exists for team "Team USA"
        And a fighter "Jane Doe" exists for team "Team USA"
        When I create a fight on "2025-06-15" at "Battle Arena Denver"
        And I add fighter "John Smith" to side 1 as "fighter"
        And I add fighter "Jane Doe" to side 2 as "fighter"
        Then the fight is created successfully
        And the fight date is "2025-06-15"
        And the fight location is "Battle Arena Denver"
        And the fight has 2 participants
        And participant "John Smith" is on side 1 with role "fighter"
        And participant "Jane Doe" is on side 2 with role "fighter"

        Verifies:
        - POST /fights with participants creates fight atomically
        - Response contains correct fight data
        - Participations are created and linked
        """
        # Arrange: Override the database dependency
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        # Create prerequisite entities (Country, Team, Fighters)
        from app.repositories.country_repository import CountryRepository
        from app.repositories.team_repository import TeamRepository
        from app.repositories.fighter_repository import FighterRepository

        country_repo = CountryRepository(db_session)
        team_repo = TeamRepository(db_session)
        fighter_repo = FighterRepository(db_session)

        # Create country
        country = await country_repo.create({
            'code': 'USA',
            'name': 'United States'
        })

        # Create team
        team = await team_repo.create({
            'name': 'Team USA',
            'country_id': country.id
        })

        # Create fighters
        fighter1 = await fighter_repo.create({
            'name': 'John Smith',
            'team_id': team.id
        })
        fighter2 = await fighter_repo.create({
            'name': 'Jane Doe',
            'team_id': team.id
        })
        await db_session.commit()

        # Fight data with participants
        fight_data = {
            'date': '2025-06-15',
            'location': 'Battle Arena Denver',
            'participations': [
                {
                    'fighter_id': str(fighter1.id),
                    'side': 1,
                    'role': 'fighter'
                },
                {
                    'fighter_id': str(fighter2.id),
                    'side': 2,
                    'role': 'fighter'
                }
            ]
        }

        try:
            # Act: Create fight with participants
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/fights", json=fight_data)

            # Assert: Verify response
            assert response.status_code == 201
            response_data = response.json()

            assert response_data['date'] == '2025-06-15'
            assert response_data['location'] == 'Battle Arena Denver'
            assert 'id' in response_data
            assert 'participations' in response_data
            assert len(response_data['participations']) == 2

            # Verify participants
            participants = response_data['participations']
            fighter_ids = [p['fighter_id'] for p in participants]
            assert str(fighter1.id) in fighter_ids
            assert str(fighter2.id) in fighter_ids

            # Verify side assignments
            side_1_participants = [p for p in participants if p['side'] == 1]
            side_2_participants = [p for p in participants if p['side'] == 2]
            assert len(side_1_participants) == 1
            assert len(side_2_participants) == 1

        finally:
            app.dependency_overrides.clear()
