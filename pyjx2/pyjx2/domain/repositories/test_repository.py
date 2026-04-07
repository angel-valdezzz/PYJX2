from abc import ABC, abstractmethod
from typing import Optional
from ..entities import Test


class TestRepository(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[Test]:
        ...

    @abstractmethod
    def create(self, project_key: str, summary: str, test_type: str = "Manual", **kwargs) -> Test:
        ...

    @abstractmethod
    def clone(self, source_key: str, target_project_key: str) -> Test:
        ...

    @abstractmethod
    def update_status(self, execution_key: str, test_key: str, status: str) -> bool:
        ...

    @abstractmethod
    def upload_evidence(self, execution_key: str, test_key: str, file_path: str) -> bool:
        ...

    @abstractmethod
    def list_from_execution(self, execution_key: str) -> list[Test]:
        ...
