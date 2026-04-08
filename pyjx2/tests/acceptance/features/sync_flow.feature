Feature: Sync Flow
  As a QA engineer
  I want to match evidence files to test cases in a test execution
  So that I can automatically upload results and update test statuses

  Background:
    Given a configured PyJX2 client
    And a test execution "PROJ-30" with tests "PROJ-10" (Login), "PROJ-11" (Logout), "PROJ-12" (Register)

  Scenario: Files matching test summary prefixes are matched
    Given an evidence folder with files "Login flow.png" and "Logout flow.pdf"
    When I run the sync command for execution "PROJ-30" with status "PASS"
    Then 2 tests are matched
    And the matched tests are "PROJ-10" and "PROJ-11"

  Scenario: Matched tests have their status updated
    Given an evidence folder with files "Login flow.png" and "Logout flow.pdf"
    When I run the sync command for execution "PROJ-30" with status "FAIL"
    Then the status "FAIL" is set for all matched tests

  Scenario: Matched tests have their evidence uploaded
    Given an evidence folder with files "Login flow.png" and "Logout flow.pdf"
    When I run the sync command for execution "PROJ-30" with status "PASS"
    Then evidence is uploaded for all matched tests

  Scenario: Recursive scan picks up files in subdirectories
    Given an evidence folder with a nested file "subdir/Register user.png"
    When I run the sync command with recursive mode enabled
    Then "PROJ-12" is matched

  Scenario: Non-recursive scan ignores files in subdirectories
    Given an evidence folder with a nested file "subdir/Register user.png"
    When I run the sync command with recursive mode disabled
    Then "PROJ-12" is not matched

  Scenario: Unmatched tests are reported
    Given an evidence folder with files "Login flow.png" only
    When I run the sync command for execution "PROJ-30" with status "PASS"
    Then the unmatched tests include "PROJ-11" and "PROJ-12"

  Scenario: Unmatched files are reported
    Given an evidence folder with files "Login flow.png" and "unrelated.txt"
    When I run the sync command for execution "PROJ-30" with status "PASS"
    Then the unmatched files include "unrelated.txt"

  Scenario: Empty evidence folder produces no matches
    Given an empty evidence folder
    When I run the sync command for execution "PROJ-30" with status "PASS"
    Then 0 tests are matched
    And all 3 tests are unmatched

  Scenario: Sync fails when the evidence folder does not exist
    When I run the sync command with folder "/nonexistent/path/for/pyjx2"
    Then a "FileNotFoundError" is raised

  Scenario: File matching is case-insensitive for summaries
    Given an evidence folder with files "login flow.png"
    When I run the sync command for execution "PROJ-30" with status "PASS"
    Then "PROJ-10" is matched
