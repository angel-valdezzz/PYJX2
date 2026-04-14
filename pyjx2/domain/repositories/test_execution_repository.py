from abc import ABC, abstractmethod

from ..entities import Test, TestExecution
from ..value_objects import ExecutionKey, ProjectKey, TestSetKey


class TestExecutionRepository(ABC):
    @abstractmethod
    def get(self, key: ExecutionKey) -> TestExecution | None: ...

    @abstractmethod
    def create(self, project_key: ProjectKey, summary: str, **kwargs) -> TestExecution: ...

    @abstractmethod
    def update(self, key: ExecutionKey, **kwargs) -> TestExecution: ...

    @abstractmethod
    def add_test_set(self, key: ExecutionKey, test_set_key: TestSetKey) -> bool: ...

    @abstractmethod
    def get_tests(self, key: ExecutionKey) -> list[Test]: ...
