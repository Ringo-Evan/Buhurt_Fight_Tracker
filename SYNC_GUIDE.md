# Claude Instance Synchronization Guide

**Purpose**: Keep this Claude.ai planning instance aligned with Claude Code implementation sessions
**Last Updated**: 2026-01-18

---

## The Two-Claude Workflow

User is using two Claude contexts:

| Context | Purpose | Strengths |
|---------|---------|-----------|
| **Claude.ai** | Planning, brainstorming, decisions | Persistent project files, conversation history |
| **Claude Code** | Implementation, code review | Direct repo access, file editing, tests |

**Goal**: Keep them aligned so neither has stale information.

---

## What Lives Where

### Claude.ai (Project Files)

Add these to the Claude Project:

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `PROGRESS.md` | Status tracking | After each coding session |
| `DECISIONS.md` | Architectural decisions | When decisions made |
| `data-model.md` | Domain model | Rarely (stable) |
| `business-rules.md` | Business logic | When rules clarified |
| `CLAUDE.md` | AI guidance | When patterns evolve |

**Don't add**: Implementation guides, test files, code - Claude Code reads these from repo.

### Git Repository (Claude Code Access)

| Location | Purpose |
|----------|---------|
| `CLAUDE.md` | Primary guide for Claude Code |
| `planning/PHASE*_IMPLEMENTATION.md` | Step-by-step implementation |
| `app/`, `tests/` | Actual code |

---

## Sync Protocol

### After Each Coding Session (Claude Code → Claude.ai)

1. **Update PROGRESS.md** in repo
2. **Copy updated PROGRESS.md** to Claude.ai project's files
3. If decisions were made, update DECISIONS.md and copy

**Quick Copy Method**:
```bash
# In repo
cat PROGRESS.md  # Copy output
```
Then paste into Claude.ai to update project file.

### Before Each Coding Session (Claud.ai → Claude Code)

1. Review any planning discussions from claude.ai
2. If new decisions made here, add to DECISIONS.md in repo
3. Claude Code will read updated files when starting

### When Starting New Phase

1. **Here**: Discuss scope, make decisions, update DECISIONS.md
2. **Copy**: Updated DECISIONS.md to repo
3. **Create**: New `planning/PHASE*_IMPLEMENTATION.md` in repo
4. **Claude Code**: Reference new implementation guide

---

## What to Discuss Where

### Use claude.ai For:
- "Should we implement X or defer it?"
- "What's the portfolio impact of this decision?"
- "How should we structure Phase 3?"
- "Review my documentation, does it make sense?"
- Architecture and design discussions
- Scope negotiations
- Career/learning goal alignment

### Use Claude Code For:
- "Write the test for this scenario"
- "Review this implementation"
- "Why is this test failing?"
- "Create the migration"
- Actual code writing
- Debugging
- Running tests

---

## Keeping Context Fresh

### claude.ai
- Has access to conversation history (past chats tool)
- Has project files for reference
- Memory updates based on our conversations

### Claude Code
- Reads `CLAUDE.md` at start of each session
- Accesses repo files directly
- No memory between sessions (relies on docs)

**Key Point**: CLAUDE.md is Claude Code's "memory". Keep it updated.

---

## Example Workflow

### Planning a New Feature (Here)

**You**: "I'm thinking about implementing search. Worth it for portfolio?"

**Claude.aid**: Reviews PROGRESS.md, DECISIONS.md, considers portfolio goals. Recommends: "Defer to v2, document the design."

**You**: Update DECISIONS.md with the decision.

### Implementing a Feature (Claude Code)

**You**: "Let's implement Fight entity"

**Claude Code**: Reads CLAUDE.md, reads PHASE2_IMPLEMENTATION.md, follows TDD steps.

**End of Session**: Update PROGRESS.md with what was completed.

### Sync Point

**You**: Copy updated PROGRESS.md to Claude.ai project's files.

**Next Planning Session**: I have current status, can make informed recommendations.

---

## Minimal Sync (If Short on Time)

If you can't do full sync, at minimum:

1. **Update test count** in PROGRESS.md after coding
2. **Note major decisions** in DECISIONS.md when made

Everything else can be reconstructed from git history if needed.

---

## Troubleshooting

### "Claude Code seems to have forgotten something"
- Check if CLAUDE.md is updated with that information
- Add to CLAUDE.md if it's a persistent pattern/decision

### "This Claude instance has stale status"
- Upload current PROGRESS.md to project files
- Or paste the content in a message

### "Conflicting information between docs"
- PROGRESS.md is source of truth for status
- DECISIONS.md is source of truth for decisions
- Other docs should reference these, not duplicate

---

## File Templates

### Quick Status Update (copy to PROGRESS.md)

```markdown
### [DATE]: [Brief Description]
- Completed: [what]
- Tests: [count] → [new count]
- Next: [what's next]
```

### Quick Decision (copy to DECISIONS.md)

```markdown
### [ID]: [Decision Title] ✅ DECIDED

**Decision**: [One sentence]

**Rationale**: [Why]

**Trade-offs**: [What we gave up]
```

---

## Summary

1. **PROGRESS.md** = status (update after coding)
2. **DECISIONS.md** = decisions (update when decided)
3. **CLAUDE.md** = Claude Code's guide (update when patterns change)
4. claude.ai has project files + memory
5. Claude Code reads from repo each session
6. Keep them in sync with quick copy/paste after sessions
