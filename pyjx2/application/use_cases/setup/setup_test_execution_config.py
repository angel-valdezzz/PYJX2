from dataclasses import dataclass, field
from typing import Literal

from ....domain.value_objects import ExecutionKey
from .setup_test_set_config import SetupTestSetConfig


@dataclass
class SetupTestExecutionConfig:
    mode: Literal["create", "reuse"]
    test_sets: list[SetupTestSetConfig] = field(default_factory=list)
    key: ExecutionKey | None = None
    name: str | None = None

    def __post_init__(self) -> None:
        if self.mode == "reuse" and self.key is not None:
            self.key = ExecutionKey.from_value(self.key)
