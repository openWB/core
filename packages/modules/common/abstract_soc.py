from abc import abstractmethod
from dataclasses import dataclass


@dataclass
class SocUpdateData:
    charge_state: bool = False


class AbstractSoc:
    @abstractmethod
    def __init__(self, soc_config: dict) -> None:
        pass

    @abstractmethod
    def update(self, soc_update_data: SocUpdateData) -> None:
        pass
