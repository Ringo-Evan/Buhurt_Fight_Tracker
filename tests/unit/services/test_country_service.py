"""
Unit tests for CountryService.

Tests the business logic layer for Country entity operations with mocked CountryRepository.
Following TDD approach - these tests are written before implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, UTC

# These imports will fail until implementation exists - that's expected in TDD
from app.services.country_service import CountryService
from app.repositories.country_repository import CountryRepository
from app.models.country import Country
from app.exceptions import (
    CountryNotFoundError,
    DuplicateCountryCodeError,
    ValidationError
)


class TestCountryServiceCreate:
    """Test suite for country creation business logic."""

    @pytest.mark.asyncio
    async def test_create_country_with_valid_data_succeeds(self):
        """
        Test that creating a country with valid data succeeds (happy path).

        Arrange: Mock repository with no existing conflicts
        Act: Call service.create() with valid data
        Assert: Repository create called and country returned
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        country_data = {
            "name": "Czech Republic",
            "code": "CZE"
        }

        expected_country = Country(
            id=uuid4(),
            name="Czech Republic",
            code="CZE",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_repository.get_by_code.return_value = None  # No existing country
        mock_repository.create.return_value = expected_country

        # Act
        result = await service.create(country_data)

        # Assert
        assert result == expected_country
        assert result.name == "Czech Republic"
        assert result.code == "CZE"
        mock_repository.get_by_code.assert_awaited_once_with("CZE", include_deleted=False)
        mock_repository.create.assert_awaited_once_with(country_data)

    @pytest.mark.asyncio
    async def test_create_country_rejects_duplicate_active_code(self):
        """
        Test that creating a country with duplicate active code is rejected.

        Arrange: Mock repository returning existing active country with same code
        Act: Attempt to create country with duplicate code
        Assert: DuplicateCountryCodeError raised
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        country_data = {
            "name": "Czechia",
            "code": "CZE"
        }

        existing_country = Country(
            id=uuid4(),
            name="Czech Republic",
            code="CZE",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_repository.get_by_code.return_value = existing_country

        # Act & Assert
        with pytest.raises(DuplicateCountryCodeError, match="Country with code CZE already exists"):
            await service.create(country_data)

        mock_repository.get_by_code.assert_awaited_once_with("CZE", include_deleted=False)
        mock_repository.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_country_allows_code_reuse_for_deleted_countries(self):
        """
        Test that country code can be reused if previous country is soft-deleted.

        Arrange: Mock repository returning None (deleted countries are filtered out by repository)
        Act: Create new country with same code
        Assert: Creation succeeds
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        country_data = {
            "name": "Czechia",
            "code": "CZE"
        }

        new_country = Country(
            id=uuid4(),
            name="Czechia",
            code="CZE",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        # Repository filters out deleted countries, so get_by_code returns None
        mock_repository.get_by_code.return_value = None
        mock_repository.create.return_value = new_country

        # Act
        result = await service.create(country_data)

        # Assert
        assert result == new_country
        assert result.name == "Czechia"
        mock_repository.create.assert_awaited_once_with(country_data)

    @pytest.mark.asyncio
    async def test_create_country_rejects_empty_name(self):
        """
        Test that creating a country with empty name is rejected.

        Arrange: Mock repository and prepare data with empty name
        Act: Attempt to create country with empty name
        Assert: ValidationError raised
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        country_data = {
            "name": "",
            "code": "CZE"
        }

        # Act & Assert
        with pytest.raises(ValidationError, match="name is required"):
            await service.create(country_data)

        mock_repository.get_by_code.assert_not_awaited()
        mock_repository.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_country_validates_iso_code_format(self):
        """
        Test that country code must match ISO 3166-1 alpha-3 format.

        Arrange: Mock repository and prepare data with invalid code formats
        Act: Attempt to create country with invalid codes
        Assert: ValidationError raised for each invalid format
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        invalid_codes = [
            ("cze", "must be 3 uppercase letters"),  # lowercase
            ("CZ", "must be 3 uppercase letters"),   # too short
            ("CZEE", "must be 3 uppercase letters"), # too long
            ("CZ1", "must be 3 uppercase letters"),  # contains number
            ("NAR", "must be a valid ISO 3166-1 alpha-3 code")  # not a real country
        ]

        for invalid_code, expected_message in invalid_codes:
            country_data = {
                "name": "Test Country",
                "code": invalid_code
            }

            # Act & Assert
            with pytest.raises(ValidationError, match=expected_message):
                await service.create(country_data)

        mock_repository.create.assert_not_awaited()


class TestCountryServiceRetrieve:
    """Test suite for country retrieval business logic."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_country_when_exists(self):
        """
        Test successful retrieval of country by ID.

        Arrange: Mock repository returning country
        Act: Call service.get_by_id()
        Assert: Returns country object
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        country_id = uuid4()
        expected_country = Country(
            id=country_id,
            name="Czech Republic",
            code="CZE",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_repository.get_by_id.return_value = expected_country

        # Act
        result = await service.get_by_id(country_id)

        # Assert
        assert result == expected_country
        assert result.id == country_id
        mock_repository.get_by_id.assert_awaited_once_with(country_id, include_deleted=False)

    @pytest.mark.asyncio
    async def test_get_by_id_raises_not_found_error_when_not_exists(self):
        """
        Test that get_by_id raises CountryNotFoundError for non-existent country.

        Arrange: Mock repository returning None
        Act: Call service.get_by_id()
        Assert: CountryNotFoundError raised
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        country_id = uuid4()
        mock_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(CountryNotFoundError, match="Country not found"):
            await service.get_by_id(country_id)

        mock_repository.get_by_id.assert_awaited_once_with(country_id, include_deleted=False)

    @pytest.mark.asyncio
    async def test_get_by_code_returns_country_when_exists(self):
        """
        Test successful retrieval of country by ISO code.

        Arrange: Mock repository returning country
        Act: Call service.get_by_code()
        Assert: Returns country object
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        expected_country = Country(
            id=uuid4(),
            name="Czech Republic",
            code="CZE",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_repository.get_by_code.return_value = expected_country

        # Act
        result = await service.get_by_code("CZE")

        # Assert
        assert result == expected_country
        assert result.code == "CZE"
        mock_repository.get_by_code.assert_awaited_once_with("CZE", include_deleted=False)


class TestCountryServiceDelete:
    """Test suite for country deletion business logic."""

    @pytest.mark.asyncio
    async def test_delete_country_delegates_to_repository(self):
        """
        Test that delete operation delegates to repository soft_delete.

        Arrange: Mock repository
        Act: Call service.delete()
        Assert: Repository soft_delete called with correct ID
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        country_id = uuid4()
        mock_repository.soft_delete.return_value = None

        # Act
        await service.delete(country_id)

        # Assert
        mock_repository.soft_delete.assert_awaited_once_with(country_id)

    @pytest.mark.asyncio
    async def test_delete_country_handles_non_existent_country(self):
        """
        Test that delete raises error for non-existent country.

        Arrange: Mock repository raising ValueError
        Act: Call service.delete() with non-existent ID
        Assert: CountryNotFoundError raised
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        country_id = uuid4()
        mock_repository.soft_delete.side_effect = ValueError("Country not found")

        # Act & Assert
        with pytest.raises(CountryNotFoundError, match="Country not found"):
            await service.delete(country_id)

        mock_repository.soft_delete.assert_awaited_once_with(country_id)


class TestCountryServiceUpdate:
    """Test suite for country update business logic."""

    @pytest.mark.asyncio
    async def test_update_country_name_succeeds(self):
        """
        Test that updating a country's name with valid data succeeds.

        Arrange: Mock repository with no existing conflicts
        Act: Call service.update() with new name
        Assert: Repository update called and updated country returned
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        country_id = uuid4()
        update_data = {"name": "Czechia"}

        updated_country = Country(
            id=country_id,
            name="Czechia",
            code="CZE",
            is_deleted=False,
            created_at=datetime.now(UTC)
        )

        mock_repository.update.return_value = updated_country

        # Act
        result = await service.update(country_id, update_data)

        # Assert
        assert result == updated_country
        assert result.name == "Czechia"
        mock_repository.update.assert_awaited_once_with(country_id, update_data)

    @pytest.mark.asyncio
    async def test_update_country_code_validates_format(self):
        """
        Test that updating country code validates ISO format.

        Arrange: Mock repository
        Act: Attempt to update with invalid code
        Assert: ValidationError raised before repository call
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        country_id = uuid4()
        update_data = {"code": "cze"}  # lowercase - invalid

        # Act & Assert
        with pytest.raises(ValidationError, match="must be 3 uppercase letters"):
            await service.update(country_id, update_data)

        mock_repository.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_country_rejects_duplicate_code(self):
        """
        Test that updating to duplicate code is rejected.

        Arrange: Mock repository raising IntegrityError
        Act: Attempt to update with duplicate code
        Assert: DuplicateCountryCodeError raised
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        country_id = uuid4()
        update_data = {"code": "POL"}

        from sqlalchemy.exc import IntegrityError
        mock_repository.update.side_effect = IntegrityError(
            statement="UPDATE countries...",
            params={},
            orig=Exception("duplicate key value violates unique constraint")
        )

        # Act & Assert
        with pytest.raises(DuplicateCountryCodeError, match="Country with code POL already exists"):
            await service.update(country_id, update_data)

        mock_repository.update.assert_awaited_once_with(country_id, update_data)

    @pytest.mark.asyncio
    async def test_update_country_rejects_empty_name(self):
        """
        Test that updating to empty name is rejected.

        Arrange: Mock repository
        Act: Attempt to update with empty name
        Assert: ValidationError raised
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        country_id = uuid4()
        update_data = {"name": ""}

        # Act & Assert
        with pytest.raises(ValidationError, match="name is required"):
            await service.update(country_id, update_data)

        mock_repository.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_country_handles_non_existent_country(self):
        """
        Test that update raises error for non-existent country.

        Arrange: Mock repository raising ValueError
        Act: Attempt to update non-existent country
        Assert: CountryNotFoundError raised
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        country_id = uuid4()
        update_data = {"name": "New Name"}

        mock_repository.update.side_effect = ValueError("Country not found")

        # Act & Assert
        with pytest.raises(CountryNotFoundError, match="Country not found"):
            await service.update(country_id, update_data)

        mock_repository.update.assert_awaited_once_with(country_id, update_data)


class TestCountryServiceAdminAccess:
    """Test suite for admin-specific country operations."""

    @pytest.mark.asyncio
    async def test_get_by_id_as_admin_returns_deleted_country(self):
        """
        Test that admin can retrieve soft-deleted countries.

        Arrange: Mock repository with include_deleted flag
        Act: Call service.get_by_id(include_deleted=True)
        Assert: Returns deleted country
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        country_id = uuid4()
        deleted_country = Country(
            id=country_id,
            name="Czech Republic",
            code="CZE",
            is_deleted=True,
            created_at=datetime.now(UTC)
        )

        mock_repository.get_by_id.return_value = deleted_country

        # Act
        result = await service.get_by_id(country_id, include_deleted=True)

        # Assert
        assert result == deleted_country
        assert result.is_deleted is True
        mock_repository.get_by_id.assert_awaited_once_with(country_id, include_deleted=True)

    @pytest.mark.asyncio
    async def test_list_all_as_admin_includes_deleted_countries(self):
        """
        Test that admin can list all countries including deleted ones.

        Arrange: Mock repository returning active and deleted countries
        Act: Call service.list_all(include_deleted=True)
        Assert: Returns all countries including deleted
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        all_countries = [
            Country(
                id=uuid4(),
                name="Czech Republic",
                code="CZE",
                is_deleted=False,
                created_at=datetime.now(UTC)
            ),
            Country(
                id=uuid4(),
                name="Poland",
                code="POL",
                is_deleted=True,
                created_at=datetime.now(UTC)
            )
        ]

        mock_repository.list_all.return_value = all_countries

        # Act
        result = await service.list_all(include_deleted=True)

        # Assert
        assert len(result) == 2
        assert any(c.is_deleted for c in result)
        mock_repository.list_all.assert_awaited_once_with(include_deleted=True)


class TestCountryServicePermanentDelete:
    """Test suite for permanent deletion business logic."""

    @pytest.mark.asyncio
    async def test_permanent_delete_succeeds_when_no_relationships(self):
        """
        Test that permanent delete succeeds when country has no relationships.

        Arrange: Mock repository with 0 relationship count
        Act: Call service.permanent_delete()
        Assert: Repository permanent_delete called
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        country_id = uuid4()
        mock_repository.count_relationships.return_value = 0
        mock_repository.permanent_delete.return_value = None

        # Act
        await service.permanent_delete(country_id)

        # Assert
        mock_repository.count_relationships.assert_awaited_once_with(country_id)
        mock_repository.permanent_delete.assert_awaited_once_with(country_id)

    @pytest.mark.asyncio
    async def test_permanent_delete_rejects_country_with_relationships(self):
        """
        Test that permanent delete fails when country has relationships.

        Arrange: Mock repository with non-zero relationship count
        Act: Attempt to permanently delete country with relationships
        Assert: ValidationError raised, permanent_delete not called
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        country_id = uuid4()
        mock_repository.count_relationships.return_value = 3  # Has relationships

        # Act & Assert
        with pytest.raises(ValidationError, match="Cannot permanently delete country with existing relationships"):
            await service.permanent_delete(country_id)

        mock_repository.count_relationships.assert_awaited_once_with(country_id)
        mock_repository.permanent_delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_permanent_delete_handles_non_existent_country(self):
        """
        Test that permanent delete raises error for non-existent country.

        Arrange: Mock repository raising ValueError
        Act: Attempt to permanently delete non-existent country
        Assert: CountryNotFoundError raised
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        country_id = uuid4()
        mock_repository.count_relationships.return_value = 0
        mock_repository.permanent_delete.side_effect = ValueError("Country not found")

        # Act & Assert
        with pytest.raises(CountryNotFoundError, match="Country not found"):
            await service.permanent_delete(country_id)

        mock_repository.permanent_delete.assert_awaited_once_with(country_id)


class TestCountryServiceReplace:
    """Test suite for country replacement business logic."""

    @pytest.mark.asyncio
    async def test_replace_country_transfers_relationships(self):
        """
        Test that replace successfully transfers all relationships.

        Arrange: Mock repository returning successful replacement count
        Act: Call service.replace()
        Assert: Repository replace called and count returned
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        old_country_id = uuid4()
        new_country_id = uuid4()
        mock_repository.replace.return_value = 3  # 3 relationships transferred

        # Act
        result = await service.replace(old_country_id, new_country_id)

        # Assert
        assert result == 3
        mock_repository.replace.assert_awaited_once_with(old_country_id, new_country_id)

    @pytest.mark.asyncio
    async def test_replace_country_handles_non_existent_old_country(self):
        """
        Test that replace raises error when old country doesn't exist.

        Arrange: Mock repository raising ValueError for old country
        Act: Attempt to replace non-existent old country
        Assert: CountryNotFoundError raised
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        old_country_id = uuid4()
        new_country_id = uuid4()
        mock_repository.replace.side_effect = ValueError("Old country not found")

        # Act & Assert
        with pytest.raises(CountryNotFoundError, match="Old country not found"):
            await service.replace(old_country_id, new_country_id)

        mock_repository.replace.assert_awaited_once_with(old_country_id, new_country_id)

    @pytest.mark.asyncio
    async def test_replace_country_handles_non_existent_new_country(self):
        """
        Test that replace raises error when new country doesn't exist.

        Arrange: Mock repository raising ValueError for new country
        Act: Attempt to replace with non-existent new country
        Assert: CountryNotFoundError raised
        """
        # Arrange
        mock_repository = AsyncMock(spec=CountryRepository)
        service = CountryService(mock_repository)

        old_country_id = uuid4()
        new_country_id = uuid4()
        mock_repository.replace.side_effect = ValueError("New country not found")

        # Act & Assert
        with pytest.raises(CountryNotFoundError, match="New country not found"):
            await service.replace(old_country_id, new_country_id)

        mock_repository.replace.assert_awaited_once_with(old_country_id, new_country_id)
