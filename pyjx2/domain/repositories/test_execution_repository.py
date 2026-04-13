from abc import ABC, abstractmethod
from typing import Optional

from ..entities import TestExecution
from ..value_objects import ExecutionKey, ProjectKey, TestSetKey


class TestExecutionRepository(ABC):
    @abstractmethod
    def get(self, key: ExecutionKey) -> Optional[TestExecution]:
        ...

    @abstractmethod
    def create(self, project_key: ProjectKey, summary: str, **kwargs) -> TestExecution:
        ...

    @abstractmethod
    def update(self, key: ExecutionKey, **kwargs) -> TestExecution:
        ...

    @abstractmethod
    def add_test_set(self, key: ExecutionKey, test_set_key: TestSetKey) -> bool:
        ...

    @abstractmethod
    def get_tests(self, key: ExecutionKey) -> list[dict]:
        ...
