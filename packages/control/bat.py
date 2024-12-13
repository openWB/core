from dataclasses import dataclass, field
import logging
from typing import List

from dataclass_utils.factories import currents_list_factory
from helpermodules.constants import NO_ERROR

log = logging.getLogger(__name__)


@dataclass
class Get:
    currents: List[float] = field(default_factory=currents_list_factory, metadata={
                                  "topic": "get/currents"})
    soc: float = field(default=0, metadata={"topic": "get/soc"})
    daily_exported: float = field(default=0, metadata={"topic": "get/daily_exported"})
    daily_imported: float = field(default=0, metadata={"topic": "get/daily_imported"})
    imported: float = field(default=0, metadata={"topic": "get/imported"})
    exported: float = field(default=0, metadata={"topic": "get/exported"})
    fault_state: int = field(default=0, metadata={"topic": "get/fault_state"})
    fault_str: str = field(default=NO_ERROR, metadata={"topic": "get/fault_str"})
    power: float = field(default=0, metadata={"topic": "get/power"})
    power_limit_controllable: bool = field(default=False, metadata={"topic": "get/power_limit_controllable"})


def get_factory() -> Get:
    return Get()


@dataclass
class Set:
    power_limit: float = field(default=0, metadata={"topic": "set/power_limit"})


def set_factory() -> Set:
    return Set()


@dataclass
class BatData:
    get: Get = field(default_factory=get_factory)
    set: Set = field(default_factory=set_factory)


class Bat:

    def __init__(self, index):
        self.data = BatData()
        self.num = index
