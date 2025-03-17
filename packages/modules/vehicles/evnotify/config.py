from typing import Optional


class EVNotifyConfiguration:
    def __init__(self, id: int = 0, akey: Optional[str] = None, token: Optional[str] = None):
        self.id = id
        self.akey = akey
        self.token = token


class EVNotify:
    def __init__(self,
                 name: str = "EVNotify",
                 type: str = "evnotify",
                 official: bool = False,
                 configuration: EVNotifyConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or EVNotifyConfiguration()
