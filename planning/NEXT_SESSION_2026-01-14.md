# Next Session Plan: 2026-01-14

**Previous Session**: 2026-01-13 (Team Implementation + Country Unblocking)
**Current Status**: Country and Team entities complete, ready for Fighter entity
**Estimated Time**: 3-5 hours

---

## 🎯 Session Goals

### Primary Path: Begin Fighter Entity
**If Country and Team both complete**:
- Create Fighter BDD scenarios (most complex yet - includes roles, participation)
- Create Fighter model with Team FK relationship
- Create Fighter unit tests (repository + service)
- Create Fighter integration tests
- Ready for Fighter implementation (next session)

### Alternate Path A: Add API Endpoints
**If Team just completed but want to validate before Fighter**:
- Create Country API endpoints (FastAPI router)
- Create Team API endpoints
- Integration tests for API layer
- API documentation review
- Postman/Thunder Client manual testing

### Alternate Path B: Team Polish
**If Team implementation had issues**:
- Fix any Team integration test failures
- Add missing edge case tests
- Performance optimization (eager loading, query optimization)
- Create Team API endpoints
- Complete Team before starting Fighter

---

## 📊 Expected Starting State

### Primary Path Assumptions
From previous session (2026-01-13), we expect:
- ✅ Country entity fully complete and verified
- ✅ Team entity fully implemented
- ✅ All Country methods unblocked (count_relationships, replace, permanent_delete)
- ✅ All 48 Country unit tests passing
- ✅ All 14 Country integration tests passing
- ✅ All 21 Country BDD scenarios passing
- ✅ All ~40 Team unit tests passing
- ✅ All ~10 Team integration tests passing
- ✅ All ~10 Team BDD scenarios passing
- ✅ Alembic migrations for both Country and Team applied
- ✅ Issues #27, #28, #29, #30, #31, #32, #33 CLOSED
- ⏸️ No API endpoints yet (deferred intentionally)

### Key Achievements Unlocked
- ✅ Soft delete pattern established
- ✅ Foreign key relationships working
- ✅ Eager loading preventing N+1 queries
- ✅ Service layer validation pattern established
- ✅ Testcontainers infrastructure proven
- ✅ BDD → Unit → Integration → Implementation workflow validated

---

## 📋 Detailed Tasks

## PRIMARY PATH: Fighter Entity (Full TDD Cycle)

### Phase 1: Fighter Domain Analysis ⏱️ 20 min

#### Task 1.1: Review Fighter Requirements

**From docs/domain/business-rules.md**:
- Fighters belong to exactly one Team (FK constraint)
- Fighters have a role in fights (fighter, coach, alternate)
- Fighters can participate in multiple fights
- Fighters can be on either side of a fight (side 1 or side 2)
- Fighters cannot be on both sides of the same fight
- Soft delete preserves fight participation history

**Fighter Attributes**:
- id (UUID)
- name (String 100)
- team_id (UUID FK to teams)
- is_deleted (Boolean)
- created_at (DateTime)

**Relationships**:
- team: Many-to-one with Team (eager loaded)
- fight_participations: One-to-many with FightParticipation

**Complexity Factors**:
- Fighter depends on Team which depends on Country (3-level hierarchy)
- Fighter participates in Fights (many-to-many through FightParticipation)
- Must validate team exists and is active
- Must eager load team → country for nested data

---

### Phase 2: Fighter BDD Scenarios ⏱️ 60 min

#### Task 2.1: Create Fighter BDD Feature File

**File**: `tests/features/fighter_management.feature`

This is the most complex feature file yet. Need to cover:

**Basic CRUD scenarios** (similar to Team):
1. Create fighter with valid team
2. Create fighter with non-existent team (error)
3. Create fighter with soft-deleted team (error)
4. Retrieve fighter with nested team and country data
5. List fighters filtered by team
6. Soft delete fighter preserves team relationship

**Fighter-specific scenarios** (NEW complexity):
7. List fighters filtered by country (traversing team relationship)
8. Update fighter's team (transfer between teams)
9. Prevent creating fighter with empty name
10. Retrieve fighter includes team's country data (3-level nesting)

**Example scenario structure**:
```gherkin
Feature: Fighter Management
  As a system administrator
  I want to manage fighters and their team associations
  So that I can track fighter rosters and transfers

  Background:
    Given the database is empty

  # Happy path
  Scenario: Create fighter with valid team
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    When I create a fighter "John Smith" for team "Team USA"
    Then the fighter is created successfully
    And the fighter name is "John Smith"
    And the fighter's team is "Team USA"
    And the fighter's team country is "United States"

  # Validation
  Scenario: Create fighter with non-existent team fails
    Given no team exists with name "Ghost Team"
    When I attempt to create a fighter "John Smith" for team "Ghost Team"
    Then I receive a validation error
    And the error says "Team not found"

  Scenario: Create fighter with soft-deleted team fails
    Given an active country exists with code "USA" and name "United States"
    And a soft-deleted team "Defunct Team" exists for country "USA"
    When I attempt to create a fighter "John Smith" for team "Defunct Team"
    Then I receive a validation error
    And the error says "Team is not active"

  # Relationships
  Scenario: Retrieve fighter includes nested team and country data
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    When I retrieve the fighter "John Smith"
    Then the response includes team data
    And the team data includes country data
    And the country code is "USA"

  # Filtering
  Scenario: List fighters filtered by team
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    And an active country exists with code "CAN" and name "Canada"
    And a team "Team Canada" exists for country "CAN"
    And a fighter "Bob Jones" exists for team "Team Canada"
    When I list fighters filtered by team "Team USA"
    Then I receive exactly 2 fighters
    And all fighters belong to team "Team USA"

  Scenario: List fighters filtered by country
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA Alpha" exists for country "USA"
    And a team "Team USA Beta" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA Alpha"
    And a fighter "Jane Doe" exists for team "Team USA Beta"
    And an active country exists with code "CAN" and name "Canada"
    And a team "Team Canada" exists for country "CAN"
    And a fighter "Bob Jones" exists for team "Team Canada"
    When I list fighters filtered by country "USA"
    Then I receive exactly 2 fighters
    And all fighters belong to teams from country "USA"

  # Updates
  Scenario: Transfer fighter to different team
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA Alpha" exists for country "USA"
    And a team "Team USA Beta" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA Alpha"
    When I update fighter "John Smith" to team "Team USA Beta"
    Then the fighter's team is "Team USA Beta"
    And the fighter's team country is still "United States"

  Scenario: Transfer fighter to team with different country
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And an active country exists with code "CAN" and name "Canada"
    And a team "Team Canada" exists for country "CAN"
    When I update fighter "John Smith" to team "Team Canada"
    Then the fighter's team is "Team Canada"
    And the fighter's team country is "Canada"

  # Soft delete
  Scenario: Soft delete fighter preserves team relationship
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    When I soft delete fighter "John Smith"
    Then the fighter is marked as deleted
    And the team relationship is intact
    And listing fighters excludes the deleted fighter

  # Edge cases
  Scenario: List fighters when none exist
    When I list all fighters
    Then I receive an empty list

  Scenario: Retrieve non-existent fighter
    When I retrieve a fighter with non-existent ID
    Then I receive a not found error
```

**Key complexity**: 3-level nested relationships (Fighter → Team → Country)

---

### Phase 3: Fighter Model ⏱️ 20 min

#### Task 3.1: Create Fighter Model

**File**: `app/models/fighter.py`

```python
"""
SQLAlchemy ORM model for Fighter entity.

Implements soft delete pattern with is_deleted flag.
Uses UUID primary keys and foreign key relationship to Team.
"""

from datetime import datetime, UTC
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.country import Base


class Fighter(Base):
    """
    Fighter entity with soft delete support and team relationship.

    Attributes:
        id: UUID primary key (auto-generated)
        name: Fighter name (max 100 characters)
        team_id: Foreign key to teams table (UUID)
        is_deleted: Soft delete flag (defaults to False)
        created_at: Timestamp of creation (auto-generated)

        team: Relationship to Team entity (eager loaded)
              Team relationship includes Country (2-level eager load)
    """
    __tablename__ = "fighters"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    team_id: Mapped[UUID] = mapped_column(
        ForeignKey("teams.id"),
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
    team: Mapped["Team"] = relationship(
        "Team",
        lazy="joined",  # Eager load team by default
        foreign_keys=[team_id]
    )

    def __init__(self, **kwargs):
        """
        Initialize Fighter with Python-level defaults.

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
        return f"<Fighter(id={self.id}, name='{self.name}', team_id={self.team_id}, is_deleted={self.is_deleted})>"
```

**Important**: Team model should also eager load Country, so:
- Fighter loads → Team loads → Country loads
- Single query retrieves all 3 levels (if Team uses `lazy="joined"`)

---

### Phase 4: Fighter Unit Tests ⏱️ 90 min

#### Task 4.1: Fighter Repository Unit Tests ⏱️ 45 min

**File**: `tests/unit/repositories/test_fighter_repository.py`

**Test classes**:
```python
class TestFighterRepositoryCreate:
    - test_create_fighter_calls_session_methods_correctly
    - test_create_fighter_with_team_relationship
    - test_create_fighter_handles_fk_constraint_violation

class TestFighterRepositoryGetById:
    - test_get_by_id_returns_fighter_with_eager_loaded_team
    - test_get_by_id_returns_none_when_not_exists
    - test_get_by_id_filters_soft_deleted_fighters
    - test_get_by_id_includes_nested_country_data

class TestFighterRepositoryList:
    - test_list_all_excludes_soft_deleted_fighters
    - test_list_by_team_filters_correctly
    - test_list_by_team_excludes_soft_deleted
    - test_list_by_country_traverses_team_relationship

class TestFighterRepositorySoftDelete:
    - test_soft_delete_sets_is_deleted_flag
    - test_soft_delete_preserves_team_fk

class TestFighterRepositoryUpdate:
    - test_update_fighter_name_succeeds
    - test_update_fighter_team_succeeds
    - test_update_fighter_with_non_existent_team_fails
```

**Key differences from Team tests**:
- Must test 3-level eager loading (Fighter → Team → Country)
- Must test filtering by country (joins through team)
- Must test team transfers (updating team_id)

---

#### Task 4.2: Fighter Service Unit Tests ⏱️ 45 min

**File**: `tests/unit/services/test_fighter_service.py`

**Test classes**:
```python
class TestFighterServiceCreate:
    - test_create_fighter_with_valid_team_succeeds
    - test_create_fighter_with_non_existent_team_raises_error
    - test_create_fighter_with_soft_deleted_team_raises_error
    - test_create_fighter_validates_empty_name

class TestFighterServiceRetrieve:
    - test_get_by_id_returns_fighter_with_nested_data
    - test_get_by_id_raises_not_found_error

class TestFighterServiceList:
    - test_list_fighters_by_team
    - test_list_fighters_by_country
    - test_list_all_fighters

class TestFighterServiceUpdate:
    - test_update_fighter_validates_new_team_exists
    - test_update_fighter_validates_new_team_not_deleted
    - test_update_fighter_name
    - test_transfer_fighter_to_different_team

class TestFighterServiceDelete:
    - test_delete_fighter_soft_deletes_successfully
```

**Key differences from Team service tests**:
- Must mock both FighterRepository AND TeamRepository
- Service must validate team exists and is active
- Must test team transfer logic
- Must test filtering by country (requires traversing relationships)

---

### Phase 5: Fighter Integration Tests ⏱️ 45 min

#### Task 5.1: Create Fighter Integration Tests

**File**: `tests/integration/test_fighter_integration.py`

**Key tests**:
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_fighter_and_retrieve_with_nested_relationships(db_session):
    """
    Test creating fighter and retrieving with Team and Country data.

    Verifies:
    - Foreign key relationship to Team works
    - Eager loading fetches Team
    - Team eager loading fetches Country (3-level nesting)
    """
    # Create country → team → fighter
    country_repo = CountryRepository(db_session)
    country = await country_repo.create({"name": "United States", "code": "USA"})

    team_repo = TeamRepository(db_session)
    team = await team_repo.create({
        "name": "Team USA",
        "country_id": country.id
    })

    fighter_repo = FighterRepository(db_session)
    fighter = await fighter_repo.create({
        "name": "John Smith",
        "team_id": team.id
    })

    # Retrieve and verify nested data
    retrieved = await fighter_repo.get_by_id(fighter.id)
    assert retrieved.team.name == "Team USA"
    assert retrieved.team.country.code == "USA"
    assert retrieved.team.country.name == "United States"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_fighters_filtered_by_country(db_session):
    """Test filtering fighters by country (through team relationship)."""
    # Setup: Create 2 countries with teams and fighters
    country_repo = CountryRepository(db_session)
    usa = await country_repo.create({"name": "USA", "code": "USA"})
    can = await country_repo.create({"name": "Canada", "code": "CAN"})

    team_repo = TeamRepository(db_session)
    team_usa = await team_repo.create({"name": "Team USA", "country_id": usa.id})
    team_can = await team_repo.create({"name": "Team Canada", "country_id": can.id})

    fighter_repo = FighterRepository(db_session)
    await fighter_repo.create({"name": "Fighter 1", "team_id": team_usa.id})
    await fighter_repo.create({"name": "Fighter 2", "team_id": team_usa.id})
    await fighter_repo.create({"name": "Fighter 3", "team_id": team_can.id})

    # Act: List fighters by country
    usa_fighters = await fighter_repo.list_by_country(usa.id)

    # Assert
    assert len(usa_fighters) == 2
    assert all(f.team.country_id == usa.id for f in usa_fighters)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_foreign_key_constraint_prevents_orphan_fighters(db_session):
    """
    Test that database FK constraint prevents creating fighter with non-existent team.
    """
    fighter_repo = FighterRepository(db_session)
    fake_team_id = uuid4()

    with pytest.raises(IntegrityError):
        await fighter_repo.create({
            "name": "Orphan Fighter",
            "team_id": fake_team_id
        })


@pytest.mark.integration
@pytest.mark.asyncio
async def test_transfer_fighter_to_different_team(db_session):
    """Test updating fighter's team_id (transfer between teams)."""
    # Setup: Create 2 teams, 1 fighter
    country_repo = CountryRepository(db_session)
    country = await country_repo.create({"name": "USA", "code": "USA"})

    team_repo = TeamRepository(db_session)
    team_a = await team_repo.create({"name": "Team A", "country_id": country.id})
    team_b = await team_repo.create({"name": "Team B", "country_id": country.id})

    fighter_repo = FighterRepository(db_session)
    fighter = await fighter_repo.create({"name": "John", "team_id": team_a.id})

    # Act: Transfer fighter to Team B
    await fighter_repo.update(fighter.id, {"team_id": team_b.id})

    # Assert
    updated = await fighter_repo.get_by_id(fighter.id)
    assert updated.team_id == team_b.id
    assert updated.team.name == "Team B"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_soft_delete_fighter_preserves_team_relationship(db_session):
    """
    Test that soft deleting a fighter doesn't break the team FK.
    """
    # Setup
    country_repo = CountryRepository(db_session)
    country = await country_repo.create({"name": "USA", "code": "USA"})

    team_repo = TeamRepository(db_session)
    team = await team_repo.create({"name": "Team USA", "country_id": country.id})

    fighter_repo = FighterRepository(db_session)
    fighter = await fighter_repo.create({"name": "John", "team_id": team.id})

    # Act: Soft delete
    await fighter_repo.soft_delete(fighter.id)

    # Assert: Can still retrieve with include_deleted
    deleted_fighter = await fighter_repo.get_by_id(fighter.id, include_deleted=True)
    assert deleted_fighter.is_deleted is True
    assert deleted_fighter.team.name == "Team USA"  # Relationship intact
```

**Expected**: All tests RED (no implementation yet)

---

### Phase 6: Fighter Step Definitions ⏱️ 45 min

#### Task 6.1: Create Fighter Step Definitions

**File**: `tests/step_defs/fighter_steps.py`

This will be the most complex step definition file yet because it needs to:
1. Set up 3-level data (Country → Team → Fighter)
2. Handle nested assertions (fighter.team.country.code)
3. Support filtering by both team and country
4. Handle team transfers

**Key step patterns**:
```python
from pytest_bdd import scenarios, given, when, then, parsers

scenarios('../features/fighter_management.feature')

@given(parsers.parse('a fighter "{fighter_name}" exists for team "{team_name}"'))
async def fighter_exists(context, db_session, fighter_name, team_name):
    """Create fighter for specified team."""
    # Look up team from context (created by previous step)
    team = context['teams'][team_name]

    fighter_repo = FighterRepository(db_session)
    fighter = await fighter_repo.create({
        "name": fighter_name,
        "team_id": team.id
    })

    if 'fighters' not in context:
        context['fighters'] = {}
    context['fighters'][fighter_name] = fighter


@when(parsers.parse('I list fighters filtered by country "{country_code}"'))
async def list_fighters_by_country(context, db_session, country_code):
    """List fighters filtered by country (through team relationship)."""
    country = context['countries'][country_code]

    fighter_repo = FighterRepository(db_session)
    service = FighterService(fighter_repo, TeamRepository(db_session))

    context['result'] = await service.list_fighters(country_id=country.id)


@then(parsers.parse('the fighter\'s team country is "{expected_country}"'))
def verify_fighter_team_country(context, expected_country):
    """Verify nested country data."""
    fighter = context['result']
    assert fighter.team.country.name == expected_country
```

---

### Phase 7: Verify Tests Are RED ⏱️ 10 min

#### Task 7.1: Run All Fighter Tests (Expect Failures)

```bash
# Unit tests (should fail - no implementation)
pytest tests/unit/repositories/test_fighter_repository.py -v
pytest tests/unit/services/test_fighter_service.py -v

# Integration tests (should fail - no implementation)
pytest tests/integration/test_fighter_integration.py -v

# BDD scenarios (should fail - no implementation)
pytest tests/step_defs/fighter_steps.py -v
```

**Expected**: 100% RED (all tests failing due to missing implementation)

**Verify**:
- Tests are failing for the RIGHT reasons (not found, not implemented)
- No syntax errors in test files
- Mock objects are set up correctly
- Test structure is clear and maintainable

---

### Phase 8: Update Team Methods (Blocked on Fighter) ⏱️ 20 min

Now that Fighter model is defined, we can implement Team methods that were blocked!

#### Task 8.1: Implement Team.count_relationships()

**File**: `app/repositories/team_repository.py`

```python
async def count_relationships(self, team_id: UUID) -> int:
    """
    Count fighters associated with this team.

    Returns:
        Number of active fighters for this team
    """
    from app.models.fighter import Fighter

    query = select(func.count(Fighter.id)).where(
        Fighter.team_id == team_id,
        Fighter.is_deleted == False
    )
    result = await self.session.execute(query)
    return result.scalar_one()
```

---

#### Task 8.2: Implement Team.replace()

**File**: `app/repositories/team_repository.py`

```python
async def replace(
    self,
    old_team_id: UUID,
    new_team_id: UUID
) -> int:
    """
    Replace all references to old team with new team.

    Updates all fighters that reference old_team_id to reference new_team_id.

    Args:
        old_team_id: Team to be replaced
        new_team_id: Team to replace with

    Returns:
        Number of fighters updated

    Raises:
        TeamNotFoundError: If either team doesn't exist
    """
    from app.models.fighter import Fighter

    # Validate both teams exist
    old_team = await self.get_by_id(old_team_id)
    new_team = await self.get_by_id(new_team_id)

    if not old_team:
        raise TeamNotFoundError(f"Old team {old_team_id} not found")
    if not new_team:
        raise TeamNotFoundError(f"New team {new_team_id} not found")

    # Update all fighters
    query = (
        update(Fighter)
        .where(Fighter.team_id == old_team_id)
        .values(team_id=new_team_id)
    )
    result = await self.session.execute(query)
    await self.session.commit()

    return result.rowcount
```

---

#### Task 8.3: Implement Team.permanent_delete()

**File**: `app/services/team_service.py`

```python
async def permanent_delete(self, team_id: UUID) -> None:
    """
    Permanently delete team if no fighters exist.

    Business rules:
    - Team must not have any active fighters
    - Hard delete (removes from database)

    Args:
        team_id: Team to permanently delete

    Raises:
        TeamNotFoundError: Team doesn't exist
        ValidationError: Team has active fighters
    """
    # Check if team exists
    team = await self.repository.get_by_id(team_id)
    if not team:
        raise TeamNotFoundError(f"Team {team_id} not found")

    # Check for relationships
    fighter_count = await self.repository.count_relationships(team_id)
    if fighter_count > 0:
        raise ValidationError(
            f"Cannot permanently delete team with {fighter_count} active fighters. "
            f"Soft delete recommended instead."
        )

    # Safe to permanently delete
    await self.repository.permanent_delete(team_id)
```

---

### Phase 9: Update GitHub Issues ⏱️ 15 min

#### Task 9.1: Create Fighter Issues

```bash
# Create Fighter BDD Scenarios issue
gh issue create --title "Ticket 9: Fighter BDD Scenarios" \
  --body "Create BDD scenarios for Fighter entity covering CRUD operations, team relationships, and country filtering." \
  --label "testing,bdd,fighter-feature"

# Create Fighter Unit Tests issue
gh issue create --title "Ticket 10: Fighter Unit Tests (Repository + Service)" \
  --body "Write comprehensive unit tests for Fighter repository and service layers. Must test 3-level nested relationships (Fighter → Team → Country)." \
  --label "testing,unit-test,fighter-feature"

# Create Fighter Integration Tests issue
gh issue create --title "Ticket 11: Fighter Integration Tests (Testcontainers)" \
  --body "Write integration tests using Testcontainers to verify Fighter functionality with real PostgreSQL. Test nested eager loading and team transfers." \
  --label "testing,integration-test,fighter-feature"

# Create Fighter Implementation issue
gh issue create --title "Ticket 12: Fighter Implementation (Models, Repositories, Services, API)" \
  --body "Implement Fighter entity following TDD principles. Write implementation AFTER tests are in place and failing." \
  --label "feature,implementation,fighter-feature"
```

#### Task 9.2: Update Team Issue with Blockers Resolved

```bash
# Add comment to Issue #33
gh issue comment 33 -c "✅ Team entity blockers resolved! count_relationships(), replace(), and permanent_delete() now implemented (blocked on Fighter previously)."
```

---

## ALTERNATE PATH A: API Endpoints

### Phase 1: Country API Endpoints ⏱️ 60 min

#### Task 1.1: Create Country Router

**File**: `app/api/v1/countries.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from app.schemas.country import CountryCreate, CountryResponse
from app.services.country_service import CountryService
from app.exceptions import CountryNotFoundError, DuplicateCountryCodeError

router = APIRouter(prefix="/countries", tags=["countries"])

@router.post("/", response_model=CountryResponse, status_code=status.HTTP_201_CREATED)
async def create_country(
    data: CountryCreate,
    service: CountryService = Depends(get_country_service)
):
    """Create new country."""
    try:
        country = await service.create_country(data.dict())
        return country
    except DuplicateCountryCodeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{country_id}", response_model=CountryResponse)
async def get_country(
    country_id: UUID,
    service: CountryService = Depends(get_country_service)
):
    """Retrieve country by ID."""
    try:
        country = await service.get_country(country_id)
        return country
    except CountryNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/", response_model=list[CountryResponse])
async def list_countries(
    service: CountryService = Depends(get_country_service)
):
    """List all active countries."""
    countries = await service.list_countries()
    return countries

@router.delete("/{country_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_country(
    country_id: UUID,
    service: CountryService = Depends(get_country_service)
):
    """Soft delete country."""
    try:
        await service.delete_country(country_id)
    except CountryNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

---

### Phase 2: Team API Endpoints ⏱️ 60 min

Similar structure to Country endpoints but with:
- Team depends on Country
- Must return nested Country data
- Must validate country_id in requests

---

### Phase 3: API Integration Tests ⏱️ 45 min

Test API layer using FastAPI TestClient:
- Test request validation (Pydantic)
- Test status codes (201, 200, 204, 404, 400)
- Test error responses
- Test OpenAPI docs generation

---

## 🎯 Definition of Done

### Primary Path Success (Fighter Tests Complete)
- [ ] Fighter BDD scenarios created (10-12 scenarios)
- [ ] Fighter model implemented
- [ ] Fighter unit tests created (repository + service)
- [ ] Fighter integration tests created
- [ ] Fighter step definitions implemented
- [ ] All Fighter tests FAILING (RED phase)
- [ ] Team count_relationships(), replace(), permanent_delete() implemented
- [ ] GitHub issues created for Fighter entity
- [ ] Ready for Fighter implementation next session
- [ ] Committed with descriptive message

### Alternate Path A Success (API Endpoints)
- [ ] Country API router created
- [ ] Team API router created
- [ ] API integration tests passing
- [ ] OpenAPI docs generated and reviewed
- [ ] Manual testing with Postman/Thunder Client
- [ ] Proper HTTP status codes
- [ ] Error handling converts exceptions to HTTP errors
- [ ] Committed with descriptive message

### Alternate Path B Success (Team Polish)
- [ ] All Team integration tests passing
- [ ] Team API endpoints created
- [ ] Edge case tests added
- [ ] Performance optimized
- [ ] Ready to start Fighter next session

---

## 📊 Time Estimates

### Primary Path (Fighter Tests)
- Domain analysis: 20 min
- BDD scenarios: 60 min
- Fighter model: 20 min
- Repository unit tests: 45 min
- Service unit tests: 45 min
- Integration tests: 45 min
- Step definitions: 45 min
- Verify RED: 10 min
- Unblock Team methods: 20 min
- Update issues: 15 min
- **Total: 5-6 hours**

### Alternate Path A (API Endpoints)
- Country API: 60 min
- Team API: 60 min
- API integration tests: 45 min
- Manual testing: 30 min
- Documentation review: 15 min
- **Total: 3.5 hours**

---

## 📚 Reference Materials

### Fighter Implementation Patterns
- `app/models/team.py` - FK relationship pattern
- `app/repositories/team_repository.py` - Nested eager loading
- `app/services/team_service.py` - Parent validation pattern
- `tests/unit/repositories/test_team_repository.py` - FK test patterns

### 3-Level Nesting
- SQLAlchemy nested eager loading: https://docs.sqlalchemy.org/en/20/orm/loading_relationships.html
- Relationship chaining: Fighter → Team → Country

### FastAPI Patterns
- Dependency injection: https://fastapi.tiangolo.com/tutorial/dependencies/
- Exception handling: https://fastapi.tiangolo.com/tutorial/handling-errors/
- Status codes: https://fastapi.tiangolo.com/tutorial/response-status-code/

---

## ⚠️ Common Pitfalls to Avoid

### From Team Implementation Experience

1. **3-level eager loading is tricky**
   - Make sure Team eager loads Country
   - Make sure Fighter eager loads Team
   - Result: Fighter → Team (with Country) in single query

2. **List by country requires join**
   - Must join through Team to filter by Country
   - Use SQLAlchemy join syntax or filter through relationship

3. **Service layer needs two repositories**
   - FighterService needs FighterRepository AND TeamRepository
   - Must mock both in service unit tests

4. **Test data setup is complex**
   - Must create Country → Team → Fighter in correct order
   - Use fixtures or context dict to track test data

5. **Team transfers need validation**
   - Validate new team exists and is active
   - Handle FK constraint violations gracefully

---

## 🎓 Predicted Lessons Learned

### What Will Go Well ✅
- Following Country → Team patterns makes Fighter faster
- 3-entity hierarchy validates architecture decisions
- Testcontainers handles complex relationships well
- BDD scenarios document complex business rules clearly

### What Might Be Challenging 🤔
- 3-level eager loading configuration
- Complex test data setup (3 entities)
- Service layer with 2 repository dependencies
- Step definitions with nested data assertions
- Query performance with multiple joins

### Key Insights 💡
1. Eager loading is critical at 3+ levels
2. Test fixtures save huge amounts of setup code
3. Context dict in BDD steps prevents tight coupling
4. Repository pattern makes nested relationships manageable
5. Integration tests verify query performance

---

## 🔍 Quick Command Reference

```bash
# Fighter test workflow
pytest tests/unit/repositories/test_fighter_repository.py -v
pytest tests/unit/services/test_fighter_service.py -v
pytest tests/integration/test_fighter_integration.py -v
pytest tests/step_defs/fighter_steps.py -v

# Verify all tests RED
pytest tests/unit/repositories/test_fighter_repository.py -v 2>&1 | grep FAILED | wc -l
# Should be > 0

# Create Fighter issues
gh issue create --title "Ticket 9: Fighter BDD Scenarios" --label "testing,bdd,fighter-feature"
gh issue create --title "Ticket 10: Fighter Unit Tests" --label "testing,unit-test,fighter-feature"
gh issue create --title "Ticket 11: Fighter Integration Tests" --label "testing,integration-test,fighter-feature"
gh issue create --title "Ticket 12: Fighter Implementation" --label "feature,implementation,fighter-feature"

# API testing (if Alternate Path A)
uvicorn app.main:app --reload  # Start dev server
# Test with curl or Postman
curl -X GET http://localhost:8000/api/v1/countries
curl -X POST http://localhost:8000/api/v1/countries -H "Content-Type: application/json" -d '{"name":"Test","code":"TST"}'
```

---

**Session Goal**: Create comprehensive Fighter test suite OR add API endpoints for Country/Team

**Success Metric**: Fighter entity ready for implementation (all tests RED) OR API layer working and documented

**Key Milestone**: 3-level entity hierarchy (Fighter → Team → Country)! 🎉

**Achievement Unlocked**: Complex nested relationships with eager loading! 🏆

---

*Document created*: 2026-01-10
*For session*: 2026-01-14
*Estimated duration*: 3-6 hours depending on path
*Status*: Speculative - based on expected progress from 2026-01-12 and 2026-01-13 sessions
*Confidence*: Medium (depends on two future sessions going smoothly)
