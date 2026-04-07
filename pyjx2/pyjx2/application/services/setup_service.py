from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Callable

from ...domain.entities import Test, TestSet, TestExecution
from ...domain.repositories import (
    TestRepository,
    TestSetRepository,
    TestExecutionRepository,
    TestPlanRepository,
)


@dataclass
class SetupInput:
    project_key: str
    test_plan_key: str
    execution_summary: str
    test_set_summary: str
    reuse_tests: bool = False


@dataclass
class SetupResult:
    test_execution: TestExecution
    test_set: TestSet
    tests: list[Test]
    reused: list[str]
    created: list[str]
    cloned: list[str]


class SetupService:
    """
    Orchestrates the full setup flow:
    1. Read test plan to get required tests
    2. Create / reuse / clone tests
    3. Create test set and link tests
    4. Create test execution and link test set
    """

    def __init__(
        self,
        test_repo: TestRepository,
        test_set_repo: TestSetRepository,
        test_exec_repo: TestExecutionRepository,
        test_plan_repo: TestPlanRepository,
    ) -> None:
        self._test_repo = test_repo
        self._test_set_repo = test_set_repo
        self._test_exec_repo = test_exec_repo
        self._test_plan_repo = test_plan_repo

    def run(
        self,
        input_data: SetupInput,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> SetupResult:
        def notify(msg: str) -> None:
            if progress_callback:
                progress_callback(msg)

        notify(f"Fetching test plan: {input_data.test_plan_key}")
        test_plan = self._test_plan_repo.get(input_data.test_plan_key)
        if not test_plan:
            raise ValueError(f"Test plan not found: {input_data.test_plan_key}")

        plan_tests_data = self._test_plan_repo.get_tests(input_data.test_plan_key)
        notify(f"Found {len(plan_tests_data)} tests in test plan")

        tests: list[Test] = []
        reused: list[str] = []
        created: list[str] = []
        cloned: list[str] = []

        for test_data in plan_tests_data:
            test_key = test_data.get("key", "")
            if not test_key:
                continue

            if input_data.reuse_tests:
                existing = self._test_repo.get(test_key)
                if existing:
                    notify(f"Reusing existing test: {test_key}")
                    tests.append(existing)
                    reused.append(test_key)
                    continue

            notify(f"Cloning test: {test_key}")
            cloned_test = self._test_repo.clone(test_key, input_data.project_key)
            tests.append(cloned_test)
            cloned.append(cloned_test.key)

        notify(f"Creating test set: {input_data.test_set_summary}")
        test_set = self._test_set_repo.create(
            project_key=input_data.project_key,
            summary=input_data.test_set_summary,
        )

        test_keys_to_add = [t.key for t in tests]
        if test_keys_to_add:
            notify(f"Adding {len(test_keys_to_add)} tests to test set {test_set.key}")
            self._test_set_repo.add_tests(test_set.key, test_keys_to_add)

        notify(f"Creating test execution: {input_data.execution_summary}")
        test_exec = self._test_exec_repo.create(
            project_key=input_data.project_key,
            summary=input_data.execution_summary,
        )

        notify(f"Linking test set {test_set.key} to test execution {test_exec.key}")
        self._test_exec_repo.add_test_set(test_exec.key, test_set.key)

        notify("Setup complete!")
        return SetupResult(
            test_execution=test_exec,
            test_set=test_set,
            tests=tests,
            reused=reused,
            created=created,
            cloned=cloned,
        )
