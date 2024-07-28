from typing import Optional


class SambaBackupCloudConfiguration:
    def __init__(self,
                 smb_path: Optional[str] = "/",
                 smb_server: Optional[str] = None,
                 smb_share: Optional[str] = None,
                 smb_user: Optional[str] = None,
                 smb_password: Optional[str] = None):
        self.smb_path = smb_path
        self.smb_server = smb_server
        self.smb_share = smb_share
        self.smb_user = smb_user
        self.smb_password = smb_password


class SambaBackupCloud:
    def __init__(self,
                 name: str = "Samba",
                 type: str = "samba",
                 configuration: SambaBackupCloudConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or SambaBackupCloudConfiguration()
