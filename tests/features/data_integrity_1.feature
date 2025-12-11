Feature: Data Integrity and Edge Cases
  As the system
  I want to maintain data consistency
  So that the database remains reliable and queryable

  # Soft Delete Behavior
  Scenario: Soft deleted entities are excluded from default queries
    Given the following fighters exist:
      | fighter_id | name        | isDeleted |
      | fighter-1  | John Smith  | false     |
      | fighter-2  | Jane Doe    | false     |
      | fighter-3  | Bob Johnson | true      |
    When a user queries for all fighters
    Then the results should include fighters with ids "fighter-1,fighter-2"
    And the results should not include fighter with id "fighter-3"

  Scenario: Soft deleted entities can be retrieved with explicit flag
    Given the following fighters exist:
      | fighter_id | name        | isDeleted |
      | fighter-1  | John Smith  | false     |
      | fighter-2  | Jane Doe    | false     |
      | fighter-3  | Bob Johnson | true      |
    When a user queries for all fighters including deleted
    Then the results should include fighters with ids "fighter-1,fighter-2,fighter-3"

  # UUID Primary Keys
  Scenario: System generates valid UUID v4 for new entities
    When an admin creates a new fighter with name "Test Fighter"
    Then the fighter should have an id that matches UUID v4 format
    And the fighter id should be unique in the database

  # Timestamp Tracking
  Scenario: Created_at timestamp is automatically set on entity creation
    When an admin creates a new fighter with name "Test Fighter"
    Then the fighter should have a created_at timestamp
    And the created_at timestamp should be within 1 second of current time
    And the created_at timestamp should be in UTC

  # Referential Integrity
  Scenario: Cannot create tag with non-existent fight_id
    Given no fight exists with id "fake-fight-id"
    When a user attempts to create a tag with fight_id "fake-fight-id"
    Then the request should be rejected with error "Fight not found"

  Scenario: Cannot create tag with non-existent tag_type_id
    Given a fight exists with id "fight-1"
    And no tag type exists with id "fake-tag-type-id"
    When a user attempts to create a tag with tag_type_id "fake-tag-type-id"
    Then the request should be rejected with error "Tag type not found"

  # Voting Edge Cases
  Scenario: Request automatically resolves when exact threshold is reached
    Given a tag change request exists with threshold 10 and 9 votes for
    When 1 vote "for" is cast on the request
    Then the request status should immediately change to "accepted"
    And no additional votes should be allowed on the request

  Scenario: Vote counts are accurate with mixed votes
    Given a tag change request exists with threshold 10
    When the following votes are cast:
      | vote_type | count |
      | for       | 7     |
      | against   | 3     |
    Then the request should have votes_for equal to 7
    And the request should have votes_against equal to 3
    And the request status should be "pending"

  # Concurrent Request Handling
  Scenario: Resolving one request allows new request for same tag type
    Given a pending tag change request exists for fight "fight-1" and tag_type "weapon"
    When the request is resolved with status "accepted"
    Then a new tag change request can be created for fight "fight-1" and tag_type "weapon"

  # Parent Tag Relationships
  Scenario: Parent tag must exist before creating child tag
    Given a fight "fight-1" has no tags
    When a subcategory tag is attempted to be added without a category tag
    Then the request should be rejected
    And the fight should still have 0 tags

  # Tag Type Hierarchy Validation
  Scenario: Tag type parent relationships must be valid
    When an admin attempts to create a tag type with the following details:
      | name   | parent_tag_type_id |
      | weapon | category           |
    Then the request should be rejected with error "Invalid parent tag type hierarchy"

  # Fight Date Validation
  Scenario: Fight dates cannot be in distant future
    When an admin attempts to create a fight with fight_date "2100-01-01"
    Then the request should be rejected with error "Fight date cannot be more than 1 year in the future"

  Scenario: Fight dates can be historical
    When an admin creates a fight with fight_date "1990-05-15"
    Then the fight should be created successfully

  # Location Validation
  Scenario: Fight location is required
    When an admin attempts to create a fight without a location
    Then the request should be rejected with error "Fight location is required"

  # Tag Value Constraints
  Scenario: Tag values have maximum length
    When a user attempts to create a custom tag with value longer than 200 characters
    Then the request should be rejected with error "Tag value exceeds maximum length"

  Scenario: Tag values cannot be empty
    When a user attempts to create a tag with empty string value
    Then the request should be rejected with error "Tag value cannot be empty"

  Scenario: Admin can cancel any request
    Given user "user-1" created a pending tag change request "req-1"
    When admin "admin-1" cancels request "req-1"
    Then the request should be cancelled successfully

  # Team Relationships
  Scenario: Fighter can be assigned to team from different country
    Given a team exists with the following details:
      | team_id | name        | country_id |
      | team-1  | London Team | GB         |
    When an admin creates a fighter with the following details:
      | name       | country_id | team_id |
      | John Smith | US         | team-1  |
    Then the fighter should be created successfully
    And the fighter country_id should be "US"
    And the fighter team_id should be "team-1"
