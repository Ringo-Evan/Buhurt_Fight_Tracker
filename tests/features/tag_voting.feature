Feature: Tag Voting System
  As a community member
  I want to propose and vote on fight tags
  So that fights are accurately categorized through community consensus

  Background:
    Given the following tag types exist:
      | name        | is_privileged | sort_order |
      | category    | true          | 1          |
      | subcategory | true          | 2          |
      | weapon      | true          | 3          |
      | custom      | false         | 99         |
    And a fight exists with the following details:
      | fight_id | fight_date | location        | created_by |
      | fight-1  | 2024-03-15 | London, UK      | admin-1    |
    And the fight "fight-1" has the following tags:
      | tag_type    | value   |
      | category    | Singles |

  # Happy Path: Successful Tag Change via Voting
  Scenario: Privileged tag change request reaches threshold and is accepted
    Given a tag change request exists with the following details:
      | request_id | fight_id | tag_type | current_value | proposed_value | threshold |
      | req-1      | fight-1  | weapon   | null          | Longsword      | 10        |
    When the following votes are cast on request "req-1":
      | session_id | vote_type |
      | session-1  | for       |
      | session-2  | for       |
      | session-3  | for       |
      | session-4  | for       |
      | session-5  | for       |
      | session-6  | for       |
      | session-7  | for       |
      | session-8  | for       |
      | session-9  | for       |
      | session-10 | for       |
    Then the tag change request "req-1" should have status "accepted"
    And the fight "fight-1" should have a tag with tag_type "weapon" and value "Longsword"
    And the tag change request "req-1" should have resolved_at timestamp set

  # Rejection Path: Not Enough Support
  Scenario: Privileged tag change request fails to reach threshold
    Given a tag change request exists with the following details:
      | request_id | fight_id | tag_type | current_value | proposed_value | threshold |
      | req-2      | fight-1  | weapon   | null          | Longsword      | 10        |
    When the following votes are cast on request "req-2":
      | session_id  | vote_type |
      | session-11  | for       |
      | session-12  | for       |
      | session-13  | for       |
      | session-14  | for       |
      | session-15  | for       |
      | session-16  | against   |
      | session-17  | against   |
      | session-18  | against   |
      | session-19  | against   |
      | session-20  | against   |
    Then the tag change request "req-2" should have status "rejected"
    And the fight "fight-1" should not have a tag with tag_type "weapon"
    And the tag change request "req-2" should have resolved_at timestamp set

  # Tie Scenario: Favor Rejection
  Scenario: Privileged tag change with tied votes is rejected
    Given a tag change request exists with the following details:
      | request_id | fight_id | tag_type | current_value | proposed_value | threshold |
      | req-3      | fight-1  | weapon   | null          | Polearm        | 10        |
    When the following votes are cast on request "req-3":
      | session_id  | vote_type |
      | session-21  | for       |
      | session-22  | for       |
      | session-23  | for       |
      | session-24  | for       |
      | session-25  | for       |
      | session-26  | against   |
      | session-27  | against   |
      | session-28  | against   |
      | session-29  | against   |
      | session-30  | against   |
    Then the tag change request "req-3" should have status "rejected"
    And the fight "fight-1" should not have a tag with tag_type "weapon"

  # Custom Tags: Auto-Accept
  Scenario: Custom tag is immediately accepted without voting
    When a user "user-1" creates a custom tag change request with the following details:
      | fight_id | tag_type | proposed_value        |
      | fight-1  | custom   | awesome spinning move |
    Then the tag change request should have status "accepted"
    And the fight "fight-1" should have a tag with tag_type "custom" and value "awesome spinning move"
    And the tag change request should have votes_for equal to 0
    And the tag change request should have votes_against equal to 0

  # Fraud Prevention: One Vote Per Session
  Scenario: User cannot vote twice on same request with same session
    Given a tag change request exists with the following details:
      | request_id | fight_id | tag_type | current_value | proposed_value   | threshold |
      | req-4      | fight-1  | weapon   | null          | Sword and Shield | 10        |
    And session "session-40" has already voted "for" on request "req-4"
    When session "session-40" attempts to vote "for" on request "req-4"
    Then the vote should be rejected with error "Session has already voted on this request"
    And the tag change request "req-4" should have votes_for equal to 1

  # Concurrent Requests: One Pending Per Tag Type
  Scenario: Cannot create second pending request for same tag type on same fight
    Given a tag change request exists with the following details:
      | request_id | fight_id | tag_type | current_value | proposed_value    | threshold | status  |
      | req-5      | fight-1  | weapon   | null          | Sword and Buckler | 10        | pending |
    When a user "user-2" attempts to create a tag change request with the following details:
      | fight_id | tag_type | proposed_value |
      | fight-1  | weapon   | Polearm        |
    Then the request should be rejected with error "A pending tag change request already exists for this tag type"
    And only 1 pending request should exist for fight "fight-1" and tag_type "weapon"

  # Changing Existing Tag
  Scenario: Changing category tag to new value
    Given the fight "fight-1" has the following tags:
      | tag_type    | value     | tag_id |
      | category    | Singles   | tag-1  |
      | subcategory | Duel      | tag-2  |
      | weapon      | Longsword | tag-3  |
    And a tag change request exists with the following details:
      | request_id | fight_id | tag_type | current_tag_id | proposed_value | threshold |
      | req-6      | fight-1  | category | tag-1          | Team           | 10        |
    When 10 votes "for" are cast on request "req-6"
    Then the tag change request "req-6" should have status "accepted"
    And the fight "fight-1" should have a tag with tag_type "category" and value "Team"
    And the tag "tag-1" should have isDeleted equal to true
    And the tag "tag-2" should have isDeleted equal to true
    And the tag "tag-3" should have isDeleted equal to true

  # Cancellation Path
  Scenario: Tag change request creator cancels their own request
    Given a tag change request exists with the following details:
      | request_id | fight_id | tag_type | proposed_value | threshold | created_by | status  |
      | req-7      | fight-1  | weapon   | Polearm        | 10        | user-3     | pending |
    When user "user-3" cancels tag change request "req-7"
    Then the tag change request "req-7" should have status "cancelled"
    And the tag change request "req-7" should have resolved_at timestamp set
    And no tag with value "Polearm" should exist for fight "fight-1"

  # Cannot Vote on Resolved Requests
  Scenario: Cannot vote on accepted request
    Given a tag change request exists with the following details:
      | request_id | fight_id | tag_type | proposed_value | threshold | status   |
      | req-8      | fight-1  | weapon   | Claymore       | 10        | accepted |
    When session "session-50" attempts to vote "for" on request "req-8"
    Then the vote should be rejected with error "Cannot vote on resolved request"
