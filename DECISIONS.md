# Buhurt Fight Tracker - Decisions & Open Questions

**Purpose**: Single location for all architectural decisions, open questions, and their resolutions.
**Last Updated**: 2026-01-18

---

## Decision Status Key

| Status | Meaning |
|--------|---------|
| ✅ DECIDED | Decision made and implemented |
| 📋 DECIDED | Decision made, not yet implemented |
| ❓ OPEN | Needs discussion/decision |
| ⏸️ DEFERRED | Intentionally postponed |

---

## Architectural Decisions (Implemented)

### ADR-001: UUID Primary Keys ✅ DECIDED

**Decision**: Use UUIDs for all primary keys instead of auto-increment integers.

**Rationale**:
- No information leakage (can't enumerate records)
- Distributed system friendly (merge databases)
- Standard in modern systems

**Trade-offs Accepted**:
- Slightly larger storage (16 bytes vs 4-8)
- Less human-readable
- Can't sort by creation order without timestamp

**Implemented**: All entities (Country, Team, Fighter)

---

### ADR-002: Soft Deletes ✅ DECIDED

**Decision**: Use `is_deleted` boolean flag for soft deletes on all main entities.

**Rationale**:
- Preserve referential integrity
- Enable audit trails
- Support "undo" functionality

**Implementation**:
```python
is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
```

**Query Pattern**:
```python
stmt = select(Entity).where(Entity.is_deleted == False)
```

**Implemented**: All entities

---

### ADR-003: UTC Timestamps ✅ DECIDED

**Decision**: All timestamps stored in UTC using `datetime.now(UTC)`.

**Rationale**:
- Consistent regardless of server timezone
- Python 3.12+ compatible (avoids deprecated `utcnow()`)
- Standard practice for APIs

**Implementation**:
```python
from datetime import datetime, UTC
created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
```

**Implemented**: All entities

---

### ADR-004: Three-Layer Architecture ✅ DECIDED

**Decision**: Strict separation into Repository → Service → API layers.

**Rationale**:
- Clear separation of concerns
- Testable in isolation
- Industry standard pattern

**Rules**:
- Repository: Data access ONLY, no business logic
- Service: Business logic, validation, orchestration
- API: HTTP layer, error translation, no logic

**Implemented**: Country, Team, Fighter

---

### ADR-005: Eager Loading by Default ✅ DECIDED

**Decision**: Configure relationships for eager loading to prevent N+1 queries.

**Implementation**:
```python
team: Mapped["Team"] = relationship("Team", lazy="joined")

# In repository
stmt = select(Fighter).options(selectinload(Fighter.team).selectinload(Team.country))
```

**Implemented**: Fighter → Team → Country chain

---

## Architectural Decisions (Planned)

### DD-001: Tags Created on Vote Acceptance 📋 DECIDED

**Decision**: Tag records only created when vote threshold reached, not at proposal time.

**Rationale**:
- Simpler data model (no "pending tags")
- Clearer state management
- Proposed values stored as strings in TagChangeRequest

**Status**: Documented, implementation deferred (simplified tag system for v1)

---

### DD-002: Fight as Aggregate Root 📋 DECIDED

**Decision**: Fight + FightParticipations treated as single transactional unit.

**Rationale**:
- Atomic creation (all-or-nothing)
- Service layer orchestrates both repositories
- Clear consistency boundary

**Implementation Pattern**:
```python
async def create_fight_with_participants(self, fight_data, participations):
    async with self.session.begin():
        fight = await self.fight_repo.create(fight_data)
        for p in participations:
            await self.participation_repo.create({...})
        return fight
```

**Status**: Ready to implement in Phase 2

---

### DD-003: Simplified Tag System for v1 📋 DECIDED

**Decision**: Implement flat tags (no hierarchy, no voting) for portfolio version.

**Original Design** (documented in tag-rules.md):
- Hierarchical: SuperCategory → Category → Subcategory → Weapon
- Community voting on privileged tags
- Cascading soft deletes

**v1 Simplified Design**:
- TagType: Category, Gender, Custom
- Tag: Simple key-value on fights
- Custom tags: Auto-accepted
- Category/Gender: Admin-only assignment

**Rationale**:
- Full voting system adds ~15 hours without proportional portfolio value
- Design is documented, shows system thinking
- Can implement full system in v2

**Trade-offs Accepted**:
- Less impressive feature set
- But: shows pragmatic scoping (leadership skill)

---

## Open Questions

### OQ-001: Fighter.team_id Nullable? ❓ OPEN

**Question**: Can fighters compete without a team (independent)?

**Options**:
1. **Required team**: Create "Independent" placeholder team
2. **Nullable**: Allow NULL team_id

**Considerations**:
- Required simplifies queries (no NULL checks)
- Nullable matches real-world (some fighters are unaffiliated)
- Can change nullable→required easier than reverse

**Current State**: team_id is nullable in implementation

**Recommendation**: Keep nullable, revisit if it causes issues

---

### OQ-002: Soft Delete + Unique Constraints ❓ OPEN

**Question**: How to handle unique constraints with soft deletes?

**Problem**: If "USA" is soft-deleted, can we create new "USA"?

**Options**:
1. **Partial unique index**: `UNIQUE (name) WHERE is_deleted = FALSE`
2. **Include is_deleted in unique**: `UNIQUE (name, is_deleted)` (allows one active, one deleted)
3. **Hard delete for some tables**: Different strategy per entity

**Current State**: Using option 1 (partial index) where needed

**Status**: Working, monitor for issues

---

### OQ-003: Integration Test Execution ❓ OPEN

**Question**: Are integration tests running successfully?

**Current State**: 41 integration tests written, require Docker

**Blockers**:
- Docker Desktop availability varies
- Testcontainers startup time (~2-4 seconds)

**Action Needed**: Verify Docker setup, run integration tests

---

### OQ-004: BDD Test Format ⏸️ DEFERRED

**Question**: Should BDD scenarios only cover UI interactions, or also API/service behavior?

**Current Approach**: BDD scenarios document service-level behavior, implemented as integration tests.

**Options**:
1. **UI-only BDD**: Gherkin for E2E, pytest for everything else
2. **API BDD**: Gherkin for API contracts (current approach)
3. **Domain BDD**: Gherkin for service behavior (current approach)
4. **Hybrid**: All of the above

**Decision**: Keep current approach (domain BDD). Articulate this choice in interviews as intentional.

**Rationale**: For portfolio, showing behavior documentation is valuable regardless of test execution level.

---

## Deferred Decisions

### DF-001: Vote Fraud Prevention ⏸️ DEFERRED

**Original Plan**: Session ID tracking, IP logging, rate limiting

**Deferred To**: v2 (when auth implemented)

**Rationale**: Can't meaningfully prevent fraud without user accounts

---

### DF-002: Tag Hierarchy Cascading ⏸️ DEFERRED

**Original Plan**: Changing category soft-deletes subcategory and weapon

**Deferred To**: v2 (with full tag system)

**Documented In**: tag-rules.md (preserves design work)

---

### DF-003: Moderator Roles ⏸️ DEFERRED

**Original Plan**: Granular permissions (admin, moderator, user)

**v1 Approach**: Just admin/user distinction, no auth

**Deferred To**: v2 (auth phase)

---

### DF-004: Search and Filtering ⏸️ DEFERRED

**Original Plan**: Advanced search across fights, fighters, tags

**v1 Approach**: Basic list endpoints with simple filters

**Deferred To**: v2 or v3

**Documented In**: business-rules.md

---

## Scope Decisions (Portfolio Focus)

### SD-001: What's In Scope for Portfolio ✅ DECIDED

**In Scope**:
- Country, Team, Fighter (complete)
- Fight + FightParticipation
- Simplified Tags (no voting)
- Full test coverage
- API documentation
- Architecture documentation (ADRs)

**Out of Scope** (documented as future work):
- User authentication
- Tag voting system
- Frontend
- Production deployment
- E2E tests

**Rationale**: 
- Portfolio demonstrates TDD/BDD discipline, clean architecture, system design
- Partial implementation + good documentation > complete but sloppy

---

### SD-002: Target Interview Narrative ✅ DECIDED

**Story to Tell**:
1. "I designed a complex domain model for fight tracking with community tagging"
2. "I followed strict TDD/BDD discipline - every feature has tests first"
3. "I made pragmatic scope decisions - implemented core, documented future"
4. "I can show you the ADRs explaining my architectural choices"
5. "Test coverage is 90%+ across all implemented layers"

**Evidence to Show**:
- Git history with test-first commits
- ADR documents with rationale
- Comprehensive test suite
- OpenAPI documentation
- This decisions document (meta-documentation)

---

## Questions for Future Consideration

These don't need answers now, but should be considered eventually:

1. **Caching**: Should frequently accessed data (countries, tag types) be cached?
2. **Pagination**: How to handle large result sets?
3. **Audit Logging**: Should we track who changed what when?
4. **Event Sourcing**: Would fight history benefit from event log?
5. **API Versioning**: How to handle breaking changes?

---

## How to Use This Document

### When Making Decisions

1. Check if question is already answered here
2. If new decision needed, add to appropriate section
3. Document rationale (future you will forget why)
4. Update status when implemented

### When Reviewing with Claude

1. Reference decision IDs (e.g., "per ADR-001, we're using UUIDs")
2. Check open questions before asking something that might be answered
3. Add new questions that come up during implementation

### For Interviews

1. This document demonstrates system thinking
2. Shows ability to make and document decisions
3. Deferred decisions show pragmatic scoping
4. Open questions show awareness of complexity

---

## Change Log

| Date | Change |
|------|--------|
| 2026-01-18 | Initial consolidation from multiple docs |
| 2026-01-14 | ADR-001 through ADR-005 implemented |
| 2025-12-11 | Project started, initial design decisions |
