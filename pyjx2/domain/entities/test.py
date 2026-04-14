from dataclasses import dataclass, field

from ..value_objects import Status, TestKey, TestType


@dataclass
class Test:
    key: TestKey
    summary: str
    test_type: TestType = field(default_factory=lambda: TestType.from_value("Manual"))
    status: Status | None = None
    labels: list[str] = field(default_factory=list)
    description: str | None = None
    steps: list[dict] = field(default_factory=list)
    precondition: str | None = None
    issue_id: str | None = None

    def __post_init__(self) -> None:
        self.key = TestKey.from_value(self.key)
        self.test_type = TestType.from_value(self.test_type)
        if self.status is not None:
            self.status = Status.from_value(self.status)

    def __repr__(self) -> str:
        return f"Test(key={self.key!r}, summary={self.summary!r})"
