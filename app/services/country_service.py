"""
Service layer for Country business logic.

Implements business rules and validation for Country operations.
"""

from typing import Dict, Any
from uuid import UUID
import re
import pycountry
from sqlalchemy.exc import IntegrityError
from app.models.country import Country
from app.repositories.country_repository import CountryRepository
from app.exceptions import (
    CountryNotFoundError,
    DuplicateCountryCodeError,
    ValidationError
)


class CountryService:
    """
    Business logic layer for Country operations.

    Handles validation, business rules, and delegates data access to repository.
    """

    # Valid ISO 3166-1 alpha-3 country codes
    VALID_ISO_CODES = {country.alpha_3 for country in pycountry.countries}

    def __init__(self, repository: CountryRepository):
        """
        Initialize service with repository.

        Args:
            repository: CountryRepository instance for data access
        """
        self.repository = repository

    def _validate_country_data(self, data: Dict[str, Any]) -> None:
        """
        Validate country data fields.

        Args:
            data: Dictionary with country fields

        Raises:
            ValidationError: If validation fails
        """
        # Validate name
        if 'name' in data:
            name = data.get('name', '').strip()
            if not name:
                raise ValidationError("name is required")

        # Validate code format
        if 'code' in data:
            code = data.get('code', '')
            if not re.match(r'^[A-Z]{3}$', code):
                raise ValidationError("Code must be 3 uppercase letters")

            # Validate against ISO 3166-1 alpha-3 standard
            if code not in self.VALID_ISO_CODES:
                raise ValidationError("Code must be a valid ISO 3166-1 alpha-3 code")

    async def create(self, country_data: Dict[str, Any]) -> Country:
        """
        Create a new country with validation.

        Args:
            country_data: Dictionary with country fields (name, code)

        Returns:
            Created Country instance

        Raises:
            ValidationError: If validation fails
            DuplicateCountryCodeError: If code already exists for active country
        """
        # Validate input
        self._validate_country_data(country_data)

        # Check for duplicate code (only among active countries)
        code = country_data.get('code')
        existing_country = await self.repository.get_by_code(code, include_deactivated=False)
        if existing_country:
            raise DuplicateCountryCodeError(code)

        # Create country
        try:
            return await self.repository.create(country_data)
        except IntegrityError:
            raise DuplicateCountryCodeError(code)

    async def get_by_id(self, country_id: UUID, include_deactivated: bool = False) -> Country:
        """
        Retrieve a country by ID.

        Args:
            country_id: UUID of the country
            include_deactivated: If True, include soft-deleted countries

        Returns:
            Country instance

        Raises:
            CountryNotFoundError: If country not found
        """
        country = await self.repository.get_by_id(country_id, include_deactivated=include_deactivated)
        if country is None:
            raise CountryNotFoundError()

        return country

    async def get_by_code(self, code: str, include_deactivated: bool = False) -> Country | None:
        """
        Retrieve a country by ISO code.

        Args:
            code: ISO 3166-1 alpha-3 country code

        Returns:
            Country instance or None if not found
        """
        return await self.repository.get_by_code(code, include_deactivated=include_deactivated)

    async def list_all(self, include_deactivated: bool = False) -> list[Country]:
        """
        List all countries.

        Args:
            include_deactivated: If True, include soft-deleted countries

        Returns:
            List of Country instances
        """
        return await self.repository.list_all(include_deactivated=include_deactivated)

    async def delete(self, country_id: UUID) -> None:
        """
        Soft delete a country.

        Args:
            country_id: UUID of the country to delete

        Raises:
            CountryNotFoundError: If country not found
        """
        try:
            await self.repository.deactivate(country_id)
        except ValueError as e:
            raise CountryNotFoundError(str(e))

    async def update(self, country_id: UUID, update_data: Dict[str, Any], include_deactivated: bool = False) -> Country:
        """
        Update a country with validation.

        Args:
            country_id: UUID of the country to update
            update_data: Dictionary with fields to update

        Returns:
            Updated Country instance

        Raises:
            ValidationError: If validation fails
            CountryNotFoundError: If country not found
            DuplicateCountryCodeError: If code update creates duplicate
        """
        # Validate update data
        self._validate_country_data(update_data)

        # Update country
        try:
            return await self.repository.update(country_id, update_data, include_deactivated=include_deactivated)
        except ValueError as e:
            raise CountryNotFoundError(str(e))
        except IntegrityError:
            code = update_data.get('code', 'unknown')
            raise DuplicateCountryCodeError(code)

    async def permanent_delete(self, country_id: UUID) -> None:
        """
        Permanently delete a country after checking for relationships.

        Args:
            country_id: UUID of the country to delete

        Raises:
            CountryNotFoundError: If country not found
            ValidationError: If country has relationships
            NotImplementedError: Team entity not yet implemented
        """
        # Validate country exists
        country = await self.repository.get_by_id(country_id, include_deactivated=True)
        if country is None:
            raise CountryNotFoundError("Country not found")

        # Check for team relationships
        relationship_count = await self.repository.count_relationships(country_id)
        if relationship_count > 0:
            raise ValidationError(
                "Cannot permanently delete country with existing relationships"
            )

        # Permanently delete country
        try:
            await self.repository.permanent_delete(country_id)
        except ValueError as e:
            raise CountryNotFoundError(str(e))

    async def replace(self, old_country_id: UUID, new_country_id: UUID) -> int:
        """
        Replace old country with new country in all relationships.

        Args:
            old_country_id: UUID of country to replace
            new_country_id: UUID of replacement country

        Returns:
            Number of relationships updated

        Raises:
            CountryNotFoundError: If either country not found
        """
        try:
            return await self.repository.replace(old_country_id, new_country_id)
        except ValueError as e:
            error_message = str(e)
            if "Old country" in error_message:
                raise CountryNotFoundError("Old country not found")
            elif "New country" in error_message:
                raise CountryNotFoundError("New country not found")
            else:
                raise CountryNotFoundError(error_message)
