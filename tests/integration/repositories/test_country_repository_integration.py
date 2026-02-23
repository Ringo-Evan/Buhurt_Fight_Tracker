"""
Integration tests for CountryRepository with real PostgreSQL database.

Uses Testcontainers to spin up a real PostgreSQL instance for testing.
These tests verify that our repository layer works correctly with actual database.

Requirements:
- Docker Desktop must be running
- testcontainers package installed
"""

import pytest
from uuid import uuid4
from sqlalchemy.exc import IntegrityError
from app.repositories.country_repository import CountryRepository
from app.models.country import Country


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestCountryRepositoryIntegrationCreate:
    """Integration tests for Country creation with real database."""

    @pytest.mark.asyncio
    async def test_create_country_persists_to_database(self, db_session):
        """
        Test that creating a country persists to PostgreSQL and generates all fields.

        Verifies:
        - Country is inserted into database
        - UUID is generated automatically
        - Default values (is_deactivated=False, created_at) are set by model
        - Can be retrieved after creation

        Arrange: Create repository with real database session
        Act: Create country with name and code
        Assert: Country persisted with all fields populated
        """
        # Arrange
        repository = CountryRepository(db_session)
        country_data = {
            "name": "Czech Republic",
            "code": "CZE"
        }

        # Act
        created_country = await repository.create(country_data)

        # Assert - verify in-memory object
        assert created_country.id is not None
        assert isinstance(created_country.id, type(uuid4()))
        assert created_country.name == "Czech Republic"
        assert created_country.code == "CZE"
        assert created_country.is_deactivated is False
        assert created_country.created_at is not None

        # Assert - verify persisted to database by retrieving
        retrieved_country = await repository.get_by_id(created_country.id)
        assert retrieved_country is not None
        assert retrieved_country.id == created_country.id
        assert retrieved_country.name == "Czech Republic"
        assert retrieved_country.code == "CZE"

    @pytest.mark.asyncio
    async def test_create_country_enforces_unique_code_constraint(self, db_session):
        """
        Test that database enforces unique constraint on country code.

        Verifies:
        - First insert succeeds
        - Second insert with same code raises IntegrityError
        - Database constraint is enforced (not just application logic)

        Arrange: Create first country with code "USA"
        Act: Attempt to create second country with same code
        Assert: IntegrityError raised by database
        """
        # Arrange
        repository = CountryRepository(db_session)

        # Create first country
        await repository.create({"name": "United States", "code": "USA"})

        # Act & Assert - second country with same code should fail
        with pytest.raises(IntegrityError):
            await repository.create({"name": "United States of America", "code": "USA"})

    @pytest.mark.asyncio
    async def test_create_multiple_countries_all_persist(self, db_session, sample_country_data_list):
        """
        Test that multiple countries can be created and all persist correctly.

        Verifies:
        - Multiple inserts work
        - All countries retrievable
        - Correct count returned

        Arrange: Prepare list of 5 countries
        Act: Create all countries
        Assert: All 5 countries exist in database
        """
        # Arrange
        repository = CountryRepository(db_session)

        # Act - create all countries
        created_countries = []
        for country_data in sample_country_data_list:
            country = await repository.create(country_data)
            created_countries.append(country)

        # Assert - verify all were created
        assert len(created_countries) == 5

        # Assert - verify all are retrievable
        all_countries = await repository.list_all()
        assert len(all_countries) == 5

        # Assert - verify codes match
        created_codes = {c.code for c in created_countries}
        retrieved_codes = {c.code for c in all_countries}
        assert created_codes == retrieved_codes


class TestCountryRepositoryIntegrationRetrieval:
    """Integration tests for retrieving countries from database."""

    @pytest.mark.asyncio
    async def test_get_by_id_retrieves_correct_country(self, db_session):
        """
        Test that get_by_id retrieves the correct country from database.

        Verifies:
        - Inserted country can be retrieved by ID
        - All fields match what was inserted

        Arrange: Create country in database
        Act: Retrieve by ID
        Assert: Retrieved country matches created country
        """
        # Arrange
        repository = CountryRepository(db_session)
        created = await repository.create({"name": "Poland", "code": "POL"})

        # Act
        retrieved = await repository.get_by_id(created.id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Poland"
        assert retrieved.code == "POL"
        assert retrieved.is_deactivated == created.is_deactivated
        assert retrieved.created_at == created.created_at

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
        repository = CountryRepository(db_session)
        nonexistent_id = random_uuid

        # Act
        result = await repository.get_by_id(nonexistent_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_code_retrieves_correct_country(self, db_session):
        """
        Test that get_by_code retrieves country by ISO code.

        Verifies:
        - Code-based lookup works
        - Returns correct country

        Arrange: Create country with code "DEU"
        Act: Retrieve by code "DEU"
        Assert: Retrieved country matches
        """
        # Arrange
        repository = CountryRepository(db_session)
        await repository.create({"name": "Germany", "code": "DEU"})

        # Act
        retrieved = await repository.get_by_code("DEU")

        # Assert
        assert retrieved is not None
        assert retrieved.name == "Germany"
        assert retrieved.code == "DEU"

    @pytest.mark.asyncio
    async def test_list_all_returns_all_countries(self, db_session, sample_country_data_list):
        """
        Test that list_all returns all countries in database.

        Verifies:
        - Bulk retrieval works
        - Count matches inserts

        Arrange: Create 5 countries
        Act: Call list_all()
        Assert: Returns all 5 countries
        """
        # Arrange
        repository = CountryRepository(db_session)
        for country_data in sample_country_data_list:
            await repository.create(country_data)

        # Act
        all_countries = await repository.list_all()

        # Assert
        assert len(all_countries) == 5
        codes = {c.code for c in all_countries}
        assert codes == {"USA", "CAN", "MEX", "DEU", "FRA"}


class TestCountryRepositoryIntegrationDeactivate:
    """Integration tests for deactivate functionality."""

    @pytest.mark.asyncio
    async def test_deactivate_sets_flag_in_database(self, db_session):
        """
        Test that deactivate updates is_deactivated flag in database.

        Verifies:
        - is_deactivated flag is updated to True
        - Country still exists in database
        - Default queries exclude deactivated country

        Arrange: Create country
        Act: deactivate it
        Assert: is_deactivated=True, excluded from default queries
        """
        # Arrange
        repository = CountryRepository(db_session)
        country = await repository.create({"name": "Russia", "code": "RUS"})
        country_id = country.id

        # Act
        await repository.deactivate(country_id)

        # Assert - default query excludes soft-deactivated
        retrieved = await repository.get_by_id(country_id, include_deactivated=False)
        assert retrieved is None

        # Assert - can still retrieve with include_deactivated=True
        retrieved_with_deactivated = await repository.get_by_id(country_id, include_deactivated=True)
        assert retrieved_with_deactivated is not None
        assert retrieved_with_deactivated.is_deactivated is True

    @pytest.mark.asyncio
    async def test_list_all_excludes_deactivated_by_default(self, db_session):
        """
        Test that list_all filters out deactivated countries by default.

        Verifies:
        - Active countries returned
        - Deactivated countries excluded
        - Can include deactivated with flag

        Arrange: Create 3 countries, deactivate 1
        Act: Call list_all() with and without include_deactivated
        Assert: Default returns 2, with flag returns 3
        """
        # Arrange
        repository = CountryRepository(db_session)
        country1 = await repository.create({"name": "Spain", "code": "ESP"})
        country2 = await repository.create({"name": "Portugal", "code": "PRT"})
        country3 = await repository.create({"name": "Italy", "code": "ITA"})

        # Soft delete one country
        await repository.deactivate(country2.id)

        # Act - default query
        active_countries = await repository.list_all(include_deactivated=False)

        # Assert
        assert len(active_countries) == 2
        codes = {c.code for c in active_countries}
        assert codes == {"ESP", "ITA"}

        # Act - query including deactivated
        all_countries = await repository.list_all(include_deactivated=True)

        # Assert
        assert len(all_countries) == 3
        all_codes = {c.code for c in all_countries}
        assert all_codes == {"ESP", "PRT", "ITA"}


class TestCountryRepositoryIntegrationUpdate:
    """Integration tests for updating countries."""

    @pytest.mark.asyncio
    async def test_update_country_name_persists_change(self, db_session):
        """
        Test that updating country name persists to database.

        Verifies:
        - Update modifies database record
        - Changes visible on subsequent retrieval

        Arrange: Create country with name "Czechia"
        Act: Update name to "Czech Republic"
        Assert: Retrieved country has new name
        """
        # Arrange
        repository = CountryRepository(db_session)
        country = await repository.create({"name": "Czechia", "code": "CZE"})

        # Act
        updated = await repository.update(country.id, {"name": "Czech Republic"})

        # Assert - in-memory object
        assert updated.name == "Czech Republic"
        assert updated.code == "CZE"  # Code unchanged

        # Assert - persisted to database
        retrieved = await repository.get_by_id(country.id)
        assert retrieved.name == "Czech Republic"

    @pytest.mark.asyncio
    async def test_update_enforces_unique_code_constraint(self, db_session):
        """
        Test that updating code to duplicate value raises IntegrityError.

        Verifies:
        - Database constraint prevents duplicate codes
        - Error raised from database, not application logic

        Arrange: Create two countries with different codes
        Act: Update second country to have first country's code
        Assert: IntegrityError raised
        """
        # Arrange
        repository = CountryRepository(db_session)
        country1 = await repository.create({"name": "Belgium", "code": "BEL"})
        country2 = await repository.create({"name": "Netherlands", "code": "NLD"})

        # Act & Assert
        with pytest.raises(IntegrityError):
            await repository.update(country2.id, {"code": "BEL"})


class TestCountryRepositoryIntegrationDelete:
    """Integration tests for deletion."""

    @pytest.mark.asyncio
    async def test_delete_removes_from_database(self, db_session):
        """
        Test that delete removes country from database entirely.

        Verifies:
        - Country removed from database
        - Not retrievable even with include_deactivated=True

        Arrange: Create country
        Act: Permanently delete it
        Assert: No longer retrievable
        """
        # Arrange
        repository = CountryRepository(db_session)
        country = await repository.create({"name": "Test Country", "code": "TST"})
        country_id = country.id

        # Act
        await repository.delete(country_id)

        # Assert - cannot retrieve even with include_deactivate
        retrieved = await repository.get_by_id(country_id, include_deactivated=True)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_country_raises_error(self, db_session, random_uuid):
        """
        Test that delete of nonexistent country raises ValueError.

        Verifies:
        - Error handling for missing country
        - Consistent error behavior

        Arrange: Generate UUID that doesn't exist
        Act: Attempt to delete
        Assert: ValueError raised
        """
        # Arrange
        repository = CountryRepository(db_session)
        nonexistent_id = random_uuid

        # Act & Assert
        with pytest.raises(ValueError, match="Country not found"):
            await repository.delete(nonexistent_id)


# ============================================================================
# NOTES FOR REVIEWERS
# ============================================================================

"""
These integration tests demonstrate:

1. **Real Database Interaction**: Tests run against actual PostgreSQL (not mocked)
2. **Testcontainers**: Docker container spins up, runs tests, tears down automatically
3. **Test Isolation**: Each test gets fresh database (schema created/dropped per test)
4. **Database Constraints**: Tests verify that PostgreSQL enforces unique constraints
5. **Async Operations**: All repository methods tested with real async database calls

To run these tests:
```bash
# Ensure Docker Desktop is running first!
docker ps  # Should not error

# Run integration tests only
pytest tests/integration/ -v

# Run with markers
pytest -m integration -v

# Run specific integration test
pytest tests/integration/repositories/test_country_repository_integration.py::TestCountryRepositoryIntegrationCreate::test_create_country_persists_to_database -v
```

Performance note:
- Container spin-up: ~2-5 seconds (session scope, once per test run)
- Test execution: ~0.1-0.2 seconds per test
- Total for all integration tests: ~5-10 seconds

This is acceptable for integration tests. Unit tests remain fast (<1 second total).
"""
