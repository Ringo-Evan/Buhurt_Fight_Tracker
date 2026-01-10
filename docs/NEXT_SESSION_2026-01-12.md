# Next Session Plan: 2026-01-12

**Previous Session**: 2026-01-11 (Country Critical Fixes & Alembic Setup)
**Current Status**: Country entity 100% complete (excluding Team dependencies), ready for verification
**Estimated Time**: 45 min (verification only) to 3 hours (verification + Team BDD/tests)

---

## 🎯 Session Goals

### Primary Goal
**Verify Country Entity with Integration Tests** - Run full test suite with Docker

### Secondary Goal
**Begin Team Entity Test Suite** - If time permits after verification

---

## 📊 Current Status Summary

### ✅ What's Done (Session 2026-01-11)

**Critical Fixes Completed**:
- ✅ Fixed deprecated `datetime.utcnow()` → `datetime.now(UTC)` (Python 3.12+)
- ✅ Added unique constraint and index on `code` column (database-level enforcement)
- ✅ Fixed async bug in `permanent_delete()` (`session.delete` is not async)
- ✅ Fixed mock warnings in unit tests (`session.add/delete` now synchronous mocks)
- ✅ Initialized Alembic migration system
- ✅ Created migration: `ab555486f418_create_countries_table_with_soft_delete_.py`
- ✅ All unit tests passing (42 pass, 6 expected NotImplementedError)
- ✅ Changes committed with descriptive message

**Model Layer** (`app/models/country.py`):
- ✅ UUID primary keys
- ✅ Soft delete pattern
- ✅ UTC datetime (Python 3.12+ compatible)
- ✅ Unique constraint on code
- ✅ All fields properly typed
- ✅ 100% complete

**Repository Layer** (`app/repositories/country_repository.py`):
- ✅ All CRUD operations implemented
- ✅ Soft delete filtering
- ✅ 98% test coverage
- ⏸️ `count_relationships()` - NotImplementedError (Team dependency)
- ⏸️ `replace()` - NotImplementedError (Team dependency)

**Service Layer** (`app/services/country_service.py`):
- ✅ ISO 3166-1 alpha-3 validation (pycountry)
- ✅ Business logic layer complete
- ✅ 94% test coverage
- ⏸️ `permanent_delete()` - NotImplementedError (Team dependency)

**Testing**:
- ✅ 42 unit tests passing
- ✅ 6 unit tests failing with NotImplementedError (expected)
- ❌ Integration tests NOT RUN (Docker not started)
- ❌ BDD scenarios NOT RUN (Docker not started)

**Database Migrations**:
- ✅ Alembic initialized
- ✅ Migration created for countries table
- ❌ Migration NOT APPLIED (no database yet)

### ❌ What's Blocking Completion

#### 🟡 Verification Tasks (MUST DO)

1. **Start Docker Desktop** ⏱️ 2 min
   - Open Docker Desktop on Windows
   - Wait for "Docker is running" status
   - Verify: `docker ps` (should not error)

2. **Run Integration Tests** ⏱️ 8 min
   ```bash
   pytest tests/integration/ -v
   ```
   **Expected results**:
   - ~14 integration tests
   - All tests pass
   - Real PostgreSQL container spins up
   - Tests take ~5-8 seconds (container startup + execution)

3. **Run BDD Scenarios** ⏱️ 5 min
   ```bash
   pytest tests/step_defs/ -v
   ```
   **Expected results**:
   - ~21 scenarios total
   - ~15 scenarios pass
   - ~6 scenarios fail with NotImplementedError (Team dependencies)
   - Clear error messages pointing to Issue #33

4. **Optional: Apply Migration Locally** ⏱️ 5 min
   ```bash
   # Only if you want to test migrations on local DB
   alembic upgrade head
   alembic downgrade base  # Test rollback
   alembic upgrade head    # Re-apply
   ```

#### 🟢 Optional: Cosmetic Improvements

5. **Fix Test File datetime Warnings** ⏱️ 15 min
   - 25 deprecation warnings from test files using `datetime.utcnow()`
   - Not blocking, but noisy in test output
   - Files affected: `tests/unit/repositories/test_country_repository.py`, `tests/unit/services/test_country_service.py`
   - Replace `datetime.utcnow()` with `datetime.now(UTC)` in test data creation
   - Import `from datetime import UTC` in affected test files

---

## 📋 Session Checklist

### Phase 1: Verification (20 minutes)

#### Task 1.1: Start Docker Desktop ⏱️ 2 min
- [ ] Open Docker Desktop on Windows
- [ ] Wait for "Docker is running" indicator
- [ ] Verify: `docker ps` returns without error

---

#### Task 1.2: Run Integration Tests ⏱️ 8 min
```bash
pytest tests/integration/ -v
```

**Expected behavior**:
- Testcontainers downloads PostgreSQL 16 image (first run only)
- Container starts automatically
- All tables created via `Base.metadata.create_all`
- Tests execute against real database
- All tests pass
- Container destroyed after tests complete

**Success criteria**:
- [ ] ~14 tests discovered
- [ ] All tests pass
- [ ] No connection errors
- [ ] Test output shows PostgreSQL container started

**If failures occur**:
- Check Docker is running: `docker ps`
- Check container logs: `docker logs <container_id>`
- Verify migration matches model definition
- Check asyncpg is installed: `pip list | grep asyncpg`

---

#### Task 1.3: Run BDD Scenarios ⏱️ 5 min
```bash
pytest tests/step_defs/ -v
```

**Expected results**:
- [ ] Pytest discovers scenarios from `tests/features/country_management.feature`
- [ ] ~15 scenarios pass (basic CRUD operations)
- [ ] ~6 scenarios fail with NotImplementedError
- [ ] Error messages clearly indicate Team dependency blocker

**Failing scenarios** (expected):
- Scenarios involving `permanent_delete()` with relationship checks
- Scenarios involving `replace()` functionality
- Scenarios involving `count_relationships()`

**Success criteria**:
- [ ] Passing scenarios cover: create, read, update, soft delete, ISO validation
- [ ] Failing scenarios have clear NotImplementedError messages
- [ ] No unexpected failures (bugs)

---

#### Task 1.4: Optional - Fix Test Datetime Warnings ⏱️ 15 min

**Only do this if you want clean test output. Not required for Country completion.**

**Files to update**:
1. `tests/unit/repositories/test_country_repository.py` (lines 106, 194, 232, 320, 327, 388, 395, 403, 442, 505, 542, 579, 650, 767, 775, 842)
2. `tests/unit/services/test_country_service.py` (multiple lines)

**Change**:
```python
# BEFORE:
from datetime import datetime
country = Country(created_at=datetime.utcnow())

# AFTER:
from datetime import datetime, UTC
country = Country(created_at=datetime.now(UTC))
```

**Verification**:
```bash
pytest tests/unit/ -v 2>&1 | grep -i "deprecation"
# Should return zero deprecation warnings
```

---

### Phase 2: Optional - Begin Team Entity (1.5-2 hours)

**Only proceed if:**
- ✅ All integration tests passing
- ✅ All BDD scenarios running (pass + expected failures)
- ✅ Time remaining > 1.5 hours
- ✅ Energy level high

---

#### Task 2.1: Create Team BDD Scenarios ⏱️ 30 min

**File**: `tests/features/team_management.feature`

**Scenarios to cover**:

```gherkin
Feature: Team Management
  As a system administrator
  I want to manage teams associated with countries
  So that I can track team rosters and lineups

  Background:
    Given the database is empty

  # Happy path scenarios
  Scenario: Create team with valid country
    Given an active country exists with code "USA"
    When I create a team "Team USA" for country "USA"
    Then the team is created successfully
    And the team name is "Team USA"
    And the team country code is "USA"

  Scenario: Retrieve team with country data
    Given an active country exists with code "USA"
    And a team "Team USA" exists for country "USA"
    When I retrieve the team by ID
    Then the team includes nested country data
    And the country name is "United States"

  Scenario: List teams filtered by country
    Given an active country exists with code "USA"
    And an active country exists with code "CAN"
    And 3 teams exist for country "USA"
    And 2 teams exist for country "CAN"
    When I list teams filtered by country "USA"
    Then I receive exactly 3 teams
    And all teams belong to country "USA"

  Scenario: Soft delete team preserves country relationship
    Given an active country exists with code "USA"
    And a team "Team USA" exists for country "USA"
    When I soft delete the team
    Then the team is marked as deleted
    And the country relationship is intact
    And listing teams excludes the deleted team

  # Error scenarios
  Scenario: Create team with non-existent country fails
    Given no country exists with code "XYZ"
    When I attempt to create a team for country "XYZ"
    Then I receive a validation error
    And the error says "Country not found"

  Scenario: Create team with soft-deleted country fails
    Given a soft-deleted country exists with code "SUN"
    When I attempt to create a team for country "SUN"
    Then I receive a validation error
    And the error says "Country is not active"

  # Edge cases
  Scenario: List all teams when none exist
    When I list all teams
    Then I receive an empty list

  Scenario: Retrieve non-existent team
    When I retrieve a team with non-existent ID
    Then I receive a not found error
```

**Additional scenarios to add**:
- Update team name
- Update team country (validate new country exists and is active)
- Soft delete validation (can't delete already deleted team)
- Eager loading verification (no N+1 queries)

---

#### Task 2.2: Create Team Model ⏱️ 15 min

**File**: `app/models/team.py`

**Implementation**:
```python
"""
SQLAlchemy ORM model for Team entity.

Implements soft delete pattern with is_deleted flag.
Uses UUID primary keys and foreign key relationship to Country.
"""

from datetime import datetime, UTC
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.country import Base, Country


class Team(Base):
    """
    Team entity with soft delete support and country relationship.

    Attributes:
        id: UUID primary key (auto-generated)
        name: Team name (max 100 characters)
        country_id: Foreign key to countries table (UUID)
        is_deleted: Soft delete flag (defaults to False)
        created_at: Timestamp of creation (auto-generated)

        country: Relationship to Country entity (eager loaded)
    """
    __tablename__ = "teams"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    country_id: Mapped[UUID] = mapped_column(
        ForeignKey("countries.id"),
        nullable=False
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relationships
    country: Mapped["Country"] = relationship(
        "Country",
        lazy="joined",  # Eager load by default to avoid N+1
        foreign_keys=[country_id]
    )

    def __init__(self, **kwargs):
        """
        Initialize Team with Python-level defaults.

        Ensures defaults are applied when creating instances programmatically.
        """
        super().__init__(**kwargs)

        if 'id' not in kwargs:
            self.id = uuid4()
        if 'is_deleted' not in kwargs:
            self.is_deleted = False
        if 'created_at' not in kwargs:
            self.created_at = datetime.now(UTC)

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name='{self.name}', country_id={self.country_id}, is_deleted={self.is_deleted})>"
```

---

#### Task 2.3: Create Team Unit Tests ⏱️ 45 min

**Files**:
- `tests/unit/repositories/test_team_repository.py`
- `tests/unit/services/test_team_service.py`

**Repository tests** (similar structure to Country):
```python
class TestTeamRepositoryCreate:
    - test_create_team_calls_session_methods_correctly
    - test_create_team_with_country_relationship
    - test_create_team_handles_fk_constraint_violation

class TestTeamRepositoryGetById:
    - test_get_by_id_returns_team_with_eager_loaded_country
    - test_get_by_id_returns_none_when_not_exists
    - test_get_by_id_filters_soft_deleted_teams

class TestTeamRepositoryList:
    - test_list_all_excludes_soft_deleted_teams
    - test_list_by_country_filters_correctly
    - test_list_by_country_excludes_soft_deleted

class TestTeamRepositorySoftDelete:
    - test_soft_delete_sets_is_deleted_flag
    - test_soft_delete_preserves_country_fk

class TestTeamRepositoryUpdate:
    - test_update_team_name_succeeds
    - test_update_team_country_succeeds
    - test_update_team_with_non_existent_country_fails
```

**Service tests** (NEW: country validation):
```python
class TestTeamServiceCreate:
    - test_create_team_with_valid_country_succeeds
    - test_create_team_with_non_existent_country_raises_error
    - test_create_team_with_soft_deleted_country_raises_error
    - test_create_team_validates_empty_name

class TestTeamServiceRetrieve:
    - test_get_by_id_returns_team_with_country_data
    - test_get_by_id_raises_not_found_error

class TestTeamServiceUpdate:
    - test_update_team_validates_new_country_exists
    - test_update_team_validates_new_country_not_deleted

class TestTeamServiceDelete:
    - test_delete_team_soft_deletes_successfully
```

**Key differences from Country tests**:
- Must mock `CountryRepository` in service tests
- Service must validate country exists and is active
- Repository tests verify eager loading of country relationship
- Repository tests verify FK constraint enforcement

---

#### Task 2.4: Create Team Integration Tests ⏱️ 30 min

**File**: `tests/integration/test_team_integration.py`

**Test cases**:
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_team_and_retrieve_with_country_relationship(db_session):
    """
    Test creating a team and retrieving with eager-loaded country.

    Verifies:
    - Foreign key relationship works
    - Eager loading prevents N+1 queries
    - Country data is nested in response
    """
    # Create country first
    country_repo = CountryRepository(db_session)
    country = await country_repo.create({"name": "United States", "code": "USA"})

    # Create team
    team_repo = TeamRepository(db_session)
    team = await team_repo.create({
        "name": "Team USA",
        "country_id": country.id
    })

    # Retrieve and verify
    retrieved = await team_repo.get_by_id(team.id)
    assert retrieved.country.code == "USA"
    assert retrieved.country.name == "United States"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_teams_filtered_by_country(db_session):
    """Test filtering teams by country ID."""
    # Setup: Create 2 countries with teams
    country_repo = CountryRepository(db_session)
    usa = await country_repo.create({"name": "USA", "code": "USA"})
    can = await country_repo.create({"name": "Canada", "code": "CAN"})

    team_repo = TeamRepository(db_session)
    await team_repo.create({"name": "Team USA 1", "country_id": usa.id})
    await team_repo.create({"name": "Team USA 2", "country_id": usa.id})
    await team_repo.create({"name": "Team Canada", "country_id": can.id})

    # Act
    usa_teams = await team_repo.list_by_country(usa.id)

    # Assert
    assert len(usa_teams) == 2
    assert all(team.country_id == usa.id for team in usa_teams)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_foreign_key_constraint_prevents_orphan_teams(db_session):
    """
    Test that database FK constraint prevents creating team with non-existent country.
    """
    team_repo = TeamRepository(db_session)
    fake_country_id = uuid4()

    with pytest.raises(IntegrityError):
        await team_repo.create({
            "name": "Orphan Team",
            "country_id": fake_country_id
        })


@pytest.mark.integration
@pytest.mark.asyncio
async def test_soft_delete_team_preserves_country_relationship(db_session):
    """
    Test that soft deleting a team doesn't break the country FK.
    """
    # Setup
    country_repo = CountryRepository(db_session)
    country = await country_repo.create({"name": "USA", "code": "USA"})

    team_repo = TeamRepository(db_session)
    team = await team_repo.create({"name": "Team USA", "country_id": country.id})

    # Act: Soft delete
    await team_repo.soft_delete(team.id)

    # Assert: Can still retrieve with include_deleted
    deleted_team = await team_repo.get_by_id(team.id, include_deleted=True)
    assert deleted_team.is_deleted is True
    assert deleted_team.country.code == "USA"  # Relationship intact
```

---

## 🎯 Definition of Done

### Verification Complete
- [ ] Docker Desktop running
- [ ] Integration tests run and passing (~14 tests)
- [ ] BDD scenarios run (15 pass + 6 expected NotImplementedError failures)
- [ ] Country entity verified with real database
- [ ] No unexpected test failures
- [ ] Alembic migration can be applied and rolled back successfully

### Team Entity Started (Optional)
- [ ] Team BDD scenarios written (~8-10 scenarios)
- [ ] Team model created with Country FK relationship
- [ ] Team unit tests written (repository + service)
- [ ] Team integration tests written
- [ ] All tests failing (RED phase) - ready for implementation

---

## 📚 Reference Materials

### Files to Review Before Starting

**Completed Country Implementation** (reference for Team):
- `app/models/country.py` - Model pattern with soft delete
- `app/repositories/country_repository.py` - Repository CRUD pattern
- `app/services/country_service.py` - Service validation pattern
- `tests/unit/repositories/test_country_repository.py` - Unit test patterns
- `tests/integration/test_country_integration.py` - Integration test patterns
- `tests/features/country_management.feature` - BDD scenario patterns

**Alembic Configuration**:
- `alembic.ini` - Database connection config
- `alembic/env.py` - Migration environment setup
- `alembic/versions/ab555486f418_*.py` - Example migration

### GitHub Issues

- Issue #27: Country Unit Tests (READY TO CLOSE)
- Issue #28: Country Integration Tests (READY TO CLOSE after verification)
- Issue #29: Country Implementation (READY TO UPDATE)
- Issue #30: Team BDD Scenarios (NEXT)
- Issue #31: Team Unit Tests (NEXT)
- Issue #32: Team Integration Tests (NEXT)
- Issue #33: Team Implementation (FUTURE)

### Documentation

- `CLAUDE.md` - Project guidelines and TDD philosophy
- `docs/adr/001-use-uuids-for-primary-keys.md` - Architecture decisions
- `docs/data-model.md` - Entity relationships (Team → Country FK)
- `docs/testing/pytest-ini-explained.md` - Testing configuration
- `docs/NEXT_SESSION_2026-01-11.md` - Previous session plan

---

## ⚠️ Common Pitfalls to Avoid

### From Country Implementation Experience

1. **Don't skip Docker startup** - Integration tests will silently skip without Docker
2. **Don't ignore deprecation warnings** - Fix them immediately (or document as cosmetic)
3. **Don't mock what you should test** - Use real DB in integration tests
4. **Don't skip verifying eager loading** - Test that `country` relationship is loaded
5. **Don't forget FK constraints** - Database should enforce relationships

### For Team Implementation

1. **Validate country in service layer** - Not in repository
2. **Test FK constraints** - Integration tests should verify DB prevents orphans
3. **Eager load by default** - Use `lazy="joined"` to avoid N+1 queries
4. **Mock CountryRepository** - Service tests need both repositories mocked
5. **Nested schemas for responses** - TeamResponse should include CountryResponse
6. **Don't forget soft delete filtering** - List operations must exclude deleted

---

## 📊 Time Estimates

### Minimum Session (Verification Only)
- Start Docker: 2 min
- Run integration tests: 8 min
- Run BDD scenarios: 5 min
- Review results: 5 min
- Update GitHub issues: 10 min
- **Total: 30 minutes**

### Optimal Session (Verification + Team Tests)
- Verification: 30 min
- Team BDD scenarios: 30 min
- Team model creation: 15 min
- Team unit tests: 45 min
- Team integration tests: 30 min
- **Total: 2.5 hours**

### Full Session (Verification + Team Tests + Implementation)
- Verification + Tests: 2.5 hours
- Team repository implementation: 30 min
- Team service implementation: 30 min
- Run tests to green: 20 min
- **Total: 3.5-4 hours**

---

## 🎯 Success Metrics

### Session Success Criteria
- [ ] Docker Desktop running successfully
- [ ] All integration tests passing with real PostgreSQL
- [ ] BDD scenarios executed (pass + expected failures documented)
- [ ] Zero unexpected test failures
- [ ] Country entity verified production-ready
- [ ] GitHub issues updated accurately

### Code Quality Checks

```bash
# Before closing session, run:

# 1. All unit tests
pytest tests/unit/ -v
# Expected: 42 pass, 6 NotImplementedError

# 2. All integration tests
pytest tests/integration/ -v
# Expected: ~14 pass, 0 failures

# 3. BDD scenarios
pytest tests/step_defs/ -v
# Expected: ~15 pass, ~6 NotImplementedError

# 4. Coverage check (optional)
pytest tests/unit/ --cov=app --cov-report=term-missing
# Expected: >90% coverage

# 5. No deprecation warnings (if cosmetic fixes applied)
pytest tests/unit/ -v 2>&1 | grep -i "deprecation" | wc -l
# Expected: 0
```

---

## 💡 Session Flow Recommendation

### Recommended Order

1. ☕ **Start with quick win** - Start Docker, run integration tests (build confidence)
2. 🧪 **Verify BDD scenarios** - Ensure business requirements documented
3. 📝 **Optional: Fix cosmetic warnings** - Clean up datetime deprecations
4. 📊 **Update GitHub issues** - Document current state
5. 🚀 **Start Team entity** - Only if >1.5 hours remains and all verifications pass

### Don't Start Team Entity If:
- Integration tests failing
- BDD scenarios have unexpected failures
- Docker not running reliably
- Less than 1.5 hours available
- Feeling rushed or tired

---

## 🔄 Next Next Session Preview

### If Verification Complete, Team Not Started:
**Session 2026-01-13**: Begin Team entity from scratch
- Team BDD scenarios
- Team model + migration
- Team unit tests
- Team integration tests
- Team implementation (if time)

### If Verification + Team Tests Complete:
**Session 2026-01-13**: Implement Team entity
- Team repository implementation (follow Country pattern)
- Team service implementation (add country validation)
- Run tests until green
- Create Alembic migration for teams table
- Apply migration and verify
- Optional: Team API endpoints

### If Team Fully Implemented:
**Session 2026-01-13**: Complete Team integration + Country blockers
- Unblock Country `count_relationships()` (count teams by country_id)
- Unblock Country `replace()` (update team.country_id references)
- Unblock Country `permanent_delete()` (check no teams exist)
- Close all Country issues (#27, #28, #29)
- Close all Team issues (#30, #31, #32, #33)
- Begin Fighter entity planning

---

## 📌 Important Reminders

1. **Docker is required** - Integration tests and BDD scenarios need Testcontainers
2. **Test-first is non-negotiable** - Write tests before Team implementation
3. **NotImplementedError is a feature** - Failing tests document blockers
4. **Eager loading prevents N+1** - Team must eager load country relationship
5. **FK constraints enforce relationships** - Database prevents orphan teams
6. **Validate in service layer** - Country existence checked by service, not repository
7. **Git commit frequently** - After each completed task phase

---

## 🎓 Lessons Learned from Session 2026-01-11

### What Went Well ✅
- Systematic approach to critical fixes (one at a time)
- Clear prioritization (deprecations, constraints, bugs, migrations)
- Good use of todo list to track progress
- Comprehensive commit message with all changes documented
- Fixed both production code AND test code in one session

### What to Improve 🔄
- Run integration tests DURING implementation, not just at end
- Keep Docker running throughout development session
- Fix deprecation warnings in test files at same time as production code
- Apply migrations immediately after creation to verify they work
- Consider using `psycopg2-binary` for Alembic (avoids async issues)

### Key Takeaways 💡
1. `session.delete()` and `session.add()` are synchronous - don't await them!
2. Alembic needs synchronous driver (psycopg2), app uses async driver (asyncpg)
3. Deprecation warnings are not just cosmetic - they predict future breaking changes
4. Database constraints should enforce business rules, not just application code
5. Unit tests catch logic bugs, integration tests catch configuration bugs

---

**Session Goal**: Verify Country entity is production-ready with real database tests

**Stretch Goal**: Begin Team entity test suite (BDD + unit + integration tests)

**Success Metric**: Can confidently deploy Country CRUD operations to staging environment knowing tests verify correctness against real PostgreSQL

---

*Document created*: 2026-01-11
*For session*: 2026-01-12
*Estimated duration*: 30 min (minimum) to 3.5 hours (optimal)
*Status*: Ready to execute

---

## 🔍 Quick Reference: Key Commands

```bash
# Verification Phase
docker ps                                    # Check Docker running
pytest tests/integration/ -v                 # Run integration tests
pytest tests/step_defs/ -v                   # Run BDD scenarios
alembic upgrade head                         # Apply migrations
alembic downgrade base                       # Rollback migrations

# Team Implementation Phase
pytest tests/unit/repositories/test_team_repository.py -v  # Team repo tests
pytest tests/unit/services/test_team_service.py -v         # Team service tests
pytest tests/integration/test_team_integration.py -v       # Team integration tests

# Code Quality
pytest tests/unit/ --cov=app --cov-report=term-missing     # Coverage report
pytest tests/unit/ -v 2>&1 | grep -i deprecation           # Check warnings

# Git Operations
git status                                   # Check changes
git add .                                    # Stage all
git commit -m "message"                      # Commit with message
git log --oneline -5                         # Recent commits
```
