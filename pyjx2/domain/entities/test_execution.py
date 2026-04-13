from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TestExecution:
    key: str
    summary: str
    issue_id: Optional[str] = None
    test_set_keys: list[str] = field(default_factory=list)
    test_keys: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"TestExecution(key={self.key!r}, summary={self.summary!r})"
