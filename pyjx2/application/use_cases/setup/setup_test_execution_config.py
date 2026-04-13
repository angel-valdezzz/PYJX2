from dataclasses import dataclass, field
from typing import List, Literal, Optional

from ....domain.value_objects import ExecutionKey
from .setup_test_set_config import SetupTestSetConfig


@dataclass
class SetupTestExecutionConfig:
    mode: Literal["create", "reuse"]
    test_sets: List[SetupTestSetConfig] = field(default_factory=list)
    key: Optional[ExecutionKey] = None
    name: Optional[str] = None

    def __post_init__(self) -> None:
        if self.mode == "reuse" and self.key is not None:
            self.key = ExecutionKey.from_value(self.key)
