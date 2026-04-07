"""
Acceptance tests for the full sync flow.
These tests validate the complete sync pipeline with a real filesystem
and mock repositories.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pyjx2.api.client import PyJX2
from pyjx2.domain.entities import Test


class TestSyncFlowEndToEnd:
    """Full sync flow via the PyJX2 public API with real filesystem."""

    def _build_client(self, settings, test_keys, test_data=None):
        """Build a PyJX2 client with mocked repositories."""
        test_repo = MagicMock()
        exec_repo = MagicMock()

        default_tests = {
            "PROJ-10": Test(key="PROJ-10", summary="Login flow"),
            "PROJ-11": Test(key="PROJ-11", summary="Logout flow"),
            "PROJ-12": Test(key="PROJ-12", summary="Dashboard load"),
        }
        tests = test_data or default_tests

        test_repo.get.side_effect = lambda k: tests.get(k)
        test_repo.update_status.return_value = True
        test_repo.upload_evidence.return_value = True

        exec_repo.get_tests.return_value = [{"key": k} for k in test_keys]

        client = PyJX2.__new__(PyJX2)
        client._settings = settings
        client._test_repo = test_repo
        client._test_set_repo = MagicMock()
        client._test_exec_repo = exec_repo
        client._test_plan_repo = MagicMock()

        return client, test_repo, exec_repo

    def test_matches_files_to_tests_and_updates_status(self, settings, evidence_folder):
        client, test_repo, _ = self._build_client(
            settings, ["PROJ-10", "PROJ-11", "PROJ-12"]
        )
        result = client.sync(
            execution_key="PROJ-30",
            folder=str(evidence_folder),
            status="PASS",
            recursive=True,
        )
        matched_keys = {m.test_key for m in result.matches}
        assert "PROJ-10" in matched_keys
        assert "PROJ-11" in matched_keys

    def test_matched_tests_have_status_updated(self, settings, evidence_folder):
        client, test_repo, _ = self._build_client(
            settings, ["PROJ-10", "PROJ-11", "PROJ-12"]
        )
        client.sync(
            execution_key="PROJ-30",
            folder=str(evidence_folder),
            status="FAIL",
            recursive=True,
        )
        calls = test_repo.update_status.call_args_list
        statuses = [c[0][2] for c in calls]
        assert all(s == "FAIL" for s in statuses)

    def test_matched_tests_have_evidence_uploaded(self, settings, evidence_folder):
        client, test_repo, _ = self._build_client(
            settings, ["PROJ-10", "PROJ-11", "PROJ-12"]
        )
        result = client.sync(
            execution_key="PROJ-30",
            folder=str(evidence_folder),
            status="PASS",
            recursive=True,
        )
        assert all(m.uploaded for m in result.matches)

    def test_recursive_scan_picks_up_nested_file(self, settings, evidence_folder):
        client, test_repo, _ = self._build_client(
            settings, ["PROJ-10", "PROJ-11", "PROJ-12"]
        )
        result = client.sync(
            execution_key="PROJ-30",
            folder=str(evidence_folder),
            status="PASS",
            recursive=True,
        )
        matched_keys = {m.test_key for m in result.matches}
        assert "PROJ-12" in matched_keys

    def test_non_recursive_does_not_pick_up_nested_file(self, settings, evidence_folder):
        client, test_repo, _ = self._build_client(
            settings, ["PROJ-10", "PROJ-11", "PROJ-12"]
        )
        result = client.sync(
            execution_key="PROJ-30",
            folder=str(evidence_folder),
            status="PASS",
            recursive=False,
        )
        matched_keys = {m.test_key for m in result.matches}
        assert "PROJ-12" not in matched_keys

    def test_unmatched_tests_are_reported(self, settings, evidence_folder):
        client, _, _ = self._build_client(
            settings, ["PROJ-10", "PROJ-11", "PROJ-12"]
        )
        result = client.sync(
            execution_key="PROJ-30",
            folder=str(evidence_folder),
            status="PASS",
            recursive=False,
        )
        assert "PROJ-12" in result.unmatched_tests

    def test_unmatched_files_are_reported(self, settings, evidence_folder):
        client, _, _ = self._build_client(settings, ["PROJ-10", "PROJ-11", "PROJ-12"])
        result = client.sync(
            execution_key="PROJ-30",
            folder=str(evidence_folder),
            status="PASS",
            recursive=True,
        )
        unmatched = " ".join(result.unmatched_files)
        assert "unrelated-file.txt" in unmatched

    def test_progress_callback_receives_messages(self, settings, evidence_folder):
        messages = []
        client, _, _ = self._build_client(settings, ["PROJ-10", "PROJ-11"])
        client.sync(
            execution_key="PROJ-30",
            folder=str(evidence_folder),
            status="PASS",
            recursive=True,
            progress_callback=messages.append,
        )
        assert len(messages) > 0

    def test_nonexistent_folder_raises_file_not_found(self, settings):
        client, _, _ = self._build_client(settings, ["PROJ-10"])
        with pytest.raises(FileNotFoundError):
            client.sync(
                execution_key="PROJ-30",
                folder="/tmp/this_folder_does_not_exist_pyjx2",
                status="PASS",
            )

    def test_empty_folder_produces_empty_result(self, settings):
        client, _, _ = self._build_client(settings, ["PROJ-10", "PROJ-11"])
        with tempfile.TemporaryDirectory() as tmpdir:
            result = client.sync(
                execution_key="PROJ-30",
                folder=tmpdir,
                status="PASS",
            )
        assert result.matches == []
        assert len(result.unmatched_tests) == 2

    def test_all_tests_matched_leaves_no_unmatched_tests(self, settings):
        client, _, _ = self._build_client(settings, ["PROJ-10", "PROJ-11"])
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            (folder / "PROJ-10.png").write_text("data")
            (folder / "PROJ-11.pdf").write_text("data")
            result = client.sync(
                execution_key="PROJ-30",
                folder=tmpdir,
                status="PASS",
            )
        assert result.unmatched_tests == []
        assert len(result.matches) == 2
