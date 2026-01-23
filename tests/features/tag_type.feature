Feature: Tag_Typo_CRUD
    As the system
    I want to manage tag types effectively
    So that tag types can be created, read, updated, and deleted as needed
    
    Background:
        Given the following tag types exist:
        | name        | is_privileged | parent_tag_type | sort_order |
        | category    | true          | null            | 1          |
        | subcategory | true          | category        | 2          |
        | weapon      | true          | subcategory     | 3          |
    
    Scenario: Create a new tag type
        When I create a tag type with the following details:
        | name        | is_privileged | parent_tag_type | sort_order |
        | material    | false         | weapon          | 4          |
        Then the tag type "material" should exist with is_privileged equal to false
        And its parent_tag_type should be "weapon"
        And its sort_order should be 4
    
    Scenario: Read existing tag types
        When I retrieve the list of tag types
        Then I should see the following tag types:
        | name        | is_privileged | parent_tag_type | sort_order |
        | category    | true          | null            | 1          |
        | subcategory | true          | category        | 2          |
        | weapon      | true          | subcategory     | 3          |
    
    Scenario: Update an existing tag type
        Given the tag type "subcategory" exists
        When I update the tag type "subcategory" to have is_privileged equal to false
        Then the tag type "subcategory" should have is_privileged equal to false
    
    Scenario: Delete an existing tag type
        Given the tag type "weapon" exists
        When I delete the tag type "weapon"
        Then the tag type "weapon" should not exist anymore

    Scenario: Prevent tag type deletion if in use
        Given the tag type "category" exists
        And there is a tag using the tag type "category"
        When I attempt to delete the tag type "category"
        Then I should receive an error indicating that the tag type cannot be deleted because it is in use
    
    Scenario: Prevent duplicate tag type creation
        When I attempt to create a tag type with the name "category"
        Then I should receive an error indicating that the tag type name must be unique

    Scenario: Custom is the only non-privileged tag type
        When I create a tag type with the following details:
        | name        | is_privileged | parent_tag_type | sort_order |
        | custom      | false         | null            | 5          |
        Then the tag type "custom" should exist with is_privileged equal to false
        And all other tag types should have is_privileged equal to true