"""YourCharge Daten
"""
import logging

from typing import List

from dataclasses import dataclass, field
from dataclass_utils.factories import empty_dict_factory, empty_list_factory


log = logging.getLogger(__name__)


@dataclass
class YcConfig:
    active: bool = False
    allowed_rfid_ev: List[str] = field(default_factory=empty_list_factory)
    allowed_rfid_std_socket: List[str] = field(default_factory=empty_list_factory)

def three_zero_ints_factory() -> List[int]:
    return [ 0, 0, 0 ]

def three_zero_floatss_factory() -> List[float]:
    return [ 0.0, 0.0, 0.0 ]

@dataclass
class YcSystemStatus:
    allowed_peak_power: float = None
    allowed_total_current_per_phase: float = None
    allowed_load_imbalance: float = None
    charging_vehicles: List[int] = field(default_factory=three_zero_ints_factory)
    total_current_consumption: List[float] = field(default_factory=three_zero_floatss_factory)
    total_power: float = None
    imbalance_current_consumption: List[float] = field(default_factory=three_zero_floatss_factory)


@dataclass
class YcData:
    def __init__(self):
        self._fixed_charge_current = 0.0
        self._yc_config = YcConfig()
        self._yc_status = YcSystemStatus()
        self._last_controller_publish = 0

    @property
    def yc_config(self) -> YcConfig:
        return self._yc_config

    @property
    def yc_status(self) -> YcSystemStatus:
        return self.__yc_status

    @property
    def fixed_charge_current(self) -> float:
        return self._fixed_charge_current

    @property
    def last_controller_publish(self) -> int:
        return self._last_controller_publish

    @fixed_charge_current.setter
    def fixed_charge_current(self, value):
        if value is None or float(value) < 0:
            self._fixed_charge_current = None
        else:
            self._fixed_charge_current = float(value)


class YourCharge:
    """Config and data for use by YourCharge charge system algorithms
    """

    def __init__(self):
        self.data: YcData = YcData()
