Feature: Setup Flow
  As a QA engineer
  I want to automate the creation of a Test Execution and Test Set from a Test Plan
  So that I can run tests consistently without manual Jira configuration

  Background:
    Given a configured PyJX2 client
    And the test plan "PROJ-1" has 2 tests

  Scenario: Full setup creates a test execution and a test set
    When I run the setup command for project "PROJ" with test plan "PROJ-1"
    Then a test execution is created
    And a test set is created

  Scenario: The test set is linked to the test execution after setup
    When I run the setup command for project "PROJ" with test plan "PROJ-1"
    Then the test set is linked to the test execution

  Scenario: Setup clones tests by default
    When I run the setup command with clone mode
    Then 2 tests are cloned
    And no tests are reused

  Scenario: Setup reuses existing tests when the flag is enabled
    When I run the setup command with reuse mode
    Then 2 tests are reused
    And no tests are cloned

  Scenario: Cloned tests are added to the test set
    When I run the setup command with clone mode
    Then all cloned tests are added to the test set

  Scenario: Setup fails when the test plan does not exist
    Given the test plan "PROJ-999" does not exist
    When I run the setup command with test plan "PROJ-999"
    Then a "ValueError" is raised containing "not found"

  Scenario: Progress messages are emitted during setup
    When I run the setup command with a progress callback
    Then at least 4 progress messages are received

  Scenario: Empty test plan still produces an execution and a test set
    Given the test plan "PROJ-1" has 0 tests
    When I run the setup command for project "PROJ" with test plan "PROJ-1"
    Then a test execution is created
    And a test set is created
    And 0 tests are processed
