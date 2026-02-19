Feature: Fight Tag Management
  As an administrator
  I want to manage tags on fights
  So that fights can be accurately categorised

  # --- Supercategory ---

  Scenario: Creating a fight links supercategory tag to the fight
    Given a valid fight is created with supercategory "singles"
    When I retrieve the fight
    Then the fight has an active supercategory tag with value "singles"
    And the tag has the correct fight_id

  # --- Category tags ---

  Scenario: Add a valid category tag to a singles fight
    Given a singles fight exists
    When I add a category tag "duel" to the fight
    Then the fight has an active category tag with value "duel"

  Scenario: Add a valid category tag to a melee fight
    Given a melee fight exists
    When I add a category tag "5s" to the fight
    Then the fight has an active category tag with value "5s"

  Scenario: Cannot add a melee category to a singles fight
    Given a singles fight exists
    When I add a category tag "5s" to the fight
    Then I receive a 422 validation error

  Scenario: Cannot add a singles category to a melee fight
    Given a melee fight exists
    When I add a category tag "duel" to the fight
    Then I receive a 422 validation error

  Scenario: Cannot add two active category tags to the same fight
    Given a singles fight with an active category tag "duel"
    When I add a second category tag "profight" to the fight
    Then I receive a 422 validation error

  # --- Supercategory immutability ---

  Scenario: Cannot update supercategory tag after fight creation
    Given a singles fight exists
    When I update the supercategory tag to "melee"
    Then I receive a 422 validation error

  # --- Cascade deactivation ---

  Scenario: Changing supercategory deactivates the category tag
    Given a singles fight with an active category tag "duel"
    When I deactivate the supercategory tag
    Then the category tag "duel" is also deactivated

  # --- Gender tags ---

  Scenario: Add a gender tag to a fight
    Given a singles fight exists
    When I add a gender tag "male" to the fight
    Then the fight has an active gender tag with value "male"

  Scenario: Cannot add an invalid gender value
    Given a singles fight exists
    When I add a gender tag "unknown" to the fight
    Then I receive a 422 validation error

  Scenario: Cannot add two active gender tags to the same fight
    Given a singles fight with an active gender tag "male"
    When I add a second gender tag "female" to the fight
    Then I receive a 422 validation error

  # --- Custom tags ---

  Scenario: Add a custom tag to a fight
    Given a singles fight exists
    When I add a custom tag "great technique" to the fight
    Then the fight has a custom tag with value "great technique"

  Scenario: Fight can have multiple custom tags
    Given a singles fight exists
    When I add custom tags "exciting" and "controversial" to the fight
    Then the fight has a custom tag with value "exciting"
    And the fight has a custom tag with value "controversial"

  # --- Deactivate tag ---

  Scenario: Deactivate a category tag on a fight
    Given a singles fight with an active category tag "duel"
    When I deactivate the category tag
    Then the category tag is deactivated
    And the fight's active tags do not include a category tag

  # --- Delete tag ---

  Scenario: Hard delete a tag that has no children
    Given a singles fight with an active gender tag "male"
    When I hard delete the gender tag
    Then the gender tag no longer exists

  Scenario: Cannot delete a tag that has active children
    Given a singles fight with an active category tag "duel"
    When I hard delete the supercategory tag
    Then I receive a 422 validation error
    And the supercategory tag still exists

  # --- Cross-fight access guard ---

  Scenario: Cannot manage a tag via a different fight's endpoint
    Given fight A has an active gender tag
    When I try to deactivate that tag via fight B's endpoint
    Then I receive a 404 error
