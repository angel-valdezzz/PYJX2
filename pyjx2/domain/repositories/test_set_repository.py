from abc import ABC, abstractmethod
from typing import Optional

from ..entities import TestSet
from ..value_objects import ProjectKey, TestKey, TestSetKey


class TestSetRepository(ABC):
    @abstractmethod
    def get(self, key: TestSetKey) -> Optional[TestSet]:
        ...

    @abstractmethod
    def create(self, project_key: ProjectKey, summary: str) -> TestSet:
        ...

    @abstractmethod
    def update(self, key: TestSetKey, **kwargs) -> TestSet:
        ...

    @abstractmethod
    def add_tests(self, key: TestSetKey, test_keys: list[TestKey]) -> bool:
        ...
