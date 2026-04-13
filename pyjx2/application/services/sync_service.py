from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable, Dict, List

from ...domain.repositories import TestRepository, TestExecutionRepository


@dataclass
class SyncInput:
    execution_key: str
    folder: str
    default_status: str = "PASS"
    status_overrides: Dict[str, str] = field(default_factory=dict)
    allowed_extensions: Optional[List[str]] = None
    recursive: bool = True
    upload_mode: str = "append"  # "append" | "replace"


@dataclass
class SyncMatch:
    test_key: str
    test_summary: str
    file_path: str
    uploaded: bool
    status_updated: bool


@dataclass
class SyncResult:
    test_execution: str
    processed_tests: int = 0
    updated_tests: int = 0
    tests_without_evidence: List[str] = field(default_factory=list)
    files_uploaded: int = 0
    files_unused: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


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
        test_exec_repo: TestExecutionRepository,
    ) -> None:
        self._test_repo = test_repo
        self._test_exec_repo = test_exec_repo

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
            tests = self._test_exec_repo.list_from_execution(input_data.execution_key)
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
            if input_data.upload_mode == "replace":
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

