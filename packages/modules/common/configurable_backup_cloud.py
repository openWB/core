from typing import TypeVar, Generic, Callable


T_BACKUP_CLOUD_CONFIG = TypeVar("T_BACKUP_CLOUD_CONFIG")


class ConfigurableBackupCloud(Generic[T_BACKUP_CLOUD_CONFIG]):
    def __init__(self,
                 config: T_BACKUP_CLOUD_CONFIG,
                 component_updater: Callable[[str, bytes], None]) -> None:
        self.__component_updater = component_updater
        self.config = config

    def update(self, backup_filename: str, backup_file: bytes):
        self.__component_updater(backup_filename, backup_file)
