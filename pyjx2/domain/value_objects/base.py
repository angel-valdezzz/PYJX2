from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, TypeVar, cast

TValueObject = TypeVar("TValueObject", bound="_StringValueObject")


@dataclass(frozen=True)
class _StringValueObject:
    value: str
    label: ClassVar[str] = "value"

    def __post_init__(self) -> None:
        normalized = self._normalize(self.value)
        self._validate(normalized)
        object.__setattr__(self, "value", normalized)

    @classmethod
    def from_value(cls: type[TValueObject], value: str | TValueObject) -> TValueObject:
        if isinstance(value, cls):
            return value
        return cls(cast(str, value))

    @classmethod
    def _normalize(cls, value: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{cls.label} must be a string")
        return value.strip()

    @classmethod
    def _validate(cls, value: str) -> None:
        if not value:
            raise ValueError(f"{cls.label} cannot be empty")

    def __str__(self) -> str:
        return self.value
