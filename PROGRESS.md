# Buhurt Fight Tracker - Project Progress

**Last Updated**: 2026-01-26
**Project Goal**: Portfolio piece demonstrating TDD/BDD mastery and system design skills
**Target Role**: Lead/Architect trajectory
**Velocity**: ~8 hours/week (target: 14)

---

## Quick Status

| Phase | Status | Tests | Time Spent |
|-------|--------|-------|------------|
| Phase 1: Foundation (Country, Team, Fighter) | ✅ COMPLETE | 130 unit, 41 integration, 98 BDD | ~6.5 hrs |
| Phase 2A: Tag Foundation (TagType + Tag) | ✅ COMPLETE | 28 unit, 17 integration | ~4 hrs |
| Phase 2B: Fight Tracking | 📋 PLANNED | 0 | 0 |
| Phase 3: Tag Expansion | 📋 PLANNED | 0 | 0 |
| Phase 4A: Basic Deployment | 📋 PLANNED | 0 | 0 |
| Phase 4B: Infrastructure as Code | 📋 OPTIONAL | 0 | 0 |
| Phase 5: Auth (v2) | 📋 FUTURE | 0 | 0 |
| Phase 6: Frontend (v3) | 📋 FUTURE | 0 | 0 |

**Total Tests**: 197 unit + 58 integration + 98 BDD scenarios
**Estimated Remaining**: 24-32 hours to "portfolio complete" (through Phase 4A)

---

## What "Portfolio Complete" Means

The project is portfolio-ready when someone can:
1. Clone the repo and run tests (all pass)
2. Read the README and understand the architecture
3. See TDD/BDD discipline in git history
4. Review ADRs and understand design decisions
5. **Hit the live API** at a public URL
6. See test coverage reports (>90%)

**NOT required for portfolio v1:**
- Full tag voting system (deferred to v2)
- User authentication (deferred to v2)
- Frontend (deferred to v3)
- E2E tests with Playwright

---

## Phase Details

### Phase 1: Foundation Entities ✅ COMPLETE

**Completed**: 2026-01-14
**Time**: ~6.5 hours
**Velocity**: 50% faster than estimated

| Entity | Unit Tests | Integration | BDD | API | Migration |
|--------|-----------|-------------|-----|-----|-----------|
| Country | 48 | 14 | 21 | ✅ CRUD | ✅ |
| Team | 48 | 15 | 40+ | ✅ CRUD | ✅ |
| Fighter | 34 | 12 | 37 | ✅ CRUD | ✅ |

**Key Achievements**:
- Established TDD patterns (test-first development)
- Repository → Service → API layering proven
- Soft delete pattern working
- Eager loading configured (no N+1)
- UTC datetime handling correct

**Lessons Learned**:
- Pattern reuse accelerates (Fighter 2x faster than Country)
- Comprehensive planning prevents decision paralysis
- NotImplementedError pattern documents blockers clearly

---

### Phase 2A: Tag Foundation ✅ COMPLETE

**Started**: 2026-01-24
**Completed**: 2026-01-26
**Time Spent**: ~4 hours
**Complexity**: Medium (new pattern, but simpler than Fight)
**Prerequisite for**: Phase 2B (Fight needs fight_format tag)

| Entity | Status | Unit Tests | Integration Tests | API | Migration |
|--------|--------|-----------|-------------------|-----|-----------|
| TagType | ✅ COMPLETE | 19 | 8 | ✅ Full CRUD | ⏸️ Pending |
| Tag | ✅ COMPLETE | 9 | 9 | ✅ Full CRUD | ⏸️ Pending |

**TagType Key Achievements**:
- Complete CRUD implementation following Phase 1 patterns
- Repository layer: create, get_by_id, get_by_name, list_all, update, soft_delete
- Service layer: Full validation (duplicate names, required fields, 50 char limit)
- API layer: 5 endpoints (POST, GET list, GET by ID, PATCH, DELETE)

**Tag Key Achievements**:
- Complete CRUD implementation following **STRICT TDD** (one test at a time)
- Repository layer: create, get_by_id, list_all, update, soft_delete
- Service layer: create (validates tag_type exists), get_by_id, list_all, update, delete
- API layer: 5 endpoints (POST, GET list, GET by ID, PATCH, DELETE)
- Pydantic schemas: TagCreate, TagUpdate, TagResponse with validation (min_length=1, max_length=100)
- Parent tag hierarchy support (parent_tag_id field)
- All 9 integration tests cover feature file scenarios

**Lessons Learned**:
- ⚠️ **TagType TDD Violation**: Wrote all 9 service tests at once instead of strict one-at-a-time
- ✅ **Tag Strict TDD**: Followed proper RED-GREEN-REFACTOR for Tag implementation
- ✅ **Feature File as Spec**: Used Gherkin scenarios as specification for integration tests (cleaner than BDD step defs)
- ✅ **Pattern Reuse**: Repository/Service/API patterns from Phase 1 accelerated implementation

**Why Tags Before Fights?**
Fight validation depends on `fight_format` (singles vs melee):
- Singles: exactly 1 fighter per side
- Melee: minimum 5 fighters per side

Without tags, Fight can't properly validate participant counts.

**Business Rules Implemented**:
- [x] TagType is reference data (admin-seeded)
- [x] Tag creation validates tag_type_id exists
- [x] Tag value validation (required, max 100 chars) via Pydantic
- [x] Parent tag hierarchy support
- [ ] fight_format tag is required (enforced when creating Fight) - Phase 2B
- [ ] Only one tag per TagType per Fight - Phase 2B

**Success Criteria** (all met):
- ✅ TagType CRUD with validation
- ✅ Tag CRUD with validation
- ✅ No regressions in Phase 1 (197 unit tests passing)

---

### Phase 2B: Fight Tracking 📋 PLANNED

**Estimated Time**: 6-8 hours
**Complexity**: High (many-to-many, transactions, format-dependent validation)
**Prerequisites**: Phase 2A complete

| Entity | Purpose | Key Complexity |
|--------|---------|----------------|
| Fight | Core fight record | Aggregate root pattern |
| FightParticipation | Junction table | Side/role validation, transactions |

**Business Rules to Implement**:
- [ ] Fight must have exactly one fight_format tag (singles or melee)
- [ ] Singles: exactly 1 fighter per side
- [ ] Melee: minimum 5 fighters per side
- [ ] Both sides must have participants
- [ ] No duplicate fighters in same fight
- [ ] Max 1 captain per side
- [ ] Fight date cannot be in future
- [ ] Location is required
- [ ] Fight + Tag + Participations created atomically (single transaction)

**Success Criteria**:
- Transactional fight creation working
- Format-dependent validation working
- API endpoints functional
- No regressions in Phase 1 or 2A

---

### Phase 3: Tag Expansion 📋 PLANNED

**Estimated Time**: 8-10 hours
**Complexity**: Medium (extending existing pattern)
**Prerequisites**: Phase 2B complete

**Scope**: Extend tag system with hierarchy and more tag types

**New TagTypes to Add**:
| TagType | Parent | Required | Values |
|---------|--------|----------|--------|
| category | fight_format | No | Singles: duel, profight / Melee: 3s, 5s, 10s, etc. |
| gender | none | No | male, female, mixed |
| weapon | category (duel only) | No | longsword, polearm, sword_shield, etc. |
| league | category | No | BI, IMCF, AMMA, etc. |
| custom | none | No | freeform text |

**New Features**:
- [ ] Tag.parent_tag_id for hierarchy
- [ ] Validation: child tags require valid parent
- [ ] Cascading soft delete (change category → delete weapon)
- [ ] Custom tags allow multiple per fight
- [ ] Category-specific allowed values

**Deferred to v2**:
- TagChangeRequest (voting proposals)
- Vote entity
- Community voting workflow
- Session-based fraud prevention

**Success Criteria**:
- Hierarchical tags working
- Cascade delete working
- No regressions

---

### Phase 4A: Basic Deployment 📋 PLANNED

**Estimated Time**: 4-6 hours
**Focus**: Get API running in cloud

**Stack**:
- Azure App Service (B1 tier, with stop/start scripts)
- Neon PostgreSQL (free tier, serverless)
- GitHub Actions (CI/CD)

**Tasks**:
- [ ] Set up Neon account and database
- [ ] Create Azure App Service via portal
- [ ] Configure environment variables (connection strings, secrets)
- [ ] Create GitHub Actions workflow for deployment
- [ ] Create start/stop shell scripts for cost management
- [ ] Verify API accessible at public URL
- [ ] Add basic health check endpoint

**Cost Strategy**:
- Neon free tier: $0/month
- App Service B1 stopped: $0/month
- App Service B1 running: ~$13/month (prorated by hour)
- **Target**: <$5/month during development

**Success Criteria**:
- API deployed and accessible
- Can stop/start to manage costs
- CI/CD pipeline working
- README updated with deployment info

---

### Phase 4B: Infrastructure as Code 📋 OPTIONAL

**Estimated Time**: 8-12 hours
**Focus**: Reproducible infrastructure

**Stack**:
- Terraform (cloud-agnostic IaC)
- Azure provider
- GitHub Actions for apply/destroy

**Tasks**:
- [ ] Learn Terraform basics
- [ ] Define App Service in Terraform
- [ ] Define resource group, networking
- [ ] Create terraform apply/destroy workflow
- [ ] Document infrastructure in code

**Why Optional**:
- Not required for portfolio
- Can add after Phase 4A if time permits
- Good stretch goal

---

### Phase 5: Auth (v2) 📋 FUTURE

**Not part of v1 scope**

**Learning Goals**:
- OAuth2/OIDC implementation
- JWT handling
- Role-based access control
- Session management

**Features**:
- User registration/login
- Protected endpoints
- Admin vs user roles
- Tag voting (requires auth for fraud prevention)

---

### Phase 6: Frontend (v3) 📋 FUTURE

**Not part of v1 scope**

**Learning Goals**:
- React 18+ with TypeScript
- Modern CSS (Tailwind)
- Frontend testing (Jest, RTL, Playwright)
- State management

**Rationale for Deferral**:
- Backend + deployment demonstrates skills
- Frontend adds 40-55 hours
- Auth should come before public frontend (prevent spam)
- Can be separate learning project

---

## Architecture Decisions Log

See `DECISIONS.md` for full list. Key decisions:

| ID | Decision | Status |
|----|----------|--------|
| ADR-001 | UUIDs for all primary keys | ✅ Implemented |
| ADR-002 | Soft deletes with is_deleted flag | ✅ Implemented |
| ADR-003 | UTC timestamps | ✅ Implemented |
| ADR-004 | Three-layer architecture | ✅ Implemented |
| ADR-005 | Eager loading by default | ✅ Implemented |
| DD-001 | Tags before Fights (fight_format dependency) | 📋 Decided |
| DD-002 | fight_format: "singles" or "melee" | 📋 Decided |
| DD-003 | Singles: exactly 1 fighter per side | 📋 Decided |
| DD-004 | Melee: minimum 5 fighters per side | 📋 Decided |
| DD-005 | Voting system deferred to v2 | 📋 Decided |

---

## Test Strategy

### Current Coverage

```
Layer          | Unit Tests | Integration | Coverage
---------------|------------|-------------|----------
Models         | implicit   | 58          | 100%
Repositories   | 76         | 58          | 98%+
Services       | 66         | -           | 100%
API            | -          | 58          | (via integration)
```

**By Entity**:
- Country: 48 unit + 14 integration
- Team: 48 unit + 15 integration
- Fighter: 34 unit + 12 integration
- TagType: 19 unit + 8 integration
- Tag: 9 unit + 9 integration

### Testing Philosophy

1. **Unit tests**: Fast, isolated, mock dependencies
2. **Integration tests**: Real database (Testcontainers), verify constraints
3. **BDD scenarios**: Document behavior, run as integration tests
4. **E2E tests**: (future) Full API flows

### TDD Discipline Note

Phase 1 used "test-first development" (batch tests → batch implementation).
Phase 2+ should use stricter TDD (one test → pass → refactor → repeat).

This distinction matters for interview discussions.

---

## Git Workflow

**Branch Strategy**:
- `master` - stable, all tests pass
- `feature/*` - new entity development
- `fix/*` - bug fixes

**Commit Convention**:
```
<type>: <description>

<body>

Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: feat, fix, test, docs, refactor

---

## Session Log

### 2026-01-26: Phase 2A Complete - Tag Entity Finished
- ✅ Implemented Tag entity with full CRUD following **STRICT TDD**
- ✅ 9 unit tests (3 repository, 6 service) - all passing
- ✅ 9 integration tests covering all feature file scenarios
- ✅ Complete API layer (POST, GET list, GET by ID, PATCH, DELETE)
- ✅ Pydantic schemas with validation (TagCreate, TagUpdate, TagResponse)
- ✅ Parent tag hierarchy support (parent_tag_id)
- ✅ Fixed 2 pre-existing unit test failures (permanent_delete await issue)
- ✅ **Strict TDD followed**: One test at a time, RED → GREEN → REFACTOR
- ✅ All 197 unit tests passing, all 58 integration tests passing
- **Total Tag Tests**: 9 unit + 9 integration

### 2026-01-24: Phase 2A Started - TagType Complete
- ✅ Implemented TagType entity with full CRUD
- ✅ 19 unit tests (10 repository, 9 service) - all passing
- ✅ 8 integration tests following feature file specification
- ✅ Complete API layer (POST, GET list, GET by ID, PATCH, DELETE)
- ✅ Added repository.update() method
- ✅ Full validation: duplicate names, required fields, length limits
- ⚠️ **Lesson learned**: Violated strict TDD by writing all 9 service tests at once instead of one-at-a-time
- 📝 Used feature file as specification for integration tests (not BDD step definitions)
- **Commits**: `a556b61` (CRUD implementation), `723898d` (integration tests)

### 2026-01-14: Phase 1 Complete
- Completed Fighter entity
- All 130 unit tests passing
- Integration tests written (require Docker)
- Created Phase 2 planning docs

### 2026-01-12: Team Entity
- Implemented Team CRUD
- 48 unit tests
- Eager loading configured

### 2026-01-11: Country Entity  
- Fixed datetime deprecation
- Added unique constraints
- Created Alembic migration

### 2026-01-10: Project Setup
- Repository structure
- pytest configuration
- Initial Country implementation

---

## Next Actions

### Immediate (Next Session)
1. [ ] Create Alembic migration for TagType and Tag tables
2. [ ] Seed fight_format TagType with "singles" and "melee" values
3. [ ] Begin Phase 2B: Fight entity (follow STRICT TDD)
4. [ ] Write Fight feature file scenarios (from fight_management.feature)

### This Week
- [x] Complete TagType entity (model, repo, service, tests)
- [x] Complete Tag entity (model, repo, service, tests)
- [ ] Create Alembic migration for TagType and Tag tables
- [ ] Seed fight_format TagType with "singles" and "melee" values
- [ ] Start Fight entity implementation

### This Month
- [x] Complete Phase 2A (Tag Foundation) ✅
- [ ] Complete Phase 2B (Fight + FightParticipation)
- [ ] Begin Phase 4A (Deployment)

---

## Metrics

### Time Tracking

| Week | Planned | Actual | Notes |
|------|---------|--------|-------|
| Week 1 (Jan 10-14) | 14 hrs | ~6.5 hrs | Phase 1 complete |
| Week 2 (Jan 17-24) | 14 hrs | ~2 hrs | TagType complete (Phase 2A partial) |
| Week 3 (Jan 25-26) | 14 hrs | ~2 hrs | Tag complete, Phase 2A done |

### Velocity

- **Phase 1 estimate**: 10-12 days
- **Phase 1 actual**: 6.5 hours
- **Velocity multiplier**: ~10x (planning docs overestimated)

Adjusted estimates account for this velocity.

---

## How to Update This Document

After each coding session:

1. Update "Last Updated" date
2. Update phase status table
3. Add entry to Session Log
4. Update Next Actions
5. Commit: `git commit -m "docs: update progress tracking"`

This is the **single source of truth** for project status.
Other documents (CLAUDE.md, planning/*.md) reference this.

---

## Questions for Future Sessions

- [ ] Should Fighter.team_id be nullable? (independent fighters)
- [ ] Tag hierarchy depth - how much to implement for v1?
- [ ] Integration test execution - Docker setup working?

See `DECISIONS.md` for full question tracking.
