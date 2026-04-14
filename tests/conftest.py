"""
Shared pytest fixtures for pyjx2 test suite.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pyjx2.domain.entities import Test, TestExecution, TestPlan, TestSet
from pyjx2.infrastructure.config.settings import AuthSettings, ProjectSettings, Settings

# ── Settings fixture ────────────────────────────────────────────────────────


@pytest.fixture
def auth_settings():
    return AuthSettings(
        env="QA",
        username="user@test.com",
        password="test_token",
    )


@pytest.fixture
def project_settings():
    return ProjectSettings(key="PROJ")


@pytest.fixture
def settings(auth_settings, project_settings):
    return Settings(auth=auth_settings, project=project_settings)


# ── Entity fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def sample_test():
    return Test(key="PROJ-10", summary="Login test", test_type="Manual", labels=["smoke"])


@pytest.fixture
def sample_test_set():
    return TestSet(key="PROJ-20", summary="Sprint 1 Set", issue_id="100020")


@pytest.fixture
def sample_execution():
    return TestExecution(key="PROJ-30", summary="Sprint 1 Execution", issue_id="100030")


@pytest.fixture
def sample_test_plan():
    return TestPlan(key="PROJ-1", summary="Sprint 1 Plan", issue_id="100001")


# ── Mock repository factories ───────────────────────────────────────────────


@pytest.fixture
def mock_test_repo(sample_test):
    repo = MagicMock()
    repo.get.return_value = sample_test
    repo.create.return_value = Test(key="PROJ-11", summary="Created test")
    repo.clone.return_value = Test(key="PROJ-12", summary="[Clone] Login test")
    repo.update_status.return_value = True
    repo.upload_evidence.return_value = True
    repo.list_from_execution.return_value = [sample_test]
    repo.clear_evidence.return_value = True
    return repo


@pytest.fixture
def mock_test_set_repo(sample_test_set):
    repo = MagicMock()
    repo.get.return_value = sample_test_set
    repo.create.return_value = sample_test_set
    repo.update.return_value = sample_test_set
    repo.add_tests.return_value = True
    return repo


@pytest.fixture
def mock_exec_repo(sample_execution):
    repo = MagicMock()
    repo.get.return_value = sample_execution
    repo.create.return_value = sample_execution
    repo.update.return_value = sample_execution
    repo.add_test_set.return_value = True
    repo.get_tests.return_value = [
        Test(key="PROJ-10", summary="Login test", status="TODO"),
    ]
    return repo


@pytest.fixture
def mock_plan_repo(sample_test_plan):
    repo = MagicMock()
    repo.get.return_value = sample_test_plan
    repo.get_tests.return_value = [
        Test(key="PROJ-10", summary="Login test"),
        Test(key="PROJ-11", summary="Logout test"),
    ]
    return repo


# ── Filesystem fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def evidence_folder():
    """A temporary folder with evidence files named after test keys."""
    with tempfile.TemporaryDirectory() as tmpdir:
        folder = Path(tmpdir)
        (folder / "PROJ-10.png").write_text("screenshot data")
        (folder / "PROJ-11.pdf").write_text("pdf report")
        (folder / "unrelated-file.txt").write_text("no match")
        (folder / "subdir").mkdir()
        (folder / "subdir" / "PROJ-12.png").write_text("nested screenshot")
        yield folder


# ── Config file fixtures ────────────────────────────────────────────────────


@pytest.fixture
def valid_toml_config(tmp_path):
    cfg = tmp_path / "pyjx2.toml"
    cfg.write_text("""
[auth]
env = "QA"
username = "user@example.com"
password = "my_token"

[project]
key = "PROJ"

[setup]
test_plan_key = "PROJ-100"
execution_summary = "Sprint Execution"
test_set_summary = "Sprint Set"
reuse_tests = false

[sync]
execution_key = "PROJ-200"
folder = "./evidence"
status = "PASS"
recursive = true
""")
    return cfg


@pytest.fixture
def valid_json_config(tmp_path):
    cfg = tmp_path / "pyjx2.json"
    cfg.write_text(
        json.dumps(
            {
                "auth": {
                    "env": "QA",
                    "username": "user@example.com",
                    "password": "my_json_token",
                },
                "project": {
                    "key": "PROJ",
                },
                "setup": {
                    "test_plan_key": "PROJ-200",
                    "reuse_tests": True,
                },
                "sync": {
                    "status": "FAIL",
                    "recursive": False,
                },
            },
            indent=2,
        )
    )
    return cfg
