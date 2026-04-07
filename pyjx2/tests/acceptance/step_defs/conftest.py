"""
Shared fixtures and step definitions reused across all BDD acceptance tests.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers

from pyjx2.api.client import PyJX2
from pyjx2.domain.entities import Test, TestSet, TestExecution, TestPlan


# ── Mutable context dict shared across all steps in a scenario ───────────────

@pytest.fixture
def ctx() -> dict:
    """Mutable bag passed between Given / When / Then steps."""
    return {}


# ── Entities ─────────────────────────────────────────────────────────────────

@pytest.fixture
def _sample_execution():
    return TestExecution(key="PROJ-30", summary="Sprint 1 Execution", issue_id="100030")


@pytest.fixture
def _sample_test_set():
    return TestSet(key="PROJ-20", summary="Sprint 1 Test Set", issue_id="100020")


@pytest.fixture
def _sample_plan():
    return TestPlan(key="PROJ-1", summary="Sprint 1 Plan", issue_id="100001")


# ── Mock repository builder ───────────────────────────────────────────────────

def build_mocked_client(
    settings,
    plan_tests: list[dict],
    exec_test_keys: Optional[list[str]] = None,
    sample_execution: Optional[TestExecution] = None,
    sample_test_set: Optional[TestSet] = None,
    sample_plan: Optional[TestPlan] = None,
) -> PyJX2:
    """Build a PyJX2 instance with all repositories mocked."""
    execution = sample_execution or TestExecution(
        key="PROJ-30", summary="Sprint 1 Execution", issue_id="100030"
    )
    test_set = sample_test_set or TestSet(
        key="PROJ-20", summary="Sprint 1 Test Set", issue_id="100020"
    )
    plan = sample_plan or TestPlan(key="PROJ-1", summary="Sprint Plan", issue_id="100001")

    all_tests = {
        "PROJ-10": Test(key="PROJ-10", summary="Login flow"),
        "PROJ-11": Test(key="PROJ-11", summary="Logout flow"),
        "PROJ-12": Test(key="PROJ-12", summary="Dashboard load"),
    }

    test_repo = MagicMock()
    test_repo.get.side_effect = lambda k: all_tests.get(k)
    test_repo.create.return_value = Test(key="PROJ-50", summary="Created test")
    clone_counter = [0]

    def _clone(src, proj):
        clone_counter[0] += 1
        return Test(key=f"PROJ-{50 + clone_counter[0]}", summary=f"[Clone] {src}")

    test_repo.clone.side_effect = _clone
    test_repo.update_status.return_value = True
    test_repo.upload_evidence.return_value = True
    test_repo.list_from_execution.return_value = list(all_tests.values())

    test_set_repo = MagicMock()
    test_set_repo.get.return_value = test_set
    test_set_repo.create.return_value = test_set
    test_set_repo.update.return_value = test_set
    test_set_repo.add_tests.return_value = True

    exec_repo = MagicMock()
    exec_repo.get.return_value = execution
    exec_repo.create.return_value = execution
    exec_repo.update.return_value = execution
    exec_repo.add_test_set.return_value = True
    keys = exec_test_keys if exec_test_keys is not None else ["PROJ-10", "PROJ-11", "PROJ-12"]
    exec_repo.get_tests.return_value = [{"key": k} for k in keys]

    plan_repo = MagicMock()
    plan_repo.get.return_value = plan
    plan_repo.get_tests.return_value = plan_tests

    client = PyJX2.__new__(PyJX2)
    client._settings = settings
    client._test_repo = test_repo
    client._test_set_repo = test_set_repo
    client._test_exec_repo = exec_repo
    client._test_plan_repo = plan_repo
    return client


# ── Shared Background step ────────────────────────────────────────────────────

@given("a configured PyJX2 client")
def _(ctx, settings):
    """Build a default client with 2-test plan; overridden by more specific steps."""
    ctx.setdefault("plan_tests", [
        {"key": "PROJ-10", "summary": "Login flow"},
        {"key": "PROJ-11", "summary": "Logout flow"},
    ])
    ctx["client"] = build_mocked_client(settings, ctx["plan_tests"])
    ctx["settings"] = settings


@given(parsers.parse('the test plan "{plan_key}" has {n:d} tests'))
def _(ctx, settings, plan_key, n):
    tests = [
        {"key": f"PROJ-{10 + i}", "summary": f"Test {i}"}
        for i in range(n)
    ]
    ctx["plan_tests"] = tests
    ctx["plan_key"] = plan_key
    ctx["client"] = build_mocked_client(settings, tests)
