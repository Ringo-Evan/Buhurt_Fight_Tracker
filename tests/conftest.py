"""
Pytest fixtures for testing.

Provides fixtures for unit tests (mocks) and integration tests (Testcontainers).
"""

import pytest
import pytest_asyncio
from uuid import uuid4, UUID
from datetime import datetime, UTC
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sa

# Import all models to ensure proper relationship resolution
# This must be done before Base.metadata.create_all() is called
from app.models import (  # noqa: F401
    Base,
    Country,
    Team,
    Fighter,
    Fight,
    FightParticipation,
    TagType,
    Tag,
    TagChangeRequest,
    Vote
)


# ============================================================================
# TESTCONTAINERS FIXTURES (Integration Tests)
# ============================================================================

@pytest.fixture(scope="session")
def postgres_container():
    """
    Session-scoped PostgreSQL container.

    - Starts once for entire test session
    - Shared across all integration tests
    - Automatically destroyed when tests complete

    Requires Docker Desktop to be running!

    Returns:
        PostgresContainer: Running PostgreSQL 16 container
    """
    with PostgresContainer("postgres:16", driver=None) as postgres:
        yield postgres


@pytest_asyncio.fixture(scope="function")
async def db_engine(postgres_container):
    """
    Function-scoped async database engine.

    - Creates new engine for each test function
    - Ensures test isolation (fresh schema per test)
    - Creates all tables before test, drops after

    Args:
        postgres_container: Session-scoped container from postgres_container fixture

    Returns:
        AsyncEngine: SQLAlchemy async engine connected to test database
    """
    # Get connection URL from container
    connection_url = postgres_container.get_connection_url()

    # Convert to asyncpg URL for async operations
    # Testcontainers may return "postgresql://..." or "postgresql+psycopg2://..."
    # We need "postgresql+asyncpg://..." for SQLAlchemy async
    if "+psycopg2" in connection_url:
        async_url = connection_url.replace("psycopg2", "asyncpg")
    elif connection_url.startswith("postgresql://"):
        async_url = connection_url.replace("postgresql://", "postgresql+asyncpg://")
    else:
        async_url = connection_url

    # Create async engine
    engine = create_async_engine(
        async_url,
        echo=False,  # Set to True for SQL query logging during tests
        pool_pre_ping=True  # Verify connections before using
    )

    # Create all tables in the test database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Seed reference TagTypes (mirrors production migration data)
        now = datetime.now(UTC)
        await conn.execute(sa.text("""
            INSERT INTO tag_types (id, name, is_privileged, is_parent, has_children, display_order, is_deactivated, created_at)
            VALUES
                ('00000000-0000-0000-0000-000000000001', 'supercategory', true,  true,  true,  0, false, :now),
                ('00000000-0000-0000-0000-000000000004', 'category',      true,  false, false, 1, false, :now),
                ('00000000-0000-0000-0000-000000000005', 'gender',        false, false, false, 2, false, :now),
                ('00000000-0000-0000-0000-000000000006', 'custom',        false, false, false, 3, false, :now)
            ON CONFLICT (name) DO NOTHING
        """).bindparams(now=now))

    yield engine

    # Cleanup: Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Dispose of engine connection pool
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """
    Function-scoped async database session.

    - Each test gets a fresh session
    - Automatically rolls back after test (test isolation)
    - Use this fixture for integration tests that need real database

    Args:
        db_engine: Function-scoped engine from db_engine fixture

    Returns:
        AsyncSession: SQLAlchemy async session for database operations

    Example:
        ```python
        @pytest.mark.integration
        @pytest.mark.asyncio
        async def test_create_country(db_session):
            repository = CountryRepository(db_session)
            country = await repository.create({"name": "USA", "code": "USA"})
            assert country.id is not None
        ```
    """
    # Create async session factory
    async_session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False  # Don't expire objects after commit
    )

    # Create session
    async with async_session_factory() as session:
        yield session
        # Rollback any uncommitted changes after test
        await session.rollback()


# ============================================================================
# SHARED TEST DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_country_data():
    """
    Sample country data for tests.

    Returns:
        dict: Valid country data (name, code)

    Example:
        ```python
        def test_create_country(sample_country_data):
            assert sample_country_data["code"] == "USA"
        ```
    """
    return {
        "name": "United States",
        "code": "USA"
    }


@pytest.fixture
def sample_country_data_list():
    """
    List of sample countries for bulk testing.

    Returns:
        list[dict]: Multiple country data dictionaries
    """
    return [
        {"name": "United States", "code": "USA"},
        {"name": "Canada", "code": "CAN"},
        {"name": "Mexico", "code": "MEX"},
        {"name": "Germany", "code": "DEU"},
        {"name": "France", "code": "FRA"},
    ]


@pytest.fixture
def random_uuid():
    """
    Generate a random UUID for testing.

    Returns:
        UUID: Random UUID v4
    """
    return uuid4()


# ============================================================================
# BDD CONTEXT FIXTURE (for pytest-bdd)
# ============================================================================

@pytest.fixture
def context():
    """
    Shared context for BDD scenarios.

    Used to pass data between Given/When/Then steps in BDD tests.

    Returns:
        dict: Empty dictionary for storing scenario data

    Example:
        ```python
        @given("I have a country")
        def country_exists(context, db_session):
            country = Country(name="USA", code="USA")
            context["country"] = country

        @then("the country should exist")
        def verify_country(context):
            assert context["country"].name == "USA"
        ```
    """
    return {}


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """
    Configure pytest with custom markers and settings.

    This runs once when pytest starts up.
    """
    # Register markers (also defined in pytest.ini, but this provides descriptions)
    config.addinivalue_line(
        "markers",
        "integration: Integration tests requiring real database (Testcontainers)"
    )
    config.addinivalue_line(
        "markers",
        "unit: Unit tests with mocked dependencies (fast)"
    )
    config.addinivalue_line(
        "markers",
        "bdd: BDD scenarios using pytest-bdd (Gherkin)"
    )
    config.addinivalue_line(
        "markers",
        "slow: Slow tests (>1 second), skip with -m 'not slow'"
    )


# ============================================================================
# TESTCONTAINERS TROUBLESHOOTING
# ============================================================================

"""
IMPORTANT: Testcontainers requires Docker Desktop to be running!

If you see errors like:
- "Cannot connect to the Docker daemon"
- "docker.errors.DockerException"

Solutions:
1. **Windows/WSL**: Start Docker Desktop on Windows
2. **Linux**: Start Docker daemon: `sudo systemctl start docker`
3. **Mac**: Start Docker Desktop

Verify Docker is running:
```bash
docker ps
```

You should see a list of containers (or empty list, not an error).

For more info: https://testcontainers-python.readthedocs.io/
"""
