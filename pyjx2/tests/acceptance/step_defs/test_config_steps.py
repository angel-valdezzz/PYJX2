"""
Step definitions for: features/config_flow.feature
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from pyjx2.infrastructure.config.settings import load_settings

scenarios("../features/config_flow.feature")


# ── Given ─────────────────────────────────────────────────────────────────────

@given("a TOML config file with valid credentials")
def _(ctx, valid_toml_config):
    ctx["config_file"] = str(valid_toml_config)


@given("a JSON config file with valid credentials")
def _(ctx, valid_json_config):
    ctx["config_file"] = str(valid_json_config)


@given(parsers.parse('a "pyjx2.toml" file exists in the current directory'))
def _(ctx, tmp_path, monkeypatch):
    cfg = tmp_path / "pyjx2.toml"
    cfg.write_text("""
[jira]
url = "https://discovered.atlassian.net"
username = "found@example.com"
api_token = "found_token"

[xray]
client_id = "found_cid"
client_secret = "found_csec"
""")
    monkeypatch.chdir(tmp_path)
    ctx["config_file"] = None


@given(parsers.parse('a "pyjx2.json" file exists in the current directory'))
def _(ctx, tmp_path, monkeypatch):
    cfg = tmp_path / "pyjx2.json"
    cfg.write_text(json.dumps({
        "jira": {
            "url": "https://json-discovered.atlassian.net",
            "username": "json@example.com",
            "api_token": "json_token",
        },
        "xray": {"client_id": "jcid", "client_secret": "jcsec"},
    }))
    monkeypatch.chdir(tmp_path)
    ctx["config_file"] = None


@given(parsers.parse('the environment variable "{var}" is set to "{value}"'))
def _(ctx, var, value):
    ctx.setdefault("env_overrides", {})[var] = value


@given(parsers.parse('a TOML config file with invalid sync status "{status}"'))
def _(ctx, tmp_path, status):
    cfg = tmp_path / "pyjx2.toml"
    cfg.write_text(f"""
[jira]
url = "https://example.atlassian.net"
username = "user@example.com"
api_token = "token"

[xray]
client_id = "cid"
client_secret = "csec"

[sync]
status = "{status}"
""")
    ctx["config_file"] = str(cfg)


@given(parsers.parse('a JSON config file missing "{field}" in the jira section'))
def _(ctx, tmp_path, field):
    jira = {
        "url": "https://example.atlassian.net",
        "username": "user@example.com",
        "api_token": "token",
    }
    del jira[field]
    cfg = tmp_path / "pyjx2.json"
    cfg.write_text(json.dumps({
        "jira": jira,
        "xray": {"client_id": "c", "client_secret": "s"},
    }))
    ctx["config_file"] = str(cfg)


# ── When ──────────────────────────────────────────────────────────────────────

@when("I load settings from that file")
def _(ctx):
    env_overrides = ctx.get("env_overrides", {})
    try:
        with patch.dict(os.environ, env_overrides):
            s = load_settings(config_file=ctx.get("config_file"))
        ctx["settings"] = s
        ctx["error"] = None
    except Exception as e:
        ctx["settings"] = None
        ctx["error"] = e


@when("I load settings without specifying a file")
def _(ctx):
    try:
        s = load_settings()
        ctx["settings"] = s
        ctx["error"] = None
    except Exception as e:
        ctx["settings"] = None
        ctx["error"] = e


@when("I load settings with no configuration at all")
def _(ctx):
    env_clear = {
        "PYJX2_JIRA_URL": "",
        "PYJX2_JIRA_USERNAME": "",
        "PYJX2_JIRA_API_TOKEN": "",
        "PYJX2_XRAY_CLIENT_ID": "",
        "PYJX2_XRAY_CLIENT_SECRET": "",
    }
    try:
        with patch.dict(os.environ, env_clear, clear=False):
            s = load_settings()
        ctx["settings"] = s
        ctx["error"] = None
    except Exception as e:
        ctx["settings"] = None
        ctx["error"] = e


@when(parsers.parse('I load settings from that file with api_token override "{token}"'))
def _(ctx, token):
    try:
        s = load_settings(
            config_file=ctx["config_file"],
            overrides={"jira": {"api_token": token}},
        )
        ctx["settings"] = s
        ctx["error"] = None
    except Exception as e:
        ctx["settings"] = None
        ctx["error"] = e


# ── Then ──────────────────────────────────────────────────────────────────────

@then(parsers.parse('the Jira URL is "{url}"'))
def _(ctx, url):
    assert ctx["settings"] is not None, f"Settings not loaded: {ctx.get('error')}"
    assert ctx["settings"].jira.url == url, (
        f"Expected Jira URL '{url}', got '{ctx['settings'].jira.url}'"
    )


@then(parsers.parse('the Jira URL is still "{url}"'))
def _(ctx, url):
    assert ctx["settings"].jira.url == url


@then(parsers.parse('the Jira username is "{username}"'))
def _(ctx, username):
    assert ctx["settings"].jira.username == username


@then(parsers.parse('the Jira API token is "{token}"'))
def _(ctx, token):
    assert ctx["settings"].jira.api_token == token


@then(parsers.parse('the Xray client ID is "{client_id}"'))
def _(ctx, client_id):
    assert ctx["settings"].xray.client_id == client_id


@then(parsers.parse('the setup test plan key is "{key}"'))
def _(ctx, key):
    assert ctx["settings"].setup.test_plan_key == key


@then(parsers.parse('the sync status is "{status}"'))
def _(ctx, status):
    assert ctx["settings"].sync.status == status


@then(parsers.parse("the setup reuse_tests is {value}"))
def _(ctx, value):
    expected = value.strip() == "True"
    assert ctx["settings"].setup.reuse_tests is expected


@then(parsers.parse("the sync recursive is {value}"))
def _(ctx, value):
    expected = value.strip() == "True"
    assert ctx["settings"].sync.recursive is expected


@then(parsers.parse('a "{error_type}" is raised'))
def _(ctx, error_type):
    assert ctx["error"] is not None, f"Expected {error_type} but no error was raised"
    assert type(ctx["error"]).__name__ == error_type, (
        f"Expected {error_type}, got {type(ctx['error']).__name__}: {ctx['error']}"
    )


@then(parsers.parse('the error message mentions "{field}"'))
def _(ctx, field):
    assert ctx["error"] is not None
    assert field in str(ctx["error"]), (
        f"Expected '{field}' in error: {ctx['error']}"
    )


@then("a schema validation error is raised")
def _(ctx):
    assert ctx["error"] is not None, "Expected a schema validation error but none was raised"
    err_type = type(ctx["error"]).__name__
    assert err_type in ("ValidationError", "ValueError", "jsonschema.exceptions.ValidationError"), (
        f"Expected a schema validation error, got {err_type}: {ctx['error']}"
    )
