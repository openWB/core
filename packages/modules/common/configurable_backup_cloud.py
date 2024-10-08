from typing import TypeVar, Generic, Callable

from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_type import ComponentType
from modules.common.fault_state import ComponentInfo, FaultState


T_BACKUP_CLOUD_CONFIG = TypeVar("T_BACKUP_CLOUD_CONFIG")


class ConfigurableBackupCloud(Generic[T_BACKUP_CLOUD_CONFIG]):
    def __init__(self,
                 config: T_BACKUP_CLOUD_CONFIG,
                 component_initializer: Callable[[], float]) -> None:
        self.config = config
        self.fault_state = FaultState(ComponentInfo(None, self.config.name,
                                                    ComponentType.BACKUP_CLOUD.value))
        with SingleComponentUpdateContext(self.fault_state):
            self._component_updater = component_initializer(config)

    def update(self, backup_filename: str, backup_file: bytes):
        if hasattr(self, "_component_updater"):
            # Wenn beim Initialisieren etwas schief gelaufen ist, ursprüngliche Fehlermeldung beibehalten
            self._component_updater(backup_filename, backup_file)
