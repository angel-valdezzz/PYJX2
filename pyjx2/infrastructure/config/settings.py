from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import jsonschema

CONFIG_FILENAMES = ["pyjx2.toml", "pyjx2.json"]
_SCHEMA_PATH = Path(__file__).parent / "schema.json"


class JiraSettings:
    """Jira connection settings. URL and project key are derived from the environment."""

    def __init__(self, username: str, password: str, env: str = "QA") -> None:
        self.username = username
        self.password = password
        self.env = env.upper() if env else "QA"

    @property
    def url(self) -> str:
        return "https://qa.ejemplo.com" if self.env == "QA" else "https://dev.ejemplo.com"

    @property
    def project_key(self) -> str:
        return "QAX"


@dataclass
class XraySettings:
    client_id: str
    client_secret: str
    base_url: str = "https://xray.cloud.getxray.app/api/v2"


@dataclass
class SetupDefaults:
    test_plan_key: Optional[str] = None
    execution_summary: Optional[str] = None
    test_mode: str = "clone"   # "clone" | "add"


@dataclass
class SyncDefaults:
    execution_key: Optional[str] = None
    folder: Optional[str] = None
    status: Optional[str] = None
    recursive: bool = True
    upload_mode: str = "append"  # "append" | "replace"
    allowed_extensions: list[str] = field(default_factory=lambda: [".pdf"])


@dataclass
class Settings:
    jira: JiraSettings
    xray: XraySettings
    setup: SetupDefaults = field(default_factory=SetupDefaults)
    sync: SyncDefaults = field(default_factory=SyncDefaults)


def _load_file(path: Path) -> dict:
    if path.suffix == ".toml":
        try:
            import tomllib
            with open(path, "rb") as f:
                return tomllib.load(f)
        except ModuleNotFoundError:
            import toml
            with open(path, "r") as f:
                return toml.load(f)
    elif path.suffix == ".json":
        with open(path, "r") as f:
            return json.load(f)
    else:
        raise ValueError(f"Unsupported config format: {path.suffix}")


def _validate_schema(data: dict) -> None:
    schema = json.loads(_SCHEMA_PATH.read_text())
    jsonschema.validate(instance=data, schema=schema)


def _find_config_file() -> Optional[Path]:
    cwd = Path.cwd()
    for name in CONFIG_FILENAMES:
        candidate = cwd / name
        if candidate.exists():
            return candidate
    return None


def _dict_to_settings(data: dict) -> Settings:
    auth_data = data.get("auth", {})
    setup_data = data.get("setup", {})
    sync_data = data.get("sync", {})

    if not auth_data.get("username") or not auth_data.get("password"):
        raise ValueError("Missing authentication credentials (username/password)")

    return Settings(
        jira=JiraSettings(
            env=auth_data.get("env", "QA"),
            username=auth_data["username"],
            password=auth_data["password"],
        ),
        xray=XraySettings(
            client_id=auth_data["username"],
            client_secret=auth_data["password"],
            base_url="https://xray.cloud.getxray.app/api/v2",
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
    }
    result = {k: dict(v) for k, v in data.items()} if data else {}
    for env_key, (section, key) in env_map.items():
        val = os.environ.get(env_key)
        if val:
            if section not in result:
                result[section] = {}
            result[section][key] = val
    return result


def load_settings(
    config_file: Optional[str] = None,
    overrides: Optional[dict] = None,
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
                data[section].update({k: v for k, v in values.items() if v is not None})
            else:
                data[section] = values

    # Validation: Auth credentials are always required.
    missing = []
    
    auth_data = data.get("auth", {})
    if not auth_data.get("username"): missing.append("auth.username")
    if not auth_data.get("password"): missing.append("auth.password")

    if missing:
        raise ValueError(
            f"Missing required configuration: {', '.join(missing)}. "
            "Provide them via pyjx2.toml, pyjx2.json, environment variables (PYJX2_AUTH_*), or CLI arguments."
        )

    return _dict_to_settings(data)
