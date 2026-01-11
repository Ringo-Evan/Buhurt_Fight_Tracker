"""
Unit tests for CountryRepository.

Tests the data access layer for Country entity operations with mocked SQLAlchemy AsyncSession.
Following TDD approach - these tests are written before implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
from sqlalchemy.exc import IntegrityError

# These imports will fail until implementation exists - that's expected in TDD
from app.repositories.country_repository import CountryRepository
from app.models.country import Country


class TestCountryRepositoryCreate:
    """Test suite for country creation operations."""

    @pytest.mark.asyncio
    async def test_create_country_calls_session_methods_correctly(self):
        """
        Test that creating a country calls add(), commit(), and refresh() in correct order.

        Arrange: Mock AsyncSession and create test country data
        Act: Call repository.create() with country data
        Assert: Verify session methods called with correct arguments
        """
        # Arrange
        mock_session = AsyncMock()
        mock_session.add = MagicMock()  # session.add() is not async
        repository = CountryRepository(mock_session)

        country_data = {
            "name": "Czech Republic",
            "code": "CZE"
        }

        # Act
        result = await repository.create(country_data)

        # Assert
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()

        # Verify the created country has expected attributes
        assert result.name == "Czech Republic"
        assert result.code == "CZE"
        assert result.is_deleted is False
        assert result.id is not None
        assert result.created_at is not None

    @pytest.mark.asyncio
    async def test_create_country_handles_duplicate_code_constraint_violation(self):
        """
        Test that creating a country with duplicate code raises appropriate error.

        Arrange: Mock AsyncSession to raise IntegrityError on commit
        Act: Attempt to create country with duplicate code
        Assert: IntegrityError is propagated
        """
        # Arrange
        mock_session = AsyncMock()
        mock_session.add = MagicMock()  # session.add() is not async
        mock_session.commit.side_effect = IntegrityError(
            statement="INSERT INTO countries...",
            params={},
            orig=Exception("duplicate key value violates unique constraint")
        )
        repository = CountryRepository(mock_session)

        country_data = {
            "name": "Czech Republic",
            "code": "CZE"
        }

        # Act & Assert
        with pytest.raises(IntegrityError):
            await repository.create(country_data)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()


class TestCountryRepositoryGetById:
    """Test suite for retrieving countries by ID."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_country_when_exists(self):
        """
        Test successful country lookup by ID.

        Arrange: Mock session with execute returning a country
        Act: Call repository.get_by_id()
        Assert: Returns the country object
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()
        expected_country = Country(
            id=country_id,
            name="Czech Republic",
            code="CZE",
            is_deleted=False,
            created_at=datetime.utcnow()
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_country
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        # Act
        result = await repository.get_by_id(country_id)

        # Assert
        assert result == expected_country
        assert result.id == country_id
        assert result.name == "Czech Republic"
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_exists(self):
        """
        Test that get_by_id returns None for non-existent country.

        Arrange: Mock session returning None
        Act: Call repository.get_by_id() with non-existent ID
        Assert: Returns None
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        # Act
        result = await repository.get_by_id(country_id)

        # Assert
        assert result is None
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_id_filters_soft_deleted_countries(self):
        """
        Test that get_by_id excludes soft-deleted countries.

        Arrange: Mock session that would return a soft-deleted country
        Act: Call repository.get_by_id()
        Assert: Returns None (soft-deleted filtered out)
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()

        # The query should filter is_deleted=False, so it returns None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        # Act
        result = await repository.get_by_id(country_id)

        # Assert
        assert result is None
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_id_as_admin_returns_soft_deleted_country(self):
        """
        Test that get_by_id with include_deleted=True returns soft-deleted countries.

        Arrange: Mock session returning a soft-deleted country
        Act: Call repository.get_by_id(include_deleted=True)
        Assert: Returns the soft-deleted country
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()
        deleted_country = Country(
            id=country_id,
            name="Czech Republic",
            code="CZE",
            is_deleted=True,
            created_at=datetime.utcnow()
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = deleted_country
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        # Act
        result = await repository.get_by_id(country_id, include_deleted=True)

        # Assert
        assert result == deleted_country
        assert result.is_deleted is True
        mock_session.execute.assert_awaited_once()


class TestCountryRepositoryGetByCode:
    """Test suite for retrieving countries by ISO code."""

    @pytest.mark.asyncio
    async def test_get_by_code_returns_country_when_exists(self):
        """
        Test successful country lookup by ISO code.

        Arrange: Mock session returning country with matching code
        Act: Call repository.get_by_code()
        Assert: Returns the country object
        """
        # Arrange
        mock_session = AsyncMock()
        expected_country = Country(
            id=uuid4(),
            name="Czech Republic",
            code="CZE",
            is_deleted=False,
            created_at=datetime.utcnow()
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_country
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        # Act
        result = await repository.get_by_code("CZE")

        # Assert
        assert result == expected_country
        assert result.code == "CZE"
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_code_returns_none_when_not_exists(self):
        """
        Test that get_by_code returns None for non-existent code.

        Arrange: Mock session returning None
        Act: Call repository.get_by_code() with non-existent code
        Assert: Returns None
        """
        # Arrange
        mock_session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        # Act
        result = await repository.get_by_code("XYZ")

        # Assert
        assert result is None
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_code_filters_soft_deleted_countries(self):
        """
        Test that get_by_code excludes soft-deleted countries.

        Arrange: Mock session that filters out deleted countries
        Act: Call repository.get_by_code()
        Assert: Returns None (soft-deleted filtered out)
        """
        # Arrange
        mock_session = AsyncMock()

        # The query should filter is_deleted=False, so it returns None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        # Act
        result = await repository.get_by_code("CZE")

        # Assert
        assert result is None
        mock_session.execute.assert_awaited_once()


class TestCountryRepositoryList:
    """Test suite for listing countries."""

    @pytest.mark.asyncio
    async def test_list_all_excludes_soft_deleted_countries(self):
        """
        Test that list_all excludes soft-deleted entries.

        Arrange: Mock session returning only active countries
        Act: Call repository.list_all()
        Assert: Returns list without deleted countries
        """
        # Arrange
        mock_session = AsyncMock()
        active_countries = [
            Country(
                id=uuid4(),
                name="Czech Republic",
                code="CZE",
                is_deleted=False,
                created_at=datetime.utcnow()
            ),
            Country(
                id=uuid4(),
                name="Poland",
                code="POL",
                is_deleted=False,
                created_at=datetime.utcnow()
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = active_countries
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        # Act
        result = await repository.list_all()

        # Assert
        assert len(result) == 2
        assert all(not country.is_deleted for country in result)
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_all_returns_empty_list_when_no_active_countries(self):
        """
        Test that list_all returns empty list when no active countries exist.

        Arrange: Mock session returning empty list
        Act: Call repository.list_all()
        Assert: Returns empty list
        """
        # Arrange
        mock_session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        # Act
        result = await repository.list_all()

        # Assert
        assert result == []
        assert len(result) == 0
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_all_as_admin_includes_soft_deleted_countries(self):
        """
        Test that list_all with include_deleted=True includes soft-deleted countries.

        Arrange: Mock session returning both active and deleted countries
        Act: Call repository.list_all(include_deleted=True)
        Assert: Returns list with both active and deleted countries
        """
        # Arrange
        mock_session = AsyncMock()
        all_countries = [
            Country(
                id=uuid4(),
                name="Czech Republic",
                code="CZE",
                is_deleted=False,
                created_at=datetime.utcnow()
            ),
            Country(
                id=uuid4(),
                name="Poland",
                code="POL",
                is_deleted=True,  # Soft-deleted
                created_at=datetime.utcnow()
            ),
            Country(
                id=uuid4(),
                name="Germany",
                code="DEU",
                is_deleted=False,
                created_at=datetime.utcnow()
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = all_countries
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        # Act
        result = await repository.list_all(include_deleted=True)

        # Assert
        assert len(result) == 3
        assert any(country.is_deleted for country in result)
        mock_session.execute.assert_awaited_once()


class TestCountryRepositorySoftDelete:
    """Test suite for soft deletion operations."""

    @pytest.mark.asyncio
    async def test_soft_delete_sets_is_deleted_flag_to_true(self):
        """
        Test that soft delete updates is_deleted flag to True.

        Arrange: Mock session and existing country
        Act: Call repository.soft_delete()
        Assert: is_deleted flag set to True and changes committed
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()
        country = Country(
            id=country_id,
            name="Czech Republic",
            code="CZE",
            is_deleted=False,
            created_at=datetime.utcnow()
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = country
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        # Act
        await repository.soft_delete(country_id)

        # Assert
        assert country.is_deleted is True
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_soft_delete_raises_error_for_non_existent_country(self):
        """
        Test that soft delete raises error for non-existent country.

        Arrange: Mock session returning None for country lookup
        Act: Attempt to soft delete non-existent country
        Assert: Raises appropriate exception
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        # Act & Assert
        with pytest.raises(ValueError, match="Country not found"):
            await repository.soft_delete(country_id)

        mock_session.commit.assert_not_awaited()


class TestCountryRepositoryUpdate:
    """Test suite for country update operations."""

    @pytest.mark.asyncio
    async def test_update_country_name_succeeds(self):
        """
        Test that updating a country's name succeeds.

        Arrange: Mock session with existing country
        Act: Call repository.update() with new name
        Assert: Name updated and changes committed
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()
        country = Country(
            id=country_id,
            name="Czech Republic",
            code="CZE",
            is_deleted=False,
            created_at=datetime.utcnow()
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = country
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        update_data = {"name": "Czechia"}

        # Act
        result = await repository.update(country_id, update_data)

        # Assert
        assert result.name == "Czechia"
        assert result.code == "CZE"
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_country_code_succeeds(self):
        """
        Test that updating a country's code succeeds.

        Arrange: Mock session with existing country
        Act: Call repository.update() with new code
        Assert: Code updated and changes committed
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()
        country = Country(
            id=country_id,
            name="Czechia",
            code="CZE",
            is_deleted=False,
            created_at=datetime.utcnow()
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = country
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        update_data = {"code": "CZK"}

        # Act
        result = await repository.update(country_id, update_data)

        # Assert
        assert result.name == "Czechia"
        assert result.code == "CZK"
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_country_with_duplicate_code_raises_integrity_error(self):
        """
        Test that updating to duplicate code raises IntegrityError.

        Arrange: Mock session raising IntegrityError on commit
        Act: Attempt to update country with duplicate code
        Assert: IntegrityError is propagated
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()
        country = Country(
            id=country_id,
            name="Czech Republic",
            code="CZE",
            is_deleted=False,
            created_at=datetime.utcnow()
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = country
        mock_session.execute.return_value = mock_result
        mock_session.commit.side_effect = IntegrityError(
            statement="UPDATE countries...",
            params={},
            orig=Exception("duplicate key value violates unique constraint")
        )

        repository = CountryRepository(mock_session)

        update_data = {"code": "POL"}  # Duplicate code

        # Act & Assert
        with pytest.raises(IntegrityError):
            await repository.update(country_id, update_data)

        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_country_raises_error_for_non_existent_country(self):
        """
        Test that update raises error for non-existent country.

        Arrange: Mock session returning None for country lookup
        Act: Attempt to update non-existent country
        Assert: Raises ValueError
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        update_data = {"name": "New Name"}

        # Act & Assert
        with pytest.raises(ValueError, match="Country not found"):
            await repository.update(country_id, update_data)

        mock_session.commit.assert_not_awaited()


class TestCountryRepositoryPermanentDelete:
    """Test suite for permanent deletion operations."""

    @pytest.mark.asyncio
    async def test_permanent_delete_removes_country_from_database(self):
        """
        Test that permanent delete removes country from database.

        Arrange: Mock session with soft-deleted country
        Act: Call repository.permanent_delete()
        Assert: session.delete() called and changes committed
        """
        # Arrange
        mock_session = AsyncMock()
        mock_session.delete = MagicMock()  # session.delete() is not async
        country_id = uuid4()
        country = Country(
            id=country_id,
            name="Czech Republic",
            code="CZE",
            is_deleted=True,
            created_at=datetime.utcnow()
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = country
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        # Act
        await repository.permanent_delete(country_id)

        # Assert
        mock_session.delete.assert_called_once_with(country)
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_permanent_delete_raises_error_for_non_existent_country(self):
        """
        Test that permanent delete raises error for non-existent country.

        Arrange: Mock session returning None
        Act: Attempt to permanently delete non-existent country
        Assert: Raises ValueError
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        # Act & Assert
        with pytest.raises(ValueError, match="Country not found"):
            await repository.permanent_delete(country_id)

        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_count_relationships_returns_correct_count(self):
        """
        Test that count_relationships returns the number of related entities.

        Arrange: Mock session returning relationship count
        Act: Call repository.count_relationships()
        Assert: Returns correct count
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()
        country = Country(
            id=country_id,
            name="United States",
            code="USA",
            is_deleted=False,
            created_at=datetime.utcnow()
        )

        # First execute: get_by_id returns country
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = country

        # Second execute: count query returns 3
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 3

        mock_session.execute.side_effect = [mock_get_result, mock_count_result]

        repository = CountryRepository(mock_session)

        # Act
        result = await repository.count_relationships(country_id)

        # Assert
        assert result == 3
        assert mock_session.execute.await_count == 2  # get_by_id + count query

    @pytest.mark.asyncio
    async def test_count_relationships_returns_zero_for_no_relationships(self):
        """
        Test that count_relationships returns 0 when no relationships exist.

        Arrange: Mock session returning 0
        Act: Call repository.count_relationships()
        Assert: Returns 0
        """
        # Arrange
        mock_session = AsyncMock()
        country_id = uuid4()
        country = Country(
            id=country_id,
            name="Test Country",
            code="TST",
            is_deleted=False,
            created_at=datetime.utcnow()
        )

        # Mock get_by_id result (first execute call)
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = country

        # Mock count result (second execute call)
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_session.execute.side_effect = [mock_get_result, mock_count_result]

        repository = CountryRepository(mock_session)

        # Act
        result = await repository.count_relationships(country_id)

        # Assert
        assert result == 0
        assert mock_session.execute.await_count == 2  # get_by_id + count query


class TestCountryRepositoryReplace:
    """Test suite for country replacement operations."""

    @pytest.mark.asyncio
    async def test_replace_country_transfers_relationships(self):
        """
        Test that replace transfers all relationships from old to new country.

        Arrange: Mock session with old and new countries and relationships
        Act: Call repository.replace()
        Assert: Relationships transferred and changes committed
        """
        # Arrange
        mock_session = AsyncMock()
        old_country_id = uuid4()
        new_country_id = uuid4()

        old_country = Country(
            id=old_country_id,
            name="Soviet Union",
            code="SUN",
            is_deleted=True,
            created_at=datetime.utcnow()
        )

        new_country = Country(
            id=new_country_id,
            name="Russia",
            code="RUS",
            is_deleted=False,
            created_at=datetime.utcnow()
        )

        # Mock the queries to return countries
        def mock_execute_side_effect(query):
            mock_result = MagicMock()
            # This is simplified - in reality we'd inspect the query
            mock_result.scalar_one_or_none.return_value = old_country if hasattr(query, '_old') else new_country
            mock_result.rowcount = 3  # 3 relationships updated
            return mock_result

        mock_session.execute.side_effect = mock_execute_side_effect

        repository = CountryRepository(mock_session)

        # Act
        updated_count = await repository.replace(old_country_id, new_country_id)

        # Assert
        assert updated_count == 3
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_replace_country_raises_error_for_non_existent_old_country(self):
        """
        Test that replace raises error when old country doesn't exist.

        Arrange: Mock session returning None for old country
        Act: Attempt to replace non-existent country
        Assert: Raises ValueError
        """
        # Arrange
        mock_session = AsyncMock()
        old_country_id = uuid4()
        new_country_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repository = CountryRepository(mock_session)

        # Act & Assert
        with pytest.raises(ValueError, match="Old country not found"):
            await repository.replace(old_country_id, new_country_id)

        mock_session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_replace_country_raises_error_for_non_existent_new_country(self):
        """
        Test that replace raises error when new country doesn't exist.

        Arrange: Mock session returning old country but None for new country
        Act: Attempt to replace with non-existent new country
        Assert: Raises ValueError
        """
        # Arrange
        mock_session = AsyncMock()
        old_country_id = uuid4()
        new_country_id = uuid4()

        old_country = Country(
            id=old_country_id,
            name="Soviet Union",
            code="SUN",
            is_deleted=True,
            created_at=datetime.utcnow()
        )

        call_count = 0

        def mock_execute_side_effect(query):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.scalar_one_or_none.return_value = old_country
            else:
                mock_result.scalar_one_or_none.return_value = None
            return mock_result

        mock_session.execute.side_effect = mock_execute_side_effect

        repository = CountryRepository(mock_session)

        # Act & Assert
        with pytest.raises(ValueError, match="New country not found"):
            await repository.replace(old_country_id, new_country_id)

        mock_session.commit.assert_not_awaited()
