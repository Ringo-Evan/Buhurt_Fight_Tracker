# BDD Scenarios - Implementation Guide

## Overview
This document provides a complete set of BDD scenarios for the MMA Fight Tracking System, covering all core workflows and edge cases identified in the domain model and business rules.

## Scenario Coverage

### 1. Tag Voting System (`tag_voting.feature`)
**Purpose**: Test the community-driven tag voting mechanism

**Scenarios Covered** (11 total):
- ✅ Happy path: Privileged tag reaches threshold and is accepted
- ✅ Rejection path: Insufficient votes lead to rejection
- ✅ Tie scenario: Tied votes favor rejection (maintain current state)
- ✅ Custom tags: Auto-acceptance without voting
- ✅ Fraud prevention: One vote per session ID
- ✅ Concurrent requests: One pending request per tag type
- ✅ Changing existing tags: Replacing current tag values
- ✅ Cancellation: Request creator can cancel
- ✅ Cannot vote on resolved requests

**Key Business Rules Tested**:
- Voting threshold of 10 (configurable)
- Ties favor rejection
- Custom tags bypass voting
- Session-based fraud prevention
- Request status lifecycle (pending → accepted/rejected/cancelled)

### 2. Tag Hierarchy Cascading (`tag_hierarchy.feature`)
**Purpose**: Validate hierarchical tag relationships and cascade behaviors

**Scenarios Covered** (8 total):
- ✅ Category change cascades to all children (subcategory + weapon)
- ✅ Subcategory change cascades to weapon only
- ✅ Weapon change has no cascade effect
- ✅ Adding child tags links to parent via parent_tag_id
- ✅ Orphan prevention: Cannot add child without parent
- ✅ Multiple children restriction: One active child per type
- ✅ Soft delete preserves history

**Key Business Rules Tested**:
- Hierarchy: category → subcategory → weapon
- Cascading soft deletes (isDeleted = true)
- Parent tag linking via parent_tag_id
- Validation prevents orphaned tags
- History preservation through soft deletes

### 3. Fight Creation (`fight_creation.feature`)
**Purpose**: Test fight creation workflow and authorization

**Scenarios Covered** (11 total):
- ✅ Admin creates singles fight with category tag
- ✅ System user creates team fight with multiple fighters
- ✅ Authorization: Regular users cannot create fights
- ✅ Validation: Category tag required at creation
- ✅ Validation: Minimum one fighter per side
- ✅ Validation: Fighter cannot be on both sides
- ✅ Optional: Recording winner_side
- ✅ Optional: Multiple roles per fighter (fighter, coach, alternate)
- ✅ Validation: Only sides 1 or 2 allowed
- ✅ Soft delete: Fighter deletion doesn't break fight

**Key Business Rules Tested**:
- Admin/system-only fight creation (v1)
- Category tag mandatory at creation
- Fight participation rules (sides, roles)
- Winner recording (optional)
- Referential integrity with soft deletes

### 4. Data Integrity & Edge Cases (`data_integrity.feature`)
**Purpose**: Validate system-level constraints and edge cases

**Scenarios Covered** (20 total):
- ✅ Soft delete filtering in queries
- ✅ UUID v4 generation and uniqueness
- ✅ Automatic timestamp tracking (created_at in UTC)
- ✅ Referential integrity validation
- ✅ Country code validation (ISO 3166-1)
- ✅ Vote threshold edge cases (exact threshold, mixed votes)
- ✅ Concurrent request handling
- ✅ Tag hierarchy validation
- ✅ Session ID constraints
- ✅ Fight date validation (no distant future, allows historical)
- ✅ Required field validation (location, tag values)
- ✅ Length constraints (tag values, session IDs)
- ✅ Permission checks (request cancellation)
- ✅ Cross-country team assignment
- ✅ Threshold boundaries (positive, maximum)

**Key Technical Aspects Tested**:
- UUID primary keys
- Soft delete behavior
- Timestamp handling (UTC)
- Foreign key validation
- Input validation and sanitization
- Business rule enforcement
- Permission systems

## Scenario Statistics

| Feature File           | Scenarios | Focus Area                  |
|------------------------|-----------|----------------------------|
| tag_voting.feature     | 11        | Community voting workflow   |
| tag_hierarchy.feature  | 8         | Cascading tag relationships |
| fight_creation.feature | 11        | Fight CRUD and authorization|
| data_integrity.feature | 20        | System constraints & edges  |
| **TOTAL**              | **50**    | **Comprehensive coverage**  |

## Implementation Order

### Phase 1: Database Layer (Week 1-2)
Start with `data_integrity.feature` scenarios to establish:
1. SQLAlchemy models with UUID primary keys
2. Soft delete implementation
3. Timestamp handling
4. Foreign key relationships
5. Input validation at model level

**Why first**: These are foundational and needed by all other features.

### Phase 2: Fight Creation (Week 2-3)
Implement `fight_creation.feature` scenarios:
1. Fight model and FightParticipation model
2. Authorization layer (admin/system role checks)
3. Fight creation service with validation
4. Repository pattern for data access

**Why second**: Fights are the central entity; tags depend on fights existing.

### Phase 3: Basic Tagging (Week 3-4)
Implement non-voting aspects of `tag_hierarchy.feature`:
1. Tag and TagType models
2. Hierarchy validation
3. Parent-child linking
4. Cascade logic for soft deletes

**Why third**: Establish tag structure before adding voting complexity.

### Phase 4: Voting System (Week 4-6)
Implement `tag_voting.feature` scenarios:
1. TagChangeRequest and Vote models
2. Session-based voting logic
3. Threshold calculation
4. Request status lifecycle
5. Custom vs privileged tag handling

**Why last**: Most complex feature; builds on all previous components.

## pytest-bdd Setup

### Required Dependencies
```python
# requirements.txt or pyproject.toml
pytest>=7.4.0
pytest-bdd>=6.1.1
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
sqlalchemy>=2.0.0
alembic>=1.11.0
testcontainers>=3.7.0
```

### Step Definition Structure
```
tests/
├── features/               # .feature files (already created)
│   ├── tag_voting.feature
│   ├── tag_hierarchy.feature
│   ├── fight_creation.feature
│   └── data_integrity.feature
├── step_defs/             # Step definitions (to create)
│   ├── __init__.py
│   ├── common_steps.py    # Shared Given/When/Then
│   ├── tag_voting_steps.py
│   ├── tag_hierarchy_steps.py
│   ├── fight_creation_steps.py
│   └── data_integrity_steps.py
├── conftest.py            # Pytest fixtures
└── unit/                  # Traditional unit tests
```

### Example Step Definition Pattern
```python
# tests/step_defs/tag_voting_steps.py
from pytest_bdd import scenarios, given, when, then, parsers

# Load all scenarios from the feature file
scenarios('../features/tag_voting.feature')

@given(parsers.parse('a tag change request exists with threshold {threshold:d}'))
async def tag_change_request_exists(threshold, db_session):
    # Arrange: Create test data
    request = TagChangeRequest(threshold=threshold, status="pending")
    db_session.add(request)
    await db_session.commit()
    return request

@when(parsers.parse('{count:d} votes "for" are cast on the request'))
async def cast_votes(count, tag_change_request, db_session):
    # Act: Execute behavior
    for i in range(count):
        vote = Vote(
            request_id=tag_change_request.id,
            session_id=f"session-{i}",
            vote_type="for"
        )
        db_session.add(vote)
    await db_session.commit()

@then(parsers.parse('the request status should be "{status}"'))
async def verify_status(status, tag_change_request, db_session):
    # Assert: Verify expectations
    await db_session.refresh(tag_change_request)
    assert tag_change_request.status == status
```

## Next Steps

### 1. Review These Scenarios
**Action Items for You**:
- [ ] Read through all 4 feature files
- [ ] Identify any missing scenarios or edge cases
- [ ] Question any business rules that seem unclear
- [ ] Verify scenarios match your understanding of requirements

**Questions to Consider**:
- Do these scenarios cover all user workflows you envision?
- Are there any tag voting edge cases I missed?
- Should there be scenarios for team management?
- Do we need scenarios for user management (beyond authorization)?

### 2. Create pytest-bdd Infrastructure
**Next Development Tasks**:
1. Set up `conftest.py` with database fixtures (Testcontainers)
2. Create `tests/step_defs/common_steps.py` for shared steps
3. Implement step definitions for `data_integrity.feature` (simplest)
4. Write corresponding SQLAlchemy models
5. Verify tests fail appropriately (TDD red phase)

### 3. Decide on Deferred Scenarios
**Optional Scenarios to Add Later**:
- User registration and authentication (v1 uses session_id only)
- Fighter profile management (CRUD operations)
- Team management (creating teams, adding/removing fighters)
- Search and filtering (finding fights by tags, date, location)
- Pagination for large result sets
- Rate limiting for API endpoints

## Business Rules Summary

These scenarios validate the following business rules documented in `docs/business-rules.md`:

| Rule | Scenarios |
|------|-----------|
| Privileged tags require voting | tag_voting.feature (multiple) |
| Custom tags auto-accepted | tag_voting: "Custom tag is immediately accepted" |
| One pending request per tag type | tag_voting: "Cannot create second pending request" |
| Vote threshold = 10 | tag_voting: Multiple scenarios use threshold |
| Ties favor rejection | tag_voting: "Tied votes is rejected" |
| Category change cascades | tag_hierarchy: "Changing category nullifies..." |
| Subcategory change cascades | tag_hierarchy: "Changing subcategory nullifies weapon" |
| Category required at creation | fight_creation: "Cannot create fight without category" |
| Admin/system only creates fights | fight_creation: "Regular user cannot create fight" |
| Anonymous voting via session_id | tag_voting: Multiple voting scenarios |

## Testing Philosophy

These BDD scenarios follow your project's TDD principles:

1. **Scenarios First**: Written BEFORE any implementation code
2. **Behavior-Focused**: Describe WHAT the system does, not HOW
3. **Business Language**: Readable by non-technical stakeholders
4. **Comprehensive**: Cover happy paths, error cases, and edge cases
5. **Maintainable**: Clear structure, reusable steps, good naming

## Common Patterns Used

### Scenario Pattern
```gherkin
Scenario: [What is being tested] [under what conditions] [expected result]
  Given [initial state]
  And [additional context]
  When [action is performed]
  Then [observable outcome]
  And [additional verification]
```

### Data Table Pattern
```gherkin
Given the following entities exist:
  | field1 | field2 | field3 |
  | value1 | value2 | value3 |
```

### Background Pattern
Used in every feature file to set up common test data, reducing repetition across scenarios.

## Coverage Gaps to Address in Unit Tests

BDD scenarios test behavior; unit tests should cover:
- Individual validation functions (e.g., `validate_iso_country_code()`)
- Edge cases in utility functions
- Error message formatting
- Database query optimization
- Async error handling
- Type conversions and parsing

## Questions for Review

1. **Missing Workflows**: Are there any user workflows not covered?
2. **Tag Types**: Should we add scenarios for creating/managing tag types themselves?
3. **Thresholds**: Should threshold be configurable per tag type, not just per request?
4. **Notifications**: Do we need scenarios for notifying users when their requests resolve?
5. **Moderation**: Should admins be able to override vote outcomes?
6. **History**: Do we need a scenario for viewing tag change history?
7. **Fighter Teams**: Should fighters be required to have teams, or can they be independent?

Please review and let me know what needs adjustment or addition!
