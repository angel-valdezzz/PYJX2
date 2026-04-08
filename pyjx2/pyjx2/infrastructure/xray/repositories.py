from __future__ import annotations

from pathlib import Path
from typing import Optional

from ...domain.entities import Test, TestSet, TestExecution, TestPlan
from ...domain.repositories import (
    TestRepository,
    TestSetRepository,
    TestExecutionRepository,
    TestPlanRepository,
)
from .client import XrayClient
from ..jira.client import JiraClient


XRAY_TEST_ISSUE_TYPE = "Test"
XRAY_TEST_SET_ISSUE_TYPE = "Test Set"
XRAY_TEST_EXECUTION_ISSUE_TYPE = "Test Execution"


class XrayTestRepository(TestRepository):
    def __init__(self, xray: XrayClient, jira: JiraClient) -> None:
        self._xray = xray
        self._jira = jira

    def get(self, key: str) -> Optional[Test]:
        try:
            issue = self._jira.get_issue(key)
            fields = issue.get("fields", {})
            return Test(
                key=issue["key"],
                summary=fields.get("summary", ""),
                test_type=fields.get("issuetype", {}).get("name", "Manual"),
                labels=fields.get("labels", []),
                description=fields.get("description", {}).get("content", [{}])[0].get("content", [{}])[0].get("text", "") if fields.get("description") else None,
                issue_id=issue.get("id"),
            )
        except Exception:
            return None

    def create(self, project_key: str, summary: str, test_type: str = "Manual", **kwargs) -> Test:
        fields: dict = {
            "project": {"key": project_key},
            "issuetype": {"name": XRAY_TEST_ISSUE_TYPE},
            "summary": summary,
        }
        if kwargs.get("labels"):
            fields["labels"] = kwargs["labels"]
        issue = self._jira.create_issue(fields)
        return Test(
            key=issue["key"],
            summary=summary,
            test_type=test_type,
            issue_id=issue.get("id"),
        )

    def clone(self, source_key: str, target_project_key: str) -> Test:
        source = self.get(source_key)
        if not source:
            raise ValueError(f"Source test not found: {source_key}")
        cloned = self.create(
            project_key=target_project_key,
            summary=f"[Clone] {source.summary}",
            labels=source.labels,
        )
        return cloned

    def update_labels(self, key: str, new_labels: list[str]) -> bool:
        try:
            issue = self._jira.get_issue(key)
            existing = issue.get("fields", {}).get("labels", [])
            merged = list(set(existing + new_labels))
            self._jira.update_issue(key, {"labels": merged})
            return True
        except Exception:
            return False

    def update_status(self, execution_key: str, test_key: str, status: str) -> bool:
        issue = self._jira.get_issue(test_key)
        test_id = issue.get("id")
        exec_issue = self._jira.get_issue(execution_key)
        exec_id = exec_issue.get("id")

        tests = self._xray.get(f"testexec/{exec_id}/test")
        run_id = None
        if isinstance(tests, list):
            for t in tests:
                if t.get("key") == test_key:
                    run_id = t.get("id")
                    break

        if run_id:
            self._xray.put(f"testrun/{run_id}/status", {"status": status})
            return True
        return False

    def upload_evidence(self, execution_key: str, test_key: str, file_path: str) -> bool:
        try:
            exec_issue = self._jira.get_issue(execution_key)
            exec_id = exec_issue.get("id")
            tests = self._xray.get(f"testexec/{exec_id}/test")
            run_id = None
            if isinstance(tests, list):
                for t in tests:
                    if t.get("key") == test_key:
                        run_id = t.get("id")
                        break
            if run_id:
                self._xray.upload_file(f"testrun/{run_id}/attachment", file_path)
                return True
            return False
        except Exception:
            return False

    def clear_evidence(self, execution_key: str, test_key: str) -> bool:
        """Elimina todos los adjuntos existentes en un Test Run."""
        try:
            exec_issue = self._jira.get_issue(execution_key)
            exec_id = exec_issue.get("id")
            tests = self._xray.get(f"testexec/{exec_id}/test")
            run_id = None
            if isinstance(tests, list):
                for t in tests:
                    if t.get("key") == test_key:
                        run_id = t.get("id")
                        break
            
            if not run_id:
                return False

            # Obtener adjuntos actuales
            attachments = self._xray.get(f"testrun/{run_id}/attachment")
            if isinstance(attachments, list):
                for att in attachments:
                    att_id = att.get("id")
                    if att_id:
                        self._xray.delete(f"attachment/{att_id}")
            return True
        except Exception:
            return False

    def list_from_execution(self, execution_key: str) -> list[Test]:
        exec_issue = self._jira.get_issue(execution_key)
        exec_id = exec_issue.get("id")
        tests_data = self._xray.get(f"testexec/{exec_id}/test")
        result = []
        if isinstance(tests_data, list):
            for t in tests_data:
                result.append(Test(
                    key=t.get("key", ""),
                    summary=t.get("summary", ""),
                    status=t.get("status"),
                    issue_id=t.get("id"),
                ))
        return result


class XrayTestSetRepository(TestSetRepository):
    def __init__(self, xray: XrayClient, jira: JiraClient) -> None:
        self._xray = xray
        self._jira = jira

    def get(self, key: str) -> Optional[TestSet]:
        try:
            issue = self._jira.get_issue(key)
            fields = issue.get("fields", {})
            issue_id = issue.get("id")
            tests_data = self._xray.get(f"testset/{issue_id}/test")
            test_keys = []
            if isinstance(tests_data, dict):
                test_keys = [t.get("key") for t in tests_data.get("tests", [])]
            elif isinstance(tests_data, list):
                test_keys = [t.get("key") for t in tests_data]
            return TestSet(
                key=issue["key"],
                summary=fields.get("summary", ""),
                issue_id=issue_id,
                test_keys=test_keys,
            )
        except Exception:
            return None

    def create(self, project_key: str, summary: str) -> TestSet:
        fields = {
            "project": {"key": project_key},
            "issuetype": {"name": XRAY_TEST_SET_ISSUE_TYPE},
            "summary": summary,
        }
        issue = self._jira.create_issue(fields)
        return TestSet(key=issue["key"], summary=summary, issue_id=issue.get("id"))

    def update(self, key: str, **kwargs) -> TestSet:
        fields: dict = {}
        if "summary" in kwargs:
            fields["summary"] = kwargs["summary"]
        if fields:
            self._jira.update_issue(key, fields)
        updated = self.get(key)
        if not updated:
            raise ValueError(f"Test set not found after update: {key}")
        return updated

    def add_tests(self, key: str, test_keys: list[str]) -> bool:
        issue = self._jira.get_issue(key)
        issue_id = issue.get("id")
        self._xray.post(f"testset/{issue_id}/test", {"add": test_keys})
        return True


class XrayTestExecutionRepository(TestExecutionRepository):
    def __init__(self, xray: XrayClient, jira: JiraClient) -> None:
        self._xray = xray
        self._jira = jira

    def get(self, key: str) -> Optional[TestExecution]:
        try:
            issue = self._jira.get_issue(key)
            fields = issue.get("fields", {})
            return TestExecution(
                key=issue["key"],
                summary=fields.get("summary", ""),
                issue_id=issue.get("id"),
            )
        except Exception:
            return None

    def create(self, project_key: str, summary: str, **kwargs) -> TestExecution:
        fields: dict = {
            "project": {"key": project_key},
            "issuetype": {"name": XRAY_TEST_EXECUTION_ISSUE_TYPE},
            "summary": summary,
        }
        issue = self._jira.create_issue(fields)
        return TestExecution(key=issue["key"], summary=summary, issue_id=issue.get("id"))

    def update(self, key: str, **kwargs) -> TestExecution:
        fields: dict = {}
        if "summary" in kwargs:
            fields["summary"] = kwargs["summary"]
        if fields:
            self._jira.update_issue(key, fields)
        updated = self.get(key)
        if not updated:
            raise ValueError(f"Test execution not found after update: {key}")
        return updated

    def add_test_set(self, key: str, test_set_key: str) -> bool:
        issue = self._jira.get_issue(key)
        exec_id = issue.get("id")
        ts_issue = self._jira.get_issue(test_set_key)
        ts_id = ts_issue.get("id")
        self._xray.post(f"testexec/{exec_id}/testset", {"add": [ts_id]})
        return True

    def get_tests(self, key: str) -> list[dict]:
        issue = self._jira.get_issue(key)
        exec_id = issue.get("id")
        result = self._xray.get(f"testexec/{exec_id}/test")
        if isinstance(result, list):
            return result
        return result.get("tests", []) if isinstance(result, dict) else []


class XrayTestPlanRepository(TestPlanRepository):
    def __init__(self, xray: XrayClient, jira: JiraClient) -> None:
        self._xray = xray
        self._jira = jira

    def get(self, key: str) -> Optional[TestPlan]:
        try:
            issue = self._jira.get_issue(key)
            fields = issue.get("fields", {})
            return TestPlan(
                key=issue["key"],
                summary=fields.get("summary", ""),
                issue_id=issue.get("id"),
            )
        except Exception:
            return None

    def get_tests(self, key: str) -> list[dict]:
        issue = self._jira.get_issue(key)
        plan_id = issue.get("id")
        result = self._xray.get(f"testplan/{plan_id}/test")
        if isinstance(result, list):
            return result
        return result.get("tests", []) if isinstance(result, dict) else []
