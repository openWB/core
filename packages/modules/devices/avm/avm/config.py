from typing import Optional
from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup


@auto_str
class AvmConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 session_id: Optional[str] = None,
                 session_mtime: Optional[str] = None) -> None:
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.session_id = session_id  # don't show in UI
        self.session_mtime = session_mtime  # don't show in UI


@auto_str
class Avm:
    def __init__(self,
                 name: str = "AVM Fritz!Box",
                 type: str = "avm",
                 id: int = 0,
                 configuration: AvmConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or AvmConfiguration()


@auto_str
class AvmCounterConfiguration:
    def __init__(self, name: Optional[str] = None):
        self.name = name


@auto_str
class AvmCounterSetup(ComponentSetup[AvmCounterConfiguration]):
    def __init__(self,
                 name: str = "Avm Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: AvmCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or AvmCounterConfiguration())
