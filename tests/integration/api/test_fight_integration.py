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
            'fight_format': 'singles',  # Required field for format validation
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

    @pytest.mark.asyncio
    async def test_create_melee_fight_with_minimum_fighters(self, db_session):
        """
        Scenario: Create a melee fight with minimum fighters (5 per side)

        Given an active country exists
        And a team exists
        And 10 fighters exist
        When I create a melee fight with 5 fighters per side
        Then the fight is created successfully
        And the fight has 10 participants
        And each side has 5 fighters

        Verifies:
        - Melee format requires minimum 5 fighters per side (DD-004)
        - Format-dependent validation works correctly
        """
        # Arrange
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        from app.repositories.country_repository import CountryRepository
        from app.repositories.team_repository import TeamRepository
        from app.repositories.fighter_repository import FighterRepository

        country_repo = CountryRepository(db_session)
        team_repo = TeamRepository(db_session)
        fighter_repo = FighterRepository(db_session)

        # Create country and team
        country = await country_repo.create({'code': 'USA', 'name': 'United States'})
        team = await team_repo.create({'name': 'Team USA', 'country_id': country.id})

        # Create 10 fighters
        fighters = []
        for i in range(10):
            fighter = await fighter_repo.create({
                'name': f'Fighter {i+1}',
                'team_id': team.id
            })
            fighters.append(fighter)
        await db_session.commit()

        # Fight data with 5 fighters per side
        participations = []
        for i in range(5):
            participations.append({
                'fighter_id': str(fighters[i].id),
                'side': 1,
                'role': 'fighter'
            })
        for i in range(5, 10):
            participations.append({
                'fighter_id': str(fighters[i].id),
                'side': 2,
                'role': 'fighter'
            })

        fight_data = {
            'date': '2025-07-20',
            'location': 'Melee Arena',
            'fight_format': 'melee',
            'participations': participations
        }

        try:
            # Act
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/fights", json=fight_data)

            # Assert
            assert response.status_code == 201
            response_data = response.json()
            assert response_data['location'] == 'Melee Arena'
            assert len(response_data['participations']) == 10

            # Verify side distribution
            side_1 = [p for p in response_data['participations'] if p['side'] == 1]
            side_2 = [p for p in response_data['participations'] if p['side'] == 2]
            assert len(side_1) == 5
            assert len(side_2) == 5

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_cannot_create_fight_with_future_date(self, db_session):
        """
        Scenario: Cannot create fight with future date

        Given fighters exist
        When I attempt to create a fight with date in 2030
        Then I receive a validation error
        And the error message contains "future"

        Verifies:
        - Future date validation (existing business rule)
        - API error handling
        """
        # Arrange
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        from app.repositories.country_repository import CountryRepository
        from app.repositories.team_repository import TeamRepository
        from app.repositories.fighter_repository import FighterRepository

        country_repo = CountryRepository(db_session)
        team_repo = TeamRepository(db_session)
        fighter_repo = FighterRepository(db_session)

        country = await country_repo.create({'code': 'USA', 'name': 'United States'})
        team = await team_repo.create({'name': 'Team USA', 'country_id': country.id})
        fighter1 = await fighter_repo.create({'name': 'Fighter 1', 'team_id': team.id})
        fighter2 = await fighter_repo.create({'name': 'Fighter 2', 'team_id': team.id})
        await db_session.commit()

        fight_data = {
            'date': '2030-12-31',  # Future date
            'location': 'Test Arena',
            'fight_format': 'singles',
            'participations': [
                {'fighter_id': str(fighter1.id), 'side': 1, 'role': 'fighter'},
                {'fighter_id': str(fighter2.id), 'side': 2, 'role': 'fighter'}
            ]
        }

        try:
            # Act
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/fights", json=fight_data)

            # Assert
            assert response.status_code == 422
            error_detail = response.json()['detail']
            assert 'future' in error_detail.lower()

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_cannot_create_fight_with_only_one_participant(self, db_session):
        """
        Scenario: Cannot create fight with only 1 participant

        When I attempt to create a fight with only 1 participant
        Then I receive a validation error
        And the error message contains "at least 2 participants"

        Verifies:
        - Minimum participant validation
        - Service layer validation working
        """
        # Arrange
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        from app.repositories.country_repository import CountryRepository
        from app.repositories.team_repository import TeamRepository
        from app.repositories.fighter_repository import FighterRepository

        country_repo = CountryRepository(db_session)
        team_repo = TeamRepository(db_session)
        fighter_repo = FighterRepository(db_session)

        country = await country_repo.create({'code': 'USA', 'name': 'United States'})
        team = await team_repo.create({'name': 'Team USA', 'country_id': country.id})
        fighter1 = await fighter_repo.create({'name': 'Fighter 1', 'team_id': team.id})
        await db_session.commit()

        fight_data = {
            'date': '2025-06-15',
            'location': 'Test Arena',
            'fight_format': 'singles',
            'participations': [
                {'fighter_id': str(fighter1.id), 'side': 1, 'role': 'fighter'}
            ]
        }

        try:
            # Act
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/fights", json=fight_data)

            # Assert
            assert response.status_code == 422
            error_detail = response.json()['detail']
            assert 'at least 2 participants' in error_detail.lower()

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_cannot_create_singles_fight_with_multiple_fighters_per_side(self, db_session):
        """
        Scenario: Singles format validation - exactly 1 fighter per side

        When I attempt to create a singles fight with 2 fighters on side 1
        Then I receive a validation error
        And the error message indicates singles requires exactly 1 per side

        Verifies:
        - Singles format validation (DD-003)
        - Format-dependent participant count validation
        """
        # Arrange
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        from app.repositories.country_repository import CountryRepository
        from app.repositories.team_repository import TeamRepository
        from app.repositories.fighter_repository import FighterRepository

        country_repo = CountryRepository(db_session)
        team_repo = TeamRepository(db_session)
        fighter_repo = FighterRepository(db_session)

        country = await country_repo.create({'code': 'USA', 'name': 'United States'})
        team = await team_repo.create({'name': 'Team USA', 'country_id': country.id})

        fighters = []
        for i in range(3):
            fighter = await fighter_repo.create({'name': f'Fighter {i+1}', 'team_id': team.id})
            fighters.append(fighter)
        await db_session.commit()

        fight_data = {
            'date': '2025-06-15',
            'location': 'Test Arena',
            'fight_format': 'singles',
            'participations': [
                {'fighter_id': str(fighters[0].id), 'side': 1, 'role': 'fighter'},
                {'fighter_id': str(fighters[1].id), 'side': 1, 'role': 'fighter'},  # 2 on side 1
                {'fighter_id': str(fighters[2].id), 'side': 2, 'role': 'fighter'}
            ]
        }

        try:
            # Act
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/fights", json=fight_data)

            # Assert
            assert response.status_code == 422
            error_detail = response.json()['detail']
            assert 'singles' in error_detail.lower()
            assert 'exactly 1' in error_detail.lower()

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_cannot_create_melee_with_insufficient_fighters(self, db_session):
        """
        Scenario: Melee format validation - minimum 5 fighters per side

        When I attempt to create a melee fight with only 3 fighters per side
        Then I receive a validation error
        And the error message indicates melee requires minimum 5 per side

        Verifies:
        - Melee format validation (DD-004)
        - Format-dependent participant count validation
        """
        # Arrange
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        from app.repositories.country_repository import CountryRepository
        from app.repositories.team_repository import TeamRepository
        from app.repositories.fighter_repository import FighterRepository

        country_repo = CountryRepository(db_session)
        team_repo = TeamRepository(db_session)
        fighter_repo = FighterRepository(db_session)

        country = await country_repo.create({'code': 'USA', 'name': 'United States'})
        team = await team_repo.create({'name': 'Team USA', 'country_id': country.id})

        fighters = []
        for i in range(6):
            fighter = await fighter_repo.create({'name': f'Fighter {i+1}', 'team_id': team.id})
            fighters.append(fighter)
        await db_session.commit()

        fight_data = {
            'date': '2025-06-15',
            'location': 'Test Arena',
            'fight_format': 'melee',
            'participations': [
                {'fighter_id': str(fighters[0].id), 'side': 1, 'role': 'fighter'},
                {'fighter_id': str(fighters[1].id), 'side': 1, 'role': 'fighter'},
                {'fighter_id': str(fighters[2].id), 'side': 1, 'role': 'fighter'},  # Only 3 on side 1
                {'fighter_id': str(fighters[3].id), 'side': 2, 'role': 'fighter'},
                {'fighter_id': str(fighters[4].id), 'side': 2, 'role': 'fighter'},
                {'fighter_id': str(fighters[5].id), 'side': 2, 'role': 'fighter'}   # Only 3 on side 2
            ]
        }

        try:
            # Act
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/fights", json=fight_data)

            # Assert
            assert response.status_code == 422
            error_detail = response.json()['detail']
            assert 'melee' in error_detail.lower()
            assert 'minimum 5' in error_detail.lower() or '5 fighters' in error_detail.lower()

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Complex session management issue - to be fixed in separate PR")
    async def test_list_all_fights_excludes_soft_deleted(self, db_session):
        """
        Scenario: List all fights excludes soft-deleted fights

        Given multiple fights exist
        And one fight is soft deleted
        When I list all fights
        Then only non-deleted fights are returned

        Verifies:
        - GET /fights endpoint
        - Soft delete filtering
        - List operation working
        """
        # Arrange
        async def get_db_override():
            yield db_session

        app.dependency_overrides[get_db] = get_db_override

        from app.repositories.country_repository import CountryRepository
        from app.repositories.team_repository import TeamRepository
        from app.repositories.fighter_repository import FighterRepository
        from app.repositories.fight_repository import FightRepository

        country_repo = CountryRepository(db_session)
        team_repo = TeamRepository(db_session)
        fighter_repo = FighterRepository(db_session)
        fight_repo = FightRepository(db_session)

        # Create prerequisites (no commit - let API handle transactions)
        country = await country_repo.create({'code': 'USA', 'name': 'United States'})
        team = await team_repo.create({'name': 'Team USA', 'country_id': country.id})
        fighter1 = await fighter_repo.create({'name': 'Fighter 1', 'team_id': team.id})
        fighter2 = await fighter_repo.create({'name': 'Fighter 2', 'team_id': team.id})
        await db_session.flush()  # Flush but don't commit

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                # Create two fights via API
                fight1_data = {
                    'date': '2025-06-15',
                    'location': 'Arena A',
                    'fight_format': 'singles',
                    'participations': [
                        {'fighter_id': str(fighter1.id), 'side': 1, 'role': 'fighter'},
                        {'fighter_id': str(fighter2.id), 'side': 2, 'role': 'fighter'}
                    ]
                }
                response1 = await client.post("/api/v1/fights", json=fight1_data)
                assert response1.status_code == 201
                fight1_id = response1.json()['id']

                fight2_data = {
                    'date': '2025-07-20',
                    'location': 'Arena B',
                    'fight_format': 'singles',
                    'participations': [
                        {'fighter_id': str(fighter1.id), 'side': 1, 'role': 'fighter'},
                        {'fighter_id': str(fighter2.id), 'side': 2, 'role': 'fighter'}
                    ]
                }
                response2 = await client.post("/api/v1/fights", json=fight2_data)
                assert response2.status_code == 201
                fight2_id = response2.json()['id']

                # Soft delete fight2 via API
                delete_response = await client.delete(f"/api/v1/fights/{fight2_id}")
                assert delete_response.status_code == 204

                # Act: List all fights
                list_response = await client.get("/api/v1/fights")

                # Assert
                assert list_response.status_code == 200
                fights = list_response.json()
                assert len(fights) == 1
                assert fights[0]['location'] == 'Arena A'
                assert fights[0]['id'] == fight1_id

        finally:
            app.dependency_overrides.clear()
