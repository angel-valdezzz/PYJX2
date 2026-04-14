from collections.abc import Callable

from ....domain.entities import TestSet
from ....domain.repositories import TestSetRepository
from ....domain.value_objects import ProjectKey, TestSetKey
from .setup_test_set_config import SetupTestSetConfig


class TestSetResolver:
    def __init__(self, repo: TestSetRepository):
        self.repo = repo

    def resolve(
        self,
        config: SetupTestSetConfig,
        project_key: ProjectKey,
        clean_before: bool = False,
        logger: Callable | None = None,
    ) -> TestSet:
        if not str(config.application):
            raise ValueError("[FAIL FAST] Application es abstracta pero mandatoria en Test Sets")

        summary = f"[{config.application}] Test Set {config.key or ''}"
        if config.mode == "create":
            return self.repo.create(project_key=project_key, summary=summary)
        if config.mode == "reuse":
            if not config.key:
                raise ValueError("[FAIL FAST] Key de TestSet requerida para modo reuse")
            existing = self.repo.get(TestSetKey.from_value(config.key))
            if not existing:
                raise ValueError(f"[FAIL FAST] Test Set {config.key} invalido o no existe.")
            if clean_before and logger:
                logger(f"Limpiando items previos del Test Set: {config.key}")
            return existing
        raise ValueError(f"Modo invalido de test set: {config.mode}")
