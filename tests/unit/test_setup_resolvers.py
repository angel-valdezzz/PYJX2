from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pyjx2.application.use_cases.setup import (
    SetupSourceConfig,
    SetupTestExecutionConfig,
    SetupTestSetConfig,
    TestCaseSourceResolver,
    TestExecutionResolver,
    TestSetResolver,
)
from pyjx2.domain.entities import Test, TestExecution, TestSet
from pyjx2.domain.value_objects import ProjectKey, TestKey


class TestSetupSourceConfig:
    def test_list_source_normalizes_test_keys(self):
        source = SetupSourceConfig(type="list", items=[" proj-1 ", "PROJ-2"])

        assert source.items == [TestKey.from_value("PROJ-1"), TestKey.from_value("PROJ-2")]

    def test_list_source_requires_items(self):
        with pytest.raises(ValueError, match="requires items"):
            SetupSourceConfig(type="list")

    def test_folder_source_requires_path(self):
        with pytest.raises(ValueError, match="requires path"):
            SetupSourceConfig(type="folder")

    def test_test_plan_source_rejects_extra_payload(self):
        with pytest.raises(ValueError, match="does not accept path or items"):
            SetupSourceConfig(type="test_plan", items=["PROJ-1"])


class TestReuseResolvers:
    def test_reuse_execution_fetches_existing_entity(self):
        repo = MagicMock()
        existing = TestExecution(key="PROJ-30", summary="Existing execution")
        repo.get.return_value = existing

        resolver = TestExecutionResolver(repo)
        result = resolver.resolve(
            SetupTestExecutionConfig(mode="reuse", key="PROJ-30"),
            ProjectKey.from_value("PROJ"),
        )

        assert result is existing
        repo.get.assert_called_once_with(existing.key)

    def test_reuse_execution_raises_when_missing(self):
        repo = MagicMock()
        repo.get.return_value = None
        resolver = TestExecutionResolver(repo)

        with pytest.raises(ValueError, match="Test Execution PROJ-30 invalida o no existe"):
            resolver.resolve(
                SetupTestExecutionConfig(mode="reuse", key="PROJ-30"),
                ProjectKey.from_value("PROJ"),
            )

    def test_reuse_test_set_fetches_existing_entity(self):
        repo = MagicMock()
        existing = TestSet(key="PROJ-20", summary="Existing set")
        repo.get.return_value = existing

        resolver = TestSetResolver(repo)
        result = resolver.resolve(
            SetupTestSetConfig(mode="reuse", key="PROJ-20", application="APP_WEB"),
            ProjectKey.from_value("PROJ"),
        )

        assert result is existing
        repo.get.assert_called_once_with(existing.key)

    def test_reuse_test_set_raises_when_missing(self):
        repo = MagicMock()
        repo.get.return_value = None
        resolver = TestSetResolver(repo)

        with pytest.raises(ValueError, match="Test Set PROJ-20 invalido o no existe"):
            resolver.resolve(
                SetupTestSetConfig(mode="reuse", key="PROJ-20", application="APP_WEB"),
                ProjectKey.from_value("PROJ"),
            )


class TestCaseSourceResolverBehavior:
    def test_folder_source_uses_repository_and_filters_by_plan(self):
        repo = MagicMock()
        repo.list_from_folder.return_value = [
            Test(key="PROJ-10", summary="Login"),
            Test(key="OTHER-1", summary="Ignored"),
        ]
        resolver = TestCaseSourceResolver(repo)

        result = resolver.resolve(
            SetupSourceConfig(type="folder", path="123"),
            valid_keys=[TestKey.from_value("PROJ-10")],
        )

        assert result == [TestKey.from_value("PROJ-10")]
        repo.list_from_folder.assert_called_once_with("123")
