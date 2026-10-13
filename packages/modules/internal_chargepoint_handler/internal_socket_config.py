from dataclasses import dataclass, field
from typing import List, Optional

from dataclass_utils.factories import currents_list_factory, voltages_list_factory
from helpermodules.constants import NO_ERROR


@dataclass
class InternalSocketData:
    detected: bool = False
    set_state: bool = False


@dataclass
class InternalSocketGet:
    state: bool = False
    power: float = 0
    imported: float = 0
    exported: float = 0
    currents: List[float] = field(default_factory=currents_list_factory)
    voltages: List[float] = field(default_factory=voltages_list_factory)
    powers: List[float] = field(default_factory=currents_list_factory)
    fault_state: int = 0
    fault_str: str = NO_ERROR
    timestamp: float = 0
    error_timestamp: Optional[float] = None


@dataclass
class InternalSocket:
    data: InternalSocketData = field(default_factory=InternalSocketData)
    get: InternalSocketGet = field(default_factory=InternalSocketGet)
