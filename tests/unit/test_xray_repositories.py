from __future__ import annotations

from unittest.mock import MagicMock

from pyjx2.domain.entities import Test
from pyjx2.domain.value_objects import ExecutionKey, Status, TestKey, TestPlanKey
from pyjx2.infrastructure.xray.repositories import (
    XrayTestPlanRepository,
    XrayTestRepository,
)


def test_xray_test_repository_update_status_resolves_test_run_and_calls_xray():
    xray = MagicMock()
    jira = MagicMock()
    jira.get_issue.side_effect = [
        {"id": "2001", "key": "PROJ-10"},
        {"id": "3001", "key": "PROJ-30"},
    ]
    xray.get.return_value = [
        {"key": "PROJ-10", "id": "run-10"},
        {"key": "PROJ-11", "id": "run-11"},
    ]

    repo = XrayTestRepository(xray, jira)

    result = repo.update_status(
        ExecutionKey.from_value("PROJ-30"),
        TestKey.from_value("PROJ-10"),
        Status.from_value("PASS"),
    )

    assert result is True
    xray.put.assert_called_once_with("testrun/run-10/status", {"status": "PASS"})


def test_xray_test_repository_clear_evidence_deletes_each_attachment():
    xray = MagicMock()
    jira = MagicMock()
    jira.get_issue.return_value = {"id": "3001", "key": "PROJ-30"}
    xray.get.side_effect = [
        [{"key": "PROJ-10", "id": "run-10"}],
        [{"id": "att-1"}, {"id": "att-2"}],
    ]

    repo = XrayTestRepository(xray, jira)

    result = repo.clear_evidence(
        ExecutionKey.from_value("PROJ-30"),
        TestKey.from_value("PROJ-10"),
    )

    assert result is True
    xray.delete.assert_any_call("attachment/att-1")
    xray.delete.assert_any_call("attachment/att-2")


def test_xray_test_plan_repository_maps_dict_payloads_to_domain_tests():
    xray = MagicMock()
    jira = MagicMock()
    jira.get_issue.return_value = {"id": "5001", "key": "PROJ-1"}
    xray.get.return_value = {
        "tests": [
            {"key": "PROJ-10", "summary": "Login flow", "status": "TODO", "id": "10010"},
            {"key": "PROJ-11", "summary": "Logout flow", "status": "PASS", "id": "10011"},
        ]
    }

    repo = XrayTestPlanRepository(xray, jira)

    tests = repo.get_tests(TestPlanKey.from_value("PROJ-1"))

    assert tests == [
        Test(key="PROJ-10", summary="Login flow", status="TODO", issue_id="10010"),
        Test(key="PROJ-11", summary="Logout flow", status="PASS", issue_id="10011"),
    ]
