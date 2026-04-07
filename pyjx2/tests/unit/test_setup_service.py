"""Unit tests for SetupService."""
from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from pyjx2.application.services.setup_service import SetupService, SetupInput
from pyjx2.domain.entities import Test, TestSet, TestExecution, TestPlan


class TestSetupServiceRun:
    """Tests for SetupService.run()"""

    def _make_service(self, test_repo, test_set_repo, exec_repo, plan_repo):
        return SetupService(test_repo, test_set_repo, exec_repo, plan_repo)

    def test_returns_setup_result_with_correct_entities(
        self, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo,
        sample_execution, sample_test_set,
    ):
        svc = self._make_service(mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo)
        result = svc.run(SetupInput(
            project_key="PROJ",
            test_plan_key="PROJ-1",
            execution_summary="Sprint Exec",
            test_set_summary="Sprint Set",
        ))
        assert result.test_execution.key == sample_execution.key
        assert result.test_set.key == sample_test_set.key

    def test_clones_tests_by_default(
        self, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo,
    ):
        svc = self._make_service(mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo)
        result = svc.run(SetupInput(
            project_key="PROJ",
            test_plan_key="PROJ-1",
            execution_summary="E",
            test_set_summary="S",
            reuse_tests=False,
        ))
        assert mock_test_repo.clone.called
        assert len(result.cloned) == 2
        assert len(result.reused) == 0

    def test_reuses_tests_when_flag_is_set(
        self, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo,
    ):
        svc = self._make_service(mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo)
        result = svc.run(SetupInput(
            project_key="PROJ",
            test_plan_key="PROJ-1",
            execution_summary="E",
            test_set_summary="S",
            reuse_tests=True,
        ))
        assert not mock_test_repo.clone.called
        assert len(result.reused) == 2
        assert len(result.cloned) == 0

    def test_creates_test_set_with_correct_project(
        self, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo,
    ):
        svc = self._make_service(mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo)
        svc.run(SetupInput(
            project_key="PROJ",
            test_plan_key="PROJ-1",
            execution_summary="Exec",
            test_set_summary="My Test Set",
        ))
        mock_test_set_repo.create.assert_called_once_with(
            project_key="PROJ",
            summary="My Test Set",
        )

    def test_adds_tests_to_set(
        self, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo,
        sample_test_set,
    ):
        svc = self._make_service(mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo)
        svc.run(SetupInput(
            project_key="PROJ",
            test_plan_key="PROJ-1",
            execution_summary="E",
            test_set_summary="S",
        ))
        assert mock_test_set_repo.add_tests.called
        call_args = mock_test_set_repo.add_tests.call_args
        assert call_args[0][0] == sample_test_set.key
        assert len(call_args[0][1]) == 2

    def test_creates_execution_with_correct_summary(
        self, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo,
    ):
        svc = self._make_service(mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo)
        svc.run(SetupInput(
            project_key="PROJ",
            test_plan_key="PROJ-1",
            execution_summary="Sprint 1 Execution",
            test_set_summary="S",
        ))
        mock_exec_repo.create.assert_called_once_with(
            project_key="PROJ",
            summary="Sprint 1 Execution",
        )

    def test_links_test_set_to_execution(
        self, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo,
        sample_execution, sample_test_set,
    ):
        svc = self._make_service(mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo)
        svc.run(SetupInput(
            project_key="PROJ",
            test_plan_key="PROJ-1",
            execution_summary="E",
            test_set_summary="S",
        ))
        mock_exec_repo.add_test_set.assert_called_once_with(
            sample_execution.key, sample_test_set.key
        )

    def test_raises_when_test_plan_not_found(
        self, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo,
    ):
        mock_plan_repo.get.return_value = None
        svc = self._make_service(mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo)
        with pytest.raises(ValueError, match="Test plan not found"):
            svc.run(SetupInput(
                project_key="PROJ",
                test_plan_key="PROJ-999",
                execution_summary="E",
                test_set_summary="S",
            ))

    def test_progress_callback_called(
        self, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo,
    ):
        messages = []
        svc = self._make_service(mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo)
        svc.run(
            SetupInput(
                project_key="PROJ",
                test_plan_key="PROJ-1",
                execution_summary="E",
                test_set_summary="S",
            ),
            progress_callback=messages.append,
        )
        assert len(messages) > 0
        assert any("test plan" in m.lower() for m in messages)

    def test_empty_test_plan_still_creates_set_and_execution(
        self, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo,
    ):
        mock_plan_repo.get_tests.return_value = []
        svc = self._make_service(mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo)
        result = svc.run(SetupInput(
            project_key="PROJ",
            test_plan_key="PROJ-1",
            execution_summary="E",
            test_set_summary="S",
        ))
        assert result.tests == []
        assert mock_test_set_repo.create.called
        assert mock_exec_repo.create.called

    def test_tests_without_key_are_skipped(
        self, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo,
    ):
        mock_plan_repo.get_tests.return_value = [
            {"key": "PROJ-10"},
            {"key": ""},
            {},
        ]
        svc = self._make_service(mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo)
        result = svc.run(SetupInput(
            project_key="PROJ",
            test_plan_key="PROJ-1",
            execution_summary="E",
            test_set_summary="S",
        ))
        assert mock_test_repo.clone.call_count == 1
