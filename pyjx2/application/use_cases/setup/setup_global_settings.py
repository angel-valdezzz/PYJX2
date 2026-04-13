from dataclasses import dataclass
from typing import Literal


@dataclass
class SetupGlobalSettings:
    clean_test_set_before: bool = False
    on_missing_test_case: Literal["warn", "fail"] = "warn"
    on_duplicate: Literal["skip", "fail"] = "skip"
    on_empty_source: Literal["warn", "fail"] = "warn"
