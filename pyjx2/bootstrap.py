from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .application.services.sync_service import SyncService
from .application.use_cases.setup.setup_interactor import SetupInteractor
from .infrastructure.config import load_settings
from .infrastructure.config.settings import JiraSettings, Settings, XraySettings
from .infrastructure.jira.client import JiraClient
from .infrastructure.security.encryption import SymmetricEncryptionService
from .infrastructure.xray.client import XrayClient
from .infrastructure.xray.repositories import (
    XrayTestExecutionRepository,
    XrayTestPlanRepository,
    XrayTestRepository,
    XrayTestSetRepository,
)


@dataclass
class PyJX2Runtime:
    settings: Settings
    jira: JiraClient
    xray: XrayClient
    test_repo: XrayTestRepository
    test_set_repo: XrayTestSetRepository
    test_exec_repo: XrayTestExecutionRepository
    test_plan_repo: XrayTestPlanRepository
    setup_interactor: SetupInteractor
    sync_service: SyncService
    encryption_service: SymmetricEncryptionService


def build_settings_from_credentials(
    username: str,
    password: str,
    env: str = "QA",
) -> Settings:
    return Settings(
        jira=JiraSettings(username=username, password=password, env=env),
        xray=XraySettings(client_id=username, client_secret=password),
    )


def build_runtime(settings: Settings) -> PyJX2Runtime:
    jira = JiraClient(settings.jira)
    xray = XrayClient(settings.xray)

    test_repo = XrayTestRepository(xray, jira)
    test_set_repo = XrayTestSetRepository(xray, jira)
    test_exec_repo = XrayTestExecutionRepository(xray, jira)
    test_plan_repo = XrayTestPlanRepository(xray, jira)

    return PyJX2Runtime(
        settings=settings,
        jira=jira,
        xray=xray,
        test_repo=test_repo,
        test_set_repo=test_set_repo,
        test_exec_repo=test_exec_repo,
        test_plan_repo=test_plan_repo,
        setup_interactor=SetupInteractor(
            test_plan_repo=test_plan_repo,
            test_exec_repo=test_exec_repo,
            test_set_repo=test_set_repo,
            test_repo=test_repo,
        ),
        sync_service=SyncService(test_repo),
        encryption_service=SymmetricEncryptionService(),
    )


def build_runtime_from_config(
    config_file: Optional[str] = None,
    overrides: Optional[dict] = None,
) -> PyJX2Runtime:
    settings = load_settings(config_file=config_file, overrides=overrides)
    return build_runtime(settings)


def build_runtime_from_credentials(
    username: str,
    password: str,
    env: str = "QA",
) -> PyJX2Runtime:
    return build_runtime(build_settings_from_credentials(username, password, env=env))


def build_api(settings: Settings):
    from .api.client import PyJX2

    return PyJX2(build_runtime(settings))


def build_api_from_config(
    config_file: Optional[str] = None,
    overrides: Optional[dict] = None,
):
    from .api.client import PyJX2

    return PyJX2(build_runtime_from_config(config_file=config_file, overrides=overrides))


def build_api_from_credentials(
    username: str,
    password: str,
    env: str = "QA",
):
    from .api.client import PyJX2

    return PyJX2(build_runtime_from_credentials(username, password, env=env))


__all__ = [
    "PyJX2Runtime",
    "build_api",
    "build_api_from_config",
    "build_api_from_credentials",
    "build_runtime",
    "build_runtime_from_config",
    "build_runtime_from_credentials",
    "build_settings_from_credentials",
]
