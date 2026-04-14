from collections.abc import Callable

from ....domain.repositories import TestRepository
from ....domain.value_objects import TestKey
from .setup_source_config import SetupSourceConfig


class TestCaseSourceResolver:
    def __init__(self, test_repo: TestRepository):
        self.test_repo = test_repo

    def resolve(
        self,
        source: SetupSourceConfig,
        valid_keys: list[TestKey],
        logger: Callable | None = None,
    ) -> list[TestKey]:
        keys: list[TestKey] = []
        if source.type == "test_plan":
            keys = valid_keys
        elif source.type == "list":
            keys = source.items or []
        elif source.type == "folder":
            if logger:
                logger(f"Obteniendo tests desde Xray Folder ID: {source.path}")
            if hasattr(self.test_repo, "list_from_folder"):
                fetched = self.test_repo.list_from_folder(source.path)
                keys.extend([t.key for t in fetched if getattr(t, "key", None)])
            elif logger:
                logger(
                    "[WARN] Metodo `list_from_folder` no implementado en el TestRepository, omitiendo."
                )

        if valid_keys:
            filtered = []
            for key in keys:
                if key in valid_keys:
                    filtered.append(key)
                elif logger:
                    logger(
                        f"[WARN] El TestCase {key} no pertenece al Test Plan subyacente y sera descartado."
                    )
            return filtered

        return keys
