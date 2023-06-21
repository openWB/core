from typing import Optional


class OneDriveBackupCloudConfiguration:
    def __init__(self, backuppath: str = "/openWB/Backup/", persistent_tokencache: Optional[str] = None) -> None:
        self.backuppath = backuppath
        self.persistent_tokencache = persistent_tokencache


class OneDriveBackupCloud:
    def __init__(self,
                 name: str = "OneDrive",
                 type: str = "onedrive",
                 configuration: OneDriveBackupCloudConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or OneDriveBackupCloudConfiguration()
