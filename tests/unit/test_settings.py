"""Unit tests for configuration loading and validation."""

from __future__ import annotations

import json
import os
from unittest.mock import patch

import pytest
from pyjx2.infrastructure.config.settings import _apply_env_overrides, load_settings


class TestLoadSettingsFromOverrides:
    """Settings loaded purely from runtime override dicts."""

    def _valid_overrides(self, **extra):
        base = {
            "auth": {
                "env": "QA",
                "username": "u@test.com",
                "password": "token",
            },
            "project": {"key": "PROJ"},
        }
        base.update(extra)
        return base

    def test_loads_valid_overrides(self):
        s = load_settings(overrides=self._valid_overrides())
        assert s.jira.env == "QA"
        assert "qa" in s.jira.url.lower()
        assert s.jira.username == "u@test.com"
        assert s.jira.password == "token"
        # Xray is now forced to recycle Jira
        assert s.xray.client_id == "u@test.com"
        assert s.xray.client_secret == "token"

    def test_xray_default_base_url(self):
        s = load_settings(overrides=self._valid_overrides())
        assert s.xray.base_url.endswith("/rest/raven/2.0/api")

    def test_project_key_comes_from_configuration(self):
        s = load_settings(overrides=self._valid_overrides())
        assert s.jira.project_key == "PROJ"

    def test_dev_env_uses_dev_url(self):
        overrides = self._valid_overrides()
        overrides["auth"]["env"] = "DEV"
        s = load_settings(overrides=overrides)
        assert "dev" in s.jira.url.lower()

    def test_missing_jira_username_raises(self):
        overrides = {
            "auth": {"env": "QA", "password": "token"},
        }
        with pytest.raises(ValueError, match="auth.username"):
            load_settings(overrides=overrides)

    def test_missing_jira_token_raises(self):
        overrides = {
            "auth": {"env": "QA", "username": "u@test.com"},
        }
        with pytest.raises(ValueError, match="auth.password"):
            load_settings(overrides=overrides)

    def test_recycles_jira_credentials_for_xray(self):
        overrides = {
            "auth": {"env": "QA", "username": "u@test.com", "password": "token"},
            # No xray section at all
        }
        s = load_settings(overrides=overrides)
        assert s.xray.client_id == "u@test.com"
        assert s.xray.client_secret == "token"

    def test_explicit_xray_is_ignored(self):
        overrides = {
            "auth": {"env": "QA", "username": "u@test.com", "password": "p"},
            "xray": {"client_id": "explicit_id", "client_secret": "explicit_secret"},
        }
        s = load_settings(overrides=overrides)
        # It should STILL use "u@test.com" and "p" because xray section is ignored
        assert s.xray.client_id == "u@test.com"
        assert s.xray.client_secret == "p"

    def test_missing_all_credentials_raises(self):
        with pytest.raises(ValueError) as exc_info:
            load_settings()
        msg = str(exc_info.value)
        assert "auth.username" in msg or "authentication credentials" in msg

    def test_setup_defaults_populated(self):
        overrides = self._valid_overrides()
        overrides["setup"] = {
            "test_plan_key": "PROJ-100",
        }
        s = load_settings(overrides=overrides)
        assert s.setup.test_plan_key == "PROJ-100"

    def test_sync_defaults_populated(self):
        overrides = self._valid_overrides()
        overrides["sync"] = {"status": "FAIL", "recursive": False}
        s = load_settings(overrides=overrides)
        assert s.sync.status == "FAIL"
        assert s.sync.recursive is False

    def test_setup_defaults_when_section_absent(self):
        s = load_settings(overrides=self._valid_overrides())
        assert s.setup.test_plan_key is None

    def test_sync_defaults_when_section_absent(self):
        s = load_settings(overrides=self._valid_overrides())
        assert s.sync.recursive is True
        assert s.sync.status is None


class TestLoadSettingsFromTOML:
    """Settings loaded from a TOML config file."""

    def test_loads_toml_file(self, valid_toml_config):
        s = load_settings(config_file=str(valid_toml_config))
        assert "qa" in s.jira.url.lower()
        assert s.jira.username == "user@example.com"
        # Xray section in TOML is now ignored or should be removed from test fixture
        assert s.xray.client_id == "user@example.com"

    def test_toml_setup_section(self, valid_toml_config):
        s = load_settings(config_file=str(valid_toml_config))
        assert s.setup.test_plan_key == "PROJ-100"
        assert s.setup.execution_summary == "Sprint Execution"

    def test_toml_sync_section(self, valid_toml_config):
        s = load_settings(config_file=str(valid_toml_config))
        assert s.sync.status == "PASS"
        assert s.sync.recursive is True

    def test_toml_project_section(self, valid_toml_config):
        s = load_settings(config_file=str(valid_toml_config))
        assert s.jira.project_key == "PROJ"

    def test_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_settings(config_file=str(tmp_path / "nonexistent.toml"))

    def test_toml_overridden_by_runtime_dict(self, valid_toml_config):
        s = load_settings(
            config_file=str(valid_toml_config),
            overrides={"auth": {"password": "overridden_token"}},
        )
        assert s.jira.password == "overridden_token"
        assert "qa" in s.jira.url.lower()


class TestLoadSettingsFromJSON:
    """Settings loaded from a JSON config file."""

    def test_loads_json_file(self, valid_json_config):
        s = load_settings(config_file=str(valid_json_config))
        assert s.jira.username == "user@example.com"
        assert s.xray.client_id == "user@example.com"

    def test_json_setup_section(self, valid_json_config):
        s = load_settings(config_file=str(valid_json_config))
        assert s.setup.test_plan_key == "PROJ-200"

    def test_json_sync_section(self, valid_json_config):
        s = load_settings(config_file=str(valid_json_config))
        assert s.sync.status == "FAIL"
        assert s.sync.recursive is False

    def test_json_project_section(self, valid_json_config):
        s = load_settings(config_file=str(valid_json_config))
        assert s.jira.project_key == "PROJ"


class TestJsonSchemaValidation:
    """The config file is validated against schema.json before loading."""

    def test_valid_toml_passes_schema(self, tmp_path):
        cfg = tmp_path / "pyjx2.toml"
        cfg.write_text("""
[auth]
env = "QA"
username = "u@example.com"
password = "token"
""")
        s = load_settings(config_file=str(cfg))
        assert s.jira.username == "u@example.com"

    def test_json_without_xray_section_recycles_and_passes(self, tmp_path):
        cfg = tmp_path / "pyjx2.json"
        cfg.write_text(
            json.dumps({"auth": {"env": "QA", "username": "u@test.com", "password": "token"}})
        )
        s = load_settings(config_file=str(cfg))
        assert s.jira.username == "u@test.com"
        assert s.xray.client_id == "u@test.com"


class TestEnvironmentVariableOverrides:
    """Environment variables override file and dict settings."""

    def test_env_vars_override_empty_config(self):
        env = {
            "PYJX2_AUTH_ENV": "DEV",
            "PYJX2_AUTH_USERNAME": "env_user",
            "PYJX2_AUTH_PASSWORD": "env_token",
            "PYJX2_PROJECT_KEY": "OPS",
        }
        with patch.dict(os.environ, env):
            s = load_settings()
        assert "dev" in s.jira.url.lower()
        assert s.jira.username == "env_user"
        assert s.xray.client_id == "env_user"
        assert s.jira.project_key == "OPS"

    def test_runtime_override_wins_over_env_var(self):
        env = {
            "PYJX2_AUTH_ENV": "DEV",
            "PYJX2_AUTH_USERNAME": "env_user",
            "PYJX2_AUTH_PASSWORD": "env_token",
        }
        with patch.dict(os.environ, env):
            s = load_settings(
                overrides={
                    "auth": {"env": "QA"},
                }
            )
        assert "qa" in s.jira.url.lower()

    def test_apply_env_overrides_returns_merged_dict(self):
        env = {"PYJX2_AUTH_ENV": "DEV", "PYJX2_PROJECT_KEY": "OPS"}
        with patch.dict(os.environ, env, clear=False):
            result = _apply_env_overrides({})
        assert result["auth"]["env"] == "DEV"
        assert result["project"]["key"] == "OPS"

    def test_apply_env_overrides_does_not_set_empty_values(self):
        result = _apply_env_overrides({})
        for section in result.values():
            for val in section.values():
                assert val is not None
