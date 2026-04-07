Feature: CLI Sync Command
  As a QA engineer
  I want to run the sync command from the terminal
  So that I can automatically match evidence files to test results

  Scenario: Sync command succeeds with all required arguments
    When I invoke "pyjx2 sync" with all required arguments
    Then the exit code is 0

  Scenario: Sync command output shows matched tests table
    When I invoke "pyjx2 sync" with all required arguments
    Then the exit code is 0
    And the output contains "PROJ-10"

  Scenario: Sync command fails when --execution is missing
    When I invoke "pyjx2 sync" without "--execution"
    Then the exit code is not 0

  Scenario: Sync command fails when --folder is missing
    When I invoke "pyjx2 sync" without "--folder"
    Then the exit code is not 0

  Scenario: Sync command fails when --status is missing
    When I invoke "pyjx2 sync" without "--status"
    Then the exit code is not 0

  Scenario: Sync command rejects an invalid status value
    When I invoke "pyjx2 sync" with status "INVALID_STATUS"
    Then the exit code is not 0

  Scenario Outline: Sync command accepts all valid status values
    When I invoke "pyjx2 sync" with status "<status>"
    Then the exit code is 0

    Examples:
      | status     |
      | PASS       |
      | FAIL       |
      | TODO       |
      | EXECUTING  |
      | ABORTED    |

  Scenario: Sync command fails gracefully when folder is not found
    Given the sync API raises a FileNotFoundError
    When I invoke "pyjx2 sync" with all required arguments
    Then the exit code is not 0

  Scenario: Sync command shows unmatched tests in output
    Given the sync result has 2 unmatched tests
    When I invoke "pyjx2 sync" with all required arguments
    Then the output contains "Unmatched tests"

  Scenario: Sync command passes --no-recursive flag to the API
    When I invoke "pyjx2 sync" with "--no-recursive"
    Then the recursive parameter is False in the API call

  Scenario: Sync command defaults to recursive mode
    When I invoke "pyjx2 sync" with all required arguments
    Then the recursive parameter is True in the API call
