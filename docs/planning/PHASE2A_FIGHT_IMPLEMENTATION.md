# Implementation Plan: Phase 2 - Tag Foundation & Fight System

**Created**: 2026-01-11
**Last Updated**: 2026-01-26
**Author**: Claude Opus 4.5
**Scope**: Phase 2A (TagType, Tag) + Phase 2B (Fight, FightParticipation)

---

## Executive Summary

This document outlines the TDD implementation plan for the remaining core domain entities. All design decisions are documented with rationale.

**Phase 2A Status**: ✅ COMPLETE (2026-01-26)
**Phase 2B Status**: 📋 READY TO BEGIN

---

## Entity Dependency Graph

```
                    Country ✅
                       │
                    Team ✅
                       │
                   Fighter ✅
                       │
    ┌──────────────────┼──────────────────┐
    │                  │                  │
    ▼                  ▼                  │
  Fight ⏸️ ◄─── FightParticipation ⏸️    │
    │                                     │
    │         TagType ✅ (2026-01-24)     │
    │              │                      │
    └──────────────┼──────────────────────┘
                   │
                   ▼
                  Tag ✅ (2026-01-26)
                   │
                   ▼
           TagChangeRequest 📋 (deferred to v2)
                   │
                   ▼
                 Vote 📋 (deferred to v2)
```

**Status Update (2026-01-26)**:
- ✅ TagType: Complete with 19 unit tests + 8 integration tests
- ✅ Tag: Complete with 9 unit tests + 9 integration tests (STRICT TDD)
- ⏸️ Fight: Next to implement
- ⏸️ FightParticipation: After Fight
- 📋 TagChangeRequest + Vote: Deferred to v2 (per DD-006)

---

## Design Decisions

### DD-001: Fight Date Handling
**Decision**: Store fight date as `DATE` (not `DATETIME`)
**Rationale**: Fights are events that happen on a specific day; exact time is rarely known or relevant for historical fights.

### DD-002: Fight Location
**Decision**: Store location as simple `VARCHAR(200)` string
**Rationale**: For a portfolio project, complex geocoding is over-engineering. A simple string like "IMCF World Championship 2024, Warsaw, Poland" is sufficient.

### DD-003: Fight Video URL
**Decision**: Single `video_url` field (VARCHAR 500)
**Rationale**: Most fights have one primary video source. Multiple URLs can be added later if needed.

### DD-004: Winner Tracking
**Decision**: `winner_side` field with values 1, 2, or NULL (draw/unknown)
**Rationale**: Simpler than tracking winner_fighter_id. Side-based tracking works for both singles and team fights.

### DD-005: FightParticipation Roles
**Decision**: Enum with values: 'fighter', 'captain', 'alternate', 'coach'
**Rationale**: Covers all common Buhurt participation types. Captain is special for team fights.

### DD-006: TagType as Database Table (not Python Enum)
**Decision**: Store tag types in database table, not Python enum
**Rationale**:
- Allows adding new tag types without code deployment
- Foreign key integrity between Tag and TagType
- Easier to query and filter

### DD-007: Tag Hierarchy via parent_tag_id
**Decision**: Self-referential FK on Tag table
**Rationale**: Simple, efficient, supports arbitrary depth. No junction tables needed.

### DD-008: Voting Threshold
**Decision**: Default threshold of 10 votes, stored in TagChangeRequest
**Rationale**: Per-request threshold allows future flexibility (e.g., higher threshold for supercategory changes).

### DD-009: Session-Based Anonymous Voting
**Decision**: Track votes by session_id (UUID), not user_id
**Rationale**: Phase 1 has no user auth. Session ID provides basic duplicate prevention.

### DD-010: Vote Direction as Boolean
**Decision**: `is_upvote: bool` (True = for, False = against)
**Rationale**: Simple binary voting. Boolean is cleaner than enum for two values.

---

## Implementation Order

### 1. Fight Entity
- Model with: id, date, location, video_url, winner_side, is_deleted, created_at
- No FK dependencies on new entities (depends only on existing Fighter)
- Repository: CRUD + list_by_date_range
- Service: Validation (date not future, URL format)
- Schema: FightCreate, FightUpdate, FightResponse
- API: Full CRUD endpoints

### 2. FightParticipation Entity (Junction)
- Model with: id, fight_id (FK), fighter_id (FK), side (1 or 2), role (enum)
- Composite unique constraint: (fight_id, fighter_id)
- Repository: CRUD + list_by_fight + list_by_fighter
- Service: Validate fighter not on both sides
- Schema: Participation schemas
- API: Nested under /fights/{id}/participants

### 3. TagType Entity
- Model with: id, name, is_privileged, display_order, is_deleted
- Seed data: category, subcategory, weapon, gender, rule_set, league, custom
- Repository: Simple CRUD
- Service: Minimal (mostly read-only reference data)
- Schema: TagTypeResponse (read-only)
- API: GET only (admin can POST/PATCH)

### 4. Tag Entity
- Model with: id, fight_id (FK), tag_type_id (FK), value, parent_tag_id (self-FK), is_deleted
- Unique constraint: (fight_id, tag_type_id, value) WHERE NOT is_deleted
- Repository: CRUD + list_by_fight + get_hierarchy
- Service: Validate parent exists, hierarchy rules, cascade soft-delete
- Schema: TagCreate, TagResponse, TagHierarchyResponse
- API: Full CRUD under /fights/{id}/tags

### 5. TagChangeRequest Entity
- Model with: id, fight_id (FK), tag_type_id (FK), proposed_value, current_value, status, threshold, votes_for, votes_against, created_at, resolved_at
- Status enum: pending, accepted, rejected
- Repository: CRUD + list_pending + resolve
- Service: Create request, check duplicates, auto-resolve on threshold
- Schema: Request/Response schemas
- API: POST to create, GET to list, no direct PATCH (resolved via votes)

### 6. Vote Entity
- Model with: id, tag_change_request_id (FK), session_id, is_upvote, created_at
- Unique constraint: (tag_change_request_id, session_id)
- Repository: CRUD + count_by_request
- Service: Validate not duplicate, trigger request resolution check
- Schema: VoteCreate, VoteResponse
- API: POST /tag-requests/{id}/votes

---

## Test Strategy (TDD)

For each entity, follow this order:

1. **Write BDD Scenarios** (tests/features/{entity}.feature)
   - Happy path CRUD
   - Validation errors
   - Edge cases
   - Relationship constraints

2. **Write Unit Tests - Repository** (tests/unit/repositories/)
   - Mock AsyncSession
   - Test all repository methods
   - Test soft delete filtering
   - Test relationship loading

3. **Write Unit Tests - Service** (tests/unit/services/)
   - Mock repository
   - Test business logic
   - Test validation
   - Test error handling

4. **Implement Model** (app/models/)
   - SQLAlchemy model
   - Relationships
   - Constraints

5. **Implement Repository** (app/repositories/)
   - All CRUD methods
   - Eager loading
   - Soft delete filtering

6. **Implement Service** (app/services/)
   - Business logic
   - Validation
   - Exception handling

7. **Implement Schema** (app/schemas/)
   - Pydantic models
   - Validation

8. **Implement API** (app/api/v1/)
   - FastAPI router
   - Error handling
   - OpenAPI docs

9. **Create Migration** (alembic/versions/)
   - Create table
   - Add constraints
   - Add indexes

10. **Verify All Tests Pass**

---

## File Structure (New Files)

```
app/
├── models/
│   ├── fight.py              # NEW
│   ├── fight_participation.py # NEW
│   ├── tag_type.py           # NEW
│   ├── tag.py                # NEW
│   ├── tag_change_request.py # NEW
│   └── vote.py               # NEW
├── repositories/
│   ├── fight_repository.py
│   ├── fight_participation_repository.py
│   ├── tag_type_repository.py
│   ├── tag_repository.py
│   ├── tag_change_request_repository.py
│   └── vote_repository.py
├── services/
│   ├── fight_service.py
│   ├── fight_participation_service.py
│   ├── tag_type_service.py
│   ├── tag_service.py
│   ├── tag_change_request_service.py
│   └── vote_service.py
├── schemas/
│   ├── fight.py
│   ├── fight_participation.py
│   ├── tag_type.py
│   ├── tag.py
│   ├── tag_change_request.py
│   └── vote.py
└── api/v1/
    ├── fights.py
    ├── tag_types.py
    └── tag_requests.py

tests/
├── unit/
│   ├── repositories/
│   │   ├── test_fight_repository.py
│   │   ├── test_fight_participation_repository.py
│   │   ├── test_tag_type_repository.py
│   │   ├── test_tag_repository.py
│   │   ├── test_tag_change_request_repository.py
│   │   └── test_vote_repository.py
│   └── services/
│       ├── test_fight_service.py
│       ├── test_fight_participation_service.py
│       ├── test_tag_type_service.py
│       ├── test_tag_service.py
│       ├── test_tag_change_request_service.py
│       └── test_vote_service.py
└── features/
    ├── fight_management.feature
    ├── fight_participation.feature
    ├── tagging.feature
    └── tag_voting.feature

alembic/versions/
├── xxxx_create_fights_table.py
├── xxxx_create_fight_participation_table.py
├── xxxx_create_tag_types_table.py
├── xxxx_create_tags_table.py
├── xxxx_create_tag_change_requests_table.py
└── xxxx_create_votes_table.py
```

---

## Estimated Scope

| Entity | Unit Tests | Est. LOC | Complexity |
|--------|-----------|----------|------------|
| Fight | ~25 | ~400 | Medium |
| FightParticipation | ~20 | ~350 | Medium |
| TagType | ~10 | ~150 | Low |
| Tag | ~30 | ~500 | High |
| TagChangeRequest | ~25 | ~450 | High |
| Vote | ~15 | ~250 | Medium |
| **Total** | **~125** | **~2100** | - |

---

## Success Criteria

1. ✅ All new unit tests pass
2. ✅ Existing 130 tests still pass
3. ✅ Code coverage >90%
4. ✅ All API endpoints functional
5. ✅ OpenAPI docs generated
6. ✅ Migrations apply cleanly
7. ✅ No lint errors
8. ✅ Documented design decisions

---

## Let's Begin!

Starting with Fight entity following TDD workflow...
