from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable

from ...domain.entities import Test
from ...domain.repositories import TestRepository, TestExecutionRepository


@dataclass
class SyncInput:
    execution_key: str
    folder: str
    status: str
    recursive: bool = True


@dataclass
class SyncMatch:
    test_key: str
    test_summary: str
    file_path: str
    uploaded: bool
    status_updated: bool


@dataclass
class SyncResult:
    matches: list[SyncMatch]
    unmatched_tests: list[str]
    unmatched_files: list[str]


class SyncService:
    """
    Orchestrates the sync flow:
    1. Get tests from a test execution
    2. Recursively scan a folder for files
    3. Match files to tests by name (stem matches test key or summary tokens)
    4. Update status and upload evidence for matched tests
    """

    def __init__(
        self,
        test_repo: TestRepository,
        test_exec_repo: TestExecutionRepository,
    ) -> None:
        self._test_repo = test_repo
        self._test_exec_repo = test_exec_repo

    def _collect_files(self, folder: str, recursive: bool) -> list[Path]:
        root = Path(folder)
        if not root.exists():
            raise FileNotFoundError(f"Folder not found: {folder}")
        if recursive:
            return [p for p in root.rglob("*") if p.is_file()]
        else:
            return [p for p in root.iterdir() if p.is_file()]

    def _match_file_to_test(self, file_path: Path, tests: list[Test]) -> Optional[Test]:
        stem = file_path.stem.upper().replace(" ", "-").replace("_", "-")
        for test in tests:
            if stem == test.key.upper():
                return test
            safe_summary = test.summary.upper().replace(" ", "-").replace("_", "-")
            if stem == safe_summary:
                return test
        return None

    def run(
        self,
        input_data: SyncInput,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> SyncResult:
        def notify(msg: str) -> None:
            if progress_callback:
                progress_callback(msg)

        notify(f"Fetching tests from execution: {input_data.execution_key}")
        exec_tests = self._test_exec_repo.get_tests(input_data.execution_key)

        tests: list[Test] = []
        for td in exec_tests:
            key = td.get("key", "")
            if key:
                t = self._test_repo.get(key)
                if t:
                    tests.append(t)

        notify(f"Found {len(tests)} tests in execution")

        notify(f"Scanning folder: {input_data.folder} (recursive={input_data.recursive})")
        files = self._collect_files(input_data.folder, input_data.recursive)
        notify(f"Found {len(files)} files")

        matches: list[SyncMatch] = []
        matched_test_keys: set[str] = set()
        matched_files: set[str] = set()

        for file_path in files:
            test = self._match_file_to_test(file_path, tests)
            if test:
                notify(f"Matched: {file_path.name} → {test.key} — updating status to {input_data.status}")
                status_ok = self._test_repo.update_status(
                    input_data.execution_key, test.key, input_data.status
                )
                notify(f"Uploading evidence: {file_path}")
                upload_ok = self._test_repo.upload_evidence(
                    input_data.execution_key, test.key, str(file_path)
                )
                matches.append(SyncMatch(
                    test_key=test.key,
                    test_summary=test.summary,
                    file_path=str(file_path),
                    uploaded=upload_ok,
                    status_updated=status_ok,
                ))
                matched_test_keys.add(test.key)
                matched_files.add(str(file_path))

        unmatched_tests = [t.key for t in tests if t.key not in matched_test_keys]
        unmatched_files = [str(f) for f in files if str(f) not in matched_files]

        notify(f"Sync complete. {len(matches)} matches, {len(unmatched_tests)} unmatched tests, {len(unmatched_files)} unmatched files")
        return SyncResult(
            matches=matches,
            unmatched_tests=unmatched_tests,
            unmatched_files=unmatched_files,
        )
