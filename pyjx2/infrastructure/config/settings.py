from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import jsonschema

CONFIG_FILENAMES = ["pyjx2.toml", "pyjx2.json"]
_SCHEMA_PATH = Path(__file__).parent / "schema.json"

_ENV_ENDPOINTS = {
    "QA": {
        "platform_base_url": "https://qa.ejemplo.com",
        "xray_api_path": "/rest/raven/2.0/api",
        "xray_graphql_path": "/rest/raven/2.0/api/graphql",
    },
    "DEV": {
        "platform_base_url": "https://dev.ejemplo.com",
        "xray_api_path": "/rest/raven/2.0/api",
        "xray_graphql_path": "/rest/raven/2.0/api/graphql",
    },
}


def _normalize_env(env: str | None) -> str:
    normalized = env.upper().strip() if env else "QA"
    if normalized not in _ENV_ENDPOINTS:
        allowed = ", ".join(sorted(_ENV_ENDPOINTS))
        raise ValueError(f"Invalid environment: {env!r}. Expected one of: {allowed}")
    return normalized


def _normalize_project_key(key: str | None) -> str | None:
    if key is None:
        return None
    normalized = key.strip().upper()
    return normalized or None


def _platform_profile(env: str | None) -> dict[str, str]:
    return _ENV_ENDPOINTS[_normalize_env(env)]


class JiraSettings:
    """Internal Jira settings derived from public platform configuration."""

    def __init__(
        self,
        username: str,
        password: str,
        env: str = "QA",
        project_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.username = username
        self.password = password
        self.env = _normalize_env(env)
        profile = _platform_profile(self.env)
        self._base_url = (base_url or profile["platform_base_url"]).rstrip("/")
        self._project_key = _normalize_project_key(project_key)

    @property
    def url(self) -> str:
        return self._base_url

    @property
    def project_key(self) -> str | None:
        return self._project_key


@dataclass
class XraySettings:
    client_id: str
    client_secret: str
    env: str = "QA"
    base_url: str | None = None
    graphql_url: str | None = None

    def __post_init__(self) -> None:
        self.env = _normalize_env(self.env)
        profile = _platform_profile(self.env)
        base = profile["platform_base_url"].rstrip("/")
        if self.base_url is None:
            self.base_url = f"{base}{profile['xray_api_path']}"
        if self.graphql_url is None:
            self.graphql_url = f"{base}{profile['xray_graphql_path']}"


@dataclass
class AuthSettings:
    username: str
    password: str
    env: str = "QA"

    def __post_init__(self) -> None:
        self.env = _normalize_env(self.env)


@dataclass
class ProjectSettings:
    key: str | None = None

    def __post_init__(self) -> None:
        self.key = _normalize_project_key(self.key)


@dataclass
class SetupDefaults:
    test_plan_key: str | None = None
    execution_summary: str | None = None
    test_mode: str = "clone"


@dataclass
class SyncDefaults:
    execution_key: str | None = None
    folder: str | None = None
    status: str | None = None
    recursive: bool = True
    upload_mode: str = "append"
    allowed_extensions: list[str] = field(default_factory=lambda: [".pdf"])


@dataclass
class Settings:
    auth: AuthSettings
    project: ProjectSettings = field(default_factory=ProjectSettings)
    setup: SetupDefaults = field(default_factory=SetupDefaults)
    sync: SyncDefaults = field(default_factory=SyncDefaults)

    @property
    def jira(self) -> JiraSettings:
        return JiraSettings(
            username=self.auth.username,
            password=self.auth.password,
            env=self.auth.env,
            project_key=self.project.key,
        )

    @property
    def xray(self) -> XraySettings:
        return XraySettings(
            client_id=self.auth.username,
            client_secret=self.auth.password,
            env=self.auth.env,
        )


def _load_file(path: Path) -> dict[str, Any]:
    if path.suffix == ".toml":
        if sys.version_info >= (3, 11):
            import tomllib

            with open(path, "rb") as f:
                return tomllib.load(f)
        import toml

        with open(path, encoding="utf-8") as f:
            return cast(dict[str, Any], toml.load(f))
    if path.suffix == ".json":
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    raise ValueError(f"Unsupported config format: {path.suffix}")


def _validate_schema(data: dict) -> None:
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=data, schema=schema)


def _find_config_file() -> Path | None:
    cwd = Path.cwd()
    for name in CONFIG_FILENAMES:
        candidate = cwd / name
        if candidate.exists():
            return candidate
    return None


def _dict_to_settings(data: dict) -> Settings:
    auth_data = data.get("auth", {})
    project_data = data.get("project", {})
    setup_data = data.get("setup", {})
    sync_data = data.get("sync", {})

    if not auth_data.get("username") or not auth_data.get("password"):
        raise ValueError("Missing authentication credentials (username/password)")

    return Settings(
        auth=AuthSettings(
            env=auth_data.get("env", "QA"),
            username=auth_data["username"],
            password=auth_data["password"],
        ),
        project=ProjectSettings(
            key=project_data.get("key"),
        ),
        setup=SetupDefaults(
            test_plan_key=setup_data.get("test_plan_key"),
            execution_summary=setup_data.get("execution_summary"),
            test_mode=setup_data.get("test_mode", "clone"),
        ),
        sync=SyncDefaults(
            execution_key=sync_data.get("execution_key"),
            folder=sync_data.get("folder"),
            status=sync_data.get("status"),
            recursive=sync_data.get("recursive", True),
            upload_mode=sync_data.get("upload_mode", "append"),
            allowed_extensions=sync_data.get("allowed_extensions", [".pdf"]),
        ),
    )


def _apply_env_overrides(data: dict) -> dict:
    """Allow environment variables to override config values."""
    env_map = {
        "PYJX2_AUTH_ENV": ("auth", "env"),
        "PYJX2_AUTH_USERNAME": ("auth", "username"),
        "PYJX2_AUTH_PASSWORD": ("auth", "password"),
        "PYJX2_PROJECT_KEY": ("project", "key"),
    }
    result = {k: dict(v) if isinstance(v, dict) else v for k, v in data.items()} if data else {}
    for env_key, (section, key) in env_map.items():
        val = os.environ.get(env_key)
        if val:
            if section not in result or not isinstance(result.get(section), dict):
                result[section] = {}
            result[section][key] = val
    return result


def load_settings(
    config_file: str | None = None,
    overrides: dict | None = None,
) -> Settings:
    """
    Load settings from:
    1. Auto-discovered pyjx2.toml / pyjx2.json in the current directory
    2. Explicit config file path if provided
    3. Environment variables (PYJX2_*)
    4. Runtime overrides dict (CLI arguments)
    """
    data: dict = {}

    path = Path(config_file) if config_file else _find_config_file()
    if path:
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        raw = _load_file(path)
        _validate_schema(raw)
        data = raw

    data = _apply_env_overrides(data)

    if overrides:
        for section, values in overrides.items():
            if section not in data:
                data[section] = {}
            if isinstance(values, dict):
                current = data.get(section)
                if not isinstance(current, dict):
                    current = {}
                    data[section] = current
                current.update({k: v for k, v in values.items() if v is not None})
            else:
                data[section] = values

    missing = []

    auth_data = data.get("auth", {})
    if not auth_data.get("username"):
        missing.append("auth.username")
    if not auth_data.get("password"):
        missing.append("auth.password")

    if missing:
        raise ValueError(
            f"Missing required configuration: {', '.join(missing)}. "
            "Provide them via pyjx2.toml, pyjx2.json, environment variables "
            "(PYJX2_AUTH_* / PYJX2_PROJECT_KEY), or CLI arguments."
        )

    return _dict_to_settings(data)
