from dataclasses import dataclass, field

from ..value_objects import TestKey, TestSetKey


@dataclass
class TestSet:
    key: TestSetKey
    summary: str
    issue_id: str | None = None
    test_keys: list[TestKey] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.key = TestSetKey.from_value(self.key)
        self.test_keys = [TestKey.from_value(key) for key in self.test_keys]

    def __repr__(self) -> str:
        return f"TestSet(key={self.key!r}, summary={self.summary!r})"
