Feature: Fight Management
  As a tournament organizer
  I want to manage fight records and participant rosters
  So that I can track fight history, outcomes, and fighter participation

  Background:
    Given the database is empty

  # ===== HAPPY PATH SCENARIOS =====

  Scenario: Create a singles duel fight with two participants
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    When I create a fight on "2025-06-15" at "Battle Arena Denver"
    And I add fighter "John Smith" to side 1 as "fighter"
    And I add fighter "Jane Doe" to side 2 as "fighter"
    Then the fight is created successfully
    And the fight date is "2025-06-15"
    And the fight location is "Battle Arena Denver"
    And the fight has 2 participants
    And participant "John Smith" is on side 1 with role "fighter"
    And participant "Jane Doe" is on side 2 with role "fighter"

  Scenario: Create a team fight with multiple fighters per side
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    And a fighter "Bob Wilson" exists for team "Team USA"
    And a fighter "Alice Johnson" exists for team "Team USA"
    When I create a fight on "2025-07-20" at "Chicago Combat Arena"
    And I add fighter "John Smith" to side 1 as "captain"
    And I add fighter "Jane Doe" to side 1 as "fighter"
    And I add fighter "Bob Wilson" to side 2 as "captain"
    And I add fighter "Alice Johnson" to side 2 as "fighter"
    Then the fight is created successfully
    And the fight has 4 participants
    And side 1 has 2 fighters
    And side 2 has 2 fighters
    And side 1 has exactly 1 captain
    And side 2 has exactly 1 captain

  Scenario: Create fight with video URL and winner side
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    When I create a fight on "2025-08-10" at "Seattle Armory"
    And I add fighter "John Smith" to side 1 as "fighter"
    And I add fighter "Jane Doe" to side 2 as "fighter"
    And I set video URL to "https://youtube.com/watch?v=abc123"
    And I set winner side to 1
    And I set notes to "Epic battle with great technique"
    Then the fight is created successfully
    And the fight video URL is "https://youtube.com/watch?v=abc123"
    And the fight winner side is 1
    And the fight notes are "Epic battle with great technique"

  Scenario: Create fight with alternate and coach roles
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    And a fighter "Bob Wilson" exists for team "Team USA"
    And a fighter "Alice Johnson" exists for team "Team USA"
    And a fighter "Coach Mike" exists for team "Team USA"
    When I create a fight on "2025-09-15" at "Portland Arena"
    And I add fighter "John Smith" to side 1 as "captain"
    And I add fighter "Bob Wilson" to side 1 as "alternate"
    And I add fighter "Coach Mike" to side 1 as "coach"
    And I add fighter "Jane Doe" to side 2 as "fighter"
    And I add fighter "Alice Johnson" to side 2 as "fighter"
    Then the fight is created successfully
    And participant "Bob Wilson" has role "alternate"
    And participant "Coach Mike" has role "coach"

  Scenario: Retrieve fight with nested participant and fighter data
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    And a fight exists on "2025-06-15" at "Test Arena" with fighters:
      | fighter    | side | role    |
      | John Smith | 1    | fighter |
      | Jane Doe   | 2    | fighter |
    When I retrieve the fight by ID
    Then the response includes the fight
    And the fight includes nested participation data
    And the participation data includes nested fighter data
    And fighter "John Smith" data includes team "Team USA"
    And fighter "Jane Doe" data includes team "Team USA"

  Scenario: List all fights excludes soft-deleted fights
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    And a fight exists on "2025-06-15" at "Arena A" with fighters:
      | fighter    | side | role    |
      | John Smith | 1    | fighter |
      | Jane Doe   | 2    | fighter |
    And a fight exists on "2025-07-20" at "Arena B" with fighters:
      | fighter    | side | role    |
      | John Smith | 1    | fighter |
      | Jane Doe   | 2    | fighter |
    And the fight at "Arena B" is soft deleted
    When I list all fights
    Then I receive exactly 1 fight
    And the fight at "Arena A" is in the list
    And the fight at "Arena B" is not in the list

  Scenario: List fights by date range
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    And a fight exists on "2025-06-15" at "Arena A" with fighters:
      | fighter    | side | role    |
      | John Smith | 1    | fighter |
      | Jane Doe   | 2    | fighter |
    And a fight exists on "2025-07-20" at "Arena B" with fighters:
      | fighter    | side | role    |
      | John Smith | 1    | fighter |
      | Jane Doe   | 2    | fighter |
    And a fight exists on "2025-08-10" at "Arena C" with fighters:
      | fighter    | side | role    |
      | John Smith | 1    | fighter |
      | Jane Doe   | 2    | fighter |
    When I list fights between "2025-06-01" and "2025-07-31"
    Then I receive exactly 2 fights
    And the fight at "Arena A" is in the list
    And the fight at "Arena B" is in the list
    And the fight at "Arena C" is not in the list

  Scenario: List fights by fighter participation
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    And a fighter "Bob Wilson" exists for team "Team USA"
    And a fight exists on "2025-06-15" at "Arena A" with fighters:
      | fighter    | side | role    |
      | John Smith | 1    | fighter |
      | Jane Doe   | 2    | fighter |
    And a fight exists on "2025-07-20" at "Arena B" with fighters:
      | fighter    | side | role    |
      | John Smith | 1    | fighter |
      | Bob Wilson | 2    | fighter |
    And a fight exists on "2025-08-10" at "Arena C" with fighters:
      | fighter    | side | role    |
      | Jane Doe   | 1    | fighter |
      | Bob Wilson | 2    | fighter |
    When I list fights for fighter "John Smith"
    Then I receive exactly 2 fights
    And the fight at "Arena A" is in the list
    And the fight at "Arena B" is in the list
    And the fight at "Arena C" is not in the list

  Scenario: Update fight location and winner
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    And a fight exists on "2025-06-15" at "Original Arena" with fighters:
      | fighter    | side | role    |
      | John Smith | 1    | fighter |
      | Jane Doe   | 2    | fighter |
    When I update the fight location to "Updated Arena"
    And I update the fight winner side to 2
    Then the fight is updated successfully
    And the fight location is "Updated Arena"
    And the fight winner side is 2

  Scenario: Soft delete a fight
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    And a fight exists on "2025-06-15" at "Test Arena" with fighters:
      | fighter    | side | role    |
      | John Smith | 1    | fighter |
      | Jane Doe   | 2    | fighter |
    When I soft delete the fight
    Then the fight is marked as deleted
    And the fight does not appear in default listings

  # ===== VALIDATION ERRORS =====

  Scenario: Cannot create fight with future date
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    When I attempt to create a fight on "2030-12-31" at "Test Arena"
    And I add fighter "John Smith" to side 1 as "fighter"
    And I add fighter "Jane Doe" to side 2 as "fighter"
    Then I receive a validation error
    And the error message contains "future"

  Scenario: Cannot create fight with empty location
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    When I attempt to create a fight on "2025-06-15" at ""
    And I add fighter "John Smith" to side 1 as "fighter"
    And I add fighter "Jane Doe" to side 2 as "fighter"
    Then I receive a validation error
    And the error message contains "location"

  Scenario: Cannot create fight with only 1 participant
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    When I attempt to create a fight on "2025-06-15" at "Test Arena"
    And I add fighter "John Smith" to side 1 as "fighter"
    Then I receive a validation error
    And the error message contains "at least 2 participants"

  Scenario: Cannot create fight with participants on only one side
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    When I attempt to create a fight on "2025-06-15" at "Test Arena"
    And I add fighter "John Smith" to side 1 as "fighter"
    And I add fighter "Jane Doe" to side 1 as "fighter"
    Then I receive a validation error
    And the error message contains "both sides"

  Scenario: Cannot add same fighter twice to same fight
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    When I attempt to create a fight on "2025-06-15" at "Test Arena"
    And I add fighter "John Smith" to side 1 as "fighter"
    And I add fighter "John Smith" to side 2 as "fighter"
    And I add fighter "Jane Doe" to side 2 as "fighter"
    Then I receive a validation error
    And the error message contains "duplicate fighter"

  Scenario: Cannot have multiple captains on same side
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    And a fighter "Bob Wilson" exists for team "Team USA"
    And a fighter "Alice Johnson" exists for team "Team USA"
    When I attempt to create a fight on "2025-06-15" at "Test Arena"
    And I add fighter "John Smith" to side 1 as "captain"
    And I add fighter "Jane Doe" to side 1 as "captain"
    And I add fighter "Bob Wilson" to side 2 as "fighter"
    And I add fighter "Alice Johnson" to side 2 as "fighter"
    Then I receive a validation error
    And the error message contains "multiple captains"

  Scenario: Cannot create fight with nonexistent fighter
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    When I attempt to create a fight on "2025-06-15" at "Test Arena"
    And I add fighter "John Smith" to side 1 as "fighter"
    And I add nonexistent fighter with ID "00000000-0000-0000-0000-000000000000" to side 2 as "fighter"
    Then I receive a validation error
    And the error message contains "fighter not found"

  Scenario: Cannot set winner side to invalid value
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    When I attempt to create a fight on "2025-06-15" at "Test Arena"
    And I add fighter "John Smith" to side 1 as "fighter"
    And I add fighter "Jane Doe" to side 2 as "fighter"
    And I set winner side to 5
    Then I receive a validation error
    And the error message contains "winner side must be 1 or 2"

  Scenario: Cannot create fight with invalid participation role
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    When I attempt to create a fight on "2025-06-15" at "Test Arena"
    And I add fighter "John Smith" to side 1 as "invalid_role"
    And I add fighter "Jane Doe" to side 2 as "fighter"
    Then I receive a validation error
    And the error message contains "invalid role"

  # ===== BUSINESS RULES =====

  Scenario: Fight can have null winner (draw or not yet determined)
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    When I create a fight on "2025-06-15" at "Test Arena"
    And I add fighter "John Smith" to side 1 as "fighter"
    And I add fighter "Jane Doe" to side 2 as "fighter"
    And I set winner side to null
    Then the fight is created successfully
    And the fight winner side is null

  Scenario: Fight can have no video URL
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    When I create a fight on "2025-06-15" at "Test Arena"
    And I add fighter "John Smith" to side 1 as "fighter"
    And I add fighter "Jane Doe" to side 2 as "fighter"
    Then the fight is created successfully
    And the fight video URL is null

  Scenario: Fight can have optional notes
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    When I create a fight on "2025-06-15" at "Test Arena"
    And I add fighter "John Smith" to side 1 as "fighter"
    And I add fighter "Jane Doe" to side 2 as "fighter"
    And I set notes to "Championship round - best of 3"
    Then the fight is created successfully
    And the fight notes are "Championship round - best of 3"

  Scenario: Fighters from different teams can participate in same fight
    Given an active country exists with code "USA" and name "United States"
    And an active country exists with code "CAN" and name "Canada"
    And a team "Team USA" exists for country "USA"
    And a team "Team Canada" exists for country "CAN"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team Canada"
    When I create a fight on "2025-06-15" at "International Arena"
    And I add fighter "John Smith" to side 1 as "fighter"
    And I add fighter "Jane Doe" to side 2 as "fighter"
    Then the fight is created successfully
    And participant "John Smith" belongs to team "Team USA"
    And participant "Jane Doe" belongs to team "Team Canada"

  Scenario: Same fighter can participate in multiple different fights
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    And a fighter "Bob Wilson" exists for team "Team USA"
    And a fight exists on "2025-06-15" at "Arena A" with fighters:
      | fighter    | side | role    |
      | John Smith | 1    | fighter |
      | Jane Doe   | 2    | fighter |
    When I create a fight on "2025-07-20" at "Arena B"
    And I add fighter "John Smith" to side 1 as "fighter"
    And I add fighter "Bob Wilson" to side 2 as "fighter"
    Then the fight is created successfully
    And fighter "John Smith" has 2 fight participations

  # ===== TRANSACTION SCENARIOS =====

  Scenario: Fight creation rolls back when participant validation fails
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    When I attempt to create a fight on "2025-06-15" at "Test Arena"
    And I add fighter "John Smith" to side 1 as "fighter"
    And I add nonexistent fighter with ID "00000000-0000-0000-0000-000000000000" to side 2 as "fighter"
    Then I receive a validation error
    And no fight is created in the database
    And no participations are created in the database

  Scenario: Fight creation is atomic - all participants created together
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    And a fighter "Bob Wilson" exists for team "Team USA"
    And a fighter "Alice Johnson" exists for team "Team USA"
    When I create a fight on "2025-06-15" at "Test Arena"
    And I add fighter "John Smith" to side 1 as "captain"
    And I add fighter "Jane Doe" to side 1 as "fighter"
    And I add fighter "Bob Wilson" to side 2 as "captain"
    And I add fighter "Alice Johnson" to side 2 as "fighter"
    Then the fight is created successfully
    And all 4 participations are created atomically
    And the fight includes all 4 participants when retrieved

  Scenario: Update fight preserves existing participations
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    And a fight exists on "2025-06-15" at "Original Arena" with fighters:
      | fighter    | side | role    |
      | John Smith | 1    | fighter |
      | Jane Doe   | 2    | fighter |
    When I update the fight location to "Updated Arena"
    Then the fight is updated successfully
    And the fight still has 2 participants
    And participant "John Smith" is still on side 1
    And participant "Jane Doe" is still on side 2

  Scenario: Soft delete fight does not delete participations
    Given an active country exists with code "USA" and name "United States"
    And a team "Team USA" exists for country "USA"
    And a fighter "John Smith" exists for team "Team USA"
    And a fighter "Jane Doe" exists for team "Team USA"
    And a fight exists on "2025-06-15" at "Test Arena" with fighters:
      | fighter    | side | role    |
      | John Smith | 1    | fighter |
      | Jane Doe   | 2    | fighter |
    When I soft delete the fight
    Then the fight is marked as deleted
    And the participations still exist in database
    And the participations are still linked to the fight
