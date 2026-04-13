from abc import ABC, abstractmethod
from typing import Optional
from ..entities import TestPlan


class TestPlanRepository(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[TestPlan]:
        ...

    @abstractmethod
    def get_tests(self, key: str) -> list[dict]:
        ...
