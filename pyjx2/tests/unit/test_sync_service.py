"""Unit tests for SyncService."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pyjx2.application.services.sync_service import SyncService, SyncInput
from pyjx2.domain.entities import Test


class TestSyncServiceFileMatching:
    """Tests for the core file→test matching logic."""

    def _make_service(self, test_keys=None):
        test_repo = MagicMock()
        exec_repo = MagicMock()

        all_tests = {
            "PROJ-10": Test(key="PROJ-10", summary="Login flow"),
            "PROJ-11": Test(key="PROJ-11", summary="Logout flow"),
            "PROJ-12": Test(key="PROJ-12", summary="Register user"),
        }

        def get_side(key):
            return all_tests.get(key)

        test_repo.get.side_effect = get_side
        test_repo.update_status.return_value = True
        test_repo.upload_evidence.return_value = True

        # Use explicit sentinel so callers can pass [] without it being treated as falsy
        keys = ["PROJ-10", "PROJ-11"] if test_keys is None else test_keys
        exec_repo.get_tests.return_value = [{"key": k} for k in keys]

        return SyncService(test_repo, exec_repo), test_repo, exec_repo

    def _run_with_files(self, filenames, test_keys=None, recursive=True):
        svc, test_repo, exec_repo = self._make_service(test_keys)
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            for name in filenames:
                parts = name.split("/")
                if len(parts) > 1:
                    (folder / Path(*parts[:-1])).mkdir(parents=True, exist_ok=True)
                (folder / name).write_text("data")
            return svc.run(
                SyncInput(
                    execution_key="PROJ-200",
                    folder=str(folder),
                    status="PASS",
                    recursive=recursive,
                ),
            ), test_repo

    def test_matches_file_by_test_key_stem(self):
        result, _ = self._run_with_files(["PROJ-10.png"])
        assert len(result.matches) == 1
        assert result.matches[0].test_key == "PROJ-10"

    def test_matches_multiple_files(self):
        result, _ = self._run_with_files(["PROJ-10.png", "PROJ-11.pdf"])
        assert len(result.matches) == 2

    def test_unmatched_files_reported(self):
        result, _ = self._run_with_files(["PROJ-10.png", "unrelated.txt"])
        assert len(result.matches) == 1
        assert len(result.unmatched_files) == 1
        assert any("unrelated.txt" in f for f in result.unmatched_files)

    def test_unmatched_tests_reported(self):
        result, _ = self._run_with_files(["PROJ-10.png"])
        assert "PROJ-11" in result.unmatched_tests

    def test_recursive_finds_nested_files(self):
        result, _ = self._run_with_files(
            ["subdir/PROJ-10.png", "subdir/nested/PROJ-11.pdf"],
            recursive=True,
        )
        assert len(result.matches) == 2

    def test_non_recursive_ignores_nested_files(self):
        result, _ = self._run_with_files(
            ["subdir/PROJ-10.png"],
            recursive=False,
        )
        assert len(result.matches) == 0
        assert len(result.unmatched_tests) == 2

    def test_matching_is_case_insensitive_for_key(self):
        result, _ = self._run_with_files(["proj-10.png"])
        assert len(result.matches) == 1
        assert result.matches[0].test_key == "PROJ-10"

    def test_file_with_no_extension_matches_by_key(self):
        result, _ = self._run_with_files(["PROJ-10"])
        assert len(result.matches) == 1

    def test_empty_folder_produces_no_matches(self):
        result, _ = self._run_with_files([])
        assert len(result.matches) == 0
        assert len(result.unmatched_tests) == 2

    def test_no_tests_in_execution_produces_no_matches(self):
        svc, _, _ = self._make_service(test_keys=[])
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "PROJ-10.png").write_text("data")
            result = svc.run(SyncInput(
                execution_key="PROJ-200",
                folder=tmpdir,
                status="PASS",
            ))
        assert len(result.matches) == 0
        assert len(result.unmatched_files) == 1

    def test_status_update_called_for_each_match(self):
        result, test_repo = self._run_with_files(["PROJ-10.png", "PROJ-11.pdf"])
        assert test_repo.update_status.call_count == 2

    def test_upload_called_for_each_match(self):
        result, test_repo = self._run_with_files(["PROJ-10.png", "PROJ-11.pdf"])
        assert test_repo.upload_evidence.call_count == 2

    def test_match_records_status_and_upload_results(self):
        result, _ = self._run_with_files(["PROJ-10.png"])
        m = result.matches[0]
        assert m.status_updated is True
        assert m.uploaded is True

    def test_failed_status_update_recorded(self):
        svc, test_repo, exec_repo = self._make_service()
        test_repo.update_status.return_value = False
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "PROJ-10.png").write_text("data")
            result = svc.run(SyncInput(
                execution_key="PROJ-200",
                folder=tmpdir,
                status="PASS",
            ))
        assert result.matches[0].status_updated is False

    def test_failed_upload_recorded(self):
        svc, test_repo, exec_repo = self._make_service()
        test_repo.upload_evidence.return_value = False
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "PROJ-10.png").write_text("data")
            result = svc.run(SyncInput(
                execution_key="PROJ-200",
                folder=tmpdir,
                status="PASS",
            ))
        assert result.matches[0].uploaded is False

    def test_nonexistent_folder_raises(self):
        svc, _, _ = self._make_service()
        with pytest.raises(FileNotFoundError):
            svc.run(SyncInput(
                execution_key="PROJ-200",
                folder="/nonexistent/path/that/does/not/exist",
                status="PASS",
            ))

    def test_progress_callback_is_called(self):
        messages = []
        svc, _, _ = self._make_service()
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "PROJ-10.png").write_text("data")
            svc.run(
                SyncInput(execution_key="PROJ-200", folder=tmpdir, status="PASS"),
                progress_callback=messages.append,
            )
        assert len(messages) > 0
