from typing import Optional


class NfsBackupCloudConfiguration:
    def __init__(self, nfs_share: Optional[str] = None):
        self.nfs_share = nfs_share


class NfsBackupCloud:
    def __init__(self,
                 name: str = "Nfs",
                 type: str = "nfs",
                 configuration: NfsBackupCloudConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or NfsBackupCloudConfiguration()
