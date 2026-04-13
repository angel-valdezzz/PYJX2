from dataclasses import dataclass, field
from typing import List

from ....domain.value_objects import ProjectKey
from .setup_global_settings import SetupGlobalSettings
from .setup_test_execution_config import SetupTestExecutionConfig
from .setup_test_plan_config import SetupTestPlanConfig


@dataclass
class SetupConfig:
    project_key: ProjectKey
    test_plan: SetupTestPlanConfig
    test_executions: List[SetupTestExecutionConfig] = field(default_factory=list)
    settings: SetupGlobalSettings = field(default_factory=SetupGlobalSettings)

    def __post_init__(self) -> None:
        self.project_key = ProjectKey.from_value(self.project_key)
