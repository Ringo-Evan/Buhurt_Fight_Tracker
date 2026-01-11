# Next Session Plan: 2026-01-11

**Previous Session**: 2026-01-10 (Code Review & Country Unit Tests)
**Current Status**: Country entity ~85% complete, Team entity next in queue
**Estimated Time**: 2-3 hours to complete Country + start Team

---

## 🎯 Session Goals

### Primary Goal
**Complete Country Entity to 100%** - No technical debt carried forward

### Secondary Goal
**Begin Team Entity Implementation** - If time permits after Country completion

---

## 📊 Current Status Summary

### ✅ What's Done (Country Entity)

**Model Layer** (`app/models/country.py`):
- ✅ UUID primary keys
- ✅ Soft delete pattern
- ✅ All fields properly typed
- ⚠️ **ISSUE**: `datetime.utcnow()` deprecated (Python 3.12+)
- ⚠️ **ISSUE**: Missing unique constraint on `code` column

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
- ✅ Integration test files created
- ❌ Integration tests NOT RUN (Docker not started)
- ❌ BDD scenarios NOT RUN

**Documentation**:
- ✅ Comprehensive code review document
- ✅ Testing infrastructure documented
- ✅ ADR-001 (UUIDs) established

### ❌ What's Blocking Completion

#### 🔴 Critical Issues (MUST FIX)
1. **Deprecated `datetime.utcnow()` usage**
   - Files: `app/models/country.py` (lines 56, 80)
   - Fix: Replace with `datetime.now(UTC)`
   - Impact: 20+ deprecation warnings, future Python incompatibility
   - Time: 5 minutes

2. **Missing database constraint on `code` uniqueness**
   - File: `app/models/country.py` (line 43)
   - Fix: Add `unique=True, index=True` to `mapped_column`
   - Impact: Database doesn't enforce business rule
   - Time: 2 minutes

3. **No Alembic migration created**
   - Action: `alembic revision --autogenerate -m "Create countries table"`
   - Impact: Can't run integration tests, no schema version control
   - Time: 10 minutes

#### 🟡 Verification Tasks (MUST DO)
4. **Integration tests not run**
   - Requirement: Docker Desktop running
   - Action: `pytest tests/integration/ -v`
   - Expected: All tests pass
   - Time: 5 minutes

5. **BDD scenarios not run**
   - Action: `pytest tests/features/ -v`
   - Expected: ~15 pass, ~6 fail with NotImplementedError
   - Time: 5 minutes

6. **Two mock warnings in tests**
   - Issue: Unawaited coroutines in `session.add()` mocks
   - Files: `tests/unit/repositories/test_country_repository.py`
   - Impact: Test output noise
   - Time: 10 minutes

---

## 📋 Session Checklist

### Phase 1: Fix Critical Issues (20 minutes)

#### Task 1.1: Fix Datetime Deprecation ⏱️ 5 min
```python
# File: app/models/country.py

# BEFORE:
from datetime import datetime
created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

# AFTER:
from datetime import datetime, UTC
created_at: Mapped[datetime] = mapped_column(
    DateTime,
    default=lambda: datetime.now(UTC)
)
```

**Changes needed**:
- [ ] Line 1: Add `UTC` to imports
- [ ] Line 56: Update `created_at` default
- [ ] Line 80: Update `__init__` assignment to `datetime.now(UTC)`

**Verify**: Run unit tests - warnings should disappear

---

#### Task 1.2: Add Unique Constraint on Code ⏱️ 2 min
```python
# File: app/models/country.py (line ~43)

# BEFORE:
code: Mapped[str] = mapped_column(String(3), nullable=False)

# AFTER:
code: Mapped[str] = mapped_column(
    String(3),
    nullable=False,
    unique=True,  # Enforce at database level
    index=True    # Optimize lookups
)
```

**Changes needed**:
- [ ] Add `unique=True` to enforce business rule
- [ ] Add `index=True` for query performance

**Rationale**: Database should enforce uniqueness, not just application

---

#### Task 1.3: Create Alembic Migration ⏱️ 10 min

**Step 1**: Generate migration
```bash
alembic revision --autogenerate -m "Create countries table with soft delete support"
```

**Step 2**: Review generated migration
- [ ] Verify `countries` table created
- [ ] Verify all columns present (id, name, code, is_deleted, created_at)
- [ ] Verify unique constraint on `code`
- [ ] Verify index on `code`

**Step 3**: Apply migration to test database (if needed)
```bash
alembic upgrade head
```

**Note**: Integration tests will handle migrations automatically via Testcontainers

---

#### Task 1.4: Fix Mock Warnings ⏱️ 10 min

**Issue**: `session.add()` returns coroutine in AsyncMock but we don't await it

**File**: `tests/unit/repositories/test_country_repository.py`

**Find affected tests**:
- `TestCountryRepositoryCreate::test_create_country_calls_session_methods_correctly`
- `TestCountryRepositoryCreate::test_create_country_handles_duplicate_code_constraint_violation`

**Fix approach**:
```python
# The issue: session.add() is mocked as async but isn't awaited in actual code
# Repository code: self.session.add(country)  # Not async

# Solution: Configure mock to not return a coroutine
mock_session = AsyncMock()
mock_session.add = MagicMock()  # Make add() synchronous, not async
```

**Verify**: Run tests - no more "coroutine was never awaited" warnings

---

### Phase 2: Run Verification Tests (15 minutes)

#### Task 2.1: Start Docker Desktop ⏱️ 2 min
- [ ] Open Docker Desktop on Windows
- [ ] Wait for "Docker is running" status
- [ ] Verify: `docker ps` (should not error)

---

#### Task 2.2: Run Integration Tests ⏱️ 8 min
```bash
pytest tests/integration/ -v
```

**Expected results**:
- [ ] ~14 integration tests
- [ ] All tests pass
- [ ] Real PostgreSQL container spins up
- [ ] Tests take ~5-8 seconds (container startup + execution)

**If failures occur**:
- Check container logs
- Verify migration applied correctly
- Verify connection string format (asyncpg vs psycopg2)

---

#### Task 2.3: Run BDD Scenarios ⏱️ 5 min
```bash
pytest tests/features/ -v
```

**Expected results**:
- [ ] ~21 scenarios total
- [ ] ~15 scenarios pass
- [ ] ~6 scenarios fail with NotImplementedError (Team dependencies)
- [ ] Clear error messages pointing to Issue #33

**Failing scenarios** (expected):
- Scenarios involving `permanent_delete()` with relationship checks
- Scenarios involving `replace()` functionality
- Scenarios involving `count_relationships()`

---

### Phase 3: Update GitHub Issues (10 minutes)

#### Task 3.1: Close Issue #27 (Country Unit Tests)
```bash
gh issue close 27 --comment "✅ Completed in session 2026-01-10.

**Accomplishments**:
- 48 unit tests created (42 passing, 6 NotImplementedError)
- 98% repository coverage
- 94% service coverage
- Tests follow AAA pattern
- Proper async mocking with AsyncMock

**Blocked features documented**:
- permanent_delete() - blocked on Team entity
- replace() - blocked on Team entity
- count_relationships() - blocked on Team entity

See docs/code-review-country-2026-01-10.md for detailed review."
```

---

#### Task 3.2: Close Issue #28 (Country Integration Tests)
```bash
gh issue close 28 --comment "✅ Completed in session 2026-01-11.

**Accomplishments**:
- 14 integration tests created and passing
- Testcontainers PostgreSQL setup working
- Tests verify real database behavior
- Database migrations applied correctly
- Soft delete filtering validated

**Infrastructure established**:
- pytest.ini configuration
- conftest.py fixtures (session/function scoped)
- Testcontainers pattern for future entities"
```

---

#### Task 3.3: Update Issue #29 (Country Implementation)

**Mark completed items**:
- [x] Model layer complete
- [x] Repository layer complete
- [x] Service layer complete
- [x] Custom exceptions complete
- [x] Database migration created

**Mark incomplete items**:
- [ ] Schema layer (not created - API endpoints needed)
- [ ] API layer (not created - future work)

**Add comment**:
```bash
gh issue comment 29 --body "📊 Status Update (2026-01-11):

**Completed Layers**:
✅ Model layer (app/models/country.py)
✅ Repository layer (app/repositories/country_repository.py)
✅ Service layer (app/services/country_service.py)
✅ Custom exceptions (app/exceptions.py)
✅ Database migration (alembic/versions/XXX_create_countries_table.py)

**Remaining Work**:
⏸️ Schema layer (app/schemas/country.py) - blocked until API endpoints needed
⏸️ API layer (app/api/v1/countries.py) - deferred to future epic

**Test Results**:
- Unit tests: 42 passing, 6 NotImplementedError (expected)
- Integration tests: 14 passing
- BDD scenarios: ~15 passing, ~6 NotImplementedError (expected)
- Coverage: 98% repository, 94% service, 100% model

**Blocked Features** (waiting for Team entity):
- permanent_delete() with relationship checking
- replace() functionality
- count_relationships()

**Ready for**: Team entity implementation (Issue #33)"
```

---

#### Task 3.4: Update Issue #33 (Team Implementation)

**Mark as ready to start**:
```bash
gh issue comment 33 --body "🚀 Ready to Begin (2026-01-11)

**Prerequisites Complete**:
✅ Country entity fully implemented
✅ Testing patterns established (unit, integration, BDD)
✅ Repository pattern proven
✅ Soft delete pattern working
✅ Alembic migration workflow established

**Starting Point**:
Follow same TDD workflow as Country:
1. Write BDD scenarios (Issue #30)
2. Write unit tests (Issue #31)
3. Write integration tests (Issue #32)
4. Implement model → repository → service → API

**Key Differences from Country**:
- Foreign key relationship to Country
- Eager loading of country relationship
- Country validation in service layer
- Nested country data in API responses

**Estimated Time**: 4-6 hours total (2-3 sessions)"
```

---

### Phase 4: Begin Team Entity (Optional - If Time Permits)

**Only proceed if Country entity 100% complete and time remaining > 1 hour**

#### Task 4.1: Create Team BDD Scenarios ⏱️ 30 min
**File**: `tests/features/team_management.feature`

**Key scenarios to cover**:
```gherkin
Feature: Team Management
  As a system administrator
  I want to manage teams associated with countries
  So that I can track team rosters and lineups

  Scenario: Create team with valid country
    Given an active country exists
    When I create a team for that country
    Then the team is created successfully
    And the team includes the country data

  Scenario: Create team with non-existent country
    Given no country exists with a specific ID
    When I create a team for that country ID
    Then I receive a validation error
    And the error says "Country not found"

  Scenario: Create team with soft-deleted country
    Given a soft-deleted country exists
    When I create a team for that country
    Then I receive a validation error
    And the error says "Country is not active"

  Scenario: List teams filtered by country
    Given 3 teams exist for country A
    And 2 teams exist for country B
    When I list teams filtered by country A
    Then I receive 3 teams
    And all teams belong to country A

  Scenario: Soft delete team preserves country relationship
    Given a team exists for a country
    When I soft delete the team
    Then the team is marked as deleted
    But the country relationship remains intact
```

**Additional scenarios**:
- Retrieve team with eager-loaded country data
- Soft delete team
- List all teams (no filter)
- Handle non-existent team retrieval

---

#### Task 4.2: Create Team Unit Tests ⏱️ 45 min
**Files**:
- `tests/unit/repositories/test_team_repository.py`
- `tests/unit/services/test_team_service.py`

**Repository tests** (similar to Country):
- Create team
- Get by ID (with eager loading)
- List all teams
- List teams filtered by country_id
- Soft delete team
- Verify soft delete filtering

**Service tests** (new: country validation):
- Create team with valid country
- Create team with non-existent country (raises InvalidCountryError)
- Create team with soft-deleted country (raises InvalidCountryError)
- Get team
- List teams with/without country filter
- Soft delete team

**Key difference from Country**: Mock CountryRepository in service tests

---

#### Task 4.3: Create Team Integration Tests ⏱️ 30 min
**File**: `tests/integration/test_team_integration.py`

**Test cases**:
1. Create team and retrieve with country relationship
2. List teams filtered by country
3. Verify FK constraint (can't create team for non-existent country)
4. Soft delete team preserves FK relationship
5. Verify eager loading (no N+1 queries)

---

## 🎯 Definition of Done

### Country Entity: 100% Complete
- [x] All critical issues fixed (datetime, unique constraint)
- [x] Alembic migration created and working
- [x] Integration tests run and passing
- [x] BDD scenarios run (passing + expected failures)
- [x] Mock warnings fixed
- [x] GitHub issues updated
- [x] Code review document exists
- [x] No deprecation warnings in test output
- [x] >90% code coverage maintained

### Team Entity: Started (if time permits)
- [ ] BDD scenarios written
- [ ] Unit tests written (failing - red phase)
- [ ] Integration tests written (failing - red phase)
- [ ] Ready for implementation in next session

---

## 📚 Reference Materials

### Files to Review Before Starting
- `docs/code-review-country-2026-01-10.md` - Today's comprehensive review
- `app/models/country.py` - Model pattern to replicate
- `app/repositories/country_repository.py` - Repository pattern
- `app/services/country_service.py` - Service pattern with validation
- `tests/unit/repositories/test_country_repository.py` - Test patterns

### GitHub Issues
- Issue #27: Country Unit Tests (to close)
- Issue #28: Country Integration Tests (to close)
- Issue #29: Country Implementation (to update)
- Issue #30: Team BDD Scenarios (next)
- Issue #31: Team Unit Tests (next)
- Issue #32: Team Integration Tests (next)
- Issue #33: Team Implementation (future)

### Documentation
- `CLAUDE.md` - Project guidelines and TDD philosophy
- `docs/adr/001-use-uuids-for-primary-keys.md` - Architecture decisions
- `docs/data-model.md` - Entity relationships
- `docs/testing/pytest-ini-explained.md` - Testing configuration

---

## ⚠️ Common Pitfalls to Avoid

### From Country Implementation Experience
1. **Don't skip migration creation** - Integration tests will fail
2. **Don't ignore deprecation warnings** - Fix them immediately
3. **Don't mock what you should test** - Use real DB in integration tests
4. **Don't skip running tests** - Docker + Testcontainers must be verified
5. **Don't forget unique constraints** - Database should enforce rules

### For Team Implementation
1. **Eager loading is critical** - Avoid N+1 queries from start
2. **Validate country in service layer** - Not in repository
3. **Test FK constraints** - Integration tests should verify DB constraints
4. **Mock both repositories** - Service tests need CountryRepository mock too
5. **Nested schemas** - Response schema must include CountryResponse

---

## 📊 Time Estimates

### Minimum Session (Country Completion Only)
- Fix critical issues: 20 min
- Run verification tests: 15 min
- Update GitHub issues: 10 min
- **Total: 45 minutes**

### Optimal Session (Country + Start Team)
- Fix critical issues: 20 min
- Run verification tests: 15 min
- Update GitHub issues: 10 min
- Team BDD scenarios: 30 min
- Team unit tests: 45 min
- Team integration tests: 30 min
- **Total: 2.5 hours**

### Full Session (Country + Team Tests Complete)
- All of the above: 2.5 hours
- Buffer for debugging: 30 min
- **Total: 3 hours**

---

## 🎯 Success Metrics

### Session Success Criteria
- [ ] Zero deprecation warnings in test output
- [ ] All integration tests passing with real PostgreSQL
- [ ] BDD scenarios document business requirements
- [ ] GitHub issues accurately reflect completion status
- [ ] Alembic migration working
- [ ] Code coverage >90% maintained
- [ ] Clean git status (all changes committed)

### Code Quality Checks
```bash
# Run before committing
pytest tests/unit/ --cov=app --cov-report=term-missing  # >90% coverage
pytest tests/integration/ -v                             # All pass
pytest tests/features/ -v                                # Expected failures documented
ruff check app/                                          # No linting errors (if configured)
mypy app/                                                # No type errors (if configured)
```

---

## 💡 Session Flow Recommendation

### Recommended Order
1. ☕ **Start with quick wins** (datetime fix, unique constraint) - Build momentum
2. 🗄️ **Create migration** - Unlock integration testing
3. 🧪 **Run all tests** - Verify everything works end-to-end
4. 📝 **Update issues** - Document progress and blockers
5. 🚀 **Start Team entity** - Only if >1 hour remains and energy is high

### Don't Start Team Entity If:
- Country entity has any failing tests (other than NotImplementedError)
- Integration tests haven't been run
- Deprecation warnings still present
- Less than 1 hour available
- Feeling rushed or tired

---

## 🔄 Next Next Session Preview

### After This Session, Next Will Be:
**If Country completed, Team started**:
- Continue Team implementation (model → repository → service)
- Run Team tests until green
- Create Team API endpoints (optional)

**If Country completed, Team not started**:
- Team BDD scenarios
- Team unit tests
- Team integration tests
- Team implementation

---

## 📌 Important Reminders

1. **Test-first is non-negotiable** - Write tests before implementation
2. **NotImplementedError is a feature** - Failing tests document blockers
3. **Docker must be running** - Integration tests require Testcontainers
4. **Git commit frequently** - After each completed task
5. **Update issues honestly** - Reflect actual status, not aspirations

---

**Session Goal**: Leave Country entity in **production-ready state** with zero technical debt.

**Stretch Goal**: Begin Team entity test suite (BDD + unit + integration).

**Success Metric**: Can confidently demo Country CRUD operations to interviewer using real PostgreSQL database.

---

*Document created*: 2026-01-10
*For session*: 2026-01-11
*Estimated duration*: 45 min (minimum) to 3 hours (optimal)
*Status*: Ready to execute
