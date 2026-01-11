# Next Session Plan: 2026-01-13

**Previous Session**: 2026-01-12 (Country Verification + Team Tests Start)
**Current Status**: Country verified production-ready, Team entity tests in progress
**Estimated Time**: 2-4 hours

---

## 🎯 Session Goals

### Scenario A: Team Tests Complete (Primary Path)
**If previous session completed Team test suite**:
- Implement Team entity (repository, service, model)
- Get all Team tests passing (GREEN phase)
- Create Alembic migration for teams table
- Verify Team entity with integration tests

### Scenario B: Team Tests Incomplete (Alternate Path)
**If previous session only verified Country**:
- Complete Team BDD scenarios
- Complete Team unit tests (repository + service)
- Complete Team integration tests
- Ready for Team implementation (next session)

---

## 📊 Expected Starting State

### Scenario A Assumptions
From previous session (2026-01-12), we expect:
- ✅ Country entity verified with Docker
- ✅ All 14 Country integration tests passing
- ✅ BDD scenarios executed (~15 pass, 6 NotImplementedError)
- ✅ Issues #27 and #28 closed
- ✅ Team BDD scenarios created (`tests/features/team_management.feature`)
- ✅ Team model stub created (`app/models/team.py`)
- ✅ Team unit tests created (~30-40 tests, all RED)
- ✅ Team integration tests created (~8-10 tests, all RED)

### Scenario B Assumptions
From previous session (2026-01-12), we expect:
- ✅ Country entity verified with Docker
- ✅ All 14 Country integration tests passing
- ✅ Issues #27 and #28 closed
- ⏸️ Team tests not started (time constraint)

---

## 📋 Detailed Tasks

## SCENARIO A: Team Implementation (Primary Path)

### Phase 1: Team Repository Implementation ⏱️ 45 min

#### Task 1.1: Implement Team Repository
**File**: `app/repositories/team_repository.py`

**Methods to implement**:
```python
class TeamRepository:
    """
    Data access layer for Team entity.

    Similar to CountryRepository but includes:
    - Foreign key relationship to Country
    - Eager loading of country data
    - Filtering by country_id
    """

    async def create(self, data: dict) -> Team:
        """Create new team with country relationship."""

    async def get_by_id(
        self,
        team_id: UUID,
        include_deleted: bool = False
    ) -> Team | None:
        """Retrieve team by ID with eager-loaded country."""

    async def list_all(
        self,
        include_deleted: bool = False
    ) -> list[Team]:
        """List all teams with eager-loaded countries."""

    async def list_by_country(
        self,
        country_id: UUID,
        include_deleted: bool = False
    ) -> list[Team]:
        """List teams filtered by country_id."""

    async def update(
        self,
        team_id: UUID,
        data: dict
    ) -> Team:
        """Update team (name or country_id)."""

    async def soft_delete(self, team_id: UUID) -> None:
        """Soft delete team (preserves FK to country)."""
```

**Key Implementation Points**:
1. Use `selectinload(Team.country)` or rely on `lazy="joined"` for eager loading
2. Always filter `is_deleted = False` unless `include_deleted=True`
3. Handle FK constraint violations (IntegrityError)
4. Validate country_id exists when updating

**Run tests after implementation**:
```bash
pytest tests/unit/repositories/test_team_repository.py -v
# Expected: All repository tests GREEN
```

---

#### Task 1.2: Verify Repository Tests Pass ⏱️ 5 min

```bash
pytest tests/unit/repositories/test_team_repository.py -v --tb=short
```

**Expected Results**:
- ✅ All ~15-20 repository tests passing
- ✅ No IntegrityError leaks
- ✅ Eager loading verified

**If failures occur**:
- Check FK constraint handling
- Verify soft delete filtering
- Check async/await patterns
- Review mock assertions

---

### Phase 2: Team Service Implementation ⏱️ 60 min

#### Task 2.1: Implement Team Service
**File**: `app/services/team_service.py`

**Dependencies**: Needs both `TeamRepository` AND `CountryRepository`

**Methods to implement**:
```python
class TeamService:
    """
    Business logic layer for Team entity.

    CRITICAL: Must validate country exists and is active.
    """

    def __init__(
        self,
        team_repository: TeamRepository,
        country_repository: CountryRepository
    ):
        """Inject both repositories."""
        self.team_repo = team_repository
        self.country_repo = country_repository

    async def create_team(self, data: dict) -> Team:
        """
        Create team after validating country exists and is active.

        Business rules:
        - Country must exist
        - Country must not be soft-deleted
        - Team name must not be empty

        Raises:
            CountryNotFoundError: Country doesn't exist or is deleted
            ValidationError: Invalid team data
        """

    async def get_team(self, team_id: UUID) -> Team:
        """
        Retrieve team by ID.

        Raises:
            TeamNotFoundError: Team doesn't exist or is deleted
        """

    async def list_teams(
        self,
        country_id: UUID | None = None
    ) -> list[Team]:
        """
        List all teams, optionally filtered by country.
        """

    async def update_team(
        self,
        team_id: UUID,
        data: dict
    ) -> Team:
        """
        Update team (name or country_id).

        Business rules:
        - If updating country_id, new country must exist and be active
        - Team name must not be empty

        Raises:
            TeamNotFoundError: Team doesn't exist
            CountryNotFoundError: New country invalid
        """

    async def delete_team(self, team_id: UUID) -> None:
        """
        Soft delete team.

        Raises:
            TeamNotFoundError: Team doesn't exist
        """
```

**Key Implementation Points**:
1. **Validate country before creating/updating team**:
   ```python
   country = await self.country_repo.get_by_id(data["country_id"])
   if not country:
       raise CountryNotFoundError(f"Country {data['country_id']} not found")
   ```

2. **Create custom exceptions**:
   - Add `TeamNotFoundError` to `app/exceptions.py`
   - Reuse `CountryNotFoundError` from Country entity

3. **Validation order**:
   - Check country exists BEFORE calling team repository
   - Validate team data format
   - Then delegate to repository

**Run tests after implementation**:
```bash
pytest tests/unit/services/test_team_service.py -v
# Expected: All service tests GREEN
```

---

#### Task 2.2: Add Team Exceptions ⏱️ 5 min

**File**: `app/exceptions.py`

```python
class TeamNotFoundError(Exception):
    """Raised when team not found or soft-deleted."""
    pass
```

---

#### Task 2.3: Verify Service Tests Pass ⏱️ 5 min

```bash
pytest tests/unit/services/test_team_service.py -v --tb=short
```

**Expected Results**:
- ✅ All ~15-20 service tests passing
- ✅ Country validation working
- ✅ Proper exception handling

---

### Phase 3: Team Integration Tests ⏱️ 20 min

#### Task 3.1: Run Team Integration Tests

```bash
# Start Docker Desktop first (if not already running)
docker ps

# Run Team integration tests
pytest tests/integration/test_team_integration.py -v
```

**Expected Results**:
- ✅ All ~8-10 integration tests passing
- ✅ FK constraints enforced by database
- ✅ Eager loading prevents N+1 queries
- ✅ Soft delete preserves country relationship

**If failures occur**:
- Check Alembic migration created
- Apply migration: `alembic upgrade head`
- Verify FK constraint in database
- Check cascade behavior

---

### Phase 4: Create Alembic Migration ⏱️ 15 min

#### Task 4.1: Generate Migration

```bash
# Generate migration (Alembic detects Team model)
alembic revision --autogenerate -m "Create teams table with country foreign key"
```

**Expected Migration Content**:
```python
def upgrade():
    op.create_table(
        'teams',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('country_id', postgresql.UUID(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['country_id'],
            ['countries.id'],
            name='fk_teams_country_id'
        )
    )
    op.create_index('ix_teams_country_id', 'teams', ['country_id'])
```

**Review checklist**:
- [ ] UUID type for id and country_id
- [ ] Foreign key constraint to countries.id
- [ ] Index on country_id for query performance
- [ ] is_deleted defaults to False
- [ ] created_at has default (or handled by model)

---

#### Task 4.2: Apply Migration to Test Database ⏱️ 5 min

```bash
# Apply migration
alembic upgrade head

# Verify migration applied
alembic current

# Test rollback
alembic downgrade -1

# Re-apply
alembic upgrade head
```

---

#### Task 4.3: Re-run Integration Tests with Migration ⏱️ 5 min

```bash
pytest tests/integration/test_team_integration.py -v
```

**Verify**:
- ✅ Tests still pass with migration-created schema
- ✅ FK constraints work
- ✅ Indexes created

---

### Phase 5: Run BDD Scenarios ⏱️ 10 min

#### Task 5.1: Execute Team BDD Scenarios

```bash
pytest tests/step_defs/ -v --tb=short
```

**Expected Results**:
- ✅ All Team scenarios pass (8-10 scenarios)
- ✅ Country scenarios still pass (~15 scenarios)
- ✅ Country NotImplementedError scenarios still fail (6 scenarios - expected)

**If failures occur**:
- Check service layer country validation
- Verify FK constraint handling
- Review error messages in scenarios

---

### Phase 6: Unblock Country Methods ⏱️ 45 min

Now that Team entity exists, we can implement the blocked Country methods!

#### Task 6.1: Implement Country.count_relationships()

**File**: `app/repositories/country_repository.py`

```python
async def count_relationships(self, country_id: UUID) -> int:
    """
    Count teams associated with this country.

    Returns:
        Number of active teams for this country

    Note: Only counts non-deleted teams
    """
    from app.models.team import Team

    query = select(func.count(Team.id)).where(
        Team.country_id == country_id,
        Team.is_deleted == False
    )
    result = await self.session.execute(query)
    return result.scalar_one()
```

**Run tests**:
```bash
pytest tests/unit/repositories/test_country_repository.py::TestCountryRepositoryCountRelationships -v
# Expected: 2 tests GREEN (previously NotImplementedError)
```

---

#### Task 6.2: Implement Country.replace()

**File**: `app/repositories/country_repository.py`

```python
async def replace(
    self,
    old_country_id: UUID,
    new_country_id: UUID
) -> int:
    """
    Replace all references to old country with new country.

    Updates all teams that reference old_country_id to reference new_country_id.

    Args:
        old_country_id: Country to be replaced
        new_country_id: Country to replace with

    Returns:
        Number of teams updated

    Raises:
        CountryNotFoundError: If either country doesn't exist
    """
    from app.models.team import Team

    # Validate both countries exist
    old_country = await self.get_by_id(old_country_id)
    new_country = await self.get_by_id(new_country_id)

    if not old_country:
        raise CountryNotFoundError(f"Old country {old_country_id} not found")
    if not new_country:
        raise CountryNotFoundError(f"New country {new_country_id} not found")

    # Update all teams
    query = (
        update(Team)
        .where(Team.country_id == old_country_id)
        .values(country_id=new_country_id)
    )
    result = await self.session.execute(query)
    await self.session.commit()

    return result.rowcount
```

**Run tests**:
```bash
pytest tests/unit/repositories/test_country_repository.py::TestCountryRepositoryReplace -v
# Expected: 1 test GREEN (previously NotImplementedError)
```

---

#### Task 6.3: Implement Country.permanent_delete()

**File**: `app/services/country_service.py`

```python
async def permanent_delete(self, country_id: UUID) -> None:
    """
    Permanently delete country if no teams exist.

    Business rules:
    - Country must not have any active teams
    - Hard delete (removes from database)

    Args:
        country_id: Country to permanently delete

    Raises:
        CountryNotFoundError: Country doesn't exist
        ValidationError: Country has active teams
    """
    # Check if country exists
    country = await self.repository.get_by_id(country_id)
    if not country:
        raise CountryNotFoundError(f"Country {country_id} not found")

    # Check for relationships
    team_count = await self.repository.count_relationships(country_id)
    if team_count > 0:
        raise ValidationError(
            f"Cannot permanently delete country with {team_count} active teams. "
            f"Soft delete recommended instead."
        )

    # Safe to permanently delete
    await self.repository.permanent_delete(country_id)
```

**Run tests**:
```bash
pytest tests/unit/services/test_country_service.py::TestCountryServicePermanentDelete -v
# Expected: 3 tests GREEN (previously NotImplementedError)
```

---

#### Task 6.4: Verify All Country Tests Pass ⏱️ 5 min

```bash
# Run ALL Country tests (unit + integration + BDD)
pytest tests/unit/repositories/test_country_repository.py -v
pytest tests/unit/services/test_country_service.py -v
pytest tests/integration/test_country_repository_integration.py -v
pytest tests/step_defs/ -v
```

**Expected Results**:
- ✅ ALL 48 unit tests passing (0 NotImplementedError!)
- ✅ All 14 integration tests passing
- ✅ All 21 BDD scenarios passing (no more NotImplementedError!)
- ✅ Code coverage: ~98-99%

---

### Phase 7: Update GitHub Issues ⏱️ 15 min

#### Task 7.1: Close Country Issues

```bash
# Close Issue #27 (Country Unit Tests)
gh issue close 27 -c "✅ All 48 unit tests passing. Country entity fully tested."

# Close Issue #28 (Country Integration Tests)
gh issue close 28 -c "✅ All 14 integration tests passing. Verified with real PostgreSQL."

# Close Issue #29 (Country Implementation)
gh issue close 29 -c "✅ Country entity fully implemented. All CRUD operations working. All Team-dependent methods now unblocked."
```

#### Task 7.2: Update Team Issues

```bash
# Update Issue #30 (Team BDD Scenarios)
gh issue close 30 -c "✅ Team BDD scenarios complete. All scenarios passing."

# Update Issue #31 (Team Unit Tests)
gh issue close 31 -c "✅ Team unit tests complete. Repository: 20 tests, Service: 18 tests. All passing."

# Update Issue #32 (Team Integration Tests)
gh issue close 32 -c "✅ Team integration tests complete. 10 tests passing with real PostgreSQL."

# Update Issue #33 (Team Implementation)
gh issue close 33 -c "✅ Team entity fully implemented. Model, Repository, Service, Migration complete. All tests passing."
```

---

## SCENARIO B: Complete Team Tests (Alternate Path)

### Phase 1: Team BDD Scenarios ⏱️ 30 min

Follow the structure outlined in NEXT_SESSION.md (lines 125-139).

**File**: `tests/features/team_management.feature`

Create 8-10 scenarios covering:
- Create team with valid country
- Create team with non-existent country (error)
- Create team with soft-deleted country (error)
- Retrieve team with nested country data
- List teams filtered by country
- Soft delete team preserves relationship
- Update team name
- Update team country

---

### Phase 2: Team Model ⏱️ 15 min

Follow the structure outlined in NEXT_SESSION.md (lines 141-153).

**File**: `app/models/team.py`

Implement Team model with:
- UUID primary key
- name, country_id, is_deleted, created_at
- Relationship to Country (eager loaded)

---

### Phase 3: Team Unit Tests ⏱️ 90 min

**Files**:
- `tests/unit/repositories/test_team_repository.py` (45 min)
- `tests/unit/services/test_team_service.py` (45 min)

Follow patterns from Country tests. Key differences:
- Repository tests verify FK constraints
- Repository tests verify eager loading
- Service tests mock BOTH TeamRepository AND CountryRepository
- Service tests validate country exists and is active

---

### Phase 4: Team Integration Tests ⏱️ 30 min

**File**: `tests/integration/test_team_integration.py`

Create 8-10 integration tests covering:
- CRUD operations with real database
- FK constraint enforcement
- Eager loading verification
- Soft delete preservation

---

## 🎯 Definition of Done

### Scenario A Success
- [ ] Team repository implemented and all tests GREEN
- [ ] Team service implemented and all tests GREEN
- [ ] Team integration tests passing with real PostgreSQL
- [ ] Alembic migration created and applied
- [ ] Team BDD scenarios all passing
- [ ] Country `count_relationships()` implemented and tested
- [ ] Country `replace()` implemented and tested
- [ ] Country `permanent_delete()` implemented and tested
- [ ] ALL 48 Country unit tests passing (0 NotImplementedError)
- [ ] ALL 21 Country BDD scenarios passing
- [ ] Issues #27, #28, #29, #30, #31, #32, #33 CLOSED
- [ ] Committed with descriptive message

### Scenario B Success
- [ ] Team BDD scenarios complete (8-10 scenarios)
- [ ] Team model implemented
- [ ] Team unit tests complete (repository + service)
- [ ] Team integration tests complete
- [ ] All Team tests FAILING (RED phase)
- [ ] Ready for Team implementation next session
- [ ] Committed with descriptive message

---

## 📊 Time Estimates

### Scenario A (Team Implementation)
- Repository: 45 min
- Service: 60 min
- Integration verification: 20 min
- Alembic migration: 15 min
- BDD scenarios: 10 min
- Unblock Country methods: 45 min
- Update GitHub issues: 15 min
- **Total: 3.5-4 hours**

### Scenario B (Team Tests)
- BDD scenarios: 30 min
- Team model: 15 min
- Repository tests: 45 min
- Service tests: 45 min
- Integration tests: 30 min
- **Total: 2.5-3 hours**

---

## 📚 Reference Materials

### Team Implementation Patterns
- `app/models/country.py` - Model structure
- `app/repositories/country_repository.py` - Repository patterns
- `app/services/country_service.py` - Service patterns
- `tests/unit/repositories/test_country_repository.py` - Test patterns

### Foreign Key Implementation
- SQLAlchemy relationships: https://docs.sqlalchemy.org/en/20/orm/relationships.html
- Eager loading: https://docs.sqlalchemy.org/en/20/orm/loading_relationships.html
- FK constraints: https://docs.sqlalchemy.org/en/20/core/constraints.html

### Alembic Migration
- Foreign keys: https://alembic.sqlalchemy.org/en/latest/ops.html#alembic.operations.Operations.create_foreign_key
- Indexes: https://alembic.sqlalchemy.org/en/latest/ops.html#alembic.operations.Operations.create_index

---

## ⚠️ Common Pitfalls to Avoid

### From Country Implementation Experience

1. **Don't forget country validation in service layer**
   - Service must check country exists AND is active
   - Do this BEFORE calling team repository

2. **Mock both repositories in service tests**
   - TeamService needs TeamRepository AND CountryRepository mocked
   - Don't forget to mock country validation calls

3. **Test FK constraints in integration tests**
   - Verify database prevents orphan teams
   - Test with non-existent country_id

4. **Eager load by default**
   - Use `lazy="joined"` in relationship
   - Prevents N+1 queries when listing teams

5. **Soft delete filtering**
   - Filter teams by `is_deleted = False`
   - Filter countries by `is_deleted = False` in validation

6. **Handle IntegrityError**
   - Catch and convert to meaningful error message
   - Don't let database errors leak to API

---

## 🎓 Predicted Lessons Learned

### What Will Go Well ✅
- Following Country patterns makes Team implementation faster
- Test-first approach catches FK constraint issues early
- Alembic autogenerate handles FK relationships well
- Unblocking Country methods feels satisfying

### What Might Be Challenging 🤔
- Mocking two repositories in service tests
- Understanding eager loading behavior
- Deciding when to validate FK vs relying on DB constraint
- Handling cascade deletes (soft vs hard)

### Key Insights 💡
1. Service layer validation catches issues before database
2. Eager loading is critical for performance
3. FK constraints provide safety net
4. Integration tests verify real relationships
5. Unblocking dependent code validates architecture decisions

---

## 🔍 Quick Command Reference

```bash
# Implementation workflow
pytest tests/unit/repositories/test_team_repository.py -v --tb=short
pytest tests/unit/services/test_team_service.py -v --tb=short
pytest tests/integration/test_team_integration.py -v

# Alembic migration
alembic revision --autogenerate -m "Create teams table with country FK"
alembic upgrade head
alembic current

# Verify unblocked Country methods
pytest tests/unit/repositories/test_country_repository.py::TestCountryRepositoryCountRelationships -v
pytest tests/unit/repositories/test_country_repository.py::TestCountryRepositoryReplace -v
pytest tests/unit/services/test_country_service.py::TestCountryServicePermanentDelete -v

# Full test suite
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/step_defs/ -v

# Code coverage
pytest tests/unit/ --cov=app --cov-report=term-missing

# Close issues
gh issue close 27 28 29 30 31 32 33 -c "✅ Country and Team entities complete"
```

---

**Session Goal**: Implement Team entity OR complete Team test suite

**Success Metric**: Team entity fully functional with all tests GREEN (Scenario A) OR Team tests complete and ready for implementation (Scenario B)

**Key Milestone**: First entity with foreign key relationships! 🎉

---

*Document created*: 2026-01-10
*For session*: 2026-01-13
*Estimated duration*: 2.5-4 hours depending on scenario
*Status*: Speculative - based on expected progress from 2026-01-12 session
