# Repository Structure Recommendations

**Purpose**: Clean up documentation sprawl, establish clear organization
**Date**: 2026-01-18

---

## Current State (Problem)

The `planning/` folder has grown organically with overlapping documents:

```
planning/
├── README.md                              # Navigation (useful but duplicates info)
├── AUTONOMOUS_EXECUTION_PROGRESS.md       # Progress tracking (overlaps PROGRESS.md)
├── COMPREHENSIVE_REVIEW_2026-01-11.md     # Historical review
├── IMPLEMENTATION_PLAN_PHASE1.md          # Confusing name (covers Phase 2/3)
├── IMPLEMENTATION_PLAN_PHASE2.md          # Good, keep
├── NEXT_SESSION_2026-01-11.md             # Historical, completed
├── NEXT_SESSION_2026-01-12.md             # Historical, completed
├── NEXT_SESSION_2026-01-13.md             # Historical, completed  
├── NEXT_SESSION_2026-01-14.md             # Historical, completed
├── NEXT_SESSION_2026-01-12_PHASE2.md      # Active session guide
└── PLANNING_UPDATE_2026-01-12.md          # Meta-doc about docs
```

**Problems**:
1. Multiple places tracking status
2. Historical session docs clutter active workspace
3. Naming inconsistency (Phase1 doc covers Phase2/3 content)
4. Navigation README duplicates CLAUDE.md content

---

## Recommended Structure

### Root Level

```
/
├── README.md                    # Project overview (public-facing)
├── CLAUDE.md                    # AI assistant guide (keep as-is, excellent)
├── PROGRESS.md                  # Single source of truth for status (NEW)
├── DECISIONS.md                 # Consolidated decisions/questions (NEW)
├── pytest.ini
├── requirements.txt
├── alembic.ini
├── app/                         # Application code
├── tests/                       # All tests
├── docs/                        # Domain documentation
├── planning/                    # Implementation planning (simplified)
└── alembic/                     # Migrations
```

### docs/ Folder (Domain Knowledge)

```
docs/
├── data-model.md                # ER diagram
├── business-rules.md            # Business logic documentation
├── tag-rules.md                 # Tag hierarchy (design, even if not fully implemented)
├── tag-types.md                 # Reference data
├── endpoints.md                 # API endpoint planning
└── adr/                         # Architecture Decision Records
    ├── 000-tracking-decisions.md
    ├── 001-use-uuids-for-primary-keys.md
    └── template.md
```

**Note**: Keep `open-questions.md` content merged into root `DECISIONS.md`

### planning/ Folder (Simplified)

```
planning/
├── README.md                    # Brief navigation (simplified)
├── PHASE2_FIGHT_IMPLEMENTATION.md    # Renamed from IMPLEMENTATION_PLAN_PHASE2.md
├── PHASE3_TAGS_IMPLEMENTATION.md     # Create when starting Phase 3
└── archive/                     # Historical documents
    ├── IMPLEMENTATION_PLAN_PHASE1.md      # Rename to clarify
    ├── AUTONOMOUS_EXECUTION_PROGRESS.md   # Superseded by PROGRESS.md
    ├── COMPREHENSIVE_REVIEW_2026-01-11.md
    ├── NEXT_SESSION_2026-01-11.md
    ├── NEXT_SESSION_2026-01-12.md
    ├── NEXT_SESSION_2026-01-13.md
    ├── NEXT_SESSION_2026-01-14.md
    ├── NEXT_SESSION_2026-01-12_PHASE2.md
    └── PLANNING_UPDATE_2026-01-12.md
```

---

## Migration Steps

### Step 1: Add New Root Files

```bash
# Copy from wherever you store the generated files
cp PROGRESS.md /repo/PROGRESS.md
cp DECISIONS.md /repo/DECISIONS.md
git add PROGRESS.md DECISIONS.md
git commit -m "docs: add consolidated progress and decisions tracking"
```

### Step 2: Create Archive Folder

```bash
mkdir -p planning/archive
```

### Step 3: Move Historical Docs

```bash
# Move completed session guides
mv planning/NEXT_SESSION_2026-01-11.md planning/archive/
mv planning/NEXT_SESSION_2026-01-12.md planning/archive/
mv planning/NEXT_SESSION_2026-01-13.md planning/archive/
mv planning/NEXT_SESSION_2026-01-14.md planning/archive/
mv planning/NEXT_SESSION_2026-01-12_PHASE2.md planning/archive/

# Move superseded docs
mv planning/AUTONOMOUS_EXECUTION_PROGRESS.md planning/archive/
mv planning/PLANNING_UPDATE_2026-01-12.md planning/archive/
mv planning/COMPREHENSIVE_REVIEW_2026-01-11.md planning/archive/

# Move and rename confusing doc
mv planning/IMPLEMENTATION_PLAN_PHASE1.md planning/archive/ORIGINAL_DESIGN_FIGHT_AND_TAGS.md
```

### Step 4: Rename Active Docs

```bash
# Clear naming for active implementation guide
mv planning/IMPLEMENTATION_PLAN_PHASE2.md planning/PHASE2_FIGHT_IMPLEMENTATION.md
```

### Step 5: Update Planning README

Replace `planning/README.md` with simplified version:

```markdown
# Planning Documents

## Active Implementation Guides

- **[PHASE2_FIGHT_IMPLEMENTATION.md](./PHASE2_FIGHT_IMPLEMENTATION.md)** - Fight entity TDD guide

## Project Status

See root [`PROGRESS.md`](../PROGRESS.md) for current status.
See root [`DECISIONS.md`](../DECISIONS.md) for architectural decisions.

## Archive

Historical planning documents in `archive/` folder.
These are kept for reference but are no longer actively maintained.
```

### Step 6: Update CLAUDE.md References

In CLAUDE.md, update the "Quick Links" section to reference new structure:

```markdown
## 🔗 Quick Links

**Status & Decisions**:
- [PROGRESS.md](PROGRESS.md) - Single source of truth for project status
- [DECISIONS.md](DECISIONS.md) - Architectural decisions and open questions

**Implementation Guides**:
- [Phase 2: Fight Entity](planning/PHASE2_FIGHT_IMPLEMENTATION.md)

**Domain Documentation**:
- [Data Model](docs/data-model.md)
- [Business Rules](docs/business-rules.md)
- [ADRs](docs/adr/)
```

### Step 7: Commit Changes

```bash
git add -A
git commit -m "docs: reorganize planning folder, consolidate status tracking

- Add PROGRESS.md as single source of truth
- Add DECISIONS.md consolidating open questions and ADRs
- Archive historical session documents
- Simplify planning folder structure
- Update CLAUDE.md references

This cleanup reduces documentation sprawl and makes it clearer
where to find/update project information."
```

---

## What Goes Where (Reference)

| Information Type | Location | Updated When |
|-----------------|----------|--------------|
| Project status, test counts, phase progress | `PROGRESS.md` | After each session |
| Architectural decisions, rationale | `DECISIONS.md` | When decisions made |
| Open questions needing discussion | `DECISIONS.md` | As questions arise |
| AI assistant guidance | `CLAUDE.md` | When patterns change |
| Domain business rules | `docs/business-rules.md` | When rules clarified |
| Implementation steps for current phase | `planning/PHASE*_IMPLEMENTATION.md` | Created per phase |
| Historical documents | `planning/archive/` | Never (reference only) |

---

## Files for This Claude Project

To maintain alignment between this planning Claude instance and Claude Code, add these to your Claude Project files:

**Essential** (add now):
1. `PROGRESS.md` - Status tracking
2. `DECISIONS.md` - Decision reference
3. `CLAUDE.md` - AI guidance (already conceptually there via project instructions)

**Useful** (already uploaded):
- `data-model.md` - Domain model
- `business-rules.md` - Business logic
- `tag-rules.md` - Tag system design

**Not Needed in Project Files**:
- Implementation guides (PHASE*_IMPLEMENTATION.md) - Claude Code reads from repo
- Historical docs - Not relevant for new sessions
- Test files - Claude Code accesses directly

---

## Benefits of This Structure

### For You
- One place to update status (PROGRESS.md)
- One place for decisions (DECISIONS.md)
- Less mental overhead navigating docs

### For Claude Code
- Clear guidance in CLAUDE.md (unchanged)
- Implementation guides in predictable location
- Less confusion from conflicting status info

### For This Claude Instance
- Project files stay current with PROGRESS.md and DECISIONS.md
- Can reference decisions without re-reading everything
- Clear separation of "what's decided" vs "what's open"

### For Portfolio/Interviews
- Clean repo structure demonstrates organization
- DECISIONS.md shows system thinking
- Archive shows you didn't just delete history

---

## Optional: Further Cleanup

If you want to go further (not required):

### Consolidate ADRs
Move content from `DECISIONS.md` into proper ADR files:

```
docs/adr/
├── 001-uuid-primary-keys.md
├── 002-soft-delete-pattern.md
├── 003-utc-timestamps.md
├── 004-three-layer-architecture.md
├── 005-eager-loading.md
├── 006-simplified-tags-v1.md
└── template.md
```

### Add Diagrams
Create `docs/diagrams/` with:
- Architecture diagram (layers)
- Entity relationship diagram (rendered from data-model.md)
- Test strategy diagram

### README Enhancement
Expand root README.md for portfolio presentation:
- Project overview
- Tech stack badges
- Quick start instructions
- Architecture overview
- Link to documentation
- Test coverage badge

---

## Questions?

If this structure doesn't work for your workflow, we can adjust.
The key principles are:
1. Single source of truth for status
2. Clear separation of active vs archived
3. Predictable locations for common operations
