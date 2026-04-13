from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from .base import _StringValueObject


@dataclass(frozen=True)
class TestType(_StringValueObject):
    canonical: ClassVar[dict[str, str]] = {
        "manual": "Manual",
        "automated": "Automated",
        "test": "Test",
    }
    label: ClassVar[str] = "test type"

    @classmethod
    def _normalize(cls, value: str) -> str:
        normalized = super()._normalize(value).lower()
        return cls.canonical.get(normalized, normalized.title())

    @classmethod
    def _validate(cls, value: str) -> None:
        super()._validate(value)
        if value not in cls.canonical.values():
            raise ValueError(
                f"Invalid {cls.label}: {value!r}. Allowed values: {', '.join(cls.canonical.values())}"
            )

    @classmethod
    def allowed_values(cls) -> tuple[str, ...]:
        return tuple(cls.canonical.values())
