from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from pyjx2.api.client import PyJX2
from pyjx2.domain.entities import Test
from .conftest import build_mocked_client

scenarios("../features/sync_flow.feature")


# ── Given ─────────────────────────────────────────────────────────────────────

@given(parsers.parse('a test execution "{exec_key}" with tests "PROJ-10" (Login), "PROJ-11" (Logout), "PROJ-12" (Register)'))
def _(ctx, settings, exec_key):
    ctx["exec_key"] = exec_key
    # Mapeo explícito para que el mock devuelva tests con estos summaries
    ctx["test_defs"] = [
        Test(key="PROJ-10", summary="Login flow"),
        Test(key="PROJ-11", summary="Logout flow"),
        Test(key="PROJ-12", summary="Register user"),
    ]
    ctx["client"] = build_mocked_client(
        settings, [], exec_test_keys=["PROJ-10", "PROJ-11", "PROJ-12"]
    )
    # Sobrescribir el mock para que devuelva los objetos Test con summary
    ctx["client"]._test_exec_repo.list_from_execution.return_value = ctx["test_defs"]


@given(parsers.parse('an evidence folder with files "{file1}" and "{file2}"'))
def _(ctx, file1, file2):
    tmpdir = tempfile.mkdtemp()
    ctx.setdefault("_tmpdirs", []).append(tmpdir)
    folder = Path(tmpdir)
    (folder / file1).write_text("evidence data")
    (folder / file2).write_text("evidence data")
    ctx["folder"] = str(folder)


@given(parsers.parse('an evidence folder with files "{file1}" only'))
def _(ctx, file1):
    tmpdir = tempfile.mkdtemp()
    ctx.setdefault("_tmpdirs", []).append(tmpdir)
    folder = Path(tmpdir)
    (folder / file1).write_text("evidence data")
    ctx["folder"] = str(folder)


@given(parsers.parse('an evidence folder with files "{file1}"'))
def _(ctx, file1):
    tmpdir = tempfile.mkdtemp()
    ctx.setdefault("_tmpdirs", []).append(tmpdir)
    folder = Path(tmpdir)
    (folder / file1).write_text("evidence data")
    ctx["folder"] = str(folder)


@given(parsers.parse('an evidence folder with a nested file "{nested_path}"'))
def _(ctx, nested_path):
    tmpdir = tempfile.mkdtemp()
    ctx.setdefault("_tmpdirs", []).append(tmpdir)
    folder = Path(tmpdir)
    nested = folder / nested_path
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_text("evidence data")
    ctx["folder"] = str(folder)


@given("an empty evidence folder")
def _(ctx):
    tmpdir = tempfile.mkdtemp()
    ctx.setdefault("_tmpdirs", []).append(tmpdir)
    ctx["folder"] = tmpdir


# ── When ──────────────────────────────────────────────────────────────────────

@when(parsers.parse('I run the sync command for execution "{exec_key}" with status "{status}"'))
def _(ctx, exec_key, status):
    folder = ctx.get("folder", tempfile.mkdtemp())
    try:
        result = ctx["client"].sync(
            execution_key=exec_key,
            folder=folder,
            status=status,
            recursive=True,
        )
        ctx["sync_result"] = result
        ctx["sync_error"] = None
    except Exception as e:
        ctx["sync_result"] = None
        ctx["sync_error"] = e


@when("I run the sync command with recursive mode enabled")
def _(ctx):
    folder = ctx.get("folder", tempfile.mkdtemp())
    exec_key = ctx.get("exec_key", "PROJ-30")
    try:
        result = ctx["client"].sync(
            execution_key=exec_key,
            folder=folder,
            status="PASS",
            recursive=True,
        )
        ctx["sync_result"] = result
        ctx["sync_error"] = None
    except Exception as e:
        ctx["sync_result"] = None
        ctx["sync_error"] = e


@when("I run the sync command with recursive mode disabled")
def _(ctx):
    folder = ctx.get("folder", tempfile.mkdtemp())
    exec_key = ctx.get("exec_key", "PROJ-30")
    try:
        result = ctx["client"].sync(
            execution_key=exec_key,
            folder=folder,
            status="PASS",
            recursive=False,
        )
        ctx["sync_result"] = result
        ctx["sync_error"] = None
    except Exception as e:
        ctx["sync_result"] = None
        ctx["sync_error"] = e


@when(parsers.parse('I run the sync command with folder "{folder_path}"'))
def _(ctx, folder_path):
    exec_key = ctx.get("exec_key", "PROJ-30")
    try:
        result = ctx["client"].sync(
            execution_key=exec_key,
            folder=folder_path,
            status="PASS",
        )
        ctx["sync_result"] = result
        ctx["sync_error"] = None
    except Exception as e:
        ctx["sync_result"] = None
        ctx["sync_error"] = e


# ── Then ──────────────────────────────────────────────────────────────────────

@then(parsers.parse("{n:d} tests are matched"))
def _(ctx, n):
    result = ctx["sync_result"]
    assert result is not None, f"Sync failed with: {ctx.get('sync_error')}"
    # updated_tests representa cuántos tests únicos tuvieron matches
    assert result.updated_tests == n, (
        f"Expected {n} matches, got {result.updated_tests}"
    )


@then(parsers.parse('the matched tests are "{key1}" and "{key2}"'))
def _(ctx, key1, key2):
    # En el nuevo SyncResult no guardamos la lista de matches directos por key, 
    # pero podemos inferir por tests_without_evidence
    without = ctx["sync_result"].tests_without_evidence
    assert key1 not in without, f"{key1} matches not found"
    assert key2 not in without, f"{key2} matches not found"


@then(parsers.parse('the status "{status}" is set for all matched tests'))
def _(ctx, status):
    client = ctx["client"]
    calls = client._test_repo.update_status.call_args_list
    assert len(calls) > 0, "update_status was never called"
    for call in calls:
        actual_status = call[0][2]
        assert actual_status == status, f"Expected status {status}, got {actual_status}"


@then("evidence is uploaded for all matched tests")
def _(ctx):
    result = ctx["sync_result"]
    assert result.files_uploaded > 0


@then(parsers.parse('"{key}" is matched'))
def _(ctx, key):
    without = ctx["sync_result"].tests_without_evidence
    assert key not in without, f"{key} was not matched"


@then(parsers.parse('"{key}" is not matched'))
def _(ctx, key):
    without = ctx["sync_result"].tests_without_evidence
    assert key in without, f"{key} was matched but should not be"


@then(parsers.parse('the unmatched tests include "{key1}" and "{key2}"'))
def _(ctx, key1, key2):
    unmatched = ctx["sync_result"].tests_without_evidence
    assert key1 in unmatched, f"{key1} not in tests_without_evidence: {unmatched}"
    assert key2 in unmatched, f"{key2} not in tests_without_evidence: {unmatched}"


@then(parsers.parse('the unmatched files include "{filename}"'))
def _(ctx, filename):
    unmatched_files = ctx["sync_result"].files_unused
    assert any(filename in f for f in unmatched_files), (
        f"'{filename}' not found in unmatched files: {unmatched_files}"
    )


@then(parsers.parse("all {n:d} tests are unmatched"))
def _(ctx, n):
    result = ctx["sync_result"]
    assert len(result.tests_without_evidence) == n, (
        f"Expected {n} unmatched tests, got {len(result.tests_without_evidence)}"
    )


@then(parsers.parse('a "{error_type}" is raised'))
def _(ctx, error_type):
    error = ctx.get("sync_error")
    assert error is not None, f"Expected {error_type} but no error was raised"
    assert type(error).__name__ == error_type, (
        f"Expected {error_type}, got {type(error).__name__}: {error}"
    )
