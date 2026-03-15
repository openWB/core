from typing import Optional


class NextcloudBackupCloudConfiguration:
    def __init__(self, ip_address: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        self.ip_address = ip_address
        self.user = user
        self.password = password


class NextcloudBackupCloud:
    def __init__(self,
                 name: str = "NextCloud",
                 type: str = "nextcloud",
                 official: bool = True,
                 configuration: NextcloudBackupCloudConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or NextcloudBackupCloudConfiguration()
