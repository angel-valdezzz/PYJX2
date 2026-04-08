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
env = "QA"
username = "found@example.com"
password = "found_token"

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
            "env": "DEV",
            "username": "json@example.com",
            "password": "json_token",
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
env = "QA"
username = "user@example.com"
password = "token"

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
        "env": "QA",
        "username": "user@example.com",
        "password": "token",
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
        "PYJX2_JIRA_ENV": "",
        "PYJX2_JIRA_USERNAME": "",
        "PYJX2_JIRA_PASSWORD": "",
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


@when(parsers.parse('I load settings from that file with password override "{password}"'))
def _(ctx, password):
    try:
        s = load_settings(
            config_file=ctx["config_file"],
            overrides={"jira": {"password": password}},
        )
        ctx["settings"] = s
        ctx["error"] = None
    except Exception as e:
        ctx["settings"] = None
        ctx["error"] = e


# ── Then ──────────────────────────────────────────────────────────────────────

@then(parsers.parse('the Jira environment is "{env}"'))
def _(ctx, env):
    assert ctx["settings"] is not None, f"Settings not loaded: {ctx.get('error')}"
    assert ctx["settings"].jira.env.upper() == env.upper(), (
        f"Expected Jira env '{env}', got '{ctx['settings'].jira.env}'"
    )


@then(parsers.parse('the Jira environment is still "{env}"'))
def _(ctx, env):
    assert ctx["settings"].jira.env.upper() == env.upper()


@then(parsers.parse('the Jira username is "{username}"'))
def _(ctx, username):
    assert ctx["settings"].jira.username == username


@then(parsers.parse('the Jira password is "{password}"'))
def _(ctx, password):
    assert ctx["settings"].jira.password == password


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
