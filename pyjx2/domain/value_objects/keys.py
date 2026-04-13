from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar

from .base import _StringValueObject


@dataclass(frozen=True)
class _IssueKey(_StringValueObject):
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"^[A-Z][A-Z0-9_]*-\d+$")
    label: ClassVar[str] = "issue key"

    @classmethod
    def _normalize(cls, value: str) -> str:
        return super()._normalize(value).upper()

    @classmethod
    def _validate(cls, value: str) -> None:
        super()._validate(value)
        if not cls.pattern.fullmatch(value):
            raise ValueError(f"Invalid {cls.label}: {value!r}. Expected format ABC-123")


@dataclass(frozen=True)
class ProjectKey(_StringValueObject):
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"^[A-Z][A-Z0-9_]*$")
    label: ClassVar[str] = "project key"

    @classmethod
    def _normalize(cls, value: str) -> str:
        return super()._normalize(value).upper()

    @classmethod
    def _validate(cls, value: str) -> None:
        super()._validate(value)
        if not cls.pattern.fullmatch(value):
            raise ValueError(f"Invalid {cls.label}: {value!r}. Expected format ABC")


@dataclass(frozen=True)
class TestKey(_IssueKey):
    label: ClassVar[str] = "test key"


@dataclass(frozen=True)
class ExecutionKey(_IssueKey):
    label: ClassVar[str] = "execution key"


@dataclass(frozen=True)
class TestPlanKey(_IssueKey):
    label: ClassVar[str] = "test plan key"


@dataclass(frozen=True)
class TestSetKey(_IssueKey):
    label: ClassVar[str] = "test set key"
