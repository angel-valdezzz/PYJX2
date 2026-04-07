"""
Acceptance tests for CLI commands (setup, sync).
Uses typer's test runner and mocks the PyJX2 API layer.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from pyjx2.cli.app import app
from pyjx2.application.services.setup_service import SetupResult
from pyjx2.application.services.sync_service import SyncResult, SyncMatch
from pyjx2.domain.entities import Test, TestSet, TestExecution


runner = CliRunner()

# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_setup_result():
    return SetupResult(
        test_execution=TestExecution(key="PROJ-30", summary="Sprint Exec"),
        test_set=TestSet(key="PROJ-20", summary="Sprint Set"),
        tests=[Test(key="PROJ-10", summary="Login test")],
        reused=[],
        created=[],
        cloned=["PROJ-10"],
    )


def _make_sync_result(num_matches=2, unmatched_tests=0, unmatched_files=1):
    matches = [
        SyncMatch(
            test_key=f"PROJ-{10 + i}",
            test_summary=f"Test {i}",
            file_path=f"/tmp/PROJ-{10 + i}.png",
            uploaded=True,
            status_updated=True,
        )
        for i in range(num_matches)
    ]
    return SyncResult(
        matches=matches,
        unmatched_tests=[f"PROJ-{99 + i}" for i in range(unmatched_tests)],
        unmatched_files=["/tmp/extra.txt"] * unmatched_files,
    )


REQUIRED_SETUP_ARGS = [
    "--project", "PROJ",
    "--test-plan", "PROJ-1",
    "--execution-summary", "Sprint Exec",
    "--test-set-summary", "Sprint Set",
    "--jira-url", "https://test.atlassian.net",
    "--jira-username", "u@test.com",
    "--jira-token", "token",
    "--xray-client-id", "cid",
    "--xray-client-secret", "csec",
]

REQUIRED_SYNC_ARGS = [
    "--execution", "PROJ-30",
    "--folder", "/tmp",
    "--status", "PASS",
    "--jira-url", "https://test.atlassian.net",
    "--jira-username", "u@test.com",
    "--jira-token", "token",
    "--xray-client-id", "cid",
    "--xray-client-secret", "csec",
]


# ── Help ───────────────────────────────────────────────────────────────────────

class TestHelpCommands:
    def test_root_help_exits_zero(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_root_help_lists_all_commands(self):
        result = runner.invoke(app, ["--help"])
        assert "setup" in result.output
        assert "sync" in result.output
        assert "tui" in result.output

    def test_setup_help_shows_required_options(self):
        result = runner.invoke(app, ["setup", "--help"])
        assert result.exit_code == 0
        assert "--project" in result.output
        assert "--test-plan" in result.output
        assert "--execution-summary" in result.output

    def test_sync_help_shows_required_options(self):
        result = runner.invoke(app, ["sync", "--help"])
        assert result.exit_code == 0
        assert "--execution" in result.output
        assert "--folder" in result.output
        assert "--status" in result.output


# ── Setup command ──────────────────────────────────────────────────────────────

class TestSetupCommand:
    def _mock_pjx2(self, result=None):
        mock = MagicMock()
        mock.setup.return_value = result or _make_setup_result()
        return mock

    def test_setup_exits_zero_on_success(self):
        mock_pjx = self._mock_pjx2()
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            result = runner.invoke(app, ["setup"] + REQUIRED_SETUP_ARGS)
        assert result.exit_code == 0

    def test_setup_output_contains_execution_key(self):
        mock_pjx = self._mock_pjx2()
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            result = runner.invoke(app, ["setup"] + REQUIRED_SETUP_ARGS)
        assert "PROJ-30" in result.output

    def test_setup_output_contains_test_set_key(self):
        mock_pjx = self._mock_pjx2()
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            result = runner.invoke(app, ["setup"] + REQUIRED_SETUP_ARGS)
        assert "PROJ-20" in result.output

    def test_setup_output_shows_summary_table(self):
        mock_pjx = self._mock_pjx2()
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            result = runner.invoke(app, ["setup"] + REQUIRED_SETUP_ARGS)
        assert "Test Execution" in result.output
        assert "Test Set" in result.output

    def test_setup_missing_project_exits_nonzero(self):
        args = [a for a in REQUIRED_SETUP_ARGS if a not in ("--project", "PROJ")]
        result = runner.invoke(app, ["setup"] + args)
        assert result.exit_code != 0

    def test_setup_missing_test_plan_exits_nonzero(self):
        args = [a for a in REQUIRED_SETUP_ARGS if a not in ("--test-plan", "PROJ-1")]
        result = runner.invoke(app, ["setup"] + args)
        assert result.exit_code != 0

    def test_setup_missing_credentials_exits_nonzero(self):
        result = runner.invoke(app, [
            "setup",
            "--project", "PROJ",
            "--test-plan", "PROJ-1",
            "--execution-summary", "E",
            "--test-set-summary", "S",
        ])
        assert result.exit_code != 0

    def test_setup_api_exception_exits_nonzero(self):
        mock_pjx = self._mock_pjx2()
        mock_pjx.setup.side_effect = RuntimeError("Jira connection failed")
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            result = runner.invoke(app, ["setup"] + REQUIRED_SETUP_ARGS)
        assert result.exit_code != 0
        assert "failed" in result.output.lower() or "error" in result.output.lower()

    def test_setup_reuse_tests_flag_passed_to_api(self):
        mock_pjx = self._mock_pjx2()
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            runner.invoke(app, ["setup"] + REQUIRED_SETUP_ARGS + ["--reuse-tests"])
        call_kwargs = mock_pjx.setup.call_args[1]
        assert call_kwargs.get("reuse_tests") is True

    def test_setup_clone_tests_is_default(self):
        mock_pjx = self._mock_pjx2()
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            runner.invoke(app, ["setup"] + REQUIRED_SETUP_ARGS)
        call_kwargs = mock_pjx.setup.call_args[1]
        assert call_kwargs.get("reuse_tests") is False

    def test_setup_passes_correct_project_key_to_api(self):
        mock_pjx = self._mock_pjx2()
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            runner.invoke(app, ["setup"] + REQUIRED_SETUP_ARGS)
        call_kwargs = mock_pjx.setup.call_args[1]
        assert call_kwargs.get("project_key") == "PROJ"

    def test_setup_with_explicit_config_file(self, valid_toml_config):
        mock_pjx = self._mock_pjx2()
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            result = runner.invoke(app, [
                "setup",
                "--config", str(valid_toml_config),
                "--project", "PROJ",
                "--test-plan", "PROJ-1",
                "--execution-summary", "E",
                "--test-set-summary", "S",
            ])
        assert result.exit_code == 0


# ── Sync command ───────────────────────────────────────────────────────────────

class TestSyncCommand:
    def _mock_pjx2(self, result=None):
        mock = MagicMock()
        mock.sync.return_value = result or _make_sync_result()
        return mock

    def test_sync_exits_zero_on_success(self):
        mock_pjx = self._mock_pjx2()
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            result = runner.invoke(app, ["sync"] + REQUIRED_SYNC_ARGS)
        assert result.exit_code == 0

    def test_sync_output_shows_match_table(self):
        mock_pjx = self._mock_pjx2()
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            result = runner.invoke(app, ["sync"] + REQUIRED_SYNC_ARGS)
        assert "PROJ-10" in result.output

    def test_sync_missing_execution_exits_nonzero(self):
        args = [a for a in REQUIRED_SYNC_ARGS if a not in ("--execution", "PROJ-30")]
        result = runner.invoke(app, ["sync"] + args)
        assert result.exit_code != 0

    def test_sync_missing_folder_exits_nonzero(self):
        args = [a for a in REQUIRED_SYNC_ARGS if a not in ("--folder", "/tmp")]
        result = runner.invoke(app, ["sync"] + args)
        assert result.exit_code != 0

    def test_sync_invalid_status_exits_nonzero(self):
        args = REQUIRED_SYNC_ARGS[:]
        idx = args.index("--status") + 1
        args[idx] = "INVALID_STATUS"
        result = runner.invoke(app, ["sync"] + args)
        assert result.exit_code != 0

    def test_sync_valid_statuses_accepted(self):
        for status in ("PASS", "FAIL", "TODO", "EXECUTING", "ABORTED"):
            mock_pjx = self._mock_pjx2()
            with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
                args = REQUIRED_SYNC_ARGS[:]
                idx = args.index("--status") + 1
                args[idx] = status
                result = runner.invoke(app, ["sync"] + args)
            assert result.exit_code == 0, f"Status {status} should be accepted"

    def test_sync_file_not_found_exits_nonzero(self):
        mock_pjx = self._mock_pjx2()
        mock_pjx.sync.side_effect = FileNotFoundError("/no/such/folder")
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            result = runner.invoke(app, ["sync"] + REQUIRED_SYNC_ARGS)
        assert result.exit_code != 0

    def test_sync_api_exception_exits_nonzero(self):
        mock_pjx = self._mock_pjx2()
        mock_pjx.sync.side_effect = RuntimeError("Connection refused")
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            result = runner.invoke(app, ["sync"] + REQUIRED_SYNC_ARGS)
        assert result.exit_code != 0

    def test_sync_unmatched_tests_shown_in_output(self):
        mock_pjx = self._mock_pjx2(result=_make_sync_result(unmatched_tests=2))
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            result = runner.invoke(app, ["sync"] + REQUIRED_SYNC_ARGS)
        assert "Unmatched tests" in result.output

    def test_sync_no_matches_does_not_show_table(self):
        mock_pjx = self._mock_pjx2(result=_make_sync_result(num_matches=0))
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            result = runner.invoke(app, ["sync"] + REQUIRED_SYNC_ARGS)
        assert result.exit_code == 0

    def test_sync_passes_correct_execution_key(self):
        mock_pjx = self._mock_pjx2()
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            runner.invoke(app, ["sync"] + REQUIRED_SYNC_ARGS)
        call_kwargs = mock_pjx.sync.call_args[1]
        assert call_kwargs.get("execution_key") == "PROJ-30"

    def test_sync_passes_recursive_flag(self):
        mock_pjx = self._mock_pjx2()
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            runner.invoke(app, ["sync"] + REQUIRED_SYNC_ARGS + ["--no-recursive"])
        call_kwargs = mock_pjx.sync.call_args[1]
        assert call_kwargs.get("recursive") is False

    def test_sync_recursive_is_default(self):
        mock_pjx = self._mock_pjx2()
        with patch("pyjx2.cli.app.PyJX2", return_value=mock_pjx):
            runner.invoke(app, ["sync"] + REQUIRED_SYNC_ARGS)
        call_kwargs = mock_pjx.sync.call_args[1]
        assert call_kwargs.get("recursive") is True
