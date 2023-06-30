from abc import abstractmethod
from dataclasses import dataclass


@dataclass
class SocUpdateData:
    plug_state: bool = False
    charge_state: bool = False
    imported_since_plugged: float = 0
    battery_capacity: float = 82


class AbstractSoc:
    @abstractmethod
    def __init__(self, soc_config: dict) -> None:
        pass

    @abstractmethod
    def update(self, soc_update_data: SocUpdateData) -> None:
        pass
