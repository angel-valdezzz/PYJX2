from dataclasses import dataclass
from typing import List, Literal, Optional

from ....domain.value_objects import TestKey


@dataclass
class SetupSourceConfig:
    type: Literal["folder", "list", "test_plan"]
    path: Optional[str] = None
    items: Optional[List[TestKey]] = None

    def __post_init__(self) -> None:
        self.path = self.path.strip() if self.path else None
        if self.items is not None:
            self.items = [TestKey.from_value(item) for item in self.items]
        self._validate_shape()

    def _validate_shape(self) -> None:
        if self.type == "test_plan":
            if self.path or self.items:
                raise ValueError("SetupSourceConfig(type='test_plan') does not accept path or items")
            return

        if self.type == "list":
            if self.path:
                raise ValueError("SetupSourceConfig(type='list') does not accept path")
            if not self.items:
                raise ValueError("SetupSourceConfig(type='list') requires items")
            return

        if self.type == "folder":
            if self.items:
                raise ValueError("SetupSourceConfig(type='folder') does not accept items")
            if not self.path:
                raise ValueError("SetupSourceConfig(type='folder') requires path")
