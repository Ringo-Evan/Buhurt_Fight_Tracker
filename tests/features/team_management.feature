Feature: Team Management
  As a system administrator
  I want to manage teams associated with countries
  So that I can track team rosters and lineups for Buhurt fights

  Background:
    Given the database is empty

  # ============================================================================
  # HAPPY PATH SCENARIOS - Team Creation
  # ============================================================================

  Scenario: Create team with valid country
    Given an active country exists with code "USA"
    When I create a team "Team USA" for country "USA"
    Then the team is created successfully
    And the team name is "Team USA"
    And the team country code is "USA"
    And the team is not marked as deleted

  Scenario: Create multiple teams for same country
    Given an active country exists with code "USA"
    When I create a team "Team USA East" for country "USA"
    And I create a team "Team USA West" for country "USA"
    Then both teams are created successfully
    And both teams belong to country "USA"

  # ============================================================================
  # VALIDATION SCENARIOS - Country Relationship
  # ============================================================================

  Scenario: Create team with non-existent country fails
    Given no country exists with code "XYZ"
    When I attempt to create a team "Team XYZ" for country "XYZ"
    Then I receive a validation error
    And the error says "Country not found"
    And the team is not created

  Scenario: Create team with soft-deleted country fails
    Given a soft-deleted country exists with code "SUN"
    When I attempt to create a team "Soviet Team" for country "SUN"
    Then I receive a validation error
    And the error message contains "not active"
    And the team is not created

  Scenario: Create team with empty name fails
    Given an active country exists with code "USA"
    When I attempt to create a team with empty name for country "USA"
    Then I receive a validation error
    And the error says "name"
    And the team is not created

  # ============================================================================
  # RETRIEVAL SCENARIOS - With Eager Loading
  # ============================================================================

  Scenario: Retrieve team with nested country data
    Given an active country "United States" exists with code "USA"
    And a team "Team USA" exists for country "USA"
    When I retrieve the team by ID
    Then the team includes nested country data
    And the country code is "USA"
    And the country name is "United States"
    And the team name is "Team USA"

  Scenario: Retrieve non-existent team returns not found
    When I attempt to retrieve a team with non-existent ID
    Then I receive a not found error
    And the error says "Team not found"

  Scenario: Retrieve soft-deleted team as regular user returns not found
    Given an active country exists with code "USA"
    And a soft-deleted team exists for country "USA"
    When I attempt to retrieve the soft-deleted team
    Then I receive a not found error
    And the error says "Team not found"

  Scenario: Retrieve soft-deleted team as admin returns team
    Given an active country exists with code "USA"
    And a soft-deleted team "Deleted Team" exists for country "USA"
    When I retrieve the soft-deleted team as admin
    Then the team is returned successfully
    And the team name is "Deleted Team"
    And the team is marked as deleted
    And the team country code is "USA"

  # ============================================================================
  # LIST SCENARIOS - Filtering and Soft Delete
  # ============================================================================

  Scenario: List all teams excludes soft-deleted teams
    Given an active country exists with code "USA"
    And an active team "Active Team" exists for country "USA"
    And a soft-deleted team "Deleted Team" exists for country "USA"
    When I list all teams
    Then I receive 1 team
    And the team name is "Active Team"

  Scenario: List all teams when none exist returns empty list
    When I list all teams
    Then I receive an empty list

  Scenario: List teams filtered by country
    Given an active country exists with code "USA"
    And an active country exists with code "CAN"
    And 3 teams exist for country "USA"
    And 2 teams exist for country "CAN"
    When I list teams filtered by country "USA"
    Then I receive exactly 3 teams
    And all teams belong to country "USA"

  Scenario: List teams filtered by non-existent country returns empty list
    When I list teams filtered by country "XYZ"
    Then I receive an empty list

  # ============================================================================
  # UPDATE SCENARIOS - Team Attributes
  # ============================================================================

  Scenario: Update team name succeeds
    Given an active country exists with code "USA"
    And a team "Old Name" exists for country "USA"
    When I update the team name to "New Name"
    Then the update is successful
    And the team name is "New Name"
    And the team country code is still "USA"

  Scenario: Update team country to valid country succeeds
    Given an active country exists with code "USA"
    And an active country exists with code "CAN"
    And a team "Relocating Team" exists for country "USA"
    When I update the team country to "CAN"
    Then the update is successful
    And the team country code is "CAN"
    And the team name is still "Relocating Team"

  Scenario: Update team country to non-existent country fails
    Given an active country exists with code "USA"
    And a team "Team USA" exists for country "USA"
    When I attempt to update the team country to "XYZ"
    Then I receive a validation error
    And the error says "Country not found"
    And the team country code is still "USA"

  Scenario: Update team country to soft-deleted country fails
    Given an active country exists with code "USA"
    And a soft-deleted country exists with code "SUN"
    And a team "Team USA" exists for country "USA"
    When I attempt to update the team country to "SUN"
    Then I receive a validation error
    And the error message contains "not active"
    And the team country code is still "USA"

  # ============================================================================
  # SOFT DELETE SCENARIOS - Relationship Preservation
  # ============================================================================

  Scenario: Soft delete team preserves country relationship
    Given an active country "United States" exists with code "USA"
    And a team "Team USA" exists for country "USA"
    When I soft delete the team
    Then the team is marked as deleted
    And the country relationship is intact
    And I can retrieve the country data as admin
    And the country name is "United States"

  Scenario: Soft delete team excludes it from regular listings
    Given an active country exists with code "USA"
    And a team "Active Team" exists for country "USA"
    And a team "To Delete" exists for country "USA"
    When I soft delete the team "To Delete"
    And I list all teams
    Then I receive 1 team
    And the team name is "Active Team"

  Scenario: Soft delete non-existent team fails
    When I attempt to soft delete a team with non-existent ID
    Then I receive a not found error
    And the error says "Team not found"

  Scenario: Soft delete already deleted team fails
    Given an active country exists with code "USA"
    And a soft-deleted team exists for country "USA"
    When I attempt to soft delete the same team again
    Then I receive a validation error
    And the error message indicates the team is already deleted

  # ============================================================================
  # EDGE CASES - Database Constraints
  # ============================================================================

  Scenario: Database prevents orphan teams via FK constraint
    # This tests database-level enforcement, not just application validation
    Given an active country exists with code "USA"
    When I attempt to create a team with a fake country ID at database level
    Then the database rejects the insert with FK violation
    And no team is created

  Scenario: Deleting country with teams is prevented
    # This tests referential integrity - can't delete country if teams exist
    Given an active country exists with code "USA"
    And 2 teams exist for country "USA"
    When I attempt to permanently delete the country
    Then the deletion is rejected
    And the error message indicates teams still exist
    And the country still exists

  # ============================================================================
  # EAGER LOADING - Performance Verification
  # ============================================================================

  Scenario: Retrieving team eager loads country data (no N+1)
    Given an active country "United States" exists with code "USA"
    And a team "Team USA" exists for country "USA"
    When I retrieve the team by ID
    Then the country data is already loaded
    And no additional database query is needed for country
    And I can access country name without lazy loading

  Scenario: Listing teams eager loads all country data
    Given an active country exists with code "USA"
    And an active country exists with code "CAN"
    And 2 teams exist for country "USA"
    And 1 team exists for country "CAN"
    When I list all teams
    Then all country data is eager loaded
    And I can access each team's country name without N+1 queries
