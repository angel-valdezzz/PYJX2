Feature: CLI Setup Command
  As a QA engineer
  I want to run the setup command from the terminal
  So that I can create test infrastructure without writing Python scripts

  Scenario: Setup command succeeds with all required arguments
    When I invoke "pyjx2 setup" with all required arguments
    Then the exit code is 0
    And the output contains the test execution key "PROJ-30"
    And the output contains the test set key "PROJ-20"

  Scenario: Setup command shows a summary table
    When I invoke "pyjx2 setup" with all required arguments
    Then the exit code is 0
    And the output contains "Test Execution"
    And the output contains "Test Set"

  Scenario: Setup command fails when --project is missing
    When I invoke "pyjx2 setup" without "--project"
    Then the exit code is not 0

  Scenario: Setup command fails when --test-plan is missing
    When I invoke "pyjx2 setup" without "--test-plan"
    Then the exit code is not 0

  Scenario: Setup command fails when --execution-summary is missing
    When I invoke "pyjx2 setup" without "--execution-summary"
    Then the exit code is not 0

  Scenario: Setup command fails when Jira credentials are missing
    When I invoke "pyjx2 setup" without credentials
    Then the exit code is not 0

  Scenario: Setup command uses --reuse-tests flag
    When I invoke "pyjx2 setup" with "--reuse-tests"
    Then the reuse_tests parameter is True in the API call

  Scenario: Setup command defaults to clone mode
    When I invoke "pyjx2 setup" with all required arguments
    Then the reuse_tests parameter is False in the API call

  Scenario: Setup command fails gracefully when API raises an error
    Given the setup API raises a RuntimeError "Jira connection failed"
    When I invoke "pyjx2 setup" with all required arguments
    Then the exit code is not 0
    And the output contains an error message

  Scenario: Setup command accepts an explicit config file
    Given a valid TOML config file
    When I invoke "pyjx2 setup" with "--config" pointing to that file
    Then the exit code is 0
