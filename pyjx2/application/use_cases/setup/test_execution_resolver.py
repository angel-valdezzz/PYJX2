from ....domain.entities import TestExecution
from ....domain.repositories import TestExecutionRepository
from ....domain.value_objects import ProjectKey
from .setup_test_execution_config import SetupTestExecutionConfig


class TestExecutionResolver:
    def __init__(self, repo: TestExecutionRepository):
        self.repo = repo

    def resolve(self, config: SetupTestExecutionConfig, project_key: ProjectKey) -> TestExecution:
        if config.mode == "create":
            if not config.name:
                raise ValueError("[FAIL FAST] Nombre requerido para la ejecucion modo create")
            return self.repo.create(project_key=project_key, summary=config.name)
        if config.mode == "reuse":
            if not config.key:
                raise ValueError("[FAIL FAST] Key requerida para execution modo reuse")
            execution = self.repo.get(config.key)
            if not execution:
                raise ValueError(f"[FAIL FAST] Test Execution {config.key} invalida o no existe.")
            return execution
        raise ValueError(f"Modo test execution invalido: {config.mode}")
