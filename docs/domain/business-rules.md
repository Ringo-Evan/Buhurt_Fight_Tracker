# Business Rules

## Tag System
1. Privileged tags require voting (category, subcategory, weapon, etc.)
2. Custom tags are auto-accepted
3. Only one pending change request per tag type per fight
4. Vote threshold: 10 (configurable per request)
5. Ties favor rejection (maintain current state)

## Tag Hierarchy Cascading
- Changing category → nullifies subcategory and weapon
- Changing subcategory → nullifies weapon
- Implemented via soft delete (isDeleted=true)

## Fight Creation
- Must specify category tag at creation (business rule, enforced in code)
- Created by admin/system users only (v1)

## Voting
- Anonymous 
- One vote per session per request
- Voting closes when threshold reached
- Admin can override at any time


## Searching and Filtering
- Advanced searching to specify one or more matching types(fight name, privileged tags custom tags, fighters, country, team, etc)
- Filtering based on predefined fields(country, privileged tags, fighter, team)
- General search matching any text
- Sort order can be specified by fight date, fight creation timestamp, fighter/team 1 name, fighter/team 2 name, country,  category tag ONLY(not sub category or custom tags)

## Country
### Validation
- Country names are required (non-empty, non-null)
- ISO country codes must be exactly 3 uppercase letters (ISO 3166-1 alpha-3 format)
- Unique constraint on name and code applies only to active (not deleted) countries
- Duplicate active country codes are rejected
- Countries must exist

### Relationships
- Countries can have many teams

### Archiving/Deletion
- Deleting a country will archive it (soft delete) and preserve relationships
- Archived countries do not appear in list operations for regular users
- Admin users can view and retrieve archived countries
- Regular users receive 404 when attempting to retrieve archived countries by ID
- Countries can be replaced by admins updating the new country with all the old country's relationships
- Archived countries can be permanently deleted by admins only if they have no relationships

## Teams
- Name cannot exceed 100 chars(arbitrary limit)
- Team name must be unique
- Teams must have one and only one country
- Fighters of a team do NOT need to match the country
- Only admin can create now
- Later teams can be created with new videos(or via vote?)
- If a team is archived maintain all relationships
- Add replace method to update all reltations from archived to active team
- Fighters can be part of many teams
- Teams have lineups which are sets of fighters
- Only admins can remove fighters from teams
- only admin be able to add fighters to teams(revisit these in phase two with auth implemented)


