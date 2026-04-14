from dataclasses import dataclass
from typing import Literal

from ....domain.value_objects import Application, TestSetKey
from .setup_source_config import SetupSourceConfig


@dataclass
class SetupTestSetConfig:
    mode: Literal["create", "reuse"]
    application: Application
    key: str | TestSetKey | None = None
    apply_source: bool = False
    source: SetupSourceConfig | None = None
    test_case_mode: Literal["clone", "link", "add"] = "clone"

    def __post_init__(self) -> None:
        self.application = Application.from_value(self.application)
        if self.mode == "reuse" and self.key is not None:
            self.key = TestSetKey.from_value(self.key)
