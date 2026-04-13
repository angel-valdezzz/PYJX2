from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Test:
    key: str
    summary: str
    test_type: str = "Manual"
    status: Optional[str] = None
    labels: list[str] = field(default_factory=list)
    description: Optional[str] = None
    steps: list[dict] = field(default_factory=list)
    precondition: Optional[str] = None
    issue_id: Optional[str] = None

    def __repr__(self) -> str:
        return f"Test(key={self.key!r}, summary={self.summary!r})"
