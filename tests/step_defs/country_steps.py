"""
BDD step definitions for Country Management feature.

Maps Gherkin steps to Python code using pytest-bdd.
Uses integration testing with Testcontainers for real database operations.
"""

import pytest
from uuid import uuid4
from pytest_bdd import scenarios, given, when, then, parsers
from app.repositories.country_repository import CountryRepository
from app.services.country_service import CountryService
from app.models.country import Country
from app.exceptions import (
    CountryNotFoundError,
    DuplicateCountryCodeError,
    ValidationError
)


# Load all scenarios from the feature file
scenarios('../features/country_management.feature')


# ============================================================================
# GIVEN STEPS - Test Setup and Preconditions
# ============================================================================

@given('the database is empty')
async def database_is_empty(db_session):
    """
    Ensure database is empty.

    The db_session fixture already provides a clean database for each test.
    This step is more declarative for BDD readability.
    """
    # Database is already clean due to fixture's function scope
    pass


@given(parsers.parse('I have valid country data:\n{table}'),
       target_fixture='country_data')
def valid_country_data_from_table(table):
    """
    Parse valid country data from Gherkin table.

    Args:
        table: Multi-line string from Gherkin table

    Returns:
        dict: Parsed country data {"name": ..., "code": ...}
    """
    lines = [line.strip() for line in table.strip().split('\n')]
    # Parse header
    headers = [h.strip() for h in lines[0].split('|') if h.strip()]
    # Parse data row
    values = [v.strip() for v in lines[1].split('|') if v.strip()]

    return dict(zip(headers, values))


@given(parsers.parse('I have country data:\n{table}'),
       target_fixture='country_data')
def country_data_from_table(table):
    """
    Parse country data from Gherkin table (may be invalid).

    Same as valid_country_data_from_table but used for negative tests.
    """
    lines = [line.strip() for line in table.strip().split('\n')]
    headers = [h.strip() for h in lines[0].split('|') if h.strip()]
    values = [v.strip() for v in lines[1].split('|') if v.strip()]

    # Handle empty values
    data = {}
    for header, value in zip(headers, values):
        data[header] = value if value else ''  # Empty string for empty cells

    return data


@given(parsers.parse('I have country data with null name and code "{code}"'),
       target_fixture='country_data')
def country_data_with_null_name(code):
    """
    Create country data with null name.

    Args:
        code: ISO country code

    Returns:
        dict: Country data with name=None
    """
    return {"name": None, "code": code}


@given(parsers.parse('the following countries exist:\n{table}'),
       target_fixture='existing_countries')
async def create_countries_from_table(table, db_session, context):
    """
    Create multiple countries from Gherkin table.

    Args:
        table: Multi-line string from Gherkin table
        db_session: Database session fixture
        context: Shared context for storing created countries

    Returns:
        list[Country]: List of created countries
    """
    lines = [line.strip() for line in table.strip().split('\n')]
    headers = [h.strip() for h in lines[0].split('|') if h.strip()]

    repository = CountryRepository(db_session)
    service = CountryService(repository)

    countries = []
    country_lookup = {}  # Map name -> Country for later retrieval

    for line in lines[1:]:  # Skip header
        values = [v.strip() for v in line.split('|') if v.strip()]
        country_data = dict(zip(headers, values))

        country = await service.create(country_data)
        countries.append(country)
        country_lookup[country.name] = country

    # Store in context for other steps to access
    context['countries'] = country_lookup
    context['country_list'] = countries

    return countries


@given(parsers.parse('the country "{country_name}" has been deactivated'))
async def deactivate_country(country_name, db_session, context):
    """
    Deactivate a country by name.

    Args:
        country_name: Name of country to deactivate
        db_session: Database session
        context: Shared context containing countries

    Raises:
        KeyError: If country name not found in context
    """
    country = context['countries'][country_name]
    repository = CountryRepository(db_session)
    await repository.deactivate(country.id)


@given(parsers.parse('the country "{country_name}" has {count:d} team relationship'),
       target_fixture='team_relationship_count')
@given(parsers.parse('the country "{country_name}" has {count:d} team relationships'),
       target_fixture='team_relationship_count')
def country_has_team_relationships(country_name, count, context):
    """
    Stub for team relationship setup.

    This step requires Team entity implementation.

    Raises:
        NotImplementedError: Team entity not yet implemented
    """
    raise NotImplementedError(
        f"Setting up team relationships requires Team entity implementation. "
        f"Cannot create {count} team(s) for country '{country_name}'. "
        f"See Issue #33 and docs/domain/business-rules.md"
    )


@given(parsers.parse('the country "{country_name}" has no relationships'))
def country_has_no_relationships(country_name, context):
    """
    Mark country as having no relationships (validation only).

    This is a precondition check. Since Team entity doesn't exist,
    all countries have no relationships by default.
    """
    # No-op: all countries have 0 relationships until Team entity exists
    pass


# ============================================================================
# WHEN STEPS - Actions Under Test
# ============================================================================

@when('I create a country', target_fixture='create_result')
async def create_country(country_data, db_session, context):
    """
    Create a country using service layer.

    Args:
        country_data: Country data fixture
        db_session: Database session
        context: Shared context

    Returns:
        Country: Created country instance
    """
    repository = CountryRepository(db_session)
    service = CountryService(repository)

    try:
        country = await service.create(country_data)
        context['result'] = country
        context['error'] = None
        return country
    except Exception as e:
        context['result'] = None
        context['error'] = e
        return None


@when('I attempt to create a country', target_fixture='create_attempt_result')
async def attempt_create_country(country_data, db_session, context):
    """
    Attempt to create a country (expecting failure).

    Same as create_country but used in negative test scenarios.
    """
    return await create_country(country_data, db_session, context)


@when(parsers.parse('I retrieve the country "{country_name}" by ID'),
      target_fixture='retrieve_result')
async def retrieve_country_by_id(country_name, db_session, context):
    """
    Retrieve a country by its ID.

    Args:
        country_name: Name of country to retrieve (lookup in context)
        db_session: Database session
        context: Shared context

    Returns:
        Country | None: Retrieved country or None
    """
    country = context['countries'][country_name]
    repository = CountryRepository(db_session)
    service = CountryService(repository)

    try:
        result = await service.get_by_id(country.id)
        context['result'] = result
        context['error'] = None
        return result
    except Exception as e:
        context['result'] = None
        context['error'] = e
        return None


@when('I retrieve a country by a random UUID', target_fixture='retrieve_random_result')
async def retrieve_by_random_uuid(db_session, context):
    """
    Attempt to retrieve country by non-existent UUID.

    Args:
        db_session: Database session
        context: Shared context

    Returns:
        None (country doesn't exist)
    """
    random_id = uuid4()
    repository = CountryRepository(db_session)
    service = CountryService(repository)

    try:
        result = await service.get_by_id(random_id)
        context['result'] = result
        context['error'] = None
        return result
    except Exception as e:
        context['result'] = None
        context['error'] = e
        return None


@when(parsers.parse('I retrieve the country by code "{code}"'),
      target_fixture='retrieve_by_code_result')
async def retrieve_country_by_code(code, db_session, context):
    """
    Retrieve a country by ISO code.

    Args:
        code: ISO 3166-1 alpha-3 code
        db_session: Database session
        context: Shared context

    Returns:
        Country | None: Retrieved country or None
    """
    repository = CountryRepository(db_session)
    service = CountryService(repository)

    try:
        result = await service.get_by_code(code)
        context['result'] = result
        context['error'] = None
        return result
    except Exception as e:
        context['result'] = None
        context['error'] = e
        return None


@when('I request the list of all countries', target_fixture='list_result')
@when('I request the list of all countries as a regular user', target_fixture='list_result')
async def list_all_countries(db_session, context):
    """
    List all active countries (regular user context).

    Args:
        db_session: Database session
        context: Shared context

    Returns:
        list[Country]: List of active countries
    """
    repository = CountryRepository(db_session)
    service = CountryService(repository)

    try:
        result = await service.list_all(include_deactivated=False)
        context['result'] = result
        context['error'] = None
        return result
    except Exception as e:
        context['result'] = None
        context['error'] = e
        return None


@when('I request the list of all countries as an admin', target_fixture='list_admin_result')
async def list_all_countries_as_admin(db_session, context):
    """
    List all countries including soft-deleted (admin context).

    Args:
        db_session: Database session
        context: Shared context

    Returns:
        list[Country]: List of all countries
    """
    repository = CountryRepository(db_session)
    service = CountryService(repository)

    try:
        result = await service.list_all(include_deactivated=True)
        context['result'] = result
        context['error'] = None
        return result
    except Exception as e:
        context['result'] = None
        context['error'] = e
        return None


@when(parsers.parse('I retrieve the country "{country_name}" by ID as a regular user'),
      target_fixture='retrieve_as_user_result')
async def retrieve_by_id_as_regular_user(country_name, db_session, context):
    """
    Retrieve country by ID as regular user (excludes soft-deleted).

    Args:
        country_name: Name of country to retrieve
        db_session: Database session
        context: Shared context

    Returns:
        Country | None: Retrieved country or None
    """
    country = context['countries'][country_name]
    repository = CountryRepository(db_session)
    service = CountryService(repository)

    try:
        result = await service.get_by_id(country.id, include_deactivated=False)
        context['result'] = result
        context['error'] = None
        return result
    except Exception as e:
        context['result'] = None
        context['error'] = e
        return None


@when(parsers.parse('I retrieve the country "{country_name}" by ID as an admin'),
      target_fixture='retrieve_as_admin_result')
async def retrieve_by_id_as_admin(country_name, db_session, context):
    """
    Retrieve country by ID as admin (includes soft-deleted).

    Args:
        country_name: Name of country to retrieve
        db_session: Database session
        context: Shared context

    Returns:
        Country | None: Retrieved country or None
    """
    country = context['countries'][country_name]
    repository = CountryRepository(db_session)
    service = CountryService(repository)

    try:
        result = await service.get_by_id(country.id, include_deactivated=True)
        context['result'] = result
        context['error'] = None
        return result
    except Exception as e:
        context['result'] = None
        context['error'] = e
        return None


@when(parsers.parse('I retrieve the country by code "{code}" as a regular user'),
      target_fixture='retrieve_by_code_as_user_result')
async def retrieve_by_code_as_regular_user(code, db_session, context):
    """
    Retrieve country by code as regular user.

    Args:
        code: ISO code
        db_session: Database session
        context: Shared context

    Returns:
        Country | None
    """
    repository = CountryRepository(db_session)
    service = CountryService(repository)

    try:
        result = await service.get_by_code(code, include_deactivated=False)
        context['result'] = result
        context['error'] = None
        return result
    except Exception as e:
        context['result'] = None
        context['error'] = e
        return None


@when(parsers.parse('I delete the country "{country_name}"'),
      target_fixture='delete_result')
async def delete_country(country_name, db_session, context):
    """
    Deactivate a country.

    Args:
        country_name: Name of country to delete
        db_session: Database session
        context: Shared context

    Returns:
        None (successful deletion)
    """
    country = context['countries'][country_name]
    repository = CountryRepository(db_session)
    service = CountryService(repository)

    try:
        await service.delete(country.id)
        context['result'] = True
        context['error'] = None
        return True
    except Exception as e:
        context['result'] = None
        context['error'] = e
        return None


@when(parsers.parse('I update the country "{country_name}" with new data'),
      target_fixture='update_result')
async def update_country(country_name, country_data, db_session, context):
    """
    Update a country with new data.

    Args:
        country_name: Name of country to update
        country_data: New country data
        db_session: Database session
        context: Shared context

    Returns:
        Country: Updated country
    """
    country = context['countries'][country_name]
    repository = CountryRepository(db_session)
    service = CountryService(repository)

    try:
        result = await service.update(country.id, country_data)
        context['result'] = result
        context['error'] = None
        return result
    except Exception as e:
        context['result'] = None
        context['error'] = e
        return None


@when(parsers.parse('I attempt to update the country "{country_name}" with new data'),
      target_fixture='update_attempt_result')
async def attempt_update_country(country_name, country_data, db_session, context):
    """
    Attempt to update country (expecting failure).

    Same as update_country but for negative tests.
    """
    return await update_country(country_name, country_data, db_session, context)


@when(parsers.parse('I permanently delete the country "{country_name}" as an admin'),
      target_fixture='permanent_delete_result')
@when(parsers.parse('I attempt to permanently delete the country "{country_name}" as an admin'),
      target_fixture='permanent_delete_result')
async def permanently_delete_country_as_admin(country_name, db_session, context):
    """
    Permanently delete a country (admin action).

    This requires Team entity for relationship checking.

    Raises:
        NotImplementedError: Team entity not implemented
    """
    country = context['countries'][country_name]
    repository = CountryRepository(db_session)
    service = CountryService(repository)

    try:
        await service.permanent_delete(country.id)
        context['result'] = True
        context['error'] = None
        return True
    except Exception as e:
        context['result'] = None
        context['error'] = e
        return None


@when(parsers.parse('I replace the country "{old_name}" with "{new_name}" as an admin'),
      target_fixture='replace_result')
async def replace_country_as_admin(old_name, new_name, db_session, context):
    """
    Replace old country with new country (admin action).

    This requires Team entity for transferring relationships.

    Raises:
        NotImplementedError: Team entity not implemented
    """
    old_country = context['countries'][old_name]
    new_country = context['countries'][new_name]

    repository = CountryRepository(db_session)
    service = CountryService(repository)

    try:
        await service.replace(old_country.id, new_country.id)
        context['result'] = True
        context['error'] = None
        return True
    except Exception as e:
        context['result'] = None
        context['error'] = e
        return None


# ============================================================================
# THEN STEPS - Assertions and Verification
# ============================================================================

@then('the country is created successfully')
def country_created_successfully(context):
    """Assert country was created without errors."""
    assert context.get('error') is None, f"Expected no error, but got: {context.get('error')}"
    assert context.get('result') is not None, "Expected country to be created"


@then('the country has a unique ID')
def country_has_unique_id(context):
    """Assert country has a UUID."""
    country = context['result']
    assert country.id is not None
    assert isinstance(country.id, type(uuid4()))


@then(parsers.parse('the country has the name "{expected_name}"'))
def country_has_name(expected_name, context):
    """Assert country has expected name."""
    country = context['result']
    assert country.name == expected_name


@then(parsers.parse('the country has the code "{expected_code}"'))
def country_has_code(expected_code, context):
    """Assert country has expected code."""
    country = context['result']
    assert country.code == expected_code


@then('the country is not deleted')
def country_is_not_deleted(context):
    """Assert country is_deactivated flag is False."""
    country = context['result']
    assert country.is_deactivated is False


@then('the country is marked as deleted')
def country_is_marked_deleted(context):
    """Assert country is_deactivated flag is True."""
    country = context['result']
    assert country.is_deactivated is True


@then('the country has a creation timestamp')
def country_has_timestamp(context):
    """Assert country has created_at timestamp."""
    country = context['result']
    assert country.created_at is not None


@then('I receive the country details')
def receive_country_details(context):
    """Assert country details were retrieved."""
    assert context.get('result') is not None
    assert isinstance(context.get('result'), Country)


@then(parsers.parse('I receive a list of {count:d} countries'))
def receive_country_list(count, context):
    """Assert list contains expected number of countries."""
    result = context['result']
    assert isinstance(result, list)
    assert len(result) == count


@then(parsers.parse('the list contains a country with code "{code}"'))
def list_contains_code(code, context):
    """Assert list contains country with specified code."""
    countries = context['result']
    codes = {c.code for c in countries}
    assert code in codes, f"Expected code '{code}' in {codes}"


@then(parsers.parse('the list does not contain a country with code "{code}"'))
def list_does_not_contain_code(code, context):
    """Assert list does not contain country with specified code."""
    countries = context['result']
    codes = {c.code for c in countries}
    assert code not in codes, f"Did not expect code '{code}' in {codes}"


@then('the request is rejected')
def request_is_rejected(context):
    """Assert request failed with an error."""
    assert context.get('error') is not None, "Expected an error but none was raised"


@then(parsers.parse('I receive an error message "{expected_message}"'))
def receive_error_message(expected_message, context):
    """Assert error message matches expected."""
    error = context.get('error')
    assert error is not None
    assert expected_message in str(error), f"Expected '{expected_message}' in error: {error}"


@then('I receive a validation error indicating name is required')
def validation_error_name_required(context):
    """Assert validation error for missing name."""
    error = context.get('error')
    assert isinstance(error, ValidationError)
    assert 'name' in str(error).lower()


@then('I receive a validation error indicating code must be 3 uppercase letters')
def validation_error_code_format(context):
    """Assert validation error for invalid code format."""
    error = context.get('error')
    assert isinstance(error, ValidationError)
    assert '3 uppercase letters' in str(error) or 'invalid iso' in str(error).lower()


@then('I receive a validation error indicating code must be a valid ISO 3166-1 alpha-3 code')
def validation_error_invalid_iso_code(context):
    """Assert validation error for invalid ISO code."""
    error = context.get('error')
    assert isinstance(error, ValidationError)
    assert 'iso' in str(error).lower() or 'valid country code' in str(error).lower()


@then(parsers.parse('the request fails with status {status_code:d}'))
def request_fails_with_status(status_code, context):
    """
    Assert request failed with HTTP status code.

    Note: This step is for API layer testing. We're testing service layer,
    so we verify the appropriate exception was raised instead.
    """
    error = context.get('error')
    assert error is not None

    # Map status codes to expected exceptions
    if status_code == 404:
        assert isinstance(error, CountryNotFoundError)
    elif status_code == 400:
        assert isinstance(error, (ValidationError, DuplicateCountryCodeError))
    else:
        raise NotImplementedError(f"Status code {status_code} mapping not implemented")


@then('the deletion is successful')
def deletion_successful(context):
    """Assert deletion completed without error."""
    assert context.get('error') is None
    assert context.get('result') is not None


@then(parsers.parse('the country "{country_name}" is marked as deleted in the database'))
async def country_marked_deleted_in_db(country_name, db_session, context):
    """Assert country is marked as deleted in database."""
    country = context['countries'][country_name]
    repository = CountryRepository(db_session)

    # Retrieve with include_deactivated=True
    retrieved = await repository.get_by_id(country.id, include_deactivated=True)
    assert retrieved is not None
    assert retrieved.is_deactivated is True


@then(parsers.parse('the country "{country_name}" is not removed from the database'))
async def country_not_removed_from_db(country_name, db_session, context):
    """Assert country still exists in database (deactivate, not hard delete)."""
    country = context['countries'][country_name]
    repository = CountryRepository(db_session)

    # Should exist with include_deactivated=True
    retrieved = await repository.get_by_id(country.id, include_deactivated=True)
    assert retrieved is not None


@then(parsers.parse('the country "{country_name}" is permanently removed from the database'))
async def country_permanently_removed(country_name, db_session, context):
    """Assert country no longer exists in database."""
    country = context['countries'][country_name]
    repository = CountryRepository(db_session)

    # Should not exist even with include_deactivated=True
    retrieved = await repository.get_by_id(country.id, include_deactivated=True)
    assert retrieved is None


@then('the update is successful')
def update_successful(context):
    """Assert update completed without error."""
    assert context.get('error') is None
    assert context.get('result') is not None


@then('the replacement is successful')
def replacement_successful(context):
    """Assert replacement completed without error."""
    assert context.get('error') is None


@then(parsers.parse('the country "{country_name}" has {count:d} team relationship'))
@then(parsers.parse('the country "{country_name}" has {count:d} team relationships'))
async def verify_team_relationship_count(country_name, count, db_session, context):
    """
    Verify country has expected number of team relationships.

    This requires Team entity implementation.

    Raises:
        NotImplementedError: Team entity not implemented
    """
    raise NotImplementedError(
        f"Verifying team relationships requires Team entity implementation. "
        f"Cannot verify that '{country_name}' has {count} relationship(s). "
        f"See Issue #33 and docs/domain/business-rules.md"
    )
