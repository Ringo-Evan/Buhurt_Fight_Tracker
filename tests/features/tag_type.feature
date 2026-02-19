Feature: TagType CRUD Operations
    As a system administrator
    I want to manage tag type reference data
    So that I can categorize fights with appropriate tags

    Background:
        Given the following tag types exist:
        | name          | is_privileged | is_parent | has_children | display_order |
        | fight_format  | true          | false     | false        | 1             |
        | category      | true          | true      | false        | 2             |
        | weapon        | true          | false     | false        | 3             |

    Scenario: Create a new tag type
        When I create a tag type with the following details:
        | name     | is_privileged | is_parent | has_children | display_order |
        | league   | true          | false     | false        | 4             |
        Then the tag type "league" should exist
        And the tag type "league" should have is_privileged equal to true
        And the tag type "league" should have display_order equal to 4

    Scenario: Retrieve all tag types ordered by display_order
        When I retrieve the list of tag types
        Then I should see tag types in this order:
        | name          | is_privileged | display_order |
        | fight_format  | true          | 1             |
        | category      | true          | 2             |
        | weapon        | true          | 3             |

    Scenario: Retrieve a specific tag type by ID
        Given the tag type "category" exists
        When I retrieve the tag type "category" by ID
        Then I should receive the tag type with name "category"
        And it should have is_privileged equal to true

    Scenario: Update an existing tag type
        Given the tag type "weapon" exists
        When I update the tag type "weapon" with the following:
        | display_order |
        | 10            |
        Then the tag type "weapon" should have display_order equal to 10

    Scenario: Soft delete a tag type
        Given the tag type "weapon" exists
        When I delete the tag type "weapon"
        Then the tag type "weapon" should not appear in the list
        But the tag type "weapon" should still exist in the database with is_deactivated true

    Scenario: Prevent duplicate tag type names
        Given the tag type "category" exists
        When I attempt to create a tag type with name "category"
        Then I should receive an error indicating the name must be unique

    Scenario: Validate tag type name is required
        When I attempt to create a tag type with an empty name
        Then I should receive an error indicating name is required

    Scenario: Validate tag type name length
        When I attempt to create a tag type with a name longer than 50 characters
        Then I should receive an error indicating name is too long