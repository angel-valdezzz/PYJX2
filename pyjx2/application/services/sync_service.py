from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable, Dict, List

from ...domain.repositories import TestRepository
from ...domain.value_objects import ExecutionKey, Status, TestKey, UploadMode


@dataclass
class SyncInput:
    execution_key: ExecutionKey
    folder: str
    default_status: Status = field(default_factory=lambda: Status.from_value("PASS"))
    status_overrides: Dict[TestKey, Status] = field(default_factory=dict)
    allowed_extensions: Optional[List[str]] = None
    recursive: bool = True
    upload_mode: UploadMode = field(default_factory=lambda: UploadMode.from_value("append"))

    def __post_init__(self) -> None:
        self.execution_key = ExecutionKey.from_value(self.execution_key)
        self.default_status = Status.from_value(self.default_status)
        self.status_overrides = {
            TestKey.from_value(test_key): Status.from_value(status)
            for test_key, status in self.status_overrides.items()
        }
        self.upload_mode = UploadMode.from_value(self.upload_mode)


@dataclass
class SyncMatch:
    test_key: TestKey
    test_summary: str
    file_path: str
    uploaded: bool
    status_updated: bool

    def __post_init__(self) -> None:
        self.test_key = TestKey.from_value(self.test_key)


@dataclass
class SyncResult:
    test_execution: ExecutionKey
    processed_tests: int = 0
    updated_tests: int = 0
    tests_without_evidence: List[TestKey] = field(default_factory=list)
    files_uploaded: int = 0
    files_unused: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.test_execution = ExecutionKey.from_value(self.test_execution)
        self.tests_without_evidence = [TestKey.from_value(key) for key in self.tests_without_evidence]


class SyncService:
    """
    Sincronización de evidencias (Fase 2):
    1. Valida el Test Execution.
    2. Escanea la carpeta local de forma recursiva.
    3. Asocia archivos a tests si el nombre del archivo INICIA con el summary del test (prefix_summary).
    4. Actualiza estados (default o por test) y sube evidencias.
    """

    def __init__(
        self,
        test_repo: TestRepository,
    ) -> None:
        self._test_repo = test_repo

    def _collect_files(self, folder: str, recursive: bool, allowed_ext: Optional[List[str]]) -> list[Path]:
        root = Path(folder)
        if not root.exists():
            raise FileNotFoundError(f"Directorio de evidencias no encontrado: {folder}")
        
        pattern = "**/*" if recursive else "*"
        files = [p for p in root.glob(pattern) if p.is_file()]
        
        if allowed_ext:
            # Normalizar extensiones a .ext
            exts = [e.lower() if e.startswith(".") else f".{e.lower()}" for e in allowed_ext]
            files = [f for f in files if f.suffix.lower() in exts]
            
        return files

    def _match_files_to_test(self, test_summary: str, files: list[Path]) -> list[Path]:
        """
        Regla de matching: Un archivo coincide si su nombre (stem) empieza con el summary del test.
        Case insensitive.
        """
        matches = []
        summary_upper = test_summary.upper()
        for f in files:
            if f.stem.upper().startswith(summary_upper):
                matches.append(f)
        return matches

    def run(
        self,
        input_data: SyncInput,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> SyncResult:
        def notify(msg: str) -> None:
            if progress_callback:
                progress_callback(msg)

        result = SyncResult(test_execution=input_data.execution_key)

        try:
            notify(f"Obteniendo tests de la ejecución: {input_data.execution_key}")
            tests = self._test_repo.list_from_execution(input_data.execution_key)
            result.processed_tests = len(tests)
            notify(f"Se encontraron {len(tests)} tests procesables.")
        except Exception as e:
            msg = f"Error al validar Test Execution {input_data.execution_key}: {e}"
            notify(f"[FAIL FAST] {msg}")
            result.errors.append(msg)
            return result

        notify(f"Escaneando evidencias en: {input_data.folder} (recursivo={input_data.recursive})")
        all_files = self._collect_files(input_data.folder, input_data.recursive, input_data.allowed_extensions)
        notify(f"Se encontraron {len(all_files)} archivos válidos para procesar.")

        matched_files_paths: set[str] = set()
        tests_updated_count = 0
        total_uploads = 0

        for test in tests:
            test_matches = self._match_files_to_test(test.summary, all_files)
            
            if not test_matches:
                result.tests_without_evidence.append(test.key)
                continue

            # Determinar estado
            status = input_data.status_overrides.get(test.key, input_data.default_status)
            notify(f"Actualizando {test.key} ('{test.summary}') a estado: {status}")
            
            status_ok = self._test_repo.update_status(input_data.execution_key, test.key, status)
            if status_ok:
                tests_updated_count += 1

            # Si el modo es REPLACE, limpiar evidencias previas
            if input_data.upload_mode == UploadMode.from_value("replace"):
                notify(f"  Modo REPLACE: Limpiando evidencias previas para {test.key}...")
                self._test_repo.clear_evidence(input_data.execution_key, test.key)

            for f_path in test_matches:
                notify(f"  Subiendo evidencia: {f_path.name}")
                upload_ok = self._test_repo.upload_evidence(input_data.execution_key, test.key, str(f_path))
                if upload_ok:
                    total_uploads += 1
                else:
                    result.errors.append(f"Falla al subir {f_path.name} para {test.key}")
                
                matched_files_paths.add(str(f_path))

        result.updated_tests = tests_updated_count
        result.files_uploaded = total_uploads
        result.files_unused = [str(f.name) for f in all_files if str(f) not in matched_files_paths]

        notify(f"Sincronización finalizada. Tests actualizados: {result.updated_tests}. Archivos subidos: {result.files_uploaded}.")
        if result.files_unused:
            notify(f"Archivos sin asociación: {len(result.files_unused)}")

        return result

