from dataclasses import dataclass, field
from typing import Optional

from ..value_objects import ExecutionKey, TestKey, TestSetKey


@dataclass
class TestExecution:
    key: ExecutionKey
    summary: str
    issue_id: Optional[str] = None
    test_set_keys: list[TestSetKey] = field(default_factory=list)
    test_keys: list[TestKey] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.key = ExecutionKey.from_value(self.key)
        self.test_set_keys = [TestSetKey.from_value(key) for key in self.test_set_keys]
        self.test_keys = [TestKey.from_value(key) for key in self.test_keys]

    def __repr__(self) -> str:
        return f"TestExecution(key={self.key!r}, summary={self.summary!r})"
