from abc import ABC, abstractmethod
from typing import Optional

from ..entities import Test
from ..value_objects import ExecutionKey, ProjectKey, Status, TestKey, TestType


class TestRepository(ABC):
    @abstractmethod
    def get(self, key: TestKey) -> Optional[Test]:
        ...

    @abstractmethod
    def create(
        self,
        project_key: ProjectKey,
        summary: str,
        test_type: TestType = TestType.from_value("Manual"),
        **kwargs,
    ) -> Test:
        ...

    @abstractmethod
    def clone(self, source_key: TestKey, target_project_key: ProjectKey) -> Test:
        ...

    @abstractmethod
    def update_labels(self, key: TestKey, new_labels: list[str]) -> bool:
        ...

    @abstractmethod
    def update_status(self, execution_key: ExecutionKey, test_key: TestKey, status: Status) -> bool:
        ...

    @abstractmethod
    def upload_evidence(self, execution_key: ExecutionKey, test_key: TestKey, file_path: str) -> bool:
        ...

    @abstractmethod
    def list_from_execution(self, execution_key: ExecutionKey) -> list[Test]:
        ...

    @abstractmethod
    def clear_evidence(self, execution_key: ExecutionKey, test_key: TestKey) -> bool:
        ...
