from dataclasses import dataclass

from ....domain.value_objects import TestPlanKey


@dataclass
class SetupTestPlanConfig:
    key: TestPlanKey

    def __post_init__(self) -> None:
        self.key = TestPlanKey.from_value(self.key)
