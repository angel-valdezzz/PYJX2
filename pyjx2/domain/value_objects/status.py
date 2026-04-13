from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from .base import _StringValueObject


@dataclass(frozen=True)
class Status(_StringValueObject):
    allowed: ClassVar[tuple[str, ...]] = ("PASS", "FAIL", "TODO", "EXECUTING", "ABORTED")
    label: ClassVar[str] = "status"

    @classmethod
    def _normalize(cls, value: str) -> str:
        return super()._normalize(value).upper()

    @classmethod
    def _validate(cls, value: str) -> None:
        super()._validate(value)
        if value not in cls.allowed:
            raise ValueError(f"Invalid {cls.label}: {value!r}. Allowed values: {', '.join(cls.allowed)}")

    @classmethod
    def allowed_values(cls) -> tuple[str, ...]:
        return cls.allowed
