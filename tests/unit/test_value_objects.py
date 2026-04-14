"""Unit tests for domain value objects."""
from __future__ import annotations

import pytest

from pyjx2.domain.value_objects import (
    Application,
    ExecutionKey,
    ProjectKey,
    Status,
    TestKey,
    TestPlanKey,
    TestSetKey,
    TestType,
    UploadMode,
)


@pytest.mark.parametrize(
    ("cls", "raw", "expected"),
    [
        (ProjectKey, " qax ", "QAX"),
        (TestKey, " qax-1 ", "QAX-1"),
        (ExecutionKey, " qax-2 ", "QAX-2"),
        (TestPlanKey, " qax-3 ", "QAX-3"),
        (TestSetKey, " qax-4 ", "QAX-4"),
        (Status, " pass ", "PASS"),
        (Application, " axa_web ", "AXA_WEB"),
        (UploadMode, "REPLACE", "replace"),
        (TestType, " manual ", "Manual"),
    ],
)
def test_value_objects_normalize_valid_values(cls, raw, expected):
    value = cls.from_value(raw)
    assert str(value) == expected
    assert value == cls.from_value(expected)


@pytest.mark.parametrize(
    ("cls", "raw", "error_type"),
    [
        (ProjectKey, "QAX-1", ValueError),
        (ProjectKey, "", ValueError),
        (ProjectKey, None, TypeError),
        (TestKey, "PROJ", ValueError),
        (TestKey, "123-PROJ", ValueError),
        (ExecutionKey, "", ValueError),
        (Status, "DONE", ValueError),
        (Application, "axa web", ValueError),
        (UploadMode, "merge", ValueError),
        (TestType, "exploratory", ValueError),
    ],
)
def test_value_objects_reject_invalid_values(cls, raw, error_type):
    with pytest.raises(error_type):
        cls.from_value(raw)


def test_allowed_values_are_exposed_from_enums_like_objects():
    assert Status.allowed_values() == ("PASS", "FAIL", "TODO", "EXECUTING", "ABORTED")
    assert UploadMode.allowed_values() == ("append", "replace")
    assert "Manual" in TestType.allowed_values()
