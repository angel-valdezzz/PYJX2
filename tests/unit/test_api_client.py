"""Unit tests for PyJX2 API boundary coercion."""
from __future__ import annotations

from unittest.mock import MagicMock

from pyjx2.api.client import PyJX2
from pyjx2.domain.entities import Test, TestExecution, TestPlan, TestSet
from pyjx2.domain.value_objects import (
    ExecutionKey,
    ProjectKey,
    Status,
    TestKey,
    TestPlanKey,
    TestSetKey,
    TestType,
)
from pyjx2.infrastructure.config.settings import AuthSettings, ProjectSettings, Settings


def _build_client() -> PyJX2:
    client = PyJX2.__new__(PyJX2)
    client._settings = Settings(
        auth=AuthSettings(env="QA", username="user@test.com", password="token"),
        project=ProjectSettings(key="PROJ"),
    )
    client._test_repo = MagicMock()
    client._test_set_repo = MagicMock()
    client._test_exec_repo = MagicMock()
    client._test_plan_repo = MagicMock()
    return client


def test_create_and_clone_test_coerce_string_arguments():
    client = _build_client()

    client.create_test(" qax ", "Login flow", test_type=" manual ")
    client.clone_test(" qax-1 ", " qax ")

    client._test_repo.create.assert_called_once_with(
        project_key=ProjectKey.from_value("QAX"),
        summary="Login flow",
        test_type=TestType.from_value("Manual"),
        labels=[],
    )
    client._test_repo.clone.assert_called_once_with(
        TestKey.from_value("QAX-1"),
        ProjectKey.from_value("QAX"),
    )


def test_setup_and_sync_accept_string_inputs_and_coerce_early():
    client = _build_client()

    client._test_plan_repo.get.return_value = TestPlan(key="PROJ-100", summary="Plan")
    client._test_plan_repo.get_tests.return_value = [{"key": "PROJ-1"}]
    client._test_exec_repo.create.return_value = TestExecution(key="PROJ-200", summary="Exec")
    client._test_set_repo.create.return_value = TestSet(key="PROJ-300", summary="Set")
    client._test_repo.clone.return_value = Test(key="PROJ-400", summary="Clone")
    client._test_repo.list_from_execution.return_value = []

    client.setup(
        test_plan_key=" qax-100 ",
        execution_summary="Sprint 1",
        application=" axa_web ",
    )
    client.sync(
        execution_key=" qax-200 ",
        folder=".",
        status=" pass ",
        status_overrides={" qax-1 ": " fail "},
        upload_mode="REPLACE",
    )

    client._test_plan_repo.get.assert_called_once_with(TestPlanKey.from_value("QAX-100"))
    client._test_repo.clone.assert_called_once_with(
        TestKey.from_value("PROJ-1"),
        ProjectKey.from_value("PROJ"),
    )
    client._test_repo.list_from_execution.assert_called_once_with(ExecutionKey.from_value("QAX-200"))


def test_mutation_methods_coerce_keys_and_statuses():
    client = _build_client()

    client.update_test_status(" qax-200 ", " qax-1 ", " pass ")
    client.add_tests_to_set(" qax-300 ", [" qax-1 ", " qax-2 "])
    client.add_test_set_to_execution(" qax-200 ", " qax-300 ")
    client.get_tests_from_plan(" qax-100 ")

    client._test_repo.update_status.assert_called_once_with(
        ExecutionKey.from_value("QAX-200"),
        TestKey.from_value("QAX-1"),
        Status.from_value("PASS"),
    )
    client._test_set_repo.add_tests.assert_called_once_with(
        TestSetKey.from_value("QAX-300"),
        [TestKey.from_value("QAX-1"), TestKey.from_value("QAX-2")],
    )
    client._test_exec_repo.add_test_set.assert_called_once_with(
        ExecutionKey.from_value("QAX-200"),
        TestSetKey.from_value("QAX-300"),
    )
    client._test_plan_repo.get_tests.assert_called_once_with(TestPlanKey.from_value("QAX-100"))
