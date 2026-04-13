from abc import ABC, abstractmethod
from typing import Optional
from ..entities import TestSet


class TestSetRepository(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[TestSet]:
        ...

    @abstractmethod
    def create(self, project_key: str, summary: str) -> TestSet:
        ...

    @abstractmethod
    def update(self, key: str, **kwargs) -> TestSet:
        ...

    @abstractmethod
    def add_tests(self, key: str, test_keys: list[str]) -> bool:
        ...
