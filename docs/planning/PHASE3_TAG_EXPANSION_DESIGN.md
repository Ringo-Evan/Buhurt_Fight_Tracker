# Phase 3: Tag Expansion — Design Document

**Status**: Ready for review
**Decisions**: DD-007, DD-008, DD-009, DD-010
**Scope**: supercategory (rename) + category + gender + custom tags + fight-scoped tag API

---

## What Phase 3 Is

Extend the tag system so fights can be described beyond just singles/melee. Introduce a tag
management API scoped to fights. Fix the existing fight_format bug and harden the data model.

## What Phase 3 Is NOT

- Weapon, League, RuleSet tags (deferred — require category-value-dependent validation)
- Team size enforcement per category (deferred — changes fight creation logic deeply)
- Missing Fighter placeholders (deferred)
- Tag voting / change requests (deferred to v2)

---

## Data Model Changes

### 1. Migration: `tags.fight_id` NOT NULL

```
tags.fight_id: nullable=True  →  nullable=False
```

The column exists and the relationship is already wired. This is a constraint-only migration.
Requires verifying no NULL fight_ids exist in the database before applying.

### 2. Data Migration: Rename fight_format → supercategory

```sql
UPDATE tag_types SET name = 'supercategory' WHERE name = 'fight_format';
```

Code references to `"fight_format"` in `fight_service.py` and tests must be updated to
`"supercategory"`.

### 3. Data Migration: Seed new TagTypes

```sql
INSERT INTO tag_types (id, name) VALUES
  (gen_random_uuid(), 'category'),
  (gen_random_uuid(), 'gender'),
  (gen_random_uuid(), 'custom');
```

### No new tables required.

The Tag model already has everything needed:
- `fight_id` — links tag to its fight
- `tag_type_id` — discriminates supercategory / category / gender / custom
- `parent_tag_id` — hierarchy (category's parent is the supercategory tag instance)
- `value` — the string value ("singles", "duel", "male", etc.)
- `is_deactivated` — soft deactivation for cascade

---

## Layer Changes

### TagRepository — NO CHANGES

All existing methods stay. No new methods needed at this layer beyond what's already there.

### TagService — NO CHANGES TO EXISTING METHODS

Existing methods (`create`, `get_by_id`, `update`, `deactivate`, `delete`) remain as internal
utilities. No new public methods added. TagService is no longer exposed via its own write
endpoints but is available for FightService to call if needed.

### FightService — NEW METHODS + BUG FIX

**Bug fix** (existing method `create_with_participants`):
```python
# Before (broken — no fight_id):
await self.tag_repository.create({
    "tag_type_id": fight_format_tag_type.id,
    "value": fight_format
})

# After (correct):
await self.tag_repository.create({
    "fight_id": fight.id,
    "tag_type_id": supercategory_tag_type.id,
    "value": fight_format
})
```

**New methods**:

```python
async def add_tag(self, fight_id: UUID, tag_type_name: str, value: str,
                  parent_tag_id: UUID | None = None) -> Tag
```
- Validates fight exists and is active
- Validates tag_type_name is a known type
- Validates value is allowed for that tag type
- Enforces one-per-type rule (supercategory, category, gender)
- Enforces parent requirements (category requires supercategory tag on fight)
- Creates tag with fight_id set

```python
async def update_tag(self, fight_id: UUID, tag_id: UUID, new_value: str) -> Tag
```
- Validates tag belongs to this fight
- Validates new_value is allowed for the tag's type
- If tag is supercategory or category: deactivates child tags (cascade)
- Updates value

```python
async def deactivate_tag(self, fight_id: UUID, tag_id: UUID) -> Tag
```
- Validates tag belongs to this fight
- Deactivates the tag
- Cascades deactivation to child tags (by parent_tag_id)
- Returns updated tag

```python
async def delete_tag(self, fight_id: UUID, tag_id: UUID) -> None
```
- Validates tag belongs to this fight
- Hard deletes tag (and cascade-deletes children via DB or service)

### fight_controller (fights.py) — NEW ENDPOINTS

```
POST   /fights/{fight_id}/tags
PATCH  /fights/{fight_id}/tags/{tag_id}
PATCH  /fights/{fight_id}/tags/{tag_id}/deactivate
DELETE /fights/{fight_id}/tags/{tag_id}
```

### tag_controller.py — ALL WRITE ENDPOINTS REMOVED

Remove: `POST /tags`, `PATCH /tags/{id}`, `PATCH /tags/{id}/deactivate`, `DELETE /tags/{id}`,
`GET /tags`, `GET /tags/{id}`

The file may be removed entirely or kept with a comment marking it for deletion. The existing
tag integration tests (`test_tag_delete_integration.py` and any others that POST to `/tags`) must
be deleted.

### TagType controller — UNCHANGED

`/tag_types` endpoints stay exactly as-is. TagTypes are admin reference data.

---

## Validation Rules (for FightService)

### Allowed values per tag type

| tag_type | allowed values |
|----------|---------------|
| supercategory | "singles", "melee" |
| category (parent=singles) | "duel", "profight" |
| category (parent=melee) | "3s", "5s", "10s", "12s", "16s", "21s", "30s", "mass" |
| gender | "male", "female", "mixed" |
| custom | any non-empty string, max 200 chars |

### One-per-type rule

A fight may have at most ONE active (non-deactivated) tag of each type, EXCEPT custom
(unlimited).

### Parent requirement for category

A fight must have an active supercategory tag before a category tag can be added.
Since supercategory is required at fight creation, this is always satisfied.

### Category-supercategory compatibility

The category value must be valid for the fight's active supercategory value:
- supercategory="singles" → category must be "duel" or "profight"
- supercategory="melee" → category must be one of the size values ("3s", "5s", etc.)

### Cascade deactivation

| Tag being deactivated/changed | Children deactivated |
|-------------------------------|---------------------|
| supercategory | all active category tags on this fight |
| category | none (weapon/league/ruleset deferred to Phase 3B) |
| gender | none |
| custom | none |

Cascade is implemented by querying `tags WHERE fight_id = :fight_id AND parent_tag_id = :tag_id
AND is_deactivated = false` and deactivating each result.

---

## FightResponse Changes

The `FightResponse` schema should include the fight's active tags. They are already eager-loaded
via the `tags` relationship on the Fight model (`lazy="selectin"`). The response schema needs a
`tags` field added:

```python
class FightResponse(BaseModel):
    ...
    tags: list[TagResponse] = []
```

Currently `FightResponse` likely omits tags (they were broken/unlinked in Phase 2). This needs
to be added.

---

## BDD Scenarios (Phase 3 Feature File)

```gherkin
Feature: Fight Tag Management
  As an administrator
  I want to manage tags on fights
  So that fights can be accurately categorised

  # --- Supercategory (bug fix + rename) ---

  Scenario: Creating a fight links supercategory tag to the fight
    Given a valid fight is created with supercategory "singles"
    When I retrieve the fight
    Then the fight has an active supercategory tag with value "singles"
    And the tag has the correct fight_id

  # --- Category tags ---

  Scenario: Add a valid category tag to a singles fight
    Given a singles fight exists
    When I add a category tag "duel" to the fight
    Then the fight has an active category tag with value "duel"

  Scenario: Add a valid category tag to a melee fight
    Given a melee fight exists
    When I add a category tag "5s" to the fight
    Then the fight has an active category tag with value "5s"

  Scenario: Cannot add a melee category to a singles fight
    Given a singles fight exists
    When I add a category tag "5s" to the fight
    Then I receive a 422 validation error

  Scenario: Cannot add a singles category to a melee fight
    Given a melee fight exists
    When I add a category tag "duel" to the fight
    Then I receive a 422 validation error

  Scenario: Cannot add two active category tags to the same fight
    Given a singles fight with an active category "duel"
    When I add a second category tag "profight" to the fight
    Then I receive a 422 validation error

  # --- Cascade ---

  Scenario: Changing supercategory deactivates the category tag
    Given a singles fight with an active category tag "duel"
    When I update the supercategory tag to "melee"
    Then the category tag "duel" is deactivated
    And the supercategory tag value is "melee"

  # --- Gender tags ---

  Scenario: Add a gender tag to a fight
    Given a fight exists
    When I add a gender tag "male" to the fight
    Then the fight has an active gender tag with value "male"

  Scenario: Cannot add an invalid gender value
    Given a fight exists
    When I add a gender tag "unknown" to the fight
    Then I receive a 422 validation error

  # --- Custom tags ---

  Scenario: Add a custom tag to a fight
    Given a fight exists
    When I add a custom tag "great technique"
    Then the fight has a custom tag with value "great technique"

  Scenario: Fight can have multiple custom tags
    Given a fight exists
    When I add custom tags "exciting" and "controversial"
    Then the fight has both custom tags

  # --- Deactivate / Delete ---

  Scenario: Deactivate a tag on a fight
    Given a fight with an active category tag "duel"
    When I deactivate the category tag
    Then the category tag is deactivated
    And the fight's active tags do not include the category

  Scenario: Cannot manage tags on a different fight
    Given fight A has tag X
    When I try to deactivate tag X via fight B's endpoint
    Then I receive a 404 error
```

---

## Implementation Order (TDD)

For each BDD scenario, follow strict RED → GREEN:

1. Fix supercategory bug + rename fight_format → these are prep work, not a new scenario
2. `FightResponse` includes tags → write integration test first
3. Add category tag (valid) → repo/service/controller TDD
4. Add category tag (invalid supercategory mismatch) → validation test
5. One-per-type rule → validation test
6. Cascade on supercategory change → service test + integration test
7. Gender tag → follows same pattern as category
8. Custom tag → simpler (no parent, no allowed values restriction)
9. Deactivate tag → should be mostly done by cascade infrastructure
10. Tag belongs to fight guard → cross-fight access test

---

## Files Changed Summary

| File | Change |
|------|--------|
| `app/models/tag.py` | `fight_id` nullable=False |
| `app/services/fight_service.py` | Bug fix + 4 new methods |
| `app/api/v1/fights.py` | 4 new tag endpoints |
| `app/api/v1/tag_controller.py` | Delete entire file (or empty write endpoints) |
| `app/schemas/fight.py` | Add `tags: list[TagResponse]` to FightResponse |
| `alembic/versions/` | 2 new migrations (NOT NULL constraint + data migration) |
| `tests/unit/services/test_fight_service.py` | New test classes for each new method |
| `tests/integration/api/test_fight_tag_integration.py` | New integration test file |
| `tests/integration/api/test_tag_delete_integration.py` | Delete (endpoint removed) |
| `tests/features/fight_tag_management.feature` | New feature file |

---

## Resolved Design Questions

1. **Supercategory is immutable after creation.** ✅ DECIDED
   Once a fight is created as "singles" or "melee" it cannot be changed. The supercategory tag
   value is locked. `PATCH /fights/{id}/tags/{tag_id}` must reject attempts to update a
   supercategory tag with 422.

2. **DELETE rejects if children exist.** ✅ DECIDED
   `DELETE /fights/{id}/tags/{tag_id}` returns 422 if the tag has any active children
   (tags with `parent_tag_id = tag_id` and `is_deactivated = false`). Caller must deactivate
   or delete children first. No cascade-delete logic needed.
