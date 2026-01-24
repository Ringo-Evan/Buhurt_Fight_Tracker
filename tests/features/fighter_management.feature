Feature: Fighter Management
  As a system administrator
  I want to manage fighters and their team associations
  So that I can track fighter rosters, transfers, and participation history

  Background:
    Given the database is empty

  # ===== HAPPY PATH SCENARIOS =====

  Scenario: Create fighter with valid team
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    When I create a fighter "John Smith" for team "Team USA"
    Then the fighter is created successfully
    And the fighter name is "John Smith"
    And the fighter's team is "Team USA"
    And the fighter's team country is "United States"

  Scenario: Retrieve fighter with nested team and country data
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    When I retrieve the fighter "John Smith"
    Then the response includes the fighter
    And the fighter includes nested team data
    And the team data includes nested country data
    And the country code is "USA"
    And the country name is "United States"

  Scenario: List all fighters excludes soft-deleted fighters
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    And fighter "Jane Doe" is soft deleted
    When I list all fighters
    Then I receive exactly 1 fighter
    And the fighter "John Smith" is in the list
    And the fighter "Jane Doe" is not in the list

  Scenario: Admin can retrieve soft-deleted fighter
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And fighter "John Smith" is soft deleted
    When I retrieve fighter "John Smith" as admin with include_deleted
    Then the response includes the fighter
    And the fighter is marked as deleted
    And the team relationship is intact

  # ===== TEAM VALIDATION SCENARIOS =====

  Scenario: Create fighter with non-existent team fails
    When I attempt to create a fighter "John Smith" for non-existent team ID
    Then I receive a validation error
    And the error says "Team not found"

  Scenario: Create fighter with soft-deleted team fails
    Given an active country exists with code "USA" and name "United States"
    And a soft-deleted team "Defunct Team" exists for country "USA"
    When I attempt to create a fighter "John Smith" for team "Defunct Team"
    Then I receive a validation error
    And the error says "Team is not active"

  Scenario: Update fighter to non-existent team fails
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    When I attempt to update fighter "John Smith" to non-existent team ID
    Then I receive a validation error
    And the error says "Team not found"

  Scenario: Update fighter to soft-deleted team fails
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a team "Defunct Team" exists for country "USA"
    And team "Defunct Team" is soft deleted
    And a fighter "John Smith" exists for team "Team USA"
    When I attempt to update fighter "John Smith" to team "Defunct Team"
    Then I receive a validation error
    And the error says "Team is not active"

  # ===== FILTERING SCENARIOS =====

  Scenario: List fighters filtered by team
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA Alpha" exists for country "USA"
    And a team "Team USA Beta" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA Alpha"
    And a fighter "Jane Doe" exists for team "Team USA Alpha"
    And a fighter "Bob Jones" exists for team "Team USA Beta"
    When I list fighters filtered by team "Team USA Alpha"
    Then I receive exactly 2 fighters
    And all fighters belong to team "Team USA Alpha"

  Scenario: List fighters filtered by country
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA Alpha" exists for country "USA"
    And a team "Team USA Beta" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA Alpha"
    And a fighter "Jane Doe" exists for team "Team USA Beta"
    And an active country exists with code "CAN" and name "Canada"
    And a team "Team Canada" exists for country "CAN"
    And a fighter "Bob Jones" exists for team "Team Canada"
    When I list fighters filtered by country "USA"
    Then I receive exactly 2 fighters
    And all fighters belong to teams from country "USA"

  Scenario: List fighters by team excludes soft-deleted fighters
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    And fighter "Jane Doe" is soft deleted
    When I list fighters filtered by team "Team USA"
    Then I receive exactly 1 fighter
    And the fighter "John Smith" is in the list

  Scenario: List fighters by country excludes soft-deleted fighters
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    And fighter "Jane Doe" is soft deleted
    When I list fighters filtered by country "USA"
    Then I receive exactly 1 fighter
    And the fighter "John Smith" is in the list

  # ===== UPDATE SCENARIOS =====

  Scenario: Update fighter name
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    When I update fighter "John Smith" name to "Jonathan Smith"
    Then the fighter name is "Jonathan Smith"
    And the fighter's team is still "Team USA"

  Scenario: Transfer fighter to different team (same country)
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA Alpha" exists for country "USA"
    And a team "Team USA Beta" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA Alpha"
    When I update fighter "John Smith" to team "Team USA Beta"
    Then the fighter's team is "Team USA Beta"
    And the fighter's team country is "United States"

  Scenario: Transfer fighter to team with different country
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And an active country exists with code "CAN" and name "Canada"
    And a team "Team Canada" exists for country "CAN"
    When I update fighter "John Smith" to team "Team Canada"
    Then the fighter's team is "Team Canada"
    And the fighter's team country is "Canada"

  # ===== SOFT DELETE SCENARIOS =====

  Scenario: Soft delete fighter sets is_deleted flag
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    When I soft delete fighter "John Smith"
    Then the fighter is marked as deleted
    And listing fighters excludes the deleted fighter
    And admin can still retrieve the deleted fighter

  Scenario: Soft delete fighter preserves team relationship
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    When I soft delete fighter "John Smith"
    Then the fighter is marked as deleted
    And the team relationship is intact
    And retrieving as admin includes team data

  Scenario: Cannot soft delete already deleted fighter
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And fighter "John Smith" is soft deleted
    When I attempt to soft delete fighter "John Smith" again
    Then I receive a not found error

  # ===== VALIDATION SCENARIOS =====

  Scenario: Create fighter with empty name fails
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    When I attempt to create a fighter with empty name for team "Team USA"
    Then I receive a validation error
    And the error says "name is required"

  Scenario: Create fighter with whitespace-only name fails
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    When I attempt to create a fighter with name "   " for team "Team USA"
    Then I receive a validation error
    And the error says "name is required"

  Scenario: Update fighter with empty name fails
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    When I attempt to update fighter "John Smith" name to empty string
    Then I receive a validation error
    And the error says "name is required"

  # ===== EDGE CASE SCENARIOS =====

  Scenario: List fighters when none exist
    When I list all fighters
    Then I receive an empty list

  Scenario: Retrieve non-existent fighter by ID
    When I retrieve a fighter with non-existent ID
    Then I receive a not found error

  Scenario: Update non-existent fighter fails
    When I attempt to update a fighter with non-existent ID
    Then I receive a not found error

  Scenario: Soft delete non-existent fighter fails
    When I attempt to soft delete a fighter with non-existent ID
    Then I receive a not found error

  Scenario: Eager loading prevents N+1 queries
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    When I retrieve the fighter "John Smith"
    Then the team data is eager loaded
    And the country data is eager loaded within team
    And no additional queries are executed for relationships

  # ===== 3-LEVEL HIERARCHY SCENARIOS =====

  Scenario: Fighter inherits country through team relationship
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    When I retrieve the fighter "John Smith"
    Then the fighter's country (via team) is "United States"
    And the fighter's country code (via team) is "USA"

  Scenario: Multiple fighters from different countries
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And an active country exists with code "CAN" and name "Canada"
    And a team "Team Canada" exists for country "CAN"
    And a fighter "Jane Doe" exists for team "Team Canada"
    And an active country exists with code "GBR" and name "United Kingdom"
    And a team "Team UK" exists for country "GBR"
    And a fighter "Bob Jones" exists for team "Team UK"
    When I list all fighters
    Then I receive exactly 3 fighters
    And fighter "John Smith" belongs to country "USA" via team
    And fighter "Jane Doe" belongs to country "CAN" via team
    And fighter "Bob Jones" belongs to country "GBR" via team

  Scenario: Team soft delete does not cascade to fighters (FK RESTRICT)
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    When I attempt to soft delete team "Team USA"
    Then the soft delete succeeds
    And the team is marked as deleted
    But the fighter "John Smith" is still active
    And the fighter's team reference is intact

  Scenario: Country soft delete does not cascade to fighters (via team FK)
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    When I soft delete country "USA"
    Then the country is marked as deleted
    But the team "Team USA" is still active
    And the fighter "John Smith" is still active
    And the full hierarchy is intact
