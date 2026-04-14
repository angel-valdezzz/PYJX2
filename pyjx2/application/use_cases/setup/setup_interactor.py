from typing import Callable, Optional
from .setup_config import SetupConfig
from .setup_result import SetupResult
from .setup_result_metrics import SetupResultMetrics
from .test_case_source_resolver import TestCaseSourceResolver
from .test_execution_resolver import TestExecutionResolver
from .test_plan_resolver import TestPlanResolver
from .test_set_resolver import TestSetResolver
from ....domain.repositories import (
    TestPlanRepository, TestExecutionRepository, TestSetRepository, TestRepository
)
from ....domain.value_objects import TestKey

class SetupInteractor:
    def __init__(
        self,
        test_plan_repo: TestPlanRepository,
        test_exec_repo: TestExecutionRepository,
        test_set_repo: TestSetRepository,
        test_repo: TestRepository
    ):
        self.plan_resolver = TestPlanResolver(test_plan_repo)
        self.exec_resolver = TestExecutionResolver(test_exec_repo)
        self.set_resolver = TestSetResolver(test_set_repo)
        self.source_resolver = TestCaseSourceResolver(test_repo)
        
        self.test_repo = test_repo
        self.plan_repo = test_plan_repo
        self.exec_repo = test_exec_repo
        self.set_repo = test_set_repo

    def execute(self, config: SetupConfig, logger: Optional[Callable[[str], None]] = None) -> SetupResult:
        def log(msg: str):
            if logger: logger(msg)

        metrics = SetupResultMetrics()
        final_execs = []
        final_sets = []
        final_tests = []

        log(f"Iniciando Setup Pipeline (Clean Architecture) para proyecto: {config.project_key}")

        # 1. Validar Test Plan (FAIL FAST)
        self.plan_resolver.validate(config.test_plan.key)
        
        plan_tests = self.plan_repo.get_tests(config.test_plan.key)
        valid_plan_test_keys = [test.key for test in plan_tests]
        log(f"Test Plan validado correctamente ({len(valid_plan_test_keys)} tests maestros encontrados).")

        for exec_conf in config.test_executions:
            # 2. Manejo de Test Executions
            try:
                exec_ticket = self.exec_resolver.resolve(exec_conf, config.project_key)
                final_execs.append(exec_ticket)
                if exec_conf.mode == "create": metrics.executions_created += 1
                else: metrics.executions_reused += 1
                log(f"Test Execution resuelta: -> {exec_ticket.key}")
            except Exception as e:
                metrics.errors.append(str(e))
                log(f"[FAIL FAST] TestExecution: {e}")
                raise ValueError(e)

            for set_conf in exec_conf.test_sets:
                # 3. Manejo de Test Sets y Application validation
                try:
                    set_ticket = self.set_resolver.resolve(
                        set_conf, 
                        config.project_key, 
                        config.settings.clean_test_set_before,
                        log
                    )
                    final_sets.append(set_ticket)
                    if set_conf.mode == "create": metrics.sets_created += 1
                    else: metrics.sets_reused += 1
                    log(f"Test Set adscrita: -> {set_ticket.key} [App={set_conf.application}]")
                except Exception as e:
                    metrics.errors.append(str(e))
                    log(f"[FAIL FAST] TestSet: {e}")
                    raise ValueError(e)
                
                # 4. Discovery de Tests desde orígenes hibridos
                if set_conf.apply_source and set_conf.source:
                    raw_keys = self.source_resolver.resolve(set_conf.source, valid_plan_test_keys, log)
                    
                    if not raw_keys:
                        if config.settings.on_empty_source == "fail":
                            raise ValueError("[FAIL FAST] Operación abortada: Entorno de source retornó 0 casos.")
                        else:
                            log("[WARN] El listado base del source se reporta vacío.")

                    unique_keys = []
                    for k in raw_keys:
                        if k in unique_keys:
                            if config.settings.on_duplicate == "fail":
                                raise ValueError(f"[FAIL FAST] Elemento duplicado detectado prohibitivamente: {k}")
                            elif config.settings.on_duplicate == "skip":
                                log(f"[SKIP] Duplicado omitido inteligentemente: {k}")
                                continue
                        unique_keys.append(k)

                    # 5. Adición de Tests al T.Set (Clone vs Agregar/Link)
                    processed_test_keys = []
                    for t_key in unique_keys:
                        if set_conf.test_case_mode == "clone":
                            log(f"  Clonando test raíz temporalmente: {t_key}")
                            try:
                                cloned = self.test_repo.clone(t_key, config.project_key)
                                processed_test_keys.append(cloned.key)
                                final_tests.append(cloned)
                                metrics.tests_cloned += 1
                                # Auto Tag
                                self.test_repo.update_labels(cloned.key, ["CICD-Pipeline"])
                            except Exception as e:
                                if config.settings.on_missing_test_case == "fail":
                                    raise ValueError(f"[FAIL FAST] Falla materializando clon de {t_key}: {e}")
                                log(f"[WARN] Imposible clonar {t_key}: {e}")
                        else:
                            # Modo "link" o "add": agregar el test original sin clonar
                            log(f"  Agregando (sin clonar) test nativo: {t_key}")
                            processed_test_keys.append(t_key)
                            metrics.tests_linked += 1
                            # Auto Tag
                            try:
                                self.test_repo.update_labels(t_key, ["CICD-Pipeline"])
                            except Exception as e:
                                log(f"[WARN] Imposible inyectar etiqueta CICD-Pipeline a {t_key}: {e}")


                    if processed_test_keys:
                        self.set_repo.add_tests(set_ticket.key, processed_test_keys)
                    
                    self.exec_repo.add_test_set(exec_ticket.key, set_ticket.key)

        log("🚀 Ambientación (Setup) Concluida mediante Motor Arquitectónico Limpio.")
        return SetupResult(
            test_executions=final_execs,
            test_sets=final_sets,
            tests=final_tests,
            metrics=metrics
        )
