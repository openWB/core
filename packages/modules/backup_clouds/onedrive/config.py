from typing import Optional


class OneDriveBackupCloudConfiguration:
    def __init__(self, backuppath: str = "/openWB/Backup/",
                 persistent_tokencache: Optional[str] = None,
                 authurl: Optional[str] = None,
                 authcode: Optional[str] = None,
                 scope: Optional[list] = ["https://graph.microsoft.com/Files.ReadWrite"],
                 authority: Optional[str] = "https://login.microsoftonline.com/consumers/",
                 clientID: Optional[str] = "e529d8d2-3b0f-4ae4-b2ba-2d9a2bba55b2",
                 flow: Optional[str] = None) -> None:
        self.backuppath = backuppath
        self.persistent_tokencache = persistent_tokencache
        self.authurl = authurl
        self.authcode = authcode
        self.scope = scope
        self.authority = authority
        self.clientID = clientID
        self.flow = flow


class OneDriveBackupCloud:
    def __init__(self,
                 name: str = "OneDrive",
                 type: str = "onedrive",
                 configuration: OneDriveBackupCloudConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or OneDriveBackupCloudConfiguration()
