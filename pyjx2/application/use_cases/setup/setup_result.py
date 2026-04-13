from dataclasses import dataclass

from ....domain.entities.test import Test
from ....domain.entities.test_execution import TestExecution
from ....domain.entities.test_set import TestSet
from .setup_result_metrics import SetupResultMetrics


@dataclass
class SetupResult:
    test_executions: list[TestExecution]
    test_sets: list[TestSet]
    tests: list[Test]
    metrics: SetupResultMetrics
