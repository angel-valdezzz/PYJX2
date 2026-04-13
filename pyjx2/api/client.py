from __future__ import annotations

from typing import Optional, Dict, List

from ..domain.entities import Test, TestSet, TestExecution, TestPlan
from ..infrastructure.config.settings import Settings
from ..infrastructure.jira.client import JiraClient
from ..infrastructure.xray.client import XrayClient
from ..infrastructure.xray.repositories import (
    XrayTestRepository,
    XrayTestSetRepository,
    XrayTestExecutionRepository,
    XrayTestPlanRepository,
)
from ..application.services.sync_service import SyncService, SyncInput, SyncResult


class PyJX2:
    """
    High-level API facade for Jira / Xray automation.

    All public methods are composable and can be used independently to build
    custom automation scripts.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._jira = JiraClient(settings.jira)
        self._xray = XrayClient(settings.xray)

        self._test_repo = XrayTestRepository(self._xray, self._jira)
        self._test_set_repo = XrayTestSetRepository(self._xray, self._jira)
        self._test_exec_repo = XrayTestExecutionRepository(self._xray, self._jira)
        self._test_plan_repo = XrayTestPlanRepository(self._xray, self._jira)

    # ── Tests ────────────────────────────────────────────────────────────────

    def get_test(self, key: str) -> Optional[Test]:
        """Fetch a single test by Jira issue key."""
        return self._test_repo.get(key)

    def create_test(
        self,
        project_key: str,
        summary: str,
        test_type: str = "Manual",
        labels: Optional[list[str]] = None,
    ) -> Test:
        """Create a new test issue in Jira/Xray."""
        return self._test_repo.create(
            project_key=project_key,
            summary=summary,
            test_type=test_type,
            labels=labels or [],
        )

    def clone_test(self, source_key: str, target_project_key: str) -> Test:
        """Clone an existing test into the target project."""
        return self._test_repo.clone(source_key, target_project_key)

    def get_tests_from_execution(self, execution_key: str) -> list[Test]:
        """Get all tests associated with a test execution."""
        return self._test_repo.list_from_execution(execution_key)

    def update_test_status(
        self,
        execution_key: str,
        test_key: str,
        status: str,
    ) -> bool:
        """Update the run status of a test within a test execution."""
        return self._test_repo.update_status(execution_key, test_key, status)

    def upload_test_evidence(
        self,
        execution_key: str,
        test_key: str,
        file_path: str,
    ) -> bool:
        """Upload a file as evidence for a test run."""
        return self._test_repo.upload_evidence(execution_key, test_key, file_path)

    # ── Test Sets ─────────────────────────────────────────────────────────────

    def get_test_set(self, key: str) -> Optional[TestSet]:
        """Fetch a test set by Jira issue key."""
        return self._test_set_repo.get(key)

    def create_test_set(self, project_key: str, summary: str) -> TestSet:
        """Create a new test set issue."""
        return self._test_set_repo.create(project_key, summary)

    def update_test_set(self, key: str, **kwargs) -> TestSet:
        """Update an existing test set (e.g. summary='New title')."""
        return self._test_set_repo.update(key, **kwargs)

    def add_tests_to_set(self, test_set_key: str, test_keys: list[str]) -> bool:
        """Add one or more tests to a test set."""
        return self._test_set_repo.add_tests(test_set_key, test_keys)

    # ── Test Executions ───────────────────────────────────────────────────────

    def get_test_execution(self, key: str) -> Optional[TestExecution]:
        """Fetch a test execution by Jira issue key."""
        return self._test_exec_repo.get(key)

    def create_test_execution(self, project_key: str, summary: str, **kwargs) -> TestExecution:
        """Create a new test execution issue."""
        return self._test_exec_repo.create(project_key, summary, **kwargs)

    def update_test_execution(self, key: str, **kwargs) -> TestExecution:
        """Update an existing test execution (e.g. summary='New title')."""
        return self._test_exec_repo.update(key, **kwargs)

    def add_test_set_to_execution(self, execution_key: str, test_set_key: str) -> bool:
        """Link a test set to a test execution."""
        return self._test_exec_repo.add_test_set(execution_key, test_set_key)

    # ── Test Plans ────────────────────────────────────────────────────────────

    def get_test_plan(self, key: str) -> Optional[TestPlan]:
        """Fetch a test plan by Jira issue key."""
        return self._test_plan_repo.get(key)

    def get_tests_from_plan(self, plan_key: str) -> list[dict]:
        """Get all tests associated with a test plan."""
        return self._test_plan_repo.get_tests(plan_key)

    # ── High-level flows ──────────────────────────────────────────────────────

    def setup(
        self,
        test_plan_key: str,
        execution_summary: str,
        application: str,
        test_mode: str = "clone",
        progress_callback=None,
    ):
        """
        Flujo completo de Preparación orquestado por el Interactor de Clean Architecture.

        Crea un Test Execution y un Test Set en Jira/Xray a partir de un Test Plan.

        Args:
            test_plan_key: Llave del Test Plan origen (ej. ``QAX-100``).
            execution_summary: Título para el nuevo Test Execution.
            application: Calificador de aplicación (ej. ``AXA_WEB``).
            test_mode: ``"clone"`` (default) crea una copia de cada test en QAX.
                       ``"add"`` agrega los tests originales directamente, sin clonar.
            progress_callback: Callable opcional ``(msg: str) -> None`` para reportar progreso.

        Returns:
            :class:`SetupResult` con las llaves de Executions, Sets y Tests creados.
        """
        from ..application.use_cases.setup.models import (
            SetupConfig, SetupTestPlanConfig, SetupTestExecutionConfig,
            SetupTestSetConfig, SetupGlobalSettings, SetupSourceConfig
        )
        from ..application.use_cases.setup.setup_interactor import SetupInteractor

        effective_mode = test_mode if test_mode in ("clone", "link", "add") else "clone"

        interactor = SetupInteractor(
            test_plan_repo=self._test_plan_repo,
            test_exec_repo=self._test_exec_repo,
            test_set_repo=self._test_set_repo,
            test_repo=self._test_repo
        )

        config = SetupConfig(
            project_key="QAX",
            test_plan=SetupTestPlanConfig(key=test_plan_key),
            test_executions=[
                SetupTestExecutionConfig(
                    mode="create",
                    name=execution_summary,
                    test_sets=[
                        SetupTestSetConfig(
                            mode="create",
                            application=application,
                            key=execution_summary,
                            apply_source=True,
                            source=SetupSourceConfig(type="test_plan"),
                            test_case_mode=effective_mode
                        )
                    ]
                )
            ],
            settings=SetupGlobalSettings()
        )

        return interactor.execute(config, logger=progress_callback)


    def sync(
        self,
        execution_key: str,
        folder: str,
        status: str = "PASS",
        status_overrides: Optional[Dict[str, str]] = None,
        allowed_extensions: Optional[List[str]] = None,
        upload_mode: str = "append",
        recursive: bool = True,
        progress_callback=None,
    ) -> SyncResult:
        """
        Flujo completo de Sincronización: obtiene tests del Execution → escanea carpeta →
        empareja archivos por prefijo → actualiza estados y sube evidencias.

        Args:
            execution_key: Llave del Test Execution en Jira (ej. ``QAX-200``).
            folder: Ruta local con los archivos de evidencia.
            status: Estado por defecto para todos los tests encontrados.
                    Valores: ``PASS``, ``FAIL``, ``TODO``, ``EXECUTING``, ``ABORTED``.
            status_overrides: Dict que mapea llaves de test a estados específicos.
                              Ej: ``{"QAX-1": "FAIL", "QAX-2": "PASS"}``.
            allowed_extensions: Lista de extensiones a incluir (ej. ``[".pdf", ".png"]``).
                                 Por defecto: ``[".pdf"]``.
            upload_mode: ``"append"`` (añade evidencia a la existente) o
                         ``"replace"`` (limpia y reemplaza la evidencia anterior).
            recursive: Si ``True``, escanea subcarpetas recursivamente.
            progress_callback: Callable opcional ``(msg: str) -> None``.

        Returns:
            :class:`SyncResult` con métricas detalladas del proceso.
        """
        from ..application.services.sync_service import SyncService, SyncInput

        service = SyncService(self._test_repo, self._test_exec_repo)

        sync_input = SyncInput(
            execution_key=execution_key,
            folder=folder,
            default_status=status,
            status_overrides=status_overrides or {},
            allowed_extensions=allowed_extensions,
            upload_mode=upload_mode,
            recursive=recursive
        )

        return service.run(sync_input, progress_callback=progress_callback)

    # ── Factory classmethods ─────────────────────────────────────────────────

    @classmethod
    def from_credentials(
        cls,
        username: str,
        password: str,
        env: str = "QA",
    ) -> "PyJX2":
        """
        Crea una instancia de PyJX2 directamente con credenciales de Jira.

        No requiere archivo de configuración. Las credenciales de Xray se reciclan
        automáticamente desde las de Jira.

        Args:
            username: Usuario o email de Jira (ej. ``usuario@empresa.com``).
            password: Contraseña de Jira o token de API. Soporta formato ``ENC:...``.
            env: Entorno a utilizar: ``"QA"`` (default) o ``"DEV"``.

        Returns:
            Instancia de :class:`PyJX2` lista para operar.

        Example::

            from pyjx2.api.client import PyJX2

            pjx = PyJX2.from_credentials(
                username="user@empresa.com",
                password="mi_token",
                env="QA",
            )
            result = pjx.setup(test_plan_key="QAX-100", execution_summary="Regresión", application="AXA_WEB")
        """
        from ..infrastructure.config.settings import JiraSettings, XraySettings, Settings
        settings = Settings(
            jira=JiraSettings(username=username, password=password, env=env),
            xray=XraySettings(client_id=username, client_secret=password),
        )
        return cls(settings)

    @classmethod
    def from_config(
        cls,
        config_file: Optional[str] = None,
    ) -> "PyJX2":
        """
        Crea una instancia de PyJX2 a partir de un archivo de configuración o
        variables de entorno ``PYJX2_*``.

        Busca automáticamente ``pyjx2.toml`` o ``pyjx2.json`` en el directorio actual
        si no se especifica ``config_file``.

        Args:
            config_file: Ruta opcional al archivo de configuración (``.toml`` o ``.json``).

        Returns:
            Instancia de :class:`PyJX2` lista para operar.

        Example::

            from pyjx2.api.client import PyJX2

            # Usa pyjx2.toml del directorio actual
            pjx = PyJX2.from_config()

            # Usa un archivo específico
            pjx = PyJX2.from_config("./config/pyjx2.toml")
        """
        from ..infrastructure.config import load_settings
        return cls(load_settings(config_file=config_file))

    # ── Raw clients (escape hatch) ────────────────────────────────────────────

    @property
    def jira(self) -> JiraClient:
        """Direct access to the low-level Jira REST client."""
        return self._jira

    @property
    def xray(self) -> XrayClient:
        """Direct access to the low-level Xray REST client."""
        return self._xray

    # ── Security utilities ───────────────────────────────────────────────────

    @staticmethod
    def encrypt_password(plain_text: str) -> str:
        """
        Encrypt a plaintext password using the internal symmetric encryption feature.
        This provides a 128-bit AES encrypted token string using Fernet, prefixed with ENC:
        """
        from ..infrastructure.security.encryption import SymmetricEncryptionService
        svc = SymmetricEncryptionService()
        return svc.encrypt(plain_text)

    @staticmethod
    def decrypt_password(encrypted_text: str) -> str:
        """
        Decrypt a previously encrypted password string.
        Only correctly encrypted tokens (prefixed with ENC:) will be decrypted.
        Others are safely returned unmodified.
        """
        from ..infrastructure.security.encryption import SymmetricEncryptionService
        svc = SymmetricEncryptionService()
        return svc.decrypt(encrypted_text)
