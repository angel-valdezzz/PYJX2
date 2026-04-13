from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional

from ..application.services.sync_service import SyncInput, SyncResult, SyncService
from ..domain.entities import Test, TestExecution, TestPlan, TestSet
from ..infrastructure.config.settings import Settings

if TYPE_CHECKING:
    from ..bootstrap import PyJX2Runtime
    from ..infrastructure.jira.client import JiraClient
    from ..infrastructure.xray.client import XrayClient


class PyJX2:
    """
    High-level API facade for Jira / Xray automation.

    Public behavior stays compatible while dependency wiring lives in bootstrap.
    """

    def __init__(self, settings_or_runtime: Settings | "PyJX2Runtime") -> None:
        if isinstance(settings_or_runtime, Settings):
            from ..bootstrap import build_runtime

            runtime = build_runtime(settings_or_runtime)
        else:
            runtime = settings_or_runtime

        self._bind_runtime(runtime)

    def _bind_runtime(self, runtime: "PyJX2Runtime") -> None:
        self._runtime = runtime
        self._settings = runtime.settings
        self._jira = runtime.jira
        self._xray = runtime.xray
        self._test_repo = runtime.test_repo
        self._test_set_repo = runtime.test_set_repo
        self._test_exec_repo = runtime.test_exec_repo
        self._test_plan_repo = runtime.test_plan_repo

    def _get_setup_interactor(self):
        runtime = getattr(self, "_runtime", None)
        if runtime is not None:
            return runtime.setup_interactor

        from ..application.use_cases.setup.setup_interactor import SetupInteractor

        return SetupInteractor(
            test_plan_repo=self._test_plan_repo,
            test_exec_repo=self._test_exec_repo,
            test_set_repo=self._test_set_repo,
            test_repo=self._test_repo,
        )

    def _get_sync_service(self) -> SyncService:
        runtime = getattr(self, "_runtime", None)
        if runtime is not None:
            return runtime.sync_service

        return SyncService(self._test_repo, self._test_exec_repo)

    def get_test(self, key: str) -> Optional[Test]:
        return self._test_repo.get(key)

    def create_test(
        self,
        project_key: str,
        summary: str,
        test_type: str = "Manual",
        labels: Optional[list[str]] = None,
    ) -> Test:
        return self._test_repo.create(
            project_key=project_key,
            summary=summary,
            test_type=test_type,
            labels=labels or [],
        )

    def clone_test(self, source_key: str, target_project_key: str) -> Test:
        return self._test_repo.clone(source_key, target_project_key)

    def get_tests_from_execution(self, execution_key: str) -> list[Test]:
        return self._test_repo.list_from_execution(execution_key)

    def update_test_status(
        self,
        execution_key: str,
        test_key: str,
        status: str,
    ) -> bool:
        return self._test_repo.update_status(execution_key, test_key, status)

    def upload_test_evidence(
        self,
        execution_key: str,
        test_key: str,
        file_path: str,
    ) -> bool:
        return self._test_repo.upload_evidence(execution_key, test_key, file_path)

    def get_test_set(self, key: str) -> Optional[TestSet]:
        return self._test_set_repo.get(key)

    def create_test_set(self, project_key: str, summary: str) -> TestSet:
        return self._test_set_repo.create(project_key, summary)

    def update_test_set(self, key: str, **kwargs) -> TestSet:
        return self._test_set_repo.update(key, **kwargs)

    def add_tests_to_set(self, test_set_key: str, test_keys: list[str]) -> bool:
        return self._test_set_repo.add_tests(test_set_key, test_keys)

    def get_test_execution(self, key: str) -> Optional[TestExecution]:
        return self._test_exec_repo.get(key)

    def create_test_execution(self, project_key: str, summary: str, **kwargs) -> TestExecution:
        return self._test_exec_repo.create(project_key, summary, **kwargs)

    def update_test_execution(self, key: str, **kwargs) -> TestExecution:
        return self._test_exec_repo.update(key, **kwargs)

    def add_test_set_to_execution(self, execution_key: str, test_set_key: str) -> bool:
        return self._test_exec_repo.add_test_set(execution_key, test_set_key)

    def get_test_plan(self, key: str) -> Optional[TestPlan]:
        return self._test_plan_repo.get(key)

    def get_tests_from_plan(self, plan_key: str) -> list[dict]:
        return self._test_plan_repo.get_tests(plan_key)

    def setup(
        self,
        test_plan_key: str,
        execution_summary: str,
        application: str,
        test_mode: str = "clone",
        progress_callback=None,
    ):
        from ..application.use_cases.setup.models import (
            SetupConfig,
            SetupGlobalSettings,
            SetupSourceConfig,
            SetupTestExecutionConfig,
            SetupTestPlanConfig,
            SetupTestSetConfig,
        )

        effective_mode = test_mode if test_mode in ("clone", "link", "add") else "clone"
        interactor = self._get_setup_interactor()
        project_key = self._settings.jira.project_key

        config = SetupConfig(
            project_key=project_key,
            test_plan=SetupTestPlanConfig(key=test_plan_key),
            test_executions=[
                SetupTestExecutionConfig(
                    mode="create",
                    name=execution_summary,
                    test_sets=[
                        SetupTestSetConfig(
                            mode="create",
                            application=application,
                            key=execution_summary,
                            apply_source=True,
                            source=SetupSourceConfig(type="test_plan"),
                            test_case_mode=effective_mode,
                        )
                    ],
                )
            ],
            settings=SetupGlobalSettings(),
        )

        return interactor.execute(config, logger=progress_callback)

    def sync(
        self,
        execution_key: str,
        folder: str,
        status: str = "PASS",
        status_overrides: Optional[Dict[str, str]] = None,
        allowed_extensions: Optional[List[str]] = None,
        upload_mode: str = "append",
        recursive: bool = True,
        progress_callback=None,
    ) -> SyncResult:
        service = self._get_sync_service()

        sync_input = SyncInput(
            execution_key=execution_key,
            folder=folder,
            default_status=status,
            status_overrides=status_overrides or {},
            allowed_extensions=allowed_extensions,
            upload_mode=upload_mode,
            recursive=recursive,
        )

        return service.run(sync_input, progress_callback=progress_callback)

    @classmethod
    def from_credentials(
        cls,
        username: str,
        password: str,
        env: str = "QA",
    ) -> "PyJX2":
        from ..bootstrap import build_runtime_from_credentials

        runtime = build_runtime_from_credentials(username=username, password=password, env=env)
        return cls(runtime)

    @classmethod
    def from_config(
        cls,
        config_file: Optional[str] = None,
    ) -> "PyJX2":
        from ..bootstrap import build_runtime_from_config

        runtime = build_runtime_from_config(config_file=config_file)
        return cls(runtime)

    @property
    def jira(self) -> "JiraClient":
        return self._jira

    @property
    def xray(self) -> "XrayClient":
        return self._xray

    @staticmethod
    def encrypt_password(plain_text: str) -> str:
        from ..infrastructure.security.encryption import SymmetricEncryptionService

        return SymmetricEncryptionService().encrypt(plain_text)

    @staticmethod
    def decrypt_password(encrypted_text: str) -> str:
        from ..infrastructure.security.encryption import SymmetricEncryptionService

        return SymmetricEncryptionService().decrypt(encrypted_text)
