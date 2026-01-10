Feature: Fight Creation
  As an administrator
  I want to create fight records
  So that the community can tag and categorize them

  Background:
    Given the following users exist:
      | user_id | username | role   |
      | admin-1 | admin    | admin  |
      | user-1  | john     | user   |
      | system-1| system   | system |
    And the following countries exist:
      | country_id | name           | code |
      | country-1  | United States  | US   |
      | country-2  | United Kingdom | GB   |
    And the following fighters exist:
      | fighter_id | name          | country_id |
      | fighter-1  | John Smith    | country-1  |
      | fighter-2  | Jane Doe      | country-2  |
      | fighter-3  | Bob Johnson   | country-1  |
      | fighter-4  | Alice Brown   | country-2  |
    And the following tag types exist:
      | name     | is_privileged |
      | category | true          |

  # Happy Path: Admin Creates Singles Fight
  Scenario: Admin creates singles fight with category tag
    When admin "admin-1" creates a fight with the following details:
      | fight_date | location        | category |
      | 2024-03-15 | London, UK      | Singles  |
    And adds the following participants:
      | fighter_id | side | role    |
      | fighter-1  | 1    | fighter |
      | fighter-2  | 2    | fighter |
    Then a fight should be created with status "success"
    And the fight should have a category tag with value "Singles"
    And the fight should have 2 participants
    And participant fighter "fighter-1" should be on side 1 with role "fighter"
    And participant fighter "fighter-2" should be on side 2 with role "fighter"
    And the fight created_by should be "admin-1"

  # Happy Path: System Creates Team Fight
  Scenario: System user creates team fight with multiple fighters per side
    When system user "system-1" creates a fight with the following details:
      | fight_date | location     | category | size |
      | 2024-04-20 | New York, US | Team     |   5  |
    And adds the following participants:
      | fighter_id | side | role    |
      | fighter-1  | 1    | fighter |
      | fighter-3  | 1    | fighter |
      | fighter-5  | 1    | fighter |
      | fighter-7  | 1    | fighter |
      | fighter-9  | 1    | fighter |
      | fighter-2  | 2    | fighter |
      | fighter-4  | 2    | fighter |
      | fighter-6  | 2    | fighter |
      | fighter-8  | 2    | fighter |
      | fighter-10 | 2    | fighter |
    Then a fight should be created with status "success"
    And the fight should have a category tag with value "Team"
    And the fight should have 10 participants
    And side 1 should have 5 fighters
    And side 2 should have 5 fighters

  # Validation: Category Tag Required
  Scenario: Cannot create fight without category tag
    When admin "admin-1" attempts to create a fight with the following details:
      | fight_date | location   |
      | 2024-05-01 | Paris, FR  |
    Then the request should be rejected with error "Category tag is required for fight creation"
    And no fight should be created

  # Validation: At Least One Fighter Per Side
  Scenario: Cannot create singles fight with only one participant
    When admin "admin-1" attempts to create a fight with the following details:
      | fight_date | location   | category |
      | 2024-05-01 | Paris, FR  | Singles  |
    And adds the following participants:
      | fighter_id | side | role    |
      | fighter-1  | 1    | fighter |
    Then the request should be accepted with notification "Fight must have at least one fighter on each side, adding 'Missing Fighter'"
    And fight should be created with the following participant:
      | fighter_id | side | role    |
      | fighter-1  | 1    | fighter |
      | fighter-0  | 2    | fighter |

  # Validation: Fighter Cannot Be On Both Sides
  Scenario: Fighter cannot participate on both sides of same fight
    When admin "admin-1" attempts to create a fight with the following details:
      | fight_date | location   | category |
      | 2024-05-01 | Paris, FR  | Singles  |
    And adds the following participants:
      | fighter_id | side | role    |
      | fighter-1  | 1    | fighter |
      | fighter-1  | 2    | fighter |
    Then the request should be rejected with error "Fighter cannot participate on multiple sides"
    And no fight should be created

  # Optional: Recording Winner
  Scenario: Admin creates fight and records winner
    When admin "admin-1" creates a fight with the following details:
      | fight_date | location   | category | winner_side |
      | 2024-05-01 | Paris, FR  | Singles  | 1           |
    And adds the following participants:
      | fighter_id | side | role    |
      | fighter-1  | 1    | fighter |
      | fighter-2  | 2    | fighter |
    Then a fight should be created with status "success"
    And the fight winner_side should be 1

  # Optional: Multiple Roles
  Scenario: Fighter can have multiple roles in same fight
    When admin "admin-1" creates a fight with the following details:
      | fight_date | location   | category |
      | 2024-05-01 | Paris, FR  | Team     |
    And adds the following participants:
      | fighter_id | side | role      |
      | fighter-1  | 1    | fighter   |
      | fighter-2  | 1    | coach     |
      | fighter-3  | 2    | fighter   |
      | fighter-4  | 2    | fighter   |
    Then a fight should be created with status "success"
    And fighter "fighter-2" should have role "coach" on side 1

  # Validation: Valid Sides Only
  Scenario: Cannot create participant with invalid side number
    When admin "admin-1" attempts to create a fight with the following details:
      | fight_date | location   | category |
      | 2024-05-01 | Paris, FR  | Singles  |
    And adds the following participants:
      | fighter_id | side | role    |
      | fighter-1  | 1    | fighter |
      | fighter-2  | 3    | fighter |
    Then the request should be rejected with error "Side must be 1 or 2"
    And no fight should be created

  # Soft Delete: Fighter Deletion Doesn't Break Fight
  Scenario: Fight remains valid when participant fighter is deleted
    Given a fight "fight-1" exists with the following details:
      | fight_date | location   | category | created_by |
      | 2024-03-15 | London, UK | Singles  | admin-1    |
    And the fight has the following participants:
      | fighter_id | side | role    |
      | fighter-1  | 1    | fighter |
      | fighter-2  | 2    | fighter |
    When fighter "fighter-1" is soft deleted
    Then the fight "fight-1" should still exist
    And the fight participation record for fighter "fighter-1" should have fighter_id set to null
    And the fight participation record should preserve side and role information
