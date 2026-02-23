# ADR-001: Domain Model Design Decisions



## Status
Accepted

## Context
Building a buhurt fight tracking system with community-driven tagging. Need to make foundational decisions about data architecture that will be difficult to change later.

Key requirements:
- Support community voting on fight tags
- Track historical changes to tags
- Allow soft deletes to preserve referential integrity
- Support hierarchical tag relationships (category → subcategory)
- Enable fight participation by fighters across different sides and roles

## Decision

### 1. Use UUIDs for All Primary Keys
**Instead of:** Auto-incrementing integers

**Rationale:**
- Enables distributed system growth (merge databases from different sources)
- No information leakage (can't guess IDs or count records)
- Easier to work with external APIs
- Standard in modern systems

**Trade-offs:**
- Slightly larger storage (16 bytes vs 4-8 bytes)
- Less human-readable
- Can't sort by creation order without timestamp

### 2. Implement Soft Deletes with `isDeleted` Flag
**Instead of:** Hard deletes (DELETE FROM table)

**Rationale:**
- Preserve referential integrity (fighter deleted but fight record remains valid)
- Enable audit trails and historical queries
- Support "undo" functionality
- Maintain data for analytics even after user-facing deletion

**Implementation:**
- Add `isDeleted BOOLEAN DEFAULT FALSE` to all entities
- Filter `WHERE isDeleted = FALSE` in default queries
- Use partial indexes for performance: `CREATE INDEX idx_active_fighters ON fighters (id) WHERE isDeleted = FALSE`

**Trade-offs:**
- Database grows larger over time
- Must remember to filter deleted records in queries
- Potential unique constraint conflicts (revisit if needed)

### 3. Tags Created Only on Vote Acceptance
**Instead of:** Creating tag immediately and marking "pending"

**Rationale:**
- Simpler data model (no "pending tags")
- Clearer state management (tag either exists or doesn't)
- Easier to reason about tag history
- Proposed changes stored in `TagChangeRequest.proposed_value` as string

**Implementation:**
- `TagChangeRequest` has `proposed_value: string` (e.g., "Longsword", "Team")
- When votes reach threshold, create `Tag` record with that value
- `TagChangeRequest.current_tag_id` links to tag being replaced (nullable for new tags)

### 4. Store Proposed Tag Values as Strings
**Instead of:** Foreign key to pre-existing tag or enum

**Rationale:**
- Flexibility: users can propose any value (validated later)
- Simplicity: no need to pre-create all possible tag values
- Works for custom tags (freeform text)
- Validation happens at proposal creation, not storage

**Trade-offs:**
- Possible typos in proposals (mitigated by UI autocomplete)
- No referential integrity for proposed values
- Must validate proposed value matches tag type rules

### 5. Default Voting Threshold: 10
**Instead of:** Variable thresholds per tag type

**Rationale:**
- Simple to implement and understand
- Can be made configurable later without data migration

**Future consideration:** Make threshold configurable per tag type or per fight category

### 6. One Pending Request Per (Fight, Tag Type)
**Instead of:** Multiple concurrent requests per tag type

**Rationale:**
- Prevents confusion (which proposal wins?)
- Simpler voting logic (no need to compare proposals)
- Clear user experience (see current proposal, vote or cancel it)
- Can be relaxed later if needed

**Implementation:**
- Unique constraint: `UNIQUE (fight_id, tag_type_id) WHERE status = 'pending'`
- User must cancel existing request before proposing new one
- Admin can override and create new request (cancels old automatically)

### 7. Anonymous Voting via Session ID (Phase 1)
**Instead of:** Requiring authentication

**Rationale:**
- Lower barrier to entry (no signup required)
- Faster MVP development (no user management)
- Can add authentication in Phase 2 without breaking existing votes

**Implementation:**
- `Vote.session_id` tracks browser sessions
- Frontend generates/stores session ID in localStorage
- One vote per session per request
- Basic fraud prevention

**Trade-offs:**
- Vulnerable to sophisticated vote manipulation
- Can't tie votes to user profiles
- Session IDs can be cleared/reset by users

### 8. Tag Hierarchy via Parent Tag ID
**Instead of:** Separate junction tables for hierarchy

**Rationale:**
- Simpler model: `Tag.parent_tag_id` links to parent tag
- Cascading deletes: changing parent soft-deletes children automatically
- Query flexibility: can traverse hierarchy with recursive CTEs
- Matches actual business logic (weapon depends on subcategory)

**Implementation:**
```sql
-- Example: Singles → Duel → Longsword
category_tag (parent_tag_id = NULL)
  ↓
subcategory_tag (parent_tag_id = category_tag.id)
  ↓
weapon_tag (parent_tag_id = subcategory_tag.id)
```

**Hierarchy rules:**
- Category has no parent
- Subcategory must have category parent
- Weapon must have subcategory parent
- Changing parent cascades soft-delete to children

### 9. Fighter Must Have Team (NOT NULL)
**Instead of:** Nullable team_id

**Rationale:**
- Simplifies fight creation logic (no independent fighters)
- Can create "Independent" or "Unaffiliated" team for solo fighters
- Easier to change to nullable later than to make required later

**Trade-offs:**
- Requires creating placeholder teams
- Extra database records for independent fighters

### 10. Fight Participation Tracks Side and Role
**Instead of:** Simple many-to-many join

**Rationale:**
- Need to know which side fighter was on (winner determination)
- Support multiple roles (fighter, coach, alternate)
- Preserve data even if fighter deleted (fighter_id nullable on delete)

**Schema:**
```sql
FightParticipation:
  - fight_id (FK, not null)
  - fighter_id (FK, nullable) -- NULL if fighter deleted
  - side (1 or 2)
  - role (fighter, coach, alternate)
```

## Consequences

### Positive
- ✅ Flexible data model that can grow
- ✅ Preserves historical data for analytics
- ✅ Simple voting logic that's easy to reason about
- ✅ Low barrier to entry (no auth required initially)
- ✅ Clear separation of concerns (tags vs proposals)

### Negative
- ⚠️ Database grows larger over time (soft deletes)
- ⚠️ Vote fraud possible with session IDs (mitigated in Phase 2)
- ⚠️ Must remember to filter `isDeleted = FALSE` in queries
- ⚠️ UUID URLs are ugly (can add slug field later)

### Risks
- **Unique constraint conflicts with soft deletes** (e.g., fighter name)
  - Mitigation: Can switch to audit table pattern if needed
- **Session ID fraud**
  - Mitigation: Add authentication in Phase 2
- **Database size growth**
  - Mitigation: Archive old soft-deleted records (future)

## Alternatives Considered

### Hard Deletes
**Rejected because:** Breaks referential integrity, loses audit trail

### Pending Tags in Tag Table
**Rejected because:** Messy state management, harder to query "accepted tags"

### Sequential Integer IDs
**Rejected because:** Developer Preference

## Future Decisions to Revisit

1. **Soft delete strategy per table** - Some tables might need hard deletes for unique constraints
2. **Vote fraud prevention** - Add IP tracking, rate limiting, CAPTCHA
3. **Threshold configurability** - Make threshold per tag type or category
4. **Tag value validation** - Pre-seed valid values vs freeform
5. **Fighter independence** - Allow NULL team_id if use case emerges

## References
- [Soft Delete Pattern](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [UUID Best Practices](https://www.postgresql.org/docs/current/datatype-uuid.html)
- ADR template: https://github.com/joelparkerhenderson/architecture-decision-record

---

**Date:** 2024-12-04
**Author:** Ring0
**Reviewers:** Claude (AI Assistant)