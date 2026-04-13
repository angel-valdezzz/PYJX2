from dataclasses import dataclass, field
from typing import List


@dataclass
class SetupResultMetrics:
    executions_created: int = 0
    executions_reused: int = 0
    sets_created: int = 0
    sets_reused: int = 0
    tests_cloned: int = 0
    tests_linked: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def tests_added(self) -> int:
        return self.tests_linked
