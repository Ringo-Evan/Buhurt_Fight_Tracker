Feature: Tag Management
    As a system administrator
    I want to manage tags that categorize fights
    So that fights can be filtered and searched effectively

    Background:
        Given the following tag types exist:
        | name          | is_privileged | display_order |
        | fight_format  | true          | 1             |
        | category      | true          | 2             |
        | weapon        | true          | 3             |

    Scenario: Create a tag with valid tag type
        When I create a tag with the following details:
        | tag_type_name | value    |
        | fight_format  | singles  |
        Then the tag should exist with value "singles"
        And the tag should reference tag type "fight_format"

    Scenario: Create tag with parent tag (hierarchy)
        Given a tag exists with tag_type "category" and value "melee"
        When I create a tag with the following details:
        | tag_type_name | value | parent_tag_value |
        | weapon        | sword | melee            |
        Then the tag should exist with value "sword"
        And the tag should have parent tag with value "melee"

    Scenario: Prevent tag creation with nonexistent tag type
        When I attempt to create a tag with tag_type "nonexistent" and value "test"
        Then I should receive an error indicating tag type does not exist

    Scenario: Retrieve tag by ID
        Given a tag exists with tag_type "fight_format" and value "singles"
        When I retrieve the tag by ID
        Then I should receive the tag with value "singles"
        And it should reference tag type "fight_format"

    Scenario: List all tags
        Given the following tags exist:
        | tag_type_name | value   |
        | fight_format  | singles |
        | fight_format  | melee   |
        | category      | duel    |
        When I retrieve the list of tags
        Then I should see 3 tags

    Scenario: Update a tag value
        Given a tag exists with tag_type "category" and value "duel"
        When I update the tag value to "profight"
        Then the tag should have value "profight"
        And the tag type should remain "category"

    Scenario: Soft delete a tag
        Given a tag exists with tag_type "weapon" and value "sword"
        When I delete the tag
        Then the tag should not appear in the list
        But the tag should still exist in the database with is_deleted true

    Scenario: Validate tag value is required
        When I attempt to create a tag with empty value
        Then I should receive an error indicating value is required

    Scenario: Validate tag value length
        When I attempt to create a tag with a value longer than 100 characters
        Then I should receive an error indicating value is too long
