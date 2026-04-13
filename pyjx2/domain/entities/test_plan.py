from dataclasses import dataclass, field
from typing import Optional

from ..value_objects import TestKey, TestPlanKey


@dataclass
class TestPlan:
    key: TestPlanKey
    summary: str
    issue_id: Optional[str] = None
    test_keys: list[TestKey] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.key = TestPlanKey.from_value(self.key)
        self.test_keys = [TestKey.from_value(key) for key in self.test_keys]

    def __repr__(self) -> str:
        return f"TestPlan(key={self.key!r}, summary={self.summary!r})"
