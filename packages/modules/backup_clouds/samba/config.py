from typing import Optional


class SambaBackupCloudConfiguration:
    def __init__(self,
                 smb_path: Optional[str] = "/",
                 smb_server: Optional[str] = None,
                 smb_share: Optional[str] = None,
                 smb_user: Optional[str] = None,
                 smb_password: Optional[str] = None,
                 max_backups: Optional[int] = None):
        self.smb_path = smb_path
        self.smb_server = smb_server
        self.smb_share = smb_share
        self.smb_user = smb_user
        self.smb_password = smb_password
        # None oder <= 0 bedeutet: keine automatische Löschung alter Backups
        self.max_backups = max_backups


class SambaBackupCloud:
    def __init__(self,
                 name: str = "Samba",
                 type: str = "samba",
                 official: bool = False,
                 configuration: SambaBackupCloudConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or SambaBackupCloudConfiguration()
