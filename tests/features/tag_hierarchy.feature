Feature: Tag Hierarchy Cascading
  As the system
  I want to maintain tag hierarchy integrity
  So that child tags are automatically removed when parent tags change

  Background:
    Given the following tag types exist with hierarchy:
      | name        | is_privileged | parent_tag_type | sort_order |
      | category    | true          | null            | 1          |
      | subcategory | true          | category        | 2          |
      | weapon      | true          | subcategory     | 3          |
    And a fight exists with id "fight-1"

  # Category Change Cascades to All Children
  Scenario: Changing category nullifies subcategory and weapon
    Given the fight "fight-1" has the following tags:
      | tag_id | tag_type    | value      | parent_tag_id |
      | tag-1  | category    | Singles    | null          |
      | tag-2  | subcategory | Duel       | tag-1         |
      | tag-3  | weapon      | Longsword  | tag-2         |
    When the category tag for fight "fight-1" is changed from "Singles" to "Team"
    Then the tag "tag-1" should have isDeleted equal to true
    And the tag "tag-2" should have isDeleted equal to true
    And the tag "tag-3" should have isDeleted equal to true
    And a new tag should exist with tag_type "category" and value "Team"
    And the new category tag should have parent_tag_id equal to null

  # Subcategory Change Cascades to Weapon Only
  Scenario: Changing subcategory nullifies weapon but keeps category
    Given the fight "fight-1" has the following tags:
      | tag_id | tag_type    | value      | parent_tag_id |
      | tag-1  | category    | Singles    | null          |
      | tag-2  | subcategory | Duel       | tag-1         |
      | tag-3  | weapon      | Longsword  | tag-2         |
    When the subcategory tag for fight "fight-1" is changed from "Duel" to "Outrance"
    Then the tag "tag-1" should have isDeleted equal to false
    And the tag "tag-2" should have isDeleted equal to true
    And the tag "tag-3" should have isDeleted equal to true
    And a new tag should exist with tag_type "subcategory" and value "Outrance"
    And the new subcategory tag should have parent_tag_id equal to "tag-1"

  # Weapon Change Has No Cascade
  Scenario: Changing weapon does not affect parent tags
    Given the fight "fight-1" has the following tags:
      | tag_id | tag_type    | value      | parent_tag_id |
      | tag-1  | category    | Singles    | null          |
      | tag-2  | subcategory | Duel       | tag-1         |
      | tag-3  | weapon      | Longsword  | tag-2         |
    When the weapon tag for fight "fight-1" is changed from "Longsword" to "Polearm"
    Then the tag "tag-1" should have isDeleted equal to false
    And the tag "tag-2" should have isDeleted equal to false
    And the tag "tag-3" should have isDeleted equal to true
    And a new tag should exist with tag_type "weapon" and value "Polearm"
    And the new weapon tag should have parent_tag_id equal to "tag-2"

  # Adding Child Tag Links to Parent
  Scenario: Adding subcategory links to existing category
    Given the fight "fight-1" has the following tags:
      | tag_id | tag_type    | value   | parent_tag_id |
      | tag-1  | category    | Singles | null          |
    When a subcategory tag "Duel" is added to fight "fight-1"
    Then a new tag should exist with tag_type "subcategory" and value "Duel"
    And the new subcategory tag should have parent_tag_id equal to "tag-1"

   # Adding Child of a Different Parent
  Scenario: Adding subcategory links to existing category
    Given the fight "fight-1" has the following tags:
      | tag_id | tag_type    | value   | parent_tag_id |
      | tag-1  | category    | Team | null          |
    When a subcategory tag "Duel" is added to fight "fight-1"
    Then no new tag should exist with tag_type "subcategory" and value "Duel"
    And the request should be rejected with error  "child tag must match parent tag"

  # Orphan Prevention: Cannot Add Child Without Parent
  Scenario: Cannot add subcategory without category
    Given the fight "fight-1" has no tags
    When a user attempts to add a subcategory tag "Duel" to fight "fight-1"
    Then the request should be rejected with error "Cannot add subcategory without existing category tag"

  Scenario: Cannot add weapon without subcategory
    Given the fight "fight-1" has the following tags:
      | tag_id | tag_type | value   | parent_tag_id |
      | tag-1  | category | Singles | null          |
    When a user attempts to add a weapon tag "Longsword" to fight "fight-1"
    Then the request should be rejected with error "Cannot add weapon without existing subcategory tag"

  # Multiple Children of Same Type Not Allowed
  Scenario: Cannot have multiple active subcategories under one category
    Given the fight "fight-1" has the following tags:
      | tag_id | tag_type    | value   | parent_tag_id |
      | tag-1  | category    | Singles | null          |
      | tag-2  | subcategory | Duel    | tag-1         |
    When a user attempts to add a subcategory tag "Profight" to fight "fight-1"
    Then the request should be rejected with error "Fight already has an active subcategory tag"

  # Soft Delete Preserves History
  Scenario: Cascaded deletes preserve tag history
    Given the fight "fight-1" has the following tags:
      | tag_id | tag_type    | value      | parent_tag_id |
      | tag-1  | category    | Singles    | null          |
      | tag-2  | subcategory | Duel       | tag-1         |
      | tag-3  | weapon      | Longsword  | tag-2         |
    When the category tag for fight "fight-1" is changed from "Singles" to "Team"
    Then the database should contain 4 tag records for fight "fight-1"
    And tags with tag_ids "tag-1,tag-2,tag-3" should have isDeleted equal to true
    And the created_at timestamps for tags "tag-1,tag-2,tag-3" should be preserved
