Feature: Country Management
  As a system administrator
  I want to manage countries in the fight tracking system
  So that fighters and teams can be associated with their countries

  Background:
    Given the database is empty

  # ============================================================================
  # HAPPY PATHS (~40% of scenarios)
  # ============================================================================

  Scenario: Create country with valid data
    Given I have valid country data:
      | name           | code |
      | Czech Republic | CZE  |
    When I create a country
    Then the country is created successfully
    And the country has a unique ID
    And the country has the name "Czech Republic"
    And the country has the code "CZE"
    And the country is not deleted
    And the country has a creation timestamp

  Scenario: Retrieve country by ID
    Given the following countries exist:
      | name           | code |
      | Czech Republic | CZE  |
      | Poland         | POL  |
    When I retrieve the country "Czech Republic" by ID
    Then I receive the country details
    And the country has the name "Czech Republic"
    And the country has the code "CZE"

  Scenario: List all active countries
    Given the following countries exist:
      | name           | code |
      | Czech Republic | CZE  |
      | Poland         | POL  |
      | Germany        | DEU  |
    When I request the list of all countries
    Then I receive a list of 3 countries
    And the list contains a country with code "CZE"
    And the list contains a country with code "POL"
    And the list contains a country with code "DEU"

  Scenario: Retrieve country by ISO code
    Given the following countries exist:
      | name           | code |
      | Czech Republic | CZE  |
      | Poland         | POL  |
    When I retrieve the country by code "CZE"
    Then I receive the country details
    And the country has the name "Czech Republic"

  # ============================================================================
  # NEGATIVE CASES (~45% of scenarios)
  # ============================================================================

  Scenario: Reject country with duplicate ISO code
    Given the following countries exist:
      | name           | code |
      | Czech Republic | CZE  |
    And I have country data:
      | name                | code |
      | Czechia (alternate) | CZE  |
    When I attempt to create a country
    Then the request is rejected
    And I receive an error message "Country with code CZE already exists"

  Scenario: Reject country with empty name
    Given I have country data:
      | name | code |
      |      | CZE  |
    When I attempt to create a country
    Then the request is rejected
    And I receive a validation error indicating name is required

  Scenario: Reject country with null name
    Given I have country data with null name and code "CZE"
    When I attempt to create a country
    Then the request is rejected
    And I receive a validation error indicating name is required

  Scenario: Reject country with invalid ISO code format - lowercase
    Given I have country data:
      | name           | code |
      | Czech Republic | cze  |
    When I attempt to create a country
    Then the request is rejected
    And I receive a validation error indicating code must be 3 uppercase letters

  Scenario: Reject country with invalid ISO code format - too long
    Given I have country data:
      | name           | code |
      | Czech Republic | CZEE |
    When I attempt to create a country
    Then the request is rejected
    And I receive a validation error indicating code must be 3 uppercase letters

  Scenario: Reject country with invalid ISO code format - too short
    Given I have country data:
      | name           | code |
      | Czech Republic | CZ   |
    When I attempt to create a country
    Then the request is rejected
    And I receive a validation error indicating code must be 3 uppercase letters

  Scenario: Reject country with invalid ISO code format - contains numbers
    Given I have country data:
      | name           | code |
      | Czech Republic | CZ1  |
    When I attempt to create a country
    Then the request is rejected
    And I receive a validation error indicating code must be 3 uppercase letters


  Scenario: Reject country with Code that doesn't match any known ISO 3166-1 alpha-3 codes
    Given I have country data:
      | name           | code |
      | Narnia        | NAR  |
    When I attempt to create a country
    Then the request is rejected
    And I receive a validation error indicating code must be a valid ISO 3166-1 alpha-3 code

    
  Scenario: Return 404 when retrieving non-existent country by ID
    Given the database is empty
    When I retrieve a country by a random UUID
    Then the request fails with status 404
    And I receive an error message "Country not found"

  # ============================================================================
  # EDGE CASES (~15% of scenarios)
  # ============================================================================

  Scenario: Soft delete country marks it as deleted without removing from database
    Given the following countries exist:
      | name           | code |
      | Czech Republic | CZE  |
    When I delete the country "Czech Republic"
    Then the deletion is successful
    And the country "Czech Republic" is marked as deleted in the database
    And the country "Czech Republic" is not removed from the database

  Scenario: Allow creating country with same code as soft-deleted country
    Given the following countries exist:
      | name           | code |
      | Czech Republic | CZE  |
    And the country "Czech Republic" has been soft deleted
    And I have country data:
      | name    | code |
      | Czechia | CZE  |
    When I create a country
    Then the country is created successfully
    And the country has the name "Czechia"
    And the country has the code "CZE"

  Scenario: List countries excludes soft-deleted countries for regular users
    Given the following countries exist:
      | name           | code |
      | Czech Republic | CZE  |
      | Poland         | POL  |
      | Germany        | DEU  |
    And the country "Poland" has been soft deleted
    When I request the list of all countries as a regular user
    Then I receive a list of 2 countries
    And the list contains a country with code "CZE"
    And the list contains a country with code "DEU"
    And the list does not contain a country with code "POL"

  Scenario: Retrieve by ID returns 404 for soft-deleted country for regular users
    Given the following countries exist:
      | name           | code |
      | Czech Republic | CZE  |
    And the country "Czech Republic" has been soft deleted
    When I retrieve the country "Czech Republic" by ID as a regular user
    Then the request fails with status 404
    And I receive an error message "Country not found"

  Scenario: Admin can retrieve soft-deleted country by ID
    Given the following countries exist:
      | name           | code |
      | Czech Republic | CZE  |
    And the country "Czech Republic" has been soft deleted
    When I retrieve the country "Czech Republic" by ID as an admin
    Then I receive the country details
    And the country has the name "Czech Republic"
    And the country has the code "CZE"
    And the country is marked as deleted

  Scenario: Admin can list all countries including soft-deleted
    Given the following countries exist:
      | name           | code |
      | Czech Republic | CZE  |
      | Poland         | POL  |
      | Germany        | DEU  |
    And the country "Poland" has been soft deleted
    When I request the list of all countries as an admin
    Then I receive a list of 3 countries
    And the list contains a country with code "CZE"
    And the list contains a country with code "POL"
    And the list contains a country with code "DEU"

  Scenario: Retrieve by code returns null for soft-deleted country
    Given the following countries exist:
      | name           | code |
      | Czech Republic | CZE  |
    And the country "Czech Republic" has been soft deleted
    When I retrieve the country by code "CZE" as a regular user
    Then the request fails with status 404
    And I receive an error message "Country not found"

  Scenario: Update country name successfully
    Given the following countries exist:
      | name           | code |
      | Czech Republic | CZE  |
    And I have country data:
      | name    | code |
      | Czechia | CZE  |
    When I update the country "Czech Republic" with new data
    Then the update is successful
    And the country has the name "Czechia"
    And the country has the code "CZE"

  Scenario: Update country code successfully
    Given the following countries exist:
      | name    | code |
      | Czechia | CZE  |
    And I have country data:
      | name    | code |
      | Czechia | CZK  |
    When I update the country "Czechia" with new data
    Then the update is successful
    And the country has the name "Czechia"
    And the country has the code "CZK"

  Scenario: Reject update with duplicate active country code
    Given the following countries exist:
      | name           | code |
      | Czech Republic | CZE  |
      | Poland         | POL  |
    And I have country data:
      | name           | code |
      | Czech Republic | POL  |
    When I attempt to update the country "Czech Republic" with new data
    Then the request is rejected
    And I receive an error message "Country with code POL already exists"

  Scenario: Cannot permanently delete country with team relationships
    Given the following countries exist:
      | name           | code |
      | Czech Republic | CZE  |
    And the country "Czech Republic" has been soft deleted
    And the country "Czech Republic" has 1 team relationship
    When I attempt to permanently delete the country "Czech Republic" as an admin
    Then the request is rejected
    And I receive an error message "Cannot permanently delete country with existing relationships"

  Scenario: Admin can permanently delete country without relationships
    Given the following countries exist:
      | name           | code |
      | Czech Republic | CZE  |
    And the country "Czech Republic" has been soft deleted
    And the country "Czech Republic" has no relationships
    When I permanently delete the country "Czech Republic" as an admin
    Then the deletion is successful
    And the country "Czech Republic" is permanently removed from the database

  Scenario: Replace archived country with new country including relationships
    Given the following countries exist:
      | name           | code |
      | Soviet Union   | SUN  |
      | Russia         | RUS  |
    And the country "Soviet Union" has been soft deleted
    And the country "Soviet Union" has 3 team relationships
    When I replace the country "Soviet Union" with "Russia" as an admin
    Then the replacement is successful
    And the country "Russia" has 3 team relationships
    And the country "Soviet Union" has 0 team relationships
