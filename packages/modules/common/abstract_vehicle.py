from dataclasses import dataclass
from typing import Optional


@dataclass
class VehicleUpdateData:
    plug_state: bool = False
    charge_state: bool = False
    imported: float = 0
    battery_capacity: float = 82
    soc_from_cp: float = 0


@dataclass
class GeneralVehicleConfig:
    efficiency: float = 90
    use_soc_from_cp: bool = False
    request_interval_charging: int = 5
    request_interval_not_charging: int = 720
    request_only_plugged: bool = False


@dataclass
class CalculatedSocState:
    imported_start: Optional[float] = 0  # don't show in UI
    manual_soc: Optional[int] = None  # don't show in UI
    request_start_soc: bool = True  # don't show in UI
    soc_start: float = 0  # don't show in UI
