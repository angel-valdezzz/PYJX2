from abc import ABC, abstractmethod
from typing import Optional

from ..entities import TestPlan
from ..value_objects import TestPlanKey


class TestPlanRepository(ABC):
    @abstractmethod
    def get(self, key: TestPlanKey) -> Optional[TestPlan]:
        ...

    @abstractmethod
    def get_tests(self, key: TestPlanKey) -> list[dict]:
        ...
