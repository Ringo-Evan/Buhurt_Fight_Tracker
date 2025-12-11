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
- Filtering based on predefined fields(country, privileged tags, country, fighter, team)
- General search matching any text
- Display ranking can be specified by fight date, fight creation timestamp, fighter/team 1 name, fighter/team 2 name, country,  category tag ONLY(not sub category or custom tags)

