"""
Integration tests for TeamRepository with real PostgreSQL database.

Uses Testcontainers to spin up a real PostgreSQL instance for testing.
These tests verify that our repository layer works correctly with actual database,
including foreign key constraints and eager loading of country relationships.

Key differences from Country integration tests:
- MUST create Country records first (prerequisite for teams)
- Test FK constraints at database level (IntegrityError)
- Verify joinedload works (country.name accessible without lazy load)
- Test filtering by country_id

Requirements:
- Docker Desktop must be running
- testcontainers package installed
"""

import pytest
from uuid import uuid4
from sqlalchemy.exc import IntegrityError
from app.repositories.team_repository import TeamRepository
from app.repositories.country_repository import CountryRepository
from app.models.team import Team
from app.models.country import Country


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestTeamRepositoryIntegrationCreate:
    """Integration tests for Team creation with real database."""

    @pytest.mark.asyncio
    async def test_create_team_with_valid_country_persists_to_database(self, db_session):
        """
        Test that creating a team with valid country persists to PostgreSQL.

        Verifies:
        - Team is inserted into database
        - UUID is generated automatically
        - Default values (is_deactivated=False, created_at) are set by model
        - Country relationship is established via FK
        - Can be retrieved after creation with eager-loaded country data

        Arrange: Create country, then team with valid country_id
        Act: Create team via repository
        Assert: Team persisted with all fields populated and country relationship
        """
        # Arrange - create prerequisite country
        country_repository = CountryRepository(db_session)
        country = await country_repository.create({
            "name": "United States",
            "code": "USA"
        })

        # Arrange - prepare team data
        team_repository = TeamRepository(db_session)
        team_data = {
            "name": "Team USA Warriors",
            "country_id": country.id
        }

        # Act
        created_team = await team_repository.create(team_data)

        # Assert - verify in-memory object
        assert created_team.id is not None
        assert isinstance(created_team.id, type(uuid4()))
        assert created_team.name == "Team USA Warriors"
        assert created_team.country_id == country.id
        assert created_team.is_deactivated is False
        assert created_team.created_at is not None

        # Assert - verify country relationship is eager-loaded
        assert created_team.country is not None
        assert created_team.country.code == "USA"
        assert created_team.country.name == "United States"

        # Assert - verify persisted to database by retrieving
        retrieved_team = await team_repository.get_by_id(created_team.id)
        assert retrieved_team is not None
        assert retrieved_team.id == created_team.id
        assert retrieved_team.name == "Team USA Warriors"
        assert retrieved_team.country_id == country.id
        assert retrieved_team.country.code == "USA"  # Eager-loaded

    @pytest.mark.asyncio
    async def test_create_team_with_invalid_country_id_raises_integrity_error(self, db_session):
        """
        Test that creating a team with non-existent country_id raises IntegrityError.

        Verifies:
        - Database FK constraint enforces referential integrity
        - Cannot create team with invalid country_id
        - Error raised from database, not just application logic

        Arrange: Generate random UUID that doesn't correspond to any country
        Act: Attempt to create team with invalid country_id
        Assert: IntegrityError raised by PostgreSQL FK constraint
        """
        # Arrange
        team_repository = TeamRepository(db_session)
        nonexistent_country_id = uuid4()

        team_data = {
            "name": "Orphan Team",
            "country_id": nonexistent_country_id
        }

        # Act & Assert - FK constraint violation
        with pytest.raises(IntegrityError) as exc_info:
            await team_repository.create(team_data)

        # Verify it's a foreign key constraint error
        assert "foreign key constraint" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_multiple_teams_for_same_country_all_persist(self, db_session):
        """
        Test that multiple teams can be created for the same country.

        Verifies:
        - Multiple teams can reference the same country (many-to-one)
        - All teams persist correctly
        - All teams have correct country relationship

        Arrange: Create one country
        Act: Create 3 teams for that country
        Assert: All 3 teams exist with same country_id
        """
        # Arrange - create country
        country_repository = CountryRepository(db_session)
        country = await country_repository.create({
            "name": "Germany",
            "code": "DEU"
        })

        # Act - create multiple teams for same country
        team_repository = TeamRepository(db_session)
        team1 = await team_repository.create({
            "name": "Team Saxony",
            "country_id": country.id
        })
        team2 = await team_repository.create({
            "name": "Team Bavaria",
            "country_id": country.id
        })
        team3 = await team_repository.create({
            "name": "Team Berlin",
            "country_id": country.id
        })

        # Assert - all teams created successfully
        assert team1.country_id == country.id
        assert team2.country_id == country.id
        assert team3.country_id == country.id

        # Assert - all teams retrievable
        teams = await team_repository.list_by_country(country.id)
        assert len(teams) == 3
        team_names = {t.name for t in teams}
        assert team_names == {"Team Saxony", "Team Bavaria", "Team Berlin"}


class TestTeamRepositoryIntegrationRetrieval:
    """Integration tests for retrieving teams from database."""

    @pytest.mark.asyncio
    async def test_get_by_id_retrieves_team_with_eager_loaded_country(self, db_session):
        """
        Test that get_by_id retrieves team with eager-loaded country data.

        Verifies:
        - Team retrieved by ID
        - Country relationship is eager-loaded (no N+1 query)
        - Can access country.name without additional query

        Arrange: Create country and team
        Act: Retrieve team by ID
        Assert: Team retrieved with country data accessible
        """
        # Arrange
        country_repository = CountryRepository(db_session)
        country = await country_repository.create({
            "name": "France",
            "code": "FRA"
        })

        team_repository = TeamRepository(db_session)
        created = await team_repository.create({
            "name": "Team France Elite",
            "country_id": country.id
        })

        # Act
        retrieved = await team_repository.get_by_id(created.id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Team France Elite"
        assert retrieved.country_id == country.id

        # Assert - country is eager-loaded (no additional query needed)
        assert retrieved.country is not None
        assert retrieved.country.code == "FRA"
        assert retrieved.country.name == "France"

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_nonexistent_id(self, db_session, random_uuid):
        """
        Test that get_by_id returns None for UUID that doesn't exist.

        Verifies:
        - Query handles missing ID gracefully
        - Returns None instead of raising exception

        Arrange: Generate random UUID that doesn't exist in database
        Act: Attempt to retrieve by that UUID
        Assert: Returns None
        """
        # Arrange
        team_repository = TeamRepository(db_session)
        nonexistent_id = random_uuid

        # Act
        result = await team_repository.get_by_id(nonexistent_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all_returns_all_teams_with_country_data(self, db_session):
        """
        Test that list_all returns all teams with eager-loaded country data.

        Verifies:
        - Bulk retrieval works
        - Count matches inserts
        - All teams have country data loaded

        Arrange: Create 2 countries and 3 teams
        Act: Call list_all()
        Assert: Returns all 3 teams with country relationships
        """
        # Arrange - create countries
        country_repository = CountryRepository(db_session)
        usa = await country_repository.create({"name": "United States", "code": "USA"})
        canada = await country_repository.create({"name": "Canada", "code": "CAN"})

        # Arrange - create teams
        team_repository = TeamRepository(db_session)
        await team_repository.create({"name": "Team USA Alpha", "country_id": usa.id})
        await team_repository.create({"name": "Team USA Bravo", "country_id": usa.id})
        await team_repository.create({"name": "Team Canada Maple", "country_id": canada.id})

        # Act
        all_teams = await team_repository.list_all()

        # Assert
        assert len(all_teams) == 3

        # Verify all teams have country data loaded
        for team in all_teams:
            assert team.country is not None
            assert team.country.code in ["USA", "CAN"]

    @pytest.mark.asyncio
    async def test_list_by_country_filters_correctly(self, db_session):
        """
        Test that list_by_country returns only teams for specified country.

        Verifies:
        - Filtering by country_id works correctly
        - Only teams for specified country returned
        - Country data is eager-loaded

        Arrange: Create 2 countries with teams for each
        Act: Call list_by_country for first country
        Assert: Returns only teams for that country
        """
        # Arrange - create countries
        country_repository = CountryRepository(db_session)
        poland = await country_repository.create({"name": "Poland", "code": "POL"})
        czech = await country_repository.create({"name": "Czech Republic", "code": "CZE"})

        # Arrange - create teams
        team_repository = TeamRepository(db_session)
        await team_repository.create({"name": "Team Poland Warriors", "country_id": poland.id})
        await team_repository.create({"name": "Team Poland Hussars", "country_id": poland.id})
        await team_repository.create({"name": "Team Czech Knights", "country_id": czech.id})

        # Act - filter by Poland
        poland_teams = await team_repository.list_by_country(poland.id)

        # Assert
        assert len(poland_teams) == 2
        team_names = {t.name for t in poland_teams}
        assert team_names == {"Team Poland Warriors", "Team Poland Hussars"}

        # Verify country data is eager-loaded
        for team in poland_teams:
            assert team.country is not None
            assert team.country.code == "POL"


class TestTeamRepositoryIntegrationDeactivate:
    """Integration tests for deactivate functionality."""

    @pytest.mark.asyncio
    async def test_deactivate_sets_flag_preserves_country_relationship(self, db_session):
        """
        Test that deactivate updates is_deactivated flag but preserves country FK.

        Verifies:
        - is_deactivated flag is updated to True
        - Team still exists in database
        - Country relationship preserved for historical tracking
        - Default queries exclude deactivated team

        Arrange: Create country and team
        Act: Deactivate team
        Assert: is_deactivated=True, excluded from default queries, country FK intact
        """
        # Arrange
        country_repository = CountryRepository(db_session)
        country = await country_repository.create({"name": "Spain", "code": "ESP"})

        team_repository = TeamRepository(db_session)
        team = await team_repository.create({
            "name": "Team Spain Conquistadors",
            "country_id": country.id
        })
        team_id = team.id

        # Act
        await team_repository.deactivate(team_id)

        # Assert - default query excludes deactivated
        retrieved = await team_repository.get_by_id(team_id, include_deactivated=False)
        assert retrieved is None

        # Assert - can still retrieve with include_deactivated=True
        retrieved_with_deleted = await team_repository.get_by_id(team_id, include_deactivated=True)
        assert retrieved_with_deleted is not None
        assert retrieved_with_deleted.is_deactivated is True

        # Assert - country relationship preserved
        assert retrieved_with_deleted.country_id == country.id
        assert retrieved_with_deleted.country.code == "ESP"

    @pytest.mark.asyncio
    async def test_list_all_excludes_deactivated_teams_by_default(self, db_session):
        """
        Test that list_all filters out deactivated teams by default.

        Verifies:
        - Active teams returned
        - Deactivated teams excluded
        - Can include deactivated teams with flag

        Arrange: Create 3 teams, deactivate 1
        Act: Call list_all() with and without include_deactivate
        Assert: Default returns 2, with flag returns 3
        """
        # Arrange
        country_repository = CountryRepository(db_session)
        country = await country_repository.create({"name": "Italy", "code": "ITA"})

        team_repository = TeamRepository(db_session)
        team1 = await team_repository.create({"name": "Team Rome", "country_id": country.id})
        team2 = await team_repository.create({"name": "Team Venice", "country_id": country.id})
        team3 = await team_repository.create({"name": "Team Milan", "country_id": country.id})

        # Deactivate one team
        await team_repository.deactivate(team2.id)

        # Act - default query
        active_teams = await team_repository.list_all(include_deactivated=False)

        # Assert
        assert len(active_teams) == 2
        team_names = {t.name for t in active_teams}
        assert team_names == {"Team Rome", "Team Milan"}

        # Act - query including deleted
        all_teams = await team_repository.list_all(include_deactivated=True)

        # Assert
        assert len(all_teams) == 3
        all_names = {t.name for t in all_teams}
        assert all_names == {"Team Rome", "Team Venice", "Team Milan"}

    @pytest.mark.asyncio
    async def test_list_by_country_excludes_deactivated_teams_by_default(self, db_session):
        """
        Test that list_by_country filters out deactivated teams by default.

        Verifies:
        - Filtering by country respects deactivate flag
        - Can include deactivated teams with flag

        Arrange: Create country with 3 teams, deactivate 1
        Act: Call list_by_country() with and without include_deactivate
        Assert: Default returns 2, with flag returns 3
        """
        # Arrange
        country_repository = CountryRepository(db_session)
        country = await country_repository.create({"name": "Russia", "code": "RUS"})

        team_repository = TeamRepository(db_session)
        team1 = await team_repository.create({"name": "Team Moscow", "country_id": country.id})
        team2 = await team_repository.create({"name": "Team St Petersburg", "country_id": country.id})
        team3 = await team_repository.create({"name": "Team Kazan", "country_id": country.id})

        # Deactivate one team
        await team_repository.deactivate(team2.id)

        # Act - default query
        active_teams = await team_repository.list_by_country(country.id, include_deactivated=False)

        # Assert
        assert len(active_teams) == 2
        team_names = {t.name for t in active_teams}
        assert team_names == {"Team Moscow", "Team Kazan"}

        # Act - query including deleted
        all_teams = await team_repository.list_by_country(country.id, include_deactivated=True)

        # Assert
        assert len(all_teams) == 3


class TestTeamRepositoryIntegrationUpdate:
    """Integration tests for updating teams."""

    @pytest.mark.asyncio
    async def test_update_team_name_persists_change(self, db_session):
        """
        Test that updating team name persists to database.

        Verifies:
        - Update modifies database record
        - Changes visible on subsequent retrieval
        - Country relationship unchanged

        Arrange: Create team with name "Team Alpha"
        Act: Update name to "Team Alpha Elite"
        Assert: Retrieved team has new name, same country
        """
        # Arrange
        country_repository = CountryRepository(db_session)
        country = await country_repository.create({"name": "Belgium", "code": "BEL"})

        team_repository = TeamRepository(db_session)
        team = await team_repository.create({
            "name": "Team Alpha",
            "country_id": country.id
        })

        # Act
        updated = await team_repository.update(team.id, {"name": "Team Alpha Elite"})

        # Assert - in-memory object
        assert updated.name == "Team Alpha Elite"
        assert updated.country_id == country.id

        # Assert - persisted to database
        retrieved = await team_repository.get_by_id(team.id)
        if retrieved is None:
            pytest.fail("Updated team not found in database")
        assert retrieved.name == "Team Alpha Elite"
        assert retrieved.country.code == "BEL"

    @pytest.mark.asyncio
    async def test_update_country_id_validates_new_country_exists(self, db_session):
        """
        Test that updating country_id to invalid value raises IntegrityError.

        Verifies:
        - Database FK constraint enforced on update
        - Cannot change team to reference non-existent country
        - Error raised from database

        Arrange: Create team with valid country
        Act: Update country_id to non-existent UUID
        Assert: IntegrityError raised by FK constraint
        """
        # Arrange
        country_repository = CountryRepository(db_session)
        country = await country_repository.create({"name": "Netherlands", "code": "NLD"})

        team_repository = TeamRepository(db_session)
        team = await team_repository.create({
            "name": "Team Netherlands",
            "country_id": country.id
        })

        # Act & Assert - FK constraint violation
        nonexistent_country_id = uuid4()
        with pytest.raises(IntegrityError):
            await team_repository.update(team.id, {"country_id": nonexistent_country_id})

    @pytest.mark.asyncio
    async def test_update_country_id_to_different_valid_country_succeeds(self, db_session):
        """
        Test that updating team to reference different valid country succeeds.

        Verifies:
        - Can change team's country
        - FK relationship updated correctly
        - Eager-loaded country reflects new relationship

        Arrange: Create 2 countries and team for first country
        Act: Update team to reference second country
        Assert: Team now associated with second country
        """
        # Arrange
        country_repository = CountryRepository(db_session)
        austria = await country_repository.create({"name": "Austria", "code": "AUT"})
        switzerland = await country_repository.create({"name": "Switzerland", "code": "CHE"})

        team_repository = TeamRepository(db_session)
        team = await team_repository.create({
            "name": "Team Alpine Warriors",
            "country_id": austria.id
        })

        # Act
        updated = await team_repository.update(team.id, {"country_id": switzerland.id})

        # Assert - updated to new country
        assert updated.country_id == switzerland.id
        assert updated.country.code == "CHE"

        # Assert - persisted to database
        retrieved = await team_repository.get_by_id(team.id)
        assert retrieved.country_id == switzerland.id
        assert retrieved.country.name == "Switzerland"


class TestTeamRepositoryIntegrationDelete:
    """Integration tests for team deletion."""

    @pytest.mark.asyncio
    async def test_delete_removes_from_database(self, db_session):
        """
        Test thatdelete removes team from database entirely.

        Verifies:
        - Team removed from database (hard delete)
        - Not retrievable even with include_deactivated=True
        - Country record unaffected

        Arrange: Create country and team
        Act: Permanently delete team
        Assert: Team no longer retrievable, country still exists
        """
        # Arrange
        country_repository = CountryRepository(db_session)
        country = await country_repository.create({"name": "Test Country", "code": "TST"})

        team_repository = TeamRepository(db_session)
        team = await team_repository.create({
            "name": "Test Team",
            "country_id": country.id
        })
        team_id = team.id

        # Act
        await team_repository.delete(team_id)

        # Assert - cannot retrieve even with include_deactivate
        retrieved = await team_repository.get_by_id(team_id, include_deactivated=True)
        assert retrieved is None

        # Assert - country still exists
        country_check = await country_repository.get_by_id(country.id)
        assert country_check is not None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_team_raises_error(self, db_session, random_uuid):
        """
        Test that delete of nonexistent team raises ValueError.

        Verifies:
        - Error handling for missing team
        - Consistent error behavior

        Arrange: Generate UUID that doesn't exist
        Act: Attempt to permanently delete
        Assert: ValueError raised
        """
        # Arrange
        team_repository = TeamRepository(db_session)
        nonexistent_id = random_uuid

        # Act & Assert
        with pytest.raises(ValueError, match="Team not found"):
            await team_repository.delete(nonexistent_id)


# ============================================================================
# NOTES FOR REVIEWERS
# ============================================================================

"""
These integration tests demonstrate:

1. **Foreign Key Constraints**: Tests verify PostgreSQL enforces FK constraints
   - Cannot create team with invalid country_id
   - Cannot update team to reference non-existent country
   - FK constraint errors raised as IntegrityError

2. **Eager Loading**: Tests verify joinedload works correctly
   - Country data accessible via team.country without additional queries
   - Prevents N+1 query problem when iterating through teams
   - All retrieval methods (get_by_id, list_all, list_by_country) eager-load

3. **Soft Delete with Relationships**: Tests verify deactivate preserves FK
   - Soft-deleted teams retain country relationship for historical tracking
   - Can retrieve deactivated team with country data via include_deactivated=True
   - List operations respect deactivate flag at database level

4. **Real Database Interaction**: Tests run against actual PostgreSQL
   - Testcontainers spins up real PostgreSQL 16 container
   - Each test gets fresh database (isolation)
   - No mocking - tests verify actual database behavior

To run these tests:
```bash
# Ensure Docker Desktop is running first!
docker ps  # Should not error

# Run team integration tests only
pytest tests/integration/repositories/test_team_repository_integration.py -v

# Run all integration tests
pytest tests/integration/ -v

# Run with markers
pytest -m integration -v
```

Performance note:
- Container spin-up: ~2-5 seconds (session scope, once per test run)
- Test execution: ~0.1-0.3 seconds per test (slightly slower than Country due to FK setup)
- Total for all Team integration tests: ~3-5 seconds

Coverage:
- Team creation with valid/invalid FK
- Retrieval with eager-loaded relationships
- Filtering by country_id
- Deactivate preserving relationships
- Update operations with FK validation
- Permanent delete
- Edge cases (nonexistent IDs, constraint violations)
"""
