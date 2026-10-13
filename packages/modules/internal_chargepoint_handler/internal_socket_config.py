from dataclasses import dataclass, field
from typing import List, Optional

from dataclass_utils.factories import currents_list_factory, voltages_list_factory

MAX_MEASUREMENT_AGE = 15


@dataclass
class InternalSocketData:
    set_state: bool = False
    heartbeat: float = 0


@dataclass
class InternalSocketGet:
    state: bool = False
    power: float = 0
    imported: float = 0
    exported: float = 0
    currents: List[float] = field(default_factory=currents_list_factory)
    voltages: List[float] = field(default_factory=voltages_list_factory)
    powers: List[float] = field(default_factory=currents_list_factory)
    fault_state: int = 2
    fault_str: str = "Steckdosenmessung noch nicht initialisiert."
    timestamp: float = 0
    error_timestamp: Optional[float] = None


@dataclass
class InternalSocket:
    data: InternalSocketData = field(default_factory=InternalSocketData)
    get: InternalSocketGet = field(default_factory=InternalSocketGet)
