"""
Step definitions for: features/cli_setup.feature and features/cli_sync.feature
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from typer.testing import CliRunner

from pyjx2.cli.app import app
from pyjx2.application.use_cases.setup.models import SetupResult, SetupResultMetrics
from pyjx2.application.services.sync_service import SyncResult, SyncMatch
from pyjx2.domain.entities import Test, TestSet, TestExecution

scenarios("../features/cli_setup.feature")
scenarios("../features/cli_sync.feature")

runner = CliRunner()


# ── Shared CLI result data builders ───────────────────────────────────────────

def _default_setup_result():
    return SetupResult(
        test_executions=[TestExecution(key="PROJ-30", summary="Sprint Exec")],
        test_sets=[TestSet(key="PROJ-20", summary="Sprint Set")],
        tests=[Test(key="PROJ-10", summary="Login test")],
        metrics=SetupResultMetrics(tests_cloned=1, tests_linked=0)
    )


def _default_sync_result(unmatched_tests=0):
    unmatched = [f"PROJ-{99 + i}" for i in range(unmatched_tests)]
    return SyncResult(
        test_execution="PROJ-30",
        processed_tests=2 + unmatched_tests,
        updated_tests=2,
        tests_without_evidence=unmatched,
        files_uploaded=2,
        files_unused=[],
        errors=[]
    )


# ── Base args ──────────────────────────────────────────────────────────────────

BASE_SETUP_ARGS = [
    "--test-plan", "PROJ-1",
    "--execution-summary", "Sprint Exec",
    "--application", "AXA_WEB",
    "--env", "QA",
    "--jira-username", "u@test.com",
    "--password", "token",
]

BASE_SYNC_ARGS = [
    "--execution", "PROJ-30",
    "--folder", "/tmp",
    "--status", "PASS",
    "--env", "QA",
    "--jira-username", "u@test.com",
    "--password", "token",
]


# ── Given ─────────────────────────────────────────────────────────────────────

@given(parsers.parse('the setup API raises a RuntimeError "{message}"'))
def _(ctx, message):
    ctx["setup_api_error"] = RuntimeError(message)


@given("a valid TOML config file")
def _(ctx, valid_toml_config):
    ctx["config_file"] = str(valid_toml_config)


@given(parsers.parse("the sync result has {n:d} unmatched tests"))
def _(ctx, n):
    ctx["sync_result_override"] = _default_sync_result(unmatched_tests=n)


@given("the sync API raises a FileNotFoundError")
def _(ctx):
    ctx["sync_api_error"] = FileNotFoundError("/no/such/folder")


# ── When — setup CLI ──────────────────────────────────────────────────────────

@when('I invoke "pyjx2 setup" with all required arguments')
def _(ctx):
    mock_pjx = MagicMock()
    mock_pjx.setup.return_value = _default_setup_result()
    if ctx.get("setup_api_error"):
        mock_pjx.setup.side_effect = ctx["setup_api_error"]
    with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
        result = runner.invoke(app, ["setup"] + BASE_SETUP_ARGS)
    ctx["cli_result"] = result
    ctx["mock_pjx"] = mock_pjx


@when('I invoke "pyjx2 setup" without "--test-plan"')
def _(ctx):
    args = [a for a in BASE_SETUP_ARGS if a != "--test-plan"]
    ctx["cli_result"] = runner.invoke(app, ["setup"] + args)


@when('I invoke "pyjx2 setup" without "--application"')
def _(ctx):
    args = [a for a in BASE_SETUP_ARGS if a != "--application"]
    ctx["cli_result"] = runner.invoke(app, ["setup"] + args)


@when('I invoke "pyjx2 setup" without "--execution-summary"')
def _(ctx):
    # Eliminamos el flag y su valor correspondiente para asegurar que falte
    args = list(BASE_SETUP_ARGS)
    try:
        idx = args.index("--execution-summary")
        args.pop(idx) # flag
        args.pop(idx) # value
    except ValueError:
        pass
    ctx["cli_result"] = runner.invoke(app, ["setup"] + args)


@when('I invoke "pyjx2 setup" without credentials')
def _(ctx):
    with runner.isolated_filesystem():
        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(app, [
                "setup",
                "--test-plan", "PROJ-1",
                "--execution-summary", "E",
                "--application", "APP",
            ])
    ctx["cli_result"] = result


@when('I invoke "pyjx2 setup" con modo agregar \"--test-mode add\"')
def _(ctx):
    mock_pjx = MagicMock()
    mock_pjx.setup.return_value = _default_setup_result()
    with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
        result = runner.invoke(app, ["setup"] + BASE_SETUP_ARGS + ["--test-mode", "add"])
    ctx["cli_result"] = result
    ctx["mock_pjx"] = mock_pjx


@when('I invoke "pyjx2 setup" with "--config" pointing to that file')
def _(ctx):
    mock_pjx = MagicMock()
    mock_pjx.setup.return_value = _default_setup_result()
    with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
        result = runner.invoke(app, [
            "setup",
            "--config", ctx["config_file"],
            "--test-plan", "PROJ-1",
            "--execution-summary", "E",
            "--application", "A",
        ])
    ctx["cli_result"] = result


# ── When — sync CLI ───────────────────────────────────────────────────────────

@when('I invoke "pyjx2 sync" with all required arguments')
def _(ctx):
    mock_pjx = MagicMock()
    sync_result = ctx.get("sync_result_override") or _default_sync_result()
    
    def sync_side_effect(*args, **kwargs):
        cb = kwargs.get("progress_callback")
        if cb:
            cb("Actualizando PROJ-10 ('Login test') a estado: PASS")
        return sync_result

    if ctx.get("sync_api_error"):
        mock_pjx.sync.side_effect = ctx["sync_api_error"]
    else:
        mock_pjx.sync.side_effect = sync_side_effect
    
    with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
        result = runner.invoke(app, ["sync"] + BASE_SYNC_ARGS)
    ctx["cli_result"] = result
    ctx["mock_pjx"] = mock_pjx


@when('I invoke "pyjx2 sync" without "--execution"')
def _(ctx):
    args = [a for a in BASE_SYNC_ARGS if a != "--execution"]
    ctx["cli_result"] = runner.invoke(app, ["sync"] + args)


@when('I invoke "pyjx2 sync" without "--folder"')
def _(ctx):
    args = [a for a in BASE_SYNC_ARGS if a != "--folder"]
    ctx["cli_result"] = runner.invoke(app, ["sync"] + args)


@when('I invoke "pyjx2 sync" without "--status"')
def _(ctx):
    # En la nueva CLI, status es obligatorio (...). 
    # Typer generara un codigo de error 2 si falta.
    args = [a for a in BASE_SYNC_ARGS if a != "--status"]
    ctx["cli_result"] = runner.invoke(app, ["sync"] + args)


@when(parsers.parse('I invoke "pyjx2 sync" with status "{status}"'))
def _(ctx, status):
    mock_pjx = MagicMock()
    mock_pjx.sync.return_value = _default_sync_result()
    args = BASE_SYNC_ARGS[:]
    idx = args.index("--status") + 1
    args[idx] = status
    with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
        result = runner.invoke(app, ["sync"] + args)
    ctx["cli_result"] = result
    ctx["mock_pjx"] = mock_pjx


@when('I invoke "pyjx2 sync" with "--no-recursive"')
def _(ctx):
    mock_pjx = MagicMock()
    mock_pjx.sync.return_value = _default_sync_result()
    with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
        result = runner.invoke(app, ["sync"] + BASE_SYNC_ARGS + ["--no-recursive"])
    ctx["cli_result"] = result
    ctx["mock_pjx"] = mock_pjx


# ── Then — general ────────────────────────────────────────────────────────────

@then("the exit code is 0")
def _(ctx):
    result = ctx["cli_result"]
    assert result.exit_code == 0, (
        f"Expected exit code 0, got {result.exit_code}.\nOutput:\n{result.output}"
    )


@then("the exit code is not 0")
def _(ctx):
    result = ctx["cli_result"]
    assert result.exit_code != 0, (
        f"Expected non-zero exit code, got 0.\nOutput:\n{result.output}"
    )


@then(parsers.parse('the output contains "{text}"'))
@then(parsers.parse('the output contains the text "{text}"'))
def _(ctx, text):
    assert text in ctx["cli_result"].output, (
        f"Expected '{text}' in output:\n{ctx['cli_result'].output}"
    )

@then(parsers.parse('the output contains the test execution key "{key}"'))
def _(ctx, key):
    assert key in ctx["cli_result"].output, (
        f"Expected '{key}' in output:\n{ctx['cli_result'].output}"
    )

@then(parsers.parse('the output contains the test set key "{key}"'))
def _(ctx, key):
    assert key in ctx["cli_result"].output, (
        f"Expected '{key}' in output:\n{ctx['cli_result'].output}"
    )

@then("the output contains an error message")
def _(ctx):
    output = ctx["cli_result"].output.lower()
    assert any(word in output for word in ("error", "failed", "fail")), (
        f"Expected error message in output:\n{ctx['cli_result'].output}"
    )

@then("the output shows unmatched tests")
def _(ctx):
    # La nueva CLI usa "Tests sin evidencia" o "Archivos No Utilizados"
    # El paso anterior agregó "Unmatched tests found." para compatibilidad
    output = ctx["cli_result"].output
    assert any(x in output for x in ("Tests sin evidencia", "Archivos No Utilizados", "Unmatched tests")), (
        f"Expected unmatched tests info in output:\n{output}"
    )


@then(parsers.parse('the test_mode parameter is "{mode}" in the API call'))
def _(ctx, mode):
    call_kwargs = ctx["mock_pjx"].setup.call_args[1]
    assert call_kwargs.get("test_mode") == mode, (
        f"Expected test_mode='{mode}', got {call_kwargs.get('test_mode')!r}"
    )


@then("the recursive parameter is False in the API call")
def _(ctx):
    call_kwargs = ctx["mock_pjx"].sync.call_args[1]
    assert call_kwargs.get("recursive") is False


@then("the recursive parameter is True in the API call")
def _(ctx):
    call_kwargs = ctx["mock_pjx"].sync.call_args[1]
    assert call_kwargs.get("recursive") is True
