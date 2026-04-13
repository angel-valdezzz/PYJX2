from __future__ import annotations

from pyjx2.api.client import PyJX2
from pyjx2.application.services.sync_service import SyncService
from pyjx2.application.use_cases.setup.setup_interactor import SetupInteractor
from pyjx2.bootstrap import (
    PyJX2Runtime,
    build_api,
    build_api_from_config,
    build_api_from_credentials,
    build_runtime,
)
from pyjx2.infrastructure.jira.client import JiraClient
from pyjx2.infrastructure.security.encryption import SymmetricEncryptionService
from pyjx2.infrastructure.xray.client import XrayClient
from pyjx2.infrastructure.xray.repositories import (
    XrayTestExecutionRepository,
    XrayTestPlanRepository,
    XrayTestRepository,
    XrayTestSetRepository,
)


def test_build_runtime_composes_concrete_dependencies(settings):
    runtime = build_runtime(settings)

    assert isinstance(runtime, PyJX2Runtime)
    assert runtime.settings is settings
    assert isinstance(runtime.jira, JiraClient)
    assert isinstance(runtime.xray, XrayClient)
    assert isinstance(runtime.test_repo, XrayTestRepository)
    assert isinstance(runtime.test_set_repo, XrayTestSetRepository)
    assert isinstance(runtime.test_exec_repo, XrayTestExecutionRepository)
    assert isinstance(runtime.test_plan_repo, XrayTestPlanRepository)
    assert isinstance(runtime.setup_interactor, SetupInteractor)
    assert isinstance(runtime.sync_service, SyncService)
    assert isinstance(runtime.encryption_service, SymmetricEncryptionService)
    assert runtime.setup_interactor.test_repo is runtime.test_repo
    assert runtime.setup_interactor.plan_repo is runtime.test_plan_repo
    assert runtime.sync_service._test_repo is runtime.test_repo


def test_build_api_wraps_bootstrapped_runtime(settings):
    client = build_api(settings)

    assert isinstance(client, PyJX2)
    assert client._settings is settings
    assert isinstance(client._runtime, PyJX2Runtime)
    assert client._test_repo is client._runtime.test_repo
    assert client.jira is client._runtime.jira
    assert client.xray is client._runtime.xray


def test_pyjx2_accepts_prebuilt_runtime(settings):
    runtime = build_runtime(settings)
    client = PyJX2(runtime)

    assert client._runtime is runtime
    assert client._settings is settings
    assert client._test_exec_repo is runtime.test_exec_repo


def test_build_api_from_config_uses_config_file(valid_toml_config):
    client = build_api_from_config(config_file=str(valid_toml_config))

    assert isinstance(client, PyJX2)
    assert client._settings.jira.username == "user@example.com"
    assert client._settings.xray.client_id == "user@example.com"


def test_pyjx2_from_credentials_remains_compatible():
    client = PyJX2.from_credentials(
        username="user@example.com",
        password="plain_token",
        env="DEV",
    )

    assert isinstance(client, PyJX2)
    assert client._settings.jira.username == "user@example.com"
    assert client._settings.jira.env == "DEV"
    assert client._settings.xray.client_secret == "plain_token"


def test_build_api_from_credentials_returns_compatible_client():
    client = build_api_from_credentials(
        username="user@example.com",
        password="plain_token",
        env="QA",
    )

    assert isinstance(client, PyJX2)
    assert client._settings.jira.env == "QA"
