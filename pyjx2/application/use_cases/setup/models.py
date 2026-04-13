from dataclasses import dataclass, field
from typing import Optional, Literal, List

from ....domain.entities.test_execution import TestExecution
from ....domain.entities.test_set import TestSet
from ....domain.entities.test import Test


@dataclass
class SetupTestPlanConfig:
    key: str


@dataclass
class SetupSourceConfig:
    type: Literal["folder", "list"]
    path: Optional[str] = None
    items: Optional[List[str]] = None


@dataclass
class SetupTestSetConfig:
    mode: Literal["create", "reuse"]
    application: str
    key: Optional[str] = None
    apply_source: bool = False
    source: Optional[SetupSourceConfig] = None
    # "clone" = clonar el test en QAX antes de añadirlo
    # "link" / "add" = agregar el test original directamente (sin clonar)
    test_case_mode: Literal["clone", "link", "add"] = "clone"


@dataclass
class SetupTestExecutionConfig:
    mode: Literal["create", "reuse"]
    test_sets: List[SetupTestSetConfig] = field(default_factory=list)
    key: Optional[str] = None
    name: Optional[str] = None


@dataclass
class SetupGlobalSettings:
    clean_test_set_before: bool = False
    on_missing_test_case: Literal["warn", "fail"] = "warn"
    on_duplicate: Literal["skip", "fail"] = "skip"
    on_empty_source: Literal["warn", "fail"] = "warn"


@dataclass
class SetupConfig:
    project_key: str
    test_plan: SetupTestPlanConfig
    test_executions: List[SetupTestExecutionConfig] = field(default_factory=list)
    settings: SetupGlobalSettings = field(default_factory=SetupGlobalSettings)


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
