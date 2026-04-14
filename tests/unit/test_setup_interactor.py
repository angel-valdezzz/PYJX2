"""Unit tests for SetupInteractor Clean Architecture."""
from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from pyjx2.application.use_cases.setup.setup_interactor import SetupInteractor
from pyjx2.application.use_cases.setup import (
    SetupConfig, SetupTestPlanConfig, SetupTestExecutionConfig, SetupTestSetConfig,
    SetupGlobalSettings, SetupSourceConfig
)
from pyjx2.domain.entities import Test, TestSet, TestExecution, TestPlan
from pyjx2.domain.value_objects import ProjectKey, TestKey, TestSetKey

class TestSetupInteractorExecute:
    """Tests for SetupInteractor.execute()"""

    def _make_interactor(self, plan_repo, exec_repo, set_repo, test_repo):
        return SetupInteractor(
            test_plan_repo=plan_repo,
            test_exec_repo=exec_repo,
            test_set_repo=set_repo,
            test_repo=test_repo
        )
        
    def _make_base_config(self):
        return SetupConfig(
            project_key="PROJ",
            test_plan=SetupTestPlanConfig(key="PROJ-1"),
            test_executions=[
                SetupTestExecutionConfig(
                    mode="create",
                    name="Sprint Exec",
                    test_sets=[
                        SetupTestSetConfig(
                            mode="create",
                            application="AXA_WEB",
                            key="Sprint Set",
                            apply_source=True,
                            source=SetupSourceConfig(type="list", items=["PROJ-10", "PROJ-11"]),
                            test_case_mode="clone"
                        )
                    ]
                )
            ],
            settings=SetupGlobalSettings(on_missing_test_case="warn", on_duplicate="skip")
        )

    def test_creates_execution_and_set_correctly(
        self, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo,
        sample_execution, sample_test_set
    ):
        mock_plan_repo.get_tests.return_value = [
            Test(key="PROJ-10", summary="Login flow"),
            Test(key="PROJ-11", summary="Logout flow"),
        ]
        
        interactor = self._make_interactor(mock_plan_repo, mock_exec_repo, mock_test_set_repo, mock_test_repo)
        config = self._make_base_config()
        
        result = interactor.execute(config)
        
        assert len(result.test_executions) == 1
        assert result.test_executions[0].key == sample_execution.key
        mock_exec_repo.create.assert_called_once_with(
            project_key=ProjectKey.from_value("PROJ"),
            summary="Sprint Exec",
        )
        
        assert len(result.test_sets) == 1
        assert result.test_sets[0].key == sample_test_set.key
        mock_test_set_repo.create.assert_called_once_with(
            project_key=ProjectKey.from_value("PROJ"),
            summary="[AXA_WEB] Test Set Sprint Set",
        )
        
        mock_exec_repo.add_test_set.assert_called_once_with(sample_execution.key, sample_test_set.key)

    def test_cloning_tests(
        self, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo,
        sample_test_set
    ):
        mock_plan_repo.get_tests.return_value = [
            Test(key="PROJ-10", summary="Login flow"),
            Test(key="PROJ-11", summary="Logout flow"),
        ]
        
        interactor = self._make_interactor(mock_plan_repo, mock_exec_repo, mock_test_set_repo, mock_test_repo)
        config = self._make_base_config()
        result = interactor.execute(config)
        
        assert mock_test_repo.clone.call_count == 2
        assert result.metrics.tests_cloned == 2
        assert mock_test_set_repo.add_tests.called
        mock_test_repo.clone.assert_any_call(
            TestKey.from_value("PROJ-10"),
            ProjectKey.from_value("PROJ"),
        )

    def test_reusing_tests(
        self, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo,
    ):
        mock_plan_repo.get_tests.return_value = [
            Test(key="PROJ-10", summary="Login flow"),
            Test(key="PROJ-11", summary="Logout flow"),
        ]
        
        interactor = self._make_interactor(mock_plan_repo, mock_exec_repo, mock_test_set_repo, mock_test_repo)
        config = self._make_base_config()
        config.test_executions[0].test_sets[0].test_case_mode = "add"
        
        result = interactor.execute(config)
        
        assert mock_test_repo.clone.call_count == 0
        assert result.metrics.tests_linked == 2
        assert result.metrics.tests_cloned == 0
        mock_test_set_repo.add_tests.assert_called_once_with(
            TestSetKey.from_value("PROJ-20"),
            [TestKey.from_value("PROJ-10"), TestKey.from_value("PROJ-11")],
        )

    def test_fail_fast_on_missing_plan(
        self, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo,
    ):
        mock_plan_repo.get.return_value = None
        interactor = self._make_interactor(mock_plan_repo, mock_exec_repo, mock_test_set_repo, mock_test_repo)
        config = self._make_base_config()
        
        with pytest.raises(ValueError, match=r"\[FAIL FAST\]"):
            interactor.execute(config)

    def test_skips_duplicates(
        self, mock_test_repo, mock_test_set_repo, mock_exec_repo, mock_plan_repo,
    ):
        mock_plan_repo.get_tests.return_value = [Test(key="PROJ-10", summary="Login flow")]
        interactor = self._make_interactor(mock_plan_repo, mock_exec_repo, mock_test_set_repo, mock_test_repo)
        config = self._make_base_config()
        config.test_executions[0].test_sets[0].source.items = [
            TestKey.from_value("PROJ-10"),
            TestKey.from_value("PROJ-10"),
        ]
        
        result = interactor.execute(config)
        
        assert mock_test_repo.clone.call_count == 1
        assert result.metrics.tests_cloned == 1
