from dataclasses import dataclass, field
from typing import Optional, Literal, List

from ....domain.entities.test_execution import TestExecution
from ....domain.entities.test_set import TestSet
from ....domain.entities.test import Test
from ....domain.value_objects import (
    Application,
    ExecutionKey,
    ProjectKey,
    TestKey,
    TestPlanKey,
    TestSetKey,
)


@dataclass
class SetupTestPlanConfig:
    key: TestPlanKey

    def __post_init__(self) -> None:
        self.key = TestPlanKey.from_value(self.key)


@dataclass
class SetupSourceConfig:
    type: Literal["folder", "list", "test_plan"]
    path: Optional[str] = None
    items: Optional[List[TestKey]] = None

    def __post_init__(self) -> None:
        if self.items is not None:
            self.items = [TestKey.from_value(item) for item in self.items]


@dataclass
class SetupTestSetConfig:
    mode: Literal["create", "reuse"]
    application: Application
    key: Optional[str] = None
    apply_source: bool = False
    source: Optional[SetupSourceConfig] = None
    # "clone" = clonar el test en QAX antes de añadirlo
    # "link" / "add" = agregar el test original directamente (sin clonar)
    test_case_mode: Literal["clone", "link", "add"] = "clone"

    def __post_init__(self) -> None:
        self.application = Application.from_value(self.application)
        if self.mode == "reuse" and self.key is not None:
            self.key = TestSetKey.from_value(self.key)


@dataclass
class SetupTestExecutionConfig:
    mode: Literal["create", "reuse"]
    test_sets: List[SetupTestSetConfig] = field(default_factory=list)
    key: Optional[ExecutionKey] = None
    name: Optional[str] = None

    def __post_init__(self) -> None:
        if self.mode == "reuse" and self.key is not None:
            self.key = ExecutionKey.from_value(self.key)


@dataclass
class SetupGlobalSettings:
    clean_test_set_before: bool = False
    on_missing_test_case: Literal["warn", "fail"] = "warn"
    on_duplicate: Literal["skip", "fail"] = "skip"
    on_empty_source: Literal["warn", "fail"] = "warn"


@dataclass
class SetupConfig:
    project_key: ProjectKey
    test_plan: SetupTestPlanConfig
    test_executions: List[SetupTestExecutionConfig] = field(default_factory=list)
    settings: SetupGlobalSettings = field(default_factory=SetupGlobalSettings)

    def __post_init__(self) -> None:
        self.project_key = ProjectKey.from_value(self.project_key)


@dataclass
class SetupResultMetrics:
    executions_created: int = 0
    executions_reused: int = 0
    sets_created: int = 0
    sets_reused: int = 0
    tests_cloned: int = 0
    tests_linked: int = 0   # alias interno; en modo "add" se incrementa igualmente
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def tests_added(self) -> int:
        """Alias de tests_linked para mostrar en UI cuando el modo es 'agregar'."""
        return self.tests_linked


@dataclass
class SetupResult:
    test_executions: List[TestExecution]
    test_sets: List[TestSet]
    tests: List[Test]
    metrics: SetupResultMetrics
