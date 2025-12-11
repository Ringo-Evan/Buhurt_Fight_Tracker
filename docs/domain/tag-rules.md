# Tag Hierarchy Rules

## Overview
This document defines the hierarchical relationships between tag types and the rules governing how tags can be applied to fights.

## Tag Type Hierarchy
```
Fight
├── Super Category (required, privileged, only one)
│   ├── Singles
│   │   └── Category (optional, privileged, only one)
│   │       ├── Duel
|   |       |    └── Subcategory (optional, privileged, one of each allowed)
|   |       |        |── Rule Set (optional, priviliged)
|   |       |        |    ├── AMMA(rules)
|   |       |        |    ├── Outrance
|   |       |        |    ├── Championship Fights(This might be wrong, double check)
|   |       |        |    ├── Knight Fight
|   |       |        |    └── Other?
|   |       |        |     
|   |       |        ├── League
|   |       |        |    ├── BI
|   |       |        |    ├── IMCF
|   |       |        |    ├── ACL
|   |       |        |    ├── ACW
|   |       |        |    ├── ACS
|   |       |        |    ├── HMB
|   |       |        |    └── Other?
|   |       |        |    
│   │       |        └── Weapon (optional, privileged)
│   │       |             ├── Longsword
│   │       |             ├── Polearm
│   │       |             ├── Sword & Shield
│   │       |             ├── Sword $ Buckler
│   │       |             └── Other
|   |       |
|   |       └── ProFight
|   |            └── Subcategory (optional, privileged, one of each allowed)
|   |                 ├──  Rule Set (optional, priviliged)
|   |                 |     ├── AMMA(rules)
|   |                 |     ├── Outrance
|   |                 |     ├── Championship Fights(This might be wrong, double check)
|   |                 |     ├── Knight Fight
|   |                 |     └── Other?
|   |                 |     
|   |                 |     
|   |                 └── League
|   |                       ├── AMMA
|   |                       ├── PWR
|   |                       ├── BI
|   |                       ├── IMCF
|   |                       ├── ACL
|   |                       ├── ACW
|   |                       ├── ACS
|   |                       ├── HMB
|   |                       ├── Golden Ring
|   |                       └── Other?
│   │
│   └── Melee
|        └── Category (optional, privileged, only one of each)
│              ├── Size (required, privileged)
│                  ├── 3's
|                  |    └── Subcategory (optional, privileged, one of each allowed)
|                  |         ├── Rule Set (optional, priviliged)                           
|                  |         |    ├── IMCF
|                  |         |    └── Other?
|                  |         └── League (optional, priviliged)
|                  |              ├── IMCF                           
|                  |              ├── ACS
|                  |              ├── ACL
|                  |              └── ACW
│                  ├── 5's
|                  |    └── Subcategory (optional, privileged, one of each allowed)
|                  |         ├── Rule Set (optional, priviliged)                   
|                  |         |    ├── HMBIA        
|                  |         |    ├── BI
|                  |         |    ├── IMCF
|                  |         |    └── Other?
|                  |         └── League (optional, priviliged)                           
|                  |              ├── HMB
|                  |              ├── IMCF
|                  |              ├── ACL
|                  |              ├── ACS
|                  |              ├── BI
|                  |              └── ACW
│                  ├── 10's
|                  |    └── Subcategory (optional, privileged, one of each allowed)
|                  |         ├── Rule Set (optional, priviliged)                           
|                  |         |    ├── IMCF
|                  |         |    └── Other?
|                  |         └── League (optional, priviliged)                           
|                  |              ├── IMCF                       
|                  |              ├── ACS
|                  |              ├── ACL
|                  |              └── ACW
│                  ├── 12's
|                  |    └── Subcategory (optional, privileged, one of each allowed)
|                  |         ├── Rule Set (optional, priviliged)                           
|                  |         |    ├── BI
|                  |         |    └── Other?
|                  |         └── League (optional, priviliged)                           
|                  |              ├── BI
|                  |              └── HMB
│                  ├── 16's
|                  |    └── Subcategory (optional, privileged, one of each allowed)
|                  |         ├── Rule Set (optional, priviliged)                           
|                  |         |    ├── IMCF
|                  |         |    └── Other?
|                  |         └── League (optional, priviliged)                         
|                  |              ├── IMCF                         
|                  |              ├── ACS
|                  |              ├── ACL
|                  |              └── ACW
|                  ├── 21's
|                  |    └── Subcategory (optional, privileged, one of each allowed)
|                  |         ├── Rule Set (optional, priviliged)                           
|                  |         |    ├── HMBIA
|                  |         |    └── Other?
|                  |         └── League (optional, priviliged)                           
|                  |              └── HMB
|                  ├── 30's
|                  |    └── Subcategory (optional, privileged, one of each allowed)
|                  |         ├── Rule Set (optional, priviliged)                           
|                  |         |    ├── BI
|                  |         |    └── Other?
|                  |         └── League (optional, priviliged)
|                  |              └── BI
│                  └── Mass
|                  |    └── Subcategory (optional, privileged, one of each allowed)
|                  |         ├── Rule Set (optional, priviliged)                                                     
|                  |         |    ├── BI
|                  |         |    ├── HMB
|                  |         |    ├── IMCF
|                  |         |    └── Other?
|                  |         └── League (optional, priviliged)                           
|                  |              ├── IMCF
|                  |              ├── HMB
|                  |              └── BI
│             
│
├── Gender (optional, privileged)
│   ├── Male
│   ├── Female
│   └── Mixed
│
└── Custom (optional, non-privileged)
    └── [Any freeform text]
```

## Hierarchy Rules

### 1. Parent-Child Relationships

| Child Tag Type | Required Parent | Optional? | Number Allowed |
|----------------|----------------|-----------| -----------|
| Supercategory  | None | ❌ Required at fight creation | 1 |
| Category | Supercategory | Optional | 0 or 1 |
| Subcategory | Category | ✅ Always optional | depends on Category |
| Gender | None | ✅ Optional | 1 |
| Custom | None | ✅ Optional | unlimited |

### 2. Supercategory-Specific Rules

#### Singles Fights
- **Category**: OPTIONAL
  - If present, must be: `Duel` or `Melee`
- **Subcategory**: OPTIONAL
  - **Weapon**: OPTIONAL
    - Can only be added if Category exists and is Duel
  - **League**: Optional
    - Can only be added if Category exists. Different options for duel vs profight
  - **Rule Set**: Optional
    - Can only be added if Category exists. Different options for duel vs profight

#### Team Fights
- **Category**: OPTIONAL
  - Must be one of: `3s`, `5s`, `10s`, `12s`, `16s`, `21s`, `30's`, `Mass`
- **Subcategory**: OPTIONAL
  - **Rule Set**: OPTIONAL
    - Can only be added if Category exists
  - **League**: Optional
    - Can only be added if Category exists.
- **Fighter count**: Must match subcategory (see Team Size Rules below)

### 3. Cascading Change Rules

When a parent tag changes, all child tags are soft-deleted (isDeleted = true):

| Parent Changed | Children Affected | Example |
|----------------|-------------------|---------|
| Supercategory | Category + Subcategory | Singles → Team removes "Duel" and "Longsword" |
| Category | Subcategory only | Duel → Melee removes "Longsword" |
| Subcategory | None | Longsword → has no cascade |

**Important**: Gender and Custom tags are independent and not affected by category/subcategory/weapon changes.

### 4. Orphan Prevention

Tags cannot be added without their required parent:
```
❌ INVALID: Add Weapon "Longsword" when no Category exists
✅ VALID: Add Category "Duel", THEN add Weapon "Longsword"

❌ INVALID: Add Weapon "Longsword" when no Category is Profight
✅ VALID: Change Category to "Duel", THEN add Weapon "Longsword"

❌ INVALID: Add Category "Duel" when no SuperCategory exists
✅ VALID: Fight always has Category at creation

```

### 5. Single Active Child Rule

A fight can only have ONE active tag of each type at a time:
```
❌ INVALID: Fight has both "Duel" AND "Melee" subcategories
✅ VALID: Fight has "Duel" subcategory only

❌ INVALID: Fight has "Longsword" AND "Polearm" weapons
✅ VALID: Fight has "Longsword" weapon only
```

**Exception**: Custom tags can have multiple instances (e.g., "awesome fight", "great technique", etc.)

## Team Size Rules

Team fights MUST have at least the min number of fighters and no more than the max number of fighters per side based on Category:

| Category | Required Fighters Per Side | Action if Insufficient | Action if Excess |
|-------------|---------------------------|------------------------|------------------|
| 3's | 3-5 | Add "Missing Fighter" placeholders | ❌ Reject fight creation |
| 5s | 5-8 | Add "Missing Fighter" placeholders | ❌ Reject fight creation |
| 10s | 10-15 | Add "Missing Fighter" placeholders | ❌ Reject fight creation |
| 12s | 12-20 | Add "Missing Fighter" placeholders | ❌ Reject fight creation |
| 16s | 16-21 | Add "Missing Fighter" placeholders | ❌ Reject fight creation |
| 21s | 21-30 | Add "Missing Fighter" placeholders | ❌ Reject fight creation |
| 30s | 30-50 | Add "Missing Fighter" placeholders | ❌ Reject fight creation |
| Mass| No requiremen | NA | ✅ Accept fight creation |

### Missing Fighter Behavior

When a team has fewer fighters than required:
- Create placeholder `FightParticipation` records with `fighter_id = NULL`
- Set `role = "Missing Fighter"`
- Maintain correct `side` assignment
- Allow these to be filled in later via fight updates

**Example**: 5s fight with only 4 fighters on Side 1
```
Side 1:
- Fighter A (fighter_id = uuid-a, role = fighter)
- Fighter B (fighter_id = uuid-b, role = fighter)
- Fighter C (fighter_id = uuid-c, role = fighter)
- Fighter D (fighter_id = uuid-d, role = fighter)
- Missing Fighter (fighter_id = NULL, role = "Missing Fighter")

Side 2:
- [8 fighters, properly filled]
```

## Tag Change Validation

### Valid Tag Changes

| From | To | Validation |
|------|-----|-----------|
| Singles | Melee | ✅ Always valid, cascades delete Category/Subcategory |
| Melee | Singles | ✅ Always valid, cascades delete Category/Subcategory |
| Duel | Profight | ✅ Valid, cascades delete Subcategory(s) |
| 5s | 12s | ✅ Valid if fighter count is correct for new size |
| Longsword | Polearm | ✅ Always valid (same level) |
| No Weapon | Longsword | ✅ Valid if Category is duel |

### Invalid Tag Changes

| From | To | Reason |
|------|-----|--------|
| Singles | Duel | Cannot add change Supercategory to category |
| Mell - 5s  | Melee - Duel  | "Duel" is not valid for Melee category |
| No Category | Longsword | Missing required parent (Category) |

TODO add some more examples

## Tag Type Validation

### When Adding Tags

**Category tags:**
- Must be added at fight creation
- Cannot be removed (only changed to different category)
- Must be one of: `Singles`, `Melee`

**Subcategory tags:**
- For Singles: Must be `Duel` or `Profight` or `None`
- For Melee:  Must be `3s`, `5s`, `10s`, `12s`, `16s`, `21s`, `30's`, `Mass`
- Cannot add if no Supercategory exists
- Cannot add `Duel` to a `Melee` fight (validate parent compatibility)

**Weapon tags:**
- Must have Category Duel parent
- Must be one of the valid weapon types (see Tag Types document)
- Cannot add if Category is not duel

**Gender tags:**
- Independent of category/subcategory/weapon
- Must be one of: `Male`, `Female`, `Mixed`
- Optional for all fights

**Rule Set tags:**
- Optional for all fights
- Available rule sets depend on Category
- Must have parent category

**League Tags**
- Optional for all fights
- Availble leagues depend on Category
- Must have parent Category

**Custom tags:**
- No validation beyond max length (200 chars)
- Freeform text
- Multiple custom tags allowed per fight
- Auto-accepted (no voting required)

## Examples

### Example 1: Valid Singles Fight Evolution
```
1. Fight created with Category = "Singles"
2. User proposes Subcategory = "Duel" → Voting → Accepted
3. User proposes Weapon = "Longsword" → Voting → Accepted
4. User proposes Gender = "Male" → Voting → Accepted

Final state:
- Category: Singles
- Subcategory: Duel
- Weapon: Longsword
- Gender: Male
```

### Example 2: Category Change Cascade
```
Initial state:
- Category: Singles
- Subcategory: Duel
- Weapon: Longsword

User proposes Category = "Melee" → Voting → Accepted

New state:
- Category: Melee
- Subcategory: [DELETED]
- Weapon: [DELETED]
```

### Example 3: Invalid Tag Addition
```
Current state:
- Supercategory: Singles
- (no subcategory)

User attempts to propose Weapon = "Longsword"
❌ REJECTED: "Cannot add weapon tag without existing Category tag"

User must first add Category, then can add Weapon.
```

### Example 4: Melee Fight Validation
```
User creates Melee fight with Category = "5s"
User adds 4 fighters to Side 1
User adds 5 fighters to Side 2

System automatically:
- Creates "Missing Fighter" placeholder for Side 1 (5th slot)
- Fight is valid and can be saved
```

## Querying Tag Hierarchies

### Get Complete Tag Hierarchy for a Fight
```sql
WITH RECURSIVE tag_tree AS (
  -- Get root tags (no parent)
  SELECT id, fight_id, tag_type_id, value, parent_tag_id, 0 as level
  FROM tags
  WHERE fight_id = :fight_id AND parent_tag_id IS NULL AND isDeleted = FALSE
  
  UNION ALL
  
  -- Get child tags
  SELECT t.id, t.fight_id, t.tag_type_id, t.value, t.parent_tag_id, tt.level + 1
  FROM tags t
  INNER JOIN tag_tree tt ON t.parent_tag_id = tt.id
  WHERE t.isDeleted = FALSE
)
SELECT * FROM tag_tree ORDER BY level, tag_type_id;
```

### Validate Tag Can Be Added
```sql
-- Check if weapon can be added (needs subcategory parent)
SELECT EXISTS(
  SELECT 1 FROM tags
  WHERE fight_id = :fight_id
    AND tag_type_id = (SELECT id FROM tag_types WHERE name = 'subcategory')
    AND isDeleted = FALSE
) AS has_required_parent;
```

## References
- See `tag-types.md` for complete list of valid tag values
- See `business-rules.md` for voting rules on privileged tags
- See ADR-001 for technical implementation of tag hierarchy