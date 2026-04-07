"""
Step definitions for: features/cli_setup.feature and features/cli_sync.feature
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from typer.testing import CliRunner

from pyjx2.cli.app import app
from pyjx2.application.services.setup_service import SetupResult
from pyjx2.application.services.sync_service import SyncResult, SyncMatch
from pyjx2.domain.entities import Test, TestSet, TestExecution

scenarios("../features/cli_setup.feature")
scenarios("../features/cli_sync.feature")

runner = CliRunner()


# ── Shared CLI result data builders ───────────────────────────────────────────

def _default_setup_result():
    return SetupResult(
        test_execution=TestExecution(key="PROJ-30", summary="Sprint Exec"),
        test_set=TestSet(key="PROJ-20", summary="Sprint Set"),
        tests=[Test(key="PROJ-10", summary="Login test")],
        reused=[],
        created=[],
        cloned=["PROJ-10"],
    )


def _default_sync_result(unmatched_tests=0):
    matches = [
        SyncMatch(
            test_key="PROJ-10",
            test_summary="Login flow",
            file_path="/tmp/PROJ-10.png",
            uploaded=True,
            status_updated=True,
        ),
        SyncMatch(
            test_key="PROJ-11",
            test_summary="Logout flow",
            file_path="/tmp/PROJ-11.pdf",
            uploaded=True,
            status_updated=True,
        ),
    ]
    unmatched = [f"PROJ-{99 + i}" for i in range(unmatched_tests)]
    return SyncResult(matches=matches, unmatched_tests=unmatched, unmatched_files=[])


# ── Base args ──────────────────────────────────────────────────────────────────

BASE_SETUP_ARGS = [
    "--project", "PROJ",
    "--test-plan", "PROJ-1",
    "--execution-summary", "Sprint Exec",
    "--test-set-summary", "Sprint Set",
    "--jira-url", "https://test.atlassian.net",
    "--jira-username", "u@test.com",
    "--password", "token",
    "--xray-client-id", "cid",
    "--xray-client-secret", "csec",
]

BASE_SYNC_ARGS = [
    "--execution", "PROJ-30",
    "--folder", "/tmp",
    "--status", "PASS",
    "--jira-url", "https://test.atlassian.net",
    "--jira-username", "u@test.com",
    "--password", "token",
    "--xray-client-id", "cid",
    "--xray-client-secret", "csec",
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


@when('I invoke "pyjx2 setup" without "--project"')
def _(ctx):
    args = [a for a in BASE_SETUP_ARGS if a not in ("--project", "PROJ")]
    ctx["cli_result"] = runner.invoke(app, ["setup"] + args)


@when('I invoke "pyjx2 setup" without "--test-plan"')
def _(ctx):
    args = [a for a in BASE_SETUP_ARGS if a not in ("--test-plan", "PROJ-1")]
    ctx["cli_result"] = runner.invoke(app, ["setup"] + args)


@when('I invoke "pyjx2 setup" without "--execution-summary"')
def _(ctx):
    args = [a for a in BASE_SETUP_ARGS if a not in ("--execution-summary", "Sprint Exec")]
    ctx["cli_result"] = runner.invoke(app, ["setup"] + args)


@when('I invoke "pyjx2 setup" without credentials')
def _(ctx):
    result = runner.invoke(app, [
        "setup",
        "--project", "PROJ",
        "--test-plan", "PROJ-1",
        "--execution-summary", "E",
        "--test-set-summary", "S",
    ])
    ctx["cli_result"] = result


@when('I invoke "pyjx2 setup" with "--reuse-tests"')
def _(ctx):
    mock_pjx = MagicMock()
    mock_pjx.setup.return_value = _default_setup_result()
    with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
        result = runner.invoke(app, ["setup"] + BASE_SETUP_ARGS + ["--reuse-tests"])
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
            "--project", "PROJ",
            "--test-plan", "PROJ-1",
            "--execution-summary", "E",
            "--test-set-summary", "S",
        ])
    ctx["cli_result"] = result


# ── When — sync CLI ───────────────────────────────────────────────────────────

@when('I invoke "pyjx2 sync" with all required arguments')
def _(ctx):
    mock_pjx = MagicMock()
    sync_result = ctx.get("sync_result_override") or _default_sync_result()
    if ctx.get("sync_api_error"):
        mock_pjx.sync.side_effect = ctx["sync_api_error"]
    else:
        mock_pjx.sync.return_value = sync_result
    with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
        result = runner.invoke(app, ["sync"] + BASE_SYNC_ARGS)
    ctx["cli_result"] = result
    ctx["mock_pjx"] = mock_pjx


@when('I invoke "pyjx2 sync" without "--execution"')
def _(ctx):
    args = [a for a in BASE_SYNC_ARGS if a not in ("--execution", "PROJ-30")]
    ctx["cli_result"] = runner.invoke(app, ["sync"] + args)


@when('I invoke "pyjx2 sync" without "--folder"')
def _(ctx):
    args = [a for a in BASE_SYNC_ARGS if a not in ("--folder", "/tmp")]
    ctx["cli_result"] = runner.invoke(app, ["sync"] + args)


@when('I invoke "pyjx2 sync" without "--status"')
def _(ctx):
    args = [a for a in BASE_SYNC_ARGS if a not in ("--status", "PASS")]
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


@then(parsers.parse('the output contains "{text}"'))
def _(ctx, text):
    assert text in ctx["cli_result"].output, (
        f"Expected '{text}' in output:\n{ctx['cli_result'].output}"
    )


@then("the output contains an error message")
def _(ctx):
    output = ctx["cli_result"].output.lower()
    assert any(word in output for word in ("error", "failed", "fail")), (
        f"Expected error message in output:\n{ctx['cli_result'].output}"
    )


@then("the reuse_tests parameter is True in the API call")
def _(ctx):
    call_kwargs = ctx["mock_pjx"].setup.call_args[1]
    assert call_kwargs.get("reuse_tests") is True


@then("the reuse_tests parameter is False in the API call")
def _(ctx):
    call_kwargs = ctx["mock_pjx"].setup.call_args[1]
    assert call_kwargs.get("reuse_tests") is False


@then("the recursive parameter is False in the API call")
def _(ctx):
    call_kwargs = ctx["mock_pjx"].sync.call_args[1]
    assert call_kwargs.get("recursive") is False


@then("the recursive parameter is True in the API call")
def _(ctx):
    call_kwargs = ctx["mock_pjx"].sync.call_args[1]
    assert call_kwargs.get("recursive") is True
