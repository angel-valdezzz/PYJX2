"""Unit tests for SyncService."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pyjx2.application.services.sync_service import SyncInput, SyncService
from pyjx2.domain.entities import Test
from pyjx2.domain.value_objects import ExecutionKey, Status, TestKey


class TestSyncServiceFileMatching:
    """Tests for the core file→test matching logic (prefix_summary)."""

    def _make_service(self, tests=None):
        test_repo = MagicMock()

        # Default tests if none provided
        if tests is None:
            tests = [
                Test(key="PROJ-10", summary="Login flow"),
                Test(key="PROJ-11", summary="Logout flow"),
            ]

        test_repo.update_status.return_value = True
        test_repo.upload_evidence.return_value = True
        test_repo.list_from_execution.return_value = tests
        test_repo.clear_evidence.return_value = True

        return SyncService(test_repo), test_repo

    def _run_with_files(
        self, filenames, tests=None, recursive=True, extensions=None, overrides=None
    ):
        svc, test_repo = self._make_service(tests)
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
                    default_status="PASS",
                    status_overrides=overrides or {},
                    allowed_extensions=extensions,
                    recursive=recursive,
                ),
            ), test_repo

    def test_matches_file_by_summary_prefix(self):
        # "Login flow.png" should match test with summary "Login flow"
        result, _ = self._run_with_files(["Login flow.png"])
        assert result.updated_tests == 1
        assert result.files_uploaded == 1
        assert len(result.files_unused) == 0

    def test_matches_multiple_files_for_same_test(self):
        # Multiple files starting with the same summary prefix
        result, test_repo = self._run_with_files(["Login flow_1.png", "Login flow_2.jpg"])
        assert result.updated_tests == 1
        assert result.files_uploaded == 2
        assert test_repo.upload_evidence.call_count == 2

    def test_matching_is_case_insensitive(self):
        result, _ = self._run_with_files(["login flow.png"])
        assert result.updated_tests == 1

    def test_documented_key_matching_is_not_supported_by_current_algorithm(self):
        # Docs mention key-based matching, but the current implementation only uses summary prefix.
        result, test_repo = self._run_with_files(["PROJ-10.png"])
        assert result.updated_tests == 0
        assert TestKey.from_value("PROJ-10") in result.tests_without_evidence
        assert "PROJ-10.png" in result.files_unused
        assert test_repo.upload_evidence.call_count == 0

    def test_documented_summary_normalization_is_not_supported_by_current_algorithm(self):
        # Docs mention normalized matching, but underscores currently break the prefix check.
        result, test_repo = self._run_with_files(["Login_Flow.png"])
        assert result.updated_tests == 0
        assert TestKey.from_value("PROJ-10") in result.tests_without_evidence
        assert "Login_Flow.png" in result.files_unused
        assert test_repo.upload_evidence.call_count == 0

    def test_matching_is_accent_sensitive(self):
        tests = [Test(key="PROJ-20", summary="Validacion login")]
        result, test_repo = self._run_with_files(
            ["Validación login.png"],
            tests=tests,
        )
        assert result.updated_tests == 0
        assert TestKey.from_value("PROJ-20") in result.tests_without_evidence
        assert "Validación login.png" in result.files_unused
        assert test_repo.upload_evidence.call_count == 0

    def test_extra_spaces_break_match_without_normalization(self):
        result, test_repo = self._run_with_files(["Login  flow.png"])
        assert result.updated_tests == 0
        assert TestKey.from_value("PROJ-10") in result.tests_without_evidence
        assert "Login  flow.png" in result.files_unused
        assert test_repo.upload_evidence.call_count == 0

    def test_unmatched_files_reported(self):
        result, _ = self._run_with_files(["Login flow.png", "random_file.txt"])
        assert result.updated_tests == 1
        assert len(result.files_unused) == 1
        assert "random_file.txt" in result.files_unused

    def test_tests_without_evidence_reported(self):
        result, _ = self._run_with_files(["Login flow.png"])
        assert TestKey.from_value("PROJ-11") in result.tests_without_evidence

    def test_recursive_finds_nested_files(self):
        result, _ = self._run_with_files(
            ["subdir/Login flow.png"],
            recursive=True,
        )
        assert result.updated_tests == 1

    def test_non_recursive_ignores_nested_files(self):
        result, test_repo = self._run_with_files(
            ["subdir/Login flow.png"],
            recursive=False,
        )
        assert result.updated_tests == 0
        assert TestKey.from_value("PROJ-10") in result.tests_without_evidence
        assert test_repo.upload_evidence.call_count == 0

    def test_duplicate_filenames_in_different_folders_upload_independently(self):
        result, test_repo = self._run_with_files(
            ["chrome/Login flow.png", "firefox/Login flow.png"],
            recursive=True,
        )
        assert result.updated_tests == 1
        assert result.files_uploaded == 2
        assert test_repo.upload_evidence.call_count == 2

    def test_ambiguous_summaries_match_the_same_file_to_multiple_tests(self):
        tests = [
            Test(key="PROJ-10", summary="Login"),
            Test(key="PROJ-11", summary="Login flow"),
        ]
        result, test_repo = self._run_with_files(
            ["Login flow.png"],
            tests=tests,
        )

        assert result.updated_tests == 2
        assert result.files_uploaded == 2
        test_repo.update_status.assert_any_call(
            ExecutionKey.from_value("PROJ-200"),
            TestKey.from_value("PROJ-10"),
            Status.from_value("PASS"),
        )
        test_repo.update_status.assert_any_call(
            ExecutionKey.from_value("PROJ-200"),
            TestKey.from_value("PROJ-11"),
            Status.from_value("PASS"),
        )

    def test_extension_filter_works(self):
        result, _ = self._run_with_files(["Login flow.png", "Login flow.txt"], extensions=[".png"])
        assert result.files_uploaded == 1
        assert (
            "Login flow.txt" not in result.files_unused
        )  # It's ignored by collector, so not unused

    def test_status_override_per_test(self):
        result, test_repo = self._run_with_files(
            ["Login flow.png", "Logout flow.png"], overrides={"PROJ-11": "FAIL"}
        )
        # PROJ-10 (Login) -> PASS (default)
        # PROJ-11 (Logout) -> FAIL (override)
        test_repo.update_status.assert_any_call(
            ExecutionKey.from_value("PROJ-200"),
            TestKey.from_value("PROJ-10"),
            Status.from_value("PASS"),
        )
        test_repo.update_status.assert_any_call(
            ExecutionKey.from_value("PROJ-200"),
            TestKey.from_value("PROJ-11"),
            Status.from_value("FAIL"),
        )

    def test_nonexistent_folder_raises(self):
        svc, _ = self._make_service()
        with pytest.raises(FileNotFoundError):
            svc.run(
                SyncInput(
                    execution_key="PROJ-200",
                    folder="/nonexistent/path/that/does/not/exist",
                )
            )

    def test_progress_callback_is_called(self):
        messages = []
        svc, _ = self._make_service()
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "Login flow.png").write_text("data")
            svc.run(
                SyncInput(execution_key="PROJ-200", folder=tmpdir),
                progress_callback=messages.append,
            )
        assert len(messages) > 0

    def test_fail_fast_on_invalid_execution(self):
        test_repo = MagicMock()
        test_repo.list_from_execution.side_effect = Exception("Not found")
        svc = SyncService(test_repo)

        result = svc.run(SyncInput(execution_key="PROJ-999", folder="."))
        assert len(result.errors) == 1
        assert "PROJ-999" in result.errors[0]

    def test_replace_mode_clears_evidence(self):
        svc, test_repo = self._make_service()
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "Login flow.png").write_text("data")

            svc.run(SyncInput(execution_key="PROJ-200", folder=tmpdir, upload_mode="replace"))

            # Verify clear_evidence was called for PROJ-10 (the matched test)
            test_repo.clear_evidence.assert_called_once_with(
                ExecutionKey.from_value("PROJ-200"),
                TestKey.from_value("PROJ-10"),
            )

    def test_upload_failures_are_reported_per_file(self):
        svc, test_repo = self._make_service()
        test_repo.upload_evidence.return_value = False

        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "Login flow.png").write_text("data")
            result = svc.run(
                SyncInput(
                    execution_key="PROJ-200",
                    folder=tmpdir,
                )
            )

        assert result.files_uploaded == 0
        assert len(result.errors) == 1
        assert "Login flow.png" in result.errors[0]

    def test_status_update_failure_does_not_block_evidence_upload(self):
        svc, test_repo = self._make_service()
        test_repo.update_status.return_value = False

        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "Login flow.png").write_text("data")
            result = svc.run(
                SyncInput(
                    execution_key="PROJ-200",
                    folder=tmpdir,
                )
            )

        assert result.updated_tests == 0
        assert result.files_uploaded == 1
        assert result.errors == []
        test_repo.upload_evidence.assert_called_once()
