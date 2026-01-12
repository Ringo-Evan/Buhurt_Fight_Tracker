# Implementation Plan: Phase 2 - Fight Entity & Fight Participation

**Created**: 2026-01-12
**Author**: Claude Sonnet 4.5
**Status**: Ready to Execute
**Prerequisites**: ✅ Country, Team, Fighter entities complete (Phase 1)
**Estimated Time**: 6-8 hours (based on Phase 1 velocity)

---

## Executive Summary

Phase 2 implements the **Fight** and **FightParticipation** entities, representing the core domain logic of tracking Buhurt fights. This phase introduces:

- **Many-to-many relationships** (Fight ↔ Fighter via FightParticipation junction table)
- **Transactional complexity** (Fight + multiple Participations created atomically)
- **Business rules** (max 2 sides, role validation, no duplicate fighters)
- **Aggregate patterns** (Fight as aggregate root, Participations as children)

**Key Difference from Phase 1**: Phase 1 entities were simple CRUD with linear foreign keys (Fighter → Team → Country). Phase 2 introduces complex relationships and transactional boundaries.

---

## Prerequisites Check

Before starting Phase 2, verify:

- ✅ Phase 1 complete: Country, Team, Fighter entities implemented
- ✅ All 130 unit tests passing
- ✅ Alembic initialized with 3 migrations created
- ✅ TDD patterns established and proven
- ✅ Git history clean with descriptive commits

If any prerequisites fail, complete Phase 1 first.

---

## Entity Overview

### Fight Entity

**Purpose**: Represents a single Buhurt fight event (singles duel, team melee, profights, etc.)

**Core Fields**:
- `id`: UUID primary key
- `fight_date`: Date (not datetime - historical fights rarely have exact times)
- `location`: VARCHAR(200) - simple string like "IMCF World Championship 2024, Warsaw, Poland"
- `video_url`: VARCHAR(500) - optional link to fight footage
- `winner_side`: INTEGER (1, 2, or NULL for draw/unknown)
- `notes`: TEXT - optional fight description
- `is_deleted`: BOOLEAN - soft delete flag
- `created_at`: DATETIME - audit timestamp

**Relationships**:
- Has many `FightParticipation` (bidirectional)
- Participations link to Fighters

**Business Rules**:
1. Fight date cannot be in the future
2. Winner side must be 1, 2, or NULL (validated at service layer)
3. Location is required (cannot be empty)
4. Video URL format validation (if provided)
5. Cannot soft-delete fight with pending tag change requests (future phase)

---

### FightParticipation Entity (Junction Table)

**Purpose**: Links Fighters to Fights with additional metadata (side, role)

**Core Fields**:
- `id`: UUID primary key
- `fight_id`: UUID FK to fights table (NOT NULL)
- `fighter_id`: UUID FK to fighters table (NOT NULL)
- `side`: INTEGER (1 or 2) - which side fighter was on
- `role`: ENUM ('fighter', 'captain', 'alternate', 'coach') - participation type
- `created_at`: DATETIME - audit timestamp

**Relationships**:
- Belongs to `Fight` (many-to-one)
- Belongs to `Fighter` (many-to-one)

**Constraints**:
1. Composite unique: (fight_id, fighter_id) - fighter can't be in same fight twice
2. Check constraint: side IN (1, 2)
3. FK cascade: ON DELETE CASCADE (if fight deleted, participations cascade)

**Business Rules**:
1. Fight must have at least 2 participants (validated at service layer)
2. Fight must have participants on both sides (1 and 2)
3. Each side must have at least 1 participant
4. Fighter cannot be on both sides of same fight
5. Only 1 captain per side (validated at service layer)
6. Coach doesn't count toward minimum fighter requirements

---

## Architecture Patterns

### Aggregate Pattern

**Fight is an Aggregate Root**:
- Fight and its Participations form a transactional boundary
- Always create/update Fight + Participations together
- Service layer orchestrates both repositories in single transaction
- Repository layer focuses on data access only

**Example Service Pattern**:
```python
class FightService:
    def __init__(
        self,
        fight_repo: FightRepository,
        participation_repo: FightParticipationRepository,
        fighter_repo: FighterRepository  # Validate fighters exist
    ):
        self.fight_repo = fight_repo
        self.participation_repo = participation_repo
        self.fighter_repo = fighter_repo

    async def create_fight_with_participants(
        self,
        fight_data: dict,
        participations: List[ParticipationData]
    ) -> Fight:
        """
        Create fight and participants in single transaction.

        Validation:
        - All fighters exist
        - At least 2 participants
        - Both sides represented
        - No duplicate fighters
        - Max 1 captain per side
        """
        async with self.session.begin():  # Transaction boundary
            # Validate business rules
            await self._validate_fight_creation(fight_data, participations)

            # Create fight
            fight = await self.fight_repo.create(fight_data)

            # Create all participations
            for p_data in participations:
                await self.participation_repo.create({
                    "fight_id": fight.id,
                    "fighter_id": p_data.fighter_id,
                    "side": p_data.side,
                    "role": p_data.role
                })

            # Return fight with eager-loaded participations
            return await self.fight_repo.get_by_id(fight.id)
```

---

## TDD/BDD Workflow (CRITICAL)

### Overview: Red → Green → Refactor

Every feature follows this exact cycle:

1. **RED**: Write tests that fail (entity doesn't exist yet)
2. **GREEN**: Write minimal code to make tests pass
3. **REFACTOR**: Clean up code while keeping tests green

**Never write implementation before tests.**

---

## Detailed Implementation Steps

### Entity 1: Fight

#### Step 1.1: Write BDD Scenarios (RED Phase) ⏱️ 45 minutes

**File**: `tests/features/fight_management.feature`

**What to do**:
1. Create the feature file in `tests/features/`
2. Write Gherkin scenarios documenting all business requirements
3. Focus on clarity - these scenarios are your specification

**BDD Scenarios to Write**:

```gherkin
Feature: Fight Management
  As a fight tracker administrator
  I want to record and manage Buhurt fights
  So that I can maintain a historical database of events

  Background:
    Given the database is empty
    And the following fighters exist:
      | name          | team        | country |
      | Jan Kowalski  | Husaria     | Poland  |
      | Hans Schmidt  | Teutons     | Germany |
      | Ivan Petrov   | Rus Guards  | Russia  |
      | Erik Larsson  | Vikings     | Sweden  |

  # ========================================
  # HAPPY PATH SCENARIOS
  # ========================================

  Scenario: Create a singles duel fight
    Given I am an administrator
    When I create a fight with the following details:
      | field        | value                              |
      | fight_date   | 2024-03-15                         |
      | location     | IMCF World Championship, Warsaw    |
      | video_url    | https://youtube.com/watch?v=abc123 |
    And I add the following participants:
      | fighter       | side | role    |
      | Jan Kowalski  | 1    | fighter |
      | Hans Schmidt  | 2    | fighter |
    Then the fight should be created successfully
    And the fight should have 2 participants
    And side 1 should have 1 participant
    And side 2 should have 1 participant

  Scenario: Create a team fight with multiple fighters per side
    Given I am an administrator
    When I create a fight on "2024-05-20" at "Battle of Nations"
    And I add the following participants:
      | fighter       | side | role    |
      | Jan Kowalski  | 1    | captain |
      | Ivan Petrov   | 1    | fighter |
      | Hans Schmidt  | 2    | captain |
      | Erik Larsson  | 2    | fighter |
    Then the fight should be created successfully
    And the fight should have 4 participants
    And side 1 should have 1 captain
    And side 2 should have 1 captain

  Scenario: Record fight outcome with winner
    Given a fight exists between "Jan Kowalski" and "Hans Schmidt"
    When I update the fight to set winner as side 1
    Then the fight winner should be side 1
    And retrieving the fight should show the winner

  Scenario: Retrieve fight with eager-loaded participants
    Given a fight exists with 4 participants
    When I retrieve the fight by ID
    Then the fight should include all participant data
    And each participant should include fighter details
    And no additional database queries should be made (N+1 prevention)

  Scenario: List fights filtered by date range
    Given the following fights exist:
      | fight_date | location     |
      | 2024-01-15 | Tournament A |
      | 2024-03-20 | Tournament B |
      | 2024-06-10 | Tournament C |
    When I list fights between "2024-02-01" and "2024-05-31"
    Then I should receive exactly 1 fight
    And the fight should be from "Tournament B"

  Scenario: List fights by fighter
    Given "Jan Kowalski" participated in 3 fights
    And "Hans Schmidt" participated in 2 fights
    When I list fights for fighter "Jan Kowalski"
    Then I should receive exactly 3 fights
    And all fights should include "Jan Kowalski" as a participant

  Scenario: Soft delete a fight
    Given a fight exists with ID "550e8400-e29b-41d4-a716-446655440000"
    When I soft delete the fight
    Then the fight should be marked as deleted
    And listing active fights should exclude the deleted fight
    But the fight should still exist in the database

  # ========================================
  # VALIDATION ERROR SCENARIOS
  # ========================================

  Scenario: Cannot create fight with future date
    Given I am an administrator
    When I attempt to create a fight with date "2030-01-01"
    Then I should receive a validation error
    And the error should mention "cannot be in the future"

  Scenario: Cannot create fight with only 1 participant
    Given I am an administrator
    When I attempt to create a fight with the following participants:
      | fighter       | side | role    |
      | Jan Kowalski  | 1    | fighter |
    Then I should receive a validation error
    And the error should mention "at least 2 participants"

  Scenario: Cannot create fight with participants on only 1 side
    Given I am an administrator
    When I attempt to create a fight with the following participants:
      | fighter       | side | role    |
      | Jan Kowalski  | 1    | fighter |
      | Ivan Petrov   | 1    | fighter |
    Then I should receive a validation error
    And the error should mention "both sides must have participants"

  Scenario: Cannot add same fighter twice to same fight
    Given a fight exists with "Jan Kowalski" on side 1
    When I attempt to add "Jan Kowalski" to side 2
    Then I should receive a validation error
    And the error should mention "already participating"

  Scenario: Cannot create fight with empty location
    Given I am an administrator
    When I attempt to create a fight with empty location
    Then I should receive a validation error
    And the error should mention "location is required"

  Scenario: Cannot have multiple captains on same side
    Given I am an administrator
    When I attempt to create a fight with the following participants:
      | fighter       | side | role    |
      | Jan Kowalski  | 1    | captain |
      | Ivan Petrov   | 1    | captain |
      | Hans Schmidt  | 2    | captain |
    Then I should receive a validation error
    And the error should mention "only one captain per side"

  # ========================================
  # EDGE CASES
  # ========================================

  Scenario: Create fight with optional video URL omitted
    Given I am an administrator
    When I create a fight without video_url field
    And I add 2 participants on different sides
    Then the fight should be created successfully
    And the fight video_url should be null

  Scenario: Create fight with winner_side null (draw)
    Given I am an administrator
    When I create a fight without specifying a winner
    And I add 2 participants on different sides
    Then the fight should be created successfully
    And the fight winner_side should be null

  Scenario: Update fight location
    Given a fight exists at location "Old Location"
    When I update the fight location to "New Location"
    Then the fight location should be "New Location"
    And all participants should remain unchanged

  Scenario: Cannot retrieve fight with non-existent ID
    Given no fight exists with ID "00000000-0000-0000-0000-000000000000"
    When I attempt to retrieve the fight
    Then I should receive a not found error

  # ========================================
  # TRANSACTION ROLLBACK SCENARIOS (CRITICAL)
  # ========================================

  Scenario: Fight creation rolls back when participant invalid
    Given I am an administrator
    When I attempt to create a fight with the following participants:
      | fighter       | side | role    |
      | Jan Kowalski  | 1    | fighter |
      | NonExistent   | 2    | fighter |
    Then I should receive a validation error
    And no fight should be created in the database
    And no participations should be created in the database

  Scenario: Fight creation rolls back when business rule violated
    Given I am an administrator
    When I attempt to create a fight with invalid data
    Then the transaction should roll back completely
    And the database should remain in consistent state
```

**Success Criteria**:
- [ ] 20+ scenarios written
- [ ] All business rules covered
- [ ] Happy path + validation + edge cases + transactions
- [ ] Clear, readable Gherkin
- [ ] File saved in `tests/features/fight_management.feature`

**Verification**:
```bash
# Scenarios won't run yet (no step definitions), but file should parse
pytest tests/features/fight_management.feature --collect-only
# Should show: "collected X items"
```

---

#### Step 1.2: Create Fight Model (Still RED) ⏱️ 20 minutes

**File**: `app/models/fight.py`

**What to do**:
1. Create SQLAlchemy model with all fields
2. Define relationships to FightParticipation
3. Configure eager loading to prevent N+1 queries
4. Follow patterns from Country/Team/Fighter models

**Implementation**:

```python
"""
SQLAlchemy ORM model for Fight entity.

Represents a single Buhurt fight event with participants.
Implements soft delete pattern and aggregate root for Fight + Participations.
"""

from datetime import date, datetime, UTC
from uuid import UUID, uuid4
from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from app.models.base import Base  # Assuming Base is defined


class Fight(Base):
    """
    Fight entity representing a Buhurt combat event.

    Attributes:
        id: UUID primary key (auto-generated)
        fight_date: Date of the fight (DATE, not DATETIME)
        location: Fight location description (max 200 chars)
        video_url: Optional link to fight footage (max 500 chars)
        winner_side: Which side won (1, 2, or NULL for draw/unknown)
        notes: Optional fight description (TEXT)
        is_deleted: Soft delete flag (defaults to False)
        created_at: Timestamp of creation (auto-generated)

        participations: Relationship to FightParticipation entities (eager loaded)
    """
    __tablename__ = "fights"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False
    )

    fight_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True  # For date range queries
    )

    location: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    video_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        default=None
    )

    winner_side: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=None
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True  # For filtering active fights
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relationships
    participations: Mapped[List["FightParticipation"]] = relationship(
        "FightParticipation",
        back_populates="fight",
        lazy="joined",  # Eager load by default to avoid N+1
        cascade="all, delete-orphan"  # If fight deleted, cascade to participations
    )

    def __init__(self, **kwargs):
        """
        Initialize Fight with Python-level defaults.

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
        return (
            f"<Fight(id={self.id}, "
            f"fight_date={self.fight_date}, "
            f"location='{self.location}', "
            f"winner_side={self.winner_side}, "
            f"is_deleted={self.is_deleted})>"
        )
```

**Update**: `app/models/__init__.py`

Add import:
```python
from app.models.fight import Fight
```

**Success Criteria**:
- [ ] Model created with all fields
- [ ] Relationships defined
- [ ] Follows Phase 1 patterns (UTC datetime, soft delete, UUID pk)
- [ ] File saved in `app/models/fight.py`

---

#### Step 1.3: Create FightParticipation Model (Still RED) ⏱️ 20 minutes

**File**: `app/models/fight_participation.py`

**Implementation**:

```python
"""
SQLAlchemy ORM model for FightParticipation entity.

Junction table linking Fighters to Fights with side and role metadata.
"""

from datetime import datetime, UTC
from enum import Enum
from uuid import UUID, uuid4
from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class ParticipationRole(str, Enum):
    """
    Role types for fight participation.

    - fighter: Regular combatant
    - captain: Team leader (only 1 per side)
    - alternate: Backup fighter (didn't fight)
    - coach: Non-combatant team support
    """
    FIGHTER = "fighter"
    CAPTAIN = "captain"
    ALTERNATE = "alternate"
    COACH = "coach"


class FightParticipation(Base):
    """
    Junction table linking Fighters to Fights.

    Attributes:
        id: UUID primary key (auto-generated)
        fight_id: Foreign key to fights table (UUID)
        fighter_id: Foreign key to fighters table (UUID)
        side: Which side fighter was on (1 or 2)
        role: Participation type (fighter, captain, alternate, coach)
        created_at: Timestamp of creation (auto-generated)

        fight: Relationship to Fight entity (many-to-one)
        fighter: Relationship to Fighter entity (many-to-one)
    """
    __tablename__ = "fight_participations"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False
    )

    fight_id: Mapped[UUID] = mapped_column(
        ForeignKey("fights.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # For queries by fight
    )

    fighter_id: Mapped[UUID] = mapped_column(
        ForeignKey("fighters.id", ondelete="RESTRICT"),
        nullable=False,
        index=True  # For queries by fighter
    )

    side: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ParticipationRole.FIGHTER.value
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relationships
    fight: Mapped["Fight"] = relationship(
        "Fight",
        back_populates="participations"
    )

    fighter: Mapped["Fighter"] = relationship(
        "Fighter",
        lazy="joined"  # Eager load fighter data
    )

    # Constraints
    __table_args__ = (
        # Fighter cannot participate in same fight twice
        UniqueConstraint('fight_id', 'fighter_id', name='uq_fight_fighter'),

        # Side must be 1 or 2
        CheckConstraint('side IN (1, 2)', name='ck_side_valid'),

        # Role must be valid enum value
        CheckConstraint(
            f"role IN ('{ParticipationRole.FIGHTER.value}', "
            f"'{ParticipationRole.CAPTAIN.value}', "
            f"'{ParticipationRole.ALTERNATE.value}', "
            f"'{ParticipationRole.COACH.value}')",
            name='ck_role_valid'
        ),
    )

    def __init__(self, **kwargs):
        """Initialize FightParticipation with Python-level defaults."""
        super().__init__(**kwargs)

        if 'id' not in kwargs:
            self.id = uuid4()
        if 'created_at' not in kwargs:
            self.created_at = datetime.now(UTC)
        if 'role' not in kwargs:
            self.role = ParticipationRole.FIGHTER.value

    def __repr__(self) -> str:
        return (
            f"<FightParticipation(id={self.id}, "
            f"fight_id={self.fight_id}, "
            f"fighter_id={self.fighter_id}, "
            f"side={self.side}, "
            f"role='{self.role}')>"
        )
```

**Update**: `app/models/__init__.py`

Add imports:
```python
from app.models.fight_participation import FightParticipation, ParticipationRole
```

**Update**: `app/models/fighter.py`

Add relationship:
```python
from typing import List

# Add to Fighter class:
participations: Mapped[List["FightParticipation"]] = relationship(
    "FightParticipation",
    back_populates="fighter"
)
```

**Success Criteria**:
- [ ] Model created with all fields and constraints
- [ ] Enum defined for roles
- [ ] Relationships bidirectional
- [ ] Constraints defined (unique, check)
- [ ] File saved

---

#### Step 1.4: Write Fight Repository Unit Tests (RED) ⏱️ 60 minutes

**File**: `tests/unit/repositories/test_fight_repository.py`

**What to do**:
1. Mock AsyncSession
2. Write tests for all repository methods
3. Test soft delete filtering
4. Test eager loading

**Test Structure**:

```python
"""
Unit tests for FightRepository.

Tests repository data access methods with mocked AsyncSession.
Follows TDD RED phase - tests written before implementation.
"""

import pytest
from datetime import date, datetime, UTC
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.fight_repository import FightRepository
from app.models.fight import Fight


@pytest.fixture
def mock_session():
    """Create mock AsyncSession for testing."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()  # Synchronous
    session.delete = MagicMock()  # Synchronous
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def fight_repository(mock_session):
    """Create FightRepository with mocked session."""
    return FightRepository(session=mock_session)


@pytest.fixture
def sample_fight():
    """Create sample Fight for testing."""
    return Fight(
        id=uuid4(),
        fight_date=date(2024, 3, 15),
        location="IMCF World Championship, Warsaw",
        video_url="https://youtube.com/watch?v=abc123",
        winner_side=1,
        notes="Exciting singles duel",
        is_deleted=False,
        created_at=datetime.now(UTC)
    )


# ============================================================
# CREATE TESTS
# ============================================================

class TestFightRepositoryCreate:
    """Test fight creation."""

    @pytest.mark.asyncio
    async def test_create_fight_calls_session_methods_correctly(
        self, fight_repository, mock_session
    ):
        """Verify create() calls session.add, flush, refresh."""
        fight_data = {
            "fight_date": date(2024, 3, 15),
            "location": "Test Location",
        }

        await fight_repository.create(fight_data)

        # Verify session methods called
        mock_session.add.assert_called_once()
        mock_session.flush.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_fight_with_all_fields(
        self, fight_repository, mock_session
    ):
        """Verify all fight fields are set correctly."""
        fight_data = {
            "fight_date": date(2024, 3, 15),
            "location": "IMCF World Championship",
            "video_url": "https://youtube.com/watch?v=abc",
            "winner_side": 1,
            "notes": "Great fight"
        }

        fight = await fight_repository.create(fight_data)

        assert fight.fight_date == date(2024, 3, 15)
        assert fight.location == "IMCF World Championship"
        assert fight.video_url == "https://youtube.com/watch?v=abc"
        assert fight.winner_side == 1
        assert fight.notes == "Great fight"
        assert fight.is_deleted is False
        assert isinstance(fight.id, UUID)

    @pytest.mark.asyncio
    async def test_create_fight_with_optional_fields_omitted(
        self, fight_repository, mock_session
    ):
        """Verify optional fields default to None."""
        fight_data = {
            "fight_date": date(2024, 3, 15),
            "location": "Test Location",
        }

        fight = await fight_repository.create(fight_data)

        assert fight.video_url is None
        assert fight.winner_side is None
        assert fight.notes is None


# ============================================================
# GET BY ID TESTS
# ============================================================

class TestFightRepositoryGetById:
    """Test retrieving fights by ID."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_fight_when_exists(
        self, fight_repository, mock_session, sample_fight
    ):
        """Verify get_by_id returns fight when found."""
        fight_id = sample_fight.id

        # Mock execute to return sample fight
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_fight
        mock_session.execute.return_value = mock_result

        result = await fight_repository.get_by_id(fight_id)

        assert result == sample_fight
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_exists(
        self, fight_repository, mock_session
    ):
        """Verify get_by_id returns None when fight not found."""
        fake_id = uuid4()

        # Mock execute to return None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await fight_repository.get_by_id(fake_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_filters_soft_deleted_fights(
        self, fight_repository, mock_session
    ):
        """Verify get_by_id excludes soft-deleted fights by default."""
        deleted_fight_id = uuid4()

        # Mock execute to return None (soft-deleted fight filtered out)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await fight_repository.get_by_id(deleted_fight_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_with_participations_eager_loaded(
        self, fight_repository, mock_session, sample_fight
    ):
        """Verify participations are eager-loaded (no N+1 queries)."""
        # This tests the relationship configuration
        # Actual eager loading verified in integration tests
        fight_id = sample_fight.id

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_fight
        mock_session.execute.return_value = mock_result

        result = await fight_repository.get_by_id(fight_id)

        # If relationship configured correctly, participations accessible
        assert hasattr(result, 'participations')


# ============================================================
# LIST TESTS
# ============================================================

class TestFightRepositoryList:
    """Test listing fights."""

    @pytest.mark.asyncio
    async def test_list_all_excludes_soft_deleted_fights(
        self, fight_repository, mock_session, sample_fight
    ):
        """Verify list_all excludes soft-deleted fights."""
        # Mock execute to return active fights only
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [sample_fight]
        mock_session.execute.return_value = mock_result

        results = await fight_repository.list_all()

        assert len(results) == 1
        assert results[0].is_deleted is False

    @pytest.mark.asyncio
    async def test_list_by_date_range(
        self, fight_repository, mock_session, sample_fight
    ):
        """Verify list_by_date_range filters correctly."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [sample_fight]
        mock_session.execute.return_value = mock_result

        results = await fight_repository.list_by_date_range(start_date, end_date)

        assert len(results) == 1
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_by_fighter(
        self, fight_repository, mock_session, sample_fight
    ):
        """Verify list_by_fighter returns fights for specific fighter."""
        fighter_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [sample_fight]
        mock_session.execute.return_value = mock_result

        results = await fight_repository.list_by_fighter(fighter_id)

        assert len(results) >= 0  # May be empty
        mock_session.execute.assert_awaited_once()


# ============================================================
# UPDATE TESTS
# ============================================================

class TestFightRepositoryUpdate:
    """Test updating fights."""

    @pytest.mark.asyncio
    async def test_update_fight_location(
        self, fight_repository, mock_session, sample_fight
    ):
        """Verify update() modifies fight fields."""
        sample_fight.location = "Old Location"

        # Mock get_by_id to return sample fight
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_fight
        mock_session.execute.return_value = mock_result

        updated = await fight_repository.update(
            sample_fight.id,
            {"location": "New Location"}
        )

        assert updated.location == "New Location"
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_fight_winner_side(
        self, fight_repository, mock_session, sample_fight
    ):
        """Verify winner_side can be updated."""
        sample_fight.winner_side = None

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_fight
        mock_session.execute.return_value = mock_result

        updated = await fight_repository.update(
            sample_fight.id,
            {"winner_side": 2}
        )

        assert updated.winner_side == 2


# ============================================================
# SOFT DELETE TESTS
# ============================================================

class TestFightRepositorySoftDelete:
    """Test soft deleting fights."""

    @pytest.mark.asyncio
    async def test_soft_delete_sets_is_deleted_flag(
        self, fight_repository, mock_session, sample_fight
    ):
        """Verify soft_delete sets is_deleted=True."""
        # Mock get_by_id to return sample fight
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_fight
        mock_session.execute.return_value = mock_result

        success = await fight_repository.soft_delete(sample_fight.id)

        assert success is True
        assert sample_fight.is_deleted is True
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_soft_delete_returns_false_when_not_exists(
        self, fight_repository, mock_session
    ):
        """Verify soft_delete returns False when fight not found."""
        fake_id = uuid4()

        # Mock get_by_id to return None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        success = await fight_repository.soft_delete(fake_id)

        assert success is False
```

**Continue with 20+ more tests...**

Test checklist:
- [ ] Create fight (various field combinations)
- [ ] Get by ID (exists, not exists, soft deleted)
- [ ] List all (exclude deleted)
- [ ] List by date range
- [ ] List by fighter
- [ ] Update fight fields
- [ ] Soft delete
- [ ] Verify eager loading configuration

**Success Criteria**:
- [ ] 25+ repository tests written
- [ ] All tests FAIL (RED phase) - repository doesn't exist yet
- [ ] Tests are clear and well-documented

**Verification**:
```bash
pytest tests/unit/repositories/test_fight_repository.py -v
# Expected: All tests FAIL with ImportError or NotImplementedError
```

---

#### Step 1.5: Write FightParticipation Repository Unit Tests (RED) ⏱️ 45 minutes

**File**: `tests/unit/repositories/test_fight_participation_repository.py`

Similar structure to Fight repository tests. Focus on:
- Create participation
- Get by fight_id
- Get by fighter_id
- Validate unique constraint (fight_id, fighter_id)
- Validate side constraint (must be 1 or 2)
- Eager load fighter details

**Success Criteria**:
- [ ] 20+ repository tests written
- [ ] All tests FAIL (RED phase)

---

#### Step 1.6: Write Fight Service Unit Tests (RED) ⏱️ 90 minutes

**File**: `tests/unit/services/test_fight_service.py`

**What to do**:
1. Mock FightRepository, FightParticipationRepository, FighterRepository
2. Test business logic (validation rules)
3. Test transactional behavior (create fight + participations atomically)

**Key Tests**:

```python
"""
Unit tests for FightService.

Tests business logic with mocked repositories.
Focus on validation, business rules, and transaction coordination.
"""

import pytest
from datetime import date, datetime, UTC
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from app.services.fight_service import FightService, ParticipationData
from app.models.fight import Fight
from app.models.fighter import Fighter
from app.exceptions import (
    ValidationError,
    FighterNotFoundError,
    InvalidFightDataError
)


@pytest.fixture
def mock_fight_repo():
    """Mock FightRepository."""
    return AsyncMock()


@pytest.fixture
def mock_participation_repo():
    """Mock FightParticipationRepository."""
    return AsyncMock()


@pytest.fixture
def mock_fighter_repo():
    """Mock FighterRepository."""
    return AsyncMock()


@pytest.fixture
def fight_service(mock_fight_repo, mock_participation_repo, mock_fighter_repo):
    """Create FightService with mocked repositories."""
    return FightService(
        fight_repo=mock_fight_repo,
        participation_repo=mock_participation_repo,
        fighter_repo=mock_fighter_repo
    )


# ============================================================
# VALIDATION TESTS (BUSINESS RULES)
# ============================================================

class TestFightServiceValidation:
    """Test fight creation validation."""

    @pytest.mark.asyncio
    async def test_create_fight_with_future_date_raises_error(
        self, fight_service, mock_fighter_repo
    ):
        """Cannot create fight with date in the future."""
        future_date = date(2030, 1, 1)
        fight_data = {"fight_date": future_date, "location": "Test"}
        participations = [
            ParticipationData(fighter_id=uuid4(), side=1, role="fighter"),
            ParticipationData(fighter_id=uuid4(), side=2, role="fighter"),
        ]

        # Mock fighters exist
        mock_fighter_repo.get_by_id.return_value = Fighter(name="Test")

        with pytest.raises(ValidationError) as exc_info:
            await fight_service.create_fight_with_participants(
                fight_data, participations
            )

        assert "future" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_fight_with_empty_location_raises_error(
        self, fight_service
    ):
        """Location is required."""
        fight_data = {"fight_date": date(2024, 1, 1), "location": ""}
        participations = [
            ParticipationData(fighter_id=uuid4(), side=1, role="fighter"),
            ParticipationData(fighter_id=uuid4(), side=2, role="fighter"),
        ]

        with pytest.raises(ValidationError) as exc_info:
            await fight_service.create_fight_with_participants(
                fight_data, participations
            )

        assert "location" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_fight_with_less_than_2_participants_raises_error(
        self, fight_service, mock_fighter_repo
    ):
        """Fight must have at least 2 participants."""
        fight_data = {"fight_date": date(2024, 1, 1), "location": "Test"}
        participations = [
            ParticipationData(fighter_id=uuid4(), side=1, role="fighter"),
        ]

        mock_fighter_repo.get_by_id.return_value = Fighter(name="Test")

        with pytest.raises(ValidationError) as exc_info:
            await fight_service.create_fight_with_participants(
                fight_data, participations
            )

        assert "at least 2 participants" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_fight_with_only_one_side_raises_error(
        self, fight_service, mock_fighter_repo
    ):
        """Both sides must have participants."""
        fight_data = {"fight_date": date(2024, 1, 1), "location": "Test"}
        participations = [
            ParticipationData(fighter_id=uuid4(), side=1, role="fighter"),
            ParticipationData(fighter_id=uuid4(), side=1, role="fighter"),
        ]

        mock_fighter_repo.get_by_id.return_value = Fighter(name="Test")

        with pytest.raises(ValidationError) as exc_info:
            await fight_service.create_fight_with_participants(
                fight_data, participations
            )

        assert "both sides" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_fight_with_duplicate_fighter_raises_error(
        self, fight_service, mock_fighter_repo
    ):
        """Same fighter cannot be on fight twice."""
        fighter_id = uuid4()
        fight_data = {"fight_date": date(2024, 1, 1), "location": "Test"}
        participations = [
            ParticipationData(fighter_id=fighter_id, side=1, role="fighter"),
            ParticipationData(fighter_id=fighter_id, side=2, role="fighter"),
        ]

        mock_fighter_repo.get_by_id.return_value = Fighter(name="Test")

        with pytest.raises(ValidationError) as exc_info:
            await fight_service.create_fight_with_participants(
                fight_data, participations
            )

        assert "already participating" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_fight_with_multiple_captains_same_side_raises_error(
        self, fight_service, mock_fighter_repo
    ):
        """Only 1 captain allowed per side."""
        fight_data = {"fight_date": date(2024, 1, 1), "location": "Test"}
        participations = [
            ParticipationData(fighter_id=uuid4(), side=1, role="captain"),
            ParticipationData(fighter_id=uuid4(), side=1, role="captain"),
            ParticipationData(fighter_id=uuid4(), side=2, role="captain"),
        ]

        mock_fighter_repo.get_by_id.return_value = Fighter(name="Test")

        with pytest.raises(ValidationError) as exc_info:
            await fight_service.create_fight_with_participants(
                fight_data, participations
            )

        assert "one captain per side" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_fight_with_nonexistent_fighter_raises_error(
        self, fight_service, mock_fighter_repo
    ):
        """All fighters must exist."""
        fight_data = {"fight_date": date(2024, 1, 1), "location": "Test"}
        participations = [
            ParticipationData(fighter_id=uuid4(), side=1, role="fighter"),
            ParticipationData(fighter_id=uuid4(), side=2, role="fighter"),
        ]

        # First fighter exists, second doesn't
        mock_fighter_repo.get_by_id.side_effect = [
            Fighter(name="Exists"),
            None  # Fighter not found
        ]

        with pytest.raises(FighterNotFoundError):
            await fight_service.create_fight_with_participants(
                fight_data, participations
            )


# ============================================================
# TRANSACTION TESTS (CRITICAL)
# ============================================================

class TestFightServiceTransactions:
    """Test transactional behavior."""

    @pytest.mark.asyncio
    async def test_create_fight_calls_repos_in_transaction(
        self, fight_service, mock_fight_repo, mock_participation_repo,
        mock_fighter_repo
    ):
        """Verify fight and participations created in correct order."""
        fight_data = {"fight_date": date(2024, 1, 1), "location": "Test"}
        fighter1_id = uuid4()
        fighter2_id = uuid4()
        participations = [
            ParticipationData(fighter_id=fighter1_id, side=1, role="fighter"),
            ParticipationData(fighter_id=fighter2_id, side=2, role="fighter"),
        ]

        # Mock fighters exist
        mock_fighter_repo.get_by_id.return_value = Fighter(name="Test")

        # Mock fight creation
        created_fight = Fight(
            id=uuid4(),
            fight_date=date(2024, 1, 1),
            location="Test"
        )
        mock_fight_repo.create.return_value = created_fight

        await fight_service.create_fight_with_participants(
            fight_data, participations
        )

        # Verify fight created first
        mock_fight_repo.create.assert_awaited_once()

        # Verify participations created (2 times)
        assert mock_participation_repo.create.await_count == 2


# ============================================================
# HAPPY PATH TESTS
# ============================================================

class TestFightServiceHappyPath:
    """Test successful fight creation."""

    @pytest.mark.asyncio
    async def test_create_singles_fight_succeeds(
        self, fight_service, mock_fight_repo, mock_participation_repo,
        mock_fighter_repo
    ):
        """Verify singles fight creation."""
        fight_data = {
            "fight_date": date(2024, 3, 15),
            "location": "IMCF World Championship"
        }
        participations = [
            ParticipationData(fighter_id=uuid4(), side=1, role="fighter"),
            ParticipationData(fighter_id=uuid4(), side=2, role="fighter"),
        ]

        mock_fighter_repo.get_by_id.return_value = Fighter(name="Test")
        created_fight = Fight(
            id=uuid4(),
            fight_date=date(2024, 3, 15),
            location="IMCF World Championship"
        )
        mock_fight_repo.create.return_value = created_fight
        mock_fight_repo.get_by_id.return_value = created_fight

        result = await fight_service.create_fight_with_participants(
            fight_data, participations
        )

        assert result.fight_date == date(2024, 3, 15)
        assert result.location == "IMCF World Championship"

    @pytest.mark.asyncio
    async def test_create_team_fight_with_captains_succeeds(
        self, fight_service, mock_fight_repo, mock_participation_repo,
        mock_fighter_repo
    ):
        """Verify team fight with captains creation."""
        fight_data = {"fight_date": date(2024, 1, 1), "location": "Test"}
        participations = [
            ParticipationData(fighter_id=uuid4(), side=1, role="captain"),
            ParticipationData(fighter_id=uuid4(), side=1, role="fighter"),
            ParticipationData(fighter_id=uuid4(), side=2, role="captain"),
            ParticipationData(fighter_id=uuid4(), side=2, role="fighter"),
        ]

        mock_fighter_repo.get_by_id.return_value = Fighter(name="Test")
        created_fight = Fight(id=uuid4(), fight_date=date(2024, 1, 1), location="Test")
        mock_fight_repo.create.return_value = created_fight
        mock_fight_repo.get_by_id.return_value = created_fight

        result = await fight_service.create_fight_with_participants(
            fight_data, participations
        )

        # Should succeed - exactly 1 captain per side
        assert result is not None
```

**Continue with 30+ more service tests...**

Test checklist:
- [ ] All validation rules tested
- [ ] Transaction coordination tested
- [ ] Happy path scenarios tested
- [ ] Error handling tested
- [ ] Mock assertions verify correct repo calls

**Success Criteria**:
- [ ] 35+ service tests written
- [ ] All tests FAIL (RED phase)

---

#### Step 1.7: Implement Fight Repository (GREEN Phase) ⏱️ 45 minutes

**File**: `app/repositories/fight_repository.py`

**What to do**:
1. Implement all repository methods
2. Follow patterns from Country/Team/Fighter repositories
3. Run tests frequently - watch them turn GREEN

**Implementation**:

```python
"""
Repository for Fight entity data access.

Handles all database operations for Fight entities.
"""

from datetime import date
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.fight import Fight


class FightRepository:
    """Repository for Fight entity CRUD operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize FightRepository.

        Args:
            session: AsyncSession for database operations
        """
        self.session = session

    async def create(self, fight_data: dict) -> Fight:
        """
        Create a new fight.

        Args:
            fight_data: Dictionary with fight fields

        Returns:
            Created Fight instance
        """
        fight = Fight(**fight_data)
        self.session.add(fight)
        await self.session.flush()
        await self.session.refresh(fight)
        return fight

    async def get_by_id(self, fight_id: UUID) -> Optional[Fight]:
        """
        Get fight by ID, excluding soft-deleted fights.

        Args:
            fight_id: UUID of the fight

        Returns:
            Fight instance or None if not found
        """
        stmt = (
            select(Fight)
            .options(selectinload(Fight.participations))  # Eager load
            .where(Fight.id == fight_id, Fight.is_deleted == False)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> List[Fight]:
        """
        List all active fights.

        Returns:
            List of Fight instances (excludes soft-deleted)
        """
        stmt = (
            select(Fight)
            .options(selectinload(Fight.participations))
            .where(Fight.is_deleted == False)
            .order_by(Fight.fight_date.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_date_range(
        self, start_date: date, end_date: date
    ) -> List[Fight]:
        """
        List fights within a date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            List of Fight instances
        """
        stmt = (
            select(Fight)
            .options(selectinload(Fight.participations))
            .where(
                Fight.fight_date >= start_date,
                Fight.fight_date <= end_date,
                Fight.is_deleted == False
            )
            .order_by(Fight.fight_date.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_fighter(self, fighter_id: UUID) -> List[Fight]:
        """
        List all fights for a specific fighter.

        Args:
            fighter_id: UUID of the fighter

        Returns:
            List of Fight instances
        """
        stmt = (
            select(Fight)
            .join(Fight.participations)
            .options(selectinload(Fight.participations))
            .where(
                FightParticipation.fighter_id == fighter_id,
                Fight.is_deleted == False
            )
            .order_by(Fight.fight_date.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, fight_id: UUID, fight_data: dict) -> Optional[Fight]:
        """
        Update fight fields.

        Args:
            fight_id: UUID of fight to update
            fight_data: Dictionary with fields to update

        Returns:
            Updated Fight instance or None if not found
        """
        fight = await self.get_by_id(fight_id)
        if not fight:
            return None

        for key, value in fight_data.items():
            if hasattr(fight, key):
                setattr(fight, key, value)

        await self.session.flush()
        await self.session.refresh(fight)
        return fight

    async def soft_delete(self, fight_id: UUID) -> bool:
        """
        Soft delete a fight.

        Args:
            fight_id: UUID of fight to delete

        Returns:
            True if deleted, False if not found
        """
        fight = await self.get_by_id(fight_id)
        if not fight:
            return False

        fight.is_deleted = True
        await self.session.flush()
        return True
```

**Success Criteria**:
- [ ] All repository methods implemented
- [ ] Eager loading configured (`selectinload`)
- [ ] Soft delete filtering applied
- [ ] Run tests: `pytest tests/unit/repositories/test_fight_repository.py -v`
- [ ] **All tests should PASS (GREEN)** ✅

---

#### Step 1.8: Implement FightParticipation Repository (GREEN) ⏱️ 30 minutes

Similar to Fight repository. Implement:
- `create()`
- `get_by_id()`
- `list_by_fight()`
- `list_by_fighter()`
- `delete()` (hard delete since it's a junction table)

**Success Criteria**:
- [ ] All methods implemented
- [ ] Tests PASS ✅

---

#### Step 1.9: Implement Fight Service (GREEN) ⏱️ 90 minutes

**File**: `app/services/fight_service.py`

**What to do**:
1. Implement business logic
2. Coordinate multiple repositories
3. Validate all business rules
4. Handle transactions

**Implementation**:

```python
"""
Service layer for Fight business logic.

Coordinates Fight and FightParticipation operations with validation.
"""

from dataclasses import dataclass
from datetime import date, datetime, UTC
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.fight_repository import FightRepository
from app.repositories.fight_participation_repository import FightParticipationRepository
from app.repositories.fighter_repository import FighterRepository
from app.models.fight import Fight
from app.models.fight_participation import ParticipationRole
from app.exceptions import (
    ValidationError,
    FighterNotFoundError,
    FightNotFoundError,
    InvalidFightDataError
)


@dataclass
class ParticipationData:
    """Data transfer object for fight participation."""
    fighter_id: UUID
    side: int
    role: str


class FightService:
    """Service for Fight business logic."""

    def __init__(
        self,
        fight_repo: FightRepository,
        participation_repo: FightParticipationRepository,
        fighter_repo: FighterRepository
    ):
        """
        Initialize FightService.

        Args:
            fight_repo: Repository for Fight data access
            participation_repo: Repository for FightParticipation data access
            fighter_repo: Repository for Fighter validation
        """
        self.fight_repo = fight_repo
        self.participation_repo = participation_repo
        self.fighter_repo = fighter_repo

    async def create_fight_with_participants(
        self,
        fight_data: dict,
        participations: List[ParticipationData],
        session: AsyncSession
    ) -> Fight:
        """
        Create fight with participants in single transaction.

        Args:
            fight_data: Dictionary with fight fields
            participations: List of ParticipationData
            session: Database session for transaction

        Returns:
            Created Fight with participations

        Raises:
            ValidationError: If business rules violated
            FighterNotFoundError: If fighter doesn't exist
        """
        async with session.begin():
            # Validate fight data
            await self._validate_fight_data(fight_data)

            # Validate participations
            await self._validate_participations(participations)

            # Create fight
            fight = await self.fight_repo.create(fight_data)

            # Create participations
            for p in participations:
                await self.participation_repo.create({
                    "fight_id": fight.id,
                    "fighter_id": p.fighter_id,
                    "side": p.side,
                    "role": p.role
                })

            # Reload with participations
            return await self.fight_repo.get_by_id(fight.id)

    async def _validate_fight_data(self, fight_data: dict) -> None:
        """
        Validate fight data before creation.

        Args:
            fight_data: Dictionary with fight fields

        Raises:
            ValidationError: If validation fails
        """
        # Date cannot be in the future
        fight_date = fight_data.get("fight_date")
        if fight_date and fight_date > date.today():
            raise ValidationError("Fight date cannot be in the future")

        # Location is required
        location = fight_data.get("location", "").strip()
        if not location:
            raise ValidationError("Location is required")

        # Winner side must be 1, 2, or None
        winner_side = fight_data.get("winner_side")
        if winner_side is not None and winner_side not in (1, 2):
            raise ValidationError("Winner side must be 1, 2, or null")

    async def _validate_participations(
        self, participations: List[ParticipationData]
    ) -> None:
        """
        Validate participations before creation.

        Args:
            participations: List of ParticipationData

        Raises:
            ValidationError: If business rules violated
            FighterNotFoundError: If fighter doesn't exist
        """
        # Must have at least 2 participants
        if len(participations) < 2:
            raise ValidationError("Fight must have at least 2 participants")

        # Must have both sides represented
        sides = set(p.side for p in participations)
        if len(sides) < 2:
            raise ValidationError("Both sides must have participants")

        # No duplicate fighters
        fighter_ids = [p.fighter_id for p in participations]
        if len(fighter_ids) != len(set(fighter_ids)):
            raise ValidationError("Fighter already participating in fight")

        # Max 1 captain per side
        captains_per_side = {}
        for p in participations:
            if p.role == ParticipationRole.CAPTAIN.value:
                captains_per_side[p.side] = captains_per_side.get(p.side, 0) + 1

        for side, count in captains_per_side.items():
            if count > 1:
                raise ValidationError(f"Only one captain allowed per side (side {side} has {count})")

        # Validate all fighters exist
        for p in participations:
            fighter = await self.fighter_repo.get_by_id(p.fighter_id)
            if not fighter:
                raise FighterNotFoundError(p.fighter_id)

    async def get_fight(self, fight_id: UUID) -> Fight:
        """
        Get fight by ID.

        Args:
            fight_id: UUID of the fight

        Returns:
            Fight instance

        Raises:
            FightNotFoundError: If fight not found
        """
        fight = await self.fight_repo.get_by_id(fight_id)
        if not fight:
            raise FightNotFoundError(fight_id)
        return fight

    # ... Additional service methods: list_fights, update_fight, delete_fight, etc.
```

**Success Criteria**:
- [ ] All service methods implemented
- [ ] All validation rules enforced
- [ ] Transactions handled correctly
- [ ] Run tests: `pytest tests/unit/services/test_fight_service.py -v`
- [ ] **All tests should PASS (GREEN)** ✅

---

#### Step 1.10: Create Alembic Migrations (GREEN) ⏱️ 20 minutes

**Create migrations for Fight and FightParticipation tables**

```bash
# Create Fight migration
alembic revision --autogenerate -m "create_fights_table_with_soft_delete"

# Create FightParticipation migration
alembic revision --autogenerate -m "create_fight_participations_junction_table"
```

**Review migrations** before committing. Verify:
- [ ] All columns created
- [ ] Indexes on fight_date, is_deleted
- [ ] Foreign keys configured correctly
- [ ] Unique constraint on (fight_id, fighter_id)
- [ ] Check constraints on side and role

**Success Criteria**:
- [ ] 2 migrations created
- [ ] Migrations reviewed and correct
- [ ] Committed to git

---

#### Step 1.11: Create Pydantic Schemas ⏱️ 30 minutes

**Files**:
- `app/schemas/fight.py`
- `app/schemas/fight_participation.py`

**Success Criteria**:
- [ ] Request/Response schemas created
- [ ] Validation rules configured
- [ ] Nested schemas for relationships

---

#### Step 1.12: Create API Endpoints ⏱️ 60 minutes

**File**: `app/api/v1/fights.py`

Implement:
- `POST /api/v1/fights` - Create fight with participants
- `GET /api/v1/fights/{id}` - Get fight by ID
- `GET /api/v1/fights` - List all fights (with filters)
- `PATCH /api/v1/fights/{id}` - Update fight
- `DELETE /api/v1/fights/{id}` - Soft delete fight
- `GET /api/v1/fighters/{id}/fights` - List fights by fighter

**Success Criteria**:
- [ ] All endpoints implemented
- [ ] Error handling configured
- [ ] OpenAPI docs generated
- [ ] Manual testing with curl/Postman

---

#### Step 1.13: Run All Tests ⏱️ 10 minutes

```bash
# Run all unit tests
pytest tests/unit/ -v

# Expected: 130 (Phase 1) + ~60 (Fight + FightParticipation) = ~190 tests PASSING

# Run integration tests (if Docker available)
pytest tests/integration/ -v

# Run BDD scenarios (if Docker available)
pytest tests/step_defs/ -v
```

**Success Criteria**:
- [ ] All unit tests passing
- [ ] No regressions in Phase 1 tests
- [ ] Integration tests passing (if Docker available)

---

#### Step 1.14: Git Commit ⏱️ 10 minutes

```bash
git add .
git commit -m "$(cat <<'EOF'
Implement Fight and FightParticipation entities (TDD complete)

Phase 2: Fight tracking system

## Models
- Created Fight model with date, location, video_url, winner_side fields
- Created FightParticipation model with side and role fields
- Configured many-to-many relationship via junction table
- Eager loading configured to prevent N+1 queries

## Repositories
- FightRepository: CRUD + list_by_date_range + list_by_fighter
- FightParticipationRepository: CRUD + list_by_fight + list_by_fighter
- Soft delete filtering applied

## Services
- FightService: Aggregate pattern for Fight + Participations
- Business rules validation:
  * At least 2 participants
  * Both sides represented
  * No duplicate fighters
  * Max 1 captain per side
  * Date not in future
- Transactional fight creation (atomic Fight + Participations)

## Tests
- 60+ new unit tests (repositories + services)
- 20+ BDD scenarios
- All tests passing (GREEN phase)
- No regressions in Phase 1 tests

## Migrations
- Created migration for fights table
- Created migration for fight_participations table
- Foreign keys, constraints, and indexes configured

## API
- Full CRUD endpoints for fights
- Nested participant management
- OpenAPI documentation

Test Results: 190/190 unit tests passing

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Success Criteria for Phase 2

### Code Quality
- [ ] All unit tests passing (no regressions)
- [ ] Code coverage >90%
- [ ] No lint errors
- [ ] Following established patterns

### Functionality
- [ ] Can create fights with participants
- [ ] Transaction rollback works (invalid participant = no fight created)
- [ ] All business rules enforced
- [ ] API endpoints functional

### Documentation
- [ ] BDD scenarios document requirements
- [ ] Code comments explain complex logic
- [ ] Commit messages descriptive
- [ ] ADRs updated if needed

---

## Time Estimates

| Task | Estimated Time | Notes |
|------|---------------|-------|
| Fight BDD Scenarios | 45 min | Document all business requirements |
| Fight Model | 20 min | Follow Phase 1 patterns |
| FightParticipation Model | 20 min | Junction table with constraints |
| Fight Repository Tests | 60 min | 25+ tests |
| FightParticipation Repo Tests | 45 min | 20+ tests |
| Fight Service Tests | 90 min | 35+ tests, complex validation |
| Fight Repository Implementation | 45 min | CRUD + queries |
| FightParticipation Repo Impl | 30 min | Simpler than Fight |
| Fight Service Implementation | 90 min | Business logic + transactions |
| Alembic Migrations | 20 min | 2 migrations |
| Pydantic Schemas | 30 min | Request/Response models |
| API Endpoints | 60 min | Full CRUD |
| Testing & Verification | 10 min | Run full suite |
| Git Commit | 10 min | Descriptive message |
| **TOTAL** | **~9 hours** | **Budget for breaks** |

**Actual velocity from Phase 1**: 50% faster than estimated
**Realistic estimate**: **6-7 hours**

---

## Common Pitfalls to Avoid

### 1. Skipping Tests
**Don't:** Write implementation before tests
**Do:** Follow RED → GREEN → REFACTOR religiously

### 2. Transaction Boundaries
**Don't:** Create fight and participations in separate transactions
**Do:** Use `async with session.begin()` to ensure atomicity

### 3. N+1 Queries
**Don't:** Lazy load participations (triggers extra queries)
**Do:** Use `selectinload(Fight.participations)` in repository

### 4. Validation Location
**Don't:** Validate business rules in repository
**Do:** Keep validation in service layer, data access in repository

### 5. Error Messages
**Don't:** Generic errors like "Invalid data"
**Do:** Specific messages: "Fighter already participating in fight"

---

## Next Phase Preview

**Phase 3: Tag System** (After Phase 2 complete)
- TagType (reference data)
- Tag (hierarchical tagging)
- TagChangeRequest (community voting)
- Vote (session-based voting)

Estimated: 8-10 hours

---

## Questions?

If you encounter blockers:
1. Review Phase 1 code for patterns
2. Check CLAUDE.md for lessons learned
3. Refer to Engineering Implementation document
4. Run tests frequently (fast feedback)

---

**Document Status**: Ready to Execute
**Created**: 2026-01-12
**Phase**: 2 (Fight Entities)
**Prerequisites**: Phase 1 Complete ✅
**Estimated Time**: 6-7 hours

**Good luck! Follow TDD discipline and the tests will guide you to success.** 🎯
