# Next Session Plan: Phase 2 - Fight Entity Implementation

**Date**: 2026-01-12 (or next development session)
**Phase**: 2 - Fight Tracking System
**Prerequisites**: ✅ Phase 1 complete (Country, Team, Fighter entities)
**Estimated Time**: 6-7 hours (with breaks)
**Difficulty**: High (many-to-many relationships, transactions, business rules)

---

## 🎯 Session Goal

**Implement Fight and FightParticipation entities following strict TDD discipline**

By end of session:
- [ ] 60+ new tests written and passing
- [ ] Fight entity fully functional (CRUD + business rules)
- [ ] FightParticipation junction table working
- [ ] Transactional fight creation (atomic Fight + Participations)
- [ ] All Phase 1 tests still passing (no regressions)
- [ ] 2 Alembic migrations created
- [ ] API endpoints functional

---

## 📋 Pre-Session Checklist

### Verify Prerequisites

```bash
# 1. Check Phase 1 tests still passing
pytest tests/unit/ -v
# Expected: 130 tests passing

# 2. Check git status clean
git status
# Should show all Phase 1 work committed

# 3. Check you're on correct branch
git branch
# Recommend creating feature branch: git checkout -b feature/fight-entity

# 4. Review Phase 2 implementation plan
cat planning/IMPLEMENTATION_PLAN_PHASE2.md
# Read through to understand scope
```

### Mental Preparation

**Key Mindset**:
- 🔴 **RED first** - Write failing tests before any implementation
- ✅ **GREEN next** - Write minimal code to pass tests
- ♻️ **REFACTOR last** - Clean up while keeping tests green
- 🚫 **Never skip tests** - Every feature needs tests first

**This Phase is Different**:
- Phase 1: Simple CRUD with linear FKs (Fighter → Team → Country)
- **Phase 2**: Complex relationships, transactions, business rules
- Expect to spend more time on validation logic
- Transactions are critical - test rollback behavior

---

## 📖 Session Flow (6-7 hours)

### Part 1: Fight BDD Scenarios (45 min) 🔴 RED

**Goal**: Document all business requirements in Gherkin

**File**: `tests/features/fight_management.feature`

**What to write**:
1. Happy path scenarios (create singles fight, team fight)
2. Validation errors (future date, missing location, <2 participants)
3. Business rules (both sides represented, no duplicate fighters, 1 captain/side)
4. Edge cases (null winner, no video URL)
5. Transaction scenarios (rollback when participant invalid)

**Key Scenarios** (must include):
```gherkin
Scenario: Create a singles duel fight
Scenario: Create a team fight with multiple fighters per side
Scenario: Cannot create fight with future date
Scenario: Cannot create fight with only 1 participant
Scenario: Cannot create fight with participants on only 1 side
Scenario: Cannot add same fighter twice to same fight
Scenario: Cannot have multiple captains on same side
Scenario: Fight creation rolls back when participant invalid
```

**Success Criteria**:
- [ ] 20+ scenarios written
- [ ] All business rules documented
- [ ] File parses correctly: `pytest tests/features/fight_management.feature --collect-only`

**Break**: 5 min ☕

---

### Part 2: Models (40 min) 🔴 RED

**Goal**: Create SQLAlchemy models for Fight and FightParticipation

**Files**:
- `app/models/fight.py`
- `app/models/fight_participation.py`

**Fight Model** (20 min):
- Fields: id, fight_date, location, video_url, winner_side, notes, is_deleted, created_at
- Relationship to FightParticipation (one-to-many, eager loaded)
- Follow Country/Team/Fighter patterns (UUID pk, soft delete, UTC datetime)

**FightParticipation Model** (20 min):
- Fields: id, fight_id (FK), fighter_id (FK), side, role, created_at
- Enum: ParticipationRole (fighter, captain, alternate, coach)
- Constraints:
  - Unique: (fight_id, fighter_id)
  - Check: side IN (1, 2)
  - Check: role IN (valid enum values)
- Relationships: fight (many-to-one), fighter (many-to-one, eager loaded)

**Update** `app/models/__init__.py`:
```python
from app.models.fight import Fight
from app.models.fight_participation import FightParticipation, ParticipationRole
```

**Update** `app/models/fighter.py`:
```python
# Add to Fighter class
participations: Mapped[List["FightParticipation"]] = relationship(
    "FightParticipation",
    back_populates="fighter"
)
```

**Success Criteria**:
- [ ] Models created with all fields
- [ ] Relationships bidirectional
- [ ] Constraints defined
- [ ] Imports updated

**Break**: 5 min ☕

---

### Part 3: Repository Unit Tests (105 min) 🔴 RED

**Goal**: Write comprehensive repository tests (all should FAIL initially)

**Fight Repository Tests** (60 min):

**File**: `tests/unit/repositories/test_fight_repository.py`

Test classes:
```python
class TestFightRepositoryCreate:
    # test_create_fight_calls_session_methods_correctly
    # test_create_fight_with_all_fields
    # test_create_fight_with_optional_fields_omitted

class TestFightRepositoryGetById:
    # test_get_by_id_returns_fight_when_exists
    # test_get_by_id_returns_none_when_not_exists
    # test_get_by_id_filters_soft_deleted_fights
    # test_get_by_id_with_participations_eager_loaded

class TestFightRepositoryList:
    # test_list_all_excludes_soft_deleted_fights
    # test_list_by_date_range
    # test_list_by_fighter

class TestFightRepositoryUpdate:
    # test_update_fight_location
    # test_update_fight_winner_side

class TestFightRepositorySoftDelete:
    # test_soft_delete_sets_is_deleted_flag
    # test_soft_delete_returns_false_when_not_exists
```

**Target**: 25+ tests

**FightParticipation Repository Tests** (45 min):

**File**: `tests/unit/repositories/test_fight_participation_repository.py`

Test classes:
```python
class TestFightParticipationRepositoryCreate:
    # test_create_participation_calls_session_methods
    # test_create_participation_with_all_fields

class TestFightParticipationRepositoryGetById:
    # test_get_by_id_returns_participation_when_exists
    # test_get_by_id_returns_none_when_not_exists

class TestFightParticipationRepositoryList:
    # test_list_by_fight
    # test_list_by_fighter

class TestFightParticipationRepositoryDelete:
    # test_delete_participation (hard delete for junction table)
```

**Target**: 20+ tests

**Success Criteria**:
- [ ] 45+ repository tests written
- [ ] All tests use AsyncMock for session
- [ ] All tests FAIL (ImportError or NotImplementedError)
- [ ] Verify: `pytest tests/unit/repositories/test_fight*.py -v` (all FAIL)

**Break**: 10 min ☕ + stretch

---

### Part 4: Service Unit Tests (90 min) 🔴 RED

**Goal**: Write service tests for business logic

**File**: `tests/unit/services/test_fight_service.py`

**Critical Test Classes**:

```python
class TestFightServiceValidation:
    """Business rule validation"""
    # test_create_fight_with_future_date_raises_error
    # test_create_fight_with_empty_location_raises_error
    # test_create_fight_with_less_than_2_participants_raises_error
    # test_create_fight_with_only_one_side_raises_error
    # test_create_fight_with_duplicate_fighter_raises_error
    # test_create_fight_with_multiple_captains_same_side_raises_error
    # test_create_fight_with_nonexistent_fighter_raises_error

class TestFightServiceTransactions:
    """Transactional behavior"""
    # test_create_fight_calls_repos_in_transaction
    # test_transaction_rolls_back_on_validation_error
    # test_transaction_rolls_back_on_fighter_not_found

class TestFightServiceHappyPath:
    """Successful operations"""
    # test_create_singles_fight_succeeds
    # test_create_team_fight_with_captains_succeeds
    # test_get_fight_by_id
    # test_list_fights
    # test_update_fight
    # test_delete_fight
```

**Target**: 35+ tests

**Key Points**:
- Mock FightRepository, FightParticipationRepository, FighterRepository
- Test all validation rules thoroughly
- Test transaction coordination (service creates fight + participations)
- Test error handling

**Success Criteria**:
- [ ] 35+ service tests written
- [ ] All validation rules tested
- [ ] Transaction behavior tested
- [ ] All tests FAIL (NotImplementedError)
- [ ] Verify: `pytest tests/unit/services/test_fight_service.py -v` (all FAIL)

**Break**: 15 min ☕ + walk around

---

### Part 5: Repository Implementation (75 min) ✅ GREEN

**Goal**: Implement repositories to make tests pass

**Fight Repository** (45 min):

**File**: `app/repositories/fight_repository.py`

Implement methods:
```python
class FightRepository:
    async def create(fight_data: dict) -> Fight
    async def get_by_id(fight_id: UUID) -> Optional[Fight]
    async def list_all() -> List[Fight]
    async def list_by_date_range(start: date, end: date) -> List[Fight]
    async def list_by_fighter(fighter_id: UUID) -> List[Fight]
    async def update(fight_id: UUID, data: dict) -> Optional[Fight]
    async def soft_delete(fight_id: UUID) -> bool
```

**Key Details**:
- Use `selectinload(Fight.participations)` for eager loading
- Filter soft-deleted: `Fight.is_deleted == False`
- Order by `fight_date.desc()` in list methods

**FightParticipation Repository** (30 min):

**File**: `app/repositories/fight_participation_repository.py`

Implement methods:
```python
class FightParticipationRepository:
    async def create(data: dict) -> FightParticipation
    async def get_by_id(participation_id: UUID) -> Optional[FightParticipation]
    async def list_by_fight(fight_id: UUID) -> List[FightParticipation]
    async def list_by_fighter(fighter_id: UUID) -> List[FightParticipation]
    async def delete(participation_id: UUID) -> bool  # Hard delete
```

**Run tests frequently**:
```bash
# Watch tests turn GREEN
pytest tests/unit/repositories/test_fight_repository.py -v
pytest tests/unit/repositories/test_fight_participation_repository.py -v
```

**Success Criteria**:
- [ ] All repository tests PASSING ✅
- [ ] No regressions in Phase 1 tests
- [ ] Code follows Phase 1 patterns

**Break**: 10 min ☕

---

### Part 6: Service Implementation (90 min) ✅ GREEN

**Goal**: Implement Fight service with business logic

**File**: `app/services/fight_service.py`

**Critical Method**:
```python
async def create_fight_with_participants(
    self,
    fight_data: dict,
    participations: List[ParticipationData],
    session: AsyncSession
) -> Fight:
    """Create fight + participants in single transaction."""
    async with session.begin():  # Transaction boundary!
        # 1. Validate fight data
        await self._validate_fight_data(fight_data)

        # 2. Validate participations
        await self._validate_participations(participations)

        # 3. Create fight
        fight = await self.fight_repo.create(fight_data)

        # 4. Create participations
        for p in participations:
            await self.participation_repo.create({
                "fight_id": fight.id,
                "fighter_id": p.fighter_id,
                "side": p.side,
                "role": p.role
            })

        # 5. Reload with participations
        return await self.fight_repo.get_by_id(fight.id)
```

**Validation Methods**:
```python
async def _validate_fight_data(fight_data: dict):
    # Date not in future
    # Location not empty
    # Winner side 1, 2, or None

async def _validate_participations(participations: List[ParticipationData]):
    # At least 2 participants
    # Both sides represented (1 and 2)
    # No duplicate fighters
    # Max 1 captain per side
    # All fighters exist (call fighter_repo.get_by_id)
```

**Other Methods**:
```python
async def get_fight(fight_id: UUID) -> Fight
async def list_fights() -> List[Fight]
async def list_fights_by_date_range(start: date, end: date) -> List[Fight]
async def list_fights_by_fighter(fighter_id: UUID) -> List[Fight]
async def update_fight(fight_id: UUID, data: dict) -> Fight
async def delete_fight(fight_id: UUID) -> None
```

**Run tests**:
```bash
pytest tests/unit/services/test_fight_service.py -v
# All tests should PASS ✅
```

**Success Criteria**:
- [ ] All service tests PASSING ✅
- [ ] All validation rules enforced
- [ ] Transaction handling correct
- [ ] Custom exceptions raised

**Break**: 15 min ☕ + celebrate turning tests GREEN! 🎉

---

### Part 7: Migrations, Schemas, API (100 min) ✅ GREEN

**Alembic Migrations** (20 min):

```bash
# Generate migrations
alembic revision --autogenerate -m "create_fights_table_with_soft_delete"
alembic revision --autogenerate -m "create_fight_participations_junction_table"

# Review generated migrations
# Verify: columns, constraints, indexes, foreign keys

# Apply migrations (if Docker available)
alembic upgrade head
```

**Pydantic Schemas** (30 min):

**Files**:
- `app/schemas/fight.py`
- `app/schemas/fight_participation.py`

Create schemas:
```python
# app/schemas/fight.py
class FightCreate(BaseModel):
    fight_date: date
    location: str = Field(..., min_length=1, max_length=200)
    video_url: Optional[HttpUrl] = None
    winner_side: Optional[int] = Field(None, ge=1, le=2)
    notes: Optional[str] = None

class FightUpdate(BaseModel):
    fight_date: Optional[date] = None
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    video_url: Optional[HttpUrl] = None
    winner_side: Optional[int] = Field(None, ge=1, le=2)
    notes: Optional[str] = None

class ParticipationData(BaseModel):
    fighter_id: UUID
    side: int = Field(..., ge=1, le=2)
    role: str = Field(..., pattern="^(fighter|captain|alternate|coach)$")

class FightWithParticipantsCreate(BaseModel):
    fight: FightCreate
    participations: List[ParticipationData] = Field(..., min_items=2)

class FightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    fight_date: date
    location: str
    video_url: Optional[str]
    winner_side: Optional[int]
    notes: Optional[str]
    is_deleted: bool
    created_at: datetime
    participations: List["ParticipationResponse"]

class ParticipationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    fighter_id: UUID
    side: int
    role: str
    created_at: datetime
    fighter: "FighterResponse"  # Nested fighter data
```

**API Endpoints** (50 min):

**File**: `app/api/v1/fights.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import date
from uuid import UUID
from app.schemas.fight import FightWithParticipantsCreate, FightResponse, FightUpdate
from app.services.fight_service import FightService
from app.api.dependencies import get_fight_service

router = APIRouter(prefix="/fights", tags=["fights"])

@router.post("/", response_model=FightResponse, status_code=status.HTTP_201_CREATED)
async def create_fight_with_participants(
    data: FightWithParticipantsCreate,
    service: FightService = Depends(get_fight_service)
):
    """Create a fight with participants in single transaction."""
    try:
        fight = await service.create_fight_with_participants(
            fight_data=data.fight.dict(),
            participations=data.participations,
            session=service.session
        )
        return fight
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FighterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{fight_id}", response_model=FightResponse)
async def get_fight(
    fight_id: UUID,
    service: FightService = Depends(get_fight_service)
):
    """Get fight by ID with participants."""
    try:
        return await service.get_fight(fight_id)
    except FightNotFoundError:
        raise HTTPException(status_code=404, detail="Fight not found")

@router.get("/", response_model=List[FightResponse])
async def list_fights(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    fighter_id: Optional[UUID] = None,
    service: FightService = Depends(get_fight_service)
):
    """List fights with optional filters."""
    if start_date and end_date:
        return await service.list_fights_by_date_range(start_date, end_date)
    elif fighter_id:
        return await service.list_fights_by_fighter(fighter_id)
    else:
        return await service.list_fights()

@router.patch("/{fight_id}", response_model=FightResponse)
async def update_fight(
    fight_id: UUID,
    data: FightUpdate,
    service: FightService = Depends(get_fight_service)
):
    """Update fight details."""
    try:
        return await service.update_fight(fight_id, data.dict(exclude_unset=True))
    except FightNotFoundError:
        raise HTTPException(status_code=404, detail="Fight not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{fight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fight(
    fight_id: UUID,
    service: FightService = Depends(get_fight_service)
):
    """Soft delete a fight."""
    try:
        await service.delete_fight(fight_id)
    except FightNotFoundError:
        raise HTTPException(status_code=404, detail="Fight not found")
```

**Update**: `app/main.py`

```python
from app.api.v1 import fights

app.include_router(fights.router, prefix="/api/v1")
```

**Test endpoints** (manual):
```bash
# Start FastAPI app
uvicorn app.main:app --reload

# Open browser
http://localhost:8000/docs
# Test endpoints in Swagger UI
```

**Success Criteria**:
- [ ] 2 migrations created and reviewed
- [ ] Schemas created with validation
- [ ] All API endpoints functional
- [ ] OpenAPI docs generated
- [ ] Manual testing successful

---

### Part 8: Final Testing & Commit (20 min)

**Run Full Test Suite**:

```bash
# Run all unit tests
pytest tests/unit/ -v

# Expected:
# - 130 Phase 1 tests PASSING
# - ~60 Phase 2 tests PASSING
# - Total: ~190 tests PASSING

# Run integration tests (if Docker available)
pytest tests/integration/ -v

# Run BDD scenarios (if Docker available)
pytest tests/step_defs/ -v
```

**Git Commit**:

```bash
git add .
git status  # Review changes

git commit -m "$(cat <<'EOF'
Implement Fight and FightParticipation entities (TDD complete)

Phase 2: Fight tracking system with many-to-many relationships

## Models
- Created Fight model (date, location, video_url, winner_side, notes)
- Created FightParticipation junction table (side, role enum)
- Configured bidirectional relationships with eager loading
- Database constraints: unique (fight_id, fighter_id), check (side, role)

## Repositories
- FightRepository: CRUD + list_by_date_range + list_by_fighter
- FightParticipationRepository: CRUD + list_by_fight + list_by_fighter
- Soft delete filtering for fights
- Eager loading configured (prevent N+1 queries)

## Services
- FightService: Aggregate pattern for Fight + Participations
- Transactional fight creation (atomic operations)
- Business rule validation:
  * At least 2 participants required
  * Both sides must have participants
  * No duplicate fighters in same fight
  * Maximum 1 captain per side
  * Fight date cannot be in future
  * Location is required
- Custom exceptions for validation errors

## Tests
- 25+ Fight repository unit tests
- 20+ FightParticipation repository unit tests
- 35+ Fight service unit tests
- 20+ BDD scenarios for fight management
- All tests passing (GREEN phase)
- Transaction rollback behavior tested
- No regressions in Phase 1 tests

## Migrations
- Created migration for fights table (indexes, soft delete)
- Created migration for fight_participations table (constraints)
- Foreign key cascade behavior configured

## API Endpoints
- POST /api/v1/fights - Create fight with participants
- GET /api/v1/fights/{id} - Get fight by ID
- GET /api/v1/fights - List fights (with date/fighter filters)
- PATCH /api/v1/fights/{id} - Update fight
- DELETE /api/v1/fights/{id} - Soft delete fight

## Schemas
- Pydantic v2 schemas with validation
- Nested schemas for responses (fight includes participations)
- Request validation (date format, URL format, enum values)

Test Results: 190/190 unit tests passing (130 Phase 1 + 60 Phase 2)
Code Coverage: >90% across all layers

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"

git log --oneline -5  # Verify commit
```

**Success Criteria**:
- [ ] All 190 unit tests passing
- [ ] No regressions in Phase 1
- [ ] Code committed with descriptive message
- [ ] Git history clean

---

## 🎉 Session Complete!

### What You Accomplished

✅ Fight entity fully implemented
✅ FightParticipation junction table working
✅ 60+ new tests written and passing
✅ Complex business rules enforced
✅ Transactional fight creation
✅ API endpoints functional
✅ Phase 1 tests still passing (no regressions)

### Metrics

- **Time Spent**: ~6-7 hours (estimate)
- **Tests Added**: ~60 (Fight + FightParticipation)
- **Total Tests**: ~190 (Phase 1 + Phase 2)
- **Lines of Code**: ~2,100 (models, repos, services, tests, schemas, API)
- **Migrations**: 2

### Next Phase Preview

**Phase 3: Tag System** (8-10 hours estimated)
- TagType (reference data)
- Tag (hierarchical tagging)
- TagChangeRequest (community voting)
- Vote (session-based anonymous voting)

---

## 🚨 If You Encounter Issues

### Tests Not Passing

1. **Read the error message carefully**
2. **Check Phase 1 code** for similar patterns
3. **Verify mock setup** (AsyncMock vs MagicMock)
4. **Run single test** to isolate: `pytest tests/unit/services/test_fight_service.py::TestClass::test_name -v`

### Transaction Issues

1. **Verify `async with session.begin()`** wraps entire operation
2. **Check service calls** both fight_repo and participation_repo
3. **Test rollback** by raising error mid-transaction

### Import Errors

1. **Check `__init__.py`** imports updated
2. **Verify relative imports** correct
3. **Restart Python interpreter** if needed

### Performance Issues

1. **Check eager loading** configured (`selectinload`)
2. **Profile queries** (add SQL logging)
3. **Verify indexes** on foreign keys

---

## 📚 Reference Materials

**Documentation**:
- `planning/IMPLEMENTATION_PLAN_PHASE2.md` - Detailed implementation guide
- `planning/AUTONOMOUS_EXECUTION_PROGRESS.md` - Progress tracking
- `buhurt Fight Tracker - Engineering Implementation.md` - Phase 2 overview (lines 614-711)
- `CLAUDE.md` - Project patterns and lessons learned

**Phase 1 Code** (reference patterns):
- `app/models/fighter.py` - Model pattern
- `app/repositories/fighter_repository.py` - Repository pattern
- `app/services/fighter_service.py` - Service pattern (dual repos)
- `tests/unit/services/test_fighter_service.py` - Service test pattern

**Key Patterns**:
- Aggregate Pattern: Fight + Participations
- Dual Repository Service: FightService uses 3 repos
- Transaction Management: `async with session.begin()`
- Eager Loading: `selectinload(Fight.participations)`

---

## ⏰ Session Timing

| Phase | Activity | Time | Running Total |
|-------|----------|------|---------------|
| 1 | BDD Scenarios | 45 min | 0:45 |
| - | Break | 5 min | 0:50 |
| 2 | Models | 40 min | 1:30 |
| - | Break | 5 min | 1:35 |
| 3 | Repository Tests | 105 min | 3:20 |
| - | Break | 10 min | 3:30 |
| 4 | Service Tests | 90 min | 5:00 |
| - | Break | 15 min | 5:15 |
| 5 | Repository Impl | 75 min | 6:30 |
| - | Break | 10 min | 6:40 |
| 6 | Service Impl | 90 min | 8:10 |
| - | Break | 15 min | 8:25 |
| 7 | Migrations/Schemas/API | 100 min | 10:05 |
| 8 | Testing & Commit | 20 min | 10:25 |

**Total Active Time**: ~9.5 hours
**With breaks**: ~10.5 hours
**Realistic (based on Phase 1 velocity)**: **6-7 hours**

**Recommendation**: Split into 2 sessions if needed:
- Session A: Steps 1-4 (write all tests) - 4 hours
- Session B: Steps 5-8 (implementation) - 3 hours

---

**Document Status**: Ready to Execute
**Created**: 2026-01-12
**Prerequisites**: Phase 1 Complete ✅
**Estimated Time**: 6-7 hours

**Remember: RED → GREEN → REFACTOR. Tests first, always!** 🎯
