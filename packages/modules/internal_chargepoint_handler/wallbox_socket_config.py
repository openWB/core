from dataclasses import dataclass, field
from typing import List, Optional

from dataclass_utils.factories import currents_list_factory, voltages_list_factory
from helpermodules.constants import NO_ERROR


@dataclass
class WallboxSocketData:
    detected: bool = False
    set_state: bool = False
    last_tag: Optional[str] = None


@dataclass
class WallboxSocketGet:
    rfid: Optional[str] = None
    state: bool = False
    power: float = 0
    imported: float = 0
    exported: float = 0
    currents: List[float] = field(default_factory=currents_list_factory)
    voltages: List[float] = field(default_factory=voltages_list_factory)
    powers: List[float] = field(default_factory=currents_list_factory)
    fault_state: int = 0
    fault_str: str = NO_ERROR
    error_timestamp: Optional[float] = None


@dataclass
class WallboxSocket:
    data: WallboxSocketData = field(default_factory=WallboxSocketData)
    get: WallboxSocketGet = field(default_factory=WallboxSocketGet)
