# Phase 3B: Tag Expansion — Implementation Plan

**Status**: Ready for implementation
**Decisions**: DD-014 through DD-021
**Prerequisites**: Phase 3A complete (fight_format, category, gender, custom tags working)
**Scope**: weapon, league, ruleset tags + team size min/max enforcement

---

## What Phase 3B Is

Extend the tag system with category-dependent child tags (weapon, league, ruleset) and enforce
team size rules (min/max fighters per side) based on category.

## What Phase 3B Is NOT

- Missing Fighter placeholders (deferred per DD-021)
- Tag voting system (deferred to v2)
- Authentication (deferred to Phase 5)

---

## Data Model Changes

### 1. Migration: Seed new TagTypes

```sql
INSERT INTO tag_types (id, name, created_at) VALUES
  (gen_random_uuid(), 'weapon', NOW()),
  (gen_random_uuid(), 'league', NOW()),
  (gen_random_uuid(), 'ruleset', NOW());
```

### No schema changes required

The Tag model already supports everything needed:
- `fight_id` — links tag to fight
- `tag_type_id` — discriminates weapon / league / ruleset
- `parent_tag_id` — links to category tag (for cascade)
- `value` — the string value ("Longsword", "IMCF", etc.)
- `is_deactivated` — soft deactivation for cascade

---

## Validation Constants

Add to `app/services/fight_service.py` (or new `app/core/constants.py`):

```python
# Team size rules: (min, max) per category
# max=None means unlimited
TEAM_SIZE_RULES: dict[str, tuple[int, int | None]] = {
    "3s": (3, 5),
    "5s": (5, 8),
    "10s": (10, 15),
    "12s": (12, 20),
    "16s": (16, 21),
    "21s": (21, 30),
    "30s": (30, 50),
    "mass": (5, None),
}

# Weapon values (only valid for category="duel")
VALID_WEAPONS: list[str] = [
    "Longsword",
    "Polearm",
    "Sword & Shield",
    "Sword & Buckler",
    "Other",
]

# League values per category
VALID_LEAGUES: dict[str, list[str]] = {
    "duel": ["BI", "IMCF", "ACL", "ACW", "ACS", "HMB"],
    "profight": ["AMMA", "PWR", "BI", "IMCF", "ACL", "ACW", "ACS", "HMB", "Golden Ring"],
    "3s": ["IMCF", "ACS", "ACL", "ACW"],
    "5s": ["HMB", "IMCF", "ACL", "ACS", "BI", "ACW"],
    "10s": ["IMCF", "ACS", "ACL", "ACW"],
    "12s": ["BI", "HMB"],
    "16s": ["IMCF", "ACS", "ACL", "ACW"],
    "21s": ["HMB"],
    "30s": ["BI"],
    "mass": ["IMCF", "HMB", "BI"],
}

# Ruleset values per category
VALID_RULESETS: dict[str, list[str]] = {
    "duel": ["AMMA", "Outrance", "Championship Fights", "Knight Fight", "Other"],
    "profight": ["AMMA", "Outrance", "Championship Fights", "Knight Fight", "Other"],
    "3s": ["IMCF", "Other"],
    "5s": ["HMBIA", "BI", "IMCF", "Other"],
    "10s": ["IMCF", "Other"],
    "12s": ["BI", "Other"],
    "16s": ["IMCF", "Other"],
    "21s": ["HMBIA", "Other"],
    "30s": ["BI", "Other"],
    "mass": ["BI", "HMB", "IMCF", "Other"],
}
```

---

## Layer Changes

### FightService — MODIFIED METHODS

#### 1. `add_tag()` — Extended validation

Add validation for weapon, league, ruleset:

```python
async def add_tag(self, fight_id: UUID, tag_type_name: str, value: str, ...) -> Tag:
    # ... existing validation ...

    # NEW: Get category tag for context
    category_tag = self._get_active_tag_by_type(fight, "category")

    if tag_type_name == "weapon":
        self._validate_weapon_tag(category_tag, value)
    elif tag_type_name == "league":
        self._validate_league_tag(category_tag, value)
    elif tag_type_name == "ruleset":
        self._validate_ruleset_tag(category_tag, value)

    # ... create tag with parent_tag_id = category_tag.id ...
```

#### 2. `update_tag()` — Extended cascade + team size check

When category changes:
1. Validate new category is compatible with fight_format (existing)
2. **NEW**: Validate participation count satisfies new category's team size rules
3. **NEW**: Cascade-delete ALL child tags (weapon, league, ruleset)

```python
async def update_tag(self, fight_id: UUID, tag_id: UUID, new_value: str) -> Tag:
    tag = await self._get_tag_or_404(fight_id, tag_id)
    tag_type = await self._get_tag_type(tag.tag_type_id)

    if tag_type.name == "category":
        # Validate team size for new category
        self._validate_team_size_for_category(fight, new_value)
        # Cascade delete ALL children (weapon, league, ruleset)
        await self._cascade_delete_children(tag)

    # ... update tag value ...
```

#### 3. `create_with_participants()` — Team size validation

When fight is created with category, enforce team size:

```python
async def create_with_participants(self, fight_data, fight_format, participations,
                                    category: str | None = None, ...) -> Fight:
    # ... existing validation ...

    # NEW: If category provided, validate team size
    if category and fight_format == "melee":
        self._validate_team_size_for_category_at_creation(participations, category)

    # ... create fight, tags, participations ...
```

### FightService — NEW PRIVATE METHODS

```python
def _validate_weapon_tag(self, category_tag: Tag | None, value: str) -> None:
    """Validate weapon tag can be added. Only valid for category='duel'."""
    if not category_tag:
        raise MissingParentTagError("Weapon requires a category tag")
    if category_tag.value != "duel":
        raise InvalidTagError("Weapon tags only valid for 'duel' category")
    if value not in VALID_WEAPONS:
        valid = ", ".join(VALID_WEAPONS)
        raise InvalidTagValueError(f"Invalid weapon '{value}'. Valid options: {valid}")

def _validate_league_tag(self, category_tag: Tag | None, value: str) -> None:
    """Validate league tag value for the current category."""
    if not category_tag:
        raise MissingParentTagError("League requires a category tag")
    category = category_tag.value
    if category not in VALID_LEAGUES:
        raise InvalidTagError(f"League tags not valid for category '{category}'")
    if value not in VALID_LEAGUES[category]:
        valid = ", ".join(VALID_LEAGUES[category])
        raise InvalidTagValueError(
            f"Invalid league '{value}' for category '{category}'. Valid options: {valid}"
        )

def _validate_ruleset_tag(self, category_tag: Tag | None, value: str) -> None:
    """Validate ruleset tag value for the current category."""
    if not category_tag:
        raise MissingParentTagError("Ruleset requires a category tag")
    category = category_tag.value
    if category not in VALID_RULESETS:
        raise InvalidTagError(f"Ruleset tags not valid for category '{category}'")
    if value not in VALID_RULESETS[category]:
        valid = ", ".join(VALID_RULESETS[category])
        raise InvalidTagValueError(
            f"Invalid ruleset '{value}' for category '{category}'. Valid options: {valid}"
        )

def _validate_team_size_for_category(self, fight: Fight, category: str) -> None:
    """Validate fight's current participations satisfy category team size rules."""
    if category not in TEAM_SIZE_RULES:
        return  # No team size rule for this category (singles categories)

    min_size, max_size = TEAM_SIZE_RULES[category]

    for side in [1, 2]:
        count = len([p for p in fight.participations
                     if p.side == side and not p.is_deleted])
        if count < min_size:
            raise InvalidParticipantCountError(
                f"Cannot use category '{category}': requires {min_size}-{max_size} "
                f"fighters per side, but side {side} has {count}"
            )
        if max_size and count > max_size:
            raise InvalidParticipantCountError(
                f"Cannot use category '{category}': requires {min_size}-{max_size} "
                f"fighters per side, but side {side} has {count}"
            )

def _validate_team_size_for_category_at_creation(
    self, participations: list[ParticipationCreate], category: str
) -> None:
    """Validate participations at fight creation time."""
    if category not in TEAM_SIZE_RULES:
        return

    min_size, max_size = TEAM_SIZE_RULES[category]

    for side in [1, 2]:
        count = len([p for p in participations if p.side == side])
        if count < min_size:
            raise InvalidParticipantCountError(
                f"Category '{category}' requires {min_size}-{max_size} "
                f"fighters per side, but side {side} has {count}"
            )
        if max_size and count > max_size:
            raise InvalidParticipantCountError(
                f"Category '{category}' requires {min_size}-{max_size} "
                f"fighters per side, but side {side} has {count}"
            )

async def _cascade_delete_children(self, parent_tag: Tag) -> None:
    """Cascade-delete all child tags (weapon, league, ruleset)."""
    children = await self.tag_repository.get_children(parent_tag.id)
    for child in children:
        if not child.is_deactivated:
            await self.tag_repository.deactivate(child.id)
```

### TagRepository — NEW METHOD (if not exists)

```python
async def get_children(self, parent_tag_id: UUID) -> list[Tag]:
    """Get all tags with given parent_tag_id."""
    stmt = select(Tag).where(
        Tag.parent_tag_id == parent_tag_id,
        Tag.is_deactivated == False
    )
    result = await self.session.execute(stmt)
    return list(result.scalars().all())
```

### API Endpoints — NO CHANGES

Phase 3A endpoints handle all tag operations:
- `POST /fights/{fight_id}/tags` — add weapon/league/ruleset
- `PATCH /fights/{fight_id}/tags/{tag_id}` — update (with new cascade logic)
- `PATCH /fights/{fight_id}/tags/{tag_id}/deactivate` — deactivate
- `DELETE /fights/{fight_id}/tags/{tag_id}` — delete

### Schemas — NEW OPTIONAL FIELD

`FightCreate` may accept optional `category` for convenience:

```python
class FightCreate(BaseModel):
    date: date
    location: str
    fight_format: str  # "singles" or "melee" (existing, renamed from fight_format)
    category: str | None = None  # NEW: optional, e.g. "5s", "duel"
    participations: list[ParticipationCreate]
```

---

## BDD Scenarios

Create `tests/features/fight_tag_phase3b.feature`:

```gherkin
Feature: Phase 3B Tag Expansion
  As an administrator
  I want to add weapon, league, and ruleset tags to fights
  So that fights can be fully categorised

  # --- Weapon Tags (Duel only) ---

  Scenario: Add weapon tag to a duel fight
    Given a singles fight with category "duel"
    When I add a weapon tag "Longsword"
    Then the fight has an active weapon tag with value "Longsword"

  Scenario: Cannot add weapon tag without category
    Given a singles fight without a category tag
    When I add a weapon tag "Longsword"
    Then I receive a 422 error "Weapon requires a category tag"

  Scenario: Cannot add weapon tag to profight
    Given a singles fight with category "profight"
    When I add a weapon tag "Longsword"
    Then I receive a 422 error "Weapon tags only valid for 'duel' category"

  Scenario: Cannot add weapon tag to melee
    Given a melee fight with category "5s"
    When I add a weapon tag "Longsword"
    Then I receive a 422 error "Weapon tags only valid for 'duel' category"

  Scenario: Invalid weapon value rejected
    Given a singles fight with category "duel"
    When I add a weapon tag "Trebuchet"
    Then I receive a 422 error containing "Valid options: Longsword, Polearm"

  # --- League Tags ---

  Scenario: Add league tag to a duel fight
    Given a singles fight with category "duel"
    When I add a league tag "IMCF"
    Then the fight has an active league tag with value "IMCF"

  Scenario: Add league tag to a melee fight
    Given a melee fight with category "5s"
    When I add a league tag "HMB"
    Then the fight has an active league tag with value "HMB"

  Scenario: Cannot add league without category
    Given a melee fight without a category tag
    When I add a league tag "HMB"
    Then I receive a 422 error "League requires a category tag"

  Scenario: Invalid league for category rejected
    Given a melee fight with category "3s"
    When I add a league tag "HMB"
    Then I receive a 422 error "Invalid league 'HMB' for category '3s'. Valid options: IMCF, ACS, ACL, ACW"

  # --- Ruleset Tags ---

  Scenario: Add ruleset tag to a fight
    Given a singles fight with category "duel"
    When I add a ruleset tag "AMMA"
    Then the fight has an active ruleset tag with value "AMMA"

  Scenario: Invalid ruleset for category rejected
    Given a melee fight with category "3s"
    When I add a ruleset tag "HMBIA"
    Then I receive a 422 error "Invalid ruleset 'HMBIA' for category '3s'. Valid options: IMCF, Other"

  # --- Category Change Cascade (DD-014) ---

  Scenario: Changing category deletes all child tags
    Given a duel fight with weapon "Longsword" and league "BI"
    When I update the category tag to "profight"
    Then the weapon tag is deleted
    And the league tag is deleted
    And the category tag value is "profight"

  # --- Team Size Enforcement (DD-019) ---

  Scenario: Create 5s fight with valid team size
    Given 6 fighters per side are prepared
    When I create a melee fight with category "5s"
    Then the fight is created successfully

  Scenario: Cannot create 5s fight with too few fighters
    Given 4 fighters per side are prepared
    When I create a melee fight with category "5s"
    Then I receive a 422 error "requires 5-8 fighters per side, but side 1 has 4"

  Scenario: Cannot create 5s fight with too many fighters
    Given 10 fighters per side are prepared
    When I create a melee fight with category "5s"
    Then I receive a 422 error "requires 5-8 fighters per side, but side 1 has 10"

  Scenario: Cannot change category if team size invalid (DD-015)
    Given a melee fight with category "5s" and 6 fighters per side
    When I update the category tag to "10s"
    Then I receive a 422 error "requires 10-15 fighters per side, but side 1 has 6"

  # --- Fallback for no category (DD-016) ---

  Scenario: Melee without category uses minimum 5 rule
    Given 4 fighters per side are prepared
    When I create a melee fight without category
    Then I receive a 422 error "Melee fights require at least 5 fighters per side"

  Scenario: Melee without category accepts 5+ fighters
    Given 7 fighters per side are prepared
    When I create a melee fight without category
    Then the fight is created successfully

  # --- Error messages include valid options (DD-020) ---

  Scenario: League error shows valid options
    Given a melee fight with category "21s"
    When I add a league tag "IMCF"
    Then I receive a 422 error "Invalid league 'IMCF' for category '21s'. Valid options: HMB"
```

---

## Implementation Order (TDD)

Follow strict RED → GREEN for each item:

### Step 1: Setup (non-TDD prep)
- [ ] Create migration to seed weapon, league, ruleset TagTypes
- [ ] Add validation constants to `fight_service.py` or `constants.py`
- [ ] Update conftest.py to seed new TagTypes for tests

### Step 2: Weapon Tag Validation
- [ ] Integration test: add weapon to duel fight (happy path)
- [ ] Unit test: `_validate_weapon_tag` rejects missing category
- [ ] Unit test: `_validate_weapon_tag` rejects non-duel category
- [ ] Unit test: `_validate_weapon_tag` rejects invalid value
- [ ] Unit test: `_validate_weapon_tag` accepts valid value
- [ ] Implement `_validate_weapon_tag`
- [ ] Wire into `add_tag()`

### Step 3: League Tag Validation
- [ ] Integration test: add league to duel fight
- [ ] Integration test: add league to 5s fight
- [ ] Unit test: `_validate_league_tag` rejects missing category
- [ ] Unit test: `_validate_league_tag` rejects invalid value for category
- [ ] Unit test: `_validate_league_tag` accepts valid value
- [ ] Implement `_validate_league_tag`
- [ ] Wire into `add_tag()`

### Step 4: Ruleset Tag Validation
- [ ] Integration test: add ruleset to duel fight
- [ ] Unit test: `_validate_ruleset_tag` (same pattern as league)
- [ ] Implement `_validate_ruleset_tag`
- [ ] Wire into `add_tag()`

### Step 5: Category Change Cascade (DD-014)
- [ ] Integration test: change category deletes weapon and league
- [ ] Unit test: `_cascade_delete_children` deactivates all children
- [ ] Implement `TagRepository.get_children()` if needed
- [ ] Implement `_cascade_delete_children()`
- [ ] Wire into `update_tag()` for category type

### Step 6: Team Size Enforcement at Creation (DD-019)
- [ ] Integration test: create 5s with valid count succeeds
- [ ] Integration test: create 5s with too few rejects
- [ ] Integration test: create 5s with too many rejects
- [ ] Unit test: `_validate_team_size_for_category_at_creation` min
- [ ] Unit test: `_validate_team_size_for_category_at_creation` max
- [ ] Implement `_validate_team_size_for_category_at_creation`
- [ ] Wire into `create_with_participants()`

### Step 7: Team Size Enforcement on Category Change (DD-015)
- [ ] Integration test: change 5s to 10s rejects if count invalid
- [ ] Unit test: `_validate_team_size_for_category` rejects under min
- [ ] Unit test: `_validate_team_size_for_category` rejects over max
- [ ] Implement `_validate_team_size_for_category`
- [ ] Wire into `update_tag()` for category type

### Step 8: Fallback for No Category (DD-016)
- [ ] Integration test: melee without category uses DD-004 rule
- [ ] Verify existing DD-004 logic still works (regression test)

### Step 9: Error Message Quality (DD-020)
- [ ] Verify all error messages include valid options
- [ ] Add any missing "Valid options:" text

### Step 10: Full Regression
- [ ] Run all unit tests (should be ~260+)
- [ ] Run all integration tests via CI
- [ ] Verify no regressions in Phase 3A functionality

---

## Files Changed Summary

| File | Change |
|------|--------|
| `alembic/versions/` | 1 new migration (seed TagTypes) |
| `app/services/fight_service.py` | Validation constants + 5 new methods + modify `add_tag`, `update_tag`, `create_with_participants` |
| `app/repositories/tag_repository.py` | Add `get_children()` method |
| `app/exceptions.py` | Add `MissingParentTagError`, `InvalidTagValueError` if not exist |
| `app/schemas/fight.py` | Optional: add `category` field to `FightCreate` |
| `tests/conftest.py` | Seed weapon, league, ruleset TagTypes |
| `tests/unit/services/test_fight_service.py` | ~15-20 new unit tests |
| `tests/integration/api/test_fight_tag_phase3b_integration.py` | New file, ~15 integration tests |
| `tests/features/fight_tag_phase3b.feature` | New feature file |

---

## Estimated Scope

| Item | Count |
|------|-------|
| New unit tests | ~20 |
| New integration tests | ~15 |
| New service methods | 5-6 private methods |
| Modified service methods | 3 (`add_tag`, `update_tag`, `create_with_participants`) |
| New repository methods | 1 (`get_children`) |
| Migrations | 1 (seed TagTypes) |

---

## Success Criteria

- [ ] All new BDD scenarios pass as integration tests
- [ ] Weapon tags only addable to duel fights
- [ ] League/ruleset tags validate against category-specific allowed values
- [ ] Category change cascade-deletes weapon/league/ruleset
- [ ] Team size min/max enforced at creation and category change
- [ ] Melee without category falls back to DD-004 (min 5)
- [ ] Error messages include valid options
- [ ] All 242+ existing unit tests still pass
- [ ] All 75+ existing integration tests still pass
- [ ] CI green

---

## Open Questions (None)

All design questions resolved in DD-014 through DD-021.
