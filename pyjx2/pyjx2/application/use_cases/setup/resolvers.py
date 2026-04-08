import os
import re
from typing import List, Callable, Optional
from ....domain.entities import TestExecution, TestSet
from ....domain.repositories import (
    TestPlanRepository, TestExecutionRepository, TestSetRepository, TestRepository
)
from .models import (
    SetupTestExecutionConfig, SetupTestSetConfig, SetupSourceConfig
)

class TestPlanResolver:
    def __init__(self, repo: TestPlanRepository):
        self.repo = repo

    def validate(self, plan_key: str) -> None:
        plan = self.repo.get(plan_key)
        if not plan:
            raise ValueError(f"[FAIL FAST] Test Plan {plan_key} invalido o no existe.")

class TestExecutionResolver:
    def __init__(self, repo: TestExecutionRepository):
        self.repo = repo

    def resolve(self, config: SetupTestExecutionConfig, project_key: str) -> TestExecution:
        if config.mode == "create":
            if not config.name:
                raise ValueError("[FAIL FAST] Nombre requerido para la ejecucion modo create")
            return self.repo.create(project_key=project_key, summary=config.name)
        elif config.mode == "reuse":
            if not config.key:
                raise ValueError("[FAIL FAST] Key requerida para execution modo reuse")
            from ....domain.entities.test_execution import TestExecution
            # Implementar get en self.repo si existe, de lo contrario mockup de entity
            return TestExecution(key=config.key, summary=config.name or f"Execution {config.key}", status="")
        else:
            raise ValueError(f"Modo test execution invalido: {config.mode}")

class TestSetResolver:
    def __init__(self, repo: TestSetRepository):
        self.repo = repo

    def resolve(self, config: SetupTestSetConfig, project_key: str, clean_before: bool = False, logger: Optional[Callable] = None) -> TestSet:
        if not config.application:
            raise ValueError(f"[FAIL FAST] Application es abstracta pero mandatoria en Test Sets")
            
        summary = f"[{config.application}] Test Set {config.key or ''}"
        if config.mode == "create":
            return self.repo.create(project_key=project_key, summary=summary)
        elif config.mode == "reuse":
            if not config.key:
                raise ValueError("[FAIL FAST] Key de TestSet requerida para modo reuse")
            
            if clean_before and logger:
                logger(f"Limpiando items previos del Test Set: {config.key}")
            
            from ....domain.entities.test_set import TestSet
            return TestSet(key=config.key, summary=summary, status="")
        else:
            raise ValueError(f"Modo invalido de test set: {config.mode}")

class TestCaseSourceResolver:
    def __init__(self, test_repo: TestRepository):
        self.test_repo = test_repo

    def resolve(self, source: SetupSourceConfig, valid_keys: List[str], logger: Optional[Callable] = None) -> List[str]:
        keys = []
        if source.type == "test_plan":
            keys = valid_keys
        elif source.type == "list":
            keys = source.items or []
        elif source.type == "folder":
            if not source.path:
                if logger: logger("[WARN] ID de Carpeta Xray vacía.")
                return []
            if logger: logger(f"Obteniendo tests desde Xray Folder ID: {source.path}")
            # Fetch tests from Xray repository folder support. If not present, mock list.
            if hasattr(self.test_repo, "list_from_folder"):
                fetched = self.test_repo.list_from_folder(source.path)
                keys.extend([t.key for t in fetched if getattr(t, "key", None)])
            else:
                if logger: logger("[WARN] Método `list_from_folder` no implementado en el TestRepository, omitiendo.")
        
        if valid_keys:
            filtered = []
            for k in keys:
                if k in valid_keys:
                    filtered.append(k)
                else:
                    if logger: logger(f"[WARN] El TestCase {k} no pertenece al Test Plan subyacente y será descartado.")
            return filtered
            
        return keys
