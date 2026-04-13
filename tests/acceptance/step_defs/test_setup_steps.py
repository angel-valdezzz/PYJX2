"""
Step definitions for: features/setup_flow.feature
"""
from __future__ import annotations

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from pyjx2.domain.entities import Test

from .conftest import build_mocked_client

scenarios("../features/setup_flow.feature")


# ── Dado ──────────────────────────────────────────────────────────────────────

@given(parsers.parse('que el plan de pruebas "{plan_key}" no existe'))
def _(ctx, settings, plan_key):
    client = build_mocked_client(settings, [])
    client._test_plan_repo.get.return_value = None
    ctx["client"] = client
    ctx["plan_key"] = plan_key

@given(parsers.parse('que el plan de pruebas "{plan_key}" tiene {n:d} pruebas'))
def _(ctx, settings, plan_key, n):
    tests = [Test(key=f"PROJ-{i+10}", summary=f"Test {i}") for i in range(n)]
    client = build_mocked_client(settings, tests)
    ctx["client"] = client
    ctx["plan_key"] = plan_key

@given(parsers.parse('el plan de pruebas "{plan_key}" tiene {n:d} pruebas'))
def _(ctx, settings, plan_key, n):
    tests = [Test(key=f"PROJ-{i+10}", summary=f"Test {i}") for i in range(n)]
    client = build_mocked_client(settings, tests)
    ctx["client"] = client
    ctx["plan_key"] = plan_key

@given("un cliente PyJX2 configurado")
def _(ctx, settings):
    tests = [Test(key="PROJ-10", summary="Login flow"), Test(key="PROJ-11", summary="Logout flow")]
    client = build_mocked_client(settings, tests)
    ctx["client"] = client

# ── Cuando ────────────────────────────────────────────────────────────────────

@when(parsers.parse('ejecuto el comando setup con test plan "{plan_key}" y aplicacion "{application}"'))
def _(ctx, plan_key, application):
    try:
        result = ctx["client"].setup(
            test_plan_key=plan_key,
            execution_summary="Sprint 1 Execution",
            application=application,
        )
        ctx["result"] = result
        ctx["error"] = None
    except Exception as e:
        ctx["result"] = None
        ctx["error"] = e


@when("ejecuto el comando setup con modo de clonacion")
def _(ctx):
    plan_key = ctx.get("plan_key", "PROJ-1")
    try:
        result = ctx["client"].setup(
            test_plan_key=plan_key,
            execution_summary="Sprint 1 Execution",
            application="AXA_WEB",
            test_mode="clone",
        )
        ctx["result"] = result
        ctx["error"] = None
    except Exception as e:
        ctx["result"] = None
        ctx["error"] = e


@when("ejecuto el comando setup con modo de agregar")
def _(ctx):
    plan_key = ctx.get("plan_key", "PROJ-1")
    try:
        result = ctx["client"].setup(
            test_plan_key=plan_key,
            execution_summary="Sprint 1 Execution",
            application="AXA_WEB",
            test_mode="add",
        )
        ctx["result"] = result
        ctx["error"] = None
    except Exception as e:
        ctx["result"] = None
        ctx["error"] = e


@when(parsers.parse('ejecuto el comando setup con test plan "{plan_key}"'))
def _(ctx, plan_key):
    try:
        result = ctx["client"].setup(
            test_plan_key=plan_key,
            execution_summary="E",
            application="APP",
        )
        ctx["result"] = result
        ctx["error"] = None
    except Exception as e:
        ctx["result"] = None
        ctx["error"] = e


@when("ejecuto el comando setup con un callback de progreso")
def _(ctx):
    messages = []
    plan_key = ctx.get("plan_key", "PROJ-1")
    ctx["client"].setup(
        test_plan_key=plan_key,
        execution_summary="E",
        application="APP",
        progress_callback=messages.append,
    )
    ctx["progress_messages"] = messages


# ── Entonces ──────────────────────────────────────────────────────────────────

@then("se crea una ejecución de pruebas")
def _(ctx):
    assert ctx.get("error") is None, f"Encountered error: {ctx.get('error')}"
    assert ctx["result"] is not None
    assert ctx["result"].test_executions is not None
    assert len(ctx["result"].test_executions) > 0
    assert ctx["result"].test_executions[0].key != ""


@then("se crea un test set")
def _(ctx):
    assert ctx["result"] is not None
    assert ctx["result"].test_sets is not None
    assert len(ctx["result"].test_sets) > 0
    assert ctx["result"].test_sets[0].key != ""


@then("el test set queda enlazado a la ejecución de pruebas")
def _(ctx):
    client = ctx["client"]
    exec_key = ctx["result"].test_executions[0].key
    set_key = ctx["result"].test_sets[0].key
    assert client._test_exec_repo.add_test_set.call_count >= 1


@then(parsers.parse("{n:d} pruebas son clonadas"))
def _(ctx, n):
    assert ctx.get("error") is None, f"Encountered error: {ctx.get('error')}"
    assert ctx["result"].metrics.tests_cloned == n


@then(parsers.parse("{n:d} pruebas son reusadas"))
def _(ctx, n):
    assert ctx.get("error") is None, f"Encountered error: {ctx.get('error')}"
    assert ctx["result"].metrics.tests_linked == n


@then("todas las pruebas clonadas se agregan al test set")
def _(ctx):
    client = ctx["client"]
    add_call = client._test_set_repo.add_tests.call_args
    assert add_call is not None, "add_tests was never called"
    
    added_keys = set(add_call[0][1])
    assert len(added_keys) == ctx["result"].metrics.tests_cloned


@then(parsers.parse('se lanza una excepción de tipo "{error_type}" conteniendo "{message}"'))
def _(ctx, error_type, message):
    assert ctx["error"] is not None, f"Expected a {error_type} but no error was raised"
    assert type(ctx["error"]).__name__ == error_type, (
        f"Expected {error_type}, got {type(ctx['error']).__name__}"
    )
    assert message.lower() in str(ctx["error"]).lower(), (
        f"Expected '{message}' in error message: {ctx['error']}"
    )


@then(parsers.parse("al menos {n:d} mensajes de progreso son recibidos"))
def _(ctx, n):
    assert len(ctx.get("progress_messages", [])) >= n


@then(parsers.parse("{n:d} pruebas son procesadas"))
def _(ctx, n):
    result = ctx["result"]
    assert result is not None
    total = len(result.tests)
    assert total == n, f"Expected {n} tests processed, got {total}"
