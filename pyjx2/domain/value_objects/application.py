from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar

from .base import _StringValueObject


@dataclass(frozen=True)
class Application(_StringValueObject):
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"^[A-Z0-9_-]+$")
    label: ClassVar[str] = "application"

    @classmethod
    def _normalize(cls, value: str) -> str:
        return super()._normalize(value).upper()

    @classmethod
    def _validate(cls, value: str) -> None:
        super()._validate(value)
        if not cls.pattern.fullmatch(value):
            raise ValueError(
                f"Invalid {cls.label}: {value!r}. Allowed characters: A-Z, 0-9, _ and -"
            )
