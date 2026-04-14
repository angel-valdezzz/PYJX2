from abc import ABC, abstractmethod

from ..entities import Test, TestPlan
from ..value_objects import TestPlanKey


class TestPlanRepository(ABC):
    @abstractmethod
    def get(self, key: TestPlanKey) -> TestPlan | None: ...

    @abstractmethod
    def get_tests(self, key: TestPlanKey) -> list[Test]: ...
