Feature: Configuration Loading
  As a pyjx2 user
  I want to configure the tool via files, environment variables, or CLI arguments
  So that I can adapt it to any workflow without repeating credentials

  Scenario: Settings are loaded from a TOML config file
    Given a TOML config file with valid credentials
    When I load settings from that file
    Then the Jira URL is "https://example.atlassian.net"
    And the Xray client ID is "my_client"
    And the setup test plan key is "PROJ-100"
    And the sync status is "PASS"

  Scenario: Settings are loaded from a JSON config file
    Given a JSON config file with valid credentials
    When I load settings from that file
    Then the Jira username is "user@example.com"
    And the Xray client ID is "json_client"
    And the setup reuse_tests is True
    And the sync recursive is False

  Scenario: pyjx2.toml is auto-discovered in the current directory
    Given a "pyjx2.toml" file exists in the current directory
    When I load settings without specifying a file
    Then the Jira URL is "https://discovered.atlassian.net"

  Scenario: pyjx2.json is auto-discovered in the current directory
    Given a "pyjx2.json" file exists in the current directory
    When I load settings without specifying a file
    Then the Jira URL is "https://json-discovered.atlassian.net"

  Scenario: Runtime overrides take precedence over the config file
    Given a TOML config file with valid credentials
    When I load settings from that file with password override "runtime_token"
    Then the Jira password is "runtime_token"
    And the Jira URL is still "https://example.atlassian.net"

  Scenario: Environment variables take precedence over the config file
    Given a TOML config file with valid credentials
    And the environment variable "PYJX2_JIRA_PASSWORD" is set to "env_token"
    When I load settings from that file
    Then the Jira password is "env_token"

  Scenario: Missing required fields raise a descriptive error
    When I load settings with no configuration at all
    Then a "ValueError" is raised
    And the error message mentions "jira.url"
    And the error message mentions "xray.client_id"

  Scenario: Invalid sync status in config fails schema validation
    Given a TOML config file with invalid sync status "NOT_VALID"
    When I load settings from that file
    Then a schema validation error is raised

  Scenario: Missing required jira.username in JSON fails schema validation
    Given a JSON config file missing "username" in the jira section
    When I load settings from that file
    Then a schema validation error is raised
