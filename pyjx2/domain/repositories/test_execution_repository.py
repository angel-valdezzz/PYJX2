from abc import ABC, abstractmethod
from typing import Optional
from ..entities import TestExecution


class TestExecutionRepository(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[TestExecution]:
        ...

    @abstractmethod
    def create(self, project_key: str, summary: str, **kwargs) -> TestExecution:
        ...

    @abstractmethod
    def update(self, key: str, **kwargs) -> TestExecution:
        ...

    @abstractmethod
    def add_test_set(self, key: str, test_set_key: str) -> bool:
        ...

    @abstractmethod
    def get_tests(self, key: str) -> list[dict]:
        ...
