from ....domain.repositories import TestPlanRepository
from ....domain.value_objects import TestPlanKey


class TestPlanResolver:
    def __init__(self, repo: TestPlanRepository):
        self.repo = repo

    def validate(self, plan_key: TestPlanKey) -> None:
        plan = self.repo.get(plan_key)
        if not plan:
            raise ValueError(f"[FAIL FAST] Test Plan {plan_key} invalido o no existe.")
