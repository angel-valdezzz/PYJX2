from __future__ import annotations

from typing import TYPE_CHECKING

from ..application.services.sync_service import SyncInput, SyncResult, SyncService
from ..domain.entities import Test, TestExecution, TestPlan, TestSet
from ..domain.value_objects import (
    ExecutionKey,
    ProjectKey,
    Status,
    TestKey,
    TestPlanKey,
    TestSetKey,
    TestType,
)
from ..infrastructure.config.settings import Settings

if TYPE_CHECKING:
    from ..bootstrap import PyJX2Runtime
    from ..infrastructure.jira.client import JiraClient
    from ..infrastructure.xray.client import XrayClient


class PyJX2:
    def __init__(self, settings_or_runtime: Settings | PyJX2Runtime) -> None:
        if isinstance(settings_or_runtime, Settings):
            from ..bootstrap import build_runtime

            runtime = build_runtime(settings_or_runtime)
        else:
            runtime = settings_or_runtime

        self._bind_runtime(runtime)

    def _bind_runtime(self, runtime: PyJX2Runtime) -> None:
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
        return SyncService(self._test_repo)

    def get_test(self, key: str | TestKey) -> Test | None:
        return self._test_repo.get(TestKey.from_value(key))

    def create_test(
        self,
        project_key: str | ProjectKey,
        summary: str,
        test_type: str | TestType = "Manual",
        labels: list[str] | None = None,
    ) -> Test:
        return self._test_repo.create(
            project_key=ProjectKey.from_value(project_key),
            summary=summary,
            test_type=TestType.from_value(test_type),
            labels=labels or [],
        )

    def clone_test(self, source_key: str | TestKey, target_project_key: str | ProjectKey) -> Test:
        return self._test_repo.clone(
            TestKey.from_value(source_key),
            ProjectKey.from_value(target_project_key),
        )

    def get_tests_from_execution(self, execution_key: str | ExecutionKey) -> list[Test]:
        return self._test_repo.list_from_execution(ExecutionKey.from_value(execution_key))

    def update_test_status(
        self,
        execution_key: str | ExecutionKey,
        test_key: str | TestKey,
        status: str | Status,
    ) -> bool:
        return self._test_repo.update_status(
            ExecutionKey.from_value(execution_key),
            TestKey.from_value(test_key),
            Status.from_value(status),
        )

    def upload_test_evidence(
        self,
        execution_key: str | ExecutionKey,
        test_key: str | TestKey,
        file_path: str,
    ) -> bool:
        return self._test_repo.upload_evidence(
            ExecutionKey.from_value(execution_key),
            TestKey.from_value(test_key),
            file_path,
        )

    def get_test_set(self, key: str | TestSetKey) -> TestSet | None:
        return self._test_set_repo.get(TestSetKey.from_value(key))

    def create_test_set(self, project_key: str | ProjectKey, summary: str) -> TestSet:
        return self._test_set_repo.create(ProjectKey.from_value(project_key), summary)

    def update_test_set(self, key: str | TestSetKey, **kwargs) -> TestSet:
        return self._test_set_repo.update(TestSetKey.from_value(key), **kwargs)

    def add_tests_to_set(
        self, test_set_key: str | TestSetKey, test_keys: list[str | TestKey]
    ) -> bool:
        return self._test_set_repo.add_tests(
            TestSetKey.from_value(test_set_key),
            [TestKey.from_value(test_key) for test_key in test_keys],
        )

    def get_test_execution(self, key: str | ExecutionKey) -> TestExecution | None:
        return self._test_exec_repo.get(ExecutionKey.from_value(key))

    def create_test_execution(
        self,
        project_key: str | ProjectKey,
        summary: str,
        **kwargs,
    ) -> TestExecution:
        return self._test_exec_repo.create(ProjectKey.from_value(project_key), summary, **kwargs)

    def update_test_execution(self, key: str | ExecutionKey, **kwargs) -> TestExecution:
        return self._test_exec_repo.update(ExecutionKey.from_value(key), **kwargs)

    def add_test_set_to_execution(
        self,
        execution_key: str | ExecutionKey,
        test_set_key: str | TestSetKey,
    ) -> bool:
        return self._test_exec_repo.add_test_set(
            ExecutionKey.from_value(execution_key),
            TestSetKey.from_value(test_set_key),
        )

    def get_test_plan(self, key: str | TestPlanKey) -> TestPlan | None:
        return self._test_plan_repo.get(TestPlanKey.from_value(key))

    def get_tests_from_plan(self, plan_key: str | TestPlanKey) -> list[Test]:
        return self._test_plan_repo.get_tests(TestPlanKey.from_value(plan_key))

    def resolve_project_key(self, test_plan_key: str | None = None) -> str | None:
        explicit_key = self._settings.jira.project_key
        if explicit_key:
            return explicit_key
        if test_plan_key:
            normalized_plan_key = str(TestPlanKey.from_value(test_plan_key))
            return normalized_plan_key.split("-", 1)[0]
        return None

    def setup(
        self,
        test_plan_key: str,
        execution_summary: str,
        application: str,
        test_mode: str = "clone",
        progress_callback=None,
    ):
        from ..application.use_cases.setup import (
            SetupConfig,
            SetupGlobalSettings,
            SetupSourceConfig,
            SetupTestExecutionConfig,
            SetupTestPlanConfig,
            SetupTestSetConfig,
        )

        effective_mode = test_mode if test_mode in ("clone", "link", "add") else "clone"
        interactor = self._get_setup_interactor()
        normalized_plan_key = str(TestPlanKey.from_value(test_plan_key))
        project_key = self.resolve_project_key(normalized_plan_key)
        if not project_key:
            raise ValueError(
                "Missing project key. Configure project.key or provide a test plan key with format PROJ-123."
            )

        config = SetupConfig(
            project_key=project_key,
            test_plan=SetupTestPlanConfig(key=normalized_plan_key),
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
        status_overrides: dict[str, str] | None = None,
        allowed_extensions: list[str] | None = None,
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
    def from_credentials(cls, username: str, password: str, env: str = "QA") -> PyJX2:
        from ..bootstrap import build_runtime_from_credentials

        return cls(build_runtime_from_credentials(username=username, password=password, env=env))

    @classmethod
    def from_config(cls, config_file: str | None = None) -> PyJX2:
        from ..bootstrap import build_runtime_from_config

        return cls(build_runtime_from_config(config_file=config_file))

    @property
    def jira(self) -> JiraClient:
        return self._jira

    @property
    def xray(self) -> XrayClient:
        return self._xray

    @staticmethod
    def encrypt_password(plain_text: str) -> str:
        from ..infrastructure.security.encryption import SymmetricEncryptionService

        return SymmetricEncryptionService().encrypt(plain_text)

    @staticmethod
    def decrypt_password(encrypted_text: str) -> str:
        from ..infrastructure.security.encryption import SymmetricEncryptionService

        return SymmetricEncryptionService().decrypt(encrypted_text)
