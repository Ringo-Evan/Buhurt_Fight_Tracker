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

### DD-001: Tags Before Fights (Dependency Order) 📋 DECIDED

**Decision**: Build Tag Foundation (Phase 2A) before Fight entity (Phase 2B).

**Rationale**:
- Fight validation rules depend on `fight_format` tag (singles vs melee)
- Singles allows exactly 1 fighter per side
- Melee requires minimum 5 fighters per side
- Without tags, Fight cannot properly validate participant counts

**Trade-offs Accepted**:
- Slightly more work before "Fight" entity exists
- But: no throwaway code, no refactoring needed later

**Alternative Rejected**: Enum on Fight model (would require migration to tags later)

---

### DD-002: fight_format Tag Type 📋 DECIDED

**Decision**: Use `fight_format` as the name for the required singles/melee distinction.

**Values**: `"singles"`, `"melee"`

**Properties**:
- Required: Yes (every fight must have exactly one)
- Created: Atomically with Fight (same transaction)

**Alternatives Considered**:
- `super_category` (original name) - too abstract
- `fight_type` - could be confused with other meanings
- `match_type` - less clear
- `format` - too generic

---

### DD-003: Singles Fighter Validation 📋 DECIDED

**Decision**: Singles fights allow exactly 1 fighter per side.

**Validation**:
```python
if fight_format == "singles":
    side_1_count = len([p for p in participants if p.side == 1 and p.role == "fighter"])
    side_2_count = len([p for p in participants if p.side == 2 and p.role == "fighter"])
    if side_1_count != 1 or side_2_count != 1:
        raise InvalidParticipantCountError("Singles fights require exactly 1 fighter per side")
```

**Note**: Alternates/coaches may be allowed in future, but don't count toward fighter requirement.

---

### DD-004: Melee Fighter Validation 📋 DECIDED

**Decision**: Melee fights require minimum 5 fighters per side.

**Rationale**:
- 5v5 is the smallest standard melee format
- Allows testing with real-world data (5s fights are common)
- Team size maximums (3s, 5s, 10s, etc.) deferred to Phase 3

**Validation**:
```python
if fight_format == "melee":
    side_1_count = len([p for p in participants if p.side == 1 and p.role == "fighter"])
    side_2_count = len([p for p in participants if p.side == 2 and p.role == "fighter"])
    if side_1_count < 5 or side_2_count < 5:
        raise InvalidParticipantCountError("Melee fights require at least 5 fighters per side")
```

**Future (Phase 3)**: Category tag (3s, 5s, 10s, etc.) will enforce specific team sizes.

---

### DD-005: Fight as Aggregate Root 📋 DECIDED

**Decision**: Fight + Tag + FightParticipations treated as single transactional unit.

**Rationale**:
- Atomic creation (all-or-nothing)
- Service layer orchestrates multiple repositories
- Clear consistency boundary

**Implementation Pattern**:
```python
async def create_fight_with_participants(self, fight_data, fight_format, participations):
    async with self.session.begin():
        fight = await self.fight_repo.create(fight_data)
        await self.tag_repo.create({
            "fight_id": fight.id,
            "tag_type_id": self.fight_format_tag_type_id,
            "value": fight_format
        })
        for p in participations:
            await self.participation_repo.create({...})
        return fight
```

**Status**: Ready to implement in Phase 2B

---

### DD-006: Simplified Tag System for v1 📋 DECIDED

**Decision**: Implement tag hierarchy without voting for portfolio version.

**v1 Scope** (Phases 2A + 3):
- TagType: fight_format (required), category, gender, weapon, league, custom
- Tag: Links to fights with hierarchy support
- Cascading soft deletes when parent changes
- Admin-only tag management (no community voting)

**Deferred to v2**:
- TagChangeRequest entity
- Vote entity
- Community voting workflow
- Session-based fraud prevention

**Rationale**:
- Voting system adds ~15 hours without proportional portfolio value
- Hierarchy and cascading demonstrate domain modeling skills
- Design is documented in tag-rules.md, shows system thinking
- Can implement full voting in v2 after auth exists

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


### OQ-005: Open Tofu or Teraform

**Question**: Whether to change to Open Tofu from Teraform for IAC?

**Current Choice**: Teraform

**Pros**:
 * Open-Source better fit for community project
 * No worries about licenscing
 * Have more experience with it than Teraform proper

**Cons**:
 * Not as common in corporate projects
 * No official support from Hashicorp
 * Possibly behind?

**Action Needed**: Investigate practical differences between the two


### OQ-006: Trunk Based Development

**Question**: Is there value to following a strict Trunk based development process?
 
**Current Branching Strategy**: None, Many commits straight to dev

**Pros**
 * Only one developer and AI agent working so branches less important anyway
 * Should force smaller commits and running tests constantly
 * Force Pipeline work earlier

**Cons**
 * Branching strategies are more common
 * Not familiar with TBD

**Actions Needed**




---

## Deferred Decisions

### DF-001: Vote Fraud Prevention ⏸️ DEFERRED

**Original Plan**: Session ID tracking, IP logging, rate limiting

**Deferred To**: v2 (when auth implemented)

**Rationale**: Can't meaningfully prevent fraud without user accounts

---

### DF-002: Team Size Maximums ⏸️ DEFERRED

**Original Plan**: Enforce exact team sizes (3s = 3-5, 5s = 5-8, etc.)

**v1 Approach**: Just minimum 5 for melee, no maximum

**Deferred To**: Phase 3 (when category tag added)

**Rationale**: Minimum validation proves the pattern; maximums are straightforward extension

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

### DF-005: Full Azure PostgreSQL ⏸️ DEFERRED

**Original Plan**: Azure Database for PostgreSQL Flexible Server (~$25/mo)

**v1 Approach**: Neon free tier (serverless Postgres, $0/mo)

**Deferred To**: Production deployment (if ever)

**Rationale**: 
- Neon is real Postgres, same SQL/features
- Free tier sufficient for portfolio
- Can migrate data if needed later

---

### DF-006: Infrastructure as Code ⏸️ OPTIONAL

**Plan**: Terraform for reproducible infrastructure

**Status**: Phase 4B, optional stretch goal

**Rationale**:
- High learning value
- Not required for portfolio complete
- Can add after basic deployment works

---

## Scope Decisions (Portfolio Focus)

### SD-001: What's In Scope for Portfolio ✅ DECIDED

**In Scope (v1)**:
- Country, Team, Fighter (✅ complete)
- TagType + Tag (fight_format required, hierarchy in Phase 3)
- Fight + FightParticipation
- Format-dependent validation (singles vs melee)
- Full test coverage (unit, integration, BDD)
- API documentation (OpenAPI)
- Architecture documentation (ADRs)
- **Cloud deployment (Azure App Service + Neon)**
- CI/CD pipeline (GitHub Actions)

**Out of Scope (documented as v2/v3)**:
- User authentication
- Tag voting system
- Frontend (React/TypeScript)
- Production-grade infrastructure (managed Postgres, monitoring)
- E2E tests with Playwright

**Rationale**: 
- Portfolio demonstrates TDD/BDD discipline, clean architecture, deployment skills
- Deployed API is more impressive than localhost demo
- Partial implementation + documentation > complete but undocumented

---

### SD-002: Target Interview Narrative ✅ DECIDED

**Story to Tell**:
1. "I designed a complex domain model for fight tracking with hierarchical tagging"
2. "I discovered that Fight depends on Tags for validation - showing I understood the domain"
3. "I followed strict TDD discipline - tests defined requirements before code"
4. "I made pragmatic scope decisions - implemented core, documented future work"
5. "I deployed to Azure with cost-conscious infrastructure choices"
6. "I can show you ADRs explaining my architectural choices"
7. "Test coverage is 90%+ across all implemented layers"

**Evidence to Show**:
- Git history with test-first commits
- ADR documents with rationale
- Comprehensive test suite
- OpenAPI documentation
- Live deployed API
- This decisions document (meta-documentation)
- Cost management scripts (shows operational thinking)

---

### SD-003: Deployment Strategy ✅ DECIDED

**Stack**:
- **Compute**: Azure App Service B1 (~$13/mo when running)
- **Database**: Neon PostgreSQL free tier ($0/mo)
- **CI/CD**: GitHub Actions
- **Cost Management**: Stop/start scripts

**Rationale**:
- Real cloud deployment (not just localhost)
- Near-zero cost during development
- Learn Azure fundamentals
- Neon is production-quality Postgres
- Can upgrade components independently

**Monthly Cost Target**: <$5/month during development

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
| 2026-01-18 | Added DD-001 through DD-006 (tags before fights, fight_format, validation rules) |
| 2026-01-18 | Added SD-003 (deployment strategy with Neon + Azure) |
| 2026-01-18 | Added DF-005, DF-006 (Azure Postgres deferred, IaC optional) |
| 2026-01-18 | Restructured phases: 2A (tags) → 2B (fights) → 3 (tag expansion) → 4A/4B (deployment) |
| 2026-01-18 | Initial consolidation from multiple docs |
| 2026-01-14 | ADR-001 through ADR-005 implemented |
| 2025-12-11 | Project started, initial design decisions |
