"""
Acceptance tests for configuration loading across different formats and sources.
Validates that the full config pipeline (file + env vars + overrides) works correctly.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from pyjx2.infrastructure.config.settings import load_settings


class TestConfigFileDiscovery:
    """Auto-discovery of pyjx2.toml / pyjx2.json in the current directory."""

    def test_discovers_toml_in_cwd(self, tmp_path):
        toml_cfg = tmp_path / "pyjx2.toml"
        toml_cfg.write_text("""
[jira]
url = "https://discovered.atlassian.net"
username = "found@example.com"
api_token = "found_token"

[xray]
client_id = "found_cid"
client_secret = "found_csec"
""")
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            s = load_settings()
            assert s.jira.url == "https://discovered.atlassian.net"
        finally:
            os.chdir(original_cwd)

    def test_discovers_json_in_cwd(self, tmp_path):
        json_cfg = tmp_path / "pyjx2.json"
        json_cfg.write_text(json.dumps({
            "jira": {
                "url": "https://json-discovered.atlassian.net",
                "username": "json@example.com",
                "api_token": "json_token",
            },
            "xray": {"client_id": "jcid", "client_secret": "jcsec"},
        }))
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            s = load_settings()
            assert s.jira.url == "https://json-discovered.atlassian.net"
        finally:
            os.chdir(original_cwd)

    def test_explicit_file_overrides_discovery(self, tmp_path, valid_toml_config):
        other = tmp_path / "other.toml"
        other.write_text("""
[jira]
url = "https://other.atlassian.net"
username = "other@example.com"
api_token = "other_token"

[xray]
client_id = "ocid"
client_secret = "ocsec"
""")
        s = load_settings(config_file=str(other))
        assert s.jira.url == "https://other.atlassian.net"


class TestConfigPrecedenceChain:
    """
    Precedence order (highest to lowest):
    runtime overrides > environment variables > config file > defaults
    """

    def test_runtime_override_beats_config_file(self, valid_toml_config):
        s = load_settings(
            config_file=str(valid_toml_config),
            overrides={"jira": {"api_token": "runtime_token"}},
        )
        assert s.jira.api_token == "runtime_token"

    def test_env_var_beats_config_file(self, valid_toml_config):
        with patch.dict(os.environ, {"PYJX2_JIRA_API_TOKEN": "env_token"}):
            s = load_settings(config_file=str(valid_toml_config))
        assert s.jira.api_token == "env_token"

    def test_runtime_override_beats_env_var(self, valid_toml_config):
        with patch.dict(os.environ, {"PYJX2_JIRA_API_TOKEN": "env_token"}):
            s = load_settings(
                config_file=str(valid_toml_config),
                overrides={"jira": {"api_token": "runtime_token"}},
            )
        assert s.jira.api_token == "runtime_token"

    def test_config_file_values_persist_when_not_overridden(self, valid_toml_config):
        s = load_settings(
            config_file=str(valid_toml_config),
            overrides={"jira": {"api_token": "new_token"}},
        )
        assert s.jira.url == "https://example.atlassian.net"
        assert s.jira.username == "user@example.com"


class TestTOMLFormat:
    """TOML-specific loading behavior."""

    def test_loads_all_sections_from_toml(self, valid_toml_config):
        s = load_settings(config_file=str(valid_toml_config))
        assert s.jira.url is not None
        assert s.xray.client_id is not None
        assert s.setup.test_plan_key is not None
        assert s.sync.status is not None

    def test_toml_boolean_values_parsed_correctly(self, valid_toml_config):
        s = load_settings(config_file=str(valid_toml_config))
        assert isinstance(s.setup.reuse_tests, bool)
        assert isinstance(s.sync.recursive, bool)

    def test_partial_toml_without_setup_section(self, tmp_path):
        cfg = tmp_path / "pyjx2.toml"
        cfg.write_text("""
[jira]
url = "https://x.atlassian.net"
username = "u"
api_token = "t"

[xray]
client_id = "c"
client_secret = "s"
""")
        s = load_settings(config_file=str(cfg))
        assert s.setup.reuse_tests is False
        assert s.setup.test_plan_key is None


class TestJSONFormat:
    """JSON-specific loading behavior."""

    def test_loads_all_sections_from_json(self, valid_json_config):
        s = load_settings(config_file=str(valid_json_config))
        assert s.jira.username == "user@example.com"
        assert s.xray.client_id == "json_client"

    def test_json_boolean_values_parsed_correctly(self, valid_json_config):
        s = load_settings(config_file=str(valid_json_config))
        assert isinstance(s.setup.reuse_tests, bool)
        assert isinstance(s.sync.recursive, bool)

    def test_unsupported_extension_raises(self, tmp_path):
        cfg = tmp_path / "pyjx2.yaml"
        cfg.write_text("jira:\n  url: test\n")
        with pytest.raises((ValueError, Exception)):
            load_settings(config_file=str(cfg))


class TestSchemaValidation:
    """JSON Schema enforces structure of both TOML and JSON configs."""

    def test_rejects_toml_with_invalid_sync_status(self, tmp_path):
        cfg = tmp_path / "pyjx2.toml"
        cfg.write_text("""
[jira]
url = "https://x.atlassian.net"
username = "u"
api_token = "t"

[xray]
client_id = "c"
client_secret = "s"

[sync]
status = "NOT_A_VALID_STATUS"
""")
        with pytest.raises(Exception):
            load_settings(config_file=str(cfg))

    def test_rejects_json_missing_required_jira_fields(self, tmp_path):
        cfg = tmp_path / "pyjx2.json"
        cfg.write_text(json.dumps({
            "jira": {"url": "https://x.atlassian.net"},
            "xray": {"client_id": "c", "client_secret": "s"},
        }))
        with pytest.raises(Exception):
            load_settings(config_file=str(cfg))

    def test_accepts_minimal_valid_toml(self, tmp_path):
        cfg = tmp_path / "pyjx2.toml"
        cfg.write_text("""
[jira]
url = "https://x.atlassian.net"
username = "u"
api_token = "t"

[xray]
client_id = "c"
client_secret = "s"
""")
        s = load_settings(config_file=str(cfg))
        assert s.jira.url == "https://x.atlassian.net"
