from abc import abstractmethod
from typing import Generic, TypeVar

from control.chargepoint.charging_type import ChargingType


class AbstractChargepoint:
    @abstractmethod
    def __init__(self, id: int, connection_module: dict, power_module: dict) -> None:
        pass

    @abstractmethod
    def set_current(self, current: float) -> None:
        pass

    @abstractmethod
    def get_values(self) -> None:
        pass

    @abstractmethod
    def switch_phases(self, phases_to_use: int, duration: int) -> None:
        pass

    @abstractmethod
    def interrupt_cp(self, duration: int) -> None:
        pass

    @abstractmethod
    def clear_rfid(self) -> None:
        pass

    @abstractmethod
    def add_conversion_loss_to_current(self, current: float) -> float:
        return current

    @abstractmethod
    def subtract_conversion_loss_from_current(self, current: float) -> float:
        return current


T = TypeVar("T")


class SetupChargepoint(Generic[T]):
    def __init__(self,
                 name: str,
                 type: str,
                 id: int,
                 configuration: T,
                 charging_type: str = ChargingType.AC.value,
                 visibility: bool = True) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration
        self.charging_type = charging_type
        self.visibility = visibility
