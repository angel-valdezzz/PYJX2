"""
Acceptance tests for the full setup flow.
These tests validate that all layers work together correctly
using mock repositories (no real Jira/Xray calls).
"""
from __future__ import annotations

import pytest

from pyjx2.api.client import PyJX2
from pyjx2.application.services.setup_service import SetupInput
from pyjx2.domain.entities import Test, TestSet, TestExecution


class TestSetupFlowEndToEnd:
    """
    Full setup flow exercised via the PyJX2 public API
    with repositories mocked at the infrastructure boundary.
    """

    def _build_client(
        self,
        settings,
        mock_test_repo,
        mock_test_set_repo,
        mock_exec_repo,
        mock_plan_repo,
    ) -> PyJX2:
        client = PyJX2.__new__(PyJX2)
        client._settings = settings
        client._test_repo = mock_test_repo
        client._test_set_repo = mock_test_set_repo
        client._test_exec_repo = mock_exec_repo
        client._test_plan_repo = mock_plan_repo
        return client

    def test_full_setup_returns_all_entities(
        self, settings, mock_test_repo, mock_test_set_repo,
        mock_exec_repo, mock_plan_repo, sample_execution, sample_test_set,
    ):
        client = self._build_client(
            settings, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo
        )
        result = client.setup(
            project_key="PROJ",
            test_plan_key="PROJ-1",
            execution_summary="Sprint 1 Execution",
            test_set_summary="Sprint 1 Test Set",
            reuse_tests=False,
        )
        assert result.test_execution is not None
        assert result.test_set is not None
        assert result.test_execution.key == sample_execution.key
        assert result.test_set.key == sample_test_set.key

    def test_setup_with_clone_mode_clones_all_plan_tests(
        self, settings, mock_test_repo, mock_test_set_repo,
        mock_exec_repo, mock_plan_repo,
    ):
        client = self._build_client(
            settings, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo
        )
        result = client.setup(
            project_key="PROJ",
            test_plan_key="PROJ-1",
            execution_summary="E",
            test_set_summary="S",
            reuse_tests=False,
        )
        assert len(result.cloned) == 2
        assert len(result.reused) == 0
        assert mock_test_repo.clone.call_count == 2

    def test_setup_with_reuse_mode_does_not_clone(
        self, settings, mock_test_repo, mock_test_set_repo,
        mock_exec_repo, mock_plan_repo,
    ):
        client = self._build_client(
            settings, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo
        )
        result = client.setup(
            project_key="PROJ",
            test_plan_key="PROJ-1",
            execution_summary="E",
            test_set_summary="S",
            reuse_tests=True,
        )
        assert len(result.reused) == 2
        assert mock_test_repo.clone.call_count == 0

    def test_setup_links_test_set_to_execution(
        self, settings, mock_test_repo, mock_test_set_repo,
        mock_exec_repo, mock_plan_repo, sample_execution, sample_test_set,
    ):
        client = self._build_client(
            settings, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo
        )
        client.setup(
            project_key="PROJ",
            test_plan_key="PROJ-1",
            execution_summary="E",
            test_set_summary="S",
        )
        mock_exec_repo.add_test_set.assert_called_once_with(
            sample_execution.key, sample_test_set.key
        )

    def test_setup_adds_cloned_tests_to_set(
        self, settings, mock_test_repo, mock_test_set_repo,
        mock_exec_repo, mock_plan_repo, sample_test_set,
    ):
        cloned_keys = ["PROJ-50", "PROJ-51"]
        call_count = [0]

        def clone_side(*args, **kwargs):
            t = Test(key=cloned_keys[call_count[0]], summary="Cloned")
            call_count[0] += 1
            return t

        mock_test_repo.clone.side_effect = clone_side

        client = self._build_client(
            settings, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo
        )
        client.setup(
            project_key="PROJ",
            test_plan_key="PROJ-1",
            execution_summary="E",
            test_set_summary="S",
        )

        add_call = mock_test_set_repo.add_tests.call_args
        added_keys = add_call[0][1]
        assert set(added_keys) == set(cloned_keys)

    def test_setup_progress_callback_receives_messages(
        self, settings, mock_test_repo, mock_test_set_repo,
        mock_exec_repo, mock_plan_repo,
    ):
        messages = []
        client = self._build_client(
            settings, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo
        )
        client.setup(
            project_key="PROJ",
            test_plan_key="PROJ-1",
            execution_summary="E",
            test_set_summary="S",
            progress_callback=messages.append,
        )
        assert len(messages) >= 4

    def test_setup_fails_when_plan_not_found(
        self, settings, mock_test_repo, mock_test_set_repo,
        mock_exec_repo, mock_plan_repo,
    ):
        mock_plan_repo.get.return_value = None
        client = self._build_client(
            settings, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo
        )
        with pytest.raises(ValueError, match="not found"):
            client.setup(
                project_key="PROJ",
                test_plan_key="PROJ-999",
                execution_summary="E",
                test_set_summary="S",
            )
