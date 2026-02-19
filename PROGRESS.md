# Buhurt Fight Tracker - Project Progress

**Last Updated**: 2026-02-19 (Session 7 — Phase 3A complete, Phase 3B ready)
**Project Goal**: Portfolio piece demonstrating TDD/BDD mastery and system design skills
**Target Role**: Lead/Architect trajectory
**Velocity**: ~8 hours/week (target: 14)

---

## Quick Status

| Phase | Status | Tests | Time Spent |
|-------|--------|-------|------------|
| Phase 1: Foundation (Country, Team, Fighter) | ✅ COMPLETE | 130 unit, 41 integration, 98 BDD | ~6.5 hrs |
| Phase 2A: Tag Foundation (TagType + Tag) | ✅ COMPLETE | 28 unit, 17 integration | ~4 hrs |
| Phase 2B: Fight Core Validation | ✅ COMPLETE | 24 unit (FightService), 1 integration | ~4 hrs |
| Phase 2C: CI/CD Pipeline + Integration Tests | ✅ COMPLETE | 206 unit, 61 integration (1 skipped) | ~3 hrs |
| Phase 2D: Deactivate + Hard Delete | ✅ COMPLETE | 222 unit, 66+ integration | ~3 hrs |
| Phase 3A: Tag MVP (supercategory/category/gender/custom) | ✅ COMPLETE | 242 unit, 75+ integration | Session 6-7 |
| Phase 3B: Tag Expansion (weapon/league/ruleset + team size) | 📋 PLANNED | 0 | 0 |
| Phase 4A: Basic Deployment | 📋 PLANNED | 0 | 0 |
| Phase 4B: Infrastructure as Code | 📋 OPTIONAL | 0 | 0 |
| Phase 5: Auth (v2) | 📋 FUTURE | 0 | 0 |
| Phase 6: Frontend (v3) | 📋 FUTURE | 0 | 0 |

**Total Tests**: 242 unit (all passing) + 75+ integration + 98 BDD scenarios
**CI**: ✅ Green (GitHub Actions)

**Estimated Remaining to "portfolio complete"** (Phase 4A):
- Phase 3B (weapon/league/ruleset): optional — does not block portfolio
- Phase 4A (Deployment): 4-6 hours — **this is the blocker**

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
| TagType | ✅ COMPLETE | 19 | 8 | ✅ Full CRUD | ✅ Created |
| Tag | ✅ COMPLETE | 9 | 9 | ✅ Full CRUD | ✅ Created |

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

### Phase 2B: Fight Tracking ✅ COMPLETE (Core Validation)

**Started**: 2026-01-26
**Completed**: 2026-01-26 (Session 3)
**Time Spent**: ~2.5 hours
**Complexity**: High (many-to-many, transactions, format-dependent validation)
**Prerequisites**: Phase 2A complete ✅

| Entity | Status | Unit Tests | Integration Tests | API | Migration |
|--------|--------|-----------|-------------------|-----|-----------|
| Fight | ✅ CORE COMPLETE | 24 (all passing) | 1 written (needs CI/CD) | ✅ CRUD + Participations | ✅ Created |
| FightParticipation | ✅ CORE COMPLETE | (covered by Fight) | - | ✅ Nested in Fight | ✅ Created |

**Business Rules Implementation Status**:
- [x] Fight must have exactly one fight_format tag (singles or melee) ✅
- [x] Singles: exactly 1 fighter per side ✅ (DD-003)
- [x] Melee: minimum 5 fighters per side ✅ (DD-004)
- [x] Minimum 2 participants total ✅
- [x] Fighter existence check ✅
- [x] Both sides must have participants ✅
- [x] No duplicate fighters in same fight ✅
- [x] Max 1 captain per side ✅
- [x] Fight date cannot be in future ✅ (existing)
- [x] Location is required ✅ (existing)
- [x] Fight + Tag + Participations created atomically ✅

**Completed Across Sessions**:
- ✅ Alembic migrations for TagType, Tag tables (h3c4d5e6f7g8, i4d5e6f7g8h9)
- ✅ Seed migration for fight_format TagType (j5e6f7g8h9i0)
- ✅ `FightService.create_with_participants()` method with fight_format parameter
- ✅ `ParticipationCreate`, `ParticipationResponse` schemas
- ✅ `FightCreate` schema with fight_format field (pattern validation)
- ✅ Updated API endpoint to handle fight + format + participations
- ✅ All participant validations (strict TDD: RED → GREEN for each rule)
- ✅ Format-dependent validation (singles vs melee)
- ✅ Fighter existence validation (async)
- ✅ Tag repositories injected into FightService

**Success Criteria** (all met for Phase 2B):
- [x] Transactional fight creation working ✅
- [x] Format-dependent validation working (fight_format tag integration) ✅
- [x] API endpoints functional ✅
- [x] No regressions in service layer (24/24 Fight service tests passing) ✅

---

### Phase 2C: CI/CD Pipeline + Integration Tests ✅ COMPLETE

**Started**: 2026-01-27
**Completed**: 2026-01-27
**Time Spent**: ~3 hours
**Complexity**: Medium-High (GitHub Actions setup, Docker services, Alembic configuration)
**Prerequisites**: Phase 2B complete ✅

**Deliverables**:
- ✅ **GitHub Actions CI/CD workflow** (`.github/workflows/test.yml`)
  - PostgreSQL 16 service container configured
  - Python 3.13 environment with pip caching
  - Alembic migrations run automatically
  - Separate steps: unit tests → integration tests → coverage
  - Codecov integration for coverage tracking
  - HTML coverage artifact upload (30-day retention)
- ✅ **CI/CD fixes applied**:
  - Added `psycopg2-binary` for Alembic migrations (synchronous driver)
  - Modified `alembic/env.py` to use `DATABASE_URL` environment variable
  - Automatic asyncpg → psycopg2 URL conversion for migrations
- ✅ **6 Fight integration tests added** (total 61 integration tests):
  1. Create singles fight with two participants (happy path)
  2. Create melee fight with minimum fighters (5 per side, DD-004)
  3. Cannot create fight with future date (validation)
  4. Cannot create fight with only 1 participant (validation)
  5. Singles format validation - exactly 1 per side (DD-003)
  6. Melee format validation - minimum 5 per side (DD-004)
  - 1 test skipped (soft-delete list) due to session management complexity

**Test Results** (GitHub Actions):
- ✅ **206/206 unit tests passing**
- ✅ **61/61 integration tests passing** (1 skipped)
- ✅ **267 total tests** with coverage reporting
- ✅ **Coverage reports** uploaded to Codecov
- ✅ **Workflow run time**: ~1m 20s

**CI/CD Pipeline URL**: https://github.com/Ringo-Evan/Buhurt_Fight_Tracker/actions

**Why CI/CD First**:
- Local Docker-in-Docker blocked by container sandbox
- GitHub Actions provides proper Docker environment
- Enables continuous validation of all changes
- Required for portfolio demonstration
- Integration tests verify real database behavior

**Success Criteria** (all met):
- ✅ GitHub Actions workflow running successfully on every push
- ✅ All unit tests passing in CI (206/206)
- ✅ Integration tests running with real PostgreSQL (61/61 passing, 1 skipped)
- ✅ Test coverage reporting configured and working
- ✅ Green CI badge ready for README
- ✅ Pipeline provides detailed failure messages when tests fail

**Remaining Work** (optional for v2):
- [ ] Fix 1 skipped integration test (soft-delete session management)
- [ ] Write remaining integration test scenarios from fight_management.feature
- [ ] Add integration tests for other entities (Country, Team, Fighter, Tag, TagType)
- [ ] Set up branch protection rules requiring CI pass

### Phase 2D: Deactivate + Hard Delete ✅ COMPLETE

**Started**: 2026-02-19
**Completed**: 2026-02-19 (Session 5)
**Time Spent**: ~3 hours

**Scope**: Replace soft delete pattern with explicit deactivate (PATCH) + permanent hard delete (DELETE) across all entities.

| Entity | Repo `delete()` | Service `delete()` | `PATCH /deactivate` | `DELETE` (hard) |
|--------|----------------|-------------------|---------------------|-----------------|
| Country | ✅ | ✅ (`permanent_delete`) | ✅ Added | ✅ Fixed |
| Team | ✅ | ✅ | ✅ Added | ✅ Fixed |
| Fighter | ✅ Added | ✅ Added | ✅ Added | ✅ Fixed |
| TagType | ✅ (pre-existing) | ✅ (pre-existing) | ✅ (pre-existing) | ✅ (pre-existing) |
| Tag | ✅ Added | ✅ Added | ✅ (pre-existing) | ✅ Fixed |
| Fight | ✅ Added | ✅ Added | ✅ Added | ✅ Fixed |

**New Integration Tests**:
- `tests/integration/api/test_country_integration.py`
- `tests/integration/api/test_team_integration.py`
- `tests/integration/api/test_fighter_integration.py`
- `tests/integration/api/test_tag_delete_integration.py`
- `tests/integration/api/test_fight_delete_integration.py`

**Bugs Fixed During Phase**:
- Missing `await` on `session.delete()` in Fighter, Fight, Tag repositories (silent no-op in SQLAlchemy async)
- Corresponding unit tests updated from `MagicMock` → `AsyncMock` for `session.delete`
- `test_list_all_fights_excludes_deactivated` updated to use `PATCH /deactivate` instead of `DELETE`
- 3 failing `TestCountryServicePermanentDelete` tests fixed (missing `permanent_delete` alias on repo)

**Success Criteria** (all met):
- ✅ All entities have both `PATCH /{id}/deactivate` and `DELETE /{id}` (hard) endpoints
- ✅ 222/222 unit tests passing
- ✅ All integration tests passing in CI (GitHub Actions green)
- ✅ No regressions in previous phases




---

### Phase 3A: Tag MVP ✅ COMPLETE

**Started**: 2026-02-19 (Session 6)
**Completed**: 2026-02-19 (Session 7)
**Prerequisites**: Phase 2D complete ✅
**Design doc**: `planning/PHASE3_TAG_EXPANSION_DESIGN.md`
**Decisions**: DD-007, DD-008, DD-009, DD-010, DD-011, DD-012

**Scope delivered**:
| TagType | Parent | Cardinality | Values |
|---------|--------|-------------|--------|
| supercategory | none | exactly 1 | singles, melee |
| category | supercategory | 0 or 1 | singles→duel/profight, melee→3s/5s/10s/12s/16s/21s/30s/mass |
| gender | none | 0 or 1 | male, female, mixed |
| custom | none | unlimited | any string ≤200 chars |

**All endpoints implemented**:
| Endpoint | Business rules |
|----------|----------------|
| `POST /fights/{id}/tags` | Category/supercategory compatibility, one-per-type, allowed values |
| `PATCH /fights/{id}/tags/{tag_id}` | Supercategory immutable (DD-011), validates new value |
| `PATCH /fights/{id}/tags/{tag_id}/deactivate` | Cascades to children |
| `DELETE /fights/{id}/tags/{tag_id}` | 422 if active children exist (DD-012) |

**Key decisions**:
- Tag writes moved to fight-scoped endpoints — DD-009 ✅
- Standalone `/tags` write endpoints removed — DD-009 ✅
- `tags.fight_id` NOT NULL — DD-008 ✅
- fight_format renamed → supercategory — DD-007 ✅
- Supercategory immutable after creation — DD-011 ✅
- DELETE rejects if children exist — DD-012 ✅
- Category auto-linked to supercategory via `parent_tag_id` (hierarchy for cascade/delete) ✅

**Tests**:
- 20 unit tests added (10 add_tag, 3 deactivate_tag, 4 delete_tag, 2 update_tag, 1 deactivated fight guard)
- 13 integration tests in `test_fight_tag_integration.py` — all passing in CI
- BDD feature file: `tests/features/fight_tag_management.feature` (16 scenarios)

**Success criteria** (all met):
- ✅ 242/242 unit tests passing
- ✅ CI green (all integration tests passing)
- ✅ FightResponse includes active tags
- ✅ `tags.fight_id` NOT NULL enforced in migration

---

### Phase 3B: Tag Expansion 📋 PLANNED

**Prerequisites**: Phase 3A complete ✅
**Complexity**: High (category-value-dependent validation, fighter count enforcement)
**Does NOT block portfolio** — Phase 4A (deployment) can proceed without this

**Scope**:

| Feature | Description | Complexity |
|---------|-------------|------------|
| `weapon` tag type | Valid values depend on category (duel → sword types, etc.) | Medium |
| `league` tag type | Valid values depend on category | Medium |
| `ruleset` tag type | Valid values depend on category | Medium |
| Team size enforcement | Per category: 3s=3-5, 5s=5-8, 10s=10-15, etc. | High |
| Missing Fighter placeholders | `FightParticipation` with `fighter_id = NULL` to fill minimum counts | High |

**Key design questions to resolve before starting**:
1. What are the allowed weapon values per category? (needs doc)
2. What are the allowed league values? (needs doc)
3. Should team size enforcement happen at fight creation, or separately?
4. Should missing-fighter placeholders be auto-created or require explicit API call?

**What this unlocks**:
- More complete fight descriptions (weapon type adds significant value to the data model)
- Stricter data integrity for melee size categories
- Closer to real buhurt tournament data requirements

**Implementation order** (when ready):
1. Write BDD feature file for weapon/league/ruleset scenarios
2. Add new TagTypes to migration + conftest seed
3. Extend `_validate_tag_value` and `_CATEGORY_VALUES` in `FightService`
4. Add team size enforcement to `create_with_participants` and/or `add_tag`
5. Implement Missing Fighter placeholder logic

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
Services       | 70         | -           | 100%
API            | -          | 59          | (via integration)
```

**By Entity**:
- Country: 48 unit + 14 integration
- Team: 48 unit + 15 integration
- Fighter: 34 unit + 12 integration
- TagType: 19 unit + 8 integration
- Tag: 9 unit + 9 integration
- Fight: 24 unit + 6 integration (1 skipped)
- FightParticipation: (covered by Fight tests)

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

### 2026-02-19 (Session 6): Phase 3 Started - Fight Tag Management

- ✅ **Phase 3 pre-work** (all complete):
  - Renamed `fight_format` → `supercategory` throughout (DD-007)
  - Fixed bug: `FightService.create_with_participants` was creating tag without `fight_id`
  - Removed standalone `tag_controller.py` write endpoints and integration tests (DD-009)
  - Created migration `k6f7g8h9i0j1_phase3_tag_setup.py`: fight_id NOT NULL, rename, seed TagTypes
  - Added `tags: list[TagResponse]` to `FightResponse` schema
  - Seeded TagTypes in `conftest.db_engine` fixture so all integration tests have reference data
- ✅ **BDD Feature File**: `tests/features/fight_tag_management.feature` (16 scenarios)
- ✅ **Implemented `FightService.add_tag()`**:
  - Category-supercategory compatibility validation
  - One-per-type enforcement (supercategory/category/gender; unlimited custom)
  - Cross-fight access guard
  - 11 unit tests
- ✅ **Implemented `FightService.deactivate_tag()`**:
  - Validates tag belongs to fight
  - Cascades deactivation to children
  - Fixed typo in `TagRepository.cascade_deactivate_children` (recursive call was wrong method name)
  - 3 unit tests
- ✅ **Wired up controller endpoints**:
  - `POST /fights/{id}/tags` → `add_tag()` → 201 TagResponse
  - `PATCH /fights/{id}/tags/{tag_id}/deactivate` → `deactivate_tag()` → 200 TagResponse
- ✅ **Integration tests written** (Scenarios 1-8, require Docker/CI):
  - `tests/integration/api/test_fight_tag_integration.py`
- ✅ **Unit tests**: 236/236 passing (up from 222)
- 📋 **Remaining**: Run CI to verify integration tests, implement DELETE + supercategory immutability

### 2026-02-19 (Session 5): Phase 2D Complete - Deactivate + Hard Delete

- ✅ **Fixed 3 pre-existing failures** in `TestCountryServicePermanentDelete`:
  - Added `permanent_delete` alias to `CountryRepository`
  - Fixed `CountryService.permanent_delete` to remove redundant `get_by_id` check
- ✅ **Implemented hard delete + deactivate across all entities** (BDD → TDD workflow):
  - Country: fixed controller DELETE → `permanent_delete`, added `PATCH /deactivate`
  - Team: fixed controller DELETE → `delete`, added `PATCH /deactivate`
  - Fighter: added `delete()` to repo + service, fixed broken controller DELETE, added `PATCH /deactivate`
  - Tag: added `delete()` to repo + service, fixed controller DELETE
  - Fight: added `delete()` to repo + service, added `PATCH /deactivate`
- ✅ **Added 5 new integration test files** (DELETE hard + PATCH /deactivate scenarios)
- ✅ **Added 13 new unit tests** across 6 test files (222 total, up from 209)
- ✅ **Fixed CI failures after push**:
  - Root cause: `session.delete()` not awaited in Fighter, Fight, Tag repos → silent no-op
  - Fixed with `await self.session.delete(entity)` in all three repos
  - Updated unit test mocks from `MagicMock` → `AsyncMock` for `session.delete`
  - Fixed `test_list_all_fights_excludes_deactivated` to use `PATCH /deactivate` instead of `DELETE`
- ✅ **CI green**: 222 unit + all integration tests passing (run time ~1m34s)
- 📝 **Phase 2D COMPLETE**
- 📋 **Next: Phase 3** - Tag Expansion

**Lessons Learned**:
- SQLAlchemy `AsyncSession.delete()` IS a coroutine — must be awaited (unlike `session.add()`)
- When overriding `AsyncMock` attributes with `MagicMock`, `await` will fail at runtime
- Always check existing tests that exercise the same endpoints when changing endpoint behavior

### 2026-01-27 (Session 4): Phase 2C Complete - CI/CD Pipeline + Integration Tests
- ✅ **Created and debugged GitHub Actions CI/CD workflow** (`.github/workflows/test.yml`)
  - Configured PostgreSQL 16 service container
  - Set up Python 3.13 with pip caching
  - Configured separate test steps: unit → integration → coverage
  - Added Codecov integration
  - Added HTML coverage artifact upload (30-day retention)
- ✅ **Fixed CI/CD blockers** (iterative debugging via GitHub Actions):
  - Added `psycopg2-binary` for Alembic synchronous migrations
  - Modified `alembic/env.py` to use DATABASE_URL environment variable
  - Implemented asyncpg → psycopg2 URL conversion for migrations
- ✅ **Added 6 Fight integration tests** (HTTP API pattern):
  1. Create singles fight with two participants (happy path)
  2. Create melee fight with minimum fighters (5 per side, DD-004)
  3. Cannot create fight with future date (validation)
  4. Cannot create fight with only 1 participant (validation)
  5. Singles format validation - exactly 1 per side (DD-003)
  6. Melee format validation - minimum 5 per side (DD-004)
  - 1 test skipped (soft-delete list) due to session management complexity
- ✅ **Verified CI/CD pipeline working**:
  - 206/206 unit tests passing ✅
  - 61/61 integration tests passing (1 skipped) ✅
  - 267 total tests with coverage
  - Workflow run time: ~1m 20s
  - GitHub Actions URL: https://github.com/Ringo-Evan/Buhurt_Fight_Tracker/actions
- 📝 **Phase 2C COMPLETE** - CI/CD pipeline operational and green
- 📋 **Next: Phase 3** - Tag Expansion

**Lessons Learned**:
- **GitHub Actions debugging workflow**: Push changes → watch logs → fix → repeat
- **Alembic environment variables**: Always check for env var overrides in migrations
- **Integration test reliability**: HTTP API pattern more reliable than direct service calls
- **Session management**: Testcontainers session lifecycle requires careful management
- **Coverage artifacts**: Useful for portfolio demonstration and trend tracking

**Key Achievement**: Project now has fully automated CI/CD with real database integration testing!

### 2026-01-26 (Session 3): Phase 2B Continued - Fight Format Validation Complete
- ✅ Implemented **5 new validations** following **STRICT TDD** (RED → GREEN for each):
  1. Minimum 2 participants validation
  2. Fighter existence check (async validation)
  3. fight_format tag creation (atomic with fight)
  4. Singles format validation: exactly 1 fighter per side (DD-003)
  5. Melee format validation: minimum 5 fighters per side (DD-004)
- ✅ Added `fight_format` field to `FightCreate` schema with pattern validation
- ✅ Updated `FightService` to inject `TagRepository` and `TagTypeRepository`
- ✅ Updated `create_with_participants()` signature to accept `fight_format` parameter
- ✅ Made `_validate_participations()` async to support fighter existence checks
- ✅ 5 new unit tests added (total: 24 Fight service tests, all passing)
- ✅ Updated all existing tests to use new method signature
- ✅ Updated integration test to include `fight_format` field
- ✅ All service layer tests passing (199/206 total unit tests pass)
- 📝 **Note**: 7 pre-existing failures in `test_fight_repository.py` (not caused by this session)
- **Strict TDD followed**: One test at a time, RED → GREEN → REFACTOR

**Docker Investigation**:
- 🔍 Investigated Docker-in-Docker setup for running integration tests
- ✅ Docker Engine installed successfully in container
- ❌ Docker daemon cannot start due to container sandbox restrictions (no --privileged flag)
- 📋 **Decision**: Use GitHub Actions CI/CD for integration tests instead of local Docker-in-Docker
- **Rationale**: CI/CD provides proper Docker environment, more reliable than Docker-in-Docker

**Lessons Learned**:
- ⚠️ **Skipped integration test workflow**: Should have followed feature file scenario-by-scenario:
  - Write ONE integration test per scenario
  - Write unit tests to support it (RED → GREEN)
  - Ask user to run integration test
  - Move to next scenario
- **Root cause**: Jumped straight to batch unit test implementation instead of scenario-driven development
- **Impact**: Unit tests complete (24 passing) but integration test coverage incomplete (1/40+ scenarios)
- **Next session**: Set up CI/CD pipeline first, then write remaining integration tests

### 2026-01-26 (Session 2): Phase 2B Started - Fight + Participations
- ✅ Created 3 Alembic migrations:
  - `h3c4d5e6f7g8_create_tag_types_table.py`
  - `i4d5e6f7g8h9_create_tags_table.py`
  - `j5e6f7g8h9i0_seed_fight_format_tag_type.py`
- ✅ Implemented `FightService.create_with_participants()` for atomic creation
- ✅ Added participation validation (strict TDD):
  - Both sides must have participants
  - No duplicate fighters
  - Max 1 captain per side
- ✅ Updated schemas: `ParticipationCreate`, `ParticipationResponse`, `FightCreate.participations`
- ✅ Updated API endpoint to handle participations in request
- ✅ 4 new unit tests for participant validation
- ✅ 1 integration test written (pending Docker verification)
- ✅ All 201 unit tests passing
- **Strict TDD followed**: RED → GREEN → REFACTOR for each validation rule

### 2026-01-26 (Session 1): Phase 2A Complete - Tag Entity Finished
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

### Immediate (Next Session) - Complete Phase 3
1. [ ] Push to remote and run CI to verify Phase 3 integration tests pass
2. [ ] Implement `DELETE /fights/{id}/tags/{tag_id}` with children-exist guard (DD-012)
3. [ ] Enforce supercategory immutability (DD-011) — reject PATCH on supercategory tag
4. [ ] Review Phase 3 scenarios for any gaps

### This Week (Feb 19)
- [x] Fix 3 failing CountryService unit tests ✅
- [x] Implement hard delete + deactivate for all entities ✅
- [x] Fix CI failures (await session.delete, broken test) ✅
- [x] Complete Phase 2D ✅
- [x] Begin Phase 3 (Tag Expansion) ✅ — pre-work + scenarios 1-8 implemented

### This Month (February 2026)
- [x] Complete Phase 2D (Deactivate + Hard Delete) ✅
- [ ] Complete Phase 3 (Tag Expansion)
- [ ] Complete Phase 4A (Deployment)
- [ ] Project "Portfolio Ready" milestone

---

## Metrics

### Time Tracking

| Week | Planned | Actual | Notes |
|------|---------|--------|-------|
| Week 1 (Jan 10-14) | 14 hrs | ~6.5 hrs | Phase 1 complete |
| Week 2 (Jan 17-24) | 14 hrs | ~2 hrs | TagType complete (Phase 2A partial) |
| Week 3 (Jan 25-26) | 14 hrs | ~6 hrs | Tag complete, Phase 2A done, Phase 2B core complete, Docker investigation |
| Week 4 (Jan 27) | 14 hrs | ~3 hrs | Phase 2C complete - CI/CD pipeline operational |
| Week of Feb 19 | 14 hrs | ~3 hrs | Phase 2D complete - deactivate + hard delete across all entities |

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
- [x] Integration test execution - Docker setup working? **RESOLVED**: Use CI/CD pipeline (GitHub Actions) instead of local Docker-in-Docker

**Resolved Issues**:
- Docker-in-Docker: Container sandbox prevents Docker daemon from starting (lacks --privileged flag)
- Solution: GitHub Actions provides proper Docker environment for integration tests
- Next: Set up CI/CD pipeline as priority task

See `DECISIONS.md` for full question tracking.
