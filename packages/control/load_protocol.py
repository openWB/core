from dataclasses import dataclass
from typing import List, Optional, Protocol

from control.algorithm.utils import get_medium_charging_current
from control.chargepoint.control_parameter import ControlParameter
from helpermodules.timecheck import create_timestamp


@dataclass
class LoadGet:
    charge_state: bool
    currents: List[float]
    daily_imported: float
    daily_exported: float
    error_timestamp: int
    exported: float
    fault_str: str
    fault_state: int
    imported: float
    phases_in_use: int
    power: float
    powers: List[float]
    state_str: Optional[str]
    voltages: List[float]


@dataclass
class LoadSet:
    current: float
    phases_to_use: int
    plug_time: Optional[float]
    required_power: float
    current_prev: float
    target_current: float
    charge_state_prev: bool


@dataclass
class LoadData:
    control_parameter: ControlParameter
    get: LoadGet
    set: LoadSet


class Load(Protocol):
    STANDBY_THRESHOLD = 0.5

    num: int
    chargemode_changed: bool
    submode_changed: bool
    data: LoadData

    def get_mean_current(self) -> float:
        """Mittlerer Ist-Strom aktiver Phasen mit der Schwelle des jeweiligen Lasttyps."""
        return get_medium_charging_current(self.data.get.currents, threshold=self.STANDBY_THRESHOLD)

    def set_timestamp_charge_start(self) -> None:
        # Beim Ladestart Timer laufen lassen, manche Fahrzeuge brauchen sehr lange.
        # Nach dem Algorithmus setzen, sonst steht set current noch nicht fest.
        if self.data.control_parameter.timestamp_charge_start is None:
            if self.data.set.current_prev == 0 and self.data.set.current != 0:
                self.data.control_parameter.timestamp_charge_start = create_timestamp()
        elif self.data.set.current == 0:
            self.data.control_parameter.timestamp_charge_start = None

    def is_charging_stop_allowed(self) -> bool:
        ...

    def set_state_and_log(self, message: str) -> None:
        ...
