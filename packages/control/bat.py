from dataclasses import dataclass, field
import logging
from typing import List

from dataclass_utils.factories import currents_list_factory

log = logging.getLogger(__name__)


@dataclass
class Get:
    currents: List[float] = field(default_factory=currents_list_factory)
    soc: float = 0
    daily_exported: float = 0
    daily_imported: float = 0
    imported: float = 0
    exported: float = 0
    fault_state: int = 0
    fault_str: str = ""
    power: float = 0


def get_factory() -> Get:
    return Get()


@dataclass
class BatData:
    get: Get = field(default_factory=get_factory)


class Bat:

    def __init__(self, index):
        self.data = BatData()
        self.num = index
