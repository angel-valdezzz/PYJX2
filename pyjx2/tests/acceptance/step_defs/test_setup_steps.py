"""
Step definitions for: features/setup_flow.feature
"""
from __future__ import annotations

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from .conftest import build_mocked_client

scenarios("../features/setup_flow.feature")


# ── Given ─────────────────────────────────────────────────────────────────────

@given(parsers.parse('the test plan "{plan_key}" does not exist'))
def _(ctx, settings, plan_key):
    client = build_mocked_client(settings, [])
    client._test_plan_repo.get.return_value = None
    ctx["client"] = client
    ctx["plan_key"] = plan_key


# ── When ──────────────────────────────────────────────────────────────────────

@when(parsers.parse('I run the setup command for project "{project}" with test plan "{plan_key}"'))
def _(ctx, project, plan_key):
    try:
        result = ctx["client"].setup(
            project_key=project,
            test_plan_key=plan_key,
            execution_summary="Sprint 1 Execution",
            test_set_summary="Sprint 1 Test Set",
            reuse_tests=False,
        )
        ctx["result"] = result
        ctx["error"] = None
    except Exception as e:
        ctx["result"] = None
        ctx["error"] = e


@when("I run the setup command with clone mode")
def _(ctx):
    plan_key = ctx.get("plan_key", "PROJ-1")
    try:
        result = ctx["client"].setup(
            project_key="PROJ",
            test_plan_key=plan_key,
            execution_summary="Sprint 1 Execution",
            test_set_summary="Sprint 1 Test Set",
            reuse_tests=False,
        )
        ctx["result"] = result
        ctx["error"] = None
    except Exception as e:
        ctx["result"] = None
        ctx["error"] = e


@when("I run the setup command with reuse mode")
def _(ctx):
    plan_key = ctx.get("plan_key", "PROJ-1")
    try:
        result = ctx["client"].setup(
            project_key="PROJ",
            test_plan_key=plan_key,
            execution_summary="Sprint 1 Execution",
            test_set_summary="Sprint 1 Test Set",
            reuse_tests=True,
        )
        ctx["result"] = result
        ctx["error"] = None
    except Exception as e:
        ctx["result"] = None
        ctx["error"] = e


@when(parsers.parse('I run the setup command with test plan "{plan_key}"'))
def _(ctx, plan_key):
    try:
        result = ctx["client"].setup(
            project_key="PROJ",
            test_plan_key=plan_key,
            execution_summary="E",
            test_set_summary="S",
        )
        ctx["result"] = result
        ctx["error"] = None
    except Exception as e:
        ctx["result"] = None
        ctx["error"] = e


@when("I run the setup command with a progress callback")
def _(ctx):
    messages = []
    plan_key = ctx.get("plan_key", "PROJ-1")
    ctx["client"].setup(
        project_key="PROJ",
        test_plan_key=plan_key,
        execution_summary="E",
        test_set_summary="S",
        progress_callback=messages.append,
    )
    ctx["progress_messages"] = messages


# ── Then ──────────────────────────────────────────────────────────────────────

@then("a test execution is created")
def _(ctx):
    assert ctx["result"] is not None
    assert ctx["result"].test_execution is not None
    assert ctx["result"].test_execution.key != ""


@then("a test set is created")
def _(ctx):
    assert ctx["result"] is not None
    assert ctx["result"].test_set is not None
    assert ctx["result"].test_set.key != ""


@then("the test set is linked to the test execution")
def _(ctx):
    client = ctx["client"]
    exec_key = ctx["result"].test_execution.key
    set_key = ctx["result"].test_set.key
    client._test_exec_repo.add_test_set.assert_called_once_with(exec_key, set_key)


@then(parsers.parse("{n:d} tests are cloned"))
def _(ctx, n):
    assert len(ctx["result"].cloned) == n


@then("no tests are reused")
def _(ctx):
    assert len(ctx["result"].reused) == 0


@then(parsers.parse("{n:d} tests are reused"))
def _(ctx, n):
    assert len(ctx["result"].reused) == n


@then("no tests are cloned")
def _(ctx):
    assert len(ctx["result"].cloned) == 0


@then("all cloned tests are added to the test set")
def _(ctx):
    client = ctx["client"]
    cloned_keys = set(ctx["result"].cloned)
    add_call = client._test_set_repo.add_tests.call_args
    assert add_call is not None, "add_tests was never called"
    added_keys = set(add_call[0][1])
    assert added_keys == cloned_keys


@then(parsers.parse('a "{error_type}" is raised containing "{message}"'))
def _(ctx, error_type, message):
    assert ctx["error"] is not None, f"Expected a {error_type} but no error was raised"
    assert type(ctx["error"]).__name__ == error_type, (
        f"Expected {error_type}, got {type(ctx['error']).__name__}"
    )
    assert message.lower() in str(ctx["error"]).lower(), (
        f"Expected '{message}' in error message: {ctx['error']}"
    )


@then(parsers.parse("at least {n:d} progress messages are received"))
def _(ctx, n):
    assert len(ctx.get("progress_messages", [])) >= n


@then(parsers.parse("{n:d} tests are processed"))
def _(ctx, n):
    result = ctx["result"]
    assert result is not None
    total = len(result.tests)
    assert total == n, f"Expected {n} tests processed, got {total}"
