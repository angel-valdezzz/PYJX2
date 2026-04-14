from __future__ import annotations

from ...domain.entities import Test, TestExecution, TestPlan, TestSet
from ...domain.repositories import (
    TestExecutionRepository,
    TestPlanRepository,
    TestRepository,
    TestSetRepository,
)
from ...domain.value_objects import (
    ExecutionKey,
    ProjectKey,
    Status,
    TestKey,
    TestPlanKey,
    TestSetKey,
    TestType,
)
from ..jira.client import JiraClient
from .client import XrayClient

XRAY_TEST_ISSUE_TYPE = "Test"
XRAY_TEST_SET_ISSUE_TYPE = "Test Set"
XRAY_TEST_EXECUTION_ISSUE_TYPE = "Test Execution"
DEFAULT_TEST_TYPE = TestType.from_value("Manual")


class XrayTestRepository(TestRepository):
    def __init__(self, xray: XrayClient, jira: JiraClient) -> None:
        self._xray = xray
        self._jira = jira

    def get(self, key: TestKey) -> Test | None:
        try:
            issue = self._jira.get_issue(str(key))
            fields = issue.get("fields", {})
            return Test(
                key=issue["key"],
                summary=fields.get("summary", ""),
                test_type=fields.get("issuetype", {}).get("name", "Manual"),
                labels=fields.get("labels", []),
                description=fields.get("description", {})
                .get("content", [{}])[0]
                .get("content", [{}])[0]
                .get("text", "")
                if fields.get("description")
                else None,
                issue_id=issue.get("id"),
            )
        except Exception:
            return None

    def create(
        self,
        project_key: ProjectKey,
        summary: str,
        test_type: TestType = DEFAULT_TEST_TYPE,
        **kwargs,
    ) -> Test:
        fields: dict = {
            "project": {"key": str(project_key)},
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

    def clone(self, source_key: TestKey, target_project_key: ProjectKey) -> Test:
        source = self.get(source_key)
        if not source:
            raise ValueError(f"Source test not found: {source_key}")
        cloned = self.create(
            project_key=target_project_key,
            summary=f"[Clone] {source.summary}",
            labels=source.labels,
        )
        return cloned

    def update_labels(self, key: TestKey, new_labels: list[str]) -> bool:
        try:
            issue = self._jira.get_issue(str(key))
            existing = issue.get("fields", {}).get("labels", [])
            merged = list(set(existing + new_labels))
            self._jira.update_issue(str(key), {"labels": merged})
            return True
        except Exception:
            return False

    def update_status(self, execution_key: ExecutionKey, test_key: TestKey, status: Status) -> bool:
        self._jira.get_issue(str(test_key))
        exec_issue = self._jira.get_issue(str(execution_key))
        exec_id = exec_issue.get("id")

        tests = self._xray.get(f"testexec/{exec_id}/test")
        run_id = None
        if isinstance(tests, list):
            for t in tests:
                if t.get("key") == str(test_key):
                    run_id = t.get("id")
                    break

        if run_id:
            self._xray.put(f"testrun/{run_id}/status", {"status": str(status)})
            return True
        return False

    def upload_evidence(
        self, execution_key: ExecutionKey, test_key: TestKey, file_path: str
    ) -> bool:
        try:
            exec_issue = self._jira.get_issue(str(execution_key))
            exec_id = exec_issue.get("id")
            tests = self._xray.get(f"testexec/{exec_id}/test")
            run_id = None
            if isinstance(tests, list):
                for t in tests:
                    if t.get("key") == str(test_key):
                        run_id = t.get("id")
                        break
            if run_id:
                self._xray.upload_file(f"testrun/{run_id}/attachment", file_path)
                return True
            return False
        except Exception:
            return False

    def clear_evidence(self, execution_key: ExecutionKey, test_key: TestKey) -> bool:
        """Elimina todos los adjuntos existentes en un Test Run."""
        try:
            exec_issue = self._jira.get_issue(str(execution_key))
            exec_id = exec_issue.get("id")
            tests = self._xray.get(f"testexec/{exec_id}/test")
            run_id = None
            if isinstance(tests, list):
                for t in tests:
                    if t.get("key") == str(test_key):
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

    def list_from_execution(self, execution_key: ExecutionKey) -> list[Test]:
        exec_issue = self._jira.get_issue(str(execution_key))
        exec_id = exec_issue.get("id")
        tests_data = self._xray.get(f"testexec/{exec_id}/test")
        result = []
        if isinstance(tests_data, list):
            for t in tests_data:
                result.append(
                    Test(
                        key=t.get("key", ""),
                        summary=t.get("summary", ""),
                        status=t.get("status"),
                        issue_id=t.get("id"),
                    )
                )
        return result


class XrayTestSetRepository(TestSetRepository):
    def __init__(self, xray: XrayClient, jira: JiraClient) -> None:
        self._xray = xray
        self._jira = jira

    def get(self, key: TestSetKey) -> TestSet | None:
        try:
            issue = self._jira.get_issue(str(key))
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

    def create(self, project_key: ProjectKey, summary: str) -> TestSet:
        fields = {
            "project": {"key": str(project_key)},
            "issuetype": {"name": XRAY_TEST_SET_ISSUE_TYPE},
            "summary": summary,
        }
        issue = self._jira.create_issue(fields)
        return TestSet(key=issue["key"], summary=summary, issue_id=issue.get("id"))

    def update(self, key: TestSetKey, **kwargs) -> TestSet:
        fields: dict = {}
        if "summary" in kwargs:
            fields["summary"] = kwargs["summary"]
        if fields:
            self._jira.update_issue(str(key), fields)
        updated = self.get(key)
        if not updated:
            raise ValueError(f"Test set not found after update: {key}")
        return updated

    def add_tests(self, key: TestSetKey, test_keys: list[TestKey]) -> bool:
        issue = self._jira.get_issue(str(key))
        issue_id = issue.get("id")
        self._xray.post(
            f"testset/{issue_id}/test", {"add": [str(test_key) for test_key in test_keys]}
        )
        return True


class XrayTestExecutionRepository(TestExecutionRepository):
    def __init__(self, xray: XrayClient, jira: JiraClient) -> None:
        self._xray = xray
        self._jira = jira

    def get(self, key: ExecutionKey) -> TestExecution | None:
        try:
            issue = self._jira.get_issue(str(key))
            fields = issue.get("fields", {})
            return TestExecution(
                key=issue["key"],
                summary=fields.get("summary", ""),
                issue_id=issue.get("id"),
            )
        except Exception:
            return None

    def create(self, project_key: ProjectKey, summary: str, **kwargs) -> TestExecution:
        fields: dict = {
            "project": {"key": str(project_key)},
            "issuetype": {"name": XRAY_TEST_EXECUTION_ISSUE_TYPE},
            "summary": summary,
        }
        issue = self._jira.create_issue(fields)
        return TestExecution(key=issue["key"], summary=summary, issue_id=issue.get("id"))

    def update(self, key: ExecutionKey, **kwargs) -> TestExecution:
        fields: dict = {}
        if "summary" in kwargs:
            fields["summary"] = kwargs["summary"]
        if fields:
            self._jira.update_issue(str(key), fields)
        updated = self.get(key)
        if not updated:
            raise ValueError(f"Test execution not found after update: {key}")
        return updated

    def add_test_set(self, key: ExecutionKey, test_set_key: TestSetKey) -> bool:
        issue = self._jira.get_issue(str(key))
        exec_id = issue.get("id")
        ts_issue = self._jira.get_issue(str(test_set_key))
        ts_id = ts_issue.get("id")
        self._xray.post(f"testexec/{exec_id}/testset", {"add": [ts_id]})
        return True

    def get_tests(self, key: ExecutionKey) -> list[Test]:
        issue = self._jira.get_issue(str(key))
        exec_id = issue.get("id")
        result = self._xray.get(f"testexec/{exec_id}/test")
        if isinstance(result, list):
            tests_data = result
        elif isinstance(result, dict):
            tests_data = result.get("tests", [])
        else:
            tests_data = []

        return [
            Test(
                key=test_data.get("key", ""),
                summary=test_data.get("summary", ""),
                status=test_data.get("status"),
                issue_id=test_data.get("id"),
            )
            for test_data in tests_data
            if test_data.get("key")
        ]


class XrayTestPlanRepository(TestPlanRepository):
    def __init__(self, xray: XrayClient, jira: JiraClient) -> None:
        self._xray = xray
        self._jira = jira

    def get(self, key: TestPlanKey) -> TestPlan | None:
        try:
            issue = self._jira.get_issue(str(key))
            fields = issue.get("fields", {})
            return TestPlan(
                key=issue["key"],
                summary=fields.get("summary", ""),
                issue_id=issue.get("id"),
            )
        except Exception:
            return None

    def get_tests(self, key: TestPlanKey) -> list[Test]:
        issue = self._jira.get_issue(str(key))
        plan_id = issue.get("id")
        result = self._xray.get(f"testplan/{plan_id}/test")
        if isinstance(result, list):
            tests_data = result
        elif isinstance(result, dict):
            tests_data = result.get("tests", [])
        else:
            tests_data = []

        return [
            Test(
                key=test_data.get("key", ""),
                summary=test_data.get("summary", ""),
                status=test_data.get("status"),
                issue_id=test_data.get("id"),
            )
            for test_data in tests_data
            if test_data.get("key")
        ]
